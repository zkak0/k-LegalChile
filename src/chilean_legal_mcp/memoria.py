"""Memoria persistente del abogado — el MCP recuerda todo entre sesiones.

Diseño confirmado con el usuario:
- Historial completo de preguntas y respuestas (rol usuario/asistente)
- Cache circular FIFO: máximo 500 mensajes (el 501 borra al más viejo)
- Limpieza automática de mensajes con más de 30 días
- Notas manuales del abogado (clientes, causas, claves, TODOs) — estas NO expiran
- Búsqueda FTS5 ultrarrápida sobre todo lo guardado
- Todo local, en un solo archivo SQLite — nada sale del computador

Peso estimado en el peor caso: ~1-2 MB. Nada.
"""

from __future__ import annotations

from datetime import datetime

from .db import get_db

LIMITE_MENSAJES = 500
DIAS_RETENCION = 30


def _hoy() -> str:
    return datetime.now().strftime("%d-%m-%Y %H:%M")


def registrar_mensaje(rol: str, contenido: str, sesion_id: str | None = None,
                      herramientas: str | None = None) -> int:
    """Guarda un mensaje del historial. Aplica cache circular y limpieza temporal.

    rol: 'usuario' | 'asistente' | 'consulta_auto'
    Devuelve el id insertado.
    """
    db = get_db()
    cur = db._conn.execute(
        "INSERT INTO memoria_mensajes (sesion_id, rol, contenido, herramientas) VALUES (?,?,?,?)",
        (sesion_id, rol, contenido[:8000], herramientas))
    # Cache circular FIFO: conservar solo los últimos LIMITE_MENSAJES
    db._conn.execute(
        "DELETE FROM memoria_mensajes WHERE id NOT IN "
        "(SELECT id FROM memoria_mensajes ORDER BY id DESC LIMIT ?)",
        (LIMITE_MENSAJES,))
    # Limpieza temporal: nada con más de DIAS_RETENCION días
    db._conn.execute(
        "DELETE FROM memoria_mensajes WHERE fecha < datetime('now', 'localtime', ?)",
        (f'-{DIAS_RETENCION} days',))
    db._conn.commit()
    return cur.lastrowid


def guardar_nota(nombre: str, contenido: str, tipo: str = "nota") -> int:
    """Guarda una nota manual del abogado. Las notas NO expiran ni rotan."""
    db = get_db()
    cur = db._conn.execute(
        "INSERT INTO memoria_notas (tipo, nombre, contenido) VALUES (?,?,?)",
        (tipo, nombre, contenido))
    db._conn.commit()
    return cur.lastrowid


def consultar_memoria(query: str, limite: int = 10) -> dict:
    """Búsqueda FTS5 sobre notas + mensajes. Ultrarrápido (milisegundos)."""
    from .db import _fts_prefix_query
    db = get_db()
    try:
        q = _fts_prefix_query(query)
    except ValueError:
        return {"notas": [], "mensajes": []}
    notas = [dict(r) for r in db._conn.execute(
        "SELECT n.id, n.tipo, n.nombre, substr(n.contenido,1,400) AS contenido, n.fecha "
        "FROM memoria_notas_fts f JOIN memoria_notas n ON n.rowid=f.rowid "
        "WHERE memoria_notas_fts MATCH ? ORDER BY bm25(memoria_notas_fts) LIMIT ?",
        (q, limite)).fetchall()]
    mensajes = [dict(r) for r in db._conn.execute(
        "SELECT m.id, m.rol, substr(m.contenido,1,400) AS contenido, m.fecha "
        "FROM memoria_mensajes_fts f JOIN memoria_mensajes m ON m.rowid=f.rowid "
        "WHERE memoria_mensajes_fts MATCH ? ORDER BY bm25(memoria_mensajes_fts) LIMIT ?",
        (q, limite)).fetchall()]
    return {"notas": notas, "mensajes": mensajes}


def historial_reciente(limite: int = 20) -> list[dict]:
    """Los últimos N mensajes en orden cronológico."""
    db = get_db()
    rows = db._conn.execute(
        "SELECT rol, contenido, herramientas, fecha FROM memoria_mensajes "
        "ORDER BY id DESC LIMIT ?", (limite,)).fetchall()
    return [{"rol": r[0], "contenido": r[1], "herramientas": r[2], "fecha": r[3]}
            for r in reversed(rows)]


def resumen_trabajo(dias: int = 7) -> dict:
    """Qué se trabajó los últimos N días: conteo por día + notas activas."""
    db = get_db()
    por_dia = [dict(r) for r in db._conn.execute(
        "SELECT date(fecha) AS dia, COUNT(*) AS consultas FROM memoria_mensajes "
        "WHERE fecha >= datetime('now', 'localtime', ?) GROUP BY date(fecha) ORDER BY dia DESC",
        (f'-{dias} days',)).fetchall()]
    total_mensajes = db._conn.execute("SELECT COUNT(*) FROM memoria_mensajes").fetchone()[0]
    total_notas = db._conn.execute("SELECT COUNT(*) FROM memoria_notas").fetchone()[0]
    notas_recientes = [dict(r) for r in db._conn.execute(
        "SELECT tipo, nombre, substr(contenido,1,200) AS contenido, fecha "
        "FROM memoria_notas ORDER BY id DESC LIMIT 10").fetchall()]
    return {
        "por_dia": por_dia,
        "total_mensajes": total_mensajes,
        "total_notas": total_notas,
        "notas_recientes": notas_recientes,
        "limite_cache": LIMITE_MENSAJES,
        "dias_retencion": DIAS_RETENCION,
    }


def formatear_memoria(resultado_busqueda: dict, query: str) -> str:
    """Texto listo para mostrar al abogado."""
    lineas = [f"Resultados en tu memoria para '{query}':", ""]
    if resultado_busqueda["notas"]:
        lineas.append("📌 Notas guardadas:")
        for n in resultado_busqueda["notas"]:
            lineas.append(f"• [{n['tipo']}] {n['nombre']} ({n['fecha']})")
            if n.get("contenido"):
                lineas.append(f"  {n['contenido']}")
            lineas.append("")
    else:
        lineas.append("📌 Sin notas guardadas que coincidan.")
        lineas.append("")
    if resultado_busqueda["mensajes"]:
        lineas.append(f"💬 Conversaciones anteriores:")
        for m in resultado_busqueda["mensajes"]:
            quien = "Abogado" if m["rol"] == "usuario" else ("Auto" if m["rol"] == "consulta_auto" else "Asistente")
            lineas.append(f"• [{quien} · {m['fecha']}] {m['contenido']}")
            lineas.append("")
    else:
        lineas.append("💬 Sin conversaciones anteriores que coincidan.")
    return "\n".join(lineas)


def formatear_resumen(resumen: dict) -> str:
    """Resumen de trabajo listo para mostrar."""
    lineas = ["📊 Resumen de tu trabajo reciente:", ""]
    if resumen["por_dia"]:
        for d in resumen["por_dia"][:7]:
            lineas.append(f"• {d['dia']}: {d['consultas']} interacciones")
    else:
        lineas.append("Sin actividad registrada aún.")
    lineas.append("")
    lineas.append(f"Total en memoria: {resumen['total_mensajes']} mensajes "
                  f"(cache circular máx {resumen['limite_cache']}, retención {resumen['dias_retencion']} días)")
    lineas.append(f"Notas guardadas: {resumen['total_notas']} (estas nunca expiran)")
    if resumen["notas_recientes"]:
        lineas.append("")
        lineas.append("Últimas notas:")
        for n in resumen["notas_recientes"][:5]:
            lineas.append(f"• [{n['tipo']}] {n['nombre']}: {n['contenido'][:100]}")
    return "\n".join(lineas)
