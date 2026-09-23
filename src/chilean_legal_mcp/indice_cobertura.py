"""Indice de cobertura del corpus K-LegalChile.

Mapea cada materia juridica a la fuente interna que la cubre, con su volumen
real medido en los datos locales y su nivel de confianza.

Regla de decision:
- confianza "alta"    -> usar la fuente interna como primaria.
- confianza "baja"    -> intentar interno; si no hay coincidencia clara, salir a externo.
- confianza "ninguna" -> ir directo a fuentes externas (no buscar a ciegas adentro).

Volumenes medidos (data/normas.db, data/jpl/corpus.db, kb/kb_index.db):
  normas (Leyes/Textos LeyChile) = 65.027
  Contraloria (cgr_dictamenes 41.845 + citas_legales 10.000 + criterios 91 + embeddings 11.291)
  Tribunal Constitucional (tc_sentencias 859 con texto completo)
  JPL (leyes 53 + ordenanzas 5.925 en 339 comunas + 6 manuales de formatos)
  KB (35 documentos Markdown, ambito JPL)
  SII 23 | TGR 16 | INAPI 4 | TDLC 3 | SMA 6 | SuperIR 2
  Familia / Civil / Laboral / Penal / Garantia = 0 (solo externo)
"""

from __future__ import annotations

import re
import unicodedata

# materia -> {fuentes internas, volumen, confianza, estrategia}
COBERTURA: dict[str, dict] = {
    "leyes_normas": {
        "fuentes": ["normas"],
        "volumen": 65027,
        "confianza": "alta",
        "descripcion": "Leyes y textos oficiales (base LeyChile) indexados en texto completo.",
    },
    "contraloria": {
        "fuentes": ["cgr_dictamenes", "citas_legales", "criterios_estado"],
        "volumen": 52136,
        "confianza": "alta",
        "descripcion": "Dictamenes CGR (municipios, funcionarios, probidad, estatuto administrativo) con estado del criterio.",
    },
    "tribunal_constitucional": {
        "fuentes": ["tc_sentencias"],
        "volumen": 859,
        "confianza": "alta",
        "descripcion": "Sentencias del Tribunal Constitucional con texto completo (inaplicabilidad, inconstitucionalidad, conflicto).",
    },
    "policia_local": {
        "fuentes": ["jpl_leyes", "jpl_ordenanzas", "jpl_manuales", "kb"],
        "volumen": 6019,
        "confianza": "alta",
        "descripcion": "Juzgado de Policia Local: leyes del ambito, ordenanzas municipales (339 comunas), formatos reales y base de conocimiento.",
    },
    "sii": {
        "fuentes": ["sii_oficios", "sii_circulares", "sii_resoluciones", "sii_fallos"],
        "volumen": 23,
        "confianza": "baja",
        "descripcion": "SII: solo registros puntuales. Intentar interno; si no calza, externo.",
    },
    "tgr": {
        "fuentes": ["tgr_dictamenes", "tgr_resoluciones", "tgr_circulares", "tgr_fallos"],
        "volumen": 16,
        "confianza": "baja",
        "descripcion": "Tesoreria General: registros puntuales. Interno si calza, sino externo.",
    },
    "inapi": {
        "fuentes": ["inapi_marcas"],
        "volumen": 4,
        "confianza": "baja",
        "descripcion": "INAPI marcas: registros puntuales. Interno si calza, sino externo.",
    },
    "tdlc": {
        "fuentes": ["tdpi_juris"],
        "volumen": 3,
        "confianza": "baja",
        "descripcion": "Libre competencia: registros puntuales. Interno si calza, sino externo.",
    },
    "sma": {
        "fuentes": ["sma_sancionatorio"],
        "volumen": 6,
        "confianza": "baja",
        "descripcion": "Medio ambiente sancionatorio: registros puntuales. Interno si calza, sino externo.",
    },
    "ambiental": {
        "fuentes": ["tribunales_ambientales", "fne", "sma_sancionatorio"],
        "volumen": 0,
        "confianza": "baja",
        "descripcion": "Tribunales Ambientales y FNE: conectores a portales oficiales (sin corpus local). Interno si calza, sino externo.",
    },
    "superir": {
        "fuentes": ["superir_boletin"],
        "volumen": 2,
        "confianza": "baja",
        "descripcion": "Insolvencia: registros puntuales. Interno si calza, sino externo.",
    },
    "familia": {"fuentes": [], "volumen": 0, "confianza": "ninguna",
                "descripcion": "Sin cobertura interna. Ir directo a externo."},
    "civil": {"fuentes": [], "volumen": 0, "confianza": "ninguna",
              "descripcion": "Sin cobertura interna (salvo choque/transito en JPL). Ir directo a externo."},
    "laboral": {"fuentes": [], "volumen": 0, "confianza": "ninguna",
                "descripcion": "Sin cobertura interna. Ir directo a externo."},
    "penal": {"fuentes": [], "volumen": 0, "confianza": "ninguna",
              "descripcion": "Sin cobertura interna. Ir directo a externo."},
}

# Palabras clave (normalizadas, sin tildes) por materia.
_CLAVES: dict[str, list[str]] = {
    "contraloria": [
        "contraloria", "dictamen", "cgr", "funcionario publico", "funcionaria",
        "municipalidad", "alcalde", "concejal", "estatuto administrativo",
        "probidad", "inhabilidad", "sumario administrativo", "toma de razon",
        "reconsideracion", "desvinculacion", "planta", "contrata", "honorarios",
    ],
    "tribunal_constitucional": [
        "tribunal constitucional", "tc", "inaplicabilidad", "inconstitucionalidad",
        "constitucionalidad", "accion de inaplicabilidad", "por inconstitucionalidad",
        "requerimiento de inaplicabilidad", "auto acordado", "quorum constitucional",
    ],
    "ambiental": [
        "tribunal ambiental", "tribunales ambientales", "impacto ambiental",
        "evaluacion de impacto", "rca", "plan de descontaminacion", "smce",
        "fiscalia nacional economica", "fne", "libre competencia", "colusion",
        "abuso de posicion dominante", "actuacion de la fne",
    ],
    "policia_local": [
        "policia local", "jpl", "ordenanza", "ordenanzas", "ruidos molestos",
        "multa de transito", "parte policial", "tag", "permiso de circulacion",
        "patente municipal", "aseo", "ornato", "microbasural", "botar basura",
        "cierre de calle", "fonda", "ramada", "alcoholes", "botilleria",
        "tenencia responsable", "mascota", "perro", "feria", "comercio ambulante",
        "letrero", "publicidad", "construccion sin permiso", "obra sin permiso",
        "denuncia infraccional", "comparendo", "actuario", "reclusion nocturna",
        "registro de multas", "multas impagas", "licencia de conducir",
    ],
    "sii": [
        "sii", "impuesto", "tributario", "renta", "iva", "contribuciones",
        "f22", "f29", "factura", "boleta", "fiscalizacion", "tasacion",
    ],
    "tgr": ["tesoreria", "tgr", "cobranza", "deuda fiscal", "remate fiscal"],
    "inapi": ["inapi", "marca comercial", "registro de marca", "propiedad industrial", "patente de invencion", "oposicion marcaria"],
    "tdlc": ["libre competencia", "tdlc", "colusion", "abuso posicion dominante"],
    "sma": ["medio ambiente", "sma", "superintendencia del medio ambiente", "rca", "evaluacion ambiental", "sancion ambiental"],
    "superir": ["insolvencia", "quiebra", "reorganizacion", "liquidacion", "superir", "acuerdo extrajudicial"],
    "familia": [
        "familia", "divorcio", "alimentos", "pension de alimentos", "cuidado personal",
        "tuicion", "relacion directa", "visitas", "violencia intrafamiliar", "vif",
        "adopcion", "filiacion", "compensacion economica", "separacion judicial",
    ],
    "laboral": [
        "laboral", "despido", "trabajo", "contrato de trabajo", "finiquito",
        "indemnizacion laboral", "sueldo", "cotizaciones", "afp", "isapre",
        "accidente del trabajo", "fuero", "sindicato", "negociacion colectiva",
    ],
    "penal": [
        "penal", "delito", "fiscalia", "ministerio publico", "garantia",
        "juzgado de garantia", "prision preventiva", "formalizar", "querella criminal",
        "hurto", "robo", "estafa", "homicidio", "lesiones", "trafico de drogas",
    ],
    "civil": [
        "arrendamiento", "arriendo", "contrato", "responsabilidad civil",
        "indemnizacion de perjuicios", "danos y perjuicios", "herencia",
        "sucesion", "testamento", "posesion efectiva", "prescripcion adquisitiva",
        "servidumbre", "copropiedad", "condominio", "cobro de pesos",
    ],
}

_PATRON_LEY = re.compile(r"(?:ley|art\.?|articulo)\s*n?°?\s*\d[\d.\-]*", re.IGNORECASE)


def _norm(s: str) -> str:
    s = s.lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s


def clasificar(consulta: str) -> dict:
    """Clasifica la consulta por materias y devuelve la estrategia de busqueda.

    Retorna: {"materias": [...], "estrategia": "interno"|"hibrido"|"externo",
              "detalle": [{"materia":..., "confianza":..., "estrategia":...}]}
    - "interno": todas las materias detectadas tienen confianza alta.
    - "externo": ninguna materia tiene cobertura interna.
    - "hibrido": mezcla (o consulta general de leyes: base normas + respaldo externo).
    """
    q = _norm(consulta or "")
    halladas: list[str] = []
    for materia, claves in _CLAVES.items():
        for k in claves:
            if len(k) <= 4:
                # Siglas cortas (rca, iva, tag, sii...): exigir palabra completa
                # para no matchear dentro de otras palabras ("marca", "privado").
                if re.search(r"\b" + re.escape(k) + r"\b", q):
                    halladas.append(materia)
                    break
            elif k in q:
                halladas.append(materia)
                break
    cita_ley = bool(_PATRON_LEY.search(consulta or ""))

    if not halladas and not cita_ley:
        # Sin senal de materia: base de normas internas + respaldo externo.
        return {
            "materias": ["leyes_normas"],
            "estrategia": "hibrido",
            "detalle": [{"materia": "leyes_normas", "confianza": "alta",
                         "estrategia": "interno", "nota": "pregunta general: base de normas + externo si falta"}],
        }

    detalle = []
    for m in halladas:
        conf = COBERTURA[m]["confianza"]
        est = {"alta": "interno", "baja": "hibrido", "ninguna": "externo"}[conf]
        detalle.append({"materia": m, "confianza": conf, "estrategia": est,
                        "fuentes": COBERTURA[m]["fuentes"]})
    if cita_ley and "leyes_normas" not in halladas:
        detalle.append({"materia": "leyes_normas", "confianza": "alta",
                        "estrategia": "interno", "fuentes": COBERTURA["leyes_normas"]["fuentes"]})

    confs = {d["confianza"] for d in detalle}
    if confs <= {"alta"}:
        estrategia = "interno"
    elif confs <= {"ninguna"}:
        estrategia = "externo"
    else:
        estrategia = "hibrido"
    return {
        "materias": [d["materia"] for d in detalle],
        "estrategia": estrategia,
        "detalle": detalle,
    }


def tabla_cobertura_texto() -> str:
    """Tabla legible del indice para auditoria y para mostrar al usuario."""
    lineas = ["# Indice de cobertura del corpus K-LegalChile",
              "",
              "| Materia | Fuentes internas | Registros | Confianza | Estrategia |",
              "|---|---|---|---|---|"]
    for materia, info in COBERTURA.items():
        fuentes = ", ".join(info["fuentes"]) if info["fuentes"] else "—"
        est = {"alta": "interno", "baja": "interno→externo si no calza", "ninguna": "externo directo"}[info["confianza"]]
        lineas.append(f"| {materia} | {fuentes} | {info['volumen']} | {info['confianza']} | {est} |")
    return "\n".join(lineas)
