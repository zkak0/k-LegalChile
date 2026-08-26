"""Tests del módulo de vigilancias legales (estilo Monitor)."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest

import chilean_legal_mcp.vigilancia as vig


@pytest.fixture()
def db_tmp(monkeypatch):
    """BD temporal aislada por test."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        import chilean_legal_mcp.db as db_mod
        instancia = db_mod.NormasDB(db_path)
        monkeypatch.setattr(db_mod, "_db_singleton", instancia)
        yield instancia
        instancia.close()


# --- extraer_palabras_clave --------------------------------------------------

def test_extraer_palabras_clave_filtra_stopwords():
    q = vig.extraer_palabras_clave(
        "Avísame de todo lo nuevo sobre protección de datos de salud")
    palabras = q.split()
    assert "avisa" not in palabras and "nuevo" not in palabras and "sobre" not in palabras
    assert len(palabras) <= vig.MAX_PALABRAS_QUERY


def test_extraer_palabras_clave_deduplica():
    q = vig.extraer_palabras_clave("salud salud salud mental")
    assert q.count("salud") == 1


# --- crear / listar / eliminar ----------------------------------------------

def test_crear_y_listar(db_tmp):
    res = vig.crear_vigilancia("datos", "protección de datos de salud", ["tc", "cgr"])
    assert res["ok"] is True
    vigs = vig.listar_vigilancias()
    assert len(vigs) == 1
    assert vigs[0]["nombre"] == "datos"
    assert vigs[0]["fuentes"] == ["tc", "cgr"]
    assert vigs[0]["activa"] is True


def test_crear_nombre_duplicado_rechazado(db_tmp):
    vig.crear_vigilancia("dup", "condición", ["cgr"])
    res = vig.crear_vigilancia("dup", "otra condición", ["tc"])
    assert res["ok"] is False
    assert "Ya existe" in res["error"]


def test_crear_fuente_invalida_rechazada(db_tmp):
    res = vig.crear_vigilancia("mala", "condición", ["twitter"])
    assert res["ok"] is False
    assert "Fuentes inválidas" in res["error"]


def test_eliminar_borra_items(db_tmp):
    vig.crear_vigilancia("borrable", "condición", ["cgr"])
    # insertar un ítem manualmente para verificar borrado en cascada
    db = db_tmp
    vid = db._conn.execute("SELECT id FROM vigilancias WHERE nombre='borrable'").fetchone()["id"]
    db._conn.execute(
        "INSERT INTO vigilancia_items (vigilancia_id, fuente, identificador, titulo, url) "
        "VALUES (?, 'cgr', 'http://x', 't', 'http://x')", (vid,))
    db._conn.commit()
    res = vig.eliminar_vigilancia("borrable")
    assert res["ok"] is True
    assert vig.listar_vigilancias() == []
    queda = db._conn.execute("SELECT COUNT(*) FROM vigilancia_items").fetchone()[0]
    assert queda == 0


# --- ejecutar con fetchers mockeados ----------------------------------------

def test_ejecutar_detecta_solo_nuevos(db_tmp, monkeypatch):
    vig.crear_vigilancia("mon", "dictámenes sobre licencias médicas", ["cgr"])

    items_falsos = [
        {"fuente": "cgr", "titulo": "Dictamen E12345 — Licencias médicas",
         "url": "https://contraloria.cl/x1", "identificador": "https://contraloria.cl/x1",
         "fecha_publicacion": None},
        {"fuente": "cgr", "titulo": "Dictamen E67890 — Compras públicas",
         "url": "https://contraloria.cl/x2", "identificador": "https://contraloria.cl/x2",
         "fecha_publicacion": None},
    ]
    monkeypatch.setattr(vig, "_fetch_cgr", lambda q, lim: list(items_falsos))

    r1 = vig.ejecutar_vigilancia("mon")
    assert r1["ok"] is True
    assert len(r1["nuevos"]) == 2

    # Segunda ejecución sin cambios: cero novedades (dedupe por identificador)
    r2 = vig.ejecutar_vigilancia("mon")
    assert r2["ok"] is True
    assert len(r2["nuevos"]) == 0
    assert r2["total_analizados"] == 2

    # Aparece una tercera publicación nueva: solo esa se reporta
    monkeypatch.setattr(vig, "_fetch_cgr", lambda q, lim: items_falsos + [
        {"fuente": "cgr", "titulo": "Dictamen E11111 — Nuevo fallo",
         "url": "https://contraloria.cl/x3", "identificador": "https://contraloria.cl/x3",
         "fecha_publicacion": None}])
    r3 = vig.ejecutar_vigilancia("mon")
    assert len(r3["nuevos"]) == 1
    assert "Nuevo fallo" in r3["nuevos"][0]["titulo"]


def test_ejecutar_error_de_fuente_no_rompe(db_tmp, monkeypatch):
    vig.crear_vigilancia("mixta", "condición", ["cgr", "tc"])
    monkeypatch.setattr(vig, "_fetch_cgr",
                        lambda q, lim: (_ for _ in ()).throw(RuntimeError("timeout")))
    monkeypatch.setattr(vig, "_fetch_tc", lambda q, lim: [])
    r = vig.ejecutar_vigilancia("mixta")
    assert r["ok"] is True
    assert "cgr" in r["errores"]
    assert "timeout" in r["errores"]["cgr"]


def test_ejecutar_vigilancia_inexistente(db_tmp):
    r = vig.ejecutar_vigilancia("fantasma")
    assert r["ok"] is False


def test_ejecutar_pausada_rechazada(db_tmp):
    vig.crear_vigilancia("pausa", "condición", ["cgr"])
    vig.pausar_o_activar("pausa", activa=False)
    r = vig.ejecutar_vigilancia("pausa")
    assert r["ok"] is False
    assert "pausada" in r["error"]


# --- historial / marcar revisados -------------------------------------------

def test_historial_y_marcar_revisados(db_tmp, monkeypatch):
    vig.crear_vigilancia("hist", "condición", ["cgr"])
    monkeypatch.setattr(vig, "_fetch_cgr", lambda q, lim: [
        {"fuente": "cgr", "titulo": "Ítem A", "url": "u1", "identificador": "u1",
         "fecha_publicacion": None}])
    vig.ejecutar_vigilancia("hist")

    nuevos = vig.historial_vigilancia("hist", solo_nuevos=True)
    assert len(nuevos) == 1

    marcados = vig.marcar_revisados("hist")
    assert marcados == 1
    assert vig.historial_vigilancia("hist", solo_nuevos=True) == []
    total = vig.historial_vigilancia("hist", solo_nuevos=False)
    assert len(total) == 1
    assert total[0]["estado"] == "visto"


# --- formato narrativo -------------------------------------------------------

def test_formatear_informe_narrativo_con_novedades():
    res = {"ok": True, "vigilancia": "demo",
           "condicion": "protección de datos", "query_usada": "protección datos",
           "nuevos": [{"fuente": "tc", "titulo": "Sentencia Rol 9000-2026",
                       "url": "https://tcchile.cl/x", "fecha_publicacion": None}],
           "total_analizados": 5, "errores": {}, "ejecutada": "25-08-2026 10:00"}
    txt = vig.formatear_informe_ejecucion(res)
    assert "INFORME DE VIGILANCIA" in txt
    assert "Sentencia Rol 9000-2026" in txt
    assert "https://tcchile.cl/x" in txt          # link oficial verificable
    assert "FILTRADO SEMÁNTICO" in txt            # honestidad sobre límites
    assert "NOVEDADES" in txt


def test_formatear_listado_y_historial():
    txt_lista = vig.formatear_listado([])
    assert "No tienes vigilancias" in txt_lista
    txt_hist = vig.formatear_historial("x", [], True)
    assert "Historial" in txt_hist


# --- schema -------------------------------------------------------------------

def test_schema_tablas_existen(db_tmp):
    tablas = {r[0] for r in db_tmp._conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "vigilancias" in tablas
    assert "vigilancia_items" in tablas
