from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import schemas
from core.database import get_db
from services.billing_service import BillingService
from services.access_service import AccessService
from .utils import normalize_plate

router = APIRouter()

@router.post("/access/validate-plate", response_model=schemas.AccessResponse)
def validate_plate(data: schemas.PlateValidation, db: Session = Depends(get_db), request: Request = None):
    """Valida una patente detectada."""
    return AccessService.validate_plate(db, data, request)

@router.post("/access/exit-plate", response_model=schemas.AccessResponse)
def exit_plate(data: schemas.PlateValidation, db: Session = Depends(get_db), request: Request = None):
    """Valida la salida de un vehículo."""
    return AccessService.exit_plate(db, data, request)

@router.post("/access/validate-qr", response_model=schemas.AccessResponse)
def validate_qr(data: schemas.QRValidation, db: Session = Depends(get_db), request: Request = None):
    """Valida un Pase Digital (QR)."""
    return AccessService.validate_qr(db, data, request)

@router.post("/access/pay-stay")
def pay_stay(plate: str, db: Session = Depends(get_db)):
    """Procesa el pago de una estadía en curso."""
    result = BillingService.process_payment(db, normalize_plate(plate))
    if result["status"] == "ok": return result
    raise HTTPException(status_code=400, detail=result["message"])
