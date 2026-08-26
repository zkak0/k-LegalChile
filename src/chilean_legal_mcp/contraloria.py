"""Crawler de dictámenes de la Contraloría General de la República (CGR).

Fuente: https://www.contraloria.cl/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/FormConsultaWeb2k
La base es Domino: la búsqueda real es POST a FormConsultaWeb2k?OpenForm&Seq=1 con HaPresionadoBotonBuscar=SI.
"""

from __future__ import annotations

import re
import html as html_lib
import urllib.parse

import httpx

BASE = "https://www.contraloria.cl/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf"


def buscar_cgr(query: str, limite: int = 10, timeout: float = 25.0) -> list[dict]:
    query = query.strip()
    if not query:
        return []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "es-CL,es;q=0.9",
        "Accept": "text/html",
        "Referer": "https://www.contraloria.cl/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/FormConsultaWeb2k?OpenForm",
        "Cookie": "JURIS=OK",
    }
    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=timeout) as c:
            # 1. GET para Seq dinámico y hidden fields
            r0 = c.get(f"{BASE}/FormConsultaWeb2k?OpenForm", headers=headers)
            seq_match = re.search(r"Seq=(\d+)", r0.text) if r0.status_code == 200 else None
            seq = seq_match.group(1) if seq_match else "1"
            hidden = {m.group(1): m.group(2) for m in re.finditer(r'<input[^>]+name="([^"]+)"[^>]+value="([^"]*)"', r0.text)} if r0.status_code == 200 else {}
            url = f"{BASE}/FormConsultaWeb2k?OpenForm&Seq={seq}&TextoLibre={urllib.parse.quote(query)}&NumeroDictamen=&Materia=Cualquiera&FechaDesde=&FechaHasta=&desde=1&dpp={limite}&porPagina={limite}&Orden=1&hpbb=SI"
            data = {**hidden, "__Click": "0", "HaPresionadoBotonBuscar": "SI", "TextoLibre": query, "NumeroDictamen": "", "Materia": "Cualquiera", "FechaDesde": "", "FechaHasta": "", "desde": "1", "dpp": str(limite), "porPagina": str(limite), "Orden": "1"}
            r = c.post(url, data=data, headers={**headers, "Content-Type": "application/x-www-form-urlencoded", "Origin": "https://www.contraloria.cl"}, follow_redirects=True)
            if r.status_code != 200 or "Dictamen" not in r.text:
                r = c.get(url, headers=headers, follow_redirects=True)
            r.raise_for_status()
    except Exception:
        try:
            url = f"{BASE}/FormConsultaWeb2k?OpenForm&Seq=1&TextoLibre={urllib.parse.quote(query)}&NumeroDictamen=&Materia=Cualquiera&FechaDesde=&FechaHasta=&desde=1&dpp={limite}&porPagina={limite}&Orden=1&hpbb=SI"
            r = httpx.get(url, timeout=timeout, headers=headers, follow_redirects=True)
            r.raise_for_status()
        except Exception:
            return []

    text = r.text
    resultados: list[dict] = []

    # Dictámenes aparecen como enlaces a documentos Domino: .../0/<UNID>?OpenDocument
    for href, inner in re.findall(r'<a[^>]+href="([^"]*OpenDocument[^"]*)"[^>]*>(.*?)</a>', text, re.I | re.S):
        num_raw = html_lib.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        # Validar que parezca número de dictamen (al menos 4 chars, contiene dígito, no es solo paginación)
        if len(num_raw) < 4 or not re.search(r"\d", num_raw):
            continue
        if re.fullmatch(r"\s*\d{1,2}\s*", num_raw):
            continue  # paginación 1..50
        # URL completa
        full_url = href if href.startswith("http") else f"https://www.contraloria.cl{href}"
        # Título: texto cercano en la misma fila (siguiente <td>)
        # Buscar la fila que contiene este href
        idx = text.find(href)
        row = text[max(0, idx-600): idx+800]
        # Extraer materia/descripción de la fila
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

    # Filtrar basura que haya pasado (paginación)
    resultados = [r for r in resultados if len(r["numero"]) >= 4 and not re.fullmatch(r"\d{1,2}", r["numero"].strip())]
    return resultados[:limite]
