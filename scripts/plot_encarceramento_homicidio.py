#!/usr/bin/env python3
"""Gera o dataviz encarceramento x homicidio por UF (HTML estatico + SVG inline).

Cruza a populacao prisional do SISDEPEN (br_mjsp_sisdepen.populacao_carceraria,
ciclo 1 = 2o sem 2016 e ciclo 13 = 2o sem 2022) com os homicidios do SIM
(br_ms_sim.microdados, CID-10 X85-Y09 + Y35) e a populacao do IBGE, nas 27 UFs.

Achado: r = -0,18 bruto; -0,01 ponderado por populacao; R2 de 3,4 por cento --
a relacao entre encarcerar mais e o homicidio cair nao sobrevive a checagens
de robustez (remover PR e DF inverte o sinal para +0,01).

Os dados abaixo foram apurados em 26/07/2026 via `ssh beelink` (ver CLAUDE.md) e
estao embutidos para o script rodar sem depender do beelink.

Uso:
    python3 scripts/plot_encarceramento_homicidio.py
    -> dataviz/encarceramento_homicidio.html
"""
import json, math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / 'dataviz' / 'encarceramento_homicidio.html'

ROWS = json.loads("""[{"uf":"SP","e16":514,"e22":440,"m16":10.3,"m22":6.8,"de":-14.5,"dm":-33.9,"pop":44411238},
{"uf":"AC","e16":747,"e22":716,"m16":44.4,"m22":23.0,"de":-4.1,"dm":-48.2,"pop":830018},
{"uf":"PB","e16":306,"e22":322,"m16":33.9,"m22":26.6,"de":5.2,"dm":-21.5,"pop":3974687},
{"uf":"AP","e16":375,"e22":406,"m16":48.7,"m22":38.2,"de":8.1,"dm":-21.6,"pop":733759},
{"uf":"MG","e16":311,"e22":341,"m16":22.0,"m22":9.6,"de":9.4,"dm":-56.3,"pop":20539989},
{"uf":"PE","e16":488,"e22":552,"m16":47.2,"m22":36.0,"de":13.3,"dm":-23.7,"pop":9058931},
{"uf":"MS","e16":683,"e22":787,"m16":24.3,"m22":16.9,"de":15.2,"dm":-30.7,"pop":2757013},
{"uf":"RS","e16":314,"e22":369,"m16":28.2,"m22":16.9,"de":17.3,"dm":-40.3,"pop":10882965},
{"uf":"RJ","e16":307,"e22":361,"m16":33.2,"m22":11.6,"de":17.6,"dm":-64.9,"pop":16055174},
{"uf":"SC","e16":297,"e22":355,"m16":13.9,"m22":7.8,"de":19.3,"dm":-43.9,"pop":7610361},
{"uf":"TO","e16":225,"e22":272,"m16":36.9,"m22":29.5,"de":20.8,"dm":-20.1,"pop":1511460},
{"uf":"ES","e16":499,"e22":604,"m16":31.9,"m22":25.5,"de":21.0,"dm":-19.9,"pop":3833712},
{"uf":"AM","e16":256,"e22":317,"m16":36.3,"m22":39.7,"de":23.8,"dm":9.3,"pop":3941613},
{"uf":"BA","e16":89,"e22":117,"m16":44.6,"m22":38.0,"de":31.1,"dm":-14.6,"pop":14141626},
{"uf":"PA","e16":180,"e22":243,"m16":51.0,"m22":34.0,"de":34.9,"dm":-33.4,"pop":8120131},
{"uf":"GO","e16":278,"e22":379,"m16":45.2,"m22":20.9,"de":36.2,"dm":-53.9,"pop":7056495},
{"uf":"PI","e16":132,"e22":180,"m16":21.8,"m22":22.9,"de":36.4,"dm":5.1,"pop":3271199},
{"uf":"SE","e16":220,"e22":305,"m16":64.6,"m22":33.2,"de":38.7,"dm":-48.6,"pop":2210004},
{"uf":"RO","e16":672,"e22":938,"m16":39.2,"m22":35.7,"de":39.6,"dm":-8.8,"pop":1581196},
{"uf":"RR","e16":487,"e22":717,"m16":39.5,"m22":28.1,"de":47.3,"dm":-28.8,"pop":636707},
{"uf":"CE","e16":275,"e22":424,"m16":40.6,"m22":31.0,"de":53.8,"dm":-23.6,"pop":8794957},
{"uf":"MT","e16":352,"e22":542,"m16":35.7,"m22":26.4,"de":53.9,"dm":-26.0,"pop":3658649},
{"uf":"MA","e16":118,"e22":186,"m16":34.6,"m22":26.8,"de":58.2,"dm":-22.7,"pop":6776699},
{"uf":"AL","e16":212,"e22":385,"m16":54.2,"m22":31.7,"de":81.7,"dm":-41.6,"pop":3127683},
{"uf":"DF","e16":502,"e22":968,"m16":25.5,"m22":8.0,"de":92.8,"dm":-68.6,"pop":2817381},
{"uf":"RN","e16":191,"e22":368,"m16":53.3,"m22":29.0,"de":93.0,"dm":-45.6,"pop":3302729},
{"uf":"PR","e16":327,"e22":761,"m16":26.6,"m22":15.8,"de":132.6,"dm":-40.5,"pop":11444380}]""")

def fmt(v, d=1):
    s = f"{v:.{d}f}".replace('.', ',')
    return s
def sig(v, d=1):
    return ('+' if v > 0 else '−' if v < 0 else '') + fmt(abs(v), d)
def pop_fmt(p):
    return f"{p:,}".replace(',', '.')

# ---------------------------------------------------------------- scatter A
AW, AH = 960, 520
AL, AR, AT, AB = 64, 28, 28, 60
apw, aph = AW - AL - AR, AH - AT - AB          # 868 x 432
AX0, AX1 = -25.0, 140.0
AY0, AY1 = -75.0, 15.0
def ax(v): return AL + (v - AX0) / (AX1 - AX0) * apw
def ay(v): return AT + (AY1 - v) / (AY1 - AY0) * aph
def rad(p): return 4.5 + math.sqrt(p / 1e6) * 1.5

A_SLOPE, A_INT = -0.1057, -28.28
LABELS_A = {   # uf: (dx, dy, anchor)
    'SP': (1, 4, 'start'), 'AC': (1, 4, 'start'), 'MG': (-1, 4, 'end'),
    'RJ': (1, 4, 'start'), 'AM': (1, 4, 'start'), 'PI': (1, 4, 'start'),
    'RO': (1, 4, 'start'), 'GO': (1, 4, 'start'), 'DF': (1, 4, 'start'),
    'PR': (0, -15, 'middle'),
}

def scatter_a():
    p = []
    # grid
    for gv in (15, 0, -15, -30, -45, -60, -75):
        y = ay(gv)
        cls = 'zero' if gv == 0 else 'grid'
        p.append(f'<line class="{cls}" x1="{AL}" y1="{y:.1f}" x2="{AL+apw}" y2="{y:.1f}"/>')
        p.append(f'<text class="tick" x="{AL-10:.0f}" y="{y+4:.1f}" text-anchor="end">{sig(gv,0)}%</text>')
    for gv in (0, 25, 50, 75, 100, 125):
        x = ax(gv)
        cls = 'zero-v' if gv == 0 else 'grid'
        p.append(f'<line class="{cls}" x1="{x:.1f}" y1="{AT}" x2="{x:.1f}" y2="{AT+aph}"/>')
        p.append(f'<text class="tick" x="{x:.1f}" y="{AT+aph+22:.0f}" text-anchor="middle">{sig(gv,0)}%</text>')
    # trend
    x1, y1 = ax(AX0), ay(A_INT + A_SLOPE * AX0)
    x2, y2 = ax(AX1), ay(A_INT + A_SLOPE * AX1)
    p.append(f'<line class="trend" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    p.append(f'<text class="trend-lab" x="{x2-8:.1f}" y="{y2+20:.1f}" text-anchor="end">tendência · r = −0,18</text>')
    # quadrant note
    p.append(f'<text class="qnote" x="{AL+8}" y="{AT+16}">homicídio subiu</text>')
    p.append(f'<text class="qnote" x="{AL+8}" y="{ay(0)+18:.1f}">homicídio caiu</text>')
    # dots
    for r in sorted(ROWS, key=lambda z: -z['pop']):
        cx, cy, rr = ax(r['de']), ay(r['dm']), rad(r['pop'])
        tip = (f"{r['uf']} · encarceramento {sig(r['de'])}% · "
               f"homicídio {sig(r['dm'])}% · {pop_fmt(r['pop'])} hab.")
        p.append(f'<circle class="dot" cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}"/>')
        p.append(f'<circle class="hit" cx="{cx:.1f}" cy="{cy:.1f}" r="{max(rr+9,14):.1f}" '
                 f'tabindex="0" role="img" data-tip="{tip}" aria-label="{tip}"/>')
    for uf, (sx, sy, anc) in LABELS_A.items():
        r = next(z for z in ROWS if z['uf'] == uf)
        cx, cy, rr = ax(r['de']), ay(r['dm']), rad(r['pop'])
        tx = cx + (rr + 7) * sx
        p.append(f'<text class="dotlab" x="{tx:.1f}" y="{cy+sy:.1f}" text-anchor="{anc}">{uf}</text>')
    p.append(f'<text class="axtitle" x="{AL}" y="{AH-8}">variação da taxa de encarceramento 2016→2022 →</text>')
    return (f'<svg viewBox="0 0 {AW} {AH}" role="img" '
            f'aria-label="Dispersão: variação do encarceramento contra variação do homicídio, 27 UFs.">'
            + ''.join(p) + '</svg>')

# ---------------------------------------------------------------- twin strip
SW, SH = 960, 340
SL, SR = 64, 28
spw = SW - SL - SR
SORTED = sorted(ROWS, key=lambda z: z['de'])
slot = spw / len(SORTED)
BARW = 17
T_Y0, T_H = 38, 104
T_D0, T_D1 = -20.0, 140.0
B_Y0, B_H = 186, 104
B_D0, B_D1 = -75.0, 15.0
UF_Y = 312
def ty(v): return T_Y0 + (T_D1 - v) / (T_D1 - T_D0) * T_H
def by(v): return B_Y0 + (B_D1 - v) / (B_D1 - B_D0) * B_H

def strip():
    p = []
    tz, bz = ty(0), by(0)
    p.append(f'<text class="panlab" x="{SL}" y="{T_Y0-13}">variação do ENCARCERAMENTO · critério de ordenação →</text>')
    p.append(f'<text class="panlab" x="{SL}" y="{B_Y0-13}">variação do HOMICÍDIO · mesma ordem de estados</text>')
    for v in (140, 70, 0):
        y = ty(v)
        p.append(f'<line class="{"zero" if v==0 else "grid"}" x1="{SL}" y1="{y:.1f}" x2="{SL+spw}" y2="{y:.1f}"/>')
        p.append(f'<text class="tick" x="{SL-10}" y="{y+4:.1f}" text-anchor="end">{sig(v,0)}%</text>')
    for v in (0, -35, -70):
        y = by(v)
        p.append(f'<line class="{"zero" if v==0 else "grid"}" x1="{SL}" y1="{y:.1f}" x2="{SL+spw}" y2="{y:.1f}"/>')
        p.append(f'<text class="tick" x="{SL-10}" y="{y+4:.1f}" text-anchor="end">{sig(v,0)}%</text>')
    for i, r in enumerate(SORTED):
        cx = SL + slot * (i + 0.5)
        bx = cx - BARW / 2
        # top: context bars (muted) — the sort key
        y_t = ty(max(r['de'], 0)); h_t = abs(ty(r['de']) - tz)
        p.append(f'<rect class="ctx" x="{bx:.1f}" y="{y_t:.1f}" width="{BARW}" height="{max(h_t,1.5):.1f}" rx="2"/>')
        # bottom: outcome bars (diverging)
        cls = 'up' if r['dm'] > 0 else 'down'
        y_b = by(max(r['dm'], 0)); h_b = abs(by(r['dm']) - bz)
        p.append(f'<rect class="{cls}" x="{bx:.1f}" y="{y_b:.1f}" width="{BARW}" height="{max(h_b,1.5):.1f}" rx="2"/>')
        p.append(f'<text class="uf" x="{cx:.1f}" y="{UF_Y}" text-anchor="middle">{r["uf"]}</text>')
        tip = f"{r['uf']} · encarceramento {sig(r['de'])}% · homicídio {sig(r['dm'])}%"
        p.append(f'<rect class="hit" x="{cx-slot/2:.1f}" y="{T_Y0-6}" width="{slot:.1f}" '
                 f'height="{UF_Y-T_Y0+4}" tabindex="0" role="img" data-tip="{tip}" aria-label="{tip}"/>')
    return (f'<svg viewBox="0 0 {SW} {SH}" role="img" '
            f'aria-label="Estados ordenados pelo aumento do encarceramento; a variação do homicídio não acompanha a ordem.">'
            + ''.join(p) + '</svg>')

# ---------------------------------------------------------------- scatter B
BW, BH = 960, 400
BL, BR_, BT, BB = 64, 28, 24, 56
bpw, bph = BW - BL - BR_, BH - BT - BB
BX0, BX1 = 60.0, 1010.0
BY0, BY1 = 0.0, 45.0
def bx_(v): return BL + (v - BX0) / (BX1 - BX0) * bpw
def by_(v): return BT + (BY1 - v) / (BY1 - BY0) * bph
B_SLOPE, B_INT = -0.0102, 29.46
LABELS_B = {'SP': (1,4,'start'), 'BA': (1,4,'start'), 'DF': (-1,4,'end'),
            'RO': (-1,4,'end'), 'AM': (1,4,'start'), 'SE': (1,4,'start'),
            'AC': (1,4,'start'), 'PR': (1,4,'start')}

def scatter_b():
    p = []
    for gv in (0, 15, 30, 45):
        y = by_(gv)
        p.append(f'<line class="grid" x1="{BL}" y1="{y:.1f}" x2="{BL+bpw}" y2="{y:.1f}"/>')
        p.append(f'<text class="tick" x="{BL-10}" y="{y+4:.1f}" text-anchor="end">{gv}</text>')
    for gv in (100, 300, 500, 700, 900):
        x = bx_(gv)
        p.append(f'<line class="grid" x1="{x:.1f}" y1="{BT}" x2="{x:.1f}" y2="{BT+bph}"/>')
        p.append(f'<text class="tick" x="{x:.1f}" y="{BT+bph+22:.0f}" text-anchor="middle">{gv}</text>')
    x1, y1 = bx_(BX0), by_(B_INT + B_SLOPE * BX0)
    x2, y2 = bx_(BX1), by_(B_INT + B_SLOPE * BX1)
    p.append(f'<line class="trend" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    p.append(f'<text class="trend-lab" x="{x2-8:.1f}" y="{y2+20:.1f}" text-anchor="end">tendência · r = −0,23</text>')
    for r in sorted(ROWS, key=lambda z: -z['pop']):
        cx, cy, rr = bx_(r['e22']), by_(r['m22']), rad(r['pop'])
        tip = (f"{r['uf']} · {fmt(r['e22'],0)} presos/100 mil · "
               f"{fmt(r['m22'])} homicídios/100 mil")
        p.append(f'<circle class="dot" cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}"/>')
        p.append(f'<circle class="hit" cx="{cx:.1f}" cy="{cy:.1f}" r="{max(rr+9,14):.1f}" '
                 f'tabindex="0" role="img" data-tip="{tip}" aria-label="{tip}"/>')
    for uf, (sx, sy, anc) in LABELS_B.items():
        r = next(z for z in ROWS if z['uf'] == uf)
        cx, cy, rr = bx_(r['e22']), by_(r['m22']), rad(r['pop'])
        p.append(f'<text class="dotlab" x="{cx+(rr+7)*sx:.1f}" y="{cy+sy:.1f}" text-anchor="{anc}">{uf}</text>')
    p.append(f'<text class="axtitle" x="{BL}" y="{BH-8}">presos por 100 mil habitantes, 2022 →</text>')
    return (f'<svg viewBox="0 0 {BW} {BH}" role="img" '
            f'aria-label="Dispersão: taxa de encarceramento contra taxa de homicídio em 2022, 27 UFs.">'
            + ''.join(p) + '</svg>')

# ---------------------------------------------------------------- table
def table():
    body = []
    for r in sorted(ROWS, key=lambda z: z['uf']):
        body.append(
            f'<tr><th scope="row">{r["uf"]}</th>'
            f'<td>{fmt(r["e16"],0)}</td><td>{fmt(r["e22"],0)}</td><td class="d">{sig(r["de"])}%</td>'
            f'<td>{fmt(r["m16"])}</td><td>{fmt(r["m22"])}</td>'
            f'<td class="d {"up" if r["dm"]>0 else "down"}">{sig(r["dm"])}%</td>'
            f'<td>{pop_fmt(r["pop"])}</td></tr>')
    return ''.join(body)

HTML = f'''<title>Prender mais faz o homicídio cair?</title>
<style>
:root {{
  color-scheme: light;
  --plane:#eef1f5; --surface:#fbfcfd;
  --ink:#0f1319; --ink-2:#4a5462; --ink-3:#78828f;
  --blue:#2a78d6; --red:#e34948; --ctx:#98a2ae;
  --rule:rgba(15,19,25,.13); --grid:#e4e8ed; --axis:#c8cfd7;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  --mono:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
}}
@media (prefers-color-scheme:dark) {{
  :root:where(:not([data-theme="light"])) {{
    color-scheme: dark;
    --plane:#0c0e12; --surface:#171a1e;
    --ink:#f2f5f8; --ink-2:#a9b3bf; --ink-3:#78828f;
    --blue:#3987e5; --red:#e66767; --ctx:#6b7681;
    --rule:rgba(242,245,248,.14); --grid:#262b31; --axis:#394048;
  }}
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
  --plane:#0c0e12; --surface:#171a1e;
  --ink:#f2f5f8; --ink-2:#a9b3bf; --ink-3:#78828f;
  --blue:#3987e5; --red:#e66767; --ctx:#6b7681;
  --rule:rgba(242,245,248,.14); --grid:#262b31; --axis:#394048;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--plane); color:var(--ink);
  font-family:var(--sans); font-size:16px; line-height:1.62;
  -webkit-font-smoothing:antialiased;
}}
.wrap {{ max-width:1080px; margin:0 auto; padding:clamp(28px,5vw,68px) clamp(18px,4vw,36px) 96px; }}
.measure {{ max-width:64ch; }}
.eyebrow {{
  font-family:var(--mono); font-size:.6875rem; letter-spacing:.15em;
  text-transform:uppercase; color:var(--ink-3); margin:0 0 10px;
}}
h1 {{
  font-size:clamp(1.9rem,4.4vw,2.9rem); line-height:1.12; letter-spacing:-.022em;
  font-weight:600; margin:0 0 18px; text-wrap:balance;
}}
h2 {{
  font-size:clamp(1.2rem,2.4vw,1.5rem); line-height:1.22; letter-spacing:-.015em;
  font-weight:600; margin:0 0 12px; text-wrap:balance;
}}
p {{ margin:0 0 15px; color:var(--ink-2); }}
p.lead {{ font-size:1.0625rem; color:var(--ink); }}
strong {{ font-weight:600; color:var(--ink); }}
.src {{ font-family:var(--mono); font-size:.75rem; line-height:1.6; color:var(--ink-3); }}
section {{ margin-top:clamp(40px,6vw,72px); }}
hr {{ border:0; border-top:1px solid var(--rule); margin:0; }}

/* stat row */
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:1px;
  background:var(--rule); border:1px solid var(--rule); border-radius:4px; overflow:hidden; margin-top:32px; }}
.stat {{ background:var(--surface); padding:20px 22px 22px; }}
.stat .k {{ font-family:var(--mono); font-size:.6875rem; letter-spacing:.11em; text-transform:uppercase;
  color:var(--ink-3); margin:0 0 8px; }}
.stat .v {{ font-size:2.6rem; line-height:1; font-weight:600; letter-spacing:-.03em; color:var(--ink); }}
.stat .n {{ font-size:.8125rem; line-height:1.5; color:var(--ink-2); margin:9px 0 0; }}

/* chart card */
figure {{ margin:24px 0 0; background:var(--surface); border:1px solid var(--rule);
  border-radius:4px; padding:22px clamp(14px,2.2vw,24px) 18px; }}
figcaption {{ margin:0 0 4px; }}
figcaption .t {{ font-size:.9375rem; font-weight:600; color:var(--ink); display:block; }}
figcaption .s {{ font-family:var(--mono); font-size:.75rem; color:var(--ink-3); display:block; margin-top:4px; }}
.plot {{ overflow-x:auto; margin-top:14px; }}
.plot svg {{ display:block; width:100%; height:auto; }}
.plot.wide svg {{ min-width:720px; }}
.legend {{ display:flex; flex-wrap:wrap; gap:16px; margin-top:12px;
  font-family:var(--mono); font-size:.75rem; color:var(--ink-2); }}
.legend i {{ display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:6px;
  vertical-align:baseline; }}

/* svg */
.grid {{ stroke:var(--grid); stroke-width:1; }}
.zero, .zero-v {{ stroke:var(--axis); stroke-width:1; }}
.tick, .uf {{ font-family:var(--mono); font-size:11px; fill:var(--ink-3); }}
.uf {{ font-size:10px; }}
.axtitle {{ font-family:var(--mono); font-size:11px; fill:var(--ink-3);
  letter-spacing:.06em; text-transform:uppercase; }}
.panlab {{ font-family:var(--mono); font-size:11px; fill:var(--ink-2); letter-spacing:.07em; }}
.qnote {{ font-family:var(--mono); font-size:10px; fill:var(--ink-3); letter-spacing:.05em; }}
.trend {{ stroke:var(--ink-3); stroke-width:2; stroke-dasharray:7 5; }}
.trend-lab {{ font-family:var(--mono); font-size:11px; fill:var(--ink-3); }}
.dot {{ fill:var(--blue); fill-opacity:.72; stroke:var(--surface); stroke-width:2; }}
.dotlab {{ font-family:var(--mono); font-size:11px; font-weight:600; fill:var(--ink); }}
.ctx {{ fill:var(--ctx); }}
.down {{ fill:var(--blue); }}
.up {{ fill:var(--red); }}
.hit {{ fill:transparent; cursor:crosshair; outline:none; }}
.hit:focus-visible {{ stroke:var(--ink); stroke-width:2; }}

/* tooltip */
#tip {{ position:fixed; z-index:20; pointer-events:none; opacity:0; transform:translateY(3px);
  transition:opacity .1s ease, transform .1s ease; background:var(--ink); color:var(--surface);
  font-family:var(--mono); font-size:.75rem; line-height:1.45; padding:7px 10px; border-radius:4px;
  max-width:280px; }}
#tip.on {{ opacity:1; transform:translateY(0); }}
@media (prefers-reduced-motion:reduce) {{ #tip {{ transition:none; }} }}

/* caveats */
ul.notes {{ margin:0; padding:0; list-style:none; display:grid; gap:14px; }}
ul.notes li {{ padding-left:18px; position:relative; color:var(--ink-2); font-size:.9375rem; }}
ul.notes li::before {{ content:""; position:absolute; left:0; top:.62em; width:7px; height:1px;
  background:var(--ink-3); }}

/* table */
.tablewrap {{ overflow-x:auto; margin-top:22px; border:1px solid var(--rule);
  border-radius:4px; background:var(--surface); }}
table {{ border-collapse:collapse; width:100%; min-width:660px;
  font-variant-numeric:tabular-nums; font-size:.8125rem; }}
caption {{ text-align:left; padding:16px 18px 0; font-size:.8125rem; color:var(--ink-3);
  font-family:var(--mono); }}
th, td {{ text-align:right; padding:7px 12px; border-bottom:1px solid var(--rule); }}
thead th {{ font-family:var(--mono); font-size:.6875rem; letter-spacing:.07em; text-transform:uppercase;
  color:var(--ink-3); font-weight:400; vertical-align:bottom; position:sticky; top:0;
  background:var(--surface); }}
tbody th {{ text-align:left; font-family:var(--mono); font-weight:600; color:var(--ink); }}
td {{ color:var(--ink-2); }}
td.d {{ font-family:var(--mono); }}
td.d.down {{ color:var(--blue); }}
td.d.up {{ color:var(--red); }}
tbody tr:last-child th, tbody tr:last-child td {{ border-bottom:0; }}
</style>

<div class="wrap">

<header class="measure">
  <p class="eyebrow">Encarceramento × homicídio · 27 UFs · 2016–2022</p>
  <h1>Prender mais faz o homicídio cair?</h1>
  <p class="lead">Entre 2016 e 2022 o Brasil aumentou a população prisional em 18% e viu o
  homicídio cair 26%. É tentador ler as duas curvas como causa e efeito. Mas quando se
  olha estado por estado — onde as políticas de fato variam — <strong>a relação
  praticamente desaparece</strong>.</p>
  <p>Cada ponto abaixo é uma unidade da federação. O eixo horizontal mede quanto o estado
  passou a encarcerar; o vertical, o que aconteceu com sua taxa de homicídio no mesmo
  período. Se prender mais derrubasse o homicídio, os pontos desceriam da esquerda para a
  direita. Eles não descem.</p>
</header>

<div class="stats">
  <div class="stat">
    <p class="k">Correlação (bruta)</p>
    <div class="v">−0,18</div>
    <p class="n">Pearson entre variação do encarceramento e do homicídio, 27 UFs.</p>
  </div>
  <div class="stat">
    <p class="k">Ponderada por população</p>
    <div class="v">−0,01</div>
    <p class="n">Dando a cada estado o peso dos seus habitantes, a relação some.</p>
  </div>
  <div class="stat">
    <p class="k">Variância explicada</p>
    <div class="v">3,4%</div>
    <p class="n">R². Os outros 96,6% do que aconteceu com o homicídio estão fora deste gráfico.</p>
  </div>
</div>

<section>
  <div class="measure">
    <p class="eyebrow">O teste</p>
    <h2>Quem mais encarcerou não foi quem mais reduziu mortes</h2>
    <p>A nuvem é larga e a linha de tendência, quase plana. Os casos extremos contam a
    história melhor que a média: <strong>SP</strong> foi o único estado a reduzir a taxa de
    encarceramento e ainda assim derrubou o homicídio em 34%; <strong>PR</strong> mais que dobrou
    a sua e caiu 41% — pouco mais que <strong>RJ</strong>, que quase não mexeu no encarceramento
    e caiu 65%. No outro extremo, <strong>AM</strong> prendeu 24% mais e viu o homicídio
    <em>subir</em>.</p>
  </div>
  <figure>
    <figcaption>
      <span class="t">Variação do encarceramento × variação do homicídio, por UF</span>
      <span class="s">2016 → 2022 · área do círculo = população do estado em 2022</span>
    </figcaption>
    <div class="plot wide">{scatter_a()}</div>
    <div class="legend">
      <span><i style="background:var(--blue);opacity:.72"></i>uma UF · círculo maior = mais habitantes</span>
      <span>eixo vertical: variação da taxa de homicídio por 100 mil</span>
    </div>
  </figure>
</section>

<section>
  <div class="measure">
    <p class="eyebrow">A mesma coisa, sem a nuvem</p>
    <h2>Ordene os estados pelo quanto prenderam. O homicídio não segue a ordem.</h2>
    <p>Em cima, os 27 estados enfileirados do que menos ao que mais aumentou o encarceramento —
    uma rampa limpa, por construção. Embaixo, o que aconteceu com o homicídio de cada um,
    na mesma ordem. Se houvesse relação, a fileira de baixo também teria inclinação.
    Ela é ruído.</p>
  </div>
  <figure>
    <figcaption>
      <span class="t">Estados ordenados pelo aumento do encarceramento</span>
      <span class="s">barras cinza = variação do encarceramento (o critério de ordenação) · barras coloridas = variação do homicídio</span>
    </figcaption>
    <div class="plot wide">{strip()}</div>
    <div class="legend">
      <span><i style="background:var(--ctx)"></i>variação do encarceramento</span>
      <span><i style="background:var(--blue)"></i>homicídio caiu (25 UFs)</span>
      <span><i style="background:var(--red)"></i>homicídio subiu (AM, PI)</span>
    </div>
  </figure>
</section>

<section>
  <div class="measure">
    <p class="eyebrow">E o nível, não só a variação</p>
    <h2>Estados que prendem muito também não são os mais seguros</h2>
    <p>Talvez o que importe não seja o quanto um estado mudou, mas o quanto ele prende em
    termos absolutos. Também não: em 2022, a correlação entre taxa de encarceramento e taxa
    de homicídio é de apenas −0,23. <strong>RO</strong> e <strong>AC</strong> estão entre os
    que mais prendem no país e seguem com homicídio alto; <strong>BA</strong> prende pouco e
    também tem homicídio alto; <strong>SP</strong> prende muito e tem a menor taxa. A dispersão
    é grande em qualquer faixa.</p>
  </div>
  <figure>
    <figcaption>
      <span class="t">Taxa de encarceramento × taxa de homicídio, 2022</span>
      <span class="s">ambos por 100 mil habitantes · área do círculo = população</span>
    </figcaption>
    <div class="plot wide">{scatter_b()}</div>
    <div class="legend">
      <span>eixo vertical: homicídios por 100 mil habitantes em 2022</span>
    </div>
  </figure>
</section>

<section>
  <div class="measure">
    <p class="eyebrow">Ressalvas</p>
    <h2>O que este gráfico não prova</h2>
    <ul class="notes">
      <li><strong>Ausência de correlação não prova ausência de efeito.</strong> Prova que,
      no recorte estado-ano, o volume de encarceramento não organiza o que aconteceu com o
      homicídio. Um efeito real pode existir e estar encoberto por fatores mais fortes —
      dinâmica de facções, mutações no policiamento, demografia.</li>
      <li><strong>A relação fraca é também frágil.</strong> Ela cai de −0,18 para
      −0,01 quando se pondera pela população, e vira +0,01 (troca de sinal) removendo apenas
      dois pontos de alavancagem, PR e DF. Não é um sinal fraco e estável; é ruído.</li>
      <li><strong>É uma correlação ecológica.</strong> Vale para estados, não para
      pessoas: nada aqui diz o que acontece com um indivíduo preso ou solto.</li>
      <li><strong>Os pontos não têm o mesmo peso.</strong> A correlação bruta trata Roraima
      (637 mil habitantes) e São Paulo (44,4 milhões) como uma observação cada — por isso a
      versão ponderada está reportada ao lado dela, e não no lugar dela.</li>
      <li><strong>As fontes têm limites conhecidos.</strong> O SISDEPEN é autodeclarado pelos
      próprios estabelecimentos penais. O SIM registra o óbito, não a autoria; a contagem de
      homicídio usada aqui (CID-10 X85–Y09 mais Y35) inclui mortes por intervenção policial.</li>
      <li><strong>Os anos não foram escolhidos a dedo.</strong> 2016 é o primeiro ciclo do
      SISDEPEN com população prisional preenchível e 2022 é o último ano fechado do SIM no
      espelho local — são as pontas disponíveis, não um recorte conveniente.</li>
    </ul>
  </div>
</section>

<section>
  <div class="measure">
    <p class="eyebrow">Dados</p>
    <h2>Os 27 estados, valores completos</h2>
    <p>Taxas por 100 mil habitantes. Toda a base está aqui — os gráficos acima não mostram
    nada que esta tabela não mostre.</p>
  </div>
  <div class="tablewrap">
    <table>
      <caption>Encarceramento e homicídio por UF, 2016 e 2022</caption>
      <thead>
        <tr>
          <th scope="col">UF</th>
          <th scope="col">Presos<br>2016</th>
          <th scope="col">Presos<br>2022</th>
          <th scope="col">Var.</th>
          <th scope="col">Homic.<br>2016</th>
          <th scope="col">Homic.<br>2022</th>
          <th scope="col">Var.</th>
          <th scope="col">População<br>2022</th>
        </tr>
      </thead>
      <tbody>{table()}</tbody>
    </table>
  </div>
  <p class="src" style="margin-top:20px">
    Fontes · População prisional: SISDEPEN/SENAPPEN, ciclos 1 (2º sem. 2016) e 13
    (2º sem. 2022), campo 4.1 &ldquo;população prisional total&rdquo;, agregado por UF a partir do
    censo por estabelecimento.<br>
    Homicídios: MS/SVS Sistema de Informações sobre Mortalidade (SIM), causa básica
    CID-10 X85–Y09 e Y35, por UF de residência.<br>
    População: IBGE, estimativas por UF.<br>
    Apurado em 26/07/2026 sobre o espelho local do projeto rodado
    (<span style="white-space:nowrap">br_mjsp_sisdepen</span>,
    <span style="white-space:nowrap">br_ms_sim</span>,
    <span style="white-space:nowrap">br_ibge_populacao</span>).
  </p>
</section>

</div>

<div id="tip" role="status" aria-live="polite"></div>

<script>
(function () {{
  var tip = document.getElementById('tip');
  var cur = null;
  function show(el, x, y) {{
    tip.textContent = el.getAttribute('data-tip');
    tip.classList.add('on');
    var r = tip.getBoundingClientRect();
    var lx = Math.min(Math.max(8, x + 14), window.innerWidth - r.width - 8);
    var ly = y - r.height - 12;
    if (ly < 8) ly = y + 20;
    tip.style.left = lx + 'px';
    tip.style.top = ly + 'px';
  }}
  function hide() {{ tip.classList.remove('on'); cur = null; }}
  document.querySelectorAll('.hit').forEach(function (el) {{
    el.addEventListener('pointerenter', function (e) {{ cur = el; show(el, e.clientX, e.clientY); }});
    el.addEventListener('pointermove', function (e) {{ if (cur === el) show(el, e.clientX, e.clientY); }});
    el.addEventListener('pointerleave', hide);
    el.addEventListener('focus', function () {{
      var b = el.getBoundingClientRect();
      show(el, b.left + b.width / 2, b.top);
    }});
    el.addEventListener('blur', hide);
  }});
  window.addEventListener('scroll', hide, {{ passive: true }});
}})();
</script>
'''

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(HTML)
print(f"wrote {OUT} ({len(HTML)} bytes)")
print(f"scatter A dots: {len(ROWS)}, strip bars: {len(SORTED)*2}, table rows: {len(ROWS)}")
