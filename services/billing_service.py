import datetime
import math
from sqlalchemy.orm import Session
import models

from core.config import settings

# --- SERVICIO DE FACTURACIÓN Y PUNTOS ---

from models.enums import VehicleType

class BillingService:
    @staticmethod
    def get_rate(db: Session, tipo: str = "hora", sucursal: str = None, tipo_vehiculo: VehicleType = VehicleType.AUTO) -> float:
        """Obtiene la tarifa configurada según la modalidad de estadía, sede y tipo de vehículo."""
        setting_map = {
            "hora": "precio_hora",
            "dia": "precio_dia",
            "semana": "precio_semana",
            "quincena": "precio_quincena",
            "mes": "precio_mes",
        }
        clave = setting_map.get(tipo, "precio_hora")
        
        # Si es moto, buscamos la clave específica (ej: precio_hora_moto)
        if tipo_vehiculo == VehicleType.MOTO:
            clave = f"{clave}_moto"
        
        # Buscar tarifa por sede
        setting = db.query(models.Settings).filter(
            models.Settings.clave == clave,
            models.Settings.sucursal == sucursal
        ).first()
        
        # Fallback a global si no hay sede específica
        if not setting and sucursal:
            setting = db.query(models.Settings).filter(
                models.Settings.clave == clave,
                models.Settings.sucursal == None
            ).first()
            
        return float(setting.valor) if setting else settings.DEFAULT_BASE_RATE

    @staticmethod
    def get_hourly_rate(db: Session, sucursal: str = None, tipo_vehiculo: str = "Auto") -> float:
        """Acceso rápido a la tarifa por hora base."""
        clave = "precio_hora"
        if tipo_vehiculo == "Moto":
            clave = "precio_hora_moto"

        setting = db.query(models.Settings).filter(
            models.Settings.clave == clave,
            models.Settings.sucursal == sucursal
        ).first()
        
        if not setting and sucursal:
            setting = db.query(models.Settings).filter(
                models.Settings.clave == clave,
                models.Settings.sucursal == None
            ).first()
            
        return float(setting.valor) if setting else settings.DEFAULT_HOURLY_RATE

    @staticmethod
    def calculate_debt(entry_time_str: str, db: Session, sucursal: str = None, tipo_vehiculo: str = "Auto") -> float:
        """Calcula la deuda acumulada basada en bloques de horas, sede y tipo de vehículo."""
        precio_hora = BillingService.get_hourly_rate(db, sucursal=sucursal, tipo_vehiculo=tipo_vehiculo)
        entrada_dt = datetime.datetime.fromisoformat(entry_time_str)
        
        delta = datetime.datetime.now() - entrada_dt
        horas_transcurridas = delta.total_seconds() / 3600
        
        # Cobro por bloques de hora (redondeo hacia arriba, mínimo 1 hora)
        bloques_a_cobrar = max(1, math.ceil(horas_transcurridas))
        return float(bloques_a_cobrar * precio_hora)

    @staticmethod
    def calculate_total_amount(db: Session, tipo_estadia: str, fecha_inicio: str, fecha_fin: str, sucursal: str = None, tipo_vehiculo: VehicleType = VehicleType.AUTO) -> float:
        """Calcula el monto total basado en la duración y el tipo de estadía."""
        start = datetime.datetime.fromisoformat(fecha_inicio)
        end = datetime.datetime.fromisoformat(fecha_fin)
        duration_hours = (end - start).total_seconds() / 3600
        
        if duration_hours <= 0:
            return 0.0
            
        rate = BillingService.get_rate(db, tipo_estadia, sucursal=sucursal, tipo_vehiculo=tipo_vehiculo)
        
        if tipo_estadia == "hora":
            return float(math.ceil(duration_hours) * rate)
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
        """Calcula los puntos AutoPass ganados (10 pts por cada $1000 abonados)."""
        puntos = int(amount / 100) # Equivale a (monto / 1000) * 10
        return max(1, puntos) if amount > 0 else 0

    @staticmethod
    def process_payment(db: Session, plate: str) -> dict:
        """Procesa el cobro de una estadía pendiente en la sede correspondiente."""
        log = db.query(models.AccessLog).filter(
            models.AccessLog.patente_detectada == plate,
            models.AccessLog.tipo_evento == "ENTRADA",
            models.AccessLog.pago_confirmado == False
        ).order_by(models.AccessLog.id.desc()).first()

        if not log:
            return {"status": "error", "message": "No se encontraron estadías pendientes de pago"}

        monto_real = BillingService.calculate_debt(log.fecha_hora, db, sucursal=log.sucursal, tipo_vehiculo=log.tipo_vehiculo)
        
        # Confirmación de pago en el log
        log.pago_confirmado = True
        log.metodo_pago = "DIGITAL"
        log.costo_estadia = monto_real
        log.fecha_pago = datetime.datetime.now().isoformat()
        
        # Acreditación de beneficios por fidelización
        vehiculo = db.query(models.Vehicle).filter(models.Vehicle.patente == plate).first()
        puntos_ganados = 0
        if vehiculo and vehiculo.owner:
            puntos_ganados = BillingService.calculate_points(monto_real)
            vehiculo.owner.puntos_acumulados += puntos_ganados
            
            db.add(models.PointsLog(
                user_id=vehiculo.owner.id,
                cantidad=puntos_ganados,
                motivo=f"Estadía abonada: {plate}",
                fecha=datetime.datetime.now().isoformat()
            ))
        
        db.commit()
        return {"status": "ok", "monto_cobrado": monto_real, "puntos_ganados": puntos_ganados}
