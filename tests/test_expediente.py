"""Tests del módulo de análisis de expedientes (indexar/preguntar/timeline/partes)."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest

import chilean_legal_mcp.expediente as exp


@pytest.fixture()
def db_tmp(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        import chilean_legal_mcp.db as db_mod
        instancia = db_mod.NormasDB(db_path)
        monkeypatch.setattr(db_mod, "_db_singleton", instancia)
        yield instancia
        instancia.close()


@pytest.fixture()
def carpeta_caso():
    """Carpeta temporal con un TXT y un DOCX simulando un expediente real."""
    from docx import Document
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "resolucion_482.txt").write_text(
            "RESOLUCIÓN N° 482/26. Viña del Mar, 10 de agosto de 2026. "
            "Se destituye a Rocío Maffet Estay, RUT 17.161.063-K, por incumplimiento "
            "grave de sus obligaciones. Notificada el 11-08-2026. "
            "El sumario fue instruido por Resolución N° 427/25 del 04-08-2025.",
            encoding="utf-8")
        doc = Document()
        doc.add_paragraph(
            "VISTA FISCAL N°10/2026 de fecha 03-08-2026. El fiscal concluye que "
            "los hechos cometidos por doña Maffet Estay constituyen falta grave. "
            "La funcionaria prestó declaración el 02/09/2025.")
        doc.save(base / "vista_fiscal.docx")
        (base / "imagen_escaneada.txt").write_text("   \n", encoding="utf-8")  # sin texto
        yield str(base)


# --- indexación ----------------------------------------------------------------

def test_indexar_carpeta_completa(db_tmp, carpeta_caso):
    res = exp.indexar_carpeta("caso_demo", carpeta_caso)
    assert res["ok"] is True
    assert res["num_documentos"] == 2          # txt + docx (el vacío va a errores)
    tipos = {d.split(".")[-1] for d in res["documentos_indexados"]}
    assert "txt" in tipos and "docx" in tipos
    assert len(res["errores"]) == 1            # imagen escaneada sin texto


def test_indexar_carpeta_inexistente(db_tmp):
    res = exp.indexar_carpeta("x", "/ruta/que/no/existe/xyz")
    assert res["ok"] is False
    assert "no existe" in res["error"].lower()


def test_reemplazar_expediente_existente(db_tmp, carpeta_caso):
    exp.indexar_carpeter = None  # noop para lint
    r1 = exp.indexar_carpeta("caso", carpeta_caso)
    assert r1["ok"] is True
    r2 = exp.indexar_carpeta("caso", carpeta_caso, reemplazar=True)
    assert r2["ok"] is True
    lista = exp.listar_expedientes()
    assert len(lista) == 1                     # no duplica


def test_listar_y_eliminar(db_tmp, carpeta_caso):
    exp.indexar_carpeta("caso_del", carpeta_caso)
    lista = exp.listar_expedientes()
    assert lista[0]["nombre"] == "caso_del"
    assert lista[0]["num_documentos"] == 2
    res = exp.eliminar_expediente("caso_del")
    assert res["ok"] is True
    assert exp.listar_expedientes() == []


# --- consulta -------------------------------------------------------------------

def test_preguntar_encuentra_fragmento_con_fuente(db_tmp, carpeta_caso):
    exp.indexar_carpeta("caso_q", carpeta_caso)
    res = exp.preguntar("caso_q", "destitución Maffet")
    assert res["ok"] is True
    assert len(res["coincidencias"]) >= 1
    hit = res["coincidencias"][0]
    assert hit["documento"]                    # cita al documento fuente
    assert len(hit["fragmento"]) > 20
    assert "Maffet" in hit["fragmento"] or "destitu" in hit["fragmento"].lower()


def test_preguntar_sin_coincidencias_es_honesto(db_tmp, carpeta_caso):
    exp.indexar_carpeta("caso_v", carpeta_caso)
    res = exp.preguntar("caso_v", "zzzqqqxxx")
    assert res["ok"] is True
    assert res["coincidencias"] == []


def test_preguntar_expediente_inexistente(db_tmp):
    res = exp.preguntar("fantasma", "pregunta")
    assert res["ok"] is False


# --- timeline ---------------------------------------------------------------------

def test_timeline_ordena_cronologicamente(db_tmp, carpeta_caso):
    exp.indexar_carpeta("caso_t", carpeta_caso)
    res = exp.timeline("caso_t")
    assert res["ok"] is True
    fechas = [e["fecha"] for e in res["eventos"]]
    assert fechas == sorted(fechas)
    # el evento más antiguo es la instrucción del sumario (Resolución 427/25, 04-08-2025)
    assert fechas[0] == "2025-08-04"
    # formato chileno presente
    assert any(e["fecha_cl"] == "10-08-2026" for e in res["eventos"])
    # detecta también '10 de agosto de 2026' (palabras) sin duplicar
    assert fechas.count("2026-08-10") == 1


# --- partes ------------------------------------------------------------------------

def test_partes_detecta_rut_y_nombres(db_tmp, carpeta_caso):
    exp.indexar_carpeta("caso_p", carpeta_caso)
    res = exp.partes("caso_p")
    assert res["ok"] is True
    ruts = {r["rut"] for r in res["ruts"]}
    assert "17.161.063-K" in ruts
    assert any(n["apariciones"] >= 1 for n in res["nombres_frecuentes"])
    assert "CANDIDATOS" in res["nota"]         # honestidad sobre límites


# --- formato narrativo --------------------------------------------------------------

def test_formateadores_narrativos(db_tmp, carpeta_caso):
    idx = exp.indexar_carpeta("fmt", carpeta_caso)
    txt_idx = exp.formatear_indexacion(idx)
    assert "EXPEDIENTE INDEXADO" in txt_idx
    assert "https://" not in txt_idx           # sin links inventados

    resp = exp.preguntar("fmt", "sumario instruido")
    txt_resp = exp.formatear_respuesta(resp)
    assert "RESPUESTA DESDE EL EXPEDIENTE" in txt_resp
    assert "«" in txt_resp                     # documento citado

    tl = exp.timeline("fmt")
    txt_tl = exp.formatear_timeline(tl)
    assert "LÍNEA DE TIEMPO" in txt_tl
    assert "—— AÑO" in txt_tl

    pt = exp.partes("fmt")
    txt_pt = exp.formatear_partes(pt)
    assert "PARTES DEL EXPEDIENTE" in txt_pt

    txt_lista = exp.formatear_listado([])
    assert "No tienes expedientes" in txt_lista


# --- OCR degradado honesto (B7) -------------------------------------------------

def test_pdf_vacio_sin_motor_ocr_mensaje_util(db_tmp, monkeypatch):
    """PDF sin texto + sin herramienta OCR → mensaje que explica cómo instalarla."""
    monkeypatch.setattr(exp, "_ocr_disponible", lambda: None)
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        from pypdf import PdfWriter
        PdfWriter().write(base / "hoja_escaneada.pdf")   # 0 páginas, sin texto
        res = exp.indexar_carpeta("caso_ocr", str(base))
        assert res["num_documentos"] == 0
        assert res["errores"][0]["archivo"] == "hoja_escaneada.pdf"
        assert "ocrmypdf" in res["errores"][0]["problema"]


def test_pdf_vacio_con_ocr_fallido_no_inventa(db_tmp, monkeypatch):
    """Si el OCR no produce texto, se informa sin maquillar."""
    monkeypatch.setattr(exp, "_ocr_disponible", lambda: "ocrmypdf")
    monkeypatch.setattr(exp, "_ocr_pdf", lambda ruta: None)
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        from pypdf import PdfWriter
        PdfWriter().write(base / "hoja_rara.pdf")
        res = exp.indexar_carpeta("caso_ocr2", str(base))
        assert "tras intento de OCR" in res["errores"][0]["problema"]


def test_ocr_exitoso_indexa_como_pdf_ocr(db_tmp, monkeypatch):
    monkeypatch.setattr(exp, "_ocr_disponible", lambda: "ocrmypdf")
    monkeypatch.setattr(exp, "_ocr_pdf", lambda ruta: "SENTENCIA. Santiago, quince de mayo de 2024. Resuelve.")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        from pypdf import PdfWriter
        PdfWriter().write(base / "resolucion_escaneada.pdf")
        res = exp.indexar_carpeta("caso_ocr3", str(base))
        assert res["num_documentos"] == 1
        assert not res["errores"]


def test_schema_tablas_existen(db_tmp):
    tablas = {r[0] for r in db_tmp._conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "expedientes" in tablas
    assert "expediente_docs" in tablas
