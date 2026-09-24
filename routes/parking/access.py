from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import models, schemas
from core.database import get_db
from core.limiter import limiter
from core.security import get_operational_user
from core.alpr_security import require_alpr_node
from services.billing_service import BillingService
from services.access_service import AccessService
from .utils import normalize_plate
 
router = APIRouter()

@router.post("/access/validate-plate", response_model=schemas.AccessResponse)
@limiter.limit("120/minute")
def validate_plate(request: Request, data: schemas.PlateValidation, db: Session = Depends(get_db), _: None = Depends(require_alpr_node)):
    """VALIDA UNA PATENTE DETECTADA (SOLO NODO ALPR AUTORIZADO)."""
    return AccessService.validate_plate(db, data, request)

@router.post("/access/exit-plate", response_model=schemas.AccessResponse)
@limiter.limit("120/minute")
def exit_plate(request: Request, data: schemas.PlateValidation, db: Session = Depends(get_db), _: None = Depends(require_alpr_node)):
    """VALIDA LA SALIDA DE UN VEHICULO (SOLO NODO ALPR AUTORIZADO)."""
    return AccessService.exit_plate(db, data, request)

@router.post("/access/validate-qr", response_model=schemas.AccessResponse)
@limiter.limit("60/minute")
def validate_qr(request: Request, data: schemas.QRValidation, db: Session = Depends(get_db), _: None = Depends(require_alpr_node)):
    """VALIDA UN PASE DIGITAL (QR) (SOLO NODO ALPR AUTORIZADO)."""
    return AccessService.validate_qr(db, data, request)

@router.post("/access/pay-stay")
@limiter.limit("10/minute")
def pay_stay(request: Request, plate: str, metodo: str = "DIGITAL", db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """PROCESA EL PAGO DE UNA ESTADIA EN CURSO (SOLO PERSONAL OPERATIVO)."""
    result = BillingService.process_payment(db, normalize_plate(plate), metodo=metodo.upper())
    if result["status"] == "ok": return result
    raise HTTPException(status_code=400, detail=result["message"])
