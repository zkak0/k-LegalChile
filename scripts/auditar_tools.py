#!/usr/bin/env python3
"""Auditoría real: prueba cada tool con parámetros realistas y clasifica resultado.

Clasificación:
  OK      — retorna datos sustantivos reales de la fuente
  EMPTY   — funciona pero no retorna nada útil para la consulta
  BROKEN  — error, excepción, o mensaje de bloqueo/falla
  LOCAL   — herramienta local (sin red); se verifica que no lance excepción
"""
import sys, time, traceback, json
sys.path.insert(0, "src")
from chilean_legal_mcp import server

RESULTS = []

def run(name, fn, *args, **kwargs):
    t0 = time.time()
    try:
        out = fn(*args, **kwargs)
        dt = time.time() - t0
        text = str(out)
        low = text.lower()
        broken_markers = ["error", "traceback", "excepción", "no disponible", "bloque", "fall", "403", "404", "500",
                          "sin acceso", "no se pudo", "imposible"]
        empty_markers = ["sin resultados", "0 resultado", "no se encontr", "vacío", "sin coincidencias"]
        status = "OK"
        if any(m in low for m in broken_markers) and len(text) < 400:
            status = "BROKEN"
        elif any(m in low for m in broken_markers) and ("error" in low or "no disponible" in low or "bloque" in low):
            # si tiene marcador de error dominante
            if text.count("http") == 0 and len(text) < 600:
                status = "BROKEN"
        if status == "OK" and any(m in low for m in empty_markers):
            status = "EMPTY"
        RESULTS.append({
            "tool": name, "status": status, "secs": round(dt, 1),
            "chars": len(text), "sample": text[:500]
        })
    except Exception as e:
        dt = time.time() - t0
        RESULTS.append({
            "tool": name, "status": "BROKEN", "secs": round(dt, 1),
            "chars": 0, "sample": f"EXCEPCIÓN: {type(e).__name__}: {e}"[:500]
        })

# ─── LOCALES: JPL ───
run("jpl_listar_leyes", server.jpl_listar_leyes)
run("jpl_buscar_ley", server.jpl_buscar_ley, "bebidas alcohólicas")
run("jpl_buscar_articulo", server.jpl_buscar_articulo, "18.287", 14)
run("jpl_verificar_vigencia", server.jpl_verificar_vigencia, "18.287")
run("jpl_listar_ordenanzas", server.jpl_listar_ordenanzas, "providencia")
run("jpl_buscar_ordenanza", server.jpl_buscar_ordenanza, "providencia", "ruidos")
run("jpl_buscar_texto", server.jpl_buscar_texto, "tenencia responsable")
run("jpl_generar_documento", server.jpl_generar_documento, "sentencia",
    '{"comuna":"Santiago","denunciado":"Juan Pérez","rut":"12.345.678-9","hecho":"ruidos","ley":"18.287","articulo":24,"dia":15,"mes":9,"ano":2026}')
run("jpl_estado", server.jpl_estado)

# ─── LOCALES: KB ───
run("kb_status", server.kb_status)
run("kb_search", server.kb_search, "comercio ambulante")
run("kb_get", server.kb_get, "leyes/Ley_19925_Analcoholes.md" if False else "manuales/formatos_sentencias.md")

# ─── BCN / LeyChile ───
run("buscar_normas", server.buscar_normas, "ley sobre alcoholes")
run("obtener_texto_norma", server.obtener_texto_norma, "29705")
run("obtener_texto_norma_pag2", server.obtener_texto_norma, "29705", 8000)
run("citar_norma", server.citar_norma, "29705")
run("citar_json", server.citar_json, "29705")
run("exportar_norma", server.exportar_norma, "29705", "docx")
run("historial_norma", server.historial_norma, "29705")
run("estado_vigencia", server.estado_vigencia, "18287")
run("obtener_articulo_texto", server.obtener_articulo_texto, "29705", "14")

# ─── Semántico ───
run("estado_indexacion", server.estado_indexacion)
run("buscar_semantico", server.buscar_semantico, "multas por ruidos molestos")

# ─── CGR ───
run("buscar_dictamenes", server.buscar_dictamenes, "municipalidades personal a contrata")

# ─── PJUD ───
run("buscar_jurisprudencia", server.buscar_jurisprudencia, "responsabilidad civil")

# ─── TC ───
run("buscar_tc", server.buscar_tc, "debido proceso")

# ─── Doctrina / SciELO / Historia de la Ley ───
run("buscar_doctrina", server.buscar_doctrina, "debido proceso")
run("buscar_scielo", server.buscar_scielo, "derecho ambiental chile")
run("buscar_historia_ley", server.buscar_historia_ley, "responsabilidad penal adolescente")

# ─── Fuentes externas: entidades ───
run("buscar_dt", server.buscar_dt, "despido injustificado")
run("buscar_diario_oficial", server.buscar_diario_oficial, "ley")
run("buscar_suseso", server.buscar_suseso, "accidente trabajo")
run("buscar_sii", server.buscar_sii, "IVA")
run("buscar_cmf", server.buscar_cmf, "bancos")
run("buscar_tdlc", server.buscar_tdlc, "colusión")
run("buscar_cplt", server.buscar_cplt, "transparencia")
run("buscar_datos_gob", server.buscar_datos_gob, "educación")

# ─── SII específicos ───
run("sii_buscar_oficio", server.sii_buscar_oficio, "IVA servicios")
run("sii_buscar_circular", server.sii_buscar_circular, "factura electrónica")
run("sii_buscar_resolucion", server.sii_buscar_resolucion, "timbraje")
run("sii_buscar_fallo", server.sii_buscar_fallo, "reclamo")

# ─── TGR específicos ───
run("tgr_buscar_dictamen", server.tgr_buscar_dictamen, "contribuciones")
run("tgr_buscar_resolucion", server.tgr_buscar_resolucion, "multa")
run("tgr_buscar_circular", server.tgr_buscar_circular, "pago")
run("tgr_buscar_fallo", server.tgr_buscar_fallo, "apelación")

# ─── INAPI / TDPI / SUPERIR / SMA ───
run("inapi_buscar_marca", server.inapi_buscar_marca, "colun")
run("inapi_estados_diarios", server.inapi_estados_diarios)
run("tdpi_jurisprudencia", server.tdpi_jurisprudencia, "marca notoria")
run("superir_buscar_boletin", server.superir_buscar_boletin, "quiebra")
run("sma_buscar_sancionatorio", server.sma_buscar_sancionatorio, "minera")

# ─── Salud de fuentes ───
run("salud_fuentes", server.salud_fuentes)

# ─── Agregadores ───
run("buscar_todo", server.buscar_todo, "responsabilidad civil")
run("buscar_todo_fuentes_externas", server.buscar_todo_fuentes_externas, "amparo")
run("buscar_casos", server.buscar_casos, "despido")

# ─── Escritos / workflows / analizar ───
run("tipos_escrito_disponibles", server.tipos_escrito_disponibles)
run("generar_escrito", server.generar_escrito, "demanda",
    '{"tribunal":"1° Juzgado Civil de Santiago","caratula":"Pérez con González","materia":"cobro de pesos"}' if False else "cobro de pesos por $1.000.000 contra Juan Pérez")
run("analizar_consulta", server.analizar_consulta, "me multaron por vender alcohol después de hora, ¿qué hago?")

# ─── Memoria ───
run("guardar_memoria", server.guardar_memoria, "test_auditoria", "contenido de prueba", "nota")
run("consultar_memoria", server.consultar_memoria, "auditoria")
run("historial_conversacion", server.historial_conversacion)
run("registrar_interaccion", server.registrar_interaccion, "pregunta test", "respuesta test")
run("resumen_trabajo", server.resumen_trabajo, 7)

# ─── Vigilancia ───
run("vigilancia_listar", server.vigilancia_listar)
run("vigilancia_pausar", server.vigilancia_pausar, "inexistente")

# ─── Acceso abogado ───
run("ayuda_acceso_abogado", server.ayuda_acceso_abogado)

# ─── Expedientes ───
run("expediente_listar", server.expediente_listar)

# ─── Cómputo ───
run("computar_plazo_procesal", server.computar_plazo_procesal, "2026-09-01", 10, "habiles")
run("computar_plazo_procesal_civil", server.computar_plazo_procesal, "2026-09-01", 10, "corridos")

# ─── Workflows ───
run("listar_workflows", server.listar_workflows)

# ─── Salida ───
with open("data/auditoria_tools.json", "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, ensure_ascii=False, indent=2)

ok = [r for r in RESULTS if r["status"] == "OK"]
empty = [r for r in RESULTS if r["status"] == "EMPTY"]
broken = [r for r in RESULTS if r["status"] == "BROKEN"]
print(f"\n{'='*60}")
print(f"AUDITORÍA: {len(RESULTS)} tools probadas")
print(f"  OK:     {len(ok)}")
print(f"  EMPTY:  {len(empty)}")
print(f"  BROKEN: {len(broken)}")
print(f"\n--- BROKEN ---")
for r in broken:
    print(f"  {r['tool']}: {r['sample'][:150]}")
print(f"\n--- EMPTY ---")
for r in empty:
    print(f"  {r['tool']}: {r['sample'][:120]}")
