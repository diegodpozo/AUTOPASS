from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from core.database import get_db
from core.security import get_operational_user
from services.reservation_service import ReservationService

router = APIRouter()

@router.get("/reservations/patente-lookup")
def patente_lookup(patente: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """BUSCA SI UNA PATENTE ESTA REGISTRADA A UN USUARIO PARA VINCULARLA A UNA RESERVA MANUAL."""
    return ReservationService.lookup_patente(db, patente)

@router.get("/reservations/new-count")
def get_new_reservations_count(
    since_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    staff: models.User = Depends(get_operational_user)
):
    """RETORNA LA CANTIDAD DE RESERVAS NUEVAS DESDE since_id Y EL ULTIMO ID REGISTRADO.
    Alimenta la burbuja de notificación en la pestaña de Reservas del Dashboard."""
    return ReservationService.get_new_reservations_count(db, staff, since_id)

@router.get("/reservations", response_model=List[schemas.UserReservationResponse])
def list_reservations(estado: Optional[str] = Query(None), sucursal: Optional[str] = Query(None), db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """LISTA TODAS LAS RESERVAS. LOS LOCALES SOLO VEN LAS DE SU SEDE."""
    return ReservationService.list_admin_reservations(db, staff, estado, sucursal)

@router.post("/reservations")
def create_admin_reservation(data: schemas.AdminReservationCreate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """PERMITE AL ADMINISTRADOR O EMPLEADO CREAR UNA RESERVA MANUAL."""
    return ReservationService.create_admin_reservation(db, staff, data)

@router.put("/reservations/{res_id}")
def update_admin_reservation(res_id: int, data: schemas.AdminReservationCreate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """EDITA UNA RESERVA CREADA POR ADMINISTRADOR O EMPLEADO (NO LAS CREADAS POR CLIENTES)."""
    return ReservationService.update_admin_reservation(db, staff, res_id, data)

@router.post("/reservations/{res_id}/confirm-payment")
def confirm_reservation_payment(res_id: int, data: schemas.ConfirmPaymentRequest = None, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """CONFIRMACION MANUAL DE PAGO."""
    return ReservationService.confirm_reservation_payment(db, staff, res_id, data)

@router.post("/reservations/{res_id}/cancel")
def cancel_reservation_admin(res_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """CANCELACION MANUAL."""
    ReservationService.get_permissioned_reservation(db, staff, res_id)
    result = ReservationService.cancel_reservation(db, None, res_id)
    if result["status"] == "ok":
        return result
    raise HTTPException(status_code=400, detail=result["message"])

@router.get("/reservations/{res_id}/redemptions")
def reservation_available_redemptions(res_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """LISTA LOS DESCUENTOS DE RESERVA (%) VIGENTES DEL USUARIO VINCULADO A UNA RESERVA Y APLICABLES A SU SUCURSAL.
    Se usa antes de registrar un pago en caja para informar y aplicar el descuento."""
    reserva = ReservationService.get_permissioned_reservation(db, staff, res_id)
    descuentos = ReservationService.get_available_redemption_discounts(db, reserva.user_id, reserva.sucursal_nombre)
    monto = reserva.monto_total or 0.0
    return [{
        "id": d.id,
        "titulo": d.titulo,
        "valor_descuento": d.valor_descuento or 0,
        "monto": monto,
        "descuento_peso": round(monto * (d.valor_descuento or 0) / 100.0, 2),
        "monto_final": round(monto - monto * (d.valor_descuento or 0) / 100.0, 2),
        "created_at": d.created_at
    } for d in descuentos]

@router.get("/reservations/{res_id}/redemption-info")
def reservation_redemption_info(res_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """INFORMA SI A UNA RESERVA APLICA DESCUENTO PARA MOSTRARLO EN LA EDICIÓN DEL PANEL.
    - fuente 'vigente': el usuario tiene un canje descuento_reserva VIGENTE aplicable (aún no consumido).
    - fuente 'aplicado': la reserva ya se pagó en caja con un descuento (ticket consumido en esta reserva)."""
    reserva = ReservationService.get_permissioned_reservation(db, staff, res_id)
    info = {
        "aplica": False,
        "fuente": None,
        "valor_descuento": None,
        "ticket_id": None,
        "monto": reserva.monto_total or 0.0
    }
    vigente = ReservationService.get_available_redemption_discounts(db, reserva.user_id, reserva.sucursal_nombre)
    if vigente:
        d = vigente[0]
        info.update(aplica=True, fuente="vigente", valor_descuento=d.valor_descuento or 0, ticket_id=d.id)
        return info
    ticket_aplicado = db.query(models.RedemptionTicket).filter(
        models.RedemptionTicket.reserva_id == reserva.id,
        models.RedemptionTicket.tipo_canje == "descuento_reserva",
        models.RedemptionTicket.estado == "USADO"
    ).first()
    if ticket_aplicado and ticket_aplicado.valor_descuento:
        info.update(aplica=True, fuente="aplicado", valor_descuento=ticket_aplicado.valor_descuento, ticket_id=ticket_aplicado.id)
    return info

@router.get("/redemptions/available")
def admin_available_redemptions(user_id: int, sucursal: str = None, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """LISTA LOS DESCUENTOS DE RESERVA (%) VIGENTES DE UN USUARIO APLICABLES A UNA SUCURSAL.
    Se usa en el flujo de nueva reserva manual en caja para ofrecer el descuento antes de crear y pagar."""
    descuentos = ReservationService.get_available_redemption_discounts(db, user_id, sucursal)
    return [{"id": d.id, "titulo": d.titulo, "valor_descuento": d.valor_descuento or 0, "created_at": d.created_at} for d in descuentos]