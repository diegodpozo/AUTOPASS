import datetime
import time
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
import models
import schemas
from services.billing_service import BillingService
from services.branch_service import BranchService
from core.config import settings
from services.email_service import EmailService
from services.notification_service import NotificationService
from services.time_service import TimeService
from repositories.reservation_repository import ReservationRepository
from fastapi import HTTPException
from models.enums import ReservationStatus, PaymentStatus, VehicleType, AccessEventType
from core.logger import get_logger

logger = get_logger("ReservationService")

# --- HELPERS DE AFORO ---

from core.normalize import normalize_name as _normalizar_sucursal


_CACHE_AVAILABILITY = {}
_CACHE_AVAILABILITY_TTL_SECONDS = 30


def _capacidad_reservas_para_tipo(db: Session, sucursal_nombre: str, tipo_vehiculo: str) -> int:
    """CAPACIDAD TOTAL DE PLAZAS EXCLUSIVAS PARA RESERVAS DEL TIPO DE VEHICULO (PB + PISOS)."""
    tipo_vehiculo = (tipo_vehiculo or "Auto").strip().title()
    attr_cap = "capacidad_reservas_autos"
    if tipo_vehiculo == "Moto":
        attr_cap = "capacidad_reservas_motos"
    elif tipo_vehiculo == "Camioneta":
        attr_cap = "capacidad_reservas_camionetas"

    branch = db.query(models.ParkingBranch).options(joinedload(models.ParkingBranch.floors)).filter(models.ParkingBranch.nombre == sucursal_nombre).first()
    if branch and branch.floors:
        cap_floors = sum(getattr(f, attr_cap, 5) or 0 for f in branch.floors)
        if cap_floors > 0:
            return cap_floors

    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal_nombre).first()
    if aforo:
        val = getattr(aforo, attr_cap, 5)
        return val if (val is not None and val > 0) else 5
    return 5


def _reservas_activas_tipo(db: Session, sucursal_nombre: str, desde_str: str, hasta_str: str, tipo_vehiculo: str, exclude_id: int = None) -> list:
    """RESERVAS ACTIVAS/PENDIENTES SOLAPADAS EN EL RANGO [desde, hasta) FILTRADAS POR TIPO DE VEHICULO."""
    tipo_vehiculo = (tipo_vehiculo or "Auto").strip().title()
    q = db.query(models.Reservation).filter(
        models.Reservation.sucursal_nombre == sucursal_nombre,
        models.Reservation.estado_reserva.in_(["Pendiente", "Activa"]),
        models.Reservation.estado_pago.in_(["Pendiente", "Pagado"]),
        models.Reservation.fecha_inicio < hasta_str,
        models.Reservation.fecha_fin > desde_str
    )
    if exclude_id:
        q = q.filter(models.Reservation.id != exclude_id)
    all_res = q.all()

    if not all_res:
        return []

    patentes = [r.patente for r in all_res]
    v_map = {v.patente: v.tipo for v in db.query(models.Vehicle).filter(models.Vehicle.patente.in_(patentes)).all()}
    return [r for r in all_res if v_map.get(r.patente, r.tipo_vehiculo or "Auto").strip().title() == tipo_vehiculo]


def _get_cached_availability(key: tuple, generator):
    """CACHE CON TTL CORTO PARA CALLULOS DE DISPONIBILIDAD (EVITA RECALCULO MASIVO EN SELECTOR DE HORARIOS)."""
    ahora = time.monotonic()
    hit = _CACHE_AVAILABILITY.get(key)
    if hit and (ahora - hit[0]) < _CACHE_AVAILABILITY_TTL_SECONDS:
        return hit[1]
    resultado = generator()
    _CACHE_AVAILABILITY[key] = (ahora, resultado)
    return resultado


def _calcular_ocupacion_maxima_simultanea(reservas, f_inicio_str: str, f_fin_str: str) -> int:
    """CALCULA LA OCUPACIÓN MÁXIMA SIMULTÁNEA DE RESERVAS EN EL INTERVALO USANDO SWEEP-LINE ALGORITHM."""
    if not reservas:
        return 0

    try:
        f_inicio_dt = datetime.datetime.fromisoformat(f_inicio_str.replace("/", "-"))
        f_fin_dt = datetime.datetime.fromisoformat(f_fin_str.replace("/", "-"))
    except (ValueError, TypeError):
        return len(reservas)

    eventos = []
    conteo_base = 0

    for r in reservas:
        try:
            r_ini = datetime.datetime.fromisoformat(r.fecha_inicio.replace("/", "-"))
            r_fin = datetime.datetime.fromisoformat(r.fecha_fin.replace("/", "-"))
        except (ValueError, TypeError):
            continue

        if r_ini >= f_fin_dt or r_fin <= f_inicio_dt:
            continue

        if r_ini <= f_inicio_dt:
            conteo_base += 1

        t_ini = max(r_ini, f_inicio_dt)
        t_fin = min(r_fin, f_fin_dt)

        if t_ini > f_inicio_dt:
            eventos.append((t_ini, 1))
        if t_fin < f_fin_dt:
            eventos.append((t_fin, -1))

    # Ordenar eventos: por fecha, y si coinciden marcas de tiempo, los -1 (salidas) antes que +1 (entradas)
    eventos.sort(key=lambda x: (x[0], x[1]))

    max_ocupacion = conteo_base
    ocupacion_actual = conteo_base

    for dt, cambio in eventos:
        ocupacion_actual += cambio
        if ocupacion_actual > max_ocupacion:
            max_ocupacion = ocupacion_actual

    return max_ocupacion


def verificar_disponibilidad(db: Session, sucursal_nombre: str, fecha_inicio: str, fecha_fin: str, exclude_id: int = None, tipo_vehiculo: str = "Auto"):
    """VERIFICA SI HAY PLAZAS DE RESERVA DISPONIBLES EN LA SUCURSAL PARA EL PERIODO Y TIPO DE VEHICULO SOLICITADO.
    RETORNA {disponible, capacidad_total, ocupada, restan, mensaje}."""
    tipo_vehiculo = (tipo_vehiculo or "Auto").strip().title()
    attr_cap = "capacidad_reservas_autos"
    if tipo_vehiculo == "Moto":
        attr_cap = "capacidad_reservas_motos"
    elif tipo_vehiculo == "Camioneta":
        attr_cap = "capacidad_reservas_camionetas"

    # 1. OBTENER CAPACIDAD TOTAL DE PLAZAS EXCLUSIVAS PARA RESERVAS DEL TIPO DE VEHICULO (PB + PISOS)
    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == sucursal_nombre).first()
    capacidad_reservas = 0
    if branch and branch.floors:
        capacidad_reservas = sum(getattr(f, attr_cap, 5) for f in branch.floors)
    else:
        aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal_nombre).first()
        if aforo:
            capacidad_reservas = getattr(aforo, attr_cap, 5)

    if capacidad_reservas == 0:
        return {"disponible": False, "capacidad_total": 0, "ocupada": 0, "restan": 0, "mensaje": f"La sede no cuenta con plazas asignadas para reservas de {tipo_vehiculo}s."}

    # 2. CONSULTAR RESERVAS SOLAPADAS EN EL RANGO (EXCLUYENDO CANCELADAS/COMPLETADAS)
    query = db.query(models.Reservation).filter(
        models.Reservation.sucursal_nombre == sucursal_nombre,
        models.Reservation.estado_reserva.in_(["Pendiente", "Activa"]),
        models.Reservation.estado_pago.in_(["Pendiente", "Pagado"]),
        models.Reservation.fecha_inicio < fecha_fin,
        models.Reservation.fecha_fin > fecha_inicio
    )
    if exclude_id:
        query = query.filter(models.Reservation.id != exclude_id)

    all_res = query.all()
    reservas_filtradas = []
    if all_res:
        patentes = [r.patente for r in all_res]
        v_map = {v.patente: v.tipo for v in db.query(models.Vehicle).filter(models.Vehicle.patente.in_(patentes)).all()}
        for r in all_res:
            v_tipo = v_map.get(r.patente, r.tipo_vehiculo or "Auto")
            if v_tipo.strip().title() == tipo_vehiculo:
                reservas_filtradas.append(r)

    # 3. ALGORITMO SWEEP-LINE: OCUPACIÓN MÁXIMA SIMULTÁNEA EN EL INTERVALO
    ocupada = _calcular_ocupacion_maxima_simultanea(reservas_filtradas, fecha_inicio, fecha_fin)

    disponible = ocupada < capacidad_reservas
    restan = max(0, capacidad_reservas - ocupada)
    return {
        "disponible": disponible,
        "capacidad_total": capacidad_reservas,
        "ocupada": ocupada,
        "restan": restan,
        "mensaje": f"Quedan {restan} plaza{'s' if restan != 1 else ''} de reserva para {tipo_vehiculo}s disponible{'s' if restan != 1 else ''}" if disponible else f"No hay plazas exclusivas de reserva para {tipo_vehiculo}s en el horario solicitado."
    }


def obtener_fechas_deshabilitadas(
    db: Session,
    sucursal_nombre: str,
    tipo_vehiculo: str = "Auto",
    tipo_estadia: str = "dia",
    fecha_desde_str: str = None,
    dias_evaluar: int = 90
) -> list[str]:
    """CALCULA LAS FECHAS (YYYY-MM-DD) QUE DEBEN DESHABILITARSE EN EL SELECTOR DE FECHAS
    PORQUE PARA ESA FECHA DE INICIO Y TIPO DE ESTADÍA NO HAY CAPACIDAD DISPONIBLE."""
    if not sucursal_nombre:
        return []

    try:
        if fecha_desde_str:
            desde_dt = datetime.datetime.fromisoformat(fecha_desde_str.split("T")[0])
        else:
            desde_dt = TimeService.now().replace(hour=0, minute=0, second=0, microsecond=0)
    except Exception:
        desde_dt = TimeService.now().replace(hour=0, minute=0, second=0, microsecond=0)

    cache_key = ("fechas", sucursal_nombre, tipo_vehiculo, tipo_estadia, desde_dt.strftime("%Y-%m-%d"), dias_evaluar)
    return _get_cached_availability(cache_key, lambda: _calcular_fechas_deshabilitadas(
        db, sucursal_nombre, tipo_vehiculo, tipo_estadia, desde_dt, dias_evaluar
    ))


def _calcular_fechas_deshabilitadas(
    db: Session,
    sucursal_nombre: str,
    tipo_vehiculo: str,
    tipo_estadia: str,
    desde_dt: datetime.datetime,
    dias_evaluar: int
) -> list[str]:
    duracion_dias_map = {"dia": 1, "semana": 7, "quincena": 15, "mes": 30}
    duracion_dias = duracion_dias_map.get(tipo_estadia, 1)

    capacidad_reservas = _capacidad_reservas_para_tipo(db, sucursal_nombre, tipo_vehiculo)
    if capacidad_reservas == 0:
        return [(desde_dt + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(dias_evaluar)]

    # UNA SOLA CONSULTA: TODAS LAS RESERVAS SOLAPADAS CON EL VENTANA COMPLETA EVALUADA
    ventana_ini = desde_dt.strftime("%Y-%m-%d 00:00")
    ventana_fin = (desde_dt + datetime.timedelta(days=dias_evaluar - 1 + duracion_dias)).strftime("%Y-%m-%d 23:59")
    reservas = _reservas_activas_tipo(db, sucursal_nombre, ventana_ini, ventana_fin, tipo_vehiculo)

    fechas_deshabilitadas = []
    for i in range(dias_evaluar):
        curr_dt = desde_dt + datetime.timedelta(days=i)
        curr_str = curr_dt.strftime("%Y-%m-%d")

        # PRE-FILTRO POR DÍA: SOLO RESERVAS QUE TOCAN ESTE DÍA (REDUCE EL SWEEP-LINE POR HORA)
        dia_ini_str = f"{curr_str} 00:00"
        dia_fin_str = f"{curr_str} 23:59"
        reservas_dia = [r for r in reservas if r.fecha_inicio < dia_fin_str and r.fecha_fin > dia_ini_str]

        if tipo_estadia == "hora":
            # Para hora, marcar el día como deshabilitado solo si NINGUNA hora del día tiene lugar libre
            dia_completo_lleno = True
            for h in range(24):
                f_ini = f"{curr_str} {h:02d}:00"
                f_fin = f"{curr_str} {h:02d}:59"
                ocupada = _calcular_ocupacion_maxima_simultanea(reservas_dia, f_ini, f_fin)
                if ocupada < capacidad_reservas:
                    dia_completo_lleno = False
                    break
            if dia_completo_lleno:
                fechas_deshabilitadas.append(curr_str)
        else:
            f_ini = f"{curr_str} 00:00"
            fin_dt = curr_dt + datetime.timedelta(days=duracion_dias - 1)
            f_fin = f"{fin_dt.strftime('%Y-%m-%d')} 23:59"
            if _calcular_ocupacion_maxima_simultanea(reservas_dia, f_ini, f_fin) >= capacidad_reservas:
                fechas_deshabilitadas.append(curr_str)

    return fechas_deshabilitadas


def obtener_horas_deshabilitadas(
    db: Session,
    sucursal_nombre: str,
    fecha_str: str,
    tipo_vehiculo: str = "Auto",
    duracion_horas: float = 1.0,
    paso_minutos: int = 30
) -> list[str]:
    """CALCULA LOS SLOTS HORARIOS (HH:MM) DESHABILITADOS PARA UN DÍA ESPECÍFICO CON GRANULARIDAD DE MINUTOS."""
    if not sucursal_nombre or not fecha_str:
        return []

    fecha_clean = fecha_str.split("T")[0].split(" ")[0]
    cache_key = ("horas", sucursal_nombre, fecha_clean, tipo_vehiculo, duracion_horas, paso_minutos)
    return _get_cached_availability(cache_key, lambda: _calcular_horas_deshabilitadas(
        db, sucursal_nombre, fecha_clean, tipo_vehiculo, duracion_horas, paso_minutos
    ))


def obtener_horas_deshabilitadas_con_reservas(
    db: Session,
    sucursal_nombre: str,
    fecha_str: str,
    tipo_vehiculo: str = "Auto",
    duracion_horas: float = 1.0,
    paso_minutos: int = 30,
    exclude_id: int = None
) -> dict:
    """SLOTS DESHABILITADOS + RANGOS REALMENTE RESERVADOS DEL DÍA.
    PERMITE A LA GRILLA DISTINGUIR LO QUE ESTÁ OCUPADO POR UNA RESERVA (RANGO EXACTO)
    DE LAS HORAS DE MARGEN QUE SOLO SE DESHABILITAN POR SOLAPAMIENTO.
    exclude_id: AL EDITAR, EXCLUYE LA PROPIA RESERVA DE LOS RANGOS OCUPADOS."""
    if not sucursal_nombre or not fecha_str:
        return {"disabled_hours": [], "reserved_ranges": []}
    fecha_clean = fecha_str.split("T")[0].split(" ")[0]
    disabled_hours = obtener_horas_deshabilitadas(
        db, sucursal_nombre, fecha_clean, tipo_vehiculo, duracion_horas, paso_minutos
    )
    reserved_ranges = _obtener_rangos_reservados_dia(db, sucursal_nombre, fecha_clean, tipo_vehiculo, exclude_id)
    return {
        "disabled_hours": disabled_hours,
        "reserved_ranges": reserved_ranges
    }


def _obtener_rangos_reservados_dia(db: Session, sucursal_nombre: str, fecha_clean: str, tipo_vehiculo: str, exclude_id: int = None) -> list[dict]:
    """RANGOS [inicio, fin) EN HH:MM DE LAS RESERVAS ACTIVAS QUE TOCAN EL DÍA, RECORTADOS AL DÍA."""
    dia_ini = f"{fecha_clean} 00:00"
    dia_fin = f"{fecha_clean} 23:59"
    reservas = _reservas_activas_tipo(db, sucursal_nombre, dia_ini, dia_fin, tipo_vehiculo, exclude_id)
    if not reservas:
        return []
    dia_ini_dt = datetime.datetime.fromisoformat(dia_ini)
    dia_fin_dt = datetime.datetime.fromisoformat(dia_fin)
    rangos = []
    for r in reservas:
        try:
            r_ini_dt = datetime.datetime.fromisoformat(r.fecha_inicio.replace("/", "-"))
            r_fin_dt = datetime.datetime.fromisoformat(r.fecha_fin.replace("/", "-"))
        except (ValueError, TypeError):
            continue
        if r_fin_dt <= r_ini_dt:
            continue
        ini_dt = max(r_ini_dt, dia_ini_dt)
        fin_dt = min(r_fin_dt, dia_fin_dt)
        if fin_dt > ini_dt:
            rangos.append({"inicio": ini_dt.strftime("%H:%M"), "fin": fin_dt.strftime("%H:%M")})
    return rangos


def _calcular_horas_deshabilitadas(
    db: Session,
    sucursal_nombre: str,
    fecha_clean: str,
    tipo_vehiculo: str,
    duracion_horas: float,
    paso_minutos: int
) -> list[str]:
    capacidad_reservas = _capacidad_reservas_para_tipo(db, sucursal_nombre, tipo_vehiculo)

    duracion_sec = int(duracion_horas * 3600)
    total_minutos = 24 * 60

    # SI ES HOY, LOS SLOTS QUE NO RESPETEN LA ANTICIPACION MINIMA NO PUEDEN RESERVARSE
    ahora = TimeService.now()
    es_hoy = fecha_clean == ahora.strftime("%Y-%m-%d")
    antelacion_min = settings.RESERVA_HORA_MIN_SEGUNDOS

    if capacidad_reservas == 0:
        return [f"{h:02d}:{m:02d}" for min_curr in range(0, total_minutos, paso_minutos)
                for h, m in [divmod(min_curr, 60)]]

    # VENTANA ÚNICA: DÍA COMPLETO MÁS LA DURACIÓN MÁXIMA DE UN SLOT QUE PUEDE CRUZAR LA MEDIANOCHE
    ultimo_slot_min = total_minutos - paso_minutos
    ventana_ini = f"{fecha_clean} 00:00"
    ventana_fin = ((datetime.datetime.fromisoformat(f"{fecha_clean} 00:00")
                    + datetime.timedelta(minutes=ultimo_slot_min, seconds=duracion_sec))).strftime("%Y-%m-%d %H:%M")
    reservas = _reservas_activas_tipo(db, sucursal_nombre, ventana_ini, ventana_fin, tipo_vehiculo)

    horas_deshabilitadas = []
    for min_curr in range(0, total_minutos, paso_minutos):
        h = min_curr // 60
        m = min_curr % 60
        h_str = f"{h:02d}:{m:02d}"

        try:
            start_dt = datetime.datetime.fromisoformat(f"{fecha_clean} {h:02d}:{m:02d}")
            end_dt = start_dt + datetime.timedelta(seconds=duracion_sec)
        except Exception:
            continue

        # HOY: BLOQUEAR SLOTS QUE YA PASARON O FALTAN MENOS DE LA ANTICIPACION MINIMA (MINIMO EL SLOT ACTUAL)
        if es_hoy and (start_dt - ahora).total_seconds() < antelacion_min:
            horas_deshabilitadas.append(h_str)
            continue

        f_ini = start_dt.strftime("%Y-%m-%d %H:%M")
        f_fin = end_dt.strftime("%Y-%m-%d %H:%M")

        ocupada = _calcular_ocupacion_maxima_simultanea(reservas, f_ini, f_fin)
        if ocupada >= capacidad_reservas:
            horas_deshabilitadas.append(h_str)

    return horas_deshabilitadas

def _reservar_plaza_en_aforo(db: Session, res: "models.Reservation"):
    """YA NO PRE-OCUPA PLAZA FISICA. La ocupación la maneja exclusivamente el ALPR (entrada/salida física)."""
    pass

def _liberar_plaza_en_aforo(db: Session, res: "models.Reservation"):
    """YA NO LIBERA PLAZA FISICA. La ocupación la maneja exclusivamente el ALPR (entrada/salida física)."""
    pass

# --- SERVICIO DE GESTION DE RESERVAS ---

class ReservationService:
    @staticmethod
    def create_reservation(db: Session, data: schemas.AdminReservationCreate) -> models.Reservation:
        """CREA UNA NUEVA RESERVA MANUAL DESDE EL PANEL ADMINISTRATIVO."""
        vehiculo = db.query(models.Vehicle).filter(models.Vehicle.patente == data.patente).first()
        tipo_vehiculo = getattr(data, "tipo_vehiculo", None) or (vehiculo.tipo if vehiculo else VehicleType.AUTO)
        tipo_v_str = tipo_vehiculo.value if hasattr(tipo_vehiculo, "value") else str(tipo_vehiculo)

        monto = BillingService.calculate_total_amount(
            db, data.tipo_estadia, data.fecha_inicio, data.fecha_fin, 
            sucursal=data.sucursal_nombre, tipo_vehiculo=tipo_vehiculo
        )

        info_sede = BranchService.get_branch_info_str(db, data.sucursal_nombre)

        new_res = models.Reservation(
            user_id=data.user_id,
            patente=data.patente,
            fecha_inicio=data.fecha_inicio,
            fecha_fin=data.fecha_fin,
            monto_total=monto,
            estado_pago=PaymentStatus.PENDIENTE,
            estado_reserva=ReservationStatus.PENDIENTE,
            tipo_estadia=data.tipo_estadia,
            sucursal_nombre=data.sucursal_nombre,
            sucursal_info=info_sede,
            cliente_nombre=data.cliente_nombre,
            tipo_vehiculo=tipo_v_str,
            origen="manual"
        )
        db.add(new_res)
        db.commit()
        db.refresh(new_res)
        try:
            from services.notification_service import NotificationService
            NotificationService.notify_occupancy_change(db, new_res.sucursal_nombre)
        except Exception:
            pass
        return new_res

    @staticmethod
    def get_available_redemption_discounts(db: Session, user_id: int, sucursal: str = None):
        """LISTA LOS DESCUENTOS DE RESERVA (%) VIGENTES DE UN USUARIO APLICABLES A UNA SUCURSAL.
        Se usa en caja (admin) para detectar el descuento que corresponde aplicar al cobrar.
        Si no hay usuario vinculado, devuelve lista vacía."""
        if not user_id:
            return []
        q = db.query(models.RedemptionTicket).filter(
            models.RedemptionTicket.user_id == user_id,
            models.RedemptionTicket.tipo_canje == "descuento_reserva",
            models.RedemptionTicket.estado == "VIGENTE"
        )
        if sucursal:
            q = q.filter(ReservationService.redemption_sucursal_clause(sucursal))
        return q.order_by(models.RedemptionTicket.id.desc()).all()

    @staticmethod
    def pay_reservation_manual(db: Session, res: "models.Reservation", metodo_pago: str = None, redemption_ticket_id: int = None):
        """MARCA UNA RESERVA COMO PAGADA (PAGO MANUAL ADMIN) SIN DESCONTAR SALDO NI USAR MERCADO PAGO.
        Si se indica un redemption_ticket_id (descuento % de reserva) vigente del usuario
        y de la misma sucursal (o global) se aplica el descuento sobre el monto total
        y la reserva queda pagada por el valor final descontado."""
        if res.estado_pago == PaymentStatus.PAGADO:
            return {"status": "ok", "message": "La reserva ya se encuentra pagada", "monto": res.monto_total, "monto_a_cobrar": res.monto_total, "descuento": 0.0, "metodo_pago": res.metodo_pago}

        # --- APLICAR DESCUENTO POR CANJE (% de descuento en estacionamiento) ---
        descuento = 0.0
        monto_a_cobrar = res.monto_total or 0.0
        if redemption_ticket_id:
            if not res.user_id:
                raise HTTPException(status_code=400, detail="La reserva no tiene un usuario vinculado para aplicar el descuento")
            ticket_redencion = ReservationService.validate_redemption_ticket(db, res.user_id, redemption_ticket_id, res.sucursal_nombre)
            porc = ticket_redencion.valor_descuento or 0
            descuento = round(monto_a_cobrar * porc / 100.0, 2)
            monto_a_cobrar = round(monto_a_cobrar - descuento, 2)
            res.monto_total = monto_a_cobrar
            res.monto_reembolsado = 0.0
            ticket_redencion.estado = "USADO"
            ticket_redencion.fecha_uso = datetime.datetime.now().isoformat()
            ticket_redencion.reserva_id = res.id

        res.estado_pago = PaymentStatus.PAGADO
        res.estado_reserva = ReservationStatus.ACTIVA
        res.fecha_pago = datetime.datetime.now().isoformat()
        res.metodo_pago = metodo_pago

        if res.user:
            puntos_ganados = BillingService.calculate_points(monto_a_cobrar)
            res.user.puntos_acumulados += puntos_ganados
            db.add(models.PointsLog(
                user_id=res.user.id,
                cantidad=puntos_ganados,
                motivo=f"Abono Manual Reserva: {res.patente}",
                fecha=datetime.datetime.now().isoformat()
            ))
            if puntos_ganados > 0:
                try:
                    from services.user_notification_service import UserNotificationService
                    UserNotificationService.create_notification(
                        db, res.user.id,
                        tipo=models.NotificationType.POINTS_EARNED,
                        titulo="¡Puntos AutoPass!",
                        mensaje=f"¡Ganaste {puntos_ganados} puntos por abonar la reserva #{res.id} ({res.patente})!",
                        reserva_id=res.id
                    )
                except Exception:
                    pass

        db.commit()
        db.refresh(res)
        return {"status": "ok", "message": "Pago registrado", "monto": res.monto_total, "monto_a_cobrar": monto_a_cobrar, "descuento": descuento, "metodo_pago": res.metodo_pago}

    @staticmethod
    def cleanup_overdue_reservations(db: Session):
        """CANCELA AUTOMATICAMENTE RESERVAS IMPAGAS CUYO TIEMPO DE INICIO YA PASO CON UN MARGEN DE GRACIA.
        NO CANCELA RESERVAS CUYO VEHICULO YA INGRESO AL PREDIO."""
        now = TimeService.now()
        grace_cutoff = now - datetime.timedelta(hours=2)
        cutoff_str = grace_cutoff.strftime("%Y-%m-%d %H:%M")
        
        overdue = db.query(models.Reservation).filter(
            models.Reservation.estado_pago == PaymentStatus.PENDIENTE,
            models.Reservation.estado_reserva == ReservationStatus.PENDIENTE,
            models.Reservation.fecha_inicio <= cutoff_str,
            models.Reservation.tipo_estadia == "hora"
        ).all()
        
        if overdue:
            logger.info(f"Cancelando {len(overdue)} reservas impagas vencidas. Cutoff: {cutoff_str}")
            for r in overdue:
                # SI EL VEHICULO YA INGRESO AL PREDIO CON SU RESERVA, NO CANCELAR
                entry = db.query(models.AccessLog).filter(
                    models.AccessLog.reserva_id == r.id,
                    models.AccessLog.tipo_evento == AccessEventType.ENTRADA
                ).first()
                if entry:
                    continue
                r.estado_reserva = ReservationStatus.CANCELADA
                r.estado_pago = PaymentStatus.FALLIDO
            db.commit()
            return len(overdue)
        return 0

    @staticmethod
    def auto_finalize_reservations(db: Session, user_id: int):
        """MARCA COMO COMPLETADAS LAS RESERVAS DE UN USUARIO CUYO TIEMPO DE ESTADIA YA EXPIRO."""
        now_str = TimeService.now_str()
        past_reservations = ReservationRepository.get_past_reservations(db, user_id, now_str)
        if past_reservations:
            for r in past_reservations:
                r.estado_reserva = ReservationStatus.COMPLETADA
            db.commit()

    @staticmethod
    def auto_finalize_all_reservations(db: Session):
        """MARCA COMO COMPLETADAS TODAS LAS RESERVAS VENCIDAS DEL SISTEMA."""
        now_str = TimeService.now_str()
        # BUSCAMOS RESERVAS QUE ESTEN PENDIENTES O ACTIVAS PERO CUYA FECHA_FIN YA PASO
        vencidas = db.query(models.Reservation).filter(
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA]),
            models.Reservation.fecha_fin < now_str
        ).all()
        
        if vencidas:
            logger.info(f"Finalizando {len(vencidas)} reservas vencidas.")
            for r in vencidas:
                r.estado_reserva = ReservationStatus.COMPLETADA
                # LIBERAR PLAZA SI ES NO HORARIA (NUNCA SE LIBERA EN SALIDA FISICA)
                if r.tipo_estadia != "hora" and r.sucursal_nombre:
                    _liberar_plaza_en_aforo(db, r)
            db.commit()
            # NOTIFICAR A LOS DASHBOARDS PARA QUE REFLEJEN LA DEUDA ACUMULADA TRAS EL VENCIMIENTO
            try:
                from services.notification_service import NotificationService
                sucursales = {_normalizar_sucursal(r.sucursal_nombre) for r in vencidas if r.sucursal_nombre}
                for s in sucursales:
                    NotificationService.notify_occupancy_change(db=db, sucursal_norm=s)
            except Exception as e:
                logger.error(f"Error notificando vencimiento de reservas: {e}")
            return len(vencidas)
        return 0

    @staticmethod
    def get_en_predio_ids(db: Session, reserva_ids) -> set:
        """DEVUELVE LOS IDS DE RESERVAS CUYO ULTIMO EVENTO FISICO FUE UN INGRESO (VEHICULO DENTRO DEL PREDIO)."""
        if not reserva_ids:
            return set()
        latest = (
            db.query(models.AccessLog.reserva_id, func.max(models.AccessLog.id).label('max_id'))
            .filter(models.AccessLog.reserva_id.in_(list(reserva_ids)))
            .group_by(models.AccessLog.reserva_id)
            .subquery()
        )
        rows = (
            db.query(latest.c.reserva_id)
            .join(models.AccessLog, models.AccessLog.id == latest.c.max_id)
            .filter(models.AccessLog.tipo_evento == AccessEventType.ENTRADA)
            .all()
        )
        return {row[0] for row in rows}

    @staticmethod
    def redemption_sucursal_clause(sucursal):
        """CLÁUSULA DE FILTRADO DE REDEMPTION TICKET POR SUCURSAL.
        Acepta el ticket global (sucursal NULL), igualdad exacta o igualdad normalizada
        (sin prefijo 'AUTOPASS ', sin espacios extra y sin diferenciar mayúsculas),
        para tolerar datos legados donde algunas sucursales se guardaron con prefijo."""
        from sqlalchemy import or_, func
        col = models.RedemptionTicket.sucursal
        if not sucursal:
            return or_(col == None, col == '')
        norm_col = func.trim(func.replace(func.lower(col), 'autopass ', ''))
        norm_param = func.trim(func.replace(func.lower(func.trim(sucursal)), 'autopass ', ''))
        return or_(col == sucursal, col == None, norm_col == norm_param)

    @classmethod
    def validate_redemption_ticket(cls, db: Session, user_id: int, redemption_ticket_id: int, sucursal: str = None) -> models.RedemptionTicket:
        """Valida y obtiene un ticket de descuento por canje para un usuario y sucursal."""
        if not redemption_ticket_id:
            return None
        ticket = db.query(models.RedemptionTicket).filter(
            models.RedemptionTicket.id == redemption_ticket_id,
            models.RedemptionTicket.user_id == user_id,
            models.RedemptionTicket.tipo_canje == "descuento_reserva",
            models.RedemptionTicket.estado == "VIGENTE",
            cls.redemption_sucursal_clause(sucursal)
        ).first()
        if not ticket:
            raise HTTPException(status_code=400, detail="El descuento seleccionado no es válido para esta reserva o sucursal")
        return ticket

    @staticmethod
    def pay_reservation(db: Session, user: models.User, res_id: int, redemption_ticket_id: int = None):
        """ABONA UNA RESERVA UTILIZANDO EL SALDO DISPONIBLE DEL USUARIO.
        Si se indica un redemption_ticket_id (descuento % de reserva) vigente del usuario
        y de la misma sucursal (o global), se aplica el descuento sobre el monto total
        y el resto se paga con saldo."""
        res = ReservationRepository.get_by_user_and_id(db, user.id, res_id)
        
        if not res: 
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        if res.estado_reserva in [ReservationStatus.CANCELADA, ReservationStatus.COMPLETADA]:
            raise HTTPException(status_code=400, detail=f"No se puede abonar una reserva en estado '{res.estado_reserva}'")

        if res.estado_pago == PaymentStatus.PAGADO:
            return {"status": "ok", "message": "La reserva ya ha sido abonada"}

        # --- APLICAR DESCUENTO POR CANJE (% de descuento en estacionamiento) ---
        descuento = 0.0
        ticket_redencion = None
        monto_a_cobrar = res.monto_total

        if redemption_ticket_id:
            ticket_redencion = ReservationService.validate_redemption_ticket(db, user.id, redemption_ticket_id, res.sucursal_nombre)
            porc = ticket_redencion.valor_descuento or 0
            descuento = round(res.monto_total * porc / 100.0, 2)
            monto_a_cobrar = round(res.monto_total - descuento, 2)


        if user.saldo < monto_a_cobrar:
            raise HTTPException(status_code=400, detail=f"Saldo insuficiente en su cuenta AutoPass (necesita ${monto_a_cobrar:,.2f})")
        
        # DEDUCCION DE SALDO Y ACTUALIZACION DE ESTADO
        user.saldo -= monto_a_cobrar
        res.estado_pago = PaymentStatus.PAGADO
        res.estado_reserva = ReservationStatus.ACTIVA
        res.fecha_pago = datetime.datetime.now().isoformat()
        res.metodo_pago = "SALDO"
        # SI SE APLICO DESCUENTO, LA RESERVA QUEDA CON SU VALOR FINAL
        if ticket_redencion:
            res.monto_total = monto_a_cobrar
            res.monto_reembolsado = 0.0

        # ACREDITACION DE PUNTOS POR LEALTAD (SOBRE LO EFECTIVAMENTE ABONADO)
        puntos_ganados = BillingService.calculate_points(monto_a_cobrar)
        user.puntos_acumulados += puntos_ganados
        
        db.add(models.PointsLog(
            user_id=user.id,
            cantidad=puntos_ganados,
            motivo=f"Reserva: {res.patente}",
            fecha=datetime.datetime.now().isoformat()
        ))

        # MARCAR EL TICKET DE DESCUENTO COMO USADO (si aplico descuento)
        if ticket_redencion:
            ticket_redencion.estado = "USADO"
            ticket_redencion.fecha_uso = datetime.datetime.now().isoformat()
            ticket_redencion.reserva_id = res.id
        
        db.commit()

        # RESERVAR PLAZA EN AFORO PARA RESERVAS NO HORARIAS (DIA/SEMANA/QUINCENA/MES)
        # SOLO SI LA RESERVA YA COMENZO; SI ES FUTURA, LO HARA EL WORKER AL INICIAR
        if res.tipo_estadia != "hora" and res.sucursal_nombre:
            now_str = TimeService.now_str()
            if res.fecha_inicio <= now_str:
                _reservar_plaza_en_aforo(db, res)

        # ENVIAR MAIL DE CONFIRMACION
        dir_info = res.sucursal_info
        if not dir_info or dir_info == "Sede no especificada." or dir_info.startswith("Sede no especificada"):
            dir_info = BranchService.get_branch_info_str(db, res.sucursal_nombre)
        res_info = {
            "id": res.id,
            "sucursal": res.sucursal_nombre,
            "direccion": dir_info,
            "patente": res.patente,
            "fecha_inicio": res.fecha_inicio,
            "fecha_fin": res.fecha_fin,
            "costo": res.monto_total
        }
        EmailService.send_reservation_confirmation(user.email, user.nombre, res_info)

        try:
            from services.user_notification_service import UserNotificationService
            UserNotificationService.create_notification(
                db, user.id, "RESERVATION_CONFIRMED",
                f"Reserva #{res.id} confirmada",
                f"Se abonó con éxito tu reserva en {res.sucursal_nombre} por ${res.monto_total:,.2f}.",
                res.id
            )
            if puntos_ganados > 0:
                UserNotificationService.create_notification(
                    db, user.id, "POINTS_EARNED",
                    "¡Puntos AutoPass!",
                    f"¡Ganaste {puntos_ganados} puntos por abonar la reserva #{res.id} ({res.patente}).",
                    res.id
                )
        except Exception as e:
            print(f"[ERROR NOTIF] No se pudo notificar pago de reserva: {e}")

        return {"status": "ok", "message": "Reserva abonada con éxito", "puntos_ganados": puntos_ganados}

    @staticmethod
    def pay_reservation_mp(db: Session, user: models.User, res: models.Reservation, monto_a_cobrar: float, redemption_ticket_id: int = None):
        """MARCA UNA RESERVA COMO PAGADA POR MERCADO PAGO (CHECKOUT PRO) SIN DESCONTAR SALDO.
        El monto confirmado por Mercado Pago ya incluye el descuento por canje si correspondía."""
        if res.estado_reserva in [ReservationStatus.CANCELADA, ReservationStatus.COMPLETADA]:
            raise HTTPException(status_code=400, detail=f"No se puede abonar una reserva en estado '{res.estado_reserva}'")

        if res.estado_pago == PaymentStatus.PAGADO:
            return {"status": "ok", "message": "La reserva ya ha sido abonada", "aplicado": False}

        # VALIDAR Y CONSUMIR DESCUENTO POR CANJE (si aplicó)
        ticket_redencion = None
        if redemption_ticket_id:
            ticket_redencion = ReservationService.validate_redemption_ticket(db, user.id, redemption_ticket_id, res.sucursal_nombre)

        # ACTUALIZACION DE ESTADO
        res.estado_pago = PaymentStatus.PAGADO
        res.estado_reserva = ReservationStatus.ACTIVA
        res.fecha_pago = datetime.datetime.now().isoformat()
        res.metodo_pago = "MERCADOPAGO"
        if ticket_redencion:
            res.monto_total = monto_a_cobrar
            res.monto_reembolsado = 0.0
            ticket_redencion.estado = "USADO"
            ticket_redencion.fecha_uso = datetime.datetime.now().isoformat()
            ticket_redencion.reserva_id = res.id

        # ACREDITACION DE PUNTOS POR LEALTAD (SOBRE LO EFECTIVAMENTE ABONADO)
        puntos_ganados = BillingService.calculate_points(monto_a_cobrar)
        user.puntos_acumulados += puntos_ganados

        db.add(models.PointsLog(
            user_id=user.id,
            cantidad=puntos_ganados,
            motivo=f"Reserva (Mercado Pago): {res.patente}",
            fecha=datetime.datetime.now().isoformat()
        ))

        db.commit()

        # RESERVAR PLAZA EN AFORO PARA RESERVAS NO HORARIAS YA INICIADAS (NO-OP desde v9.5)
        if res.tipo_estadia != "hora" and res.sucursal_nombre:
            now_str = TimeService.now_str()
            if res.fecha_inicio <= now_str:
                _reservar_plaza_en_aforo(db, res)

        # ENVIAR MAIL DE CONFIRMACION
        dir_info = res.sucursal_info
        if not dir_info or dir_info == "Sede no especificada." or dir_info.startswith("Sede no especificada"):
            dir_info = BranchService.get_branch_info_str(db, res.sucursal_nombre)
        res_info = {
            "id": res.id,
            "sucursal": res.sucursal_nombre,
            "direccion": dir_info,
            "patente": res.patente,
            "fecha_inicio": res.fecha_inicio,
            "fecha_fin": res.fecha_fin,
            "costo": res.monto_total
        }
        EmailService.send_reservation_confirmation(user.email, user.nombre, res_info)

        try:
            from services.user_notification_service import UserNotificationService
            UserNotificationService.create_notification(
                db, user.id, "RESERVATION_CONFIRMED",
                f"Reserva #{res.id} confirmada",
                f"Se abonó con Mercado Pago tu reserva en {res.sucursal_nombre} por ${res.monto_total:,.2f}.",
                res.id
            )
            if puntos_ganados > 0:
                UserNotificationService.create_notification(
                    db, user.id, "POINTS_EARNED",
                    "¡Puntos AutoPass!",
                    f"¡Ganaste {puntos_ganados} puntos por abonar la reserva #{res.id} ({res.patente}).",
                    res.id
                )
        except Exception as e:
            print(f"[ERROR NOTIF] No se pudo notificar pago de reserva MP: {e}")

        return {"status": "ok", "message": "Reserva abonada con éxito", "puntos_ganados": puntos_ganados, "aplicado": True}

    @staticmethod
    def simulate_refund(db: Session, res: models.Reservation):
        """CALCULA EL REEMBOLSO POTENCIAL SIN EJECUTAR LA CANCELACION."""
        # 1. VERIFICACION DE PRESENCIA FISICA
        import re
        norm_pat = re.sub(r'[^A-Z0-9]', '', (res.patente or '').upper())
        vinc_log = db.query(models.AccessLog).filter(
            models.AccessLog.normalized_patente == norm_pat,
            models.AccessLog.tipo_evento == AccessEventType.ENTRADA,
            models.AccessLog.sucursal == res.sucursal_nombre
        ).order_by(models.AccessLog.id.desc()).first()

        es_presencial = False
        if vinc_log:
            salida = db.query(models.AccessLog).filter(
                models.AccessLog.patente_detectada == vinc_log.patente_detectada,
                models.AccessLog.tipo_evento == AccessEventType.SALIDA,
                models.AccessLog.id > vinc_log.id,
                models.AccessLog.sucursal == vinc_log.sucursal
            ).first()
            if not salida:
                es_presencial = True

        if es_presencial:
            return {"reembolso": 0.0, "error": "Vehículo en el predio"}

        # 2. CALCULO DE REEMBOLSO
        monto_a_reembolsar = 0.0
        if res.estado_pago == PaymentStatus.PAGADO:
            now = datetime.datetime.now()
            start = datetime.datetime.fromisoformat(res.fecha_inicio)
            end = datetime.datetime.fromisoformat(res.fecha_fin)

            if now < start:
                monto_a_reembolsar = res.monto_total
            elif now > end:
                monto_a_reembolsar = 0.0
            else:
                if res.tipo_estadia == "hora" and vinc_log:
                    monto_a_reembolsar = 0.0
                else:
                    duracion_total = (end - start).total_seconds()
                    tiempo_restante = (end - now).total_seconds()
                    if duracion_total > 0:
                        porcentaje_restante = max(0, tiempo_restante / duracion_total)
                        monto_a_reembolsar = round(res.monto_total * porcentaje_restante, 2)
        
        return {"reembolso": monto_a_reembolsar, "error": None}

    @staticmethod
    def cancel_reservation(db: Session, user: models.User, res_id: int):
        """CANCELA UNA RESERVA Y GESTIONA REEMBOLSOS PROPORCIONALES."""
        res = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
        
        if not res: 
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        if res.estado_reserva == ReservationStatus.CANCELADA:
            return {"status": "ok", "message": "La reserva ya se encuentra cancelada"}
        
        if res.estado_reserva == ReservationStatus.COMPLETADA:
            return {"status": "error", "message": "La reserva ya finalizó y no puede cancelarse"}
            
        # USAMOS LA SIMULACION PARA OBTENER EL MONTO
        sim = ReservationService.simulate_refund(db, res)
        if sim["error"]:
            raise HTTPException(status_code=400, detail=sim["error"])
        
        monto_a_reembolsar = sim["reembolso"]

        # 3. EJECUCION DEL REEMBOLSO
        target_user = user or res.user
        if monto_a_reembolsar > 0 and target_user:
            target_user.saldo += monto_a_reembolsar
            
            # AJUSTE DE PUNTOS (SOLO SOBRE LO REEMBOLSADO)
            puntos_a_descontar = BillingService.calculate_points(monto_a_reembolsar)
            target_user.puntos_acumulados = max(0, target_user.puntos_acumulados - puntos_a_descontar)
            
            db.add(models.PointsLog(
                user_id=target_user.id,
                cantidad=-puntos_a_descontar,
                motivo=f"Reembolso por Cancelación (Proporcional): {res.patente}",
                fecha=datetime.datetime.now().isoformat()
            ))

        res.estado_reserva = ReservationStatus.CANCELADA
        res.estado_pago = PaymentStatus.REEMBOLSADO if monto_a_reembolsar > 0 else PaymentStatus.CANCELADO
        res.monto_reembolsado = float(monto_a_reembolsar)
        
        if monto_a_reembolsar > 0:
            res.fecha_pago = datetime.datetime.now().isoformat()
            
        db.commit()

        if res.tipo_estadia != "hora" and res.sucursal_nombre:
            _liberar_plaza_en_aforo(db, res)
        
        msg = f"Reserva cancelada. Reembolso: ${monto_a_reembolsar}" if monto_a_reembolsar > 0 else "Reserva cancelada sin reembolso."
        
        try:
            from services.user_notification_service import UserNotificationService
            if target_user:
                notif_msg = f"Tu reserva #{res.id} en {res.sucursal_nombre} fue cancelada."
                if monto_a_reembolsar > 0:
                    notif_msg += f" Se reembolsaron ${monto_a_reembolsar:,.2f} a tu saldo."
                UserNotificationService.create_notification(
                    db, target_user.id, "RESERVATION_CANCELLED",
                    f"Reserva #{res.id} cancelada",
                    notif_msg,
                    res.id
                )
        except Exception as e:
            print(f"[ERROR NOTIF] No se pudo notificar cancelacion de reserva: {e}")

        return {"status": "ok", "message": msg, "reembolso": monto_a_reembolsar}
