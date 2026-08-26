"""Anti-WAF: fallback con Playwright cuando httpx es bloqueado.

Sitios chilenos con WAF/bot-protection conocidos:
- www3.sii.cl (Cloudflare/anti-bot intermitente)
- contraloria.cl (Domino con cookie JURIS=OK + Seq dinámico)
- diariooficial.interior.gob.cl (_csrf + cookies)
- buscador.tcchile.cl (SPA con tokens)
- jurisprudencia.cplt.cl (Imperva)

Estrategia:
1. Intento con httpx directo (rápido, sin overhead)
2. Si detecta bloqueo (status 403/503, respuesta corta con JS challenge, cookies vacías), hace fallback a Playwright
3. Playwright resuelve el challenge JS, guarda cookies en disco para reusarlas en consultas siguientes
"""

from __future__ import annotations

import re
import json
import os
import time
import httpx
from pathlib import Path

# Cache de cookies por dominio
_COOKIE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "cookies"
_COOKIE_DIR.mkdir(parents=True, exist_ok=True)

# Dominios que requieren anti-WAF
_WAF_DOMAINS = {
    "www3.sii.cl": {"selector": "body", "challenge_text": ["Request Rejected", "cloudflare", "access denied"]},
    "contraloria.cl": {"selector": "body", "challenge_text": ["Request Rejected", "JURIS"]},
    "diariooficial.interior.gob.cl": {"selector": "body", "challenge_text": ["Request Rejected", "_csrf"]},
    "buscador.tcchile.cl": {"selector": "body", "challenge_text": ["Request Rejected", "cloudflare"]},
    "jurisprudencia.cplt.cl": {"selector": "body", "challenge_text": ["Request Rejected", "Imperva"]},
}

# Indicadores de bloqueo WAF
_BLOCK_PATTERNS = [
    r"Request Rejected",
    r"cloudflare",
    r"access denied",
    r"accesscontrol",
    r"Please enable JavaScript",
    r"bpb_cookie",
    r"TSPD",
    r"bobcmn",
    r"_cf_chl",
    r"md5.js",
    r"challenge-platform",
]


def _detectar_bloqueo(resp: httpx.Response) -> bool:
    """Detecta si la respuesta es un WAF challenge en vez de contenido real."""
    if resp.status_code in (403, 503):
        return True
    # Respuestas muy cortas con texto de bloqueo conocidos
    texto = resp.text or ""
    if len(texto) < 600 and any(re.search(p, texto, re.I) for p in _BLOCK_PATTERNS):
        return True
    # Si devuelve texto pero ningún link href de dominio chileno conocido
    if len(texto) < 2000:
        chile_domains = [".gob.cl", ".cl", "bcn.cl", "pjud.cl", "tribunalconstitucional.cl",
                         "tesoreria.cl", "tta.cl", "suseso.cl", "sii.cl", "inapi.cl",
                         "diariooficial.interior.gob.cl", "contraloria.cl", "snifa.sma.gob.cl",
                         "boletinconcursal.cl", "superir.gob.cl", "portalchile.org"]
        has_valid_link = any(d in texto for d in chile_domains)
        if not has_valid_link:
            return True
    return False


def _cookie_path(dominio: str) -> Path:
    """Ruta del archivo de cookies para un dominio."""
    safe = re.sub(r"[^a-z0-9]", "_", dominio.lower())
    return _COOKIE_DIR / f"{safe}_cookies.json"


def _cargar_cookies(dominio: str) -> dict:
    """Carga cookies guardadas para un dominio."""
    path = _cookie_path(dominio)
    if path.exists():
        try:
            data = json.loads(path.read_text())
            if time.time() - data.get("ts", 0) < 3600:  # 1 hora de validez
                return data.get("cookies", {})
        except Exception:
            pass
    return {}


def _guardar_cookies(dominio: str, cookies: dict) -> None:
    """Guarda cookies para un dominio."""
    path = _cookie_path(dominio)
    try:
        path.write_text(json.dumps({"ts": time.time(), "cookies": cookies}, ensure_ascii=False))
    except Exception:
        pass


def _extraer_cookies_playwright(url: str, dominio: str, *, esperar: int = 3) -> dict:
    """Usa Playwright para resolver challenge JS y obtener cookies."""
    cookies = {}
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
                locale="es-CL",
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(esperar * 1000)
            cookies = {c["name"]: c["value"] for c in context.cookies() if c.get("domain") in (dominio, f".{dominio}")}
            browser.close()
    except Exception:
        pass
    return cookies


def httpx_con_fallback(
    metodo: str,
    url: str,
    *,
    dominio: str | None = None,
    headers: dict | None = None,
    params: dict | None = None,
    data: dict | None = None,
    timeout: float = 20.0,
    solo_cookies: bool = False,
) -> httpx.Response | dict:
    """Hace request con httpx; si detecta WAF, hace fallback con Playwright cookies.

    Si solo_cookies=True, devuelve dict de cookies en vez de Response.
    """
    headers = headers or {}
    dominio = dominio or _extraer_dominio(url)

    # 1. Intentar con cookies guardadas primero (si hay)
    cookies_guardadas = _cargar_cookies(dominio)
    if cookies_guardadas:
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies_guardadas.items())

    metodo_fn = getattr(httpx, metodo.lower())
    kwargs = {"headers": headers, "timeout": timeout, "follow_redirects": True}
    if params:
        kwargs["params"] = params
    if data:
        kwargs["data"] = data

    try:
        resp = metodo_fn(url, **kwargs)
    except Exception:
        resp = None

    # 2. Detectar si hay bloqueo
    if resp and _detectar_bloqueo(resp):
        pass
    elif resp and not _detectar_bloqueo(resp):
        # Guardar cookies si la respuesta fue exitosa
        if resp.status_code == 200:
            resp_cookies = {c.name: c.value for c in resp.cookies}
            if resp_cookies:
                _guardar_cookies(dominio, resp_cookies)
        if solo_cookies:
            return resp_cookies
        return resp

    # 3. Fallback: Playwright
    cookies_pw = _extraer_cookies_playwright(url, dominio)
    if cookies_pw:
        _guardar_cookies(dominio, cookies_pw)
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies_pw.items())
        try:
            resp2 = metodo_fn(url, **kwargs)
            if resp2 and resp2.status_code == 200 and not _detectar_bloqueo(resp2):
                if solo_cookies:
                    return cookies_pw
                return resp2
        except Exception:
            pass

    # 4. Último recurso: devolver la respuesta original (puede ser un link de error)
    if solo_cookies:
        return cookies_guardadas
    return resp


def _extraer_dominio(url: str) -> str:
    from urllib.parse import urlparse
    return urlparse(url).netloc


def verificar_sitio(url: str, timeout: float = 15.0) -> dict:
    """Verifica si un sitio oficial está accesible. Devuelve diagnóstico."""
    from urllib.parse import urlparse
    dominio = _extraer_dominio(url)
    inicio = time.time()

    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0"})
        bloqueado = _detectar_bloqueo(resp)
        return {
            "url": url,
            "dominio": dominio,
            "status_code": resp.status_code,
            "accessible": resp.status_code == 200 and not bloqueado,
            "bloqueado_waf": bloqueado,
            "latencia_ms": round((time.time() - inicio) * 1000),
            "tamano": len(resp.text),
        }
    except Exception as e:
        return {
            "url": url,
            "dominio": dominio,
            "status_code": None,
            "accessible": False,
            "bloqueado_waf": False,
            "latencia_ms": round((time.time() - inicio) * 1000),
            "error": str(e),
        }