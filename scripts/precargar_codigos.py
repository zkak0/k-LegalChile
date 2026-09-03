#!/usr/bin/env python3
"""Precarga en caché local (tabla `textos`) los cuerpos legales de uso frecuente.

Resuelve cada cuerpo contra la BD local de normas (sin adivinar ids), descarga
el texto oficial XML de LeyChile, verifica que el contenido corresponde antes de
cachearlo y deja lo demás intacto. Idempotente.

Uso:
    python scripts/precargar_codigos.py            # precarga los 6 códigos base
    python scripts/precargar_codigos.py --lista    # solo muestra qué descargaría
    python scripts/precargar_codigos.py --forzar   # vuelve a descargar aunque exista
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from chilean_legal_mcp.db import NormasDB
from chilean_legal_mcp.texto import fetch_texto

# (nombre legible, idNorma LeyChile canónico VERIFICADO, marcador obligatorio)
# Los ids fueron contrastados contra BCN/SPARQL (ver historial de repo):
#   CPC: Ley N° 1552 → idNorma 22740;  COT: Ley N° 7.421 → idNorma 25563.
# El texto se cachea ÍNTEGRO (fetch_texto con tope amplio) para que
# obtener_articulo_texto corte cualquier artículo, no solo los primeros.
MAX_CHARS_CUERPO = 2_000_000

OBJETIVOS = [
    ("Constitución Política de la República", "137535", "CONSTITUCION POLITICA"),
    ("Código Civil",                          "172986", "CODIGO CIVIL"),
    ("Código de Procedimiento Civil",         "22740",  "PROCEDIMIENTO CIVIL"),
    ("Código Orgánico de Tribunales",         "25563",  "ORGANICO DE TRIBUNALES"),
    ("Código del Trabajo",                    "207436", "CODIGO DEL TRABAJO"),
    ("Código Procesal Penal",                 "176595", "CODIGO PROCESAL PENAL"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lista", action="store_true",
                    help="solo muestra qué se descargaría (sin red)")
    ap.add_argument("--forzar", action="store_true",
                    help="vuelve a descargar aunque ya esté en caché")
    args = ap.parse_args()

    db = NormasDB()
    total_ok = total_fallo = 0

    for nombre, lid, marcador in OBJETIVOS:
        # saneamiento: el id pinnado debe existir en la BD local (verificación interna)
        fila = db._conn.execute(
            "SELECT titulo, numero FROM normas WHERE leychile_id = ?", (lid,)).fetchone()
        referencia = fila["titulo"][:80] if fila else "(sin fila local — se usa el id canónico verificado)"
        existente = db.get_texto(lid)
        if args.lista:
            marca = f"en caché ({len(existente):,} chars)" if existente else "a descargar"
            print(f"• {nombre}: idNorma={lid} ({marca})")
            print(f"    fuente local: {referencia}")
            continue
        if existente and len(existente) > 50_000 and not args.forzar:
            print(f"✔ {nombre}: ya en caché completa (idNorma={lid}, {len(existente):,} chars)")
            total_ok += 1
            continue
        try:
            texto = fetch_texto(lid, max_chars=MAX_CHARS_CUERPO)
        except Exception as exc:  # noqa: BLE001
            print(f"✘ {nombre}: error de red al descargar idNorma={lid}: {exc}")
            total_fallo += 1
            continue
        if not texto:
            print(f"✘ {nombre}: LeyChile no devolvió texto para idNorma={lid}")
            total_fallo += 1
            continue
        if marcador not in texto.upper():
            print(f"✘ {nombre}: el texto descargado NO contiene '{marcador}' — "
                  f"abortado por seguridad (posible id errado, idNorma={lid})")
            total_fallo += 1
            continue
        if "texto truncado" in texto:
            print(f"✘ {nombre}: el texto descargado quedó truncado ({len(texto):,} chars); "
                  f"no se cachea un cuerpo incompleto (idNorma={lid})")
            total_fallo += 1
            continue
        db.save_texto(lid, texto)
        print(f"✔ {nombre}: cacheado íntegro (idNorma={lid}, {len(texto):,} chars)")
        total_ok += 1

    if not args.lista:
        print(f"\nResultado: {total_ok} ok, {total_fallo} con problemas.")
        print("Verificación rápida: obtener_texto_norma / obtener_articulo_texto.")
    return 0 if total_fallo == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
