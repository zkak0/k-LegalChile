"""Extracción de citas normativas de texto libre (documentos de un expediente).

Detecta citas al estilo jurídico chileno y las devuelve estructuradas a nivel de
artículo e inciso, con el texto literal citado y su posición en el documento:

  - "artículo 148 del Código Civil"             → cuerpo + artículo
  - "arts. 1705 y 1712 del Código Civil"        → lista de artículos
  - "artículo 148, inciso primero, del CC"      → cuerpo + artículo + inciso
  - "art. 64 CPC" (abreviatura)                  → cuerpo normalizado
  - "artículo 19, N° 24, de la Constitución"     → cuerpo + artículo + N°
  - "Ley N° 19.966" / "Ley 19.966, art. 24"      → norma numerada (± artículo)
  - "Decreto Supremo 47, de 2020, del MINSAL"    → decreto numerado

Además provee `extraer_articulo`: corte forense del articulado de una norma ya
descargada (texto plano), respetando el ordinal con "º/°" que usa LeyChile
("Artículo 2°" no debe confundirse con "artículo 20").

Todo el módulo es offline: no descarga nada; opera sobre texto.
"""

from __future__ import annotations

import re

# --- Cuerpos legales reconocibles ---------------------------------------------

CUERPOS: list[tuple[str, str]] = [
    # (forma texto completo, nombre canónico)
    (r"C[óo]digo\s+Civil", "Código Civil"),
    (r"C[óo]digo\s+de\s+Procedimiento\s+Civil", "Código de Procedimiento Civil"),
    (r"C[óo]digo\s+de\s+Procedimiento\s+Penal", "Código de Procedimiento Penal"),
    (r"C[óo]digo\s+Procesal\s+Penal", "Código de Procedimiento Penal"),
    (r"C[óo]digo\s+Org[áa]nico\s+de\s+Tribunales", "Código Orgánico de Tribunales"),
    (r"C[óo]digo\s+del\s+Trabajo", "Código del Trabajo"),
    (r"C[óo]digo\s+Penal", "Código Penal"),
    (r"C[óo]digo\s+de\s+Comercio", "Código de Comercio"),
    (r"C[óo]digo\s+Sanitario", "Código Sanitario"),
    (r"C[óo]digo\s+de\s+Aguas", "Código de Aguas"),
    (r"C[óo]digo\s+de\s+Miner[íi]a", "Código de Minería"),
    (r"C[óo]digo\s+Tributario", "Código Tributario"),
    (r"C[óo]digo\s+Aeron[áa]utico", "Código Aeronáutico"),
    (r"Constituci[óo]n\s+Pol[íi]tica\s+de\s+la\s+Rep[úu]blica",
     "Constitución Política de la República"),
    (r"Constituci[óo]n(?:\s+Pol[íi]tica)?", "Constitución Política de la República"),
]

ABREVIATURAS: dict[str, str] = {
    "CC": "Código Civil",
    "CPC": "Código de Procedimiento Civil",
    "CPP": "Código de Procedimiento Penal",
    "COT": "Código Orgánico de Tribunales",
    "CT": "Código del Trabajo",
    "CO": "Código de Comercio",
    "CS": "Código Sanitario",
    "CMin": "Código de Minería",
    "CPr": "Constitución Política de la República",
    "CPR": "Constitución Política de la República",
}

ORDINALES: dict[str, str] = {
    "primero": "1", "primera": "1", "segundo": "2", "segunda": "2",
    "tercero": "3", "tercera": "3", "cuarto": "4", "cuarta": "4",
    "quinto": "5", "quinta": "5", "sexto": "6", "sexta": "6",
    "séptimo": "7", "septimo": "7", "séptima": "7", "septima": "7",
    "octavo": "8", "octava": "8", "noveno": "9", "novena": "9",
    "décimo": "10", "decimo": "10", "décima": "10", "decima": "10",
    "final": "final",
    # "transitorio" NO es inciso: el inciso transitorio no existe; el transitorio
    # es un artículo aparte (véase _RE_ART_TRANSITORIO).
}

_CUERPO_ALT = "|".join(rx for rx, _ in sorted(CUERPOS, key=lambda c: -len(c[0])))
_LISTA_ART = r"[\d]+[º°]?(?:\s*(?:,|\sy\s)\s*[\d]+[º°]?)*"
_INCISO = r"(?:primero|primera|segundo|segunda|tercero|tercera|cuarto|cuarta|quinto|quinta|sexto|sexta|s[ée]ptim[oa]|octav[oa]|noveno|novena|d[ée]cim[oa]|final|\d+[º°]?)"

_ORDINAL = r"(?:primero|primera|segundo|segunda|tercero|tercera|cuarto|cuarta|quinto|quinta|sexto|sexta|s[ée]ptim[oa]|octav[oa]|noveno|novena|d[ée]cim[oa]|[úu]ltimo|\d+[º°]?)"

# "artículo primero transitorio" / "artículos 2° y 3° transitorios"
_RE_ART_TRANSITORIO = re.compile(
    rf"\bart[íi]culo(s)?\s+(?P<ordinarios>{_ORDINAL}(?:\s*(?:,|\sy\s)\s*{_ORDINAL})*)"
    rf"\s+transitorio(s)?\b",
    re.IGNORECASE)

# "el artículo antes citado" / "dicha disposición" / "la norma referida"
_RE_CORREFERENCIA = re.compile(
    r"\b(?:el|la|los|las)\s+(?:art[íi]culo|norma|disposici[óo]n|cuerpo\s+legal)\s+"
    r"(?:antes\s+citad[oa]|precedente|referid[oa]|mencionad[oa])\b"
    r"|\bdich[oa]\s+(?:art[íi]culo|norma|disposici[óo]n)\b",
    re.IGNORECASE)

# artículo 148 / arts. 1705 y 1712 / artículo 19, N° 24  (+ cuerpo completo o abreviado)
_ART_BASE = r"(?:art[íi]culos?|arts?\.)"

_RE_ART_CUERPO = re.compile(
    rf"\b{_ART_BASE}\s+(?P<articulos>{_LISTA_ART})"
    rf"(?:\s*,?\s*(?:N[°º]\s*)?(?P<numero_garantia>\d+))?"
    rf"(?:\s*,?\s*(?:en\s+su\s+)?inciso\s+(?:N?[°º]?\s*)?(?P<inciso>{_INCISO}))?"
    rf"\s*,?\s*(?:de\s+la\s+|del?\s+)"
    rf"(?:mism[oa]\s+|referido\s+|precitad[oa]\s+|mencionad[oa]\s+)?"
    rf"(?P<cuerpo>{_CUERPO_ALT})\b",
    re.IGNORECASE)

_RE_ART_ABREV = re.compile(
    rf"\b{_ART_BASE}\s+(?P<articulos>{_LISTA_ART})"
    rf"(?:\s*,?\s*(?:N[°º]\s*)?(?P<numero_garantia>\d+))?"
    rf"(?:\s*,?\s*(?:en\s+su\s+)?inciso\s+(?:N?[°º]?\s*)?(?P<inciso>{_INCISO}))?"
    rf"\s*,?\s*(?:del?\s+|de\s+la\s+)?"
    rf"(?P<abrev>{'|'.join(sorted(ABREVIATURAS, key=len, reverse=True))})\b",
    re.IGNORECASE)

# Ley N° 19.966 / ley 21453 / DFL N° 1, de 2005 / Decreto Supremo 47, de 2020 / D.S. 14/2022
_RE_NORMA_NUM = re.compile(
    r"\b(?P<tipo>ley(?:\s+org[áa]nica\s+constitucional)?|dfl|decreto\s+con\s+fuerza\s+de\s+ley"
    r"|decreto\s+(?:con\s+fuerza\s+de\s+ley|supremo|supremo\s+exento|exento|ley)|d\.?\s?s\.?|decreto)"
    r"\s*,?\s*(?:N[°º]\s*n?\.?\s*(?:úmero\s+)?|núm\.?\s+|número\s+)?"
    r"(?P<numero>\d{1,3}(?:\.\d{3})+|\d+)"
    r"(?:\s*/\s*(?P<anno>19|20)?(?P<anno2>\d{2}))?"
    r"(?:\s*,?\s*(?:,?\s*de(?:l\s+año)?\s+)(?P<anno_completo>19\d{2}|20\d{2}))?",
    re.IGNORECASE)

# "artículo 24 de la Ley 19.966" (cuerpo numerado como referente)
# OJO: sin f-string aquí; los cuantificadores {1,3} se interpretarían como formato.
_RE_ART_LEY_NUM = re.compile(
    r"\bart[íi]culo\s+(?P<articulo>\d+[º°]?)"
    r"(?:\s*,?\s*(?:en\s+su\s+)?inciso\s+(?:N?[°º]?\s*)?(?P<inciso>" + _INCISO + r"))?"
    r"\s*,?\s*de\s+la\s+(?:ley\s+(?:N[°º]\s*)?)(?P<numero>\d{1,3}(?:\.\d{3})+|\d+)",
    re.IGNORECASE)


def _normalizar_inciso(valor: str | None) -> str | None:
    if not valor:
        return None
    v = valor.strip().lower().rstrip("º°.")
    return ORDINALES.get(v, v)


def _lista_articulos(cadena: str) -> list[str]:
    """'1705 y 1712' → ['1705', '1712']; conserva el ordinal ('2°')."""
    return [a.strip() for a in re.split(r"\s*(?:,|\sy\s)\s*", cadena.strip()) if a.strip()]


def extraer_citas(texto: str) -> list[dict]:
    """Devuelve las citas normativas detectadas en `texto`, en orden de aparición.

    Cada cita: {tipo, cuerpo|numero_norma, articulos[], inciso, literal, posicion}.
    """
    if not texto:
        return []
    plano = re.sub(r"\s+", " ", texto)
    citas: list[dict] = []
    ocupantes: list[tuple[int, int]] = []  # rangos ya capturados por patrones

    def _ocupado(start: int, end: int) -> bool:
        return any(not (end <= a or start >= b) for a, b in ocupantes)

    # 1) artículo + cuerpo legal completo
    for m in _RE_ART_CUERPO.finditer(plano):
        citas.append({
            "tipo": "articulo",
            "cuerpo": _canonico_cuerpo(m.group("cuerpo")),
            "articulos": _lista_articulos(m.group("articulos")),
            "numero_garantia": m.group("numero_garantia"),
            "inciso": _normalizar_inciso(m.group("inciso")),
            "literal": m.group(0).strip(),
            "posicion": m.start(),
        })
        ocupantes.append((m.start(), m.end()))

    # 2) artículo + cuerpo abreviado (art. 64 CPC)
    for m in _RE_ART_ABREV.finditer(plano):
        if _ocupado(m.start(), m.end()):
            continue
        citas.append({
            "tipo": "articulo",
            "cuerpo": ABREVIATURAS[m.group("abrev")],
            "articulos": _lista_articulos(m.group("articulos")),
            "numero_garantia": None,
            "inciso": _normalizar_inciso(m.group("inciso")),
            "literal": m.group(0).strip(),
            "posicion": m.start(),
        })
        ocupantes.append((m.start(), m.end()))

    # 3) artículo de ley numerada ("artículo 24 de la Ley 19.966")
    for m in _RE_ART_LEY_NUM.finditer(plano):
        if _ocupado(m.start(), m.end()):
            continue
        citas.append({
            "tipo": "articulo",
            "cuerpo": f"Ley {m.group('numero')}",
            "articulos": [m.group("articulo")],
            "numero_garantia": None,
            "inciso": _normalizar_inciso(m.group("inciso")),
            "literal": m.group(0).strip(),
            "posicion": m.start(),
        })
        ocupantes.append((m.start(), m.end()))

    # 4) norma numerada sin artículo ("Ley N° 19.966", "D.S. 47/2020")
    # (los rangos ya capturados por 1-3 quedan fuera)
    for m in _RE_NORMA_NUM.finditer(plano):
        if _ocupado(m.start(), m.end()):
            continue
        tipo = re.sub(r"\s+", " ", m.group("tipo").strip()).lower()
        tipo = "decreto con fuerza de ley" if tipo == "dfl" else tipo
        tipo = "decreto supremo" if tipo in ("d.s.", "d s") else tipo
        anno = m.group("anno_completo")
        if not anno and m.group("anno"):
            anno = f"{m.group('anno')}{m.group('anno2')}"
        citas.append({
            "tipo": "norma",
            "clase": tipo,
            "numero": m.group("numero"),
            "anno": anno,
            "articulos": [],
            "inciso": None,
            "literal": m.group(0).strip(),
            "posicion": m.start(),
        })

    citas.sort(key=lambda c: c["posicion"])

    # 5) artículos transitorios ("artículo primero transitorio"): heredan el
    #    cuerpo de la cita anterior del propio documento (si lo hubiera)
    citas = _anexar_transitorios(plano, citas, ocupantes)

    # 6) correferencias ("el artículo antes citado"): se anclan a la cita
    #    inmediatamente anterior del documento, marcadas como inferencia
    citas = _anexar_correferencias(plano, citas, ocupantes)

    citas.sort(key=lambda c: c["posicion"])
    return citas


def _heredar_cuerpo(citas: list[dict], posicion: int) -> str | None:
    """Cuerpo de la última cita concreta que aparece ANTES de `posicion`."""
    previas = [c for c in citas
               if c["posicion"] < posicion and c.get("cuerpo") and not c.get("correferencia_de")]
    return previas[-1]["cuerpo"] if previas else None


def _anexar_transitorios(plano: str, citas: list[dict], ocupantes: list[tuple[int, int]]) -> list[dict]:

    def _ocupado(start: int, end: int) -> bool:
        return any(not (end <= a or start >= b) for a, b in ocupantes)

    out = list(citas)
    for m in _RE_ART_TRANSITORIO.finditer(plano):
        if _ocupado(m.start(), m.end()):
            continue
        nums = [o for o in re.split(r"\s*(?:,|\sy\s)\s*", m.group("ordinarios")) if o]
        ordinarios = [ORDINALES.get(o.strip().lower().rstrip("º°."), o.strip()) for o in nums]
        out.append({
            "tipo": "articulo",
            "cuerpo": _heredar_cuerpo(out, m.start()),
            "articulos": ordinarios,
            "transitorio": True,
            "inciso": None,
            "numero_garantia": None,
            "literal": m.group(0).strip(),
            "posicion": m.start(),
        })
        ocupantes.append((m.start(), m.end()))
    return out


def _anexar_correferencias(plano: str, citas: list[dict], ocupantes: list[tuple[int, int]]) -> list[dict]:

    def _ocupado(start: int, end: int) -> bool:
        return any(not (end <= a or start >= b) for a, b in ocupantes)

    out = list(citas)
    for m in _RE_CORREFERENCIA.finditer(plano):
        if _ocupado(m.start(), m.end()):
            continue
        ancla = next((c for c in reversed(out) if c["posicion"] < m.start()
                      and c.get("cuerpo") and not c.get("correferencia_de")), None)
        if not ancla:
            continue  # sin referente previo: no se puede inferir con honestidad
        out.append({
            "tipo": "articulo",
            "cuerpo": ancla["cuerpo"],
            "articulos": list(ancla["articulos"]),
            "inciso": ancla.get("inciso"),
            "numero_garantia": None,
            "correferencia_de": ancla["literal"],
            "literal": m.group(0).strip(),
            "posicion": m.start(),
        })
        ocupantes.append((m.start(), m.end()))
    return out


def _canonico_cuerpo(texto: str) -> str:
    """Mapea la forma detectada ('Codigo civil', 'CÓDIGO CIVIL') al nombre canónico."""
    for rx, canon in CUERPOS:
        if re.fullmatch(rx, texto.strip(), re.IGNORECASE):
            return canon
    return texto.strip()


# --- Corte forense de articulado (texto plano de una norma ya descargada) -----

# LeyChile marca los artículos de dos formas según la época de digitalización:
# 'Artículo 2°.' (obtxml reciente) o 'Art. 2291.' (códigos antiguos).
_RE_CAB_ARTICULO = re.compile(
    r"\b(?:art[íi]culo|art\.)\s+([0-9]+[º°.]?(?:\s*(?:bis|ter|quater|quinquies|sexies))?)",
    re.IGNORECASE)


def _patron_articulo(articulo: str) -> re.Pattern:
    """Patrón de cabecera para el artículo pedido.

    Formatos reales LeyChile: 'Artículo 2°.', 'Art. 2291.', 'Artículo 2º'.
    Pedir el artículo 2 NO debe traer el 20 ni el 21 (el 'º'/'°' es carácter
    de palabra: no basta con \\b tras el número).
    """
    num = articulo.strip().rstrip("º°.")
    sufijo = ""
    m = re.search(r"\s*(bis|ter|quater|quinquies|sexies)$", articulo.strip(), re.IGNORECASE)
    if m:
        sufijo = rf"\s*{m.group(1)}"
    return re.compile(
        rf"\b(?:art[íi]culo|art\.)\s+{re.escape(num)}{sufijo}[º°.]?(?![\dº°])",
        re.IGNORECASE)


def extraer_articulo(texto_norma: str, articulo: str, inciso: str | None = None) -> dict:
    """Extrae el texto del `articulo` (y opcionalmente de un `inciso`) de una norma.

    `texto_norma` es el cuerpo plano previamente descargado (p. ej. desde la
    caché `textos` o el XML oficial de LeyChile). No realiza llamadas de red.
    """
    if not texto_norma:
        return {"ok": False, "error": "Texto de la norma vacío."}
    patron = _patron_articulo(articulo)
    m = patron.search(texto_norma)
    if not m:
        return {"ok": False,
                "error": f"No se encontró la cabecera 'Artículo {articulo}' en el texto de la norma."}
    corte = _RE_CAB_ARTICULO.search(texto_norma, m.end())
    cuerpo = texto_norma[m.start(): corte.start() if corte else len(texto_norma)].strip()

    # Incisos: LeyChile los marca explícitamente ("Inciso primero.") o son
    # párrafos corridos tras el encabezado del artículo.
    marcas = list(re.finditer(
        rf"\binciso\s+(?P<inciso>{_INCISO})\b\s*[.:—-]?", cuerpo, re.IGNORECASE))
    incisos: list[dict] = []
    for i, mk in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(cuerpo)
        incisos.append({"inciso": _normalizar_inciso(mk.group("inciso")),
                        "texto": cuerpo[mk.end():fin].strip() or cuerpo[mk.start():fin].strip()})
    if not incisos:
        # Formato antiguo LeyChile: tras 'Art. N.', los incisos son párrafos
        # corridos separados por una sangría (p. ej. 5 espacios) o línea en
        # blanco. El PRIMER párrafo (junto al número) ES el inciso primero.
        parrafos = [re.sub(r"\s*\n\s*", " ", p).strip()
                    for p in re.split(r"\n[ \t]{2,}|\n\s*\n", cuerpo) if p.strip()]
        if len(parrafos) > 1:
            incisos = [{"inciso": str(i + 1), "texto": p} for i, p in enumerate(parrafos)]

    if inciso:
        objetivo = _normalizar_inciso(inciso)
        hallados = [i for i in incisos if i.get("inciso") == objetivo]
        if not hallados:
            return {"ok": True, "articulo": articulo, "inciso_solicitado": inciso,
                    "advertencia": f"El artículo {articulo} no contiene un inciso '{inciso}' rotulado; "
                                   "se devuelve el texto íntegro del artículo.",
                    "texto_articulo": cuerpo, "incisos": incisos}
        return {"ok": True, "articulo": articulo, "inciso": objetivo,
                "texto_inciso": hallados[0]["texto"], "texto_articulo": cuerpo}

    return {"ok": True, "articulo": articulo, "texto_articulo": cuerpo, "incisos": incisos}
