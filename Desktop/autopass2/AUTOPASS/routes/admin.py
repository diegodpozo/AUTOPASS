import datetime
import math
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/v1", tags=["Admin & Settings"])

# --- GESTIÓN DE USUARIOS (Solo Admin) ---

@router.get("/admin/users")
def list_users(db: Session = Depends(get_db), admin: models.User = Depends(auth.get_local_manager)):
    """Retorna la lista de usuarios. Los administradores locales solo ven a los de su sede."""
    q = db.query(models.User)
    if admin.rol != "admin":
        q = q.filter(models.User.sucursal == admin.sucursal)
    return q.all()

@router.post("/admin/users")
def create_user_admin(user_data: schemas.UserCreate, rol: str = "user", db: Session = Depends(get_db), admin: models.User = Depends(auth.get_local_manager)):
    """Permite al administrador crear un nuevo usuario. Los locales solo crean para su sede."""
    from routes.parking import normalize_name, normalize_dni
    
    # Restricción de rol
    if admin.rol != "admin":
        if rol == "admin": raise HTTPException(status_code=403, detail="No podés crear un Administrador Global")
        user_data.sucursal = admin.sucursal # Forzar sucursal del creador
    
    # Verificar si el email ya existe
    existing = db.query(models.User).filter(models.User.email == user_data.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    if rol not in ["admin", "local_admin", "staff", "user"]:
        raise HTTPException(status_code=400, detail="Rol no válido")

    new_user = models.User(
        nombre=normalize_name(user_data.nombre),
        apellido=normalize_name(user_data.apellido),
        dni=normalize_dni(user_data.dni),
        telefono=user_data.telefono,
        email=user_data.email.lower().strip(),
        password_hash=auth.get_password_hash(user_data.password),
        rol=rol,
        sucursal=user_data.sucursal
    )
    
    db.add(new_user)
    db.commit()
    return {"status": "ok", "message": f"Usuario {new_user.nombre} creado con rol {rol} en {new_user.sucursal or 'Global'}"}

@router.post("/admin/users/{user_id}/role")
def change_user_role(user_id: int, nuevo_rol: str, db: Session = Depends(get_db), admin: models.User = Depends(auth.get_super_admin)):
    """Solo el Admin Global puede cambiar roles de nivel jerárquico."""
    if nuevo_rol not in ["admin", "local_admin", "staff", "user"]:
        raise HTTPException(status_code=400, detail="Rol no válido")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.rol = nuevo_rol
    db.commit()
    return {"status": "ok"}

@router.post("/admin/users/{user_id}/toggle-block")
def toggle_user_block(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(auth.get_local_manager)):
    """Alterna el estado de bloqueo. Los locales solo bloquean a su gente."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if admin.rol != "admin" and user.sucursal != admin.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre este usuario")

    # Evitar que el admin se bloquee a sí mismo
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="No podés bloquear tu propia cuenta")

    user.is_blocked = not getattr(user, 'is_blocked', False)
    db.commit()
    
    estado = "BLOQUEADO" if user.is_blocked else "ACTIVO"
    return {"status": "ok", "is_blocked": user.is_blocked, "message": f"Usuario {user.nombre} ahora está {estado}"}

@router.post("/admin/users/{user_id}/balance")
def adjust_user_balance(user_id: int, monto: float, db: Session = Depends(get_db), admin: models.User = Depends(auth.get_local_manager)):
    """Ajusta el saldo de un usuario."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if admin.rol != "admin" and user.sucursal != admin.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre este usuario")
        
    user.saldo = monto
    db.commit()
    return {"status": "ok"}

@router.delete("/admin/users/{user_id}")
@router.post("/admin/users/{user_id}/delete")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(auth.get_super_admin)):
    """Solo el Admin Global puede borrar cuentas definitivamente."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.id == admin.id: raise HTTPException(status_code=400, detail="No podés eliminar tu propia cuenta")
    
    db.query(models.Vehicle).filter(models.Vehicle.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"status": "ok"}

# --- GESTIÓN DE RESERVAS (Staff + Admin) ---

@router.get("/admin/reservations", response_model=List[schemas.UserReservationResponse])
def list_reservations(sucursal: Optional[str] = Query(None), db: Session = Depends(get_db), staff: models.User = Depends(auth.get_operational_user)):
    """Lista todas las reservas. Los locales solo ven las de su sede."""
    from services.reservation_service import ReservationService
    ReservationService.cleanup_overdue_reservations(db)
    
    q = db.query(models.Reservation)
    
    # Aislamiento por sede para roles no globales
    if staff.rol != "admin":
        sucursal = staff.sucursal
        q = q.filter(models.Reservation.sucursal_nombre == sucursal)
    elif sucursal:
        q = q.filter(models.Reservation.sucursal_nombre == sucursal)
        
    results = q.order_by(models.Reservation.id.desc()).all()
    
    out = []
    for r in results:
        d = schemas.UserReservationResponse.model_validate(r)
        if r.user:
            d.user_name = f"{r.user.nombre} {r.user.apellido}"
            d.user_email = r.user.email
        if r.cliente_nombre:
            d.user_name = r.cliente_nombre
        out.append(d)
    return out

@router.post("/admin/reservations")
def create_admin_reservation(data: schemas.AdminReservationCreate, db: Session = Depends(get_db), staff: models.User = Depends(auth.get_operational_user)):
    """Permite al administrador o empleado crear una reserva manual."""
    from services.billing_service import BillingService

    # Aislamiento de sede
    if staff.rol != "admin":
        data.sucursal_nombre = staff.sucursal

    if data.user_id:
        user = db.query(models.User).filter(models.User.id == data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        vehicle = db.query(models.Vehicle).filter(models.Vehicle.patente == data.patente, models.Vehicle.user_id == data.user_id).first()
        if not vehicle:
            raise HTTPException(status_code=400, detail="La patente no está vinculada a ese usuario")

    start = datetime.datetime.fromisoformat(data.fecha_inicio)
    end = datetime.datetime.fromisoformat(data.fecha_fin)
    duration_hours = (end - start).total_seconds() / 3600
    if duration_hours <= 0:
        raise HTTPException(status_code=400, detail="La fecha de fin debe ser posterior a la de inicio")

    # Cálculo de tarifa según modalidad y sede
    rate = BillingService.get_rate(db, data.tipo_estadia, sucursal=data.sucursal_nombre)
    if data.tipo_estadia == "hora":
        monto = math.ceil(duration_hours) * rate
    elif data.tipo_estadia == "dia":
        monto = max(1, math.ceil(duration_hours / 24)) * rate
    elif data.tipo_estadia == "semana":
        monto = math.ceil(duration_hours / (24 * 7)) * rate
    elif data.tipo_estadia == "quincena":
        monto = math.ceil(duration_hours / (24 * 15)) * rate
    elif data.tipo_estadia == "mes":
        monto = math.ceil(duration_hours / (24 * 30)) * rate
    else:
        monto = math.ceil(duration_hours) * rate

    sucursales_info = {
        "AUTOPASS Central": "Av. del Libertador 1200, CABA. Abierto 24hs.",
        "AUTOPASS Ituzaingó": "Punto de Acceso Estación Ituzaingó. Abierto 24hs.",
        "AUTOPASS Castelar": "Centro Comercial Castelar. Abierto 24hs.",
        "AUTOPASS Morón": "Plaza Oeste Shopping - Morón. Abierto 24hs."
    }
    info_sede = sucursales_info.get(data.sucursal_nombre, "Sede no especificada.")

    new_res = models.Reservation(
        user_id=data.user_id,
        patente=data.patente,
        fecha_inicio=data.fecha_inicio,
        fecha_fin=data.fecha_fin,
        monto_total=monto,
        estado_pago="Pendiente",
        estado_reserva="Pendiente",
        tipo_estadia=data.tipo_estadia,
        sucursal_nombre=data.sucursal_nombre,
        sucursal_info=info_sede,
        cliente_nombre=data.cliente_nombre
    )
    db.add(new_res)
    db.commit()
    return {"status": "ok", "id": new_res.id, "monto": monto}

@router.post("/admin/reservations/{res_id}/confirm-payment")
def confirm_reservation_payment(res_id: int, db: Session = Depends(get_db), staff: models.User = Depends(auth.get_operational_user)):
    """Confirmación manual de pago."""
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
    
    reserva.estado_pago = "Pagado"
    db.commit()
    return {"status": "ok"}

@router.post("/admin/reservations/{res_id}/cancel")
def cancel_reservation_admin(res_id: int, db: Session = Depends(get_db), staff: models.User = Depends(auth.get_operational_user)):
    """Cancelación manual."""
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva: raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
        
    from services.reservation_service import ReservationService
    result = ReservationService.cancel_reservation(db, None, res_id)
    if result["status"] == "ok":
        return result
    raise HTTPException(status_code=400, detail=result["message"])

# --- CONFIGURACIÓN DE TARIFAS (Solo Admin) ---

@router.get("/admin/settings")
def get_admin_settings(db: Session = Depends(get_db), admin: models.User = Depends(auth.get_local_manager)):
    """Retorna las configuraciones vigentes. Los locales solo ven las de su sede."""
    q = db.query(models.Settings)
    if admin.rol != "admin":
        q = q.filter(models.Settings.sucursal == admin.sucursal)
    else:
        # El admin global ve las globales (sucursal=None) por defecto, 
        # o podríamos mostrarle todas. Por ahora, las globales.
        q = q.filter(models.Settings.sucursal == None)
        
    all_settings = q.all()
    return {s.clave: s.valor for s in all_settings}

@router.post("/settings/prices")
def update_price(clave: str, valor: float, db: Session = Depends(get_db), admin: models.User = Depends(auth.get_local_manager)):
    """Actualiza o crea un valor de configuración para la sede del administrador."""
    sucursal = admin.sucursal if admin.rol != "admin" else None

    if clave == "capacidad_total":
        aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
        if aforo:
            aforo.capacidad_total = int(valor)
            db.commit()
            return {"status": "ok"}
        else:
            db.add(models.ParkingAforo(
                capacidad_total=int(valor), 
                ocupacion_actual=0, 
                ultima_actualizacion=datetime.datetime.now().isoformat(),
                sucursal=sucursal
            ))
            db.commit()
            return {"status": "ok"}

    setting = db.query(models.Settings).filter(
        models.Settings.clave == clave, 
        models.Settings.sucursal == sucursal
    ).first()
    
    if setting: 
        setting.valor = valor
    else: 
        db.add(models.Settings(clave=clave, valor=valor, sucursal=sucursal))
    
    db.commit()
    return {"status": "ok", "message": f"Precio {clave} actualizado para {sucursal or 'Global'}"}

# --- OPERACIONES MANUALES (Staff + Admin) ---

@router.post("/admin/open-barrier")
def open_barrier(gate_id: str, db: Session = Depends(get_db), staff: models.User = Depends(auth.get_operational_user), request: Request = None):
    """Envía un comando de apertura manual a la barrera vía MQTT."""
    from routes.parking import MQTT_TOPIC_ENTRADA, MQTT_TOPIC_SALIDA
    import json
    
    # En un sistema multi-sede real, el topic MQTT incluiría la sede
    # Por ahora simulamos que el staff solo opera su sede
    topic = MQTT_TOPIC_ENTRADA if gate_id.upper() == "ENTRADA" else MQTT_TOPIC_SALIDA
    now = datetime.datetime.now().isoformat()
    
    if request and hasattr(request.app, 'mqtt_client'):
        request.app.mqtt_client.publish(topic, json.dumps({
            "command": "OPEN", 
            "method": "MANUAL_OP", 
            "staff_id": staff.id,
            "sucursal": staff.sucursal,
            "timestamp": now
        }))
        return {"status": "ok", "message": f"Comando de apertura enviado a {gate_id} ({staff.sucursal or 'Global'})"}
    
    raise HTTPException(status_code=503, detail="Servicio MQTT no disponible")

@router.post("/admin/manual-entry")
def manual_entry(plate: str, db: Session = Depends(get_db), staff: models.User = Depends(auth.get_operational_user)):
    """Registra un ingreso forzado al predio de la sede."""
    from routes.parking import normalize_plate
    p = normalize_plate(plate)
    now = datetime.datetime.now()
    sucursal = staff.sucursal
    
    ultimo = db.query(models.AccessLog).filter(
        models.AccessLog.patente_detectada == p,
        models.AccessLog.sucursal == sucursal
    ).order_by(models.AccessLog.id.desc()).first()
    
    if ultimo and ultimo.tipo_evento == "ENTRADA":
        raise HTTPException(status_code=400, detail="El vehículo ya figura como ingresado en esta sede")
    
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
    if not aforo:
        # Inicializar aforo si no existe para la sede
        aforo = models.ParkingAforo(sucursal=sucursal, capacidad_total=20, ocupacion_actual=0)
        db.add(aforo)
    
    aforo.ocupacion_actual += 1
    db.add(models.AccessLog(patente_detectada=p, tipo_evento="ENTRADA", fecha_hora=now.isoformat(), sucursal=sucursal))
    db.commit()
    return {"status": "ok", "message": f"Ingreso manual registrado en {sucursal or 'Global'}: {p}"}

@router.post("/admin/manual-exit")
def manual_exit(plate: str, db: Session = Depends(get_db), staff: models.User = Depends(auth.get_operational_user)):
    """Registra una salida manual de la sede."""
    from routes.parking import normalize_plate
    p = normalize_plate(plate)
    sucursal = staff.sucursal
    
    ultimo = db.query(models.AccessLog).filter(
        models.AccessLog.patente_detectada == p,
        models.AccessLog.sucursal == sucursal
    ).order_by(models.AccessLog.id.desc()).first()
    
    if not ultimo or ultimo.tipo_evento != "ENTRADA":
        raise HTTPException(status_code=400, detail="El vehículo no figura en esta sede")
    
    if not ultimo.pago_confirmado:
        raise HTTPException(status_code=403, detail="DEUDA PENDIENTE en esta sede.")
    
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
    if aforo and aforo.ocupacion_actual > 0: 
        aforo.ocupacion_actual -= 1
        
    db.add(models.AccessLog(patente_detectada=p, tipo_evento="SALIDA", fecha_hora=datetime.datetime.now().isoformat(), pago_confirmado=True, sucursal=sucursal))
    db.commit()
    return {"status": "ok", "message": f"Salida manual registrada en {sucursal or 'Global'}: {p}"}
