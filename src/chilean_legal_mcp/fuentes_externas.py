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
    """CPLT — jurisprudencia.cplt.cl. Imperva WAF: httpx primero, Playwright como
    respaldo (módulo anti_waf) si hay bloqueo.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-CL,es;q=0.9",
        "Referer": "https://www.consejotransparencia.cl/",
        "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "same-origin",
        "Upgrade-Insecure-Requests": "1",
    }
    url_buscar = f"https://jurisprudencia.cplt.cl/buscar?texto={query.replace(' ', '+')}"

    def _parsear(text: str) -> list[dict]:
        rows: list[dict] = []
        for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', text, re.I | re.S):
            href, inner = m.group(1), m.group(2)
            title = html_lib.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
            title = re.sub(r"\s+", " ", title)
            if len(title) < 20:
                continue
            # Filtrar navegación genérica
            if any(k in title.lower() for k in ("iniciar sesión", "login", "ayuda", "contacto", "inicio")):
                continue
            full = href if href.startswith("http") else f"https://jurisprudencia.cplt.cl{href}"
            if any(x["url"] == full for x in rows):
                continue
            rows.append({"titulo": title[:180], "url": full})
            if len(rows) >= limite:
                break
        return rows

    # 1. Intento directo con headers completos + cookies persistidas
    from .anti_waf import _cargar_cookies, _detectar_bloqueo, _extraer_cookies_playwright, _guardar_cookies
    cookies = _cargar_cookies("jurisprudencia.cplt.cl")
    try:
        r = httpx.get(url_buscar, timeout=20, headers=headers, follow_redirects=True, cookies=cookies)
        if r.status_code == 200 and not _detectar_bloqueo(r):
            nuevas = {c.name: c.value for c in r.cookies}
            if nuevas:
                _guardar_cookies("jurisprudencia.cplt.cl", nuevas)
            filas = _parsear(r.text)
            if filas:
                return filas
    except Exception:
        pass

    # 2. Fallback Playwright (resuelve challenge Imperva y guarda cookies)
    try:
        cookies_pw = _extraer_cookies_playwright(url_buscar, "jurisprudencia.cplt.cl", esperar=6)
        if cookies_pw:
            _guardar_cookies("jurisprudencia.cplt.cl", cookies_pw)
            r2 = httpx.get(url_buscar, timeout=20, headers=headers, follow_redirects=True,
                           cookies={**cookies_pw})
            if r2.status_code == 200 and not _detectar_bloqueo(r2):
                filas = _parsear(r2.text)
                if filas:
                    return filas
    except Exception:
        pass

    return [{"titulo": f"Buscar '{query}' en CPLT — Jurisprudencia administrativa",
             "url": url_buscar}]


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
