# Diseño del Proyecto — AUTOPASS

Documentación completa del diseño del sistema siguiendo el **Proceso Unificado de Desarrollo (RUP/UP)**.

## Estructura

```
Diseno_Proyecto/
│
├── 01_Inception/                     # FASE DE INICIO
│   ├── 01_Vision_Del_Sistema.md      # Visión, propósito, propuesta de valor
│   ├── 02_Stakeholders_Y_Equipo.md   # Stakeholders, equipo, cronograma
│   ├── 03_Alcance_Y_GLOSARIO.md      # Alcance funcional, glosario, exclusiones
│   └── 04_Modelo_De_Negocio.md       # Modelo de negocio, KPIs, ventajas competitivas
│
├── 02_Elaboration/                   # FASE DE ELABORACIÓN
│   ├── 01_Requisitos_Funcionales.md  # RF-01 a RF-44 detallados
│   ├── 02_Requisitos_No_Funcionales.md # RNF-01 a RNF-29
│   ├── 03_Casos_De_Uso.md           # 20 casos de uso con flujos principales
│   └── 04_Arquitectura_General.md   # Clean Architecture, capas, patrones, flujo de datos
│
├── 03_Construction/                  # FASE DE CONSTRUCCIÓN
│   ├── 01_Modelo_De_Datos.md        # DER, entidades, columnas, relaciones
│   ├── 02_Diagramas_De_Secuencia.md # 5 diagramas de secuencia detallados
│   ├── 03_Diagrama_De_Clases.md     # Diagrama de clases por capa
│   └── 04_Diseno_Frontend.md        # Arquitectura frontend, design system, componentes
│
├── 04_Transition/                    # FASE DE TRANSICIÓN
│   ├── 01_Despliegue.md             # Instalación, configuración, producción
│   ├── 02_Pruebas.md                # Estrategia de pruebas, casos críticos, cobertura
│   └── 03_Operaciones_Y_Mantenimiento.md # Monitoreo, logs, recovery, seguridad
│
└── 05_Apendices/                     # DOCUMENTACIÓN ADICIONAL
    ├── 01_Mapa_De_Rutas_API.md       # Todos los endpoints organizados por módulo
    ├── 02_Arquitectura_ALPR.md       # Arquitectura del sistema de visión artificial
    └── 03_Integracion_Hardware.md    # ESP32, MQTT, cámaras, firmware
```

## Resumen por Fase

### 1. Inception (Inicio)
Define la **visión del sistema**: un gestor de estacionamientos inteligente con ALPR, multi-sucursal, multi-piso, facturación trimodal y reservas. Identifica 4 roles de usuario (ADMIN, LOCAL_ADMIN, STAFF, USER) y establece el alcance de la versión v9.5.0.

### 2. Elaboration (Elaboración)
Especifica **44 requisitos funcionales** y **29 no funcionales**, detalla **20 casos de uso** con flujos principales y alternativos, y define la **arquitectura Clean Architecture** con 4 capas (Routes, Services, Models, Core) más frontend Jinja2 + WebSockets.

### 3. Construction (Construcción)
Documenta el **modelo de datos** con 11 entidades y sus relaciones, **5 diagramas de secuencia** (ingreso ALPR, egreso con pago, reserva, worker, operación manual), **diagrama de clases** completo por capa, y el **diseño del frontend** con design system (Glassmorphism, dorado #C5A059, FAB).

### 4. Transition (Transición)
Cubre el **plan de despliegue** (SQLite dev / PostgreSQL prod), **estrategia de pruebas** con 8 casos críticos, y **operaciones y mantenimiento** (health checks, logs, workers, recovery).

### 5. Apéndices
Mapa completo de **rutas API**, **arquitectura del sistema ALPR** (EasyOCR + OpenCV con consenso), e **integración con hardware** ESP32 vía MQTT.

## Versión del Sistema
**AUTOPASS v9.5.0** — Julio 2026
