"""Tests para workflow multi-etapa (Fase 5) — prompt estructurado."""

import sys
sys.path.insert(0, "src")

import pytest

from chilean_legal_mcp.workflow import (
    obtener_workflow,
    listar_workflows,
    iniciar_workflow,
    continuar_workflow,
    estado_workflow,
    PasoWorkflow,
    WORKFLOWS,
)


def test_workflows_existen():
    """Los 3 workflows predefinidos existen."""
    assert "escrito_completo" in WORKFLOWS
    assert "investigacion_profunda" in WORKFLOWS
    assert "respuesta_consulta" in WORKFLOWS


def test_workflow_escrito_completo_pasos():
    """escrito_completo tiene 4 pasos en orden correcto."""
    wf = obtener_workflow("escrito_completo")
    assert len(wf) == 4
    assert [p.nombre for p in wf] == ["planificar", "investigar", "redactar", "autoverificar"]


def test_workflow_investigacion_profunda_pasos():
    """investigacion_profunda tiene 4 pasos."""
    wf = obtener_workflow("investigacion_profunda")
    assert len(wf) == 4
    assert [p.nombre for p in wf] == ["planificar", "investigar", "sintetizar", "autoverificar"]


def test_workflow_respuesta_consulta_pasos():
    """respuesta_consulta tiene 4 pasos."""
    wf = obtener_workflow("respuesta_consulta")
    assert len(wf) == 4
    assert [p.nombre for p in wf] == ["planificar", "investigar", "responder", "autoverificar"]


def test_listar_workflows():
    """listar_workflows devuelve string con todos los workflows."""
    out = listar_workflows()
    assert "WORKFLOWS MULTI-ETAPA" in out
    assert "escrito_completo" in out
    assert "investigacion_profunda" in out
    assert "respuesta_consulta" in out


def test_iniciar_workflow_valido():
    """iniciar_workflow devuelve plan con primer paso."""
    out = iniciar_workflow("escrito_completo", "despido injustificado", tribunal="Corte Santiago")
    assert "WORKFLOW INICIADO" in out
    assert "ESCRITO_COMPLETO" in out.upper()
    assert "despido injustificado" in out
    assert "Corte Santiago" in out
    assert "PASO ACTUAL: 1. PLANIFICAR" in out


def test_iniciar_workflow_invalido():
    """iniciar_workflow rechaza workflow inexistente."""
    out = iniciar_workflow("inexistente", "consulta")
    assert "no existe" in out.lower()


def test_continuar_workflow_avanza():
    """continuar_workflow avanza al siguiente paso."""
    iniciar_workflow("escrito_completo", "despido injustificado")
    out = continuar_workflow("escrito_completo", "planificar", "Plan: escrito de reposición ante Juzgado Laboral")
    assert "PASO 2: INVESTIGAR" in out
    assert "investigar" in out.lower()


def test_continuar_workflow_paso_invalido():
    """continuar_workflow rechaza paso inexistente."""
    out = continuar_workflow("escrito_completo", "paso_falso", "resultado")
    assert "no encontrado" in out.lower()


def test_continuar_workflow_completa():
    """continuar_workflow completa el workflow al final."""
    iniciar_workflow("respuesta_consulta", "vigencia ley 21.643")
    continuar_workflow("respuesta_consulta", "planificar", "Plan: consultar estado_vigencia")
    continuar_workflow("respuesta_consulta", "investigar", "Ley 21.643 vigente desde 15-01-2024")
    continuar_workflow("respuesta_consulta", "responder", "Respuesta narrativa con cita oficial")
    out = continuar_workflow("respuesta_consulta", "autoverificar", "Verificado: vigencia OK, cita OK")
    assert "COMPLETADO" in out
    assert "RESPUESTA_CONSULTA" in out.upper()


def test_estado_workflow():
    """estado_workflow reporta progreso."""
    iniciar_workflow("escrito_completo", "test")
    out = estado_workflow("escrito_completo")
    assert "ESTADO WORKFLOW" in out
    assert "PLANIFICAR" in out
    assert "INVESTIGAR" in out


def test_paso_workflow_dataclass():
    """PasoWorkflow se crea correctamente."""
    paso = PasoWorkflow(
        nombre="test",
        descripcion="descripción",
        herramienta="herramienta_test",
        parametros={"k": "v"},
    )
    assert paso.nombre == "test"
    assert paso.herramienta == "herramienta_test"
    assert paso.parametros == {"k": "v"}
    assert paso.completado is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])