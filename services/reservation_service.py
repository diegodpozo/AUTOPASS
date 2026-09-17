import datetime
import math
import re
import time
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
import models
import schemas
from services.billing_service import BillingService
from services.branch_service import BranchService
from core.config import settings
from core.normalize import format_plate
from services.email_service import EmailService
from services.notification_service import NotificationService
from services.time_service import TimeService
from repositories.reservation_repository import ReservationRepository
from fastapi import HTTPException
from models.enums import UserRole, ReservationStatus, PaymentStatus, VehicleType, AccessEventType
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
        val = getattr(aforo, attr_cap, None)
        if val is None:
            return 5
        return val if val > 0 else 0
    return 5


def _reservas_activas_tipo(db: Session, sucursal_nombre: str, desde_str: str, hasta_str: str, tipo_vehiculo: str, exclude_id: int = None) -> list:
    """RESERVAS ACTIVAS/PENDIENTES SOLAPADAS EN EL RANGO [desde, hasta) FILTRADAS POR TIPO DE VEHICULO."""
    tipo_vehiculo = (tipo_vehiculo or "Auto").strip().title()
    q = db.query(models.Reservation).filter(
        models.Reservation.sucursal_nombre == sucursal_nombre,
        models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE.value, ReservationStatus.ACTIVA.value]),
        models.Reservation.estado_pago.in_([PaymentStatus.PENDIENTE.value, PaymentStatus.PAGADO.value]),
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

    # 1. OBTENER CAPACIDAD TOTAL DE PLAZAS EXCLUSIVAS PARA RESERVAS DEL TIPO DE VEHICULO (PB + PISOS)
    capacidad_reservas = _capacidad_reservas_para_tipo(db, sucursal_nombre, tipo_vehiculo)

    if capacidad_reservas == 0:
        return {"disponible": False, "capacidad_total": 0, "ocupada": 0, "restan": 0, "mensaje": f"La sede no cuenta con plazas asignadas para reservas de {tipo_vehiculo}s."}

    # 2. CONSULTAR RESERVAS SOLAPADAS EN EL RANGO (EXCLUYENDO CANCELADAS/COMPLETADAS)
    query = db.query(models.Reservation).filter(
        models.Reservation.sucursal_nombre == sucursal_nombre,
        models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE.value, ReservationStatus.ACTIVA.value]),
        models.Reservation.estado_pago.in_([PaymentStatus.PENDIENTE.value, PaymentStatus.PAGADO.value]),
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

    # -------------------------------------------------------------------
    # RUTAS DELGADAS: helpers y wrappers completos para routes/admin y routes/user
    # -------------------------------------------------------------------

    @staticmethod
    def get_reservation_or_404(db: Session, res_id: int, user_id: int = None):
        """Obtiene una reserva o lanza 404. Con user_id, la filtra por dueño."""
        q = db.query(models.Reservation).filter(models.Reservation.id == res_id)
        if user_id is not None:
            q = q.filter(models.Reservation.user_id == user_id)
        res = q.first()
        if not res:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        return res

    @staticmethod
    def get_permissioned_reservation(db: Session, staff, res_id: int):
        """Obtiene una reserva validando que el operador tenga acceso (admin == todas)."""
        res = ReservationService.get_reservation_or_404(db, res_id)
        if staff.rol != UserRole.ADMIN and res.sucursal_nombre != staff.sucursal:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
        return res

    @staticmethod
    def lookup_patente(db: Session, patente: str) -> dict:
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
            "encontrado": True, "user_id": owner.id, "nombre": owner.nombre,
            "apellido": owner.apellido, "email": owner.email,
            "tipo_vehiculo": vehicle.tipo or "Auto",
            "marca_modelo": vehicle.marca_modelo or ""
        }

    @staticmethod
    def get_new_reservations_count(db: Session, staff, since_id: int = None) -> dict:
        q = db.query(models.Reservation)
        if staff.rol != UserRole.ADMIN:
            staff_suc = staff.sucursal or ""
            norm_col = func.trim(func.replace(func.lower(models.Reservation.sucursal_nombre), 'autopass ', ''))
            norm_staff = staff_suc.lower().replace('autopass ', '').strip()
            q = q.filter((models.Reservation.sucursal_nombre == staff_suc) | (norm_col == norm_staff))
        latest_id = q.with_entities(func.max(models.Reservation.id)).scalar() or 0
        count = 0
        if since_id is not None:
            count = q.filter(models.Reservation.id > since_id).count()
        return {"count": count, "latest_id": latest_id}

    @staticmethod
    def validar_horario_sucursal(db: Session, sucursal_nombre: str, start: datetime.datetime, end: datetime.datetime):
        if not sucursal_nombre:
            return
        branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == sucursal_nombre).first()
        if not branch or branch.is_24h or not branch.horario:
            return
        match = re.match(r'^(\d{1,2}):(\d{2})\s+(?:A|UN)\s+(\d{1,2}):(\d{2})$', branch.horario.upper().strip())
        if not match:
            return
        open_h, open_m = int(match.group(1)), int(match.group(2))
        close_h, close_m = int(match.group(3)), int(match.group(4))
        if close_h == 0 and close_m == 0:
            close_h, close_m = 23, 59
        apertura = datetime.time(open_h, open_m)
        cierre = datetime.time(close_h, close_m)
        if start.date() != end.date():
            raise HTTPException(status_code=400, detail=f"La sucursal cierra a las {match.group(3)}:{match.group(4)}. La estadía no puede extenderse más allá del cierre.")
        if start.time() < apertura or start.time() >= cierre:
            raise HTTPException(status_code=400, detail=f"La sucursal abre de {branch.horario}. La hora de inicio debe estar dentro del horario de atención.")
        if end.time() > cierre:
            raise HTTPException(status_code=400, detail=f"La sucursal cierra a las {match.group(3)}:{match.group(4)}. La hora de fin no puede exceder el horario de cierre.")

    @staticmethod
    def validate_manual_vinculacion(db: Session, user_id: int, patente: str):
        user = None
        vehicle = None
        if user_id:
            user = db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            vehicle = db.query(models.Vehicle).filter(
                models.Vehicle.user_id == user_id,
                func.replace(func.upper(models.Vehicle.patente), ' ', '') == re.sub(r'[^A-Z0-9]', '', patente.upper())
            ).first()
            if not vehicle:
                raise HTTPException(status_code=400, detail="La patente no está vinculada a ese usuario")
        return user, vehicle

    @classmethod
    def create_user_reservation(cls, db: Session, user, data: schemas.UserReservationCreate) -> dict:
        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")
        vehicle = db.query(models.Vehicle).filter(models.Vehicle.patente == data.patente, models.Vehicle.user_id == user.id).first()
        if not vehicle:
            raise HTTPException(status_code=400, detail="La patente no está vinculada a su cuenta")
        p_clean = data.patente.upper().replace(' ', '')
        existing_overlap = db.query(models.Reservation).filter(
            func.replace(func.upper(models.Reservation.patente), ' ', '') == p_clean,
            models.Reservation.sucursal_nombre == data.sucursal_nombre,
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE.value, ReservationStatus.ACTIVA.value]),
            models.Reservation.estado_pago.in_([PaymentStatus.PENDIENTE.value, PaymentStatus.PAGADO.value]),
            models.Reservation.fecha_inicio < data.fecha_fin,
            models.Reservation.fecha_fin > data.fecha_inicio
        ).first()
        if existing_overlap:
            raise HTTPException(status_code=400, detail=f"El vehículo patente {data.patente} ya posee otra reserva en la sucursal {data.sucursal_nombre} en el período solicitado.")
        rate = BillingService.get_rate(db, data.tipo_estadia, sucursal=data.sucursal_nombre, tipo_vehiculo=vehicle.tipo)
        start = datetime.datetime.fromisoformat(data.fecha_inicio)
        end = datetime.datetime.fromisoformat(data.fecha_fin)
        max_future = datetime.datetime.now() + datetime.timedelta(days=90)
        if start > max_future:
            raise HTTPException(status_code=400, detail="No se pueden reservar con más de 3 meses de anticipación.")
        if data.tipo_estadia == "hora":
            min_antelacion_min = settings.RESERVA_HORA_MIN_SEGUNDOS // 60
            if (start - datetime.datetime.now()).total_seconds() < settings.RESERVA_HORA_MIN_SEGUNDOS:
                raise HTTPException(status_code=400, detail=f"Las reservas por hora deben realizarse con al menos {min_antelacion_min} minutos de anticipación.")
            cls.validar_horario_sucursal(db, data.sucursal_nombre, start, end)
        disp = verificar_disponibilidad(db, data.sucursal_nombre, data.fecha_inicio, data.fecha_fin, tipo_vehiculo=vehicle.tipo)
        if not disp["disponible"]:
            raise HTTPException(status_code=400, detail=disp["mensaje"])
        duration_hours = (end - start).total_seconds() / 3600
        if duration_hours <= 0:
            raise HTTPException(status_code=400, detail="La fecha de fin debe ser posterior a la de inicio")
        if data.tipo_estadia == "dia" and data.dias_semana:
            dias_seleccionados = [int(d.strip()) for d in data.dias_semana.split(",") if d.strip()]
            count, d = 0, start
            while d <= end:
                if d.weekday() in dias_seleccionados:
                    count += 1
                d += datetime.timedelta(days=1)
            if count == 0:
                raise HTTPException(status_code=400, detail="No hay días seleccionados dentro del rango")
            monto = count * rate
        elif data.tipo_estadia == "hora":
            v_str = vehicle.tipo.value if hasattr(vehicle.tipo, "value") else str(vehicle.tipo)
            tarifa_30min = BillingService.get_30min_rate(db, sucursal=data.sucursal_nombre, tipo_vehiculo=v_str)
            monto = max(1, math.ceil(duration_hours * 2)) * tarifa_30min
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
        estado_pago = PaymentStatus.PENDIENTE
        info_sede = BranchService.get_branch_info_str(db, data.sucursal_nombre)
        tipo_v_str = vehicle.tipo.value if hasattr(vehicle.tipo, "value") else str(vehicle.tipo)
        new_res = models.Reservation(
            user_id=user.id, patente=data.patente, fecha_inicio=data.fecha_inicio, fecha_fin=data.fecha_fin,
            tipo_estadia=data.tipo_estadia, monto_total=monto, estado_pago=estado_pago, estado_reserva=ReservationStatus.PENDIENTE,
            sucursal_nombre=data.sucursal_nombre, sucursal_info=info_sede,
            dias_semana=data.dias_semana, tipo_vehiculo=tipo_v_str
        )
        db.add(new_res)
        db.commit()
        db.refresh(new_res)
        try:
            NotificationService.notify_occupancy_change(db, new_res.sucursal_nombre)
        except Exception as e:
            logger.error(f"Error notificando nueva reserva: {e}")
        return {"status": "ok", "monto": monto, "estado_pago": estado_pago}

    @classmethod
    def modify_user_reservation(cls, db: Session, user, res_id: int, data: schemas.ReservationUpdate) -> dict:
        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")
        res = db.query(models.Reservation).filter(models.Reservation.id == res_id, models.Reservation.user_id == user.id).first()
        if not res:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        if res.estado_reserva in (ReservationStatus.COMPLETADA, ReservationStatus.CANCELADA):
            raise HTTPException(status_code=400, detail=f"No se puede modificar una reserva en estado '{res.estado_reserva}'.")
        tipo_efectivo = data.tipo_estadia if data.tipo_estadia else res.tipo_estadia
        suc_efectivo = data.sucursal_nombre if data.sucursal_nombre else res.sucursal_nombre
        start_efectivo = datetime.datetime.fromisoformat(data.fecha_inicio) if data.fecha_inicio else datetime.datetime.fromisoformat(res.fecha_inicio)
        end_efectivo = datetime.datetime.fromisoformat(data.fecha_fin) if data.fecha_fin else datetime.datetime.fromisoformat(res.fecha_fin)
        max_future = datetime.datetime.now() + datetime.timedelta(days=90)
        if start_efectivo > max_future:
            raise HTTPException(status_code=400, detail="No se pueden reservar con más de 3 meses de anticipación.")
        if tipo_efectivo == "hora":
            min_antelacion_min = settings.RESERVA_HORA_MIN_SEGUNDOS // 60
            if (start_efectivo - datetime.datetime.now()).total_seconds() < settings.RESERVA_HORA_MIN_SEGUNDOS:
                raise HTTPException(status_code=400, detail=f"No se puede modificar una reserva por hora con menos de {min_antelacion_min} minutos de antelación")
            cls.validar_horario_sucursal(db, suc_efectivo, start_efectivo, end_efectivo)
        fec_ini = data.fecha_inicio if data.fecha_inicio else res.fecha_inicio
        fec_fin = data.fecha_fin if data.fecha_fin else res.fecha_fin
        suc_efect = data.sucursal_nombre if data.sucursal_nombre else res.sucursal_nombre
        disp = verificar_disponibilidad(db, suc_efect, fec_ini, fec_fin, exclude_id=res.id)
        if not disp["disponible"]:
            raise HTTPException(status_code=400, detail=disp["mensaje"])
        monto_anterior, ya_pagado = res.monto_total, res.estado_pago == PaymentStatus.PAGADO
        if data.fecha_inicio:
            res.fecha_inicio = data.fecha_inicio
        if data.fecha_fin:
            res.fecha_fin = data.fecha_fin
        if data.patente:
            if not db.query(models.Vehicle).filter(models.Vehicle.patente == data.patente, models.Vehicle.user_id == user.id).first():
                raise HTTPException(status_code=400, detail="Patente no vinculada")
            res.patente = data.patente
        if data.tipo_estadia:
            res.tipo_estadia = data.tipo_estadia
        if data.sucursal_nombre:
            res.sucursal_nombre = data.sucursal_nombre
        vehiculo_mod = db.query(models.Vehicle).filter(models.Vehicle.patente == res.patente).first()
        tipo_vehiculo_mod = vehiculo_mod.tipo if vehiculo_mod else "Auto"
        rate = BillingService.get_rate(db, res.tipo_estadia, sucursal=res.sucursal_nombre, tipo_vehiculo=tipo_vehiculo_mod)
        duration_hours = (datetime.datetime.fromisoformat(res.fecha_fin) - datetime.datetime.fromisoformat(res.fecha_inicio)).total_seconds() / 3600
        if duration_hours <= 0:
            raise HTTPException(status_code=400, detail="Fechas inválidas")
        monto_nuevo = math.ceil(duration_hours) * rate
        if res.tipo_estadia == "hora":
            tarifa_30min = BillingService.get_30min_rate(db, sucursal=res.sucursal_nombre, tipo_vehiculo=tipo_vehiculo_mod)
            monto_nuevo = max(1, math.ceil(duration_hours * 2)) * tarifa_30min
        elif res.tipo_estadia == "dia":
            monto_nuevo = max(1, math.ceil(duration_hours / 24)) * rate
        elif res.tipo_estadia == "semana":
            monto_nuevo = math.ceil(duration_hours / (24 * 7)) * rate
        elif res.tipo_estadia == "quincena":
            monto_nuevo = math.ceil(duration_hours / (24 * 15)) * rate
        elif res.tipo_estadia == "mes":
            monto_nuevo = math.ceil(duration_hours / (24 * 30)) * rate
        if ya_pagado:
            diferencia = monto_nuevo - monto_anterior
            dif_puntos = BillingService.calculate_points(monto_nuevo) - BillingService.calculate_points(monto_anterior)
            if dif_puntos != 0:
                user.puntos_acumulados += dif_puntos
                db.add(models.PointsLog(user_id=user.id, cantidad=dif_puntos, motivo=f"Ajuste Reserva: {res.patente}", fecha=datetime.datetime.now().isoformat()))
            if diferencia > 0:
                if user.saldo < diferencia:
                    raise HTTPException(status_code=400, detail=f"Saldo insuficiente (+${diferencia})")
                user.saldo -= diferencia
            else:
                user.saldo += abs(diferencia)
        else:
            res.estado_pago = PaymentStatus.PENDIENTE
        res.monto_total = monto_nuevo
        db.commit()
        try:
            from services.user_notification_service import UserNotificationService
            msg_detalle = f"Tu reserva #{res.id} ({res.patente}) en {res.sucursal_nombre} fue modificada exitosamente."
            if ya_pagado and diferencia != 0:
                if diferencia > 0:
                    msg_detalle += f" Se debitó una diferencia de ${diferencia:,.2f} de tu saldo."
                else:
                    msg_detalle += f" Se acreditó un reembolso de ${abs(diferencia):,.2f} a tu saldo."
            UserNotificationService.create_notification(
                db, user_id=user.id,
                tipo=models.NotificationType.RESERVATION_MODIFIED,
                titulo="Reserva modificada",
                mensaje=msg_detalle,
                reserva_id=res.id
            )
        except Exception as e:
            logger.error(f"Error creando notificación de reserva modificada: {e}")
        return {"status": "ok", "monto_total": monto_nuevo, "estado_pago": res.estado_pago}

    @staticmethod
    def list_user_reservations(db: Session, user_id: int):
        ReservationService.cleanup_overdue_reservations(db)
        ReservationService.auto_finalize_reservations(db, user_id)
        reservations = db.query(models.Reservation).filter(models.Reservation.user_id == user_id).order_by(models.Reservation.id.desc()).all()
        en_predio = ReservationService.get_en_predio_ids(db, [r.id for r in reservations])
        updated = False
        for r in reservations:
            r.en_predio = r.id in en_predio
            if not r.sucursal_info or "Sede no especificada" in r.sucursal_info or r.sucursal_info.startswith("Sucursal "):
                info_str = BranchService.get_branch_info_str(db, r.sucursal_nombre)
                if info_str and info_str != "Dirección no disponible":
                    r.sucursal_info = info_str
                    updated = True
        if updated:
            try:
                db.commit()
            except Exception:
                pass
        return reservations

    @staticmethod
    def confirm_reminder(db: Session, user_id: int, res_id: int) -> dict:
        res = db.query(models.Reservation).filter(models.Reservation.id == res_id, models.Reservation.user_id == user_id).first()
        if not res:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        res.recordatorio_confirmado = True
        from services.user_notification_service import UserNotificationService
        UserNotificationService.mark_reservation_notifications_as_read(db, user_id, res_id, tipo="REMINDER_UNPAID")
        db.commit()
        return {"status": "ok", "message": "Recordatorio confirmado"}

    @staticmethod
    def list_admin_reservations(db: Session, staff, estado: str = None, sucursal: str = None):
        ReservationService.cleanup_overdue_reservations(db)
        q = db.query(models.Reservation)
        if estado:
            q = q.filter(models.Reservation.estado_reserva == estado)
        if staff.rol != UserRole.ADMIN:
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

    @staticmethod
    def create_admin_reservation(db: Session, staff, data) -> dict:
        data.patente = format_plate(data.patente)
        if staff.rol != UserRole.ADMIN:
            data.sucursal_nombre = staff.sucursal
        user, vehicle = ReservationService.validate_manual_vinculacion(db, data.user_id, data.patente)
        tipo_v = data.tipo_vehiculo or "Auto"
        if vehicle:
            tipo_v = data.tipo_vehiculo or (vehicle.tipo.value if hasattr(vehicle.tipo, 'value') else str(vehicle.tipo))
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
                from services.user_notification_service import UserNotificationService
                UserNotificationService.create_notification(
                    db, user_id=new_res.user_id,
                    tipo=models.NotificationType.RESERVATION_CREATED_ADMIN,
                    titulo="Reserva creada por administrador",
                    mensaje=f"Se creó una reserva para {new_res.patente} el {new_res.fecha_inicio} en {new_res.sucursal_nombre}.",
                    reserva_id=new_res.id
                )
            return {"status": "ok", "id": new_res.id, "monto": new_res.monto_total, "pagado": bool(data.pagar),
                    "metodo_pago": data.metodo_pago,
                    "descuento": (result or {}).get("descuento", 0.0),
                    "monto_a_cobrar": (result or {}).get("monto_a_cobrar", new_res.monto_total)}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    def update_admin_reservation(db: Session, staff, res_id: int, data) -> dict:
        data.patente = format_plate(data.patente)
        reserva = ReservationService.get_reservation_or_404(db, res_id)
        if (getattr(reserva, "origen", None) or "cliente") != "manual":
            raise HTTPException(status_code=400, detail="Solo se pueden editar reservas creadas por administración o empleados")
        if reserva.estado_reserva in (ReservationStatus.COMPLETADA, ReservationStatus.CANCELADA):
            raise HTTPException(status_code=400, detail="No se puede editar una reserva completada o cancelada")
        if staff.rol != UserRole.ADMIN and reserva.sucursal_nombre != staff.sucursal:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
        if staff.rol != UserRole.ADMIN:
            data.sucursal_nombre = staff.sucursal
        if data.fecha_fin <= data.fecha_inicio:
            raise HTTPException(status_code=400, detail="La fecha de fin debe ser posterior a la de inicio")
        vehicle = None
        if data.user_id:
            _, vehicle = ReservationService.validate_manual_vinculacion(db, data.user_id, data.patente)
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
        disp = verificar_disponibilidad(db, data.sucursal_nombre, data.fecha_inicio, data.fecha_fin, exclude_id=res_id, tipo_vehiculo=tipo_v_str)
        if not disp["disponible"]:
            raise HTTPException(status_code=400, detail=disp["mensaje"])
        try:
            monto = BillingService.calculate_total_amount(
                db, data.tipo_estadia, data.fecha_inicio, data.fecha_fin,
                sucursal=data.sucursal_nombre, tipo_vehiculo=tipo_v_str
            )
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
            devolucion_a_saldo = False
            if reserva.estado_pago == PaymentStatus.PAGADO:
                if diferencia > 0:
                    accion = "cobro"
                    metodo_ajuste = data.cobrar_diferencia_metodo
                    reserva.monto_total = round(monto_anterior + diferencia, 2)
                    if metodo_ajuste:
                        reserva.metodo_pago = metodo_ajuste
                    reserva.fecha_pago = datetime.datetime.now().isoformat()
                elif diferencia < 0:
                    accion = "reembolso"
                    metodo_ajuste = data.reembolsar_diferencia_metodo
                    if not metodo_ajuste:
                        metodo_ajuste = reserva.metodo_pago or "Saldo"
                    reembolso = round(abs(diferencia), 2)
                    reserva.monto_reembolsado = round(reembolsado_previo + reembolso, 2)
                    reserva.metodo_pago = metodo_ajuste
                    reserva.fecha_pago = datetime.datetime.now().isoformat()
                    norm_metodo = re.sub(r'[^A-Z]', '', str(metodo_ajuste).upper())
                    devolucion_a_saldo = norm_metodo in ("SALDO", "DIGITAL", "BILLETERA", "BILLETERAAUTOPASS")
                    if devolucion_a_saldo and reserva.user_id and reserva.user:
                        reserva.user.saldo += reembolso
                        puntos_desc = BillingService.calculate_points(reembolso)
                        reserva.user.puntos_acumulados = max(0, reserva.user.puntos_acumulados - puntos_desc)
                        db.add(models.PointsLog(
                            user_id=reserva.user_id, cantidad=-puntos_desc,
                            motivo=f"Reembolso por Edición de Reserva: {reserva.patente}",
                            fecha=datetime.datetime.now().isoformat()
                        ))
                else:
                    reserva.monto_total = monto
            else:
                reserva.monto_total = monto
            if data.metodo_pago and reserva.estado_pago == PaymentStatus.PENDIENTE:
                reserva.metodo_pago = data.metodo_pago
            db.commit()
            db.refresh(reserva)
            if reserva.user_id and reserva.user:
                from services.user_notification_service import UserNotificationService
                if accion == "cobro":
                    UserNotificationService.create_notification(
                        db, user_id=reserva.user_id, tipo=models.NotificationType.RESERVATION_MODIFIED,
                        titulo="Reserva modificada por administrador",
                        mensaje=f"Tu reserva para {reserva.patente} fue actualizada. Se registró un cobro de ${diferencia:,.2f} por la diferencia ({metodo_ajuste or 'Caja'}).",
                        reserva_id=reserva.id
                    )
                elif accion == "reembolso":
                    UserNotificationService.create_notification(
                        db, user_id=reserva.user_id, tipo=models.NotificationType.RESERVATION_MODIFIED,
                        titulo="Reserva modificada por administrador",
                        mensaje=(f"Tu reserva para {reserva.patente} fue actualizada. Se te reembolsaron ${abs(diferencia):,.2f} a tu saldo."
                                 if devolucion_a_saldo
                                 else f"Tu reserva para {reserva.patente} fue actualizada. Se te devolvieron ${abs(diferencia):,.2f} en efectivo."),
                        reserva_id=reserva.id
                    )
                else:
                    UserNotificationService.create_notification(
                        db, user_id=reserva.user_id, tipo=models.NotificationType.RESERVATION_MODIFIED,
                        titulo="Reserva modificada por administrador",
                        mensaje=f"Tu reserva para {reserva.patente} fue actualizada: del {reserva.fecha_inicio} al {reserva.fecha_fin} en {reserva.sucursal_nombre}.",
                        reserva_id=reserva.id
                    )
            return {
                "status": "ok", "id": reserva.id, "monto": reserva.monto_total,
                "monto_anterior": monto_anterior, "diferencia": diferencia,
                "accion": accion, "metodo_pago": metodo_ajuste or reserva.metodo_pago,
                "reembolsado_total": reserva.monto_reembolsado or 0.0
            }
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    def confirm_reservation_payment(db: Session, staff, res_id: int, data=None) -> dict:
        reserva = ReservationService.get_reservation_or_404(db, res_id)
        if staff.rol != UserRole.ADMIN and reserva.sucursal_nombre != staff.sucursal:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
        metodo = (data.metodo_pago if data else None) or "Caja"
        redemption_ticket_id = (data.redemption_ticket_id if data else None)
        result = ReservationService.pay_reservation_manual(db, reserva, metodo, redemption_ticket_id)
        if reserva.user:
            from services.user_notification_service import UserNotificationService
            UserNotificationService.create_notification(
                db, user_id=reserva.user.id,
                tipo=models.NotificationType.RESERVATION_CONFIRMED,
                titulo="Pago confirmado",
                mensaje=f"El pago de tu reserva #{res_id} ({reserva.patente}) fue confirmado por administrador.",
                reserva_id=res_id
            )
        return {"status": "ok", "message": result["message"], "monto": result["monto"],
                "descuento": result["descuento"], "monto_a_cobrar": result["monto_a_cobrar"]}
