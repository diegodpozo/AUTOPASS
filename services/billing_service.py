import datetime
import math
from sqlalchemy.orm import Session
import models

from core.config import settings
from services.time_service import TimeService

# --- SERVICIO DE FACTURACION Y PUNTOS ---

from models.enums import VehicleType

class BillingService:
    @staticmethod
    def get_rate(db: Session, tipo: str = "hora", sucursal: str = None, tipo_vehiculo: VehicleType = VehicleType.AUTO) -> float:
        """OBTIENE LA TARIFA CONFIGURADA SEGUN LA MODALIDAD DE ESTADIA, SEDE Y TIPO DE VEHICULO."""
        from core.cache import ttl_cache
        v_str = tipo_vehiculo.value if hasattr(tipo_vehiculo, "value") else str(tipo_vehiculo)
        cache_key = f"rate_get_{tipo}_{sucursal}_{v_str}"
        cached = ttl_cache.get(cache_key)
        if cached is not None:
            return cached

        setting_map = {
            "hora": "precio_hora",
            "dia": "precio_dia",
            "semana": "precio_semana",
            "quincena": "precio_quincena",
            "mes": "precio_mes",
        }
        clave = setting_map.get(tipo, "precio_hora")
        
        # AJUSTAR CLAVE SEGUN TIPO DE VEHICULO
        if tipo_vehiculo == VehicleType.MOTO:
            clave = f"{clave}_moto"
        elif tipo_vehiculo == VehicleType.CAMIONETA:
            clave = f"{clave}_camioneta"
        
        # BUSCAR TARIFA POR SEDE
        setting = db.query(models.Settings).filter(
            models.Settings.clave == clave,
            models.Settings.sucursal == sucursal
        ).first()
        
        #FALLBACK UN GLOBAL SI NO HAY SEDE ESPECIFICA
        if not setting and sucursal:
            setting = db.query(models.Settings).filter(
                models.Settings.clave == clave,
                models.Settings.sucursal == None
            ).first()
            
        val = float(setting.valor) if setting else settings.DEFAULT_BASE_RATE
        ttl_cache.set(cache_key, val, ttl=300.0)
        return val

    @staticmethod
    def get_hourly_rate(db: Session, sucursal: str = None, tipo_vehiculo: str = "Auto") -> float:
        """ACCESO RAPIDO A LA TARIFA POR HORA BASE."""
        from core.cache import ttl_cache
        cache_key = f"rate_hourly_{sucursal}_{tipo_vehiculo}"
        cached = ttl_cache.get(cache_key)
        if cached is not None:
            return cached

        clave = "precio_hora"
        if tipo_vehiculo == "Moto":
            clave = "precio_hora_moto"
        elif tipo_vehiculo == "Camioneta":
            clave = "precio_hora_camioneta"

        setting = db.query(models.Settings).filter(
            models.Settings.clave == clave,
            models.Settings.sucursal == sucursal
        ).first()
        
        if not setting and sucursal:
            setting = db.query(models.Settings).filter(
                models.Settings.clave == clave,
                models.Settings.sucursal == None
            ).first()
            
        val = float(setting.valor) if setting else settings.DEFAULT_HOURLY_RATE
        ttl_cache.set(cache_key, val, ttl=300.0)
        return val

    @staticmethod
    def get_30min_rate(db: Session, sucursal: str = None, tipo_vehiculo: str = "Auto") -> float:
        """TARIFA DE LA FRACCION DE 30 MIN. SI NO ESTA CONFIGURADA, USA LA MITAD DE LA TARIFA HORA."""
        from core.cache import ttl_cache
        cache_key = f"rate_30min_{sucursal}_{tipo_vehiculo}"
        cached = ttl_cache.get(cache_key)
        if cached is not None:
            return cached

        clave = "precio_30min"
        if tipo_vehiculo == "Moto":
            clave = "precio_30min_moto"
        elif tipo_vehiculo == "Camioneta":
            clave = "precio_30min_camioneta"

        setting = db.query(models.Settings).filter(
            models.Settings.clave == clave,
            models.Settings.sucursal == sucursal
        ).first()

        if not setting and sucursal:
            setting = db.query(models.Settings).filter(
                models.Settings.clave == clave,
                models.Settings.sucursal == None
            ).first()

        # FALLBACK: MITAD DE LA TARIFA POR HORA
        val = float(setting.valor) if setting else (BillingService.get_hourly_rate(db, sucursal=sucursal, tipo_vehiculo=tipo_vehiculo) / 2)
        ttl_cache.set(cache_key, val, ttl=300.0)
        return val

    @staticmethod
    def calculate_debt(entry_time_str: str, db: Session, sucursal: str = None, tipo_vehiculo: str = "Auto") -> float:
        """CALCULA LA DEUDA ACUMULADA BASADA EN BLOQUES DE 30 MIN, SEDE Y TIPO DE VEHICULO."""
        tarifa_30min = BillingService.get_30min_rate(db, sucursal=sucursal, tipo_vehiculo=tipo_vehiculo)
        entrada_dt = datetime.datetime.fromisoformat(entry_time_str)
        
        delta = TimeService.now() - entrada_dt
        horas_transcurridas = delta.total_seconds() / 3600
        
        # COBRO POR BLOQUES DE 30 MIN (REDONDEO HACIA ARRIBA, MINIMO 1 BLOQUE)
        bloques_a_cobrar = max(1, math.ceil(horas_transcurridas * 2))
        return float(bloques_a_cobrar * tarifa_30min)

    @staticmethod
    def calculate_total_amount(db: Session, tipo_estadia: str, fecha_inicio: str, fecha_fin: str, sucursal: str = None, tipo_vehiculo: VehicleType = VehicleType.AUTO) -> float:
        """CALCULA EL MONTO TOTAL BASADO EN LA DURACION Y EL TIPO DE ESTADIA."""
        start = datetime.datetime.fromisoformat(fecha_inicio)
        end = datetime.datetime.fromisoformat(fecha_fin)
        duration_hours = (end - start).total_seconds() / 3600
        
        if duration_hours <= 0:
            return 0.0
            
        rate = BillingService.get_rate(db, tipo_estadia, sucursal=sucursal, tipo_vehiculo=tipo_vehiculo)
        v_str = tipo_vehiculo.value if hasattr(tipo_vehiculo, "value") else str(tipo_vehiculo)
        tarifa_30min = BillingService.get_30min_rate(db, sucursal=sucursal, tipo_vehiculo=v_str)
        
        if tipo_estadia == "hora":
            return float(max(1, math.ceil(duration_hours * 2)) * tarifa_30min)
        elif tipo_estadia == "dia":
            return float(max(1, math.ceil(duration_hours / 24)) * rate)
        elif tipo_estadia == "semana":
            return float(math.ceil(duration_hours / (24 * 7)) * rate)
        elif tipo_estadia == "quincena":
            return float(math.ceil(duration_hours / (24 * 15)) * rate)
        elif tipo_estadia == "mes":
            return float(math.ceil(duration_hours / (24 * 30)) * rate)
        else:
            return float(math.ceil(duration_hours) * rate)

    @staticmethod
    def calculate_points(amount: float) -> int:
        """CALCULA LOS PUNTOS AUTOPASS GANADOS (10 PTS POR CADA $1000 ABONADOS)."""
        puntos = int(amount / 100) #EQUIVALE UN (MONTO / 1000) * 10
        return max(1, puntos) if amount > 0 else 0

    @staticmethod
    def apply_stay_mp_payment(db: Session, user, log: "models.AccessLog", monto: float) -> dict:
        """MARCA UNA ESTADIA COMO PAGADA POR MERCADO PAGO (CHECKOUT PRO) SIN DESCONTAR SALDO."""
        if log.pago_confirmado:
            return {"status": "ok", "message": "La estadía ya ha sido abonada", "aplicado": False}

        log.pago_confirmado = True
        log.metodo_pago = "MERCADOPAGO"
        log.costo_estadia = monto
        log.fecha_pago = datetime.datetime.now().isoformat()

        # ACREDITACION DE BENEFICIOS POR FIDELIZACION
        vehiculo = db.query(models.Vehicle).filter(models.Vehicle.patente == log.patente_detectada).first()
        puntos_ganados = BillingService.calculate_points(monto)
        if vehiculo and vehiculo.owner:
            vehiculo.owner.puntos_acumulados += puntos_ganados
            db.add(models.PointsLog(
                user_id=vehiculo.owner.id,
                cantidad=puntos_ganados,
                motivo=f"Estadía abonada (Mercado Pago): {log.patente_detectada}",
                fecha=datetime.datetime.now().isoformat()
            ))
        elif user:
            user.puntos_acumulados += puntos_ganados
            db.add(models.PointsLog(
                user_id=user.id,
                cantidad=puntos_ganados,
                motivo=f"Estadía abonada (Mercado Pago): {log.patente_detectada}",
                fecha=datetime.datetime.now().isoformat()
            ))

        db.commit()
        return {"status": "ok", "monto_cobrado": monto, "puntos_ganados": puntos_ganados, "aplicado": True}

    @staticmethod
    def process_payment(db: Session, plate: str, metodo: str = "DIGITAL") -> dict:
        """PROCESA EL COBRO DE UNA ESTADIA PENDIENTE EN LA SEDE CORRESPONDIENTE."""
        from models.enums import ReservationStatus, PaymentStatus

        log = db.query(models.AccessLog).filter(
            models.AccessLog.patente_detectada == plate,
            models.AccessLog.tipo_evento == "ENTRADA"
        ).order_by(models.AccessLog.id.desc()).first()

        if not log:
            return {"status": "error", "message": "No se encontraron estadías pendientes de pago"}

        # SI YA ESTA PAGADO, VERIFICAR SI TIENE RESERVA VENCIDA (EXTRA TIME)
        if log.pago_confirmado:
            if log.reserva_id:
                r = db.query(models.Reservation).filter(models.Reservation.id == log.reserva_id).first()
                if r:
                    now_str = TimeService.now_str()
                    if not (r.estado_reserva in [ReservationStatus.COMPLETADA, ReservationStatus.CANCELADA] or r.fecha_fin < now_str):
                        return {"status": "error", "message": "La reserva sigue vigente"}
                    # RESERVA VENCIDA: cobrar desde fecha_fin
                    monto_real = BillingService.calculate_debt(r.fecha_fin, db, sucursal=log.sucursal, tipo_vehiculo=log.tipo_vehiculo)
                    log.costo_estadia = (log.costo_estadia or 0) + monto_real
                    log.fecha_pago = datetime.datetime.now().isoformat()
                    log.pago_confirmado = True
                    log.metodo_pago = metodo
                    
                    puntos_ganados = 0
                    vehiculo = db.query(models.Vehicle).filter(models.Vehicle.patente == plate).first()
                    if vehiculo and vehiculo.owner:
                        puntos_ganados = BillingService.calculate_points(monto_real)
                        vehiculo.owner.puntos_acumulados += puntos_ganados
                        db.add(models.PointsLog(
                            user_id=vehiculo.owner.id,
                            cantidad=puntos_ganados,
                            motivo=f"Extra por reserva vencida: {plate}",
                            fecha=datetime.datetime.now().isoformat()
                        ))
                    db.commit()
                    return {"status": "ok", "monto_cobrado": monto_real, "puntos_ganados": puntos_ganados}
            return {"status": "error", "message": "No se encontraron estadías pendientes de pago"}

        monto_real = 0.0
        motivo_puntos = f"Estadía abonada: {plate}"
        now_str = TimeService.now_str()
        if log.reserva_id:
            r = db.query(models.Reservation).filter(models.Reservation.id == log.reserva_id).first()
            if r and r.estado_pago != PaymentStatus.PAGADO:
                # RESERVA IMPAGA QUE YA INGRESÓ: COBRAR MONTO DE LA RESERVA + EXTRA ACUMULADO SI VENCIÓ
                monto_real = (r.monto_total or 0)
                if r.fecha_fin < now_str:
                    monto_real += BillingService.calculate_debt(r.fecha_fin, db, sucursal=log.sucursal, tipo_vehiculo=log.tipo_vehiculo)
                # MARCAR LA RESERVA COMO PAGADA (SE ABONÓ EN EL PREDIO)
                r.estado_pago = PaymentStatus.PAGADO
                if r.estado_reserva == ReservationStatus.PENDIENTE:
                    r.estado_reserva = ReservationStatus.ACTIVA
                r.fecha_pago = datetime.datetime.now().isoformat()
                r.metodo_pago = metodo
                motivo_puntos = f"Reserva abonada en predio: {plate}"
            elif r and r.fecha_fin < now_str:
                # RESERVA YA PAGADA (ONLINE) PERO EL LOG NO: COBRAR SOLO EL EXTRA ACUMULADO
                monto_real = BillingService.calculate_debt(r.fecha_fin, db, sucursal=log.sucursal, tipo_vehiculo=log.tipo_vehiculo)
        else:
            monto_real = BillingService.calculate_debt(log.fecha_hora, db, sucursal=log.sucursal, tipo_vehiculo=log.tipo_vehiculo)
        
        # CONFIRMACION DE PAGO EN EL LOG
        log.pago_confirmado = True
        log.metodo_pago = metodo
        log.costo_estadia = (log.costo_estadia or 0) + monto_real
        log.fecha_pago = datetime.datetime.now().isoformat()
        
        # ACREDITACION DE BENEFICIOS POR FIDELIZACION
        vehiculo = db.query(models.Vehicle).filter(models.Vehicle.patente == plate).first()
        puntos_ganados = 0
        if vehiculo and vehiculo.owner:
            puntos_ganados = BillingService.calculate_points(monto_real)
            vehiculo.owner.puntos_acumulados += puntos_ganados
            
            db.add(models.PointsLog(
                user_id=vehiculo.owner.id,
                cantidad=puntos_ganados,
                motivo=motivo_puntos,
                fecha=datetime.datetime.now().isoformat()
            ))
        
        db.commit()
        return {"status": "ok", "monto_cobrado": monto_real, "puntos_ganados": puntos_ganados}
