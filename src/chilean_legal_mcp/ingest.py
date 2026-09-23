"""Ingesta de normas desde el SPARQL de la BCN hacia la base local SQLite."""

from __future__ import annotations

import time

from .db import NormasDB
from .sparql_client import BCNClient

SEED_QUERIES = [
    "acoso laboral",
    "despido injustificado",
    "contrato de trabajo",
    "pensión alimenticia",
    "divorcio",
    "violencia intrafamiliar",
    "arriendo",
    "copropiedad inmobiliaria",
    "sociedades anónimas",
    "protección de datos personales",
    "consumidor",
    "delitos económicos",
    "corrupción",
    "salud",
    "educación",
    "seguridad social",
    "trabajo a distancia",
    "sindicato",
    "negociación colectiva",
    "ley karin",
]


def ingest(db_path: str | None = None, queries: list[str] | None = None,
           bulk: bool = False, desde_anio: int | None = None) -> dict:
    client = BCNClient()
    db = NormasDB(db_path)
    inserted = 0
    total_rows = 0
    used_queries = queries or SEED_QUERIES

    if bulk:
        return _bulk_ingest(client, db, desde_anio=None if desde_anio is None else int(desde_anio))

    for q in used_queries:
        try:
            rows = client.search_by_title(q, limit=50)
        except Exception as exc:  # noqa: BLE001
            print(f"  [!] error en '{q}': {exc}")
            continue
        for row in rows:
            uri = row.get("uri") or row.get("s")
            if not (uri and "titulo" in row):
                continue
            if db.upsert_norma(
                uri=uri,
                titulo=row["titulo"],
                numero=row.get("numero"),
                fecha=row.get("fecha"),
                leychile_id=row.get("leychileId"),
            ):
                inserted += 1
        total_rows += len(rows)
        print(f"  [{q}] filas={len(rows)} nuevas={inserted} acumuladas")
        time.sleep(0.5)

    result = {"consultas": len(used_queries), "filas": total_rows,
              "insertadas": inserted, "total_db": db.count()}
    db.close()
    client.close()
    return result


def _bulk_ingest(client: BCNClient, db: NormasDB, desde_anio: int | None = None) -> dict:
    """Bulk optimizado: pagina por año de publicación (1810–hoy) en vez de OFFSET.

    `ORDER BY fecha OFFSET N` fuerza a SPARQL a ordenar 360k filas cada llamada.
    En cambio filtrar por año es rápido porque cada lote es pequeño (miles).
    Si el año en curso aún no llegó al total se usa un fallback con OFFSET 0.
    """
    from datetime import datetime
    anio_actual = datetime.now().year
    anio_inicio = desde_anio or 1810
    batch = 1000
    total_inserted = 0

    print(f"Bulk por año: {anio_inicio} → {anio_actual}")
    for anio in range(anio_inicio, anio_actual + 1):
        offset_anio = 0
        while True:
            sparql = f"""PREFIX bcn: <http://datos.bcn.cl/ontologies/bcn-norms#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
SELECT ?uri ?titulo ?numero ?fecha ?leychileId WHERE {{
  ?s a bcn:RootNorm ; dc:title ?titulo ; bcn:publishDate ?fecha .
  FILTER(YEAR(?fecha) = {anio})
  BIND(?s AS ?uri)
  OPTIONAL {{ ?s bcn:hasNumber ?numero }}
  OPTIONAL {{ ?s bcn:leychileCode ?leychileId }}
}} LIMIT {batch} OFFSET {offset_anio}"""
            try:
                rows = client.query(sparql)
            except Exception as exc:  # noqa: BLE001
                print(f"  [!] bulk error año {anio} offset {offset_anio}: {exc}")
                break
            if not rows:
                break
            for row in rows:
                uri = row.get("uri")
                if not (uri and "titulo" in row):
                    continue
                if db.upsert_norma(uri, row["titulo"], row.get("numero"),
                                     row.get("fecha"), row.get("leychileId")):
                    total_inserted += 1
            offset_anio += batch
            print(f"  año {anio} offset {offset_anio} nuevas={total_inserted} total_db={db.count()}")
            time.sleep(0.2)  # rate limit respetuoso
            if len(rows) < batch:
                break
        db._conn.commit()  # persistir por año

    return {"anios_cubiertos": anio_actual - 1990 + 1,
            "insertadas": total_inserted,
            "total_db": db.count()}


if __name__ == "__main__":
    import sys
    bulk = "--bulk" in sys.argv
    desde_anio = None
    for i, a in enumerate(sys.argv):
        if a == "--desde" and i + 1 < len(sys.argv):
            desde_anio = int(sys.argv[i + 1])
    print(f"Ingesta {'masiva' if bulk else 'inicial'} de normas chilenas...")
    stats = ingest(bulk=bulk, desde_anio=desde_anio)
    print(stats)
