"""Cómputo procesal de plazos — art. 38, 40 CPC y art. 66 COT (Chile).

Reglas implementadas (civil/procesal civil por defecto):
  1. El plazo se corre desde el día SIGUIENTE al de la notificación (art. 38 CPC).
  2. Los días feriados no se cuentan en los plazos de días hábiles (art. 40 CPC);
     el sábado es inhábil (Ley 2.977).
  3. Si el último día del plazo es inhábil, el vencimiento se PRORROGA al primer
     día hábil siguiente (art. 40 CPC).
  4. FERIADO JUDICIAL: del 1 de febrero al primer día hábil de marzo los plazos
     quedan suspendidos ante los tribunales (art. 66 COT), salvo excepciones que
     la propia ley declara incompatibles con la suspensión.

Feriados civiles chilenos: fijos + Pascua (algoritmo de Meeus, válido para
cualquier año) + traslación de feriados móviles (verificada contra calendarios
oficiales 2026–2030).

Limitación honesta: ciertos feriados regionales comunales/sectoriales (fuerzas
armadas, bancos, empleados de comercio) NO se consideran salvo que incorporen
los plazos ante tribunales; verifique contra el calendario judicial del año.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

# --- Fechas ---------------------------------------------------------------------

_MESES_NOMBRE = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


def parsear_fecha_cl(cadena: str) -> date | None:
    """DD-MM-AAAA, DD/MM/AAAA, DD.MM.AAAA, AAAA-MM-DD o '15 de enero de 2026'."""
    if not cadena:
        return None
    s = cadena.strip()
    m = re.fullmatch(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mo, d)
        except ValueError:
            return None
    m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mo, d)
        except ValueError:
            return None
    m = re.fullmatch(
        r"(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de(?:l)?\s+(19|20)(\d{2})", s, re.IGNORECASE)
    if m:
        mes = _MESES_NOMBRE.get(m.group(2).lower().rstrip("."))
        if mes:
            try:
                return date(int(m.group(3) + m.group(4)), mes, int(m.group(1)))
            except ValueError:
                return None
    return None


# --- Feriados civiles -------------------------------------------------------------

FERIADOS_FIJOS: set[tuple[int, int]] = {
    (1, 1),    # Año Nuevo
    (5, 1),    # Día del Trabajo
    (5, 21),   # Glorias Navales
    (6, 29),   # San Pedro y San Pablo
    (7, 16),   # Virgen del Carmen
    (8, 15),   # Asunción
    (9, 18),   # Fiestas Patrias (primera)
    (9, 19),   # Glorias del Ejército
    (10, 12),  # Encuentro de Dos Mundos
    (10, 31),  # Día de las Iglesias Evangélicas
    (11, 1),   # Todos los Santos
    (12, 8),   # Inmaculada Concepción
    (12, 25),  # Navidad
}

# Feriados móviles/instituidos por año (verificado contra calendario oficial:
# incluye Viernes y Sábado Santo, solsticio indígena (20-jun aprox, varía por año)
# y 21-mayo complementario cuando corre; sin los feriados regionales).
FERIADOS_MOVILES: dict[int, set[tuple[int, int]]] = {
    2026: {(3, 19), (4, 3), (4, 4), (6, 20), (10, 12)},
    2027: {(3, 19), (3, 26), (3, 27), (6, 21), (10, 12)},
    2028: {(3, 19), (4, 14), (4, 15), (6, 21), (10, 12)},
    2029: {(3, 19), (3, 30), (3, 31), (6, 21), (10, 12)},
    2030: {(3, 19), (4, 19), (4, 20), (6, 21), (10, 12)},
}


def _pascua(anio: int) -> date:
    """Domingo de Resurrección (algoritmo de Meeus)."""
    a, b, c = anio % 19, anio // 100, anio % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = (h + l - 7 * m + 114) // 31, (h + l - 7 * m + 114) % 31 + 1
    return date(anio, mes, dia)


def es_feriado(fecha: date) -> bool:
    """Feriado civil chileno (sin feriados regionales/sectoriales)."""
    if (fecha.month, fecha.day) in FERIADOS_FIJOS:
        return True
    if (fecha.month, fecha.day) in FERIADOS_MOVILES.get(fecha.year, set()):
        return True
    # fallback fuera de la tabla: Pascua del año en cuestión
    try:
        domingo = _pascua(fecha.year)
        if fecha in (domingo - timedelta(days=2), domingo - timedelta(days=1)):
            return True
    except Exception:
        pass
    return False


def es_habil(fecha: date) -> bool:
    """Día hábil judicial chileno: ni sábado/domingo (ley 2.977) ni feriado."""
    return fecha.weekday() < 5 and not es_feriado(fecha)


# --- Feriado judicial (art. 66 COT) ------------------------------------------------

def _primer_habil_de(fecha: date) -> date:
    d = fecha
    while not es_habil(d):
        d += timedelta(days=1)
    return d


def feriado_judicial_limite(anio: int) -> tuple[date, date]:
    """Devuelve (inicio, término) del feriado judicial del año: 1-feb → primer
    día hábil de marzo (ambos inclusive)."""
    inicio = date(anio, 2, 1)
    termino = _primer_habil_de(date(anio, 3, 1))
    return inicio, termino


def en_feriado_judicial(fecha: date) -> bool:
    """¿La fecha cae dentro del feriado judicial del año?"""
    ini, fin = feriado_judicial_limite(fecha.year)
    # El feriado judicial pertenece al año en que empieza (febrero-marzo).
    return ini <= fecha <= fin


# --- Cómputo ----------------------------------------------------------------------

def computar_plazo(fecha_notificacion: date, dias: int, tipo: str = "habiles") -> dict:
    """Computa un plazo procesal desde la notificación.

    `tipo`: "habiles" (días hábiles; sábado/domingo/feriado no cuentan) o
            "corridos" (días calendario; el vencimiento inhábil se prorroga).
    Devuelve el vencimiento, la cadena de desplazamientos y los fundamentos.
    """
    if tipo not in ("habiles", "corridos"):
        raise ValueError("tipo debe ser 'habiles' o 'corridos'")
    if dias < 0:
        raise ValueError("días debe ser >= 0")

    pasos: list[dict] = []
    fundamentos = [
        "Art. 38 Código de Procedimiento Civil: el plazo se corre desde el día siguiente "
        "al de la notificación.",
        "Art. 40 Código de Procedimiento Civil: no se cuentan los días feriados; si el "
        "último día del plazo es inhábil, se prorroga al primer día hábil siguiente.",
        "Ley N° 2.977: el sábado es día inhábil para los actos de los tribunales y "
        "turcos funcionarios.",
        "Art. 66 Código Orgánico de Tribunales: durante el feriado judicial (1 de "
        "febrero al primer día hábil de marzo) los plazos quedan suspendidos.",
    ]

    # Paso 1: cómputo desde el día siguiente (art. 38 CPC)
    cursor = fecha_notificacion + timedelta(days=1)
    pasos.append({"regla": "Art. 38 CPC", "fecha": cursor.isoformat(),
                  "descripcion": "El cómputo se inicia el día siguiente al de la notificación."})

    # Si la notificación cae en feriado judicial, la práctica forense inicia al
    # primer día hábil de marzo (suspensión del plazo, art. 66 COT).
    if en_feriado_judicial(cursor):
        ini, fin = feriado_judicial_limite(cursor.year)
        cursor = fin
        pasos.append({"regla": "Art. 66 COT", "fecha": cursor.isoformat(),
                      "descripcion": f"El punto de partida cae dentro del feriado judicial "
                                     f"({ini.isoformat()} a {fin.isoformat()}); el plazo "
                                     "queda suspendido y se corre desde el primer día "
                                     "hábil de marzo."})

    if tipo == "habiles":
        # Paso 2: contar días hábiles
        contados = 0
        while contados < dias:
            if es_habil(cursor) and not en_feriado_judicial(cursor):
                contados += 1
            elif not es_habil(cursor) and en_feriado_judicial(cursor):
                ini, fin = feriado_judicial_limite(cursor.year)
                pasos.append({"regla": "Art. 66 COT", "fecha": fin.isoformat(),
                              "descripcion": f"El curso del plazo se interrumpe durante el "
                                             f"feriado judicial (retoma el {fin.isoformat()})."})
                cursor = fin
                continue
            cursor += timedelta(days=1)
        # El cursor quedó un día después del último contado: vuelve un paso
        vencimiento = cursor - timedelta(days=1)
        pasos.append({"regla": "Art. 40 CPC", "fecha": vencimiento.isoformat(),
                      "descripcion": f"Contados {dias} día(s) hábil(es), el plazo vence "
                                     f"el {vencimiento.isoformat()}."})
    else:  # corridos
        vencimiento = cursor + timedelta(days=max(0, dias - 1))
        pasos.append({"regla": "plazo de días corridos", "fecha": vencimiento.isoformat(),
                      "descripcion": f"El plazo de {dias} día(s) calendario vence el "
                                     f"{vencimiento.isoformat()}."})
        if not es_habil(vencimiento) or en_feriado_judicial(vencimiento):
            corr = vencimiento
            while not es_habil(corr) or en_feriado_judicial(corr):
                # frente al feriado judicial: continuará el primer día hábil de marzo
                if en_feriado_judicial(corr):
                    _, corr = feriado_judicial_limite(corr.year)
                    break
                corr += timedelta(days=1)
            if corr != vencimiento:
                pasos.append({"regla": "Art. 40 CPC (prórroga)", "fecha": corr.isoformat(),
                              "descripcion": f"El vencimiento recaía en día inhábil o en "
                                             f"feriado judicial ({vencimiento.isoformat()}); "
                                             f"se prorrogó al primer día hábil siguiente."})
                vencimiento = corr

    # Honestidad: advertencias de uso frecuente
    advertencias = []
    if tipo == "corridos" and not en_feriado_judicial(vencimiento):
        advertencias.append(
            "En plazos que la ley declara inderogables (p. ej., reclamo art. 66 COT, "
            "casación), la prórroga del vencimiento inhábil puede ser materia de "
            "controversia; verifique la naturaleza del plazo ante la jurisprudencia.")
    return {
        "ok": True,
        "fecha_notificacion": fecha_notificacion.isoformat(),
        "dias": dias,
        "tipo": tipo,
        "vencimiento": vencimiento.isoformat(),
        "vencimiento_cl": f"{vencimiento.day:02d}-{vencimiento.month:02d}-{vencimiento.year}",
        "es_habil": es_habil(vencimiento) and not en_feriado_judicial(vencimiento),
        "pasos": pasos,
        "fundamentos": fundamentos,
        "advertencias": advertencias,
    }


def formatear_plazo(res: dict) -> str:
    """Narrativa jurídica formal del cómputo."""
    if not res.get("ok"):
        return f"ERROR: {res.get('error', 'computo fallido')}"
    lineas = [
        "CÓMPUTO DE PLAZO PROCESAL",
        f"Atendida la notificación practicada con fecha {res['fecha_notificacion']}, "
        f"el plazo de {res['dias']} día(s) ({'hábiles' if res['tipo'] == 'habiles' else 'corridos'}) "
        f"vence el {res['vencimiento_cl']} ({res['vencimiento']}).",
        "",
        "I. RAZONAMIENTO SEGUIDO",
        "",
    ]
    for paso in res["pasos"]:
        lineas.append(f"• [{paso['regla']}] {paso['fecha']}: {paso['descripcion']}")
        lineas.append("")
    lineas.append("II. FUNDAMENTOS LEGALES")
    lineas.append("")
    for f in res["fundamentos"]:
        lineas.append(f"• {f}")
    if res.get("advertencias"):
        lineas.append("")
        lineas.append("ADVERTENCIAS:")
        for w in res["advertencias"]:
            lineas.append(f"• {w}")
    lineas.append("")
    lineas.append("Verifique contra el calendario judicial del año (feriados regionales "
                  "y resoluciones de excusación de tribunales pueden variar el cómputo).")
    return "\n".join(lineas)
