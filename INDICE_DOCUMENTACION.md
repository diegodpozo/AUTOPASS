# ÍNDICE DE DOCUMENTACIÓN — AUTOPASS

**Actualizado:** 10/11/2026  
**Propósito:** Catálogo central de la documentación técnica y de diseño del proyecto. Toda la documentación funcional y formal del sistema vive de manera canónica dentro de la carpeta `Diseno_Proyecto/`.

---

## 1. Normativo y Continuidad (Raíz)

| Documento | Qué es | Estado |
|---|---|---|
| [`AGENTS.md`](AGENTS.md) | Reglas de arquitectura, modularidad, estilo y buenas prácticas. **Se lee primero.** | **VIGENTE** |
| [`PENDIENTES_PROXIMA_SESION.md`](PENDIENTES_PROXIMA_SESION.md) | Registro de continuidad, tareas cerradas y puntos abiertos. **Se lee al arrancar.** | **VIGENTE** |
| [`README.md`](README.md) | Portada principal y guía de instalación/ejecución del sistema. | **VIGENTE** |

---

## 2. Diseño Formal del Proyecto (Metodología RUP)

Toda la documentación técnica, de requerimientos, arquitectura y construcción reside en [`Diseno_Proyecto/`](Diseno_Proyecto/README.md):

| Fase / Carpeta | Documentos | Descripción |
|---|---|---|
| **01 Inception** | `01_Vision_Del_Sistema.md`<br>`02_Stakeholders_Y_Equipo.md`<br>`03_Alcance_Y_GLOSARIO.md`<br>`04_Modelo_De_Negocio.md` | Visión del sistema, partes interesadas, alcance del MVP y modelo de negocio. |
| **02 Elaboration** | `01_Requisitos_Funcionales.md`<br>`02_Requisitos_No_Funcionales.md`<br>`03_Casos_De_Uso.md`<br>`04_Arquitectura_General.md` | Especificación de requisitos funcionales/no funcionales, casos de uso del sistema y arquitectura global. |
| **03 Construction** | `01_Modelo_De_Datos.md`<br>`02_Diagramas_De_Secuencia.md`<br>`03_Diagrama_De_Clases.md`<br>`04_Diseno_Frontend.md` | Modelo entidad-relación / tablas, diagramas de secuencia de flujos críticos, diagrama de clases y diseño UI/UX. |
| **04 Transition** | `01_Despliegue.md`<br>`02_Pruebas.md`<br>`03_Operaciones_Y_Mantenimiento.md` | Guías de despliegue, estrategia de pruebas y mantenimiento operativo. |
| **05 Apéndices** | `01_Mapa_De_Rutas_API.md`<br>`02_Arquitectura_ALPR.md`<br>`03_Integracion_Hardware.md` | Catálogo de endpoints de la API, arquitectura de visión artificial ALPR y comunicación con maqueta física (Arduino / IoT). |

---

## 3. Conexión con el Tablero de Trabajo

- **Tablero Web del Backlog:** Carpeta local `backlogAUTOPASS/` (desplegable en GitHub Pages).
- **Actualización por API:** Según las directivas especificadas en [`AGENTS.md`](AGENTS.md).
