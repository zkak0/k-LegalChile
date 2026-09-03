"""Tests offline de extracción de citas normativas y corte forense de articulado."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest

from chilean_legal_mcp.citas import extraer_citas, extraer_articulo
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


# --- extracción plana ---------------------------------------------------------

def test_articulo_cuerpo_completo():
    citas = extraer_citas("conforme al artículo 148 del Código Civil")
    assert len(citas) == 1
    c = citas[0]
    assert c["tipo"] == "articulo"
    assert c["cuerpo"] == "Código Civil"
    assert c["articulos"] == ["148"]
    assert c["inciso"] is None


def test_lista_articulos():
    citas = extraer_citas("los arts. 1705 y 1712 del Código Civil disponen que")
    arts = [a for c in citas if c["cuerpo"] == "Código Civil" for a in c["articulos"]]
    assert arts == ["1705", "1712"]


def test_articulo_con_inciso_palabra_y_numero():
    citas = extraer_citas("el artículo 148, inciso primero, del Código Civil "
                          "y el artículo 19, inciso 3°, de la Constitución")
    c148 = next(c for c in citas if "148" in c["articulos"])
    c19 = next(c for c in citas if "19" in c["articulos"])
    assert c148["inciso"] == "1"
    assert c19["inciso"] == "3"


def test_articulo_abreviatura_del_y_directa():
    citas = extraer_citas("el art. 1 del CPC y el art. 64 CPC y el art. 8 COT")
    cuerpos = [c["cuerpo"] for c in citas]
    assert "Código de Procedimiento Civil" in cuerpos
    assert "Código Orgánico de Tribunales" in cuerpos
    assert len(citas) == 3


def test_constitucion_con_numero_garantia():
    citas = extraer_citas(
        "el artículo 19, N° 24, inciso primero, de la Constitución Política de la República")
    assert len(citas) == 1
    c = citas[0]
    assert c["cuerpo"] == "Constitución Política de la República"
    assert c["articulos"] == ["19"]
    assert c["numero_garantia"] == "24"
    assert c["inciso"] == "1"


def test_ley_numerada_y_articulo_de_ley():
    citas = extraer_citas("la Ley N° 19.966; también el artículo 24 de la Ley 19.966")
    norma = next(c for c in citas if c["tipo"] == "norma")
    art = next(c for c in citas if c["tipo"] == "articulo")
    assert norma["clase"] == "ley"
    assert norma["numero"] == "19.966"
    assert art["cuerpo"] == "Ley 19.966"
    assert art["articulos"] == ["24"]
    # la Ley citada dentro de la cita de artículo no se duplica
    assert len(citas) == 2


def test_decreto_supremo_y_dfl():
    citas = extraer_citas("DFL N° 1 de 2005; Decreto Supremo 47, de 2020; D.S. 90/1996")
    clases = {c["clase"] for c in citas}
    assert "decreto con fuerza de ley" in clases
    assert "decreto supremo" in clases
    dfl = next(c for c in citas if c["numero"] == "1")
    ds = next(c for c in citas if c["numero"] == "47")
    assert dfl["anno"] == "2005"
    assert ds["anno"] == "2020"
    slash = next(c for c in citas if c["numero"] == "90")
    assert slash["anno"] == "1996"


def test_sin_citas_no_inventa():
    assert extraer_citas("La parte empleadora despidió al trabajador sin causa.") == []
    assert extraer_citas("") == []


def test_false_positivos_minimos():
    # "ley" en sentido genérico sin número no debe capturar
    assert extraer_citas("según lo que dispone la ley procesal en general") == []


def test_articulo_transitorio_hereda_cuerpo():
    citas = extraer_citas(
        "Según lo dispuesto en la Ley N° 20.000, el artículo primero transitorio "
        "estableció un plazo especial.")
    trans = next((c for c in citas if c.get("transitorio")), None)
    assert trans is not None
    assert trans["articulos"] == ["1"]
    assert trans["cuerpo"] is None or "20.000" in (trans["cuerpo"] or "")


def test_articulo_transitorio_no_es_inciso():
    # "transitorio" jamás debe salir como inciso
    citas = extraer_citas("el artículo 148, inciso transitorio, del Código Civil")
    for c in citas:
        assert c["inciso"] not in ("transitorio",)


def test_correferencia_se_ancla_a_la_cita_previa():
    citas = extraer_citas(
        "El artículo 148 del Código Civil concede la acción. "
        "El artículo antes citado exige la concurrencia de incumplimiento.")
    corr = next((c for c in citas if c.get("correferencia_de")), None)
    assert corr is not None
    assert corr["cuerpo"] == "Código Civil"
    assert corr["articulos"] == ["148"]
    assert corr["correferencia_de"] == "artículo 148 del Código Civil"


def test_correferencia_sin_ancla_honesta_no_inventa():
    citas = extraer_citas("El artículo antes citado se aplica aquí.")
    assert all("correferencia_de" not in c for c in citas)


def test_dicho_articulo_tambien_es_correferencia():
    citas = extraer_citas(
        "el art. 64 CPC es procedente; dicho artículo regula las excepciones.")
    corr = next((c for c in citas if c.get("correferencia_de")), None)
    assert corr is not None
    assert corr["cuerpo"] == "Código de Procedimiento Civil"


# --- corte forense de articulado ---------------------------------------------------

TEXTO_FICTICIO = (
    "CODIGO FICTICIO\n\n"
    "Artículo 1°. Disposición general.\n\n"
    "Artículo 2°. La acción procede cuando concurren estos requisitos:\n"
    "Inciso primero. Que exista incumplimiento.\n"
    "Inciso segundo. Que el incumplimiento sea imputable.\n"
    "Inciso 3°. Que no medie excusa legal.\n\n"
    "Artículo 20. Contenido del veinte, no confundir con el 2°.\n"
    "Inciso primero. Párrafo inicial del veinte.\n\n"
    "Artículo 21. Contenido del veintiuno.\n"
)


def test_extraer_articulo_no_confunde_ordinal():
    r = extraer_articulo(TEXTO_FICTICIO, "2")
    assert r["ok"] is True
    assert "requisitos" in r["texto_articulo"]
    assert "veinte" not in r["texto_articulo"]          # 2 ≠ 20
    assert {i["inciso"] for i in r["incisos"]} == {"1", "2", "3"}


def test_extraer_articulo_20_sin_ordinal_biblico():
    r = extraer_articulo(TEXTO_FICTICIO, "20")
    assert r["ok"] is True
    assert "veinte" in r["texto_articulo"]
    assert "veintiuno" not in r["texto_articulo"]


def test_extraer_inciso_especifico():
    r = extraer_articulo(TEXTO_FICTICIO, "2", inciso="segundo")
    assert r["ok"] is True
    assert r["texto_inciso"] == "Que el incumplimiento sea imputable."


def test_inciso_inexistente_advierte_honestamente():
    r = extraer_articulo(TEXTO_FICTICIO, "2", inciso="quinto")
    assert r["ok"] is True
    assert "advertencia" in r
    assert "no contiene" in r["advertencia"]


def test_articulo_inexistente():
    r = extraer_articulo(TEXTO_FICTICIO, "99")
    assert r["ok"] is False
    assert "99" in r["error"]


# --- integración con expediente -------------------------------------------------

@pytest.fixture()
def carpeta_caso():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "demanda.txt").write_text(
            "DEMANDA CIVIL. En derecho: el artículo 148 del Código Civil y los "
            "arts. 1705 y 1712 del mismo Código Civil. Invoca además el artículo 19, "
            "N° 24, inciso primero, de la Constitución Política de la República y la "
            "Ley N° 19.966. El art. 64 CPC sustenta el procedimiento.",
            encoding="utf-8")
        (base / "contestacion.txt").write_text(
            "CONTESTACIÓN. El artículo 148, inciso primero, del Código Civil es "
            "inaplicable al caso.",
            encoding="utf-8")
        yield str(base)


def test_citas_normativas_del_expediente(db_tmp, carpeta_caso):
    exp.indexar_carpeta("caso_citas", carpeta_caso)
    res = exp.citas_normativas("caso_citas")
    assert res["ok"] is True
    assert res["total_citas"] >= 4
    referentes = {n["referente"] for n in res["normas_invocadas"]}
    assert "Código Civil" in referentes
    assert "Constitución Política de la República" in referentes
    assert any(n["articulos_citados"] == ["148", "1705", "1712"]
               for n in res["normas_invocadas"])
    # cada norma lleva su sello honesto
    for n in res["normas_invocadas"]:
        assert n["verificacion"]["estado"] in ("verificada_local", "por_verificar")
    # la cita ubica su documento de origen
    algs = [c for c in res["citas"] if "148" in c["articulos"]]
    assert {c["documento"] for c in algs} == {"demanda", "contestacion"}


def test_citas_verificacion_contra_base_local(db_tmp, carpeta_caso):
    # si la norma está indexada en la base nacional local → verificada_local
    db_tmp._conn.execute(
        "INSERT INTO normas (uri, titulo, numero, leychile_id, tipo) VALUES (?,?,?,?,?)",
        ("x:cc", "CODIGO CIVIL", "24527", "172986", "Ley"))
    db_tmp._conn.commit()
    exp.indexar_carpeta("caso_ver", carpeta_caso)
    res = exp.citas_normativas("caso_ver")
    cc = next(n for n in res["normas_invocadas"] if n["referente"] == "Código Civil")
    assert cc["verificacion"]["estado"] == "verificada_local"
    assert cc["verificacion"]["leychile_id"] == "172986"
    cpr = next(n for n in res["normas_invocadas"]
               if n["referente"] == "Constitución Política de la República")
    assert cpr["verificacion"]["estado"] == "por_verificar"   # no está en base local


# --- vigencia de citas (A1) -------------------------------------------------------

def test_vigencia_citas_cruza_con_estado(db_tmp, carpeta_caso, monkeypatch):
    db_tmp._conn.execute(
        "INSERT INTO normas (uri, titulo, numero, leychile_id, tipo) VALUES (?,?,?,?,?)",
        ("x:cc", "CODIGO CIVIL", "24527", "172986", "Ley"))
    db_tmp._conn.commit()
    exp.indexar_carpeta("caso_vig", carpeta_caso)

    from chilean_legal_mcp import vigencia as vig_mod

    consultados = []

    def _estado_fake(identificador):
        consultados.append(identificador)
        if identificador == "172986":
            return {"estado": "VIGENTE", "ultima_modificacion": "01-03-2022",
                    "url_oficial": f"https://www.bcn.cl/leychile/navegar?idNorma={identificador}"}
        return {"estado": "VIGENTE"}

    monkeypatch.setattr(vig_mod, "estado_vigencia", _estado_fake)
    res = exp.vigencia_citas("caso_vig")
    assert res["ok"] is True
    assert res["total_normas_invocadas"] >= 3
    cc = next(n for n in res["vigencias"] if n["referente"] == "Código Civil")
    assert cc["vigencia"]["estado"] == "VIGENTE"
    assert consultados                      # se consultó por la vía canonica
    # las no verificadas en base local se reportan sin romper
    cpr = next(n for n in res["vigencias"]
               if n["referente"] == "Constitución Política de la República")
    assert cpr["vigencia"]["estado"] == "no_verificable"


def test_vigencia_citas_expediente_inexistente(db_tmp):
    res = exp.vigencia_citas("fantasma")
    assert res["ok"] is False


def test_formatear_vigencias_lenguaje_formal(db_tmp, carpeta_caso, monkeypatch):
    db_tmp._conn.execute(
        "INSERT INTO normas (uri, titulo, numero, leychile_id, tipo) VALUES (?,?,?,?,?)",
        ("x:cc", "CODIGO CIVIL", "24527", "172986", "Ley"))
    db_tmp._conn.commit()
    exp.indexar_carpeta("caso_vigf", carpeta_caso)
    from chilean_legal_mcp import vigencia as vig_mod
    monkeypatch.setattr(vig_mod, "estado_vigencia",
                        lambda i: {"estado": "DEROGADA", "derogada_por": "Ley 21.000"})
    txt = exp.formatear_vigencias(exp.vigencia_citas("caso_vigf"))
    assert "VIGENCIA DE LAS NORMAS INVOCADAS" in txt
    assert "Atendido lo anterior" in txt
    assert "[⚠ DEROGADA]" in txt
    assert "intertemporalidad" in txt.lower()


def test_formatear_citas_lenguaje_formal(db_tmp, carpeta_caso):
    exp.indexar_carpeta("caso_fmt", carpeta_caso)
    txt = exp.formatear_citas(exp.citas_normativas("caso_fmt"))
    assert "CITAS NORMATIVAS DEL EXPEDIENTE" in txt
    assert "Atendido el examen" in txt
    assert "I. NORMAS INVOCADAS" in txt
    assert "II. DETALLE DE LAS CITAS" in txt
    assert "«demanda»" in txt
    assert "obtener_articulo_texto" in txt      # sugiere el siguiente paso forense
