from fastapi import APIRouter
from .users import router as users_router
from .reservations import router as reservations_router
from .settings import router as settings_router
from .branches import router as branches_router
from .promotions import router as promotions_router
from .operations import router as operations_router

router = APIRouter(prefix="/v1/admin", tags=["Administration"])

router.include_router(users_router)
router.include_router(reservations_router)
router.include_router(settings_router)
router.include_router(branches_router)
router.include_router(promotions_router)
router.include_router(operations_router)
