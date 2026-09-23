"""Servidor MCP de investigación legal chilena K-LegalChile.

Herramientas (93):
- buscar_normas: legislación con filtros fecha/tipo/materia + paginación offset + FTS body + DD-MM-AAAA.
- obtener_texto_norma: texto completo XML LeyChile con chunk/offset.
- obtener_articulo_texto: artículo (e inciso) exacto, corte forense del texto oficial (ordinal º/°; art. 2 ≠ art. 20).
- estado_vigencia: VIGENTE/DEROGADA/REFUNDIDA leyendo el encabezado legal oficial renderizado.
- buscar_casos: casos reales parecidos extraídos de documentos oficiales (hechos/resolución).
- guardar_memoria / consultar_memoria / historial_conversacion / registrar_interaccion / resumen_trabajo: memoria persistente del abogado (cerebro local, cache circular 500, retención 30 días).
- buscar_dictamenes: CGR + BCN.
- estado_corpus_lex / buscar_dictamenes_corpus / estado_criterio / ficha_dictamen_doctrinal / obtener_sentencia_cadena / boletin_criterios_nuevos: corpus CGR local K-LegalChile (búsqueda semántica, estado del criterio, cadena judicial, ficha doctrinal y boletín de criterios nuevos).
- buscar_jurisprudencia: BCN + CGR + TC + PJUD público.
- buscar_doctrina: artículos (30k) + fallback normas.
- historial_norma: vigencia y relaciones (hasVersion/modifiesTo).
- citar_norma / citar_json: citas texto y JSON con DD-MM-AAAA + URL LeyChile.
- exportar_norma: Word (.docx) y PDF (.pdf) con formato profesional.
- indexar_semantico / buscar_semantico / estado_indexacion: embeddings MiniLM multilingüe (Fase 3).
- generar_escrito / generar_escrito_desde_investigacion / tipos_escrito_disponibles: redacción de escritos jurídicos (Fase 4).
- iniciar_workflow / continuar_workflow / estado_workflow / listar_workflows: prompt multi-etapa planificar→investigar→redactar→autoverificar (Fase 5).
- jpl_buscar_ley / jpl_buscar_articulo / jpl_verificar_vigencia / jpl_listar_leyes / jpl_listar_ordenanzas / jpl_buscar_ordenanza / jpl_buscar_texto / jpl_generar_documento / jpl_estado: corpus JPL (Ley 18.287 + ordenanzas 344 comunas, auto-activo si data/jpl/corpus.db existe).
- kb_search / kb_get / kb_status: índice FTS5 searchable del corpus legal (leyes, ordenanzas 344 comunas, manuales de formatos y plazos).
- buscar_scielo / buscar_dt / buscar_diario_oficial / buscar_suseso / buscar_tc / buscar_historia_ley / buscar_sii / buscar_cmf / buscar_tdlc / buscar_cplt / buscar_datos_gob: fuentes sectoriales oficiales.
- buscar_todo: búsqueda multi-fuente paralela real (ThreadPoolExecutor 6 workers).
- vigilancia_crear / vigilancia_listar / vigilancia_ejecutar / vigilancia_historial / vigilancia_marcar_revisados / vigilancia_eliminar / vigilancia_pausar: monitor legal automático (condición en lenguaje natural + fuentes oficiales, dedupe e informe narrativo).
- expediente_indexar / expediente_preguntar / expediente_timeline / expediente_partes / expediente_listar / expediente_eliminar: análisis de expedientes propios (carpeta PDF/DOCX/TXT → FTS5 local, respuestas con citas al documento, línea de tiempo y partes).
- expediente_citas_legales: DERECHO INVOCADO del expediente — citas con precisión de artículo e inciso, ubicación en el expediente y verificación contra la base nacional local.
- expediente_vigencia_citas: estado de vigencia (VIGENTE/DEROGADA/REFUNDIDA) de cada norma citada en el expediente, con advertencia intertemporal.
- expediente_plazos: plazos procesales detectados en los documentos, computados (arts. 38/40 CPC, 66 COT) y estado frente a hoy.
- computar_plazo_procesal: cómputo de plazos chilenos (desde notificación, hábiles/corridos, feriado judicial, prórroga vencimiento inhábil) con fundamentos.
- analizar_consulta: análisis jurídico con formato K-LegalChile (respuesta directa, artículos literales, casos por tipo, criterios, lo no cubierto), ruteado por índice de cobertura.
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
import re
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from .contraloria import buscar_cgr, CGRNoDisponible
from .db import NormasDB
from .indice_cobertura import clasificar as _clasificar
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
    citas_normativas as _exp_citas,
    vigencia_citas as _exp_vigencia_citas,
    plazos_expediente as _exp_plazos,
    formatear_plazos_expediente as _exp_fmt_plazos,
    formatear_indexacion as _exp_fmt_index,
    formatear_respuesta as _exp_fmt_respuesta,
    formatear_timeline as _exp_fmt_timeline,
    formatear_partes as _exp_fmt_partes,
    formatear_listado as _exp_fmt_listado,
    formatear_citas as _exp_fmt_citas,
    formatear_vigencias as _exp_fmt_vigencias,
)
from .citas import extraer_articulo as _extraer_articulo
from .plazos import (
    computar_plazo as _computar_plazo,
    parsear_fecha_cl as _parsear_fecha_cl,
    formatear_plazo as _fmt_plazo,
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
from .fuentes_externas import buscar_fne as _buscar_fne
from .fuentes_externas import buscar_historia_ley as _buscar_historia
from .fuentes_externas import buscar_scielo as _buscar_scielo
from .fuentes_externas import buscar_sii as _buscar_sii
from .fuentes_externas import buscar_suseso as _buscar_suseso
from .fuentes_externas import buscar_tc as _buscar_tc
from .fuentes_externas import buscar_tdlc as _buscar_tdlc
from .fuentes_externas import buscar_tribunal_ambiental as _buscar_tribunal_ambiental
from .semantico import (
    indexar_semantico as _sem_indexar,
    buscar_semantico as _sem_buscar,
    estado_indexacion as _sem_estado,
    formatear_resultado_semantico as _sem_fmt,
)
from .criterios import (
    marcar_estados as _crit_marcar,
    estado_principal as _crit_estado,
    ficha_dictamen as _crit_ficha,
    boletin_criterios as _crit_boletin,
    materia_de as _crit_materia,
    url_oficial_dictamen as _crit_url_oficial,
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
from pathlib import Path as _Path
# JPL — import condicional (solo si corpus disponible, pero tools siempre registradas con mensaje degradado)
try:
    from .jpl import db as _jpl_db
    from .jpl import generator as _jpl_gen
    _JPL_AVAILABLE = True
except Exception:
    _jpl_db = None  # type: ignore
    _jpl_gen = None  # type: ignore
    _JPL_AVAILABLE = False

def _jpl_check() -> tuple[bool, str]:
    """Verifica si JPL está instalado y FTS listo. Devuelve (ok, mensaje)."""
    if not _JPL_AVAILABLE or _jpl_db is None:
        return False, "JPL no instalado. Ejecuta: python scripts/install_jpl.py (requiere acceso al repo privado K-LegalJPL)."
    # Existe corpus.db.zlib o corpus.db ?
    jpl_root = _Path(__file__).resolve().parents[2] / "data" / "jpl"
    has_zst = (jpl_root / "corpus.db.zlib").exists()
    has_db = (jpl_root / "corpus.db").exists()
    alt_zst = _Path(__file__).resolve().parents[3] / "K-LegalJPL" / "corpus.db.zlib"
    alt_db = _Path(__file__).resolve().parents[3] / "K-LegalJPL" / "corpus.db"
    if not (has_zst or has_db or alt_zst.exists() or alt_db.exists()):
        return False, "JPL no instalado. Ejecuta: python scripts/install_jpl.py (requiere acceso al repo privado K-LegalJPL)."
    return True, ""

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
                return buscar_semantico(query, top_k=limite)
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
    salida.append("• PJUD: https://juris.pjud.cl/busqueda/lista_buscadores")
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


# ── JPL — corpus de Juzgado de Policía Local (auto-activo si data/jpl/corpus.db existe) ──

@mcp.tool()
def jpl_buscar_ley(consulta: str, limite: int = 10) -> str:
    """Busca un término en todas las leyes JPL del corpus (tránsito, alcoholes, consumidor, rentas, aseo, etc.). Corpus nacional JPL."""
    ok, msg = _jpl_check()
    if not ok:
        return msg
    consulta = consulta.strip()
    if not consulta:
        return "Error: consulta vacía."
    try:
        res = _jpl_db.buscar_ley(consulta, limite=min(limite, 20))  # type: ignore
    except Exception as e:
        return f"Error JPL buscar_ley: {e}"
    if not res:
        return f"JPL: sin resultados para '{consulta}'. Prueba términos más amplios o verifica con jpl_buscar_texto."
    out = [f"JPL — LEYES para '{consulta}' ({len(res)}):", ""]
    for r in res[:limite]:
        ley = r.get("ley","")
        titulo = r.get("titulo","")
        out.append(f"• {ley} — {titulo}")
        for ex in r.get("extractos",[])[:2]:
            out.append(f"  → \"{ex[:180]}...\"")
        out.append(f"  Coincidencias: {r.get('coincidencias',0)}")
        out.append("")
    out.append("Fuente: corpus JPL local (Ley 18.287 + 53 leyes vigentes). Usa jpl_buscar_articulo(ley, articulo) para el texto exacto.")
    return "\n".join(out)


@mcp.tool()
def jpl_buscar_articulo(ley: str, articulo: int) -> str:
    """Extrae el texto exacto de un artículo de una ley JPL (ej. ley='18.287', articulo=14)."""
    ok, msg = _jpl_check()
    if not ok:
        return msg
    ley = ley.strip()
    if not ley:
        return "Error: ley vacía."
    try:
        res = _jpl_db.buscar_articulo(ley, articulo)  # type: ignore
    except Exception as e:
        return f"Error JPL buscar_articulo: {e}"
    if not res:
        return f"JPL: artículo {articulo} no encontrado en '{ley}'. Verifica con jpl_verificar_vigencia('{ley}') o jpl_buscar_ley('{ley}')."
    out = [f"JPL — ARTÍCULO {articulo} de {ley}:", ""]
    for item in res:
        texto = item.get("texto","")[:3000]
        num = item.get("articulo", articulo)
        out.append(f"Art. {num}: {texto}")
        for n in item.get("numerales",[]):
            if n.get("numeral"):
                out.append(f"  N° {n['numeral']}: {n['texto'][:400]}...")
        out.append("")
    out.append("Fuente: corpus JPL local. Verifica vigencia con jpl_verificar_vigencia antes de citar.")
    return "\n".join(out)


@mcp.tool()
def jpl_verificar_vigencia(ley: str) -> str:
    """Devuelve metadatos de vigencia de una ley JPL: tipo, número, organismo, versión BCN vigente, estado (no derogado/derogado), idNorma."""
    ok, msg = _jpl_check()
    if not ok:
        return msg
    ley = ley.strip()
    if not ley:
        return "Error: ley vacía."
    try:
        res = _jpl_db.verificar_vigencia(ley)  # type: ignore
    except Exception as e:
        return f"Error JPL verificar_vigencia: {e}"
    if not res:
        return f"JPL: ley '{ley}' no encontrada en el corpus."
    out = [f"JPL — VIGENCIA de '{ley}':", ""]
    for m in res:
        for k, v in m.items():
            if v:
                out.append(f"• {k}: {v}")
        out.append("")
    return "\n".join(out)


@mcp.tool()
def jpl_listar_leyes() -> str:
    """Lista todas las leyes JPL disponibles en el corpus (53 leyes con metadatos)."""
    ok, msg = _jpl_check()
    if not ok:
        return msg
    try:
        res = _jpl_db.listar_leyes()  # type: ignore
    except Exception as e:
        return f"Error JPL listar_leyes: {e}"
    out = [f"JPL — LEYES en corpus ({len(res)}):", ""]
    for r in res:
        out.append(f"• {r.get('archivo','')} — {r.get('tipo','')} N° {r.get('numero','')} — {r.get('estado','')} — idNorma {r.get('idNorma','')}")
    return "\n".join(out)


@mcp.tool()
def jpl_listar_ordenanzas(municipalidad: str | None = None) -> str:
    """Lista ordenanzas JPL. Sin argumento: todas las municipalidades con conteo. Con municipalidad: ordenanzas de esa comuna."""
    ok, msg = _jpl_check()
    if not ok:
        return msg
    try:
        res = _jpl_db.listar_ordenanzas(municipalidad)  # type: ignore
    except Exception as e:
        return f"Error JPL listar_ordenanzas: {e}"
    if not res:
        return f"JPL: sin ordenanzas para '{municipalidad}'." if municipalidad else "JPL: corpus de ordenanzas vacío."
    if municipalidad is None:
        out = [f"JPL — ORDENANZAS por municipalidad ({len(res)} comunas):", ""]
        for r in res:
            out.append(f"• {r.get('municipalidad','')}: {r.get('ordenanzas',0)} ordenanzas")
        return "\n".join(out)
    out = [f"JPL — ORDENANZAS de {municipalidad} ({len(res)}):", ""]
    for r in res[:50]:
        out.append(f"• {r.get('archivo','')} — N° {r.get('numero','')} — {r.get('estado','')}")
    if len(res) > 50:
        out.append(f"\n... y {len(res)-50} más. Usa jpl_buscar_ordenanza('{municipalidad}', 'materia') para filtrar.")
    return "\n".join(out)


@mcp.tool()
def jpl_buscar_ordenanza(municipalidad: str, materia: str, limite: int = 10) -> str:
    """Busca una materia dentro de las ordenanzas de una municipalidad JPL (ej. 'ruidos', 'aseo', 'ferias libres')."""
    ok, msg = _jpl_check()
    if not ok:
        return msg
    municipalidad = municipalidad.strip()
    materia = materia.strip()
    if not municipalidad or not materia:
        return "Error: municipalidad y materia son requeridos."
    try:
        res = _jpl_db.buscar_ordenanza(municipalidad, materia, limite=min(limite,20))  # type: ignore
    except Exception as e:
        return f"Error JPL buscar_ordenanza: {e}"
    if not res:
        return f"JPL: sin resultados para '{materia}' en {municipalidad}. Prueba jpl_listar_ordenanzas('{municipalidad}') para ver disponibles."
    out = [f"JPL — ORDENANZA '{materia}' en {municipalidad} ({len(res)}):", ""]
    for r in res[:limite]:
        out.append(f"• {r.get('archivo','')} — coincidencias: {r.get('coincidencias',0)}")
        for ex in r.get("extractos",[])[:2]:
            out.append(f"  → \"{ex[:180]}...\"")
        out.append("")
    return "\n".join(out)


@mcp.tool()
def jpl_buscar_texto(consulta: str, limite: int = 10) -> str:
    """Búsqueda full-text en TODO el corpus JPL a la vez (leyes + ordenanzas 344 comunas + manuales)."""
    ok, msg = _jpl_check()
    if not ok:
        return msg
    consulta = consulta.strip()
    if not consulta:
        return "Error: consulta vacía."
    try:
        res = _jpl_db.buscar_texto(consulta, limite=min(limite,20))  # type: ignore
    except Exception as e:
        return f"Error JPL buscar_texto: {e}"
    if not res:
        return f"JPL: sin resultados para '{consulta}'."
    out = [f"JPL — BÚSQUEDA GLOBAL '{consulta}' ({len(res)}):", ""]
    for r in res[:limite]:
        tipo = r.get("tipo","")
        ref = r.get("referencia","")
        out.append(f"• [{tipo}] {ref} — coincidencias: {r.get('coincidencias',0)}")
        for ex in r.get("extractos",[])[:2]:
            out.append(f"  → \"{ex[:180]}...\"")
        out.append("")
    return "\n".join(out)


@mcp.tool()
def jpl_generar_documento(tipo: str, datos: str, formato: str = "md") -> str:
    """Genera documento judicial JPL (sentencia, resolucion, oficio, certificado, exhorto, comparendo, plazo). Datos es JSON string con {rol, comuna, denunciado, rut, domicilio, hecho, ley, articulo, dia, mes, ano}."""
    ok, msg = _jpl_check()
    if not ok:
        return msg
    tipo = tipo.strip()
    if not tipo:
        return "Error: tipo es requerido. Válidos: sentencia, resolucion, oficio, certificado, exhorto, comparendo, plazo."
    if _jpl_gen is None:
        return "Error: generador JPL no disponible."
    try:
        datos_dict = json.loads(datos) if isinstance(datos, str) and datos.strip().startswith("{") else {}
        if isinstance(datos, dict):  # por si FastMCP ya deserializa
            datos_dict = datos  # type: ignore
    except Exception:
        datos_dict = {}
    # Si datos viene como string JSON pero el tool lo recibe ya parseado, manejar ambos
    if isinstance(datos, str) and not datos.strip().startswith("{"):
        # datos es JSON string mal formado, intentar parsear igual
        try:
            datos_dict = json.loads(datos)
        except Exception:
            return f"Error: datos debe ser JSON válido. Recibido: {datos[:200]}"
    try:
        res = _jpl_gen.generar(tipo, datos_dict, formato)  # type: ignore
    except Exception as e:
        return f"Error JPL generar_documento: {e}"
    if "error" in res:
        return f"JPL generar_documento error: {res['error']}"
    out = [f"JPL — DOCUMENTO '{tipo}' generado:", ""]
    out.append(res.get("documento_md",""))
    out.append("")
    ver = res.get("verificacion",{})
    if ver:
        out.append(f"Verificación: {ver.get('advertencia','')}")
        out.append(f"Score: {ver.get('score','')}")
    exp = res.get("export",{})
    if exp and exp.get("ruta_md"):
        out.append(f"Ruta: {exp.get('ruta_md')}")
    if exp and exp.get("ruta_docx"):
        out.append(f"Ruta DOCX: {exp.get('ruta_docx')}")
    return "\n".join(out)


@mcp.tool()
def jpl_estado() -> str:
    """Reporta estado del corpus JPL: disponible, tamaño, leyes y ordenanzas cargadas, FTS listo."""
    if not _JPL_AVAILABLE or _jpl_db is None:
        return "JPL no instalado. Ejecuta: python scripts/install_jpl.py"
    jpl_root = _Path(__file__).resolve().parents[2] / "data" / "jpl"
    has_zst = (jpl_root / "corpus.db.zlib").exists()
    has_db = (jpl_root / "corpus.db").exists()
    alt_zst = _Path(__file__).resolve().parents[3] / "K-LegalJPL" / "corpus.db.zlib"
    alt_db = _Path(__file__).resolve().parents[3] / "K-LegalJPL" / "corpus.db"
    lines = ["JPL — ESTADO del corpus:", ""]
    lines.append(f"• data/jpl/corpus.db.zlib: {'✅ ' + str((jpl_root / 'corpus.db.zlib').stat().st_size/1024/1024)[:4] + ' MB' if has_zst else '❌ no existe'}")
    lines.append(f"• data/jpl/corpus.db: {'✅ ' + str((jpl_root / 'corpus.db').stat().st_size/1024/1024)[:4] + ' MB' if has_db else '❌ no existe (se genera al primer uso)'}")
    lines.append(f"• K-LegalJPL sibling: {'✅ disponible' if alt_zst.exists() or alt_db.exists() else '❌ no clonado'}")
    if not (has_zst or has_db or alt_zst.exists() or alt_db.exists()):
        lines.append("")
        lines.append("Instala JPL con: python scripts/install_jpl.py")
        lines.append("→ requiere acceso al repo privado K-LegalJPL (token GitHub).")
        return "\n".join(lines)
    # Intentar contar
    try:
        _jpl_db._ensure_db()  # type: ignore
        leyes = _jpl_db.listar_leyes()  # type: ignore
        ordenanzas = _jpl_db.listar_ordenanzas(None)  # type: ignore
        total_ord = sum(r.get("ordenanzas",0) for r in ordenanzas) if ordenanzas and "ordenanzas" in ordenanzas[0] else len(ordenanzas)
        lines.append(f"• Leyes en corpus: {len(leyes)} (ej. 18.287, 18.290, 19.925, ...)")
        lines.append(f"• Ordenanzas: {total_ord} en {len(ordenanzas) if ordenanzas else 0} comunas")
        # check FTS
        import sqlite3
        con = _jpl_db._db_conn()  # type: ignore
        try:
            cur = con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE name LIKE '%_fts'")
            fts = [r[0] for r in cur.fetchall()]
        finally:
            con.close()
        lines.append(f"• Índices FTS: {', '.join(fts) if fts else '❌ no construidos (se crean al buscar)'}")
        lines.append("")
        lines.append("JPL listo — tools disponibles: jpl_buscar_ley, jpl_buscar_articulo, jpl_buscar_texto, jpl_buscar_ordenanza, jpl_generar_documento, ...")
    except Exception as e:
        lines.append(f"• Error verificando corpus: {e}")
    return "\n".join(lines)


# ── KB — índice FTS5 searchable del corpus legal ──

def _kb_search():
    try:
        from chilean_legal_mcp.kb_search import search_kb as _s, get_document as _g, kb_status as _st
        return _s, _g, _st
    except Exception:
        return None, None, None


@mcp.tool()
def kb_search(query: str, limite: int = 10) -> str:
    """Búsqueda full-text FTS5 sobre todo el corpus legal indexado: leyes (53), ordenanzas (344 comunas) y manuales de formatos y plazos JPL."""
    _s, _g, _st = _kb_search()
    if _s is None:
        return "KB no disponible. Ejecuta: python scripts/install_jpl.py o verifica data/jpl/corpus.db."
    try:
        res = _s(query, limit=min(limite, 20))
    except Exception as e:
        return f"Error KB search: {e}"
    if not res:
        return f"KB: sin resultados para '{query}'."
    out = [f"KB — BÚSQUEDA '{query}' ({len(res)}):", ""]
    for r in res:
        out.append(f"• {r['path']}")
        out.append(f"  Score: {r['score']:.3f}")
        out.append(f"  {r['snippet']}")
        out.append("")
    return "\n".join(out)


@mcp.tool()
def kb_get(ruta: str) -> str:
    """Retorna el contenido completo de un documento del índice KB por su ruta relativa (ej: 'leyes/Ley_18287_ESTABLECE_PROCEDIMIENTO_ANTE_LOS_JUZGADOS_DE_POLICIA_LOCAL.md')."""
    _s, _g, _st = _kb_search()
    if _g is None:
        return "KB no disponible."
    texto = _g(ruta)
    if texto is None:
        return f"KB: documento '{ruta}' no encontrado. Usa kb_search para localizarlo."
    return texto


@mcp.tool()
def kb_status() -> str:
    """Reporta estado del índice KB: documentos indexados, chunks, rutas disponibles."""
    _s, _g, _st = _kb_search()
    if _st is None:
        return "KB no disponible."
    try:
        info = _st()
    except Exception as e:
        return f"Error KB status: {e}"
    out = ["KB — ESTADO del índice:", ""]
    out.append(f"• Documentos indexados: {info.get('docs', 0)}")
    out.append(f"• Chunks indexados: {info.get('chunks', 0)}")
    out.append(f"• Rutas únicas: {info.get('paths', 0)}")
    out.append("")
    out.append("Categories:")
    out.append("  • leyes/ — 53 leyes del corpus (18.287, 18.290, 19.925, 19.496, 21.020, CPC, Constitución, ...)")
    out.append("  • manuales/ — 6 manuales de formatos (sentencias, comparendos, resoluciones, oficios, certificados, plazos)")
    out.append("  • ordenanzas/ — índices por comuna (providencia, santiago, las condes, rancagua, ...)")
    out.append("")
    out.append("Tools: kb_search(query, limite), kb_get(ruta), kb_status()")
    return "\n".join(out)


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
    # Paginación: si el texto cabe en un chunk se devuelve entero; si no, por partes
    # (los cuerpos precargados íntegros pueden tener más de 8000 chars).
    total = len(texto)
    if offset or chunk != 8000 or total > chunk:
        texto = texto[offset: offset + chunk]
        texto += f"\n\n---\nMostrando {offset}-{offset+len(texto)} de {total} chars. Usa offset={offset+chunk} para siguiente chunk."
    texto += "\n\n---\n🔗 Links oficiales:\n"
    texto += f"• Ver en LeyChile: https://www.bcn.cl/leychile/navegar?idNorma={leychile_id}\n"
    texto += "• CGR: https://www.contraloria.cl/web/cgr/dictamenes-y-pronunciamientos\n"
    texto += "• PJUD: https://juris.pjud.cl/busqueda/lista_buscadores\n"
    return texto


@mcp.tool()
def buscar_dictamenes(query: str, limite: int = 10) -> str:
    """Busca dictámenes de la Contraloría General de la República por texto libre.

    Fuente: la CGR misma (contraloria.cl, en vivo). Caché local solo lo ya consultado.
    Si la CGR no responde, se informa honestamente; no se cambia de fuente a escondidas.
    """
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    local = _db.search_dictamenes(query, limit=limite)
    cgr_estado = "en vivo"
    try:
        cgr_rows = buscar_cgr(query, limite=limite)
    except CGRNoDisponible as exc:
        cgr_rows = []
        cgr_estado = f"CGR no disponible ({exc})"
    for r in cgr_rows:
        cid = f"cgr:{r['numero']}"
        _db.upsert_dictamen(cid, r["numero"], r["titulo"], None, r["url"])
        if not any(x["numero"] == r["numero"] for x in local):
            local.append({"numero": r["numero"], "titulo": r["titulo"], "fecha": None, "url": r["url"]})
    if not local:
        extra = "" if cgr_estado == "en vivo" else f"\nNOTA: la consulta en vivo falló: {cgr_estado}."
        return (f"CONCLUSIÓN: No se encontraron dictámenes para '{query}' en la Contraloría.{extra}\n"
                "Este vacío NO significa que el asunto no exista: prueba términos más amplios "
                "o revisa directamente https://www.contraloria.cl/web/cgr/dictamenes-y-pronunciamientos")
    out = ["DICTÁMENES CONTRALORÍA GENERAL DE LA REPÚBLICA",
           _narr_encabezado("CGR", query, len(local[:limite])),
           f"(fuente: {'CGR en vivo, contraloria.cl' if cgr_rows else 'caché local de consultas previas'})",
           ""]
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
    out.append("• PJUD: https://juris.pjud.cl/busqueda/lista_buscadores")
    return "\n".join(out)


@mcp.tool()
def buscar_jurisprudencia(query: str, limite: int = 10,
                          buscador: str | None = None) -> str:
    """Busca jurisprudencia chilena — fuentes públicas y legales. Búsqueda real
    en el portal oficial PJUD (juris.pjud.cl: Corte Suprema por defecto; con
    ``buscador`` se puede elegir 'corte_de_apelaciones', 'civiles', 'familia',
    'penales', 'laborales', 'cobranza', 'compendio_extranjeria',
    'lineas_jurisprudenciales' o 'salud_cs'), más BCN/TC/CGR."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    # 0. PJUD (juris.pjud.cl) — fuente primaria en vivo
    pjud_docs, pjud_total, pjud_msg = [], 0, ""
    try:
        from .pjud_juris import buscar_sentencias_pjud, PJUDNoDisponible
        pjud_docs, pjud_total = buscar_sentencias_pjud(query, limite=limite,
                                                       buscador=buscador)
    except Exception as e:
        pjud_msg = f"(PJUD en vivo no disponible: {type(e).__name__})"
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
        tc_rows = [r for r in tc_rows
                   if len(r.get("titulo", "").strip()) > 15
                   and "Buscar '" not in r.get("titulo", "")
                   and "favicon" not in r.get("url", "")]
    except Exception:
        pass
    header = f"Jurisprudencia para '{query}' (fuentes públicas):\n"
    if pjud_docs:
        header += (f"**PJUD portal oficial ({pjud_total} sentencias encontradas, "
                   f"se listan {len(pjud_docs)}):**\n")
        for d in pjud_docs:
            header += (f"\n• {d['tribunal']} {d['sala']} — Rol {d['rol']} ({d['fecha']})\n"
                       f"  {d['caratulado'][:120]}\n"
                       f"  {d['tipo_recurso']} — {d['resultado']}\n"
                       f"  {d['texto'][:400].replace('<br/>',' ')}\n"
                       f"  🔗 {d['url']}\n")
    elif pjud_msg:
        header += f"{pjud_msg}\n"
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
        "• PJUD: https://juris.pjud.cl/busqueda/lista_buscadores\n"
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
        out.append("🔗 https://www.bcn.cl/leychile/navegar?idNorma=<id> | https://juris.pjud.cl/busqueda/lista_buscadores")
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
def buscar_tribunal_ambiental(query: str, limite: int = 5) -> str:
    """Busca sentencias de los Tribunales Ambientales (1º/2º/3º) — PDFs oficiales de tribunalambiental.cl."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _buscar_tribunal_ambiental(query, limite=limite)
    except Exception as exc:  # noqa: BLE001
        return f"Error Tribunales Ambientales: {exc}"
    out = [f"TRIBUNALES AMBIENTALES — '{query}' ({len(rows)}):", ""]
    for r in rows:
        out.append(f"• {r['titulo']}")
        out.append(f"  URL: {r['url']}")
        out.append("")
    out.append("Fuente: Tribunales Ambientales (tribunalambiental.cl).")
    return "\n".join(out)


@mcp.tool()
def buscar_fne(query: str, limite: int = 5) -> str:
    """Busca jurisprudencia y actuaciones de la FNE (libre competencia)."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    try:
        rows = _buscar_fne(query, limite=limite)
    except Exception as exc:  # noqa: BLE001
        return f"Error FNE: {exc}"
    out = [f"FNE — '{query}' ({len(rows)}):", ""]
    for r in rows:
        out.append(f"• {r['titulo']}")
        out.append(f"  URL: {r['url']}")
        out.append("")
    out.append("Fuente: FNE (fne.gob.cl).")
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
    """Búsqueda multi-fuente PARALELO real: normas + CGR + jurisprudencia + SciELO + JPL (si está instalado)."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    # Detectar JPL para incluirlo en paralelo si está disponible
    _jpl_ok, _ = _jpl_check()
    max_w = 6 if _jpl_ok else 5
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_w) as ex:
        f_normas = ex.submit(buscar_normas, query, limite)
        f_cgr = ex.submit(buscar_dictamenes, query, limite)
        f_juris = ex.submit(buscar_jurisprudencia, query, limite)
        f_scielo = ex.submit(buscar_scielo, query, 3)
        f_tc = ex.submit(_buscar_dictamenes_corpus_tc, query, min(limite, 5))
        f_jpl = ex.submit(jpl_buscar_texto, query, 4) if _jpl_ok else None
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
        try:
            r_tc_corpus = f_tc.result(timeout=30)
        except Exception as e:
            r_tc_corpus = f"Error TC local: {e}"
        r_jpl = None
        if f_jpl:
            try:
                r_jpl = f_jpl.result(timeout=30)
            except Exception as e:
                r_jpl = f"Error JPL: {e}"
    partes: list[str] = [f"# Búsqueda multi-fuente (paralelo) para '{query}'\n"]
    partes.append("## 1. Legislación")
    partes.append(r_normas)
    partes.append("\n## 2. Dictámenes Contraloría")
    partes.append(r_cgr)
    partes.append("\n## 3. Sentencias Tribunal Constitucional (corpus local)")
    partes.append(r_tc_corpus)
    partes.append("\n## 4. Jurisprudencia")
    partes.append(r_juris)
    partes.append("\n## 5. Doctrina SciELO")
    partes.append(r_scielo)
    if r_jpl is not None:
        partes.append("\n## 6. JPL (corpus local: leyes + ordenanzas 344 comunas + manuales)")
        partes.append(r_jpl)
    body = _db.search_textos(query, limit=3)
    if body:
        partes.append("\n## 7. Cuerpo de normas ya cacheadas")
        for h in body:
            partes.append(f"• id {h['leychile_id']}: {h['preview'][:150]}...")
    partes.append("\n---\n🔗 Links oficiales:")
    partes.append("• LeyChile: https://www.bcn.cl/leychile/navegar?idNorma=<id>")
    partes.append("• CGR: https://www.contraloria.cl/web/cgr/dictamenes-y-pronunciamientos")
    partes.append("• TC: https://buscador.tcchile.cl/")
    partes.append("• PJUD: https://juris.pjud.cl/busqueda/lista_buscadores")
    partes.append("• SciELO: https://search.scielo.org/?q=<query>&lang=es")
    partes.append("• DT: https://www.dt.gob.cl/legislacion/1624/w3-channel.html")
    partes.append("• Diario Oficial: https://www.diariooficial.interior.gob.cl/buscador/solicitud/buscar?texto=<query>")
    return "\n".join(partes)


# ---------------------------------------------------------------------------
# Análisis de consulta — formato de respuesta K-LegalChile
# Respuesta directa primero, fundamento con texto literal, casos por tipo con
# carátula/rol/fechas/qué resolvió/por qué aplica/link, criterios, lo no
# cubierto y referencias. Ruteo por índice de cobertura (interno/híbrido/externo).
# ---------------------------------------------------------------------------
_ANALISIS_BUSCADOR_POR_MATERIA = {
    "familia": "familia",
    "laboral": "laborales",
    "penal": "penales",
    "civil": "civiles",
}
_ANALISIS_PATRON_LEY = re.compile(r"ley\s*n?°?\s*(\d[\d.]*)", re.IGNORECASE)
_ANALISIS_PATRON_ART = re.compile(r"art(?:[ií]culo|\.)?\s*n?°?\s*(\d+)", re.IGNORECASE)
_ANALISIS_STOP = {"que", "qué", "una", "unos", "unas", "para", "porque", "como", "cómo",
                   "donde", "cuando", "este", "esta", "estos", "estas", "entre", "sobre",
                   "tiene", "tienen", "puede", "hace", "hacen", "cada", "todo", "toda"}


def _analisis_consulta_corta(consulta: str, top: int = 6) -> str:
    """Palabras significativas para búsquedas FTS estrictas (las preguntas en
    lenguaje natural no calzan con AND literal)."""
    pals = [w.strip("¿?¡!.,;:()\"'") for w in (consulta or "").lower().split()]
    sig = [w for w in pals if len(w) >= 4 and w not in _ANALISIS_STOP]
    return " ".join(sig[:top]) or (consulta or "")[:80]


def _analisis_palabras(q: str | None) -> list[str]:
    return re.findall(r"[a-záéíóúñü]{4,}", (q or "").lower())


def _analisis_coincidencia(query: str, texto: str | None, top: int = 6) -> list[str]:
    inter = set(_analisis_palabras(query)) & set(_analisis_palabras(texto))
    return sorted(inter)[:top]


def _analisis_detectar_ley_art(consulta: str) -> tuple[str | None, str | None]:
    ley = art = None
    m = _ANALISIS_PATRON_LEY.search(consulta or "")
    if m:
        ley = m.group(1)
    m = _ANALISIS_PATRON_ART.search(consulta or "")
    if m:
        art = m.group(1)
    return ley, art


def _analisis_articulo_literal(ley: str, art: str) -> tuple[str, bool]:
    """Texto literal del artículo: corpus JPL local primero, luego LeyChile en vivo."""
    if _JPL_AVAILABLE and _jpl_db is not None:
        try:
            filas = _jpl_db.buscar_articulo(ley, art)
            if filas:
                t = filas[0]
                return (
                    "FUENTE INTERNA — corpus JPL (leyes)\n"
                    f"Ley {t.get('ley', ley)} — Artículo {t.get('articulo', art)}:\n"
                    f"{t.get('texto', '')}",
                    True,
                )
        except Exception:
            pass
    try:
        return obtener_articulo_texto(ley.replace(".", ""), art) + "\n[texto oficial LeyChile]", True
    except Exception as exc:  # noqa: BLE001
        return f"No se pudo recuperar el texto del art. {art} de la ley {ley}: {exc}", False


def _analisis_casos_cgr(consulta: str, limite: int = 5) -> tuple[str, int, str]:
    """Casos Contraloría del corpus local: N°+año, fecha, materia, solicitante,
    sumario completo (qué se pidió y qué resolvió), estado del criterio,
    por-qué-aplica factual y link oficial. Retorna (texto, n, titular)."""
    vistos: set[str] = set()
    pares: list[tuple[float | None, dict]] = []
    try:
        sem = _sem_buscar(_db, consulta, top_k=max(limite, 6), fuente="dictamenes") or []
        for r in sem:
            if isinstance(r, dict) and "error" not in r:
                sc = r.get("score")
                if sc is not None and sc < 0.45:
                    continue  # coincidencia semántica débil: no presentar como caso
                f = _db.consultar_dictamen_cgr(dictamen_id=r.get("fuente_id"))
                if f and str(f["id"]) not in vistos:
                    vistos.add(str(f["id"]))
                    pares.append((r.get("score"), dict(f)))
    except Exception:
        pass
    if len(pares) < limite:
        try:
            fts = _db.search_dictamenes_cgr(consulta, limit=max(limite, 8), offset=len(pares)) or []
            for f in fts:
                f = dict(f)
                if str(f.get("id")) not in vistos:
                    vistos.add(str(f.get("id")))
                    full = _db.consultar_dictamen_cgr(dictamen_id=f.get("id")) or f
                    pares.append((None, dict(full)))
        except Exception:
            pass
    if not pares:
        return f"Sin dictámenes en el corpus local para '{consulta}'.", 0, ""
    out: list[str] = []
    for i, (score, r) in enumerate(pares[:limite], 1):
        try:
            estado = _crit_estado(_db, dictamen_id=r["id"])
        except Exception:
            estado = {"estado": "—", "descripcion": ""}
        try:
            materia = _crit_materia(numero=r.get("numero"), anio=r.get("anio"),
                                    organismo_consultante=r.get("organismo_consultante"),
                                    texto=r.get("sumario", ""))
        except Exception:
            materia = r.get("materia") or "—"
        url = _crit_url_oficial(r)
        overlap = _analisis_coincidencia(consulta, (r.get("sumario") or "") + " " + str(materia))
        head = (f"### Caso {i} — Dictamen N° {r.get('numero')}"
                + (f" de {r.get('anio')}" if r.get("anio") else "") + " (Tipo: Contraloría)")
        out.append(head)
        out.append(f"- Fecha: {r.get('fecha') or '—'}")
        out.append(f"- Materia: {materia}")
        out.append(f"- Solicitante: {r.get('organismo_consultante') or '—'}")
        out.append(f"- Estado del criterio: {estado.get('estado', '—')}"
                   + (f" — {estado.get('descripcion')}" if estado.get("descripcion") else ""))
        out.append(f"- Sumario (extracto del dataset público; texto completo en la fuente oficial):\n{r.get('sumario') or '—'}")
        aplica = f"coincide en materia «{materia}»"
        if overlap:
            aplica += f" y términos: {', '.join(overlap)}"
        if score is not None:
            aplica += f" (similitud {score:.3f})"
        out.append(f"- Por qué aplica a tu consulta: {aplica}.")
        out.append(f"- Fuente oficial: {url}")
        out.append("")
    top = pares[0][1]
    titular = (f"Dictamen N° {top.get('numero')}"
               + (f" de {top.get('anio')}" if top.get("anio") else ""))
    return "\n".join(out), len(pares[:limite]), titular


def _analisis_casos_pjud(consulta: str, materias: list[str], limite: int = 6) -> tuple[str, int, str]:
    """Jurisprudencia judicial en vivo: caratulado completo, rol, fechas, resultado y link."""
    buscador = None
    tipo = "Judicial"
    nombres = {"familia": "Familia", "laboral": "Laboral", "penal": "Penal", "civil": "Civil"}
    for m in materias or []:
        if m in _ANALISIS_BUSCADOR_POR_MATERIA:
            buscador = _ANALISIS_BUSCADOR_POR_MATERIA[m]
            tipo = nombres[m]
            break
    try:
        from .pjud_juris import buscar_sentencias_pjud
        docs, total = buscar_sentencias_pjud(consulta, limite=limite, buscador=buscador)
    except Exception as exc:  # noqa: BLE001
        return f"PJUD no disponible ({type(exc).__name__}: {exc}).", 0, ""
    if not docs:
        return "Sin sentencias PJUD para esta consulta.", 0, ""
    out = [f"Sentencias PJUD ({total} encontradas, se muestran {len(docs)}):", ""]
    for i, d in enumerate(docs, 1):
        out.append(f"### Caso {i} — Rol {d.get('rol', 's/r')} ({d.get('fecha', 's/f')}) (Tipo: {tipo})")
        out.append(f"- Tribunal: {d.get('tribunal', '—')} {d.get('sala', '')}".rstrip())
        out.append(f"- Caratulado: {d.get('caratulado', '—')}")
        out.append(f"- Recurso: {d.get('tipo_recurso', '—')} — Resultado: {d.get('resultado', '—')}")
        texto = (d.get("texto") or "").replace("<br/>", " ")
        out.append(f"- Texto del fallo:\n{texto}")
        overlap = _analisis_coincidencia(consulta, texto + " " + str(d.get("caratulado", "")))
        aplica = (f"coincide en términos: {', '.join(overlap)}" if overlap
                  else "seleccionada por el buscador PJUD para esta consulta")
        out.append(f"- Por qué aplica a tu consulta: {aplica}.")
        out.append(f"- Fuente oficial: {d.get('url', '—')}")
        out.append("")
    top = docs[0]
    titular = f"Rol {top.get('rol', 's/r')} ({top.get('fecha', 's/f')}) — {top.get('resultado', '')}".strip()
    return "\n".join(out), len(docs), titular


def _analisis_vacio(v) -> bool:
    if v is None:
        return True
    if isinstance(v, tuple):
        return v[1] == 0 or not v[0]
    s = str(v)
    sl = s.lower()
    return (not s.strip() or sl.startswith("[no disponible") or sl.startswith("[tiempo agotado")
            or "sin resultados" in sl or "sin dictámenes" in sl or "sin dictamenes" in sl
            or "sin sentencias" in sl or "sin casos" in sl or "sin resultados indexados" in sl
            or "no disponible" in sl[:80])


@mcp.tool()
def analizar_consulta(consulta: str) -> str:
    """Análisis jurídico con formato de respuesta K-LegalChile.

    Rutea por el índice de cobertura (corpus local / híbrido / externo directo) y
    devuelve: respuesta directa primero, fundamento normativo con texto literal de
    artículos, casos por tipo (carátula, rol/dictamen, fechas, qué resolvió, por qué
    aplica, link oficial), criterios, lo no cubierto y referencias. Sin recortes ni
    plantillas con espacios en blanco.
    """
    consulta = (consulta or "").strip()
    if not consulta:
        return "Error: consulta vacía."
    clas = _clasificar(consulta)
    estrategia = clas.get("estrategia", "hibrido")
    materias = clas.get("materias", ["leyes_normas"])
    ley, art = _analisis_detectar_ley_art(consulta)

    def _safe(fn, *a):
        try:
            return fn(*a)
        except Exception as exc:  # noqa: BLE001
            return f"[No disponible: {type(exc).__name__}: {exc}]"

    usar_interno = estrategia in ("interno", "hibrido")
    usar_externo = estrategia in ("externo", "hibrido")
    fut: dict = {}
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=8)
    try:
        if usar_interno:
            fut["normas"] = ex.submit(_safe, buscar_normas, _analisis_consulta_corta(consulta), 6)
            fut["cgr"] = ex.submit(_safe, _analisis_casos_cgr, consulta, 5)
            if "policia_local" in materias:
                fut["jpl"] = ex.submit(_safe, jpl_buscar_texto, consulta, 8)
                fut["kb"] = ex.submit(_safe, kb_search, consulta, 5)
            if "sii" in materias:
                fut["sii"] = ex.submit(_safe, buscar_sii, consulta, 5)
            if "tdlc" in materias:
                fut["tdlc"] = ex.submit(_safe, buscar_tdlc, consulta, 5)
            if ley and art:
                fut["articulo"] = ex.submit(_safe, _analisis_articulo_literal, ley, art)
            if ley:
                fut["vigencia"] = ex.submit(_safe, estado_vigencia, ley)
        if usar_externo:
            fut["pjud"] = ex.submit(_safe, _analisis_casos_pjud, consulta, materias, 6)
            fut["todo"] = ex.submit(_safe, buscar_todo, consulta, 6)
            fut["scielo"] = ex.submit(_safe, buscar_scielo, consulta, 3)
        _timeouts = {"pjud": 60, "todo": 75, "scielo": 45}
        res: dict = {}
        for k, f in fut.items():
            try:
                res[k] = f.result(timeout=_timeouts.get(k, 60))
            except Exception as exc:  # noqa: BLE001
                res[k] = f"[Tiempo agotado o error: {exc}]"
    finally:
        # No esperar hilos bloqueados (navegador PJUD/Playwright): responder igual.
        ex.shutdown(wait=False, cancel_futures=True)

    fecha_hoy = datetime.now().strftime("%d-%m-%Y")
    cgr = res.get("cgr") if isinstance(res.get("cgr"), tuple) else ("", 0, "")
    pjud = res.get("pjud") if isinstance(res.get("pjud"), tuple) else ("", 0, "")
    artv = res.get("articulo") if isinstance(res.get("articulo"), tuple) else ("", False)
    cgr_txt, cgr_n, cgr_top = cgr
    pjud_txt, pjud_n, pjud_top = pjud
    art_txt, art_ok = artv

    directa: list[str] = []
    vig_txt = res.get("vigencia", "")
    if isinstance(vig_txt, str) and vig_txt and not _analisis_vacio(vig_txt):
        directa.append(vig_txt.splitlines()[0])
    if art_ok and art_txt and not art_txt.startswith("No se pudo"):
        directa.append(f"Norma aplicable: Ley N° {ley}, art. {art} — texto literal en §1.")
    if cgr_top and cgr_n:
        directa.append(f"Caso Contraloría más cercano: {cgr_top} — detalle en §2.")
    jpl_d = res.get("jpl", "")
    if "policia_local" in materias and isinstance(jpl_d, str) and jpl_d and not _analisis_vacio(jpl_d):
        for ln in jpl_d.splitlines():
            if ln.strip().startswith("• ["):
                directa.append(f"Corpus JPL: {ln.strip()[2:].strip()[:220]} — detalle en §2.")
                break
    if pjud_top and pjud_n:
        directa.append(f"Jurisprudencia más cercana: {pjud_top} — detalle en §2.")
    todo_d = res.get("todo", "")
    if isinstance(todo_d, str) and todo_d and not _analisis_vacio(todo_d):
        for ln in todo_d.splitlines():
            if ln.strip().startswith("CONCLUSIÓN:"):
                directa.append(f"Fuentes externas: {ln.strip()[:250]} — detalle en §2.")
                break

    s: list[str] = []
    s.append("# RESPUESTA DIRECTA\n")
    s.append(f"Consulta: \"{consulta}\" — {fecha_hoy} — Estrategia: {estrategia} "
             f"(materias: {', '.join(materias)}).")
    if directa:
        s.extend(f"- {d}" for d in directa)
    else:
        s.append("- No se encontró material suficiente en las fuentes consultadas. Ver §4 (lo no cubierto).")
    s.append("\n# 1. FUNDAMENTO NORMATIVO (texto literal)\n")
    if art_ok and art_txt:
        s.append(art_txt)
        s.append("")
    normas_txt = res.get("normas", "")
    if isinstance(normas_txt, str) and normas_txt and not _analisis_vacio(normas_txt):
        s.append("## Normas relacionadas\n")
        s.append(normas_txt)
    if isinstance(vig_txt, str) and vig_txt and not _analisis_vacio(vig_txt):
        s.append("\n## Vigencia\n")
        s.append(vig_txt)
    s.append("\n# 2. CASOS\n")
    if cgr_n:
        s.append("## 2.1 Contraloría — dictámenes del corpus local\n")
        s.append(cgr_txt)
    jpl_txt = res.get("jpl", "")
    kb_txt = res.get("kb", "")
    if isinstance(jpl_txt, str) and jpl_txt and not _analisis_vacio(jpl_txt):
        s.append("## 2.2 Policía Local — leyes, ordenanzas y formatos\n")
        s.append(jpl_txt)
    if isinstance(kb_txt, str) and kb_txt and not _analisis_vacio(kb_txt):
        s.append("## Base de conocimiento (formatos y doctrina JPL)\n")
        s.append(kb_txt)
    if pjud_n:
        s.append("## 2.3 Jurisprudencia judicial\n")
        s.append(pjud_txt)
    n_ext = 4
    for clave, titulo in (("sii", "SII — jurisprudencia administrativa tributaria"),
                          ("tdlc", "Libre competencia"),
                          ("todo", "Otras fuentes oficiales"),
                          ("scielo", "Doctrina")):
        v = res.get(clave, "")
        if isinstance(v, str) and v and not _analisis_vacio(v):
            s.append(f"## 2.{n_ext} {titulo}\n")
            n_ext += 1
            s.append(v)
    s.append("\n# 3. CRITERIOS\n")
    if cgr_n:
        s.append("Los estados del criterio de cada dictamen van en su ficha (§2.1). "
                 "Para recalcular todo el corpus: estado_criterio(actualizar=True).")
    else:
        s.append("Sin criterios del corpus local para esta consulta.")
    s.append("\n# 4. LO NO CUBIERTO POR LAS FUENTES\n")
    faltantes = [k for k, v in res.items() if _analisis_vacio(v)]
    if faltantes:
        s.append("Sin material en: " + ", ".join(faltantes) + ".")
        s.append("Esto no significa que el asunto no exista: amplía términos o revisa las referencias.")
    else:
        s.append("Todas las fuentes consultadas aportaron material.")
    s.append("\n## Referencias y links oficiales\n")
    s.append("- LeyChile: https://www.bcn.cl/leychile/")
    s.append("- CGR dictámenes: https://www.contraloria.cl/web/cgr/dictamenes-y-pronunciamientos")
    s.append("- PJUD: https://juris.pjud.cl/busqueda/lista_buscadores")
    s.append("- (Los links específicos de cada caso van en su ficha.)")
    s.append("\n---\nDescargo: información trazable de fuentes oficiales chilenas; no constituye asesoría legal.")
    try:  # auto-registro en memoria (nunca rompe el análisis)
        _registrar_mensaje("usuario", f"Análisis de consulta: {consulta}", herramientas="analizar_consulta")
        _registrar_mensaje("asistente", f"Informe generado: estrategia {estrategia}, materias {','.join(materias)}",
                           herramientas="analizar_consulta")
    except Exception:
        pass
    return "\n".join(s)




# ---------------------------------------------------------------------------
# Corpus CGR local K-LegalChile (dictámenes, criterios, cadena judicial)
# ---------------------------------------------------------------------------
@mcp.tool()
def estado_corpus_lex() -> str:
    """Estado del corpus jurídico local K-LegalChile (dictámenes CGR, sentencias TC, normas, citaciones, criterios)."""
    n_dict = _db.count_dictamenes_cgr()
    n_tc = _db.count_sentencias_tc()
    n_normas = _db.count()
    n_citas = _db.count_citas_legales()
    n_crit = _db.count_criterios()
    n_emb = _db.count_embeddings()
    out = [
        "ESTADO DEL CORPUS JURÍDICO LOCAL K-LegalChile",
        "──────────────────────────────────────────────",
        f"• Dictámenes CGR con texto completo: {n_dict:,}",
        f"• Sentencias del Tribunal Constitucional: {n_tc:,}",
        f"• Normas del catálogo (BCN/LeyChile): {n_normas:,}",
        f"• Aristas de citación (aplica/funda/cita): {n_citas:,}",
        f"• Criterios con estado (vigencia/superación): {n_crit:,}",
        f"• Chunks indexados en embeddings semánticos: {n_emb:,}",
        "",
        "Fuente: datasets públicos (CGR, Tribunal Constitucional, biblioteca del Congreso) + fuentes oficiales en vivo.",
        "Para ampliar el corpus ejecutar: python scripts/ingest_dictamenes.py --index-semantico",
    ]
    return "\n".join(out)


@mcp.tool()
def _buscar_dictamenes_corpus_tc(query: str, limite: int = 5) -> str:
    """Helper: busca sentencias TC en el corpus local (FTS) y las formatea breve."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    rows = _db.search_sentencias_tc(query, limit=max(limite, 5))
    if not rows:
        return f"Sin sentencias TC en el corpus local para '{query}'. Usa buscar_tc (buscador oficial en vivo)."
    out = []
    for r in rows[:limite]:
        head = f"• Rol {r.get('rol') or '?'}"
        if r.get("fecha"):
            head += f" | {str(r['fecha'])[:10]}"
        out.append(head)
        out.append(f"  Materia/tipo: {r.get('materia') or r.get('tipo_proceso') or r.get('resultado') or '—'}")
        if r.get("considerandos_preview"):
            out.append(f"  Fragmento: {r['considerandos_preview'].replace(chr(10), ' ')[:180]}")
        out.append("")
    out.append("🔗 Ficha oficial: https://buscador.tcchile.cl/ (buscador del Tribunal Constitucional).")
    return "\n".join(out)


def buscar_dictamenes_corpus(query: str, limite: int = 8, anio: int | None = None,
                             semantico: bool = True) -> str:
    """Búsqueda semántica (por significado jurídico) y textual en el corpus local de dictámenes CGR.

    Retorna los más similares con sus metadatos
    (numero, fecha, organismo consultante) y su estado del criterio.
    """
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    hallados: list[tuple[float | None, dict]] = []

    if semantico:
        try:
            res = _sem_buscar(_db, query, top_k=max(limite, 6), fuente="dictamenes")
            for r in res:
                if "error" in r:
                    break
                fila = _db.consultar_dictamen_cgr(dictamen_id=r["fuente_id"])
                if fila:
                    hallados.append((r["score"], fila))
        except Exception:
            pass
    if len(hallados) < limite:
        for r in _db.search_dictamenes_cgr(query, limit=max(limite, 8), anio=anio,
                                           offset=len(hallados)):
            if all(str(h[1]["id"]) != str(r["id"]) for h in hallados):
                hallados.append((None, dict(r)))

    if not hallados:
        return f"Sin dictámenes en el corpus local para '{query}'. Ejecuta la ingesta (scripts/ingest_dictamenes.py) o usa buscar_dictamenes (CGR en vivo)."

    out = [f"BÚSQUEDA DE DICTÁMENES EN CORPUS LOCAL para '{query}' ({len(hallados)} resultados):", ""]
    for score, r in hallados[:limite]:
        estado = _crit_estado(_db, dictamen_id=r["id"])
        materia = _crit_materia(numero=r["numero"], anio=r["anio"],
                                organismo_consultante=r["organismo_consultante"], texto=r.get("sumario", ""))
        head = f"• Dictamen N° {r['numero']}" + (f" de {r['anio']}" if r['anio'] else "")
        if score is not None:
            head += f" — similitud {score:.3f}"
        out.append(head)
        out.append(f"  Materia: {materia}")
        out.append(f"  Estado del criterio: {estado['estado']}")
        out.append(f"  Solicitante: {r['organismo_consultante'] or '—'} | Fecha: {r['fecha'] or '—'}")
        out.append(f"  Fuente: {_crit_url_oficial(r)}")
        out.append("")
    out.append("🔗 Texto completo y análisis: ficha_dictamen_doctrinal(numero, anio).")
    return "\n".join(out)


@mcp.tool()
def estado_criterio(numero: str | None = None, anio: int | None = None,
                    dictamen_id: str | None = None, actualizar: bool = False) -> str:
    """Estado del criterio de un dictamen CGR: VIGENTE/RECONSIDERADO/MODIFICADO/DEROGADO/COMPLEMENTADO/REAFIRMADO.

    Detecta jurisprudencia vigente o superada y el "estado del criterio".
    Si actualizar=True, recalcula el estado de todo el corpus.
    """
    if actualizar:
        resultado = _crit_marcar(_db)
    estado = _crit_estado(_db, dictamen_id=dictamen_id, numero=numero, anio=anio)
    if "error" in estado:
        return estado["error"]
    r = estado.pop("dictamen")
    detalle = estado.pop("detalle", [])
    out = [
        "ESTADO DEL CRITERIO — DICTAMEN CGR",
        "───────────────────────────────────",
        f"Dictamen N° {r['numero']}" + (f" de {r['anio']}" if r['anio'] else ""),
        f"ESTADO: {estado['estado']}",
        f"Fundamento: {estado['descripcion']}",
    ]
    if detalle:
        out.append("Línea de evolución:")
        for e in detalle:
            out.append(f"  • {e['estado']} — {e['descripcion']} ({e['fuente']})")
    out.append(f"Fuente oficial: {_crit_url_oficial(r)}")
    if actualizar:
        out.append("")
        out.append(f"Recálculo: {resultado['dictamenes_evaluados']} evaluados, {resultado['marcados']} marcados.")
    return "\n".join(out)


@mcp.tool()
def ficha_dictamen_doctrinal(numero: str | None = None, anio: int | None = None,
                             dictamen_id: str | None = None, breve: bool = False) -> str:
    """Ficha doctrinal de un dictamen CGR del corpus K-LegalChile.
    Campos: identificación, materia (taxonomía cerrada), normas aplicadas, quién lo requirió,
    estado del criterio, antecedentes, criterio, por qué importa, antecedentes jurisprudenciales y fuente oficial.
    """
    return _crit_ficha(_db, dictamen_id=dictamen_id, numero=numero, anio=anio, breve=breve)


@mcp.tool()
def obtener_sentencia_cadena(sentencia_id: str | None = None, rol: str | None = None) -> str:
    """Cadena judicial de una sentencia a partir del grafo de citaciones del corpus.

    El texto completo de la
    sentencia se recupera en vivo con buscar_jurisprudencia (PJUD); aquí se entrega su cadena:
    sentencias citadas y normas aplicadas que la sustentan.
    """
    if not sentencia_id and not rol:
        return "Indica sentencia_id (id numérico del grafo) o rol (para el texto via PJUD)."
    if rol:
        return ("Texto completo de sentencia: usa buscar_jurisprudencia con el rol (PJUD en vivo, publicada). "
                "Para su cadena judicial indique sentencia_id numérico del corpus de citaciones.")
    sid = str(sentencia_id)
    salientes = _db.get_citas(source_kind="sentencia", source_id=sid, limit=40)
    entrantes = _db.get_citas(target_kind="sentencia", target_id=sid, limit=40)
    if not salientes and not entrantes:
        return f"Sin aristas para la sentencia {sid} en el grafo local de citaciones."
    out = [
        f"CADENA JUDICIAL — SENTENCIA {sid}",
        "─────────────────────────────────",
        "Aristas hacia otras sentencias y normas (salientes):",
    ]
    for c in salientes[:25]:
        tgt = c["target_external_ref"] or f"{c['target_kind'] or 'external'} {c['target_id'] or '—'}".strip()
        out.append(f"  • [{c['tipo']}] → {tgt} (conf. {c['confidence'] or '—'})")
    out.append("")
    out.append("Citas que recibe de otras sentencias (entrantes — cadena inversa):")
    for c in entrantes[:25]:
        out.append(f"  • [{c['tipo']}] desde {c['source_id']} → {c['target_external_ref'] or '—'} (conf. {c['confidence'] or '—'})")
    out.append("")
    out.append("Nota: el grafo local cubre hasta 10.000 aristas del dataset público.")
    return "\n".join(out)


@mcp.tool()
def boletin_criterios_nuevos(dias: int = 7, limite: int = 10) -> str:
    """Boletín de criterios nuevos en la CGR desde el corpus local K-LegalChile."""
    if dias < 1:
        dias = 7
    return _crit_boletin(_db, dias=dias, limite=max(1, limite))


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
def sma_buscar_procedimiento(query: str, limite: int = 5, offset: int = 0) -> str:
    """SMA — expedientes de fiscalización ambiental y procedimientos (SNIFA)."""
    query = query.strip()
    if not query:
        return "Error: consulta vacía."
    cached = _db._search_generic("sma_procedimientos", "sma_procedimientos_fts", query, limite, offset)
    if cached:
        out = [f"SMA Procedimientos para '{query}' ({len(cached)} cache):", ""]
        for r in cached:
            out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
        return "\n".join(out)
    rows = _sma_mod.buscar_procedimiento_fiscalizacion(query, limite + offset)[offset: offset + limite]
    for r in rows:
        _db._upsert_generic("sma_procedimientos", "sma_procedimientos_fts", f"sma:{r['numero']}", r["numero"], r["titulo"], r["url"])
    out = [f"SMA Procedimientos para '{query}' ({len(rows)}):", ""]
    for r in rows:
        out.append(f"• {r['titulo']}\n  URL: {r['url']}\n")
    out.append("🔗 https://snifa.sma.gob.cl/ExpedienteAmbiental")
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
        "   https://juris.pjud.cl/busqueda/lista_buscadores\n\n"
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


@mcp.tool()
def expediente_citas_legales(nombre: str, limite: int = 50) -> str:
    """Extrae de los documentos del expediente todo el DERECHO INVOCADO: citas a cuerpos legales con precisión de artículo e inciso ('artículo 148, inciso primero, del Código Civil', 'art. 64 CPC', 'Ley N° 19.966'), indicando el documento y el contexto donde cada una aparece. Verifica cada norma contra la base nacional local: [VERIFICADA EN BASE LOCAL] o [POR VERIFICAR]."""
    if limite < 1 or limite > 200:
        limite = 50
    return _exp_fmt_citas(_exp_citas(nombre, limite))


@mcp.tool()
def obtener_articulo_texto(identificador: str, articulo: str, inciso: str | None = None) -> str:
    """Devuelve el texto literal de un artículo —y opcionalmente de un inciso— de una norma chilena, cortado con precisión forense del texto oficial (LeyChile). Distingue el ordinal 'º/°': pedir el artículo 2 no trae el 20 ni el 21. Usa la caché local; si la norma no está descargada, intenta bajarla de LeyChile. Ejemplo: obtener_articulo_texto(identificador='21643', articulo='2', inciso='1')"""
    texto = obtener_texto_norma(identificador)
    encabezado = f"Norma consultada: {identificador} — Artículo {articulo}"
    if inciso:
        encabezado += f", inciso {inciso}"
    res = _extraer_articulo(texto, articulo, inciso)
    if not res.get("ok"):
        return (f"{encabezado}\n\nERROR: {res.get('error', 'artículo no encontrado')}\n"
                "Compruebe que la norma se descargó íntegramente y cite de la fuente oficial: "
                "https://www.bcn.cl/leychile/")
    salida = [encabezado, ""]
    if res.get("advertencia"):
        salida.append(f"ADVERTENCIA: {res['advertencia']}")
        salida.append("")
    if inciso and res.get("texto_inciso"):
        salida.append(f"Inciso {res.get('inciso', inciso)}:")
        salida.append(res["texto_inciso"])
    else:
        salida.append(res["texto_articulo"])
    if res.get("incisos") and not inciso:
        salida.append("")
        salida.append("Párrafos del artículo detectados:")
        salida.extend(f"• inciso {i['inciso']}" for i in res["incisos"] if i.get("inciso"))
    salida.append("")
    salida.append("NOTA: extracto literal del texto oficial en caché/descargado; contraste con "
                  "https://www.bcn.cl/leychile/ antes de citarlo en escrito al tribunal.")
    return "\n".join(salida)


@mcp.tool()
def expediente_vigencia_citas(nombre: str) -> str:
    """Verifica el estado de vigencia (VIGENTE / DEROGADA / REFUNDIDA) de cada norma citada en el expediente, con fecha de última modificación y advertencia intertemporal. Base: expediente_citas_legales + estado_vigencia (caché 7 días)."""
    return _exp_fmt_vigencias(_exp_vigencia_citas(nombre))


@mcp.tool()
def expediente_plazos(nombre: str) -> str:
    """Detecta plazos procesales en los documentos del expediente ('plazo de 15 días', 'dentro del sexto día'), los computa con arts. 38/40 CPC + feriado judicial, y reporta su estado contra hoy (vencido / vence en N días / sin fecha de referencia)."""
    return _exp_fmt_plazos(_exp_plazos(nombre))


@mcp.tool()
def computar_plazo_procesal(fecha_notificacion: str, dias: int, tipo: str = "habiles") -> str:
    """Computa un plazo procesal chileno desde la notificación: arts. 38/40 CPC, sábado inhábil (Ley 2.977) y feriado judicial 1-feb → primer hábil de marzo (art. 66 COT). Recibe la fecha DD-MM-AAAA (o "15 de enero de 2026"), N días y tipo 'habiles' o 'corridos'. Devuelve el vencimiento con la cadena de razonamiento y los fundamentos legales. Ejemplo: computar_plazo_procesal('15-01-2026', 10, 'habiles')"""
    fecha = _parsear_fecha_cl(fecha_notificacion)
    if fecha is None:
        return (f"ERROR: no entendí la fecha '{fecha_notificacion}'. "
                "Use DD-MM-AAAA, DD/MM/AAAA o '15 de enero de 2026'.")
    if tipo not in ("habiles", "corridos"):
        return "ERROR: tipo debe ser 'habiles' o 'corridos'."
    try:
        res = _computar_plazo(fecha, dias, tipo)
    except ValueError as exc:
        return f"ERROR: {exc}"
    return _fmt_plazo(res)


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
