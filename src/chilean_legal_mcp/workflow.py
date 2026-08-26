"""Prompt multi-etapa para investigación y redacción jurídica (Fase 5 Magnar libre).

Flujo: planificar → investigar → redactar → autoverificar
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PasoWorkflow:
    """Un paso del workflow multi-etapa."""
    nombre: str
    descripcion: str
    herramienta: str | None = None
    parametros: dict[str, Any] = field(default_factory=dict)
    salida_esperada: str = ""
    completado: bool = False
    resultado: str = ""


# Workflows predefinidos
WORKFLOWS = {
    "escrito_completo": [
        PasoWorkflow(
            nombre="planificar",
            descripcion=(
                "Analiza la consulta del usuario y define: (1) tipo de escrito necesario, "
                "(2) tribunal competente, (3) hechos clave a probar, (4) fuentes a consultar, "
                "(5) estrategia de argumentación. NO ejecutes búsquedas aún."
            ),
            herramienta=None,
            salida_esperada="Plan escrito con tipo, tribunal, hechos, fuentes y estrategia.",
        ),
        PasoWorkflow(
            nombre="investigar",
            descripcion=(
                "Ejecuta investigación multi-fuente según el plan: "
                "analizar_consulta (informe I-V), buscar_normas (legislación), "
                "buscar_jurisprudencia (fallos), buscar_dictamenes (CGR), "
                "buscar_semantico (embeddings si indexado). Acumula citas verificables."
            ),
            herramienta="analizar_consulta",
            parametros={"consulta": "{consulta_usuario}"},
            salida_esperada="Conjunto de fuentes oficiales con citas (Ley N°, fecha, URL).",
        ),
        PasoWorkflow(
            nombre="redactar",
            descripcion=(
                "Genera borrador del escrito usando generar_escrito_desde_investigacion "
                "o generar_escrito con los fundamentos recolectados. Completa todos los campos."
            ),
            herramienta="generar_escrito_desde_investigacion",
            parametros={
                "consulta": "{consulta_usuario}",
                "tipo": "{tipo_escrito}",
                "tribunal": "{tribunal}",
                "causa_rol": "{causa_rol}",
                "caratulado": "{caratulado}",
            },
            salida_esperada="Archivo .docx/.pdf con escrito completo y citas oficiales.",
        ),
        PasoWorkflow(
            nombre="autoverificar",
            descripcion=(
                "Verifica el borrador generado: (1) cada cita tiene URL oficial verificable, "
                "(2) fechas en formato DD-MM-AAAA, (3) vigencia de normas con estado_vigencia, "
                "(4) jurisprudencia tiene rol/fecha/tribunal y resolución en fondo, "
                "(5) no hay invención de doctrina ni jurisprudencia inexistente, "
                "(6) petitorio coherente con fundamentos, (7) formato narrativo jurídico completo. "
                "Reporta hallazgos y qué falta corregir."
            ),
            herramienta="estado_vigencia",
            parametros={"identificador": "{leychile_id}"},
            salida_esperada="Informe de verificación con checklist y correcciones necesarias.",
        ),
    ],
    "investigacion_profunda": [
        PasoWorkflow(
            nombre="planificar",
            descripcion=(
                "Define pregunta jurídica, descompón en sub-preguntas, identifica fuentes "
                "relevantes por materia (laboral, tributario, constitucional, etc.), "
                "define criterios de relevancia y exclusión."
            ),
            herramienta=None,
            salida_esperada="Plan de investigación con sub-preguntas y fuentes por materia.",
        ),
        PasoWorkflow(
            nombre="investigar",
            descripcion=(
                "Ejecuta búsquedas paralelas: buscar_todo (multi-fuente), buscar_semantico "
                "(si indexado), vigilancia_crear (para seguimiento), expediente_indexar "
                "(si hay documentos propios). Itera refinando queries."
            ),
            herramienta="buscar_todo",
            parametros={"consulta": "{consulta_usuario}", "limite": 10},
            salida_esperada="Corpus de fuentes oficiales organizado por materia y relevancia.",
        ),
        PasoWorkflow(
            nombre="sintetizar",
            descripcion=(
                "Sintetiza hallazgos en informe estructurado: (1) norma aplicable con artículos, "
                "(2) jurisprudencia favorable/desfavorable con distinción, "
                "(3) doctrina académica, (4) dictámenes CGR, (5) criterios de tribunales superiores, "
                "(6) vacíos informativos explícitos."
            ),
            herramienta="analizar_consulta",
            parametros={"consulta": "{consulta_usuario}"},
            salida_esperada="Informe I-V con tesis, contrapesos y conclusiones honestas.",
        ),
        PasoWorkflow(
            nombre="autoverificar",
            descripcion=(
                "Cross-check: verifica cada cita con fuente original (URL), vigencia actual, "
                "que no hay falsos positivos en FTS/semántica, que la síntesis no inventa. "
                "Declara qué NO se pudo verificar."
            ),
            herramienta=None,
            salida_esperada="Informe de verificación con confianza por cita (alta/media/baja).",
        ),
    ],
    "respuesta_consulta": [
        PasoWorkflow(
            nombre="planificar",
            descripcion=(
                "Clasifica la consulta: (a) vigencia de norma, (b) jurisprudencia sobre X, "
                "(c) procedimiento ante Y, (d) doctrina sobre Z. Define herramientas mínimas."
            ),
            herramienta=None,
            salida_esperada="Clasificación y plan de herramientas a usar.",
        ),
        PasoWorkflow(
            nombre="investigar",
            descripcion=(
                "Ejecuta herramientas según clasificación: estado_vigencia, buscar_jurisprudencia, "
                "buscar_normas, buscar_dictamenes, ayuda_acceso_abogado."
            ),
            herramienta="buscar_normas",
            parametros={"consulta": "{consulta_usuario}", "limite": 8},
            salida_esperada="Respuestas directas con fuentes oficiales citadas.",
        ),
        PasoWorkflow(
            nombre="responder",
            descripcion=(
                "Redacta respuesta en formato narrativo jurídico obligatorio: encabezado con "
                "fuente/fecha, explicación contextual, casos con hechos/resolución/alcance, "
                "fragmentos textuales entre comillas, link oficial, conclusión honesta con vacíos."
            ),
            herramienta=None,
            salida_esperada="Respuesta narrativa jurídica completa lista para el usuario.",
        ),
        PasoWorkflow(
            nombre="autoverificar",
            descripcion=(
                "Verifica: formato narrativo cumplido, fechas DD-MM-AAAA, links funcionan, "
                "no hay afirmaciones sin fuente, vacíos declarados."
            ),
            herramienta=None,
            salida_esperada="Confirmación de calidad o lista de correcciones.",
        ),
    ],
}


def obtener_workflow(nombre: str) -> list[PasoWorkflow]:
    """Obtiene un workflow predefinido por nombre."""
    return WORKFLOWS.get(nombre, [])


def listar_workflows() -> str:
    """Lista workflows disponibles."""
    out = ["WORKFLOWS MULTI-ETAPA DISPONIBLES (Fase 5):", ""]
    for key, pasos in WORKFLOWS.items():
        out.append(f"• {key}:")
        for i, p in enumerate(pasos, 1):
            out.append(f"  {i}. {p.nombre.upper()}: {p.descripcion[:100]}...")
        out.append("")
    out.append("Uso: iniciar_workflow('escrito_completo', consulta='despido injustificado', ...)")
    return "\n".join(out)


def iniciar_workflow(
    nombre: str,
    consulta_usuario: str,
    **kwargs: Any,
) -> str:
    """Inicia un workflow multi-etapa y devuelve el plan con el primer paso."""
    workflow = obtener_workflow(nombre)
    if not workflow:
        return f"Workflow '{nombre}' no existe. Disponibles: {list(WORKFLOWS.keys())}"

    # Sustituir placeholders en parámetros
    for paso in workflow:
        if paso.parametros:
            nuevos_params = {}
            for k, v in paso.parametros.items():
                if isinstance(v, str):
                    nuevos_params[k] = v.format(
                        consulta_usuario=consulta_usuario,
                        tipo_escrito=kwargs.get("tipo_escrito", "solicitud"),
                        tribunal=kwargs.get("tribunal", "[TRIBUNAL]"),
                        causa_rol=kwargs.get("causa_rol", "[ROL]"),
                        caratulado=kwargs.get("caratulado", "[CARATULADO]"),
                        leychile_id=kwargs.get("leychile_id", ""),
                    )
                else:
                    nuevos_params[k] = v
            paso.parametros = nuevos_params

    out = [f"🔄 WORKFLOW INICIADO: {nombre.upper()}", ""]
    out.append(f"Consulta: {consulta_usuario}")
    out.append("")
    out.append("PASOS DEL FLUJO:")
    for i, paso in enumerate(workflow, 1):
        out.append(f"  {i}. {paso.nombre.upper()}: {paso.descripcion}")
        if paso.herramienta:
            out.append(f"     Herramienta: {paso.herramienta} {paso.parametros}")
    out.append("")
    out.append("PASO ACTUAL: 1. PLANIFICAR")
    out.append(workflow[0].descripcion)
    out.append("")
    out.append("📋 INSTRUCCIÓN: Ejecuta el plan descrito. Luego avanza al siguiente paso con:")
    out.append("  continuar_workflow('planificar', resultado='<tu plan escrito>', ...)")
    return "\n".join(out)


def continuar_workflow(
    nombre: str,
    paso_actual: str,
    resultado: str,
    **kwargs: Any,
) -> str:
    """Avanza al siguiente paso del workflow con el resultado del paso anterior."""
    workflow = obtener_workflow(nombre)
    if not workflow:
        return f"Workflow '{nombre}' no existe."

    # Encontrar índice del paso actual
    idx = next((i for i, p in enumerate(workflow) if p.nombre == paso_actual), -1)
    if idx == -1:
        return f"Paso '{paso_actual}' no encontrado en workflow '{nombre}'."

    # Marcar completado
    workflow[idx].completado = True
    workflow[idx].resultado = resultado

    # Verificar si hay siguiente paso
    if idx + 1 >= len(workflow):
        # Workflow completado
        out = [f"✅ WORKFLOW '{nombre.upper()}' COMPLETADO", ""]
        out.append("RESUMEN DE PASOS:")
        for p in workflow:
            estado = "✅" if p.completado else "⏳"
            out.append(f"  {estado} {p.nombre.upper()}: {p.resultado[:100]}...")
        out.append("")
        out.append("PRÓXIMOS PASOS MANUALES:")
        out.append("• Revisar borrador generado (.docx/.pdf)")
        out.append("• Completar campos entre corchetes [ ]")
        out.append("• Verificar vigencias con estado_vigencia")
        out.append("• Presentar ante tribunal competente")
        return "\n".join(out)

    # Siguiente paso
    siguiente = workflow[idx + 1]
    out = [f"➡️  PASO {idx + 2}: {siguiente.nombre.upper()}", ""]
    out.append(f"Descripción: {siguiente.descripcion}")
    if siguiente.herramienta:
        out.append(f"Herramienta sugerida: {siguiente.herramienta}")
        out.append(f"Parámetros: {siguiente.parametros}")
    out.append("")
    out.append("📋 INSTRUCCIÓN: Ejecuta la herramienta sugerida o la acción descrita.")
    out.append(f"Luego avanza con: continuar_workflow('{siguiente.nombre}', resultado='<resultado>', ...)")
    return "\n".join(out)


def estado_workflow(nombre: str) -> str:
    """Reporta estado actual de un workflow."""
    workflow = obtener_workflow(nombre)
    if not workflow:
        return f"Workflow '{nombre}' no existe."

    out = [f"ESTADO WORKFLOW: {nombre.upper()}", ""]
    for i, p in enumerate(workflow, 1):
        estado = "✅ COMPLETADO" if p.completado else ("🔄 ACTUAL" if not any(wp.completado for wp in workflow[i:]) else "⏳ PENDIENTE")
        out.append(f"  {i}. {p.nombre.upper()}: {estado}")
        if p.completado:
            out.append(f"     Resultado: {p.resultado[:150]}...")
    return "\n".join(out)