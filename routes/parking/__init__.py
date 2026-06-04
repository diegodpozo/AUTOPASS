from fastapi import APIRouter
from .status import router as status_router
from .access import router as access_router
from .utils import normalize_plate, format_plate, normalize_name, normalize_dni

router = APIRouter(prefix="/v1", tags=["Parking & Access"])

router.include_router(status_router)
router.include_router(access_router)
