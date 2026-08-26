"""Capa narrativa — convierte datos crudos de jurisprudencia en texto explicativo.

El servidor MCP no entrega listas secas: cada caso se presenta con contexto
(qué se pidió, quién lo pidió, qué garantías se invocaron, cómo se resolvió,
qué NO se analizó) para que la respuesta sea entendible por sí sola.
"""

import re

# ── Utilidades de fecha en palabras → DD-MM-AAAA ─────────────────────────────
_MESES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "setiembre": "09", "octubre": "10",
    "noviembre": "11", "diciembre": "12",
}
_UNIDADES = {
    "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
    "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
    "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16,
    "dieciséis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
    "veinte": 20, "veintiuno": 21, "veintidós": 22, "veintidos": 22,
    "veintitrés": 23, "veintitres": 23, "veinticuatro": 24,
    "veinticinco": 25, "veintiséis": 26, "veintiseis": 26,
    "veintisiete": 27, "veintiocho": 28, "veintinueve": 29,
    "treinta": 30, "treinta y uno": 31,
}


def _parse_fecha_palabras(frase: str) -> str | None:
    """'tres de septiembre de dos mil veintiuno' → '03-09-2021' (mejor esfuerzo)."""
    m = re.search(r"(\w+(?:\s+y\s+\w+)?)\s+de\s+(\w+)\s+de\s+d?o?s?\s*mil\s*(\w*)", frase.lower())
    if not m:
        return None
    dia_txt, mes_txt, anio_extra = m.groups()
    dia = _UNIDADES.get(dia_txt.strip())
    mes = _MESES.get(mes_txt)
    if not dia or not mes:
        return None
    # año: "dos mil" base + unidades tras mil (mejor esfuerzo para fechas modernas)
    extra = 0
    for palabra in (anio_extra or "").split():
        v = _UNIDADES.get(palabra)
        if v:
            extra += v
    anio = 2000 + extra if extra else None
    if not anio or anio < 1800 or anio > 2100:
        return None
    return f"{dia:02d}-{mes}-{anio}"


def _extraer_fecha(content: str) -> str | None:
    m = re.search(r"Santiago,\s*([^\.]{5,60})\.", content)
    if m:
        f = _parse_fecha_palabras(m.group(1))
        if f:
            return f
        return m.group(1).strip()
    return None


# ── Parser de sentencias TC ───────────────────────────────────────────────────
_RES_INADMISIBLE = re.compile(r"inadmisibilidad|inadmisible", re.I)
_RES_RECHAZADA = re.compile(
    r"(?:se\s+)?no\s+acoger|rechaz\w+\s+(?:el|los)\s+requerimiento|desestima\w*\s+el\s+requerimiento", re.I)
_RES_ACOGIDA = re.compile(
    r"acoger\s+el\s+requerimiento|declarar\s+la\s+inaplicabilidad|declarar(se)?\s+la\s+inconstitucionalidad", re.I)
_TIPO_MAP = [
    ("requerimiento de inaplicabilidad por inconstitucionalidad", "Inaplicabilidad por inconstitucionalidad (art. 93 N°2 CPR)"),
    ("requerimiento de inconstitucionalidad", "Inconstitucionalidad (art. 93 N°1/N°6 CPR)"),
    ("inaplicabilidad por inconstitucionalidad", "Inaplicabilidad por inconstitucionalidad"),
    ("requerimiento de inaplicabilidad", "Inaplicabilidad"),
    ("cuestión de constitucionalidad", "Cuestión de constitucionalidad"),
    ("requerimiento", "Requerimiento"),
]
_GARANTIA_RE = re.compile(r"art[íi]culo[s]?\s+(?:19\s*,?\s*N?[°º]?\s*(\d{1,2})|(\d{1,3}))")


def analizar_sentencia_tc(content: str, rol: str = "") -> dict:
    """Extrae estructura explicativa desde el texto crudo de una sentencia del TC."""
    c = re.sub(r"\s+", " ", content or "")
    out: dict = {"rol": rol}

    # Tipo de acción
    tipo = ""
    low = c.lower()
    for patron, etiqueta in _TIPO_MAP:
        if patron in low:
            tipo = etiqueta
            break
    out["tipo"] = tipo

    # Fecha
    out["fecha"] = _extraer_fecha(content or "")

    # Requirente / parte
    m = re.search(
        r"(?:presentado por|requerimiento[^\.]{0,80}por)\s+([A-ZÁÉÍÓÚÑ][^,\.;]{4,90})", content or "")
    out["requirente"] = m.group(1).strip() if m else ""

    # Norma impugnada: buscar menciones de ley/dfl/auto acordado
    normas = []
    for nm in re.finditer(r"(?:Ley|DFL|D\.F\.L\.|DL)\s*N?[°º]?\s*([\d\.]{4,9})|(Auto Acordado[^,;\.]{0,120})", c):
        trozo = (nm.group(2) or f"Ley {nm.group(1)}").strip()
        if trozo and trozo not in normas:
            normas.append(trozo)
    out["norma_impugnada"] = "; ".join(normas[:3])

    # Garantías constitucionales invocadas (art. 19 N°X y otros artículos CPR)
    arts = []
    for gm in _GARANTIA_RE.finditer(c[:4000]):
        n = gm.group(1) or gm.group(2)
        if n and n not in arts:
            arts.append(n)
    out["garantias"] = arts[:6]

    # Resolución
    if _RES_INADMISIBLE.search(c):
        resolucion = "INADMISIBLE — el TC no analizó el fondo"
        fondo = ("La causa terminó por admisibilidad: el requirente no demostró "
                 "con precisión cómo la norma afectaba sus derechos. El fondo "
                 "(si el cobro/norma es o no inconstitucional) quedó SIN resolver.")
    elif _RES_ACOGIDA.search(c):
        resolucion = "ACOGIDA — acogió el requerimiento"
        fondo = "El Tribunal analizó el fondo y acogió la impugnación."
    elif _RES_RECHAZADA.search(c):
        resolucion = "RECHAZADA — no acogió el requerimiento"
        fondo = "El Tribunal analizó el fondo y rechazó la impugnación."
    elif re.search(r"téngase presente|proveído|traslado|tenga presente", c[:1500], re.I):
        resolucion = "PROVIDENCIA — resolución de trámite, no sentencia de fondo"
        fondo = ("Lo mostrado es una resolución administrativa (proveído), no una "
                 "sentencia: aún no hay decisión sobre el fondo.")
    else:
        resolucion = "SIN DETERMINAR — revisar texto completo"
        fondo = ""
    out["resolucion"] = resolucion
    out["fondo"] = fondo

    # Primer considerando útil como contexto
    m_ctx = re.search(r"(?:VISTOS?[^A-Z]*Y CONSIDERANDO:?|CONSIDERANDO:?)(.{200,700})", content or "")
    out["contexto"] = re.sub(r"\s+", " ", m_ctx.group(1)).strip()[:600] if m_ctx else ""
    return out


def formatear_caso_tc(item: dict, analisis: dict) -> str:
    """Bloque narrativo legible por humanos para un caso del TC."""
    lineas = [f"CASO Rol {analisis.get('rol') or item.get('rol', '?')}"]
    if analisis.get("tipo"):
        lineas.append(f"Tipo de acción: {analisis['tipo']}")
    if analisis.get("fecha"):
        lineas.append(f"Fecha de la resolución: {analisis['fecha']}")
    if analisis.get("requirente"):
        lineas.append(f"Requirente: {analisis['requirente']}")
    if analisis.get("norma_impugnada"):
        lineas.append(f"Norma cuestionada: {analisis['norma_impugnada']}")
    if analisis.get("garantias"):
        gs = ", ".join(a if a.isdigit() else f"19 N°{a.lstrip('0')}" for a in analisis["garantias"])
        lineas.append(f"Artículos CPR invocados: {gs}")
    lineas.append(f"Resolución: {analisis.get('resolucion', '—')}")
    if analisis.get("fondo"):
        lineas.append(f"Alcance: {analisis['fondo']}")
    if analisis.get("contexto"):
        lineas.append(f"Contexto (considerandos iniciales): \"{analisis['contexto']}…\"")
    frag = (item.get("frag") or "").strip()
    if frag:
        lineas.append(f"Fragmento destacado: \"{frag}…\"")
    lineas.append(f"Ficha oficial: {item.get('url', '')}")
    return "\n".join(lineas)


# ── Noticias/fallos TGR ───────────────────────────────────────────────────────
def limpiar_html(texto_html: str) -> str:
    """HTML → texto plano limpio."""
    t = re.sub(r"<script[^>]*>.*?</script>", " ", texto_html or "", flags=re.S)
    t = re.sub(r"<style[^>]*>.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&")
    t = t.replace("&#8220;", '"').replace("&#8221;", '"')
    t = t.replace("&#8221;", '"').replace("&ldquo;", '"').replace("&rdquo;", '"')
    return re.sub(r"\s+", " ", t).strip()


def extraer_noticia(texto_plano: str, max_chars: int = 2200) -> dict:
    """Desde el HTML limpio de una noticia TGR/gob, separa cuerpo útil."""
    # Cortar menús: buscar el primer párrafo largo (>300 chars sin nav típica)
    idx = -1
    for marca in ("Santiago,", "Tesorería General", "La Tesorería", "Con fecha",
                  "Mediante", "El fallo", "La Corte"):
        i = texto_plano.find(marca)
        if i > -1 and (idx == -1 or i < idx):
            idx = i
    cuerpo = texto_plano[idx:] if idx > -1 else texto_plano
    # Quitar colas típicas de footer/nav
    for cola in ("Mantención programada", "Busca tu trámite", "Iniciar Sesión",
                 "Comenzar actividad"):
        j = cuerpo.find(cola)
        if j > 400:
            cuerpo = cuerpo[:j]
    return {"cuerpo": cuerpo[:max_chars].strip()}


def formatear_noticia_tgr(titulo: str, url: str, fecha: str, cuerpo: str, resultado: str = "") -> str:
    lineas = [f"NOTICIA OFICIAL TGR: {titulo}"]
    if fecha:
        lineas.append(f"Fecha publicación: {fecha}")
    if resultado:
        lineas.append(f"Resultado detectado: {resultado}")
    if cuerpo:
        lineas.append(f"Contenido: {cuerpo}")
    lineas.append(f"Fuente oficial: {url}")
    return "\n".join(lineas)


# ── Formato genérico para cualquier fuente ───────────────────────────────────
DESCRIPCION_FUENTES = {
    "TC": "Sentencias del Tribunal Constitucional (control de constitucionalidad).",
    "TGR": "Tesorería General de la República: cobranza fiscal, fallos y comunicados oficiales.",
    "CGR": "Contraloría General de la República: dictámenes vinculantes sobre legalidad administrativa.",
    "BCN": "Biblioteca del Congreso Nacional: legislación consolidada y dictámenes.",
    "SII": "Servicio de Impuestos Internos: oficios, circulares y resoluciones tributarias.",
    "TDPI": "Tribunal de Defensa de la Libre Competencia (TDLC): resoluciones competitivas.",
    "SMA": "Superintendencia del Medio Ambiente: sancionatorios ambientales.",
    "INAPI": "Instituto Nacional de Propiedad Industrial: marcas y patentes.",
    "Superir": "Boletín Concursal: liquidaciones y reorganizaciones.",
    "CMF": "Comisión para el Mercado Financiero: normativa bancaria/financiera.",
    "DT": "Dirección del Trabajo: jurisprudencia administrativa laboral.",
    "SciELO": "Doctrina académica revisada por pares [vía DOI/Crossref].",
}


def bloque_item(fuente: str, titulo: str, url: str, contexto: str = "",
                detalle: str = "", fecha: str = "", resultado: str = "") -> str:
    """Bloque narrativo estándar para un resultado cualquiera."""
    lineas = [f"• {titulo}"]
    if fecha:
        lineas.append(f"  Fecha: {fecha}")
    if resultado:
        lineas.append(f"  Resultado/detalle: {resultado}")
    if contexto:
        lineas.append(f"  Contexto: {contexto}")
    if detalle:
        lineas.append(f"  Contenido: {detalle[:1800]}")
    if url:
        lineas.append(f"  Fuente oficial: {url}")
    return "\n".join(lineas)


def encabezado_informe(fuente: str, consulta: str, n_resultados: int) -> str:
    """Encabezado estándar con explicación de qué es la fuente."""
    desc = DESCRIPCION_FUENTES.get(fuente, "")
    out = [f"[{fuente.upper()}] Consulta: '{consulta}' — {n_resultados} resultado(s) — {fecha_hoy()}"]
    if desc:
        out.append(f"Acerca de esta fuente: {desc}")
    return "\n".join(out)


def conclusion_simple(consulta: str, n: int, matiz: str = "") -> str:
    """Párrafo de cierre honesto: qué se encontró y qué no."""
    if n == 0:
        return ("CONCLUSIÓN: No se encontraron resultados en esta fuente para la consulta. "
                "Esto NO significa que el asunto no exista jurídicamente: prueba términos "
                "más amplios u otra fuente oficial. Se declara el vacío informativo.")
    base = (f"CONCLUSIÓN: Se recuperaron {n} resultado(s) relevantes para '{consulta}'. "
            f"Revísalos caso a caso; cada link permite verificar el texto oficial completo.")
    if matiz:
        base += f" {matiz}"
    return base


def fecha_hoy() -> str:
    from datetime import datetime
    return datetime.now().strftime("%d-%m-%Y")
