from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import time
import schemas
from core.database import get_db
from services.billing_service import BillingService
from services.access_service import AccessService
from .utils import normalize_plate
 
router = APIRouter()

@router.post("/access/validate-plate", response_model=schemas.AccessResponse)
def validate_plate(data: schemas.PlateValidation, db: Session = Depends(get_db), request: Request = None):
    """VALIDA UNA PATENTE DETECTADA."""
    t0 = time.time()
    result = AccessService.validate_plate(db, data, request)
    backend_time = round(time.time() - t0, 3)
    if result.get("status") == "allowed":
        from models import AccessLog
        last = db.query(AccessLog).order_by(AccessLog.id.desc()).first()
        if last:
            last.backend_time = backend_time
            db.commit()
    return result

@router.post("/access/exit-plate", response_model=schemas.AccessResponse)
def exit_plate(data: schemas.PlateValidation, db: Session = Depends(get_db), request: Request = None):
    """VALIDA LA SALIDA DE UN VEHICULO."""
    t0 = time.time()
    result = AccessService.exit_plate(db, data, request)
    backend_time = round(time.time() - t0, 3)
    if result.get("status") == "allowed":
        from models import AccessLog
        last = db.query(AccessLog).order_by(AccessLog.id.desc()).first()
        if last:
            last.backend_time = backend_time
            db.commit()
    return result

@router.post("/access/validate-qr", response_model=schemas.AccessResponse)
def validate_qr(data: schemas.QRValidation, db: Session = Depends(get_db), request: Request = None):
    """VALIDA UN PASE DIGITAL (QR)."""
    return AccessService.validate_qr(db, data, request)

@router.post("/access/pay-stay")
def pay_stay(plate: str, db: Session = Depends(get_db)):
    """PROCESA EL PAGO DE UNA ESTADIA EN CURSO."""
    result = BillingService.process_payment(db, normalize_plate(plate))
    if result["status"] == "ok": return result
    raise HTTPException(status_code=400, detail=result["message"])
