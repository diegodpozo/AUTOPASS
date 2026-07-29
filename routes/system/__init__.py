"""
Módulo de Rutas de Sistema y Salud (system) modularizado.
"""
from fastapi import APIRouter
from routes.system.common import stop_all_cameras, CAMERA_PROCESSES, manager
from routes.system.health import router as health_router
from routes.system.cameras import router as cameras_router
from routes.system.video import router as video_router

router = APIRouter(tags=["System & Health"])
router.include_router(health_router)
router.include_router(cameras_router)
router.include_router(video_router)

__all__ = ["router", "stop_all_cameras", "CAMERA_PROCESSES", "manager"]
