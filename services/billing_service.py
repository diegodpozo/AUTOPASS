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
            
        return float(setting.valor) if setting else settings.DEFAULT_BASE_RATE

    @staticmethod
    def get_hourly_rate(db: Session, sucursal: str = None, tipo_vehiculo: str = "Auto") -> float:
        """ACCESO RAPIDO A LA TARIFA POR HORA BASE."""
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
            
        return float(setting.valor) if setting else settings.DEFAULT_HOURLY_RATE

    @staticmethod
    def calculate_debt(entry_time_str: str, db: Session, sucursal: str = None, tipo_vehiculo: str = "Auto") -> float:
        """CALCULA LA DEUDA ACUMULADA BASADA EN BLOQUES DE HORAS, SEDE Y TIPO DE VEHICULO."""
        precio_hora = BillingService.get_hourly_rate(db, sucursal=sucursal, tipo_vehiculo=tipo_vehiculo)
        entrada_dt = datetime.datetime.fromisoformat(entry_time_str)
        
        delta = TimeService.now() - entrada_dt
        horas_transcurridas = delta.total_seconds() / 3600
        
        # COBRO POR BLOQUES DE HORA (REDONDEO HACIA ARRIBA, MINIMO 1 HORA)
        bloques_a_cobrar = max(1, math.ceil(horas_transcurridas))
        return float(bloques_a_cobrar * precio_hora)

    @staticmethod
    def calculate_total_amount(db: Session, tipo_estadia: str, fecha_inicio: str, fecha_fin: str, sucursal: str = None, tipo_vehiculo: VehicleType = VehicleType.AUTO) -> float:
        """CALCULA EL MONTO TOTAL BASADO EN LA DURACION Y EL TIPO DE ESTADIA."""
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
        """CALCULA LOS PUNTOS AUTOPASS GANADOS (10 PTS POR CADA $1000 ABONADOS)."""
        puntos = int(amount / 100) #EQUIVALE UN (MONTO / 1000) * 10
        return max(1, puntos) if amount > 0 else 0

    @staticmethod
    def process_payment(db: Session, plate: str) -> dict:
        """PROCESA EL COBRO DE UNA ESTADIA PENDIENTE EN LA SEDE CORRESPONDIENTE."""
        log = db.query(models.AccessLog).filter(
            models.AccessLog.patente_detectada == plate,
            models.AccessLog.tipo_evento == "ENTRADA",
            models.AccessLog.pago_confirmado == False
        ).order_by(models.AccessLog.id.desc()).first()

        if not log:
            return {"status": "error", "message": "No se encontraron estadías pendientes de pago"}

        monto_real = BillingService.calculate_debt(log.fecha_hora, db, sucursal=log.sucursal, tipo_vehiculo=log.tipo_vehiculo)
        
        # CONFIRMACION DE PAGO EN EL LOG
        log.pago_confirmado = True
        log.metodo_pago = "DIGITAL"
        log.costo_estadia = monto_real
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
                motivo=f"Estadía abonada: {plate}",
                fecha=datetime.datetime.now().isoformat()
            ))
        
        db.commit()
        return {"status": "ok", "monto_cobrado": monto_real, "puntos_ganados": puntos_ganados}
