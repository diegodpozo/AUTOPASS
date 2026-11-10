# ÍNDICE DE DOCUMENTACIÓN — AUTOPASS

**Actualizado:** 20/10/2026
**Para qué sirve:** un solo lugar donde ver qué documento hay, para qué sirve y cuál es el
**vigente** cuando dos cubren lo mismo. Si un documento no está acá, es porque vive en una
carpeta con su propio índice (`Diseno_Proyecto/README.md`).

> **Regla de oro:** cuando este índice marca "vigente" y "secundario", **vale el vigente**.
> Los secundarios se conservan por historia o por detalle puntual, no para decidir.

---

## 1. Normativo (reglas del proyecto)

| Documento | Qué es | Estado |
|---|---|---|
| `AGENTS.md` | Reglas para asistentes: estilo, nomenclatura, git, BD, backlog. **Se lee primero.** | VIGENTE |
| `.opencode/skills/software-engineering/SKILL.md` | Disciplina de ingeniería (verificación, git seguro, secretos). | VIGENTE (no versionado) |
| `_tools/analysis/NORMAS.md` | Normas internas de la capa de análisis. | VIGENTE |

## 2. Estado y continuidad (por dónde va el trabajo)

| Documento | Qué es | Estado |
|---|---|---|
| `PENDIENTES_PROXIMA_SESION.md` | Estado de la última tanda y pendientes abiertos. **Se lee al arrancar.** | VIGENTE |
| `Info proyecto/ESTADO_PROYECTO.md` | Estado del proyecto por versiones (muy largo; mezcla estado + historial). | VIGENTE |
| `Info proyecto/HISTORIAL.md` | Historial cronológico de versiones. | VIGENTE |
| `BUGS_A_RESOLVER.md` | Registro de bugs pendientes (los tests lo citan por número). | VIGENTE |

## 3. Arquitectura y contexto técnico

| Documento | Qué es | Estado |
|---|---|---|
| `Info proyecto/CONTEXTO_SISTEMA.md` | Arquitectura de comunicación y flujo de datos, capa por capa. | **VIGENTE** |
| `Info proyecto/ARQUITECTURA_DETALLADA.md` | Árbol de directorios y flujo de datos paso a paso. Solapa con el anterior. | Secundario |
| `Info proyecto/GUIA_DESARROLLO.md` | Guía para programar: capas, convenciones, concurrencia, mandatos. | VIGENTE |
| `Info proyecto/DEPENDENCIAS.md` | Librerías y herramientas del stack. | VIGENTE (cabecera vieja) |
| `Info proyecto/EXPLICACION_CODIGO.md` | Índice del visor "EXPLICACION DE CODIGO". | VIGENTE |
| `Info proyecto/ANALISIS_OCR_PLACAS.md` | Pipeline de OCR de patentes (técnico). | VIGENTE |
| `Info proyecto/INICIALIZACION.md` | Puesta en marcha paso a paso. | VIGENTE |
| `AISLAMIENTO_MULTIORG.md` | Aislamiento multiempresa (multi-tenant). | VIGENTE |

## 4. Concurrencia y secciones críticas

| Documento | Qué es | Estado |
|---|---|---|
| `Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md` | Informe **técnico** del plan de concurrencia (6 fases, SQL, decisiones). | VIGENTE |
| `Info proyecto/BLOQUEO_TRANSACCIONAL_PARA_DUMMIES.md` | El mismo plan en **lenguaje llano** (analogías, sin código). | VIGENTE |

## 5. Auditorías

| Documento | Qué es | Estado |
|---|---|---|
| `Info proyecto/AUDITORIAS.md` | Consolidado de la ronda A1–A9 + transversales + CSS (AC-1 a AC-5). | VIGENTE |
| `Info proyecto/AUDITORIA_RBAC.md` | Autorización / IDOR (R1–R10). Ronda posterior, informe propio. | VIGENTE |
| `Info proyecto/AUDITORIA_VALIDACIONES.md` | Validaciones de entrada (V1–V12). Ronda posterior, informe propio. | VIGENTE |
| `AUDITORIA_DB_NEON.md` | Integridad de la base Neon/Postgres. | **VIGENTE** |
| `AUDITORIA_DB.md` | Auditoría de la base SQLite seed (ronda antigua). | Histórico |

## 6. Registros fechados (changelogs)

| Documento | Qué es |
|---|---|
| `Info proyecto/CAMBIOS_BACKLOG_2026-08-30.md` | Cambios aplicados al backlog en esa fecha. |
| `Info proyecto/CHANGELOG_ALPR_QR_2026-06-23.md` | Cambios de ALPR/QR en esa fecha. |

## 7. Conexión con el backlog

- Tablero web: `https://marianojac.github.io/backlogAUTOPASS/` (repo `backlogAUTOPASS/`).
- Cómo escribirle filas por API: ver la sección "Backlog web" de `AGENTS.md`.
- `Info proyecto/RESPONSABLES_BACKLOG.md`: relevamiento de **qué responsable tiene cada
  función/historia** (320 filas, fuente Firebase), con reparto por sección y tareas abiertas.

## 8. Diseño del proyecto (RUP)

Carpeta `Diseno_Proyecto/` con 5 fases (Inception, Elaboration, Construction, Transition,
Apéndices). Tiene su **propio índice**: `Diseno_Proyecto/README.md`.
**Ojo:** su contenido es de una etapa temprana (v9.6.0) y sus nombres no siguen
`SCREAMING_SNAKE_CASE`; se conserva como documentación académica de diseño.

## 9. Qué va en la raíz y qué no

En la raíz solo deben vivir **entradas del sistema y documentos transversales**:

- **Código de entrada:** `main.py` (backend), `init_db.py`, `alpr_service.py`, `locustfile.py`.
- **Configuración:** `.env` / `.env.example`, `alembic.ini`, `pytest.ini`, `requirements.txt`,
  `.gitignore`, los `.bat` (`run_server`, `setup_backend`, `acceso_remoto`, `detener_acceso_remoto`).
- **Datos de prueba de herramientas:** `usuarios_demo.csv` (lo lee `locustfile.py`) y
  `USUARIOS_PRUEBA.xlsx`.
- **Documentos transversales:** `AGENTS.md`, `README.md`, `INDICE_DOCUMENTACION.md`,
  `PENDIENTES_PROXIMA_SESION.md`, `BUGS_A_RESOLVER.md`, `AISLAMIENTO_MULTIORG.md` y las auditorías
  de BD.

**No van en la raíz:** visores HTML de documentación (van a `Info proyecto/`), copias comprimidas
de carpetas ya versionadas, bases de datos sueltas (`.db`) o respaldos (`.bak`). Recordá que
`*.db`, `*.bak`, `.env`, `.coverage` y `coverage_html/` están en `.gitignore`: son basura local,
no archivos del repo.


---

## Cifras del sistema (medidas en disco — NO repetir de memoria)

Estos son los números **reales** al 20/10/2026. Si ves otro valor en algún documento, ese
documento está desactualizado y hay que corregirlo contra esta tabla:

| Qué | Cuánto | Cómo se mide |
|---|---|---|
| Módulos JS | **68** | `Get-ChildItem static\js\modules -Recurse -Filter *.js` |
| Scripts puente JS | **9** | `Get-ChildItem static\js -File -Filter *.js` |
| Archivos CSS | **47** | `Get-ChildItem static\css -Recurse -Filter *.css` |
| Templates HTML | **58** | `Get-ChildItem templates -Recurse -Filter *.html` |
| Componentes Jinja | **14** | `Get-ChildItem templates\components -Filter *.html` |
| Servicios | **20** | `Get-ChildItem services -File -Filter *.py` |
| Repositorios | **17** | `Get-ChildItem repositories -File -Filter *.py` |
| Archivos de test | **73** | `Get-ChildItem tests -Recurse -Filter test_*.py` |
| Tests totales | **956** | `941` por defecto + `15` del grupo `postgres` |
| Head Alembic | `b1c2d3e4f5a6` | `alembic heads` |

> **Nota:** los conteos de JS/CSS/servicios/repos subieron desde los valores que figuran en
> documentos viejos (65 JS, 46 CSS, 19 servicios, 16 repos). El conteo de módulos JS incluye
> subcarpetas, por eso difiere de las mediciones anteriores que solo miraban el nivel raíz.

---

## Cómo mantener este índice

1. Cuando agregues o borres un documento, **actualizá este índice** en la misma tanda.
2. Cuando dos documentos cubran lo mismo, marcá uno como **VIGENTE** y el otro como
   **Secundario** (y poné la nota cruzada adentro de cada archivo, como se hizo con
   `CONTEXTO_SISTEMA.md` / `ARQUITECTURA_DETALLADA.md`).
3. Si un número cambia (tests, módulos, etc.), corregilo **acá primero** y después en el resto.
