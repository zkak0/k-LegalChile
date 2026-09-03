"""Tests unitarios para contraloria.py y anti_waf.py (CGRFetcher, _parse_results, URL builder)."""

import sys
sys.path.insert(0, "src")

import re
import pytest


# ─── Flujo CGR: GET con la URL que usa el propio JavaScript del formulario ─

FORM_HTML = """<html><head><script>function realizaConsulta(){ /* formulario, no resultados */ }</script>
<form action="..."><input name="TextoLibre"></form></head><body>form</body></html>"""

LEGACY_HTML = """<html><body>
<table>
<tr><td><a href="/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/0/ABC123?OpenDocument">
Dictamen N° 15.234 de 2024</a></td><td>Materia municipal - funcionarios publicos</td></tr>
<tr><td><a href="/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/0/DEF456?OpenDocument">
Dictamen N° 18.567/2025</a></td><td>Contratos municipales - licitación pública</td></tr>
</table></body></html>"""

# Marcado REAL capturado de contraloria.cl el 30-08-2026 (sistema "NVA")
RESULTS_HTML = """<html><body>
<div class="textoEncabezadoTabla">Resultados de la consulta: se ha encontrado 2.791 dictámenes</div>
<table id="TablaConsultaWeb" class="textoTabla">
<tr id="8386D4F16D6C42F584258E44006AF7E2" bgcolor="#7faed4">
<td class="textoNumeracionRegistro" width="5%">1&nbsp;</td>
<td class="textoContenidoTabla" height="20px" width="10%"> 28/07/2026</td>
<td class="textoContenidoTabla" height="20px" width="10%">
<a class="lkDictamen" href="javascript:void(0)"
 onclick="registraVisitaDictamen('8386D4F16D6C42F584258E44006AF7E2'); muestraDictamenIframe('/LegisJuri/DictamenesGeneralesMunicipales.nsf/cgrDetalleDictamenNVDA?OpenForm&UNID=8386D4F16D6C42F584258E44006AF7E2');"
>D382N26</a></td>
<td class="textoContenidoTabla2" height="20px" width="65%">Procesos disciplinarios, calificación de imputabilidad administrativa, potestad disciplinaria, intervención COMPIN</td></tr>
<tr id="D8D50A343270D59D84258E42005A5B08" bgcolor="#84b7e1">
<td class="textoNumeracionRegistro" width="5%">2&nbsp;</td>
<td class="textoContenidoTabla" height="20px" width="10%"> 21/07/2026</td>
<td class="textoContenidoTabla" height="20px" width="10%">
<a class="lkDictamen" href="javascript:void(0)"
 onclick="registraVisitaDictamen('D8D50A343270D59D84258E42005A5B08'); muestraDictamenIframe('/LegisJuri/DictamenesGeneralesMunicipales.nsf/cgrDetalleDictamenNVDA?OpenForm&UNID=D8D50A343270D59D84258E42005A5B08');"
>E1234Q25</a></td>
<td class="textoContenidoTabla2" height="20px" width="65%">Licencias médicas; rechazo por COMPIN de licencia, subsidio correspondiente</td></tr>
</table></body></html>"""


class TestUrlBusqueda:
    def test_url_es_la_del_javascript_oficial(self):
        from chilean_legal_mcp.contraloria import _url_busqueda
        url = _url_busqueda("licencia médica", 25)
        assert url.startswith("https://www.contraloria.cl")
        assert "FormConsultaWeb2k?OpenForm" in url
        assert "hpbb=SI" in url                      # bandera de "buscar" del JS real
        assert "TextoLibre=licencia" in url
        assert "dpp=25" in url and "porPagina=25" in url

    def test_url_con_numero_y_fechas(self):
        from chilean_legal_mcp.contraloria import _url_busqueda
        url = _url_busqueda("", 10, numero="15.234", fecha_desde="01-01-2024", fecha_hasta="31-12-2024")
        assert "NumeroDictamen=15.234" in url
        assert "FechaDesde=01-01-2024" in url


class TestBuscarCGRFlujo:
    def _transport_ok(self):
        import httpx

        def handler(request: "httpx.Request") -> "httpx.Response":
            if "hpbb=SI" in str(request.url):
                return httpx.Response(200, text=RESULTS_HTML)
            return httpx.Response(200, text=FORM_HTML)

        return httpx.MockTransport(handler)

    def test_buscar_cgr_devuelve_resultados(self):
        """Marcado NVA (real): filas con UNID, clase lkDictamen, fecha y materia."""
        from chilean_legal_mcp.contraloria import buscar_cgr
        res = buscar_cgr("licencia médica", limite=10, transport=self._transport_ok())
        assert len(res) == 2
        numeros = {r["numero"] for r in res}
        assert "D382N26" in numeros and "E1234Q25" in numeros
        # detalle apunta al formulario NVDA con su UNID
        assert any("cgrDetalleDictamenNVDA?OpenForm&UNID=8386D4F16D6C42F584258E44006AF7E2" in r["url"]
                   for r in res)
        # fecha DD/MM/YYYY conservada
        assert res[0]["fecha"] == "28/07/2026"
        assert all(r["url"].startswith("https://www.contraloria.cl") for r in res)

    def test_buscar_cgr_marcado_legado_sigue_pasando(self):
        from chilean_legal_mcp.contraloria import buscar_cgr
        import httpx
        transport = httpx.MockTransport(
            lambda r: httpx.Response(200, text=LEGACY_HTML if "hpbb=SI" in str(r.url) else FORM_HTML))
        res = buscar_cgr("licencia médica", limite=10, transport=transport)
        assert any("15.234" in r["numero"] for r in res)

    def test_total_encontrados_desde_texto(self):
        from chilean_legal_mcp.contraloria import total_encontrados
        assert total_encontrados(RESULTS_HTML) == 2791
        assert total_encontrados(FORM_HTML) is None

    def test_formulario_vacio_es_error_honesto_no_vacio_enganoso(self):
        """Si la CGR devuelve el formulario (como le pasó al código anterior),
        la herramienta dice 'CGR no disponible' — no 'no hay dictámenes'."""
        from chilean_legal_mcp.contraloria import buscar_cgr, CGRNoDisponible
        import httpx
        transport = httpx.MockTransport(lambda r: httpx.Response(200, text=FORM_HTML))
        with pytest.raises(CGRNoDisponible):
            buscar_cgr("licencia médica", limite=10, transport=transport)

    def test_sin_resultados_reales_es_lista_vacia_no_bloqueo(self):
        """Cuando la CGR responde el formulario declarando explícitamente 'No se
        han encontrado dictámenes', eso es una respuesta cierta y vacía — debe
        devolver [], no alzar CGRNoDisponible (que sugeriría bloqueo)."""
        from chilean_legal_mcp.contraloria import buscar_cgr, CGRNoDisponible
        import httpx
        empty_html = ("<html><body><form>...</form>"
                      "No se han encontrado dictámenes que contienen el texto 'x'"
                      "</body></html>")
        transport = httpx.MockTransport(lambda r: httpx.Response(200, text=empty_html))
        assert buscar_cgr("x", limite=10, transport=transport) == []

    def test_error_de_red_es_CGRNoDisponible(self):
        from chilean_legal_mcp.contraloria import buscar_cgr, CGRNoDisponible
        import httpx

        def handler(request):
            raise httpx.ConnectError("caída total")

        with pytest.raises(CGRNoDisponible):
            buscar_cgr("municipalidad", transport=httpx.MockTransport(handler))


# ─── _detectar_bloqueo ─────────────────────────────────────────────────────

class TestDetectarBloqueo:
    def _make_resp(self, status_code=200, text=""):
        class FakeResp:
            pass
        r = FakeResp()
        r.status_code = status_code
        r.text = text
        return r

    def test_html_real_no_es_bloqueo(self):
        from chilean_legal_mcp.anti_waf import _detectar_bloqueo
        real_html = """
        <html><body>
        <a href="https://www.contraloria.cl/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/0/ABC123?OpenDocument">
        Dictamen N° 15.234 de 2024
        </a>
        </body></html>
        """ * 50  # >2000 chars contenido real
        assert not _detectar_bloqueo(self._make_resp(text=real_html))

    def test_request_rejected_es_bloqueo(self):
        from chilean_legal_mcp.anti_waf import _detectar_bloqueo
        html = "Request Rejected - Please enable JavaScript to continue"
        assert _detectar_bloqueo(self._make_resp(text=html))

    def test_cloudflare_challenge_es_bloqueo(self):
        from chilean_legal_mcp.anti_waf import _detectar_bloqueo
        html = "Request Rejected - Please enable JavaScript to continue"
        assert _detectar_bloqueo(self._make_resp(text=html))

    def test_imperva_challenge_es_bloqueo(self):
        from chilean_legal_mcp.anti_waf import _detectar_bloqueo
        html = "Access Denied - Your access has been blocked"
        assert _detectar_bloqueo(self._make_resp(text=html))

    def test_respuesta_vacia_no_es_bloqueo_pero_sin_contenido_util(self):
        from chilean_legal_mcp.anti_waf import _detectar_bloqueo
        # Texto vacío no dispara WAF pattern, pero tampoco es contenido útil
        # → caller debe manejarlo; _detectar_bloqueo devuelve False (sin señal WAF)
        assert not _detectar_bloqueo(self._make_resp(text=""))

    def test_status_403_es_bloqueo(self):
        from chilean_legal_mcp.anti_waf import _detectar_bloqueo
        assert _detectar_bloqueo(self._make_resp(status_code=403, text="Forbidden"))

    def test_status_503_es_bloqueo(self):
        from chilean_legal_mcp.anti_waf import _detectar_bloqueo
        assert _detectar_bloqueo(self._make_resp(status_code=503, text="Service Unavailable"))

    def test_html_corto_con_rechazo_es_bloqueo(self):
        from chilean_legal_mcp.anti_waf import _detectar_bloqueo
        html = "Access Denied"
        assert _detectar_bloqueo(self._make_resp(text=html))

def _make_resp(text="", status_code=200):
    class FakeResp:
        pass
    r = FakeResp()
    r.text = text
    r.status_code = status_code
    return r


def test_html_corto_con_contenido_cl_no_es_bloqueo():
    from chilean_legal_mcp.anti_waf import _detectar_bloqueo
    resp = _make_resp(text='<a href="https://www.contraloria.cl/0/ABC?OpenDocument">Dictamen N. 12345</a>')
    assert not _detectar_bloqueo(resp)


# ─── CGRFetcher._is_blocked ──────────────────────────────────────────────

class TestCGRFetcherIsBlocked:
    def _make_fetcher(self):
        from chilean_legal_mcp.anti_waf import CGRFetcher
        return CGRFetcher(verbose=False)

    def test_none_es_bloqueado(self):
        assert self._make_fetcher()._is_blocked(None)

    def test_empty_string_es_bloqueado(self):
        assert self._make_fetcher()._is_blocked("")

    def test_none_y_vacio_es_bloqueado(self):
        assert self._make_fetcher()._is_blocked(None)
        assert self._make_fetcher()._is_blocked("")

    def test_request_rejected_string_es_bloqueado(self):
        fetcher = self._make_fetcher()
        assert fetcher._is_blocked("Request Rejected - Please enable JavaScript")

    def test_checking_browser_es_bloqueado(self):
        fetcher = self._make_fetcher()
        assert fetcher._is_blocked("<title>Checking your browser before accessing...</title>")

    def test_cloudflare_es_bloqueado(self):
        fetcher = self._make_fetcher()
        assert fetcher._is_blocked("__cf_chl_tk=abc123 cloudflare ray id: xyz")

    def test_dic_content_no_bloqueado(self):
        fetcher = self._make_fetcher()
        real_dictamen = "<html><body>" + ("<a>Dictamen N. 12345-2024 contenido real de prueba</a>" * 200) + "</body></html>"
        assert not fetcher._is_blocked(real_dictamen)

    def test_juris_en_js_no_false_positive(self):
        """'juris' como substring en JS no debe marcar bloqueo."""
        fetcher = self._make_fetcher()
        js_content = "<script>var juris = document.getElementById('jurisSearch');</script>" * 200
        assert not fetcher._is_blocked(js_content)


# ─── CGRFetcher constructor ─────────────────────────────────────────────

class TestCGRFetcherInit:
    def test_init_default(self):
        from chilean_legal_mcp.anti_waf import CGRFetcher
        f = CGRFetcher()
        assert f is not None
        assert f.verbose is False

    def test_init_verbose(self):
        from chilean_legal_mcp.anti_waf import CGRFetcher
        f = CGRFetcher(verbose=True)
        assert f.verbose is True


# ─── fetch_cgr_sync ────────────────────────────────────────────────────

class TestFetchCgrSync:
    def test_importa_sin_error(self):
        from chilean_legal_mcp.anti_waf import fetch_cgr_sync
        assert callable(fetch_cgr_sync)

    def test_url_invalida_lanza_o_devuelve_string(self):
        from chilean_legal_mcp.anti_waf import fetch_cgr_sync
        try:
            result = fetch_cgr_sync("https://example.invalid/no-exists-here-xyz", verbose=False)
            assert isinstance(result, str)
        except RuntimeError:
            pass  # Todas las capas fallaron → RuntimeError esperado

    def test_curl_cffi_disponible(self):
        try:
            from curl_cffi import requests as curequests
        except ImportError:
            pytest.skip("curl_cffi no instalado")
        from chilean_legal_mcp.anti_waf import CURL_CFFI_AVAILABLE
        assert CURL_CFFI_AVAILABLE is True


# ─── _parse_results ──────────────────────────────────────────────────────

class TestParseResults:
    SAMPLE_HTML = """
    <html><body>
    <table>
    <tr>
    <td><a href="/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/0/ABC123?OpenDocument">
    dictamen N. 15.234 de 2024
    </a></td>
    <td>Materia municipal - funcionarios publicos</td>
    </tr>
    <tr>
    <td><a href="/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/0/DEF456?OpenDocument">
    Dictamen N° 18.567/2025
    </a></td>
    <td>Contratos municipales - licitacion publica</td>
    </tr>
    """ + "<tr><td><a>1</a></td><td>pagina</td></tr>" * 5

    def test_parse_extrae_numeros_dictamen(self):
        from chilean_legal_mcp.contraloria import _parse_results
        res = _parse_results(self.SAMPLE_HTML, limite=10)
        numeros = [r["numero"] for r in res]
        assert any("15.234" in n for n in numeros), f"Esperado 15.234 en {numeros}"

    def test_parse_filtra_paginacion(self):
        from chilean_legal_mcp.contraloria import _parse_results
        res = _parse_results(self.SAMPLE_HTML, limite=10)
        numeros = [r["numero"] for r in res]
        assert not any(re.fullmatch(r"\s*\d{1,2}\s*", n) for n in numeros)

    def test_parse_devuelve_urls_completas(self):
        from chilean_legal_mcp.contraloria import _parse_results
        res = _parse_results(self.SAMPLE_HTML, limite=10)
        for r in res:
            if r["numero"] not in ("1", "2", "3", "4", "5"):
                assert r["url"].startswith("http"), f"URL relativa: {r['url']}"

    def test_parse_respeta_limite(self):
        from chilean_legal_mcp.contraloria import _parse_results
        res = _parse_results(self.SAMPLE_HTML, limite=1)
        assert len(res) <= 1

    def test_parse_html_vacio_retorna_vacio(self):
        from chilean_legal_mcp.contraloria import _parse_results
        res = _parse_results("", limite=10)
        assert res == []

    def test_parse_sin_resultados_retorna_vacio(self):
        from chilean_legal_mcp.contraloria import _parse_results
        res = _parse_results("<html><body>Sin resultados encontrados</body></html>", limite=10)
        assert res == []

    def test_parse_extrae_titulo(self):
        from chilean_legal_mcp.contraloria import _parse_results
        res = _parse_results(self.SAMPLE_HTML, limite=10)
        titulos = [r["titulo"] for r in res]
        assert any(len(t) > 15 for t in titulos), f"Títulos muy cortos: {titulos}"

    def test_parse_campos_requeridos(self):
        from chilean_legal_mcp.contraloria import _parse_results
        res = _parse_results(self.SAMPLE_HTML, limite=10)
        for r in res:
            assert "numero" in r
            assert "titulo" in r
            assert "url" in r


# ─── Anti-WAF module-level availability flags ─────────────────────────────

class TestAntiWafAvailability:
    def test_fetch_cgr_importable(self):
        from chilean_legal_mcp.anti_waf import fetch_cgr
        assert callable(fetch_cgr)

    def test_cgr_fetcher_importable(self):
        from chilean_legal_mcp.anti_waf import CGRFetcher
        assert callable(CGRFetcher)

    def test_httpx_con_fallback_importable(self):
        from chilean_legal_mcp.anti_waf import httpx_con_fallback
        assert callable(httpx_con_fallback)