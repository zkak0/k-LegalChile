# FORMATOS-COMPARENDOS-DECLARACIONES

**Categoría:** formatos | **ID:** 2

---

# FORMATOS DE COMPARENDOS Y DECLARACIONES — Juzgado de Policía Local de [COMUNA]

Estructura exacta extraída de las plantillas reales del tribunal
(`modelos\consolidado\plantillas\comparendos`).

---

## 1. PROTOCOLO GENERAL DE COMPARENDOS

Fuente: `01_protocolo_comparendos.txt`

Reglas comunes a todo acta de comparendo:

1. **Encabezado**: título del acta + PRIMER JUZGADO DE POLICÍA LOCAL DE
   [COMUNA]; `ACTUARIO: [APELLIDO]`; `[COMUNA], a [FECHA EN LETRAS].`
2. **Apertura**: «Tiene lugar el comparendo [de estilo / de contestación,
   conciliación y prueba] decretado para el día de hoy con la asistencia de...».
   Se individualizan todas las partes presentes y sus abogados (mandato por
   fojas o delegación de poder).
3. **Notificación**: «EL TRIBUNAL: LAS PARTES SE NOTIFICAN EN ESTE ACTO DE
   TODAS LAS RESOLUCIONES DICTADAS EN EL PROCESO.»
4. **Intervenciones de las partes** se marcan con el separador
   `------LA PARTE DE [NOMBRE]:` (o `------LA PARTE DENUNCIANTE/DENUNCIADA`).
5. **Provisión del tribunal siempre en MAYÚSCULAS**, precedida de
   «EL TRIBUNAL:». Al resolver cada solicitud se parte con «COMO SE PIDE...» o
   «EN ACUERDO DE LAS PARTES...»; las demás se resuelven según su mérito.
6. **Cierre invariable**: «Los comparecientes se notifican en este acto de las
   resoluciones que anteceden y previa lectura ratifican y firman con Usía.» +
   [FIRMAS].

Secuencia típica de incidencias dentro del comparendo:
ratificación → contestación escrita → conciliación → prueba documental →
objeciones → solicitudes de cada parte (testigos, posiciones, peritaje,
oficios) → resolución del tribunal → percepción audiovisual si se pide →
absolución de posiciones en la misma audiencia si el absolvente está presente.

---

## 2. ACTA DE COMPARENDO POR ACCIDENTE DE TRÁNSITO (CHOQUES)

Fuente: `02_acta_comparendo_choque.txt`

```
ACTA DE COMPARENDO POR ACCIDENTE DE TRÁNSITO (CHOQUES)
PRIMER JUZGADO DE POLICÍA LOCAL DE [COMUNA]

ACTUARIO: [APELLIDO DEL ACTUARIO]
[CIUDAD], a [FECHA EN LETRAS].
```

Asistentes típicos: querellante/demandante con abogado (mandato de fojas Nº),
querellado/demandado con abogado bajo delegación de poder, y compañía de
seguros/tercero con su abogado.

Bloques en orden:

1. Notificación de resoluciones (fórmula general).
2. **Ratificación del querellante**: ratifica parte policial, declaración
   indagatoria, croquis, querella infraccional y demanda civil de indemnización;
   ratifica documentos acompañados (p. ej. presupuesto) por $[MONTO], con expresa
   condenación en costas.
3. **Contestación del querellado**: contesta por escrito querella y demanda,
   pide rechazo con costas y que el escrito se tenga como parte integrante del
   comparendo. Provisión: «INCORPÓRASE A LA CAUSA ESCRITO DE CONTESTACIÓN...
   TÉNGASE POR CONTESTADA QUERELLA INFRACCIONAL Y DEMANDA CIVIL.»
4. **Conciliación**: «EL TRIBUNAL LLAMA A LAS PARTES A UNA CONCILIACIÓN LA QUE
   [SE PRODUCE EN LOS SIGUIENTES TÉRMINOS: … / NO SE PRODUCE].»
5. **Prueba documental**: lista breve numerada de documentos acompañados con
   citación; objeción modelo vía art. 346 Nº 3 CPC (documento privado simple de
   tercero ajeno al juicio); provisión «TÉNGASE POR OBJETADOS LOS DOCUMENTOS...
   Y DÉJASE SU RESOLUCIÓN PARA DEFINITIVA.»
6. **Solicitudes de cada parte** (numeradas):
   - OFRECE PRUEBA TESTIMONIAL (ratifica lista presentada; constancia de
     testigos presentes y fijación de fecha para la prueba).
   - ABSOLUCIÓN DE POSICIONES (cite al absolvente en primera citación; sobre
     cerrado firmado en custodia de la Secretaria).
   - PERITAJE (perito mecánico/contable; si están TODAS las partes se nombra en
     la misma audiencia; si falta una, audiencia posterior de designación).
   - OFICIOS (Departamento de Tránsito, SEREMI, Carabineros; qué se pide).
7. Provisión tipo: «COMO SE PIDE, CÍTESE AL ABSOLVENTE ... GUÁRDESE EL SOBRE EN
   CUSTODIA ... DESÍGNESE PERITO ... EN ACUERDO DE LAS PARTES ...».
8. Percepción audiovisual: «COMO SE PIDE, debiendo aportar luego el pen drive o
   la transcripción escrita del audio.»
9. **Absolución en la misma audiencia** (si procede): apertura del sobre cerrado
   advirtiendo que está firmado; absolvente previamente juramentado responde
   «Pregunta Nº [N]: ...»; se agrega el pliego; «SE PONE TÉRMINO A ESTA
   DILIGENCIA.»
10. Cierre y firmas.

### Variante CON PRUEBA TESTIMONIAL (testigos citados al día)

Bloque adicional:
- «1º.- Testigo [NOMBRE], C.I. [N], DOMICILIO: ..., PROFESIÓN, OCUPACIÓN U
  OFICIO: ..., quien previo juramento expone.»
- PREGUNTAS DE TACHA («1º.- Para que diga el testigo, ... RESPUESTA: ...») y
  tacha fundada en arts. 358 y ss. CPC. Provisión: «DÉJESE LA TACHA PARA
  DEFINITIVA Y SE ORDENA TOMAR DECLARACIÓN AL TESTIGO.»
- DECLARACIÓN DEL TESTIGO: relato completo (día, lugar, hora, dónde estaba,
  color de vehículos, quién chocó a quién, señalización, lesiones, ambulancia,
  Carabineros).
- REPREGUNTADO y CONTRAINTERROGADO con el mismo formato pregunta/respuesta.
- Si hay oposición a preguntas: traslado y resolución antes de continuar.

---

## 3. ACTA DE COMPARENDO POR LEY DEL CONSUMIDOR (LEY Nº 19.496)

Fuente: `03_acta_comparendo_consumidor.txt`

Partes: denunciante y demandante (comparece por sí o con abogado) y denunciada
y demandada (proveedor/empresa representada por abogado). El comparendo es «de
contestación, conciliación y prueba».

Orden de bloques:

1. Notificación de resoluciones.
2. Ratificación del denunciante (denuncia, indagatoria, demanda, documentos).
3. Contestación escrita de la denuncia y demanda. Provisión completa:
   «TÉNGASE POR CONTESTADA DENUNCIA INFRACCIONAL Y DEMANDA CIVIL; AL SEGUNDO
   OTROSÍ, TÉNGASE POR ACOMPAÑADOS LOS DOCUMENTOS, CON CITACIÓN; AL TERCER
   OTROSÍ, TÉNGASE PRESENTE; AL CUARTO OTROSÍ, COMO SE PIDE, A TRAVÉS DEL
   CORREO ELECTRÓNICO [CORREO]; AL QUINTO OTROSÍ, TÉNGASE PRESENTE LA
   DELEGACIÓN DE PODER CONFERIDA.»
4. Conciliación («la que se produce en los siguientes términos: … / la que no
   se produce. EL TRIBUNAL: QUEDA EN RESOLVER.»).
5. Prueba documental de ambas partes: cada documento identificado con número de
   factura/boleta, fecha y timbre electrónico.
6. Objeciones documentales (art. 346 Nº 3 CPC) y provisión para definitiva.
7. Solicitudes (testigos — verificando presencia de los ofrecidos por escrito—,
   posiciones, peritaje, oficios), con las mismas reglas de designación de
   perito que el choque.
8. Percepción audiovisual: «debiendo aportar en la oportunidad la parte
   interesada la transcripción escrita del audio (DEBE ACOMPÑAR PENDrive)».
9. Absolución de posiciones en la misma audiencia si el absolvente está
   presente.
10. Cierre y firmas.

### Variante SOLO CONCILIACIÓN (sin más incidencias)

Acta mínima:

> Tiene lugar el comparendo de conciliación para el día de hoy con la asistencia
> de la parte denunciante de [NOMBRE] y de la parte denunciada de [NOMBRE], ya
> individualizados en autos. El Tribunal llama a las partes a conciliación, la
> que no se produce. EL TRIBUNAL: QUEDA EN RESOLVER. Los comparecientes se
> notifican en este acto de la resolución que antecede. Previa lectura, ratifican
> y firman ante US.

---

## 4. DECLARACIÓN INDAGATORIA POR ACCIDENTE DE TRÁNSITO (CHOQUE)

Fuente: `04_declaracion_indagatoria_choque.txt`

Formulario que debe completar el involucrado ANTES del comparendo:

```
DECLARACIÓN INDAGATORIA POR ACCIDENTE DE TRÁNSITO (CHOQUE)
PRIMER JUZGADO DE POLICÍA LOCAL DE [COMUNA]

S.J.L. DE POLICÍA LOCAL DE [COMUNA] (1º)

FECHA: [FECHA]
ROL: [ROL]
ACTUARIO: [APELLIDO DEL ACTUARIO]

Comparece don/doña
NOMBRE COMPLETO: [NOMBRE]
RUT Nº: [RUT]
EDAD: [EDAD AÑOS]
ESTADO CIVIL: [ESTADO CIVIL]
PROFESIÓN U OFICIO: [PROFESIÓN U OFICIO]
DOMICILIO COMPLETO: [DOMICILIO]
Nº CELULAR: [CELULAR]
CORREO ELECTRÓNICO: [CORREO]
Solicita notificación a través de correo electrónico: SÍ (   ); NO (   )
```

Bloque de relato, con las siguientes consignas fijas en este orden:

1. **EXPLIQUE DETALLADAMENTE, EN LO POSIBLE: DÍA, HORA, LUGAR DE LOS HECHOS
   (ALTURA), PISTA DE CIRCULACIÓN, DIRECCIÓN Y VELOCIDAD** — relato tipo:
   «El día [FECHA], a las [HORA] horas, conducía el vehículo placa patente
   [PLACA], por [CALLE/AV.], por la [Nº] pista de circulación, a [VELOCIDAD]
   km/h, en dirección [DIRECCIÓN]. Al llegar a la altura de [REFERENCIA], el
   vehículo [MARCA/MODELO/COLOR] placa [PLACA] [MANIOBRA], pasando a llevar
   [ZONA DEL VEHÍCULO], causando daños...»
2. **PASAJEROS U OCUPANTES DE LOS VEHÍCULOS** — quiénes acompañaban; lesiones
   sufridas y gravedad (leves, menos graves, graves).
3. **CARACTERÍSTICAS DE LOS VEHÍCULOS** — tipo, marca, color, año y placa del
   propio y de los demás involucrados.
4. **DAÑOS Y/O LESIONES** — daños propios (p. ej. abolladura delantera, altura
   del parachoques) y de los demás intervinientes.
5. **SEÑALIZACIÓN DE TRÁNSITO, CONDICIONES DE TIEMPO Y CALZADA** — semáforo,
   signos, estado de calzada y clima.
6. **ALCOHOLEMIA** — si fue practicada y resultado.
7. **HECHOS POSTERIORES AL ACCIDENTE** — desde la colisión hasta la denuncia.
8. **OTROS ANTECEDENTES** — lo que estime relevante para el juez.
9. **LICENCIA DE CONDUCIR** — vigente/vencida/retenida en otro tribunal; clase.
10. **CROQUIS**: «Debe adjuntar un croquis que grafique el accidente de autos.»

Cierre: «Previa lectura se ratifica y firma con US.» + FIRMA DEL COMPARECIENTE.

NOTA final del formulario: debe ser firmada y presentada ante el Primer Juzgado
de Policía Local de [COMUNA], presencialmente o por medios electrónicos al
correo [CORREO DEL TRIBUNAL]; puede rellenarse digitalmente; se sugiere
adjuntar fotografía de la cédula de identidad y de la licencia de conductor.

---

## 5. NOTAS DE ESTILO TRANSVERSALES

- Separador de intervención de partes: `------LA PARTE DE [NOMBRE]:`.
- Provisión del tribunal SIEMPRE en mayúsculas, iniciada por «EL TRIBUNAL:».
- Fórmula de resolución favorable: «COMO SE PIDE,...» o «EN ACUERDO DE LAS
  PARTES,...».
- El sobre con pliego de posiciones queda «EN CUSTODIA DEL TRIBUNAL POR LA
  SEÑORA SECRETARIA».
- Designación de perito: en la misma audiencia solo si están TODAS las partes;
  si no, audiencia especial de designación.
- Todo acta termina con notificación en el acto, lectura, ratificación y firmas.
