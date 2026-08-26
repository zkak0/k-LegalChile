"""Superir — Boletín Concursal (Ley 20.720). SOLO fuente oficial boletinconcursal.cl."""

from __future__ import annotations

import re
import html as html_lib
import httpx

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"}


def buscar_boletin(query: str, limite: int = 5) -> list[dict]:
    # Fuente oficial única: Boletín Concursal (Superir). Sin APIs de terceros.
    for url in [
        f"https://www.boletinconcursal.cl/boletin/verificacion?texto={query.replace(' ', '+')}",
        "https://www.boletinconcursal.cl/boletin/",
        "https://www.superir.gob.cl/boletin-concursal",
    ]:
        try:
            r = httpx.get(url, timeout=15, headers=HEADERS, follow_redirects=True)
            if r.status_code != 200 or len(r.text) < 800:
                continue
            text = r.text
            rows: list[dict] = []
            for href, title in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{10,100})</a>', text):
                t = html_lib.unescape(title.strip())
                low = t.lower()
                if not any(k in low for k in ("liquidaci", "renegociaci", "concurso", "procedimiento", "deudor")):
                    continue
                full = href if href.startswith("http") else f"https://www.boletinconcursal.cl{href}"
                rows.append({"numero": href.split("/")[-1][:20], "titulo": t[:120], "url": full})
                if len(rows) >= limite:
                    break
            if rows:
                return rows
        except Exception:
            continue
    return [{
        "numero": query,
        "titulo": f"Verificar '{query}' en Boletín Concursal oficial (búsqueda por RUT)",
        "url": "https://www.boletinconcursal.cl/boletin/verificacion",
    }]
