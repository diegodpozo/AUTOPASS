from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import models, schemas
from core.database import get_db
from core.limiter import limiter
from core.security import get_operational_user, resolve_actor_organization_id
from core.alpr_security import require_alpr_node_org
from models.enums import UserRole
from repositories.branch_repository import BranchRepository
from services.billing_service import BillingService
from services.access_service import AccessService
from .utils import normalize_plate
 
router = APIRouter()

@router.post("/access/validate-plate", response_model=schemas.AccessResponse)
@limiter.limit("120/minute")
def validate_plate(request: Request, data: schemas.PlateValidation, db: Session = Depends(get_db), node_org: Optional[int] = Depends(require_alpr_node_org)):
    """VALIDA UNA PATENTE DETECTADA (SOLO NODO ALPR AUTORIZADO, CON SU ORGANIZACION)."""
    return AccessService.validate_plate(db, data, request, organization_id=node_org)

@router.post("/access/exit-plate", response_model=schemas.AccessResponse)
@limiter.limit("120/minute")
def exit_plate(request: Request, data: schemas.PlateValidation, db: Session = Depends(get_db), node_org: Optional[int] = Depends(require_alpr_node_org)):
    """VALIDA LA SALIDA DE UN VEHICULO (SOLO NODO ALPR AUTORIZADO, CON SU ORGANIZACION)."""
    return AccessService.exit_plate(db, data, request, organization_id=node_org)

@router.post("/access/validate-qr", response_model=schemas.AccessResponse)
@limiter.limit("60/minute")
def validate_qr(request: Request, data: schemas.QRValidation, db: Session = Depends(get_db), node_org: Optional[int] = Depends(require_alpr_node_org)):
    """VALIDA UN PASE DIGITAL (QR) (SOLO NODO ALPR AUTORIZADO, CON SU ORGANIZACION)."""
    return AccessService.validate_qr(db, data, request, organization_id=node_org)

@router.post("/access/pay-stay")
@limiter.limit("10/minute")
def pay_stay(request: Request, plate: str, metodo: str = "DIGITAL", db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """PROCESA EL PAGO DE UNA ESTADIA EN CURSO (SOLO PERSONAL OPERATIVO).

    El cobro queda acotado a la organizacion del staff (y a su sede si no es ADMIN
    global): nunca se cobra una estadia registrada por otra empresa."""
    organizacion = resolve_actor_organization_id(db, staff)
    sucursal_id = None
    if staff.rol != UserRole.ADMIN:
        sucursal_id = staff.sucursal_id or BranchRepository.get_id_by_name(db, staff.sucursal, organizacion)
    result = BillingService.process_payment(
        db, normalize_plate(plate), metodo=metodo.upper(),
        organization_id=organizacion, sucursal_id=sucursal_id,
    )
    if result["status"] == "ok": return result
    raise HTTPException(status_code=400, detail=result["message"])
