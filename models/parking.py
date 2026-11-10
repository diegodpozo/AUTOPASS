'''Modelos fisicos del estacionamiento: aforo, configuracion, camaras, logs de acceso, sucursales'''


from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Index, CheckConstraint, text
									# Importa de SQLAlchemy los tipos de columna y
									# utilidades: Column, Integer, String, Float,
									# ForeignKey, Boolean, Index, CheckConstraint y
									# text
from sqlalchemy.orm import relationship					# Importa `relationship` para declarar relaciones
									# entre entidades
from core.database import Base						# Importa `Base`, la clase base declarativa de la
									# que heredan todos los modelos
from models.types import DateTimeValue, MONEY_ZERO, MoneyValue					# Tipos compartidos para fechas y dinero
from models.branch_ref import branch_ref_property			# Importa `branch_ref_property`, un helper que
									# expone la sede como propiedad reutilizable

class ParkingAforo(Base):						# Define el modelo `ParkingAforo` (control de
									# capacidad y ocupacion)
    """CONTROL DE CAPACIDAD Y OCUPACION EN TIEMPO REAL."""
    __tablename__ = "parking_aforo"					# Fija el nombre de la tabla en la base de datos:
									# `parking_aforo`
    __table_args__ = (							# Empieza `__table_args__`, donde se declaran
									# constraints e indices de la tabla
        CheckConstraint(						# Inicia un `CheckConstraint` que impedira valores
									# negativos en capacidad/ocupacion
            "COALESCE(capacidad_total, 0) >= 0 AND COALESCE(ocupacion_actual, 0) >= 0 AND "
									# Impone que capacidad y ocupacion de autos no sean
									# negativas (COALESCE evita nulos)
            "COALESCE(capacidad_motos, 0) >= 0 AND COALESCE(ocupacion_motos, 0) >= 0 AND "
									# Impone no-negatividad para capacidad y ocupacion
									# de motos
            "COALESCE(capacidad_camionetas, 0) >= 0 AND COALESCE(ocupacion_camionetas, 0) >= 0 AND "
									# Impone no-negatividad para capacidad y ocupacion
									# de camionetas
            "COALESCE(capacidad_reservas_autos, 0) >= 0 AND COALESCE(ocupacion_reservas_autos, 0) >= 0 AND "
									# Impone no-negatividad para capacidad y ocupacion
									# de reservas de autos
            "COALESCE(capacidad_reservas_motos, 0) >= 0 AND COALESCE(ocupacion_reservas_motos, 0) >= 0 AND "
									# Impone no-negatividad para capacidad y ocupacion
									# de reservas de motos
            "COALESCE(capacidad_reservas_camionetas, 0) >= 0 AND COALESCE(ocupacion_reservas_camionetas, 0) >= 0 AND "
									# Impone no-negatividad para capacidad y ocupacion
									# de reservas de camionetas
            "COALESCE(capacidad_reservas, 0) >= 0 AND COALESCE(ocupacion_reservas, 0) >= 0",
									# Impone no-negatividad para capacidad y ocupacion
									# general de reservas
            name="ck_parking_aforo_nonneg"),				# Le da al constraint el nombre
									# `ck_parking_aforo_nonneg` para poder
									# referenciarlo
    )									# Cierra la tupla `__table_args__`
    id = Column(Integer, primary_key=True)				# Define la clave primaria `id` autoincremental
    capacidad_total = Column(Integer, default=20) # PARA AUTOS
    ocupacion_actual = Column(Integer, default=0) # PARA AUTOS
    capacidad_motos = Column(Integer, default=10)			# Define `capacidad_motos` con 10 plazas por
									# defecto
    ocupacion_motos = Column(Integer, default=0)			# Define `ocupacion_motos` con 0 por defecto
    capacidad_camionetas = Column(Integer, default=5)			# Define `capacidad_camionetas` con 5 plazas por
									# defecto
    ocupacion_camionetas = Column(Integer, default=0)			# Define `ocupacion_camionetas` con 0 por defecto
    capacidad_reservas_autos = Column(Integer, default=5)		# Define `capacidad_reservas_autos` con 5 plazas
									# por defecto
    ocupacion_reservas_autos = Column(Integer, default=0)		# Define `ocupacion_reservas_autos` con 0 por
									# defecto
    capacidad_reservas_motos = Column(Integer, default=3)		# Define `capacidad_reservas_motos` con 3 plazas
									# por defecto
    ocupacion_reservas_motos = Column(Integer, default=0)		# Define `ocupacion_reservas_motos` con 0 por
									# defecto
    capacidad_reservas_camionetas = Column(Integer, default=2)		# Define `capacidad_reservas_camionetas` con 2
									# plazas por defecto
    ocupacion_reservas_camionetas = Column(Integer, default=0)		# Define `ocupacion_reservas_camionetas` con 0 por
									# defecto
    capacidad_reservas = Column(Integer, default=10)			# Define `capacidad_reservas` (total de reservas)
									# con 10 por defecto
    ocupacion_reservas = Column(Integer, default=0)			# Define `ocupacion_reservas` (total de reservas
									# ocupadas) con 0 por defecto
    ultima_actualizacion = Column(DateTimeValue)				# Fecha/hora del ultimo cambio de aforo
    organization_id = Column(Integer, ForeignKey("organizations.id", name="fk_parking_aforo_organization_id_org",
									# Define `organization_id` como FK a
									# `organizations.id`, para el aislamiento
									# multiempresa
                                                 onupdate="CASCADE"), nullable=True, index=True)
									# Cierra la definicion de la FK de organizacion
									# (con onupdate CASCADE e indice)
    sucursal_id = Column(Integer, ForeignKey("parking_branches.id", name="fk_parking_aforo_sucursal_id_branch",
									# Define `sucursal_id` como FK a
									# `parking_branches.id`, con borrado en cascada
                                             onupdate="CASCADE", ondelete="CASCADE"), nullable=True, unique=True)
									# Cierra la FK de sucursal, marcada unique (un
									# aforo por sede) y con cascada

    branch = relationship("ParkingBranch", lazy="joined")		# Declara la relacion `branch` con `ParkingBranch`,
									# cargada ansiosamente con `lazy='joined'`
    sucursal = branch_ref_property()					# Expone `sucursal` como propiedad reutilizable via
									# `branch_ref_property()`

class Settings(Base):							# Define el modelo `Settings` para configuraciones
									# globales (precios, parametros)
    """CONFIGURACIONES GLOBALES DEL SISTEMA (PRECIOS, PARAMETROS)."""
    __tablename__ = "settings"						# Fija el nombre de tabla `settings`
    __table_args__ = (							# Empieza `__table_args__` de Settings
        CheckConstraint("COALESCE(valor, 0) >= 0", name="ck_settings_valor_nonneg"),
									# Impone con CheckConstraint que `valor` no sea
									# negativo
        # UNICIDAD DE CLAVE POR SEDE Y ORGANIZACION (MULTIEMPRESA): LA SUCURSAL/GLOBAL
        # NULL CUENTA COMO VALOR PROPIO DE CADA ORGANIZACION, PARA QUE CADA EMPRESA
        # TENGA SU PROPIO TARIFARIO GLOBAL SIN COLISIONAR CON OTRA
        Index("uq_settings_clave_sucursal_org", text("clave"), text("COALESCE(sucursal_id, -1)"),
									# Crea un indice unico sobre `clave` + sucursal +
									# organizacion (usando COALESCE para nulos)
              text("COALESCE(organization_id, -1)"), unique=True),	# Cierra el indice unico
									# `uq_settings_clave_sucursal_org`
    )									# Cierra `__table_args__` de Settings
    id = Column(Integer, primary_key=True)				# Define la clave primaria `id`
    clave = Column(String) # REMOVIDO UNIQUE=TRUE PARA PERMITIR VARIANTES POR SEDE
    valor = Column(MoneyValue, nullable=True)				# Valor monetario nullable de la configuracion
    valor_str = Column(String, nullable=True) # PARA CONFIGURACIONES DE TEXTO (IPS, ETC)
    organization_id = Column(Integer, ForeignKey("organizations.id", name="fk_settings_organization_id_org",
									# Define `organization_id` como FK a organizaciones
									# para el aislamiento multiempresa
                                                 onupdate="CASCADE"), nullable=True, index=True)
									# Cierra la FK de organizacion de Settings (con
									# onupdate CASCADE e indice)
    sucursal_id = Column(Integer, ForeignKey("parking_branches.id", name="fk_settings_sucursal_id_branch",
									# Define `sucursal_id` como FK a parking_branches,
									# con cascada de borrado
                                             onupdate="CASCADE", ondelete="CASCADE"), nullable=True, index=True)
									# Cierra la FK de sucursal (con onupdate/ondelete
									# CASCADE e indice)

    branch = relationship("ParkingBranch", lazy="joined")		# Declara la relacion `branch` con `ParkingBranch`,
									# cargada con join
    sucursal = branch_ref_property()					# Expone `sucursal` via `branch_ref_property()`

class ParkingCamera(Base):						# Define el modelo `ParkingCamera` (camaras de
									# monitoreo del estacionamiento)
    """CONFIGURACION DE CAMARAS DE MONITOREO DEL ESTACIONAMIENTO."""
    __tablename__ = "parking_cameras"					# Fija el nombre de tabla `parking_cameras`
    id = Column(Integer, primary_key=True)				# Define la clave primaria `id`
    nombre = Column(String, nullable=False)				# Define `nombre` de la camara, obligatorio
    tipo = Column(String, nullable=False) # 'ENTRADA', 'SALIDA', 'PREDIO', 'PATENTE', 'QR'
    source = Column(String, nullable=False) # IP de camara, path de video o id de camara web (ej. "0")
    sucursal_id = Column(Integer, ForeignKey("parking_branches.id", name="fk_parking_cameras_sucursal_id_branch",
									# Define `sucursal_id` como FK a parking_branches
									# con borrado en cascada
                                             onupdate="CASCADE", ondelete="CASCADE"), nullable=True, index=True)
									# Cierra la FK de sucursal de la camara
    activa = Column(Boolean, default=True)				# Define `activa` con True por defecto, para
									# habilitar o deshabilitar la camara
    orden = Column(Integer, nullable=True) # Posición manual en la grilla de monitoreo (NULL = sin ordenar, va al final)

    branch = relationship("ParkingBranch", lazy="joined")		# Declara la relacion `branch` con `ParkingBranch`,
									# cargada con join
    sucursal = branch_ref_property()					# Expone `sucursal` via `branch_ref_property()`


class AccessLog(Base):							# Define el modelo `AccessLog` (auditoria de
									# accesos ALPR)
    """AUDITORIA VISUAL Y CRONOLOGICA DE ACCESOS (ALPR)."""
    __tablename__ = "access_logs"					# Fija el nombre de tabla `access_logs`
    __table_args__ = (							# Empieza `__table_args__` de AccessLog
        Index("ix_access_logs_pat_tipo_suc_fecha", "patente_detectada", "tipo_evento",
									# Crea un indice compuesto por patente, tipo de
									# evento, sucursal y fecha para consultas rapidas
              "sucursal_id", "fecha_hora"),				# Cierra el indice compuesto
									# `ix_access_logs_pat_tipo_suc_fecha`
        Index("ix_access_logs_reserva_id", "reserva_id", "tipo_evento"),
									# Crea un indice por reserva_id y tipo de evento
        CheckConstraint("COALESCE(costo_estadia, 0) >= 0", name="ck_access_logs_costo_estadia_nonneg"),
									# Impone con CheckConstraint que `costo_estadia` no
									# sea negativo
    )									# Cierra `__table_args__` de AccessLog
    id = Column(Integer, primary_key=True)				# Define la clave primaria `id`
    patente_detectada = Column(String)					# Define `patente_detectada`, el texto crudo leido
									# por el OCR
    normalized_patente = Column(String, index=True, nullable=True)	# Define `normalized_patente` (patente
									# normalizada), indexada para busquedas
    tipo_evento = Column(String, index=True) # 'ENTRADA' O 'SALIDA'
    tipo_vehiculo = Column(String, default="Auto") # 'AUTO' O 'MOTO'
    reserva_id = Column(Integer, ForeignKey("reservations.id"), nullable=True)
									# Define `reserva_id` como FK opcional a
									# `reservations.id`
    floor_id = Column(Integer, ForeignKey("parking_floors.id"), nullable=True)
									# Define `floor_id` como FK opcional a
									# `parking_floors.id`
    fecha_hora = Column(DateTimeValue)
    fecha_pago = Column(DateTimeValue, nullable=True) # NUEVA COLUMNA PARA REPORTES FINANCIEROS
    imagen_path = Column(String, nullable=True)				# Define `imagen_path`, la ruta de la foto de
									# evidencia (nullable)
    pago_confirmado = Column(Boolean, default=False)			# Define `pago_confirmado` con False por defecto
    metodo_pago = Column(String, nullable=True) # 'DIGITAL' O 'CAJA'
    costo_estadia = Column(MoneyValue, default=MONEY_ZERO)
    sucursal_id = Column(Integer, ForeignKey("parking_branches.id", name="fk_access_logs_sucursal_id_branch",
									# Define `sucursal_id` como FK a parking_branches
									# para el aislamiento por sede
                                             onupdate="CASCADE"), nullable=True, index=True)
									# Cierra la FK de sucursal del log (con onupdate
									# CASCADE e indice)
    ocr_time = Column(Float, nullable=True)				# Define `ocr_time`, el tiempo que tardo el OCR
									# (para metricas)

    reservation = relationship("Reservation", back_populates="access_logs")
									# Declara la relacion `reservation` con
									# `Reservation` (bidireccional via access_logs)
    floor = relationship("ParkingFloor")				# Declara la relacion `floor` con `ParkingFloor`
    branch = relationship("ParkingBranch", lazy="joined")		# Declara la relacion `branch` con `ParkingBranch`,
									# cargada con join
    sucursal = branch_ref_property()					# Expone `sucursal` via `branch_ref_property()`

class ParkingBranch(Base):						# Define el modelo `ParkingBranch`
									# (sedes/sucursales de AUTOPASS)
    """PUNTOS AUTOPASS (SEDES/SUCURSALES)"""
    __tablename__ = "parking_branches"					# Fija el nombre de tabla `parking_branches`
    __table_args__ = (							# Empieza `__table_args__` de ParkingBranch
        # UNICIDAD DE NOMBRE POR ORGANIZACION (MULTIEMPRESA): DOS EMPRESAS PUEDEN
        # TENER UNA SEDE CON EL MISMO NOMBRE; DENTRO DE UNA MISMA EMPRESA NO
        Index("uq_parking_branches_nombre_org", text("nombre"),		# Crea un indice unico sobre `nombre` +
									# organizacion (COALESCE para nulos)
              text("COALESCE(organization_id, -1)"), unique=True),	# Cierra el indice unico
									# `uq_parking_branches_nombre_org`
    )									# Cierra `__table_args__`
    id = Column(Integer, primary_key=True)				# Define la clave primaria `id`
    nombre = Column(String, index=True)					# Define `nombre` de la sede, indexado
    organization_id = Column(Integer, ForeignKey("organizations.id", name="fk_parking_branches_organization_id_org",
									# Define `organization_id` como FK a
									# organizaciones, para multiempresa
                                                 onupdate="CASCADE"), nullable=True, index=True)
									# Cierra la FK de organizacion (con onupdate
									# CASCADE e indice)
    direccion = Column(String)						# Define `direccion` de la sede
    telefono = Column(String)						# Define `telefono` de la sede
    horario = Column(String) #EJ: "07:00 UN 23:00"
    is_24h = Column(Boolean, default=False)				# Define `is_24h` para marcar la sede como abierta
									# 24 horas (False por defecto)
    logo_url = Column(String, nullable=True) # NUEVA COLUMNA PARA LOGOS
    activa = Column(Boolean, default=True) # NUEVA COLUMNA PARA ESTADO DE LA SEDE
    latitude = Column(Float, nullable=True)				# Define `latitude` de la sede (nullable), util
									# para geolocalizacion
    longitude = Column(Float, nullable=True)				# Define `longitude` de la sede (nullable)

    floors = relationship("ParkingFloor", back_populates="branch", cascade="all, delete-orphan")
									# Declara la relacion `floors` con `ParkingFloor` y
									# borrado en cascada de los pisos

class ParkingFloor(Base):						# Define el modelo `ParkingFloor` (pisos o niveles
									# dentro de una sucursal)
    """PISOS O NIVELES DENTRO DE UNA SUCURSAL."""
    __tablename__ = "parking_floors"					# Fija el nombre de tabla `parking_floors`
    id = Column(Integer, primary_key=True)				# Define la clave primaria `id`
    branch_id = Column(Integer, ForeignKey("parking_branches.id"))	# Define `branch_id` como FK a parking_branches que
									# liga el piso a su sede
    nombre = Column(String) # EJ: "PISO 1", "SUBSUELO"
    capacidad_total = Column(Integer, default=20)			# Define `capacidad_total` de autos con 20 por
									# defecto
    ocupacion_actual = Column(Integer, default=0)			# Define `ocupacion_actual` de autos con 0 por
									# defecto
    capacidad_motos = Column(Integer, default=10)			# Define `capacidad_motos` con 10 por defecto
    ocupacion_motos = Column(Integer, default=0)			# Define `ocupacion_motos` con 0 por defecto
    capacidad_camionetas = Column(Integer, default=5)			# Define `capacidad_camionetas` con 5 por defecto
    ocupacion_camionetas = Column(Integer, default=0)			# Define `ocupacion_camionetas` con 0 por defecto
    capacidad_reservas_autos = Column(Integer, default=5)		# Define `capacidad_reservas_autos` con 5 por
									# defecto
    ocupacion_reservas_autos = Column(Integer, default=0)		# Define `ocupacion_reservas_autos` con 0 por
									# defecto
    capacidad_reservas_motos = Column(Integer, default=3)		# Define `capacidad_reservas_motos` con 3 por
									# defecto
    ocupacion_reservas_motos = Column(Integer, default=0)		# Define `ocupacion_reservas_motos` con 0 por
									# defecto
    capacidad_reservas_camionetas = Column(Integer, default=2)		# Define `capacidad_reservas_camionetas` con 2 por
									# defecto
    ocupacion_reservas_camionetas = Column(Integer, default=0)		# Define `ocupacion_reservas_camionetas` con 0 por
									# defecto
    capacidad_reservas = Column(Integer, default=10)			# Define `capacidad_reservas` (total) con 10 por
									# defecto
    ocupacion_reservas = Column(Integer, default=0)			# Define `ocupacion_reservas` (total) con 0 por
									# defecto

    branch = relationship("ParkingBranch", back_populates="floors")	# Declara la relacion `branch` con `ParkingBranch`
									# (lado inverso de `floors`)
