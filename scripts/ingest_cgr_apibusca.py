#!/usr/bin/env python3
"""Ingesta masiva de dictámenes CGR vía API pública apibusca.contraloria.cl

Estrategia (verificada empíricamente):
- La API NO pagina: `from` es ignorado y `size` queda capado a 20 hits por petición.
- El filtro de fecha (options con date_name) SÍ funciona y `hits.total` es exacto.
- Por lo tanto se recorre el corpus por ventanas de fecha TAN angostas que el
  total de cada ventana quepa en una sola petición (<= 20 docs).
  Si una ventana supera 20 docs, se subdivide recursivamente (por tiempo, hasta 1 hora)
  hasta que quepa; así se captura todo sin paginación y sin martillar el servidor.
- Checkpoint en data/ingest_cgr_checkpoint.json: permite reanudar tras interrupción.

Upsert por UNID (extraído de old_url/source_url), idempotente.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from chilean_legal_mcp.db import NormasDB

API_BASE = "https://www.contraloria.cl/apibusca"
SOURCE = "dictamenes"
DATE_NAME = "fecha_documento"
MAX_HITS = 20
MIN_WINDOW = timedelta(hours=1)

_RE_UNID = re.compile(r"([0-9A-Fa-f]{32})")

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

_HEADERS = {
    "User-Agent": "k-legalchile/1.0",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

CHECKPOINT_FILE = Path(__file__).resolve().parent.parent / "data" / "ingest_cgr_checkpoint.json"


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _bajar_json(url: str, payload: dict, max_retries: int = 4) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=_HEADERS, method="POST")
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


def _parse_unid(source_url: str | None) -> str | None:
    if not source_url:
        return None
    m = _RE_UNID.search(source_url)
    return m.group(1).upper() if m else None


def _upsert_one(db: NormasDB, hit: dict) -> bool:
    src = hit.get("_source", {})
    doc_id = src.get("doc_id") or src.get("_id") or ""
    numero = src.get("n_dictamen") or src.get("numero") or ""
    fecha = src.get("fecha_documento") or src.get("fecha") or ""
    org = src.get("origen_") or src.get("organismo_consultante") or ""
    sumario = src.get("materia") or src.get("materia_raw") or ""
    old_url = src.get("old_url") or src.get("source_url") or ""
    unid = _parse_unid(old_url)
    anio = None
    if fecha and len(fecha) >= 4:
        try:
            anio = int(fecha[:4])
        except ValueError:
            pass
    return db.upsert_dictamen_cgr(doc_id, numero, anio, fecha, org, sumario if sumario else None,
                                  old_url, unid, None, json.dumps({k: v for k, v in src.items() if k in (
                                      "carácter", "documento_completo", "acción", "materia_raw",
                                      "destinatarios", "fuentes_legales", "old_url", "fecha_documento",
                                      "descriptores", "origen_", "abogados", "materia", "recurso_proteccion",
                                      "boletin", "criterio", "origenes", "tema", "n_dictamen", "doc_id")}, ensure_ascii=False))


def _build_payload(date_from: datetime, date_to: datetime) -> dict:
    options = [{
        "type": "date",
        "field": DATE_NAME,
        "value": {"gt": _iso(date_from), "lt": _iso(date_to)},
        "inner_id": f"date_{date_from:%Y%m%d%H%M}_{date_to:%Y%m%d%H%M}",
        "dir": "desc",
    }]
    return {
        "search": "",
        "exact_search": False,
        "options": options,
        "order": "date",
        "date_name": DATE_NAME,
        "source": SOURCE,
        "from": 0,
        "size": MAX_HITS,
    }


def _consultar_ventana(date_from: datetime, date_to: datetime) -> dict:
    url = f"{API_BASE}/search/{SOURCE}"
    payload = _build_payload(date_from, date_to)
    return _bajar_json(url, payload)


def _guardar_checkpoint(cursor: datetime | None) -> None:
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {"cursor": cursor.strftime("%Y-%m-%dT%H:%M:%S") if cursor else None}
    CHECKPOINT_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _leer_checkpoint() -> datetime | None:
    if not CHECKPOINT_FILE.exists():
        return None
    try:
        data = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        cur = data.get("cursor")
        return datetime.strptime(cur, "%Y-%m-%dT%H:%M:%S") if cur else None
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


def _ingestar_ventana(db: NormasDB, date_from: datetime, date_to: datetime,
                      delay: float, profundidad: int = 0) -> tuple[int, int]:
    """Devuelve (docs_ingestados_en_ventana, peticiones_usadas)."""
    r = _consultar_ventana(date_from, date_to)
    total = r.get("hits", {}).get("total", {}).get("value", 0) or 0
    hits = r.get("hits", {}).get("hits", [])
    peticiones = 1

    if total == 0:
        print(f"    [ventana] {date_from:%Y-%m-%d %H%M}..{date_to:%Y-%m-%d %H%M}: 0 docs (skip{'.'*profundidad})")
        time.sleep(delay)
        return 0, peticiones

    if total <= MAX_HITS:
        nuevos = 0
        for h in hits:
            if _upsert_one(db, h):
                nuevos += 1
        print(f"    [ventana] {date_from:%Y-%m-%d %H%M}..{date_to:%Y-%m-%d %H%M}: "
              f"total={total} filas={len(hits)} nuevos={nuevos}")
        time.sleep(delay)
        return nuevos, peticiones

    n = (date_to - date_from) // 2
    if n < MIN_WINDOW:
        n = MIN_WINDOW
    mid = date_from + n
    if mid <= date_from or mid >= date_to:
        mid = date_from + (date_to - date_from) / 2
    mitad_1 = (date_from, mid)
    mitad_2 = (mid, date_to)
    ped = peticiones
    n2 = 0
    for start, end in (mitad_1, mitad_2):
        sub, puse = _ingestar_ventana(db, start, end, delay, profundidad + 1)
        n2 += sub
        ped += puse
    return n2, ped


def _procesar_rango(db: NormasDB, desde: date, hasta: date, step_dias: int,
                    delay: float, resumir: bool) -> tuple[int, int]:
    cursor = _leer_checkpoint() if resumir else None
    if cursor is None:
        start_cursor = datetime(desde.year, desde.month, desde.day)
    else:
        start_cursor = cursor
    print(f"[ingest] Desde {start_cursor:%Y-%m-%d} hasta {hasta.isoformat()} (resume={'sí' if resumir else 'no'})")

    cur = start_cursor
    fin = datetime(hasta.year, 12, 31, 23, 59, 59)
    total_nuevos = 0
    total_peticiones = 0

    while cur < fin:
        nxt = cur + timedelta(days=step_dias)
        if nxt > fin:
            nxt = fin + timedelta(seconds=1)
        print(f"[ingest] === Ventana {cur:%Y-%m-%d} .. {nxt:%Y-%m-%d} ===")
        nuevos, peticiones = _ingestar_ventana(db, cur, nxt, delay, 0)
        total_nuevos += nuevos
        total_peticiones += peticiones
        _guardar_checkpoint(nxt)
        cur = nxt

    print(f"[ingest] FIN: {total_nuevos:,} nuevos, {total_peticiones:,} peticiones")
    return total_nuevos, total_peticiones


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Ingesta masiva CGR apibusca (gratis, sin clave) — ventanas de fecha adaptativas sin paginación")
    ap.add_argument("--desde", type=int, default=2020, help="Año inicial (default 2020)")
    ap.add_argument("--hasta", type=int, default=2026, help="Año final (default 2026)")
    ap.add_argument("--step-dias", type=int, default=7, help="Ancho inicial de ventana en días (default 7)")
    ap.add_argument("--delay", type=float, default=0.3, help="Delay entre peticiones (seg)")
    ap.add_argument("--no-resumir", action="store_true", help="Ignorar checkpoint y partir de cero")
    ap.add_argument("--resumen", action="store_true", help="Solo muestra estado local")
    ap.add_argument("--reset-checkpoint", action="store_true", help="Borra el checkpoint")
    args = ap.parse_args()

    DATA_DIR = Path(__file__).resolve().parent.parent / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = NormasDB()

    if args.reset_checkpoint:
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()
            print("[checkpoint] eliminado")
        else:
            print("[checkpoint] no existía")
        return 0

    if args.resumen:
        nd = db.count_dictamenes_cgr()
        nc = db.count_citas_legales()
        nk = db.count_criterios()
        print(f"[estado] dictamenes CGR: {nd:,}")
        print(f"[estado] aristas de citación: {nc:,}")
        print(f"[estado] criterios_estado: {nk:,}")
        return 0

    print(f"[ingest] Rango {args.desde}-{args.hasta}, step_dias={args.step_dias}, delay={args.delay}")

    total_nuevos, total_peticiones = _procesar_rango(
        db, date(args.desde, 1, 1), date(args.hasta, 12, 31), args.step_dias, args.delay,
        resumir=not args.no_resumir)

    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        print("[checkpoint] completado, archivo eliminado")

    nd = db.count_dictamenes_cgr()
    print(f"[estado] dictamenes CGR: {nd:,}")
    print(f"[resumen] nuevos={total_nuevos:,} peticiones={total_peticiones:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())