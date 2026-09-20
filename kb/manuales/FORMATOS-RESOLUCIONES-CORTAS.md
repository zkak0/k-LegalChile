# FORMATOS-RESOLUCIONES-CORTAS

**Categoría:** formatos | **ID:** 4

---

# FORMATOS — RESOLUCIONES CORTAS (JPL [COMUNA])

Manual de estructura exacta de las resoluciones que el tribunal dicta a diario:
acumulación, rebajas, archivos, citaciones, plazos, reclusión sustitutiva,
medidas precautorias, fallos de denegación de licencia y providencias de mesa.
Fuente: documentos fuente del tribunal (con sus versiones).
Complementa `SKILL.md` secciones 3–6.
Todo dato variable va como `[MARCADOR]`. Las frases entre comillas son TEXTUALES
de los modelos reales (sin datos personales).

---

## 0. Convenciones comunes de las resoluciones cortas

### 0.1 Encabezado y fecha
- Las resoluciones cortas **no llevan encabezado ROL/FOJAS** en el cuerpo (el rol va en el margen del sistema). Excepciones: resoluciones con firma de juez y fallos, que sí llevan `CAUSA ROL N° [ROL]-[AÑO]`, `ACTUARIO: [INICIALES]` y `FOJAS: [N] ([N EN LETRAS])`.
- **La fecha SIEMPRE va en letras**, como primera línea: `En [CIUDAD], a [DÍA] de [MES] de [AÑO].`
- Aperturas observadas en los modelos (todas válidas): `En [CIUDAD], a …`, `[COMUNA], a …`, `[CIUDAD], a …`, `En [CIUDAD], a …`. La forma dominante es `En [CIUDAD], a [fecha en letras].`
- Horas y montos van en números (`16:00 hrs.`; `1 U.T.M.`); días, meses y años en letras.

### 0.2 Resolutiva en MAYÚSCULAS
El mandato final va al cierre del párrafo, en mayúsculas: `ACUMÚLESE`, `REBÁJESE`, `ARCHÍVESE`, `ARCHÍVENSE LOS ANTECEDENTES`, `CÍTESE`, `OFÍCIESE`, `NOTIFÍQUESE`, `TÉNGASE POR RECIBIDO`, `AUTOS PARA OÍR SENTENCIA`.
Cuando hay varios mandatos se concatenan: `Ofíciese, una vez hecho, archívese.` / `Remítase esta resolución a [PARTE]. Ofíciese.`

### 0.3 Considerandos
- Resolución corta de un párrafo: **sin considerandos**; arranca directo con `Visto…`, `Atendido…`, `Advirtiendo el tribunal que…`, `No habiendo…`.
- Resolución con fundamento: apertura `VISTOS:` / `VISTOS Y CONSIDERANDO:` y considerandos numerados `1.- Que …`, `2.- Que …` (o romanos `1º.- Que …` en fallos). Un hecho por considerando.

### 0.4 Individualización de causas acumuladas o relacionadas
Siempre **rol completo + actuario**: `causa Rol N° [ROL]-[AÑO], Actuario [INICIALES ACTUARIO].` En sentencias que tienen a la vista otras causas: `causa N° [ROL]-[AÑO] Actuario [INICIALES] de este Tribunal`. Las personas se individualizan con nombre completo + `cédula de identidad N° [RUT]`.

### 0.5 UTM
Fórmula obligatoria completa: `[N] U.T.M. ([N EN LETRAS] UNIDAD(ES) TRIBUTARIA(S) MENSUAL(ES)), vigente al momento del pago` (o `…al momento de efectuar el pago`). Con decimales se usa coma: `0,5 U.T.M`; en pago adelantado puede abreviarse `U.TM` según modelo.

### 0.6 Firmas y pie de pronunciamiento
Solo llevan firma las resoluciones que **fallan** o se dictan tras audiencia:

```
[NOMBRE JUEZ]
JUEZ TITULAR / JUEZ SUBROGANTE

[NOMBRE SECRETARIA(O)]
SECRETARIA ABOGADO / SECRETARIO ABOGADO / SECRETARIA SUBROGANTE
```

Pie opcional cuando el juez pronuncia: `PRONUNCIADA POR EL SEÑOR JUEZ TITULAR DEL PRIMER JUZGADO DE POLICÍA LOCAL DE [COMUNA], DON [NOMBRE JUEZ].` Los decretos simples de mesa **no llevan firma** en los modelos.

### 0.7 Notificación según objeto
- Informe institucional pendiente: `Ofíciese.` / `Ofíciese, una vez hecho, archívese.`
- Resolución que afecta al denunciado ausente: `Notifíquese esta resolución por carta certificada.` / `por correo certificado.`
- Compareciente presente: `El compareciente se notifica en este acto de la resolución que antecede. Previa lectura se ratifica y firma con Usía.`

---

## 1. Acumulación de causas e infracciones

**Modelo fuente:** `RES. ACUMULACION.txt`, `ACUMULACION DE CAUSAS.txt` (x2), `RES. ACUMULACION DE CAUSAS.txt`, `SENT ACUMULACION ART 23 LEY DE RENTAS.txt`, `RES. DIO CUMPLIMIENTO ACUMULACION.txt`, oficios asociados.

### Propósito y cuándo se usa
Unir causas cuyo **hecho denunciado es el mismo** (misma persona, día, evento). Se acumula la causa **de ingreso posterior** a la primera. Procede a petición de parte o **de oficio** (p. ej., todas las causas de un mismo evento, día y hora, acumuladas al primer rol).

### Cuándo NO procede (con fórmula textual)
Rangos horarios distintos del mismo vehículo el mismo día = dos infracciones autónomas. Fórmula literal de rechazo:

> `Atendido que la boleta de citación Nº[X] que dio origen a la causa Rol Nº[ROL B]/[AÑO], cursada por el Departamento de Inspección Comunal de la I. Municipalidad de [COMUNA], da cuenta de "[INFRACCIÓN]" a las [HORA 1] horas por el vehículo P.P.U. [PATENTE], y la boleta de citación Nº[Y] que dio origen a la causa Rol Nº[ROL C]/[AÑO], cursada por el Departamento de Inspección Comunal de la I. Municipalidad de [COMUNA], señala al mismo vehículo, el mismo día y por la misma infracción, pero a las [HORA 2] horas, existiendo, por tanto, un tiempo prolongado entre las dos infracciones, no ha lugar a lo solicitado a fojas [N]. Téngase por formulado los descargos, autos para oír sentencia.`

### Estructura en orden exacto
1. Fecha en letras.
2. Motivación breve (`Visto que…` o `VISTOS: Que…`).
3. Resolutiva en mayúsculas: `acumúlese aquella a esta` / `Acumúlese esta causa al proceso antes mencionado`.
4. Opcional: proveer descargos y etapa (`Téngase por formulado los descargos… Autos para oír sentencia.`).
Sin firma ni notificación especial (la resolución se notifica por estado diario).

### Frases obligatorias textuales

Variante A — decreto simple (dominante):
> `Visto que los hechos denunciados en causa [ROL B]-[AÑO] son los mismos que dieron origen a la causa [ROL A]-[AÑO], acumúlese aquella a esta.`

Variante B — con VISTOS:
> `VISTOS: Que la materia de la presenta causa, fue denunciada previamente en causa rol N° [ROL B]-[AÑO].- Acumúlese esta causa al proceso antes mencionado, por corresponder a los mismos hechos.`

Variante C — acumulación con descargos ya formulados:
> `Visto que los hechos denunciados en causa [ROL B]-[AÑO] son los mismos que dieron origen a la causa [ROL A]-[AÑO], acumúlese aquella a esta. Téngase por formulado los descargos por parte de don [NOMBRE DENUNCIADO]. Autos para oír sentencia.`

Variante D — acumulación masiva **de oficio** (considerando de sentencia, p. ej. feria con decenas de denunciados, rentas):
> `Que a fojas [N] rola resolución que ordena por parte de este tribunal la acumulación de todas las causas ahí individualizadas a la causa rol N° [ROL]-[AÑO], por tener lugar en un mismo evento, día y hora.`

Cumplimiento posterior del denuncio por acumulación de infracciones (Art. 207 letra B Ley 18.290) — informa al Registro Civil y archiva:
> `Infórmese al Servicio de Registro Civil e Identificación que el denunciado don [NOMBRE DENUNCIADO], cédula de identidad N° [RUT], dio cumplimiento a lo establecido en el Art [207 letra B] de la Ley 18.290 por acumulación de infracciones. Ofíciese, una vez hecho, archívese.`

Incumplimiento (no habido / sin comparecencia):
> `Infórmese al Servicio de Registro Civil e Identificación que el denunciado don [NOMBRE DENUNCIADO] no compareció, por lo que no se pudo hacer efectivo lo dispuesto en el Art. 207/B de la Ley 18.290. Ofíciese, una vez hecho, archívense los antecedentes.`

> `A sus antecedentes. En mérito a lo informado por Correos de Chile, infórmese al Registro Civil que don [NOMBRE DENUNCIADO], no dio cumplimiento a lo establecido en el Articulo 207 letra B de la Ley 18.290. Ofíciese, una vez hecho, archívese.`

### Esqueleto anonimizado

```
En [CIUDAD], a [DÍA] de [MES] de [AÑO].

Visto que los hechos denunciados en causa [ROL B]-[AÑO] son los mismos que
dieron origen a la causa [ROL A]-[AÑO], acumúlese aquella a esta.
[Téngase por formulado los descargos por parte de don [NOMBRE].
Autos para oír sentencia.]
```

---

## 2. Rebaja de multa

**Modelos fuente:** `Rebaja multa.txt`, `RES. REBAJA MULTA.txt`, `REBAJA MULTA AUDIENCIA.txt`, `RESOLUCION REBAJA MULTA CON SENTENCIA Y BOLETIN DE PAGO ADELANTADO.txt`, rechazos: `No ha lugar, se aplico multa minima.txt`, `NO HA LUGAR RECONSIDERACION (REINCIDENTE GRAVISIMA).txt`, `no ha lugar multa maxima.txt`, `no ha lugar multa y rebaja suspension.txt`, `RES. EXHORTO NO HA LUGAR REBAJA.txt`.

### Propósito y cuándo procede
Reducir el monto condenado tras escrito de reconsideración, en audiencia o de oficio. Fundamentos típicos: exposición del denunciado, hoja de vida limpia / primera infracción, comprobante de pago anticipado, petición vía exhorto. Antes de resolver debe consultarse reincidencia (Registro Nacional de Conductores / R.M.N.).

### Cuándo NO procede (fórmulas textuales de rechazo)
- **Multa mínima ya aplicada:**
> `Atendido que se aplicó la multa mínima establecida en la Ley para el tipo de infracción cometida, no ha lugar.`
- **Reincidencia en infracción gravísima:**
> `Atendida la gravedad de la infracción y la circunstancia de ser reincidente en su cometido, no ha lugar a la rebaja solicitada.`
- **Rechazo genérico por mérito del proceso:**
> `Atendido el merito del proceso, no ha lugar.`
- **Vía exhorto (se informa al tribunal requirente):**
> `Atendido que se aplico la multa mínima establecida en la Ley para el tipo de infracción cometida. No ha lugar. Infórmese al Juez del [TRIBUNAL REQUIRENTE]. Ofíciese.`
- **Mixta — niega multa pero acoge rebajar suspensión:**
> `Con el mérito de lo anteriormente expuesto, no ha lugar a la rebaja de la multa impuesta, y rebájese a [N] días la pena accesoria de suspensión de licencia de conductor.`

### Estructura en orden exacto
1. Fecha en letras.
2. Motivación (`Visto…` / `Atendido lo expresado…` / `Previa audiencia con el magistrado…`).
3. Resolutiva: `rebájese la multa impuesta a [N] U.T.M. ([LETRAS]), vigente al momento del pago.` (siempre con la fórmula UTM completa).
4. Si proviene de exhorto: identificación del exhorto, tribunal de origen y remisión de la resolución a la parte. Sin firma (decreto de mesa).

### Frases obligatorias textuales

Base (escrito de reconsideración acogido):
> `Visto: lo expuesto por el denunciado, rebájese la multa impuesta a [N] U.T.M. ([N EN LETRAS] UNIDAD(ES) TRIBUTARIA(S) MENSUAL(ES)), vigente al momento de efectuar el pago.`

Variante con antecedentes del proceso:
> `Visto lo expuesto y antecedentes del proceso, rebájese la multa impuesta a [N] U.T.M ([N EN LETRAS]), vigente al momento del pago.`

En audiencia:
> `Previa audiencia con el magistrado, y en vista de los antecedentes generales del proceso, rebájese la multa impuesta a [N] U.T.M, vigente al momento del pago.`

Con sentencia y boletín de pago adelantado (rebaja a lo pagado):
> `Atendido lo expresado por el denunciado y comprobante de pago agregado a los autos, rebájese la multa a la suma pagada, esto es, [MONTO] U.T.M.`

Vía exhorto (acoge):
> `Téngase por recibido Exhorto N° [NUMERO EXHORTO], perteneciente al [TRIBUNAL DE ORIGEN]; y como se pide, rebájese la multa a [N] U.T.M. ([N EN LETRAS] UNIDAD TRIBUTARIA MENSUAL) vigente al momento del pago. Remítase esta resolución a la [denunciado(a)] [NOMBRE], Cédula de Identidad N° [RUT]. Ofíciese.`

### Esqueleto anonimizado

```
En [CIUDAD], a [DÍA] de [MES] de [AÑO].

[Visto: lo expuesto por el denunciado | Atendido lo expresado por el
denunciado y comprobante de pago agregado a los autos | Previa audiencia
con el magistrado, y en vista de los antecedentes generales del proceso],
rebájese la multa impuesta a [N] U.T.M. ([N EN LETRAS] UNIDAD TRIBUTARIA
MENSUAL), vigente al momento del pago.
[Remítase esta resolución a [PARTE]. Ofíciese.]        ← solo si vía exhorto
```

---

## 3. Rebaja de días de suspensión de licencia

**Modelos fuente:** `Rebaja días de suspensión.txt`, `RESOLUCION REBAJA DIAS DE SUSPENSION DE LICENCIA JUEZ ULTIMA.txt`, `rebaje susp por hoja d vida.txt`, `RES. REBAJE SUSP..txt`, `RES. REBAJE SUSP PREVIO PAGO DE MULTA.txt`, `WP_REBAJE SUSPENSION LICENCIA.txt`, `RECLUSION CUANDO HAY REBAJE.txt`; rechazos: `LC VENCIDA NO HA LUGAR REBAJE DIAS.txt`, `WP_NO HA LUGAR REBAJE SUSPENSION.txt`, `RES. NO HA LUGAR SUSPENSION.txt`.

### Propósito y cuándo procede
Reducir los días de suspensión accesorios impuestos en sentencia. Requisitos habituales: haber **pagado la multa** (boletín agregado), hoja de vida de conductor limpia (certificado de Antecedentes de Conductor del Registro Civil), buena exposición. Suele resolverse después de acogida la rebaja de multa o junto a ella. Consultar siempre R.N.C./R.M.N. antes.

### Cuándo NO procede (fórmulas textuales de rechazo)
- **Licencia vencida (LC vencida)** — rechaza y fija conducta compensatoria:
> `Encontrándose vencida la licencia de conductor, no ha lugar; en cuanto a la solicitud de notificación electrónica, como se pide, a través del correo: [CORREO DEL TRIBUNAL]. Atendido que la suspensión decretada en autos no puede cumplirse encontrándose en custodia una licencia de conductor vencida, otórguese un plazo de 5 días hábiles al denunciado, para que indique en qué Dirección de Tránsito renovará su licencia de conductor, a fin de que esta sea remitida para dicho trámite y devuelta a este tribunal para cumplir la suspensión pendiente.`
- **No se aplicó el máximo legal** (ya hubo rebaja implícita en la condena):
> `No habiendo aplicado el máximo del plazo de suspensión de licencia de conductor que contempla la ley y su certificado de antecedentes de conductor, no ha lugar.`
> `Atendido que no se aplico el plazo máximo de suspensión de licencia de conductor y conforme a los antecedentes de la causa, no ha lugar.`
- También impiden rebajar: infracción gravísima/reincidencia, y haberse concedido rebaja previa.

### Estructura en orden exacto
1. Fecha en letras.
2. Motivación (`Resolviendo el escrito que antecede…`, `Atendido…`, `Visto…`) citando el sustento: pago acreditado a fojas, certificado de Antecedentes de Conductor, hoja de vida.
3. Resolutiva: `rebájese a [N] días la suspensión de licencia de conductor.` (+ fecha de inicio si corresponde).
4. Sin firma (decreto). Si el denunciado está presente, notificación en el acto.

### Frases obligatorias textuales

Previo pago acreditado (base):
> `Resolviendo el escrito que antecede y la circunstancia de haber pagado la multa impuesta, según consta en fojas [N] agregada a los autos, rebájese a [N] días la suspensión de licencia de conductor.`

Versión completa del juez (certificado de conductor + pago):
> `Resolviendo el escrito que antecede; atendido lo informado en el certificado de Antecedentes de Conductor otorgado por el Servicio de Registro Civil e Identificación, y la circunstancia de haber pagado la multa impuesta, según da cuenta la copia de cancelación agregada a los autos, rebájese a [N] días la suspensión de licencia de conductor.`

Por hoja de vida limpia:
> `Atendido que el denunciado no registra anotaciones en su hoja de vida de conductor, rebájese a [N] días la suspensión de licencia.`

Conforme a antecedentes (forma breve WP):
> `Atendido lo expuesto y conforme a los antecedentes de la causa, rebájese a [N] días la suspensión de su licencia de conductor.`

Indicando inicio de la suspensión rebajada:
> `VISTO: lo expuesto por el denunciado y la circunstancia de que pagó la multa impuesta, rebájese a [N] días la suspensión de licencia de conductor, la que regirá desde el día [FECHA EN NÚMEROS].`

Breve por cancelación:
> `Visto: que el denunciado canceló la multa impuesta, rebájese a [N] días la suspensión de licencia de conductor.`

Complementaria (decretar reclusión recalculada tras rebaja de multa):
> `Con el merito del certificado que antecede y atendida la rebaja de la multa establecida en la resolución de fojas [N] decrétense la reclusión del denunciado de [N] noche(s), por vía de sustitución y apremio.`

### Esqueleto anonimizado

```
En [CIUDAD], a [DÍA] de [MES] de [AÑO].

Resolviendo el escrito que antecede[, atendido lo informado en el
certificado de Antecedentes de Conductor otorgado por el Servicio de
Registro Civil e Identificación], y la circunstancia de haber pagado la
multa impuesta, según consta en fojas [N] agregada a los autos, rebájese
a [N] días la suspensión de licencia de conductor[, la que regirá desde
el día [FECHA]].
```

---

## 4. Archivo (no constituir infracción / no comparecer / variantes)

**Modelos fuente:** `Resolución archivo por no constituir infracción.txt` (2026), `ARCHIVO EXTRACCION COCO PALMA CHILENA.txt`, `ARCHIVO POR NO RATIFICAR.txt`, `ARCHIVO POR FALTA DE BOLETA DE CITACION.txt`, `Resoluciones con firma_Denunciado no habido.txt` (x2), `RES. ARCHIVO DENUNCIADO NO HABIDO.txt`, `archivo por direccion extranjera.txt`, `ARCHIVESE, DENUNCIADO CON DOMICILIO EXTRANJERO.txt`, `RES. NO HAY RESPUESTA (TRANSITO) ARCHIVO.txt`, `ARCHIVO_archivo, mantiene multa.txt`, `ARCHIVO_archivo no coinciden datos.txt`, `ARCHIVO_vocales de mesa sin direccion.txt`, `RES. ARCHIVO LEY ELECTORAL SIN DOMICILIO.txt`, `DENEGACION LICENCIA_ARCHIVO (PLAZO VENCIDO).txt`, `Por oficio de Carabineros, archívese la causa.txt`, `Como se pide, desarchivese por 10 dias.txt`, `ARCHIVO MASCARILLA.txt`, `ARCHIVO_incompetencia materia.txt`, `ARCHIVO_devuelta notificacion de sentencia.txt`.

### Propósito
Cerrar la causa sin sentencia cuando: el hecho no es infracción sancionable, el denuncio no se ratifica, el denunciado no puede ser habido/citado válidamente, o faltan antecedentes esenciales. El archivo **no extingue la responsabilidad** si queda multa impaga: antes de archivar por no habido suele **informarse al Registro Civil** la deuda pendiente (ver variante I).

### Estructura en orden exacto
1. Fecha en letras.
2. Advertencia o motivo: `Advirtiendo el tribunal que…` / `Atendido que…` / `Visto que…` / `No habiendo…` / `Teniendo presente que…` / `A sus antecedentes, en mérito del documento que antecede…`.
3. Resolutiva: `archívese la presente causa` / `archívense los antecedentes` / `archívese esta causa por falta de antecedentes`.
4. Mandatos accesorios en cadena: `infórmese al Registro Civil… Ofíciese, una vez hecho, archívese.`
5. Firma SOLO cuando el archivo lo pronuncia el juez (variante B).

### Frases obligatorias textuales por causal

**A) El hecho no constituye infracción (forma 2026):**
> `Advirtiendo que el hecho denunciado no constituye contravención a las disposiciones de la Ley N° [LEY], sino simplemente una condición de ingreso y permanencia a un recinto deportivo en los términos que previene el artículo 76 del Decreto Supremo N° 1046 de 2016 del Ministerio del Interior, no tratándose de un hecho tipificado por la ley, archívense los antecedentes.`
Patrón generalizable: `no constituye contravención a las disposiciones de la Ley N° [LEY], sino [DESCRIPCIÓN], no tratándose de un hecho tipificado por la ley, archívense los antecedentes.`

**B) Misma causal pronunciada por el juez (con firma):**
> `Atendido que el hecho denunciado no constituye una infracción que sea de conocimiento de un juzgado de policía local. Archívese la causa.`
seguida de firma y pie `PRONUNCIADA POR EL SEÑOR JUEZ TITULAR DEL PRIMER JUZGADO DE POLICÍA LOCAL DE ESTA CIUDAD, DON [NOMBRE JUEZ].`

**C) Denuncio no ratificado (no comparece el denunciante):**
> `No habiendo sido ratificado el denuncio de fojas [N], archívese.`

**D) Falta boleta de citación (art. 3 inc. 2 Ley 18.287):**
> `Advirtiendo el tribunal que no consta en la denuncia de fojas [N] que el funcionario denunciante diere cumplimiento a lo dispuesto en el artículo 3º inciso 2º de la Ley N° 18.287, en el sentido de citar al denunciado por escrito, acompañando a la audiencia una copia de la citación, archívese esta causa por falta de antecedentes.`

**E) Denunciado no habido (certificado de gestión previa):**
> `A sus antecedentes, en mérito del documento que antecede, archívese la presente causa.`
> `Atendido lo informado por Correos de Chile, archívese la presente causa`

**F) Domicilio en el extranjero:**
> `Atendido que el propietario del vehículo denunciado no registra dirección en territorio nacional, impidiendo su citación, archívese la presente causa.`
> `Atendido que el denunciado tiene domicilio en el extranjero, archívese la causa.`

**G) Sin respuesta a oficios despachados:**
> `Advirtiendo el tribunal que se despachó oficio de fecha [FECHA], citando a primera audiencia, y los oficios de fecha [FECHA 2] y [FECHA 3], respectivamente, pidiendo cuenta del resultado de la citación, todos despachados por [COMISARÍA/TRIBUNAL], sin tener respuesta de los mismos, archívense los antecedentes.`

**H/I) Archivo con informe previo de multa impaga (NO archivar sin esto):**
> `Atendido lo informado por Correos de Chile a fs. [N], infórmese al Registro Civil que el infractor mantiene multa impaga en este Tribunal. Ofíciese, una vez hecho, archívese.`
> `VISTO, lo informado por el Departamento de Inspección Comunal, infórmese al Registro Civil que el infractor mantiene multa impaga y suspensión pendiente en este Tribunal, ofíciese, una vez hecho, archívese.`

**J) Datos del vehículo no coinciden:**
> `Atendido que la patente y descripción del vehículo de fojas [N] no coinciden con los antecedentes que aparecen en el Certificado de Inscripción y Anotaciones Vigentes que rola a fojas [M], archívese la presente causa por falta de antecedentes.`

**K) Vocales de mesa sin domicilio (ley electoral):**
> `Advirtiendo el Tribunal que la nómina de vocales de mesa inasistentes agregada a fojas [N] no consigna el domicilio de la denuncia, archívese la presente causa por falta de antecedentes.`
> `Visto que en la nómina de Vocales de Mesa no se ha consignado el domicilio del denunciado, archívese por falta de antecedentes.`

**L) Reclamación de denegación de licencia fuera de plazo:**
> `Encontrándose vencido el plazo previsto en el artículo 15 inciso 3º de la Ley 18.290, archívese la causa.`

**M) Por oficio de Carabineros que da cuenta de término:**
> `A sus antecedentes, en virtud del Oficio N° [NÚMERO] con fecha [FECHA] enviado por Carabineros de [UNIDAD] y que rola en fojas [N], archívese la presente causa.`

**N) Desarchivo temporal (para tramitar algo pendiente):**
> `Como se pide, desarchívese por el término de [N] días.`

**O) Hecho despenalizado sobreviniemente (ej. mascarilla):**
> `Teniendo presente que el [HECHO] dejó de constituir una contravención por aplicación del [NORMA QUE LO DESPENALIZA], déjese sin efecto la orden de reclusión por no pago de multa que pudiere haberse decretado en la causa, y archívense los antecedentes.`

**P) Incompetencia en la materia (con firma):**
> `VISTO: Advirtiendo el Tribunal que la materia denunciada no es de competencia de este Tribunal, me declaro incompetente para seguir conociendo de estos autos y ocúrrase ante quien corresponda. Archívense los antecedentes.`

**Q) Notificación de sentencia devuelta:**
> `VISTO: que no se hizo efectiva la notificación de la sentencia al denunciado don [NOMBRE], por no corresponder el domicilio. Archívense los antecedentes.`

### Esqueleto anonimizado (archivo con informe previo — forma más completa)

```
En [CIUDAD], a [DÍA] de [MES] de [AÑO].

Advirtiendo el tribunal que [MOTIVO: el hecho denunciado no constituye
contravención… | se despacharon oficios sin respuesta… | lo informado por
Correos de Chile…], [infórmese al Registro Civil que el infractor mantiene
multa impaga en este Tribunal. Ofíciese, una vez hecho,] archívese la
presente causa.
```

---

## 5. Citación a declarar / a audiencia

**Modelos fuente:** `CERT Y CITACION (DENUNCIA PARTICULAR).txt`, `CITA PARA RATIFICAR APERCIBIMIENTO ARCHIVO.txt`, `CITACION EMPRESA POR DEPTO INSPECCION.txt`, `Res. Citese al funcionario denunciante.txt`, `PROVEYENDO, CITESE A LA SEÑALADA COMO CONDUCTORA DEL VEHICULO.txt`, `Advertiendo que la cita no se envio….txt`, `Atendido el tribunal por error en fecha….txt`, `ATENDIDO EL TRIBUNAL POR PPU INCORRECTA….txt`, `RES. DEJESE SIN EFECTO CITACION (POR PAGAR ADELANTADO).txt`, `DEJE SIN EFECTO CITACION POR PAGAR (TESORERIA).txt`, `DEJE SIN EFECTO CITACION POR EXISTIR SENTENCIA….txt`.

### Propósito
Emplazar a una parte (denunciante, denunciado, tercero señalado, representante legal, funcionario denunciante) a ratificar, declarar indagatoria o comparecer a audiencia, bajo apercibimiento (rebeldía o archivo). Las citas de empresas/funcionarios municipales se despachan por **Departamento de Inspección Comunal** o **Correos de Chile**; las de particulares, por correo certificado o notificador.

### Estructura en orden exacto
1. Fecha en letras.
2. Gatillo: `Para proveer…` / `Proveyendo el escrito de fojas [N]…` / `Advirtiendo el tribunal que…` / `Atendido el tribunal que…` / directo `CÍTESE…`.
3. Individualización del citado (nombre, calidad).
4. Objeto: ratificar denuncio, prestar declaración indagatoria, confirmar/aclarar hechos, asistir a audiencia.
5. Fecha y hora de audiencia o plazo de días + horario de atención del tribunal + correo electrónico.
6. Apercibimiento: `bajo apercibimiento de proceder en su rebeldía` / `de ARCHIVO` / `de proceder al archivo de los antecedentes`.
7. Despacho/notificación: `Despáchese la presente citación por medio del Departamento de Inspección Comunal…` / `Notifíquese esta resolución por correo certificado.` / `OFÍCIESE.`

### Frases obligatorias textuales

Citación a denunciante para ratificar y declarar (choque, denuncia particular):
> `Previo a proveer la presentación de fojas [N], cítese al denunciante, don [NOMBRE], otorgándole un plazo de quince días, a fin de que ratifique el denuncio de fojas [N] y preste declaración indagatoria personalmente en dependencias del tribunal en el siguiente horario: lunes a viernes de 09:00 a 14:00 horas; o por medio electrónico al siguiente correo: [CORREO DEL TRIBUNAL], bajo apercibimiento de proceder al archivo de los antecedentes.`

Citación a audiencia de representante legal (empresa):
> `CÍTESE AL REPRESENTANTE LEGAL DE "[RAZÓN SOCIAL]", A LA AUDIENCIA DE DÍA [FECHA], a las [HORA] horas, BAJO APERCIBIMIENTO PROCEDER EN SU REBELDÍA. DESPÁCHESE LA PRESENTE CITACIÓN POR MEDIO DEL DEPARTAMENTO DE INSPECCIÓN COMUNAL DE LA ILUSTRE MUNICIPALIDAD DE [COMUNA].`

Citación al funcionario denunciante (para confrontar declaraciones):
> `Para proveer el escrito que antecede, cítese al funcionario denunciante don [NOMBRE FUNCIONARIO], para el día [FECHA] a las [HORA] hrs., a fin de que confirme, rectifique, complemente o aclare los hechos al tenor de la declaración indagatoria del denunciado formulada a fojas [N], bajo apercibimiento de proceder en su REBELDÍA. OFÍCIESE.`

Citación a la conductora señalada en un escrito:
> `Proveyendo el escrito de fojas [N], a lo principal y otrosí, téngase presente; cítese a la señalada como conductora del vehículo el día de la infracción, doña [NOMBRE], para el día [FECHA] a las [HORA] hrs. a fin de prestar declaración indagatoria bajo apercibimiento de proceder en su rebeldía.`

Reiteración de citación no despachada:
> `Advirtiendo el tribunal que la citación no se despachó el día [FECHA], reitérese citación al representante legal de [RAZÓN SOCIAL] para audiencia el día [FECHA] a las [HORA] hrs. bajo apercibimiento de proceder en su rebeldía. Ofíciese.`

Corrección por error de fecha:
> `Atendido el tribunal que por error involuntario se citó al denunciado para el día [FECHA ERRÓNEA], en vez del día [FECHA CORRECTA], déjese sin efecto la resolución de fojas [N], y cítese a don [NOMBRE] para el día [FECHA] a las [HORA] hrs., con su cédula de identidad y licencia de conducir, bajo apercibimiento de proceder en su rebeldía. Notifíquese esta resolución por correo certificado.`

Corrección por P.P.U. incorrecta:
> `Atendido el tribunal que a fojas [N] rola un Certificado de Inscripción y Anotaciones Vigentes del Servicio de Registro Civil e Identificación correspondiente al vehículo P.P.U. [PATENTE], debiendo decir [PATENTE CORRECTA], déjase sin efecto citación y certificado que rola a fojas [N] y [M] respectivamente y cítese a [NOMBRE], para el día [FECHA], a las [HORA] hrs. bajo apercibimiento de proceder en rebeldía a fin de que preste declaración indagatoria.`

Dejar sin efecto la citación:
- Por pago adelantado: `Atendido a que el denunciado canceló oportunamente en Tesorería Municipal la multa impuesta según boletín Nº[NÚMERO], déjese sin efecto citación de fojas [N].`
- Tras pago (y archivo): `A sus antecedentes, habiéndose cancelado la multa impuesta, déjese sin efecto la citación de fojas [N]. Archívese.`
- Por existir sentencia: `Advirtiendo el tribunal que ya existe sentencia condenatoria en estos autos, déjese sin efecto la resolución de fojas [N].`

### Esqueleto anonimizado

```
En [CIUDAD], a [DÍA] de [MES] de [AÑO].

[Para proveer la presentación de fojas [N],] cítese a [CALIDAD: el
denunciante / la señalada como conductora / el representante legal de
"[RAZÓN SOCIAL]" / el funcionario denunciante] don/doña [NOMBRE],
para el día [FECHA] a las [HORA] hrs.[, u otorgándole un plazo de
quince días], a fin de que [ratifique el denuncio de fojas [N] y]
preste declaración indagatoria[, personalmente en dependencias del
tribunal en el siguiente horario: lunes a viernes de 09:00 a 14:00
horas; o por medio electrónico al siguiente correo: [CORREO DEL
TRIBUNAL]], bajo apercibimiento de [proceder en su rebeldía /
proceder al archivo de los antecedentes].
[Despáchese la presente citación por medio del Departamento de
Inspección Comunal de la I. Municipalidad de [COMUNA]. |
Notifíquese esta resolución por correo certificado. | OFÍCIESE.]
```

---

## 6. Concesión de plazo

**Modelos fuente:** `PLAZO 15 DÍAS CHOQUE.txt` (versión actualizada 2025, con cinco sub-formatos), `PLAZO 15 DIAS TRANSITO (ULTIMA).txt`, `plazo 10 dias.txt`, `PLAZO 10 DIAS RATIFIQUE DENUNCIO.txt`, `PLAZO 15 DIAS PROP (SIN EFECTO AUTOS).txt`, `PLAZO 15 DIAS RATIFICAR BAJO APERCIBIMIENTO DE ARCHIVO.txt`, `PLAZO 5 DIAS PARA ACOMPAÑAR DOCUMENTOS.txt`, `plazo 15 días choque (ULTIMA).txt`, `PROPIETARIO NO COMPARECE. CITA A COMPARENDO.txt`.

### Propósito
Otorgar a una parte un plazo determinado (5, 10, 15 días hábiles o corridos) para: prestar declaración indagatoria, ratificar denuncia, acompañar documentos o individualizar al conductor, siempre **bajo apercibimiento** (rebeldía, orden de aprehensión, archivo o sentencia derecha).

### Estructura en orden exacto
1. Fecha en letras.
2. (Opcional) Contexto normativo de contingencia (modelo COVID): `Atendida la contingencia nacional, el acuerdo de la Excelentísima Corte Suprema de fecha 16 de marzo de 2020, lo dispuesto por la autoridad municipal, y considerando el estado actual del brote de COVID-19,`
3. Beneficiario y plazo: `otórguese al/la [CALIDAD], un plazo de [N] días [hábiles]`.
4. Objeto: `a fin de que [ratifique el denuncio / preste declaración indagatoria / acompañe documentos / individualice al conductor]`.
5. Modo de cumplimiento: personalmente en dependencias del tribunal (horario de atención) **o** por medio electrónico al correo del tribunal.
6. Apercibimiento explícito: rebeldía / orden de aprehensión sin más trámite (art. 13 Ley 18.287) / archivo / dictar derechamente sentencia / hacer efectiva la responsabilidad infraccional del propietario (art. 170 inciso 4º Ley 18.290).
7. Mandatos conexos: `Suspéndase el decreto de autos.` / `Déjese sin efecto el decreto de autos.` cuando corresponde.

### Frases obligatorias textuales

**Bloque AL CONDUCTOR (choque):**
> `Otórguese a los conductores un plazo de quince días hábiles a fin de que preste declaración indagatoria personalmente en dependencias del tribunal a las 10:00 horas; o por medio electrónico al siguiente correo: [CORREO DEL TRIBUNAL], bajo apercibimiento de despachar orden de aprehensión en su contra sin más trámite, en conformidad a lo dispuesto en el artículo 13 de la Ley 18.287.`

**Bloque AL DENUNCIANTE PARA QUE RATIFIQUE DENUNCIA:**
> `Otórguese al denunciante un plazo de quince días hábiles a fin de que ratifique la denuncia de fojas uno personalmente en dependencias del tribunal a las 10:00 horas; o por medio electrónico al siguiente correo: [CORREO DEL TRIBUNAL], bajo apercibimiento de ARCHIVO si no lo hiciere.`

**Bloque AL PROPIETARIO (individualizar conductor o declarar):**
> `Otórguese al representante legal de [EMPRESA PROPIETARIA] en calidad de propietario inscrito del vehículo placa patente [PATENTE], un plazo de 15 días hábiles a fin de que preste declaración indagatoria respecto del accidente de tránsito que involucra a su vehículo, ocurrido el día [FECHA], alrededor de las [HORA] horas, en [LUGAR], o en su defecto para que individualice con nombre, cédula de identidad y domicilio al conductor de su vehículo en los términos que previene el artículo 170 inciso 4º, bajo apercibimiento de proceder en su rebeldía y hacer efectiva la eventual responsabilidad infraccional en su contra.`
Cierre común de este bloque:
> `Deberá dar cumplimiento a lo indicado, dentro del plazo de quince días contados desde la notificación de esta resolución, personalmente en dependencias del tribunal a las 10:00 horas; o por medio electrónico al siguiente correo: [CORREO DEL TRIBUNAL], bajo apercibimiento de proceder en su rebeldía y hacer efectiva la eventual responsabilidad infraccional en su contra.`

**Plazo corto para ratificar (forma clásica):**
> `Otórguese un plazo de [10] días a fin de que la denunciante ratifique su denuncio bajo apercibimiento de proceder al archivo.`
> `Otórguese un plazo de 10 días a fin de que ratifique su denuncio, bajo apercibimiento de proceder a su archivo.`

**Plazo 5 días para documentos (suspende el decreto de autos):**
> `Suspéndase el decreto de autos. Acompañe el denunciado, por medio electrónico, al correo: [CORREO DEL TRIBUNAL], los documentos que acreditan sus descargos de fojas [N], dentro del plazo de quinto día, bajo apercibimiento de dictar derechamente sentencia.`

**Plazo 10 días para acompañar documento (otrosí de demanda):**
> `Para resolver, fíjase un plazo de diez días a fin de que la parte denunciante acompañe el documento referido en el [ORDINAL] otrosí, bajo apercibimiento de archivo.-`

**Propietario que no comparece → continuar contra él y citar a comparendo (art. 170 inc. 4º):**
> `Con el mérito del certificado que antecede, y encontrándose vencido el plazo otorgado a fojas [N], prescíndase de la declaración de [QUIÉN NO DECLARÓ], y en conformidad con lo dispuesto en el artículo 170 inciso 4º de la Ley Nº 18.290, se ordena continuar el proceso contravencional en contra éste en su calidad de propietario del vehículo patente [PATENTE]. Vengan las partes a comparendo para el día [FECHA].`

**Propietario cuando el conductor no fue habido:**
> `A sus antecedentes. Atendido lo informado por Carabineros de Chile, Otórguese al propietario inscrito del vehículo denunciado placa patente [PATENTE], [NOMBRE PROPIETARIO], un plazo de quince días hábiles a fin de que preste declaración indagatoria personalmente en dependencias del tribunal a las 10:00 horas; o por medio electrónico al siguiente correo: [CORREO DEL TRIBUNAL], bajo apercibimiento de proceder en su rebeldía y hacer efectiva la eventual responsabilidad infraccional en su contra.`

**Denunciante cuando el denunciado no fue habido:**
> `A sus antecedentes, Otorguese un plazo de 15 días a la denunciante a fin de que proporcione nuevos antecedentes respecto del domicilio del denunciado, personalmente en dependencias del tribunal a las 10:00 horas; o por medio electrónico al siguiente correo: [CORREO DEL TRIBUNAL], bajo apercibimiento de archivo si no lo hiciere.`

**Variante con corrección de autos previos (propietario):**
> `Déjese sin efecto el decreto de autos. Cítese al propietario inscrito al momento de la infracción, otorgándole un plazo de quince días hábiles, a fin de que preste declaración indagatoria personalmente en dependencias del tribunal en el siguiente horario: lunes de 14:30 a 18:30 horas, de martes a viernes de 8:30 a 13:00 horas; o por medio electrónico al siguiente correo: [CORREO DEL TRIBUNAL], bajo apercibimiento de proceder en su rebeldía, por la eventual infracción consistente en: [INFRACCIÓN EN MINÚSCULAS ENTRE DOS PUNTOS].`

**Cláusula de contingencia (COVID, prefijo opcional):**
> `Atendida la contingencia nacional, el acuerdo de la Excelentísima Corte Suprema de fecha 16 de marzo de 2020, lo dispuesto por la autoridad municipal, y considerando el estado actual del brote de COVID-19, otórguese al denunciante un plazo de quince días a fin de que ratifique el denuncio interpuesto por medio electrónico al siguiente correo: [CORREO DEL TRIBUNAL], bajo apercibimiento de proceder al archivo de los antecedentes.`

### Esqueleto anonimizado

```
En [CIUDAD], a [DÍA] de [MES] de [AÑO].
[Suspéndase / Déjese sin efecto el decreto de autos.]

Otórguese al/la [CALIDAD: denunciado / denunciante / propietario inscrito
del vehículo placa patente [PATENTE]], un plazo de [N] días [hábiles] a
fin de que [ratifique el denuncio de fojas [N] / preste declaración
indagatoria / acompañe los documentos… / individualice al conductor en
los términos del artículo 170 inciso 4º de la Ley Nº 18.290],
personalmente en dependencias del tribunal en el siguiente horario:
[HORARIO]; o por medio electrónico al siguiente correo: [CORREO DEL
TRIBUNAL], bajo apercibimiento de [proceder en su rebeldía / despachar
orden de aprehensión sin más trámite (art. 13 Ley 18.287) / proceder al
archivo / dictar derechamente sentencia].
```

---

## 7. Orden de reclusión sustitutiva por no pago

**Modelos fuente:** `RESOLUCION Y ORDEN DE RECLUCION ULTIMA_ 2020!!!!.txt` (x3 variantes), `RESOL. Y ORRD. RECLUSION.txt`, `CERT RECLUSION (SECRETARIO SUBROGANANTE).txt`, `CERT. RECLUSION R51.txt`, `RECLUSION CUANDO HAY REBAJE.txt`, `SUSPENDE ORDEN DE RECLUSION POR COVID.txt`, `CORRIGE RESOLUTIVA DIAS RECLUSION.txt`, instructivo `INSTRUCTIVOS ACCION CIVIL SOBRE 4 UTM, ORDEN RECLUSION NOCTURNA…` (regla del amparo Rol Corte 8-2017).

### Propósito
Ejecutar la reclusión nocturna sustitutiva y apremio de la multa (art. 23 Ley 18.287) cuando transcurrido el plazo legal no consta pago. **Nunca es una sola resolución: es una secuencia obligatoria de cuatro piezas.**

### Regla procesal previa (instructivo interno, vinculante)
- El actuario solo puede certificar el no pago **una vez transcurridos 30 días hábiles** contados desde la notificación de la sentencia (plazo para pedir reposición o reconsideración de la multa), por fallo de amparo de la Corte.
- Igual certificado puede emitirse si se presentó reposición/reconsideración **rechazada** y dicha resolución fue notificada personalmente o por carta certificada, **siempre que hayan pasado al menos 5 días hábiles desde la notificación de la sentencia**.
- Cuando la sentencia se notificó por carta certificada, la fecha de notificación es el **quinto día hábil contado desde la recepción de la carta por Correos**.
- Los escritos de reconsideración deben agregarse al expediente apenas se reciben de la oficina de partes.

### Estructura en orden exacto (secuencia de 4 piezas)

**PIEZA 1 — NOTA del actuario (al pie del expediente):**
> `NOTA: Que en estos Autos no he recibido Boletín de Pago de Multa, la sentencia se encuentra notificada y no tengo en mi poder escrito pendiente respecto del infractor. En [CIUDAD], a [FECHA EN LETRAS].`
seguida de `[NOMBRE ACTUARIO]` / `ACTUARIO(A)`.

**PIEZA 2 — Decreto del juez pidiendo cuenta:**
> `Certifíquese por el secretario abogado subrogante, si ha transcurrido el plazo legal para el pago de la multa impuesta en estos autos, si la sentencia se encuentra notificada y si existen recursos pendientes.`

**PIEZA 3 — Certificación de la secretaría:**
> `CERTIFICO: Que han transcurrido los cinco días que establece la Ley para el pago de la multa en este proceso, cuyo monto asciende a [N] U.T.M. ([N EN LETRAS]), que la sentencia se encuentra notificada y que no existen recursos pendientes respecto del infractor. En [CIUDAD], a [FECHA EN LETRAS].`
firmada `[NOMBRE SECRETARIA(O)]` / `[SECRETARIA ABOGADO (S)]`.

**PIEZA 4 — Resolutiva del juez (dos formas según época):**

Forma moderna (dominante):
> `Con el mérito del certificado que antecede y de acuerdo con lo dispuesto en el Artículo 23 de la Ley 18.287, dese cumplimiento a la Reclusión Nocturna correspondiente a la multa aplicada en la causa. Ofíciese.`

Forma antigua (individualizada, con monto de noches):
> `Con merito del certificado que antecede y de acuerdo con lo dispuesto en el artículo 23 de la ley 18.287, decrétase por vía de sustitución de apremio RECLUSION NOCTURNA de [N] días a don [NOMBRE], Cedula de Identidad Nº[RUT], por el no pago de la multa impuesta.`

### Frases complementarias textuales
- Recálculo tras rebaja de multa (ver sección 3): `Con el merito del certificado que antecede y atendida la rebaja de la multa establecida en la resolución de fojas [N] decrétense la reclusión del denunciado de [N] noche(s), por vía de sustitución y apremio.`
- Suspensión de la orden (contingencia):
> `Atendida la contingencia nacional, el acuerdo de la Excelentísima Corte Suprema de fecha 16 de marzo de 2020, lo dispuesto por la autoridad municipal, y considerando el estado actual del brote de COVID-19, y habiendo transcurrido el plazo legal que establece la Ley para el pago de la multa en este proceso, que la sentencia se encuentra notificada y que no existen recursos pendientes, suspéndase la reclusión nocturna correspondiente a la multa aplicada en la causa hasta el término del estado de excepción constitucional. Notifíquese esta resolución por carta certificada.`
- Corrección de error en el número de noches de la resolutiva de sentencia:
> `Advirtiendo el tribunal que existe error en la parte resolutiva de la sentencia de fojas [N], específicamente en la frase ". deberán cumplir por vía de sustitución y apremio [X] noches de reclusión", debe decir "deberá cumplir por vía de sustitución y apremio [Y] noches de reclusión".`

### Convenciones
- Cada pieza lleva su propia fecha y firma; la secuencia puede ser del mismo día o de días distintos.
- La forma moderna NO repite nombre ni número de noches: remite al cálculo de la sentencia (`dese cumplimiento a la Reclusión Nocturna correspondiente`).
- Siempre cierra en `Ofíciese` (despacha la orden al recinto penitenciario por oficio).

### Esqueleto anonimizado (secuencia completa)

```
NOTA: Que en estos Autos no he recibido Boletín de Pago de Multa, la
sentencia se encuentra notificada y no tengo en mi poder escrito pendiente
respecto del infractor. En [CIUDAD], a [FECHA].
                                        [NOMBRE ACTUARIO] — ACTUARIO(A)

---

En [CIUDAD], a [FECHA].
Certifíquese por el secretario abogado subrogante, si ha transcurrido el
plazo legal para el pago de la multa impuesta en estos autos, si la
sentencia se encuentra notificada y si existen recursos pendientes.
                                        [NOMBRE JUEZ] — [CARGO]

---

CERTIFICO: Que han transcurrido los cinco días que establece la Ley para
el pago de la multa en este proceso, cuyo monto asciende a [N] U.T.M.
([N EN LETRAS]), que la sentencia se encuentra notificada y que no existen
recursos pendientes respecto del infractor. En [CIUDAD], a [FECHA].
                              [NOMBRE SECRETARIA(O)] — SECRETARIA ABOGADO (S)

---

En [CIUDAD], a [FECHA].
Con el mérito del certificado que antecede y de acuerdo con lo dispuesto
en el Artículo 23 de la Ley 18.287, dese cumplimiento a la Reclusión
Nocturna correspondiente a la multa aplicada en la causa. Ofíciese.
                                        [NOMBRE JUEZ] — [CARGO]
```

---

## 8. Medida precautoria

**Modelos fuente:** `RESOLUCIÓN PRECAUTORIA.txt` (= `CHOQUE_RESOLUCIÓN PRECAUTORIA.txt`), `prejuidicial precautoria.txt`, complementarios: `OFICIO PRECAUTORIA R. CIVIL.txt` y `CERTIFICADO PRECAUTORIA R.CIVIL.txt` (documentados en los manuales de OFICIOS y CERTIFICADOS).

### Propósito
Asegurar el resultado de la acción civil indemnizatoria (choques): prohibición de celebrar actos y contratos sobre el vehículo demandado, anotada en el Registro Civil. Se decreta dentro del proceso (medida precautoria) o antes de la demanda (medida prejudicial). Requiere caución del solicitante y receptor ad-hoc designado.

### Estructura en orden exacto (resolución precautoria)
1. Fecha en letras + `Resolviendo escrito que antecede;`
2. `a lo principal:` concesión de la medida con individualización COMPLETA del bien (tipo, patente, marca, modelo, color, año, propietario, RUN) y beneficiario.
3. `Ofíciese.` (oficio al Registro Civil).
4. Designación de receptor ad-hoc + carga del actor de aportar medios para la notificación.
5. Otrosíes: curso sin previa notificación; formación de cuaderno separado.

### Frases obligatorias textuales

Medida precautoria (dentro del proceso):
> `Resolviendo escrito que antecede; a lo principal: como se pide, decrétese Medida Precautoria de prohibición de celebrar actos y contratos respecto del vehículo [TIPO], placa patente [PATENTE], marca [MARCA] modelo [MODELO], color [COLOR], año [AÑO], de propiedad de [PROPIETARIO], RUN [RUT], siendo el beneficiario de esta medida [BENEFICIARIO]. Ofíciese. Desígnese receptor ad-hoc a doña [NOMBRE RECEPTOR], y/o [NOMBRE RECEPTOR ALTERNO], a quien el actor deberá proporcionar los medios que permitan practicar la notificación oportunamente.`
> `Al primer otrosí: como se pide, dese curso sin previa notificación.`
> `Al segundo otrosí: como se pide fórmese cuaderno separado.`

Medida prejudicial (antes de la demanda — caución):
> `A lo principal, para resolver ofrézcase y constitúyase fianza en el libro de fianza del tribunal; al otrosí, para resolver acompáñese documento que indica. Fórmese cuaderno separado.`

### Cuándo NO procede
No hay fórmula de rechazo en los modelos; en la práctica exige caución constituida y bien identificable en el registro. Si el solicitante no acompaña los medios para notificar, la diligencia simplemente no se practica (el receptor lo certifica).

### Esqueleto anonimizado

```
En [CIUDAD], a [DÍA] de [MES] de [AÑO].

Resolviendo escrito que antecede;
a lo principal: como se pide, decrétese Medida Precautoria de prohibición
de celebrar actos y contratos respecto del vehículo [TIPO], placa patente
[PATENTE], marca [MARCA] modelo [MODELO], color [COLOR], año [AÑO], de
propiedad de [PROPIETARIO], RUN [RUT], siendo el beneficiario de esta
medida [BENEFICIARIO]. Ofíciese. Desígnese receptor ad-hoc a doña
[NOMBRE], y/o [NOMBRE], a quien el actor deberá proporcionar los medios
que permitan practicar la notificación oportunamente.
Al primer otrosí: como se pide, dese curso sin previa notificación.
Al segundo otrosí: como se pide fórmese cuaderno separado.
```

---

## 9. Fallo sobre denegación de licencia de conducir

**Modelos fuente:** carpeta `DENEGACION FALLOS MAGISTRADO_` (5 fallos completos: niega lugar confirmando la denegación / acoge con licencia restringida a seis meses o un año), archivo posterior `(PLAZO VENCIDO).txt`, oficio de consulta al Depto. de Tránsito sobre fecha de notificación de la denegación.

### Propósito
Resolver la **reclamación contra la denegación de licencia** informada por el Director de Tránsito por falta de idoneidad moral. Es una **sentencia** (no un decreto): aplica arts. 13 Nº 3, 14 bis, 15 y 16 de la Ley 18.290 (condenas de los últimos cinco años). Dos desenlaces posibles: confirmar la denegación o declarar la idoneidad moral con licencia **restringida** (seis meses o un año).

### Estructura en orden exacto
1. Encabezado: `CAUSA ROL Nº [ROL]/[AÑO]` · `ACTUARIO: [INICIALES]` · `FOJAS: [N] ([N EN LETRAS])`.
2. Fecha en letras.
3. `VISTOS Y CONSIDERANDO:` con considerandos romanos numerados:
   - 1º: Ordinario Nº [X] del Director de Tránsito que informa la denegación (clase, reclamante con RUT y domicilio, fundamento art. 15 Ley 18.290).
   - 2º: Detalle de las condenas registradas en la hoja de vida (tribunal, rol, fecha, delito/infracción, pena).
   - 3º: Escrito de reconsideración del reclamante y sus fundamentos.
   - 4º: Documentos acompañados (certificados de cumplimiento de condena, programas de reinserción, alcoholemias, etc.).
   - Últimos: cita del art. 16 Ley 18.290 (quinquenio) y valoración de la idoneidad moral.
4. Fórmula de cierre de considerandos: `Por estas consideraciones, en mérito de lo expuesto, documentos acompañados y lo prescrito en los artículos 13 Nº 3, 14 bis, 15 y 16 de la Ley 18.290,`
   ⚠️ Nota de actualización: esa fórmula es TEXTUAL de los fallos reales y usa la numeración histórica de la Ley 18.290 previa a la Ley 19.495 («13 Nº 3» = hoy art. 13 Nº 1, idoneidad moral; «14 bis» = hoy art. 15). En documentos nuevos preferir la numeración vigente: `artículos 13, 15 y 16 de la Ley Nº 18.290`.
5. `SE DECLARA:` con uno de los dos desenlaces (abajo).
6. Notificación y comunicaciones: personal o cédula al reclamante; oficios al Director del Depto. de Tránsito y al Director del Servicio de Registro Civil e Identificación con copia autorizada; `Una vez hecho, archívese.`
7. Firmas: `JUEZ TITULAR` + pie `PRONUNCIADA POR EL SEÑOR JUEZ TITULAR DEL PRIMER JUZGADO DE POLICÍA LOCAL DE [COMUNA], DON [NOMBRE].` + `SECRETARIA ABOGADO`.

### Frases obligatorias textuales

Apertura del relato (considerando 1º):
> `Que mediante el Ordinario Nº [NÚMERO], de fecha [FECHA], el Director del Tránsito de la Municipalidad de [COMUNA] informa a este tribunal que denegó la licencia de conductor clase [CLASE(S)], a don [NOMBRE], RUT Nº [RUT], domiciliado en [DOMICILIO], por carecer de idoneidad moral para conducir vehículos de conformidad al artículo 15 de la Ley Nº 18.290.`

Fundamento legal del quinquenio (considerando previo al fallo):
> `Que de conformidad al artículo 16º de la Ley Nº 18.290, para calificar la idoneidad moral de los postulantes a licencia de conductor se deberán considerar las condenas que hayan sufrido en los cinco años anteriores a la solicitud, por delitos, cuasidelitos, faltas o infracciones a la Ley del Tránsito, a la ley sobre expendio y consumo de bebidas alcohólicas, y a la Ley Nº 20.000, sobre tráfico ilícito de estupefacientes y sustancias sicotrópicas, entre otros.`

Desenlace NEGATIVO (confirma denegación):
> `Que se niega lugar al reclamo interpuesto por [NOMBRE], ya individualizado, en contra de la resolución del Director de Tránsito y Transporte Público del Departamento de Tránsito de [COMUNA], y se CONFIRMA la resolución de fojas uno del Director de Tránsito y Transporte Publico de la Municipalidad de [COMUNA], que denegó el otorgamiento de la licencia de conducir clase [CLASE] al solicitante.`

Desenlace AFIRMATIVO (acoge con restricción temporal):
> `Que se acoge al reclamo interpuesto por [NOMBRE] en contra de la resolución del Director de Tránsito y Transporte Público del Departamento de Tránsito de [COMUNA], de fecha [FECHA], y se declara que tiene idoneidad moral para otorgarle licencia para conducir vehículos clase [CLASE(S)], restringida por [un año / seis meses].`

Cierre procesal (común a ambos):
> `Notifíquese esta sentencia personalmente o por cédula al reclamante y ofíciese al director del Depto. de Tránsito de [COMUNA] y al director del Servicio de Registro Civil e Identificación, remitiendo copia autorizada del presente fallo. Una vez hecho, archívese.`

Archivo posterior por plazo vencido (si nadie reclama en plazo, art. 15 inc. 3º):
> `Encontrándose vencido el plazo previsto en el artículo 15 inciso 3º de la Ley 18.290, archívese la causa.`

### Esqueleto anonimizado

```
                    CAUSA ROL Nº [ROL]/[AÑO]
                        ACTUARIO: [INICIALES]
                FOJAS: [N] ([N EN LETRAS])

[CIUDAD], [DÍA] de [MES] de [AÑO].

VISTOS Y CONSIDERANDO:
1º.- Que mediante el Ordinario Nº [NÚMERO], de fecha [FECHA], el Director
del Tránsito de la Municipalidad de [COMUNA] informa a este tribunal
que denegó la licencia de conductor clase [CLASE], a don/doña [NOMBRE],
RUT Nº [RUT], domiciliado en [DOMICILIO], por carecer de idoneidad moral
para conducir vehículos de conformidad al artículo 15 de la Ley Nº 18.290.
2º.- Que la denegación se funda en los antecedentes que registra en su
hoja de vida de conductor, en que figura: [CONDENAS: tribunal, rol, fecha,
delito, pena].
3º.- Que a fojas [N] comparece por escrito [NOMBRE], quien solicita la
reconsideración de la denegación de licencia, fundado en que [MOTIVOS].
4º.- Que a fojas [N] se acompañan [DOCUMENTOS: certificados de cumplimiento
de condena, informes de reinserción, etc.].
5º.- Que de conformidad al artículo 16º de la Ley Nº 18.290, para calificar
la idoneidad moral de los postulantes a licencia de conductor se deberán
considerar las condenas sufridas en los cinco años anteriores a la
solicitud, por delitos, cuasidelitos, faltas o infracciones a la Ley del
Tránsito, a la ley sobre expendio y consumo de bebidas alcohólicas, y a la
Ley Nº 20.000, entre otros. [VALORACIÓN DEL QUINQUENIO Y DE LA IDONEIDAD.]
Por estas consideraciones, en mérito de lo expuesto, documentos acompañados
y lo prescrito en los artículos 13 Nº 3, 14 bis, 15 y 16 de la Ley 18.290,

SE DECLARA:
[Que se niega lugar al reclamo interpuesto por [NOMBRE], ya individualizado,
… y se CONFIRMA la resolución de fojas uno del Director de Tránsito… | Que
se acoge al reclamo interpuesto por [NOMBRE] … y se declara que tiene
idoneidad moral para otorgarle licencia para conducir vehículos clase
[CLASE], restringida por [un año/seis meses].]

Notifíquese esta sentencia personalmente o por cédula al reclamante y
ofíciese al director del Depto. de Tránsito de [COMUNA] y al director
del Servicio de Registro Civil e Identificación, remitiendo copia
autorizada del presente fallo. Una vez hecho, archívese.

                                        [NOMBRE JUEZ] — JUEZ TITULAR
PRONUNCIADA POR EL SEÑOR JUEZ TITULAR DEL PRIMER JUZGADO DE POLICÍA LOCAL
DE [COMUNA], DON [NOMBRE JUEZ].

        [NOMBRE SECRETARIA] — SECRETARIA ABOGADO
```

---

## 10. "Por recibido" y providencias de mesa

**Modelos fuente:** `TENGASE POR RECIBIDO EXHORTO.txt`, `TENGASE POR RECIBIDO EXHORTO, REBAJA MULTA.txt`, `PROVEIDO DENUNCIA INFRACCIONAL (COPROPIEDAD).txt`, `resolucion querella con citacion y poder.txt`, `TENGASE POR REBELDE, AUTOS.txt`, `RESOLUCION AUTOS OIR SENTENCIA EMPADRONADO.txt`, `resolucion cuando hay citacion, sentencia y boletin de pago anticipoado.txt`, `RESOLUION CUANDO HAY CITACION, SENTENCIA Y RESOLUCION RMN.txt`, `RESOLUCIÓN SOLO CUANDO HAY CITACIÓN y paga adelantado.txt`, `VISTOS DECLARACION FUNC. DENUNCIANTE, NO HA LUGAR.txt`.

### Propósito
Primer proveído de escritos, exhortos y denuncias: dar ingreso, disponer lo pedido en cada otrosí y fijar etapa procesal. Son decretos breves, sin considerandos, estructurados por partes (`A lo principal…`, `Al primer otrosí…`).

### Frases obligatorias textuales

**A) Téngase por recibido exhorto (simple, con etapa y oficio):**
> `Téngase por recibido Exhorto N° [NÚMERO], perteneciente al [TRIBUNAL DE ORIGEN] y remítase el valor de la multa perteneciente al denunciado [NOMBRE], Cédula de Identidad N° [RUT]. Autos para oír sentencia, ofíciese.`

**B) Téngase por recibido exhorto + rebaja combinada:**
> `Téngase por recibido Exhorto N° [NÚMERO], perteneciente al [TRIBUNAL DE ORIGEN]; y como se pide, rebájese la multa a [N] U.T.M. ([N EN LETRAS] UNIDAD TRIBUTARIA MENSUAL) vigente al momento del pago. Remítase esta resolución a la [parte] [NOMBRE], Cédula de Identidad N° [RUT]. Ofíciese.`

**C) Proveído de denuncia infraccional (copropiedad) con otrosíes:**
> `A lo principal, téngase por interpuesta la denuncia y cítese a doña [NOMBRE] a audiencia el día [FECHA EN LETRAS] A LAS [HORA EN LETRAS] HORAS, a fin de que ratifique su denuncia, bajo apercibimiento de archivo; al primer otrosí, téngase por acompañados los documentos; al segundo otrosí, téngase presente.`

**D) Proveído de querella con citación y poder (estructura de otrosíes):**
> `Resolviendo la solicitud de fojas uno y siguientes, A LO PRINCIPAL, por interpuesta querella, AL PRIMER OTROSI, cítese a Doña [NOMBRE], a la audiencia del día [FECHA] a las [HORA] horas, bajo apercibimiento de proceder en su rebeldía; AL SEGUNDO OTROSI, téngase presente; AL TERCER OTRO SI, venga en forma la delegación; AL CUARTO OTRO SI, como se pide se designa receptor AD-HOC a Don [NOMBRE RECEPTOR].`

**E) Rebeldía y entrega a sentencia (dos variantes):**
> `No habiendo comparecido en las oportunidades señaladas en el proceso, téngase por rebelde al (la) denunciado (a). Autos para oír sentencia.`
> `No habiendo comparecido en las oportunidades señaladas en el proceso, téngase por rebelde al (a) denunciado (a) y al propietario (a) inscrito (a) del vehículo en que se cometió la infracción. Autos para oír sentencia.`
Complemento con certificación previa de secretaría:
> `CERTIFICO: Que llamado al denunciado a la hora y fecha señalada, este no compareció. En [CIUDAD], a [FECHA].`
y luego el decreto: `AUTOS PARA OÍR SENTENCIA.`

**F) Pago anticipado cuando ya hay citación/sentencia/RMN (dejar sin efecto lo obrado):**
- Con citación y sentencia:
> `Visto: Que se ha agregado con esta fecha boletín de ingreso municipal dando cuenta del pago de la multa en forma anticipada, déjese sin efecto lo obrado a fojas ([DESDE FOJA] a [HASTA FOJA]) y pasen los autos al Juez no inhabilitado. Notifíquese esta resolución por carta certificada.`
- Con citación, sentencia y resolución R.M.N.:
> `Visto: Que se ha agregado con esta fecha boletín de ingreso Municipal dando cuenta del pago de la multa en forma anticipada, déjese sin efecto lo obrado de fojas [DESDE FOJA] a las fojas que ordena informar al Registro de Multa y pasen los autos al Juez no inhabilitado. Notifíquese por carta certificada.`
- Solo con citación:
> `Visto: Que se ha agregado con esta fecha boletín de ingreso Municipal dando cuanta del pago de la multa en forma anticipada, déjese sin efecto la citación ordenada a fojas [N] a don/doña [NOMBRE]. Notifíquese esta resolución por carta certificada.`
Regla: el tramo dejado sin efecto va **desde la foja de la citación hasta la foja de la sentencia** (o de la resolución RMN), porque el pago anticipado (arts. 22 incs. 3º y 4º Ley 18.287; ver PLAZOS.md) hace inútil lo actuado tras la denuncia; `pasen los autos al Juez no inhabilitado` evita que falle el juez que conoció el pago. ⚠️ Una versión anterior de este manual citaba «art. 200 Nº 4 Ley 18.287»: cita errónea (el art. 200 pertenece a la Ley de Tránsito y regula infracciones, no el pago anticipado).

**G) Rechazo tras prueba del tribunal ("VISTOS" mínimo):**
> `VISTOS: La declaración del inspector denunciante, no ha lugar a lo solicitado a fojas [N].`

### Estructura en orden exacto
1. Fecha en letras.
2. Ingreso: `Téngase por interpuesta/recibido…` (o directo `Resolviendo la solicitud de fojas…`).
3. Disposición principal (audiencia, etapa, rebaja).
4. Otrosíes en orden ordinal (`al primer otrosí… al segundo otrosí…`), cada uno resuelto.
5. Cierre con etapa y comunicación: `Autos para oír sentencia, ofíciese.` / `Notifíquese esta resolución por carta certificada.`
Sin firma (proveído de mesa).

### Esqueleto anonimizado

```
[CIUDAD], a [DÍA] de [MES] de [AÑO].

[Téngase por recibido Exhorto N° [NÚMERO], perteneciente al [TRIBUNAL]; |
 A lo principal, téngase por interpuesta la denuncia y] [disposición:
 cítese a [NOMBRE] a audiencia el día [FECHA] a las [HORA] horas, a fin
 de que [ratifique su denuncia/preste declaración], bajo apercibimiento
 de [rebeldía/archivo]; rebájese la multa a [N] U.T.M. …].
al primer otrosí, [téngase por acompañados los documentos];
al segundo otrosí, téngase presente.
[Autos para oír sentencia, ofíciese.]
```

---

## Reporte de fuentes

| # | Tipo | Modelos localizados (documentos fuente del tribunal, salvo indicación) |
|---|------|--------------------------------------------------------------------------|
| 1 | Acumulación | `RES. ACUMULACION`, `ACTUARIO_ACUMULACION DE CAUSAS` (x2), `RES. ACUMULACION DE CAUSAS`, `SENT ACUMULACION ART 23 LEY DE RENTAS`, `RES. DIO CUMPLIMIENTO ACUMULACION`, `RES. NO HA LUGAR ACUMULAR DOS CAUSAS POR RANGO HORARIO`, oficios dio/no dio cumplimiento |
| 2 | Rebaja multa | `Rebaja multa`, `RES. REBAJA MULTA`, `REBAJA MULTA AUDIENCIA`, `RESOLUCION REBAJA MULTA CON SENTENCIA Y BOLETIN DE PAGO ADELANTADO`, `TENGASE POR RECIBIDO EXHORTO, REBAJA MULTA`; rechazos: `No ha lugar, se aplico multa minima`, `NO HA LUGAR RECONSIDERACION (REINCIDENTE GRAVISIMA)`, `no ha lugar multa maxima`, `no ha lugar multa y rebaja suspension`, `RES. EXHORTO NO HA LUGAR REBAJA` |
| 3 | Rebaja suspensión | `Rebaja días de suspensión`, `RESOLUCION REBAJA DIAS DE SUSPENSION DE LICENCIA JUEZ ULTIMA`, `rebaje susp por hoja d vida`, `RES. REBAJE SUSP.`, `RES. REBAJE SUSP PREVIO PAGO DE MULTA`, `WP_REBAJE SUSPENSION LICENCIA`, `RECLUSION CUANDO HAY REBAJE`; rechazos: `LC VENCIDA NO HA LUGAR REBAJE DIAS`, `WP_NO HA LUGAR REBAJE SUSPENSION`, `RES. NO HA LUGAR SUSPENSION` |
| 4 | Archivo | `Resolución archivo por no constituir infracción` (2026), `ARCHIVO EXTRACCION COCO PALMA CHILENA`, `ARCHIVO POR NO RATIFICAR`, `ARCHIVO POR FALTA DE BOLETA DE CITACION`, `Denunciado no habido` (x2), `RES. ARCHIVO DENUNCIADO NO HABIDO`, `archivo por direccion extranjera`, `ARCHIVESE, DENUNCIADO CON DOMICILIO EXTRANJERO`, `RES. NO HAY RESPUESTA (TRANSITO) ARCHIVO`, `ARCHIVO_archivo, mantiene multa`, `ARCHIVO_archivo no coinciden datos`, `ARCHIVO_vocales de mesa sin direccion`, `DENEGACION LICENCIA_ARCHIVO (PLAZO VENCIDO)`, `Por oficio de Carabineros, archívese la causa`, `Como se pide, desarchivese por 10 dias`, `ARCHIVO MASCARILLA`, `ARCHIVO_incompetencia materia`, `ARCHIVO_devuelta notificacion de sentencia` |
| 5 | Citación | `CERT Y CITACION (DENUNCIA PARTICULAR)`, `CITA PARA RATIFICAR APERCIBIMIENTO ARCHIVO`, `CITACION EMPRESA POR DEPTO INSPECCION`, `Res. Citese al funcionario denunciante`, `PROVEYENDO, CITESE A LA SEÑALADA COMO CONDUCTORA`, `Advertiendo que la cita no se envio…`, `error en fecha, cite al denunciado`, `PPU INCORRECTA, CITESE AL PROPIETARIO`, `DEJESE SIN EFECTO CITACION` (3 variantes) |
| 6 | Plazo | `PLAZO 15 DÍAS CHOQUE` (actualizada 2025, 5 bloques), `PLAZO 15 DIAS TRANSITO (ULTIMA)`, `plazo 10 dias`, `PLAZO 10 DIAS RATIFIQUE DENUNCIO`, `PLAZO 15 DIAS PROP (SIN EFECTO AUTOS)`, `PLAZO 15 DIAS RATIFICAR BAJO APERCIBIMIENTO DE ARCHIVO`, `PLAZO 5 DIAS PARA ACOMPAÑAR DOCUMENTOS`, `plazo 15 días choque (ULTIMA)`, `PROPIETARIO NO COMPARECE. CITA A COMPARENDO` |
| 7 | Reclusión | `RESOLUCION Y ORDEN DE RECLUCION ULTIMA_ 2020!!!!` (x3), `RESOL. Y ORRD. RECLUSION`, `CERT RECLUSION (SECRETARIO SUBROGANANTE)`, `CERT. RECLUSION R51`, `SUSPENDE ORDEN DE RECLUSION POR COVID`, `CORRIGE RESOLUTIVA DIAS RECLUSION`, instructivo amparo Rol Corte 8-2017 |
| 8 | Precautoria | `RESOLUCIÓN PRECAUTORIA` (2024), `prejuidicial precautoria`, `OFICIO PRECAUTORIA R. CIVIL`, `CERTIFICADO PRECAUTORIA R.CIVIL` |
| 9 | Denegación licencia (fallo) | `DENEGACION FALLOS MAGISTRADO_` ×5 (niega lugar / acoge 6 meses / acoge 1 año), `Denegación licencia` ×9, `DENEGACION LICENCIA_ARCHIVO (PLAZO VENCIDO)`, oficio consulta fecha de notificación de denegación |
| 10 | Por recibido / mesa | `TENGASE POR RECIBIDO EXHORTO` (+ variante rebaja), `PROVEIDO DENUNCIA INFRACCIONAL (COPROPIEDAD)`, `resolucion querella con citacion y poder`, `TENGASE POR REBELDE, AUTOS`, `RESOLUCION AUTOS OIR SENTENCIA EMPADRONADO`, pago adelantado ×3, `VISTOS DECLARACION FUNC. DENUNCIANTE, NO HA LUGAR` |

- **Tipos documentados:** 10 de 10, todos con modelo real y fórmulas textuales.
- **Sin modelo encontrado:** ninguno. Única salvedad: no existe en el corpus un modelo de rechazo formal de una medida precautoria (sección 8) ni de "denegación de proveer un escrito" distinta de las fórmulas `no ha lugar a lo solicitado a fojas [N]` (secciones 1, 2 y 10-G).
