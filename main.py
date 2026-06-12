import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.database import engine
from core.mqtt import mqtt_client
from services.worker_service import WorkerService
import models

# Importación de Routers
from routes import parking, reports, system, admin, user, auth
from routes.views import router as views_router

# --- CONFIGURACIÓN DE LA APLICACIÓN ---
app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)
app.mqtt_client = mqtt_client # Inyección para acceso global

# Directorio para imágenes
if not os.path.exists(settings.IMAGE_DIR):
    os.makedirs(settings.IMAGE_DIR)

# Montaje de archivos estáticos
app.mount("/images", StaticFiles(directory=settings.IMAGE_DIR), name="images")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """Inicialización de servicios al arrancar el servidor."""
    try:
        # MQTT
        mqtt_client.connect_async(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
        mqtt_client.loop_start()
        
        # Base de Datos
        models.Base.metadata.create_all(bind=engine)
        
        # Background Workers
        WorkerService.start_reservation_cleanup()
        
    except Exception as e: 
        print(f"Error en fase de inicio (MQTT/DB): {e}")

# --- REGISTRO DE RUTAS ---
# API v1
app.include_router(auth)
app.include_router(parking)
app.include_router(reports)
app.include_router(system, prefix="/v1/system")
app.include_router(admin)
app.include_router(user)

# Frontend
app.include_router(views_router)
