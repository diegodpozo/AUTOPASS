from fastapi import APIRouter
from .profile import router as profile_router
from .vehicles import router as vehicles_router
from .balance import router as balance_router
from .reservations import router as reservations_router
from .fidelization import router as fidelization_router
from .notifications import router as notifications_router
from .support import router as support_router

router = APIRouter(prefix="/v1/user", tags=["User Actions"])

router.include_router(profile_router)
router.include_router(vehicles_router)
router.include_router(balance_router)
router.include_router(reservations_router)
router.include_router(fidelization_router)
router.include_router(notifications_router)
router.include_router(support_router)
