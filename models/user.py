from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from core.database import Base
import datetime


def datetime_now_iso():
    return datetime.datetime.now().isoformat()


class User(Base):
    """MODELO PARA LA GESTION DE USUARIOS Y ADMINISTRADORES."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    apellido = Column(String)
    dni = Column(String, unique=True, index=True)
    telefono = Column(String)
    email = Column(String, unique=True, index=True)
    patente = Column(String, nullable=True) # REFERENCIA RAPIDA DE PATENTE PRINCIPAL
    direccion = Column(String, nullable=True)
    password_hash = Column(String)
    rol = Column(String, default="user") #'ADMIN', 'LOCAL_ADMIN', 'STAFF', 'USER'
    sucursal = Column(String, nullable=True) #NONE PARA ADMIN GLOBAL, O NOMBRE DE LA SEDE
    puntos_acumulados = Column(Integer, default=0)
    saldo = Column(Float, default=0.0)
    is_blocked = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    # RELACIONES
    vehicles = relationship("Vehicle", back_populates="owner")
    reservations = relationship("Reservation", back_populates="user")
    points_logs = relationship("PointsLog", back_populates="user")
    redemption_tickets = relationship("RedemptionTicket", back_populates="user")

class Vehicle(Base):
    """ENTIDAD PARA LA GESTION DE FLOTA POR USUARIO."""
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    patente = Column(String, unique=True, index=True)
    marca_modelo = Column(String)
    tipo = Column(String, default="Auto") # 'AUTO' O 'MOTO'
    is_favorite = Column(Boolean, default=False)

    owner = relationship("User", back_populates="vehicles")

class PointsLog(Base):
    """HISTORIAL DE MOVIMIENTOS DEL SISTEMA DE FIDELIZACION."""
    __tablename__ = "points_log"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    cantidad = Column(Integer)
    motivo = Column(String)
    fecha = Column(String)

    user = relationship("User", back_populates="points_logs")

class Promotion(Base):
    """CATALOGO DE BENEFICIOS CANJEABLES POR PUNTOS."""
    __tablename__ = "promotions"
    id = Column(Integer, primary_key=True)
    titulo = Column(String)
    descripcion = Column(String)
    costo_puntos = Column(Integer)
    icono = Column(String, default="fas fa-gift")
    categoria = Column(String, default="Beneficio")
    activa = Column(Boolean, default=True, server_default="1")
    sucursal = Column(String, nullable=True) # NONE PARA GLOBAL, O NOMBRE DE LA SEDE
    # TIPO DE CANJE: 'descuento_reserva' (% de descuento en estacionamiento, impacta en pago)
    #                o 'voucher' (genera un ticket con QR, sin validación automática)
    tipo_canje = Column(String, default="voucher")
    # PORCENTAJE DE DESCUENTO (solo aplica a tipo_canje == 'descuento_reserva')
    valor_descuento = Column(Integer, nullable=True)
    # UBICACION DONDE SE CANJEA EL BENEFICIO (seleccionada en el mapa al crear/editar)
    direccion = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

class RedemptionTicket(Base):
    """VOUCHER/TICKET PERSISTENTE GENERADO AL CANJEAR PUNTOS POR UN BENEFICIO."""
    __tablename__ = "redemption_tickets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    promotion_id = Column(Integer, ForeignKey("promotions.id"), nullable=True)
    codigo = Column(String, unique=True, index=True)  # TOKEN UNICO PARA EL QR
    titulo = Column(String)                            # SNAPSHOT DEL BENEFICIO
    descripcion = Column(String)
    tipo_canje = Column(String, default="voucher")     # SNAPSHOT DEL TIPO DE CANJE
    valor_descuento = Column(Integer, nullable=True)   # SNAPSHOT DEL % SI APLICA
    icono = Column(String, default="fas fa-gift")
    sucursal = Column(String, nullable=True)           # SEDE (global o especifica)
    estado = Column(String, default="VIGENTE")         # VIGENTE / USADO / CANCELADO
    qr_data = Column(String)                           # CONTENIDO DEL QR (AUTOPASS_REDEMPTION|...)
    observacion = Column(String, nullable=True)        # 'Válido por 30 días' etc.
    created_at = Column(String, default=datetime_now_iso)
    fecha_uso = Column(String, nullable=True)
    reserva_id = Column(Integer, nullable=True)        # RESERVA A LA QUE SE APLICO (si aplica)

    # SNAPSHOT DE LA UBICACION DEL CANJE (para el botón de Google Maps en la card del voucher)
    direccion = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    user = relationship("User", back_populates="redemption_tickets")

    @property
    def fecha_vencimiento(self):
        if not self.created_at:
            return None
        try:
            dt = datetime.datetime.fromisoformat(self.created_at)
            return (dt + datetime.timedelta(days=30)).isoformat()
        except Exception:
            return None
