import datetime
import math
import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List
import models, schemas
from core.database import get_db
from core.security import get_current_user

router = APIRouter()

# ---------------------------------------------------------------------------
# TICKETS DE CANJE / VOUCHER
# ---------------------------------------------------------------------------

def _generar_codigo_ticket() -> str:
    """GENERA UN TOKEN UNICO PARA EL TICKET DE CANJE (de 16 chars alfanumericos)."""
    return secrets.token_hex(8).upper()

def _crear_ticket(db: Session, user: models.User, promo: models.Promotion) -> models.RedemptionTicket:
    """CREA Y PERSISTE UN TICKET DE CANJE CON SU QR DATA Y OBSERVACIONES."""
    codigo = _generar_codigo_ticket()
    qr_data = f"AUTOPASS_REDEMPTION|ID:{codigo}"

    observacion = None
    if promo.tipo_canje == "voucher":
        observacion = "Este beneficio será válido por 30 días desde la fecha de emisión."

    ticket = models.RedemptionTicket(
        user_id=user.id,
        promotion_id=promo.id,
        codigo=codigo,
        titulo=promo.titulo,
        descripcion=promo.descripcion,
        tipo_canje=promo.tipo_canje or "voucher",
        valor_descuento=promo.valor_descuento if promo.tipo_canje == "descuento_reserva" else None,
        icono=promo.icono or "fas fa-gift",
        sucursal=promo.sucursal,
        estado="VIGENTE",
        qr_data=qr_data,
        observacion=observacion,
        created_at=datetime.datetime.now().isoformat(),
    )
    db.add(ticket)
    db.flush()  # PARA OBTENER EL ID
    # INCLUIR EL ID EN EL CONTENIDO DEL QR PARA REFERENCIA HUMANA
    ticket.qr_data = f"AUTOPASS_REDEMPTION|ID:{codigo}|TICKET:{ticket.id}"
    return ticket

@router.get("/promotions", response_model=List[schemas.PromotionResponse])
def get_promotions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """LISTA LAS PROMOCIONES Y BENEFICIOS VIGENTES FILTRADOS POR LA SEDE DEL USUARIO."""
    q = db.query(models.Promotion).filter(models.Promotion.activa == True)
    
    if current_user.sucursal:
        q = q.filter(or_(models.Promotion.sucursal == current_user.sucursal, models.Promotion.sucursal == None))
        
    return q.all()

@router.post("/redeem/{promo_id}")
def redeem_points(promo_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """PROCESA EL CANJE DE PUNTOS POR UN BENEFICIO DEL CATALOGO.
    - tipo_canje == 'descuento_reserva': genera un descuento (%) aplicable al pagar una reserva de su sucursal.
    - tipo_canje == 'voucher': genera un ticket con QR persistente (válido por 30 días), sin validación automática."""
    promo = db.query(models.Promotion).filter(models.Promotion.id == promo_id, models.Promotion.activa == True).first()
    if not promo: raise HTTPException(status_code=404, detail="Promoción no encontrada")
    if current_user.puntos_acumulados < promo.costo_puntos: raise HTTPException(status_code=400, detail="Puntos insuficientes")

    current_user.puntos_acumulados -= promo.costo_puntos
    db.add(models.PointsLog(user_id=current_user.id, cantidad=-promo.costo_puntos, motivo=f"Canje: {promo.titulo}", fecha=datetime.datetime.now().isoformat()))

    ticket = _crear_ticket(db, current_user, promo)

    try:
        from services.user_notification_service import UserNotificationService
        UserNotificationService.create_notification(
            db, current_user.id,
            tipo=models.NotificationType.PROMO_REDEEMED,
            titulo="¡Canje exitoso!",
            mensaje=f"Canjeaste {promo.costo_puntos} puntos por '{promo.titulo}' (Voucher #{ticket.id}). Tu beneficio ya está disponible en Mis Puntos."
        )
    except Exception:
        pass

    db.commit()
    db.refresh(ticket)

    result = {
        "status": "ok",
        "message": f"Canje exitoso: {promo.titulo}",
        "tipo_canje": promo.tipo_canje,
        "ticket": schemas.RedemptionTicketResponse.model_validate(ticket)
    }
    return result

@router.post("/points-adjust")
def adjust_points(delta: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """SUMAR O RESTAR PUNTOS AL USUARIO (SOLO PARA PRUEBAS). delta = +10 o -10.
    Registra el movimiento en el historial de puntos."""
    if delta == 0:
        raise HTTPException(status_code=400, detail="Delta no puede ser cero")
    if current_user.puntos_acumulados + delta < 0:
        raise HTTPException(status_code=400, detail="No podés tener puntos negativos")

    current_user.puntos_acumulados += delta
    db.add(models.PointsLog(
        user_id=current_user.id,
        cantidad=delta,
        motivo="Ajuste manual de prueba",
        fecha=datetime.datetime.now().isoformat()
    ))
    db.commit()
    return {"status": "ok", "puntos_acumulados": current_user.puntos_acumulados}

@router.get("/redemption-tickets", response_model=List[schemas.RedemptionTicketResponse])
def get_user_redemption_tickets(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """LISTA LOS TICKETS/VOUCHERS DE CANJE DEL USUARIO."""
    return db.query(models.RedemptionTicket).filter(
        models.RedemptionTicket.user_id == current_user.id
    ).order_by(models.RedemptionTicket.id.desc()).all()

@router.get("/redemptions/available")
def get_available_redemptions(sucursal: str = None, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """LISTA LOS DESCUENTOS DE RESERVA (%). CANJEADOS Y AUN VIGENTES, APLICABLES A UNA SUCURSAL."""
    q = db.query(models.RedemptionTicket).filter(
        models.RedemptionTicket.user_id == current_user.id,
        models.RedemptionTicket.tipo_canje == "descuento_reserva",
        models.RedemptionTicket.estado == "VIGENTE"
    )
    if sucursal:
        # SE PUEDE APLICAR SI ES DE ESA SUCURSAL O ES GLOBAL (con tolerancia a prefijo 'AUTOPASS')
        from services.reservation_service import ReservationService
        q = q.filter(ReservationService.redemption_sucursal_clause(sucursal))
    return q.all()

@router.post("/redemptions/{ticket_id}/cancel")
def cancel_redemption_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """CANCELA UN TICKET/USADO NO USADO Y DEVUELVE LOS PUNTOS AL USUARIO."""
    ticket = db.query(models.RedemptionTicket).filter(
        models.RedemptionTicket.id == ticket_id,
        models.RedemptionTicket.user_id == current_user.id
    ).first()
    if not ticket: raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket.estado != "VIGENTE": raise HTTPException(status_code=400, detail="El ticket ya no se encuentra vigente")

    promo = db.query(models.Promotion).filter(models.Promotion.id == ticket.promotion_id).first() if ticket.promotion_id else None
    costo = promo.costo_puntos if promo else 0

    ticket.estado = "CANCELADO"
    if costo > 0:
        current_user.puntos_acumulados += costo
        db.add(models.PointsLog(user_id=current_user.id, cantidad=costo, motivo=f"Anulación de canje: {ticket.titulo}", fecha=datetime.datetime.now().isoformat()))

    try:
        from services.user_notification_service import UserNotificationService
        UserNotificationService.create_notification(
            db, current_user.id,
            tipo=models.NotificationType.PROMO_CANCELLED,
            titulo="Canje cancelado",
            mensaje=f"Se canceló tu beneficio '{ticket.titulo}' y se te reintegraron {costo} puntos a tu cuenta."
        )
    except Exception:
        pass

    db.commit()
    return {"status": "ok", "message": "Ticket cancelado y puntos devueltos", "puntos_devueltos": costo}

@router.get("/points-history")
def get_points_history(page: int = 1, limit: int = 10, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """RETORNA EL HISTORIAL DE MOVIMIENTOS DE PUNTOS DEL USUARIO CON PAGINACION Y TOTALES."""
    query = db.query(models.PointsLog).filter(models.PointsLog.user_id == current_user.id)
    total = query.count()
    
    earned = db.query(func.sum(models.PointsLog.cantidad)).filter(
        models.PointsLog.user_id == current_user.id,
        models.PointsLog.cantidad > 0
    ).scalar() or 0
    
    redeemed = db.query(func.sum(models.PointsLog.cantidad)).filter(
        models.PointsLog.user_id == current_user.id,
        models.PointsLog.cantidad < 0
    ).scalar() or 0

    items = query.order_by(models.PointsLog.id.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if total > 0 else 1,
        "total_earned": int(earned),
        "total_redeemed": abs(int(redeemed))
    }
