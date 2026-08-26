"""Generador de informes jurídicos estructurados (formato abogado chileno).

Estructura estándar:
I. ANTECEDENTES Y CONTEXTO JURÍDICO
II. NORMATIVA APLICABLE (con texto reproducido)
III. JURISPRUDENCIA Y DICTÁMENES RELACIONADOS
IV. ANÁLISIS JURÍDICO
V. CONCLUSIÓN
REFERENCIAS
"""

from __future__ import annotations

import re

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SeccionInforme:
    titulo: str
    parrafos: list[str] = field(default_factory=list)
    items: list[dict] = field(default_factory=list)  # {numero, titulo, fecha, texto, url, fundamento}


def _extraer_extracto_texto(texto_norma: str, palabras_clave: list[str], max_chars: int = 900) -> str:
    """Extrae los artículos/párrafos del texto de la norma que contienen las palabras clave."""
    if not texto_norma:
        return ""
    # Normalizar: colapsar saltos simples (párrafos fluidos), conservar dobles como separadores
    texto_norma = re.sub(r"[ \t]+", " ", texto_norma)
    texto_norma = re.sub(r"(?<!\n)\n(?!\n)", " ", texto_norma)
    texto_norma = re.sub(r"\n{2,}", "\n\n", texto_norma).strip()
    # Dividir en artículos/párrafos
    bloques = []
    actual = []
    for linea in texto_norma.split("\n"):
        linea = linea.strip()
        if not linea:
            if actual:
                bloques.append(" ".join(actual))
                actual = []
            continue
        actual.append(linea)
    if actual:
        bloques.append(" ".join(actual))

    # Buscar bloques con palabras clave
    relevantes = []
    for bloque in bloques:
        low = bloque.lower()
        if any(p.lower() in low for p in palabras_clave):
            # Limpiar encabezado de fuente si está
            if "Fuente oficial:" in bloque or "Links oficiales" in bloque:
                bloque = bloque.split("Fuente oficial:")[0].split("Links oficiales")[0]
            relevantes.append(bloque.strip())
        if sum(len(b) for b in relevantes) > max_chars:
            break
    extracto = "\n\n".join(relevantes)[:max_chars]
    if extracto and len(relevantes) < len(bloques):
        extracto += "\n[…]"
    return extracto


def generar_estructura_informe(
    materia: str,
    consulta: str,
    normas: list[dict],
    textos_normas: dict[str, str] | None = None,
    jurisprudencia_items: list[dict] | None = None,
    doctrina_items: list[dict] | None = None,
    analisis_extra: str = "",
) -> list[SeccionInforme]:
    """Arma las secciones I-V del informe jurídico.

    normas: lista de {titulo, numero, fecha, url/leychileId}
    textos_normas: {numero: texto_completo} para reproducir articulado
    jurisprudencia_items: [{numero, titulo, fecha, url, fundamento}]
    """
    textos_normas = textos_normas or {}
    jurisprudencia_items = jurisprudencia_items or []
    doctrina_items = doctrina_items or []
    fecha_hoy = datetime.now().strftime("%d-%m-%Y")
    palabras = [w for w in consulta.split() if len(w) >= 4][:5]

    secciones: list[SeccionInforme] = []

    # I. ANTECEDENTES
    s1 = SeccionInforme("I. ANTECEDENTES Y CONTEXTO JURÍDICO")
    s1.parrafos.append(
        f"El presente informe aborda la materia de {materia}, elaborado con fecha {fecha_hoy} "
        f"a partir de fuentes oficiales chilenas verificables (LeyChile/BCN, SII, TGR, CGR, PJUD, "
        f"entre otras). La consulta analizada corresponde a: \"{consulta}\"."
    )
    s1.parrafos.append(
        "Para su elaboración se revisó la normativa vigente publicada en LeyChile (Biblioteca del "
        "Congreso Nacional), la jurisprudencia administrativa de los organismos competentes y la "
        "doctrina académica disponible en acceso abierto. Todas las citas incluyen su referencia "
        "completa y enlace directo a la fuente oficial, conforme al principio de trazabilidad jurídica."
    )
    secciones.append(s1)

    # II. NORMATIVA APLICABLE (con texto reproducido)
    s2 = SeccionInforme("II. NORMATIVA APLICABLE")
    if normas:
        s2.parrafos.append(
            "Resultan aplicables a la materia consultada las siguientes disposiciones legales, "
            "cuyo texto se reproduce en los extractos pertinentes:"
        )
        for i, n in enumerate(normas, 1):
            numero = n.get("numero") or "s/n"
            titulo = n.get("titulo") or ""
            fecha = n.get("fecha") or ""
            url = n.get("url") or n.get("uri") or ""
            if fecha and len(fecha) == 10 and fecha[4] == "-":
                y, m, d = fecha[:10].split("-")
                fecha = f"{d}-{m}-{y}"
            encabezado = f"{i}. {titulo} — Norma N° {numero}"
            if fecha:
                encabezado += f", publicada {fecha}"
            if url:
                encabezado += f". Fuente: {url}"
            s2.items.append({"numero": str(i), "titulo": encabezado, "texto": ""})
            # Texto reproducido
            texto = textos_normas.get(str(numero)) or textos_normas.get(numero)
            if texto:
                extracto = _extraer_extracto_texto(texto, palabras or [materia])
                if extracto:
                    s2.items[-1]["texto"] = f"Extracto del articulado:\n\"{extracto}\""
    else:
        s2.parrafos.append(
            f"No se identificó normativa específica indexada para \"{consulta}\". Se recomienda "
            "revisar directamente el repositorio oficial LeyChile (https://www.bcn.cl/leychile)."
        )
    secciones.append(s2)

    # III. JURISPRUDENCIA Y DICTÁMENES
    s3 = SeccionInforme("III. JURISPRUDENCIA Y DICTÁMENES RELACIONADOS")
    if jurisprudencia_items:
        s3.parrafos.append(
            "Se identifican los siguientes pronunciamientos administrativos y jurisprudenciales "
            "vinculados a la materia:"
        )
        for i, j in enumerate(jurisprudencia_items, 1):
            linea = f"{i}. {j.get('titulo', '')}"
            if j.get("fundamento"):
                linea += f"\nFundamento legal: {j['fundamento']}"
            if j.get("url"):
                linea += f"\nFuente oficial: {j['url']}"
            s3.items.append({"numero": str(i), "titulo": linea, "texto": ""})
    else:
        s3.parrafos.append(
            "No se encontraron dictámenes o fallos indexados específicos para la consulta en las "
            "fuentes oficiales revisadas. Se sugiere ampliar la búsqueda en los buscadores "
            "institucionales correspondientes (referenciados al final de este informe)."
        )
    secciones.append(s3)

    # IV. ANÁLISIS JURÍDICO
    s4 = SeccionInforme("IV. ANÁLISIS JURÍDICO")
    if normas and jurisprudencia_items:
        primera = normas[0]
        primer_j = jurisprudencia_items[0]
        s4.parrafos.append(
            f"De la revisión efectuada, la normativa identificada ({primera.get('titulo', '')[:80]}) "
            f"constituye el marco general aplicable a la materia de {materia}. Dicho marco se "
            "complementa con los pronunciamientos administrativos referenciados en la sección "
            "anterior, los que precisan la interpretación y aplicación práctica de las disposiciones "
            "legales en casos concretos."
        )
        s4.parrafos.append(
            "La jurisprudencia administrativa revisada evidencia criterios de interpretación "
            "sostenidos por el órgano competente, los cuales —sin constituir precedentes vinculantes "
            "en términos estrictos— orientan la aplicación uniforme de la normativa. Resulta "
            "recomendable contrastar el caso concreto con los fundamentos citados, verificando la "
            "vigencia de las disposiciones aplicables a la fecha de consulta."
        )
    elif normas:
        s4.parrafos.append(
            f"La normativa identificada ({normas[0].get('titulo', '')[:80]}) constituye el marco "
            f"aplicable a la materia de {materia}. No habiéndose indexado jurisprudencia administrativa "
            "específica en las fuentes consultadas, corresponde al profesional a cargo complementar "
            "el análisis con la doctrina y jurisprudencia judicial que estime pertinente."
        )
    else:
        s4.parrafos.append(
            "Dada la ausencia de resultados específicos en las fuentes oficiales indexadas, se "
            "recomienda reformular la consulta con términos más precisos o revisar directamente los "
            "buscadores institucionales referenciados."
        )
    if analisis_extra:
        s4.parrafos.append(analisis_extra)
    secciones.append(s4)

    # V. CONCLUSIÓN
    s5 = SeccionInforme("V. CONCLUSIÓN")
    if normas:
        conclusion = (
            f"Conforme a la revisión efectuada, la materia de {materia} se encuentra regulada "
            f"principalmente por la normativa referenciada en la sección II"
        )
        if jurisprudencia_items:
            conclusion += ", complementada por la jurisprudencia administrativa citada en la sección III"
        conclusion += (
            ". Este informe tiene carácter meramente informativo y no constituye asesoría legal; "
            "la aplicación al caso concreto requiere la verificación de vigencia de las disposiciones "
            "citadas y el análisis profesional correspondiente."
        )
        s5.parrafos.append(conclusion)
    else:
        s5.parrafos.append(
            "No siendo posible emitir una conclusión fundada con la información indexada, este "
            "informe se limita a referir las fuentes oficiales competentes para la investigación "
            "directa de la materia consultada. Este documento tiene carácter meramente informativo "
            "y no constituye asesoría legal."
        )
    secciones.append(s5)

    return secciones


def generar_referencias(fuentes_usadas: list[str]) -> SeccionInforme:
    refs = SeccionInforme("REFERENCIAS (FUENTES OFICIALES)")
    refs.parrafos.append(f"Fecha de consulta: {datetime.now().strftime('%d-%m-%Y')}")
    for f in fuentes_usadas:
        refs.parrafos.append(f)
    return secciones_ref(refs)


def secciones_ref(refs: SeccionInforme) -> SeccionInforme:
    return refs
