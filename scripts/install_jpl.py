#!/usr/bin/env python3
"""Instala JPL — descarga corpus.db.zlib del repo privado K-LegalJPL a data/jpl/.

Uso:
  python scripts/install_jpl.py                 # pide token por stdin (seguro)
  python scripts/install_jpl.py --token ghp_... # token por arg (cuidado historial)
  GITHUB_TOKEN=ghp_... python scripts/install_jpl.py  # via env var

El token nunca se guarda en disco ni se commitea. Solo vive en memoria durante la descarga.
Soporta 3 fuentes (primera que funcione):
  1. GitHub API: descarga corpus.db.zlib (15 MB) via contents API
  2. Git clone shallow del repo privado a /tmp
  3. Sibling clone ya existente en ../K-LegalJPL/corpus.db.zlib (copia local sin token)

Destino siempre: data/jpl/corpus.db.zlib -> se descomprime a data/jpl/corpus.db al primer uso del MCP.
"""
from __future__ import annotations

import argparse
import base64
import getpass
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JPL_DIR = PROJECT_ROOT / "data" / "jpl"
JPL_ZST = JPL_DIR / "corpus.db.zlib"
JPL_DB = JPL_DIR / "corpus.db"

PRIVATE_REPO = "zkak0/K-LegalJPL"
API_URL = f"https://api.github.com/repos/{PRIVATE_REPO}/contents/corpus.db.zlib"
RAW_URL = f"https://raw.githubusercontent.com/{PRIVATE_REPO}/main/corpus.db.zlib"

def _get_token(args_token: str | None) -> str | None:
    if args_token:
        return args_token.strip()
    env = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if env:
        return env.strip()
    # sibling token file? no
    return None

def _try_api_download(token: str) -> bool:
    """Intenta descargar via GitHub API contents (base64)."""
    try:
        import json, urllib.request, urllib.error
        req = urllib.request.Request(API_URL, headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "k-LegalChile-installer",
        })
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        # contents API returns base64 chunks; for large files (>1MB) it returns download_url instead
        if isinstance(data, dict) and data.get("download_url"):
            dl_url = data["download_url"]
            print(f"  → descargando desde {dl_url[:60]}...")
            req2 = urllib.request.Request(dl_url, headers={"Authorization": f"token {token}", "User-Agent": "k-LegalChile-installer"})
            with urllib.request.urlopen(req2, timeout=120) as r2:
                raw = r2.read()
            JPL_DIR.mkdir(parents=True, exist_ok=True)
            # Si viene base64, decode; si es binario, ya está
            # download_url devuelve raw binary, no base64
            JPL_ZST.write_bytes(raw)
            print(f"  ✅ descargado {len(raw)/1024/1024:.1f} MB → {JPL_ZST}")
            return True
        if isinstance(data, dict) and data.get("content"):
            b64 = data["content"].replace("\n","")
            raw = base64.b64decode(b64)
            JPL_DIR.mkdir(parents=True, exist_ok=True)
            JPL_ZST.write_bytes(raw)
            print(f"  ✅ descargado {len(raw)/1024/1024:.1f} MB → {JPL_ZST}")
            return True
    except Exception as e:
        print(f"  API download falló: {e}")
    return False

def _try_raw_download(token: str) -> bool:
    try:
        import urllib.request
        req = urllib.request.Request(RAW_URL, headers={
            "Authorization": f"token {token}",
            "User-Agent": "k-LegalChile-installer",
        })
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
        if len(raw) < 1000:
            return False
        JPL_DIR.mkdir(parents=True, exist_ok=True)
        JPL_ZST.write_bytes(raw)
        print(f"  ✅ raw download {len(raw)/1024/1024:.1f} MB → {JPL_ZST}")
        return True
    except Exception as e:
        print(f"  raw download falló: {e}")
        return False

def _try_git_clone(token: str) -> bool:
    try:
        tmp = Path(tempfile.mkdtemp(prefix="K-LegalJPL-"))
        url = f"https://{token}@github.com/{PRIVATE_REPO}.git"
        print(f"  → git clone --depth 1 a {tmp}...")
        subprocess.run(["git", "clone", "--depth", "1", url, str(tmp / "repo")], check=True, capture_output=True, timeout=120)
        src_zst = tmp / "repo" / "corpus.db.zlib"
        src_db = tmp / "repo" / "corpus.db"
        JPL_DIR.mkdir(parents=True, exist_ok=True)
        if src_zst.exists():
            shutil.copy2(str(src_zst), str(JPL_ZST))
            print(f"  ✅ clonado {src_zst.stat().st_size/1024/1024:.1f} MB → {JPL_ZST}")
            shutil.rmtree(str(tmp), ignore_errors=True)
            return True
        if src_db.exists():
            # Si ya existe descomprimido, comprimir?
            import zlib
            raw = src_db.read_bytes()
            JPL_ZST.write_bytes(zlib.compress(raw, 9))
            print(f"  ✅ clonado y comprimido → {JPL_ZST}")
            shutil.rmtree(str(tmp), ignore_errors=True)
            return True
        shutil.rmtree(str(tmp), ignore_errors=True)
    except Exception as e:
        print(f"  git clone falló: {e}")
    return False

def _try_sibling() -> bool:
    candidates = [
        PROJECT_ROOT.parent / "K-LegalJPL" / "corpus.db.zlib",
        PROJECT_ROOT.parent / "k-LegalJPL" / "corpus.db.zlib",
        Path("/tmp/jpl_fetch/k-LegalJPL/corpus.db.zlib"),
    ]
    for p in candidates:
        if p.exists():
            JPL_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(p), str(JPL_ZST))
            print(f"  ✅ copiado desde sibling {p} → {JPL_ZST}")
            return True
    # also try corpus.db
    for p in [PROJECT_ROOT.parent / "K-LegalJPL" / "corpus.db", Path("/tmp/jpl_fetch/k-LegalJPL/corpus.db")]:
        if p.exists():
            JPL_DIR.mkdir(parents=True, exist_ok=True)
            import zlib
            raw = p.read_bytes()
            JPL_ZST.write_bytes(zlib.compress(raw, 9))
            print(f"  ✅ copiado y comprimido desde {p} → {JPL_ZST}")
            return True
    return False

def main():
    parser = argparse.ArgumentParser(description="Instala corpus JPL privado")
    parser.add_argument("--token", help="GitHub PAT con acceso a K-LegalJPL (si no, pide por stdin)")
    args = parser.parse_args()

    print("=== Instalador JPL para k-LegalChile ===\n")
    if JPL_ZST.exists():
        print(f"Ya existe {JPL_ZST} ({JPL_ZST.stat().st_size/1024/1024:.1f} MB)")
        resp = input("¿Sobrescribir? [y/N]: ").strip().lower()
        if resp not in ("y","s","yes"):
            print("Abortado.")
            return 0
    if JPL_DB.exists():
        # No borrar DB existente, solo ZST
        pass

    # 1) Try sibling copy (no token needed)
    print("\n[1/3] Buscando sibling clone local...")
    if _try_sibling():
        print("\n✅ JPL instalado desde copia local.")
        return _verify()

    token = _get_token(args.token)
    if not token:
        print("\nNo se encontró GITHUB_TOKEN. Se pedirá por entrada segura.")
        try:
            token = getpass.getpass("GitHub PAT (ghp_...): ").strip()
        except Exception:
            token = input("GitHub PAT: ").strip()
    if not token:
        print("❌ Token vacío. Abortado.")
        print("Tip: export GITHUB_TOKEN=ghp_... y reintenta, o clona manualmente K-LegalJPL como hermano: git clone https://... ../K-LegalJPL")
        return 1

    print(f"\n[2/3] Probando descarga API (token ...{token[-4:]})...")
    if _try_api_download(token):
        return _verify()
    print("\n[3/3] Probando git clone...")
    if _try_git_clone(token):
        return _verify()

    print("\n❌ No se pudo instalar JPL. Verifica:")
    print("  - Token tiene acceso al repo privado zkak0/K-LegalJPL")
    print("  - O clona manualmente: git clone https://<token>@github.com/zkak0/K-LegalJPL.git ../K-LegalJPL")
    print("  - Luego re-ejecuta este script.")
    return 1

def _verify() -> int:
    print(f"\nVerificando {JPL_ZST}...")
    if not JPL_ZST.exists():
        print("❌ JPL_ZST no existe tras instalación")
        return 1
    print(f"  Tamaño: {JPL_ZST.stat().st_size/1024/1024:.1f} MB")
    # Try to ensure DB builds
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from chilean_legal_mcp.jpl.db import _ensure_db, listar_leyes, buscar_ley
        print("  Descomprimiendo y construyendo FTS (1-2 min primera vez)...")
        ok = _ensure_db()
        print(f"  _ensure_db: {ok}")
        leyes = listar_leyes()
        print(f"  Leyes: {len(leyes)}")
        res = buscar_ley("transito", limite=2)
        print(f"  buscar_ley('transito'): {len(res)} resultados")
        if res:
            print(f"    → {res[0].get('ley')} : {res[0].get('titulo','')[:60]}")
        print("\n✅ JPL instalado y verificado. Reinicia tu cliente MCP.")
        return 0
    except Exception as e:
        print(f"  Verificación parcial falló: {e}")
        print("  Pero corpus.db.zlib está instalado; FTS se construirá al primer uso del MCP.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
