"""
Saída por IP brasileiro para as fontes gov.br que filtram por país.

O laptop e o beelink saem por IP suíço. ANEEL, INCRA, CadÚnico (VIS DATA),
ANTT e `arquivos.receitafederal.gov.br` dão timeout (ou o "Request Rejected"
do F5) a partir daí e abrem por proxy BR. O pool vem de
`proxifly/free-proxy-list` (filtro BR), que dura dias: por isso nada aqui é
fixo, cada rodada busca a lista e testa contra o alvo.

Uso:
    from _proxy_br import Pool
    pool = Pool("https://dadosabertos.aneel.gov.br/api/3/action/package_list")
    r = pool.get(url)            # tenta proxy a proxy até um responder
    pool.download(url, destino)  # streaming, com retomada por Range

Um worker por proxy: pool gratuito satura com concorrência.
"""

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings()

LISTA = "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/countries/BR/data.txt"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


def _proxies(p):
    # socks4:// e socks5:// resolvem DNS local; o `h` delega ao proxy
    p = p.replace("socks5://", "socks5h://")
    return {"http": p, "https": p}


class Pool:
    def __init__(self, alvo: str, timeout=20, workers=40):
        def testa(p):
            try:
                # stream: o alvo pode ser um zip de 50 MB; basta o começo
                with requests.get(alvo, proxies=_proxies(p), timeout=timeout, stream=True,
                                  headers={"User-Agent": UA}, verify=False) as r:
                    inicio = next(r.iter_content(2000), b"")
                    if r.status_code < 400 and b"Request Rejected" not in inicio:
                        return p
            except Exception:
                pass
            return None

        self._testa, self._workers, self._alvo = testa, workers, alvo
        self._lock = threading.Lock()
        self._renova()

    def _renova(self):
        """(Re)testa a lista inteira. Pool gratuito morre em horas: um processo
        longo que só usasse a lista do início passava 20 min tentando mortos."""
        cands = requests.get(LISTA, timeout=30).text.split()
        with ThreadPoolExecutor(self._workers) as ex:
            vivos = [p for p in ex.map(self._testa, cands) if p]
        if not vivos:
            raise RuntimeError(f"nenhum proxy BR abre {self._alvo} ({len(cands)} testados)")
        self.vivos = vivos
        print(f"  proxy BR: {len(vivos)}/{len(cands)} abrem {self._alvo}", flush=True)

    def descarta(self, p, minimo=8):
        """Tira um proxy que falhou; abaixo de `minimo`, renova a lista."""
        with self._lock:
            if p in self.vivos:
                self.vivos.remove(p)
            if len(self.vivos) < minimo:
                self._renova()

    def get(self, url, tentativas=None, timeout=60, **kw):
        ordem = self.vivos[:]
        random.shuffle(ordem)
        erro = None
        for p in ordem[: tentativas or len(ordem)]:
            try:
                r = requests.get(url, proxies=_proxies(p), timeout=timeout, verify=False,
                                 headers={"User-Agent": UA, **kw.get("headers", {})},
                                 **{k: v for k, v in kw.items() if k != "headers"})
                # com stream=True, r.content leria o corpo inteiro (um zip de 355 MB);
                # o F5 da ANTT devolve HTML pequeno, então só confere sem stream
                rejeitado = not kw.get("stream") and b"Request Rejected" in r.content[:2000]
                if r.status_code >= 500 or rejeitado:
                    erro = f"{r.status_code} via {p}"
                    self.descarta(p)
                    continue
                return r
            except Exception as e:
                erro = f"{type(e).__name__} via {p}"
                self.descarta(p)
        raise RuntimeError(f"{url}: nenhum proxy respondeu ({erro})")

    def download(self, url, destino: Path, rodadas=6):
        """Baixa por curl, trocando de proxy e retomando (`-C -`) quando um cai.

        Não usa requests: proxy gratuito lento pinga bytes devagar, e o timeout
        de leitura do requests nunca dispara. `--speed-limit` corta o proxy que
        passar 30 s abaixo de 20 kB/s.
        """
        import subprocess

        destino = Path(destino)
        parcial = destino.with_suffix(destino.suffix + ".part")
        tamanho = None
        for rodada in range(rodadas):
            for p in random.sample(self.vivos, len(self.vivos)):
                antes = parcial.stat().st_size if parcial.exists() else 0
                if tamanho is None:
                    h = subprocess.run(
                        ["curl", "-skI", "-m", "30", "-x", p, "-A", UA, "-L", url],
                        capture_output=True, text=True)
                    m = [l for l in h.stdout.lower().splitlines() if l.startswith("content-length:")]
                    if m:
                        tamanho = int(m[-1].split(":")[1])
                r = subprocess.run(
                    ["curl", "-sk", "-L", "-f", "-x", p, "-A", UA, "-C", "-",
                     "--connect-timeout", "20", "--speed-limit", "20000", "--speed-time", "30",
                     "-o", str(parcial), url],
                    capture_output=True)
                ja = parcial.stat().st_size if parcial.exists() else 0
                if r.returncode == 0 and ja and (tamanho is None or ja >= tamanho):
                    parcial.rename(destino)
                    return destino
                if r.returncode == 33:  # servidor sem Range: recomeça
                    parcial.unlink(missing_ok=True)
                elif ja <= antes:  # não avançou nada: proxy morto
                    self.descarta(p)
            time.sleep(5 * (rodada + 1))
        raise RuntimeError(f"{url}: download não completou em {rodadas} rodadas")

    def download_paralelo(self, url, destino: Path, tamanho: int, bloco=8 << 20, workers=6):
        """Baixa em blocos de `bloco` bytes por Range, `workers` proxies ao mesmo
        tempo. Um proxy gratuito rende ~50 kB/s: o Sigef_Brasil_SP.zip (355 MB)
        levaria 2 h num só; em paralelo o limite passa a ser o número de vivos.
        Cada bloco vira um arquivo `.pNNNN` e só é aceito com o tamanho exato,
        então rodar de novo retoma de onde parou."""
        import subprocess

        destino = Path(destino)
        pasta = destino.with_suffix(destino.suffix + ".blocos")
        pasta.mkdir(parents=True, exist_ok=True)
        faixas = [(i, a, min(a + bloco, tamanho) - 1)
                  for i, a in enumerate(range(0, tamanho, bloco))]

        def um(faixa):
            i, a, b = faixa
            f = pasta / f"p{i:05d}"
            if f.exists() and f.stat().st_size == b - a + 1:
                return
            for _ in range(len(self.vivos) * 3):
                p = random.choice(self.vivos)
                subprocess.run(
                    ["curl", "-sk", "-L", "-f", "-x", p, "-A", UA, "-r", f"{a}-{b}",
                     "--connect-timeout", "20", "--speed-limit", "20000", "--speed-time", "30",
                     "-m", "900", "-o", str(f), url],
                    capture_output=True)
                if f.exists() and f.stat().st_size == b - a + 1:
                    return
                f.unlink(missing_ok=True)
                self.descarta(p)
            raise RuntimeError(f"{url}: bloco {i} não baixou")

        with ThreadPoolExecutor(workers) as ex:
            list(ex.map(um, faixas))
        with open(destino, "wb") as out:
            for i, _, _ in faixas:
                out.write((pasta / f"p{i:05d}").read_bytes())
        if destino.stat().st_size != tamanho:
            raise RuntimeError(f"{url}: montado com {destino.stat().st_size} ≠ {tamanho}")
        for f in pasta.iterdir():
            f.unlink()
        pasta.rmdir()
        return destino
