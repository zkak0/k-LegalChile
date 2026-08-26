"""Verificación de salud de las fuentes oficiales chilenas.

Ejecuta checks de conectividad contra cada endpoint oficial y devuelve
un reporte de estado: ONLINE, DEGRADADO, O WAF_BLOQUEADO.

Ideal para ejecutar al iniciar el servidor o cuando el usuario quiera
saber si hay problemas de acceso antes de iniciar una búsqueda.
"""

from __future__ import annotations

import time
import httpx

from .config import HEALTH_ENDPOINTS, TIMEOUTS, ALLOWED_DOMAINS

HEADERS = {
    "User-Agent": "chilean-legal-mcp/0.1 (verificacion de salud de fuentes)",
    "Accept-Language": "es-CL,es;q=0.9",
}


def verificar_todas(limite_ms: int = 5000) -> str:
    """Verifica el estado de todas las fuentes oficiales.

    Args:
        limite_ms: latencia máxima aceptable en ms (default 5000)

    Returns:
        Reporte en texto con estado de cada fuente.
    """
    resultados = []
    fuentes_online = 0
    fuentes_bloqueadas = 0
    fuentes_caidas = 0

    for nombre, url in HEALTH_ENDPOINTS.items():
        estado, detalle = _verificar_una(url, limite_ms)
        resultados.append((nombre, url, estado, detalle))
        if estado == "ONLINE":
            fuentes_online += 1
        elif estado == "WAF_BLOQUEADO":
            fuentes_bloqueadas += 1
        else:
            fuentes_caidas += 1

    total = len(HEALTH_ENDPOINTS)
    resumen = (
        f"=== Verificación de fuentes oficiales chilenas ===\n"
        f"Fecha: {time.strftime('%d-%m-%Y %H:%M:%S')}\n\n"
        f"Resumen: {fuentes_online}/{total} ONLINE, "
        f"{fuentes_bloqueadas} BLOQUEADAS (WAF), "
        f"{fuentes_caidas} CAÍDAS\n\n"
    )

    for nombre, url, estado, detalle in sorted(resultados, key=lambda x: (x[2] != "ONLINE", x[0])):
        icono = {"ONLINE": "OK", "WAF_BLOQUEADO": "BLOQUEADO", "CAIDO": "CAÍDO", "TIMEOUT": "TIMEOUT"}.get(estado, estado)
        resumen += f"[{icono}] {nombre}\n"
        resumen += f"  URL: {url}\n"
        resumen += f"  {detalle}\n\n"

    resumen += (
        "Nota: WAF_BLOQUEADO indica que el sitio detectó tráfico automatizado.\n"
        "El sistema aplicará Playwright como fallback automático en la próxima consulta.\n"
        "Esto no impide la búsqueda — solo la hace más lenta la primera vez.\n"
    )
    return resumen


def _verificar_una(url: str, limite_ms: int) -> tuple[str, str]:
    """Verifica un endpoint individual. Devuelve (estado, detalle)."""
    inicio = time.time()
    try:
        resp = httpx.get(
            url,
            timeout=TIMEOUTS["rapido"],
            headers=HEADERS,
            follow_redirects=True,
        )
        latencia = round((time.time() - inicio) * 1000)

        if resp.status_code == 200:
            # Verificar si hay contenido real o es un challenge WAF
            texto = resp.text or ""
            if any(p.lower() in texto.lower() for p in ("Request Rejected", "cloudflare", "access denied", "Please enable JavaScript", "_cf_chl", "bpb_cookie")):
                return "WAF_BLOQUEADO", f"WAF detectado — status 200 pero contenido de bloqueo. Latencia: {latencia}ms"
            if latencia > limite_ms:
                return "ONLINE", f"Accesible pero LENTO ({latencia}ms, límite {limite_ms}ms)"
            return "ONLINE", f"Accesible — status 200, {resp.status_code}, {latencia}ms, {len(resp.text)} bytes"
        elif resp.status_code == 403:
            return "WAF_BLOQUEADO", f"Bloqueado (403 Forbidden) — posible WAF. Latencia: {latencia}ms"
        elif resp.status_code == 503:
            return "CAIDO", f"No disponible (503 Service Unavailable). Latencia: {latencia}ms"
        else:
            return "CAIDO", f"Status inesperado {resp.status_code}. Latencia: {latencia}ms"

    except httpx.TimeoutException:
        return "TIMEOUT", f"Timeout después de {TIMEOUTS['rapido']}s"
    except httpx.ConnectError:
        return "CAIDO", "Error de conexión — sitio no responde"
    except Exception as e:
        return "CAIDO", f"Error: {type(e).__name__}: {str(e)[:80]}"