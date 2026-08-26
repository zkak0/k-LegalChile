"""Anti-WAF: fallback cascada para sitios con WAF/bot-protection.

Sitios chilenos con WAF/bot-protection conocidos:
- www3.sii.cl (Cloudflare/anti-bot intermitente)
- contraloria.cl (Imperva + Domino con cookie JURIS=OK + Seq dinámico)
- diariooficial.interior.gob.cl (_csrf + cookies)
- buscador.tcchile.cl (SPA con tokens)
- jurisprudencia.cplt.cl (Imperva)

Estrategia cascada (gratis, sin Docker):
1. curl_cffi (Chrome TLS fingerprint JA3/JA4) - rápido, ~60% éxito
2. wafer-py (native OpenSSL TLS + reese84 browser-solve once) - ~35%
3. Camoufox stealth (Firefox real stealth) - ~100%, pesado
4. Fallback: buscar por fuentes alternativas (BCN, etc.)

wafer-py maneja: native OpenSSL TLS (bypass TLS fingerprint) + reese84 browser-solve once → cookie replay cross-TLS
camoufox fetch: Firefox portable portable, canvas/WebGL real, sin webdriver
"""

from __future__ import annotations

import re
import json
import os
import time
import asyncio
import httpx
from pathlib import Path
from urllib.parse import urlparse, quote_plus

# Imports opcionales (se instalan con pip install -e ".[anti-bot]")
try:
    import wafer
    WAFER_AVAILABLE = True
except ImportError:
    WAFER_AVAILABLE = False

try:
    from curl_cffi import requests as curequests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

try:
    from camoufox import AsyncCamoufox
    CAMOUFOX_AVAILABLE = True
except ImportError:
    CAMOUFOX_AVAILABLE = False

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

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


# ──────────────────────────────────────────────────────────────────────────────
# CGRFetcher: Fallback cascada para CGR (Imperva + Domino)
# ──────────────────────────────────────────────────────────────────────────────

class CGRFetcher:
    """Fetcher con fallback cascada para CGR (Imperva + Domino).
    
    Capas:
    1. curl_cffi - Chrome TLS fingerprint (rápido, ~60%)
    2. wafer-py - native OpenSSL TLS + reese84 browser-solve once (~35%)
    3. Camoufox stealth - Firefox real stealth (~100%, pesado)
    4. Fallback: fuentes alternativas (BCN, etc.)
    
    Reutiliza pool de navegadores y cookies wafer.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._browser_pool = None
        self._wafer_session = None
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"[CGRFetcher] {msg}")
    
    def _is_blocked(self, text: str) -> bool:
        """Detecta si la respuesta es un bloqueo WAF/error (no contenido real)."""
        if not text:
            return True
        text_lower = text.lower()
        # Indicadores reales de bloqueo WAF (no falsos positivos como 'juris' en JS)
        blocked_indicators = [
            "request rejected",
            "access denied",
            "please enable javascript",
            "cloudflare",
            "incapsula",
            "imperva",
            "reese84",
            "please wait",
            "checking your browser",
            "pardon our interruption",
            "access to this page has been denied",
        ]
        if len(text) < 500:
            return True
        return any(indicator in text_lower for indicator in blocked_indicators)
    
    async def _try_curl_cffi(self, url: str) -> str | None:
        """Capa 1: curl_cffi - Chrome TLS fingerprint (rápido)."""
        if not CURL_CFFI_AVAILABLE:
            self._log("curl_cffi no disponible")
            return None
        
        self._log("Capa 1: curl_cffi (Chrome TLS fingerprint)")
        try:
            import curl_cffi.requests as curequests
            r = curequests.get(
                url,
                impersonate="chrome120",
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            )
            if r.status_code == 200 and not self._is_blocked(r.text):
                self._log("  ✓ curl_cffi éxito")
                return r.text
            else:
                self._log(f"  ✗ curl_cffi bloqueado (status={r.status_code})")
        except Exception as e:
            self._log(f"  ✗ curl_cffi error: {e}")
        return None
    
    async def _try_wafer(self, url: str) -> str | None:
        """Capa 2: wafer-py - native OpenSSL TLS + reese84 browser-solve once."""
        if not WAFER_AVAILABLE:
            self._log("wafer-py no disponible")
            return None
        
        self._log("Capa 2: wafer-py (native OpenSSL TLS + reese84)")
        try:
            import wafer
            
            # wafer usa SyncSession (sync) o AsyncSession (async)
            # Para async, usar AsyncSession con browser_solver
            async def browser_solver(url: str):
                return await self._browser_solve(url)
            
            # Usar AsyncSession para async
            async with wafer.AsyncSession(
                browser_solver=browser_solver,
                solve_origin="https://www.contraloria.cl"
            ) as session:
                resp = await session.get(url, timeout=30)
            
            if resp and resp.status_code == 200 and not self._is_blocked(resp.text):
                self._log("  ✓ wafer éxito")
                return resp.text
            else:
                self._log(f"  ✗ wafer bloqueado (status={getattr(resp, 'status_code', 'N/A')})")
        except Exception as e:
            self._log(f"  ✗ wafer error: {e}")
        return None
    
    async def _browser_solve(self, url: str) -> dict:
        """Resuelve challenge JS con navegador real (Camoufox/Playwright)."""
        from .browser_pool import get_browser_pool
        pool = await get_browser_pool()
        await pool.initialize()
        
        self._log("  → Browser solve: resolviendo challenge JS...")
        content = await pool.solve_challenge(url)
        self._log("  ✓ Browser solve completado")
        return {"content": content}
    
    async def _try_camoufox(self, url: str) -> str | None:
        """Capa 3: Camoufox stealth (Firefox real stealth)."""
        if not CAMOUFOX_AVAILABLE:
            self._log("Camoufox no disponible")
            return None
        
        self._log("Capa 3: Camoufox stealth (Firefox real)")
        try:
            from .browser_pool import get_browser_pool
            pool = await get_browser_pool()
            await pool.initialize()
            
            self._log("  → Camoufox: navegando...")
            content = await pool.fetch(url, wait_until="domcontentloaded")
            
            if not self._is_blocked(content):
                self._log("  ✓ Camoufox éxito")
                return content
            else:
                self._log("  ✗ Camoufox bloqueado")
        except Exception as e:
            self._log(f"  ✗ Camoufox error: {e}")
        return None
    
    async def _try_camoufox_sync(self, url: str) -> str | None:
        """Versión sync para compatibilidad."""
        return await self._try_camoufox(url)
    
    async def fetch(self, url: str) -> str:
        """Fetch con fallback cascada automático."""
        self._log(f"Iniciando fetch cascada para: {url}")
        
        # Capa 1: curl_cffi
        result = await self._try_curl_cffi(url)
        if result:
            return result
        
        # Capa 2: wafer
        result = await self._try_wafer(url)
        if result:
            return result
        
        # Capa 3: Camoufox
        result = await self._try_camoufox(url)
        if result:
            return result
        
        # Si todo falla, lanzar excepción para que el caller haga fallback
        raise RuntimeError(
            f"Todas las capas fallaron para {url}. "
            "El caller debe usar fuentes alternativas (BCN, etc.)."
        )
    
    async def close(self):
        """Limpia recursos."""
        try:
            from .browser_pool import close_browser_pool
            await close_browser_pool()
        except Exception:
            pass


# Función helper para uso simple
async def fetch_cgr(url: str, verbose: bool = False) -> str:
    """Fetch simple con fallback cascada para CGR."""
    fetcher = CGRFetcher(verbose=verbose)
    try:
        return await fetcher.fetch(url)
    finally:
        await fetcher.close()


# Función sync wrapper para compatibilidad
def fetch_cgr_sync(url: str, verbose: bool = False) -> str:
    """Wrapper sync para uso en código no-async."""
    return asyncio.run(fetch_cgr(url, verbose))