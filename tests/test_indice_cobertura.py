"""Tests para el índice de cobertura y el ruteo interno/externo."""

import sys
sys.path.insert(0, "src")


def test_clasificar_interno_jpl():
    from chilean_legal_mcp.indice_cobertura import clasificar
    r = clasificar("ruidos molestos ordenanza juzgado de policía local")
    assert r["estrategia"] == "interno"
    assert "policia_local" in r["materias"]


def test_clasificar_interno_contraloria():
    from chilean_legal_mcp.indice_cobertura import clasificar
    r = clasificar("dictamen de Contraloría sobre funcionario público municipal")
    assert r["estrategia"] == "interno"
    assert "contraloria" in r["materias"]


def test_clasificar_externo_familia():
    from chilean_legal_mcp.indice_cobertura import clasificar
    r = clasificar("pensión de alimentos en juicio de familia")
    assert r["estrategia"] == "externo"
    assert "familia" in r["materias"]


def test_clasificar_hibrido_sii():
    from chilean_legal_mcp.indice_cobertura import clasificar
    r = clasificar("reclamo tributario ante el SII")
    assert r["estrategia"] == "hibrido"
    assert "sii" in r["materias"]


def test_clasificar_cita_ley_va_a_normas():
    from chilean_legal_mcp.indice_cobertura import clasificar
    r = clasificar("¿qué dice el artículo 14 de la ley 18287?")
    assert "leyes_normas" in r["materias"]


def test_clasificar_sigla_no_falso_positivo():
    from chilean_legal_mcp.indice_cobertura import clasificar
    r = clasificar("marca comercial y derecho de marcas")
    assert "sma" not in r["materias"]


def test_analizar_consulta_usa_clasificar():
    """El motor de respuesta debe llamar a clasificar del índice (ruteo obligatorio)."""
    import inspect
    import chilean_legal_mcp.server as srv
    src = inspect.getsource(srv.analizar_consulta)
    assert "_clasificar(" in src, "analizar_consulta debe rutear con clasificar() del índice de cobertura"


def test_sin_placeholders_en_analizar_consulta():
    """El formato de respuesta no debe contener placeholders genéricos."""
    import inspect
    import chilean_legal_mcp.server as srv
    src = inspect.getsource(srv.analizar_consulta)
    for placeholder in ("[Redactar conclusión", "Criterio 1:", "[título del criterio]"):
        assert placeholder not in src, f"placeholder residual en analizar_consulta: {placeholder}"


def test_numero_a_letras():
    from chilean_legal_mcp.jpl.generator import _numero_a_letras
    assert _numero_a_letras(1) == "un"
    assert _numero_a_letras(21) == "veintiun"
    assert _numero_a_letras(100) == "cien"
    assert _numero_a_letras(1000) == "mil"
    assert _numero_a_letras(1500) == "mil quinientos"
    assert _numero_a_letras(241) == "doscientos cuarenta y un"


def test_sin_trifolia_en_server():
    """No debe quedar branding ajeno (Trifolia) en el servidor."""
    import inspect
    import chilean_legal_mcp.server as srv
    src = inspect.getsource(srv)
    assert "Trifolia" not in src
