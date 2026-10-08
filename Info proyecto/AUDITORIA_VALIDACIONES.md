# AUDITORÍA INTEGRAL DE VALIDACIONES — AUTOPASS

**Fecha de auditoría:** 2026-10-05
**Fecha de re-verificación:** 2026-10-08 (los 12 hallazgos siguen vigentes contra el código actual; se actualizaron referencias de archivo:línea)
**Alcance:** Backend (Pydantic, Routers, Servicios), Base de Datos (Modelos, Constraints), y Frontend (Formularios, JS, UX)
**Estado:** Auditoría completada. Identificación de fortalezas, brechas, discrepancias y plan de remediación priorizado.

---

## 1. Resumen Ejecutivo

El sistema **AUTOPASS (v9.34.78+)** cuenta con una sólida arquitectura limpia y mecanismos de validación avanzados en áreas críticas como el cálculo de disponibilidad de reservas por *sweep-line*, normalización unificada de patentes y DNI, autenticación OAuth con state HMAC, y control de accesos físicos ALPR anti-duplicados.

Sin embargo, la auditoría exhaustiva de extremo a extremo reveló **asimetrías y vacíos de validación** distribuidos en 5 capas:
1. **Esquemas Pydantic laxos o ausentes:** Uso de tipos primitivos (`str`, `float`) sin restricciones de rango, longitud ni formato (ej. `email: str` en vez de `EmailStr`, `monto` sin `gt=0`).
2. **Endpoints con parámetros en query/body sin esquema:** Mutaciones críticas (`POST /vehicles`, `POST /settings/prices`, `POST /users/{id}/balance`, etc.) recibiendo tipos primitivos sin validación previa.
3. **Manejo de unicidad y excepciones de BD:** En altas de usuarios, el DNI repetido no se valida preventivamente en el servicio, derivando en un `IntegrityError` que el router transforma en `HTTP 500 Internal Server Error`.
4. **Discrepancias Frontend vs Backend:** El validador JS del frontend acepta patentes de países limítrofes (Brasil, Uruguay, Paraguay) que el validador del backend rechaza taxativamente (solo admite Argentina).
5. **Seguridad en subida de archivos (Uploads):** Falta de control de extensiones y tamaños en la subida de logos de sucursales, y escritura completa a disco antes de medir el tamaño en adjuntos de soporte (riesgo de agotamiento de disco / DoS).

---

## 2. Matriz de Hallazgos y Severidad

| ID | Capa | Componente | Hallazgo / Defecto | Severidad | Impacto |
|---|---|---|---|---|---|
| **V1** | Backend / DB | `UserService.create_user` / `auth.py` | DNI duplicado en registro no se valida antes de insertar; genera `IntegrityError` y respuesta `HTTP 500`. | **Alta** | Mala experiencia de usuario, logs de error falsos. |
| **V2** | Backend / Seguridad | `routes/admin/branches.py` | Subida de logos de sucursal sin validación de extensión permitida ni límite de tamaño. | **Alta** | Riesgo de subida de archivos arbitrarios / DoS de almacenamiento. |
| **V3** | Backend / API | `routes/admin/users.py` (`adjust_user_balance`) | Admite saldos negativos (`monto < 0`) sin validación. | **Alta** | Corrupción contable de saldo de clientes. |
| **V4** | Backend / API | `routes/admin/settings.py` (`update_price`) | Permite tarifas y capacidades negativas o claves arbitrarias en `Settings`. | **Media-Alta** | Tarifas absurdas o aforos negativos en runtime. |
| **V5** | Backend / Schemas | `schemas/user.py` (`PromotionCreate`) | `costo_puntos` no valida `gt=0`; `valor_descuento` no valida rango `1..100%`. | **Media-Alta** | Puntos infinitos al canjear con costo negativo o reservas con costo negativo. |
| **V6** | Front vs Back | `utils.js` vs `user_service.py` | Discrepancia en patentes: frontend admite Mercosur regional (BR/UY/PY), backend solo admite AR. | **Media** | Formularios válidos en UI que rebotan con 400 en el servidor. |
| **V7** | Backend / API | `routes/user/vehicles.py` | `POST /vehicles` no usa Pydantic Schema; parámetros sueltos en query string. | **Media** | Falta de estandarización REST y validación declarativa. |
| **V8** | Backend / Seguridad | `routes/user/support.py` | Se escribe el archivo completo a disco antes de verificar si supera 1 MB. | **Media** | Posible saturación de disco local mediante uploads masivos. |
| **V9** | Backend / API | `availability.py` (`disabled-hours`) | Si `paso_minutos <= 0`, `range()` lanza `ValueError` no atrapado (`HTTP 500`). | **Media** | Caída del endpoint ante query params maliciosos o inválidos. |
| **V10** | Backend / Schemas | `schemas/auth.py`, `schemas/user.py` | `UserBase` y `UserCreate` usan `email: str` en vez de `EmailStr`; DNI sin límite de longitud en `UserCreate`. | **Media** | Registros directos vía API con correos malformados o DNI de 1 dígito. |
| **V11** | Backend / Negocio | `ReservationService.create_admin_reservation` | No valida que `fecha_inicio < fecha_fin` ni chequea solapamiento de la misma patente. | **Media** | Reservas administrativas invertidas o duplicadas para un mismo vehículo. |
| **V12** | Base de Datos | Modelos SQLAlchemy | Ausencia de `CheckConstraint` a nivel esquema SQL (`saldo >= 0`, `capacidad >= 0`, etc.). | **Baja-Media** | Falta de defensa en profundidad en base de datos. |

---

## 3. Análisis Detallado por Componente

### 3.1 Capa de Autenticación y Usuarios (V1, V10)

#### DNI Duplicado en Registro (V1)
- **Ubicación:** `services/user_service.py:28-35` (`create_user`) y `routes/auth.py:44` (`register`).
- **Problema:** `create_user` valida `UserRepository.get_by_email(db, user_data.email)`, pero **no** consulta `UserRepository.get_active_by_dni()`. En la base de datos, `User.dni` posee `unique=True`.
- **Efecto:** Si un usuario intenta registrarse con un DNI existente, SQLAlchemy arroja `IntegrityError`. El bloque `except Exception:` de `routes/auth.py:54` lo enmascara como:
  ```json
  {"status_code": 500, "detail": "Error interno al guardar el usuario."}
  ```
  En cambio, en `oauth_service.py:240` sí se realiza la validación previa correctamente (`HTTP 400: El DNI ya está registrado por otro usuario.`).

#### Validación de Tipos en Schemas de Usuario (V10)
- **Ubicación:** `schemas/user.py:6` (`UserBase`) y `schemas/auth.py:25` (`ForgotPasswordRequest`).
- **Problema:** El campo `email` está tipado como `str` genérico sin `@field_validator` ni `EmailStr`.
  - Frontend sí valida con regex (`/^[^\s@]+@[^\s@]+\.[^\s@]+$/`), pero un cliente API directo puede ingresar `"email": "usuario_sin_arroba"`.
  - En `UserCreate`, `validate_dni` solo exige `v.isdigit()`, omitiendo longitud (admite `"1"` o `"999999999999"`), mientras que `OAuthComplete` sí exige `r'\d{7,8}'`.

---

### 3.2 Capa de Gestión de Flota y Vehículos (V6, V7)

#### Discrepancia de Formato de Patente Frontend vs Backend (V6)
- **Frontend (`static/js/modules/utils.js:302`):**
  - Admite: Argentina clásica (`AAA111`), Argentina Mercosur (`AA111AA`), Brasil Mercosur (`ABC1D23`), Paraguay (`ABCD123`), Uruguay (`ABC1234`), y Moto Argentina (`A123ABC`).
- **Backend (`services/user_service.py:150`):**
  ```python
  p_clean = normalize_plate(patente)
  old_format   = re.match(r'^[A-Z]{3}[0-9]{3}$', p_clean)
  new_format   = re.match(r'^[A-Z]{2}[0-9]{3}[A-Z]{2}$', p_clean)
  moto_format  = re.match(r'^[0-9]{3}[A-Z]{3}$', p_clean) or re.match(r'^[A-Z]{1}[0-9]{3}[A-Z]{3}$', p_clean)
  if not old_format and not new_format and not moto_format:
      raise HTTPException(status_code=400, detail="Formato de patente inválido.")
  ```
- **Conflicto:** El formateador central `core/normalize.py:format_plate` tiene soporte completo para patentes de Brasil, Uruguay y Paraguay, pero `UserService.add_vehicle` las rechaza con error 400.

#### Alta de Vehículos sin Schema Pydantic (V7)
- **Ubicación:** `routes/user/vehicles.py:16` (`add_user_vehicle`).
- **Problema:** La ruta define:
  ```python
  def add_user_vehicle(patente: str, marca_modelo: str, tipo: str = "Auto", ...):
  ```
  En FastAPI, parámetros escalares en un `POST` se interpretan como query params (`/vehicles?patente=...`). Falta un esquema `VehicleCreate(BaseModel)` con normalización automática de patente y validación de tipo (`Auto`, `Moto`, `Camioneta`).

---

### 3.3 Parámetros Financieros, Precios y Saldos (V3, V4, V5)

#### Ajuste de Saldo Administrativo Negativo (V3)
- **Ubicación:** `routes/admin/users.py:137` (`adjust_user_balance`).
- **Problema:**
  ```python
  user.saldo = monto
  db.commit()
  ```
  No se valida que `monto >= 0.0`. Un administrador puede ingresar un saldo negativo por error tipográfico o acción indebida.

#### Actualización de Tarifas y Claves de Configuración (V4)
- **Ubicación:** `routes/admin/settings.py:45` (`update_price`).
- **Problema:**
  - `def update_price(clave: str, valor: float, ...)`: no valida que `valor >= 0`. Permite setear tarifas horarias o capacidades de aforo en números negativos.
  - No existe una lista blanca de claves permitidas; un usuario con rol de administración local puede inyectar claves arbitrarias en la tabla `Settings`.

#### Creación de Promociones de Fidelización (V5)
- **Ubicación:** `schemas/user.py:87` (`PromotionCreate`) y `routes/user/fidelization.py:78` (`redeem_points`).
- **Problema:**
  - `costo_puntos: int`: no exige `gt=0`. Si se crea una promo con costo `-500`, al canjearla la cuenta del cliente hace `saldo_puntos -= (-500)`, incrementando puntos fraudulentamente.
  - `valor_descuento: Optional[int]`: no exige rango `1 <= valor <= 100`. Descuentos superiores a 100% generan montos de reserva negativos.

---

### 3.4 Ciclo de Vida de Reservas (V9, V11)

#### Reservas Administrativas Manuales (V11)
- **Ubicación:** `services/reservation_service.py:458` (`create_admin_reservation`).
- **Comparativa:**
  - En `create_user_reservation` se valida: (1) cuenta no bloqueada, (2) vinculación de patente a la cuenta, (3) no solapamiento de la misma patente en la sede (`get_overlap_by_patente`), (4) anticipación máxima de 3 meses, (5) anticipación mínima por hora, (6) horario de atención de la sede, (7) `end > start`, (8) disponibilidad de cupos sweep-line.
  - En `create_admin_reservation` se valida disponibilidad y vinculación opcional, pero **se omite la validación de `end > start` y el chequeo de solapamiento de la misma patente**.

#### Parámetros en Slots Horarios Deshabilitados (V9)
- **Ubicación:** `routes/user/reservations.py:43` y `services/availability.py:335`.
- **Problema:** `paso_minutos` llega como entero opcional (default 30).
  ```python
  for min_curr in range(0, total_minutos, paso_minutos):
  ```
  Si se invoca con `paso_minutos=0`, Python detona con `ValueError`, devolviendo un 500 no controlado. Tampoco se acota `duracion_horas` (admite valores negativos o extremos).

---

### 3.5 Carga de Archivos y Almacenamiento (V2, V8)

#### Subida de Logos de Sucursales (V2)
- **Ubicación:** `routes/admin/branches.py:159, 249`.
- **Problema:**
  ```python
  if logo_file:
      file_ext = logo_file.filename.split(".")[-1]
      file_name = f"branch_{uuid.uuid4()}.{file_ext}"
      file_path = os.path.join("static", "uploads", "branches", file_name)
      with open(file_path, "wb") as buffer:
          shutil.copyfileobj(logo_file.file, buffer)
  ```
  - **No hay validación de extensiones:** Se acepta cualquier extensión (`.html`, `.svg`, `.exe`, `.js`).
  - **No hay límite de tamaño:** No se limita la cantidad de MB transferidos.

#### Adjuntos en Tickets de Soporte (V8)
- **Ubicación:** `routes/user/support.py:109`.
- **Problema:** Aunque se valida la extensión permitida (`jpg`, `jpeg`, `png`, `gif`, `webp`, `pdf`) y el tamaño máximo (1 MB), la verificación de tamaño se ejecuta **después** de escribir todo el archivo a disco con `shutil.copyfileobj`:
  ```python
  with open(file_path, "wb") as buffer:
      shutil.copyfileobj(adjunto.file, buffer)

  size = os.path.getsize(file_path)
  if size > MAX_FILE_SIZE:
      os.remove(file_path)
      raise HTTPException(status_code=400, detail="El archivo supera el tamaño máximo...")
  ```
  Un archivo de 5 GB se escribirá íntegro en disco antes de ser eliminado, generando picos de I/O y riesgo de saturación de disco.

---

### 3.6 Integridad en Base de Datos (V12)

- **Ubicación:** Modelos SQLAlchemy en `models/`.
- **Estado actual:**
  - Se utilizan claves foráneas e índices de unicidad apropiadamente (`users.dni`, `users.email`, `vehicles.patente`).
  - No existen `CheckConstraint` explícitos. Si un bug de servicio o script directo intenta persistir `User.saldo = -100` o `ParkingAforo.ocupacion_actual = -1`, el motor relacional lo permite sin oposición.

---

## 4. Aspectos Destacados y Fortalezas Actuales

1. **Complejidad de Contraseñas:** `validate_password_strength` en `schemas/validators.py` y `auth.js` garantizan simetría estricta: mínimo 8 caracteres, al menos una mayúscula y un carácter especial.
2. **Prevención de XSS:** Implementación sistemática de `escapeHtml()` en todos los renderizados dinámicos con `innerHTML` en el frontend, y uso de plantillas Jinja2 con autoescape habilitado por defecto.
3. **Flujo de Pagos e Idempotencia:** `services/mercadopago_service.py` valida rigurosamente correspondencia de montos (`abs(monto_mp - pago.monto) <= 0.01`), titularidad, estados de pago previos y no duplicación de cobros.
4. **Protección contra Inyección SQL:** Cero consultas concatenadas en crudo. Todo el acceso a datos está encapsulado en 16 repositorios que utilizan el ORM de SQLAlchemy con parámetros vinculados (*parameter binding*).
5. **Algoritmo Sweep-Line:** La disponibilidad de plazas exclusivas de reserva en `services/availability.py` calcula la concurrencia exacta de solapamientos minuto a minuto, previniendo falsos positivos de ocupación.

---

## 5. Plan de Remediación Propuesto

### Fase 1: Correcciones Críticas de Integridad y Robustez (P0 / P1)
- [ ] **F1.1 (V1):** En `UserService.create_user`, normalizar y validar `UserRepository.get_active_by_dni(db, dni)` antes de insertar, lanzando `HTTP 400: "El DNI ya se encuentra registrado"`. Capturar `IntegrityError` en `routes/auth.py` como red de seguridad.
- [ ] **F1.2 (V2):** En `routes/admin/branches.py`, agregar lista blanca estricta de extensiones para logos (`{'png', 'jpg', 'jpeg', 'webp'}`) y límite de tamaño máximo (ej. 2 MB) leyendo en chunks en memoria antes de persistir.
- [ ] **F1.3 (V3 & V4):** Agregar validación `if monto < 0: raise HTTPException(...)` en `adjust_user_balance`. En `update_price`, validar `valor >= 0` y verificar que `clave` pertenezca a un conjunto permitido.
- [ ] **F1.4 (V5):** En `schemas/user.py`, añadir validadores Pydantic en `PromotionCreate`: `costo_puntos = Field(..., gt=0)` y `valor_descuento = Field(None, ge=1, le=100)`.

### Fase 2: Simetría y Estandarización de Entrada (P2)
- [ ] **F2.1 (V6):** Alinear `UserService.add_vehicle` con `core/normalize.py` para admitir patentes Mercosur de Brasil, Uruguay y Paraguay, igualando las capacidades del frontend.
- [ ] **F2.2 (V7):** Crear `VehicleCreate(BaseModel)` en `schemas/parking.py` o `schemas/user.py` y actualizar `POST /v1/user/vehicles` para recibir cuerpo JSON en vez de query params.
- [ ] **F2.3 (V8):** En `reply_to_support_ticket`, leer el stream en bloques de 64 KB y abortar inmediatamente si el acumulador supera 1 MB, evitando escribir archivos gigantescos a disco.
- [ ] **F2.4 (V9):** En `routes/user/reservations.py`, restringir query parameters en `disabled-hours`: `paso_minutos = Query(30, ge=5, le=120)` y `duracion_horas = Query(1.0, gt=0, le=24)`.
- [ ] **F2.5 (V10):** Migrar campos de email en schemas a `EmailStr` o agregar `@field_validator` de correo; incorporar validación de longitud 7 u 8 dígitos en `UserCreate.validate_dni`.
- [ ] **F2.6 (V11):** En `ReservationService.create_admin_reservation`, incorporar chequeo de `start < end` y verificación de solapamiento de la misma patente en la sede.

### Fase 3: Defensa en Profundidad (P3)
- [ ] **F3.1 (V12):** Evaluar migración Alembic para incorporar `CheckConstraint("saldo >= 0", name="ck_users_saldo_non_negative")` y `CheckConstraint("capacidad_total >= 0")` en `parking_aforo`.