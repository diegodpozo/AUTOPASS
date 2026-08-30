# Cambios en el Backlog — 2026-08-30

Revisión del backlog contra el estado real del código en AUTOPASS. Se detectó que **27 ítems** estaban implementados pero figuraban como `PENDIENTE` o `EN CURSO`, y se marcaron como `CERRADA`.

## Alcance

- **Repositorio:** https://github.com/MarianoJAC/backlogAUTOPASS.git
- **Archivos actualizados:** `index.html` y `backlog_editable.html` (ambos con el mismo `DATA`)
- **Commits:**
  - `4ed897a` — marcar 27 ítems como CERRADA (filtro localidad, OCR, core API/JWT, flujo vehículos)
  - `0491732` — fix que restauró los HTML completos (una versión previa quedó truncada a solo el array `DATA`)
  - `7f048ca` — 2.ª ronda: app móvil a PENDIENTE y T130 con OCR actualizado
- **Rating final:** `CERRADA` 194 → **221**, `PENDIENTE` 34 → **21**, `EN CURSO` 26 → **12**
- **Campos tocados:** solo `estado`, `ffin`, `desc` y `obs` — ningún otro dato se modificó

## Ítems marcados CERRADA (27)

### Historias de usuario — filtrar por localidad (web)
Ya implementado en el buscador con autocompletado de `static/js/modules/landing-map.js`.

| ID | Descripción | ffin |
|----|-------------|------|
| H2 | Filtrar estacionamientos por localidad | 30/08/26 |
| T5 | Seleccionar localidad desde menú/buscador | 30/08/26 |
| T6 | Consultar estacionamientos de esa localidad en BD | 30/08/26 |
| T7 | Mostrar solo esos puntos en el mapa | 30/08/26 |
| T8 | Cambiar localidad y refrescar resultados | 30/08/26 |

### Historias de usuario — tiempo real y alertas
- **T15** — consultar disponibilidad en tiempo real (dots de estado + WebSocket de aforo) → `CERRADA` (30/08/26)
- **T52** — mostrar alertas en la app (toasts y centro de notificaciones) → `CERRADA` (30/08/26)

### Funcionalidades core del sistema

**Arquitectura de datos (grupo F01, ffin 05/06/26):**
- **T168** — Diseñar el modelo relacional en SQLAlchemy → `CERRADA`
- **T169** — Inyección de dependencias para sesiones BD → `CERRADA`
- **T170** — Sistema de migraciones y parches → `CERRADA`

**Motor de reconocimiento (grupo F02, ffin 22/04/26):**
- **T171** — Integración de OCR (RapidOCR/PaddleOCR, se descartó EasyOCR) con procesamiento asíncrono → `CERRADA` — *desc y obs actualizadas*
- **T172** — Algoritmo de consenso de patentes para validación → `CERRADA`
- **T173** — Pre-procesamiento de imágenes con OpenCV → `CERRADA`

**Servicios financieros (grupo F03, ffin 05/06/26):**
- **T174** — Lógica centralizada para cálculo de deudas por estadía → `CERRADA`
- **T174b** — Sistema de gamificación: generación automática de puntos → `CERRADA`
- **T175** — Tarifas dinámicas gestionadas desde DB (trimodales) → `CERRADA`

**Comunicación y control de hardware (grupo F04, ffin 22/04/26):**
- **T175b** — Protocolo MQTT para telemetría → `CERRADA`
- **T175c** — Comandos remotos (OPEN/CLOSE) vía MQTT → `CERRADA`
- **T175d** — Logs de eventos de hardware para auditoría → `CERRADA`

**Núcleo de la API y seguridad (grupo F05, ffin 30/08/26):**
- **F05** — Núcleo de la API y seguridad → `CERRADA`
- **T176** — Ruteo modular con FastAPI → `CERRADA`
- **T177** — Esquemas de validación Pydantic → `CERRADA`
- **T177b** — Sistema de autenticación y autorización JWT → `CERRADA`

**Gestión de flujo de vehículos (grupo F06, ffin 30/08/26):**
- **F06** — Gestión de flujo de vehículos (control de aforo y lógica de accesos) → `CERRADA`
- **T178** — Vinculación automática Patente-Vehículo-Usuario → `CERRADA`
- **T179** — Control de aforo en tiempo real con contadores globales → `CERRADA`
- **T179b** — Validación de estados para evitar errores de registro → `CERRADA`

## 2.ª ronda — ítems corregidos (11)

Revisión adicional contra el código: se detectaron referencias a tecnologías que el proyecto ya no usa y una feature que nunca arrancó. Commit `7f048ca`.

**OCR / ALPR**
- **T130** — "Integrar alpr con python (opencv/**easyocr**)" → desc actualizada a `opencv/RapidOCR-PaddleOCR`. El motor real es RapidOCR/PaddleOCR; EasyOCR quedó descartado.

**App móvil sin código real**
- **H43, H44, H45, H46, H48 y T136, T137, T138, T139, T141** (Expo/React Native) → `EN CURSO` → `PENDIENTE`. No existe app móvil en el repositorio; todo el alcance móvil sigue sin arrancar.

**A aplicar en el futuro**
- **T72** — "Exportar reporte en **PDF**/Excel" → queda intacta de momento: el backend no genera PDF (solo CSV/Excel; PDF vía impresión del navegador). La corrección se aplicará luego.

## Ítems que SEGUEN pendientes (no se tocaron)

- **Pasarela de pago real:** T20, T35 (redirigir a pago), T75 (configurar Mercado Pago/tarjetas) — hoy solo existe saldo virtual AUTOPASS.
- **Bloqueo de espacios:** H58, T123, T124.
- **Alertas de incidentes:** H21, T81-T84 (fallos de sensores/barreras, registrar incidentes, marcar como resuelto).
- **App móvil:** H43-H46, H48 y T136-T139, T141 (Expo/React Native — no hay código en el repo).
- **Hardware:** H51/T144 (LCD I2C) y H52/T145 (anti-colisión).
- **Calidad:** H54/T147 (pruebas de carga/estrés).
- **Documentación y entrevistas:** H56 (T149, T150), H57 (T151, T152).

## Nota operativa

El sitio en vivo `https://marianojac.github.io/backlogAUTOPASS/` lee los datos de **Firebase Realtime Database** (`backlog/rows`), no del `DATA` estático de los HTML. Este documento y los HTML actualizados quedan como fuente/seed; para ver los cambios en la página hay que replicarlos en la RTDB o desde la interfaz web del backlog.

## Sincronización con el backlog EN VIVO (Firebase RTDB)

- Se confirmó que la base **en vivo (Firebase)** estaba adelantada respecto al HTML del repo: tenía **20 ítems nuevos** que no existían en el `DATA` (`F07`, `H72`, `H73`, `T196`-`T212`, infraestructura/Neon y OCR) con estados y fechas cargados por el equipo.
- **Corrección en vivo:** `H2`, `T5`, `T6`, `T7`, `T8`, `T15` pasaron de `PENDIENTE` → `CERRADA` (ffin 30/08/26) directamente en Firebase RTDB (PATCH a `backlog/rows/{6,7,8,9,10,19}`), respetando el resto de los ítems.
- **Corrección en vivo (núcleo API):** `F05`, `T176`, `T177`, `T177b` (ruteo modular FastAPI, esquemas Pydantic, JWT) pasaron de `PENDIENTE` → `CERRADA` en Firebase (PATCH a índices `227/228/229/230`); ya están implementados en el código (`routes/*` + `__init__.py`, `core/security.py`).
- **Sync repo ← vivo:** se descargó el array completo de Firebase (285 ítems: 11 secciones + 274 filas) y se embebió como nuevo `DATA` en el `index.html` del repo `backlogAUTOPASS` y en `Info proyecto/backlog_editable.html` del repo `AUTOPASS`. Quedan así alineados en ambos lados.
- **Incidente de sync:** una primera versión del script envolvió el JSON (que ya va entre `[ ]`) con corchetes extra, dejando `const DATA = [[...]];` en los HTML del repo (commits `54fff03`/`f2fccc8`). Corrección: dump sin volver a envolver → `const DATA = [{...}];`. Verificado: 285 ítems planos, sin corchetes dobles.
- **Lección:** el tablero se edita en vivo (Firebase); los HTML del repo quedan como seed/respaldo. Cuando haya ediciones nuevas en la web, repetir este flujo (GET de `backlog/rows.json` → reemplazar `DATA` → commit) **sin agregar corchetes extra**: el dump ya es un array.