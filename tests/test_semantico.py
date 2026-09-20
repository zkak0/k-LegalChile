"""Tests para búsqueda semántica (Fase 3) — embeddings locales."""

import sys
sys.path.insert(0, "src")

import pytest

try:
    from chilean_legal_mcp.semantico import (
        _chunk_texto,
        _get_model,
        _HAS_EMBEDDINGS,
        indexar_normas,
        indexar_jurisprudencia,
        indexar_semantico,
        buscar_semantico,
        formatear_resultado_semantico,
        estado_indexacion,
    )
    from chilean_legal_mcp.db import get_db
except Exception as e:
    pytest.skip(f"Imports failed: {e}", allow_module_level=True)


def test_chunk_texto_basico():
    """_chunk_texto divide correctamente con overlap."""
    texto = "A" * 2000
    chunks = _chunk_texto(texto, max_chars=500, overlap=100)
    assert len(chunks) >= 3
    # Verificar overlap
    assert chunks[0][-100:] == chunks[1][:100]


def test_chunk_texto_corto():
    """Texto corto no se divide."""
    chunks = _chunk_texto("Hola mundo", max_chars=100)
    assert len(chunks) == 1
    assert chunks[0] == "Hola mundo"


def test_modelo_carga_si_disponible():
    """Si sentence-transformers está instalado, el modelo carga."""
    if not _HAS_EMBEDDINGS:
        pytest.skip("sentence-transformers no instalado")
    model = _get_model()
    assert model is not None


def test_estado_indexacion_no_rompe():
    """estado_indexacion devuelve string informativo sin errores."""
    db = get_db()
    out = estado_indexacion(db)
    assert isinstance(out, str)
    assert "Embeddings semánticos" in out


def test_indexar_normas_sin_modelo():
    """indexar_normas reporta error si no hay modelo."""
    db = get_db()
    res = indexar_normas(db, limite=5)
    if not _HAS_EMBEDDINGS:
        assert "error" in res
        assert "sentence-transformers" in res["error"]


def test_indexar_jurisprudencia_sin_modelo():
    """indexar_jurisprudencia reporta error si no hay modelo."""
    db = get_db()
    res = indexar_jurisprudencia(db, limite=5)
    if not _HAS_EMBEDDINGS:
        assert "error" in res


def test_indexar_semantico_fuentes():
    """indexar_semantico acepta parámetro fuente."""
    db = get_db()
    res = indexar_semantico(db, fuente="normas", limite=2)
    assert isinstance(res, dict)


def test_buscar_semantico_vacio():
    """buscar_semantico con consulta vacía es coherente: sin modelo reporta error; con modelo y data devuelve resultados."""
    db = get_db()
    res = buscar_semantico(db, "")
    assert isinstance(res, list)
    if not _HAS_EMBEDDINGS:
        assert res and "error" in res[0]
    elif res:
        assert "error" not in res[0]


def test_formatear_resultado_semantico():
    """formatear_resultado_semantico produce narrativa legible."""
    resultados = [{
        "fuente_tipo": "normas",
        "fuente_id": "12345",
        "chunk_idx": 0,
        "score": 0.85,
        "texto": "Artículo 1. Esta ley establece..."
    }]
    out = formatear_resultado_semantico(resultados, "ley karin")
    assert "BÚSQUEDA SEMÁNTICA" in out
    assert "normas" in out
    assert "0.85" in out
    assert "ley karin" in out.lower()


def test_formatear_resultado_semantico_vacio():
    """formatear_resultado_semantico maneja lista vacía."""
    out = formatear_resultado_semantico([], "query")
    assert "sin resultados indexados" in out.lower()


def test_db_embeddings_schema():
    """Tabla embeddings existe con campos correctos."""
    db = get_db()
    cols = [r[1] for r in db._conn.execute("PRAGMA table_info(embeddings)").fetchall()]
    assert "fuente_tipo" in cols
    assert "fuente_id" in cols
    assert "chunk_idx" in cols
    assert "texto" in cols
    assert "vector" in cols
    assert "created_at" in cols


def test_db_embeddings_upsert_y_search():
    """upsert_embedding y search_embeddings funcionan (mock vector)."""
    import numpy as np
    db = get_db()
    vec = np.array([0.1, 0.2, 0.3], dtype=np.float32).tobytes()
    db.upsert_embedding("test", "id1", 0, "texto prueba", vec)
    # Search with similar vector
    q_vec = np.array([0.1, 0.2, 0.3], dtype=np.float32).tobytes()
    res = db.search_embeddings(q_vec, top_k=5)
    assert isinstance(res, list)
    # Cleanup
    db._conn.execute("DELETE FROM embeddings WHERE fuente_tipo='test'")
    db._conn.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])