import datetime 
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from core.database import get_db
from core.security import get_operational_user
from services.user_notification_service import UserNotificationService

router = APIRouter()

@router.post("/open-barrier")
def open_barrier(gate_id: str, command: str = "OPEN", db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user), request: Request = None):
    """ENVIA UN COMANDO DE APERTURA O CIERRE DE BARRERA VIA MQTT Y SERIAL (ARDUINO)."""
    from services.hardware_service import HardwareService
    res = HardwareService.trigger_barrier(
        gate_id=gate_id,
        command=command,
        method="MANUAL_OP",
        details={"staff_id": staff.id, "sucursal": staff.sucursal},
        request=request
    )
    return {"status": "ok", "message": f"Comando {command} enviado a barrera {gate_id} ({staff.sucursal or 'Global'})", "data": res}

@router.post("/manual-entry")
def manual_entry(plate: str, tipo_vehiculo: str = "Auto", floor_id: int = None, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """REGISTRA UN INGRESO FORZADO AL PREDIO DE LA SEDE."""
    from routes.parking import normalize_plate
    from models.enums import PaymentStatus, ReservationStatus
    from services.time_service import TimeService
    p = normalize_plate(plate)
    now = TimeService.now()
    sucursal = staff.sucursal
    
    # Buscar la última ENTRADA y verificar si el vehículo sigue adentro
    ultima_entrada = db.query(models.AccessLog).filter(
        func.replace(func.upper(models.AccessLog.patente_detectada), ' ', '') == p,
        models.AccessLog.tipo_evento == "ENTRADA",
        models.AccessLog.sucursal == sucursal
    ).order_by(models.AccessLog.id.desc()).first()
    
    if ultima_entrada:
        tiene_salida = db.query(models.AccessLog.id).filter(
            models.AccessLog.patente_detectada == ultima_entrada.patente_detectada,
            models.AccessLog.tipo_evento == "SALIDA",
            models.AccessLog.id > ultima_entrada.id,
            models.AccessLog.sucursal == sucursal
        ).first()
        if not tiene_salida:
            return {"status": "ok", "message": "El vehículo ya figura como ingresado en esta sede; se reutilizó el registro", "access_log_id": ultima_entrada.id}
    
    # Buscar reserva activa y pagada para esta patente/sucursal
    now_str = now.strftime("%Y-%m-%d %H:%M")
    reserva = db.query(models.Reservation).filter(
        func.replace(func.upper(models.Reservation.patente), ' ', '') == p,
        models.Reservation.estado_pago == PaymentStatus.PAGADO,
        models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA]),
        models.Reservation.fecha_inicio <= now_str,
        models.Reservation.fecha_fin >= now_str
    ).filter((models.Reservation.sucursal_nombre == sucursal) | (models.Reservation.sucursal_nombre == None)).first()

    # MANEJO DE PISOS
    floor = None
    if floor_id:
        floor = db.query(models.ParkingFloor).filter(models.ParkingFloor.id == floor_id).first()
        if not floor: raise HTTPException(status_code=404, detail="Piso no encontrado")
        
        if tipo_vehiculo == "Auto":
            floor.ocupacion_actual += 1
        elif tipo_vehiculo == "Camioneta":
            floor.ocupacion_camionetas += 1
        else:
            floor.ocupacion_motos += 1
    else:
        #FALLBACK UN AFORO GLOBAL DE SEDE SI NO HAY PISOS
        aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
        if not aforo:
            aforo = models.ParkingAforo(sucursal=sucursal, capacidad_total=20, ocupacion_actual=0, capacidad_motos=10, ocupacion_motos=0)
            db.add(aforo)
        
        if tipo_vehiculo == "Auto":
            aforo.ocupacion_actual += 1
        elif tipo_vehiculo == "Camioneta":
            aforo.ocupacion_camionetas += 1
        else:
            aforo.ocupacion_motos += 1

    db.add(models.AccessLog(
        patente_detectada=p, 
        normalized_patente=p,
        tipo_evento="ENTRADA", 
        tipo_vehiculo=tipo_vehiculo, 
        fecha_hora=now.isoformat(), 
        sucursal=sucursal,
        floor_id=floor_id,
        reserva_id=reserva.id if reserva else None,
        pago_confirmado=True if reserva and reserva.estado_pago == PaymentStatus.PAGADO else False
    ))
    db.commit()
    # Notificar cambio de aforo para actualizar dashboards
    try:
        from services.notification_service import NotificationService
        from services.access_service import normalize_name as _normalize_name
        from services.hardware_service import HardwareService
        norm = _normalize_name(sucursal)
        print(f"[ADMIN OPS] Notificando cambio de aforo (manual entry) para sucursal={sucursal} norm={norm}")
        NotificationService.notify_occupancy_change(db, norm)
        HardwareService.trigger_barrier("ENTRADA", "OPEN", method="MANUAL_ENTRY", details={"plate": p, "sucursal": sucursal}, request=request)
    except Exception as e:
        print(f"[ADMIN OPS] Error notifying occupancy/hardware: {e}")
    return {"status": "ok", "message": f"Ingreso manual registrado en {floor.nombre if floor else 'Planta Baja'}: {p} ({tipo_vehiculo})"}

@router.post("/manual-exit")
def manual_exit(plate: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user), request: Request = None):
    """REGISTRA UNA SALIDA MANUAL DE LA SEDE."""
    from routes.parking import normalize_plate
    from services.time_service import TimeService
    p = normalize_plate(plate)
    sucursal = staff.sucursal
    
    ultimo = db.query(models.AccessLog).filter(
        func.replace(func.upper(models.AccessLog.patente_detectada), ' ', '') == p,
        models.AccessLog.sucursal == sucursal
    ).order_by(models.AccessLog.id.desc()).first()
    
    if not ultimo or ultimo.tipo_evento != "ENTRADA":
        raise HTTPException(status_code=400, detail="El vehículo no figura en esta sede")
    
    fecha_str = ultimo.fecha_hora.replace(' ', 'T')
    entrada_dt = datetime.datetime.fromisoformat(fecha_str)
    minutos_transcurridos = (TimeService.now() - entrada_dt).total_seconds() / 60
    dentro_cortesia = minutos_transcurridos <= 10
    
    if not ultimo.pago_confirmado and not dentro_cortesia:
        raise HTTPException(status_code=403, detail=f"DEUDA PENDIENTE en esta sede. Cortesía: 10 min, transcurridos: {int(minutos_transcurridos)} min")
    
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
    if aforo:
        if ultimo.tipo_vehiculo == "Auto" and aforo.ocupacion_actual > 0:
            aforo.ocupacion_actual -= 1
        elif ultimo.tipo_vehiculo == "Camioneta" and aforo.ocupacion_camionetas > 0:
            aforo.ocupacion_camionetas -= 1
        elif ultimo.tipo_vehiculo == "Moto" and aforo.ocupacion_motos > 0:
            aforo.ocupacion_motos -= 1

    if ultimo.floor_id:
        floor = db.query(models.ParkingFloor).filter(models.ParkingFloor.id == ultimo.floor_id).first()
        if floor:
            if ultimo.tipo_vehiculo == "Auto" and (floor.ocupacion_actual or 0) > 0:
                floor.ocupacion_actual -= 1
            elif ultimo.tipo_vehiculo == "Camioneta" and (floor.ocupacion_camionetas or 0) > 0:
                floor.ocupacion_camionetas -= 1
            elif ultimo.tipo_vehiculo == "Moto" and (floor.ocupacion_motos or 0) > 0:
                floor.ocupacion_motos -= 1

    db.add(models.AccessLog(
        patente_detectada=p, 
        normalized_patente=p,
        tipo_evento="SALIDA", 
        tipo_vehiculo=ultimo.tipo_vehiculo, 
        fecha_hora=TimeService.now().isoformat(), 
        pago_confirmado=True, 
        costo_estadia=0.0 if dentro_cortesia else None,
        metodo_pago="CAJA" if not dentro_cortesia else None,
        sucursal=sucursal,
        floor_id=ultimo.floor_id
    ))
    db.commit()
    try:
        from services.notification_service import NotificationService
        from services.access_service import normalize_name as _normalize_name
        from services.hardware_service import HardwareService
        norm = _normalize_name(sucursal)
        print(f"[ADMIN OPS] Notificando cambio de aforo (manual exit) para sucursal={sucursal} norm={norm}")
        NotificationService.notify_occupancy_change(db, norm)
        HardwareService.trigger_barrier("SALIDA", "OPEN", method="MANUAL_EXIT", details={"plate": p, "sucursal": sucursal}, request=request)
    except Exception as e:
        print(f"[ADMIN OPS] Error notifying occupancy/hardware: {e}")

    msg = f"Salida manual registrada en {sucursal or 'Global'}: {p}" + (" (Cortesía)" if dentro_cortesia else "")
    return {"status": "ok", "message": msg}

@router.post("/cancel-stay")
def cancel_stay(plate: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """CANCELA UNA ESTADIA ACTUAL. SI ESTA DENTRO DE LOS 10 MIN DE CORTESIA, NO COBRA."""
    from routes.parking import normalize_plate
    from services.time_service import TimeService
    p = normalize_plate(plate)
    sucursal = staff.sucursal
    
    ultimo = db.query(models.AccessLog).filter(
        func.replace(func.upper(models.AccessLog.patente_detectada), ' ', '') == p,
        models.AccessLog.sucursal == sucursal
    ).order_by(models.AccessLog.id.desc()).first()
    
    if not ultimo or ultimo.tipo_evento != "ENTRADA":
        raise HTTPException(status_code=400, detail="El vehículo no figura como ingresado")
    
    # VERIFICAR CORTESIA (10 MINUTOS)
    fecha_str = ultimo.fecha_hora.replace(' ', 'T')
    entrada_dt = datetime.datetime.fromisoformat(fecha_str)
    minutos_transcurridos = (TimeService.now() - entrada_dt).total_seconds() / 60
    
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
    if (aforo):
        if (ultimo.tipo_vehiculo == "Auto" and aforo.ocupacion_actual > 0):
            aforo.ocupacion_actual -= 1
        elif (ultimo.tipo_vehiculo == "Camioneta" and aforo.ocupacion_camionetas > 0):
            aforo.ocupacion_camionetas -= 1
        elif (ultimo.tipo_vehiculo == "Moto" and aforo.ocupacion_motos > 0):
            aforo.ocupacion_motos -= 1

    if ultimo.floor_id:
        floor = db.query(models.ParkingFloor).filter(models.ParkingFloor.id == ultimo.floor_id).first()
        if floor:
            if ultimo.tipo_vehiculo == "Auto" and (floor.ocupacion_actual or 0) > 0:
                floor.ocupacion_actual -= 1
            elif ultimo.tipo_vehiculo == "Camioneta" and (floor.ocupacion_camionetas or 0) > 0:
                floor.ocupacion_camionetas -= 1
            elif ultimo.tipo_vehiculo == "Moto" and (floor.ocupacion_motos or 0) > 0:
                floor.ocupacion_motos -= 1
    
    if (minutos_transcurridos <= 10):
        # CORTESIA: SALIDA SIN CARGO
        db.add(models.AccessLog(
            patente_detectada=p, 
            normalized_patente=p,
            tipo_evento="SALIDA", 
            tipo_vehiculo=ultimo.tipo_vehiculo,
            fecha_hora=TimeService.now().isoformat(), 
            pago_confirmado=True, 
            costo_estadia=0.0,
            sucursal=sucursal
        ))
        msg = f"Estadía cancelada (Cortesía: {int(minutos_transcurridos)} min). Sin cargo."
    else:
        # EXCEDIO CORTESIA: SE DEBE COBRAR
        if (not ultimo.pago_confirmado):
            from services.billing_service import BillingService
            monto = BillingService.calculate_debt(ultimo.fecha_hora, db, sucursal=sucursal, tipo_vehiculo=ultimo.tipo_vehiculo)
            raise HTTPException(status_code=402, detail=f"Excedió cortesía ({int(minutos_transcurridos)} min). Debe abonar ${monto}")
        
        # SI YA PAGO, REGISTRAMOS SALIDA NORMAL
        db.add(models.AccessLog(
            patente_detectada=p, 
            normalized_patente=p,
            tipo_evento="SALIDA", 
            tipo_vehiculo=ultimo.tipo_vehiculo,
            fecha_hora=TimeService.now().isoformat(), 
            pago_confirmado=True, 
            sucursal=sucursal
        ))
        msg = "Salida registrada con éxito."

    db.commit()

    # NOTIFICAR AL PROPIETARIO DEL VEHICULO SI ES USUARIO REGISTRADO
    try:
        vehicle = db.query(models.Vehicle).filter(
            func.replace(func.upper(models.Vehicle.patente), ' ', '') == p
        ).first()
        if vehicle and vehicle.user_id:
            owner = db.query(models.User).filter(models.User.id == vehicle.user_id).first()
            if owner and owner.rol == models.enums.UserRole.USER:
                UserNotificationService.create_notification(
                    db, user_id=owner.id,
                    tipo="estadia_cancelada_admin",
                    titulo="Estadía cancelada",
                    mensaje=f"Un administrador canceló tu estadía en {sucursal} para la patente {plate}."
                )
    except Exception:
        pass

    return {"status": "ok", "message": msg}
