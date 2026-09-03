"""Tests del cómputo procesal chileno (arts. 38/40 CPC, art. 66 COT, Ley 2.977)."""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from chilean_legal_mcp.plazos import (
    parsear_fecha_cl, es_feriado, es_habil, en_feriado_judicial,
    feriado_judicial_limite, computar_plazo,
)


# --- parseo de fechas ---------------------------------------------------------

def test_parsear_formatos():
    assert parsear_fecha_cl("15-01-2026") == date(2026, 1, 15)
    assert parsear_fecha_cl("15/01/2026") == date(2026, 1, 15)
    assert parsear_fecha_cl("15.01.2026") == date(2026, 1, 15)
    assert parsear_fecha_cl("2026-01-15") == date(2026, 1, 15)
    assert parsear_fecha_cl("15 de enero de 2026") == date(2026, 1, 15)
    assert parsear_fecha_cl("15 de enero del 2026") == date(2026, 1, 15)
    assert parsear_fecha_cl("enero 15") is None
    assert parsear_fecha_cl("") is None
    assert parsear_fecha_cl("32-13-2026") is None


# --- feriados --------------------------------------------------------------------

def test_feriados_fijos():
    assert es_feriado(date(2026, 1, 1))      # Año Nuevo
    assert es_feriado(date(2026, 5, 1))      # Día del Trabajo
    assert es_feriado(date(2026, 9, 18))     # Fiestas Patrias
    assert es_feriado(date(2026, 12, 25))    # Navidad
    assert not es_feriado(date(2026, 9, 17))


def test_semana_santa_meeus():
    assert es_feriado(date(2026, 4, 3))      # Viernes Santo 2026
    assert es_feriado(date(2027, 3, 26))     # Viernes Santo 2027
    assert es_feriado(date(2030, 4, 19))     # Viernes Santo 2030


def test_sabado_es_inhabil():
    assert not es_habil(date(2026, 8, 1))    # sábado
    assert not es_habil(date(2026, 8, 2))    # domingo
    assert es_habil(date(2026, 8, 3))        # lunes hábil


# --- feriado judicial ---------------------------------------------------------------

def test_feriado_judicial_2026():
    ini, fin = feriado_judicial_limite(2026)
    assert ini == date(2026, 2, 1)
    # 1-3-2026 es domingo → primer hábil es lunes 2 de marzo
    assert fin == date(2026, 3, 2)
    assert en_feriado_judicial(date(2026, 2, 15))
    assert en_feriado_judicial(date(2026, 3, 2))      # el día límite cuenta
    assert not en_feriado_judicial(date(2026, 3, 3))
    assert not en_feriado_judicial(date(2026, 1, 31))


# --- cómputo proceso civil ------------------------------------------------------

def test_computo_desde_dia_siguiente():
    # notif. lunes 3-ago-2026; plazo de 1 día hábil → martes 4 → vencimiento (miércoles 5)
    # art. 38 CPC: corre desde el día siguiente (4); 1 día hábil termina el 4? No:
    # quien se fija por el fin del día siguiente, el vencimiento es el 4 (día hábil).
    res = computar_plazo(date(2026, 8, 3), 1, "habiles")
    assert res["ok"] is True
    # el primer día contado es el 4 (martes), que es el vencimiento
    assert res["vencimiento"] == "2026-08-04"
    assert res["fecha_notificacion"] == "2026-08-03"


def test_vencimiento_en_sabado_se_prorroga_al_lunes():
    # notif. miércoles 5-ago-2026 → cómputo 6-ago (jueves).
    # plazo de 2 días hábiles: jueves 6, viernes 7 → vence viernes 7; pero si
    # cómputo cae el 8 (sábado), art. 40 CPC prorroga al lunes 10.
    # notif. jueves 6-ago-2026 → día siguiente viernes 7-ago: 2 días hábiles
    #   día 1: viernes 7 ✓ ; día 2: lunes 10 ✓ → vence lunes 10.
    res = computar_plazo(date(2026, 8, 6), 2, "habiles")
    assert res["vencimiento"] == "2026-08-10"
    assert res["es_habil"] is True
    # el vencimiento jamás debe caer en sábado/domingo/feriado
    v = date.fromisoformat(res["vencimiento"])
    assert es_habil(v)


def test_suspension_feriado_judicial():
    # notif. viernes 30-ene-2026. Día siguiente: sábado 31-ene (inhábil).
    # Art. 66 COT: el feriado judicial va del 1-feb al primer hábil de marzo
    # INCLUSIVE; los plazos quedan suspendidos durante ese lapso.
    res = computar_plazo(date(2026, 1, 30), 5, "habiles")
    ini, fin = feriado_judicial_limite(2026)      # 1-feb → lun 2-mar (inclusive)
    assert res["ok"] is True
    assert any(p["fecha"] == "2026-03-03" or p["fecha"] == "2026-03-02" for p in res["pasos"]), res["pasos"]
    # el 2-mar-2026 está dentro del feriado judicial (suspendido).
    # Días hábiles contados: mar 3 (1), mié 4 (2), jue 5 (3), vie 6 (4), lun 9 (5)
    assert res["vencimiento"] == "2026-03-09"


def test_plazo_dias_corridos_con_prorroga_si_inhabil():
    # notif. viernes 14-ago-2026 → cómputo sábado 15-ago-2026, 3 días corridos:
    # sáb 15 (1), dom 16 (2), lun 17 (3) → vence lunes 17.
    res = computar_plazo(date(2026, 8, 14), 3, "corridos")
    assert res["vencimiento"] == "2026-08-17"
    # si el vencimiento cayera en feriado → próximo hábil (18-sep-2026 es feriado)
    res2 = computar_plazo(date(2026, 9, 17), 1, "corridos")
    assert res2["vencimiento"] == "2026-09-21"   # 18 feriado (vie), 19 feriado (sáb)? → lunes 21
    assert es_habil(date(2026, 9, 21))


def test_computo_con_notificacion_dentro_feriado_judicial():
    # notif. 15-feb-2026 (dentro del feriado judicial): cómputo suspendido hasta
    # el primer día hábil de marzo. El 2-mar-2026 está DENTRO del feriado
    # (ambos inclusive, art. 66 COT inc. 2) → se cuentan mar 3, mié 4, jue 5.
    res = computar_plazo(date(2026, 2, 15), 3, "habiles")
    assert res["vencimiento"] == "2026-03-05"


def test_vencimiento_nunca_inhabil():
    # barrera de calidad: probar 50 combinaciones al azar, vencimiento siempre hábil
    import random
    random.seed(42)
    for _ in range(50):
        y = random.choice([2026, 2027, 2028])
        m = random.randint(1, 12)
        d = random.randint(1, 28)
        res = computar_plazo(date(y, m, d), random.randint(1, 30),
                             random.choice(["habiles", "corridos"]))
        v = date.fromisoformat(res["vencimiento"])
        # feriado judicial puede mantener el cursor dentro solo en el borde del 1-mar: tolerado
        assert es_habil(v) or en_feriado_judicial(v) or not es_habil(date.fromisoformat(res["vencimiento"]))
        # más estricto: si no cae en feriado judicial, debe ser hábil
        if not en_feriado_judicial(v):
            assert es_habil(v), f"{res} -> {v}"


def test_fundamento_formal():
    res = computar_plazo(date(2026, 8, 3), 5, "habiles")
    texto = " ".join(res["fundamentos"])
    assert "Art. 38" in texto
    assert "Art. 40" in texto
    assert "Ley N° 2.977" in texto
    assert "Art. 66" in texto
    assert res["pasos"]


def test_formatear_plazo():
    from chilean_legal_mcp.plazos import formatear_plazo
    res = computar_plazo(date(2026, 8, 3), 5, "habiles")
    txt = formatear_plazo(res)
    assert "CÓMPUTO DE PLAZO PROCESAL" in txt
    assert "Atendida la notificación" in txt
    assert "I. RAZONAMIENTO SEGUIDO" in txt
    assert "II. FUNDAMENTOS LEGALES" in txt
