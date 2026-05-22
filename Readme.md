# AUTOPASS - Estacionamiento Inteligente (v7.0 Modular)

Solución empresarial para la gestión de estacionamientos que combina **Visión Artificial (ALPR)**, **Arquitectura Limpia (Clean Architecture)** y un **Frontend Premium** de alto impacto.

## 🌟 Últimas Actualizaciones (v7.2.2)
- **Unified Account Hub**: Nueva interfaz de gestión de cuenta con seguridad integrada y diseño de doble panel.
- **Historial de Puntos Premium**: Implementación de navegación paginada y cálculos inteligentes en el backend.
- **Refinamiento UI/UX**: Centrado simétrico total, iconografía alineada y validaciones de seguridad en tiempo real.

## 🏗️ Arquitectura del Sistema

El proyecto sigue una estructura modular diseñada para el escalamiento y la alta mantenibilidad:

- **`core/`**: Infraestructura crítica (Configuración, Seguridad JWT/RBAC, DB, MQTT).
- **`models/` & `schemas/`**: Capa de datos organizada por dominios (Usuarios, Parking, Reservas).
- **`routes/`**: Controladores de API y entrega de Vistas HTML.
- **`services/`**: Inteligencia de negocio y procesos de fondo.
- **`templates/`**: Frontend modular basado en Jinja2 con componentes reutilizables.

## 🌟 Características Principales

- **Multi-Sede Nativo**: Gestión independiente de tarifas, aforo y personal por sucursal.
- **Visión Artificial Híbrida**: Reconocimiento de patentes y códigos QR en tiempo real.
- **RBAC (Role Based Access Control)**: Jerarquía de permisos (Admin, Local Admin, Staff, User).
- **Fidelización**: Sistema de puntos AutoPass por consumo.
- **IoT Ready**: Comunicación MQTT integrada para el control de hardware (barreras).

## 🚀 Inicio Rápido

1. Instalar dependencias: `pip install -r requirements.txt`
2. Inicializar DB: `python init_db.py`
3. Arrancar: `uvicorn main:app --reload`

## 🛠️ Tecnologías

- **Backend:** FastAPI (Python 3.9+)
- **Base de Datos:** SQLAlchemy (SQLite/PostgreSQL)
- **Frontend:** Vanilla JS, CSS Moderno, Jinja2, Chart.js.
- **IoT:** Paho-MQTT.
- **IA:** OpenCV + EasyOCR (Deep Learning).

---
*AUTOPASS es una marca de ParkingTech. Hecho con ❤️ para la movilidad urbana.*
