# FORMATOS-OFICIOS-PRESCRIPCION

**Categoría:** formatos | **ID:** 3

---

# FORMATOS — OFICIOS Y PRESCRIPCIÓN (JPL [COMUNA])

Manual de estructura exacta de los oficios del tribunal y de los formularios/escritos de prescripción, reconsideración, reclamación, acumulación y descargos.
Fuente: `modelos/consolidado/plantillas/oficios_prescripcion/` (13 plantillas canónicas), complementado con documentos fuente del tribunal.
Todo dato variable va como `[MARCADOR]`. Las frases entre comillas son TEXTUALES de las plantillas.

---

## 0. Convenciones comunes de los OFICIOS

### 0.1 Encabezado (orden exacto)
1. `OFICIO Nº [NUMERO]-[AÑO]` (numeración correlativa anual; algunos llevan además `ACTUARIO [INICIALES]` en el encabezado).
2. Opcional: `MAT: [MATERIA EN MAYÚSCULAS].` (p. ej. `MAT: MULTA IMPAGA.` o `MAT: PRESCRIPCIÓN`).
3. Lugar y fecha: `[COMUNA], [DIA] de [MES] de [AÑO].`
4. `DE:` tribunal emisor.
5. `A:` destinatario con cargo completo e institución.

### 0.2 Fórmulas fijas
- **Apertura obligatoria:** `Por resolución recaída en la causa rol N°[ROL]-[AÑO], se ha ordenado oficiar a Ud., a fin de informar que ...`
- **Despedidas** (según objeto):
  - `Saluda atentamente a Ud.` (dominante)
  - `Para su conocimiento y anotación correspondiente.`
  - `Lo que comunico a Ud., para su conocimiento y fines a que haya lugar.`
- **Firmas:** `[NOMBRE JUEZ]` / `[CARGO JUEZ]` y debajo `[NOMBRE SECRETARIA]` / `[CARGO SECRETARIA]`.

### 0.3 Pie de sobre / c.c.
Algunos oficios llevan al final el bloque de envío del destinatario (`DIRECTOR...`, domicilio institucional, `CAUSA [ROL]-[AÑO] ACTUARIO [X].`) o la referencia interna `c.c. causa Nº [ROL]-[AÑO] ACTUARIO: [INICIALES].`

---

## 1. Oficio Departamento de Tránsito — reclamación por denegación ACOGIDA

**Plantilla base:** `01_oficio_depto_transito_denegacion.txt`

### Propósito
Comunicar al Depto. de Tránsito que el tribunal **acogió la reclamación** contra la denegación de licencia y declaró la idoneidad moral del reclamante; ordenar nuevo control y adjuntar copia autorizada de la sentencia para que se otorgue la licencia.

### Destinatario típico
`SR. DIRECTOR DEPARTAMENTO DE TRÁNSITO Y TRANSPORTE PÚBLICO DE LA I. MUNICIPALIDAD DE [COMUNA]`

### Frases obligatorias textuales
> `Por resolución recaída en la causa rol N° [ROL]-[AÑO], se ha ordenado oficiar a Ud. a fin de informar que se acogió la reclamación deducida por [NOMBRE RECLAMANTE], Cédula de identidad N° [RUT], en contra de la resolución del Departamento de Tránsito y Transporte Público de la I. Municipalidad de [COMUNA] de fecha [FECHA DENEGACION], y se declara que tiene idoneidad moral para otorgarle la Licencia de Conducir vehículos clase [CLASE]. Que deberá realizar un nuevo control de su licencia dentro del plazo de [N] (número) años. Se adjunta copia autorizada de la sentencia de fecha [FECHA SENTENCIA].`

> `Saluda atentamente a usted.`

### Esqueleto anonimizado

```
OFICIO Nº [NUMERO] — [AÑO]
				ACTUARIO: [APELLIDO ACTUARIO]

En [CIUDAD], a [DIA] de [MES] de [AÑO].

DE	: JUEZ PRIMER JUZGADO DE POLICÍA LOCAL DE [COMUNA]
A 	: SR. DIRECTOR DEPARTAMENTO DE TRÁNSITO Y TRANSPORTE PÚBLICO
	  DE LA I. MUNICIPALIDAD DE [COMUNA]

Por resolución recaída en la causa rol N° [ROL]-[AÑO], se ha ordenado
oficiar a Ud. a fin de informar que se acogió la reclamación deducida
por [NOMBRE COMPLETO], Cédula de identidad N° [RUT], en contra de la
resolución del Departamento de Tránsito y Transporte Público de la
I. Municipalidad de [COMUNA] de fecha [DIA/MES/AÑO], y se declara
que tiene idoneidad moral para otorgarle la Licencia de Conducir
vehículos clase [CLASE]. Que deberá realizar un nuevo control de su
licencia dentro del plazo de [N] (número) años. Se adjunta copia
autorizada de la sentencia de fecha [FECHA].

Saluda atentamente a usted.

				[NOMBRE JUEZ]
				[CARGO JUEZ]

	[NOMBRE SECRETARIA]
	[CARGO SECRETARIA]

c.c. causa Nº [ROL]-[AÑO]
ACTUARIO: [APELLIDO ACTUARIO]
```

---

## 2. Oficio Servicio de Registro Civil e Identificación

**Plantilla base:** `02_oficio_registro_civil.txt`

### Propósito
Informar al SRCeI, para su anotación en el **Registro Nacional de Conductores / hoja de vida del conductor**, una de estas situaciones: condena con pena accesoria de suspensión de licencia; declaración de idoneidad moral; o cumplimiento del artículo infringido (p. ej. art. 207 letra B Ley 18.290 por acumulación de infracciones).

### Destinatario típico
`[SRA./SR.] OFICIAL DEL SERVICIO DE REGISTRO CIVIL E IDENTIFICACIÓN DE [COMUNA].`

### Fundamentos legales citados (textuales de plantilla)
- `[Art. [ARTICULO]] Letra [LETRA] de la Ley [LEY]` — típicamente **Art. 207 Letra B de la Ley Nº 18.290** (acumulación de infracciones).
- La resolución que se remite es copia autorizada de la sentencia.

### Frases obligatorias textuales
> `Por resolución recaída en la causa Rol Nº [ROL]-[AÑO], Actuario [ACTUARIO], por "[MATERIA]", se ha ordenado oficiar a Ud., a fin de informar que [don/doña] [NOMBRE], Cédula de Identidad Nº [RUT], fue [condenado(a) con fecha [FECHA] a la pena accesoria de [N] (número) días de suspensión de su licencia de conducir, dando cumplimiento al Art. [ARTICULO] Letra [LETRA] de la Ley [LEY]] [declara que tiene idoneidad moral para otorgarle la Licencia de Conducir] [ha dado cumplimiento a lo establecido en el Art. [ARTICULO] letra [LETRA] de la Ley [LEY]]. Se remite copia autorizada de la sentencia.`

> `El infractor dio cumplimiento a la sentencia, lo que se informa para su anotación correspondiente en el Registro Nacional de Conductores / hoja de vida del conductor.`

> `Saluda atentamente a Ud.`

Las tres alternativas entre corchetes son excluyentes: elegir UNA según la sentencia (condena/suspensión, idoneidad moral, cumplimiento).

### Esqueleto anonimizado

```
OFICIO Nº [NUMERO]-[AÑO] ACTUARIO [APELLIDO ACTUARIO]
[CIUDAD], [DIA] de [MES] de [AÑO].

DE: PRIMER JUZGADO DE POLICÍA LOCAL DE [COMUNA].
A: [SRA./SR.] OFICIAL DEL SERVICIO DE REGISTRO CIVIL E IDENTIFICACIÓN
   DE [COMUNA].

Por resolución recaída en la causa Rol Nº [ROL]-[AÑO], Actuario
[APELLIDO], por "[MATERIA]", se ha ordenado oficiar a Ud., a fin de
informar que don/doña [NOMBRE COMPLETO], Cédula de Identidad Nº [RUT],
fue [ALTERNATIVA ÚNICA:
  - condenado(a) con fecha [FECHA] a la pena accesoria de [N] días de
    suspensión de su licencia de conducir, dando cumplimiento al Art.
    207 Letra B de la Ley Nº 18.290;
  - declara que tiene idoneidad moral para otorgarle la Licencia de
    Conducir;
  - ha dado cumplimiento a lo establecido en el Art. 207 letra B de la
    Ley Nº 18.290].
Se remite copia autorizada de la sentencia.

El infractor dio cumplimiento a la sentencia, lo que se informa para
su anotación correspondiente en el Registro Nacional de Conductores /
hoja de vida del conductor.

Saluda atentamente a Ud.

				[NOMBRE JUEZ]
				[CARGO JUEZ]

	[NOMBRE SECRETARIA]
	[CARGO SECRETARIA]
```

---

## 3. Oficio SERNAC

**Plantilla base:** `03_oficio_sernac.txt`

### Propósito
Remitir al SERNAC copia autorizada de la sentencia dictada en una causa de consumo (Ley 19.496), informando el resultado contra la empresa denunciada.

### Destinatario típico
`SR. DIRECTOR SERVICIO NACIONAL DEL CONSUMIDOR (SERNAC)` — oficina regional regionalizada (dirección institucional en el pie).

### Frases obligatorias textuales
> `Por resolución recaída en la causa rol Nº [ROL]-[AÑO], actuaria [ACTUARIA], se ha ordenado oficiar a Ud., a fin de remitir copia autorizada de la sentencia dictada en autos, en la cual se [ABSUELVE / CONDENA / AMONESTA] a [NOMBRE EMPRESA O DENUNCIADO], representada por don/doña [NOMBRE REPRESENTANTE].`

> `Lo que comunico a Ud., para su conocimiento y fines a que haya lugar.`

### Convenciones
- El verbo del resultado va en MAYÚSCULAS entre corchetes: `ABSUELVE / CONDENA / AMONESTA`.
- El pie repite el destinatario en bloque de sobre:

```
DIRECTOR
SERVICIO NACIONAL DEL CONSUMIDOR (SERNAC)
DOMICILIO
[CALLE Nº, CIUDAD].
CAUSA [ROL]-[AÑO] ACTUARIA [ACTUARIA].
```

### Esqueleto anonimizado

```
OFICIO Nº [NUMERO]-[AÑO]
[CIUDAD], [DIA] de [MES] de [AÑO].

DE: PRIMER JUZGADO DE POLICÍA LOCAL DE [COMUNA].
A: SR. DIRECTOR SERVICIO NACIONAL DEL CONSUMIDOR (SERNAC)
   CALLE [CALLE] Nº [NUMERO]. [CIUDAD].

Por resolución recaída en la causa rol Nº [ROL]-[AÑO], actuaria
[APELLIDO ACTUARIA], se ha ordenado oficiar a Ud., a fin de remitir
copia autorizada de la sentencia dictada en autos, en la cual se
[ABSUELVE / CONDENA / AMONESTA] a [RAZÓN SOCIAL], representada por
don/doña [NOMBRE REPRESENTANTE LEGAL].

Lo que comunico a Ud., para su conocimiento y fines a que haya lugar.

Saluda atentamente a Ud.

				[NOMBRE JUEZ]
				[CARGO JUEZ]

	[NOMBRE SECRETARIA]
	[CARGO SECRETARIA]

DIRECTOR
SERVICIO NACIONAL DEL CONSUMIDOR (SERNAC)
[DIRECCIÓN INSTITUCIONAL OFICINA REGIONAL]
CAUSA [ROL]-[AÑO] ACTUARIA [APELLIDO].
```

---

## 4. Oficio multas impagas (informe al Registro Civil)

**Plantilla base:** `04_oficio_multas_impagas.txt`

### Propósito
Informar al SRCeI que una persona **mantiene multa impaga** en este tribunal, para su anotación en la hoja de vida / RNC (usado al revisar reincidencia o al tramitar renovaciones de licencia).

### Destinatario típico
`OFICIAL DEL SERVICIO REGISTRO CIVIL DE [COMUNA].`

### Frases obligatorias textuales
> `MAT: MULTA IMPAGA.`

> `Por resolución recaída en Nº [ROL]-[AÑO], Actuario [ACTUARIO], por "[INFRACCION DE TRANSITO]" / "[INFRACCIÓN]", se ha ordenado oficiar a Usted, a fin de informar que [el denunciado don/la denunciada doña] [NOMBRE], Cedula de Identidad Nº [RUT], MANTIENE MULTA IMPAGA EN ESTE TRIBUNAL, ascendente a [MONTO] [U.T.M. o valor].`

> `Para su conocimiento y anotación correspondiente.`

### Convenciones
- La materia va SIEMPRE en el asunto (`MAT: MULTA IMPAGA.`).
- El monto se expresa en U.T.M. o valor monetario según la sentencia.
- `[INFRACCION]` entre comillas y mayúsculas.

### Esqueleto anonimizado

```
OFICIO Nº [NUMERO]-[AÑO] Actuario [APELLIDO]
MAT: MULTA IMPAGA.
[CIUDAD], [DIA] de [MES] de [AÑO].-

DE: PRIMER JUZGADO DE POLICÍA LOCAL DE [COMUNA].
A: OFICIAL DEL SERVICIO REGISTRO CIVIL DE [COMUNA].

Por resolución recaída en Nº [ROL]-[AÑO], Actuario [APELLIDO],
por "[INFRACCIÓN EN MAYÚSCULAS]", se ha ordenado oficiar a Usted,
a fin de informar que el denunciado don / la denunciada doña
[NOMBRE COMPLETO], Cedula de Identidad Nº [RUT], MANTIENE MULTA IMPAGA
EN ESTE TRIBUNAL, ascendente a [MONTO] [U.T.M. o valor].

Para su conocimiento y anotación correspondiente.

		Saluda atentamente a Usted.

				[NOMBRE JUEZ]
				[CARGO JUEZ]

	[NOMBRE SECRETARIA]
	[CARGO SECRETARIA]
```

---

## 5. FORMULARIO 1 — Prescripción multa RMNP (empadronados)

**Plantilla base:** `05_prescripcion_form1_rmnp_empadronado.txt`

### Propósito
Escrito del propio interesado pidiendo declarar prescrita la multa **anotada en el Registro de Multas del Tránsito no Pagadas (R.M.N.P.)** de un vehículo empadronado cuya causa tramitó este tribunal. Plazo: **3 años desde la anotación** (art. 24 incs. 1º y 2º Ley 18.287).

### Estructura (orden exacto)
1. Sumilla doble: `EN LO PRINCIPAL: SOLICITA PRESCRIPCIÓN MULTA ANOTADA EN EL REGISTRO DE MULTAS DE TRÁNSITO NO PAGADAS (EMPADRONADOS)` + `OTROSÍ: NOTIFICACIÓN ELECTRÓNICA`.
2. Tribunal dirigido: `S.J. DE POLICÍA LOCAL DE [COMUNA] (1º)`.
3. Bloque de identificación (Nombre completo / Cédula / Edad / Profesión u oficio / Domicilio completo / Contacto telefónico).
4. Hecho 1: propiedad del vehículo (marca, modelo, color, año, placa patente única) + anotación RMNP con fecha + sentencia que la originó (fecha).
5. Hecho 2: transcurso de más de tres años desde la anotación → solicitud de declaración de prescripción.
6. Fundamento: `incisos 1º y 2º del artículo 24 de la Ley Nº 18.287`.
7. Petición: `Acceder a lo solicitado, declarando la prescripción de la multa impuesta en estos autos, oficiando al efecto.`
8. OTROSÍ: notificación electrónica al correo indicado.
9. FIRMA.

### Frases obligatorias textuales
> `Que soy propietario(a) del vehículo marca [MARCA], modelo [MODELO], color [COLOR], año [AÑO], placa patente única [PATENTE], el cual registra una anotación por multa impaga en el Registro de Multas del Tránsito no pagadas, desde el día [DIA] de [MES] de [AÑO], la cual corresponde a la multa dictada en estos autos por sentencia de fecha [DIA] de [MES] de [AÑO].`

> `Que, habiendo transcurrido más de tres años desde la fecha de la anotación, vengo en solicitar la declaración de prescripción de la referida multa.`

> `Por estas consideraciones y lo dispuesto en los incisos 1º y 2º del artículo 24 de la Ley Nº 18.287`

> `Acceder a lo solicitado, declarando la prescripción de la multa impuesta en estos autos, oficiando al efecto.`

### Esqueleto anonimizado

```
EN LO PRINCIPAL: SOLICITA PRESCRIPCIÓN MULTA ANOTADA EN EL REGISTRO
DE MULTAS DE TRÁNSITO NO PAGADAS (EMPADRONADOS)
OTROSÍ: NOTIFICACIÓN ELECTRÓNICA

S.J. DE POLICÍA LOCAL DE [COMUNA] (1º)

Nombre completo: [NOMBRE COMPLETO]
Cédula de identidad: [RUT]
Edad: [EDAD]
Profesión u oficio: [PROFESIÓN U OFICIO]
Domicilio completo: [DOMICILIO COMPLETO]
Contacto telefónico: [TELÉFONO]

	Que soy propietario(a) del vehículo marca [MARCA], modelo [MODELO],
color [COLOR], año [AÑO], placa patente única [PATENTE], el cual registra
una anotación por multa impaga en el Registro de Multas del Tránsito
no pagadas, desde el día [DIA] de [MES] de [AÑO], la cual corresponde
a la multa dictada en estos autos por sentencia de fecha [FECHA].
	Que, habiendo transcurrido más de tres años desde la fecha de la
anotación, vengo en solicitar la declaración de prescripción de la
referida multa.

Por estas consideraciones y lo dispuesto en los incisos 1º y 2º del
artículo 24 de la Ley Nº 18.287

Ruego a SS.,

	Acceder a lo solicitado, declarando la prescripción de la multa
impuesta en estos autos, oficiando al efecto.

OTROSÍ: Solicito que las resoluciones que sean dictadas al efecto se me
notifiquen al siguiente correo electrónico: [EMAIL]

FIRMA:
```

---

## 6. FORMULARIO 2 — Prescripción RMNP vía exhorto (empadronados, juzgado de otra comuna)

**Plantilla base:** `06_prescripcion_form2_rmnp_exhorto.txt`

### Propósito
Igual que el Formulario 1, pero la multa fue dictada por **OTRO juzgado de policía local**: se solicita que ESTE tribunal exhorte a aquel para que declare la prescripción. Fundamento: incisos 1º, 2º y 3º del art. 24 Ley 18.287 (el inciso 3º regula expresamente la solicitud mediante exhorto cuando el juzgado está fuera del lugar de residencia del infractor).

### Diferencias estructurales con Formulario 1
1. Sumilla: `SOLICITA EXHORTO PARA DECLARACIÓN DE PRESCRIPCIÓN DE MULTA EN REGISTRO DE MULTAS DE TRÁNSITO NO PAGADAS (EMPADRONADOS)` + `OTROSÍ: NOTIFICACIÓN ELECTRÓNICA`.
2. Fórmula inicial del cuerpo: `A US., con el debido respeto digo:`
3. Hecho adicional: identifica la sentencia de origen — `por el Juzgado de Policía Local de [TRIBUNAL], en autos Rol [ROL], actuario [ACTUARIO].`
4. Fundamento ampliado: `los incisos 1º, 2º y 3º del artículo 24 de la Ley Nº 18.287`.
5. Petición exhortativa.

### Frases obligatorias textuales
> `Que soy propietario(a) del vehículo marca [MARCA], modelo [MODELO], color [COLOR], año [AÑO], placa patente única [PATENTE], el cual registra una anotación por multa impaga en el Registro de Multas del Tránsito no pagadas, desde el día [DIA] de [MES] de [AÑO].`

> `Que la multa fue dictada mediante sentencia de fecha [DIA] de [MES] de [AÑO], por el Juzgado de Policía Local de [TRIBUNAL], en autos Rol [ROL], actuario [ACTUARIO].`

> `Que, habiendo transcurrido más de tres años desde la fecha de la anotación de la multa impaga, vengo en solicitar que se exhorte al referido Juzgado de Policía Local para efectos de que éste declare la prescripción de la multa.`

> `Acceder a lo solicitado, exhortando al Juzgado de Policía Local de la referencia, para que declare la prescripción de la multa.`

### Esqueleto anonimizado

```
SOLICITA EXHORTO PARA DECLARACIÓN DE PRESCRIPCIÓN DE MULTA EN REGISTRO
DE MULTAS DE TRÁNSITO NO PAGADAS (EMPADRONADOS)
OTROSÍ: NOTIFICACIÓN ELECTRÓNICA

S.J. DE POLICÍA LOCAL DE [COMUNA] (1º)

Nombre completo: [NOMBRE COMPLETO]
Cédula de identidad: [RUT]
Edad: [EDAD]
Profesión u oficio: [PROFESIÓN U OFICIO]
Domicilio completo: [DOMICILIO COMPLETO]
Contacto telefónico: [TELÉFONO]

A US., con el debido respeto digo:

	Que soy propietario(a) del vehículo marca [MARCA], modelo [MODELO],
color [COLOR], año [AÑO], placa patente única [PATENTE], el cual registra
una anotación por multa impaga en el Registro de Multas del Tránsito
no pagadas, desde el día [FECHA].
	Que la multa fue dictada mediante sentencia de fecha [FECHA], por
el Juzgado de Policía Local de [COMUNA/TRIBUNAL], en autos Rol [ROL-AÑO],
actuario [INICIALES].
	Que, habiendo transcurrido más de tres años desde la fecha de la
anotación de la multa impaga, vengo en solicitar que se exhorte al
referido Juzgado de Policía Local para efectos de que éste declare la
prescripción de la multa.

Por estas consideraciones y lo dispuesto en los incisos 1º, 2º y 3º del
artículo 24 de la Ley Nº 18.287

Ruego a SS.,

	Acceder a lo solicitado, exhortando al Juzgado de Policía Local de
la referencia, para que declare la prescripción de la multa.

OTROSÍ: Solicito que las resoluciones que sean dictadas al efecto se me
notifiquen al siguiente correo electrónico: [EMAIL]

FIRMA:
```

---

## 7. FORMULARIO 3 — Prescripción multa tránsito con sentencia firme (NO empadronado)

**Plantilla base:** `07_prescripcion_form3_transito_no_empadronado.txt`

### Propósito
El condenado solicita declarar prescrita una **multa de tránsito ya firme y ejecutoriada** de causa de este tribunal, sin anotación RMNP. Plazo: **1 año desde que la sentencia quedó firme** (art. 54 inc. 1º Ley 15.231).

### Estructura (orden exacto)
1. Sumilla: `EN LO PRINCIPAL: SOLICITA PRESCRIPCIÓN MULTA DE TRÁNSITO CON SENTENCIA FIRME (NO EMPADRONADO)` + `OTROSÍ: NOTIFICACIÓN ELECTRÓNICA`.
2. Tribunal + bloque de identificación (igual a Formularios 1-2).
3. Hecho 1: condena por sentencia de fecha a multa de [MONTO] UTM; notificación con fecha; estado firme y ejecutoriada.
4. Hecho 2 + fundamento juntos: más de un año desde firmeza + art. 54 inc. 1º Ley 15.231 → solicitud de prescripción.
5. Petición: declarar prescrita la multa.
6. OTROSÍ notificación electrónica + FIRMA.

### Frases obligatorias textuales
> `Que por sentencia de fecha [DIA] de [MES] de [AÑO], fui condenado al pago de una multa de [MONTO] UTM. Dicha sentencia me fue notificada con fecha [DIA] de [MES] de [AÑO] y actualmente se encuentra firme y ejecutoriada.`

> `Que, habiendo transcurrido más de un año desde que la sentencia se encuentra firme, en conformidad con lo dispuesto en el artículo 54 inciso 1° de la Ley N° 15.231, vengo en solicitar la declaración de prescripción de la referida multa.`

> `Acceder a lo solicitado, declarando prescrita la multa a la que fui condenado(a) en estos autos.`

Nota: este formulario NO cita el art. 24 de la 18.287 ni menciona R.M.N.P.; el fundamento es exclusivamente el art. 54 inc. 1º de la Ley N° 15.231.

### Esqueleto anonimizado

```
EN LO PRINCIPAL: SOLICITA PRESCRIPCIÓN MULTA DE TRÁNSITO CON SENTENCIA
FIRME (NO EMPADRONADO)
OTROSÍ: NOTIFICACIÓN ELECTRÓNICA

S.J. DE POLICÍA LOCAL DE [COMUNA] (1º)

[Bloque de identificación: Nombre / Cédula / Edad / Profesión /
Domicilio / Teléfono]

	Que por sentencia de fecha [FECHA], fui condenado al pago de una
multa de [MONTO] UTM. Dicha sentencia me fue notificada con fecha
[FECHA] y actualmente se encuentra firme y ejecutoriada.
	Que, habiendo transcurrido más de un año desde que la sentencia
se encuentra firme, en conformidad con lo dispuesto en el artículo 54
inciso 1° de la Ley N° 15.231, vengo en solicitar la declaración de
prescripción de la referida multa.

Por estas consideraciones ruego a SS.,

	Acceder a lo solicitado, declarando prescrita la multa a la que
fui condenado(a) en estos autos.

OTROSÍ: Solicito que las resoluciones que sean dictadas al efecto se me
notifiquen al siguiente correo electrónico: [EMAIL]

FIRMA:
```

---

## 8. FORMULARIO 4 — Prescripción multa tránsito vía exhorto (NO empadronado)

**Plantilla base:** `08_prescripcion_form4_transito_exhorto.txt`

### Propósito
Combinación Formulario 3 + exhorto: la sentencia firme fue dictada por **otro juzgado** y se pide exhorte a ese tribunal para declare la prescripción (art. 54 inc. 1º Ley 15.231).

### Diferencias con Formulario 3
1. Sumilla: `SOLICITA EXHORTO PARA LA DECLARACIÓN DE PRESCRIPCIÓN DE MULTA DE TRÁNSITO (NO EMPADRONADO)` + OTROSÍ.
2. Fórmula inicial: `A US., con el debido respeto digo:`
3. La identificación del juzgado origen va integrada en el primer hecho: `dictada por el Juzgado De Policía Local de [TRIBUNAL]`.
4. Petición exhortativa idéntica a la del Formulario 2.

### Frases obligatorias textuales
> `Que por sentencia de fecha [DIA] de [MES] de [AÑO] dictada por el Juzgado De Policía Local de [TRIBUNAL], fui condenado al pago de una multa de [MONTO] UTM. La sentencia me fue notificada con fecha [DIA] de [MES] de [AÑO] y actualmente se encuentra firme y ejecutoriada.`

> `Que, habiendo transcurrido más de un año desde que la sentencia se encuentra firme, vengo en solicitar que se exhorte al referido Juzgado de Policía Local para efectos de que éste declare la prescripción de la multa.`

> `Por estas consideraciones y teniendo presente lo dispuesto en el artículo 54 inciso 1° de la Ley N° 15.231,`

> `Acceder a lo solicitado, exhortando al Juzgado de Policía Local de la referencia, para que declare la prescripción de la multa.`

### Esqueleto anonimizado

```
SOLICITA EXHORTO PARA LA DECLARACIÓN DE PRESCRIPCIÓN DE MULTA DE
TRÁNSITO (NO EMPADRONADO)
OTROSÍ: NOTIFICACIÓN ELECTRÓNICA

S.J. DE POLICÍA LOCAL DE [COMUNA] (1º)

[Bloque de identificación]

A US., con el debido respeto digo:

	Que por sentencia de fecha [FECHA] dictada por el Juzgado De
Policía Local de [COMUNA/TRIBUNAL], fui condenado al pago de una multa
de [MONTO] UTM. La sentencia me fue notificada con fecha [FECHA] y
actualmente se encuentra firme y ejecutoriada.
	Que, habiendo transcurrido más de un año desde que la sentencia
se encuentra firme, vengo en solicitar que se exhorte al referido
Juzgado de Policía Local para efectos de que éste declare la
prescripción de la multa.

Por estas consideraciones y teniendo presente lo dispuesto en el
artículo 54 inciso 1° de la Ley N° 15.231,

Ruego a SS.,

	Acceder a lo solicitado, exhortando al Juzgado de Policía Local
de la referencia, para que declare la prescripción de la multa.

OTROSÍ: Solicito que las resoluciones que sean dictadas al efecto se me
notifiquen al siguiente correo electrónico: [EMAIL]

FIRMA:
```

---

## 9. Reconsideración de multa

**Plantilla base:** `09_reconsideracion_multa.txt`

### Propósito
Recurso de reposición del afectado contra la multa impuesta, pidiendo amonestación, rebaja al mínimo o reconsideración de la sanción (art. 21 Ley 18.287). Debe interponerse **antes de pagar** y **dentro de 30 días** desde la notificación de la condena.

### Estructura (orden exacto)
1. Título: `RECONSIDERACIÓN DE MULTA.`
2. Tribunal: `S. J. L. DE POLICÍA LOCAL DE [COMUNA] ([NUMERO JUZGADO])`.
3. Bloque de identificación (mismo formato de los formularios).
4. Solicitud de notificación electrónica (correo).
5. Fundamento procesal + apertura argumental (art. 21 Ley 18.287).
6. Referencia a la notificación de la multa + primer descargo.
7. Desarrollo de descargos (fecha, lugar, circunstancias, actuación del funcionario, pruebas, fojas).
8. Cierre petitorio con ALTERNATIVAS marcadas.
9. FIRMA.

### Frases obligatorias textuales
> `En conformidad a lo dispuesto en el artículo 21 de la Ley Nº 18.287, solicito a SS. una reconsideración de la multa impuesta, en virtud de los siguientes argumentos:`

> `Sr. Juez., respecto a la multa impuesta, notificada a mi persona el día [DIA] de [MES] de [AÑO], debo decir que [DESCARGO PRINCIPAL: p. ej. "no me llegó ninguna citación respecto a esta infracción, de lo contrario hubiera comparecido inmediatamente y no me condenarían en rebeldía"].`

Cierre petitorio (elegir alternativa):
> `Finalmente, solicito respetuosamente a Usía. [una amonestación por esta infracción] / [una rebaja de la multa a su monto mínimo] / [la reconsideración de la sanción], ya que [hecho fortuito / primera infracción / certificado de conductor intachable / hechos fundados], agregando que mi [Certificado de Conductor se encuentra intachable / hoja de vida favorable].`

### Convenciones
- Dirige indistintamente a `SS.` (apertura) y a `Usía.` (cierre), tal como está en la plantilla.
- Los argumentos típicos: primera infracción, hecho fortuito, hoja de vida intachable, falta de citación previa.

### Esqueleto anonimizado

```
RECONSIDERACIÓN DE MULTA.

S. J. L. DE POLICÍA LOCAL DE [COMUNA] ([Nº JUZGADO])

Nombre completo: [NOMBRE COMPLETO]
Cédula de identidad: [RUT]
Edad: [EDAD]
Profesión u oficio: [PROFESIÓN U OFICIO]
Domicilio completo: [DOMICILIO COMPLETO]
Contacto telefónico: [TELÉFONO]

Solicito que las resoluciones que se dicten en el proceso me sean
notificadas al siguiente correo electrónico: [EMAIL]

En conformidad a lo dispuesto en el artículo 21 de la Ley Nº 18.287,
solicito a SS. una reconsideración de la multa impuesta, en virtud de
los siguientes argumentos:

Sr. Juez., respecto a la multa impuesta, notificada a mi persona el día
[FECHA], debo decir que [DESCARGO PRINCIPAL: ausencia de citación /
circunstancias del hecho / actuación del inspector / pruebas y fojas].

[FUNDAMENTACIÓN ADICIONAL]

Finalmente, solicito respetuosamente a Usía. [una amonestación por esta
infracción] / [una rebaja de la multa a su monto mínimo] / [la
reconsideración de la sanción], ya que [hecho fortuito / primera
infracción / certificado de conductor intachable / hechos fundados],
agregando que mi Certificado de Conductor se encuentra intachable /
hoja de vida favorable.

FIRMA:
```

---

## 10. Reconsideración de días de suspensión de licencia

**Plantilla base:** `10_reconsideracion_suspension.txt`

### Propósito
Tras PAGAR la multa, el condenado pide rebajar los días de suspensión de su licencia (art. 21 Ley 18.287). Requisito práctico: acompañar comprobante de pago en otrosí.

### Estructura (orden exacto)
1. Título: `SOLICITA RECONSIDERACIÓN DE LOS DÍAS DE SUSPENSIÓN DE LICENCIA DE CONDUCTOR`.
2. Tribunal + bloque de identificación + solicitud correo electrónico.
3. Frase clave: pago de la multa + art. 21 + solicitud de rebaja de días.
4. Argumentos (hoja de vida favorable, necesidad laboral de la licencia, primera infracción, tiempo transcurrido).
5. `POR TANTO`: rebaja concreta a [N] días.
6. `OTROSÍ`: acompaña comprobante de pago de la multa.
7. FIRMA.

### Frases obligatorias textuales
> `Habiéndose pagado la multa impuesta, según da cuenta el comprobante que se acompaña en el otrosí, y en conformidad a lo dispuesto en el artículo 21 de la Ley Nº 18.287, solicito a SS. una rebaja de los días de suspensión de mi licencia de conductor, en virtud de los siguientes argumentos:`

> `POR TANTO, ruego a SS., acceder a lo solicitado, rebajando los días de suspensión de mi licencia de conductor a [N] días.`

> `OTROSÍ: acompañase comprobante de pago de la multa.`

### Esqueleto anonimizado

```
SOLICITA RECONSIDERACIÓN DE LOS DÍAS DE SUSPENSIÓN DE LICENCIA DE
CONDUCTOR

S. J. L. DE POLICÍA LOCAL DE [COMUNA] ([Nº JUZGADO])

[Bloque de identificación]

Solicito que las resoluciones que se dicten en el proceso me sean
notificadas al siguiente correo electrónico: [EMAIL]

Habiéndose pagado la multa impuesta, según da cuenta el comprobante que
se acompaña en el otrosí, y en conformidad a lo dispuesto en el artículo
21 de la Ley Nº 18.287, solicito a SS. una rebaja de los días de
suspensión de mi licencia de conductor, en virtud de los siguientes
argumentos:

[ARGUMENTOS: hoja de vida favorable / necesidad de la licencia para
trabajar / primera infracción / tiempo transcurrido]

POR TANTO, ruego a SS., acceder a lo solicitado, rebajando los días de
suspensión de mi licencia de conductor a [N] días.

OTROSÍ: acompañase comprobante de pago de la multa.

FIRMA:
```

---

## 11. Reclamación contra denegación de licencia de conductor

**Plantilla base:** `11_reclamacion_denegacion_licencia.txt`

### Propósito
Reclamación judicial contra la resolución del Director de Tránsito que deniega la licencia por **carencia de idoneidad moral**. Plazo fatal: **5 días hábiles** desde notificada la denegación (art. 15 inc. 3º Ley 18.290).

### Destinatario / tribunal
`S. J. L. DE POLICÍA LOCAL DE [COMUNA] ([NUMERO JUZGADO])` — el juez de policía local de la comuna resuelve breve y sumariamente, apreciando la prueba en conciencia.

### Fundamentos legales citados
- **Denegación (norma vigente):** `el artículo 15 de la Ley Nº 18.290` — su
  inciso 2º obliga al Director del Departamento de Tránsito a **rechazar,
  señalando la causal**, las solicitudes de postulantes que no cumplan los
  requisitos; y `el artículo 11 del D.S. Nº 170/1985` (Reglamento de
  Licencias: calificación de idoneidad moral, física y psíquica mediante los
  exámenes correspondientes).
- ⚠️ **Cita histórica corregida:** los formularios antiguos decían «artículo
  16 de la Ley Nº 19.495». Eso es incorrecto como cita vigente: la Ley Nº
  19.495 fue la ley MODIFICATORIA que introdujo el ex art. 14 bis (hoy art.
  15) en la Ley 18.290; no debe citarse por su propio artículo. Usar siempre
  `artículo 15 de la Ley Nº 18.290`.
  **Variante dominante documentada:** las sentencias reales del tribunal sí
  reproducen «artículo 16 de la Ley Nº 19.495» SOLO cuando transcriben lo
  invocado por la propia Dirección de Tránsito en su acto denegatorio
  (considerando 1º), para luego fundamentar en los arts. 15 inc. 3º, 16
  (quinquenio de condenas) y 20 (período de control condicional, típicamente 4
  años) de la Ley Nº 18.290. En un ESCRITO del reclamante, citar siempre el
  art. 15 Ley 18.290.
- Plazo: `el artículo 15 inciso 3° de la Ley Nº 18.290` — cinco días hábiles,
  sin recurso posterior.

### Frases obligatorias textuales
> `Que con fecha [DIA] de [MES] de [AÑO], el Director de Tránsito y Transporte Público de la I. Municipalidad de [COMUNA] determinó denegar la licencia de conductor clase [CLASE] solicitada por mí, tramitada por control, al presentar carencia de idoneidad moral para continuar conduciendo, de acuerdo con lo dispuesto en el artículo 15 de la Ley Nº 18.290 y el artículo 11 del D.L. Nº 170 de 1985.`

> `Encontrándome dentro del plazo de cinco días hábiles señalado en el artículo 15 inciso 3° de la Ley Nº 18.290, deduzco reclamación en contra de la citada resolución, fundada en los siguientes antecedentes:`

> `POR TANTO, ruego a S.S., tener por presentada esta reclamación en contra de la resolución del Director de Tránsito y Transporte Público de la I. Municipalidad de [COMUNA] y, en definitiva, acogerla, declarando que tengo idoneidad moral para que se me otorgue la licencia de conductor de vehículos clase [CLASE].`

### Documentos típicamente acompañados (lista de plantilla)
`Certificado de antecedentes del conductor`, `Informe psicológico`, `Certificados de tratamiento o controles`, `Contratos de trabajo / certificados académicos`, otros.

### Esqueleto anonimizado

```
RECLAMACIÓN EN CONTRA DE DENEGACIÓN DE LICENCIA DE CONDUCTOR

S. J. L. DE POLICÍA LOCAL DE [COMUNA] ([Nº JUZGADO])

[Bloque de identificación]

Que con fecha [FECHA], el Director de Tránsito y Transporte Público de
la I. Municipalidad de [COMUNA] determinó denegar la licencia de
conductor clase [CLASE] solicitada por mí, tramitada por control, al
presentar carencia de idoneidad moral para continuar conduciendo,
de acuerdo con lo dispuesto en el artículo 15 de la Ley Nº 18.290 y el
artículo 11 del D.L. Nº 170 de 1985.

Encontrándome dentro del plazo de cinco días hábiles señalado en el
artículo 15 inciso 3° de la Ley Nº 18.290, deduzco reclamación en contra
de la citada resolución, fundada en los siguientes antecedentes:

[ARGUMENTOS: rehabilitación / situación laboral o académica / controles
voluntarios (D.S. 409) / certificados / contratos / informes]

Se acompañan los siguientes documentos:
- [Certificado de antecedentes del conductor]
- [Informe psicológico]
- [Certificados de tratamiento o controles]
- [Contratos de trabajo / certificados académicos]
- [Otros]

POR TANTO, ruego a S.S., tener por presentada esta reclamación en contra
de la resolución del Director de Tránsito y Transporte Público de la
I. Municipalidad de [COMUNA] y, en definitiva, acogerla, declarando
que tengo idoneidad moral para que se me otorgue la licencia de conductor
de vehículos clase [CLASE].

FIRMA:
```

---

## 12. Resolución de acumulación de causas / infracciones

**Plantilla base:** `12_resolucion_acumulacion.txt`

### Propósito
Resolución judicial que acumula dos causas con **hechos denunciados idénticos** (la de ingreso posterior se acumula a la anterior) y, según el caso, informa al Registro Civil el resultado respecto del art. 207 letra B Ley 18.290.

### Estructura (orden exacto)
1. Título interno: `RESOLUCIÓN DE ACUMULACIÓN DE CAUSAS / INFRACCIONES` + `RESOLUCIÓN Nº [NUMERO]`.
2. Lugar y fecha: `[COMUNA], a [DIA] de [MES] de [AÑO].-`
3. Consideración única + decreto de acumulación.
4. VARIANTE opcional de información al Registro Civil (tres versiones).
5. Cierre procesal: `ANÓTESE, OFÍCIESE Y NOTIFÍQUESE.`
6. Firmas JUEZ + SECRETARIA con cargos.

### Frases obligatorias textuales
Núcleo dominante:
> `Visto que los hechos denunciados en la causa Rol Nº [ROL_INFERIOR]-[AÑO], Actuario [ACTUARIO], son los mismos que dieron origen a la causa Rol Nº [ROL_SUPERIOR]-[AÑO], Actuario [ACTUARIO], acumúlese aquella a esta.`

Variantes de información al Registro Civil (opcional, elegir UNA):

1. Cumplimiento por acumulación:
> `Infórmese al Registro Civil que el denunciado dio cumplimiento a lo establecido en el Art. 207 letra B de la Ley Nº 18.290 por acumulación de infracciones. Ofíciese, una vez hecho. Archívese.`

2. Absuelto por acumulación:
> `Infórmese al Registro Civil que el denunciado fue ABSUELTO del denuncio de fojas [FOJAS] por Acumulación de infracciones, ya que no se configura lo establecido en el art. 207-B de la Ley Nº 18.290 por acumulación de infracciones. Ofíciese, una vez hecho. Archívese.`

3. Dio cumplimiento acumulación infr. tránsito:
> `Ofíciese al Servicio de Registro Civil de [COMUNA], a fin de informar que el denunciado don/doña [NOMBRE], c.i. [RUT], ha dado cumplimiento con lo establecido en el Art. 207/B de la Ley Nº 18.290. Una vez hecho, archívense los antecedentes.`

Cierre:
> `ANÓTESE, OFÍCIESE Y NOTIFÍQUESE.`

### Convenciones
- Siempre individualizar AMBOS roles con su actuario.
- La causa acumulada es siempre la de ingreso posterior (Rol superior); la acumulante conserva el Rol inferior.

### Esqueleto anonimizado

```
RESOLUCIÓN Nº [NUMERO]

[CIUDAD], a [DIA] de [MES] de [AÑO].-

Visto que los hechos denunciados en la causa Rol Nº [ROL POSTERIOR]-[AÑO],
Actuario [APELLIDO], son los mismos que dieron origen a la causa Rol Nº
[ROL ANTERIOR]-[AÑO], Actuario [APELLIDO], acumúlese aquella a esta.

[VARIANTE OPCIONAL RC — ver frases 1-3 arriba]

ANÓTESE, OFÍCIESE Y NOTIFÍQUESE.

				[NOMBRE JUEZ]
				[CARGO JUEZ]

	[NOMBRE SECRETARIA]
	[CARGO SECRETARIA]
```

---

## 13. Descargos generales por infracción

**Plantilla base:** `13_descargo_general.txt`

### Propósito
Formulario de descargos del denunciado ANTES de la audiencia: acepta o niega lo dicho en el parte; si niega, fundamenta. Se invoca el art. 14 Ley 18.287 (apreciación prueba / defensa).

### Estructura (orden exacto)
1. Título: `DESCARGOS POR INFRACCIÓN`.
2. Tribunal: `S.J.L. DE POLICÍA LOCAL DE [COMUNA] ([NUMERO JUZGADO])`.
3. Fecha: `En [CIUDAD], a [DIA] de [MES] de [AÑO].`
4. Bloque de identificación + solicitud correo electrónico.
5. `QUIEN EXPONE:` con DOS alternativas marcables con "x":
   - acepta lo que dice el parte;
   - niega lo que dice el parte → fundamentación breve obligatoria.
6. `POR TANTO` con art. 14 Ley 18.287: tener por presentados los descargos, teniéndose presente lo expuesto al resolver.
7. FIRMA.

### Frases obligatorias textuales
> `QUIEN EXPONE: (Marque su alternativa con una "x")`
>
> `1.- Lo que dice el parte es efectivo (____)`
>
> `2.- Lo que dice el parte no es efectivo (____). En este caso, fundamente brevemente:`

> `POR TANTO y de conformidad a lo dispuesto en el artículo 14 de la Ley Nº 18.287, ruego a SS. tener por presentados estos descargos, teniéndose presente lo expuesto al resolver.`

### Esqueleto anonimizado

```
DESCARGOS POR INFRACCIÓN

S.J.L. DE POLICÍA LOCAL DE [COMUNA] ([Nº JUZGADO])

En [CIUDAD], a [DIA] de [MES] de [AÑO].

Nombre completo: [NOMBRE COMPLETO]
Cédula de identidad: [RUT]
Edad: [EDAD]
Profesión u oficio: [PROFESIÓN U OFICIO]
Domicilio completo: [DOMICILIO COMPLETO]
Contacto telefónico: [TELÉFONO]

Solicito que las resoluciones que se dicten en el proceso me sean
notificadas al siguiente correo electrónico: [EMAIL]

QUIEN EXPONE: (Marque su alternativa con una "x")
1.- Lo que dice el parte es efectivo (____)
2.- Lo que dice el parte no es efectivo (____). En este caso, fundamente
brevemente:

[FUNDAMENTACIÓN SI EL PARTE NO ES EFECTIVO: circunstancias, descargo,
pruebas]

POR TANTO y de conformidad a lo dispuesto en el artículo 14 de la Ley
Nº 18.287, ruego a SS. tener por presentados estos descargos,
teniéndose presente lo expuesto al resolver.

FIRMA:
```

---

## 14. RESPUESTAS TIPO PARA LA CONTESTACIÓN DE CORREOS DEL PÚBLICO

**Fuente:** documento fuente del tribunal (*RESPUESTAS CORREO.docx* — «Respuestas tipo para la contestación de correos»).

### Propósito / cuándo se usa
Plantillas de respuesta del correo institucional del tribunal para las consultas
y presentaciones más frecuentes del público. No son oficios ni resoluciones:
son respuestas administrativas de oficina de partes. Se envían desde la cuenta
de correo oficial del tribunal y cierran siempre con la fórmula
`Cordialmente, [NÚMERO] Juzgado de Policía Local de [COMUNA].`

### Convenciones comunes
- Trato: `Estimado(a):` / `Estimada (o),` indistinto en el original.
- Horario de atención (se repite en casi todas): `LUNES: de 14:30 a 18:30 horas, MARTES A VIERNES: de 8:30 a 13:00 horas.` → `[HORARIO DE ATENCIÓN]`.
- Límite de adjuntos: por razones presupuestarias **máximo 10 hojas** por documento adjunto recibido por esta vía; el excedente debe presentarse presencialmente.
- Cero datos personales en la respuesta: usar `[CORREO]`, `[ROL CAUSA]`, `[RUT]`.

### 14.1 Horario de funcionamiento del juzgado
> `Se recuerda que el juzgado se ubica en [DOMICILIO DEL TRIBUNAL]. Horario de atención de público: LUNES: de 14:30 a 18:30 horas, MARTES A VIERNES: de 8:30 a 13:00 horas. Cordialmente, Primer Juzgado de Policía Local de [COMUNA].`

### 14.2 Acuse de recibo general
> `Estimado(a), se acusa recibo. Se informa que por razones de índole presupuestaria solo se recibirán documentos adjuntos por esta vía con un máximo de 10 hojas. De exceder esta cantidad, se deberá presentar la documentación de manera presencial en los siguientes horarios de atención de público: [HORARIO DE ATENCIÓN]. Cordialmente, [NÚMERO] Juzgado de Policía Local de [COMUNA].`

### 14.3 Excede máximo de hojas
> `Estimado(a): Por razones de índole presupuestaria solo se recibirán documentos adjuntos por esta vía con un máximo de 10 hojas. De exceder esta cantidad, se deberá presentar la documentación de manera presencial en los siguientes horarios de atención de público: [HORARIO DE ATENCIÓN]. Cordialmente, [NÚMERO] Juzgado de Policía Local de [COMUNA].`

### 14.4 Pago a distancia
Aplica solo si la multa ya tiene sentencia dictada. Tres modalidades excluyentes:
1. **Vale vista por correo certificado:** indicando en la carta el número de rol
   del proceso que incide en el pago; el documento debe venir a nombre de la
   `I. MUNICIPALIDAD DE [COMUNA], RUT Nº [RUT MUNICIPALIDAD]`, al domicilio del
   tribunal (`[DOMICILIO DEL TRIBUNAL]`).
2. **Mandato:** mandatar a cualquier persona para pagar en caja; basta acudir al
   tribunal, solicitar por ventanilla la emisión del giro y pagar con el sólo
   número de cédula de identidad del condenado.
3. **Pago en línea:** solo si la causa tiene sentencia y el pago está liberado,
   ingresando al portal de pagos de la municipalidad `[URL PAGO EN LÍNEA]`.

### 14.5 Revisión de expedientes
> `Estimado(a): Puede acercarse a nuestras dependencias y en la ventanilla de oficina de partes solicitar hablar con el/la secretario(a) abogado(a) [NOMBRE SECRETARIO/A], quien le hará entrega del expediente que desee revisar. Horario de atención de público: [HORARIO DE ATENCIÓN]. Cordialmente, [NÚMERO] Juzgado de Policía Local de [COMUNA].`

### 14.6 No se recibirán consultas
> `Estimado(a): A partir del día [FECHA], este correo opera solo para la recepción de escritos, denuncias o demandas nuevas. No se responderán consultas por esta vía. Se recuerda que el juzgado se ubica en [DOMICILIO DEL TRIBUNAL]. Horario de atención de público: [HORARIO DE ATENCIÓN]. Cordialmente, [NÚMERO] Juzgado de Policía Local de [COMUNA].`

### 14.7 Excusa por no presentarse a votar
> `Estimado(a): Una vez que le llegue una citación de parte del juzgado por no presentarse a votar debe dar sus excusas entonces, no antes, ya que por el momento no tiene causa en ningún tribunal del país. Cordialmente, [NÚMERO] Juzgado de Policía Local de [COMUNA].`

---

## 15. Tabla-resumen de fundamentos legales citados

| Documento | Fundamento textual | Objeto |
|---|---|---|
| Form 1 prescripción | `incisos 1º y 2º del artículo 24 de la Ley Nº 18.287` | Multa anotada en R.M.N.P., 3 años |
| Form 2 prescripción exhorto | `los incisos 1º, 2º y 3º del artículo 24 de la Ley Nº 18.287` | Ídem + exhorto a otro juzgado |
| Form 3 prescripción | `artículo 54 inciso 1° de la Ley N° 15.231` | Multa firme no empadronada, 1 año |
| Form 4 prescripción exhorto | `artículo 54 inciso 1° de la Ley N° 15.231` | Ídem + exhorto |
| Reconsideración multa | `artículo 21 de la Ley Nº 18.287` | Reposición/moderación de multa |
| Reconsideración suspensión | `artículo 21 de la Ley Nº 18.287` | Rebaja días de suspensión |
| Reclamación licencia | `artículo 15 (incs. 2º y 3º) de la Ley Nº 18.290` + `artículo 11 del D.L. Nº 170/1985` | Plazo 5 días hábiles. NO citar «art. 16 Ley 19.495» (ley modificatoria; cita histórica errónea) |
| Acumulación | `Art. 207 letra B de la Ley Nº 18.290` | Informe RC por acumulación de infracciones |
| Descargos | `artículo 14 de la Ley Nº 18.287` | Defensa / apreciación de la prueba |
