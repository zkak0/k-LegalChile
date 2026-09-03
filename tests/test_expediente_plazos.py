"""Tests de detección y cómputo de plazos procesales dentro del expediente (B6)."""

import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest

import chilean_legal_mcp.expediente as exp
from chilean_legal_mcp.plazos import es_habil


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
def carpeta_plazos():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "auto_645.txt").write_text(
            "AUTO N° 645. Santiago, lunes 03 de agosto de 2026. Notificada la demanda "
            "el lunes 03-08-2026. Con este mérito, corremos traslado de la demanda por "
            "el plazo de 15 días. Además, dentro del sexto día deberá acompañar la "
            "documentación pertinente. El término de 30 días corridos regula el plazo "
            "de embargo. Notificado por estado diario el 03-08-2026.",
            encoding="utf-8")
        yield str(base)


def test_detecta_plazos_clasicos(db_tmp, carpeta_plazos):
    exp.indexar_carpeta("caso_plazos", carpeta_plazos)
    res = exp.plazos_expediente("caso_plazos")
    assert res["ok"] is True
    dias_detectados = {p["dias"] for p in res["plazos"]}
    assert 15 in dias_detectados
    assert 6 in dias_detectados                 # "dentro del sexto día"
    assert 30 in dias_detectados                # "término de 30 días corridos"
    corridos = [p for p in res["plazos"] if p["dias"] == 30][0]
    assert corridos["tipo"] == "corridos"


def test_computo_vencimiento_con_art_38_y_40(db_tmp, carpeta_plazos):
    exp.indexar_carpeta("caso_plazos2", carpeta_plazos)
    res = exp.plazos_expediente("caso_plazos2")
    p15 = next(p for p in res["plazos"] if p["dias"] == 15)
    # Fecha de referencia: 03-08-2026 (lunes trip). Cómputo art. 38 CPC: desde
    # martes 04-08-2026; 15 días hábiles (sin sábados ni domingos ni feriados):
    # 4,5,6,7,10,11,12,13,14,17,18,19,20,21,24 → vence 24-08-2026.
    assert p15["fecha_referencia"] == "2026-08-03"
    assert p15["vencimiento"] == "2026-08-24"
    v = date.fromisoformat(p15["vencimiento"])
    assert es_habil(v)
    assert p15["estado"] == "vencido"      # hoy es 2026-08-30, posterior al vencimiento


def test_estado_frente_a_hoy(db_tmp, carpeta_plazos):
    """El estado debe calcularse respecto de la FECHA REAL de hoy, no de una
    fecha hardcodeada: un plazo de 15 días hábiles desde 03-08-2026 vencía
    24-08-2026 y un plazo de 30 días corridos desde 04-08-2026 vence
    02-09-2026."""
    exp.indexar_carpeta("caso_plazos3", carpeta_plazos)
    res = exp.plazos_expediente("caso_plazos3")
    hoy = date.fromisoformat(res["hoy"])
    assert res["hoy"] == date.today().isoformat()

    def _estado_esperado(vencimiento: str) -> str:
        v = date.fromisoformat(vencimiento)
        delta = (v - hoy).days
        if delta < 0:
            return "vencido"
        return "vence en" if delta > 0 else "vence hoy"

    p15 = next(p for p in res["plazos"] if p["dias"] == 15)
    assert p15["vencimiento"] == "2026-08-24"
    # el estado reportado debe ser coherente con el cálculo relativo a hoy
    assert (p15["estado"] == _estado_esperado(p15["vencimiento"])
            or p15["estado"].startswith(_estado_esperado(p15["vencimiento"])))

    p30 = next(p for p in res["plazos"] if p["dias"] == 30)
    assert p30["vencimiento"] == "2026-09-02"
    assert (p30["estado"] == _estado_esperado(p30["vencimiento"])
            or p30["estado"].startswith(_estado_esperado(p30["vencimiento"])))


def test_plazo_sin_fecha_de_referencia_honesto(db_tmp):
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "texto.txt").write_text(
            "El escrito deberá presentarse dentro del plazo de 10 días hábiles.",
            encoding="utf-8")
        exp.indexar_carpeta("caso_sin_fecha", str(base))
        res = exp.plazos_expediente("caso_sin_fecha")
        assert res["plazos"][0]["estado"] == "sin fecha de referencia en el documento"
        assert "vencimiento" not in res["plazos"][0]


def test_expediente_inexistente(db_tmp):
    res = exp.plazos_expediente("fantasma")
    assert res["ok"] is False


def test_formateo_formal_y_urgencia(db_tmp, carpeta_plazos):
    exp.indexar_carpeta("caso_fmt_plazos", carpeta_plazos)
    txt = exp.formatear_plazos_expediente(exp.plazos_expediente("caso_fmt_plazos"))
    assert "PLAZOS DETECTADOS EN EL EXPEDIENTE" in txt
    assert "Atendido el examen documental" in txt
    assert "dentro del sexto día" in txt
    assert "Vence: 24-08-2026" in txt
    assert "vencido" in txt
    assert "arts. 38/40 CPC" in txt or "art. 38" in txt.lower()
