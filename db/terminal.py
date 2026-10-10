"""Terminal SQL do db.rodado.xyz (servido pelo ttyd no navegador).

Lê SQL até o `;`, roda pelo núcleo travado de rodado_sql.py e imprime a tabela
como o CLI do DuckDB. Sem os comandos de ponto do CLI: só os daqui.

A entrada é do prompt_toolkit (em vendor/, Python puro — o beelink não tem
ensurepip nem sudo para um venv): SQL colorido enquanto se digita, várias
linhas até o `;` e autocompletar de dataset, tabela e coluna. Sem ele, cai
no input() com readline.
"""

import os
import re
import shutil
import signal
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

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


def mostra(sql: str, linhas: int):
    con = rodado_sql.conecta()
    try:
        for comando in rodado_sql.separa(con, sql):
            inicio = time.monotonic()
            with rodado_sql.Cronometro(con) as crono:
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
            if alvo not in self.colunas:
                ds, tb = alvo.split(".", 1)
                try:
                    self.colunas[alvo] = [(c[0], c[1]) for c in _consulta_simples(f'DESCRIBE "{ds}"."{tb}"')]
                except duckdb.Error:
                    self.colunas[alvo] = []
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


def main():
    signal.signal(signal.SIGALRM, _ocioso)
    print(f"{MAUVE}rodado{FIM} — espelho de dados públicos brasileiros {CINZA}(DuckDB, só leitura · .ajuda){FIM}")
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
                _roda(ATALHOS[".tabelas"].format(args[0]), 10_000)
            else:
                avisa(PESSEGO, "atalho desconhecido — .ajuda lista os que existem")
            continue

        _roda(texto, linhas)


if __name__ == "__main__":
    main()
