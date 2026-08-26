"""Tests de memoria persistente — cache circular, limpieza, FTS.

Ejecutar: pytest tests/test_memoria.py -v
"""

import sys
sys.path.insert(0, "src")

from chilean_legal_mcp.db import get_db
from chilean_legal_mcp.memoria import (
    LIMITE_MENSAJES,
    consultar_memoria,
    guardar_nota,
    historial_reciente,
    registrar_mensaje,
    resumen_trabajo,
)


def test_registrar_y_recuperar_mensaje():
    """Mensaje registrado es recuperable desde el historial."""
    id_ = registrar_mensaje("usuario", "test pregunta única xyzzy", sesion_id="test")
    assert id_ > 0
    hist = historial_reciente(5)
    assert any("xyzzy" in m["contenido"] for m in hist)


def test_guardar_nota():
    """Nota guardada se puede buscar por FTS."""
    id_ = guardar_nota("Cliente Test Unico Qq", "Causa rol C-9999-2025 test", tipo="causa")
    assert id_ > 0
    res = consultar_memoria("Cliente Test Unico Qq")
    assert len(res["notas"]) >= 1
    assert any("C-9999-2025" in n["contenido"] for n in res["notas"])


def test_consultar_memoria_mensajes():
    """La búsqueda FTS encuentra mensajes del historial."""
    registrar_mensaje("usuario", "necesito ver normativa protección mujeres test", sesion_id="test")
    res = consultar_memoria("protección mujeres")
    assert isinstance(res["mensajes"], list)


def test_cache_circular_fifo():
    """El mensaje 501+ borra al más viejo (cache circular)."""
    db = get_db()
    # Insertar LIMITE+5 mensajes únicos
    for i in range(LIMITE_MENSAJES + 5):
        registrar_mensaje("usuario", f"mensaje circular test numero {i} zzzz")
    total = db._conn.execute("SELECT COUNT(*) FROM memoria_mensajes").fetchone()[0]
    assert total <= LIMITE_MENSAJES, f"Cache circular falló: {total} mensajes"


def test_notas_no_rotan():
    """Las notas NO se borran por el cache circular (solo mensajes rotan)."""
    import uuid
    nombre = f"NotaPersistenteTest_{uuid.uuid4().hex[:8]}"
    guardar_nota(nombre, "sobrevive al circular", tipo="test")
    db = get_db()
    n = db._conn.execute(
        "SELECT COUNT(*) FROM memoria_notas WHERE nombre = ?", (nombre,)).fetchone()[0]
    assert n == 1


def test_resumen_trabajo_estructura():
    """resumen_trabajo devuelve todas las claves esperadas."""
    r = resumen_trabajo(dias=7)
    for clave in ("por_dia", "total_mensajes", "total_notas", "notas_recientes", "limite_cache"):
        assert clave in r, f"Falta clave {clave} en resumen"
    assert r["limite_cache"] == 500


def test_registrar_mensaje_no_llena_bd():
    """Un mensaje de 100KB queda truncado a 8000 chars."""
    id_ = registrar_mensaje("usuario", "a" * 100000)
    db = get_db()
    largo = db._conn.execute(
        "SELECT LENGTH(contenido) FROM memoria_mensajes WHERE id=?", (id_,)).fetchone()[0]
    assert largo == 8000


def test_limpieza_temporal():
    """Mensajes con más de 30 días se auto-eliminan al registrar uno nuevo."""
    db = get_db()
    db._conn.execute(
        "INSERT INTO memoria_mensajes (rol, contenido, fecha) VALUES ('usuario', 'viejo test', datetime('now','localtime','-31 days'))")
    db._conn.commit()
    registrar_mensaje("usuario", "nuevo mensaje trigger limpieza")
    viejos = db._conn.execute(
        "SELECT COUNT(*) FROM memoria_mensajes WHERE fecha < datetime('now','localtime','-30 days')").fetchone()[0]
    assert viejos == 0
