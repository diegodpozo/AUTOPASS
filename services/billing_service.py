import datetime
import math
from typing import Optional
from sqlalchemy.orm import Session
import models

from core.logger import get_logger
from services.time_service import TimeService
from repositories.access_log_repository import AccessRepository
from repositories.reservation_repository import ReservationRepository
from repositories.settings_repository import SettingsRepository
from repositories.vehicle_repository import VehicleRepository

# --- SERVICIO DE FACTURACION Y PUNTOS ---

from models.enums import VehicleType

logger = get_logger("BillingService")

class BillingService:
    @staticmethod
    def _tipo_key(tipo_vehiculo) -> str:
        """NORMALIZA EL TIPO DE VEHICULO A UNA CLAVE CANONICA ('Auto'/'Moto'/'Camioneta').
        Unifica 'MOTO', 'moto', 'Moto', 'camioneta', etc."""
        v_str = tipo_vehiculo.value if hasattr(tipo_vehiculo, "value") else str(tipo_vehiculo)
        v_low = v_str.strip().upper()
        if v_low in ("MOTO", "MOTOCICLETA"):
            return "Moto"
        if v_low in ("CAMIONETA", "CAMIONETAS", "UTILITARIO", "UTILITARIA"):
            return "Camioneta"
        return "Auto"

    @staticmethod
    def get_rate(db: Session, tipo: str = "hora", sucursal: str = None, tipo_vehiculo: VehicleType = VehicleType.AUTO) -> float:
        """OBTIENE LA TARIFA CONFIGURADA SEGUN LA MODALIDAD DE ESTADIA, SEDE Y TIPO DE VEHICULO."""
        from core.cache import ttl_cache
        v_str = BillingService._tipo_key(tipo_vehiculo)
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
        if v_str == "Moto":
            clave = f"{clave}_moto"
        elif v_str == "Camioneta":
            clave = f"{clave}_camioneta"
        
        # TARIFA ESTRICTA POR SEDE: SI LA SUCURSAL NO TIENE TARIFA PROPIA NO HAY PRECIO
        # (no se hereda la global ni se inventa un DEFAULT). Si sucursal=None se usa la global.
        setting = SettingsRepository.get_by_clave_and_sucursal(db, clave, sucursal=sucursal)

        if not setting:
            return None
        val = float(setting.valor)
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
        if BillingService._tipo_key(tipo_vehiculo) == "Moto":
            clave = "precio_hora_moto"
        elif BillingService._tipo_key(tipo_vehiculo) == "Camioneta":
            clave = "precio_hora_camioneta"

        setting = SettingsRepository.get_by_clave_and_sucursal(db, clave, sucursal=sucursal)

        if not setting:
            return None
        val = float(setting.valor)
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
        if BillingService._tipo_key(tipo_vehiculo) == "Moto":
            clave = "precio_30min_moto"
        elif BillingService._tipo_key(tipo_vehiculo) == "Camioneta":
            clave = "precio_30min_camioneta"

        setting = SettingsRepository.get_by_clave_and_sucursal(db, clave, sucursal=sucursal)

        # FALLBACK: MITAD DE LA TARIFA POR HORA (solo si la hora existe; si no, no hay precio)
        tarifa_hora = BillingService.get_hourly_rate(db, sucursal=sucursal, tipo_vehiculo=tipo_vehiculo)
        if not setting and tarifa_hora is None:
            return None
        val = float(setting.valor) if setting else (tarifa_hora / 2)
        ttl_cache.set(cache_key, val, ttl=300.0)
        return val

    @staticmethod
    def calculate_debt(entry_time_str: str, db: Session, sucursal: str = None, tipo_vehiculo: str = "Auto") -> Optional[float]:
        """CALCULA LA DEUDA ACUMULADA BASADA EN BLOQUES DE 30 MIN, SEDE Y TIPO DE VEHICULO.
        Devuelve None si la sucursal no tiene tarifario configurado (no inventa precio)."""
        tarifa_30min = BillingService.get_30min_rate(db, sucursal=sucursal, tipo_vehiculo=tipo_vehiculo)
        if tarifa_30min is None:
            return None
        entrada_dt = datetime.datetime.fromisoformat(entry_time_str)
        
        delta = TimeService.now() - entrada_dt
        horas_transcurridas = delta.total_seconds() / 3600
        
        # COBRO POR BLOQUES DE 30 MIN (REDONDEO HACIA ARRIBA, MINIMO 1 BLOQUE)
        bloques_a_cobrar = max(1, math.ceil(horas_transcurridas * 2))
        return float(bloques_a_cobrar * tarifa_30min)

    @staticmethod
    def calculate_total_amount(db: Session, tipo_estadia: str, fecha_inicio: str, fecha_fin: str, sucursal: str = None, tipo_vehiculo: VehicleType = VehicleType.AUTO) -> Optional[float]:
        """CALCULA EL MONTO TOTAL BASADO EN LA DURACION Y EL TIPO DE ESTADIA.
        Devuelve None si la sucursal no tiene tarifario configurado (no inventa precio)."""
        start = datetime.datetime.fromisoformat(fecha_inicio)
        end = datetime.datetime.fromisoformat(fecha_fin)
        duration_hours = (end - start).total_seconds() / 3600
        
        if duration_hours <= 0:
            return 0.0
            
        rate = BillingService.get_rate(db, tipo_estadia, sucursal=sucursal, tipo_vehiculo=tipo_vehiculo)
        tarifa_30min = BillingService.get_30min_rate(db, sucursal=sucursal, tipo_vehiculo=tipo_vehiculo)
        if rate is None or tarifa_30min is None:
            return None
        
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
        vehiculo = VehicleRepository.get_by_patente(db, log.patente_detectada)
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
        target_user = (vehiculo.owner if (vehiculo and vehiculo.owner) else user)
        if target_user:
            try:
                from services.user_notification_service import UserNotificationService
                UserNotificationService.create_notification(
                    db, target_user.id,
                    tipo=models.NotificationType.STAY_PAID,
                    titulo="Estadía abonada con Mercado Pago",
                    mensaje=f"Se confirmó el pago de ${monto:,.2f} para tu estadía con patente {log.patente_detectada} en {log.sucursal or 'nuestra sede'}."
                )
                if puntos_ganados > 0:
                    UserNotificationService.create_notification(
                        db, target_user.id,
                        tipo=models.NotificationType.POINTS_EARNED,
                        titulo="¡Puntos AutoPass!",
                        mensaje=f"¡Ganaste {puntos_ganados} puntos por abonar tu estadía ({log.patente_detectada})!"
                    )
            except Exception:
                logger.warning("[BILLING] Error notificando puntos ganados en estadía", exc_info=True)

        db.commit()
        return {"status": "ok", "monto_cobrado": monto, "puntos_ganados": puntos_ganados, "aplicado": True}

    @staticmethod
    def _extra_vencimiento_ya_cobrado(log, fecha_fin: str) -> bool:
        """INDICA SI EL EXTRA POR RESERVA VENCIDA YA FUE COBRADO PARA ESTA ESTADIA.

        El extra se cobra una sola vez y cubre el tramo desde fecha_fin hasta el momento
        del cobro. Si el log ya fue pagado DESPUES de que la reserva vencio, ese tramo ya
        esta incluido en el pago anterior y volver a acumularlo cobraria de nuevo al mismo
        cliente por el mismo periodo.
        """
        if not log.fecha_pago or not fecha_fin:
            return False
        try:
            pago_dt = datetime.datetime.fromisoformat(str(log.fecha_pago).replace(" ", "T"))
            fin_dt = datetime.datetime.fromisoformat(str(fecha_fin).replace(" ", "T"))
        except ValueError:
            return False
        return pago_dt > fin_dt

    @staticmethod
    def process_payment(db: Session, plate: str, metodo: str = "DIGITAL") -> dict:
        """PROCESA EL COBRO DE UNA ESTADIA PENDIENTE EN LA SEDE CORRESPONDIENTE."""
        from models.enums import ReservationStatus, PaymentStatus

        log = AccessRepository.get_last_entry_by_patente(db, plate)

        if not log:
            return {"status": "error", "message": "No se encontraron estadías pendientes de pago"}

        # SI YA ESTA PAGADO, VERIFICAR SI TIENE RESERVA VENCIDA (EXTRA TIME)
        if log.pago_confirmado:
            if log.reserva_id:
                r = ReservationRepository.get_by_id(db, log.reserva_id)
                if r:
                    now_str = TimeService.now_str()
                    if not (r.estado_reserva in [ReservationStatus.COMPLETADA, ReservationStatus.CANCELADA] or r.fecha_fin < now_str):
                        return {"status": "error", "message": "La reserva sigue vigente"}
                    if BillingService._extra_vencimiento_ya_cobrado(log, r.fecha_fin):
                        return {"status": "ok", "message": "El extra por reserva vencida ya fue cobrado", "monto_cobrado": 0.0, "puntos_ganados": 0, "aplicado": False}
                    # RESERVA VENCIDA: cobrar desde fecha_fin
                    monto_real = BillingService.calculate_debt(r.fecha_fin, db, sucursal=log.sucursal, tipo_vehiculo=log.tipo_vehiculo)
                    if monto_real is None:
                        return {"status": "error", "message": "Tarifas no configuradas en la sucursal. Configurá el tarifario antes de cobrar."}
                    log.costo_estadia = (log.costo_estadia or 0) + monto_real
                    log.fecha_pago = TimeService.now().isoformat()
                    log.pago_confirmado = True
                    log.metodo_pago = metodo
                    
                    puntos_ganados = 0
                    vehiculo = VehicleRepository.get_by_patente(db, plate)
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
            r = ReservationRepository.get_by_id(db, log.reserva_id)
            if r and r.estado_pago != PaymentStatus.PAGADO:
                # RESERVA IMPAGA QUE YA INGRESÓ: COBRAR MONTO DE LA RESERVA + EXTRA ACUMULADO SI VENCIÓ
                monto_real = (r.monto_total or 0)
                if r.fecha_fin < now_str:
                    monto_extra = BillingService.calculate_debt(r.fecha_fin, db, sucursal=log.sucursal, tipo_vehiculo=log.tipo_vehiculo)
                    if monto_extra is None:
                        return {"status": "error", "message": "Tarifas no configuradas en la sucursal. Configurá el tarifario antes de cobrar."}
                    monto_real += monto_extra
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
                if monto_real is None:
                    return {"status": "error", "message": "Tarifas no configuradas en la sucursal. Configurá el tarifario antes de cobrar."}
        else:
            monto_real = BillingService.calculate_debt(log.fecha_hora, db, sucursal=log.sucursal, tipo_vehiculo=log.tipo_vehiculo)
            if monto_real is None:
                return {"status": "error", "message": "Tarifas no configuradas en la sucursal. Configurá el tarifario antes de cobrar."}
        
        # CONFIRMACION DE PAGO EN EL LOG
        log.pago_confirmado = True
        log.metodo_pago = metodo
        log.costo_estadia = (log.costo_estadia or 0) + monto_real
        log.fecha_pago = datetime.datetime.now().isoformat()
        
        # ACREDITACION DE BENEFICIOS POR FIDELIZACION Y NOTIFICACION
        vehiculo = VehicleRepository.get_by_patente(db, plate)
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

            # Notificación al titular del vehículo
            try:
                from services.user_notification_service import UserNotificationService
                UserNotificationService.create_notification(
                    db, vehiculo.owner.id,
                    tipo=models.NotificationType.STAY_PAID,
                    titulo="Estadía abonada",
                    mensaje=f"Se confirmó el pago de ${monto_real:,.2f} para tu vehículo con patente {plate} mediante {metodo}."
                )
                if puntos_ganados > 0:
                    UserNotificationService.create_notification(
                        db, vehiculo.owner.id,
                        tipo=models.NotificationType.POINTS_EARNED,
                        titulo="¡Puntos AutoPass!",
                        mensaje=f"¡Ganaste {puntos_ganados} puntos por abonar tu estadía ({plate})!"
                    )
            except Exception:
                logger.warning("[BILLING] Error notificando puntos ganados en estadía digital", exc_info=True)
        
        db.commit()
        return {"status": "ok", "monto_cobrado": monto_real, "puntos_ganados": puntos_ganados}
