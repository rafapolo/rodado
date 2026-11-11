"""Limites contra raspagem do /query (plano em tasks/plans/limites_abuso_db.md).

Sem dependência de DuckDB nem de rede, para testar sozinho (`python3 db/testes/limites.py`).
Quatro peças, todas configuráveis por variável de ambiente (valores em `Config.do_ambiente`):

- tokens por pessoa (`DB_TOKENS="nome:token,nome2:token2"`), que o Caddy valida e o app só
  usa para dar nome à consulta (cabeçalho `X-Rodado-Token`, posto pelo Caddy);
- cota diária de linhas devolvidas, por token (ou por IP, sem token), num SQLite no volume;
- janela deslizante de consultas por minuto e teto de consultas simultâneas, por IP;
- recusa do padrão de raspagem, lendo a árvore do `json_serialize_sql`: `OFFSET` alto e
  `SELECT *` sem filtro numa tabela grande.

`python3 limites.py regex` imprime a regex que o Caddy usa para reconhecer os tokens
(`inicia.sh` a exporta como DB_TOKENS_RE); nunca imprime nomes nem o token.
"""

import collections
import dataclasses
import datetime
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


def _inteiro(nome, padrao):
    try:
        return int(os.environ.get(nome, padrao))
    except ValueError:
        return int(padrao)


@dataclasses.dataclass
class Config:
    cota_dia: int = 200_000        # linhas devolvidas por chave e dia; 0 desliga
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
            db = sqlite3.connect(arquivo, check_same_thread=False)
        except sqlite3.Error:      # volume ausente: a cota vale até o reinício, o resto segue
            print(f"[limites] sem {arquivo}: cota só em memória", flush=True)
            db = sqlite3.connect(":memory:", check_same_thread=False)
        db.execute("CREATE TABLE IF NOT EXISTS cota (chave TEXT, dia TEXT, linhas INTEGER NOT NULL DEFAULT 0, "
                   "PRIMARY KEY (chave, dia))")
        db.execute("CREATE TABLE IF NOT EXISTS avisos (chave TEXT, dia TEXT, tipo TEXT, PRIMARY KEY (chave, dia, tipo))")
        db.execute("CREATE TABLE IF NOT EXISTS ritmo (chave TEXT, dia TEXT, recusas INTEGER NOT NULL DEFAULT 0, "
                   "PRIMARY KEY (chave, dia))")
        db.commit()
        return db

    # -- cota
    def usado(self, chave):
        with self._trava:
            r = self._db.execute("SELECT linhas FROM cota WHERE chave = ? AND dia = ?",
                                 (chave, dia_de(self.relogio()))).fetchone()
        return r[0] if r else 0

    def restante(self, chave, isento=False):
        """Linhas que a chave ainda pode receber hoje; None se não há cota."""
        if isento or not self.cfg.cota_dia:
            return None
        return max(0, self.cfg.cota_dia - self.usado(chave))

    def registra(self, chave, linhas, isento=False):
        if isento or not self.cfg.cota_dia or linhas <= 0:
            return
        agora = self.relogio()
        dia = dia_de(agora)
        with self._trava:
            self._db.execute("INSERT INTO cota (chave, dia, linhas) VALUES (?, ?, ?) "
                             "ON CONFLICT (chave, dia) DO UPDATE SET linhas = linhas + excluded.linhas",
                             (chave, dia, linhas))
            for t in ("cota", "avisos", "ritmo"):   # o histórico não serve a nada: só hoje conta
                self._db.execute(f"DELETE FROM {t} WHERE dia < ?", (dia,))
            self._db.commit()
            usado = self._db.execute("SELECT linhas FROM cota WHERE chave = ? AND dia = ?", (chave, dia)).fetchone()[0]
        if self.cfg.aviso_pct and usado * 100 >= self.cfg.cota_dia * self.cfg.aviso_pct:
            self._avisa_uma_vez(chave, dia, "cota",
                                f"{chave} usou {usado} de {self.cfg.cota_dia} linhas hoje ({usado * 100 // self.cfg.cota_dia}%)")

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
