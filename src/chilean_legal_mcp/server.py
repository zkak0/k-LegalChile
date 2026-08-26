"""Servidor MCP de investigación legal chilena — mejor que Trifolia.

Herramientas (68):
- buscar_normas: legislación con filtros fecha/tipo/materia + paginación offset + FTS body + DD-MM-AAAA.
- obtener_texto_norma: texto completo XML LeyChile con chunk/offset.
- estado_vigencia: VIGENTE/DEROGADA/REFUNDIDA leyendo el encabezado legal oficial renderizado.
- buscar_casos: casos reales parecidos extraídos de documentos oficiales (hechos/resolución).
- guardar_memoria / consultar_memoria / historial_conversacion / registrar_interaccion / resumen_trabajo: memoria persistente del abogado (cerebro local, cache circular 500, retención 30 días).
- buscar_dictamenes: CGR + BCN.
- buscar_jurisprudencia: BCN + CGR + TC + PJUD público.
- buscar_doctrina: artículos (30k) + fallback normas.
- historial_norma: vigencia y relaciones (hasVersion/modifiesTo).
- citar_norma / citar_json: citas texto y JSON con DD-MM-AAAA + URL LeyChile.
- exportar_norma: Word (.docx) y PDF (.pdf) con formato profesional.
- indexar_semantico / buscar_semantico / estado_indexacion: embeddings MiniLM multilingüe (Fase 3).
- generar_escrito / generar_escrito_desde_investigacion / tipos_escrito_disponibles: redacción de escritos jurídicos (Fase 4).
- iniciar_workflow / continuar_workflow / estado_workflow / listar_workflows: prompt multi-etapa planificar→investigar→redactar→autoverificar (Fase 5).
- buscar_scielo / buscar_dt / buscar_diario_oficial / buscar_suseso / buscar_tc / buscar_historia_ley / buscar_sii / buscar_cmf / buscar_tdlc / buscar_cplt / buscar_datos_gob: fuentes sectoriales oficiales.
- buscar_todo: búsqueda multi-fuente paralela real (ThreadPoolExecutor 6 workers).
- vigilancia_crear / vigilancia_listar / vigilancia_ejecutar / vigilancia_historial / vigilancia_marcar_revisados / vigilancia_eliminar / vigilancia_pausar: monitor legal automático (condición en lenguaje natural + fuentes oficiales, dedupe e informe narrativo).
- expediente_indexar / expediente_preguntar / expediente_timeline / expediente_partes / expediente_listar / expediente_eliminar: análisis de expedientes propios (carpeta PDF/DOCX/TXT → FTS5 local, respuestas con citas al documento, línea de tiempo y partes).
- analizar_consulta: informe jurídico estructurado I-V multi-fuente en un solo paso.
- salud_fuentes: verifica conectividad de todos los endpoints oficiales chilenos.
- sii_buscar_oficio / sii_buscar_circular / sii_buscar_resolucion / sii_buscar_fallo: SII oficial (www3/www4.sii.cl + tta.cl).
- tgr_buscar_dictamen / tgr_buscar_resolucion / tgr_buscar_circular / tgr_buscar_fallo: TGR oficial (tesoreria.cl + tgr.gob.cl).
- inapi_buscar_marca / inapi_estados_diarios / tdpi_jurisprudencia: INAPI + TDPI marcas.
- superir_buscar_boletin: Superir — Boletín Concursal (Ley 20.720).
- sma_buscar_sancionatorio: SMA — SNIFA sancionatorio ambiental.
- ayuda_acceso_abogado: todos los links oficiales.
Recursos: norma://{id}, norma://{id}/historial | Prompts: analisis_vigencia, redacta_escrito
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from .contraloria import buscar_cgr
from .db import NormasDB
from .exportar import exportar_docx, exportar_pdf
from . import inapi as _inapi_mod
from . import sii as _sii_mod
from . import sma as _sma_mod
from . import superir as _superir_mod
from . import tgr as _tgr_mod
from .salud_fuentes import verificar_todas as _verificar_fuentes
from .vigencia import estado_vigencia as _estado_vigencia, formatear_vigencia as _formatear_vigencia
from .memoria import (
    registrar_mensaje as _registrar_mensaje,
    guardar_nota as _guardar_nota,
    consultar_memoria as _consultar_memoria,
    historial_reciente as _historial_reciente,
    resumen_trabajo as _resumen_trabajo,
    formatear_memoria as _formatear_memoria,
    formatear_resumen as _formatear_resumen,
)
from .vigilancia import (
    crear_vigilancia as _vig_crear,
    listar_vigilancias as _vig_listar,
    eliminar_vigilancia as _vig_eliminar,
    ejecutar_vigilancia as _vig_ejecutar,
    historial_vigilancia as _vig_historial,
    marcar_revisados as _vig_marcar,
    pausar_o_activar as _vig_pausar,
    formatear_informe_ejecucion as _vig_fmt_informe,
    formatear_listado as _vig_fmt_listado,
    formatear_historial as _vig_fmt_historial,
)
from .expediente import (
    indexar_carpeta as _exp_indexar,
    preguntar as _exp_preguntar,
    timeline as _exp_timeline,
    partes as _exp_partes,
    listar_expedientes as _exp_listar,
    eliminar_expediente as _exp_eliminar,
    formatear_indexacion as _exp_fmt_index,
    formatear_respuesta as _exp_fmt_respuesta,
    formatear_timeline as _exp_fmt_timeline,
    formatear_partes as _exp_fmt_partes,
    formatear_listado as _exp_fmt_listado,
)
from .narrativa import (
    analizar_sentencia_tc as _analizar_sentencia_tc,
    formatear_caso_tc as _formatear_caso_tc,
    limpiar_html as _limpiar_html,
    extraer_noticia as _extraer_noticia,
    formatear_noticia_tgr as _narr_noticia_tgr,
    bloque_item as _narr_bloque_item,
    encabezado_informe as _narr_encabezado,
    conclusion_simple as _narr_conclusion,
)
from .fuentes_externas import buscar_cmf as _buscar_cmf
from .fuentes_externas import buscar_cplt as _buscar_cplt
from .fuentes_externas import buscar_datos_gob as _buscar_datos
from .fuentes_externas import buscar_diario_oficial as _buscar_diario
from .fuentes_externas import buscar_dt as _buscar_dt
from .fuentes_externas import buscar_historia_ley as _buscar_historia
from .fuentes_externas import buscar_scielo as _buscar_scielo
from .fuentes_externas import buscar_sii as _buscar_sii
from .fuentes_externas import buscar_suseso as _buscar_suseso
from .fuentes_externas import buscar_tc as _buscar_tc
from .fuentes_externas import buscar_tdlc as _buscar_tdlc
from .semantico import (
    indexar_semantico as _sem_indexar,
    buscar_semantico as _sem_buscar,
    estado_indexacion as _sem_estado,
    formatear_resultado_semantico as _sem_fmt,
)
from .redaccion import (
    generar_escrito as _red_generar,
    generar_escrito_desde_investigacion as _red_desde_inv,
    TIPOS_ESCRITO,
)
from .workflow import (
    iniciar_workflow as _wf_iniciar,
    continuar_workflow as _wf_continuar,
    estado_workflow as _wf_estado,
    listar_workflows as _wf_listar,
)
from .sparql_client import BCNClient, leychile_url
from .texto import fetch_texto

mcp = FastMCP("chilean-legal")

_db = NormasDB()
_bcn: BCNClient | None = None


def _client() -> BCNClient:
    global _bcn
    if _bcn is None:
        _bcn = BCNClient()
    return _bcn


def _to_cl(fecha: str | None) -> str:
    """Convierte YYYY-MM-DD a DD-MM-AAAA para mostrar en Chile."""
    if not fecha or len(fecha) < 10:
        return fecha or ""
    try:
        # 2024-01-15 -> 15-01-2024
        if "-" in fecha and fecha[4] == "-":
            y, m, d = fecha[:10].split("-")
            return f"{d}-{m}-{y}"
        return fecha
    except Exception:
        return fecha


def _parse_fecha_cl(fecha: str | None) -> str | None:
    """Acepta DD-MM-AAAA o YYYY-MM-DD y devuelve YYYY-MM-DD para SPARQL."""
    if not fecha:
        return None
    fecha = fecha.strip()
    if len(fecha) == 10 and fecha[2] == "-" and fecha[5] == "-":  # DD-MM-AAAA
        d, m, y = fecha.split("-")
        return f"{y}-{m}-{d}"
    if "/" in fecha:  # DD/MM/AAAA
        d, m, y = fecha.split("/")
        return f"{y}-{m}-{d}"
    return fecha  # ya es YYYY-MM-DD


def _fecha_hoy() -> str:
    """Fecha de hoy en formato chileno DD-MM-AAAA."""
    return datetime.now().strftime("%d-%m-%Y")


def _format_row(row: dict) -> str:
    lines = [f"• {row.get('titulo') or ''}"]
    if row.get("numero"):
        lines.append(f"  Norma N° {row['numero']}")
    if row.get("fecha"):
        lines.append(f"  Publicada: {_to_cl(row['fecha'])}")
    url = leychile_url(row.get("leychile_id") or row.get("leychileId"))
    if url:
        lines.append(f"  Fuente oficial: {url}")
    else:
        lines.append(f"  URI BCN: {row.get('uri', '?')}")
    return "\n".join(lines)


def _cita(row: dict) -> str:
    num = row.get("numero") or row.get("leychileId") or "s/n"
    fecha = _to_cl(row.get("fecha") or "")
    titulo = (row.get("titulo") or "")[:100]
    url = leychile_url(row.get("leychile_id") or row.get("leychileId")) or row.get("uri","")
    return f"{titulo} — Ley N° {num} ({fecha}) — {url}"


@mcp.tool()
def buscar_normas(query: str, limite: int = 10, offset: int = 0, fecha_desde: str | None = None, fecha_hasta: str | None = None, tipo: str | None = None, materia: str | None = None) -> str:
    """Busca legislación chilena con filtros opcionales fecha_desde/fecha_hasta (DD-MM-AAAA, ej: '15-01-2024'), tipo (ej: 'ley', 'dto') y materia. Soporta paginación offset/limite (ej: offset=10 para página 2)."""
    query = query.strip()
    if not query:
        return "Error: la consulta está vacía."
    fecha_desde = _parse_fecha_cl(fecha_desde)
    fecha_hasta = _parse_fecha_cl(fecha_hasta)
    # materia como filtro adicional sobre título
    if materia:
        query = f"{query} {materia}"
    resultados: list[dict] = []
    try:
        if fecha_desde or fecha_hasta or tipo:
            vivos = _client().search_by_title(query, limit=limite, offset=offset, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, tipo=tipo)
            resultados = vivos
            nota = ""
            if offset:
                nota = f"(página offset={offset})"
        else:
            try:
                # Local con paginación: pedir limite+offset y cortar
                all_local = _db.search(query, limit=limite + offset)
                resultados = all_local[offset: offset + limite]
            except ValueError:
                return "Error: la consulta no contiene términos válidos."
            body_hits = _db.search_textos(query, limit=limite)
            for h in body_hits:
                if not any(r.get("leychile_id") == h["leychile_id"] for r in resultados):
                    resultados.append({"titulo": f"[cuerpo] {h['preview'][:120]}...", "leychile_id": h["leychile_id"], "uri": leychile_url(h["leychile_id"]) or ""})
            try:
                vivos = _client().search_by_title(query, limit=limite, offset=offset)
            except Exception as exc:  # noqa: BLE001
                vivos, nota = [], f"(vivo no disponible: {exc})"
            else:
                nota = f"(página offset={offset})" if offset else ""
            vistas = {r.get("uri") or r.get("leychile_id") or "" for r in resultados}
            for r in vivos:
                if r.get("uri") not in vistas:
                    resultados.append(r)
    except Exception as exc:  # noqa: BLE001
        return f"Error búsqueda: {exc}"
    if not resultados:
        # Fallback automático a semántica para queries largas (6 palabras → AND estricto falla)
        if len(query.split()) > 3:
            try:
                return buscar_semantico(query, limite=limite)
            except Exception:
                pass
        return f"Sin resultados para '{query}'. Usa términos más amplios o consulta buscar_semantico; este vacío no implica que el asunto no exista."
    total_hint = f" — offset {offset}, limite {limite} — usa offset={offset+limite} para siguiente página" if offset or len(resultados) >= limite else ""
    salida = ["LEGISLACIÓN CHILENA (BCN/LeyChile)",
              _narr_encabezado("BCN", query, len(resultados[:limite])),
              "Acerca de: cada norma incluye su cita legal completa (artículo, ley, año) lista para usar en un escrito.",
              ""]
    for row in resultados[:limite]:
        salida.append(_format_row(row))
        salida.append(f"  Cita: {_cita(row)}")
        salida.append("")
    if 'nota' in locals() and nota:
        salida.append(nota)
    salida.append("— Búsqueda local ilimitada. Usa obtener_texto_norma para el articulado.")
    salida.append("")
    salida.append(_narr_conclusion(query, len(resultados[:limite]),
                                   "Verifica la vigencia con estado_vigencia antes de citar."))
    salida.append("")
    salida.append("🔗 Links oficiales:")
    salida.append("• LeyChile: https://www.bcn.cl/leychile/navegar?idNorma=<id>")
    salida.append("• CGR: https://www.contraloria.cl/web/cgr/dictamenes-y-pronunciamientos")
    salida.append("• PJUD: https://www.pjud.cl/portal-unificado-sentencias")
    try:  # auto-registro en memoria (nunca rompe la búsqueda)
        _registrar_mensaje("consulta_auto", f"buscar_normas('{query}') → {len(resultados)} resultados",
                           herramientas="buscar_normas")
    except Exception:
        pass
    return "\n".join(salida)


@mcp.tool()
def citar_norma(identificador: str) -> str:
    """Devuelve cita formateada lista para pegar en escrito (N°, fecha DD-MM-AAAA, título, URL LeyChile). Pasa Nº ej '21643' o id ej '1200096'."""
    identificador = identificador.strip()
    if not identificador:
        return "Error: identificador vacío."
    try:
        if identificador.isdigit():
            rows = _client().search_by_number(identificador, limit=1)
            if not rows:
                rows = _client().search_by_title(identificador, limit=1)
            if rows:
                return f"Cita: {_cita(rows[0])}"
        else:
            # Si es texto, buscar por título
            rows = _client().search_by_title(identificador, limit=1)
            if rows:
                return f"Cita: {_cita(rows[0])}"
    except Exception as exc:  # noqa: BLE001
        return f"Error cita: {exc}"
    return f"Cita: https://www.bcn.cl/leychile/navegar?idNorma={identificador}"


@mcp.tool()
def citar_json(identificador: str) -> str:
    """Devuelve cita estructurada en JSON {numero, fecha DD-MM-AAAA, titulo, url, leychileId}."""
    identificador = identificador.strip()
    if not identificador:
        return json.dumps({"error": "identificador vacío"}, ensure_ascii=False)
    try:
        if identificador.isdigit():
            rows = _client().search_by_number(identificador, limit=1)
            if not rows:
                rows = _client().search_by_title(identificador, limit=1)
            if rows:
                r = rows[0]
                data = {
                    "numero": r.get("numero"),
                    "fecha": _to_cl(r.get("fecha") or ""),
                    "titulo": r.get("titulo"),
                    "url": leychile_url(r.get("leychileId") or r.get("leychile_id") or identificador) or r.get("uri"),
                    "leychileId": r.get("leychileId") or r.get("leychile_id"),
                }
                return json.dumps(data, ensure_ascii=False, indent=2)
        return json.dumps({"url": f"https://www.bcn.cl/leychile/navegar?idNorma={identificador}"}, ensure_ascii=False, indent=2)
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


@mcp.tool()
def exportar_norma(identificador: str, formato: str = "docx") -> str:
    """Exporta una norma a Word (.docx) o PDF (.pdf). Pasa Nº ej '21643' o id '1200096' y formato 'docx' o 'pdf'. Devuelve ruta del archivo en /tmp."""
    identificador = identificador.strip()
    formato = formato.lower().strip()
    if formato not in ("docx", "pdf"):
        return "Error: formato debe ser 'docx' o 'pdf'."
    # Resolver texto
    try:
        texto_completo = obtener_texto_norma(identificador)
        if texto_completo.startswith("Error") or texto_completo.startswith("No se pudo"):
            return texto_completo
        # Extraer metadatos para portada
        rows = _client().search_by_number(identificador, limit=1) if identificador.isdigit() else []
        titulo = rows[0].get("titulo") if rows else f"Norma {identificador}"
        numero = rows[0].get("numero") if rows else identificador
        fecha = _to_cl(rows[0].get("fecha") if rows else "")
        if formato == "docx":
            ruta = exportar_docx(titulo, texto_completo, numero, fecha)
        else:
            ruta = exportar_pdf(titulo, texto_completo, numero, fecha)
        return f"Exportado a {formato.upper()}: {ruta}\nAbre el archivo y compártelo con el abogado."
    except Exception as exc:  # noqa: BLE001
        return f"Error exportar: {exc}"


@mcp.tool()
def indexar_semantico(fuente: str = "todas", limite: int = 1000) -> str:
    """Indexa normas, jurisprudencia y/o expedientes en embeddings semánticos (MiniLM multilingüe).
    Fuentes: 'normas', 'jurisprudencia', 'expedientes', 'todas'. Requiere sentence-transformers instalado."""
    res = _sem_indexar(_db, fuente=fuente, limite=limite)
    out = ["INDEXACIÓN SEMÁNTICA completada:", ""]
    for k, v in res.items():
        out.append(f"• {k}: {v}")
    out.append("")
    out.append("Ahora puedes usar buscar_semantico(query, fuente='normas|jurisprudencia|expedientes')")
    return "\n".join(out)


@mcp.tool()
def buscar_semantico(query: str, top_k: int = 10, fuente: str | None = None) -> str:
    """Busca por similitud semántica en embeddings indexados (MiniLM multilingüe).
    Fuentes opcionales: 'normas', 'jurisprudencia', 'expedientes'. Requiere indexar_semantico previo."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    resultados = _sem_buscar(_db, query, top_k=top_k, fuente=fuente)
    return _sem_fmt(resultados, query)


@mcp.tool()
def estado_indexacion() -> str:
    """Reporta estado de la indexación semántica (chunks por fuente, modelo, instalación)."""
    return _sem_estado(_db)


@mcp.tool()
def generar_escrito(
    tipo: str,
    tribunal: str,
    causa_rol: str,
    caratulado: str,
    hechos: str,
    fundamentos: str = "",
    petitorio: str = "",
    abogado: str = "[NOMBRE ABOGADO]",
    rut_abogado: str = "[RUT ABOGADO]",
    email_abogado: str = "[EMAIL ABOGADO]",
    formato: str = "docx",
) -> str:
    """Genera borrador de escrito jurídico en .docx o .pdf (Fase 4 Magnar libre).

    Tipos: reposicion, apelacion, queja, solicitud, contestacion, medida_cautelar,
    proteccion, amparo, inaplicabilidad, revision, otro.
    Hechos/fundamentos/petitorio: texto con saltos de línea (\n) para múltiples párrafos.
    Fundamentos recomendados: cita + texto de normas/jurisprudencia/dictámenes (obtenidos con analizar_consulta)."""
    # Parsear fundamentos y petitorio desde strings
    fund_list = []
    if fundamentos.strip():
        for bloque in fundamentos.split("\n\n"):
            lineas = [l.strip() for l in bloque.split("\n") if l.strip()]
            if lineas:
                fund_list.append({
                    "fuente": lineas[0] if lineas else "Fuente",
                    "cita": lineas[1] if len(lineas) > 1 else "",
                    "texto": "\n".join(lineas[2:]) if len(lineas) > 2 else (lineas[1] if len(lineas) > 1 else "")
                })

    pet_list = [p.strip() for p in petitorio.split("\n") if p.strip()] if petitorio.strip() else []
    hecho_list = [h.strip() for h in hechos.split("\n") if h.strip()]

    return _red_generar(
        db=_db,
        tipo=tipo,
        tribunal=tribunal,
        causa_rol=causa_rol,
        caratulado=caratulado,
        hechos=hecho_list,
        fundamentos=fund_list,
        petitorio=pet_list,
        abogado=abogado,
        rut_abogado=rut_abogado,
        email_abogado=email_abogado,
        formato=formato,
    )


@mcp.tool()
def generar_escrito_desde_investigacion(
    consulta: str,
    tipo: str = "solicitud",
    tribunal: str = "[TRIBUNAL]",
    causa_rol: str = "[ROL]",
    caratulado: str = "[CARATULADO]",
    formato: str = "docx",
) -> str:
    """Genera escrito a partir de investigación automática (analizar_consulta + buscar_normas + buscar_jurisprudencia + buscar_dictamenes).

    Hace investigación multi-fuente y genera borrador fundamentado. Completa los [CORCHETES] antes de presentar."""
    return _red_desde_inv(
        db=_db,
        consulta=consulta,
        tipo=tipo,
        tribunal=tribunal,
        causa_rol=causa_rol,
        caratulado=caratulado,
        formato=formato,
    )


@mcp.tool()
def tipos_escrito_disponibles() -> str:
    """Lista los tipos de escrito soportados por generar_escrito."""
    out = ["TIPOS DE ESCRITO SOPORTADOS:", ""]
    for k, v in TIPOS_ESCRITO.items():
        out.append(f"• {k}: {v}")
    out.append("")
    out.append("Uso: generar_escrito(tipo='reposicion', ...)")
    return "\n".join(out)


@mcp.tool()
def iniciar_workflow(nombre: str, consulta_usuario: str, **kwargs: str) -> str:
    """Inicia un workflow multi-etapa (Fase 5 Magnar libre).

    Workflows: 'escrito_completo' (planificar→investigar→redactar→autoverificar),
    'investigacion_profunda', 'respuesta_consulta'.
    Parámetros extra: tipo_escrito, tribunal, causa_rol, caratulado, leychile_id."""
    return _wf_iniciar(nombre, consulta_usuario, **kwargs)


@mcp.tool()
def continuar_workflow(nombre: str, paso_actual: str, resultado: str, **kwargs: str) -> str:
    """Avanza al siguiente paso de un workflow multi-etapa con el resultado del paso anterior."""
    return _wf_continuar(nombre, paso_actual, resultado, **kwargs)


@mcp.tool()
def estado_workflow(nombre: str) -> str:
    """Reporta estado actual de un workflow multi-etapa."""
    return _wf_estado(nombre)


@mcp.tool()
def listar_workflows() -> str:
    """Lista todos los workflows multi-etapa disponibles."""
    return _wf_listar()


@mcp.tool()
def obtener_texto_norma(identificador: str, offset: int = 0, chunk: int = 8000) -> str:
    """Obtiene el texto completo de una norma chilena por su Nº (ej: '21643') o por su id LeyChile (ej: '1200096'). Soporta paginación chunk/offset para no saturar el contexto (ej: offset=8000, chunk=6000)."""
    identificador = identificador.strip()
    if not identificador:
        return "Error: identificador vacío."
    leychile_id = None
    if identificador.isdigit():
        cached = _db.get_texto(identificador)
        if cached:
            return cached
        try:
            rows = _client().search_by_number(identificador, limit=3)
            if rows:
                leychile_id = rows[0].get("leychileId") or rows[0].get("leychile_id")
            else:
                leychile_id = identificador
        except Exception:  # noqa: BLE001
            leychile_id = identificador
    else:
        leychile_id = identificador
    if not leychile_id:
        return f"No se pudo resolver '{identificador}' a un id LeyChile."
    cached = _db.get_texto(leychile_id)
    if cached:
        return cached
    texto = fetch_texto(leychile_id)
    if not texto:
        url = leychile_url(leychile_id)
        return f"No se pudo descargar el texto para id {leychile_id}. Ver fuente oficial: {url}\n🔗 https://www.bcn.cl/leychile/navegar?idNorma={leychile_id}"
    _db.save_texto(leychile_id, texto)
    # Paginación
    total = len(texto)
    if offset or chunk != 8000:
        texto = texto[offset: offset + chunk]
        texto += f"\n\n---\nMostrando {offset}-{offset+len(texto)} de {total} chars. Usa offset={offset+chunk} para siguiente chunk."
    texto += "\n\n---\n🔗 Links oficiales:\n"
    texto += f"• Ver en LeyChile: https://www.bcn.cl/leychile/navegar?idNorma={leychile_id}\n"
    texto += "• CGR: https://www.contraloria.cl/web/cgr/dictamenes-y-pronunciamientos\n"
    texto += "• PJUD: https://www.pjud.cl/portal-unificado-sentencias\n"
    return texto


@mcp.tool()
def buscar_dictamenes(query: str, limite: int = 10) -> str:
    """Busca dictámenes de la Contraloría General de la República por texto libre."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    local = _db.search_dictamenes(query, limit=limite)
    cgr_rows = buscar_cgr(query, limite=limite)
    for r in cgr_rows:
        cid = f"cgr:{r['numero']}"
        _db.upsert_dictamen(cid, r["numero"], r["titulo"], None, r["url"])
        if not any(x["numero"] == r["numero"] for x in local):
            local.append({"numero": r["numero"], "titulo": r["titulo"], "fecha": None, "url": r["url"]})
    if not local:
        try:
            bcn_rows = _client().search_dictamenes(query, limit=limite)
            for r in bcn_rows:
                local.append({"numero": "", "titulo": r.get("titulo",""), "fecha": r.get("fecha"), "url": r.get("uri","")})
        except Exception:
            pass
    if not local:
        return (f"CONCLUSIÓN: No se encontraron dictámenes para '{query}' en CGR ni BCN.\n"
                "Este vacío NO significa que el asunto no exista: prueba términos más amplios "
                "o revisa directamente https://www.contraloria.cl/web/cgr/dictamenes-y-pronunciamientos")
    out = ["DICTÁMENES CONTRALORÍA GENERAL DE LA REPÚBLICA",
           _narr_encabezado("CGR", query, len(local[:limite])), ""]
    for r in local[:limite]:
        num = r.get("numero") or "s/n"
        out.append(f"• Dictamen {num} — {r.get('titulo','')}")
        if r.get("fecha"):
            out.append(f"  Fecha: {r['fecha']}")
        out.append("  Contexto: los dictámenes CGR son pronunciamientos vinculantes sobre la "
                   "legalidad de actos de la Administración; constituyen jurisprudencia administrativa.")
        out.append(f"  Fuente oficial: {r.get('url','')}")
        out.append("")
    out.append(_narr_conclusion(query, len(local[:limite]),
                                "Los dictámenes CGR son de cumplimiento obligatorio para órganos públicos."))
    out.append("")
    out.append("🔗 Links oficiales:")
    out.append("• CGR: https://www.contraloria.cl/web/cgr/dictamenes-y-pronunciamientos")
    out.append("• LeyChile: https://www.bcn.cl/leychile/navegar?idNorma=<id>")
    out.append("• PJUD: https://www.pjud.cl/portal-unificado-sentencias")
    return "\n".join(out)


@mcp.tool()
def buscar_jurisprudencia(query: str, limite: int = 10) -> str:
    """Busca jurisprudencia chilena — fuentes públicas y legales. Ahora con fallback semántico y búsqueda real PJUD/TC/TDPI."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    # 1. BCN filtrado
    try:
        rows = _client().search_by_title(query, limit=limite)
        juris = [r for r in rows if any(k in r.get("titulo","").lower() for k in ("jurisprudencia","sentencia","fallo","corte"))]
    except Exception:
        juris = []
    # 2. Si no hay, probar semántica con query corta (primeras 3 palabras)
    if not juris and len(query.split()) > 3:
        short_q = " ".join(query.split()[:3])
        try:
            rows = _client().search_by_title(short_q, limit=limite)
            juris = [r for r in rows if any(k in r.get("titulo","").lower() for k in ("jurisprudencia","sentencia","fallo","corte"))]
            # Si aún no, usar buscar_semantico y extraer
            if not juris:
                sem = _db.search(short_q, limit=limite)
                juris = sem
        except Exception:
            pass
    # 3. Complementar con TC/TDPI/CGR
    cgr = buscar_cgr(query, limite=2) if len(juris) < 3 else []
    tc_rows = []
    try:
        from .fuentes_externas import buscar_tc as _tc
        tc_rows = _tc(query, limite=2)
        # Filtrar fallback genérico
        tc_rows = [r for r in tc_rows if "Buscar '" not in r["titulo"]]
    except Exception:
        pass
    header = f"Jurisprudencia para '{query}' (fuentes públicas):\n"
    if juris:
        header += f"({len(juris)} en BCN)\n\n"
        for r in juris[:limite]:
            header += _format_row(r) + "\n\n"
    if tc_rows:
        header += "TC relacionado:\n"
        for r in tc_rows[:2]:
            header += f"• {r['titulo'][:100]}\n  URL: {r['url']}\n"
    if cgr:
        header += "Dictámenes CGR relacionados:\n"
        for r in cgr[:2]:
            header += f"• Dictamen {r['numero']} — {r['titulo'][:100]}\n  {r['url']}\n"
    if not juris and not cgr and not tc_rows:
        # Último fallback: normativa aplicable + links, no "Sin resultados"
        try:
            norm = _client().search_by_title(" ".join(query.split()[:2]), limit=2)
            if norm:
                header += "Normativa aplicable (jurisprudencia similar no indexada, se muestra norma):\n"
                for r in norm:
                    header += _format_row(r) + "\n\n"
        except Exception:
            pass
    header += (
        "\n🔗 Links oficiales:\n"
        "• PJUD: https://www.pjud.cl/portal-unificado-sentencias\n"
        "• TC: https://buscador.tcchile.cl/#/\n"
        "• CGR: https://www.contraloria.cl/web/cgr/dictamenes-y-pronunciamientos\n"
        "• LeyChile: https://www.bcn.cl/leychile/navegar?idNorma=<id>\n"
    )
    return header


@mcp.tool()
def buscar_doctrina(query: str, limite: int = 10) -> str:
    """Busca doctrina / artículos a nivel de artículo y materias."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _client().search_articulos(query, limit=limite)
    except Exception:  # noqa: BLE001
        rows = []
    if rows:
        out = [f"Artículos para '{query}' ({len(rows)}):", ""]
        for r in rows[:limite]:
            out.append(f"• {r.get('numero','')} — {r.get('texto','')[:180].replace(chr(10),' ')}...")
            out.append(f"  URI: {r.get('uri','')}")
            out.append("")
        out.append("Fuente: BCN Articulo (bodies legislativos).")
        out.append("🔗 https://www.bcn.cl/leychile/navegar?idNorma=<id> | https://www.pjud.cl/portal-unificado-sentencias")
        return "\n".join(out)
    return buscar_normas(query, limite=limite) + "\n\n[Doctrina fallback a normas — artículos sin resultados directos]"


@mcp.tool()
def historial_norma(identificador: str) -> str:
    """Muestra historial de vigencia y relaciones de una norma (versiones, qué modifica, por qué es modificada)."""
    identificador = identificador.strip()
    if not identificador:
        return "Error: identificador vacío."
    uri = identificador
    if identificador.isdigit():
        try:
            rows = _client().search_by_number(identificador, limit=1)
            if rows:
                uri = rows[0].get("uri") or rows[0].get("s") or ""
            if not uri or not uri.startswith("http"):
                uri = f"https://www.bcn.cl/leychile/navegar?idNorma={identificador}"
                return f"URI no resuelta directamente para '{identificador}'. Prueba con la URI BCN de buscar_normas."
        except Exception as exc:  # noqa: BLE001
            return f"Error resolviendo '{identificador}': {exc}"
    if not uri.startswith("http"):
        return "Pasa la URI BCN completa (la que devuelve buscar_normas) o un número como '21643'."
    try:
        rows = _client().get_historial(uri)
    except Exception as exc:  # noqa: BLE001
        return f"Error historial: {exc}"
    if not rows:
        return f"Sin historial para {uri}"
    out = [f"Historial para {uri}:", ""]
    for r in rows:
        p = r.get("p","").split("#")[-1].split("/")[-1]
        out.append(f"• {p}: {r.get('o','')[:120]}")
    out.append("")
    out.append("🔗 Ver texto: https://www.bcn.cl/leychile/navegar?idNorma=<id> (usa leychileId de buscar_normas)")
    return "\n".join(out)


@mcp.tool()
def buscar_scielo(query: str, limite: int = 5) -> str:
    """Busca doctrina en SciELO Chile (open access, revistas jurídicas)."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _buscar_scielo(query, limite=limite)
    except Exception as exc:  # noqa: BLE001
        return f"Error SciELO: {exc}"
    if not rows:
        return f"Sin resultados SciELO para '{query}'. Prueba https://search.scielo.org/?q={query.replace(' ', '+')}&lang=es"
    out = [f"SciELO Chile para '{query}' ({len(rows)}):", ""]
    for r in rows:
        out.append(f"• {r['titulo']}")
        out.append(f"  URL: {r['url']}")
        out.append("")
    out.append("Fuente: SciELO Chile (open access).")
    out.append("🔗 https://search.scielo.org/?q=<query>&lang=es")
    return "\n".join(out)


@mcp.tool()
def buscar_dt(query: str, limite: int = 5) -> str:
    """Busca dictámenes/ordinarios de la Dirección del Trabajo."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _buscar_dt(query, limite=limite)
    except Exception as exc:  # noqa: BLE001
        return f"Error DT: {exc}"
    out = [f"DT para '{query}' ({len(rows)}):", ""]
    for r in rows:
        out.append(f"• {r['titulo']}")
        out.append(f"  URL: {r['url']}")
        out.append("")
    out.append("Fuente: Dirección del Trabajo (dt.gob.cl).")
    out.append("🔗 https://www.dt.gob.cl/legislacion/1624/w3-channel.html")
    return "\n".join(out)


@mcp.tool()
def buscar_diario_oficial(query: str, limite: int = 5) -> str:
    """Busca en el Diario Oficial de la República."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _buscar_diario(query, limite=limite)
    except Exception as exc:  # noqa: BLE001
        return f"Error Diario Oficial: {exc}"
    out = [f"Diario Oficial para '{query}' ({len(rows)}):", ""]
    for r in rows:
        out.append(f"• {r['titulo']}")
        out.append(f"  URL: {r['url']}")
        out.append("")
    out.append("Fuente: Diario Oficial (diariooficial.interior.gob.cl).")
    return "\n".join(out)


@mcp.tool()
def buscar_suseso(query: str, limite: int = 5) -> str:
    """Busca dictámenes y circulares de la SUSESO (Seguridad Social, Ley 16.744, licencias médicas)."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _buscar_suseso(query, limite=limite)
    except Exception as exc:  # noqa: BLE001
        return f"Error SUSESO: {exc}"
    out = [f"SUSESO para '{query}' ({len(rows)}):", ""]
    for r in rows:
        out.append(f"• {r['titulo']}")
        out.append(f"  URL: {r['url']}")
        out.append("")
    out.append("Fuente: SUSESO (suseso.cl) — 10k+ dictámenes.")
    out.append("🔗 https://www.suseso.cl/612/w3-propertyvalue-10372.html")
    return "\n".join(out)


@mcp.tool()
def buscar_tc(query: str, limite: int = 5) -> str:
    """Busca jurisprudencia del Tribunal Constitucional con análisis narrativo por caso.

    Para CADA sentencia encontrada entrega: tipo de acción, fecha, requirente,
    norma cuestionada, artículos constitucionales invocados, resolución
    (acogida/rechazada/inadmisible), si el fondo fue o no analizado, contexto de
    los considerandos y link a la ficha oficial.
    """
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _buscar_tc(query, limite=max(1, min(int(limite), 10)))
    except Exception as exc:  # noqa: BLE001
        return f"Error TC: {exc}"
    out = [f"TRIBUNAL CONSTITUCIONAL — resultados para '{query}'", ""]
    for r in rows:
        try:
            analisis = _analizar_sentencia_tc(r.get("content", ""), rol=str(r.get("rol") or ""))
            out.append(_formatear_caso_tc(r, analisis))
        except Exception:
            out.append(f"CASO Rol {r.get('rol', '?')}")
            out.append(f"Resumen: {r.get('titulo', '')}")
            out.append(f"Ficha oficial: {r.get('url', '')}")
        out.append("")
        out.append("─" * 60)
        out.append("")
    out.append("Fuente oficial: Tribunal Constitucional (buscador.tcchile.cl).")
    return "\n".join(out)


@mcp.tool()
def buscar_historia_ley(query: str, limite: int = 5) -> str:
    """Busca Historia de la Ley (BCN) — Mensaje, Informes, Discusión Sala, Oficio, razón legislativa art. 19 CC."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _buscar_historia(query, limite=limite)
    except Exception as exc:  # noqa: BLE001
        return f"Error Historia Ley: {exc}"
    out = [f"Historia de la Ley para '{query}' ({len(rows)}):", ""]
    for r in rows:
        out.append(f"• {r['titulo']}")
        out.append(f"  URL: {r['url']}")
        out.append("")
    out.append("Fuente: BCN Historia de la Ley (bcn.cl/historiadelaley).")
    return "\n".join(out)


@mcp.tool()
def buscar_sii(query: str, limite: int = 5) -> str:
    """Busca normativa tributaria SII (Oficios, Circulares, Resoluciones, Fallos TTA) — fuentes oficiales www3/www4.sii.cl + tta.cl."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _buscar_sii(query, limite=limite)
    except Exception as exc:  # noqa: BLE001
        return f"Error SII: {exc}"
    out = [f"SII para '{query}' ({len(rows)}):", ""]
    for r in rows:
        out.append(f"• {r['titulo']}")
        out.append(f"  URL: {r['url']}")
        out.append("")
    out.append("Fuente: SII Chile (www3.sii.cl API oficial, www4.sii.cl descargas, tta.cl fallos).")
    out.append("🔗 https://www.sii.cl | https://www.tta.cl")
    return "\n".join(out)


@mcp.tool()
def buscar_cmf(query: str, limite: int = 5) -> str:
    """Busca normativa CMF (ex SVS/SBIF, Bancos/Seguros/Valores)."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _buscar_cmf(query, limite=limite)
    except Exception as exc:  # noqa: BLE001
        return f"Error CMF: {exc}"
    out = [f"CMF para '{query}' ({len(rows)}):", ""]
    for r in rows:
        out.append(f"• {r['titulo']}")
        out.append(f"  URL: {r['url']}")
        out.append("")
    out.append("Fuente: CMF (cmfchile.cl).")
    return "\n".join(out)


@mcp.tool()
def buscar_tdlc(query: str, limite: int = 5) -> str:
    """Busca jurisprudencia TDLC (libre competencia)."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _buscar_tdlc(query, limite=limite)
    except Exception as exc:  # noqa: BLE001
        return f"Error TDLC: {exc}"
    out = [f"TDLC para '{query}' ({len(rows)}):", ""]
    for r in rows:
        out.append(f"• {r['titulo']}")
        out.append(f"  URL: {r['url']}")
        out.append("")
    out.append("Fuente: TDLC (tdlc.cl).")
    return "\n".join(out)


@mcp.tool()
def buscar_cplt(query: str, limite: int = 5) -> str:
    """Busca decisiones CPLT (Transparencia, amparos)."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _buscar_cplt(query, limite=limite)
    except Exception as exc:  # noqa: BLE001
        return f"Error CPLT: {exc}"
    out = [f"CPLT para '{query}' ({len(rows)}):", ""]
    for r in rows:
        out.append(f"• {r['titulo']}")
        out.append(f"  URL: {r['url']}")
        out.append("")
    out.append("Fuente: CPLT (jurisprudencia.cplt.cl).")
    return "\n".join(out)


@mcp.tool()
def buscar_datos_gob(query: str, limite: int = 5) -> str:
    """Busca datasets en datos.gob.cl (CKAN, 3.8k datasets, sin auth)."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _buscar_datos(query, limite=limite)
    except Exception as exc:  # noqa: BLE001
        return f"Error datos.gob.cl: {exc}"
    out = [f"datos.gob.cl para '{query}' ({len(rows)}):", ""]
    for r in rows:
        out.append(f"• {r['titulo']}")
        out.append(f"  URL: {r['url']}")
        out.append("")
    out.append("Fuente: datos.gob.cl (CKAN).")
    return "\n".join(out)


@mcp.tool()
def buscar_todo(query: str, limite: int = 8) -> str:
    """Búsqueda multi-fuente PARALELO real: normas + CGR + jurisprudencia + SciELO."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        f_normas = ex.submit(buscar_normas, query, limite)
        f_cgr = ex.submit(buscar_dictamenes, query, limite)
        f_juris = ex.submit(buscar_jurisprudencia, query, limite)
        f_scielo = ex.submit(buscar_scielo, query, 3)
        try:
            r_normas = f_normas.result(timeout=60)
        except Exception as e:
            r_normas = f"Error normas: {e}"
        try:
            r_cgr = f_cgr.result(timeout=60)
        except Exception as e:
            r_cgr = f"Error CGR: {e}"
        try:
            r_juris = f_juris.result(timeout=60)
        except Exception as e:
            r_juris = f"Error juris: {e}"
        try:
            r_scielo = f_scielo.result(timeout=30)
        except Exception as e:
            r_scielo = f"Error SciELO: {e}"
    partes: list[str] = [f"# Búsqueda multi-fuente (paralelo) para '{query}'\n"]
    partes.append("## 1. Legislación")
    partes.append(r_normas)
    partes.append("\n## 2. Dictámenes Contraloría")
    partes.append(r_cgr)
    partes.append("\n## 3. Jurisprudencia")
    partes.append(r_juris)
    partes.append("\n## 4. Doctrina SciELO")
    partes.append(r_scielo)
    body = _db.search_textos(query, limit=3)
    if body:
        partes.append("\n## 5. Cuerpo de normas ya cacheadas")
        for h in body:
            partes.append(f"• id {h['leychile_id']}: {h['preview'][:150]}...")
    partes.append("\n---\n🔗 Links oficiales:")
    partes.append("• LeyChile: https://www.bcn.cl/leychile/navegar?idNorma=<id>")
    partes.append("• CGR: https://www.contraloria.cl/web/cgr/dictamenes-y-pronunciamientos")
    partes.append("• PJUD: https://www.pjud.cl/portal-unificado-sentencias")
    partes.append("• SciELO: https://search.scielo.org/?q=<query>&lang=es")
    partes.append("• DT: https://www.dt.gob.cl/legislacion/1624/w3-channel.html")
    partes.append("• Diario Oficial: https://www.diariooficial.interior.gob.cl/buscador/solicitud/buscar?texto=<query>")
    return "\n".join(partes)


@mcp.tool()
def analizar_consulta(consulta: str) -> str:
    """Análisis jurídico completo multi-fuente en un solo llamado (estilo Trifolia).

    Ejecuta búsqueda paralela en legislación + jurisprudencia + dictámenes + doctrina
    y devuelve informe estructurado I-V listo para que el LLM del usuario redacte
    el análisis jurídico final. No inventa nada — solo entrega fuentes oficiales.
    """
    consulta = consulta.strip()
    if not consulta:
        return "Error: consulta vacía."

    def _safe(fn, *a, timeout=90):
        try:
            return fn(*a)
        except Exception as e:
            return f"[Error: {e}]"

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        f_normas   = ex.submit(_safe, buscar_normas, consulta, 8)
        f_juris    = ex.submit(_safe, buscar_jurisprudencia, consulta, 6)
        f_cgr      = ex.submit(_safe, buscar_dictamenes, consulta, 4)
        f_scielo   = ex.submit(_safe, buscar_scielo, consulta, 3)
        f_todo     = ex.submit(_safe, buscar_todo_fuentes_externas, consulta, 4)
        r_normas   = f_normas.result(timeout=90)
        r_juris    = f_juris.result(timeout=90)
        r_cgr      = f_cgr.result(timeout=90)
        r_scielo   = f_scielo.result(timeout=60)
        r_todo     = f_todo.result(timeout=60)

    fecha_hoy = datetime.now().strftime("%d-%m-%Y")
    palabras  = [w for w in consulta.split() if len(w) >= 4][:6]

    secciones: list[str] = []

    secciones.append("# I. ANTECEDENTES Y CONTEXTO JURÍDICO\n")
    secciones.append(
        f"Consulta: \"{consulta}\" — elaborado {fecha_hoy} — "
        "fuentes: LeyChile/BCN, PJUD, CGR, TC, TGR, SII, SUSESO, Diario Oficial, SciELO. "
        "Todas las citas incluyen URL oficial verificable."
    )
    secciones.append(
        "Objetivo: analizar la pregunta jurídica bajo la normativa chilena vigente, "
        "la jurisprudencia de los tribunales competentes y la doctrina académica disponible."
    )
    secciones.append(
        "Alcance: este informe no reemplaza el juicio profesional del abogado. "
        "Entrega información trazable para fundamentar decisiones."
    )

    secciones.append("# II. NORMATIVA APLICABLE (texto oficial LeyChile)\n")
    secciones.append("Fuentes primarias — selecciona aquellas relevantes para la consulta:")
    for p in palabras:
        secciones.append(f"\n## Búsqueda: \"{p}\"\n")
        try:
            filas = _client().search_by_title(p, limit=4)
            for r in filas:
                secciones.append(_format_row(r))
                url = leychile_url(r.get("leychileId") or r.get("leychile_id"))
                if url:
                    secciones.append(f"  Ver texto oficial: {url}")
        except Exception:
            pass
    secciones.append("\n> Usa `obtener_texto_norma(id)` para recuperar el articulado completo de cualquier norma citada.\n")

    secciones.append("# III. JURISPRUDENCIA Y DICTÁMENES RELACIONADOS\n")
    secciones.append("### Jurisprudencia\n")
    if "Sin resultados" not in r_juris and "Error" not in r_juris:
        secciones.append(r_juris[:3000])
    else:
        secciones.append("No se encontró jurisprudencia indexada para esta consulta. "
                         "Ampliar con `buscar_jurisprudencia` o `buscar_tc`.")

    secciones.append("\n### Dictámenes CGR\n")
    cgr_raw = r_cgr[:2000]
    if "Sin dictámenes" not in cgr_raw and "Error" not in cgr_raw:
        secciones.append(cgr_raw)
    else:
        secciones.append("Sin dictámenes CGR específicos. Fuente ampliable: "
                         "https://www.contraloria.cl/web/cgr/dictamenes-y-pronunciamientos\n"
                         "Usa `buscar_dictamenes` para búsqueda directa.")

    secciones.append("\n# IV. ANÁLISIS JURÍDICO (síntesis de fuentes oficiales)\n")
    secciones.append(
        "Criterios extraídos de las fuentes anteriores — NO inventar. "
        "Listar tesis encontradas con referencia a su fuente."
    )
    secciones.append(
        "\n- Criterio 1: [título del criterio] — [organismo + N°/fecha] — [relevancia]\n"
        "- Criterio 2: ..."
    )
    secciones.append(
        "\nFundamento normativo identificado: [artículos aplicables con N° de ley y fecha DD-MM-AAAA]"
    )
    secciones.append(
        "\nAntecedentes sectoriales (si aplica):\n"
        + (r_todo[:2500] if isinstance(r_todo, str) else "")
    )

    secciones.append("\n# V. CONCLUSIÓN\n")
    secciones.append("Síntesis ejecutiva en 3-5 líneas del estado de la cuestión jurídica:\n")
    secciones.append("[Redactar conclusión a partir de las fuentes oficiales encontradas — "
                     "no agregar especulación ni opinión personal del LLM]")

    secciones.append("\n---\n## Referencias y links oficiales\n")
    links = [
        "LeyChile: https://www.bcn.cl/leychile/navegar?idNorma=<id>",
        "PJUD (jurisprudencia): https://www.pjud.cl/portal-unificado-sentencias",
        "TC: https://buscador.tcchile.cl/#/",
        "CGR (dictámenes): https://www.contraloria.cl/web/cgr/dictamenes-y-pronunciamientos",
        "SII: https://www.sii.cl",
        "SUSESO: https://www.suseso.cl",
        "DT: https://www.dt.gob.cl",
        "Diario Oficial: https://www.diariooficial.interior.gob.cl",
        "SciELO: https://search.scielo.org/?lang=es",
    ]
    for lk in links:
        secciones.append(lk)

    secciones.append(
        "\n---\nCONCLUSIÓN JURÍDICA (síntesis del servidor a partir de los hallazgos):\n"
        f"La consulta '{consulta}' arrojó material en normativa ({len(r_normas)} chars) y "
        f"jurisprudencia/fuentes ({len(r_juris)} chars). Antes de concluir, verifica: "
        "(1) la vigencia real de las normas citadas con estado_vigencia; "
        "(2) que cada caso citado esté en fondo resuelto y no sea una providencia o causa inadmisible; "
        "(3) la fecha DD-MM-AAAA de cada fuente. Declara explícitamente qué aspectos NO "
        "quedaron cubiertos por las fuentes consultadas."
    )
    secciones.append(
        "\n---\n⚠️ Descargo: Este informe se genera exclusivamente a partir de fuentes oficiales "
        "chilenas públicas. No constituye asesoría legal. El usuario es responsable del uso "
        "que haga de esta información."
    )

    try:  # auto-registro en memoria (nunca rompe el análisis)
        _registrar_mensaje("usuario", f"Análisis de consulta: {consulta}", herramientas="analizar_consulta")
        _registrar_mensaje("asistente", f"Informe generado: normativa {len(r_normas)} chars, jurisprudencia {len(r_juris)} chars",
                           herramientas="analizar_consulta")
    except Exception:
        pass
    return "\n".join(secciones)


@mcp.tool()
def buscar_todo_fuentes_externas(query: str, limite: int = 5) -> str:
    """Alias de buscar_todo para uso interno desde analizar_consulta."""
    return buscar_todo(query, limite)


@mcp.resource("norma://{leychile_id}")
def norma_resource(leychile_id: str) -> str:
    """Recurso: texto completo de la norma (cacheable, sin costo de tokens por turno)."""
    return obtener_texto_norma(leychile_id)


@mcp.resource("norma://{leychile_id}/historial")
def norma_historial(leychile_id: str) -> str:
    """Recurso: historial de vigencia de la norma."""
    return historial_norma(leychile_id)


@mcp.prompt("analisis_vigencia")
def prompt_analisis_vigencia(numero: str) -> str:
    filas = [
        f"1) historial_nigencia({numero}) -> rastrea modificaciones y derogaciones",
        f"2) obtener_texto_norma({numero}) -> texto articulado completo",
        f"3) citar_norma({numero}) -> cita lista para escrito",
        f"4) analizar_consulta('la consulta del usuario sobre {numero}') -> resultados multi-fuente",
    ]
    return ("Analiza vigencia de la norma " + numero + ": " + "; ".join(filas) +
            ". Verifica modificaciones y estado de vigencia. Cita en formato: Ley N° (DD-MM-AAAA) — URL LeyChile. "
            "PRESENTACIÓN OBLIGATORIA: responde en formato narrativo jurídico — encabezado con fuente y fecha, "
            "explicación de qué es la norma y por qué importa, historia normativa caso a caso, "
            "declaración explícita de qué NO se pudo verificar, y conclusión final. Nada de listas secas sin contexto.")


@mcp.prompt("redacta_escrito")
def prompt_redacta_escrito(materia: str) -> str:
    return (
        f"Redacta escrito jurídico sobre '{materia}':\n"
        f"1) analizar_consulta('{materia}') -> informe I-V multi-fuente en un solo paso\n"
        f"2) obtener_texto_norma(id_norma_relevante, chunk=4000) -> articulado para citar\n"
        f"3) buscar_jurisprudencia('{materia}') -> fallos y sentencias del ámbito\n"
        f"4) buscar_dictamenes('{materia}') -> dictámenes CGR\n"
        "Citas en formato: Ley N° XXXX (DD-MM-AAAA) — https://www.bcn.cl/leychile/navegar?idNorma=<id>.\n"
        "Incluye 3-5 referencias oficiales al pie. No inventar doctrina ni jurisprudencia.\n"
        "ESTILO OBLIGATORIO: texto explicativo autosuficiente — cada caso citado se presenta con "
        "identificación (rol/fecha/tribunal), hechos, resolución y alcance (indicando si el fondo "
        "quedó sin resolver), fragmentos textuales entre comillas y link oficial. Cierra con "
        "conclusión que sintetice los hallazgos y declare los vacíos informativos."
    )


@mcp.tool()
def sii_buscar_oficio(query: str, limite: int = 5, offset: int = 0) -> str:
    """SII — Oficios (Jurisprudencia administrativa)."""
    query=query.strip()
    if not query: return "Error: consulta vacía."
    cached=_db._search_generic("sii_oficios","sii_oficios_fts",query,limite,offset)
    if cached:
        out=[f"SII Oficios para '{query}' ({len(cached)} cache):",""]
        for r in cached: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
        return "\n".join(out)
    rows=_sii_mod.buscar_oficio(query, limite + offset)[offset: offset + limite]
    for r in rows: _db._upsert_generic("sii_oficios","sii_oficios_fts",f"sii_of:{r['numero']}",r["numero"],r["titulo"],r["url"])
    out=[f"SII Oficios para '{query}' ({len(rows)}):",""]
    for r in rows: out.append(f"• Oficio {r['numero']} — {r['titulo']}\n  URL: {r['url']}\n")
    out.append("🔗 Fuente oficial: https://www3.sii.cl/getPublicacionesCTByMateria")
    return "\n".join(out)

@mcp.tool()
def sii_buscar_circular(query: str, limite: int = 5, offset: int = 0) -> str:
    """SII — Circulares."""
    query=query.strip()
    if not query: return "Error: consulta vacía."
    cached=_db._search_generic("sii_circulares","sii_circulares_fts",query,limite,offset)
    if cached:
        out=[f"SII Circulares para '{query}' ({len(cached)} cache):",""]
        for r in cached: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
        return "\n".join(out)
    rows=_sii_mod.buscar_circular(query, limite + offset)[offset: offset + limite]
    for r in rows: _db._upsert_generic("sii_circulares","sii_circulares_fts",f"sii_cir:{r['numero']}",r["numero"],r["titulo"],r["url"])
    out=[f"SII Circulares para '{query}' ({len(rows)}):",""]
    for r in rows: out.append(f"• Circular {r['numero']} — {r['titulo']}\n  URL: {r['url']}\n")
    return "\n".join(out)

@mcp.tool()
def sii_buscar_resolucion(query: str, limite: int = 5, offset: int = 0) -> str:
    """SII — Resoluciones Exentas/Afectas."""
    query=query.strip()
    if not query: return "Error: consulta vacía."
    cached=_db._search_generic("sii_resoluciones","sii_resoluciones_fts",query,limite,offset)
    if cached:
        out=[f"SII Resoluciones para '{query}' ({len(cached)} cache):",""]
        for r in cached: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
        return "\n".join(out)
    rows=_sii_mod.buscar_resolucion(query, limite + offset)[offset: offset + limite]
    for r in rows: _db._upsert_generic("sii_resoluciones","sii_resoluciones_fts",f"sii_res:{r['numero']}",r["numero"],r["titulo"],r["url"])
    out=[f"SII Resoluciones para '{query}' ({len(rows)}):",""]
    for r in rows: out.append(f"• Resolución {r['numero']} — {r['titulo']}\n  URL: {r['url']}\n")
    return "\n".join(out)

@mcp.tool()
def sii_buscar_fallo(query: str, limite: int = 5, offset: int = 0) -> str:
    """SII — Fallos TTA (Tribunal Tributario y Aduanero)."""
    query=query.strip()
    if not query: return "Error: consulta vacía."
    cached=_db._search_generic("sii_fallos","sii_fallos_fts",query,limite,offset)
    if cached:
        out=[f"SII Fallos TTA para '{query}' ({len(cached)} cache):",""]
        for r in cached: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
        return "\n".join(out)
    rows=_sii_mod.buscar_fallo(query, limite + offset)[offset: offset + limite]
    for r in rows: _db._upsert_generic("sii_fallos","sii_fallos_fts",f"sii_fallo:{r['numero']}",r["numero"],r["titulo"],r["url"])
    out=[f"SII Fallos TTA para '{query}' ({len(rows)}):",""]
    for r in rows: out.append(f"• Fallo {r['numero']} — {r['titulo']}\n  URL: {r['url']}\n")
    return "\n".join(out)

@mcp.tool()
def tgr_buscar_dictamen(query: str, limite: int = 5, offset: int = 0) -> str:
    """TGR — Dictámenes."""
    query=query.strip()
    if not query: return "Error: consulta vacía."
    cached=_db._search_generic("tgr_dictamenes","tgr_dictamenes_fts",query,limite,offset)
    if cached:
        out=[f"TGR Dictámenes para '{query}' ({len(cached)} cache):",""]
        for r in cached: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
        return "\n".join(out)
    rows=_tgr_mod.buscar_dictamen(query, limite + offset)[offset: offset + limite]
    for r in rows: _db._upsert_generic("tgr_dictamenes","tgr_dictamenes_fts",f"tgr_dic:{r['numero']}",r["numero"],r["titulo"],r["url"],r.get("resultado",""))
    out=[f"TGR Dictámenes para '{query}' ({len(rows)}):",""]
    for r in rows: out.append(f"• Dictamen {r['numero']} — {r['titulo']}\n  URL: {r['url']}\n")
    return "\n".join(out)

@mcp.tool()
def tgr_buscar_resolucion(query: str, limite: int = 5, offset: int = 0) -> str:
    """TGR — Resoluciones."""
    query=query.strip()
    if not query: return "Error: consulta vacía."
    cached=_db._search_generic("tgr_resoluciones","tgr_resoluciones_fts",query,limite,offset)
    if cached:
        out=[f"TGR Resoluciones para '{query}' ({len(cached)} cache):",""]
        for r in cached: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
        return "\n".join(out)
    rows=_tgr_mod.buscar_resolucion(query, limite + offset)[offset: offset + limite]
    for r in rows: _db._upsert_generic("tgr_resoluciones","tgr_resoluciones_fts",f"tgr_res:{r['numero']}",r["numero"],r["titulo"],r["url"])
    out=[f"TGR Resoluciones para '{query}' ({len(rows)}):",""]
    for r in rows: out.append(f"• Resolución {r['numero']} — {r['titulo']}\n  URL: {r['url']}\n")
    return "\n".join(out)

@mcp.tool()
def tgr_buscar_circular(query: str, limite: int = 5, offset: int = 0) -> str:
    """TGR — Circulares."""
    query=query.strip()
    if not query: return "Error: consulta vacía."
    cached=_db._search_generic("tgr_circulares","tgr_circulares_fts",query,limite,offset)
    if cached:
        out=[f"TGR Circulares para '{query}' ({len(cached)} cache):",""]
        for r in cached: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
        return "\n".join(out)
    rows=_tgr_mod.buscar_circular(query, limite + offset)[offset: offset + limite]
    for r in rows: _db._upsert_generic("tgr_circulares","tgr_circulares_fts",f"tgr_cir:{r['numero']}",r["numero"],r["titulo"],r["url"])
    out=[f"TGR Circulares para '{query}' ({len(rows)}):",""]
    for r in rows: out.append(f"• Circular {r['numero']} — {r['titulo']}\n  URL: {r['url']}\n")
    return "\n".join(out)

@mcp.tool()
def tgr_buscar_fallo(query: str, limite: int = 5, offset: int = 0) -> str:
    """TGR — Fallos de cobranza, apelaciones y reposiciones, con texto explicativo por caso.

    Para los primeros 3 resultados trae el contenido completo de la noticia/fallo
    oficial y lo presenta con contexto jurídico (qué resolvió la corte y qué
    significa). Los demás se listan con título y link.
    """
    query=query.strip()
    if not query: return "Error: consulta vacía."
    cached=_db._search_generic("tgr_fallos","tgr_fallos_fts",query,limite,offset)
    if cached:
        rows=[dict(r) for r in cached]
    else:
        rows=_tgr_mod.buscar_fallo(query, limite + offset)[offset: offset + limite]
        for r in rows:
            _db._upsert_generic("tgr_fallos","tgr_fallos_fts",f"tgr_fallo:{r['numero']}",r["numero"],r["titulo"],r["url"],r.get("resultado",""))

    out=["TESORERÍA GENERAL DE LA REPÚBLICA (TGR)",
         _narr_encabezado("TGR", query, len(rows)), ""]
    for i, r in enumerate(rows):
        cuerpo = ""
        if i < 3 and r.get("url"):  # detalle completo solo para los 3 primeros (latencia)
            try:
                import httpx as _hx
                resp = _hx.get(r["url"], timeout=15,
                               headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
                               follow_redirects=True)
                if resp.status_code == 200:
                    plano = _limpiar_html(resp.text)
                    cuerpo = _extraer_noticia(plano)["cuerpo"]
            except Exception:
                pass
        res = r.get("resultado") or ""
        if cuerpo:
            out.append(_narr_noticia_tgr(r["titulo"], r["url"], "", cuerpo, res))
        else:
            out.append(f"• {r['titulo']}")
            if res:
                out.append(f"  Resultado: {res}")
            out.append(f"  Fuente oficial: {r['url']}")
        out.append("")
    matiz = ("Nota: los comunicados TGR reflejan la posición de esa institución; "
             "verifica siempre el fallo original en la Corte respectiva.") if rows else ""
    out.append(_narr_conclusion(query, len(rows), matiz))
    return "\n".join(out)

@mcp.tool()
def inapi_buscar_marca(query: str, limite: int = 5, offset: int = 0, modo: str = "contenga", clase: str | None = None) -> str:
    """INAPI — Buscador de marcas (Ley 19.039). Modos: contenga|exacta|comience|termine. Clase Niza opcional."""
    query=query.strip()
    if not query: return "Error: consulta vacía."
    cached=_db._search_generic("inapi_marcas","inapi_marcas_fts",query,limite,offset)
    if cached:
        out=[f"INAPI Marcas para '{query}' ({len(cached)} cache):",""]
        for r in cached: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
        return "\n".join(out)
    rows=_inapi_mod.buscar_marca(query, modo, clase, limite + offset)[offset: offset + limite]
    for r in rows: _db._upsert_generic("inapi_marcas","inapi_marcas_fts",f"inapi:{r['numero']}",r["numero"],r["titulo"],r["url"])
    out=[f"INAPI Marcas para '{query}' ({len(rows)}):",""]
    for r in rows:
        detalle = f"• Marca {r['numero']} — {r['titulo']}"
        if r.get("titular"):
            detalle += f"\n  Titular: {r['titular']}"
        if r.get("estado"):
            detalle += f"\n  Estado: {r['estado']}"
        if r.get("fuente"):
            detalle += f"\n  Fuente: {r['fuente']}"
        detalle += f"\n  URL: {r['url']}\n"
        out.append(detalle)
    out.append("🔗 https://buscadormarcas.inapi.cl/Marca/BuscarMarca.aspx")
    return "\n".join(out)

@mcp.tool()
def inapi_estados_diarios(fecha: str | None = None, limite: int = 5) -> str:
    """INAPI — Estados Diarios Marcas (notificación oficial Art. 13). Fecha DD-MM-AAAA o vacío para últimos."""
    try:
        rows=_inapi_mod.estados_diarios(fecha, limite)
    except Exception as exc:  # noqa: BLE001
        return f"Error INAPI Estados: {exc}"
    out=[f"INAPI Estados Diarios ({len(rows)}):",""]
    for r in rows: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
    return "\n".join(out)

@mcp.tool()
def tdpi_jurisprudencia(query: str, limite: int = 5, offset: int = 0) -> str:
    """TDPI — Jurisprudencia marcaria (apelaciones INAPI, Boletines)."""
    query=query.strip()
    if not query: return "Error: consulta vacía."
    cached=_db._search_generic("tdpi_juris","tdpi_juris_fts",query,limite,offset)
    if cached:
        out=[f"TDPI Jurisprudencia para '{query}' ({len(cached)} cache):",""]
        for r in cached: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
        return "\n".join(out)
    rows=_inapi_mod.tdpi_jurisprudencia(query, limite + offset)[offset: offset + limite]
    for r in rows: _db._upsert_generic("tdpi_juris","tdpi_juris_fts",f"tdpi:{r['numero']}",r["numero"],r["titulo"],r["url"])
    out=[f"TDPI Jurisprudencia para '{query}' ({len(rows)}):",""]
    for r in rows: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
    return "\n".join(out)

@mcp.tool()
def superir_buscar_boletin(query: str, limite: int = 5, offset: int = 0) -> str:
    """Superir — Boletín Concursal (Ley 20.720, renegociación/liquidación)."""
    query=query.strip()
    if not query: return "Error: consulta vacía."
    cached=_db._search_generic("superir_boletin","superir_boletin_fts",query,limite,offset)
    if cached:
        out=[f"Superir Boletín para '{query}' ({len(cached)} cache):",""]
        for r in cached: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
        return "\n".join(out)
    rows=_superir_mod.buscar_boletin(query, limite + offset)[offset: offset + limite]
    for r in rows: _db._upsert_generic("superir_boletin","superir_boletin_fts",f"superir:{r['numero']}",r["numero"],r["titulo"],r["url"])
    out=[f"Superir Boletín para '{query}' ({len(rows)}):",""]
    for r in rows: out.append(f"• {r['numero']} — {r['titulo']}\n  URL: {r['url']}\n")
    out.append("🔗 https://www.boletinconcursal.cl/boletin/verificacion")
    return "\n".join(out)

@mcp.tool()
def sma_buscar_sancionatorio(query: str, limite: int = 5, offset: int = 0) -> str:
    """SMA — SNIFA sancionatorio (fiscalización ambiental, multas hasta 10k UTA)."""
    query=query.strip()
    if not query: return "Error: consulta vacía."
    cached=_db._search_generic("sma_sancionatorio","sma_sancionatorio_fts",query,limite,offset)
    if cached:
        out=[f"SMA Sancionatorio para '{query}' ({len(cached)} cache):",""]
        for r in cached: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
        return "\n".join(out)
    rows=_sma_mod.buscar_sancionatorio(query, limite + offset)[offset: offset + limite]
    for r in rows: _db._upsert_generic("sma_sancionatorio","sma_sancionatorio_fts",f"sma:{r['numero']}",r["numero"],r["titulo"],r["url"])
    out=[f"SMA Sancionatorio para '{query}' ({len(rows)}):",""]
    for r in rows: out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
    out.append("🔗 https://snifa.sma.gob.cl/Sancionatorio")
    return "\n".join(out)

@mcp.tool()
def salud_fuentes(limite_ms: int = 5000) -> str:
    """Verifica conectividad de todos los endpoints oficiales chilenos.
    
    Chequea si cada fuente (BCN, SII, TGR, PJUD, CGR, etc.) está online,
    bloqueada por WAF, o caída. Útil para diagnosticar problemas de acceso
    antes de iniciar una búsqueda."""
    try:
        return _verificar_fuentes(limite_ms=limite_ms)
    except Exception as exc:
        return f"Error verificando fuentes: {exc}"

@mcp.tool()
def estado_vigencia(norma: str) -> str:
    """Consulta el estado de vigencia de una norma (VIGENTE/DEROGADA/REFUNDIDA).

    Pasa N° de ley (ej '21643', '21.643') o idNorma (ej '1200096'). Lee el
    encabezado oficial de la página LeyChile: estado, norma que la derogó o
    refundió, última modificación y fecha. Usa Playwright sobre la página oficial;
    cache en memoria por 7 días (la vigencia cambia raramente).
    """
    norma = norma.strip()
    if not norma:
        return "Error: indica el número de ley o el idNorma."
    try:
        return _formatear_vigencia(_estado_vigencia(norma))
    except Exception as exc:  # noqa: BLE001
        return f"Error consultando vigencia: {exc}"


@mcp.tool()
def buscar_casos(query: str, limite: int = 5, offset: int = 0) -> str:
    """Casos reales parecidos a tu consulta (extraídos de documentos oficiales).

    A diferencia de buscar_normas (que busca por título), esto lee los hechos y
    resoluciones ya extraídos de oficios/SII, fallos TGR, dictámenes CGR y otros.
    Sirve para: '¿cómo se resolvió un caso parecido?'
    """
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    rows = _db.search_casos(query, limit=limite, offset=offset)
    if not rows:
        return (f"Sin casos extractados aún para '{query}'. "
                "Prueba primero con buscar_jurisprudencia o pide un informe de análisis. "
                "Los casos se van guardando cada vez que se descarga un documento oficial.")
    out = [f"Casos parecidos a '{query}' ({len(rows)} en base local):", ""]
    for r in rows:
        out.append(f"• {r['identificacion']}")
        out.append(f"  Organismo: {r['organismo']} | Tipo: {r['tipo']}")
        if r.get("fecha"):
            out.append(f"  Fecha: {r['fecha']}")
        if r.get("hechos"):
            out.append(f"  Hechos: {r['hechos'][:300]}...")
        if r.get("resolucion"):
            out.append(f"  Resolución: {r['resolucion'][:300]}...")
        out.append(f"  URL oficial: {r['url']}")
        out.append("")
    out.append("🔗 Estos casos vienen de documentos oficiales descargados en tiempo real.")
    return "\n".join(out)


@mcp.tool()
def guardar_memoria(nombre: str, contenido: str, tipo: str = "nota") -> str:
    """Guarda una nota permanente en tu memoria local (nunca expira).

    Tipos sugeridos: 'cliente', 'causa', 'clave', 'todo', 'nota'.
    Ejemplo: guardar_memoria('Cliente Pérez', 'Causa rol C-1234-2025, 5° Juzgado Civil Santiago. Clave acceso: xyz123', 'causa')
    Todo queda guardado SOLO en este computador, privado.
    """
    nombre = nombre.strip()
    contenido = contenido.strip()
    if not nombre or not contenido:
        return "Error: se requieren nombre y contenido."
    _guardar_nota(nombre, contenido, tipo)
    return f"✅ Guardado permanentemente: [{tipo}] {nombre} ({_fecha_hoy()}). Recuperable con consultar_memoria."


@mcp.tool()
def consultar_memoria(query: str, limite: int = 10) -> str:
    """Busca en tu memoria: notas guardadas + conversaciones anteriores.

    Úsala al inicio de una sesión para retomar contexto ('¿qué estábamos viendo del cliente Pérez?').
    Búsqueda por texto — milisegundos.
    """
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    res = _consultar_memoria(query, limite)
    return _formatear_memoria(res, query)


@mcp.tool()
def historial_conversacion(limite: int = 20) -> str:
    """Últimas interacciones registradas (preguntas/respuestas), en orden cronológico.

    Útil para recordar qué se estaba haciendo antes de cerrar la sesión anterior.
    Cache circular: conserva los últimos 500 mensajes (30 días).
    """
    hist = _historial_reciente(limite)
    if not hist:
        return ("Memoria vacía aún. Cada consulta que hagas queda registrada automáticamente; "
                "también puedes guardar notas con guardar_memoria.")
    out = [f"Últimas {len(hist)} interacciones:", ""]
    for m in hist:
        quien = {"usuario": "👤 Abogado", "asistente": "🤖 Asistente", "consulta_auto": "🔍 Auto"}.get(m["rol"], m["rol"])
        out.append(f"[{m['fecha']}] {quien}:")
        out.append(f"  {m['contenido'][:400]}")
        out.append("")
    return "\n".join(out)


@mcp.tool()
def registrar_interaccion(pregunta: str, respuesta: str) -> str:
    """Registra un intercambio importante en la memoria persistente.

    El asistente debe usarla al cierre de una tarea relevante para que quede
    disponible en sesiones futuras. La memoria es circular (máx 500 mensajes).
    """
    if not pregunta.strip() or not respuesta.strip():
        return "Error: pregunta y respuesta son obligatorias."
    id1 = _registrar_mensaje("usuario", pregunta)
    id2 = _registrar_mensaje("asistente", respuesta)
    return f"✅ Registrado en memoria (ids {id1}, {id2}). Disponible en futuras sesiones con consultar_memoria o historial_conversacion."


@mcp.tool()
def resumen_trabajo(dias: int = 7) -> str:
    """Resumen de actividad reciente: días trabajados, consultas por día, notas guardadas."""
    try:
        dias = max(1, min(int(dias), 30))
    except ValueError:
        dias = 7
    return _formatear_resumen(_resumen_trabajo(dias))


@mcp.tool()
def vigilancia_crear(nombre: str, condicion: str, fuentes: list[str]) -> str:
    """Crea una vigilancia legal automática (estilo Monitor): una condición en lenguaje natural sobre fuentes oficiales.

    fuentes válidas: cgr, tc, tgr, sii, diario_oficial, normas.
    Ejemplo: vigilancia_crear(nombre='datos_salud', condicion='nuevas sentencias o normas sobre protección de datos de salud', fuentes=['tc','cgr','normas'])
    """
    res = _vig_crear(nombre, condicion, fuentes)
    if not res["ok"]:
        return f"ERROR: {res['error']}"
    return (f"✅ Vigilancia '{res['nombre']}' creada el {res['creada']}.\n"
            f"Condición: \"{condicion}\"\n"
            f"Fuentes: {', '.join(fuentes)}\n\n"
            "Ejecute vigilancia_ejecutar para la primera revisión. Cada ejecución detecta "
            "solo publicaciones NUEVAS (dedupe por URL) y las entrega en informe narrativo "
            "para que usted filtre contra la condición.")


@mcp.tool()
def vigilancia_listar() -> str:
    """Lista tus vigilancias legales con estado, última ejecución y novedades pendientes."""
    return _vig_fmt_listado(_vig_listar())


@mcp.tool()
def vigilancia_ejecutar(nombre: str, limite_por_fuente: int = 10) -> str:
    """Ejecuta una vigilancia: consulta sus fuentes oficiales con palabras clave derivadas de la condición y reporta SOLO las novedades no vistas antes (informe narrativo + links oficiales)."""
    if limite_por_fuente < 1 or limite_por_fuente > 30:
        limite_por_fuente = 10
    res = _vig_ejecutar(nombre, limite_por_fuente)
    return _vig_fmt_informe(res)


@mcp.tool()
def vigilancia_historial(nombre: str, solo_nuevos: bool = True, limite: int = 30) -> str:
    """Ítems históricos detectados por una vigilancia. solo_nuevos=True muestra solo los aún sin revisar."""
    items = _vig_historial(nombre, solo_nuevos, max(1, min(limite, 100)))
    return _vig_fmt_historial(nombre, items, solo_nuevos)


@mcp.tool()
def vigilancia_marcar_revisados(nombre: str) -> str:
    """Marca todas las novedades de una vigilancia como revisadas (estado 'visto')."""
    n = _vig_marcar(nombre)
    if n == 0:
        return f"No había novedades sin revisar en '{nombre}'."
    return f"✅ {n} ítem(s) marcados como revisados en '{nombre}'."


@mcp.tool()
def vigilancia_eliminar(nombre: str) -> str:
    """Elimina una vigilancia y todo su historial de ítems."""
    res = _vig_eliminar(nombre)
    return f"✅ Vigilancia '{nombre}' eliminada (incluye su historial)." if res["ok"] else f"ERROR: {res['error']}"


@mcp.tool()
def vigilancia_pausar(nombre: str, activar: bool = False) -> str:
    """Pausa (activar=False) o reactiva (activar=True) una vigilancia. Las pausadas no se ejecutan."""
    res = _vig_pausar(nombre, activar)
    if not res["ok"]:
        return f"ERROR: {res['error']}"
    estado = "reactivada" if activar else "pausada"
    return f"✅ Vigilancia '{nombre}' {estado}."


@mcp.tool()
def ayuda_acceso_abogado() -> str:
    """Devuelve todos los links oficiales."""
    return (
        "🔗 Links oficiales (todo público, sin registro):\n\n"
        "1. LeyChile — texto oficial:\n"
        "   https://www.bcn.cl/leychile/navegar?idNorma=1200096  (ejemplo Ley Karin)\n\n"
        "2. Contraloría — dictámenes:\n"
        "   https://www.contraloria.cl/web/cgr/dictamenes-y-pronunciamientos\n\n"
        "3. Poder Judicial — jurisprudencia:\n"
        "   https://www.pjud.cl/portal-unificado-sentencias\n\n"
        "4. SciELO Chile — doctrina:\n"
        "   https://search.scielo.org/?q=derecho&lang=es\n\n"
        "5. Dirección del Trabajo:\n"
        "   https://www.dt.gob.cl/legislacion/1624/w3-channel.html\n\n"
        "6. Diario Oficial:\n"
        "   https://www.diariooficial.interior.gob.cl/buscador/solicitud/buscar?texto=<query>\n"
    )


@mcp.tool()
def expediente_indexar(nombre: str, carpeta: str, reemplazar: bool = True) -> str:
    """Indexa una carpeta local (recursiva) con PDF, DOCX, TXT o MD para preguntar sobre el caso. Todo queda local en SQLite — los documentos nunca salen del computador.

    Ejemplo: expediente_indexar(nombre='caso_rocio', carpeta='/Users/yo/Desktop/caso')
    """
    return _exp_fmt_index(_exp_indexar(nombre, carpeta, reemplazar))


@mcp.tool()
def expediente_preguntar(nombre: str, pregunta: str, limite: int = 6) -> str:
    """Responde una pregunta buscando DENTRO del expediente indexado. Devuelve fragmentos textuales con el documento fuente citado (no interpretaciones)."""
    if limite < 1 or limite > 20:
        limite = 6
    return _exp_fmt_respuesta(_exp_preguntar(nombre, pregunta, limite))


@mcp.tool()
def expediente_timeline(nombre: str, limite: int = 40) -> str:
    """Construye la línea de tiempo del expediente: fechas detectadas en los documentos (DD-MM-AAAA, DD/MM/AAAA o '15 de enero de 2026'), ordenadas cronológicamente con su contexto."""
    if limite < 1 or limite > 200:
        limite = 40
    return _exp_fmt_timeline(_exp_timeline(nombre, limite))


@mcp.tool()
def expediente_partes(nombre: str) -> str:
    """Identifica partes del expediente: RUTs (confiables) y nombres candidatos por patrón de capitalización, con frecuencia y contexto."""
    return _exp_fmt_partes(_exp_partes(nombre))


@mcp.tool()
def expediente_listar() -> str:
    """Lista tus expedientes indexados con tamaño y ubicación."""
    return _exp_fmt_listado(_exp_listar())


@mcp.tool()
def expediente_eliminar(nombre: str) -> str:
    """Elimina un expediente indexado (los archivos originales NO se tocan)."""
    res = _exp_eliminar(nombre)
    return f"✅ Expediente '{nombre}' eliminado (archivos originales intactos)." if res["ok"] else f"ERROR: {res['error']}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="HTTP streamable en :8000")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.http:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
