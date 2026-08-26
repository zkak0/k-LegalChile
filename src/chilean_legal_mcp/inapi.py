"""INAPI + TDPI — marcas (Ley 19.039), fuera de tribunales ordinarios.

Regla de fuentes y limitaciones verificadas (2026-08-23):
1. buscadormarcas.inapi.cl — fuente oficial INAPI. Su búsqueda está protegida con
   Google reCAPTCHA: la automatización directa NO es posible sin resolver el captcha.
   El módulo intenta el flujo JSON oficial (FindMarcas) y, si el captcha lo bloquea,
   devuelve un enlace directo al buscador para consulta manual.
2. No se usan sitios de terceros: portalchile.org/marcas/buscar fue verificado y está
   caído (404), por lo que fue eliminado del código.
3. tdpi.cl — Boletín de jurisprudencia marcaria oficial del TDPI. Funcional.
4. tramites.inapi.cl — Estados Diarios oficiales (Art. 13). Funcional.
"""

from __future__ import annotations

import re
import html as html_lib
import json
from datetime import datetime
import httpx

_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36", "Accept-Language": "es-CL,es;q=0.9"}
_BASE_MARCAS = "https://buscadormarcas.inapi.cl/Marca/BuscarMarca.aspx"


def _find_marcas_json(query: str, clase: str | None, limite: int) -> list[dict] | None:
    """Intenta el endpoint JSON oficial FindMarcas. Devuelve None si el captcha bloquea."""
    try:
        r0 = httpx.get(_BASE_MARCAS, timeout=15, headers=_UA)
        hash_v = ""
        idw_v = ""
        m = re.search(r'id="hdnHash"[^>]*value="([^"]*)"', r0.text)
        if m:
            hash_v = m.group(1)
        m = re.search(r'id="hdnIDW"[^>]*value="([^"]*)"', r0.text)
        if m:
            idw_v = m.group(1)
        headers = {
            **_UA,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": _BASE_MARCAS,
            "Origin": "https://buscadormarcas.inapi.cl",
        }
        body = {"param1": "", "param2": "", "param3": query.replace("'", "''"), "param4": "",
                "param5": clase or "", "param6": "", "param7": "", "param8": "", "param9": "",
                "param10": "", "param11": "", "param12": "", "param13": "", "param14": "",
                "param15": "", "param16": "", "param17": 1, "LastNumSol": 0,
                "Hash": hash_v, "IDW": idw_v}
        r = httpx.post(f"{_BASE_MARCAS}/FindMarcas", content=json.dumps(body).encode(),
                       headers=headers, timeout=25, cookies=r0.cookies)
        if r.status_code != 200:
            return None
        data = r.json()
        d = json.loads(data["d"]) if isinstance(data.get("d"), str) else (data.get("d") or {})
        if d.get("ErrorMessage"):
            return None
        marcas = d.get("Marcas") or []
        rows = []
        for m in marcas[:limite]:
            numero = str(m.get("NumeroSolicitud") or m.get("NumSolicitud") or "")
            registro = str(m.get("NumeroRegistro") or m.get("NumRegistro") or "")
            nombre = str(m.get("NombreMarca") or m.get("Marca") or "").strip()
            titular = str(m.get("Titular") or "").strip()
            estado = str(m.get("Estado") or "").strip()
            if not nombre:
                continue
            titulo = f"Marca '{nombre}'"
            if registro and registro != "0":
                titulo += f" — Registro N° {registro}"
            if estado:
                titulo += f" ({estado})"
            rows.append({
                "numero": numero or registro or nombre[:20],
                "titulo": titulo[:140],
                "url": _BASE_MARCAS,
                "titular": titular,
                "estado": estado,
                "fuente": "INAPI oficial (buscadormarcas.inapi.cl)",
            })
        return rows
    except Exception:
        return None


def buscar_marca(query: str, modo: str = "contenga", clase: str | None = None, limite: int = 10) -> list[dict]:
    ahora = datetime.now().strftime("%d-%m-%Y")

    # 1. Endpoint JSON oficial (puede fallar por reCAPTCHA)
    rows = _find_marcas_json(query, clase, limite)
    if rows:
        return rows

    # 2. Sin API accesible: guía al buscador oficial (el captcha exige interacción humana)
    return [{
        "numero": query,
        "titulo": (f"Búsqueda de marca '{query}' requiere verificación humana (reCAPTCHA del "
                   f"buscador oficial INAPI). Abra el buscador y consulte directamente."),
        "url": f"{_BASE_MARCAS}",
        "fuente": f"INAPI oficial — buscador con captcha, verificado {ahora}",
    }]


def consulta_marca(n_solicitud: str | None = None, n_registro: str | None = None) -> dict | None:
    q = n_solicitud or n_registro or ""
    if not q:
        return None
    rows = buscar_marca(q, limite=1)
    return rows[0] if rows else None


def estados_diarios(fecha: str | None = None, limite: int = 5) -> list[dict]:
    base = "https://tramites.inapi.cl/EstadosDiariosMarcas"
    # Lista últimos 30 días en la portada
    try:
        r = httpx.get(base, timeout=15, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
        if r.status_code == 200:
            text = r.text
            rows: list[dict] = []
            for href, title in re.findall(r'<a[^>]+href="([^"]*\.pdf)"[^>]*>([^<]+)</a>', text, re.I):
                t = html_lib.unescape(title.strip())
                full = href if href.startswith("http") else f"https://tramites.inapi.cl{href}"
                rows.append({"numero": href.split("/")[-1][:20], "titulo": t[:120], "url": full})
                if len(rows) >= limite:
                    break
            if rows:
                return rows
    except Exception:
        pass
    # Fallback por fecha
    if fecha:
        # fecha DD-MM-AAAA -> YYYY-MM-DD para PDF nombre
        try:
            d, m, y = fecha.split("-")
            pdf = f"https://tramites.inapi.cl/EstadosDiariosMarcas/{y}-{m}-{d}.pdf"
            return [{"numero": fecha, "titulo": f"Estado Diario Marcas {fecha}", "url": pdf}]
        except Exception:
            pass
    return [{"numero": fecha or "hoy", "titulo": "Estados Diarios Marcas (últimos 30 días)", "url": base}]


def tdpi_jurisprudencia(query: str, limite: int = 5) -> list[dict]:
    for url in [
        f"https://www.tdpi.cl/?s={query.replace(' ', '+')}",
        "https://www.tdpi.cl/category/documentos/boletin-de-jurisprudencia-marcaria/",
    ]:
        try:
            r = httpx.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
            if r.status_code != 200:
                continue
            text = r.text
            rows: list[dict] = []
            for href, title in re.findall(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>([^<]+)</a>', text, re.I):
                t = html_lib.unescape(title.strip())
                if len(t) < 10:
                    continue
                full = href if href.startswith("http") else f"https://www.tdpi.cl{href}"
                rows.append({"numero": href.split("/")[-1][:20], "titulo": t[:120], "url": full})
                if len(rows) >= limite:
                    break
            if not rows:
                for href, title in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{15,80})</a>', text):
                    if "boletin" not in href.lower() and "jurisprudencia" not in title.lower():
                        continue
                    rows.append({"numero": href.split("/")[-1][:20], "titulo": html_lib.unescape(title.strip())[:120], "url": href if href.startswith("http") else f"https://www.tdpi.cl{href}"})
                    if len(rows) >= limite:
                        break
            if rows:
                return rows
        except Exception:
            continue
    return [{"numero": query, "titulo": f"Buscar jurisprudencia marcaria '{query}' en TDPI", "url": "https://www.tdpi.cl/category/documentos/boletin-de-jurisprudencia-marcaria/"}]
