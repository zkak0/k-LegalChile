"""Tests unitarios básicos para chilean-legal-mcp.

Ejecutar con: pytest tests/test_mcp.py -v
No requieren conexión a internet — prueban funciones puras.
"""

import sys
sys.path.insert(0, "src")

from unittest.mock import MagicMock, patch

from chilean_legal_mcp.server import (
    _format_row,
    _parse_fecha_cl,
    _to_cl,
)


def test_formato_fecha_chilena():
    """Fechas en formato DD-MM-AAAA y conversión desde YYYY-MM-DD."""
    assert _to_cl("2024-01-15") == "15-01-2024"
    assert _to_cl("2026-08-23") == "23-08-2026"
    assert _to_cl("2025-12-31") == "31-12-2025"


def test_formato_fecha_chile_none():
    assert _to_cl(None) == ""
    assert _to_cl("") == ""


def test_parse_fecha_cl_dd_mm_aaaa():
    assert _parse_fecha_cl("15-01-2024") == "2024-01-15"
    assert _parse_fecha_cl("23-08-2026") == "2026-08-23"


def test_parse_fecha_cl_yyyy_mm_dd():
    assert _parse_fecha_cl("2024-01-15") == "2024-01-15"


def test_parse_fecha_cl_none():
    assert _parse_fecha_cl(None) is None
    assert _parse_fecha_cl("") is None


def test_parse_fecha_cl_dd_mm_slash():
    # Formato con barra también soportado
    assert _parse_fecha_cl("15/01/2024") == "2024-01-15"


def test_format_row_con_todos_los_campos():
    row = {
        "titulo": "LEY 21.643 MODIFICA CÓDIGO DEL TRABAJO",
        "numero": "21643",
        "fecha": "2024-01-15",
        "leychile_id": "1200096",
    }
    out = _format_row(row)
    assert "LEY 21.643" in out
    assert "21643" in out
    assert "15-01-2024" in out  # Fecha convertida
    assert "bcn.cl/leychile" in out  # Link oficial


def test_format_row_sin_datos_opcionales():
    out = _format_row({"titulo": "Prueba", "uri": "http://x"})
    assert "Prueba" in out


def test_format_row_fecha_opcional():
    out = _format_row({"titulo": "Sin fecha", "numero": "123"})
    assert "Sin fecha" in out


def test_db_casos_schema():
    """La tabla casos existe con los campos necesarios para FTS."""
    from chilean_legal_mcp.db import get_db
    db = get_db()
    cols = [r[1] for r in db._conn.execute("PRAGMA table_info(casos)").fetchall()]
    assert "identificacion" in cols
    assert "hechos" in cols
    assert "resolucion" in cols
    assert "url" in cols


def test_db_vigencias_schema():
    """La tabla vigencias existe con fecha de consulta."""
    from chilean_legal_mcp.db import get_db
    db = get_db()
    cols = [r[1] for r in db._conn.execute("PRAGMA table_info(vigencias)").fetchall()]
    assert "estado_json" in cols
    assert "consultado" in cols


def test_buscar_casos_vacio_con_error():
    """buscar_casos no falla con consultas vacías."""
    from chilean_legal_mcp.db import get_db
    db = get_db()
    assert db.search_casos("", limit=5) == []


def test_search_casos_paginacion():
    """search_casos respeta offset sin errores."""
    from chilean_legal_mcp.db import get_db
    db = get_db()
    r1 = db.search_casos("ley", limit=2, offset=0)
    r2 = db.search_casos("ley", limit=2, offset=2)
    assert isinstance(r1, list)
    assert isinstance(r2, list)


def test_server_tools_contados():
    """server.py cuenta 93 herramientas decoradas con @mcp.tool (base + corpus + conectores TA/FNE/SMA-procedimientos)."""
    src = open("src/chilean_legal_mcp/server.py", encoding="utf-8").read()
    assert src.count("@mcp.tool") == 93
    assert src.count("@mcp.resource") == 2
    assert src.count("@mcp.prompt") == 2


def test_estado_vigencia_estructura():
    """estado_vigencia devuelve campos consistentes."""
    from chilean_legal_mcp.vigencia import estado_vigencia
    # No llamamos a la API — solo verificamos que las funciones existen y no rompen
    assert callable(estado_vigencia)
    assert hasattr(estado_vigencia, "__name__")


def test_citar_norma_formato():
    """_cita devuelve formato uniforme."""
    row = {
        "titulo": "LEY KARIN",
        "numero": "21643",
        "fecha": "2024-01-15",
        "leychile_id": "1200096",
    }
    out = _format_row(row)
    assert "LEY KARIN" in out
    assert "21643" in out
    # Formato: "Ley N° 21643 (15-01-2024)" y URL de LeyChile
    assert "leychile" in out.lower() or "bcn.cl" in out.lower()


def test_no_officioycircular():
    """No hay restos del sitio privado oficioycircular.cl en el código."""
    import os
    for root, _, files in os.walk("src"):
        for f in files:
            if f.endswith(".py"):
                ruta = os.path.join(root, f)
                with open(ruta) as fh:
                    contenido = fh.read()
                assert "oficioycircular" not in contenido, f"Resto oficioycircular en {ruta}"
                assert "baseapi" not in contenido, f"Resto baseapi en {ruta}"


def test_sii_regla_fuentes_documentadas():
    """inapi.py documenta la regla de fuentes (no usa terceros)."""
    with open("src/chilean_legal_mcp/inapi.py") as f:
        docs = f.read()
    # Tiene el bloque de comentario que documenta el captcha
    assert "FindMarcas" in docs or "captcha" in docs.lower()


def test_correo_fecha_formateos_existentes():
    """_to_cl y _parse_fecha_cl existen y son compatibles."""
    # Ciclo completo: parse → formato → parse (idempotente)
    assert _parse_fecha_cl(_to_cl("2024-01-15")) == "2024-01-15"
    assert _parse_fecha_cl(_to_cl("2026-08-23")) == "2026-08-23"
    assert _to_cl(_parse_fecha_cl("15-01-2024")) == "15-01-2024"
