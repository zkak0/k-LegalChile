#!/usr/bin/env python3
"""Ingesta de sentencias del Tribunal Constitucional vía buscador oficial.

Fuente primaria (verificada empíricamente):
- Frontend SPA en https://buscador.tcchile.cl/ consulta un backend Paperless
  en https://buscador-paperless.tcchile.cl/api/.
- `GET /api/documents/?page=N&page_size=5&query=QQ` devuelve `count` (total),
  `all` (TODOS los ids que matchean) y `results`; pagina de verdad (page 2..N
  dan ids distintos) pero conserva page_size=5 por petición.
- `GET /api/documents/{id}/` devuelve la ficha con `title` (rol) y `content`
  (texto íntegro de la sentencia).
- El `query` es obligatorio y no vacío: una búsqueda amplia ("de") lo captura todo.
- El token de autenticación queda embebido en el bundle JS del frontend.

Estrategia: una sola búsqueda amplia → `data.all` (todos los ids) → fetch por id
con checkpoint, reintentos y delays; upsert idempotente por id paperless.
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from chilean_legal_mcp.db import NormasDB

PAPERLESS_BASE = "https://buscador-paperless.tcchile.cl/api"
TOKEN = "93fbcc0604a8c5711f2e7ffc10f81a0f02b7c675"
QUERY = "de"

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

_HEADERS = {
    "User-Agent": "k-legalchile/1.0",
    "Accept": "application/json",
    "Authorization": f"Token {TOKEN}",
}

CHECKPOINT_FILE = Path(__file__).resolve().parent.parent / "data" / "ingest_tc_checkpoint.json"


def _bajar_json(url: str, max_retries: int = 4) -> dict:
    req = urllib.request.Request(url, headers=_HEADERS, method="GET")
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=60, context=_SSL_CTX) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, ConnectionRefusedError, ConnectionResetError, ssl.SSLError, TimeoutError) as e:
            if attempt == max_retries - 1:
                raise
            wait = (attempt + 1) * 5
            print(f"[ingest] Error (intento {attempt+1}/{max_retries}): {e}. Espera {wait}s...")
            time.sleep(wait)
    raise RuntimeError("No se pudo conectar tras reintentos")


def _ids_pendientes(db: NormasDB, limit: int | None) -> list[int]:
    url = f"{PAPERLESS_BASE}/documents/?page=1&page_size=5&query={QUERY}"
    d = _bajar_json(url)
    ids = d.get("all", [])
    print(f"[ingest] Corpus TC: {d.get('count', '?')} documentos, {len(ids)} ids en data.all")
    hechos = {r[0] for r in db._conn.execute("SELECT id FROM tc_sentencias").fetchall()}
    pendientes = [i for i in ids if i not in hechos]
    if limit and limit > 0:
        pendientes = pendientes[:limit]
    return pendientes


def _procesar_id(db: NormasDB, doc_id: int) -> bool:
    d = _bajar_json(f"{PAPERLESS_BASE}/documents/{doc_id}/")
    content = d.get("content") or ""
    title = d.get("title") or ""
    materias = d.get("custom_fields") or {}
    materias_text = None
    if isinstance(materias, dict):
        parts = []
        for k, v in materias.items():
            if v is not None and str(v).strip():
                parts.append(f"{k}: {v}")
        if parts:
            materias_text = " | ".join(parts)
    contenido_corto = content[:120000]
    return db.upsert_sentencia_tc(
        doc_id, title or None, d.get("title"), None, None, None, None, None,
        materias_text, contenido_corto[-40000:] if len(content) > 80000 else None,
        None, content, f"{PAPERLESS_BASE}/documents/{doc_id}/",
        json.dumps(d, ensure_ascii=False)[:100000])


def _guardar_checkpoint(ids_restantes: list[int]) -> None:
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_FILE.write_text(json.dumps({"restantes": ids_restantes}, ensure_ascii=False), encoding="utf-8")


def _leer_checkpoint() -> list[int] | None:
    if not CHECKPOINT_FILE.exists():
        return None
    try:
        data = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        return data.get("restantes")
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Ingesta sentencias TC vía buscador Paperless oficial (gratis, token público)")
    ap.add_argument("--limit", type=int, default=0, help="Límite de sentencias a procesar (0 = todas)")
    ap.add_argument("--delay", type=float, default=0.35, help="Delay entre peticiones (seg)")
    ap.add_argument("--no-resumir", action="store_true", help="Ignorar checkpoint y partir de cero")
    ap.add_argument("--resumen", action="store_true", help="Solo muestra estado local")
    ap.add_argument("--reset-checkpoint", action="store_true", help="Borra el checkpoint")
    args = ap.parse_args()

    db = NormasDB()

    if args.reset_checkpoint:
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()
            print("[checkpoint] eliminado")
        else:
            print("[checkpoint] no existía")
        return 0

    if args.resumen:
        nt = db.count_sentencias_tc()
        print(f"[estado] sentencias TC: {nt:,}")
        return 0

    pendientes = _ids_pendientes(db, args.limit)
    if not pendientes:
        print("[ingest] Sin ids pendientes")
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()
        nt = db.count_sentencias_tc()
        print(f"[estado] sentencias TC: {nt:,}")
        return 0

    if not args.no_resumir:
        prev = _leer_checkpoint()
        if prev:
            pendientes = prev
            print(f"[ingest] Reanudando con {len(pendientes)} ids restantes del checkpoint")

    print(f"[ingest] A procesar {len(pendientes)} sentencias")

    nuevos = 0
    i = 0
    while i < len(pendientes):
        doc_id = pendientes[i]
        try:
            if _procesar_id(db, doc_id):
                nuevos += 1
            i += 1
            restantes = pendientes[i:]
            if restantes and i % 25 == 0:
                _guardar_checkpoint(restantes)
            print(f"    [{i}/{len(pendientes)}] id={doc_id} ok")
        except Exception as e:
            print(f"    [{i}/{len(pendientes)}] id={doc_id} ERROR: {e}")
            _guardar_checkpoint(pendientes[i:])
            print("[ingest] checkpoint guardado; se aborta para no martillar")
            break
        time.sleep(args.delay)

    if i >= len(pendientes):
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()
        print("[checkpoint] completado, archivo eliminado")

    nt = db.count_sentencias_tc()
    print(f"[estado] sentencias TC: {nt:,}")
    print(f"[resumen] nuevos={nuevos:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())