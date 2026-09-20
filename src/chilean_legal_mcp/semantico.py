"""Búsqueda semántica con embeddings locales (sentence-transformers) — Fase 3 Magnar libre."""

from __future__ import annotations

import numpy as np
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    _HAS_EMBEDDINGS = True
except Exception:
    _HAS_EMBEDDINGS = False

_MODEL: SentenceTransformer | None = None
_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _get_model() -> SentenceTransformer | None:
    global _MODEL
    if not _HAS_EMBEDDINGS:
        return None
    if _MODEL is None:
        _MODEL = SentenceTransformer(_MODEL_NAME)
    return _MODEL


def _chunk_texto(texto: str, max_chars: int = 1500, overlap: int = 200) -> list[str]:
    """Divide texto en chunks con overlap para embeddings."""
    if len(texto) <= max_chars:
        return [texto]
    chunks = []
    start = 0
    while start < len(texto):
        end = min(start + max_chars, len(texto))
        chunks.append(texto[start:end])
        if end >= len(texto):
            break
        start = end - overlap
    return chunks


def indexar_normas(db, limite: int = 1000) -> dict:
    """Indexa normas cacheadas (tabla textos) en embeddings."""
    model = _get_model()
    if not model:
        return {"error": "sentence-transformers no instalado. pip install sentence-transformers"}

    rows = db._conn.execute(
        "SELECT leychile_id, texto FROM textos LIMIT ?", (limite,)
    ).fetchall()

    count = 0
    for r in rows:
        leychile_id = r["leychile_id"]
        texto = r["texto"]
        chunks = _chunk_texto(texto)
        for idx, chunk in enumerate(chunks):
            emb = model.encode(chunk, normalize_embeddings=True)
            db.upsert_embedding("normas", leychile_id, idx, chunk, emb.astype(np.float32).tobytes())
            count += 1
    return {"indexados": count, "normas": len(rows)}


def indexar_jurisprudencia(db, limite: int = 500) -> dict:
    """Indexa casos reales (tabla casos) en embeddings."""
    model = _get_model()
    if not model:
        return {"error": "sentence-transformers no instalado. pip install sentence-transformers"}

    rows = db._conn.execute(
        "SELECT id, hechos, resolucion, organismo, identificacion FROM casos LIMIT ?", (limite,)
    ).fetchall()

    count = 0
    for r in rows:
        cid = r["id"]
        texto = f"{r['hechos']} {r['resolucion']}".strip()
        if not texto:
            continue
        chunks = _chunk_texto(texto)
        for idx, chunk in enumerate(chunks):
            emb = model.encode(chunk, normalize_embeddings=True)
            db.upsert_embedding("jurisprudencia", cid, idx, chunk, emb.astype(np.float32).tobytes())
            count += 1
    return {"indexados": count, "casos": len(rows)}


def indexar_dictamenes(db, limite: int = 10000) -> dict:
    """Indexa dictámenes CGR (tabla cgr_dictamenes — corpus K-LegalChile) en embeddings.

    Fuente_tipo 'dictamenes'. Con limite=0 indexa todo el corpus local.
    """
    model = _get_model()
    if not model:
        return {"error": "sentence-transformers no instalado. pip install sentence-transformers"}

    sql = "SELECT id, numero, fecha, organismo_consultante, sumario FROM cgr_dictamenes"
    params: list = []
    if limite and limite > 0:
        sql += " LIMIT ?"
        params.append(int(limite))
    rows = db._conn.execute(sql, params).fetchall()

    count = 0
    for r in rows:
        cid = r["id"]
        texto = f"{r['numero'] or ''} {r['fecha'] or ''} {r['organismo_consultante'] or ''} {r['sumario'] or ''}".strip()
        if not texto:
            continue
        chunks = _chunk_texto(texto)
        for idx, chunk in enumerate(chunks):
            emb = model.encode(chunk, normalize_embeddings=True)
            db.upsert_embedding("dictamenes", cid, idx, chunk, emb.astype(np.float32).tobytes())
            count += 1
    return {"indexados": count, "dictamenes": len(rows)}


def indexar_expedientes(db, expediente_id: int | None = None) -> dict:
    """Indexa documentos de expedientes (tabla expediente_docs) en embeddings."""
    model = _get_model()
    if not model:
        return {"error": "sentence-transformers no instalado. pip install sentence-transformers"}

    sql = "SELECT id, expediente_id, titulo, texto FROM expediente_docs"
    params: list = []
    if expediente_id:
        sql += " WHERE expediente_id = ?"
        params.append(expediente_id)
    rows = db._conn.execute(sql, params).fetchall()

    count = 0
    for r in rows:
        doc_id = f"{r['expediente_id']}:{r['id']}"
        texto = f"{r['titulo']} {r['texto']}".strip()
        if not texto:
            continue
        chunks = _chunk_texto(texto)
        for idx, chunk in enumerate(chunks):
            emb = model.encode(chunk, normalize_embeddings=True)
            db.upsert_embedding("expedientes", doc_id, idx, chunk, emb.astype(np.float32).tobytes())
            count += 1
    return {"indexados": count, "documentos": len(rows)}


def indexar_semantico(db, fuente: str = "todas", limite: int = 1000) -> dict:
    """Indexa una o todas las fuentes en embeddings."""
    resultados = {}
    if fuente in ("todas", "normas"):
        resultados["normas"] = indexar_normas(db, limite)
    if fuente in ("todas", "jurisprudencia"):
        resultados["jurisprudencia"] = indexar_jurisprudencia(db, limite)
    if fuente in ("todas", "dictamenes"):
        resultados["dictamenes"] = indexar_dictamenes(db, limite)
    if fuente in ("todas", "expedientes"):
        resultados["expedientes"] = indexar_expedientes(db)
    return resultados


def buscar_semantico(db, query: str, top_k: int = 10, fuente: str | None = None) -> list[dict]:
    """Busca por similitud semántica en embeddings indexados."""
    model = _get_model()
    if not model:
        return [{"error": "sentence-transformers no instalado. pip install sentence-transformers"}]

    q_emb = model.encode(query, normalize_embeddings=True)
    return db.search_embeddings(q_emb.astype(np.float32).tobytes(), top_k=top_k, fuente_tipo=fuente)


def formatear_resultado_semantico(resultados: list[dict], query: str) -> str:
    """Formatea resultados semánticos en narrativa jurídica."""
    if not resultados:
        return f"Búsqueda semántica para '{query}': sin resultados indexados. Ejecuta indexar_semantico primero."
    if "error" in resultados[0]:
        return resultados[0]["error"]

    out = [f"BÚSQUEDA SEMÁNTICA para '{query}' ({len(resultados)} resultados):", ""]
    for r in resultados:
        tipo = r["fuente_tipo"]
        fid = r["fuente_id"]
        score = r["score"]
        texto = r["texto"][:300].replace("\n", " ")
        out.append(f"• [{tipo}] {fid} (chunk {r['chunk_idx']}) — score: {score:.3f}")
        out.append(f"  Extracto: {texto}...")
        out.append("")
    out.append("🔗 Para texto completo usa obtener_texto_norma (normas), ficha_dictamen_corpus (dictámenes) o expediente_preguntar (expedientes).")
    return "\n".join(out)


def estado_indexacion(db) -> str:
    """Reporta estado de la indexación semántica."""
    total = db.count_embeddings()
    by_tipo = db._conn.execute(
        "SELECT fuente_tipo, COUNT(*) as n FROM embeddings GROUP BY fuente_tipo"
    ).fetchall()
    desglose = ", ".join(f"{r['fuente_tipo']}: {r['n']}" for r in by_tipo)
    model_status = "instalado ✓" if _HAS_EMBEDDINGS else "NO instalado ✗ (pip install sentence-transformers)"
    return (f"Embeddings semánticos: {total} chunks indexados ({desglose or 'vacío'}). "
            f"Modelo: {_MODEL_NAME} — {model_status}")