import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core.config import settings
from core.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("System")
from core.database import engine, init_db
from core.mqtt import mqtt_client
from services.worker_service import WorkerService
import models

# IMPORTACION DE ROUTERS
from routes import parking, reports, system, admin, user, auth
from routes.system import stop_all_cameras
from routes.views import router as views_router

# RATE LIMITING
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from core.limiter import limiter

# --- CONFIGURACION DE LA APLICACION ---
app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.mqtt_client = mqtt_client #INYECCION PARA ACCESO GLOBAL

# DIRECTORIO PARA IMAGENES Y UPLOADS
for path in [settings.IMAGE_DIR, os.path.join("static", "uploads", "branches")]:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

# MONTAJE DE ARCHIVOS ESTATICOS
app.mount("/images", StaticFiles(directory=settings.IMAGE_DIR), name="images")
app.mount("/static", StaticFiles(directory="static"), name="static")

# PWA: service worker en el scope raiz (controla TODO el sitio) y manifest
@app.get("/sw.js")
async def service_worker():
    return FileResponse(
        "static/sw.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )

@app.get("/manifest.webmanifest")
async def manifest():
    return FileResponse("static/manifest.json", media_type="application/manifest+json")

# MIDDLEWARES
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def no_cache_js(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/js/"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response

@app.on_event("startup")
async def startup_event():
    """INICIALIZACION DE SERVICIOS AL ARRANCAR EL SERVIDOR."""
    try:
        import asyncio
        from services.notification_service import NotificationService
        NotificationService.set_event_loop(asyncio.get_running_loop())

        # MQTT
        mqtt_client.connect_async(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
        mqtt_client.loop_start()
        
        # BASE DE DATOS: APLICAR MIGRACIONES PENDIENTES Y LUEGO CREAR TABLAS NUEVAS
        try:
            from alembic.config import Config as AlembicConfig
            from alembic import command as AlembicCommand
            alembic_cfg = AlembicConfig("alembic.ini")
            try:
                AlembicCommand.upgrade(alembic_cfg, "head")
                logger.debug("Migraciones Alembic aplicadas correctamente.")
            except Exception:
                # Tablas ya existen de init_db(); stamp version y seguir
                AlembicCommand.stamp(alembic_cfg, "head")
                logger.debug("Migraciones stamp (tablas ya existían).")
        except Exception as alembic_err:
            logger.warning(f"Migraciones Alembic omitidas: {alembic_err}")

        init_db()
        
        # BACKGROUND WORKERS
        WorkerService.start_reservation_cleanup()
        WorkerService.start_notification_worker()
        
    except Exception as e: 
        logger.error(f"Error en fase de inicio (MQTT/DB): {e}")

@app.on_event("shutdown")
def shutdown_event():
    """LIMPIEZA DE RECURSOS AL APAGAR EL SERVIDOR."""
    logger.info("Apagando servidor, limpiando recursos...")
    stop_all_cameras()

# --- REGISTRO DE RUTAS ---
# API V1
app.include_router(auth)
app.include_router(parking)
app.include_router(reports)
app.include_router(system, prefix="/v1/system")
app.include_router(admin)
app.include_router(user)

# FRONTEND
app.include_router(views_router)
