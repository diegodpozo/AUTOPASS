import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from core.config import settings
from core.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("System")
from core.database import engine, sync_schema
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

# CONCURRENCIA (FASE 2): un unico punto de traduccion LockTimeoutError -> HTTP 409.
# Preferido a try/except en cada ruta (DRY): cualquier endpoint que entre en una
# seccion critica sin poder obtener el lock responde 409 con mensaje de reintento.
from core.db_lock import LockTimeoutError


@app.exception_handler(LockTimeoutError)
async def lock_timeout_handler(request, exc):
    """HTTP 409 cuando la seccion critica esta tomada por otra operacion concurrente."""
    logger.warning(f"Lock transaccional no obtenido: {exc}")
    return JSONResponse(
        status_code=409,
        content={"detail": "La operación está siendo procesada por otro proceso. Reintentá en unos segundos."},
    )


# CONCURRENCIA (FASE 5): traduccion unica IntegrityError -> HTTP 409 con la sesion limpia.
# Un choque de unicidad (doble webhook de MP con el mismo payment_id, reserva duplicada que
# choque contra el constraint de la Fase 4, etc.) significa "esa operacion ya se hizo": no es
# un error 500 sino un conflicto de negocio que se resuelve reintentando. El rollback deja la
# sesion usable para que el handler de la request no falle al cerrarla.
from sqlalchemy.exc import IntegrityError


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request, exc):
    """HTTP 409 ante un choque de unicidad/integridad, con db.rollback() limpio."""
    logger.warning(f"IntegrityError en {request.url.path}: {exc.orig if hasattr(exc, 'orig') else exc}")
    return JSONResponse(
        status_code=409,
        content={"detail": "La operación ya fue procesada o entra en conflicto con otra existente. "
                           "Actualizá la pantalla y reintentá."},
    )

# --- GUARD DE SEGURIDAD: SECRET_KEY DEMO (SOLO FALLA EN PRODUCCION) ---
if settings.ENVIRONMENT == "production" and settings.SECRET_KEY == "tu_super_secreto_para_produccion":
    raise RuntimeError(
        "SECRET_KEY sigue siendo el valor demo. Configurá SECRET_KEY en el entorno antes de entrar a producción."
    )
if settings.SECRET_KEY == "tu_super_secreto_para_produccion":
    logger.warning(
        "SECRET_KEY usa el valor demo. Configurá SECRET_KEY por entorno (solo crítico en producción)."
    )

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

# ORIGENES EXTERNOS PERMITIDOS POR LA CSP (CDNs, fuentes de Google y APIs de mapas)
CSP_CDNS = "https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://unpkg.com https://npmcdn.com"
CSP_GOOGLE_FONTS = "https://fonts.googleapis.com https://fonts.gstatic.com"
CSP_MAP_APIS = "https://overpass-api.de https://nominatim.openstreetmap.org"
CSP_HEADER = (
    "default-src 'self'; "
    f"script-src 'self' {CSP_CDNS} 'unsafe-inline'; "
    f"style-src 'self' 'unsafe-inline' {CSP_CDNS} {CSP_GOOGLE_FONTS}; "
    f"font-src 'self' data: https://cdnjs.cloudflare.com {CSP_GOOGLE_FONTS}; "
    "img-src 'self' data: blob: https://*.google.com https://www.google.com; "
    f"connect-src 'self' ws: wss: {CSP_MAP_APIS} {CSP_CDNS}; "
    "frame-ancestors 'self'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

@app.middleware("http")
async def no_cache_js(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/js/"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response

@app.middleware("http")
async def security_headers_middleware(request, call_next):
    """Headers de seguridad en toda respuesta (CSP pragmático, HSTS, XFO, nosniff)."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = CSP_HEADER
    forwarded = request.headers.get("x-forwarded-proto", "")
    if request.url.scheme == "https" or forwarded.lower() == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
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
        
        # BASE DE DATOS: FLUJO UNICO DE ESQUEMA (create_all de modelos + Alembic al head)
        try:
            sync_schema()
        except Exception as schema_err:
            logger.error(f"Error en sincronización de esquema: {schema_err}")
        
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
    try:
        from core.mqtt import mqtt_client
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    except Exception as e:
        logger.debug(f"Error al desconectar MQTT: {e}")
    try:
        from core.database import engine
        engine.dispose()
    except Exception as e:
        logger.debug(f"Error al disponer engine: {e}")

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
