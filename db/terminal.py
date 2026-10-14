"""Terminal SQL do db.rodado.xyz (servido pelo ttyd no navegador).

Lê SQL até o `;`, roda pelo núcleo travado de rodado_sql.py e imprime a tabela
como o CLI do DuckDB. Sem os comandos de ponto do CLI: só os daqui.

A entrada é do prompt_toolkit (instalado na imagem; vendor/ era o jeito no beelink, sem
ensurepip nem sudo para um venv): SQL colorido enquanto se digita, várias
linhas até o `;` e autocompletar de dataset, tabela e coluna. Sem ele, cai
no input() com readline.
"""

import os
import re
import shutil
import signal
import sys
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
# Sem CPR (pedido de posição do cursor): a resposta faria Suíça -> Helsinque -> Suíça a cada
# prompt (~240 ms), se misturava com texto colado e, quando se perdia, a tela parava de
# atualizar até a próxima tecla.
os.environ.setdefault("PROMPT_TOOLKIT_NO_CPR", "1")

import duckdb  # noqa: E402

import rodado_sql  # noqa: E402

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.formatted_text import ANSI
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.lexers import PygmentsLexer
    from prompt_toolkit.output import ColorDepth
    from prompt_toolkit.styles import Style, merge_styles, style_from_pygments_dict
    from pygments.lexers.sql import SqlLexer
    from pygments.token import Token
except ImportError:  # sem vendor/: entrada simples
    PromptSession = None
    import readline  # noqa: F401 — histórico e edição de linha no input()

OCIOSO = 30 * 60  # fecha a sessão parada


# Catppuccin Mocha em truecolor (https://catppuccin.com/palette).
def _cor(hexa):
    r, g, b = (int(hexa[i:i + 2], 16) for i in (0, 2, 4))
    return f"\x1b[38;2;{r};{g};{b}m"


FIM = "\x1b[0m"
MAUVE, VERMELHO, CINZA, VERDE, PESSEGO = (_cor(c) for c in ("cba6f7", "f38ba8", "9399b2", "a6e3a1", "fab387"))

AJUDA = """\
Comandos (terminam em ;, podem ocupar várias linhas — Enter só envia depois do ;):
  SELECT ... ;                 FROM dataset.tabela LIMIT 5;
  DESCRIBE dataset.tabela;     SUMMARIZE dataset.tabela;
Atalhos:
  .datasets                    lista os datasets
  .tabelas <dataset>           lista as tabelas de um dataset
  .linhas <n>                  quantas linhas mostrar (padrão 40)
  .ajuda   .sair
Tab completa dataset, tabela e coluna. Ctrl-C interrompe a consulta ou limpa a linha.
Só leitura; limite de {t} s por consulta. Filtre tabelas grandes por partição (ano, mes, sigla_uf).
"""

ATALHOS = {
    ".datasets": "SELECT schema_name AS dataset, count(*) AS tabelas FROM duckdb_views() "
    "WHERE NOT internal AND schema_name NOT LIKE '\\_%' ESCAPE '\\' GROUP BY 1 ORDER BY 1",
    ".tabelas": "SELECT view_name AS tabela FROM duckdb_views() WHERE schema_name = '{}' ORDER BY 1",
}

PALAVRAS = """SELECT FROM WHERE GROUP BY ORDER HAVING LIMIT OFFSET WITH AS AND OR NOT IN IS NULL
LIKE ILIKE BETWEEN CASE WHEN THEN ELSE END JOIN LEFT RIGHT FULL INNER OUTER CROSS ON USING
UNION ALL DISTINCT EXCEPT INTERSECT DESCRIBE SUMMARIZE SHOW TABLES QUALIFY OVER PARTITION
WINDOW ASC DESC NULLS FIRST LAST COUNT SUM AVG MIN MAX CAST TRY_CAST COALESCE NULLIF
STRFTIME STRPTIME DATE_TRUNC EXTRACT YEAR MONTH ROUND REGEXP_MATCHES STRING_AGG LIST
ARRAY_AGG ANY_VALUE ARG_MAX ARG_MIN QUANTILE_CONT MEDIAN APPROX_COUNT_DISTINCT PIVOT UNPIVOT
SAMPLE EXCLUDE REPLACE COLUMNS LATERAL""".split()


def avisa(cor, texto):
    print(f"{cor}{texto}{FIM}")


def _ocioso(*_):
    print("\nsessão encerrada por inatividade", flush=True)
    os._exit(0)


class Girando:
    """Indicador "⠹ rodando… 3,2 s" enquanto a consulta não devolve nada.

    Lida do S3, uma consulta fria leva de 10 a 15 s sem nenhum sinal de vida. rel.show()
    executa e imprime numa chamada só, mas imprime pelo sys.stdout do Python: durante a
    consulta ele é trocado por este objeto, e a primeira escrita (a tabela, um aviso) apaga
    o indicador antes de passar. Consulta rápida não pisca: só aparece depois de 0,3 s.
    """

    QUADROS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self):
        self._real = sys.stdout
        self._fim = threading.Event()
        self._trava = threading.Lock()
        self._desenhou = False
        self._thread = threading.Thread(target=self._gira, daemon=True)

    def _gira(self):
        inicio = time.monotonic()
        if self._fim.wait(0.3):
            return
        i = 0
        while True:
            with self._trava:
                if self._fim.is_set():
                    return
                seg = f"{time.monotonic() - inicio:.1f}".replace(".", ",")
                self._real.write(f"\r{CINZA}{self.QUADROS[i % len(self.QUADROS)]} rodando… {seg} s{FIM}\x1b[K")
                self._real.flush()
                self._desenhou = True
            i += 1
            if self._fim.wait(0.1):
                return

    def _para(self):
        with self._trava:
            if not self._fim.is_set():
                self._fim.set()
                if self._desenhou:
                    self._real.write("\r\x1b[K")

    def write(self, texto):
        self._para()
        return self._real.write(texto)

    def flush(self):
        self._real.flush()

    def __getattr__(self, nome):
        return getattr(self._real, nome)

    def __enter__(self):
        sys.stdout = self
        self._thread.start()
        return self

    def __exit__(self, *_):
        self._para()
        sys.stdout = self._real
        self._real.flush()


def mostra(sql: str, linhas: int):
    con = rodado_sql.conecta()
    try:
        for comando in rodado_sql.separa(con, sql):
            inicio = time.monotonic()
            with rodado_sql.Cronometro(con) as crono, Girando():
                try:
                    rel = con.sql(comando.query)
                    largura = shutil.get_terminal_size((120, 40)).columns
                    rel.show(max_width=largura, max_rows=linhas)
                except (duckdb.InterruptException, KeyboardInterrupt):
                    avisa(PESSEGO, "tempo limite estourado" if crono.estourou else "interrompido")
                    return
            avisa(CINZA, f"({time.monotonic() - inicio:.2f} s)")
    finally:
        con.close()


def _roda(sql: str, linhas: int):
    try:
        mostra(sql, linhas)
    except rodado_sql.ConsultaRecusada as e:
        avisa(VERMELHO, f"recusado: {e}")
    except KeyboardInterrupt:
        avisa(PESSEGO, "interrompido")
    except duckdb.Error as e:
        avisa(VERMELHO, str(e))


def _consulta_simples(sql):
    con = rodado_sql.conecta()
    try:
        return con.sql(sql).fetchall()
    finally:
        con.close()


if PromptSession:
    # Pygments -> Catppuccin Mocha
    ESTILO = merge_styles([
        style_from_pygments_dict({
            Token.Keyword: "#cba6f7 bold",
            Token.Name.Builtin: "#89b4fa",
            Token.Name.Function: "#89b4fa",
            Token.Literal.String: "#a6e3a1",
            Token.Literal.String.Single: "#a6e3a1",
            Token.Literal.String.Symbol: "#f9e2af",
            Token.Literal.Number: "#fab387",
            Token.Comment: "#9399b2 italic",
            Token.Operator: "#89dceb",
            Token.Punctuation: "#9399b2",
            Token.Name: "#cdd6f4",
        }),
        Style.from_dict({
            "completion-menu": "bg:#181825 #cdd6f4",
            "completion-menu.completion.current": "bg:#45475a #cdd6f4 bold",
            "completion-menu.meta.completion": "bg:#181825 #7f849c",
            "completion-menu.meta.completion.current": "bg:#45475a #a6adc8",
            "scrollbar.background": "bg:#181825",
            "scrollbar.button": "bg:#45475a",
        }),
    ])

    class Completa(Completer):
        """dataset, dataset.tabela e as colunas das tabelas já citadas na consulta."""

        def __init__(self):
            self.tabelas = {}  # dataset -> [tabela]
            self.colunas = {}  # dataset.tabela -> [(coluna, tipo)]

        def carrega(self):
            try:
                for ds, tb in _consulta_simples(
                        "SELECT schema_name, view_name FROM duckdb_views() WHERE NOT internal "
                        "AND schema_name NOT LIKE '\\_%' ESCAPE '\\' ORDER BY 1, 2"):
                    self.tabelas.setdefault(ds, []).append(tb)
            except duckdb.Error:
                pass

        def _colunas_de(self, alvo):
            """Colunas de uma tabela citada. A 1ª leitura (~100 ms) vai para uma thread:
            a tecla nunca espera, e as colunas entram na sugestão seguinte."""
            if alvo not in self.colunas:
                self.colunas[alvo] = []  # marca como "buscando"

                def busca():
                    ds, tb = alvo.split(".", 1)
                    try:
                        # do catálogo, sem religar a view (DESCRIBE releria os rodapés do S3)
                        ds, tb = ds.replace("'", "''"), tb.replace("'", "''")
                        self.colunas[alvo] = _consulta_simples(
                            "SELECT column_name, data_type FROM duckdb_columns() "
                            f"WHERE schema_name = '{ds}' AND table_name = '{tb}' ORDER BY column_index")
                    except duckdb.Error:
                        pass

                threading.Thread(target=busca, daemon=True).start()
            return self.colunas[alvo]

        def get_completions(self, documento, evento):
            palavra = documento.get_word_before_cursor(pattern=re.compile(r"[\w.]+"))
            if not palavra or (len(palavra) < 2 and not evento.completion_requested):
                return
            p = palavra.lower()
            if "." in palavra:
                ds, _, prefixo = palavra.partition(".")
                for tb in self.tabelas.get(ds, []):
                    if tb.startswith(prefixo.lower()):
                        yield Completion(f"{ds}.{tb}", -len(palavra), display=tb, display_meta=ds)
                return
            texto = documento.text
            citadas = {t for t in re.findall(r"\b(\w+\.\w+)\b", texto)
                       if t.split(".")[0] in self.tabelas and t.split(".")[1] in self.tabelas[t.split(".")[0]]}
            vistas = set()
            for alvo in sorted(citadas):
                for col, tipo in self._colunas_de(alvo):
                    if col.lower().startswith(p) and col not in vistas:
                        vistas.add(col)
                        yield Completion(col, -len(palavra), display_meta=tipo.lower())
            for ds in self.tabelas:
                if ds.startswith(p):
                    yield Completion(ds, -len(palavra), display_meta=f"{len(self.tabelas[ds])} tabelas")
            for kw in PALAVRAS:
                if kw.lower().startswith(p) and kw.lower() != p:
                    yield Completion(kw, -len(palavra))

    def _teclas():
        kb = KeyBindings()

        @kb.add("enter")
        def _(evento):
            buf = evento.current_buffer
            texto = buf.text.strip()
            # envia no ;, num atalho de ponto ou com a linha vazia; senão quebra a linha
            if not texto or texto.endswith(";") or (texto.startswith(".") and "\n" not in texto):
                buf.validate_and_handle()
            else:
                buf.insert_text("\n")

        @kb.add("escape", "enter")  # Alt-Enter envia mesmo sem ;
        def _(evento):
            evento.current_buffer.validate_and_handle()

        return kb


def _entrada():
    """Devolve uma função que lê o próximo comando (pode ter várias linhas)."""
    if not PromptSession:
        def le():
            buffer = []
            while True:
                linha = input("rodado> " if not buffer else "   ...> ")
                buffer.append(linha)
                texto = "\n".join(buffer).strip()
                if not texto or texto.endswith(";") or texto.startswith("."):
                    return texto
        return le

    completa = Completa()
    completa.carrega()
    sessao = PromptSession(
        history=InMemoryHistory(),
        lexer=PygmentsLexer(SqlLexer),
        style=ESTILO,
        completer=completa,
        complete_while_typing=True,
        multiline=True,
        key_bindings=_teclas(),
        prompt_continuation=lambda largura, *_: ANSI(f"{CINZA}{'...> '.rjust(largura)}{FIM}"),
        color_depth=ColorDepth.TRUE_COLOR,
        include_default_pygments_style=False,
    )
    return lambda: sessao.prompt(ANSI(f"{MAUVE}rodado>{FIM} ")).strip()


LOGO = r"""
               _           _
 _ __ ___   __| | __ _  __| | ___
| '__/ _ \ / _` |/ _` |/ _` |/ _ \
| | | (_) | (_| | (_| | (_| | (_) |
|_|  \___/ \__,_|\__,_|\__,_|\___/
""".strip("\n").splitlines()
# Mauve -> rosa -> pêssego, uma cor por linha do logo
DEGRADE = [_cor(c) for c in ("cba6f7", "d9a4e8", "f5c2e7", "f2b8b5", "fab387")]

# Contado do catálogo desta instância, não fixo: só o que se consulta daqui.
SQL_RESUMO = r"""
SELECT count(*), count(DISTINCT v.schema_name), coalesce(sum(m.rows), 0),
       count(DISTINCT m.source_name)
FROM duckdb_views() v
LEFT JOIN _rodado_metadata m ON m.dataset = v.schema_name AND m."table" = v.view_name
WHERE NOT v.internal AND v.schema_name NOT LIKE '\_%' ESCAPE '\' AND v.schema_name <> 'main'
"""


ATLAS = "https://rodado.xyz/atlas/?mode=temas"


def _link(url, texto):
    """Hyperlink OSC 8; index.html abre em nova aba (linkHandler do xterm)."""
    return f"\x1b]8;;{url}\x1b\\{MAUVE}{texto}{FIM}\x1b]8;;\x1b\\"


def _milhar(n):
    return f"{n:,}".replace(",", ".")


def _linhas_curto(n):
    if n >= 1e9:
        return f"{n / 1e9:.1f}".replace(".", ",") + " bi"
    if n >= 1e6:
        return f"{n / 1e6:.1f}".replace(".", ",") + " mi"
    return _milhar(int(n))


def _resumo(tab, ds, linhas, fontes):
    partes = [(_milhar(tab), "tabelas"), (_milhar(ds), "datasets"),
              (_linhas_curto(linhas), "linhas"), (_milhar(fontes), "fontes")]
    # numa tela estreita (celular) a linha quebraria e o \r da animação deixaria lixo
    largura = shutil.get_terminal_size().columns - 3
    while len(partes) > 1 and len(" · ".join(f"{n} {r}" for n, r in partes)) > largura:
        partes.pop()
    return f" {CINZA}·{FIM} ".join(f"{PESSEGO}{n}{FIM} {r}" for n, r in partes)


def _abertura():
    """Logo na hora; a linha de números gira enquanto o catálogo responde e então
    sobe de zero até o valor real."""
    print()
    for cor, linha in zip(DEGRADE, LOGO):
        print(f"{cor}{linha}{FIM}")
    print(f"\n{CINZA}= {FIM}espelho de dados públicos brasileiros{CINZA} ={FIM}")

    resultado = []

    def conta():
        try:
            resultado.extend(_consulta_simples(SQL_RESUMO))
        except duckdb.Error:
            pass  # sem números: o terminal abre do mesmo jeito

    busca = threading.Thread(target=conta, daemon=True)
    busca.start()
    i = 0
    while busca.is_alive() and i < 300:  # 30 s no máximo
        sys.stdout.write(f"\r  {CINZA}{Girando.QUADROS[i % len(Girando.QUADROS)]} contando o catálogo…{FIM}\x1b[K")
        sys.stdout.flush()
        busca.join(0.1)
        i += 1
    if not resultado:
        sys.stdout.write("\r\x1b[K")
    else:
        alvo = [float(x or 0) for x in resultado[0]]
        passos = 12
        for p in range(1, passos + 1):
            f = 1 - (1 - p / passos) ** 3  # desacelera no fim
            vals = [int(v * f) if p < passos else int(v) for v in alvo]
            sys.stdout.write(f"\r  {_resumo(*vals)}\x1b[K")
            sys.stdout.flush()
            if p < passos:
                time.sleep(0.03)
        sys.stdout.write("\n")
    rodape = "DuckDB, só leitura · .ajuda para os comandos"
    if len(f"  {rodape} · [atlas]") <= shutil.get_terminal_size().columns:
        print(f"  {CINZA}{rodape} ·{FIM} {_link(ATLAS, '[atlas]')}\n")
    else:  # tela estreita: o link desce uma linha em vez de quebrar no meio
        print(f"  {CINZA}{rodape}{FIM}\n  {_link(ATLAS, '[atlas]')}\n")


def main():
    signal.signal(signal.SIGALRM, _ocioso)
    _abertura()
    le = _entrada()
    linhas = 40
    while True:
        signal.alarm(OCIOSO)
        try:
            texto = le()
        except EOFError:
            print()
            return
        except KeyboardInterrupt:
            continue
        finally:
            signal.alarm(0)
        if not texto:
            continue

        if texto.startswith("."):
            partes = texto.rstrip(";").split()
            cmd, args = partes[0], partes[1:]
            if cmd in (".sair", ".exit", ".quit", ".q"):
                return
            if cmd in (".ajuda", ".help"):
                print(AJUDA.format(t=rodado_sql.TEMPO_LIMITE))
            elif cmd == ".linhas" and args and args[0].isdigit():
                linhas = int(args[0])
            elif cmd == ".datasets":
                _roda(ATALHOS[".datasets"], 10_000)
            elif cmd in (".tabelas", ".tables") and args and args[0].isidentifier():
                _roda(ATALHOS[".tabelas"].format(args[0].replace("'", "''")), 10_000)
            else:
                avisa(PESSEGO, "atalho desconhecido — .ajuda lista os que existem")
            continue

        _roda(texto, linhas)


if __name__ == "__main__":
    main()
