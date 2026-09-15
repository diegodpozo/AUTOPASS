import re
import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import models, schemas
from models.enums import PaymentStatus
from core.database import get_db
from core.security import get_operational_user
from core.normalize import format_plate
from services.reservation_service import ReservationService, verificar_disponibilidad
from services.user_notification_service import UserNotificationService
from services.billing_service import BillingService
from services.branch_service import BranchService

router = APIRouter()

@router.get("/reservations/patente-lookup")
def patente_lookup(patente: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """BUSCA SI UNA PATENTE ESTA REGISTRADA A UN USUARIO PARA VINCULARLA A UNA RESERVA MANUAL."""
    norm = re.sub(r'[^A-Z0-9]', '', (patente or '').upper())
    if len(norm) < 4:
        return {"encontrado": False, "patente": patente}

    vehicle = (
        db.query(models.Vehicle)
        .join(models.User, models.User.id == models.Vehicle.user_id)
        .filter(
            func.replace(func.upper(models.Vehicle.patente), ' ', '') == norm,
            models.User.is_deleted == False
        )
        .first()
    )
    if not vehicle or not vehicle.owner:
        return {"encontrado": False, "patente": patente}

    owner = vehicle.owner
    return {
        "encontrado": True,
        "user_id": owner.id,
        "nombre": owner.nombre,
        "apellido": owner.apellido,
        "email": owner.email,
        "tipo_vehiculo": vehicle.tipo or "Auto",
        "marca_modelo": vehicle.marca_modelo or ""
    }

@router.get("/reservations/new-count")
def get_new_reservations_count(
    since_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    staff: models.User = Depends(get_operational_user)
):
    """RETORNA LA CANTIDAD DE RESERVAS NUEVAS DESDE since_id Y EL ULTIMO ID REGISTRADO.
    Alimenta la burbuja de notificación en la pestaña de Reservas del Dashboard."""
    q = db.query(models.Reservation)
    if staff.rol != "admin":
        staff_suc = staff.sucursal or ""
        norm_col = func.trim(func.replace(func.lower(models.Reservation.sucursal_nombre), 'autopass ', ''))
        norm_staff = staff_suc.lower().replace('autopass ', '').strip()
        q = q.filter((models.Reservation.sucursal_nombre == staff_suc) | (norm_col == norm_staff))
    
    latest_id = q.with_entities(func.max(models.Reservation.id)).scalar() or 0
    
    count = 0
    if since_id is not None:
        count = q.filter(models.Reservation.id > since_id).count()
        
    return {
        "count": count,
        "latest_id": latest_id
    }

@router.get("/reservations", response_model=List[schemas.UserReservationResponse])
def list_reservations(estado: Optional[str] = Query(None), sucursal: Optional[str] = Query(None), db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """LISTA TODAS LAS RESERVAS. LOS LOCALES SOLO VEN LAS DE SU SEDE."""
    ReservationService.cleanup_overdue_reservations(db)
    
    q = db.query(models.Reservation)

    if estado:
        q = q.filter(models.Reservation.estado_reserva == estado)
    
    if staff.rol != "admin":
        sucursal = staff.sucursal
        q = q.filter(models.Reservation.sucursal_nombre == sucursal)
    elif sucursal:
        q = q.filter(models.Reservation.sucursal_nombre == sucursal)
        
    results = q.order_by(models.Reservation.id.desc()).all()
    
    en_predio = ReservationService.get_en_predio_ids(db, [r.id for r in results])
    
    out = []
    for r in results:
        d = schemas.UserReservationResponse.model_validate(r)
        d.en_predio = r.id in en_predio
        if r.user:
            d.usuario_nombre = r.user.nombre
            d.usuario_apellido = r.user.apellido
            d.user_name = f"{r.user.nombre} {r.user.apellido}"
            d.user_email = r.user.email
        if r.cliente_nombre:
            d.user_name = r.cliente_nombre
            parts = r.cliente_nombre.split(' ', 1)
            d.usuario_nombre = parts[0]
            d.usuario_apellido = parts[1] if len(parts) > 1 else ""
            
        out.append(d)
    return out

@router.post("/reservations")
def create_admin_reservation(data: schemas.AdminReservationCreate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """PERMITE AL ADMINISTRADOR O EMPLEADO CREAR UNA RESERVA MANUAL."""
    data.patente = format_plate(data.patente)
    if staff.rol != "admin":
        data.sucursal_nombre = staff.sucursal

    vehicle = None
    if data.user_id:
        user = db.query(models.User).filter(models.User.id == data.user_id, models.User.is_deleted == False).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        vehicle = db.query(models.Vehicle).filter(
            models.Vehicle.user_id == data.user_id,
            func.replace(func.upper(models.Vehicle.patente), ' ', '') == re.sub(r'[^A-Z0-9]', '', data.patente.upper())
        ).first()
        if not vehicle:
            raise HTTPException(status_code=400, detail="La patente no está vinculada a ese usuario")

    # VERIFICAR DISPONIBILIDAD
    tipo_v = data.tipo_vehiculo or (vehicle.tipo if vehicle else "Auto")
    disp = verificar_disponibilidad(db, data.sucursal_nombre, data.fecha_inicio, data.fecha_fin, tipo_vehiculo=tipo_v)
    if not disp["disponible"]:
        raise HTTPException(status_code=400, detail=disp["mensaje"])

    try:
        new_res = ReservationService.create_reservation(db, data)
        if data.pagar:
            result = ReservationService.pay_reservation_manual(db, new_res, data.metodo_pago, data.redemption_ticket_id)
        else:
            result = None
        if new_res.user_id:
            UserNotificationService.create_notification(
                db, user_id=new_res.user_id,
                tipo=models.NotificationType.RESERVATION_CREATED_ADMIN,
                titulo="Reserva creada por administrador",
                mensaje=f"Se creó una reserva para {new_res.patente} el {new_res.fecha_inicio} en {new_res.sucursal_nombre}.",
                reserva_id=new_res.id
            )
        return {"status": "ok", "id": new_res.id, "monto": new_res.monto_total, "pagado": bool(data.pagar), "metodo_pago": data.metodo_pago, "descuento": (result or {}).get("descuento", 0.0), "monto_a_cobrar": (result or {}).get("monto_a_cobrar", new_res.monto_total)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/reservations/{res_id}")
def update_admin_reservation(res_id: int, data: schemas.AdminReservationCreate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """EDITA UNA RESERVA CREADA POR ADMINISTRADOR O EMPLEADO (NO LAS CREADAS POR CLIENTES)."""
    data.patente = format_plate(data.patente)
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    if (getattr(reserva, "origen", None) or "cliente") != "manual":
        raise HTTPException(status_code=400, detail="Solo se pueden editar reservas creadas por administración o empleados")

    if reserva.estado_reserva in ("Completada", "Cancelada"):
        raise HTTPException(status_code=400, detail="No se puede editar una reserva completada o cancelada")

    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")

    if staff.rol != "admin":
        data.sucursal_nombre = staff.sucursal

    if data.fecha_fin <= data.fecha_inicio:
        raise HTTPException(status_code=400, detail="La fecha de fin debe ser posterior a la de inicio")

    vehicle = None
    if data.user_id:
        user = db.query(models.User).filter(models.User.id == data.user_id, models.User.is_deleted == False).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        vehicle = db.query(models.Vehicle).filter(
            models.Vehicle.user_id == data.user_id,
            func.replace(func.upper(models.Vehicle.patente), ' ', '') == re.sub(r'[^A-Z0-9]', '', data.patente.upper())
        ).first()
        if not vehicle:
            raise HTTPException(status_code=400, detail="La patente no está vinculada a ese usuario")

    # SI LA EDICION NO ENVIA USER_ID PERO LA PATENTE SIGUE SIENDO DEL USUARIO
    # YA VINCULADO, CONSERVAR EL VINCULO (EVITA DESVINCULACION ACCIDENTAL)
    vinculo_final = None
    if data.user_id:
        vinculo_final = data.user_id
    elif reserva.user_id:
        sigue_vinculada = db.query(models.Vehicle.id).filter(
            models.Vehicle.user_id == reserva.user_id,
            func.replace(func.upper(models.Vehicle.patente), ' ', '') == re.sub(r'[^A-Z0-9]', '', data.patente.upper())
        ).first()
        vinculo_final = reserva.user_id if sigue_vinculada else None

    tipo_v = data.tipo_vehiculo or (vehicle.tipo if vehicle else "Auto")
    tipo_v_str = tipo_v.value if hasattr(tipo_v, "value") else str(tipo_v)

    # VERIFICAR DISPONIBILIDAD EXCLUYENDO LA PROPIA RESERVA
    disp = verificar_disponibilidad(db, data.sucursal_nombre, data.fecha_inicio, data.fecha_fin, exclude_id=res_id, tipo_vehiculo=tipo_v_str)
    if not disp["disponible"]:
        raise HTTPException(status_code=400, detail=disp["mensaje"])

    try:
        monto = BillingService.calculate_total_amount(
            db, data.tipo_estadia, data.fecha_inicio, data.fecha_fin,
            sucursal=data.sucursal_nombre, tipo_vehiculo=tipo_v_str
        )
        # SI LA RESERVA SE PAGÓ CON UN DESCUENTO DE CANJE EN CAJA, MANTENER ESE DESCUENTO
        # AL RECALCULAR EL MONTO (EL MONTO ACTUAL YA ES EL VALOR DESCONTADO).
        ticket_aplicado = None
        if reserva.estado_pago == PaymentStatus.PAGADO:
            ticket_aplicado = db.query(models.RedemptionTicket).filter(
                models.RedemptionTicket.reserva_id == reserva.id,
                models.RedemptionTicket.tipo_canje == "descuento_reserva",
                models.RedemptionTicket.estado == "USADO"
            ).first()
        if ticket_aplicado and ticket_aplicado.valor_descuento:
            porc = ticket_aplicado.valor_descuento
            monto = round(monto * (1 - porc / 100.0), 2)
        monto_anterior = reserva.monto_total or 0.0
        reembolsado_previo = reserva.monto_reembolsado or 0.0
        valor_actual = round(monto_anterior - reembolsado_previo, 2)
        diferencia = round(monto - valor_actual, 2)

        reserva.patente = data.patente
        reserva.fecha_inicio = data.fecha_inicio
        reserva.fecha_fin = data.fecha_fin
        reserva.tipo_estadia = data.tipo_estadia
        reserva.tipo_vehiculo = tipo_v_str
        reserva.sucursal_nombre = data.sucursal_nombre
        reserva.sucursal_info = BranchService.get_branch_info_str(db, data.sucursal_nombre)
        reserva.cliente_nombre = data.cliente_nombre
        reserva.user_id = vinculo_final

        accion = "sin_cambio"
        metodo_ajuste = None
        if reserva.estado_pago == "Pagado":
            if diferencia > 0:
                # COBRAR DIFERENCIA: EL MONTO ACUMULADO SUBE
                accion = "cobro"
                metodo_ajuste = data.cobrar_diferencia_metodo
                reserva.monto_total = round(monto_anterior + diferencia, 2)
                if metodo_ajuste:
                    reserva.metodo_pago = metodo_ajuste
                reserva.fecha_pago = datetime.datetime.now().isoformat()
            elif diferencia < 0:
                # REEMBOLSAR DIFERENCIA: SE ACUMULA EN MONTO_REEMBOLSADO
                accion = "reembolso"
                metodo_ajuste = data.reembolsar_diferencia_metodo
                if not metodo_ajuste:
                    metodo_ajuste = reserva.metodo_pago or "Saldo"
                reembolso = round(abs(diferencia), 2)
                reserva.monto_reembolsado = round(reembolsado_previo + reembolso, 2)
                # MONTO TOTAL QUEDA COMO "ACUMULADO COBRADO"; EL NETO SURGE DE RESTAR REEMBOLSOS
                reserva.metodo_pago = metodo_ajuste
                reserva.fecha_pago = datetime.datetime.now().isoformat()
                # CANAL DE LA DEVOLUCIÓN: SOLO SALDO/BILLETERA ACREDITA AL SALDO VIRTUAL.
                # CAJA/EFECTIVO Y OTROS CANALES = DEVOLUCIÓN POR FUERA DEL SISTEMA (BILETES/TRANSFERENCIA),
                # SIN tocar el saldo; en el reporte financiero la baja queda imputada al método elegido.
                norm_metodo = re.sub(r'[^A-Z]', '', str(metodo_ajuste).upper())
                devolucion_a_saldo = norm_metodo in ("SALDO", "DIGITAL", "BILLETERA", "BILLETERAAUTOPASS")
                if devolucion_a_saldo and reserva.user_id and reserva.user:
                    reserva.user.saldo += reembolso
                    puntos_desc = BillingService.calculate_points(reembolso)
                    reserva.user.puntos_acumulados = max(0, reserva.user.puntos_acumulados - puntos_desc)
                    db.add(models.PointsLog(
                        user_id=reserva.user_id,
                        cantidad=-puntos_desc,
                        motivo=f"Reembolso por Edición de Reserva: {reserva.patente}",
                        fecha=datetime.datetime.now().isoformat()
                    ))
            else:
                reserva.monto_total = monto
        else:
            reserva.monto_total = monto

        # SOLO SE PUEDE AJUSTAR EL METODO DE PAGO MIENTRAS LA RESERVA ESTA SIN PAGAR
        if data.metodo_pago and reserva.estado_pago == "Pendiente":
            reserva.metodo_pago = data.metodo_pago
        db.commit()
        db.refresh(reserva)
        if reserva.user_id and reserva.user:
            if accion == "cobro":
                UserNotificationService.create_notification(
                    db, user_id=reserva.user_id,
                    tipo=models.NotificationType.RESERVATION_MODIFIED,
                    titulo="Reserva modificada por administrador",
                    mensaje=f"Tu reserva para {reserva.patente} fue actualizada. Se registró un cobro de ${diferencia:,.2f} por la diferencia ({metodo_ajuste or 'Caja'}).",
                    reserva_id=reserva.id
                )
            elif accion == "reembolso":
                UserNotificationService.create_notification(
                    db, user_id=reserva.user_id,
                    tipo=models.NotificationType.RESERVATION_MODIFIED,
                    titulo="Reserva modificada por administrador",
                    mensaje=(f"Tu reserva para {reserva.patente} fue actualizada. Se te reembolsaron ${abs(diferencia):,.2f} a tu saldo."
                             if devolucion_a_saldo
                             else f"Tu reserva para {reserva.patente} fue actualizada. Se te devolvieron ${abs(diferencia):,.2f} en efectivo."),
                    reserva_id=reserva.id
                )
            else:
                UserNotificationService.create_notification(
                    db, user_id=reserva.user_id,
                    tipo=models.NotificationType.RESERVATION_MODIFIED,
                    titulo="Reserva modificada por administrador",
                    mensaje=f"Tu reserva para {reserva.patente} fue actualizada: del {reserva.fecha_inicio} al {reserva.fecha_fin} en {reserva.sucursal_nombre}.",
                    reserva_id=reserva.id
                )
        return {
            "status": "ok",
            "id": reserva.id,
            "monto": reserva.monto_total,
            "monto_anterior": monto_anterior,
            "diferencia": diferencia,
            "accion": accion,
            "metodo_pago": metodo_ajuste or reserva.metodo_pago,
            "reembolsado_total": reserva.monto_reembolsado or 0.0
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reservations/{res_id}/confirm-payment")
def confirm_reservation_payment(res_id: int, data: schemas.ConfirmPaymentRequest = None, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """CONFIRMACION MANUAL DE PAGO."""
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
    
    metodo = (data.metodo_pago if data else None) or "Caja"
    redemption_ticket_id = (data.redemption_ticket_id if data else None)
    result = ReservationService.pay_reservation_manual(db, reserva, metodo, redemption_ticket_id)

    if reserva.user:
        UserNotificationService.create_notification(
            db, user_id=reserva.user.id,
            tipo=models.NotificationType.RESERVATION_CONFIRMED,
            titulo="Pago confirmado",
            mensaje=f"El pago de tu reserva #{res_id} ({reserva.patente}) fue confirmado por administrador.",
            reserva_id=res_id
        )

    return {"status": "ok", "message": result["message"], "monto": result["monto"], "descuento": result["descuento"], "monto_a_cobrar": result["monto_a_cobrar"]}

@router.post("/reservations/{res_id}/cancel")
def cancel_reservation_admin(res_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """CANCELACION MANUAL."""
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva: raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
        
    result = ReservationService.cancel_reservation(db, None, res_id)
    if result["status"] == "ok":
        return result
    raise HTTPException(status_code=400, detail=result["message"])


@router.get("/reservations/{res_id}/redemptions")
def reservation_available_redemptions(res_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """LISTA LOS DESCUENTOS DE RESERVA (%) VIGENTES DEL USUARIO VINCULADO A UNA RESERVA Y APLICABLES A SU SUCURSAL.
    Se usa antes de registrar un pago en caja para informar y aplicar el descuento."""
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")

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
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")

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


