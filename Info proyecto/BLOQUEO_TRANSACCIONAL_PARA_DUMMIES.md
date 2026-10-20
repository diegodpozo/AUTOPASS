# EL BLOQUEO TRANSACCIONAL EXPLICADO PARA DUMMIES

**Fecha:** 20/10/2026
**Para quién es esto:** para alguien que entiende poco o nada de bases de datos y quiere saber
qué problema había, cómo se resolvió y por qué se hizo así. Se lee de corrido, sin código.
**Qué documenta:** las 6 fases del plan de `Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md`, ya
implementadas y verificadas. Ese informe es el técnico; **este es el de la explicación llana**.

---

## 1. El problema, contado sin tecnicismos

Imaginá dos personas atendiendo el mismo mostrador, y **un solo cartel de "quedan 2 lugares"**.
Las dos leen el cartel, las dos piensan "hay lugar", y las dos anotan su reserva. Resultado:
**3 reservas para 2 lugares**. Ninguna de las dos hizo nada mal a propósito: simplemente las dos
miraron el mismo cartel en el mismo instante.

Eso es exactamente lo que hacía el sistema. Todo el código de reservas, pagos y saldo tenía esta
forma:

1. **Leer** el estado ("¿hay lugar?", "¿te alcanza el saldo?", "¿ya está pagada?").
2. **Decidir** con lo que leyó.
3. **Escribir** el resultado.

Entre el paso 1 y el paso 3 hay una **ventana de tiempo**. Si otro pedido entra en esa ventana,
los dos leyeron lo mismo y los dos escriben como si el otro no existiera. A esto se lo llama
**"check-then-act"** (chequear y después actuar) y es la raíz de todos los bugs que arreglamos.

### Los 5 agujeros que había
| # | Qué podía pasar | Traducido |
|---|---|---|
| **R1** | Se vendían más plazas de las que había (contra el cupo de reservas) | El cartel de "quedan 2" |
| **R2** | El mismo auto quedaba con dos reservas superpuestas | Doble reserva del mismo vehículo |
| **R3** | El saldo o los puntos se gastaban dos veces | Te cobran una vez y te descuentan dos |
| **R4** | El selector de horarios mostraba lugares ya ocupados | Reservás algo que ya no está |
| **R5** | El mismo pago de Mercado Pago se acreditaba dos veces | MP reintenta el aviso y te pagan doble |

Ninguno de estos se ve probando de a una persona. Todos aparecen **cuando hay dos a la vez**, que
es justamente el estado normal de un sistema en uso.

---

## 2. La idea central: la "sección crítica"

Para arreglar esto no alcanza con "chequear dos veces": hay que lograr que **entre el chequeo y la
escritura no se meta nadie**.

La analogía es el **baño con pestillo**:
- Si está libre, entrás y **ponés el pestillo**.
- Mientras el pestillo está puesto, los demás esperan afuera.
- Cuando salís, sacás el pestillo y el siguiente entra.

Eso es una **sección crítica**: un tramo de trabajo que solo puede estar haciendo **una persona a
la vez**. En el sistema, el "pestillo" se llama **bloqueo transaccional** (`bloqueo_transaccional`)
y vive en un solo archivo: `core/db_lock.py`.

### Las 3 reglas que hacen que el pestillo sea confiable

1. **Se abre antes de decidir y se cierra al confirmar.** El pestillo no cubre solo la escritura:
   cubre **desde la primera lectura de decisión hasta el commit**. Si lo pusiéramos justo antes de
   escribir, la ventana seguiría abierta entre leer y escribir, que es donde está el bug.

2. **Las llaves se piden siempre en orden alfabético.** Si dos secciones críticas necesitan las
   mismas llaves pero las piden en orden distinto, cada una se queda con una y espera la otra —
   para siempre. Eso es un **abrazo mortal (deadlock)**. Pidiéndolas siempre ordenadas, eso no
   puede pasar.

3. **Se suelta solo, y solo al final.** El pestillo se libera automáticamente cuando la operación
   termina bien (**commit**) o cuando falla y se deshace (**rollback**). No hay que acordarse de
   sacarlo, y no se puede sacar antes a propósito.

### Qué llave se usa en cada caso
No alcanza con un pestillo para todo: hay que poner el pestillo **en la puerta correcta**. Si
bloquearas todo el sistema, no podrían reservar dos personas en **sucursales distintas** al mismo
tiempo, y no hace falta. Por eso hay "llaves" hechas a medida:

| Llave | Protege | Analogía |
|---|---|---|
| `clave_aforo(sede, tipo)` | El cupo de plazas de una sede para un tipo de vehículo | El pestillo del **cartel de cupos** de esa sede |
| `clave_patente(patente, sede)` | Que un auto no quede con dos reservas superpuestas en la misma sede | El pestillo de **ese auto** en **esa sede** |
| `clave_usuario(id)` | El límite de reservas por cuenta y el saldo/puntos de esa persona | El pestillo de **esa cuenta** |
| `clave_reserva(id)` | El cambio de estado de una reserva puntual (pagar, cancelar, vencer) | El pestillo de **esa reserva** |

Dos reservas en sedes distintas usan llaves distintas: no se estorban. Dos intentos de reservar el
mismo auto en la misma sede usan la misma llave: van uno después del otro.

### Cuando el que espera se cansa
Si alguien espera el pestillo demasiado (más de `LOCK_TIMEOUT_SECONDS`), no se queda colgado
eternamente: el sistema le responde **"409, reintentá"**. Es la diferencia entre "esperá un rato y
probá de nuevo" y "el sistema se quedó congelado".

---

## 3. Un detalle importante: ¿por qué no siempre funciona igual?

Hay dos motores de base de datos en juego, y **no se comportan igual**. Esto no es un capricho:
es una realidad técnica que hay que tener en cuenta (y está documentada en el código).

| | **PostgreSQL** (producción, Neon) | **SQLite** (las pruebas y el desarrollo) |
|---|---|---|
| ¿Tiene pestillo de verdad? | **Sí**, y funciona bien | **No**: no existe la función de bloqueo |
| ¿Qué pasa en las pruebas? | Se prueba de verdad, con dos a la vez | El pestillo es un **"no-op"**: se ignora, sin error |
| ¿Se nota? | No, todo funciona | Las pruebas de a una pasan igual; las de "dos a la vez" **no probarían nada** |

**Consecuencia práctica:** los tests que de verdad comprueban que el pestillo funciona **solo
tienen sentido en PostgreSQL**. Por eso están marcados aparte (grupo `postgres`), no corren en la
corrida normal, y en el CI (integración continua) corren contra un PostgreSQL de verdad que se
levanta para eso. Es la diferencia entre "probé que mi alarma suena" y "probé que mi alarma suena
**cuando hay humo**".

---

## 4. Las 6 fases, una por una

El plan se hizo en 6 etapas, en un orden pensado: primero lo más barato y más delicado (el dinero),
después el núcleo, y al final las redes de seguridad y el cierre.

### Fase 1 — Que la plata no se toque dos veces (aritmética atómica)
**El problema:** para descontar saldo, el código hacía "¿tiene suficiente? sí... entonces
descuento". Entre el "tiene" y el "descuento" alguien podía gastar lo mismo.
**La solución:** el chequeo y el descuento se hacen **en una sola instrucción** para la base de
datos. Es como un cajero automático: no te dice "tenés saldo" y después te lo da; hace las dos
cosas **en el mismo movimiento**. Si no alcanzaba, la instrucción simplemente **no cambia nada** y
avisa "no alcanzaba".
**Dónde vive:** `repositories/user_repository.py`, con 6 operaciones (`sumar_saldo`,
`descontar_saldo`, `fijar_saldo`, `sumar_puntos`, `canjear_puntos`, `descontar_puntos_tope_cero`).

### Fase 2 — El núcleo: el helper de bloqueo
**El problema:** el bloqueo tiene que estar en **muchos lugares** (crear reserva, modificar, pagar,
cancelar, las tareas de fondo). Si cada uno lo inventa, tarde o temprano uno lo hace mal.
**La solución:** **un solo archivo** (`core/db_lock.py`) con el helper y las llaves. Todos usan
lo mismo. Se aplicó en las operaciones donde antes había carreras: crear y modificar reservas,
pagar, cancelar, confirmar pagos de Mercado Pago y las tareas automáticas de fondo (hoy son
**10 puntos de entrada** en los servicios).
**Esta es la fase más importante**, porque es la que crea la herramienta que las demás usan.

### Fase 3 — Que el calendario no mienta (invalidación del caché)
**El problema:** para que el selector de horarios no recalculte todo cada vez, el sistema
**guarda el resultado 30 segundos** ("caché"). Pero si justo reservás en ese ratito, el calendario
te sigue mostrando el horario ocupado como libre hasta que se vence ese plazo. Lo mismo al revés:
liberás un lugar y lo sigue mostrando ocupado.
**La solución:** después de cada reserva/modificación/cancelación, se **borra el caché de esa
sede** para que el próximo que mire vea la verdad.
**Ojo con el "después":** hay que borrarlo **después** de confirmar la operación, no antes. Antes
no sirve, porque si la operación luego falla y se deshace, habrías borrado el caché al pedo y
podría quedar recargado con datos viejos. Y hay un límite honesto: este caché vive **dentro de
cada programa**; si algún día se corren varios a la vez, habría que mudarlo a un lugar compartido.

### Fase 4 — La red de seguridad del motor (constraint de no-solape)
**El problema:** el pestillo (Fase 2) protege **siempre que se pase por el código**. Pero si
alguien carga una reserva por un script, por una carga de datos o escribiendo directo en la base,
el pestillo no lo ve.
**La solución:** una **regla dentro de la base de datos misma** que rechaza de plano dos reservas
vigentes del mismo auto superpuestas en la misma sede. La base se convierte en la última línea de
defensa: si algo intenta romper la regla, **la base rebota el pedido** aunque el código se haya
salteado.
**Tres detalles finos que hubo que resolver** (y que la versión inicial del plan tenía mal):
1. Se compara el auto **normalizado** (mayúsculas, sin espacios), para que `AB 123 CD` y
   `ab123cd` se reconozcan como el mismo.
2. Se usa el **identificador de la sede**, no su nombre (el nombre no es un dato directo de la
   reserva).
3. Los estados se escriben **exactamente como los usa el sistema**. La versión inicial usaba
   mayúsculas de más; con eso la regla **no habría protegido nada** — habría dado la falsa
   sensación de estar protegido, que es peor que no tenerla.
**Alcance:** funciona **solo en PostgreSQL**. En SQLite no existe; ahí la única defensa sigue
siendo el pestillo del código (ver sección 3).

### Fase 5 — Que un pago repetido no cobre dos veces (idempotencia)
**El problema:** Mercado Pago **reintenta** los avisos de pago. Si llega el mismo aviso dos veces,
el sistema podía cobrar/acreditar puntos **dos veces**.
**La solución:** cada pago de MP tiene un **número de identificación único**, y la base no admite
**dos pagos con el mismo número**. El segundo intento choca contra esa regla y el sistema responde
**"409, ya estaba aplicado"** en vez de volver a acreditar.
**Un detalle clave:** los pagos que todavía **no** tienen número de MP se guardan como "vacío"
especial (**NULL**), y muchos "vacíos" **sí** pueden convivir (a diferencia de poner comillas
vacías, que chocarían entre sí). Así los pagos pendientes no se estorban entre ellos.
**Es el mismo concepto que un número de ticket:** no podés usar dos veces el mismo.

### Fase 6 — Cierre: que esto no vuelva a romperse
**El problema:** arreglar el código no alcanza si dentro de 6 meses alguien escribe una función
nueva con el viejo patrón "leer → decidir → escribir".
**La solución, en dos partes:**
1. **Documentado y con mandato:** las reglas del pestillo quedaron escritas en la guía de
   desarrollo, con una regla de oro simple: *toda escritura que dependa de una lectura previa debe
   abrir una sección crítica*. Y quedó como **obligación arquitectónica** para el futuro.
2. **Las pruebas de verdad ahora corren solas:** el CI levanta un PostgreSQL y corre ahí los tests
   de concurrencia. Antes **no corrían**: parecía que estaban, pero el CI no tenía PostgreSQL, así
   que se saltaban en silencio. Y para que no vuelva a pasar, si el PostgreSQL del CI no responde,
   ahora el CI **falla** en vez de dar verde con todo salteado (un verde que no probó nada es peor
   que un rojo honesto).

---

## 5. Cómo saber que no está roto: las pruebas

Cada fase se probó **primero rompiendo** (reproduciendo el bug: "rojo") y **después arreglando**
("verde"). Ese ida y vuelta es lo que demuestra que la prueba sirve: si la prueba pasa **antes** de
arreglar, entonces no estaba probando el bug.

| Qué se prueba | Cuántos | Dónde | ¿Corre en la corrida normal? |
|---|---|---|---|
| Saldo y puntos (Fase 1) | 3 + 10 | `test_concurrencia_saldo_puntos.py`, `test_user_repository_atomic.py` | Sí |
| Caché de disponibilidad (Fase 3) | 5 + 3 | `test_concurrencia_cache_disponibilidad.py`, `test_concurrencia_cache_flujos.py` | Sí |
| Pagos repetidos (Fase 5) | 6 | `test_concurrencia_idempotencia_pagos.py` | Sí |
| Pestillo real en PostgreSQL (Fases 2 y 4) | 15 | `test_concurrencia_reservas.py`, `test_concurrencia_constraints_postgres.py` | **No**: grupo `postgres` |

**Los números de hoy:** la corrida normal tiene **941 pruebas** (todas pasan) y quedan **15
aparte** que son las que necesitan PostgreSQL de verdad. En total, **956 pruebas en 72 archivos**.
Además, 11 verificadores automáticos (llamados "guards") que cuidan el estilo y la coherencia del
frontend están todos en verde.

### Por qué los de PostgreSQL van aparte
Porque necesitan **una base de verdad y conexión** (en el taller no siempre hay internet), y
tardan ~40 segundos más. Por eso, por defecto se saltean y se corren a propósito. **Saltear no es
fallar**: quiere decir "esto no aplica acá". Y en el CI, donde sí hay PostgreSQL, corren de verdad
y **no se permite** que se salteen.

---

## 6. Preguntas frecuentes (las que te van a hacer)

**"¿Esto hace el sistema más lento?"**
No en la práctica. El pestillo solo frena a quien compite **por el mismo recurso exacto** (el
mismo auto, la misma cuenta, el mismo cupo de esa sede). Dos reservas en sedes distintas no se
esperan. Y hay un tope de espera, así que nadie queda colgado.

**"¿Qué pasa si dos reservan el mismo auto en el mismo segundo?"**
Uno entra, el otro espera el pestillo; cuando el primero termina, el segundo ve el estado **ya
actualizado** y recibe un mensaje claro ("ese auto ya tiene reserva en ese horario") en vez de
duplicar.

**"¿Y si la base de datos se cae?"**
La operación falla y **se deshace sola** (rollback), y el pestillo se libera. No queda nada a
medias.

**"¿Por qué hay una regla en la base Y un pestillo en el código? ¿No es doble trabajo?"**
Son dos capas con propósitos distintos, como el cinturón y el airbag: el pestillo evita el choque
en el uso normal; la regla de la base (Fase 4) limita el daño si algo entra por un camino que el
pestillo no cubre. La regla de la base **no reemplaza** al pestillo.

**"Detecté que no cubre X, ¿está mal?"**
Puede ser. Antes de agregar un pestillo nuevo, revisá si ya existe una llave que sirva (sección 2)
y **reutilizala**. Si inventás una llave nueva, avisá y documentalo: las llaves son un contrato
entre todas las partes del sistema.

**"¿Alcanza con leer el código para confiar?"**
No. La prueba de fuego es **correr los tests del grupo `postgres` contra una base real**. En este
proyecto eso ya está automatizado en el CI, así que no depende de que alguien se acuerde.

---

## 7. Dónde mirar cada cosa

| Quiero ver... | Andá a... |
|---|---|
| El plan técnico completo (por fases, con SQL y decisiones) | `Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md` |
| El pestillo y las llaves | `core/db_lock.py` |
| Las operaciones atómicas de plata y puntos | `repositories/user_repository.py` |
| El borrado del caché de horarios | `services/availability.py` (`invalidar_cache_disponibilidad`) |
| La regla de no-solape en la base | migración `alembic/versions/b1c2d3e4f5a6_*.py` |
| La regla de pago único | migración `alembic/versions/e5f6a7b8c9d0_*.py` |
| Las reglas para programar de acá en adelante | `Info proyecto/GUIA_DESARROLLO.md` (sección "Convenciones de Concurrencia") |
| El estado de la última sesión de trabajo | `PENDIENTES_PROXIMA_SESION.md` |

---

## 8. En una frase

Antes, el sistema **miraba y después actuaba**, y en el medio se le colaban las otras personas.
Ahora, para las decisiones delicadas (plata, cupos, pagos, estados), **pone un pestillo, mira y
actúa sin que nadie se meta en el medio**, con reglas en la base de datos como red de seguridad
por si algo entra por otro lado. Con eso, dos personas usando el sistema al mismo tiempo ya no
pueden romperlo.
