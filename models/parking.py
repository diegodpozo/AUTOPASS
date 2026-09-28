from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from core.database import Base

class ParkingAforo(Base):
    """CONTROL DE CAPACIDAD Y OCUPACION EN TIEMPO REAL."""
    __tablename__ = "parking_aforo"
    id = Column(Integer, primary_key=True)
    capacidad_total = Column(Integer, default=20) # PARA AUTOS
    ocupacion_actual = Column(Integer, default=0) # PARA AUTOS
    capacidad_motos = Column(Integer, default=10)
    ocupacion_motos = Column(Integer, default=0)
    capacidad_camionetas = Column(Integer, default=5)
    ocupacion_camionetas = Column(Integer, default=0)
    capacidad_reservas_autos = Column(Integer, default=5)
    ocupacion_reservas_autos = Column(Integer, default=0)
    capacidad_reservas_motos = Column(Integer, default=3)
    ocupacion_reservas_motos = Column(Integer, default=0)
    capacidad_reservas_camionetas = Column(Integer, default=2)
    ocupacion_reservas_camionetas = Column(Integer, default=0)
    capacidad_reservas = Column(Integer, default=10)
    ocupacion_reservas = Column(Integer, default=0)
    ultima_actualizacion = Column(String)
    sucursal = Column(String, unique=True, nullable=True)

class Settings(Base):
    """CONFIGURACIONES GLOBALES DEL SISTEMA (PRECIOS, PARAMETROS)."""
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    clave = Column(String) # REMOVIDO UNIQUE=TRUE PARA PERMITIR VARIANTES POR SEDE
    valor = Column(Float, nullable=True)
    valor_str = Column(String, nullable=True) # PARA CONFIGURACIONES DE TEXTO (IPS, ETC)
    sucursal = Column(String, nullable=True) #NONE = CONFIGURACION GLOBAL

class ParkingCamera(Base):
    """CONFIGURACION DE CAMARAS DE MONITOREO DEL ESTACIONAMIENTO."""
    __tablename__ = "parking_cameras"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String, nullable=False) # 'ENTRADA', 'SALIDA', 'PREDIO', 'PATENTE', 'QR'
    source = Column(String, nullable=False) # IP de camara, path de video o id de camara web (ej. "0")
    sucursal = Column(String, nullable=True) # Aislamiento por sucursal
    activa = Column(Boolean, default=True)


class AccessLog(Base):
    """AUDITORIA VISUAL Y CRONOLOGICA DE ACCESOS (ALPR)."""
    __tablename__ = "access_logs"
    __table_args__ = (
        Index("ix_access_logs_pat_tipo_suc_fecha", "patente_detectada", "tipo_evento",
              "sucursal", "fecha_hora"),
        Index("ix_access_logs_reserva_id", "reserva_id", "tipo_evento"),
    )
    id = Column(Integer, primary_key=True)
    patente_detectada = Column(String)
    normalized_patente = Column(String, index=True, nullable=True)
    tipo_evento = Column(String, index=True) # 'ENTRADA' O 'SALIDA'
    tipo_vehiculo = Column(String, default="Auto") # 'AUTO' O 'MOTO'
    reserva_id = Column(Integer, ForeignKey("reservations.id"), nullable=True)
    floor_id = Column(Integer, ForeignKey("parking_floors.id"), nullable=True)
    fecha_hora = Column(String)
    fecha_pago = Column(String, nullable=True) # NUEVA COLUMNA PARA REPORTES FINANCIEROS
    imagen_path = Column(String, nullable=True)
    pago_confirmado = Column(Boolean, default=False)
    metodo_pago = Column(String, nullable=True) # 'DIGITAL' O 'CAJA'
    costo_estadia = Column(Float, default=0.0)
    sucursal = Column(String, nullable=True, index=True)
    ocr_time = Column(Float, nullable=True)

    reservation = relationship("Reservation", back_populates="access_logs")
    floor = relationship("ParkingFloor")

class ParkingBranch(Base):
    """PUNTOS AUTOPASS (SEDES/SUCURSALES)"""
    __tablename__ = "parking_branches"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, index=True)
    direccion = Column(String)
    telefono = Column(String)
    horario = Column(String) #EJ: "07:00 UN 23:00"
    is_24h = Column(Boolean, default=False)
    logo_url = Column(String, nullable=True) # NUEVA COLUMNA PARA LOGOS
    activa = Column(Boolean, default=True) # NUEVA COLUMNA PARA ESTADO DE LA SEDE
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    floors = relationship("ParkingFloor", back_populates="branch", cascade="all, delete-orphan")

class ParkingFloor(Base):
    """PISOS O NIVELES DENTRO DE UNA SUCURSAL."""
    __tablename__ = "parking_floors"
    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("parking_branches.id"))
    nombre = Column(String) # EJ: "PISO 1", "SUBSUELO"
    capacidad_total = Column(Integer, default=20)
    ocupacion_actual = Column(Integer, default=0)
    capacidad_motos = Column(Integer, default=10)
    ocupacion_motos = Column(Integer, default=0)
    capacidad_camionetas = Column(Integer, default=5)
    ocupacion_camionetas = Column(Integer, default=0)
    capacidad_reservas_autos = Column(Integer, default=5)
    ocupacion_reservas_autos = Column(Integer, default=0)
    capacidad_reservas_motos = Column(Integer, default=3)
    ocupacion_reservas_motos = Column(Integer, default=0)
    capacidad_reservas_camionetas = Column(Integer, default=2)
    ocupacion_reservas_camionetas = Column(Integer, default=0)
    capacidad_reservas = Column(Integer, default=10)
    ocupacion_reservas = Column(Integer, default=0)

    branch = relationship("ParkingBranch", back_populates="floors")
