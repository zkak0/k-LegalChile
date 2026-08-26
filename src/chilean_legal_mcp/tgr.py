"""TGR separado por tipo — dictámenes, resoluciones, circulares, fallos (apelaciones/reposiciones con resultado). Todo ordenado."""

from __future__ import annotations

import re
import html as html_lib
import httpx


def _get(url: str) -> str | None:
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36", "Accept-Language": "es-CL,es;q=0.9"}
    try:
        r = httpx.get(url, timeout=15, headers=headers, follow_redirects=True)
        if r.status_code == 200 and len(r.text) > 800:
            return r.text
    except Exception:
        pass
    return None


def buscar_dictamen(query: str, limite: int = 5) -> list[dict]:
    # TGR dictámenes: buscador WordPress + normativa JSP
    for url in [
        f"https://tgr.gob.cl/?s={query.replace(' ', '+')}",
        "https://www.tesoreria.cl/MenuImpuestoVerde/jsp/normativa.jsp",
    ]:
        text = _get(url)
        if not text:
            continue
        rows = []
        for href, title in re.findall(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>([^<]+)</a>', text):
            t = html_lib.unescape(title.strip())
            if len(t) < 10:
                continue
            full = href if href.startswith("http") else f"https://www.tesoreria.cl{href}" if "tesoreria" in url else f"https://tgr.gob.cl{href}"
            # Filtrar por query si es específico
            if query.lower() not in t.lower() and "tgr" not in query.lower():
                # mostrar igual si es normativa general y query genérica
                pass
            rows.append({"numero": href.split("/")[-1][:20], "titulo": t[:120], "url": full, "resultado": ""})
            if len(rows) >= limite:
                return rows
        # Parsear posts de WordPress (estructura 2026: <h3><a href="...">Título</a></h3>)
        for href, title in re.findall(r'<h3[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', text, re.S):
            t = html_lib.unescape(re.sub(r"<[^>]+>", "", title)).strip()
            t = re.sub(r"\s+", " ", t)
            if len(t) < 10:
                continue
            rows.append({"numero": href.split("/")[-1][:20] or href.rstrip("/").split("/")[-2][:20], "titulo": t[:120], "url": href, "resultado": ""})
            if len(rows) >= limite:
                return rows
        # Estructura anterior (elementor) como fallback
        for href, title in re.findall(r'<h3 class="elementor-post__title">\s*<a href="([^"]+)">\s*([^<]+)', text):
            t = html_lib.unescape(re.sub(r"\s+", " ", title.strip()))
            if len(t) < 10:
                continue
            rows.append({"numero": href.split("/")[-1][:20], "titulo": t[:120], "url": href, "resultado": ""})
            if len(rows) >= limite:
                return rows
        if rows:
            return rows
    return [{"numero": query, "titulo": f"Buscar dictamen '{query}' en TGR", "url": f"https://tgr.gob.cl/?s={query.replace(' ', '+')}", "resultado": ""}]


def buscar_resolucion(query: str, limite: int = 5) -> list[dict]:
    text = _get("https://www.tesoreria.cl/MenuImpuestoVerde/jsp/normativa.jsp")
    if text:
        rows = []
        for href, title in re.findall(r'<a[^>]+href="([^"]*Resolucion[^"]+\.pdf)"[^>]*>([^<]+)</a>', text, re.I):
            t = html_lib.unescape(title.strip())
            rows.append({"numero": href.split("/")[-1][:20], "titulo": t[:120], "url": f"https://www.tesoreria.cl{href}" if href.startswith("/") else href, "resultado": ""})
            if len(rows) >= limite:
                return rows
        if rows:
            return rows
    return buscar_dictamen(query, limite)


def buscar_circular(query: str, limite: int = 5) -> list[dict]:
    # TGR circulares: mismo endpoint, filtrar por Circular
    text = _get("https://www.tesoreria.cl/MenuImpuestoVerde/jsp/normativa.jsp")
    if text:
        rows = []
        for href, title in re.findall(r'<a[^>]+href="([^"]*Circular[^"]+\.pdf)"[^>]*>([^<]+)</a>', text, re.I):
            t = html_lib.unescape(title.strip())
            rows.append({"numero": href.split("/")[-1][:20], "titulo": t[:120], "url": f"https://www.tesoreria.cl{href}" if href.startswith("/") else href, "resultado": ""})
            if len(rows) >= limite:
                return rows
        if rows:
            return rows
    return buscar_dictamen(query, limite)


def buscar_fallo(query: str, limite: int = 5) -> list[dict]:
    # Fallos cobranza / apelaciones / reposiciones TGR — buscador WordPress tgr.gob.cl
    text = _get(f"https://tgr.gob.cl/?s={query.replace(' ', '+')}+fallo")
    rows: list[dict] = []
    if text:
        # Estructura 2026: <h3><a href="...">Título</a></h3>
        for href, title in re.findall(r'<h3[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', text, re.S):
            t = html_lib.unescape(re.sub(r"<[^>]+>", "", title)).strip()
            t = re.sub(r"\s+", " ", t)
            if len(t) < 10:
                continue
            # Intentar extraer resultado (acogido/rechazado) del título y contexto cercano
            idx = text.find(href)
            snippet = text[max(0, idx-300): idx+900]
            m = re.search(r"(acogid[ao]|rechazad[ao]|apelaci[oó]n|reposici[oó]n|ratifica|confirma|revoca|acoge)", snippet, re.I)
            resultado = m.group(1).lower() if m else ""
            num_slug = href.rstrip("/").split("/")[-1][:40] or href.rstrip("/").split("/")[-2][:20]
            rows.append({"numero": num_slug, "titulo": t[:140], "url": href, "resultado": resultado})
            if len(rows) >= limite:
                break
        # Estructura anterior (elementor) como fallback
        if not rows:
            for href, title in re.findall(r'<h3 class="elementor-post__title">\s*<a href="([^"]+)">\s*([^<]+)', text):
                excerpt_idx = text.find(href)
                snippet = text[max(0, excerpt_idx-500): excerpt_idx+800]
                m = re.search(r"(acogid[ao]|rechazad[ao]|apelaci[oó]n|reposici[oó]n)", snippet, re.I)
                resultado = m.group(1) if m else ""
                t = html_lib.unescape(re.sub(r"\s+", " ", title.strip()))
                rows.append({"numero": href.split("/")[-1][:20], "titulo": t[:120], "url": href, "resultado": resultado})
                if len(rows) >= limite:
                    break
    if rows:
        return rows
    # Fallback genérico
    return buscar_dictamen(query, limite)
