#!/usr/bin/env python3
"""Ingesta del corpus jurídico de dictámenes CGR — corpus K-LegalChile.

Descarga los exports gratuitos CSV de dictámenes CGR y del grafo de citaciones
(dataset público de datos abiertos), los guarda en bruto en data/,
los ordena por fecha descendente y los indexa en la base local (FTS5 + opcional
embeddings semánticos). Idempotente: los registros ya presentes se conservan.

Uso:
    python scripts/ingest_dictamenes.py                  # ingesta dictámenes + citaciones
    python scripts/ingest_dictamenes.py --solo dictamenes
    python scripts/ingest_dictamenes.py --solo citaciones
    python scripts/ingest_dictamenes.py --index-semantico   # además indexa embeddings
    python scripts/ingest_dictamenes.py --resumen           # solo muestra estado local
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from chilean_legal_mcp.db import NormasDB  # noqa: E402

BASE = "https://datos.cochid.cl"
DATASET_DICTAMENES = "cochid_lex_dictamenes_cgr"
DATASET_CITACIONES = "cochid_lex_citations"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_RE_UNID = re.compile(r"([0-9A-Fa-f]{32})")


def _bajar(dataset: str, destino: Path) -> int:
    """Descarga el export CSV completo (acceso libre, tope 10.000 filas). Devuelve bytes."""
    url = f"{BASE}/api/dataset/{dataset}/export.csv?limit=all"
    print(f"[ingest] Descargando {url} …")
    req = urllib.request.Request(url, headers={"User-Agent": "k-legalchile/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    destino.write_bytes(data)
    print(f"[ingest] Guardado: {destino} ({len(data):,} bytes)")
    return len(data)


def _parse_unid(source_url: str | None) -> str | None:
    if not source_url:
        return None
    m = _RE_UNID.search(source_url)
    return m.group(1).upper() if m else None


def _ingestar_dictamenes(db: NormasDB, ruta: Path) -> dict:
    filas = 0
    nuevos = 0
    anios: dict[str, int] = {}
    filas_fecha = 0
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            return {"error": "CSV vacío"}
        cols = {c: i for i, c in enumerate(header)}
        for row in reader:
            filas += 1
            if not row or not any(row):
                continue
            id_ = row[cols["id"]].strip()
            numero = row[cols["numero"]].strip() if cols.get("numero") is not None else ""
            fecha = (row[cols["fecha"]].strip() if cols.get("fecha") is not None else "") or None
            org = (row[cols["organismo_consultante"]].strip() if cols.get("organismo_consultante") is not None else "") or None
            sumario = row[cols["sumario"]].strip() if cols.get("sumario") is not None else ""
            source_url = (row[cols["source_url"]].strip() if cols.get("source_url") is not None else "") or None
            anio = None
            if fecha and len(fecha) >= 4:
                try:
                    anio = int(fecha[:4])
                    anios[str(anio)] = anios.get(str(anio), 0) + 1
                except ValueError:
                    anio = None
            unid = _parse_unid(source_url)
            if db.upsert_dictamen_cgr(id_, numero, anio, fecha, org, sumario if sumario else None,
                                      source_url, unid, None):
                nuevos += 1
    print(f"[ingest] dictamenes: {nuevos:,} nuevos de {filas:,} filas")
    if anios:
        top = sorted(anios.items(), key=lambda kv: -kv[1])[:5]
        print("[ingest] anios dominantes:", ", ".join(f"{k}: {v}" for k, v in top))
    return {"filas": filas, "nuevos": nuevos}


def _ingestar_citaciones(db: NormasDB, ruta: Path) -> dict:
    filas = 0
    nuevos = 0
    tipos: set[str] = set()
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            return {"error": "CSV vacío"}
        cols = {c: i for i, c in enumerate(header)}
        for row in reader:
            filas += 1
            if not row or not any(row):
                continue
            try:
                id_ = int(row[cols["id"]].strip())
            except (ValueError, KeyError):
                continue
            source_kind = row[cols["source_kind"]].strip() if cols.get("source_kind") is not None else ""
            source_id = row[cols["source_id"]].strip() if cols.get("source_id") is not None else ""
            target_kind = row[cols["target_kind"]].strip() if cols.get("target_kind") is not None else None
            target_id = row[cols["target_id"]].strip() if cols.get("target_id") is not None else None
            ref = row[cols["target_external_ref"]].strip() if cols.get("target_external_ref") is not None else None
            tipo = row[cols["tipo"]].strip() if cols.get("tipo") is not None else None
            conf = None
            if cols.get("confidence") is not None:
                try:
                    conf = float(row[cols["confidence"]].strip())
                except ValueError:
                    conf = None
            if tipo:
                tipos.add(tipo)
            if db.upsert_cita(id_, source_kind or "?", source_id or "?",
                              target_kind, target_id, ref or None, tipo or None, conf):
                nuevos += 1
    print(f"[ingest] citaciones: {nuevos:,} nuevas de {filas:,} filas — tipos: {sorted(tipos)}")
    return {"filas": filas, "nuevos": nuevos}


def _resumen(db: NormasDB) -> None:
    nd = db.count_dictamenes_cgr()
    nc = db.count_citas_legales()
    nk = db.count_criterios()
    print(f"[estado] dictamenes CGR: {nd:,}")
    print(f"[estado] aristas de citación: {nc:,}")
    print(f"[estado] criterios_estado: {nk:,}")
    db_dir = Path(db.db_path)
    print(f"[estado] base: {db_dir}")
    if nd and sys.stdin.isatty() and input("[estado] ver muestra (s/n)? ").strip().lower() == "s":
        for d in db.listar_dictamenes_cgr(limit=5):
            print(" -", d["numero"], d["fecha"], "|", (d["organismo_consultante"] or "—"),
                  "| UNID", d["unid"])


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingesta corpus de dictámenes CGR (K-LegalChile)")
    ap.add_argument("--solo", choices=["dictamenes", "citaciones"], default=None)
    ap.add_argument("--index-semantico", action="store_true",
                    help="indexa además embeddings (sentence-transformers)")
    ap.add_argument("--resumen", action="store_true", help="muestra estado local y salir")
    args = ap.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = NormasDB()

    if args.resumen:
        _resumen(db)
        return 0

    if args.solo in (None, "dictamenes"):
        ruta = DATA_DIR / f"{DATASET_DICTAMENES}.csv"
        if not ruta.exists() or input(f"[ingest] ¿descargar {ruta.name} de nuevo? (s/n): ").strip().lower() != "s":
            if not ruta.exists():
                _bajar(DATASET_DICTAMENES, ruta)
        _ingestar_dictamenes(db, ruta)

    if args.solo in (None, "citaciones"):
        ruta = DATA_DIR / f"{DATASET_CITACIONES}.csv"
        if not ruta.exists() or input(f"[ingest] ¿descargar {ruta.name} de nuevo? (s/n): ").strip().lower() != "s":
            if not ruta.exists():
                _bajar(DATASET_CITACIONES, ruta)
        _ingestar_citaciones(db, ruta)

    if args.index_semantico:
        from chilean_legal_mcp.semantico import indexar_dictamenes
        print("[ingest] indexando embeddings semánticos …")
        resultado = indexar_dictamenes(db, limite=0)
        print("[ingest]", resultado)

    _resumen(db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())