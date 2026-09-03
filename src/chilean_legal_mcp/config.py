"""Configuración centralizada del proyecto chilean-legal-mcp.

Dominios oficiales chilenos permitidos. Cualquier request a dominio no enlistado es rechazado.
Esta lista se usa como allow-list de seguridad y para detección de WAF.
"""

from __future__ import annotations

# Dominios oficiales chilenos permitidos (fuentes de datos + auxiliares)
ALLOWED_DOMAINS = {
    # Legislación y normativa
    "www.bcn.cl",
    "datos.bcn.cl",
    "www.leychile.cl",
    "www.sii.cl",
    "www3.sii.cl",
    "www4.sii.cl",
    # Tesorería / Tribunales tributarios
    "www.tesoreria.cl",
    "tgr.gob.cl",
    "www.tta.cl",
    # Poder Judicial
    "www.pjud.cl",
    "portal-unificado-sentencias.pjud.cl",
    "juris.pjud.cl",
    # Contraloría
    "www.contraloria.cl",
    # Instituto Nacional de Propiedad Industrial
    "www.inapi.cl",
    "buscadormarcas.inapi.cl",
    "tramites.inapi.cl",
    "www.tdpi.cl",
    # Superintendencias
    "snifa.sma.gob.cl",
    "www.sma.gob.cl",
    "www.boletinconcursal.cl",
    "www.superir.gob.cl",
    # Dirección del Trabajo
    "www.dt.gob.cl",
    # SUSESO
    "www.suseso.cl",
    # Tribunal Constitucional
    "www.tribunalconstitucional.cl",
    "buscador.tcchile.cl",
    # Diario Oficial
    "www.diariooficial.interior.gob.cl",
    # CMF (Comisión para el Mercado Financiero)
    "www.cmfchile.cl",
    "www.cmfchile.cl",
    # TDLC (Tribunal de Defensa de la Libre Competencia)
    "www.tdlc.cl",
    # CPLT (Consejo para la Transparencia)
    "jurisprudencia.cplt.cl",
    "www.consejotransparencia.cl",
    # Datos abiertos
    "datos.gob.cl",
    # Academia
    "search.scielo.org",
    "api.crossref.org",
    # Referencia externa (portalchile.org — solo como alternativa INAPI, rotulado)
    "www.portalchile.org",
}

# Endpoints de salud conocidos (para verificación rápida)
HEALTH_ENDPOINTS = {
    "BCN SPARQL": "https://datos.bcn.cl/sparql",
    "SII": "https://www.sii.cl",
    "TGR": "https://tgr.gob.cl",
    "CGR": "https://www.contraloria.cl",
    "PJUD": "https://www.pjud.cl",
    "PJUD jurisprudencia": "https://juris.pjud.cl/busqueda/lista_buscadores",
    "SMA": "https://snifa.sma.gob.cl",
    "INAPI": "https://buscadormarcas.inapi.cl",
    "TDPI": "https://www.tdpi.cl",
    "Superir": "https://www.boletinconcursal.cl",
    "SUSESO": "https://www.suseso.cl",
    "TC": "https://buscador.tcchile.cl",
    "Diario Oficial": "https://www.diariooficial.interior.gob.cl",
    "CMF": "https://www.cmfchile.cl",
    "DT": "https://www.dt.gob.cl",
    "SciELO": "https://search.scielo.org",
}

# TTLs de cache por tipo de dato (en segundos)
CACHE_TTL = {
    "norma_texto": 86400,      # 24 horas — texto completo de ley
    "busqueda": 3600,           # 1 hora — resultados de búsqueda
    "jurisprudencia": 7200,     # 2 horas
    "dictamenes": 7200,         # 2 horas
    "doctrina": 43200,          # 12 horas
    "sectorial": 3600,          # 1 hora — SII, TGR, etc.
    "salud": 300,               # 5 minutos — health check
}

# Timeouts por defecto (en segundos)
TIMEOUTS = {
    "rapido": 10,
    "normal": 20,
    "lento": 30,
    "pdf": 45,
}

# User-Agent para todas las requests
USER_AGENT = "chilean-legal-mcp/0.1 (proyecto chileno de investigación jurídica; contacto: usuario@local)"