"""Jurisprudencia real del Poder Judicial de Chile (juris.pjud.cl).

El portal público es una app Angular protegida por F5 BIG-IP ASM (TSPD):
rechaza clientes HTTP puros por huella TLS y exige un token CSRF por sesión.
La solución honesta es hablarle *como un navegador real*: un Chromium vía
Playwright (con parches stealth) que resuelve el challenge de F5 una vez y
ejecuta la llamada POST al API interno ``/busqueda/buscar_sentencias`` dentro
del propio contexto JavaScript del navegador.

Uso legal: buscador público del Poder Judicial, con sesión y cookies del
portal mismo, sin evadir CAPTCHAs ni pagos. Si el portal devuelve error se
informa honestamente mediante ``PJUDNoDisponible``.
"""

from __future__ import annotations

import threading
from typing import Any

HOME = "https://juris.pjud.cl/busqueda/lista_buscadores"
API = "/busqueda/buscar_sentencias"

# id_buscador PJUD confirmados en recon (09-2026), uno por categoría del portal.
ID_BUSCADORES = {
    "corte_suprema": 528,
    "corte_de_apelaciones": 168,
    "laborales": 271,
    "penales": 268,
    "familia": 270,
    "cobranza": 269,
    "civiles": 328,
    "compendio_extranjeria": 648,
    "lineas_jurisprudenciales": 628,
    "salud_cs": 127,
}
DEFAULT_BUSCADOR = ID_BUSCADORES["corte_suprema"]

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


class PJUDNoDisponible(Exception):
    """El portal PJUD no respondió como se esperaba (NO es 'no hay fallos')."""


class _SesionPJUD:
    """Singleton: un Chromium compartido, se (re)abre bajo demanda."""

    _lock = threading.Lock()
    _pw = None
    _browser = None
    _page = None

    @classmethod
    def _boot(cls):
        from playwright.sync_api import sync_playwright
        from playwright_stealth import Stealth

        cls._pw = sync_playwright().start()
        cls._browser = cls._pw.chromium.launch(headless=True)
        ctx = cls._browser.new_context(user_agent=_UA)
        page = ctx.new_page()
        Stealth().apply_stealth_sync(page)
        try:
            page.goto(HOME, wait_until="domcontentloaded", timeout=90000, referer=HOME)
        except Exception:
            pass
        page.wait_for_timeout(4000)  # deja resolver el challenge F5 + Angular
        cls._page = page

    @classmethod
    def page(cls):
        with cls._lock:
            if cls._page is None:
                cls._boot()
            return cls._page

    @classmethod
    def reiniciar(cls):
        with cls._lock:
            try:
                if cls._browser:
                    cls._browser.close()
            except Exception:
                pass
            try:
                if cls._pw:
                    cls._pw.stop()
            except Exception:
                pass
            cls._pw = cls._browser = cls._page = None


_POST_JS = """async ([tok, idb, q, filas]) => {
  const fd = new FormData();
  fd.append('_token', tok);
  fd.append('id_buscador', String(idb));
  fd.append('filtros', JSON.stringify({
    rol:"", era:"", fec_desde:"", fec_hasta:"", todas:"", algunas:"",
    excluir:"", analisis_s:"11", submaterias:"", facetas_seleccionadas:[],
    filtros_omnibox:[{categoria:"TEXTO", valores:[q]}],
    ids_comunas_seleccionadas_mapa:[]}));
  fd.append('numero_filas_paginacion', String(filas));
  fd.append('offset_paginacion', '0');
  fd.append('orden', 'recientes');
  fd.append('personalizacion', 'false');
  const r = await fetch('/busqueda/buscar_sentencias', {
    method: 'POST', body: fd, credentials: 'include',
    headers: {'X-Requested-With': 'XMLHttpRequest'}});
  const txt = await r.text();
  try { return {status: r.status, json: JSON.parse(txt)}; }
  catch (e) { return {status: r.status, texto: txt.slice(0, 500)}; }
}"""


def _token(page) -> str:
    tok = page.evaluate(
        "() => (document.querySelector('input[name=_token]')||{}).value || "
        "(document.querySelector('meta[name=csrf-token]')||{}).content || ''")
    if not tok:
        raise PJUDNoDisponible("sin token CSRF del portal PJUD")
    return tok


def _normalizar(doc: dict[str, Any]) -> dict[str, Any]:
    fecha = (doc.get("fec_sentencia_sup_dt") or "")[:10]
    return {
        "tribunal": doc.get("gls_corte_s") or "",
        "sala": doc.get("gls_sala_sup_s") or "",
        "rol": doc.get("rol_era_sup_s") or "",
        "fecha": fecha,
        "caratulado": doc.get("caratulado_s") or "",
        "tipo_recurso": doc.get("gls_tip_recurso_sup_s") or "",
        "resultado": doc.get("resultado_recurso_sup_s") or "",
        "texto": doc.get("texto_sentencia") or "",
        "url": doc.get("url_acceso_sentencia") or doc.get("url_corta_acceso_sentencia") or "",
        "cita": doc.get("cita_bibliografica") or "",
        "origen": doc.get("gls_juz_s") or "",
    }


def _ejecutar(page, id_buscador: int, query: str, limite: int) -> dict:
    resp = page.evaluate(_POST_JS, [_token(page), id_buscador, query, limite])
    if resp.get("json") and "response" in resp["json"]:
        return resp["json"]
    # sesión caducada / challenge nuevo: re-bootstrap una sola vez
    raise _SesionCaducada(resp.get("status"))


class _SesionCaducada(Exception):
    pass


def resolver_buscador(buscador) -> int:
    """Acepta id numérico o nombre de categoría ("corte_suprema", "civiles"...)."""
    if isinstance(buscador, int):
        return buscador
    if isinstance(buscador, str):
        clave = buscador.strip().lower().replace(" ", "_")
        if clave in ID_BUSCADORES:
            return ID_BUSCADORES[clave]
        raise PJUDNoDisponible(f"buscador desconocido '{buscador}'; "
                               f"opciones: {', '.join(sorted(ID_BUSCADORES))}")
    return DEFAULT_BUSCADOR


def buscar_sentencias_pjud(query: str, limite: int = 10,
                           id_buscador: int = DEFAULT_BUSCADOR,
                           buscador: str | None = None) -> tuple[list[dict], int]:
    """Busca fallos en juris.pjud.cl. Devuelve (lista normalizada, numFound).

    ``buscador`` permite elegir categoría ("corte_suprema", "corte_de_apelaciones",
    "civiles", "penales", "familia", "laborales", "cobranza",
    "compendio_extranjeria", "lineas_jurisprudenciales", "salud_cs").

    Levanta ``PJUDNoDisponible`` si el portal no coopera (nunca inventa
    "no hay fallos" ante un fallo de transporte/anti-bot)."""
    if buscador is not None:
        id_buscador = resolver_buscador(buscador)
    else:
        id_buscador = resolver_buscador(id_buscador)
    ultimo_exc: Exception | None = None
    for intento in range(3):
        try:
            page = _SesionPJUD.page()
            data = _ejecutar(page, id_buscador, query.strip(), limite)
            resp = data["response"]
            docs = resp.get("docs") or []
            return [_normalizar(d) for d in docs], int(resp.get("numFound", 0))
        except _SesionCaducada as exc:
            ultimo_exc = exc
            _SesionPJUD.reiniciar()
        except PJUDNoDisponible:
            raise
        except Exception as exc:  # navegador caído, red, etc.
            ultimo_exc = exc
            _SesionPJUD.reiniciar()
    raise PJUDNoDisponible(f"el buscador PJUD no respondió tras 3 intentos ({ultimo_exc})")
