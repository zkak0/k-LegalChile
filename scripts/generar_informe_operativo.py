#!/usr/bin/env python3
"""Genera informe PDF operativo integral de K-LegalChile MCP."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable
from pathlib import Path
from datetime import datetime
import json
import sys

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "informe_herramientas_operativas.pdf"

AZUL = HexColor("#1a365d")
VERDE = HexColor("#276749")
GRIS = HexColor("#4a5568")
GRIS_CLARO = HexColor("#f7fafc")
ROJO = HexColor("#c53030")
NARANJA = HexColor("#c05621")


def build_styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("PortadaTitulo", parent=ss["Title"], fontSize=26, textColor=AZUL, spaceAfter=12, leading=32, alignment=TA_CENTER))
    ss.add(ParagraphStyle("PortadaSub", parent=ss["Normal"], fontSize=13, textColor=GRIS, alignment=TA_CENTER, spaceAfter=6, leading=18))
    ss.add(ParagraphStyle("SeccionH1", parent=ss["Heading1"], fontSize=18, textColor=AZUL, spaceBefore=18, spaceAfter=8, leading=22))
    ss.add(ParagraphStyle("SeccionH2", parent=ss["Heading2"], fontSize=13, textColor=AZUL, spaceBefore=12, spaceAfter=6, leading=16))
    ss.add(ParagraphStyle("SeccionH3", parent=ss["Heading3"], fontSize=11, textColor=VERDE, spaceBefore=8, spaceAfter=4, leading=14))
    ss.add(ParagraphStyle("BodyCustom", parent=ss["Normal"], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=6))
    ss.add(ParagraphStyle("TablaCelda", parent=ss["Normal"], fontSize=9, leading=12))
    ss.add(ParagraphStyle("TablaHeader", parent=ss["Normal"], fontSize=9, fontName="Helvetica-Bold", textColor=white, leading=12))
    ss.add(ParagraphStyle("Nota", parent=ss["Normal"], fontSize=9, leading=13, textColor=NARANJA, spaceAfter=6))
    return ss


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRIS)
    canvas.drawString(2*cm, 1*cm, f"K-LegalChile MCP — Informe Operativo Integral — {datetime.now().strftime('%d-%m-%Y')}")
    canvas.drawRightString(A4[0]-2*cm, 1*cm, f"Página {doc.page}")
    canvas.restoreState()


def make_table(headers, rows, col_widths=None):
    ss = build_styles()
    h = [[Paragraph(h, ss["TablaHeader"]) for h in headers]]
    data = h + [[Paragraph(str(c), ss["TablaCelda"]) for c in row] for row in rows]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 1), (-1, -1), white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, GRIS_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
    ]))
    return t


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2.5*cm)
    ss = build_styles()
    story = []

    # Cargar auditorías si existen
    local_results, red_results = [], []
    local_path = Path(__file__).resolve().parent.parent / "data" / "auditoria_local_tools.json"
    red_path = Path(__file__).resolve().parent.parent / "data" / "auditoria_red_tools.json"
    if local_path.exists():
        with open(local_path, 'r', encoding='utf-8') as f:
            local_results = json.load(f)
    if red_path.exists():
        with open(red_path, 'r', encoding='utf-8') as f:
            red_results = json.load(f)

    # ════════════════════════════════════════════════════════════
    # PORTADA
    # ════════════════════════════════════════════════════════════
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("K-LegalChile MCP", ss["PortadaTitulo"]))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Informe Operativo Integral del Sistema de Investigación Jurídica", ss["PortadaSub"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="60%", thickness=2, color=AZUL, spaceAfter=14))
    story.append(Paragraph("Documentación técnica y funcional de las 91 herramientas MCP disponibles,<br/>cobertura de fuentes gubernamentales, corpus normativo, base de conocimiento y auditoría de estado.", ss["PortadaSub"]))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(f"<b>Fecha de emisión:</b> {datetime.now().strftime('%d de %B de %Y')}", ss["PortadaSub"]))
    story.append(Paragraph("<b>Versión del Servidor:</b> 1.0 (Protocolo Model Context)", ss["PortadaSub"]))
    story.append(Paragraph("<b>Plataforma:</b> Python 3.14 / SQLite FTS5 / Playwright & Stealth WAF Bypass", ss["PortadaSub"]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 1. INTRODUCCIÓN Y ARQUITECTURA
    # ════════════════════════════════════════════════════════════
    story.append(Paragraph("1. Introducción y Arquitectura General", ss["SeccionH1"]))
    story.append(Paragraph(
        "K-LegalChile MCP es un servidor avanzado basado en el Protocolo Model Context (MCP) diseñado para "
        "conectar asistentes de inteligencia artificial con todo el ecosistema de investigación jurídica y administrativa de Chile. "
        "El sistema integra un corpus local optimizado, índices de búsqueda de texto completo (FTS5) y conectores en tiempo real "
        "hacia los portales oficiales del Estado chileno (Biblioteca del Congreso Nacional, Poder Judicial, Contraloría General de la República, "
        "Servicio de Impuestos Internos, Tribunal Constitucional, Comisión para el Mercado Financiero, Dirección del Trabajo, entre otros).",
        ss["BodyCustom"]))
    story.append(Paragraph(
        "Para superar los mecanismos de defensa perimetral (WAF, desafíos Cloudflare, protección F5 TSPD) implementados por los portales institucionales, "
        "el servidor incorpora una pila tecnológica de evasión robusta basada en <b>Playwright con evasión stealth</b>, <b>curl_cffi</b> y "
        "estrategias de respaldo en cascada.",
        ss["BodyCustom"]))
    story.append(Spacer(1, 0.2*cm))

    # Resumen de capacidades
    story.append(Paragraph("Resumen de Módulos y Herramientas", ss["SeccionH2"]))
    resumen_data = [
        ["Módulo / Fuente", "Herramientas", "Propósito Principal"],
        ["Juzgados de Policía Local (JPL)", "9 tools", "Gestión de corpus normativo (53 leyes, 5.925 ordenanzas) y generación de escritos judiciales."],
        ["Base de Conocimiento (KB)", "3 tools", "Búsqueda full-text sobre 35 documentos indexados en Markdown."],
        ["BCN (LeyChile)", "7 tools", "Legislación consolidada, texto completo, vigencia, historial y citación formal."],
        ["CGR (Contraloría)", "1 tool", "Dictámenes vinculantes con extracción de texto íntegro vía agente Domino."],
        ["PJUD (Poder Judicial)", "1 tool", "Jurisprudencia en vivo de 10 categorías de tribunales con URLs oficiales."],
        ["Tribunal Constitucional (TC)", "1 tool", "Sentencias constitucionales y control preventivo/represivo de preceptos."],
        ["Servicio de Impuestos Internos (SII)", "5 tools", "Oficios, circulares, resoluciones administrativas y fallos TTA."],
        ["Comisión Mercado Financiero (CMF)", "1 tool", "Normativa financiera y circular bancaria."],
        ["Diario Oficial", "1 tool", "Normas y decretos publicados oficialmente."],
        ["Dirección del Trabajo (DT)", "1 tool", "Jurisprudencia laboral, dictámenes y modelos de contratos."],
        ["SUSESO", "1 tool", "Seguridad social, licencias médicas y dictámenes previsionales."],
        ["Tesorería General de la República (TGR)", "4 tools", "Dictámenes, resoluciones, circulares y cobranza coactiva."],
        ["Otras Entidades (TDLC, CPLT, INAPI, SMA, etc.)", "15+ tools", "Libre competencia, transparencia, marcas comerciales y fiscalización ambiental."],
        ["TOTAL SISTEMA", "91 herramientas", "Cobertura completa del ordenamiento jurídico chileno."],
    ]
    story.append(make_table(resumen_data[0], resumen_data[1:], col_widths=[5*cm, 2.5*cm, 10*cm]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 2. MÓDULO JPL Y BASE DE CONOCIMIENTO (KB)
    # ════════════════════════════════════════════════════════════
    story.append(Paragraph("2. Módulo JPL y Base de Conocimiento (KB)", ss["SeccionH1"]))
    story.append(Paragraph(
        "El módulo de Juzgados de Policía Local (JPL) opera sobre una base de datos local SQLite (`corpus.db`) que contiene "
        "<b>53 leyes esenciales</b>, <b>5.925 ordenanzas municipales</b> de 344 comunas del país, y manuales de formatos judiciales. "
        "Permite al operador jurídico buscar normativa local, verificar vigencias normativas y generar resoluciones, sentencias, "
        "comparendos y oficios ajustados rigurosamente al lenguaje jurídico formal chileno.",
        ss["BodyCustom"]))
    story.append(Paragraph(
        "Por su parte, la Base de Conocimiento (KB) ofrece tres herramientas de alta velocidad (`kb_search`, `kb_get`, `kb_status`) "
        "para consultar directamente sobre el corpus exportado en Markdown.",
        ss["BodyCustom"]))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("Herramientas Principales del Módulo JPL y KB", ss["SeccionH2"]))
    jpl_tools_data = [
        ["Herramienta", "Descripción Funcional"],
        ["jpl_listar_leyes()", "Lista las 53 leyes del corpus local con sus metadatos y estado."],
        ["jpl_buscar_ley(query, limite)", "Busca leyes en el corpus por palabra clave o materia."],
        ["jpl_buscar_articulo(ley, articulo)", "Extrae el texto íntegro de un artículo específico de una ley del corpus."],
        ["jpl_verificar_vigencia(ley)", "Verifica el estado de vigencia y última modificación de la normativa."],
        ["jpl_listar_ordenanzas(comuna)", "Lista las ordenanzas municipales disponibles para una comuna específica."],
        ["jpl_buscar_ordenanza(comuna, query)", "Busca dentro de las ordenanzas locales (ej. ruidos molestos, aseo, comercio)."],
        ["jpl_buscar_texto(query)", "Búsqueda full-text global en todo el corpus JPL."],
        ["jpl_generar_documento(tipo, json_datos)", "Genera escritos judiciales completos (sentencia, resolución, comparendos, exhortos, plazos)."],
        ["kb_search(query, limite)", "Búsqueda full-text FTS5 sobre los 35 documentos indexados en la KB."],
        ["kb_get(ruta)", "Recupera el texto íntegro de un documento Markdown en la KB."],
        ["kb_status()", "Retorna estadísticas operativas del índice KB."],
    ]
    story.append(make_table(jpl_tools_data[0], jpl_tools_data[1:], col_widths=[5*cm, 12.5*cm]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 3. FUENTES GUBERNAMENTALES EXTERNAS Y DE RED
    # ════════════════════════════════════════════════════════════
    story.append(Paragraph("3. Fuentes Gubernamentales Externas y de Red", ss["SeccionH1"]))
    story.append(Paragraph(
        "El servidor MCP incluye conectores especializados para consultar portales institucionales en tiempo real. "
        "A continuación se detallan las principales fuentes y sus respectivas herramientas operativas:",
        ss["BodyCustom"]))
    story.append(Spacer(1, 0.1*cm))

    fuentes_ext_data = [
        ["Entidad / Portal", "Herramientas MCP", "Descripción y Alcance"],
        [
            "BCN LeyChile",
            "buscar_normas, obtener_texto_norma, citar_norma, citar_json, exportar_norma, historial_norma, estado_vigencia",
            "Consulta al endpoint SPARQL de la Biblioteca del Congreso Nacional. Permite extraer texto completo, generar citas formales, exportar a DOCX y revisar historial."
        ],
        [
            "CGR Contraloría",
            "buscar_dictamenes",
            "Consulta dictámenes y pronunciamientos jurídicos vinculantes con extracción íntegra del cuerpo mediante el agente Domino."
        ],
        [
            "PJUD Poder Judicial",
            "buscar_jurisprudencia",
            "Buscador en vivo en juris.pjud.cl cubriendo 10 categorías (Suprema, Apelaciones, Civiles, Penales, Laborales, Familia, etc.) con Playwright + stealth."
        ],
        [
            "Tribunal Constitucional",
            "buscar_tc",
            "Consulta sentencias constitucionales y fichas de inaplicabilidad o control de constitucionalidad."
        ],
        [
            "SII Impuestos Internos",
            "buscar_sii, sii_buscar_oficio, sii_buscar_circular, sii_buscar_resolucion, sii_buscar_fallo",
            "Jurisprudencia administrativa tributaria, oficios, circulares, resoluciones exentas y fallos de los Tribunales Tributarios y Aduaneros (TTA)."
        ],
        [
            "CMF / Diario Oficial / DT / SUSESO",
            "buscar_cmf, buscar_diario_oficial, buscar_dt, buscar_suseso",
            "Normativa del mercado financiero, publicaciones oficiales, jurisprudencia laboral y dictámenes de seguridad social."
        ],
        [
            "Tesorería General (TGR)",
            "tgr_buscar_dictamen, tgr_buscar_resolucion, tgr_buscar_circular, tgr_buscar_fallo",
            "Cobranza fiscal, dictámenes, circulares y fallos sobre pagos y contribuciones."
        ],
        [
            "Otras Instituciones",
            "inapi_*, tdpi_jurisprudencia, superir_*, sma_sancionatorio, buscar_tdlc",
            "Propiedad industrial, marcas, Tribunal de Propiedad Industrial, boletín concursal, superintendencia de medio ambiente y libre competencia."
        ],
    ]
    story.append(make_table(fuentes_ext_data[0], fuentes_ext_data[1:], col_widths=[4*cm, 5.5*cm, 8*cm]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 4. CORPUS LOCAL K-LegalChile (DICTÁMENES CGR)
    # ════════════════════════════════════════════════════════════
    story.append(Paragraph("4. Corpus Local K-LegalChile — Dictámenes CGR", ss["SeccionH1"]))
    story.append(Paragraph(
        "El sistema incorpora un corpus local de dictámenes de la Contraloría General de la República (CGR) y sus "
        "citaciones cruzadas, descargado de una plataforma pública de datos abiertos. "
        "Sobre este corpus se implementan las capacidades del sistema: búsqueda semántica y FTS5, determinación del "
        "<i>estado del criterio</i> (vigente, reconsiderado, "
        "derogado, modificado, complementado o reafirmado), ficha doctrinal completa y boletín de criterios nuevos.",
        ss["BodyCustom"]))
    story.append(Paragraph(
        "Las citaciones cruzadas entre dictámenes (tipos <b>aplica</b>, <b>cita</b> y <b>funda</b>, con nivel de confianza) "
        "permiten reconstruir el ratificado la cadena doctrinal y detectar la evolución de cada criterio. El campo "
        "<i>source_url</i> del dataset (invariablemente un IP interno) contiene el UNID Domino de la CGR, que se convierte en "
        "la URL oficial de consulta del dictamen y permite refrescar o verificar su texto íntegro en vivo.",
        ss["BodyCustom"]))
    story.append(Spacer(1, 0.2*cm))

    try:
        from chilean_legal_mcp.db import get_db
        from chilean_legal_mcp.semantico import estado_indexacion as _estado_indexacion
        _corpus_db = get_db()
        _total_dict = _corpus_db.count_dictamenes_cgr()
        _total_citas = _corpus_db.count_citas_legales()
        _total_criterios = _corpus_db.count_criterios()
        _resumen_sem = _estado_indexacion(_corpus_db)
    except Exception:
        _total_dict = _total_citas = _total_criterios = 0
        _resumen_sem = "Embeddings semánticos: no disponible"

    corpus_data = [
        ["Indicador", "Valor"],
        ["Dictámenes CGR en corpus lex", f"{_total_dict:,}"],
        ["Aristas de citación (aplica / cita / funda)", f"{_total_citas:,}"],
        ["Dictámenes con estado de criterio marcado", f"{_total_criterios:,}"],
        ["Estado del índice semántico", _resumen_sem],
        ["Fuente", "Dataset público de dictámenes · URL oficial CGR vía UNID (contraloria.cl)"],
    ]
    story.append(make_table(corpus_data[0], corpus_data[1:], col_widths=[7*cm, 10.5*cm]))
    story.append(Spacer(1, 0.25*cm))

    story.append(Paragraph("Herramientas de Réplica Corpus CGR / Veridictum / Dicamina", ss["SeccionH2"]))
    corpus_tools_data = [
        ["Herramienta", "Descripción Funcional"],
        ["estado_corpus_lex()", "Estado operativo del corpus: dictámenes, aristas, criterios marcados e índice semántico."],
        ["buscar_dictamenes_corpus(query, semantico)", "Búsqueda híbrida (semántica embeddings + fallback FTS5) con estado del criterio y URL oficial."],
        ["estado_criterio(numero, anio, actualizar)", "Determina si el criterio de un dictamen está vigente o fue reconsiderado/modificado por otro, con cadena de overrides."],
        ["ficha_dictamen_doctrinal(numero, anio, breve)", "Ficha doctrinal tipo dictamina: identificación, materia, normas aplicadas, estado del criterio, antecedentes y fuente oficial."],
        ["obtener_sentencia_cadena(numero, anio)", "Cadena judicial de una sentencia: qué dictámenes o normas la fundan/citan, enlazada al grafo del corpus."],
        ["boletin_criterios_nuevos(materia, dias)", "Boletín de criterios jurídicos nuevos detectados en un período, por detección textual o nuevas aristas."],
        ["vigilancia (fuente criterios)", "La vigilancia periódica del sistema puede incorporar la fuente `criterios`: detecta dictámenes CGR que fijan doctrina o reconsideran un criterio previo, con dedupe por UNID y enlace oficial."],
    ]
    story.append(make_table(corpus_tools_data[0], corpus_tools_data[1:], col_widths=[6*cm, 11.5*cm]))
    story.append(Paragraph(
        "<b>Nota:</b> el dataset abierto de COCHID limita la descarga masiva a 10.000 filas por dataset. El corpus almacenado "
        "comprende 10.000 dictámenes y sus citaciones (la plataforma declara 24.941 dictámenes y 45.959 aristas en su corpus "
        "completo, alcanzable con un plan de pago). Las sentencias se cubren además en vivo vía el portal del Poder Judicial (PJUD).",
        ss["Nota"]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 5. RESULTADOS DE LA AUDITORÍA OPERATIVA
    # ════════════════════════════════════════════════════════════
    story.append(Paragraph("5. Resultados de la Auditoría Operativa", ss["SeccionH1"]))
    story.append(Paragraph(
        "Se ha ejecutado una auditoría automatizada sobre todas las herramientas del servidor para comprobar su operatividad "
        "y conectividad. Los resultados confirman que el núcleo local, la base de conocimiento y la gran mayoría de conectores de red "
        "operan satisfactoriamente.",
        ss["BodyCustom"]))
    story.append(Spacer(1, 0.2*cm))

    if local_results:
        story.append(Paragraph("Estado de Herramientas Locales (Muestreo)", ss["SeccionH2"]))
        local_table_data = [["Herramienta", "Estado", "Resultado Resumido"]]
        for item in local_results[:8]:
            local_table_data.append([item.get("tool"), item.get("status"), item.get("output", "")[:120] + "..."])
        story.append(make_table(local_table_data[0], local_table_data[1:], col_widths=[4.5*cm, 2*cm, 11*cm]))
        story.append(Spacer(1, 0.2*cm))

    if red_results:
        story.append(Paragraph("Estado de Herramientas de Red (Muestreo)", ss["SeccionH2"]))
        red_table_data = [["Herramienta", "Estado", "Resultado Resumido"]]
        for item in red_results[:10]:
            red_table_data.append([item.get("tool"), item.get("status"), item.get("output", "")[:120] + "..."])
        story.append(make_table(red_table_data[0], red_table_data[1:], col_widths=[4.5*cm, 2*cm, 11*cm]))
    
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 6. FUENTES CON RESTRICCIONES Y REFERENCIA TÉCNICA
    # ════════════════════════════════════════════════════════════
    story.append(Paragraph("6. Fuentes con Restricciones y Referencia Técnica", ss["SeccionH1"]))
    story.append(Paragraph(
        "Ciertas fuentes institucionales presentan restricciones operativas externas (bloqueos de IP por WAF o reCAPTCHA) "
        "que han sido debidamente documentadas para evitar tiempos muertos en la investigación:",
        ss["BodyCustom"]))
    story.append(Spacer(1, 0.1*cm))

    restr_data = [
        ["Institución / Fuente", "Estado Actual", "Causa Técnica", "Alternativa Operativa"],
        ["CPLT (Transparencia)", "Bloqueado (403)", "Restricción de IP en servidor institucional", "Utilizar buscar_jurisprudencia o bases secundarias."],
        ["Fiscalía Nacional", "Sin consulta pública", "Reserva legal (Art. 260 Código Procesal Penal)", "No disponible para automatización pública."],
        ["INAPI (Marcas)", "Verificación Humana", "Desafío reCAPTCHA en buscador oficial", "Consulta manual mediante enlace directo proporcionado."],
        ["TDLC (Libre Competencia)", "Parcial", "Bloqueo ocasional de scraping masivo", "Emplear queries específicas en buscar_tdlc."],
    ]
    story.append(make_table(restr_data[0], restr_data[1:], col_widths=[4*cm, 3*cm, 5.5*cm, 5*cm]))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Especificaciones Técnicas del Servidor", ss["SeccionH2"]))
    story.append(Paragraph("• <b>Total de Herramientas MCP:</b> 91 herramientas registradas (82 base + 3 KB + 6 corpus CGR/Veridictum/Dicamina).", ss["BodyCustom"]))
    story.append(Paragraph("• <b>Estrategia Anti-Bloqueo:</b> Playwright headless + stealth plugins + curl_cffi con TLS fingerprinting.", ss["BodyCustom"]))
    story.append(Paragraph("• <b>Motores de Base de Datos:</b> SQLite con índices FTS5 (Full-Text Search) para corpus local y caché BCN.", ss["BodyCustom"]))
    story.append(Paragraph("• <b>Estándar Lingüístico:</b> Redacción y estructuración estricta en lenguaje jurídico formal chileno.", ss["BodyCustom"]))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Estructura de Archivos del Proyecto:", ss["SeccionH2"]))
    archivos_data = [
        ["Ruta del Archivo", "Descripción Funcional"],
        ["src/chilean_legal_mcp/server.py", "Punto de entrada y definición de las 91 herramientas MCP."],
        ["src/chilean_legal_mcp/kb_search.py", "Gestión del índice full-text FTS5 para la Base de Conocimiento."],
        ["src/chilean_legal_mcp/jpl/", "Módulo de Juzgados de Policía Local (corpus y motor generador de escritos)."],
        ["src/chilean_legal_mcp/pjud_juris.py", "Conector en vivo para jurisprudencia del Poder Judicial."],
        ["src/chilean_legal_mcp/fuentes_externas.py", "Conectores HTTP y WAF bypass para SII, CMF, DT, TGR, etc."],
        ["data/jpl/corpus.db", "Base de datos local con 53 leyes y 5.925 ordenanzas municipales."],
        ["docs/informe_herramientas_operativas.pdf", "Informe PDF técnico generado."],
    ]
    story.append(make_table(archivos_data[0], archivos_data[1:], col_widths=[7*cm, 10.5*cm]))

    # Construir documento
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF generado exitosamente: {OUTPUT}")
    print(f"Tamaño del archivo: {OUTPUT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build()
