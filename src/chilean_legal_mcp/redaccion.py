"""Redacción de escritos jurídicos (Fase 4 Magnar libre) — genera borradores .docx/.pdf fundamentados."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .exportar import exportar_docx, exportar_pdf
from .narrativa import encabezado_informe as _narr_encabezado, conclusion_simple as _narr_conclusion

# Tipos de escritos soportados
TIPOS_ESCRITO = {
    "reposicion": "Recurso de Reposición",
    "apelacion": "Recurso de Apelación",
    "queja": "Queja / Reclamo Administrativo",
    "solicitud": "Solicitud / Presentación",
    "contestacion": "Contestación / Escrito de Defensa",
    "medida_cautelar": "Medida Cautelar",
    "proteccion": "Recurso de Protección",
    "amparo": "Recurso de Amparo",
    "inaplicabilidad": "Inaplicabilidad por Inconstitucionalidad",
    "revision": "Recurso de Revisión",
    "otro": "Escrito Jurídico Genérico",
}


def _extraer_citas_de_texto(texto: str) -> list[dict]:
    """Extrae citas legales del texto (Ley N° XXXX, art. X, etc.)."""
    citas = []
    # Ley N° XXXX
    for m in re.finditer(r"Ley\s+N[º°]\s+(\d+(?:\.\d+)?)", texto, re.IGNORECASE):
        citas.append({"tipo": "ley", "numero": m.group(1), "texto": m.group(0)})
    # Artículo X
    for m in re.finditer(r"art[ií]culo\s+(\d+)", texto, re.IGNORECASE):
        citas.append({"tipo": "articulo", "numero": m.group(1), "texto": m.group(0)})
    # DFL / DS / DTO
    for m in re.finditer(r"(D\.?\s*[FLS]\.?\s*N?[º°]?\s*\d+)", texto, re.IGNORECASE):
        citas.append({"tipo": "decreto", "numero": m.group(1), "texto": m.group(0)})
    return citas


def _construir_hechos(hechos: list[str] | str) -> str:
    """Formatea hechos en párrafos numerados."""
    if isinstance(hechos, str):
        hechos = [h.strip() for h in hechos.split("\n") if h.strip()]
    return "\n".join(f"{i+1}º {h}" for i, h in enumerate(hechos))


def _construir_fundamentos(fundamentos: list[dict], query: str) -> str:
    """Construye la sección de fundamentos de derecho a partir de fuentes estructuradas."""
    if not fundamentos:
        return ("FUNDAMENTOS DE DERECHO\n\n"
                "[Pendiente: agregar fundamentos normativos, jurisprudenciales y doctrinarios "
                "basados en la investigación previa. Usar analizar_consulta, buscar_normas, "
                "buscar_jurisprudencia, buscar_dictamenes para obtener material citable.]")

    secciones = ["FUNDAMENTOS DE DERECHO\n"]
    for i, f in enumerate(fundamentos, 1):
        fuente = f.get("fuente", "Fuente no especificada")
        cita = f.get("cita", "")
        texto = f.get("texto", "").strip()
        if not texto:
            continue
        secciones.append(f"{i}º {fuente}")
        if cita:
            secciones.append(f"   Cita: {cita}")
        secciones.append(f"   {texto}")
        secciones.append("")
    return "\n".join(secciones)


def _construir_petitorio(petitorio: list[str] | str) -> str:
    """Formatea el petitorio en numeración romana."""
    if isinstance(petitorio, str):
        petitorio = [p.strip() for p in petitorio.split("\n") if p.strip()]
    romanos = ["PRIMERO", "SEGUNDO", "TERCERO", "CUARTO", "QUINTO", "SEXTO", "SÉPTIMO", "OCTAVO"]
    return "\n".join(f"{romanos[i] if i < len(romanos) else f'{i+1}º'}.- {p}" for i, p in enumerate(petitorio))


def generar_escrito(
    db,
    tipo: str,
    tribunal: str,
    causa_rol: str,
    caratulado: str,
    hechos: list[str] | str,
    fundamentos: list[dict] | None = None,
    petitorio: list[str] | str | None = None,
    abogado: str = "[NOMBRE ABOGADO]",
    rut_abogado: str = "[RUT ABOGADO]",
    email_abogado: str = "[EMAIL ABOGADO]",
    formato: str = "docx",
) -> str:
    """Genera borrador de escrito jurídico en .docx o .pdf.

    Args:
        tipo: uno de TIPOS_ESCRITO (reposicion, apelacion, queja, solicitud, etc.)
        tribunal: ej. "Ilustrísima Corte de Apelaciones de Santiago"
        causa_rol: ej. "Rol N° 12.345-2024"
        caratulado: ej. "FULANO DE TAL c/ EMPRESA S.A."
        hechos: lista de hechos o texto con saltos de línea
        fundamentos: lista de dicts con {fuente, cita, texto} o None
        petitorio: lista de peticiones o texto con saltos de línea
        formato: "docx" o "pdf"
    """
    tipo_norm = tipo.lower().strip()
    titulo_escrito = TIPOS_ESCRITO.get(tipo_norm, TIPOS_ESCRITO["otro"])
    hoy = datetime.now().strftime("%d-%m-%Y")

    # Encabezado
    partes = [
        f"{titulo_escrito.upper()}",
        "",
        f"SEÑOR {tribunal.upper()}",
        "",
        f"{caratulado.upper()}",
        f"{causa_rol}",
        "",
        _narr_encabezado("Escrito generado automáticamente", f"Tipo: {titulo_escrito}", 1),
        "",
    ]

    # Hechos
    partes.append("HECHOS")
    partes.append("")
    partes.append(_construir_hechos(hechos))
    partes.append("")

    # Fundamentos
    partes.append(_construir_fundamentos(fundamentos or [], ""))

    # Petitorio
    if petitorio:
        partes.append("PETITORIO")
        partes.append("")
        partes.append(_construir_petitorio(petitorio))
        partes.append("")

    # Firma
    partes.append(f"Santiago, {hoy}")
    partes.append("")
    partes.append("ATENTAMENTE,")
    partes.append("")
    partes.append(f"__________________________")
    partes.append(f"{abogado}")
    partes.append(f"Abogado — RUT: {rut_abogado}")
    partes.append(f"Email: {email_abogado}")
    partes.append("")

    # Conclusión narrativa
    partes.append(_narr_conclusion(
        f"Borrador de {titulo_escrito.lower()}",
        1,
        "Este es un borrador generado automáticamente. Revisar y completar todos los campos "
        "entre corchetes [ ] antes de presentar. Verificar citas, plazos y competencia."
    ))

    texto_completo = "\n".join(partes)

    # Exportar
    try:
        if formato.lower() == "docx":
            ruta = exportar_docx(
                titulo=f"{titulo_escrito} — {caratulado}",
                texto=texto_completo,
                numero=causa_rol,
                fecha=hoy,
            )
        else:
            ruta = exportar_pdf(
                titulo=f"{titulo_escrito} — {caratulado}",
                texto=texto_completo,
                numero=causa_rol,
                fecha=hoy,
            )
        return f"✅ {titulo_escrito} generado en {formato.upper()}: {ruta}\n\n---\n\n{texto_completo}"
    except Exception as e:
        return f"ERROR generando {formato}: {e}\n\n---\n\n{texto_completo}"


def generar_escrito_desde_investigacion(
    db,
    consulta: str,
    tipo: str = "solicitud",
    tribunal: str = "[TRIBUNAL]",
    causa_rol: str = "[ROL]",
    caratulado: str = "[CARATULADO]",
    formato: str = "docx",
) -> str:
    """Genera escrito a partir de investigación automática en la BD local (normas, casos, dictámenes)."""
    # Usar BD directamente para evitar import circular con server.py
    # 1. Buscar normas en BD local (FTS)
    normas_rows = db.search(consulta, limit=5)
    # 2. Buscar casos en BD local
    casos_rows = db.search_casos(consulta, limit=3)
    # 3. Buscar dictámenes en BD local
    dictamenes_rows = db.search_dictamenes(consulta, limit=3)

    # Construir fundamentos automáticos
    fundamentos = []

    # Extraer de normas
    for r in normas_rows:
        if r.get("numero") and r.get("leychile_id"):
            fundamentos.append({
                "fuente": "Legislación (LeyChile)",
                "cita": f"{r.get('titulo','')} — Ley N° {r.get('numero')} ({r.get('fecha','')}) — https://www.bcn.cl/leychile/navegar?idNorma={r.get('leychile_id')}",
                "texto": "Norma aplicable al asunto consultado."
            })

    # Extraer de casos/jurisprudencia
    for r in casos_rows:
        fundamentos.append({
            "fuente": f"Jurisprudencia ({r.get('organismo','')})",
            "cita": f"{r.get('identificacion','')} — {r.get('url','')}",
            "texto": f"Hechos: {r.get('hechos','')[:200]}... Resolución: {r.get('resolucion','')[:200]}..."
        })

    # Extraer de dictámenes
    for r in dictamenes_rows:
        fundamentos.append({
            "fuente": "Contraloría General de la República",
            "cita": f"Dictamen {r.get('numero','')} — {r.get('titulo','')} — {r.get('url','')}",
            "texto": "Pronunciamiento administrativo vinculante."
        })

    # Hechos genéricos basados en la consulta
    hechos = [
        f"Se consulta sobre: {consulta}",
        "Los antecedentes fácticos y jurídicos se desprenden de la investigación realizada "
        "a través de fuentes oficiales chilenas (LeyChile, PJUD, CGR, TC, SII, etc.)."
    ]

    # Petitorio genérico según tipo
    petitorios_tipo = {
        "reposicion": [
            "Se tenga por interpuesto recurso de reposición en contra de la resolución impugnada",
            "Se sirva revocar la resolución impugnada y dictar nueva en su lugar",
            "En subsidio, se conceda el plazo legal para apelar",
        ],
        "apelacion": [
            "Se tenga por interpuesto recurso de apelación en contra de la sentencia apelada",
            "Se sirva revocar la sentencia apelada y dictar sentencia de reemplazo",
        ],
        "proteccion": [
            "Se acoja el recurso de protección interpuesto",
            "Se deje sin efecto el acto recurrido y se restablezca el estado de derecho",
        ],
        "solicitud": [
            "Se tenga por presentada la solicitud en todos sus términos",
            "Se sirva acceder a lo solicitado en los fundamentos de hecho y de derecho expuestos",
        ],
    }
    petitorio = petitorios_tipo.get(tipo.lower(), petitorios_tipo["solicitud"])

    return generar_escrito(
        db=db,
        tipo=tipo,
        tribunal=tribunal,
        causa_rol=causa_rol,
        caratulado=caratulado,
        hechos=hechos,
        fundamentos=fundamentos,
        petitorio=petitorio,
        formato=formato,
    )


def formatear_escrito_narrativo(resultado: str) -> str:
    """Extrae y formatea solo el texto del escrito (sin la ruta del archivo)."""
    if "---" in resultado:
        partes = resultado.split("---", 1)
        if len(partes) > 1:
            return partes[1].strip()
    return resultado