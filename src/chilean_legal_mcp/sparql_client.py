"""Cliente SPARQL para el endpoint de datos abiertos de la Biblioteca del Congreso Nacional (BCN).

Fuente oficial: datos.bcn.cl — Biblioteca del Congreso Nacional de Chile.
Requiere acceso a internet. Cache interno en memoria con TTL configurable.
"""

from __future__ import annotations

import time

import httpx

from .config import ALLOWED_DOMAINS, CACHE_TTL, TIMEOUTS

SPARQL_ENDPOINT = "https://datos.bcn.cl/sparql"

PREFIXES = """PREFIX bcn: <http://datos.bcn.cl/ontologies/bcn-norms#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
"""

SEARCH_NORMS = PREFIXES + """
SELECT ?uri ?titulo ?numero ?fecha ?leychileId WHERE {
  ?s a bcn:RootNorm ; dc:title ?titulo .
  BIND(?s AS ?uri)
__FILTERS__
  OPTIONAL { ?s bcn:hasNumber ?numero }
  OPTIONAL { ?s bcn:publishDate ?fecha }
  OPTIONAL { ?s bcn:leychileCode ?leychileId }
} LIMIT __LIMIT__
"""

GET_BY_NUMBER = PREFIXES + """
SELECT ?s ?titulo ?numero ?fecha ?leychileId WHERE {
  ?s a bcn:RootNorm ; bcn:hasNumber ?numero ; dc:title ?titulo .
  FILTER(CONTAINS(?numero, "__NUMBER__"))
  OPTIONAL { ?s bcn:publishDate ?fecha }
  OPTIONAL { ?s bcn:leychileCode ?leychileId }
} LIMIT __LIMIT__
"""

SEARCH_NORMS_TIPO = PREFIXES + """
SELECT ?uri ?titulo ?numero ?fecha ?leychileId ?tipo WHERE {
  ?s a bcn:RootNorm ; dc:title ?titulo .
  BIND(?s AS ?uri)
__FILTERS__
  OPTIONAL { ?s bcn:hasNumber ?numero }
  OPTIONAL { ?s bcn:publishDate ?fecha }
  OPTIONAL { ?s bcn:leychileCode ?leychileId }
__EXTRA__
} LIMIT __LIMIT__
"""


class BCNClient:
    def __init__(self, timeout: float | None = None):
        self.timeout = timeout or TIMEOUTS["normal"]
        self._client = httpx.Client(
            timeout=self.timeout,
            http2=True,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=20),
        )
        self._cache: dict[str, tuple[float, list[dict]]] = {}
        self._ttl = CACHE_TTL["busqueda"]

    def query(self, sparql: str) -> list[dict]:
        import tenacity

        key = sparql
        now = time.time()
        if key in self._cache:
            ts, val = self._cache[key]
            if now - ts < self._ttl:
                return val

        @tenacity.retry(
            stop=tenacity.stop_after_attempt(3),
            wait=tenacity.wait_exponential(multiplier=1, min=1, max=8),
            retry=tenacity.retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
            reraise=True,
        )
        def _do():
            resp = self._client.get(
                SPARQL_ENDPOINT,
                params={"format": "application/sparql-results+json", "query": sparql},
                headers={"Accept": "application/sparql-results+json"},
            )
            # Reintentar en errores de servidor o rate limit
            if resp.status_code in (429, 500, 502, 503):
                raise httpx.ConnectError(f"reintentar — status {resp.status_code}")
            resp.raise_for_status()
            return resp

        resp = _do()
        data = resp.json()
        rows = []
        for binding in data.get("results", {}).get("bindings", []):
            rows.append({k: v["value"] for k, v in binding.items()})
        deduped = self._dedupe(rows)
        self._cache[key] = (now, deduped)
        if len(self._cache) > 512:
            oldest = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest]
        return deduped

    @staticmethod
    def _dedupe(rows: list[dict]) -> list[dict]:
        seen: set[str] = set()
        unique = []
        for row in rows:
            key = row.get("uri") or row.get("s") or ""
            if key in seen:
                continue
            seen.add(key)
            unique.append(row)
        return unique

    def search_by_title(self, query: str, limit: int = 10, offset: int = 0, fecha_desde: str | None = None, fecha_hasta: str | None = None, tipo: str | None = None) -> list[dict]:
        words = [w for w in query.lower().split() if len(w) >= 3]
        if not words:
            words = [query.lower()]
        filters = "\n".join(
            f'  FILTER(CONTAINS(LCASE(?titulo), "{_escape(w)}"))' for w in words
        )
        # Build mandatory patterns for filtered fields
        mandatory = ""
        if fecha_desde or fecha_hasta:
            mandatory += "  ?s bcn:publishDate ?fecha .\n"
            if fecha_desde:
                filters += f'\n  FILTER(?fecha >= "{_escape(fecha_desde)}"^^<http://www.w3.org/2001/XMLSchema#date>)'
            if fecha_hasta:
                filters += f'\n  FILTER(?fecha <= "{_escape(fecha_hasta)}"^^<http://www.w3.org/2001/XMLSchema#date>)'
        if tipo:
            mandatory += "  ?s bcn:type ?tipo .\n"
            filters += f'\n  FILTER(CONTAINS(LCASE(STR(?tipo)), "{_escape(tipo.lower())}"))'
        if mandatory:
            optional_fecha = "" if "bcn:publishDate ?fecha" in mandatory else "  OPTIONAL { ?s bcn:publishDate ?fecha }\n"
            offset_clause = f" OFFSET {offset}" if offset else ""
            sparql = f"""{PREFIXES}
SELECT ?uri ?titulo ?numero ?fecha ?leychileId WHERE {{
  ?s a bcn:RootNorm ; dc:title ?titulo .
  BIND(?s AS ?uri)
{mandatory}{filters}
  OPTIONAL {{ ?s bcn:hasNumber ?numero }}
{optional_fecha}  OPTIONAL {{ ?s bcn:leychileCode ?leychileId }}
}} LIMIT {limit}{offset_clause}"""
            return self.query(sparql)
        offset_clause = f" OFFSET {offset}" if offset else ""
        sparql = SEARCH_NORMS.replace("__FILTERS__", filters).replace("__LIMIT__", str(limit) + offset_clause)
        return self.query(sparql)

    def search_by_number(self, number: str, limit: int = 10) -> list[dict]:
        safe = _escape(number)
        sparql = GET_BY_NUMBER.replace("__NUMBER__", safe).replace(
            "__LIMIT__", str(limit))
        return self.query(sparql)
    def search_dictamenes(self, query: str, limit: int = 10) -> list[dict]:
        words = [w for w in query.lower().split() if len(w) >= 3]
        if not words:
            words = [query.lower()]
        filters = "\n".join(
            f'  FILTER(CONTAINS(LCASE(?titulo), "{_escape(w)}"))' for w in words
        )
        sparql = SEARCH_DICTAMENES.replace("__FILTERS__", filters).replace(
            "__LIMIT__", str(limit))
        return self.query(sparql)

    def search_articulos(self, query: str, limit: int = 10) -> list[dict]:
        words = [w for w in query.lower().split() if len(w) >= 4]
        if not words:
            words = [query.lower()]
        filters = "\n".join(f'  FILTER(CONTAINS(LCASE(?texto), "{_escape(w)}"))' for w in words)
        sparql = f"""PREFIX bcn: <http://datos.bcn.cl/ontologies/bcn-resources#>
SELECT ?uri ?numero ?texto WHERE {{
  ?s a bcn:Articulo ; bcn:numero ?numero ; <http://datos.bcn.cl/ontologies/bcn-resources#value> ?texto .
  BIND(?s AS ?uri)
{filters}
}} LIMIT {limit}"""
        return self.query(sparql)

    def get_historial(self, uri: str) -> list[dict]:
        # Nivel 1: relaciones directas
        sparql = f"""PREFIX bcn: <http://datos.bcn.cl/ontologies/bcn-norms#>
SELECT ?p ?o WHERE {{ <{uri}> ?p ?o }} LIMIT 80"""
        level1 = self.query(sparql)
        # Nivel 2: para cada hasVersion / modifiesTo, traer título y fecha
        extra = []
        for r in level1:
            p = r.get("p","")
            o = r.get("o","")
            if any(k in p for k in ("hasVersion","modifiesTo","isModifiedBy","versionOf","isVersionOf")) and o.startswith("http"):
                try:
                    sparql2 = f"""PREFIX bcn: <http://datos.bcn.cl/ontologies/bcn-norms#> PREFIX dc: <http://purl.org/dc/elements/1.1/>
SELECT ?titulo ?fecha WHERE {{ <{o}> dc:title ?titulo . OPTIONAL {{ <{o}> bcn:publishDate ?fecha }} }} LIMIT 1"""
                    r2 = self.query(sparql2)
                    if r2:
                        extra.append({"p": p + "->titulo", "o": f"{r2[0].get('titulo','')[:80]} ({r2[0].get('fecha','')})"})
                except Exception:
                    pass
        return level1 + extra

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


SEARCH_DICTAMENES = PREFIXES + """
SELECT ?uri ?titulo ?fecha WHERE {
  ?s a <http://datos.bcn.cl/ontologies/bcn-resources#Oficio> ; <http://purl.org/dc/elements/1.1/title> ?titulo .
  BIND(?s AS ?uri)
__FILTERS__
  OPTIONAL { ?s <http://purl.org/dc/elements/1.1/date> ?fecha }
} LIMIT __LIMIT__
"""


def leychile_url(leychile_id: str | None) -> str | None:
    if not leychile_id:
        return None
    return f"https://www.bcn.cl/leychile/navegar?idNorma={leychile_id}"
