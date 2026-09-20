# FORMATOS-CERTIFICADOS-EXHORTOS

**Categoría:** formatos | **ID:** 1

---

# FORMATOS — CERTIFICADOS Y EXHORTOS (JPL [COMUNA])

Manual de estructura exacta de los documentos de exhortos y certificados de notificación.
Fuente: `modelos/consolidado/plantillas/exhortos_certificados/` (9 plantillas canónicas), complementado con documentos fuente del tribunal.
Todo dato variable va como `[MARCADOR]`. Las frases entre comillas son TEXTUALES de las plantillas.

---

## 0. Convenciones comunes

### 0.1 Membrete y encabezado

| Tipo | Encabezado |
|---|---|
| Resoluciones que proveen exhortos entrantes | `En [CIUDAD], a [DIA] de [MES] de [AÑO].` — sin membrete, cuerpo con sangría |
| Certificados de notificación | Sin encabezado: la primera palabra es `CERTIFICO:` |
| Oficio devolución de exhorto | `OFICIO N°[NUMERO]` + `MAT: LO QUE INFORMA` + `[CIUDAD], [FECHA]` |
| Resolución incompetencia por turno | `En [CIUDAD], a [DIA] de [MES] de [AÑO].` |

### 0.2 Fechas
- En resoluciones de proveimiento: `a [DIA] de [MES] de [AÑO]` en números o letras según el original.
- En certificados: fecha de cierre SIEMPRE en letras: `En [CIUDAD], a [FECHA EN LETRAS].`
- La fecha del certificado puede ser posterior a la fecha de la diligencia (se certifica "el día [X]" y se firma "En [CIUDAD], a [Y]").

### 0.3 Firmas
- **Certificados:** bloque a la derecha, dos líneas:

```
                                                                        [NOMBRE RECEPTOR]
                                                                        RECEPTOR AD-HOC
```

- **Oficio devolución de exhorto:** dos firmas apiladas a la derecha: `[NOMBRE JUEZ]` / `JUEZ TITULAR` y debajo `[NOMBRE SECRETARIO]` / `SECRETARIO ABOGADO (S)`.
- **Incompetencia por turno:** `[NOMBRE JUEZ]` / `JUEZ TITULAR`, luego línea de cúmplase y `[NOMBRE SECRETARIO]` / `SECRETARIO (S)`.

### 0.4 Ministro de fe
Las notificaciones las practica un **receptor ad-hoc designado por resolución** (normalmente funcionaria/o del tribunal, individualizado con nombre y correo electrónico). Los derechos de notificación se consignan al final del certificado como `Derechos $[MONTO].`

---

## 1. Exhorto para citar a declarar (resolución que provee exhorto entrante)

**Plantilla base:** `exhortos_certificados/01_exhorto_citar_a_declarar.txt`

### Propósito / cuándo se usa
Cuando OTRO tribunal remite un exhorto/oficio pidiendo citar a una persona domiciliada en esta jurisdicción **a prestar declaración indagatoria** ante el tribunal exhortante. El tribunal exhortado ingresa el exhorto, fija fecha/hora y ordena notificar por Inspección Comunal.

### Estructura (orden exacto)
1. Lugar y fecha (`En [CIUDAD], a ...`).
2. Fórmula de ingreso: recibido e ingresado el exhorto.
3. Orden de citación con individualización completa de la persona.
4. Día y hora de la declaración.
5. Vía de notificación (Inspección Comunal).
6. Cierre procesal `Ofíciese.`

### Frases obligatorias textuales
> `Por recibido con esta fecha. Ingrésese exhorto Oficio N°[NUMERO], del [JUZGADO ORIGEN] y cítese a [NOMBRE DE LA PERSONA], [RUT], con domicilio en [DOMICILIO], a prestar declaración indagatoria en este tribunal, el día [FECHA DE LA DECLARACIÓN], a las [HORA] horas. Notifíquese a través del departamento de Inspección Comunal. Ofíciese.`

Variante real (documento fuente): la hora se expresa como `a la audiencia del día [FECHA], a las 17:00 horas`; el resto idéntico.

### Convenciones
- El número del exhorto entrante se cita como `Oficio N°[NUMERO]`.
- La citación siempre se notifica por **Inspección Comunal**, no por receptor ad-hoc.
- No lleva bloque de firmas (es decreto).

### Esqueleto anonimizado

```
En [CIUDAD], a [DIA] de [MES] de [AÑO].
   Por recibido con esta fecha. Ingrésese exhorto Oficio N°[NUMERO],
del [JUZGADO ORIGEN] y cítese a [NOMBRE COMPLETO], [RUT], con domicilio
en [DOMICILIO COMPLETO], a prestar declaración indagatoria en este
tribunal, el día [DIA] de [MES] de [AÑO], a las [HORA] horas.
Notifíquese a través del departamento de Inspección Comunal. Ofíciese.
```

---

## 2. Exhorto para citar audiencia

**Plantilla base:** `exhortos_certificados/02_exhorto_citar_audiencia.txt`

### Propósito / cuándo se usa
Igual que el anterior, pero la persona debe comparecer **a una audiencia** fijada por el tribunal exhortante (contestación, prueba, ratificación), no a declarar indagatoriamente.

### Estructura (orden exacto)
1. Lugar y fecha.
2. Fórmula de ingreso del exhorto (con `[TIPO]` opcional antes del número).
3. Orden de citación + individualización (nombre, RUT, domicilio).
4. Fecha y hora de la audiencia.
5. Notificación por Inspección Comunal.
6. `Ofíciese.`

### Frases obligatorias textuales
> `Por recibido con esta fecha. Ingrésese exhorto [TIPO] N°[NUMERO], del [JUZGADO ORIGEN] y cítese a [NOMBRE DE LA PARTE], [RUT], con domicilio en [DOMICILIO], a la audiencia del día [FECHA DE AUDIENCIA], a las [HORA] horas. Notifíquese a través del departamento de Inspección Comunal. Ofíciese.`

### Convenciones
- Única diferencia con el tipo 1: `a la audiencia del día...` en vez de `a prestar declaración indagatoria...`.
- `[TIPO]` admite variantes (`Exhorto`, vacío, etc.); dominante sin tipo cuando dice solo `Oficio N°`.

### Esqueleto anonimizado

```
En [CIUDAD], a [DIA] de [MES] de [AÑO].
   Por recibido con esta fecha. Ingrésese exhorto [TIPO] N°[NUMERO],
del [JUZGADO ORIGEN] y cítese a [NOMBRE COMPLETO], [RUT], con domicilio
en [DOMICILIO COMPLETO], a la audiencia del día [DIA] de [MES] de [AÑO],
a las [HORA] horas. Notifíquese a través del departamento de Inspección
Comunal. Ofíciese.
```

---

## 3. Exhorto para notificar demanda (querella + demanda civil)

**Plantilla base:** `exhortos_certificados/03_exhorto_notificar_demanda.txt`

### Propósito / cuándo se usa
Exhorto entrante pidiendo notificar en esta jurisdicción una **querella infraccional con demanda civil de indemnización de perjuicios** contra persona o entidad domiciliada aquí. A diferencia de los tipos 1-2, la diligencia la realiza un **receptor ad-hoc designado en la misma resolución**.

### Estructura (orden exacto)
1. Lugar y fecha.
2. Ingreso del exhorto, indicando proceso Rol N° de origen.
3. Objeto: notificación de querella y demanda, con su contenido entre paréntesis.
4. Individualización del notificado (nombre, RUT, representante legal si aplica).
5. Designación de receptor ad-hoc (funcionaria/o del tribunal + correo electrónico; puede designarse más de uno con `y/o`).
6. Cargo a la parte actora de proporcionar medios de contacto.

### Frases obligatorias textuales
> `Por recibido con esta fecha. Ingrésese exhorto [TIPO] N°[NUMERO], del [JUZGADO ORIGEN], respecto al proceso Rol N°[ROL], y notifíquese la querella y demanda (querella infraccional y demanda civil de indemnización de perjuicios) en contra de [NOMBRE DE LA PARTE], [RUT], representada legalmente por [NOMBRE REPRESENTANTE], y desígnese receptor ad-hoc a la funcionaria del tribunal [NOMBRE FUNCIONARIA] ([EMAIL]), y/o [NOMBRE FUNCIONARIA 2] ([EMAIL 2]), a quien el actor deberá proporcionar los medios que permitan practicar la notificación oportunamente.`

### Convenciones
- El Rol citado es el del **proceso de origen** (tribunal exhortante); el ingreso local lleva su propio control.
- Receptor ad-hoc: SIEMPRE con correo electrónico entre paréntesis.
- Si el demandado es persona jurídica, individualizar además al representante legal.

### Esqueleto anonimizado

```
En [CIUDAD], a [DIA] de [MES] de [AÑO].
   Por recibido con esta fecha. Ingrésese exhorto [TIPO] N°[NUMERO],
del [JUZGADO ORIGEN], respecto al proceso Rol N°[ROL-AÑO], y notifíquese
la querella y demanda (querella infraccional y demanda civil de
indemnización de perjuicios) en contra de [NOMBRE DE LA PARTE], [RUT],
representada legalmente por [NOMBRE REPRESENTANTE LEGAL], y desígnese
receptor ad-hoc a la funcionaria del tribunal [NOMBRE FUNCIONARIA]
([EMAIL]), y/o [NOMBRE FUNCIONARIA 2] ([EMAIL 2]), a quien el actor
deberá proporcionar los medios que permitan practicar la notificación
oportunamente.
```

**Complemento (dirección contraria).** Cuando este mismo tribunal ENVÍA el exhorto a otro juzgado para notificar una demanda de su proceso, se usa formato de oficio-exhorto (documento fuente: *CAUSAS COMPLEJAS_EXHORTO NOTIFICACION DEMANDA*): membrete del tribunal, `EXHORTO OFICIO N°[NUMERO]-[AÑO]`, `MAT.: Lo que solicita`, `DE:` juez titular / `A:` juez destino con dirección, cuerpo iniciando `Por resolución de fecha [FECHA], recaída en la Causa rol N° [ROL-AÑO], actuario [ACTUARIO], por [MATERIA], se ha ordenado exhortar al Tribunal de US., a fin de que proceda a notificar la demanda civil de indemnización de perjuicios, que rola a fojas [N] y siguientes...`, facultad de diligenciamiento y cierre `Saluda Atentamente a US.,` con firmas de JUEZ TITULAR y SECRETARIA ABOGADA (S).

---

## 4. Exhorto para notificar sentencia

**Plantilla base:** `exhortos_certificados/04_exhorto_notificar_sentencia.txt`

### Propósito / cuándo se usa
Exhorto entrante pidiendo **notificar una sentencia** (ya dictada en el proceso de origen) a una parte o su abogado domiciliado en esta jurisdicción.

### Estructura (orden exacto)
1. Lugar y fecha.
2. Ingreso del exhorto con número y juzgado origen.
3. Objeto: notificación de la sentencia al abogado/parte, con domicilio.
4. Designación de receptor ad-hoc (una o dos funcionarias con correos).
5. Cargo a la parte de proporcionar medios de contacto.

### Frases obligatorias textuales
> `Por recibido con esta fecha. Ingrésese exhorto Oficio N°[NUMERO], del [JUZGADO ORIGEN], y notifíquese la sentencia al abogado de la querellada y demandada [NOMBRE DE LA PARTE], con domicilio en [DOMICILIO]. Desígnese receptor ad-hoc a la funcionaria del tribunal [NOMBRE FUNCIONARIA] ([EMAIL]), y/o [NOMBRE FUNCIONARIA 2] ([EMAIL 2]), a quien la parte deberá proporcionar los medios que permitan practicar la notificación oportunamente.`

### Convenciones
- Diferencias con notificar demanda: aquí NO se cita Rol del proceso ni RUT; se identifica a quien recibe la notificación (`al abogado de la querellada y demandada`) y su domicilio.
- Calidad de la parte textual según el caso: ajustar (`abogado de la querellada y demandada`, `demandado`, etc.).

### Esqueleto anonimizado

```
En [CIUDAD], a [DIA] de [MES] de [AÑO].
   Por recibido con esta fecha. Ingrésese exhorto Oficio N°[NUMERO],
del [JUZGADO ORIGEN], y notifíquese la sentencia al abogado de la
[calidad de la parte: querellada y demandada / demandado] [NOMBRE],
con domicilio en [DOMICILIO COMPLETO]. Desígnese receptor ad-hoc a la
funcionaria del tribunal [NOMBRE FUNCIONARIA] ([EMAIL]), y/o [NOMBRE
FUNCIONARIA 2] ([EMAIL 2]), a quien la parte deberá proporcionar los
medios que permitan practicar la notificación oportunamente.
```

---

## 5. Certificado de notificación personal

**Plantilla base:** `exhortos_certificados/05_certificado_notificacion_personal.txt`

### Propósito / cuándo se usa
Ministro de fe deja constancia de que notificó **personalmente** (art. 8 inc. 1 Ley 18.287) al requerido, entregándole copias directamente.

### Estructura (orden exacto)
1. `CERTIFICO:` + día (día de semana + fecha), hora.
2. Constitución en el domicilio señalado en autos.
3. Objeto: notificar a [PARTE] de la querella, demanda y proveídos.
4. Forma de la diligencia: PERSONALMENTE, entrega de copias autorizadas, identificación del requerido.
5. Fórmula de fe: `Doy fe.`
6. Cierre: lugar y fecha en letras (+ `Derechos $[MONTO]` cuando corresponde).
7. Firma: RECEPTOR AD-HOC.

### Frases obligatorias textuales
> `CERTIFICO: Que el día [DÍA SEMANA] [FECHA], a las [HORA] horas, concurrí al domicilio señalado en autos, [DOMICILIO], con el objeto de notificar a [NOMBRE DE LA PARTE] de la querella, demanda y proveídos, diligencia que realicé Personalmente, haciéndole entrega de copias autorizadas al requerido, quien se identificó como tal. Doy fe. En [CIUDAD], a [FECHA EN LETRAS]`

Variante antigua (documento fuente): añade tras la identificación `y firmó para constancia (o excusó firmar)`; y exige indicar fojas: `de la (querella, demanda y proveídos, indicar fojas)`.

### Convenciones
- `Personalmente` va con mayúscula inicial en la plantilla canónica.
- La plantilla canónica cierra sin derechos; los originales suelen agregar `Derechos $[MONTO].` → incluirlo salvo instrucción en contrario.
- Identificar fojas de la querella/demanda y proveídos cuando consten.

### Esqueleto anonimizado

```
CERTIFICO: Que el día [DÍA SEMANA] [FECHA], a las [HORA] horas,
concurrí al domicilio señalado en autos, [DOMICILIO COMPLETO], con el
objeto de notificar a [NOMBRE DE LA PARTE] de la querella, demanda y
proveídos [fojas X a Y y resoluciones a fojas Z], diligencia que realicé
Personalmente, haciéndole entrega de copias autorizadas al requerido,
quien se identificó como tal. Doy fe. En [CIUDAD], a [FECHA EN LETRAS].
Derechos $[MONTO].

                                                                        [NOMBRE RECEPTOR]
                                                                        RECEPTOR AD-HOC
```

---

## 6. Certificado de notificación por cédula

**Plantilla base:** `exhortos_certificados/06_certificado_notificacion_cedula.txt`

### Propósito / cuándo se usa
La persona no fue habida personalmente (o la norma exige cédula) y se entrega la copia **a persona adulta habida en el domicilio**, dejando constancia de las búsquedas previas (art. 8 inc. 2 Ley 18.287: no habida en dos días distintos).

### Estructura (orden exacto)
1. `CERTIFICO:` + día, hora, domicilio.
2. Objeto: notificar a [PARTE] (+ representante legal si aplica).
3. Documentos: `de la querella infraccional, demanda civil de indemnización de perjuicios y sus proveídos` (ajustar a lo notificado).
4. Forma: POR CÉDULA, entrega de copias íntegras a persona adulta habida.
5. Identificación de quien recibe.
6. Declaraciones de quien recibe: conoce al demandado, está en el lugar del juicio, aquella es su morada.
7. Constancia de búsquedas anteriores (número, días y horarios distintos).
8. `Doy fe.` + cierre lugar/fecha en letras + derechos.
9. Firma RECEPTOR AD-HOC.

### Frases obligatorias textuales
> `CERTIFICO: Que el día [DÍA SEMANA] [FECHA], a las [HORA] horas, concurrí al domicilio señalado en autos, [DOMICILIO], con el objeto de notificar a [NOMBRE DE LA PARTE], representada legalmente por [NOMBRE REPRESENTANTE], de la querella infraccional, demanda civil de indemnización de perjuicios y sus proveídos, diligencia que realicé POR CÉDULA, haciendo entrega de copias íntegras a persona adulta habida en el domicilio, quien se identificó como [NOMBRE QUIEN RECIBE], quien declaró conocer al querellado y demandado, que este se encuentra en el lugar del juicio y que aquella es su morada. Se deja constancia que se practicaron [NÚMERO] búsquedas anteriores, en días y horarios distintos. Doy fe. En [CIUDAD], a [FECHA EN LETRAS]. Derechos $[MONTO].`

### Variantes registradas (dominante = plantilla canónica)
1. **Quien recibe no se identificó:** `...haciendo entrega de copias íntegras a persona adulta habida en el domicilio, quien no se identificó...` (variante Williams).
2. **Conserje/portero/encargado del edificio:** `Por cédula, haciendo entrega de copias íntegras al conserje (portero o encargado del edificio o recinto), quien declaró conocer al (querellado, demandado)...` — añadir que aquella es su morada **(o lugar de trabajo)**.
3. **Fijación en la puerta (último recurso):** `Por cédula, fijando copias autorizadas en la puerta del lugar. Se deja constancia que se constató consultando a vecinos que el (querellado, demandado) es persona conocida, que se encuentra en el lugar del juicio y que aquella es su morada (o lugar de trabajo). Se deja constancia que se practicaron dos búsquedas anteriores, en días y horarios distintos.`
4. **Búsquedas previas detalladas (estilo antiguo):** `Se deja constancia que se practicaron dos búsquedas anteriores, en el mismo domicilio antes mencionado en días y horas distintas y en ambas ocasiones no se encontró al requerido.`
5. **Lugar de trabajo:** cuando la notificación se hace donde trabaja el demandado, sustituir `su morada` por `su morada (o lugar de trabajo)`.

### Convenciones
- `POR CÉDULA` en mayúsculas.
- Número de búsquedas previas: dominante genérico `[NÚMERO]`; en los originales casi siempre `dos`.
- Derechos siempre al cierre en esta modalidad.

### Esqueleto anonimizado

```
CERTIFICO: Que el día [DÍA SEMANA] [FECHA], a las [HORA] horas,
concurrió el receptor al domicilio señalado en autos, [DOMICILIO
COMPLETO], con el objeto de notificar a [NOMBRE DE LA PARTE],
[RUT], [representada legalmente por [NOMBRE REPRESENTANTE],] de la
[documentos notificados: querella infraccional, demanda civil de
indemnización de perjuicios y sus proveídos], diligencia que realicé
POR CÉDULA, haciendo entrega de copias íntegras a persona adulta habida
en el domicilio, quien se identificó como [NOMBRE QUIEN RECIBE],
quien declaró conocer al querellado y demandado, que este se encuentra
en el lugar del juicio y que aquella es su morada. Se deja constancia
que se practicaron [NÚMERO] búsquedas anteriores, en días y horarios
distintos. Doy fe. En [CIUDAD], a [FECHA EN LETRAS]. Derechos $[MONTO].

                                                                        [NOMBRE RECEPTOR]
                                                                        RECEPTOR AD-HOC
```

---

## 7. Certificado de notificación no lograda (fracasada)

**Plantilla base:** `exhortos_certificados/07_certificado_notificacion_no_lograda.txt`

### Propósito / cuándo se usa
El ministro de fe concurrió pero **NO pudo notificar**. Deja constancia del motivo (no habido, dirección errónea, conserje no ubicó al destinatario, domicilio corresponde a otro, etc.). Este certificado habilita al tribunal a disponer nueva búsqueda, notificación por cédula o archivo.

### Estructura (orden exacto)
1. `CERTIFICO:` + fecha, hora, domicilio.
2. Objeto de la diligencia (citación, querella, demanda y proveídos).
3. Resultado NEGATIVO en mayúsculas: `NO SE PUDO REALIZAR`.
4. Motivo concreto: `ya que [MOTIVO DE LA NO NOTIFICACIÓN]`.
5. `Doy fe.` + cierre lugar/fecha en letras + derechos.
6. Firma RECEPTOR AD-HOC.

### Frases obligatorias textuales
> `CERTIFICO: Que el día [FECHA], a las [HORA] horas, concurrí al domicilio señalado en autos, [DOMICILIO], con el objeto de notificar a [NOMBRE DE LA PARTE] de la citación, querella, demanda y proveídos, diligencia que NO SE PUDO REALIZAR, ya que [MOTIVO DE LA NO NOTIFICACIÓN]. Doy fe. En [CIUDAD], a [FECHA EN LETRAS]. Derechos $[MONTO].`

Motivos usuales vistos en originales: `al entrevistarme con el conserje de nombre [NOMBRE], me informa que el Condominio consta de [N] torres, comunicándose telefónicamente con cada departamento con numeración [N] no dando con el requerido`; `por encontrarse cerrado el inmueble`; `por tratarse de una dirección incorrecta`.

### Convenciones
- Enumerar TODOS los objetos pendientes (citación + querella + demanda + proveídos), porque el certificado sirve para cualquiera de ellos.
- El motivo debe ser específico y verificable, nunca genérico.

### Esqueleto anonimizado

```
CERTIFICO: Que el día [FECHA], a las [HORA] horas, concurrí al
domicilio señalado en autos, [DOMICILIO COMPLETO], con el objeto de
notificar a [NOMBRE DE LA PARTE] de la citación, querella, demanda y
proveídos, diligencia que NO SE PUDO REALIZAR, ya que [MOTIVO ESPECÍFICO:
persona no habida / inmueble cerrado / dirección incorrecta / conserje
no ubicó al requerido]. Doy fe. En [CIUDAD], a [FECHA EN LETRAS].
Derechos $[MONTO].

                                                                        [NOMBRE RECEPTOR]
                                                                        RECEPTOR AD-HOC
```

---

## 8. Devolución de exhorto (oficio al tribunal de origen)

**Plantilla base:** `exhortos_certificados/08_oficio_devolucion_exhorto.txt`

### Propósito / cuándo se usa
Una vez diligenciado el exhorto (notificada la persona o citada), se devuelve al tribunal exhortante por oficio, adjuntando certificados y copias.

### Estructura (orden exacto)
1. `OFICIO N°[NUMERO]` (numeración propia del año en curso).
2. `MAT: LO QUE INFORMA` (a la derecha).
3. `[CIUDAD], [FECHA]` (a la derecha).
4. `DE : JUEZ TITULAR [JUZGADO COMUNICANTE]` (el tribunal que diligenció).
5. `A  : [JUZGADO DE DESTINO]` (tribunal exhortante).
6. Cuerpo único: remisión del exhorto debidamente diligenciado.
7. Despedida: `Saluda atentamente a US.`
8. Firma JUEZ TITULAR + SECRETARIO ABOGADO (S).

### Frases obligatorias textuales
> `Remito a US. Exhorto [TIPO] N°[NUMERO EXHORTO ORIGEN], relacionado con la causa Rol N°[ROL] seguida ante ese tribunal, debidamente diligenciado.`
>
> `Saluda atentamente a US.`

Variante real (documento fuente): `Remito a US Exhorto Oficio N°[NUMERO]/[AÑO], relacionado en la causa Rol [ROL]-[AÑO], seguida ante este tribunal, debidamente diligenciado.` — la referencia al Rol puede ser la del exhortante; mantener coherencia interna.

### Convenciones
- Adjuntar SIEMPRE los certificados de las diligencias practicadas y copia de lo notificado.
- `US.` / `US.` en mayúsculas (uso del tribunal); no usar "usted".

### Esqueleto anonimizado

```
OFICIO N°[NUMERO]
                                                        MAT: LO QUE INFORMA
                                                        [CIUDAD], [FECHA]

DE	: JUEZ TITULAR PRIMER JUZGADO DE POLICÍA LOCAL DE [COMUNA]
A 	: [GRADO] JUZGADO DE POLICÍA LOCAL DE [COMUNA DESTINO]

    Remito a US. Exhorto [TIPO] N°[NUMERO EXHORTO ORIGEN], relacionado
con la causa Rol N°[ROL-AÑO] seguida ante ese tribunal, debidamente
diligenciado.

    Saluda atentamente a US.

                                                                            [NOMBRE JUEZ]
                                                                            JUEZ TITULAR

                                                                            [NOMBRE SECRETARIO/A]
                                                                            SECRETARIO/A ABOGADO (S)
```

---

## 9. Incompetencia por turno (resolución de envío)

**Plantilla base:** `exhortos_certificados/09_resolucion_incompetencia_turno.txt`

### Propósito / cuándo se usa
El tribunal advierte que la materia/fecha del exhorto (o de la denuncia) **no corresponde a su turno de competencia** y remite los antecedentes al juzgado competente. La resolución sirve de nota de envío (no se despacha oficio separado).

### Estructura (orden exacto)
1. Lugar y fecha.
2. Advertencia de incompetence por turno, individualizando el exhorto/denuncia.
3. Orden de envío al juzgado competente.
4. Fórmula de nota de envío: `Sírvanse la presente resolución como atenta nota de envío.`
5. Firma JUEZ TITULAR.
6. Línea de cúmplase: `PROVEYÓ EL JUEZ TITULAR DEL [JUZGADO]. DON [NOMBRE].`
7. Firma SECRETARIO (S).

### Frases obligatorias textuales
> `Advirtiendo el tribunal que la fecha del [TIPO Y NÚMERO DEL EXHORTO], del [JUZGADO ORIGEN], no corresponde al turno de competencia de este tribunal, pasen los antecedentes al señor JUEZ DEL [JUZGADO COMPETENTE], por corresponderle su conocimiento. Sírvanse la presente resolución como atenta nota de envío.`
>
> `PROVEYÓ EL JUEZ TITULAR DEL [JUZGADO]. DON [NOMBRE JUEZ].`

Variante (denuncias internas por turno; documento fuente: *INCOMPETENCIA POR TURNO*):
> `A lo principal, primer, segundo, tercer y cuarto otrosí, advirtiendo el Tribunal que los hechos denunciados ocurrieron con fecha [FECHA], durante el turno del [NÚMERO] JUZGADO DE POLICÍA LOCAL DE [COMUNA], me declaro incompetente para seguir conociendo de ellos, pasen los autos a este Tribunal por corresponderle su conocimiento; al quinto otrosí, como se pide, a través del correo electrónico: [EMAIL TRIBUNAL]. Sirva la presente resolución de atenta nota de envío.`

Esta variante resuelve además los otrosíes pendientes (p. ej. notificación electrónica) y cierra `Sirva la presente resolución de atenta nota de envío.`

### Convenciones
- La firma del secretario va precedida de la línea `PROVEYÓ EL JUEZ TITULAR DEL [JUZGADO]. DON [NOMBRE].` (cúmplase estilo corte).
- En la variante por denuncia, la fórmula es `me declaro incompetente` (primera persona del juez); en la de exhorto, impersonal (`pasen los antecedentes`).

### Esqueleto anonimizado

```
En [CIUDAD], a [DIA] de [MES] de [AÑO].
   Advirtiendo el tribunal que la fecha del [TIPO Y NÚMERO DEL EXHORTO],
del [JUZGADO ORIGEN], no corresponde al turno de competencia de este
tribunal, pasen los antecedentes al señor JUEZ DEL [NÚMERO] JUZGADO DE
POLICÍA LOCAL DE [COMUNA], por corresponderle su conocimiento.
Sírvanse la presente resolución como atenta nota de envío.

                                                                        [NOMBRE JUEZ]
                                                                        JUEZ TITULAR

PROVEYÓ EL JUEZ TITULAR DEL [JUZGADO]. DON [NOMBRE JUEZ].

                                                                        [NOMBRE SECRETARIO]
                                                                        SECRETARIO (S)
```

---

## 10. Escrito de designación de medio electrónico de notificación

**Fuente:** documento fuente del tribunal (*SOLICITA NOTIFICACIÓN ELECTRÓNICA*).

### Propósito / cuándo se usa
Escrito independiente por el que una parte **designa su correo electrónico como
medio de notificación** para todas las resoluciones que en lo sucesivo se dicten
en el proceso. Fundamento: **artículo 18 inciso 4º de la Ley Nº 18.287**
(cualquiera de las partes podrá solicitar para sí una forma de notificación
electrónica; se entiende practicada desde el envío; válida para todas las
resoluciones salvo las del art. 8 inc. 1º y las personales o por cédula del
inc. 2º del propio art. 18). Cuando la solicitud va dentro de otro escrito
(prescripción, reconsideración, descargos), se usa la fórmula `OTROSÍ:
NOTIFICACIÓN ELECTRÓNICA` (ver manual OFICIOS); este formato es el escrito
autónomo.

### Estructura (orden exacto)
1. Título: `SOLICITA NOTIFICACIÓN ELECTRÓNICA`.
2. Tribunal dirigido: `S.J.L. DE POLICÍA LOCAL DE [COMUNA] ([NÚMERO JUZGADO])`.
3. Bloque de identificación: NOMBRE / CÉDULA DE IDENTIDAD / DOMICILIO /
   PROCESO ROL / ACTUARIO.
4. Cuerpo con fundamento legal + designación del correo.
5. Petitorio: `Por tanto, Ruego a S.S., Acceder a lo solicitado.`
6. FIRMA.

### Frases obligatorias textuales
> `En conformidad con lo dispuesto en el artículo 18 inciso 4º de la Ley Nº 18.287, solicito a S.S. tener presente que designo como medio electrónico para las notificaciones que en lo sucesivo se dicten en el proceso, el siguiente electrónico: [CORREO].`

> `Por tanto, Ruego a S.S., Acceder a lo solicitado.`

### Convenciones
- El bloque de identificación es MÁS BREVE que el de los formularios de otros
  manuales: no pide edad ni profesión; incluye PROCESO ROL y ACTUARIO porque el
  escrito se presenta en una causa ya radicada.
- Dirige a `S.S.` (no `SS.` ni `Usía.`), tal como está en el documento fuente.
- La designación rige solo si el tribunal la acepta (el art. 18 inc. 4º exige
  medios idóneos y ausencia de indefensión).

### Esqueleto anonimizado

```
SOLICITA NOTIFICACIÓN ELECTRÓNICA

S.J.L. DE POLICÍA LOCAL DE [COMUNA] ([Nº JUZGADO])

NOMBRE: [NOMBRE COMPLETO]
CÉDULA DE IDENTIDAD: [RUT]
DOMICILIO: [DOMICILIO COMPLETO]
PROCESO ROL: [ROL-AÑO]
ACTUARIO: [APELLIDO ACTUARIO]

	En conformidad con lo dispuesto en el artículo 18 inciso 4º de la
Ley Nº 18.287, solicito a S.S. tener presente que designo como medio
electrónico para las notificaciones que en lo sucesivo se dicten en el
proceso, el siguiente electrónico: [CORREO]

Por tanto,
Ruego a S.S.,

	Acceder a lo solicitado.

FIRMA:
```

---

## 11. Tabla-resumen de frases clave

| Tipo | Fórmula inicial | Fórmula de cierre |
|---|---|---|
| Proveer exhorto (citar declarar/audiencia) | `Por recibido con esta fecha. Ingrésese exhorto...` | `Notifíquese a través del departamento de Inspección Comunal. Ofíciese.` |
| Proveer exhorto (demanda/sentencia) | `Por recibido con esta fecha. Ingrésese exhorto...` | `...los medios que permitan practicar la notificación oportunamente.` |
| Certificado personal | `CERTIFICO: Que el día..., diligencia que realicé Personalmente...` | `Doy fe. En [CIUDAD], a [fecha en letras]. Derechos $[..].` |
| Certificado cédula | `CERTIFICO: Que el día..., diligencia que realicé POR CÉDULA...` | `Se deja constancia que se practicaron [N] búsquedas anteriores... Doy fe.` |
| Certificado fallido | `CERTIFICO: Que el día..., diligencia que NO SE PUDO REALIZAR, ya que...` | Ídem. |
| Devolución de exhorto | `Remito a US. Exhorto... debidamente diligenciado.` | `Saluda atentamente a US.` |
| Incompetencia por turno | `Advirtiendo el tribunal que la fecha del... no corresponde al turno...` | `Sírvanse la presente resolución como atenta nota de envío.` |
| Notificación electrónica (art. 18 inc. 4º L.18.287) | `En conformidad con lo dispuesto en el artículo 18 inciso 4º de la Ley Nº 18.287, solicito a S.S.... designo como medio electrónico...` | `Acceder a lo solicitado.` |
