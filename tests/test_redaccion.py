"""Tests para redacción de escritos (Fase 4) — generación de borradores."""

import sys
sys.path.insert(0, "src")

import pytest

from chilean_legal_mcp.redaccion import (
    _construir_hechos,
    _construir_fundamentos,
    _construir_petitorio,
    _extraer_citas_de_texto,
    TIPOS_ESCRITO,
    generar_escrito,
    generar_escrito_desde_investigacion,
)
from chilean_legal_mcp.db import get_db


def test_tipos_escrito_dict():
    """TIPOS_ESCRITO tiene las claves esperadas."""
    assert "reposicion" in TIPOS_ESCRITO
    assert "apelacion" in TIPOS_ESCRITO
    assert "proteccion" in TIPOS_ESCRITO
    assert "solicitud" in TIPOS_ESCRITO
    assert TIPOS_ESCRITO["reposicion"] == "Recurso de Reposición"


def test_construir_hechos_lista():
    """_construir_hechos numera correctamente una lista."""
    hechos = ["Hecho primero", "Hecho segundo", "Hecho tercero"]
    out = _construir_hechos(hechos)
    assert "1º Hecho primero" in out
    assert "2º Hecho segundo" in out
    assert "3º Hecho tercero" in out


def test_construir_hechos_string():
    """_construir_hechos acepta string con saltos de línea."""
    hechos = "Hecho uno\nHecho dos\n\nHecho tres"
    out = _construir_hechos(hechos)
    assert "1º Hecho uno" in out
    assert "2º Hecho dos" in out
    assert "3º Hecho tres" in out


def test_construir_fundamentos_vacio():
    """_construir_fundamentos maneja lista vacía."""
    out = _construir_fundamentos([], "consulta")
    assert "FUNDAMENTOS DE DERECHO" in out
    assert "Pendiente" in out


def test_construir_fundamentos_con_datos():
    """_construir_fundamentos formatea fuentes correctamente."""
    fundamentos = [{
        "fuente": "Ley 21.643",
        "cita": "Ley N° 21643 (15-01-2024)",
        "texto": "Modifica el Código del Trabajo en materia de acoso laboral."
    }]
    out = _construir_fundamentos(fundamentos, "acoso")
    assert "Ley 21.643" in out
    assert "Ley N° 21643" in out
    assert "acoso laboral" in out


def test_construir_petitorio():
    """_construir_petitorio usa numeración romana."""
    petitorio = ["Petición primera", "Petición segunda", "Petición tercera"]
    out = _construir_petitorio(petitorio)
    assert "PRIMERO.-" in out
    assert "SEGUNDO.-" in out
    assert "TERCERO.-" in out


def test_extraer_citas_ley():
    """_extraer_citas_de_texto detecta 'Ley N° XXXX'."""
    texto = "Según la Ley N° 21.643 y la Ley N° 20.005..."
    citas = _extraer_citas_de_texto(texto)
    assert len(citas) == 2
    assert citas[0]["numero"] == "21.643"
    assert citas[1]["numero"] == "20.005"


def test_extraer_citas_articulo():
    """_extraer_citas_de_texto detecta 'artículo X'."""
    texto = "El artículo 154 bis del Código del Trabajo..."
    citas = _extraer_citas_de_texto(texto)
    assert any(c["tipo"] == "articulo" and c["numero"] == "154" for c in citas)


def test_generar_escrito_basico():
    """generar_escrito produce texto con estructura correcta."""
    db = get_db()
    resultado = generar_escrito(
        db=db,
        tipo="solicitud",
        tribunal="Ilustrísima Corte de Apelaciones de Santiago",
        causa_rol="Rol N° 1234-2024",
        caratulado="PÉREZ c/ EMPRESA S.A.",
        hechos=["Hecho 1: El demandante fue despedido.", "Hecho 2: No se pagó indemnización."],
        fundamentos=[{
            "fuente": "Código del Trabajo",
            "cita": "Art. 168 CT",
            "texto": "El despido injustificado da derecho a indemnización."
        }],
        petitorio=["Se acoja la demanda", "Se condene al pago de indemnizaciones"],
        formato="docx",
    )
    assert "SOLICITUD" in resultado.upper()
    assert "PÉREZ" in resultado and "EMPRESA" in resultado
    assert "Rol N° 1234-2024" in resultado
    assert "HECHOS" in resultado
    assert "FUNDAMENTOS DE DERECHO" in resultado
    assert "PETITORIO" in resultado
    assert "PRIMERO.-" in resultado
    assert "SEGUNDO.-" in resultado
    assert ".docx" in resultado or ".pdf" in resultado  # ruta de archivo


def test_generar_escrito_tipo_invalido():
    """generar_escrito usa tipo genérico para tipo desconocido."""
    db = get_db()
    resultado = generar_escrito(
        db=db,
        tipo="tipo_inexistente",
        tribunal="TRIBUNAL",
        causa_rol="ROL",
        caratulado="CARATULADO",
        hechos=["Hecho"],
        formato="docx",
    )
    assert "ESCRITO JURÍDICO GENÉRICO" in resultado.upper()


def test_generar_escrito_desde_investigacion_no_rompe():
    """generar_escrito_desde_investigacion ejecuta sin errores (puede fallar por red)."""
    db = get_db()
    # Solo verificamos que la función existe y no rompe con entrada válida
    # (puede fallar por conexiones de red, pero no debe crashear)
    try:
        resultado = generar_escrito_desde_investigacion(
            db=db,
            consulta="despido injustificado indemnización",
            tipo="solicitud",
            tribunal="TRIBUNAL",
            causa_rol="ROL",
            caratulado="CARATULADO",
            formato="docx",
        )
        assert isinstance(resultado, str)
        assert len(resultado) > 0
    except Exception as e:
        # Errores de red son esperables en test sin mock
        assert "red" in str(e).lower() or "conexion" in str(e).lower() or "timeout" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])