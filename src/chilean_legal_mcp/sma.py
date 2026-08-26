"""SMA — SNIFA (fiscalización y sanciones ambientales)."""

from __future__ import annotations

import re
import html as html_lib
import httpx


def buscar_sancionatorio(query: str, limite: int = 5) -> list[dict]:
    for url in [
        f"https://snifa.sma.gob.cl/Sancionatorio?texto={query.replace(' ', '+')}",
        f"https://snifa.sma.gob.cl/RegistroPublico?texto={query.replace(' ', '+')}",
    ]:
        try:
            r = httpx.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html", "X-Requested-With": "XMLHttpRequest"}, follow_redirects=True)
            if r.status_code != 200:
                continue
            text = r.text
            rows = []
            for href, title in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{10,100})</a>', text):
                t = html_lib.unescape(title.strip())
                if len(t) < 10:
                    continue
                full = href if href.startswith("http") else f"https://snifa.sma.gob.cl{href}"
                rows.append({"numero": href.split("/")[-1][:20], "titulo": t[:120], "url": full})
                if len(rows) >= limite:
                    break
            if rows:
                return rows
        except Exception:
            continue
    return [{"numero": query, "titulo": f"Buscar '{query}' en SNIFA SMA", "url": f"https://snifa.sma.gob.cl/Sancionatorio?texto={query.replace(' ', '+')}"}]
