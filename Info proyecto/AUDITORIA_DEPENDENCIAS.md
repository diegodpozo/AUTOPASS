# Auditoría de Dependencias y Supply Chain — AUTOPASS

> **Fecha:** 2026-09-19 (revisión contra código v9.23.0, rama `main`, Python 3.14.7 en Windows)
> **Alcance:** `requirements.txt` (64 líneas, ~42 deps directas), entorno virtual instalado (`venv/`) y cadena de dependencias transitivas (pip-audit). No se audita lógica de negocio ni sea de código (es A1/A7).
> **Metodología:** `pip-audit` sobre `requirements.txt` y sobre el venv completo (`--format=json`), `pip check` para dependencias rotas, consulta de los advisories en la API de OSV (rangos afectados, CVSS, fixes), y revisión manual del uso real de cada paquete vulnerado en el código (`routes/`, `core/`, `services/`).
> **Herramientas:** `pip-audit`, `pip check`, `pip list --format=freeze`, OSV API (`api.osv.dev/v1/vulns/{id}`), PyPI JSON API.

---

## 1. Resumen Ejecutivo

**8 paquetes con CVEs conocidos** (3 directos + 5 transitivos). La mayoría son **parcheables con bump menor** sin riesgo de breaking. Dos casos requieren decisión:

- **starlette** (mayor impacto, 5 CVEs): todos los fixes exigen **saltar de 0.52.x a 1.x** (salto mayor, `BadHost`/DoS). Dado que FastAPI y slowapi **no pinnean tope superior de starlette**, el bump es viable pero debe validarse con la suite completa (152 tests).
- **ecdsa**: **SIN FIX** (CVE-2024-23342, ataque de timing Minerva). Es dependencia transitoria de `python-jose` y **el proyecto solo usa HS256**, nunca ES256/ECDSA — vector no explotable en la configuración actual.

**7 de 8 hallazgos tienen fix disponible**; 5 se resuelven con bumps menores/patch (`python-multipart`, `cryptography`, `idna`, `requests`, `click`), y 2 requieren coordinación mayor (`starlette`, con su pin en `requirements.txt:8`).

> **Estado al cierre (2026-09-19): P1+P2 aplicadas y verificadas** — re-instalación completa, `pip check` limpio, **152 tests passed**, smoke real de servidor + login + WebSocket + arranque `import main` OK. `pip-audit` final sobre el venv: **queda 1 sola vuln (`ecdsa`, sin fix upstream, no explotable por uso HS256)**. Las 9 restantes se resolvieron: 5 de `starlette` vía bump mayor 0.52.1→1.6.0, 4 de `cryptography` vía 46.0.7→50.0.1. numpy alineado en 2.4.6.

| Paquete | Versión | CVEs | Sev. máx. | Fix disponible | Comentario |
|---|---|---|---|---|---|
| starlette | ~~0.52.1~~ **1.6.0** | ~~5~~ **0** | ~~Alta (7.5)~~ | ✔ | **P2 aplicado** (bump mayor con fastapi) |
| python-multipart | ~~0.0.22~~ **0.0.31** | ~~5~~ **0** | ~~Alta (7.5)~~ | ✔ | **P1 aplicado** |
| cryptography | ~~46.0.5~~ **50.0.1** | ~~6~~ **0** | ~~**Crítica (9.8)**~~ | ✔ | **P1+P2 aplicados** |
| ecdsa | 0.19.2 | 1 | Alta (7.4) | **SIN FIX** | Transitoria de python-jose, no usada (solo HS256) |
| idna | ~~3.11~~ **3.15** | ~~1~~ **0** | ~~Baja~~ | ✔ | **P1 aplicado** |
| requests | ~~2.32.5~~ **2.33.0** | ~~1~~ **0** | ~~Media~~ | ✔ | **P1 aplicado** |
| click | ~~8.3.1~~ **8.3.3** | ~~1~~ **0** | ~~Media~~ | ✔ | **P1 aplicado** |

**Nivel de riesgo general: MEDIO-ALTO** — 1 CVE crítico (`cryptography 46.0.5` → 9.8, fijado en 46.0.6/46.0.7 casi sin costo) y 5 altos en `starlette`, pero ninguno se explota por la superficie actual del proyecto (solo HS256, sin headers Host maliciosos obvios). `pip check` limpio (0 deps rotas). Se detectó además **1 inconsistencia requirements↔venv** (numpy).

---

## 2. Hallazgos por paquete

### A2.1 — starlette 0.52.1 — **[ALTO]**

Pin: `requirements.txt:8`. Última con CVEs activos; **todos** exigen pasar a la rama 1.x.

| Advisory | CVE | Tipo | CVSS | Fix |
|---|---|---|---|---|
| PYSEC-2026-161 | CVE-2026-48710 | `BadHost`: falta validación de header `Host` → envenena `request.url.path`, bypasea checks path-based | — | 1.0.1 |
| PYSEC-2026-2281 | CVE-2026-48818 | Fuga de información (C:H) | 7.5 | 1.1.0 |
| PYSEC-2026-2280 | CVE-2026-48817 | Integridad (I:L) | 5.3 | 1.1.0 |
| PYSEC-2026-249 | CVE-2026-54283 | DoS (A:H) | 7.5 | 1.3.1 |
| PYSEC-2026-248 | CVE-2026-54282 | Integridad (I:L) | 5.3 | 1.3.0 |

**Riesgo:** el más relevante es el `BadHost` (bypasea middleware de seguridad por ruta) y los DoS. En esta app, el routing se valida con middleware también a nivel de ruta real, por lo que el impacto práctico es parcial, pero la solidez del pin es baja.

**Verificación de compatibilidad:**
- `fastapi` 0.135.1 requiere `starlette>=0.46.0` **sin tope superior** → acepta 1.x.
- `slowapi` 0.1.9/0.1.10 no declara dependencia de starlette → sin conflicto.
- Se recomienda subir **en conjunto**: `starlette==1.3.x` + `fastapi` al mínimo compatible (0.141.1 disponible) + `slowapi==0.1.10`, y ejecutar `pytest tests` completo + smoke de arranque.

**Recomendación:** bump mayor coordinado (P2), con validación de la suite.

---

### A2.2 — python-multipart 0.0.22 — **[ALTO]**

Pin: `requirements.txt:9`. 5 advisories de DoS y parsing:

| Advisory | CVE | Tipo | CVSS | Fix |
|---|---|---|---|---|
| PYSEC-2026-3036 | CVE-2026-53539 | DoS cuadrático parsing de querystring (semicolons) | 7.5 | 0.0.30 |
| PYSEC-2026-3037 | CVE-2026-53538 | Semicolon como separador → envenenamiento de parámetros (I:L) | 5.9 | 0.0.30 |
| PYSEC-2026-3038 | CVE-2026-40347 | DoS vía preamble/extensiones multipart grandes | 5.3 | 0.0.26 |
| PYSEC-2026-3039 | CVE-2026-42561 | DoS por headers de parte unbounded | 7.5 | 0.0.27 |
| PYSEC-2026-3040 | CVE-2026-53540 | `Content-Length` negativa bufferiza todo el body | — | 0.0.31 |

**Riesgo:** la app usa `python-multipart` para subida de logos/imágenes en endpoints de admin (multipart/form-data). DoS remotos sin autenticación posible en esos endpoints.

**Recomendación:** bump a `0.0.31` (cubre todos). Bump menor, sin breaking conocido.

---

### A2.3 — cryptography 46.0.5 — **[CRITICO]**

Pin: `requirements.txt:24`. Dependencia declarada — el proyecto NO la importa directo; la arrastra `python-jose`. 6 advisories, 1 crítico:

| Advisory | CVE | Tipo | CVSS | Fix |
|---|---|---|---|---|
| PYSEC-2026-36 | CVE-2026-39892 | **RCE/compromiso completo (C:H/I:H/A:H)** | **9.8** | **46.0.7** |
| PYSEC-2026-3552 | CVE-2026-69247 | Oracle Bleichenbacher en PKCS#7 EnvelopedData (C:H) | V4 alto | 50.0.0 |
| PYSEC-2026-3553 | CVE-2026-69249 | DoS: intermediates self-signed duplicados → explosión exponencial | V4 alto | 49.0.0 |
| PYSEC-2026-3554 | CVE-2026-69248 | Wildcard DNS names escapan de permiso (VI:H) | V4 medio | 49.0.0 |
| GHSA-537c-gmf6-5ccf | (OpenSSL vendido) | OpenSSL vulnerable en los wheels | 7.5 (A:H) | 48.0.1 |
| PYSEC-2026-35 | CVE-2026-34073 | Integridad (I:L) | 5.3 | 46.0.6 |

**Riesgo:** el proyecto descifra/verifica certificados en `services/oauth_service.py` (flujo OAuth) — usa `jose.jwt` con HS256, por lo que el verifier de X.509 de cryptography no se invoca en el flujo JWT propio; sin embargo el CVE 46.0.5→9.8 es el de mayor severidad de toda la auditoría y el fix 46.0.7 es un bump patch.

**Recomendación:** bump mínimo a `46.0.7` **inmediato** (cubre el crítico 9.8 y el 5.3), y en la misma pasada de P2 evaluar subir a `49.0.0`/`50.0.0` para cubrir PKCS#7/wildcard/OpenSSL.

---

### A2.4 — ecdsa 0.19.2 — **[SIN FIX — NO EXPLOTABLE]**

| Advisory | CVE | Tipo | CVSS | Fix |
|---|---|---|---|---|
| PYSEC-2026-1325 | CVE-2024-23342 | Timing attack Minerva en curva P-256 (`SigningKey.sign_digest`) | 7.4 | **SIN FIX** (mantenedores lo declaran out of scope) |

**Riesgo:** el proyecto **nunca usa ECDSA**: `core/security.py:40,46,61` firma/valida solo con `HS256` (`ALGORITHM`), igual `routes/auth.py:85` y `services/oauth_service.py:214`. `ecdsa` es transitiva de `python-jose` (instalada por default). El vector Minerva exige observar *timing de firmas* de una clave P-256 del atacante; no hay flujo ECDSA en la app → **no explotable**.

**Recomendación:** documentar y no migrar por esto. Opcional a futuro: evaluar reemplazar `python-jose` por `PyJWT` (eliminaría `ecdsa`/`passlib`/`cryptography` de la cadena), fuera de esta auditoría.

---

### A2.5 — Menores (bumps patch) — **[MEDIO / BAJO]**

| Paquete | Versión | Advisory | Tipo | Fix |
|---|---|---|---|---|
| idna | 3.11 | PYSEC-2026-215 (CVE-2026-45409) | DoS leve en parsing IDNA (A:L) | 3.15 |
| requests | 2.32.5 | PYSEC-2026-2275 (CVE-2026-25645) | Escritura de archivo/pillos local (AV:L, PR:L) | 2.33.0 |
| click | 8.3.1 | PYSEC-2026-2132 (CVE-2026-7246) | Desbordamiento en completado de shell (AV:L/AC:H/PR:H) | 8.3.3 |

Ninguno ataca la superficie de red de la app (todos requieren acceso local o parsing IDNA del lado cliente). Bump trivial.

---

## 3. Dependencias rotas, duplicadas y consistencia requirements↔venv

### 3.1 `pip check` — **[OK]**
`No broken requirements found.` Sin doble versión de numpy ni conflictos de paquetes instalados.

### 3.2 Inconsistencia numpy requirements↔venv — **[MENOR]**

- `requirements.txt:33-34`: `numpy>=2.3.0,<2.5.0; python_version >= '3.14'`.
- **Instalado real:** `numpy==2.2.6` (`pip list`), que queda **fuera del rango** exigido para py3.14.

Esto no lo reporta `pip check` porque ningún paquete instalado exige numpy ≥ 2.3 (onnxruntime pide ≥1.21.6, scipy ≥2.0, tifffile ≥2.1, todos inferiores). El rango `>=2.3` de requirements se respeta solo en instalaciones nuevas de `pip install -r`. Recomendación: **reinstalar** `requirements.txt` (o `pip install -U numpy`) para alinear el venv; es el único desvío real requirements↔venv detectado.

### 3.3 `opencv-python` + `opencv-python-headless` — **[OK]**

Ambos en `4.13.0.92` (instalados; headless llega como dep transitiva de algún paquete CV). Coexisten sin conflicto (y `DEPENDENCIAS.md:83` ya registra que se depuraron del requirements). No rompen nada; queda como nota.

---

## 4. Plan de Remediación

### P1 — Inmediato (bumps patch/menores, sin breaking esperado) — ✅ **APLICADO**
| Paquete | De | A | Cubre | Estado |
|---|---|---|---|---|
| `python-multipart` | 0.0.22 | 0.0.31 | A2.2 (5 CVEs) | ✔ aplicado |
| `cryptography` | 46.0.5 | 46.0.7 | A2.3 crítico 9.8 + 5.3 | ✔ aplicado |
| `idna` | 3.11 | 3.15 | A2.5 | ✔ aplicado |
| `requests` | 2.32.5 | 2.33.0 | A2.5 | ✔ aplicado |
| `click` | 8.3.1 | 8.3.3 | A2.5 | ✔ aplicado |
| `numpy` | venv 2.2.6 | reinstalar req → 2.4.6 | 3.2 | ✔ aplicado |

Verificado: `pip check` limpio, `pytest tests` → **152 passed** (22.96s), `pip-audit` sin vulns en estos paquetes.

### P2 — Coordinado (requiere validación de suite) — ✅ **APLICADO**
| Paquete | De | A | Cubre | Estado |
|---|---|---|---|---|
| `starlette` | 0.52.1 | 1.6.0 | A2.1 (5 CVEs) | ✔ aplicado |
| `fastapi` | 0.135.1 | 0.141.1 | via starlette | ✔ aplicado |
| `slowapi` | 0.1.9 | 0.1.10 | via starlette | ✔ aplicado |
| `cryptography` | 46.0.7 | 50.0.1 | PKCS#7/wildcard/OpenSSL | ✔ aplicado |

Verificado: `pip check` limpio, suite **152 passed** (17.67s), smoke real uvicorn puerto 8767 (login 200 + WS `/v1/parking/ws` recibe `GLOBAL_UPDATE`), `import main` OK (15 rutas top-level). Único warning registrado: deprecación `asyncio.iscoroutinefunction` en slowapi (interno, py3.16) y testclient→httpx2 (cosmético).

### P3 — No accionable
- `ecdsa` (A2.4): sin fix; no explotable por uso HS256. **Única vuln restante del venv tras P1+P2** (1/10). Documentar en `DEPENDENCIAS.md`.
- Considerar a futuro `PyJWT` en lugar de `python-jose`.

---

## 5. Checklist de Cierre

| Ítem | Estado |
|---|---|
| `pip-audit -r requirements.txt` ejecutado | ✔ |
| `pip-audit` sobre venv completo ejecutado (sin config excluida) | ✔ |
| `pip check` sin deps rotas | ✔ |
| Severidades/cvss corroboradas en OSV (advisory por advisory) | ✔ |
| Usos reales del paquete en código verificados (jose→HS256, cryptography→transitoria) | ✔ |
| P1 aplicado en `requirements.txt` + suite verde (**152 passed**) | ✔ |
| Inconsistencia numpy resuelta (venv → 2.4.6) | ✔ |
| P2 aplicado (starlette 1.6.0 + fastapi 0.141.1 + cryptography 50.0.1) + suite verde + smoke WS real | ✔ |
| `pip-audit` final: 1 vuln (ecdsa, sin fix, no explotable) | ✔ |
| `DEPENDENCIAS.md` actualizado con decisiones (starlette 1.x, ecdsa sin fix, numpy) | ⬜ |