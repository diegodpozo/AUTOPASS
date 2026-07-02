from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from core.database import Base

class User(Base):
    """MODELO PARA LA GESTION DE USUARIOS Y ADMINISTRADORES."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
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

class Vehicle(Base):
    """ENTIDAD PARA LA GESTION DE FLOTA POR USUARIO."""
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    patente = Column(String, unique=True, index=True)
    marca_modelo = Column(String)
    tipo = Column(String, default="Auto") # 'AUTO' O 'MOTO'
    is_favorite = Column(Boolean, default=False)

    owner = relationship("User", back_populates="vehicles")

class PointsLog(Base):
    """HISTORIAL DE MOVIMIENTOS DEL SISTEMA DE FIDELIZACION."""
    __tablename__ = "points_log"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    cantidad = Column(Integer)
    motivo = Column(String)
    fecha = Column(String)

    user = relationship("User", back_populates="points_logs")

class Promotion(Base):
    """CATALOGO DE BENEFICIOS CANJEABLES POR PUNTOS."""
    __tablename__ = "promotions"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String)
    descripcion = Column(String)
    costo_puntos = Column(Integer)
    icono = Column(String, default="fas fa-gift")
    categoria = Column(String, default="Beneficio")
    activa = Column(Boolean, default=True, server_default="1")
    sucursal = Column(String, nullable=True) # NONE PARA GLOBAL, O NOMBRE DE LA SEDE
