"""Tests unitarios para contraloria.py y anti_waf.py (CGRFetcher, _parse_results, URL builder)."""

import sys
sys.path.insert(0, "src")

import re
import pytest


# ─── _build_search_url ─────────────────────────────────────────────────────

class TestBuildSearchUrl:
    def test_url_contiene_query_codificada(self):
        from chilean_legal_mcp.contraloria import _build_search_url
        url = _build_search_url("despido sin causa", limite=10)
        assert "TextoLibre=despido+sin+causa" in url or "TextoLibre=despido%20sin%20causa" in url

    def test_url_contiene_limite(self):
        from chilean_legal_mcp.contraloria import _build_search_url
        url = _build_search_url("test", limite=5)
        assert "dpp=5" in url
        assert "porPagina=5" in url

    def test_url_base_correcta(self):
        from chilean_legal_mcp.contraloria import _build_search_url
        url = _build_search_url("test", limite=10)
        assert "contraloria.cl" in url
        assert "FormConsultaWeb2k" in url
        assert "OpenForm" in url

    def test_query_vacia_devuelve_url_valida(self):
        from chilean_legal_mcp.contraloria import _build_search_url
        url = _build_search_url("", limite=10)
        assert url.startswith("https://")

    def test_caracteres_especiales_codificados(self):
        from chilean_legal_mcp.contraloria import _build_search_url
        url = _build_search_url("artículo 8°", limite=10)
        assert " " not in url.split("TextoLibre=")[1].split("&")[0] or "%20" in url


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
        html = "<title>Just a moment...</title>Checking your browser before accessing"
        assert _detectar_bloqueo(self._make_resp(text=html))

    def test_imperva_challenge_es_bloqueo(self):
        from chilean_legal_mcp.anti_waf import _detectar_bloqueo
        html = "<html><body>Access to this page has been denied. Please contact the administrator.</body></html>"
        assert _detectar_bloqueo(self._make_resp(text=html))

    def test_respuesta_vacia_es_bloqueo(self):
        from chilean_legal_mcp.anti_waf import _detectar_bloqueo
        assert _detectar_bloqueo(self._make_resp(text=""))

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

    def test_html_corto_con_contenido_cl_no_es_bloqueo(self):
        from chilean_legal_mcp.anti_waf import _detectar_bloqueo
        real_html = """
        <html><body>
        <a href="https://www.contraloria.cl/0/ABC123?OpenDocument">Dictamen</a>
        <a href="https://www.bcn.cl/leychile">LeyChile</a>
        """ * 30
        resp = self._make_resp(text=real_html)
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

    def test_very_short_es_bloqueado(self):
        assert self._make_fetcher()._is_blocked("x" * 100)

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