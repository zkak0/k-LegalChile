"""Búsqueda de dictámenes de la Contraloría General de la República (CGR).

Fuente autoritativa y única para dictámenes: https://www.contraloria.cl
La base LegisJuri es Domino: la búsqueda REAL es un POST al formulario
`FormConsultaWeb2k` con los campos exactos que ese formulario declara; un GET
con parámetros en la URL NO devuelve resultados (solo el formulario vacío).

Flujo verificado (inspección del HTML 2026):
  1. GET  .../FormConsultaWeb2k?OpenForm&Seq=1        → cookies de sesión
  2. POST misma URL con el set completo de campos     → página de resultados
  3. Los dictámenes aparecen como enlaces "...?OpenDocument"

Ética: una consulta = una sesión corta (2-3 requests). Ante 403/429/timeout
la respuesta es "CGR no disponible ahora", NUNCA martilleo.
"""

from __future__ import annotations

import re
import html as html_lib

import httpx

BASE = "https://www.contraloria.cl"
FORM_URL = f"{BASE}/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/FormConsultaWeb2k?OpenForm&Seq=1"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-CL,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
    "Cookie": "JURIS=OK",
}


class CGRNoDisponible(Exception):
    """La CGR no respondió o devolvió algo que no es página de resultados."""


def _parse_results(text: str, limite: int) -> list[dict]:
    """Extrae resultados de la página de resultados CGR.

    Soporta DOS marcados (verificados contra la CGR, ago-2026):
  1. Sistema actual ("NVA"): filas `<tr id="UNID32">` con fecha DD/MM/YYYY,
     enlace `<a class="lkDictamen" onclick="muestraDictamenIframe('…/cgrDetalleDictamenNVDA?OpenForm&UNID=…')">NUMERO</a>`
     y la materia/resumen en el último <td>.
  2. Legado: enlaces clásicos `?OpenDocument` (se mantienen por compatibilidad).
    """
    resultados = _parse_filas_nva(text, limite)
    if not resultados:
        resultados = _parse_legado(text, limite)
    return resultados[:limite]


def total_encontrados(text: str) -> int | None:
    """Número total de dictámenes que la CGR reportó como hallados."""
    m = re.search(r"encontrad[oa]\s*([\d\.]+)\s+dict", text, re.I)
    if m:
        try:
            return int(m.group(1).replace(".", ""))
        except ValueError:
            return None
    return None


_RE_FILA_NVA = re.compile(r'<tr\s+id="([0-9A-Fa-f]{32})"[^>]*>([\s\S]*?)</tr>', re.I)
_RE_FECHA_FILA = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")
_RE_LINK_DICTAMEN = re.compile(r'<a[^>]+class="[^"]*lkDictamen[^"]*"[^>]*>([\s\S]*?)</a>', re.I)
_RE_UNID_DETALLE = re.compile(r"cgrDetalleDictamenNVDA\?OpenForm&UNID=([0-9A-Fa-f]{32})")
_DETALLE_URL = f"{BASE}/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/cgrDetalleDictamenNVDA?OpenForm&UNID={{}}"


def _parse_filas_nva(text: str, limite: int) -> list[dict]:
    """Marcado actual: filas <tr id="UNID"> con clase lkDictamen en el enlace."""
    salidas: list[dict] = []
    for unid, row in _RE_FILA_NVA.findall(text):
        if "lkDictamen" not in row:
            continue  # fila decorativa (fondos, headers de tabla)
        mm = _RE_LINK_DICTAMEN.search(row)
        numero = html_lib.unescape(re.sub(r"<[^>]+>", "", mm.group(1))).strip() if mm else ""
        celdas = [html_lib.unescape(re.sub(r"<[^>]+>", " ", td))
                  for td in re.findall(r"<td[^>]*>([\s\S]*?)</td>", row, re.I)]
        celdas = [re.sub(r"\s+", " ", c).strip() for c in celdas]
        fecha = ""
        for c in celdas:
            mf = _RE_FECHA_FILA.search(c)
            if mf:
                fecha = mf.group(1)
                break
        # la materia/resumen: la celda MÁS LARGA que no sea número ni fecha
        candidatos = [c for c in celdas
                      if len(c) > 20 and c != numero and not _RE_FECHA_FILA.fullmatch(c)]
        materia = max(candidatos, key=len)[:300] if candidatos else f"Dictamen {numero}"
        m_unid = _RE_UNID_DETALLE.search(row)
        url = _DETALLE_URL.format(m_unid.group(1) if m_unid else unid)
        if numero:
            salidas.append({"numero": numero, "titulo": materia, "fecha": fecha, "url": url})
        if len(salidas) >= limite:
            break
    return salidas


def _parse_legado(text: str, limite: int) -> list[dict]:
    """Formato antiguo: enlaces <a href="…OpenDocument">."""
    resultados: list[dict] = []
    for href, inner in re.findall(r'<a[^>]+href="([^"]*OpenDocument[^"]*)"[^>]*>(.*?)</a>', text, re.I | re.S):
        num_raw = html_lib.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        if len(num_raw) < 4 or not re.search(r"\d", num_raw):
            continue
        if re.fullmatch(r"\s*\d{1,2}\s*", num_raw):
            continue  # paginación 1..50
        full_url = href if href.startswith("http") else f"{BASE}{href}"
        idx = text.find(href)
        row = text[max(0, idx - 600): idx + 800]
        tds = [html_lib.unescape(re.sub(r"<[^>]+>", " ", td)).strip()
               for td in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)]
        titulo = ""
        for td in tds:
            clean = re.sub(r"\s+", " ", td)
            if len(clean) > 15 and clean != num_raw and "Dictamen" not in clean and "Buscar" not in clean:
                titulo = clean[:200]
                break
        if not titulo:
            titulo = f"Dictamen {num_raw}"
        resultados.append({"numero": re.sub(r"\s+", " ", num_raw), "titulo": titulo,
                           "fecha": None, "url": full_url})
        if len(resultados) >= limite:
            break
    resultados = [r for r in resultados if len(r["numero"]) >= 4 and not re.fullmatch(r"\d{1,2}", r["numero"].strip())]
    return resultados[:limite]


def _url_busqueda(query: str, limite: int, numero: str | None = None,
                  fecha_desde: str | None = None, fecha_hasta: str | None = None) -> str:
    """URL de búsqueda EXACTA que usa el propio JavaScript de la CGR
    (función realizaConsulta del formulario: navega un GET con hpbb=SI).
    """
    import urllib.parse
    q = urllib.parse.quote(query)
    num = urllib.parse.quote(numero or "")
    fd = urllib.parse.quote(fecha_desde or "")
    fh = urllib.parse.quote(fecha_hasta or "")
    pp = max(10, min(limite, 50))
    return (f"{BASE}/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/FormConsultaWeb2k"
            f"?OpenForm&TextoLibre={q}&NumeroDictamen={num}&Materia=Cualquiera"
            f"&FechaDesde={fd}&FechaHasta={fh}&desde=1&dpp={pp}&porPagina={pp}"
            f"&Orden=1&hpbb=SI")


def buscar_cgr(query: str, limite: int = 10, timeout: float = 25.0,
               numero: str | None = None, fecha_desde: str | None = None,
               fecha_hasta: str | None = None,
               transport: httpx.BaseTransport | None = None) -> list[dict]:
    """Busca dictámenes en la CGR hablándole con SU PROPIO idioma: la URL GET
    que el JavaScript oficial del formulario (realizaConsulta) usa para pedir
    resultados — sin POSTs redundantes ni reintentos de martillo.

    Distingue honestamente "no existen dictámenes con ese criterio" (lista
    vacía) de "la CGR no respondió" (CGRNoDisponible).

    `transport` solo existe para tests offline (httpx.MockTransport).
    """
    query = query.strip()
    if not query and not numero:
        return []
    url = _url_busqueda(query, limite, numero, fecha_desde, fecha_hasta)
    frameset_url = f"{BASE}/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/fsconsultaNva?OpenFrameset"
    try:
        with httpx.Client(headers=_HEADERS, follow_redirects=True, timeout=timeout,
                          transport=transport) as c:
            c.get(frameset_url)  # sesión inicial (cookies), como un navegador real
            r = c.get(url, headers={"Referer": frameset_url})
            r.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise CGRNoDisponible(f"la CGR no respondió o fue inalcanzable ({type(exc).__name__})") from exc

    # Marcador de "nos entendieron": la página real de resultados tiene filas
    # con UNID + clase lkDictamen ("sistema NVA") o enlaces OpenDocument (legado).
    if "lkDictamen" not in r.text and "OpenDocument" not in r.text:
        # Si la página devuelve el formulario de búsqueda y declara explícitamente
        # que NO hay resultados, es una respuesta cierta y vacía — NO un bloqueo.
        if "No se han encontrado dict" in r.text or "no se han encontrado dict" in r.text.lower():
            return []
        raise CGRNoDisponible("la CGR devolvió el formulario sin resultados "
                              "(posible bloqueo de WAF o cambio de formato)")
    hallados = _parse_results(r.text, limite)
    # si el marcador existe pero el parseo no sacó nada: hay un dictamen cuyo
    # marcado no calza — eso NO es "no existen dictámenes".
    if not hallados and ("lkDictamen" in r.text or "OpenDocument" in r.text):
        raise CGRNoDisponible("la CGR respondió una página de resultados cuyo marcado "
                              "no pude interpretar (posible cambio de formato)")
    return hallados


def obtener_texto_dictamen(url: str, timeout: float = 25.0) -> str | None:
    """Texto completo de un dictamen, como texto plano.

    El cuerpo íntegro de un dictamen CGR "NVA" no viene en el HTML estático:
    el portal lo carga después vía el agente ``CompletoDictamenJSON?OpenAgent``
    —y ese agente solo responde con datos dentro de una sesión autenticada de
    navegador (Domino rechaza las peticiones HTTP crudas con Error 500). Por
    eso: primero intentamos la lectura estática (dictámenes legados
    OpenDocument); si solo se obtuvieron metadatos ("Cargando..." / cuerpo
    ausente), abrimos un Chromium real para que el agente devuelva el JSON.
    """
    try:
        r = httpx.get(url, headers=_HEADERS, timeout=timeout, follow_redirects=True)
        r.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise CGRNoDisponible(f"no se pudo leer el dictamen ({type(exc).__name__})") from exc
    t = re.sub(r"<script[\s\S]*?</script>", " ", r.text, flags=re.I)
    t = re.sub(r"<style[\s\S]*?</style>", " ", t, flags=re.I)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</p\s*>", "\n\n", t, flags=re.I)
    t = html_lib.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    if len(t) > 200 and "Cargando" not in t:
        return t
    # Solo metadatos: el sistema NVA carga el cuerpo vía agente JSON de sesión.
    m = re.search(r"[?&]UNID=([0-9A-Fa-f]{32})", url)
    if m:
        cuerpo = _texto_dictamen_nva(m.group(1))
        if cuerpo:
            return cuerpo
    return t if len(t) > 200 else None


def _texto_dictamen_nva(unid: str, timeout_ms: int = 60_000) -> str | None:
    """Lee el JSON de ``CompletoDictamenJSON?OpenAgent`` con sesión Chromium."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None
    base = f"{BASE}/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base}/cgrDetalleDictamenNVDA?OpenForm&UNID={unid}",
                      timeout=60_000)
            page.wait_for_timeout(2500)
            res = page.evaluate(
                """async (unid) => {
                  const r = await fetch(
                    'CompletoDictamenJSON?OpenAgent&unid=' + unid,
                    {credentials: 'include'});
                  // El agente Domino declara iso-8859-1; lo leemos como bytes
                  // y lo decodificamos correctamente (evita mojibake "�").
                  const buf = await r.arrayBuffer();
                  const t = new TextDecoder('iso-8859-1').decode(buf);
                  return {ok: r.ok, t};
                }""", unid)
            browser.close()
    except Exception:
        return None
    if not res.get("ok"):
        return None
    try:
        import json
        datos = json.loads(res["t"])
        crudo = datos.get("textocompleto") or ""
    except Exception:
        return None
    t = re.sub(r"<br\s*/?>", "\n", crudo, flags=re.I)
    t = html_lib.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip() or None
