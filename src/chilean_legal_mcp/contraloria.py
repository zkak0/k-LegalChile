"""Crawler de dictámenes de la Contraloría General de la República (CGR).

Fuente: https://www.contraloria.cl/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/FormConsultaWeb2k
La base es Domino: la búsqueda real es POST a FormConsultaWeb2k?OpenForm&Seq=1 con HaPresionadoBotonBuscar=SI.

Estrategia:
1. CGRFetcher con fallback cascada (curl_cffi → wafer → Camoufox)
2. Si todo falla, fallback a fuentes alternativas (BCN, etc.)
"""

from __future__ import annotations

import re
import html as html_lib
import urllib.parse

import httpx

from .anti_waf import fetch_cgr_sync

BASE = "https://www.contraloria.cl/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf"


def _build_search_url(query: str, limite: int) -> str:
    """Construye URL de búsqueda directa (GET simple)."""
    q = urllib.parse.quote(query)
    return (
        f"https://www.contraloria.cl/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/"
        f"FormConsultaWeb2k?OpenForm&Seq=1&TextoLibre={q}&NumeroDictamen=&"
        f"Materia=Cualquiera&FechaDesde=&FechaHasta=&desde=1&dpp={limite}"
        f"&porPagina={limite}&Orden=1&hpbb=SI"
    )


def _parse_results(text: str, limite: int) -> list[dict]:
    """Extrae resultados del HTML de resultados CGR."""
    resultados: list[dict] = []

    # Dictámenes aparecen como enlaces a documentos Domino: .../0/<UNID>?OpenDocument
    for href, inner in re.findall(r'<a[^>]+href="([^"]*OpenDocument[^"]*)"[^>]*>(.*?)</a>', text, re.I | re.S):
        num_raw = html_lib.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        # Validar que parezca número de dictamen
        if len(num_raw) < 4 or not re.search(r"\d", num_raw):
            continue
        if re.fullmatch(r"\s*\d{1,2}\s*", num_raw):
            continue  # paginación 1..50
        
        full_url = href if href.startswith("http") else f"https://www.contraloria.cl{href}"
        
        # Título: texto cercano en la misma fila
        idx = text.find(href)
        row = text[max(0, idx-600): idx+800]
        tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)
        titulo = ""
        for td in tds:
            clean = html_lib.unescape(re.sub(r"<[^>]+>", " ", td)).strip()
            clean = re.sub(r"\s+", " ", clean)
            if len(clean) > 15 and clean != num_raw and "Dictamen" not in clean and "Buscar" not in clean:
                titulo = clean[:200]
                break
        if not titulo:
            titulo = f"Dictamen {num_raw}"
        resultados.append({"numero": re.sub(r"\s+", " ", num_raw), "titulo": titulo, "url": full_url})
        if len(resultados) >= limite:
            break

    # Filtrar basura (paginación)
    resultados = [r for r in resultados if len(r["numero"]) >= 4 and not re.fullmatch(r"\d{1,2}", r["numero"].strip())]
    return resultados[:limite]


def buscar_cgr(query: str, limite: int = 10, timeout: float = 25.0) -> list[dict]:
    """Busca dictámenes CGR con fallback cascada anti-WAF.
    
    1. Intenta fetch_cgr_sync (cascada: curl_cffi → wafer → Camoufox)
    2. Si falla, intenta URL GET simple (más rápido, sin anti-WAF)
    3. Si falla, fallback a fuentes alternativas (BCN) via buscar_dictamenes
    """
    query = query.strip()
    if not query:
        return []
    
    url = _build_search_url(query, limite)
    
    # Intento 1: CGRFetcher con cascada anti-WAF (~10-15s, incluye cascada)
    try:
        html_content = fetch_cgr_sync(url, verbose=False)
        resultados = _parse_results(html_content, limite)
        if resultados:
            return resultados
    except Exception:
        pass
    
    # Intento 2: GET simple con httpx (más rápido, headers CGR conocidos)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "es-CL,es;q=0.9",
            "Accept": "text/html",
            "Referer": "https://www.contraloria.cl/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/FormConsultaWeb2k?OpenForm",
            "Cookie": "JURIS=OK",
        }
        with httpx.Client(headers=headers, follow_redirects=True, timeout=timeout) as c:
            r = c.get(url, headers=headers)
            r.raise_for_status()
            resultados = _parse_results(r.text, limite)
            if resultados:
                return resultados
    except Exception:
        pass
    
    # Fallback final: buscar_dictamenes (usa BCN + fuentes alternativas)
    try:
        from .server import buscar_dictamenes
        return buscar_dictamenes(query, limite=limite)
    except Exception:
        return []
