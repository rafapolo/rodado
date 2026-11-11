"""Limites contra raspagem do /query (plano em tasks/plans/limites_abuso_db.md).

Sem dependência de DuckDB nem de rede, para testar sozinho (`python3 db/testes/limites.py`).
Peças, todas configuráveis por variável de ambiente (valores em `Config.do_ambiente`):

- tokens por pessoa (`DB_TOKENS="nome:token,nome2:token2"`), que o Caddy valida e o app só
  usa para dar nome à consulta (cabeçalho `X-Rodado-Token`, posto pelo Caddy);
- cota diária de linhas **e de bytes** devolvidos, por token (ou por IP, sem token), num SQLite
  no volume: só linhas deixava `to_json(list(...))` levar uma partição inteira numa linha;
- um balde comum a todo o tráfego sem token (senha compartilhada, link /q): trocar de IP não
  multiplica a cota; teto de bytes por resposta;
- janela deslizante de consultas por minuto e teto de consultas simultâneas, por IP (IPv6 por
  /64: quem tem uma /64 tem 2^64 endereços);
- recusa do padrão de raspagem, lendo a árvore do `json_serialize_sql`: `OFFSET` alto e
  `SELECT *` sem filtro numa tabela grande.

`python3 limites.py regex` imprime a regex que o Caddy usa para reconhecer os tokens
(`inicia.sh` a exporta como DB_TOKENS_RE); nunca imprime nomes nem o token.
"""

import collections
import dataclasses
import datetime
import ipaddress
import math
import os
import re
import sqlite3
import sys
import threading
import time

BRT = datetime.timezone(datetime.timedelta(hours=-3))
NOME_OK = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")
# só estes caracteres: entram sem escape na regex do Caddy (e o `-` fora de classe é literal)
TOKEN_OK = re.compile(r"^[A-Za-z0-9_-]{16,128}$")
REGEX_NENHUM = "a^"     # RE2 válida que nunca casa; vazia casaria o token ausente
BALDE_SENHA = "senha:todos"   # chave da cota comum de quem entra sem token pessoal
BALDE_TERMINAL = "terminal:todos"   # cota comum a todas as abas do terminal (/tty), que não sabe o IP
NOME_LINK = "link"                  # o DB_TOKEN_LINK, que o link /q grava no cookie de quem o abre
BALDE_LINK = f"token:{NOME_LINK}"   # cota comum a todos os visitantes de links


def _inteiro(nome, padrao):
    try:
        return int(os.environ.get(nome, padrao))
    except ValueError:
        return int(padrao)


@dataclasses.dataclass
class Config:
    cota_dia: int = 200_000        # linhas devolvidas por chave e dia; 0 desliga
    cota_bytes_dia: int = 250_000_000      # bytes devolvidos por chave e dia; 0 desliga
    resposta_max_bytes: int = 25_000_000   # uma resposta acima disso é recusada (413); 0 desliga
    cota_senha_dia: int = 2_000_000        # linhas por dia somando todo o tráfego sem token; 0 desliga
    cota_senha_bytes_dia: int = 2_500_000_000   # bytes, idem; 0 desliga
    prefixo_ipv6: int = 64         # IPv6 vira esta rede na chave de cota e ritmo
    cota_link_dia: int = 50_000             # linhas por dia, todos os visitantes de link /q somados
    cota_link_bytes_dia: int = 50_000_000   # bytes, idem
    terminal_max_linhas: int = 200          # teto do `.linhas` do terminal; o resto sai pelo CSV (#exporta)
    cota_terminal_dia: int = 100_000        # linhas exibidas por dia, todas as abas somadas; 0 desliga
    cota_terminal_bytes_dia: int = 100_000_000   # bytes exibidos, idem; 0 desliga
    por_minuto: int = 30           # consultas por IP numa janela de 60 s; 0 desliga
    simultaneas_ip: int = 2        # consultas ao mesmo tempo por IP; 0 desliga
    offset_max: int = 100_000      # OFFSET acima disso é recusado; 0 desliga
    amplo_linhas: int = 1_000_000  # tabela acima disso não sai inteira...
    amplo_limite: int = 1_000      # ...salvo com LIMIT (ou ?limite=) até aqui; 0 desliga
    parquet_so_token: bool = False
    aviso_pct: int = 80            # aviso (uma vez por chave e dia) ao passar disto da cota
    aviso_429: int = 20            # ...ou ao levar tantos 429 de ritmo no dia; 0 desliga
    isentos: frozenset = frozenset()   # nomes de token fora da cota
    arquivo: str = "/dados/limites.sqlite"

    @classmethod
    def do_ambiente(cls):
        e = os.environ.get
        return cls(
            cota_dia=_inteiro("RODADO_COTA_DIA", 200_000),
            cota_bytes_dia=_inteiro("RODADO_COTA_BYTES_DIA", 250_000_000),
            resposta_max_bytes=_inteiro("RODADO_RESPOSTA_MAX_BYTES", 25_000_000),
            cota_senha_dia=_inteiro("RODADO_COTA_SENHA_DIA", 2_000_000),
            cota_senha_bytes_dia=_inteiro("RODADO_COTA_SENHA_BYTES_DIA", 2_500_000_000),
            prefixo_ipv6=_inteiro("RODADO_PREFIXO_IPV6", 64),
            cota_link_dia=_inteiro("RODADO_COTA_LINK_DIA", 50_000),
            cota_link_bytes_dia=_inteiro("RODADO_COTA_LINK_BYTES_DIA", 50_000_000),
            terminal_max_linhas=_inteiro("RODADO_TERMINAL_MAX_LINHAS", 200),
            cota_terminal_dia=_inteiro("RODADO_COTA_TERMINAL_DIA", 100_000),
            cota_terminal_bytes_dia=_inteiro("RODADO_COTA_TERMINAL_BYTES_DIA", 100_000_000),
            por_minuto=_inteiro("RODADO_POR_MINUTO", 30),
            simultaneas_ip=_inteiro("RODADO_SIMULTANEAS_IP", 2),
            offset_max=_inteiro("RODADO_OFFSET_MAX", 100_000),
            amplo_linhas=_inteiro("RODADO_AMPLO_LINHAS", 1_000_000),
            amplo_limite=_inteiro("RODADO_AMPLO_LIMITE", 1_000),
            parquet_so_token=e("RODADO_PARQUET_SO_TOKEN", "0") == "1",
            aviso_pct=_inteiro("RODADO_AVISO_PCT", 80),
            aviso_429=_inteiro("RODADO_AVISO_429", 20),
            isentos=frozenset(x for x in re.split(r"[,\s]+", e("RODADO_ISENTOS", "")) if x),
            arquivo=e("RODADO_LIMITES_DB", "/dados/limites.sqlite"),
        )


# ------------------------------------------------------------------ tokens

def carrega_tokens(texto):
    """`nome:token` separados por vírgula, espaço ou quebra de linha → ({token: nome}, recusados).
    Entrada fora do formato é recusada (nunca aceita pela metade); nome ou token repetido também."""
    tokens, recusados = {}, []
    nomes = set()
    for item in re.split(r"[,\s]+", texto or ""):
        if not item:
            continue
        nome, _, token = item.partition(":")
        if not NOME_OK.match(nome) or not TOKEN_OK.match(token) or token in tokens or nome in nomes:
            recusados.append(nome[:32] or "?")   # só o nome: o token nunca vai a log
            continue
        tokens[token] = nome
        nomes.add(nome)
    return tokens, recusados


def com_token_de_link(tokens, token_link):
    """Os tokens por pessoa mais o de link (nome `link`), se ele está no formato. Um token por
    pessoa chamado `link` perderia a vez: o nome é reservado."""
    tokens = {t: n for t, n in tokens.items() if n != NOME_LINK}
    if token_link and TOKEN_OK.match(token_link) and token_link not in tokens:
        tokens[token_link] = NOME_LINK
    return tokens


def regex_tokens(tokens):
    """Regex ancorada (RE2, para o Caddy) que casa exatamente um dos tokens."""
    if not tokens:
        return REGEX_NENHUM
    return "^(?:" + "|".join(sorted(tokens)) + ")$"


# ------------------------------------------------------------------ árvore do parser

def _nos(arvore):
    pilha = [arvore]
    while pilha:
        no = pilha.pop()
        if isinstance(no, list):
            pilha.extend(no)
        elif isinstance(no, dict):
            yield no
            pilha.extend(no.values())


def _literal(no):
    """Valor numérico de uma constante da árvore, ou None se não for literal."""
    if not isinstance(no, dict) or no.get("class") != "CONSTANT":
        return None
    try:
        return float((no.get("literal") or {}).get("text"))
    except (TypeError, ValueError):
        return None


def offset_alto(arvore, maximo):
    """O primeiro OFFSET acima de `maximo` em qualquer ponto da consulta (subconsulta e CTE
    incluídas) → (valor, None); OFFSET que não é literal (conta, subconsulta) → (None, "não literal")
    porque não dá para provar que é baixo; senão None."""
    if not maximo:
        return None
    for no in _nos(arvore):
        if no.get("type") == "LIMIT_MODIFIER" and no.get("offset") is not None:
            valor = _literal(no["offset"])
            if valor is None:
                return None, "não literal"
            if valor > maximo:
                return valor, None
    return None


def selecao_ampla(arvore):
    """(dataset, tabela, limite_do_sql) se o comando de cima é uma leitura sem filtro de uma
    tabela só: colunas cruas ou `*`, sem WHERE, GROUP BY, HAVING, QUALIFY, DISTINCT nem amostra,
    sem join. `limite_do_sql` é o LIMIT literal, ou None se não há (ou se é percentual ou conta).
    Qualquer outra forma devolve None: agregação, filtro e subconsulta passam."""
    try:
        no = arvore["statements"][0]["node"]
    except (KeyError, IndexError, TypeError):
        return None
    if no.get("type") != "SELECT_NODE":
        return None
    origem = no.get("from_table") or {}
    if origem.get("type") != "BASE_TABLE" or not origem.get("schema_name") or origem.get("sample"):
        return None
    if no.get("where_clause") or no.get("group_expressions") or no.get("having") or no.get("qualify") \
            or no.get("sample") or (no.get("cte_map") or {}).get("map"):
        return None
    if not no.get("select_list") or any(c.get("class") not in ("STAR", "COLUMN_REF") for c in no["select_list"]):
        return None
    limite = None
    for m in no.get("modifiers") or []:
        if m.get("type") == "DISTINCT_MODIFIER":
            return None
        if m.get("type") == "LIMIT_MODIFIER" and m.get("limit") is not None and m.get("limit_type") == "ROW_COUNT":
            limite = _literal(m["limit"])
    return origem["schema_name"], origem.get("table_name") or "", limite


def raspagem(arvore, linhas_da_tabela, limite_pedido, cfg):
    """Mensagem e dica de 400 se a consulta tem cara de raspagem; senão None.
    `linhas_da_tabela(dataset, tabela)` → número de linhas (ou None se não se sabe)."""
    achado = offset_alto(arvore, cfg.offset_max)
    if achado:
        valor, porque = achado
        if valor is None:
            return ("OFFSET precisa ser um número literal", "escreva OFFSET <número> (até "
                    f"{cfg.offset_max}); para mais fundo, filtre por partição (ano, mes, sigla_uf)")
        return (f"OFFSET {int(valor)} acima do máximo de {cfg.offset_max}",
                "não pagine fundo: agregue no servidor (GROUP BY), filtre por partição (ano, mes, sigla_uf) "
                "ou por chave (WHERE id > <último visto> ORDER BY id LIMIT n)")
    if cfg.amplo_limite:
        amplo = selecao_ampla(arvore)
        if amplo:
            ds, t, limite_sql = amplo
            efetivo = min(x for x in (limite_sql, limite_pedido) if x is not None)
            n = linhas_da_tabela(ds, t)
            if n is not None and n > cfg.amplo_linhas and efetivo > cfg.amplo_limite:
                return (f"{ds}.{t} tem {n:,} linhas e a consulta a lê inteira, sem filtro".replace(",", "."),
                        f"agregue (GROUP BY), filtre (WHERE) ou limite a até {cfg.amplo_limite} linhas "
                        f"(LIMIT {cfg.amplo_limite} ou ?limite={cfg.amplo_limite})")
    return None


# ------------------------------------------------------------------ cota e ritmo

def chave_ip(ip, prefixo6=64):
    """O IP como chave de cota e ritmo: IPv6 agrupado na rede /prefixo6 (um cliente comum recebe
    uma /64 inteira e troca de endereço à vontade), IPv4 mapeado em IPv6 volta a IPv4, e sem IP
    (chamada de dentro do container que não repassou quem pediu) vira "interno", limitado também."""
    ip = (ip or "").strip()
    if not ip:
        return "interno"
    try:
        end = ipaddress.ip_address(ip)
    except ValueError:
        return ip
    if end.version == 6 and end.ipv4_mapped:
        return str(end.ipv4_mapped)
    if end.version == 6:
        return str(ipaddress.ip_network(f"{end}/{prefixo6}", strict=False))
    return str(end)


def dia_de(agora):
    return datetime.datetime.fromtimestamp(agora, BRT).strftime("%Y-%m-%d")


def segundos_ate_meia_noite(agora):
    d = datetime.datetime.fromtimestamp(agora, BRT)
    amanha = (d + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(1, math.ceil((amanha - d).total_seconds()))


class Limites:
    """Estado dos limites: cota em SQLite (sobrevive a deploy e reinício), janela por minuto e
    simultâneas em memória. `avisar(texto)` recebe os avisos (uma vez por chave, tipo e dia)."""

    def __init__(self, cfg, avisar=None, relogio=time.time):
        self.cfg = cfg
        self.avisar = avisar or (lambda texto: print(f"[limites] AVISO {texto}", flush=True))
        self.relogio = relogio
        self._trava = threading.Lock()
        self._janela = collections.defaultdict(collections.deque)   # ip -> instantes
        self._ativas = collections.Counter()                         # ip -> consultas em curso
        self._db = self._abre(cfg.arquivo)

    @staticmethod
    def _abre(arquivo):
        try:
            # timeout: o terminal (uma instância por aba) e o consulta.py gravam no mesmo arquivo
            db = sqlite3.connect(arquivo, check_same_thread=False, timeout=10)
        except sqlite3.Error:      # volume ausente: a cota vale até o reinício, o resto segue
            print(f"[limites] sem {arquivo}: cota só em memória", flush=True)
            db = sqlite3.connect(":memory:", check_same_thread=False)
        db.execute("CREATE TABLE IF NOT EXISTS cota (chave TEXT, dia TEXT, linhas INTEGER NOT NULL DEFAULT 0, "
                   "bytes INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (chave, dia))")
        if "bytes" not in {r[1] for r in db.execute("PRAGMA table_info(cota)")}:   # volume de antes dos bytes
            try:
                db.execute("ALTER TABLE cota ADD COLUMN bytes INTEGER NOT NULL DEFAULT 0")
            except sqlite3.OperationalError:   # o terminal ou o consulta.py acabou de acrescentar
                pass
        db.execute("CREATE TABLE IF NOT EXISTS avisos (chave TEXT, dia TEXT, tipo TEXT, PRIMARY KEY (chave, dia, tipo))")
        db.execute("CREATE TABLE IF NOT EXISTS ritmo (chave TEXT, dia TEXT, recusas INTEGER NOT NULL DEFAULT 0, "
                   "PRIMARY KEY (chave, dia))")
        db.commit()
        return db

    # -- cota
    def tetos(self, chave):
        """(linhas, bytes) por dia da chave; 0 é sem teto. O balde da senha tem os seus."""
        if chave == BALDE_SENHA:
            return self.cfg.cota_senha_dia, self.cfg.cota_senha_bytes_dia
        if chave == BALDE_LINK:
            return self.cfg.cota_link_dia, self.cfg.cota_link_bytes_dia
        if chave == BALDE_TERMINAL:
            return self.cfg.cota_terminal_dia, self.cfg.cota_terminal_bytes_dia
        return self.cfg.cota_dia, self.cfg.cota_bytes_dia

    def usado(self, chave):
        """(linhas, bytes) entregues hoje à chave."""
        with self._trava:
            r = self._db.execute("SELECT linhas, bytes FROM cota WHERE chave = ? AND dia = ?",
                                 (chave, dia_de(self.relogio()))).fetchone()
        return tuple(r) if r else (0, 0)

    def restante(self, chave, isento=False):
        """Linhas que a chave ainda pode receber hoje; None se não há cota."""
        teto = self.tetos(chave)[0]
        if isento or not teto:
            return None
        return max(0, teto - self.usado(chave)[0])

    def restante_bytes(self, chave, isento=False):
        """Bytes que a chave ainda pode receber hoje; None se não há cota."""
        teto = self.tetos(chave)[1]
        if isento or not teto:
            return None
        return max(0, teto - self.usado(chave)[1])

    def registra(self, chave, linhas, isento=False, bytes_=0):
        teto_l, teto_b = self.tetos(chave)
        if isento or not (teto_l or teto_b) or (linhas <= 0 and bytes_ <= 0):
            return
        agora = self.relogio()
        dia = dia_de(agora)
        linhas, bytes_ = max(0, linhas), max(0, bytes_)
        with self._trava:
            self._db.execute("INSERT INTO cota (chave, dia, linhas, bytes) VALUES (?, ?, ?, ?) "
                             "ON CONFLICT (chave, dia) DO UPDATE SET linhas = linhas + excluded.linhas, "
                             "bytes = bytes + excluded.bytes", (chave, dia, linhas, bytes_))
            for t in ("cota", "avisos", "ritmo"):   # o histórico não serve a nada: só hoje conta
                self._db.execute(f"DELETE FROM {t} WHERE dia < ?", (dia,))
            self._db.commit()
            usado_l, usado_b = self._db.execute("SELECT linhas, bytes FROM cota WHERE chave = ? AND dia = ?",
                                                (chave, dia)).fetchone()
        if not self.cfg.aviso_pct:
            return
        if teto_l and usado_l * 100 >= teto_l * self.cfg.aviso_pct:
            self._avisa_uma_vez(chave, dia, "cota",
                                f"{chave} usou {usado_l} de {teto_l} linhas hoje ({usado_l * 100 // teto_l}%)")
        if teto_b and usado_b * 100 >= teto_b * self.cfg.aviso_pct:
            self._avisa_uma_vez(chave, dia, "bytes",
                                f"{chave} usou {usado_b} de {teto_b} bytes hoje ({usado_b * 100 // teto_b}%)")

    def _avisa_uma_vez(self, chave, dia, tipo, texto):
        with self._trava:
            cur = self._db.execute("INSERT OR IGNORE INTO avisos (chave, dia, tipo) VALUES (?, ?, ?)", (chave, dia, tipo))
            self._db.commit()
            novo = cur.rowcount == 1
        if novo:
            self.avisar(texto)

    # -- ritmo por IP
    def admite(self, ip):
        """None se a consulta pode entrar; senão (segundos_para_tentar_de_novo, motivo).
        Reserva a vaga: quem recebe None tem de chamar `libera(ip)` ao terminar."""
        agora = self.relogio()
        with self._trava:
            fila = self._janela[ip]
            while fila and fila[0] <= agora - 60:
                fila.popleft()
            if self.cfg.por_minuto and len(fila) >= self.cfg.por_minuto:
                espera = max(1, math.ceil(fila[0] + 60 - agora))
                motivo = f"mais de {self.cfg.por_minuto} consultas por minuto neste IP"
            elif self.cfg.simultaneas_ip and self._ativas[ip] >= self.cfg.simultaneas_ip:
                espera, motivo = 5, f"mais de {self.cfg.simultaneas_ip} consultas ao mesmo tempo neste IP"
            else:
                fila.append(agora)
                self._ativas[ip] += 1
                if len(self._janela) > 5000:   # nunca cresce sem fim
                    for k in [k for k, v in self._janela.items() if not v or v[-1] <= agora - 60]:
                        if not self._ativas[k]:
                            del self._janela[k]
                return None
        self._conta_recusa(ip)
        return espera, motivo

    def libera(self, ip):
        with self._trava:
            self._ativas[ip] -= 1
            if self._ativas[ip] <= 0:
                del self._ativas[ip]

    def _conta_recusa(self, ip):
        dia = dia_de(self.relogio())
        with self._trava:
            self._db.execute("INSERT INTO ritmo (chave, dia, recusas) VALUES (?, ?, 1) "
                             "ON CONFLICT (chave, dia) DO UPDATE SET recusas = recusas + 1", (ip, dia))
            self._db.commit()
            n = self._db.execute("SELECT recusas FROM ritmo WHERE chave = ? AND dia = ?", (ip, dia)).fetchone()[0]
        if self.cfg.aviso_429 and n >= self.cfg.aviso_429:
            self._avisa_uma_vez(ip, dia, "ritmo", f"{ip} levou {n} recusas por ritmo hoje")


if __name__ == "__main__":
    if sys.argv[1:] == ["regex"]:
        tokens, recusados = carrega_tokens(os.environ.get("DB_TOKENS", ""))
        for nome in recusados:
            print(f"DB_TOKENS: entrada '{nome}' recusada (formato nome:token, token de 16+ caracteres [A-Za-z0-9_-])",
                  file=sys.stderr)
        print(regex_tokens(tokens))
    else:
        sys.exit("uso: python3 limites.py regex")
