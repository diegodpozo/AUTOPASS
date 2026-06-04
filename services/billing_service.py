import datetime
import math
from sqlalchemy.orm import Session
import models

from core.config import settings

# --- SERVICIO DE FACTURACIÓN Y PUNTOS ---

class BillingService:
    @staticmethod
    def get_rate(db: Session, tipo: str = "hora", sucursal: str = None) -> float:
        """Obtiene la tarifa configurada según la modalidad de estadía y sede."""
        setting_map = {
            "hora": "precio_hora",
            "dia": "precio_dia",
            "semana": "precio_semana",
            "quincena": "precio_quincena",
            "mes": "precio_mes",
        }
        clave = setting_map.get(tipo, "precio_hora")
        
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
    def get_hourly_rate(db: Session, sucursal: str = None) -> float:
        """Acceso rápido a la tarifa por hora base."""
        setting = db.query(models.Settings).filter(
            models.Settings.clave == "precio_hora",
            models.Settings.sucursal == sucursal
        ).first()
        
        if not setting and sucursal:
            setting = db.query(models.Settings).filter(
                models.Settings.clave == "precio_hora",
                models.Settings.sucursal == None
            ).first()
            
        return float(setting.valor) if setting else settings.DEFAULT_HOURLY_RATE

    @staticmethod
    def calculate_debt(entry_time_str: str, db: Session, sucursal: str = None) -> float:
        """Calcula la deuda acumulada basada en bloques de horas y sede."""
        precio_hora = BillingService.get_hourly_rate(db, sucursal=sucursal)
        entrada_dt = datetime.datetime.fromisoformat(entry_time_str)
        
        delta = datetime.datetime.now() - entrada_dt
        horas_transcurridas = delta.total_seconds() / 3600
        
        # Cobro por bloques de hora (redondeo hacia arriba, mínimo 1 hora)
        bloques_a_cobrar = max(1, math.ceil(horas_transcurridas))
        return float(bloques_a_cobrar * precio_hora)

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

        monto_real = BillingService.calculate_debt(log.fecha_hora, db, sucursal=log.sucursal)
        
        # Confirmación de pago en el log
        log.pago_confirmado = True
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
