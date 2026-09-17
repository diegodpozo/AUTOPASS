"""Disponibilidad de reservas: capacidad por tipo de vehículo, fechas/horas deshabilitadas y ocupación simultánea."""

import datetime
import time

from sqlalchemy.orm import Session, joinedload

import models
from core.config import settings
from models.enums import ReservationStatus, PaymentStatus
from services.time_service import TimeService


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