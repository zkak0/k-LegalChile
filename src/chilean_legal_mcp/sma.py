"""SMA — SNIFA (fiscalización y sanciones ambientales)."""

from __future__ import annotations

import re
import html as html_lib
import httpx

# Títulos del menú de navegación SNIFA (no son resultados).
_MENU = {
    "Inicio", "Fiscalizaciones", "Procedimientos sancionatorios", "Medidas provisionales",
    "Denuncias", "Expedientes", "Registro Público", "Registro publico", "Fiscalización",
    "Formularios", "Estadísticas", "Informa", "Pliego de cargos", "Resoluciones",
    "Atención de denuncias", "Puntos de atención", "Presentar denuncia", "SNIFA",
    "Impactar", "Reiniciar", "Buscar", "MAPA", "Volver", "Ingresar", "Salir",
    "Requerimientos de Ingreso", "Registro Sanciones", "Catastro Unidades fiscalizables",
    "Resoluciones de Calificación Ambiental", "Planes de Prevención y Descontaminación Ambiental",
    "Normas de Emisión", "Normas de Calidad", "Programas de Cumplimiento",
    "Otros Instrumentos", "Programas y subprogramas de fiscalización",
    "Instrucciones y requerimientos de caracter general", "Planes de Reparación",
    "Dictámenes de Contraloría", "Sentencias de Tribunales",
    "Caducidad y acreditación de vigencia de RCA", "Seguimiento Ambiental",
    "Datos Abiertos", "Ir al sitio SMA",
}

# Rutas que son pestañas/secciones del portal (no resultados).
_RUTAS_MENU = {
    "", "Fiscalizacion", "Sancionatorio", "MedidaProvisional", "RequerimientoIngreso",
    "RegistroPublico", "UnidadFiscalizable", "Instrumento", "ProgramaCumplimiento",
    "Resolucion", "PlanReparacion", "DictamenContraloria", "SentenciaTribunal",
    "CaducidadRCA", "SeguimientoAmbiental", "Estadisticas", "DatosAbiertos",
    "ExpedienteAmbiental", "Index", "Tipo", "Contraloria", "Tribunal",
    "NormativaAmbiental", "Instruccion", "Programa",
}


def _filtra(href: str, title: str) -> bool:
    t = title.strip()
    if t in _MENU:
        return False
    for seg in href.rstrip("/").split("/"):
        if seg in _RUTAS_MENU:
            return False
    return True


def buscar_sancionatorio(query: str, limite: int = 5) -> list[dict]:
    for url in [
        f"https://snifa.sma.gob.cl/Sancionatorio?texto={query.replace(' ', '+')}",
        f"https://snifa.sma.gob.cl/RegistroPublico?texto={query.replace(' ', '+')}",
        f"https://snifa.sma.gob.cl/Fiscalizacion?texto={query.replace(' ', '+')}",
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
                if not _filtra(href, t):
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


def buscar_procedimiento_fiscalizacion(query: str, limite: int = 5) -> list[dict]:
    """SMA — expedientes de fiscalización ambiental y procedimientos sancionatorios en SNIFA."""
    for url in [
        f"https://snifa.sma.gob.cl/ExpedienteAmbiental?texto={query.replace(' ', '+')}",
        f"https://snifa.sma.gob.cl/RegistroPublico?texto={query.replace(' ', '+')}",
        f"https://snifa.sma.gob.cl/Fiscalizacion?texto={query.replace(' ', '+')}",
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
                if not _filtra(href, t):
                    continue
                full = href if href.startswith("http") else f"https://snifa.sma.gob.cl{href}"
                rows.append({"numero": href.split("/")[-1][:20], "titulo": t[:120], "url": full})
                if len(rows) >= limite:
                    break
            if rows:
                return rows
        except Exception:
            continue
    return [{"numero": query, "titulo": f"Buscar '{query}' en expedientes SMA (SNIFA)", "url": f"https://snifa.sma.gob.cl/ExpedienteAmbiental?texto={query.replace(' ', '+')}"}]
