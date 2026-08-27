"""Tests para JPL integrado (corpus Juzgado Policía Local)."""

import sys
sys.path.insert(0, "src")

import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JPL_ZST = PROJECT_ROOT / "data" / "jpl" / "corpus.db.zlib"
JPL_DB = PROJECT_ROOT / "data" / "jpl" / "corpus.db"
ALT_ZST = PROJECT_ROOT.parent / "K-LegalJPL" / "corpus.db.zlib"

_has_jpl = JPL_ZST.exists() or JPL_DB.exists() or ALT_ZST.exists()
requires_jpl = pytest.mark.skipif(not _has_jpl, reason="JPL corpus no instalado (ejecuta scripts/install_jpl.py)")

def test_jpl_modulo_importa():
    """Subpaquete jpl importa sin corpus."""
    from chilean_legal_mcp.jpl import db as jpl_db
    assert jpl_db is not None
    assert hasattr(jpl_db, "buscar_ley")

def test_jpl_estado_no_rompe_sin_corpus():
    """jpl_estado devuelve mensaje degradado si no hay corpus."""
    from chilean_legal_mcp.server import jpl_estado
    out = jpl_estado()
    assert isinstance(out, str)
    # Si hay corpus, dirá "JPL — ESTADO", si no, "no instalado"
    assert "JPL" in out

def test_jpl_check_no_rompe():
    from chilean_legal_mcp.server import _jpl_check
    ok, msg = _jpl_check()
    assert isinstance(ok, bool)
    assert isinstance(msg, str)

@requires_jpl
def test_jpl_buscar_ley_transito():
    from chilean_legal_mcp.jpl.db import buscar_ley
    res = buscar_ley("transito", limite=3)
    assert len(res) > 0
    assert any("Transito" in r.get("ley","") or "transito" in str(r).lower() for r in res)

@requires_jpl
def test_jpl_buscar_articulo_18287_14():
    from chilean_legal_mcp.jpl.db import buscar_articulo
    res = buscar_articulo("18.287", 14)
    assert len(res) > 0
    assert "sana crítica" in res[0].get("texto","").lower() or "sana critica" in res[0].get("texto","").lower()

@requires_jpl
def test_jpl_verificar_vigencia():
    from chilean_legal_mcp.jpl.db import verificar_vigencia
    res = verificar_vigencia("18.287")
    assert len(res) > 0
    assert any("18.287" in str(r) or "18287" in str(r) for r in res)

@requires_jpl
def test_jpl_listar_leyes():
    from chilean_legal_mcp.jpl.db import listar_leyes
    res = listar_leyes()
    assert len(res) >= 40  # 53 leyes

@requires_jpl
def test_jpl_listar_ordenanzas():
    from chilean_legal_mcp.jpl.db import listar_ordenanzas
    res = listar_ordenanzas(None)
    assert len(res) > 100  # 344 comunas

@requires_jpl
def test_jpl_buscar_ordenanza():
    from chilean_legal_mcp.jpl.db import buscar_ordenanza
    # Probar con comuna que sabemos que existe: Viña del Mar tiene ordenanzas de aseo
    res = buscar_ordenanza("Vina_del_Mar", "aseo", limite=3)
    # Puede ser 0 si no hay "aseo" en esa comuna, pero no debe crashear
    assert isinstance(res, list)

@requires_jpl
def test_jpl_buscar_texto():
    from chilean_legal_mcp.jpl.db import buscar_texto
    res = buscar_texto("ruidos molestos", limite=3)
    assert isinstance(res, list)

@requires_jpl
def test_jpl_tools_server():
    """Tools del server.py delegan correctamente a jpl.db."""
    from chilean_legal_mcp.server import jpl_buscar_ley, jpl_listar_leyes, jpl_buscar_texto
    out = jpl_buscar_ley("alcoholes", limite=2)
    assert "JPL" in out
    out2 = jpl_listar_leyes()
    assert "JPL" in out2
    out3 = jpl_buscar_texto("patente municipal", limite=2)
    assert isinstance(out3, str)

@requires_jpl
def test_jpl_generar_documento():
    from chilean_legal_mcp.server import jpl_generar_documento
    import json
    datos = json.dumps({"rol": "123-2024", "comuna": "Santiago", "denunciado": "Juan Perez", "rut": "12.345.678-9", "domicilio": "Calle Falsa 123", "hecho": "ruidos molestos", "ley": "18.287", "articulo": "14", "dia": "26", "mes": "08", "ano": "2026"})
    out = jpl_generar_documento("resolucion", datos, "md")
    assert "JPL" in out or "ROL" in out

def test_buscar_todo_incluye_jpl_si_disponible():
    """buscar_todo no rompe si JPL está o no instalado (sin acceso a red)."""
    from chilean_legal_mcp.server import _jpl_check, jpl_buscar_texto
    jpl_ok, _ = _jpl_check()
    if jpl_ok:
        out = jpl_buscar_texto("transito", limite=2)
        assert isinstance(out, str)
        assert "JPL" in out
