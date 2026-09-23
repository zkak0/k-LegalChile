"""Fuentes externas adicionales: SciELO, DT, Diario Oficial — 100% públicas, sin registro."""

from __future__ import annotations

import re
import html as html_lib
import httpx


def buscar_scielo(query: str, limite: int = 5) -> list[dict]:
    # 1º: SciELO Chile directo (fuente académica oficial)
    # 2º (última instancia): Crossref API prefix 10.4067 — rotulado [vía DOI/Crossref]
    url = f"https://search.scielo.org/?q={query.replace(' ', '+')}&lang=es&where=ORG"
    try:
        r = httpx.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36", "Accept-Language": "es-CL,es;q=0.9", "Accept": "text/html"}, follow_redirects=True)
        if r.status_code == 200 and len(r.text) > 5000:
            text = r.text
            rows = []
            for m in re.finditer(r'<a[^>]+href="(https://[^"]*scielo[^"]*)"[^>]*>(.*?)</a>', text, re.I | re.S):
                href, inner = m.group(1), m.group(2)
                title = html_lib.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
                if len(title) < 15 or "SciELO" in title:
                    continue
                rows.append({"titulo": title[:180], "url": href})
                if len(rows) >= limite:
                    break
            if rows:
                return rows
    except Exception:
        pass
    # Última instancia: Crossref (acceso alternativo al mismo contenido abierto)
    try:
        r = httpx.get("https://api.crossref.org/works", params={"query": query, "filter": "prefix:10.4067", "rows": limite},
                      headers={"User-Agent": "chilean-legal-mcp/0.1 (mailto:contact@example.cl)"}, timeout=15)
        if r.status_code == 200:
            items = r.json().get("message", {}).get("items", [])
            rows = []
            for it in items[:limite]:
                title = (it.get("title") or [""])[0]
                if not title or len(title) < 10:
                    continue
                doi_url = it.get("URL") or ""
                # Preferir URL scielo.cl si se puede derivar del DOI
                rows.append({"titulo": f"{html_lib.unescape(title)[:160]} [vía DOI/Crossref]", "url": doi_url})
            if rows:
                return rows
    except Exception:
        pass
    return []


def buscar_dt(query: str, limite: int = 5) -> list[dict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "es-CL,es;q=0.9", "Accept": "text/html",
        "Referer": "https://www.dt.gob.cl/portal/1626/w3-search.html",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    # Verificado: POST con keywords a /portal/1626/w3-search.html
    for url in [
        "https://www.dt.gob.cl/portal/1626/w3-search.html",
        "https://www.dt.gob.cl/legislacion/1624/w3-channel.html",
    ]:
        try:
            r = httpx.post(url, data={"keywords": query}, timeout=15, headers=headers, follow_redirects=True)
            if r.status_code != 200 or len(r.text) < 1000:
                continue
            text = r.text
            rows: list[dict] = []
            for href, inner in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', text, re.I | re.S):
                title = html_lib.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
                if len(title) < 15:
                    continue
                if "portal" in href and "w3-propertyvalue" not in href and "w3-article" not in href:
                    if len(title) < 20:
                        continue
                full = href if href.startswith("http") else f"https://www.dt.gob.cl{href}"
                # Filtrar resultados relevantes
                if query.lower() not in title.lower() and query.lower() not in href.lower():
                    # Mostrar igual si es un resultado destacado
                    if "contrato" not in title.lower() and "dictamen" not in title.lower():
                        continue
                rows.append({"titulo": title[:180], "url": full})
                if len(rows) >= limite:
                    break
            if rows:
                return rows
        except Exception:
            continue
    return [{"titulo": f"Buscar '{query}' en DT (oficial)", "url": f"https://www.dt.gob.cl/portal/1626/w3-search.html"}]


def buscar_diario_oficial(query: str, limite: int = 5) -> list[dict]:
    """Diario Oficial — su buscador propio fue desactivado (el sitio devuelve 404).

    Como todas las normas del Diario Oficial son también publicadas en LeyChile,
    derivamos la búsqueda a la fuente oficial equivalente (BCN SPARQL) y lo
    rotulamos explícitamente.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html", "Accept-Language": "es-CL,es;q=0.9",
        "Referer": "https://www.diariooficial.interior.gob.cl/",
    }
    try:
        # 1. GET para _csrf y cookies (el flujo del buscador del sitio viejo puede revivir)
        with httpx.Client(headers=headers, follow_redirects=True, timeout=15) as c:
            r0 = c.get("https://www.diariooficial.interior.gob.cl/buscador/solicitud/buscador", headers=headers)
            m = re.search(r'name="_csrf" value="([^"]+)"', r0.text) if r0.status_code == 200 else None
            if m:
                csrf = m.group(1)
                r = c.post("https://www.diariooficial.interior.gob.cl/buscador/solicitud/buscar",
                           data={"_csrf": csrf, "texto": query, "tipoBusqueda": "1", "fechaDesde": "", "fechaHasta": ""},
                           headers={**headers, "Content-Type": "application/x-www-form-urlencoded", "Origin": "https://www.diariooficial.interior.gob.cl"})
                if r.status_code == 200 and len(r.text) > 500:
                    text = r.text
                    rows: list[dict] = []
                    for href, inner in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', text, re.I | re.S):
                        title = html_lib.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
                        if len(title) < 15:
                            continue
                        full = href if href.startswith("http") else f"https://www.diariooficial.interior.gob.cl{href}"
                        rows.append({"titulo": title[:180], "url": full})
                        if len(rows) >= limite:
                            break
                    if rows:
                        return rows
    except Exception:
        pass

    # 2. Derivación a BCN LeyChile (mismo contenido oficial que el DO)
    try:
        from .sparql_client import BCNClient, leychile_url
        c = BCNClient()
        rows = c.search_by_title(query, limit=limite)
        if rows:
            out = []
            for r in rows[:limite]:
                titulo = r.get("titulo") or ""
                numero = r.get("numero") or ""
                url_oficial = leychile_url(r.get("leychileId") or r.get("leychile_id")) or r.get("uri", "")
                out.append({"titulo": f"{titulo} — N° {numero}. Fuente: LeyChile (normas del Diario Oficial son las mismas que BCN)".strip(), "url": url_oficial})
            return out
    except Exception:
        pass

    return [{"titulo": f"Buscar '{query}' en el sitio oficial del Diario Oficial",
             "url": "https://www.diariooficial.interior.gob.cl/normativa/"}]


def buscar_suseso(query: str, limite: int = 5) -> list[dict]:
    # SUSESO dictámenes y circulares — 10k+ dictámenes 1926-2026, público sin registro
    urls = [
        f"https://www.suseso.cl/612/w3-propertyvalue-138569.html?texto={query.replace(' ', '+')}",
        f"https://www.suseso.cl/612/w3-propertyvalue-10372.html",
    ]
    for url in urls:
        try:
            r = httpx.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
            if r.status_code != 200:
                continue
            text = r.text
            rows: list[dict] = []
            for m in re.finditer(r'<a[^>]+href="([^"]*w3-article[^"]*)"[^>]*>(.*?)</a>', text, re.I | re.S):
                href, inner = m.group(1), m.group(2)
                title = html_lib.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
                if len(title) < 15:
                    continue
                full = href if href.startswith("http") else f"https://www.suseso.cl{href}"
                rows.append({"titulo": title[:180], "url": full})
                if len(rows) >= limite:
                    break
            if rows:
                return rows
        except Exception:
            continue
    return [{"titulo": f"Buscar '{query}' en SUSESO", "url": f"https://www.suseso.cl/612/w3-propertyvalue-138569.html"}]


def buscar_tc(query: str, limite: int = 5) -> list[dict]:
    """Tribunal Constitucional — API oficial del buscador (buscador-backend.tcchile.cl).

    Endpoint descubierto del bundle oficial del buscador SPA:
    GET /api/extended/sentencias?page=N&filter={"search":"<query>"}
    Devuelve sentencias con rol, competencia y fragmentos destacados.

    Formato respuesta:
      data = {"count":N,"all":[sentence_id,...],"results":[{id,content,sentence_id,rol,competencia,competenciaShortName,highlightParagraphs,...}]}
    """
    import json as _json
    _headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Origin": "https://buscador.tcchile.cl",
        "Referer": "https://buscador.tcchile.cl/",
    }
    resultados: list[dict] = []

    # ── Ruta primaria: API backend del TC ──────────────────────────────────────
    try:
        r = httpx.get(
            "https://buscador-backend.tcchile.cl/api/extended/sentencias",
            params={"page": 1, "filter": _json.dumps({"search": query})},
            headers=_headers,
            timeout=20,
        )
        if r.status_code == 200:
            payload = r.json() or {}
            data = payload.get("data") or {}
            items = data.get("results") or []
            for s in items[:limite]:
                # rol: prioriza campo rol (int o str) → sentence_id → id numérico
                rol_raw = s.get("rol")
                rol_id = s.get("sentence_id") or s.get("id")
                if rol_raw is not None:
                    rol = str(rol_raw)
                elif rol_id is not None:
                    rol = str(rol_id)
                else:
                    rol = "?"

                comp = (
                    str(s.get("competenciaShortName") or "").strip()
                    or str(s.get("competencia") or "").strip()
                )

                # Highlights: viene como JSON string "[]" o lista
                hl = s.get("highlightParagraphs") or ""
                frag = ""
                frags: list[str] = []
                hl_list: list = []
                if isinstance(hl, str) and hl.strip().startswith("["):
                    try:
                        hl_list = _json.loads(hl)
                    except _json.JSONDecodeError:
                        hl_list = []
                elif isinstance(hl, list):
                    hl_list = hl
                if hl_list:
                    primero = hl_list[0]
                    if isinstance(primero, dict):
                        frag = str(primero.get("full") or primero.get("text") or "")[:150]
                        for h in hl_list[:3]:
                            t_ = str(h.get("full") or h.get("text") or "").strip() if isinstance(h, dict) else str(h).strip()
                            if t_:
                                frags.append(t_[:400])

                titulo = f"Rol {rol}"
                if comp:
                    titulo += f" — {comp}"
                if frag:
                    titulo += f": {frag}"

                # URL ficha: usar sentence_id (identificador público del TC)
                sid = s.get("sentence_id") or rol_id or s.get("id", "")
                url_ficha = f"https://buscador.tcchile.cl/#/sentencia/{sid}" if sid else "https://buscador.tcchile.cl"

                resultados.append({
                    "titulo": titulo[:250],
                    "url": url_ficha,
                    "rol": rol,
                    "competencia": comp,
                    "content": (s.get("content") or "")[:20000],
                    "frags": frags,
                    "frag": frag,
                })
    except Exception:
        pass

    if resultados:
        return resultados

    # ── Ruta fallback: scraping TC (por si la API bloquea) ─────────────────────
    TC_RE = re.compile(
        r'href="(/busqueda/[^"]*|https?://(?:www\.)?tribunalconstitucional\.cl[^"]*)"[^>]*>'
        r'(.*?)(?=</a>)',
        re.I | re.S,
    )
    for url in [
        f"https://www.tribunalconstitucional.cl/busqueda/busqueda.php?texto={_json.dumps(query)}",
        f"https://buscador.tcchile.cl/#/?q={query.replace(' ', '+')}",
    ]:
        try:
            r2 = httpx.get(url, timeout=15, headers=_headers, follow_redirects=True)
            if r2.status_code == 200 and len(r2.text) > 800:
                for m in TC_RE.finditer(r2.text):
                    href = m.group(1)
                    raw_title = html_lib.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
                    if len(raw_title) < 10:
                        continue
                    full_url = href if href.startswith("http") else f"https://www.tribunalconstitucional.cl{href}"
                    resultados.append({"titulo": raw_title[:180], "url": full_url})
                    if len(resultados) >= limite:
                        break
                if resultados:
                    return resultados
        except Exception:
            continue

    return [{"titulo": f"Buscar TC: {query} — ver buscador oficial", "url": f"https://buscador.tcchile.cl/#/?q={query.replace(' ', '+')}"}]


def buscar_historia_ley(query: str, limite: int = 5) -> list[dict]:
    """Historia de la Ley BCN — formulario TYPO3 con token cHash.

    Flujo verificado 2026: GET busqueda-avanzada → extraer action+cHash y campos
    ocultos (__trustedProperties etc.) → POST con buscar=<query>.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
               "Accept-Language": "es-CL,es;q=0.9"}
    try:
        with httpx.Client(headers=headers, timeout=25, follow_redirects=True) as c:
            r0 = c.get("https://www.bcn.cl/historiadelaley/nc/busqueda-avanzada")
            if r0.status_code == 200:
                form_m = re.search(r'<form[^>]*action="([^"]*busqueda-avanzada[^"]*)"[^>]*>(.*?)</form>', r0.text, re.S)
                if form_m:
                    action = html_lib.unescape(form_m.group(1))
                    if action.startswith("/"):
                        action = f"https://www.bcn.cl{action}"
                    data = {}
                    for name, value in re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', form_m.group(2)):
                        data[html_lib.unescape(name)] = html_lib.unescape(value)
                    data["buscar"] = query
                    r = c.post(action, data=data,
                               headers={**headers, "Content-Type": "application/x-www-form-urlencoded"})
                    if r.status_code == 200 and len(r.text) > 5000:
                        rows: list[dict] = []
                        for m in re.finditer(r'<a[^>]+href="([^"]*(?:historiadelaley|historia-de-la-ley)[^"]*)"[^>]*>(.*?)</a>', r.text, re.I | re.S):
                            href, inner = m.group(1), m.group(2)
                            title = html_lib.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
                            title = re.sub(r"\s+", " ", title)
                            # Filtrar navegación genérica
                            if len(title) < 20 or title.lower() in ("inicio", "busqueda avanzada", "búsqueda avanzada", "ayuda"):
                                continue
                            full = href if href.startswith("http") else f"https://www.bcn.cl{href}"
                            if any(x["url"] == full for x in rows):
                                continue
                            rows.append({"titulo": title[:180], "url": full})
                            if len(rows) >= limite:
                                break
                        if rows:
                            return rows
    except Exception:
        pass
    url = f"https://www.bcn.cl/historiadelaley/nc/busqueda-avanzada?buscar={query.replace(' ', '+')}"
    return [{"titulo": f"Buscar '{query}' en Historia de la Ley", "url": url}]


def buscar_sii(query: str, limite: int = 5) -> list[dict]:
    # Solo fuentes oficiales SII (sin mirrors de terceros)
    for url in [
        f"https://www.sii.cl/normativa_legislacion/jurisprudencia_administrativa.htm",
        "https://www.sii.cl/pagina/jurisprudencia/adminis/indice.htm",
        "https://www.sii.cl/normativa_legislacion/index_normativa_legislacion.html",
    ]:
        try:
            r = httpx.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
            if r.status_code != 200:
                continue
            text = r.text
            rows: list[dict] = []
            for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', text, re.I | re.S):
                href, inner = m.group(1), m.group(2)
                title = html_lib.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
                if len(title) < 15:
                    continue
                if not any(k in href.lower() for k in ("oficio", "circular", "resolucion", "jurisprudencia", "normativa")):
                    continue
                full = href if href.startswith("http") else f"https://www.sii.cl{href}"
                rows.append({"titulo": title[:180], "url": full})
                if len(rows) >= limite:
                    break
            if rows:
                return rows
        except Exception:
            continue
    return [{"titulo": f"Buscar '{query}' en Normativa y Jurisprudencia SII (oficial)", "url": "https://www.sii.cl/normativa_legislacion/index_normativa_legislacion.html"}]


def buscar_cmf(query: str, limite: int = 5) -> list[dict]:
    """CMF — Consulta Global de Normativa (fuente oficial cmfchile.cl).

    Flujo verificado 2026: GET institucional/legislacion_normativa/normativa2.php
    con params buscar/enviado devuelve tabla de normas con PDFs oficiales.
    Respuesta grande (~1.6MB): usar timeout amplio.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "es-CL,es;q=0.9",
        "Referer": "https://www.cmfchile.cl/institucional/legislacion_normativa/normativa.php",
    }
    try:
        r = httpx.get(
            "https://www.cmfchile.cl/institucional/legislacion_normativa/normativa2.php",
            # Verificado: SOLO buscar+enviado funcionan; los demás campos vacíos
            # provocan respuesta de error (107 bytes)
            params={"buscar": query, "enviado": "1"},
            headers=headers,
            timeout=60,
        )
        if r.status_code == 200 and len(r.text) > 5000:
            text = r.text
            rows: list[dict] = []
            # Estructura verificada: <td>CIR</td><td><a href='../../normativa/X.pdf'>N</a></td>
            #                         <td>fecha</td><td>MATERIA</td>
            patron = re.compile(
                r"<td>([A-ZÁÉÑ]{2,4})</td>\s*"
                r"<td>\s*<a\s+href='([^']+\.pdf)'>\s*(\d{1,5})\s*</a>\s*</td>\s*"
                r"<td>\s*(\d{2}/\d{2}/\d{4})\s*</td>\s*"
                r"<td>(.*?)</td>",
                re.S,
            )
            for m in patron.finditer(text):
                tipo, href, numero, fecha, materia_html = m.groups()
                materia = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", materia_html)).strip()
                # Absolutizar: ../../normativa/x.pdf desde /institucional/legislacion_normativa/
                pdf_url = f"https://www.cmfchile.cl/normativa/{href.split('/')[-1]}"
                titulo = f"{tipo} N° {numero} del {fecha}"
                if materia:
                    titulo += f" — {materia[:120]}"
                rows.append({"titulo": titulo[:200], "url": pdf_url})
                if len(rows) >= limite:
                    break
            if rows:
                return rows
    except Exception:
        pass
    # Fallback: página oficial de Consulta Global
    return [{"titulo": f"Buscar '{query}' en CMF — Consulta Global de Normativa",
             "url": "https://www.cmfchile.cl/institucional/legislacion_normativa/normativa.php"}]


def buscar_tdlc(query: str, limite: int = 5) -> list[dict]:
    url = f"https://www.tdlc.cl/?s={query.replace(' ', '+')}"
    try:
        r = httpx.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
        if r.status_code == 200:
            text = r.text
            rows: list[dict] = []
            for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', text, re.I | re.S):
                href, inner = m.group(1), m.group(2)
                title = html_lib.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
                if len(title) < 15 or "tdlc" not in href.lower() and "sentencia" not in title.lower():
                    continue
                full = href if href.startswith("http") else f"https://www.tdlc.cl{href}"
                rows.append({"titulo": title[:180], "url": full})
                if len(rows) >= limite:
                    break
            if rows:
                return rows
    except Exception:
        pass
    return [{"titulo": f"Buscar '{query}' en TDLC", "url": f"https://www.tdlc.cl/buscador-jurisprudencia/?q={query.replace(' ', '+')}"}]


def buscar_cplt(query: str, limite: int = 5) -> list[dict]:
    """CPLT — jurisprudencia.cplt.cl (buscador oficial de decisiones).

    La búsqueda real es un POST WebForms a la raíz: campos
    ``ctl00$ContentPlaceHolder1$txtBusquedaSimple`` (texto) + ``btnBuscar``
    + tokens de página (``__VIEWSTATE``, ``__EVENTVALIDATION``). El host
    bloquea por IP (403 global desde ciertas redes), por lo que existe un
    relay opcional: si la variable ``CPLT_PROXY`` apunta a un proxy propio
    (p. ej. Cloudflare Worker gratuito, ver ``scripts/cplt_worker.js``),
    la sesión completa (GET + POST) se hace a través de él.

    Si nada funciona se informa honestamente que el portal no estuvo
    disponible desde esta red; nunca se falsifican resultados.
    """
    base = "https://jurisprudencia.cplt.cl/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-CL,es;q=0.9",
        "Origin": "https://jurisprudencia.cplt.cl",
        "Referer": base,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    import os
    relay = os.environ.get("CPLT_PROXY", "").strip().rstrip("/")

    def _urls_crudos(url: str) -> tuple[str, str]:
        """Devuelve (url_real, url_a_relay)."""
        url_relay = f"{relay}?url={url}" if relay else ""
        return url, url_relay

    def _extraer_html_por_camino(texto: str) -> list[dict]:
        """Parseo de la página de resultados del buscador CPLT."""
        rows: list[dict] = []
        for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', texto, re.I | re.S):
            href, inner = m.group(1), m.group(2)
            title = html_lib.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
            title = re.sub(r"\s+", " ", title)
            if len(title) < 15:
                continue
            if any(k in title.lower() for k in (
                "iniciar sesión", "login", "ayuda", "contacto", "inicio",
                "cplt", "transparencia", "english",
            )):
                continue
            full = href if href.startswith("http") else f"{base}{href.lstrip('/')}"
            if any(x["url"] == full for x in rows):
                continue
            rows.append({"titulo": title[:180], "url": full})
            if len(rows) >= limite:
                break
        return rows

    respuesta_vacia = [{
        "titulo": (f"CPLT jurisprudencia no disponible desde esta red "
                   f"(bloqueo 403 por IP del servidor del CPLT; no es falta "
                   f"de contenido). Buscado: '{query}'. "
                   f"Por VPN/propio relay: define CPLT_PROXY. "
                   f"Portal manual: {base}"),
        "url": base,
    }]

    try:
        with httpx.Client(headers=headers, timeout=25, follow_redirects=True) as sesion:

            def _buscar_con(cls_destino: str) -> list[dict] | None:
                """Hace la búsqueda WebForms: GET una vez para VIEWSTATE +
                EVENTVALIDATION, luego POST con el término. Devuelve filas."""
                r_get = sesion.get(cls_destino, timeout=25)
                if r_get.status_code != 200 or "ctl00_ContentPlaceHolder1_txtBusquedaSimple" not in r_get.text:
                    return None
                vs = re.search(r'name="__VIEWSTATE"[^>]*value="([^"]*)"', r_get.text)
                ev = re.search(r'name="__EVENTVALIDATION"[^>]*value="([^"]*)"', r_get.text)
                if not vs or not ev:
                    return None
                data = {
                    "__VIEWSTATEGENERATOR": "471515C9",
                    "__EVENTVALIDATION": ev.group(1),
                    "__VIEWSTATE": vs.group(1),
                    "ctl00$ContentPlaceHolder1$txtBusquedaSimple": query,
                    "ctl00$ContentPlaceHolder1$btnBuscar": "Buscar decisiones",
                    "ctl00$ContentPlaceHolder1$hdnTipoBusqueda": "1",
                }
                r = sesion.post(cls_destino, data=data, timeout=30)
                if r.status_code != 200 or len(r.text) < 3000:
                    return None
                return _extraer_html_por_camino(r.text)

            # Ruta A: directo (si la red actual no está bloqueada)
            filas = _buscar_con(base)
            if filas:
                return filas

            # Ruta B: relay configurado (proxy del propio operador)
            if relay:
                # El relay hace de túnel HTTP: POST igual, apuntando al URL
                # real como query param.
                sesion_relay = httpx.Client(headers=headers, timeout=30, follow_redirects=True)
                try:
                    r_get = sesion_relay.get(f"{relay}?url={base}", timeout=25)
                    if r_get.status_code == 200 and "txtBusquedaSimple" in r_get.text:
                        vs = re.search(r'name="__VIEWSTATE"[^>]*value="([^"]*)"', r_get.text)
                        ev = re.search(r'name="__EVENTVALIDATION"[^>]*value="([^"]*)"', r_get.text)
                        if vs and ev:
                            data = {
                                "__VIEWSTATEGENERATOR": "471515C9",
                                "__EVENTVALIDATION": ev.group(1),
                                "__VIEWSTATE": vs.group(1),
                                "ctl00$ContentPlaceHolder1$txtBusquedaSimple": query,
                                "ctl00$ContentPlaceHolder1$btnBuscar": "Buscar decisiones",
                            }
                            r_post = sesion_relay.post(f"{relay}?url={base}", data=data, timeout=30)
                            if r_post.status_code == 200:
                                filas = _extraer_html_por_camino(r_post.text)
                                if filas:
                                    return filas
                except Exception:
                    pass

    except Exception:
        pass

    return respuesta_vacia


def buscar_datos_gob(query: str, limite: int = 5) -> list[dict]:
    url = f"https://datos.gob.cl/api/3/action/package_search?q={query.replace(' ', '+')}&rows={limite}"
    try:
        r = httpx.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
        r.raise_for_status()
        data = r.json()
        results = data.get("result", {}).get("results", [])[:limite]
        rows = []
        for it in results:
            rows.append({"titulo": it.get("title", "")[:180], "url": f"https://datos.gob.cl/dataset/{it.get('name','')}"})
        if rows:
            return rows
    except Exception:
        pass
    return [{"titulo": f"Buscar '{query}' en datos.gob.cl", "url": f"https://datos.gob.cl/dataset?q={query.replace(' ', '+')}"}]


def buscar_fne(query: str, limite: int = 5) -> list[dict]:
    """Fiscalía Nacional Económica — jurisprudencia y actuaciones públicas.

    El sitio FNE (fne.gob.cl) sirve su biblioteca de jurisprudencia mediante
    carga dinámica (JS); el HTML estático de las secciones muestra solo la
    navegación. Se intentan las rutas públicas con contenido enlaceable
    (sentencias Corte Suprema y actuaciones ante tribunales); si no hay
    resultado enlaceable desde HTML estático, se informa honestamente y se
    enlaza el buscador oficial del sitio.
    """
    palabras = {w for w in query.lower().split() if len(w) >= 3}
    seeds = [
        "https://www.fne.gob.cl/biblioteca/jurisprudencia/sentencias-corte-suprema/",
        "https://www.fne.gob.cl/biblioteca/actuaciones-de-la-fne/actuaciones-ante-tribunales/",
        "https://www.fne.gob.cl/biblioteca/actuaciones-de-la-fne/investigaciones-de-la-fne/",
        "https://www.fne.gob.cl/ultimas-actuaciones/",
    ]
    for url in seeds:
        try:
            r = httpx.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
            if r.status_code != 200:
                continue
            rows: list[dict] = []
            for m in re.finditer(
                r'<a[^>]+href="(https://www\.fne\.gob\.cl/(?:wp-content/uploads/[^"]*\.pdf|biblioteca/[^"]+))"[^>]*>([^<]{5,220})</a>',
                r.text, re.I | re.S):
                href, inner = m.group(1), m.group(2)
                title = html_lib.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
                title = re.sub(r"\s+", " ", title)
                if len(title) < 8:
                    continue
                if title.lower() in {"biblioteca", "biblioteca digital", "marco normativo",
                                     "actuaciones de la fne", "actuaciones ante tribunales",
                                     "investigaciones de la fne", "inicio", "english", "más",
                                     "ver sentencia", "sentencias corte suprema"}:
                    continue
                if not palabras or any(p in title.lower() for p in palabras):
                    if any(x["url"] == href for x in rows):
                        continue
                    rows.append({"titulo": title[:180], "url": href})
                    if len(rows) >= limite:
                        return rows
            if rows:
                return rows
        except Exception:
            continue
    url_oficial = "https://www.fne.gob.cl/biblioteca/jurisprudencia/"
    return [{"titulo": (f"FNE: '{query}' — la biblioteca de jurisprudencia de la FNE se "
                        "carga dinámicamente (JS); no hay resultado enlaceable en HTML "
                        f"estático desde esta consulta. Portal oficial: {url_oficial}"),
             "url": url_oficial}]


def buscar_tribunal_ambiental(query: str, limite: int = 5) -> list[dict]:
    """Tribunales Ambientales (1º/2º/3º) — sentencias oficiales en PDF.

    Estructura verificada: la página https://tribunalambiental.cl/sentencias-e-informes/sentencias/
    lista las sentencias de los tres TA como PDF en wp-content/uploads con
    nombre del tipo 'YYYY.MM.DD-Sentencia-R-NNN-YYYY.pdf' y enlace de expediente
    a causas.tribunalambiental.cl/causas/<id>/ver. Casos en página única (p. ej.
    Recurso de Protección de la Ley de Pesca) se entregan con su título.

    El listado HTML solo indexa el rol de cada causa (el contenido está dentro
    del PDF), por lo que una consulta por materia devuelve las sentencias más
    recientes con la advertencia de consultar el texto en el PDF oficial.
    """
    palabras = {w for w in query.lower().split() if len(w) >= 3}
    rol_query = None
    rm = re.search(r"R\s*[-: ]\s*(\d{2,4})\s*[-/: ]\s*(\d{4})", query, re.I)
    if rm:
        rol_query = f"R-{rm.group(1)}-{rm.group(2)}"
    seed = "https://tribunalambiental.cl/sentencias-e-informes/sentencias/"
    try:
        r = httpx.get(seed, timeout=25, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
        if r.status_code != 200:
            raise RuntimeError(f"status {r.status_code}")
        rows: list[dict] = []
        coincidencias = 0
        for m in re.finditer(r'<a[^>]+href="(https://tribunalambiental\.cl/wp-content/uploads/[^"]+\.pdf)"[^>]*>', r.text, re.I):
            href = html_lib.unescape(m.group(1))
            filename = href.rsplit("/", 1)[-1]
            rol_m = re.search(r"[Rr]\s*[-:]\s*(\d{2,4}-\d{4})", filename)
            titulo = "Sentencia TA"
            rol = None
            if rol_m:
                rol = f"R-{rol_m.group(1)}"
                titulo = f"Sentencia Rol {rol}"
            else:
                titulo = filename.replace(".pdf", "").replace("-", " ")[:140] or "Sentencia TA"
            if rol_query:
                # Filtro por rol: comparar R-NNN-YYYY
                if rol and rol_query.lower() in f"{rol} {filename}".lower():
                    coincidencias += 1
                else:
                    continue
            else:
                # Sin rol: solo filtrar si el término calza con el rol/filename
                if palabras and not any(p in f"{rol or ''} {filename}".lower() for p in palabras):
                    continue
            if any(x["url"] == href for x in rows):
                continue
            rows.append({"tipo": "pdf", "titulo": titulo[:180], "url": href})
            if len(rows) >= limite:
                break
        if rows:
            return rows
        if rol_query and coincidencias == 0:
            return [{"titulo": f"No se encontró la sentencia {rol_query} en el directorio de TA (puede estar en otra sala o no publicada). Directorio oficial: {seed}", "url": seed}]
    except Exception:
        pass
    url_oficial = "https://tribunalambiental.cl/sentencias-e-informes/sentencias/"
    return [{"titulo": f"Buscar '{query}' en Tribunales Ambientales (oficial)", "url": url_oficial}]
