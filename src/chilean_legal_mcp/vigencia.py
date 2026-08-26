"""Estado de vigencia de normas chilenas.

La vigencia real de una ley no vive en el XML obtxml (ese solo marca derogaciones
parciales por artículo). El estado actual (VIGENTE / DEROGADA / REFUNDIDA /
DEROGADA PARCIALMENTE / MODIFICADA POR ...) se muestra en el encabezado de la
página oficial LeyChile/navegar como zona de estado + notas.

Estrategia:
1. Resolver numero->leychileId vía SPARQL si hace falta
2. Renderizar la página oficial y extraer las frases de estado del encabezado
3. Cachear el resultado (SQLite) con TTL largo — la vigencia cambia raramente

Frases verificadas (2026):
- "Esta norma ha sido derogada por ..." -> DEROGADA
- "Esta norma ha sido refundida por ..." / zona "REFUNDIDO POR" -> REFUNDIDA
- Sin patrones de derogación + "Última Versión" -> VIGENTE
- "Última modificación: FECHA - Ley N°" siempre se devuelve como dato
"""

from __future__ import annotations

import re
import time
from datetime import datetime

from .sparql_client import BCNClient, leychile_url

# Cache en memoria (TTL corto) + SQLite persistente (TTL 7 días) — la vigencia
# cambia raramente; evita renders de Playwright innecesarios
_ttl = 7 * 86400  # 7 días
_cache_memoria: dict[str, tuple[float, str]] = {}


def _db():
    """Cache SQLite de vigencia (lazy — evita dependencia circular)."""
    global __db_cache
    try:
        return __db_cache
    except NameError:
        from .db import NormasDB
        __db_cache = NormasDB()
        return __db_cache

MESES = {
    "ENE": "01", "FEB": "02", "MAR": "03", "ABR": "04", "MAY": "05", "JUN": "06",
    "JUL": "07", "AGO": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DIC": "12",
}


def _fecha_a_chile(fecha_larga: str) -> str:
    """Convierte '03-ENE-2025' a '03-01-2025'. Deja lo demás igual."""
    m = re.match(r"(\d{2})-([A-ZÁÉÍÓÚ]{3,4})-(\d{4})", fecha_larga.upper())
    if m:
        d, mes, y = m.groups()
        mnum = MESES.get(mes[:3]) or MESES.get(mes)
        if mnum:
            return f"{d}-{mnum}-{y}"
    return fecha_larga


def _resolver_leychile_id(identificador: str) -> str | None:
    """Acepta N° de ley (ej "21643", "21.643") o idNorma LeyChile (ej "1200096").

    Estrategia: si es numérico, primero buscar como N° de norma en SPARQL; si no
    existe, se asume que ya es un idNorma.
    """
    identificador = identificador.strip()
    if not identificador:
        return None
    if identificador.isdigit():
        numero_buscar = identificador.replace(".", "")
        try:
            c = BCNClient()
            rows = c.search_by_number(numero_buscar, limit=1)
            # Solo usar si el número encontrado coincide exactamente
            if rows:
                num_encontrado = str(rows[0].get("numero") or "").replace(".", "")
                if num_encontrado == numero_buscar:
                    return rows[0].get("leychileId") or rows[0].get("leychile_id")
        except Exception:
            pass
        # No hay norma con ese número → ya era un idNorma
        return identificador
    # Texto libre (número con puntos)
    numero = identificador.replace(".", "")
    if not numero.isdigit():
        return None
    try:
        c = BCNClient()
        rows = c.search_by_number(numero, limit=1)
        if rows:
            return rows[0].get("leychileId") or rows[0].get("leychile_id")
    except Exception:
        pass
    return None


def _renderizar_estado(leychile_id: str) -> dict:
    """Renderiza la página navegar oficial y extrae el estado de vigencia del encabezado."""
    resultado = {
        "estado": "DESCONOCIDO",
        "derogada_por": "",
        "refundida_por": "",
        "ultima_modificacion": "",
        "modificada_por": "",
        "fecha_ultima_version": "",
        "notas": "",
    }
    url = f"https://www.bcn.cl/leychile/navegar?idNorma={leychile_id}"
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        resultado["notas"] = "Playwright no instalado"
        return resultado

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
                locale="es-CL",
            ).new_page()
            page.goto(url, wait_until="networkidle", timeout=50000)
            page.wait_for_timeout(3500)
            texto = page.inner_text("body")
            browser.close()
    except Exception as e:
        resultado["notas"] = f"Error renderizando: {type(e).__name__}"
        return resultado

    # Colapsar espacios/line breaks para patrones
    plano = re.sub(r"\s+", " ", texto)

    # Estado superior
    dere = re.search(r"(?:norma ha sido|norma fue)\s+(derogada|refundida|rectificada)\s+por\s+([^|\.]+)", plano, re.I)
    if dere:
        tipo = dere.group(1).upper()
        norma_ref = dere.group(2).strip()
        if tipo == "DEROGADA":
            resultado["estado"] = "DEROGADA"
            resultado["derogada_por"] = norma_ref
        elif tipo == "REFUNDIDA":
            resultado["estado"] = "REFUNDIDA"
            resultado["refundida_por"] = norma_ref
        else:
            resultado["estado"] = tipo

    # Zona en mayúsculas
    if resultado["estado"] == "DESCONOCIDO":
        if re.search(r"\bDEROGAD[AO]\b", texto):
            resultado["estado"] = "DEROGADA"
            m = re.search(r"DEROGAD[AO]?\s+POR\s+([^|]+?)\s+(?:ver |Promulgación|Publicación|,)", plano, re.I)
            if m:
                resultado["derogada_por"] = m.group(1).strip()[:80]
        elif re.search(r"REFUNDIDO POR", plano, re.I):
            resultado["estado"] = "REFUNDIDA"
            m = re.search(r"REFUNDIDO\s+POR\s+([^|]+?)\s+(?:ver |Promulgación|Publicación)", plano, re.I)
            if m:
                resultado["refundida_por"] = m.group(1).strip()[:80]

    # Recortar 'refundida_por' si quedó largo (la señal "(refundida)" aparece tras la primera referencia)
    if resultado.get("refundida_por"):
        rp = resultado["refundida_por"]
        corte = re.search(r"\)\s+ver\s|ver DFL|Promulgación", rp, re.I)
        if corte:
            rp = rp[:corte.start()].strip()
        resultado["refundida_por"] = rp[:80]

    # Última versión / última modificación (limitar la norma modificadora a su referencia)
    m = re.search(r"Versión:\s*Última Versión\s*-\s*([0-9]{2}-[A-ZÁÉÍÓÚ]{3,4}-[0-9]{4})", plano, re.I)
    if m:
        resultado["fecha_ultima_version"] = _fecha_a_chile(m.group(1))
    m = re.search(r"Última\s+modificación:\s*([0-9]{2}-[A-ZÁÉÍÓÚ]{3,4}-[0-9]{4})\s*-\s*([A-Za-zÁÉÍÓÚäëïöüñÑ]+[^0-9]{0,10}\d{2,7})", plano, re.I)
    if m:
        resultado["ultima_modificacion"] = _fecha_a_chile(m.group(1))
        resultado["modificada_por"] = m.group(2).strip()[:60]

    if resultado["estado"] == "DESCONOCIDO" and resultado["fecha_ultima_version"]:
        resultado["estado"] = "VIGENTE"

    return resultado


def estado_vigencia(identificador: str) -> dict:
    """Devuelve el estado de vigencia de una norma.

    identificador: N° de ley (ej "21643" o "21.643") o id LeyChile (ej "1200096").
    """
    id_norma = _resolver_leychile_id(identificador)
    if not id_norma:
        return {"error": f"No se pudo resolver '{identificador}' a una norma LeyChile.",
                "url_referencia": f"https://www.bcn.cl/leychile/navegar?idNorma=<idNorma>"}

    clave = f"vigencia:{id_norma}"
    ahora = time.time()
    # 1. Cache memoria
    if clave in _cache_memoria:
        ts, payload = _cache_memoria[clave]
        if ahora - ts < _ttl:
            resultado = dict(payload)
            resultado["cache"] = "memoria"
            return resultado
    # 2. Cache SQLite persistente
    try:
        antiguo = _db().get_vigencia(id_norma)
        if antiguo:
            antiguo["cache"] = "sqlite"
            _cache_memoria[clave] = (ahora, antiguo)
            return antiguo
    except Exception:
        pass

    resultado = _renderizar_estado(id_norma)
    resultado.update({
        "leychile_id": id_norma,
        "url_oficial": leychile_url(id_norma) or f"https://www.bcn.cl/leychile/navegar?idNorma={id_norma}",
        "fecha_consulta": datetime.now().strftime("%d-%m-%Y"),
    })
    try:
        _db().save_vigencia(id_norma, resultado)
    except Exception:
        pass
    _cache_memoria[clave] = (ahora, resultado)
    return resultado


def formatear_vigencia(estado: dict) -> str:
    """Texto listo para mostrar al usuario."""
    if "error" in estado:
        return estado["error"]
    lineas = [
        f"Estado de vigencia de la norma (LeyChile id {estado.get('leychile_id')}):",
        f"  Estado: {estado.get('estado')}",
    ]
    if estado.get("derogada_por"):
        lineas.append(f"  Derogada por: {estado['derogada_por']}")
    if estado.get("refundida_por"):
        lineas.append(f"  Refundida por: {estado['refundida_por']}")
    if estado.get("ultima_modificacion"):
        lineas.append(f"  Última modificación: {estado['ultima_modificacion']}")
    if estado.get("modificada_por"):
        lineas.append(f"  Modificada por: {estado['modificada_por']}")
    if estado.get("notas"):
        lineas.append(f"  Nota: {estado['notas']}")
    lineas.append(f"  Fecha de consulta: {estado.get('fecha_consulta')}")
    lineas.append(f"  Fuente oficial: {estado.get('url_oficial')}")
    return "\n".join(lineas)