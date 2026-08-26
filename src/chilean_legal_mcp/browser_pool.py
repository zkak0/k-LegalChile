"""Pool de navegadores reutilizable para anti-bot (Camoufox/Playwright)."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Optional

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from camoufox import AsyncCamoufox
    CAMOUFOX_AVAILABLE = True
except ImportError:
    CAMOUFOX_AVAILABLE = False


class BrowserPool:
    """Pool de navegadores reutilizable para anti-bot.
    
    Prioridad: Camoufox (stealth real) > Playwright (fallback).
    Reutiliza instancias para evitar overhead de lanzamiento.
    """
    
    def __init__(
        self,
        max_pages: int = 5,
        timeout: int = 30000,
        headless: bool = True,
    ):
        self.max_pages = max_pages
        self.timeout = timeout
        self.headless = headless
        
        self._camoufox: Optional[AsyncCamoufox] = None
        self._playwright_browser = None
        self._playwright = None
        self._available_pages: asyncio.Queue = asyncio.Queue(maxsize=max_pages)
        self._initialized = False
    
    async def _init_camoufox(self):
        """Inicializa Camoufox (stealth Firefox real)."""
        if not CAMOUFOX_AVAILABLE:
            return False
        try:
            self._camoufox = AsyncCamoufox()
            await self._camoufox.__aenter__()
            # Pre-crear páginas
            for _ in range(self.max_pages):
                page = await self._camoufox.new_page()
                page.set_default_timeout(self.timeout)
                await self._available_pages.put(page)
            return True
        except Exception:
            return False
    
    async def _init_playwright(self):
        """Inicializa Playwright Chromium (fallback)."""
        if not PLAYWRIGHT_AVAILABLE:
            return False
        try:
            self._playwright = await async_playwright().start()
            self._playwright_browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ]
            )
            context = await self._playwright_browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="es-CL",
            )
            for _ in range(self.max_pages):
                page = await context.new_page()
                page.set_default_timeout(self.timeout)
                await self._available_pages.put(page)
            return True
        except Exception:
            return False
    
    async def initialize(self):
        """Inicializa el pool (lazy)."""
        if self._initialized:
            return
        
        # Intentar Camoufox primero (stealth real)
        if await self._init_camoufox():
            self._initialized = True
            return
        
        # Fallback a Playwright
        if await self._init_playwright():
            self._initialized = True
            return
        
        raise RuntimeError("No se pudo inicializar ningún navegador (Camoufox ni Playwright)")
    
    @asynccontextmanager
    async def get_page(self):
        """Obtiene una página del pool (context manager)."""
        if not self._initialized:
            await self.initialize()
        
        page = await self._available_pages.get()
        try:
            yield page
        finally:
            await self._available_pages.put(page)
    
    async def fetch(self, url: str, wait_until: str = "domcontentloaded") -> str:
        """Fetch simple con página del pool."""
        async with self.get_page() as page:
            await page.goto(url, wait_until=wait_until, timeout=self.timeout)
            return await page.content()
    
    async def fetch_with_retry(
        self,
        url: str,
        max_retries: int = 2,
        wait_until: str = "domcontentloaded",
    ) -> str:
        """Fetch con reintentos simples."""
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                return await self.fetch(url, wait_until)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(1 * (attempt + 1))
        raise last_error
    
    async def solve_challenge(self, url: str) -> str:
        """Resuelve challenge JS (Cloudflare/Imperva) y devuelve cookies."""
        async with self.get_page() as page:
            await page.goto(url, wait_until="networkidle", timeout=self.timeout)
            # Esperar a que se resuelva challenge (si hay)
            await page.wait_for_load_state("networkidle", timeout=30000)
            return await page.content()
    
    async def close(self):
        """Cierra el pool y libera recursos."""
        if self._camoufox:
            try:
                await self._camoufox.__aexit__(None, None, None)
            except Exception:
                pass
            self._camoufox = None
        
        if self._playwright_browser:
            try:
                await self._playwright_browser.close()
            except Exception:
                pass
            self._playwright_browser = None
        
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        
        # Vaciar queue
        while not self._available_pages.empty():
            try:
                self._available_pages.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        self._initialized = False


# Instancia global singleton
_global_pool: Optional[BrowserPool] = None


async def get_browser_pool() -> BrowserPool:
    """Obtiene el pool global (singleton lazy)."""
    global _global_pool
    if _global_pool is None:
        _global_pool = BrowserPool()
    return _global_pool


async def close_browser_pool():
    """Cierra el pool global."""
    global _global_pool
    if _global_pool:
        await _global_pool.close()
        _global_pool = None