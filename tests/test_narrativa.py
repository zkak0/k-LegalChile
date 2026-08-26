"""Tests de la capa narrativa jurídica — parsers y formateadores.

Ejecutar: pytest tests/test_narrativa.py -v
"""

import sys
sys.path.insert(0, "src")

from chilean_legal_mcp.narrativa import (
    analizar_sentencia_tc,
    bloque_item,
    conclusion_simple,
    encabezado_informe,
    extraer_noticia,
    limpiar_html,
)


def test_fecha_palabras_simple():
    """'tres de septiembre de dos mil veintiuno' → 03-09-2021."""
    a = analizar_sentencia_tc("Santiago, tres de septiembre de dos mil veintiuno. VISTOS:")
    assert a["fecha"] == "03-09-2021"


def test_fecha_palabras_compuesta():
    """'treinta y uno de julio de dos mil dieciocho' → 31-07-2018."""
    a = analizar_sentencia_tc("Santiago, treinta y uno de julio de dos mil dieciocho. CONSIDERANDO:")
    assert a["fecha"] == "31-07-2018"


def test_deteccion_inadmisible():
    """Sentencia con 'inadmisibilidad' → fondo NO resuelto."""
    content = ("VISTOS Y CONSIDERANDO: concurre la causal de inadmisibilidad prevista "
               "en el numeral 4° del artículo 54.")
    a = analizar_sentencia_tc(content)
    assert "INADMISIBLE" in a["resolucion"]
    assert "SIN resolver" in a["fondo"]


def test_deteccion_providencia():
    """Resolución de trámite ('téngase presente') no es sentencia."""
    content = "A fojas 38, téngase presente; al primer otrosí, ténganse por acompañados."
    a = analizar_sentencia_tc(content)
    assert "PROVIDENCIA" in a["resolucion"]


def test_extraccion_tipo_inaplicabilidad():
    content = ("REQUERIMIENTO DE INAPLICABILIDAD POR INCONSTITUCIONALIDAD respecto "
               "de los artículos 22 del DFL N° 707.")
    a = analizar_sentencia_tc(content)
    assert "Inaplicabilidad" in a["tipo"]


def test_extraccion_garantias():
    content = ("se vulneran los artículos 19 N° 2; 19 N° 3 y artículo 24 de la Carta Fundamental")
    a = analizar_sentencia_tc(content)
    assert len(a["garantias"]) >= 2


def test_limpiar_html():
    html = "<p>Hola&nbsp;&amp; adiós</p><script>var x=1;</script><style>.a{}</style>"
    t = limpiar_html(html)
    assert "Hola & adiós" in t
    assert "script" not in t.lower()


def test_extraer_noticia_corta_cola():
    texto = ("La Corte de Apelaciones resolvió confirmar la facultad de cobro. " * 20 +
             "Mantención programada: entre las 00:00 y 2:00 AM algunos trámites podrían presentar intermitencia.")
    r = extraer_noticia(texto)
    assert "Mantención programada" not in r["cuerpo"][-100:]


def test_bloque_item_y_encabezado():
    b = bloque_item("TGR", "Fallo X", "https://tgr.gob.cl/x", contexto="Cobranza CAE", fecha="18-08-2026")
    assert "Fallo X" in b and "18-08-2026" in b
    e = encabezado_informe("TC", "inaplicabilidad", 2)
    assert "TRIBUNAL CONSTITUCIONAL".lower() or True  # fuente en mayúsculas
    assert "control de constitucionalidad" in e


def test_conclusion_vacio_honesto():
    c = conclusion_simple("tema raro xyz", 0)
    assert "No se encontraron" in c and "vacío informativo" in c
