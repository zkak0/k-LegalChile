"""Vigilancia legal automática — estilo Magnar Monitor pero 100% local y gratuito.

El abogado define una "vigilancia": un nombre, una condición en lenguaje
natural ("todo lo nuevo sobre protección de datos en salud") y las fuentes
oficiales a vigilar. Cada ejecución consulta esas fuentes con palabras clave
derivadas de la condición, detecta lo NUEVO (dedupe por URL) y lo entrega en
formato narrativo-jurídico para que el LLM del usuario filtre lo realmente
relevante contra la condición. Cero costo de API: el filtrado semántico lo
hace el modelo del usuario, no un servicio externo.

Fuentes soportadas (todas oficiales y ya implementadas en el servidor):
  cgr             — Dictámenes Contraloría General de la República
  tc              — Sentencias Tribunal Constitucional
    tgr             — Dictámenes Tesorería General de la República
  sii             — Oficios SII (jurisprudencia administrativa tributaria)
  diario_oficial  — Normas publicadas (vía LeyChile/BCN, mismo contenido oficial)
  normas          — Legislación BCN LeyChile directa

Diseño confirmado con el usuario: primero una fase bien hecha; dedupe estricto;
formato narrativo obligatorio; links oficiales verificables siempre.
"""

from __future__ import annotations

import json
import re
from datetime import datetime

from .db import get_db

FUENTES_VALIDAS = {
    "cgr": "Dictámenes Contraloría General de la República",
    "tc": "Sentencias Tribunal Constitucional",
    "tgr": "Dictámenes Tesorería General de la República",
    "sii": "Oficios SII — jurisprudencia administrativa tributaria",
    "diario_oficial": "Normas del Diario Oficial (vía LeyChile/BCN)",
    "normas": "Legislación LeyChile/BCN",
}

_STOPWORDS = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "y", "o", "que",
    "en", "a", "del", "al", "con", "por", "para", "sobre", "todo", "toda", "todos",
    "todas", "lo", "su", "sus", "como", "mas", "más", "pero", "si", "no", "se",
    "es", "son", "sea", "sean", "este", "esta", "estos", "estas", "ese", "esa",
    "cuando", "donde", "cual", "cuál", "quienes", "quien", "me", "te", "le", "les",
    "avise", "avisa", "avisar", "detecte", "detectar", "nuevo", "nueva", "nuevos",
    "nuevas", "cambio", "cambios", "aparezca", "aparecen", "quiero", "necesito",
}

MAX_PALABRAS_QUERY = 6


def _hoy() -> str:
    return datetime.now().strftime("%d-%m-%Y %H:%M")


def extraer_palabras_clave(condicion: str) -> str:
    """Extrae hasta MAX_PALABRAS_QUERY palabras significativas de la condición."""
    palabras = re.findall(r"[a-záéíóúüñA-ZÁÉÍÓÚÜÑ][\wáéíóúüñÁÉÍÓÚÜÑ]*", condicion.lower())
    sig = [p for p in palabras if p not in _STOPWORDS and len(p) > 2]
    vistos: set[str] = set()
    out = []
    for p in sig:
        if p not in vistos:
            vistos.add(p)
            out.append(p)
        if len(out) >= MAX_PALABRAS_QUERY:
            break
    return " ".join(out)


def crear_vigilancia(nombre: str, condicion: str, fuentes: list[str]) -> dict:
    """Crea una vigilancia. Valida fuentes. Devuelve dict con estado."""
    nombre = nombre.strip()
    condicion = condicion.strip()
    if not nombre or not condicion:
        return {"ok": False, "error": "Nombre y condición son obligatorios."}
    malas = [f for f in fuentes if f not in FUENTES_VALIDAS]
    if malas:
        validas = ", ".join(sorted(FUENTES_VALIDAS))
        return {"ok": False, "error": f"Fuentes inválidas: {malas}. Válidas: {validas}"}
    db = get_db()
    existe = db._conn.execute(
        "SELECT 1 FROM vigilancias WHERE nombre = ?", (nombre,)).fetchone()
    if existe:
        return {"ok": False, "error": f"Ya existe una vigilancia llamada '{nombre}'."}
    db._conn.execute(
        "INSERT INTO vigilancias (nombre, condicion, fuentes) VALUES (?,?,?)",
        (nombre, condicion, json.dumps(fuentes)))
    db._conn.commit()
    return {"ok": True, "nombre": nombre, "condicion": condicion,
            "fuentes": fuentes, "creada": _hoy()}


def listar_vigilancias() -> list[dict]:
    db = get_db()
    rows = db._conn.execute(
        "SELECT id, nombre, condicion, fuentes, activa, creada, ultima_ejecucion "
        "FROM vigilancias ORDER BY id DESC").fetchall()
    out = []
    for r in rows:
        try:
            fuentes = json.loads(r["fuentes"])
        except Exception:
            fuentes = []
        pendientes = db._conn.execute(
            "SELECT COUNT(*) FROM vigilancia_items WHERE vigilancia_id=? AND estado='nuevo'",
            (r["id"],)).fetchone()[0]
        out.append({"id": r["id"], "nombre": r["nombre"], "condicion": r["condicion"],
                    "fuentes": fuentes, "activa": bool(r["activa"]), "creada": r["creada"],
                    "ultima_ejecucion": r["ultima_ejecucion"], "pendientes_nuevos": pendientes})
    return out


def eliminar_vigilancia(nombre: str) -> dict:
    db = get_db()
    row = db._conn.execute("SELECT id FROM vigilancias WHERE nombre=?", (nombre.strip(),)).fetchone()
    if not row:
        return {"ok": False, "error": f"No existe vigilancia '{nombre}'."}
    db._conn.execute("DELETE FROM vigilancia_items WHERE vigilancia_id=?", (row["id"],))
    db._conn.execute("DELETE FROM vigilancias WHERE id=?", (row["id"],))
    db._conn.commit()
    return {"ok": True, "eliminada": nombre}


# --- Fetchers por fuente: devuelven lista de dicts normalizados -------------

def _fetch_cgr(query: str, limite: int) -> list[dict]:
    from .contraloria import buscar_cgr
    rows = buscar_cgr(query, limite=limite)
    return [{"fuente": "cgr", "titulo": r.get("titulo", ""), "url": r.get("url", ""),
             "identificador": r.get("url", ""), "fecha_publicacion": None} for r in rows]


def _fetch_tc(query: str, limite: int) -> list[dict]:
    from .fuentes_externas import buscar_tc
    rows = buscar_tc(query, limite=limite)
    out = []
    for r in rows:
        titulo = r.get("titulo") or ""
        url = r.get("url") or ""
        if "Buscar '" in titulo:  # descarta fallback genérico
            continue
        # Solo fichas reales de sentencias (descarta favicon/nav del fallback scraping)
        if "/sentencia/" not in url:
            continue
        if len(titulo.strip()) < 15:
            continue
        out.append({"fuente": "tc", "titulo": titulo[:300], "url": url,
                    "identificador": url, "fecha_publicacion": r.get("fecha")})
    return out


def _fetch_tgr(query: str, limite: int) -> list[dict]:
    from . import tgr as _tgr
    rows = _tgr.buscar_dictamen(query, limite)
    return [{"fuente": "tgr", "titulo": r.get("titulo", ""), "url": r.get("url", ""),
             "identificador": r.get("url", ""), "fecha_publicacion": None} for r in rows]


def _fetch_sii(query: str, limite: int) -> list[dict]:
    from . import sii as _sii
    rows = _sii.buscar_oficio(query, limite)
    return [{"fuente": "sii", "titulo": r.get("titulo", ""), "url": r.get("url", ""),
             "identificador": r.get("url", ""), "fecha_publicacion": None} for r in rows]


def _fetch_diario_oficial(query: str, limite: int) -> list[dict]:
    from .fuentes_externas import buscar_diario_oficial
    rows = buscar_diario_oficial(query, limite)
    out = []
    for r in rows:
        titulo = r.get("titulo") or ""
        url = r.get("url") or ""
        if not url:
            continue
        out.append({"fuente": "diario_oficial", "titulo": titulo[:200], "url": url,
                    "identificador": url, "fecha_publicacion": None})
    return out


def _fetch_normas(query: str, limite: int) -> list[dict]:
    from .sparql_client import BCNClient, leychile_url
    c = BCNClient()
    rows = c.search_by_title(query, limit=limite)
    out = []
    for r in rows:
        lid = r.get("leychileId") or r.get("leychile_id")
        url = leychile_url(lid) or r.get("uri", "")
        numero = r.get("numero") or ""
        out.append({"fuente": "normas",
                    "titulo": f"{r.get('titulo','')}{' — N° ' + numero if numero else ''}",
                    "url": url, "identificador": url,
                    "fecha_publicacion": r.get("fecha")})
    return out


_FETCHERS_DISPONIBLES = tuple(FUENTES_VALIDAS.keys())


def ejecutar_vigilancia(nombre: str, limite_por_fuente: int = 10) -> dict:
    """Ejecuta una vigilancia: consulta cada fuente activa, deduplica y guarda novedades.

    Devuelve: items nuevos encontrados (con resumen para filtrado semántico),
    conteo de analizados, y errores por fuente si los hubo.
    """
    db = get_db()
    row = db._conn.execute(
        "SELECT id, nombre, condicion, fuentes, activa FROM vigilancias WHERE nombre=?",
        (nombre.strip(),)).fetchone()
    if not row:
        return {"ok": False, "error": f"No existe vigilancia '{nombre}'."}
    if not row["activa"]:
        return {"ok": False, "error": f"La vigilancia '{nombre}' está pausada."}
    vid = row["id"]
    fuentes = json.loads(row["fuentes"])
    query = extraer_palabras_clave(row["condicion"])
    if not query:
        return {"ok": False, "error": "La condición no contiene palabras clave utilizables."}

    nuevos: list[dict] = []
    analizados = 0
    errores: dict[str, str] = {}
    for fuente in fuentes:
        fetcher = globals().get(f"_fetch_{fuente}")
        if fetcher is None:
            errores[fuente] = "Fuente sin fetcher registrado."
            continue
        try:
            items = fetcher(query, limite_por_fuente)
        except Exception as exc:  # noqa: BLE001
            errores[fuente] = str(exc)[:300]
            continue
        for it in items:
            ident = it.get("identificador") or it.get("url")
            if not ident:
                continue
            ya = db._conn.execute(
                "SELECT 1 FROM vigilancia_items WHERE vigilancia_id=? AND identificador=?",
                (vid, ident)).fetchone()
            analizados += 1
            if ya:
                continue
            db._conn.execute(
                "INSERT INTO vigilancia_items "
                "(vigilancia_id, fuente, identificador, titulo, resumen, url, fecha_publicacion) "
                "VALUES (?,?,?,?,?,?,?)",
                (vid, it["fuente"], ident, it["titulo"][:400],
                 it.get("resumen"), it["url"], it.get("fecha_publicacion")))
            nuevos.append(it)
    db._conn.execute(
        "UPDATE vigilancias SET ultima_ejecucion=datetime('now','localtime') WHERE id=?", (vid,))
    db._conn.commit()
    return {"ok": True, "vigilancia": nombre, "condicion": row["condicion"],
            "query_usada": query, "nuevos": nuevos, "total_analizados": analizados,
            "errores": errores, "ejecutada": _hoy()}


def historial_vigilancia(nombre: str, solo_nuevos: bool = True, limite: int = 30) -> list[dict]:
    """Ítems detectados históricamente; solo_nuevos filtra los aún no revisados."""
    db = get_db()
    row = db._conn.execute("SELECT id FROM vigilancias WHERE nombre=?", (nombre.strip(),)).fetchone()
    if not row:
        return []
    sql = ("SELECT fuente, titulo, resumen, url, fecha_publicacion, estado, fecha_deteccion "
           "FROM vigilancia_items WHERE vigilancia_id=?")
    params: list = [row["id"]]
    if solo_nuevos:
        sql += " AND estado='nuevo'"
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limite)
    return [dict(r) for r in db._conn.execute(sql, params).fetchall()]


def marcar_revisados(nombre: str) -> int:
    """Marca todos los ítems 'nuevo' como 'visto'. Devuelve cuántos marcó."""
    db = get_db()
    row = db._conn.execute("SELECT id FROM vigilancias WHERE nombre=?", (nombre.strip(),)).fetchone()
    if not row:
        return 0
    cur = db._conn.execute(
        "UPDATE vigilancia_items SET estado='visto' WHERE vigilancia_id=? AND estado='nuevo'",
        (row["id"],))
    db._conn.commit()
    return cur.rowcount


def pausar_o_activar(nombre: str, activa: bool) -> dict:
    db = get_db()
    cur = db._conn.execute(
        "UPDATE vigilancias SET activa=? WHERE nombre=?", (1 if activa else 0, nombre.strip()))
    db._conn.commit()
    if cur.rowcount == 0:
        return {"ok": False, "error": f"No existe vigilancia '{nombre}'."}
    return {"ok": True, "nombre": nombre, "activa": activa}


# --- Formato narrativo -------------------------------------------------------

DESCRIPCION_FUENTE = FUENTES_VALIDAS


def formatear_informe_ejecucion(res: dict) -> str:
    """Texto narrativo-jurídico listo para el usuario tras ejecutar una vigilancia."""
    if not res.get("ok"):
        return f"ERROR: {res.get('error', 'desconocido')}"
    lineas = [
        f"INFORME DE VIGILANCIA — '{res['vigilancia']}'",
        f"Ejecutada: {res['ejecutada']}",
        "",
        f"Condición definida por usted: \"{res['condicion']}\"",
        f"Búsqueda aplicada en las fuentes: \"{res['query_usada']}\" (palabras clave derivadas automáticamente).",
        f"Se analizaron {res['total_analizados']} publicaciones; se detectaron {len(res['nuevos'])} NOVEDADES no vistas anteriormente.",
        "",
    ]
    if res["nuevos"]:
        lineas.append(f"=== NOVEDADES DETECTADAS ({len(res['nuevos'])}) ===")
        lineas.append("")
        for i, it in enumerate(res["nuevos"], 1):
            fuente_desc = DESCRIPCION_FUENTE.get(it.get("fuente"), it.get("fuente"))
            fecha = it.get("fecha_publicacion") or "sin fecha informada por la fuente"
            lineas.append(f"{i}. [{it.get('fuente','').upper()}] {it.get('titulo','(sin título)')}")
            lineas.append(f"   Qué es: publicación oficial de {fuente_desc}.")
            lineas.append(f"   Fecha: {fecha}")
            lineas.append(f"   Fuente oficial verificable: {it.get('url','')}")
            lineas.append("")
        lineas.append(
            "IMPORTANTE — FILTRADO SEMÁNTICO: estas novedades fueron detectadas por coincidencia "
            "de palabras clave con su condición. Para decidir cuáles cumplen REALMENTE la condición, "
            "lea los títulos y compare contra la condición textual de arriba. Los que no apliquen, "
            "descártelos al marcar la vigilancia como revisada.")
    else:
        lineas.append("CONCLUSIÓN: No se detectaron publicaciones nuevas respecto de la última "
                      "ejecución. Esto NO significa que no haya pasado nada: significa que nada "
                      "coincidió con las palabras clave desde la revisión anterior.")
    if res["errores"]:
        lineas.append("")
        lineas.append("ADVERTENCIA — fuentes con problemas de conexión en esta ejecución:")
        for f, err in res["errores"].items():
            lineas.append(f"• {f}: {err}")
    lineas.append("")
    lineas.append("Próximo paso sugerido: use vigilancia_historial para ver acumuladas, o "
                  "marque esta ejecución como revisada cuando haya evaluado las novedades.")
    return "\n".join(lineas)


def formatear_listado(vigs: list[dict]) -> str:
    if not vigs:
        return ("No tienes vigilancias creadas todavía.\n"
                "Ejemplo: vigilancia_crear(nombre='datos_salud', "
                "condicion='nuevas normas o sentencias sobre protección de datos de salud', "
                "fuentes=['tc','cgr','normas'])")
    lineas = [f"TUS VIGILANCIAS LEGALES ({len(vigs)}):", ""]
    for v in vigs:
        estado = "activa" if v["activa"] else "PAUSADA"
        fuentes_txt = ", ".join(v["fuentes"])
        lineas.append(f"• '{v['nombre']}' [{estado}] — creada {v['creada']}")
        lineas.append(f"  Condición: \"{v['condicion']}\"")
        lineas.append(f"  Fuentes: {fuentes_txt}")
        lineas.append(f"  Última ejecución: {v['ultima_ejecucion'] or 'nunca'} — "
                      f"Novedades sin revisar: {v['pendientes_nuevos']}")
        lineas.append("")
    return "\n".join(lineas)


def formatear_historial(nombre: str, items: list[dict], solo_nuevos: bool) -> str:
    if not items:
        base = f"Historial de '{nombre}': sin ítems "
        base += "sin revisar." if solo_nuevos else "registrados."
        return base + " Ejecute vigilancia_ejecutar para buscar novedades ahora."
    lineas = [f"HISTORIAL DE VIGILANCIA — '{nombre}' ({len(items)} ítems "
              f"{'sin revisar' if solo_nuevos else 'totales'}):", ""]
    for i, it in enumerate(items, 1):
        lineas.append(f"{i}. [{str(it.get('fuente','')).upper()}] {it.get('titulo','')}")
        if it.get("fecha_publicacion"):
            lineas.append(f"   Fecha publicación: {it['fecha_publicacion']}")
        lineas.append(f"   Detectado: {it.get('fecha_deteccion','')} — estado: {it.get('estado','')}")
        lineas.append(f"   Fuente: {it.get('url','')}")
        lineas.append("")
    return "\n".join(lineas)
