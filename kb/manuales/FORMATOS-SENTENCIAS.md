# FORMATOS-SENTENCIAS

**Categoría:** formatos | **ID:** 5

---

# FORMATOS DE SENTENCIAS — Juzgado de Policía Local de [COMUNA]

Estructura exacta extraída de las plantillas reales del tribunal
(`modelos\consolidado\plantillas\sentencias` y modelos de actuario [ACTUARIO]).

---

## 1. ESTRUCTURA COMÚN A TODAS LAS SENTENCIAS

Toda sentencia definitiva sigue este esqueleto, con variantes según la materia:

```
PRIMER JUZGADO DE POLICÍA LOCAL DE [COMUNA]
QUILLOTA Nº 0152

ROL Nº [ROL]
FOJAS: [FOJAS]                      ← solo en algunas materias
[CIUDAD], [DÍA] DE [MES] DE DOS MIL [AÑO].

VISTOS:
1.- Denuncia/querella/reclamo formulado a fojas [N], por [DENUNCIANTE], en
    contra de [NOMBRE DENUNCIADO], C.I. Nº [RUT], con domicilio en [DOMICILIO],
    por: [DESCRIPCIÓN DE LA INFRACCIÓN].
2.- [Antecedentes procesales: contestación/descargos, prueba rendida,
    conciliación, comparendos, etc.]

CONSIDERANDO:

PRIMERO: Que, conforme lo dispone el artículo 14 de la Ley 18.287, los
Tribunales de Policía Local apreciarán la prueba de acuerdo a las reglas de la
sana crítica.

SEGUNDO: Que de la prueba rendida, esto es, [DENUNCIA / PARTE / TESTIFICACIONES
/ PERITAJE / DOCUMENTOS], aparece acreditado que [HECHOS ACREDITADOS].

TERCERO: Que [análisis jurídico: calificación de la infracción, valoración de
descargos, idoneidad de testigos, prescripción, etc.].

CUARTO: Que, en consecuencia, [conclusión: corresponde condenar / absolver /
tener por prescrita la acción].

Y TENIENDO PRESENTE lo dispuesto en los artículos 1, 3, 4, 7, 8, 9, 10, 11, 12,
13, 14, 15, 16 y 18 de la Ley 18.287 y [artículos sancionadores de la ley de
fondo], SE DECLARA:

I.- QUE SE CONDENA / SE ABSUELVE a [NOMBRE], ya individualizado, ...
II.- [Sanciones accesorias: suspensión de licencia, costas, etc.]
III.- Si no se pagare la multa dentro de los cinco días, despáchese orden de
     arresto hasta por treinta días.
IV.- Para los efectos establecidos en los artículos 24 y 24 bis de la Ley
     18.287, si no pagare dentro del plazo legal de cinco días, comuníquese por
     el Sr. Secretario al Registro de Multas de Tránsito no pagadas.

REGÍSTRESE, NOTIFÍQUESE Y ARCHÍVESE.

Pronunciada por [DON/DOÑA] [NOMBRE JUEZ], [CARGO] del Primer Juzgado de Policía
Local de [COMUNA].

SECRETARIA
```

Fórmulas invariables:
- Considerando PRIMERO siempre cita el art. 14 de la Ley 18.287 (sana crítica).
- Parte resolutiva encabezada por «Y TENIENDO PRESENTE ... SE DECLARA:».
- Cierre: «REGÍSTRESE, NOTIFÍQUESE Y ARCHÍVESE.» + firma del juez + SECRETARIA.

---

## 2. SENTENCIA DE TRÁNSITO POR CHOQUE (condenatoria simple)

Fuente: `01_sentencia_transito_choque.txt`

VISTOS:
1. Denuncia de Carabineros/inspector contra el conductor, RUT y domicilio, por
   daños en choque.
2. Contestación del denunciado ratificando o negando los hechos.
3. Prueba documental acompañada (parte policial, croquis, presupuesto).
4. Conciliación: se produce / no se produce.
5. Comparendo de prueba: testimonial, absolución de posiciones, peritaje.

CONSIDERANDO: sana crítica (art. 14 L.18.287); acreditación del choque y de la
culpa; descarte de descargos.

SE DECLARA:
- Condena a multa de [MONTO] U.T.M. vigente al momento del pago.
- Suspensión de licencia por [Nº] días, entrega de la licencia en la causa
  dentro de cinco días siguientes a la notificación.
- Orden de arresto hasta por treinta días si no se paga en cinco días.
- Comunicación al Registro de Multas de Tránsito no pagadas (arts. 24 y 24 bis
  L.18.287).

---

## 3. SENTENCIA DE TRÁNSITO POR CHOQUE CON PRUEBA TESTIMONIAL

Fuente: `02_sentencia_transito_choque_testigos.txt`

Igual que la anterior, pero el VISTOS incluye:

> 3.- Que en la audiencia respectiva se recibió la prueba testimonial de
> don/doña [NOMBRE TESTIGO], C.I. Nº [RUT], quien [EXPRESA CIRCUNSTANCIAS DE
> TIEMPO, MODO Y LUGAR / señala ser testigo presencial de los hechos].

y el CONSIDERANDO agrega un considerando específico sobre el testigo:

> TERCERO: Que el testigo de la parte denunciante [CORROBORA LO EXPUESTO EN LA
> DENUNCIA / NO RESULTA IDÓNEO PARA DESVIRTUAR LOS DESCARGOS], no existiendo
> tachas ni contradicciones que hagan desmerecer su testimonio, el que se valora
> conforme a la sana crítica.

---

## 4. SENTENCIA POR PAGO CON 25% DE DESCUENTO (Ley 19.676)

Fuente: `08_sentencia_transito_pago_25porciento.txt`

Se dicta cuando el denunciado pagó la multa con el 25% de descuento (Ley Nº
19.676). VISTOS consigna: denuncia y constancia de que el denunciado pagó con
el 25% de descuento con fecha previa.

CONSIDERANDO (según plantilla):
- PRIMERO: la Ley Nº 19.676 estableció el régimen de descuento para el pago
  voluntario de multas por infracciones a la Ley del Tránsito, dentro del
  quinto día hábil siguiente a la notificación de la sentencia.
- SEGUNDO: acreditado el pago con el 25% de descuento sobre el total de la
  sanción, se ha dado cumplimiento a la sentencia recaída en autos.
- TERCERO: la multa pagada correspondió al 75% de la multa original.

SE DECLARA:
- I.- QUE SE TIENE POR CUMPLIDA la sentencia recaída en autos, en atención al
  pago efectuado por el infractor con el 25% de descuento, correspondiente a
  la suma de $[MONTO PAGADO].
- II.- Sin otras costas.

Nota: NO citar «artículo 12 de la Ley 18.287» como fundamento de este beneficio
(versión anterior errónea de este manual); el régimen del 25% es de la **Ley
Nº 19.676**, como lo cita la plantilla. El pago anticipado del art. 22 incs.
3º-4º Ley 18.287 es una figura distinta (pago posterior a la denuncia que pone
término a la causa; ver PLAZOS.md).

---

## 5. SENTENCIA ABSOLUTORIA (variante general / consumidor)

Fuente: `09_sentencia_absolutoria_consumidor.txt` (adaptable a otras leyes)

VISTOS:
1. Denuncia a fojas [N] contra el denunciado, por infracción a la [LEY],
   consistente en: [DESCRIPCIÓN].
2. Acta que da cuenta de la denuncia efectuada ante [Carabineros/SERNAC/
   inspector municipal].
3. Ratificación del denunciante, exposición de su dicho.
4. Denunciado: no compareció / compareció y formuló descargos.

CONSIDERANDO:
- SEGUNDO: «Que de la prueba rendida en autos no aparece suficientemente
  acreditada la infracción denunciada..., no habiéndose [APORTADO PRUEBA
  SUFICIENTE / DESVIRTUADO LA PRESUNCIÓN DE INOCENCIA DEL DENUNCIADO].»
- TERCERO: «Que no constando los elementos que configuran la infracción, así
  como la responsabilidad del denunciado, corresponde absolverlo.»

SE DECLARA:
- I.- QUE SE ABSUELVE a [NOMBRE], de la infracción que le fuera denunciada,
  disponiéndose el sobreseimiento de la causa.
- II.- Sin costas.

---

## 6. SENTENCIA LEY DEL CONSUMIDOR (19.496)

Fuente: `03_sentencia_consumidor.txt`

VISTOS: querella infraccional y demanda civil de indemnización de perjuicios;
contestación; conciliación (se produce / no se produce); prueba documental
(boletas, facturas, informes SERNAC), testimonial y pericial.

CONSIDERANDO: además de la sana crítica, se citan los artículos de la Ley
Nº 19.496 que sancionan la conducta (la plantilla usa como lista tipo:
**arts. 23, 24, 25, 28, 38, 39, 40 y 41**) y se cuantifica el daño emergente
con la prueba rendida.

SE DECLARA (condenatoria):
- I.- Que se condena a [NOMBRE] a la pena de multa de [MONTO] U.T.M., vigente
  al momento del pago, por la infracción a la Ley Nº 19.496.
- II.- [SÓLO SI SE ACOGE DEMANDA CIVIL:] Que se acoge la demanda civil y se
  condena al demandado a pagar la suma de $[MONTO] por concepto de [DAÑOS /
  DEVOLUCIÓN DE LO PAGADO / GARANTÍA], con reajustes e intereses conforme al
  artículo 18 de la Ley Nº 19.496 (cita textual de la plantilla).
- III.- Arresto sustitutivo y Registro de Multas (fórmulas generales).

⚠️ No citar «artículo 41 bis» ni «artículo 41 bis inciso final» de la Ley
19.496: ese artículo no existe en el corpus (`leyes\Ley_19496_Consumidor.md`).
La cita de intereses/reajustes es el art. 18, tal como lo trae la plantilla.
Variante absolutoria: ver §5.

---

## 7. SENTENCIA DE COPROPIEDAD (Ley 21.442)

Fuente: `04_sentencia_copropiedad.txt`

VISTOS: denuncia del administrador/consejo de copropietarios contra un
copropietario por infracción al reglamento de copropiedad; descargos; prueba.

CONSIDERANDO: competencia de la policía local (**art. 44 L.21.442**, no art.
30); acreditación de la calidad de copropietario y de la infracción al
reglamento; sanción según el rango del **art. 88 L.21.442** (menos graves:
multa 1–4 UTM; graves y gravísimas: multa a beneficio fiscal 5–10 UTM; leves:
amonestación), sin perjuicio de rangos propios de cada artículo infringido
(p. ej. art. 27: 1–3 UTM, duplicable por reincidencia).

SE DECLARA:
- Condena a multa de [N] UTM (dentro del rango aplicable) [y orden de cesar la
  conducta contraria al reglamento, si procede].
- Costas.

---

## 8. SENTENCIA RECLAMO LICENCIA DE CONDUCIR DENEGADA

Fuente: `05_sentencia_licencia_denegada.txt`

Encabezado igual; sin FOJAS.

VISTOS:
Reclamo interpuesto por [NOMBRE], RUT, domicilio, en contra de la resolución
[ORDINARIO/RESOLUCIÓN Nº] de fecha [FECHA], de la Dirección de Tránsito de la
I. Municipalidad de [COMUNA], que denegó la renovación/otorgamiento de licencia
clase [CLASE], por no reunir los requisitos de [IDONEIDAD MORAL / APTITUD FÍSICA
/ PSÍQUICA / CAUSAL].

VISTOS Y CONSIDERANDO: (este tipo une ambos epígrafes)
- PRIMERO: cita el **art. 15 de la Ley Nº 18.290** (rechazo con señalación de
  causal por el Director de Tránsito, inc. 2º; reclamo ante el Juez de Policía
  Local dentro de cinco días hábiles desde la notificación, quien resuelve
  breve y sumariamente apreciando la prueba en conciencia y sin recurso
  posterior, inc. 3º). ⚠️ La plantilla dice «inciso final»: corresponde a los
  incisos 2º y 3º del art. 15 (el inciso final trata de los exámenes
  prácticos). La plantilla añade además «previo informe de la Dirección de
  Tránsito», exigencia práctica del tribunal no literal del precepto.
- SEGUNDO: informe de la Dirección de Tránsito (oficio Nº, hoja de vida,
  condenas anteriores).
- TERCERO: análisis de si la causal denegatoria está acreditada.
- CUARTO: sana crítica (art. 14 L.18.287).

SE DECLARA:
- I.- QUE SE [ACOGE / RECHAZA] EL RECLAMO...
- II.- En consecuencia, [se ordena otorgar la licencia una vez cumplidos los
  demás requisitos legales, dejándose sin efecto la resolución recurrida / se
  confirma la resolución recurrida].

Y TENIENDO PRESENTE: la plantilla cierra con «los artículos 15 y siguientes de
la Ley Nº 18.290».

Modelos reales (documento fuente del tribunal, *SENTENCIA ACOGE RECLAMACION*): el
considerando 1º transcribe lo invocado por la Dirección de Tránsito (incluida
su cita histórica «art. 16 Ley 19.495»); los considerandos de fondo citan el
**art. 15 inc. 3º** (reclamo), el **art. 16 L.18.290** (condenas que califican
la idoneidad moral en los 5 años anteriores) y el **art. 20 inc. 1º
L.18.290** (período de control condicional de la idoneidad declarada,
típicamente 4 años); resolutiva «teniendo presente los artículos 15 y 20 de la
Ley Nº 18.290».

### Variante resolutiva: licencia con vigencia restringida por [PLAZO]

Fuente: documentos fuente del tribunal (*Denegación causa 9822-18, se concede
por seis meses* y *denegación causa 23050-18, se concede por un año*).

Cuando el reclamo se acoge pero el tribunal estima prudente un **período de
evaluación previo a la licencia definitiva**, la parte resolutiva concede la
licencia con vigencia/plazo restringido (fórmula generalizada: «se concede la
licencia por [PLAZO]», siendo los plazos observados en los modelos reales
**seis meses** y **un año**):

> `Que se acoge al reclamo interpuesto por [NOMBRE], en contra de la resolución del Director de Tránsito y Transporte Público del Departamento de Tránsito de [COMUNA], de fecha [FECHA], y se declara que tiene idoneidad moral para otorgarle licencia para conducir vehículos clase [CLASE], con vigencia restringida a seis meses.`

> `...y se declara que tiene idoneidad moral para otorgarle licencia para conducir vehículos clase [CLASE], restringida por un año.`

Fundamento típico del considerando habilitante (art. 16 L.18.290): si dentro
del quinquenio anterior a la solicitud sólo registra UNA condena, ello
justifica otorgar la licencia, «pero con vigencia restringida a seis meses,
lapso en que se tendrá que evaluar, a su vencimiento, la conducta desplegada
por el reclamante en esta nueva etapa de conductor». Si se exige, condicionar
además a que el reclamante apruebe los exámenes correspondientes.

Rasgos de estos fallos:
- Mismo epígrafe doble `VISTOS Y CONSIDERANDO:` con considerandos numerados
  (`1°.-`, `2º.-`, ...): informe denegatorio del Director de Tránsito
  (ordinario Nº y fecha), hoja de vida del conductor con las condenas, escrito
  de reconsideración del reclamante, certificados de estado de la causa que
  acreditan cumplimiento íntegro de condenas y multas, alcoholemia de control
  si existe, y el considerando del quinquenio (art. 16 L.18.290).
- Cierre de fundamentos: «en mérito de lo expuesto, documentos acompañados y
  lo prescrito en los artículos 13 Nº 3, 14 bis, 15 y 16 de la Ley 18.290».
- Cierre de trámite propio de esta variante: `Notifíquese esta sentencia
  personalmente o por cédula al reclamante y ofíciese al Señor Director del
  Depto. de Tránsito de [COMUNA] y director del Servicio de Registro Civil e
  Identificación, remitiendo copia autorizada del presente fallo. Una vez
  hecho, archívese.` (coincide con el oficio Nº 1 del manual OFICIOS).

---

## 9. SENTENCIA CON PRESCRIPCIÓN (aseo y ornato)

Fuente: `06_sentencia_aseo_prescripcion.txt`

VISTOS: denuncia por infracción a la ordenanza municipal de aseo; no
comparecencia o descargos; constancia del tiempo transcurrido.

CONSIDERANDO:
- Un considerando establece la fecha de comisión del hecho y la de notificación
  válida del comparendo.
- El fundamento correcto de la prescripción de la acción persecutoria es el
  **art. 54 inciso 2º de la Ley Nº 15.231**: las acciones para perseguir la
  responsabilidad por contravenciones prescriben en **seis meses** contados
  desde la fecha de la infracción, y se **interrumpen** con la deducción de la
  demanda, denuncia o querella (art. 54 inciso final Ley 15.231).
- ⚠️ La plantilla `06_sentencia_aseo_prescripcion.txt` cita «artículo 16 de la
  Ley Nº 18.287» y algunos modelos citan «art. 20»: ambas citas son ERRÓNEAS
  (el art. 16 L.18.287 regula diligencias probatorias y el art. 20 la
  suspensión condicional de la pena). Citar art. 54 incs. 2º y final Ley
  15.231; mantener las citas antiguas sólo como variante histórica documentada.

SE DECLARA:
- QUE SE TIENE POR PRESCRITA LA ACCIÓN PARA PERSEGUIR LA INFRACCIÓN... y se
  sobresee / absuelve al denunciado, archivándose los antecedentes.
- En aseo municipal la plantilla ordena además oficiar al Tesorero Municipal /
  Director de Administración y Finanzas para certificado de deuda antes de
  resolver en definitivo (estructura del VISTOS/SE DECLARA de la plantilla).

---

## 10. SENTENCIA EN REBELDÍA (no comparecencia del denunciado)

Fuente: `07_sentencia_rebelde.txt`

VISTOS: denuncia; certificado de notificación válida del comparendo; no
comparecencia; prueba de cargo incorporada.

CONSIDERANDO:
- El no comparecimiento habiendo sido legalmente citado permite declararlo
  rebelde y tenerlo por confeso / por acreditados los hechos (art. 13 L.18.287,
  que ordena comparecencia personal bajo los apercibimientos del art. 380 CPC;
  arts. 380 y 390 CPC: dar por confeso). ⚠️ No citar el art. 13 como
  «agravante de rebeldía»: la Ley 18.287 no contiene tal norma; la valoración
  de la incomparecencia se hace vía sana crítica sobre la prueba de cargo.
- La sentencia puede fundarse en la prueba de cargo existente.

SE DECLARA: condena a multa de [MONTO] UTM [eventualmente aumentada en
consideración a las circunstancias], penas accesorias si corresponden, arresto
sustitutivo y comunicación al Registro de Multas. Pronunciada por el juez;
firman juez y actuario.

---

## 11. SENTENCIA LEY DE ALCOHOLES (Ley de Tránsito DFL 1/2007; antecedente histórico Ley 17.105)

Fuente: documento fuente del tribunal (*SENTENCIA ALCOHOL*)
(condenatoria y absoluta)

### 11.1 Condenatoria por manejo bajo la influencia del alcohol

VISTOS: denuncia de Carabineros por conducir bajo la influencia del alcohol
(arts. 110, 111 y 193 de la Ley de Tránsito, DFL Nº 1/2007 — texto actual;
los modelos históricos citan el art. 1º Nº 2 b) de la Ley 17.105, hoy
refundido en esas normas); control preventivo / alcoholemia positiva;
descargos; prueba (parte policial, protocolo de alcoholemia, testigos).

CONSIDERANDO:
- Validez del procedimiento de detección (control preventivo fundado, registro
  de la alcoholemia, cadena de custodia del protocolo).
- Tasa de alcohol registrada (art. 111 DFL 1/2007): superior a 0,3 e inferior
  a 0,8 g/l → manejo bajo la influencia; igual o superior a 0,8 g/l →
  ebriedad.
- Descarte de vicios formales que invaliden la prueba.

SE DECLARA:
- Condena a multa de [1–5 UTM] (art. 193 DFL 1/2007) y suspensión de licencia
  por [3 meses] (o inhabilitación absoluta en caso de embriaguez).
- Comunicaciones al Registro Nacional de Conductores y al SRVI.

### 11.2 Absoluta (alcoholemia no probada o procedimiento viciado)

Mismos VISTOS; CONSIDERANDO que el protocolo de alcoholemia carece de validez
(falta de fundamento del control preventivo, error en el registro, negativa no
acreditada) o que la tasa no alcanza el umbral legal.

SE DECLARA:
- I.- QUE SE ABSUELVE a [NOMBRE] de la infracción que le fuera denunciada,
  disponiéndose el sobreseimiento de la causa.
- II.- Sin costas.

---

## 12. SENTENCIA COMERCIO AMBULANTE / ACTIVIDADES SIN AUTORIZACIÓN

Fuente: `10_sentencia_comercio_ambulante.txt`

VISTOS: denuncia municipal por comercio ambulante sin autorización (ordenanza
municipal / Ley de Rentas Municipales); parte policial con decomiso; descargos.

CONSIDERANDO: acreditación de la actividad comercial sin permiso en la vía
pública; infracción a la ordenanza citada; facultad sancionatoria municipal.

SE DECLARA:
- Condena a multa de [N] UTM.
- Decomiso de la mercadería si procede / devolución.
- Costas.

---

## 13. SENTENCIA CON ACUMULACIÓN DE INFRACCIONES (absolución)

Fuente: documento fuente del tribunal (*SENTENCIA ACUMULACION ABSUELTO*) (dos
versiones: modelo general y versión de actuario [ACTUARIO])

Se usa cuando hay dos o más causas acumuladas contra el mismo denunciado.

VISTOS:
1. Denuncia de fojas [N] de Carabineros en contra de [NOMBRE], RUT, domicilio,
   por infracción al art. [X] de la Ley 18.290 (u otra), consistente en
   [DESCRIPCIÓN].
2. Segunda denuncia de fojas [N] de Carabineros contra el mismo, por infracción
   al art. [X] de la Ley 18.290 (u otra), consistente en [DESCRIPCIÓN].
3. Resolución que decretó la acumulación de ambas causas para su tramitación y
   fallo conjunto.
4. Contestación del denunciado que niega los hechos.
5. Comparendo de prueba: declaraciones de Carabineros, testigos, etc.
6. Sentencias anteriores del denunciado (para reincidencia, si consta).

CONSIDERANDO:
- PRIMERO: sana crítica (art. 14 L.18.287).
- SEGUNDO: análisis prueba por prueba; cada infracción debe probarse por
  separado.
- TERCERO: «Que de las pruebas rendidas no aparecen suficientemente
  acreditadas las infracciones denunciadas, no habiéndose desvirtuado la
  presunción de inocencia del denunciado».
- CUARTO: corresponde absolver.

Y TENIENDO PRESENTE los arts. 1, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 y 18
de la Ley 18.287 y arts. [de fondo], SE DECLARA:
- I.- QUE SE ABSUELVE a [NOMBRE] de las infracciones que le fueran denunciadas,
  disponiéndose el sobreseimiento de la causa.
- II.- Sin costas.

REGÍSTRESE, NOTIFÍQUESE Y ARCHÍVESE + firmas.

Regla práctica de redacción: cada acumulada genera DOS números en el VISTOS
(una denuncia por número) y el considerando de absolución habla en plural
(«las infracciones», «las pruebas»).

---

## 14. NOTAS DE ESTILO TRANSVERSALES

- Los montos de multa se expresan en UTM («multa de [MONTO] U.T.M., vigente al
  momento del pago»).
- El arresto sustitutivo es hasta por 30 días si no se paga la multa en 5 días.
- Toda condena por tránsito incluye la cláusula del Registro de Multas de
  Tránsito no pagadas (arts. 24 y 24 bis L.18.287) cuando procede.
- La suspensión de licencia exige ordenar la entrega física de la licencia en
  la causa dentro de 5 días.
- En causas absolutas se agrega «II.- Sin costas.» y «sobreseimiento de la
  causa».
- Epígrafe doble «VISTOS Y CONSIDERANDO:» solo se observa en reclamos de
  licencia (§8); en el resto se separa VISTOS / CONSIDERANDO.
