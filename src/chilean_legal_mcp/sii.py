"""SII separado por tipo — oficios, circulares, resoluciones, fallos TTA.

REGLA DE FUENTES: solo fuentes OFICIALES del SII.
- Oficios (Jurisprudencia Administrativa): API oficial www3.sii.cl/getPublicacionesCTByMateria
  + descarga PDF oficial www4.sii.cl/gabineteAdmInternet/descargaArchivo
- Circulares: www.sii.cl/normativa_legislacion/circulares/{año}/indcir{año}.htm
- Resoluciones: www.sii.cl/normativa_legislacion/resoluciones/{año}/res_ind{año}.htm
- Fallos TTA: www.tta.cl (Tribunales Tributarios y Aduaneros)
Sin mirrors de terceros. Sitios privados solo como ÚLTIMA instancia, rotulados.
"""

from __future__ import annotations

import re
import html as html_lib
import urllib.parse
import httpx

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36", "Accept-Language": "es-CL,es;q=0.9"}


def _get(url: str) -> str | None:
    try:
        r = httpx.get(url, timeout=20, headers=HEADERS, follow_redirects=True)
        if r.status_code == 200 and len(r.text) > 500:
            return r.text
    except Exception:
        pass
    return None


def _oficio_download_url(item: dict) -> str:
    """Construye URL oficial de descarga del PDF del oficio en www4.sii.cl."""
    num = item.get("pubNumOficio", "")
    fecha = (item.get("pubFechaPubli") or "").replace("/", "_")
    blob = item.get("idBlobArchPublica", "")
    nombre = item.get("nombreArchPublica") or f"{num}-{fecha}.pdf"
    return ("https://www4.sii.cl/gabineteAdmInternet/descargaArchivo"
            f"?nombreDocumento={urllib.parse.quote(nombre)}&extension=pdf"
            f"&acc=download&id={blob}&mediaType=application/pdf")


def buscar_oficio(query: str, limite: int = 5) -> list[dict]:
    """Oficios SII vía API oficial www3.sii.cl. Busca en varias materias/años."""
    from datetime import datetime
    query_l = query.lower()
    materias = ["RENTA", "IVA", "OTROS"]
    if any(k in query_l for k in ("iva", "valor agregado")):
        materias = ["IVA", "OTROS", "RENTA"]
    rows: list[dict] = []
    anio_actual = datetime.now().year
    for materia in materias:
        for year in (anio_actual, anio_actual - 1, anio_actual - 2):
            if len(rows) >= limite:
                break
            try:
                r = httpx.post(
                    "https://www3.sii.cl/getPublicacionesCTByMateria",
                    json={"key": materia, "year": str(year)},
                    headers={**HEADERS, "Content-Type": "application/json", "Origin": "https://www.sii.cl"},
                    timeout=20,
                )
                if r.status_code != 200:
                    continue
                items = r.json() or []
                for it in items:
                    resumen = html_lib.unescape(it.get("pubResumen") or "")
                    legal = it.get("pubLegal") or ""
                    blob_text = f"{resumen} {legal}".lower()
                    # Filtrar por query si es específica
                    words = [w for w in query_l.split() if len(w) >= 4]
                    if words and not any(w in blob_text for w in words):
                        continue
                    num = it.get("pubNumOficio", "s/n")
                    fecha = it.get("pubFechaPubli", "")
                    rows.append({
                        "numero": f"{num}/{year}",
                        "titulo": f"Oficio N° {num} ({fecha}) — {resumen[:100]}",
                        "url": _oficio_download_url(it),
                        "fuente_url": "https://www.sii.cl/normativa_legislacion/jurisprudencia_administrativa.htm",
                        "fundamento": legal,
                    })
                    if len(rows) >= limite:
                        return rows
            except Exception:
                continue
    if rows:
        return rows
    # Fallback: índice oficial de jurisprudencia administrativa (nunca terceros)
    return [{
        "numero": query,
        "titulo": f"Buscar oficio '{query}' en Jurisprudencia Administrativa SII (oficial)",
        "url": "https://www.sii.cl/normativa_legislacion/jurisprudencia_administrativa.htm",
        "fundamento": "",
    }]


def _buscar_indice_pdf(query: str, base: str, pattern: str, anios=None, limite: int = 5) -> list[dict]:
    """Busca en los índices oficiales por año; devuelve PDFs oficiales sii.cl.

    Si ninguna coincide con la query, devuelve las más recientes del año en curso
    (los títulos de los índices solo contienen número y fecha, no la materia).
    """
    from datetime import datetime as _dt
    if anios is None:
        anio_actual = _dt.now().year
        anios = (anio_actual, anio_actual - 1, anio_actual - 2)
    rows: list[dict] = []
    recientes: list[dict] = []
    words = [w.lower() for w in query.split() if len(w) >= 3]
    for year in anios:
        url = base.format(year=year)
        text = _get(url)
        if not text:
            continue
        for href, title in re.findall(r"<a\s+href='([^']*" + pattern + r")'[^>]*>(.*?)</a>", text):
            t = html_lib.unescape(re.sub(r"<[^>]+>", "", title)).strip()
            # Extraer el párrafo descriptivo cercano si existe
            idx = text.find(href)
            snippet = re.sub(r"<[^>]+>", " ", text[idx:idx+400])
            snippet = html_lib.unescape(re.sub(r"\s+", " ", snippet)).strip()
            full_text = f"{t} {snippet}".lower()
            item = {
                "numero": href.replace(".pdf", "").title(),
                "titulo": (t or snippet)[:140],
                "url": f"{base.format(year=year).rsplit('/', 1)[0]}/{href}",
                "fuente_url": url,
                "fundamento": "",
            }
            if not any(item["numero"] == r["numero"] for r in recientes):
                recientes.append(item)
            if words and any(w in full_text for w in words):
                rows.append(item)
                if len(rows) >= limite:
                    return rows
        # Solo el primer año con contenido aporta "recientes"
        if rows:
            return rows
        if recientes and len(recientes) >= limite:
            break
    if recientes:
        return recientes[:limite]
    return []


def buscar_circular(query: str, limite: int = 5) -> list[dict]:
    base = "https://www.sii.cl/normativa_legislacion/circulares/{year}/indcir{year}.htm"
    rows = _buscar_indice_pdf(query, base, r"circu[^']*\.pdf", limite=limite)
    if rows:
        return rows
    return [{
        "numero": query,
        "titulo": f"Buscar circular '{query}' en Circulares SII (oficial)",
        "url": "https://www.sii.cl/normativa_legislacion/index_normativa_legislacion.html",
        "fundamento": "",
    }]


def buscar_resolucion(query: str, limite: int = 5) -> list[dict]:
    base = "https://www.sii.cl/normativa_legislacion/resoluciones/{year}/res_ind{year}.htm"
    rows = _buscar_indice_pdf(query, base, r"reso[^']*\.pdf", limite=limite)
    if rows:
        return rows
    return [{
        "numero": query,
        "titulo": f"Buscar resolución '{query}' en Resoluciones Exentas SII (oficial)",
        "url": "https://www.sii.cl/normativa_legislacion/resoluciones/",
        "fundamento": "",
    }]


def buscar_fallo(query: str, limite: int = 5) -> list[dict]:
    """Fallos TTA — fuente oficial Tribunales Tributarios y Aduaneros.

    Estrategia:
    1. Categoría oficial 'fallos-relevantes' (WordPress, artículos con tribunales/partes)
    2. Buscador WordPress general
    3. OJV tta.cl como referencia
    """
    words = [w.lower() for w in query.split() if len(w) >= 4]
    urls_a_probar = [
        "https://www.tta.cl/category/fallos-relevantes/",
        f"https://www.tta.cl/?s={query.replace(' ', '+')}",
        "https://www.tta.cl/fallos_relevantes/",
    ]
    for url in urls_a_probar:
        headers = {**HEADERS, "Referer": "https://www.tta.cl/"}
        try:
            r = httpx.get(url, timeout=15, headers=headers, follow_redirects=True)
            if r.status_code != 200 or len(r.text) < 800:
                continue
            text = r.text
            rows: list[dict] = []
            # Artículos WordPress (estructura category): <article>...<a href>...título...</a>
            for art in re.findall(r"<article[^>]*>(.*?)</article>", text, re.S):
                m = re.search(r'<a[^>]+href="(https://www\.tta\.cl/[^"]+)"[^>]*>([^<]{10,160})</a>', art)
                if not m:
                    continue
                href, title = m.group(1), re.sub(r"\s+", " ", html_lib.unescape(m.group(2)).strip())
                low = title.lower()
                # Filtrar navegación genérica
                if any(k in low for k in ("transparente", "preguntas", "procedimientos y plazos", "cómo presentar", "como presentar")):
                    continue
                # Si la query tiene palabras, priorizar coincidencias pero no descartar todo
                if words and not any(w in low for w in words):
                    continue
                # Deduplicar por URL normalizada (índice repite enlaces con anclas/barras distintas)
                url_norm = href.rstrip("/")
                if any(r["url"].rstrip("/") == url_norm for r in rows):
                    continue
                rows.append({
                    "numero": href.rstrip("/").split("/")[-1][:40],
                    "titulo": title[:140],
                    "url": href,
                    "fundamento": "",
                })
                if len(rows) >= limite:
                    break
            if rows:
                return rows
        except Exception:
            continue
    return [{
        "numero": query,
        "titulo": f"Buscar fallo TTA '{query}' en fallos relevantes oficiales",
        "url": "https://www.tta.cl/category/fallos-relevantes/",
        "fundamento": "",
    }]
