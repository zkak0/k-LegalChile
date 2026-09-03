"""Tests offline de pjud_juris: normalización y manejo honesto de fallos."""
import sys, types

import pytest

from chilean_legal_mcp import pjud_juris
from chilean_legal_mcp.pjud_juris import _normalizar, buscar_sentencias_pjud, PJUDNoDisponible

DOC_SOLR = {
    "gls_sala_sup_s": "PRIMERA, CIVIL",
    "gls_corte_s": "C.A. de Santiago",
    "rol_era_sup_s": "35796-2026",
    "era_sup_i": 2026,
    "fec_sentencia_sup_dt": "2026-07-10T00:00:00Z",
    "caratulado_s": "CONSTRUCTORA GTECH SPA/VIAL DE AMEST ANIBAL",
    "gls_tip_recurso_sup_s": "(CIVIL) CASACIÓN FONDO",
    "resultado_recurso_sup_s": "ACOGE RECURSO DE NULIDAD (M)",
    "texto_sentencia": "Santiago, diez de julio...",
    "url_acceso_sentencia": "https://juris.pjud.cl/busqueda/pagina_detalle_sentencia/?k=abc",
    "cita_bibliografica": "Cita legal completa.",
    "gls_juz_s": "TRIBUNAL X",
}


def test_normalizar_campos_clave():
    d = _normalizar(DOC_SOLR)
    assert d["rol"] == "35796-2026"
    assert d["fecha"] == "2026-07-10"
    assert d["tribunal"] == "C.A. de Santiago"
    assert d["sala"] == "PRIMERA, CIVIL"
    assert "GTECH" in d["caratulado"]
    assert d["texto"].startswith("Santiago")
    assert d["url"].startswith("https://juris.pjud.cl")
    assert d["cita"]


def test_normalizar_con_campos_faltantes_no_rompe():
    d = _normalizar({})
    assert d["rol"] == "" and d["texto"] == "" and d["url"] == ""


def test_buscar_sentencias_reinicia_sesion_ante_sesion_caducada(monkeypatch):
    class FakePage:
        def __init__(self): self.n = 0
        def evaluate(self, *a):
            self.n += 1
            raise pjud_juris._SesionCaducada(401)
    monkeypatch.setattr(pjud_juris._SesionPJUD, "page", classmethod(lambda cls: FakePage()))
    reinicios = []
    monkeypatch.setattr(pjud_juris._SesionPJUD, "reiniciar",
                        classmethod(lambda cls: reinicios.append(1)))
    with pytest.raises(PJUDNoDisponible):
        buscar_sentencias_pjud("x", limite=1)
    assert len(reinicios) == 3  # 3 intentos, 3 reinicios


def test_buscar_sentencias_devuelve_docs_y_numfound(monkeypatch):
    payload = {"response": {"numFound": 2, "docs": [DOC_SOLR, DOC_SOLR]}}
    class FakePage:
        def evaluate(self, js, args=None):
            if args is None:
                return "token123"
            return {"json": payload}
    monkeypatch.setattr(pjud_juris._SesionPJUD, "page", classmethod(lambda cls: FakePage()))
    docs, total = buscar_sentencias_pjud("arbitro", limite=2)
    assert total == 2
    assert len(docs) == 2
    assert docs[0]["rol"] == "35796-2026"
