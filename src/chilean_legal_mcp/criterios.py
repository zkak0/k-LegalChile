"""Estado del criterio en la jurisprudencia administrativa de la CGR — corpus K-LegalChile.

Determina la vigencia/superación de un dictamen a partir de dos señales:
  1) referencias cruzadas en los propios textos: otros dictámenes que explícitamente
     reconsideran, dejan sin efecto, complementan, modifican o reafirman el criterio;
  2) el grafo de citaciones del corpus local (citas_legales, tipo aplica/funda/cita).

Estados: VIGENTE (por defecto) / DEROGADO / RECONSIDERADO / MODIFICADO / COMPLEMENTADO / REAFIRMADO.

Incluye también la ficha doctrinal del corpus K-LegalChile y el
boletín de criterios nuevos.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Taxonomía cerrada de materias del corpus (~18 categorías)
# ---------------------------------------------------------------------------
MATERIAS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Contratación pública", ("licitaci", "contrato de", "mercado público", "ley 19.886", "orden de compra",
                              "adjudicat", "bases de licitaci", "oferta económica", "garantía de seriedad")),
    ("Funcionarios públicos", ("funcionario", "funcionaria", "nombramiento", "calificaci", "sumario",
                               "destituc", "ascenso", "encasillamient", "provisión de cargos", "provision de cargos")),
    ("Remuneraciones", ("remuneraci", "asignaci", "sueldo", "bonificaci", "gratificaci", "desahucio",
                        "aumento de renta", "trienio", "bienio")),
    ("Municipalidades", ("municipalidad", "alcalde", "concejo municipal", "ordenanza", "patente municipal",
                         "plan regulador", "permiso de circulaci", "derechos de aseo", "omil")),
    ("Subvenciones y transferencias", ("subvenci", "transferencia", "aporte", "fondos públicos",
                                       "convenio de transferencia")),
    ("Obras públicas", ("contrato de obra", "obra pública", "obra publica", "mandante", "recepcion de obra",
                        "termino de obra", "término de obra", "maquinaria", "seremi de obras")),
    ("Salud", ("salud", "hospital", "fonasa", "licencia médica", "licencia medica", "cesantía", "cesantia",
               "establecimiento de salud", "urgencia", "fármac", "farmac")),
    ("Educación", ("educaci", "docente", "estudiant", "colegio", "universidad", "daem", "ley 19.070",
                   "estatuto docente")),
    ("Estatuto Administrativo", ("estatuto administrativo", "ley 18.834", "ley 18.883", "planta", "contrata",
                                 "suplente", "carrera funcionaria", "zona")),
    ("Seguridad social", ("previsi", "pensi", "jubilaci", "caja de", "cotizaci", "afp", "isl",
                          "seguro social")),
    ("Presupuesto y finanzas públicas", ("presupuesto", "ejecución presupuestaria", "ejecucion presupuestaria",
                                          "gasto", "imputaci", "dipres", "partida", "subtitulo")),
    ("Bienes y patrimonio", ("bienes nacionales", "inventario", "comodato", "concesi", "regularizaci",
                             "dominio", "inmueble fiscal")),
    ("Fuerzas Armadas y de Orden", ("ff.aa.", "militar", "carabineros", "pdi", "gendarmería", "gendarmeria",
                                    "armada", "fuerza aérea", "fuerza aerea", "policía", "policia")),
    ("Probidad y transparencia", ("probidad", "transparencia", "conflicto de interés", "conflicto de interes",
                                  "negociación incompatible", "negociacion incompatible", "ley 20.880", "inhabilitad")),
    ("Vivienda y urbanismo", ("serviu", "vivienda", "subsidio", "urbanism", "plan urbano", "loteo",
                              "permiso de edificación", "permiso de edificacion")),
    ("Medio ambiente", ("medio ambiente", "medioambiente", "agua", "sanción ambiental", "sancion ambiental",
                        "sma", "residuo", "impacto ambiental")),
    ("Transporte y tránsito", ("transporte", "tránsito", "transito", "tráfico", "trafico", "conductor",
                               "licencia de conducir", "vehículo", "vehiculo")),
    ("Trabajo y remuneraciones del sector público", ("ley 18.632", "asesoría", "asesoria", "horas extraordinarias",
                                                     "jornada")),
)


def _normaliza(texto: str) -> str:
    return (texto or "").lower().strip()


def url_oficial_dictamen(r: dict) -> str:
    """URL oficial del dictamen frente a la CGR cuando disponemos del UNID (fuente: URL interna del corpus)."""
    unid = r.get("unid")
    if unid:
        return (f"https://www.contraloria.cl/appinf/LegisJuri/DictamenesGeneralesMunicipales.nsf/"
                f"cgrDetalleDictamenNVDA?OpenForm&UNID={unid}")
    return r.get("source_url") or "—"


def materia_de(numero: str | None = None, anio: int | None = None,
               organismo_consultante: str | None = None, texto: str | None = None,
               titulo: str | None = None) -> str:
    """Clasifica un dictamen dentro de la taxonomía cerrada de materias."""
    bloques = " ".join(x for x in (titulo, organismo_consultante or "", texto or "") if x)
    base = " ".join(_normaliza(b) for b in bloques)
    for materia, claves in MATERIAS:
        for clave in claves:
            if clave in base:
                return materia
    return "Materia administrativa general"


# ---------------------------------------------------------------------------
# Referencias cruzadas entre dictámenes (señal textual de vigencia/superación)
# ---------------------------------------------------------------------------
_RE_DICT_REF = re.compile(
    r"(?P<pre>[\s\S]{0,220}?)(?:dictamen|dictámenes)\s*(?:constitucional\s+)?"
    r"[Nn]?[°ºo.]?\s*(?P<num>\d[\d.]*)\s*(?:complementario\s+)?"
    r"(?:,?\s*de\s+(?P<anio>\d{4}))?", re.I)

_RE_NUMERO = re.compile(r"\d+")


def _num_limpio(raw: str | None) -> str:
    if not raw:
        return ""
    return "".join(_RE_NUMERO.findall(raw))


_CLAVES_ESTADOS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("DEROGADO", ("deja sin efecto", "dejó sin efecto", "dejo sin efecto", "dejando sin efecto",
                  "se dejan sin efecto", "quedó sin efecto", "queda sin efecto", "se deroga", "derogó", "derogado")),
    ("RECONSIDERADO", ("reconsidera", "reconsideró", "reconsidero", "reconsiderando", "reconsideración",
                       "reconsideracion", "se reconsidera")),
    ("MODIFICADO", ("modifica", "modificó", "modifico", "modificando", "sustituye", "reemplaza", "se modifica")),
    ("COMPLEMENTADO", ("complementa", "complementó", "complementando", "se complementa", "aclara")),
    ("REAFIRMADO", ("reafirma", "reitera", "confirma el criterio", "mantiene el criterio", "mantiene la doctrina",
                    "mismo criterio", "no procede variar", "se mantiene", "ratifica")),
)


def _estado_de_frase(contexto: str) -> str | None:
    ctx = _normaliza(contexto)
    for estado, claves in _CLAVES_ESTADOS:
        for clave in claves:
            if clave in ctx:
                return estado
    return None


def _referencias_cruzadas(db) -> dict[str, list[dict]]:
    """Un solo barrido del corpus: a qué dictámenes se refiere cada texto y con qué verbo."""
    rows = db._conn.execute(
        "SELECT id, numero, anio, sumario FROM cgr_dictamenes ORDER BY fecha DESC"
    ).fetchall()
    por_numero: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        por_numero[_num_limpio(r["numero"])].append(dict(r))

    salida: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        texto = r["sumario"] or ""
        num_propio = _num_limpio(r["numero"])
        for m in _RE_DICT_REF.finditer(texto):
            num = _num_limpio(m.group("num"))
            if not num or num == num_propio:
                continue
            anio_ref = int(m.group("anio")) if m.group("anio") else None
            ctx = (m.group("pre")[-200:] + texto[m.end():m.end() + 220])
            estado = _estado_de_frase(ctx)
            if estado is None:
                continue
            objetivos = por_numero.get(num, [])
            if anio_ref:
                coincidentes = [t for t in objetivos if t["anio"] == anio_ref]
                if coincidentes:
                    objetivos = coincidentes
            for t in objetivos[:3]:
                salida[t["id"]].append({
                    "estado": estado,
                    "descripcion": f"{estado} por Dictamen N° {r['numero']} de {r['anio'] or '—'}",
                    "fuente": f"Dictamen {r['numero']} de {r['anio'] or '—'}",
                })
    return dict(salida)


_ORDEN_PRIORIDAD = {"DEROGADO": 0, "RECONSIDERADO": 1, "MODIFICADO": 2,
                    "COMPLEMENTADO": 3, "REAFIRMADO": 4, "VIGENTE": 5}


def _estado_principal(estados: list[dict]) -> dict:
    estados = estados or []
    if not estados:
        return {"estado": "VIGENTE", "descripcion": "Sin resoluciones posteriores detectadas en el corpus.",
                "fuente": "corpus"}
    mejor = min(estados, key=lambda e: _ORDEN_PRIORIDAD.get(e["estado"], 5))
    return mejor


def marcar_estados(db, dictamen_ids: list[str] | None = None) -> dict:
    """Computa y persiste criterios_estado para el corpus (o un subconjunto)."""
    referencias = _referencias_cruzadas(db)
    targets = dictamen_ids if dictamen_ids is not None else list(referencias.keys())
    marcados = 0
    for tid in targets:
        estados = referencias.get(tid, [])
        if not estados:
            continue
        principal = _estado_principal(estados)
        db.upsert_criterio(tid, None, None, principal["estado"],
                           principal["descripcion"], principal["fuente"])
        for e in estados:
            db.upsert_criterio(tid, None, None, e["estado"], e["descripcion"], e["fuente"])
        marcados += 1
    return {"dictamenes_evaluados": len(targets), "marcados": marcados,
            "referencias_detectadas": sum(len(v) for v in referencias.values())}


def estado_principal(db, dictamen_id: str | None = None, numero: str | None = None,
                     anio: int | None = None) -> dict:
    r = db.consultar_dictamen_cgr(dictamen_id=dictamen_id, numero=numero, anio=anio)
    if not r:
        return {"error": "Dictamen no encontrado en el corpus local."}
    filas = db.get_criterios(r["id"])
    estados = [{"estado": f["estado"], "descripcion": f["descripcion"], "fuente": f["fuente"]} for f in filas]
    principal = _estado_principal(estados)
    principal["dictamen"] = r
    principal["detalle"] = estados
    return principal


# ---------------------------------------------------------------------------
# Ficha doctrinal del corpus K-LegalChile
# ---------------------------------------------------------------------------
def _separar_antecedentes_criterio(texto: str) -> tuple[str, str]:
    """Antecedentes = primeros párrafos; razonamiento = cierre del texto."""
    if not texto:
        return "", ""
    parrafos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    if len(parrafos) <= 2:
        return " ".join(parrafos)[:1200], ""
    return (" ".join(parrafos[:-1])[:1500], parrafos[-1][:1500])


def _extraer_normas(citas: list[dict]) -> list[str]:
    normas: list[str] = []
    for c in citas:
        ref = c.get("target_external_ref")
        if ref and "Art" in ref and ref not in normas:
            normas.append(ref)
    return normas[:12]


def ficha_dictamen(db, dictamen_id: str | None = None, numero: str | None = None,
                   anio: int | None = None, breve: bool = False) -> str:
    r = db.consultar_dictamen_cgr(dictamen_id=dictamen_id, numero=numero, anio=anio)
    if not r:
        return "Dictamen no encontrado en el corpus local."
    texto = r["sumario"] or ""
    materia = materia_de(numero=r["numero"], anio=r["anio"],
                         organismo_consultante=r["organismo_consultante"], texto=texto)
    citas = db.get_citas(source_kind="dictamen", source_id=r["id"], limit=30)
    citas += db.get_citas(target_kind="dictamen", target_id=r["id"], limit=30)
    normas = _extraer_normas(citas)
    estado = estado_principal(db, dictamen_id=r["id"])
    antecedentes, criterio = _separar_antecedentes_criterio(texto)

    lineas = [
        "FICHA DOCTRINAL — DICTAMEN CGR",
        "───────────────────────────────",
        f"Identificación: Dictamen N° {r['numero']}" + (f", de {r['anio']}" if r['anio'] else ""),
        f"Materia: {materia}",
        f"Normas aplicadas: {'; '.join(normas) if normas else 'sin citas normativas explícitas en el corpus'}",
        f"Quién lo requirió: {r['organismo_consultante'] or 'No identificado en el corpus'}",
        f"Fecha: {r['fecha'] or '—'}",
        f"ESTADO DEL CRITERIO: {estado['estado']}",
        f"Fundamento del estado: {estado['descripcion']}",
    ]
    if breve:
        lineas += [
            "Antecedentes:",
            "  " + (antecedentes or "No extraídos.").strip(),
            "Criterio (razón de decidir):",
            "  " + (criterio or "No identifico una razón de decidir separada; revisar texto completo.").strip(),
            "Fuente oficial: " + url_oficial_dictamen(r),
            "UNID Contraloría: " + (r["unid"] or "—"),
        ]
        return "\n".join(lineas)

    if estado.get("detalle"):
        lineas.append("Línea de evolución del criterio:")
        for e in estado["detalle"]:
            lineas.append(f"  • {e['estado']} — {e['descripcion']} ({e['fuente']})")
    lineas.append("Antecedentes jurisprudenciales (grafo de citaciones):")
    if citas:
        lineas.extend(
            f"  • [{c['tipo']}] {c['source_kind']} {c['source_id']} → {c['target_kind'] or 'external'}: "
            f"{c['target_external_ref'] or c['target_id'] or '—'}"
            for c in citas[:10])
    else:
        lineas.append("  • Sin aristas registradas en el corpus local.")
    lineas.append("Antecedentes:")
    lineas.append("  " + (antecedentes or "No extraídos.").strip())
    lineas.append("Criterio (razón de decidir):")
    lineas.append("  " + (criterio or "No identifico razón de decidir separada; usar texto completo.").strip())
    lineas.append("Por qué importa: dictamen que define posición doctrinal de la Contraloría frente a la "
                  "cuestión; su estado señala si sigue siendo aplicable como fundamento.")
    lineas.append("Fuente oficial: " + url_oficial_dictamen(r))
    lineas.append("UNID Contraloría: " + (r["unid"] or "—"))
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Boletín de criterios nuevos (criterio editorial del corpus)
# ---------------------------------------------------------------------------
def _es_nuevo_criterio(db, r: dict) -> tuple[bool, str]:
    citas = db.get_citas(source_kind="dictamen", source_id=r["id"], limit=40)
    estados = db.get_criterios(r["id"])
    motivos: list[str] = []
    if any(e["estado"] in ("DEROGADO", "RECONSIDERADO") for e in estados):
        motivos.append("reconsidera o altera un criterio previo")
    if any(c["tipo"] == "funda" for c in citas):
        motivos.append("establece fundamento doctrinal (funda)")
    texto = _normaliza(r["sumario"] or "")
    if any(k in texto for k in ("criterio", "doctrina", "se ajusta a derecho", "conforme a derecho",
                                "estima que", "cabe concluir", "procede acoger")):
        motivos.append("fija posición doctrinaria")
    return bool(motivos), "; ".join(motivos[:3]) or "sin señales de nuevo criterio"


def criterios_nuevos_corpus(db, dias: int = 30, limite: int = 10) -> list[dict]:
    """Dictámenes del corpus local que constituyen criterio doctrinal nuevo (estructurado).

    Sirve de insumo para el boletín legible y para la vigilancia periódica.
    """
    desde = (datetime.now() - timedelta(days=dias)).date()
    filas = db._conn.execute(
        "SELECT id, numero, anio, fecha, organismo_consultante, sumario, unid "
        "FROM cgr_dictamenes WHERE fecha >= ? ORDER BY fecha DESC",
        (desde.isoformat(),)).fetchall()
    out: list[dict] = []
    for r in filas:
        es, motivo = _es_nuevo_criterio(db, r)
        if not es:
            continue
        d = dict(r)
        out.append({
            "id": d["id"],
            "numero": d["numero"],
            "anio": d["anio"],
            "fecha": d["fecha"],
            "organismo_consultante": d["organismo_consultante"],
            "materia": materia_de(numero=d["numero"], anio=d["anio"],
                                  organismo_consultante=d["organismo_consultante"],
                                  texto=d["sumario"] or ""),
            "motivo": motivo,
            "unid": d["unid"],
            "url": url_oficial_dictamen(d),
        })
        if len(out) >= limite:
            break
    return out


def boletin_criterios(db, dias: int = 7, limite: int = 10) -> str:
    seleccion = criterios_nuevos_corpus(db, dias=dias, limite=limite)
    lineas = [
        f"BOLETÍN DE CRITERIOS NUEVOS — CGR (últimos {dias} días del corpus local)",
        "──────────────────────────────────────────────────────────────────────",
    ]
    if not seleccion:
        lineas.append("Sin dictámenes que califiquen como criterio nuevo en el periodo.")
        return "\n".join(lineas)
    for c in seleccion:
        lineas.append(f"• Dictamen N° {c['numero']}" + (f" de {c['anio']}" if c['anio'] else "")
                      + f" ({c['fecha']}) — {c['materia']}")
        lineas.append(f"  Motivo: {c['motivo']}")
        lineas.append(f"  Solicitante: {c['organismo_consultante'] or '—'}")
        lineas.append("")
    lineas.append("Nota: cobertura limitada a dictámenes presentes en el corpus local CGR.")
    return "\n".join(lineas)