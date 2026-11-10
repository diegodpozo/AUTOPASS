'''operaciones de acceso al estacionamiento: validación de patente de entrada y salida, validación de pases QR '''


import datetime								# Importa el modulo estandar datetime, usado para
									# parsear las marcas de tiempo ISO de los AccessLog
									# y comparar tiempos de estadia
import json								# Importa el modulo estandar json, necesario para
									# serializar el payload que se publica por MQTT en
									# _publish_mqtt
import base64								# Importa base64 para decodificar la imagen JPEG
									# que llega desde el nodo ALPR y poder guardarla
									# como archivo
import os								# Importa os para construir rutas de archivos y
									# crear directorios (os.path.join, os.makedirs) al
									# guardar imagenes
from sqlalchemy.orm import Session					# Importa la clase Session de SQLAlchemy, el tipo
									# de sesion de base de datos que reciben todos los
									# metodos del servicio
from fastapi import Request, HTTPException				# Importa Request y HTTPException de FastAPI:
									# Request para acceder al estado de la app (p.ej
									# mqtt_client) y HTTPException para responder
									# errores HTTP
import models								# Importa el paquete models con los modelos ORM
									# (AccessLog, ParkingAforo, etc.) que representan
									# tablas de la base de datos
import schemas								# Importa el paquete schemas con los esquemas
									# Pydantic de entrada/salida (PlateValidation,
									# QRValidation, etc.)
from core.config import settings					# Importa settings, la configuracion central de la
									# app, del que se lee por ejemplo IMAGE_DIR
from core.logger import get_logger					# Importa get_logger, factory que crea loggers con
									# nombre para trazabilidad estandarizada
from models.enums import VehicleType, AccessEventType, ReservationStatus, PaymentStatus
from models.types import MONEY_ZERO, parse_fecha
									# Importa los enums de dominio (tipo de vehiculo,
									# tipo de evento de acceso, estado de reserva y
									# estado de pago) usados en las reglas de negocio
from services.access_occupancy import AccessOccupancyMixin		# Importa AccessOccupancyMixin, la clase base que
									# aporta los helpers de plazas y aforo
									# (capacidad_por_tipo, asignar_plaza,
									# liberar_plaza)
from services.notification_service import NotificationService		# Importa NotificationService, encargado de empujar
									# eventos al dashboard (ultimo evento, cambios de
									# ocupacion, salida impaga)
from services.time_service import TimeService				# Importa TimeService, la fuente unica de tiempo
									# del sistema (TimeService.now()), para no disparar
									# datetime.now() disperso
from core.normalize import normalize_name, normalize_plate, is_valid_plate
									# Importa los helpers de normalizacion:
									# normalize_name (nombres de sede), normalize_plate
									# (patentes) e is_valid_plate (validacion de
									# formato)
from repositories.access_log_repository import AccessRepository		# Importa AccessRepository, la capa de acceso a
									# datos de los AccessLog (ultimo ingreso, salida
									# posterior, etc.)
from repositories.branch_repository import BranchRepository		# Importa BranchRepository, repositorio de
									# sucursales, pisos y aforo de una sede
from repositories.reservation_repository import ReservationRepository	# Importa ReservationRepository, repositorio de
									# reservas (buscar por id, reservas vigentes por
									# patente)
from repositories.scoping import organization_of_sede			# Importa organization_of_sede, helper de scoping
									# multiempresa que resuelve la organizacion a la
									# que pertenece una sede
from repositories.vehicle_repository import VehicleRepository		# Importa VehicleRepository, repositorio de
									# vehiculos (tipo de vehiculo y dueno activo por
									# patente)
from repositories.user_repository import UserRepository			# Importa UserRepository, repositorio de usuarios,
									# usado para notificar al dueno registrado de una
									# estadia cancelada

logger = get_logger("AccessService")					# Crea el logger nombrado 'AccessService', usado en
									# todo el archivo para registrar debug, info,
									# warning y error

class AccessService(AccessOccupancyMixin):				# Declara la clase AccessService heredando de
									# AccessOccupancyMixin, reuniendo los flujos de
									# acceso fisico del sistema
    """Flujos de acceso físico: entrada/salida ALPR, QR de reservas y operaciones manuales."""

    @staticmethod							# Decorador que convierte _save_image en un metodo
									# estatico (no depende de la instancia ni de la
									# clase)
    def _save_image(plate: str, image_base64: str) -> str:		# Define _save_image(plate, image_base64): persiste
									# en disco la foto capturada por el nodo ALPR y
									# devuelve el nombre del archivo
        if not image_base64:						# Valida si no llego imagen (cadena vacia/None)
									# para evitar intentar decodificar base64
									# inexistente
            return None							# Si no hay imagen, retorna None, dejando el campo
									# imagen_path del AccessLog sin foto
        
        now = datetime.datetime.now()					# Obtiene la hora actual del sistema con
									# datetime.now() para nombrar el archivo con su
									# hora de captura
        img_name = f"{plate}_{now.strftime('%H%M%S')}.jpg"		# Construye el nombre del archivo combinando la
									# patente y la hora en formato HHMMSS (f-string)
									# para evitar colisiones
        if not os.path.exists(settings.IMAGE_DIR):			# Comprueba si el directorio configurado en
									# settings.IMAGE_DIR no existe
            os.makedirs(settings.IMAGE_DIR)				# Si no existe, lo crea recursivamente con
									# os.makedirs para garantizar el destino de la
									# imagen
            
        with open(os.path.join(settings.IMAGE_DIR, img_name), "wb") as f:
									# Abre en modo escritura binaria ('wb') el archivo
									# destino en IMAGE_DIR para volcar los bytes de la
									# imagen
            f.write(base64.b64decode(image_base64))			# Decodifica la cadena base64 recibida del nodo
									# ALPR y escribe los bytes resultantes en el
									# archivo de imagen
        return img_name							# Devuelve el nombre del archivo guardado, que se
									# almacenara en imagen_path del AccessLog

    @staticmethod							# Decorador que marca _publish_mqtt como metodo
									# estatico
    def _publish_mqtt(request: Request, topic: str, payload: dict):	# Define _publish_mqtt(request, topic, payload):
									# publica un mensaje MQTT usando el cliente
									# guardado en la app
        if request and hasattr(request.app, 'mqtt_client'):		# Verifica que exista el request y que la app tenga
									# un atributo mqtt_client antes de intentar
									# publicar (fail-safe)
            request.app.mqtt_client.publish(topic, json.dumps(payload))
									# Publica en el topic indicado el payload
									# serializado a JSON, integrando el backend con el
									# broker MQTT

    @staticmethod							# Decorador que marca _sede_desde_gate como metodo
									# estatico
    def _sede_desde_gate(db: Session, gate_id: str, organization_id=None):
									# Define _sede_desde_gate(db, gate_id,
									# organization_id=None): resuelve la sede
									# (ParkingBranch) a la que pertenece un gate ALPR
        """SEDE (ParkingBranch) A LA QUE PERTENECE UN GATE ALPR (prefijo antes del '_').

        Atribucion gate -> sede -> empresa: con `organization_id` (binding del nodo)
        solo busca entre las sedes de esa empresa; sin el, si varias empresas tienen
        una sede con ese prefijo devuelve None porque no seria atribuible a nadie."""
        if gate_id and '_' in gate_id:					# Verifica que el gate_id exista y contenga '_'
									# (formato SEDE_ENTRADA / SEDE_SALIDA)
            suc_short = normalize_name(gate_id.split('_')[0])		# Extrae el prefijo de sede (parte antes del '_'),
									# lo normaliza con normalize_name y lo asigna a
									# suc_short
            if suc_short:						# Comprueba que el prefijo normalizado no sea vacio
									# antes de buscar la sede
                try:							# Inicia un try para aislar posibles fallos de
									# acceso a datos durante la busqueda
                    candidatas = [					# Inicia la lista por comprension 'candidatas' con
									# las sedes cuyo nombre normalizado coincide con el
									# prefijo
                        b for b in BranchRepository.get_all(db, organization_id=organization_id)
									# Recorre todas las sedes del alcance
									# (BranchRepository.get_all con organization_id)
									# para filtrarlas
                        if normalize_name(b.nombre) == suc_short	# Condicion del filtro: la sede entra si su nombre
									# normalizado equivale a suc_short
                    ]							# Cierra la comprension de la lista de sedes
									# candidatas
                except Exception:					# Captura cualquier excepcion del acceso a datos al
									# buscar sedes
                    logger.warning("[ACCESS] Error buscando sucursal por gate_id", exc_info=True)
									# Registra un warning con traceback (exc_info=True)
									# indicando el error al buscar sucursal por
									# gate_id
                    return None						# Ante error, retorna None: se prefiere no resolver
									# sede antes que atribuirla mal
                if not candidatas:					# Si no hubo ninguna sede candidata, no hay
									# atribucion posible y retorna None
                    return None						# Retorna None cuando no existe sede con ese
									# prefijo
                if organization_id is not None:				# Si el nodo esta ligado a una empresa
									# (organization_id no es None), la sede candidata
									# ya es confiable
                    return candidatas[0]				# Retorna la primera (y unica) candidata dentro de
									# la empresa del nodo ALPR
                orgs = {b.organization_id for b in candidatas}		# Sin binding, reune el conjunto de organization_id
									# distintos entre todas las candidatas para
									# detectar ambiguedad
                return candidatas[0] if len(orgs) == 1 else None	# Devuelve la candidata solo si todas pertenecen a
									# una unica empresa (len(orgs)==1); si hay
									# ambiguedad multiempresa, retorna None
        return None							# Retorna None cuando el gate_id no tiene el
									# formato esperado (sin '_' o vacio)

    @staticmethod							# Decorador que marca _branch_from_gate_id como
									# metodo estatico
    def _branch_from_gate_id(db: Session, gate_id: str, organization_id=None) -> str:
									# Define _branch_from_gate_id(db, gate_id,
									# organization_id=None): obtiene el nombre completo
									# de la sucursal a partir del gate
        """Resuelve la sucursal completa a partir del prefijo del gate_id (ALPR)."""
        sede = AccessService._sede_desde_gate(db, gate_id, organization_id)
									# Delega en _sede_desde_gate para resolver el
									# objeto sede a partir del gate_id y el alcance de
									# organizacion
        return sede.nombre if sede else None				# Retorna el nombre de la sede si se resolvio, o
									# None si no hubo atribucion

    @staticmethod							# Decorador que marca _alcance_gate como metodo
									# estatico
    def _alcance_gate(db: Session, gate_id: str, organization_id=None):
									# Define _alcance_gate(db, gate_id,
									# organization_id=None): deriva el par (sede,
									# organizacion) para un flujo de acceso
        """(SEDE, ORGANIZACION) DERIVADOS DEL GATE PARA UN FLUJO DE ACCESO.

        Prioriza el binding de la organizacion del nodo ALPR; si no lo hay, la
        organizacion sale de la sede resuelta (gate -> sede -> empresa)."""
        sede = AccessService._sede_desde_gate(db, gate_id, organization_id)
									# Resuelve el objeto sede llamando a
									# _sede_desde_gate con el gate y el alcance de
									# organizacion
        if organization_id is None and sede is not None:		# Si no vino organization_id pero si se resolvio la
									# sede, se puede inferir la empresa desde la sede
            organization_id = sede.organization_id			# Asigna la organizacion de la sede al
									# organization_id derivado
        return sede, organization_id					# Retorna la tupla (sede, organization_id) ya
									# normalizada para el flujo de acceso

    @staticmethod							# Decorador que marca _alcance_logs como metodo
									# estatico
    def _alcance_logs(sucursal: str, organization_id=None):		# Define _alcance_logs(sucursal,
									# organization_id=None): calcula la organizacion
									# usada para filtrar logs
        """ORGANIZACION P/ FILTRAR LOGS: solo cuando hubo sede resuelta (si no no hay atribucion)."""
        return organization_id if sucursal else None			# Retorna organization_id si hay sucursal resuelta;
									# si no hay sede, retorna None para no acotar por
									# una empresa incierta

    @staticmethod							# Decorador que marca _unclosed_last_entry como
									# metodo estatico
    def _unclosed_last_entry(db: Session, p: str, sucursal: str, organization_id=None):
									# Define _unclosed_last_entry(db, p, sucursal,
									# organization_id=None): busca el ultimo ingreso
									# sin salida posterior de una patente
        """Último ingreso físico de la patente que no tiene salida posterior (sigue dentro)."""
        org_log = AccessService._alcance_logs(sucursal, organization_id)
									# Calcula el alcance de organizacion para los logs
									# segun la sede resuelta
        ultima_entrada = AccessRepository.get_last_entry(db, p, sucursal, organization_id=org_log)
									# Consulta el ultimo ingreso de la patente
									# (AccessRepository.get_last_entry) filtrando por
									# sucursal y organizacion
        if ultima_entrada:						# Si se encontro un ingreso previo, hay que
									# verificar que no haya salido despues
            tiene_salida = AccessRepository.get_exit_after(db, ultima_entrada.patente_detectada, ultima_entrada.id, sucursal, organization_id=org_log)
									# Consulta si existe una salida posterior a ese
									# ingreso (get_exit_after) para la misma patente y
									# sede
            if not tiene_salida:					# Si no existe salida posterior, significa que el
									# vehiculo sigue adentro
                return ultima_entrada					# Retorna ese ingreso abierto (vehiculo actualmente
									# dentro de la sede)
        return None							# Retorna None cuando no hay ingreso abierto (no
									# hay ultimo ingreso o ya salio)

    @staticmethod							# Decorador que marca _get_aforo como metodo
									# estatico
    def _get_aforo(db: Session, sucursal: str):				# Define _get_aforo(db, sucursal): obtiene el
									# registro de aforo (ocupacion/capacidad) de una
									# sede
        return BranchRepository.get_aforo_by_sucursal(db, sucursal)	# Delega en BranchRepository.get_aforo_by_sucursal
									# para leer el ParkingAforo de la sucursal

    @staticmethod							# Decorador que marca _get_or_create_aforo como
									# metodo estatico
    def _get_or_create_aforo(db: Session, sucursal: str):		# Define _get_or_create_aforo(db, sucursal):
									# devuelve el aforo de la sede, creandolo si no
									# existe
        aforo = AccessService._get_aforo(db, sucursal)			# Intenta obtener el aforo existente de la
									# sucursal
        if not aforo:							# Si no existe aforo previo para la sede, hay que
									# crear uno por defecto
            aforo = models.ParkingAforo(sucursal=sucursal, capacidad_total=20, ocupacion_actual=0, capacidad_motos=10, ocupacion_motos=0)
									# Instancia un ParkingAforo con capacidad por
									# defecto (20 autos, 10 motos) y ocupacion en cero
            db.add(aforo)						# Agrega el nuevo aforo a la sesion SQLAlchemy para
									# que se inserte al hacer commit
        return aforo							# Retorna el aforo existente o el recien creado
									# (aun sin commit, pendiente de persistir)

    @staticmethod							# Decorador que marca _suc_key como metodo
									# estatico
    def _suc_key(sucursal: str) -> str:					# Define _suc_key(sucursal): genera la clave
									# normalizada de sucursal usada como canal de
									# notificacion
        """Clave normalizada de sucursal para notificaciones (GLOBAL si es None)."""
        return normalize_name(sucursal) if sucursal else "GLOBAL"	# Retorna normalize_name(sucursal) si hay sucursal,
									# o la clave especial 'GLOBAL' para eventos no
									# atribuibles a una sede

    @classmethod							# Decorador que marca _emit_pending_exit como
									# metodo de clase (recibe cls)
    def _emit_pending_exit(cls, db: Session, log: models.AccessLog, plate: str, sucursal: str, data=None):
									# Define _emit_pending_exit(db, log, plate,
									# sucursal, data=None): emite al dashboard el
									# evento de salida con deuda pendiente
        """Avisa al dashboard (popup de caja) que un vehiculo intento salir con deuda pendiente.
        Incluye usuario registrado (o invitado), monto a cobrar, foto (id del log de entrada) y sucursal."""
        from services.billing_service import BillingService		# Importa localmente BillingService para calcular
									# el monto pendiente sin crear dependencia circular
									# a nivel de modulo
        try:								# Inicia un try para que cualquier fallo de calculo
									# o notificacion no rompa el flujo de salida
            deuda = BillingService.preview_pending_amount(db, log)	# Calcula la deuda pendiente del vehiculo con
									# BillingService.preview_pending_amount(db, log)
            usuario = None						# Inicializa usuario en None, el nombre del dueno
									# registrado que podria informarse en el popup
            vehiculo = VehicleRepository.get_by_normalized_patente_with_active_owner(db, plate)
									# Busca el vehiculo con su dueno activo
									# (get_by_normalized_patente_with_active_owner)
									# para resolver el titular
            if vehiculo and vehiculo.owner:				# Si el vehiculo existe y tiene un dueno asociado,
									# se arma el nombre del usuario
                usuario = " ".join(filter(None, [vehiculo.owner.nombre, vehiculo.owner.apellido])).strip() or vehiculo.owner.email
									# Concatena nombre y apellido del dueno (o usa su
									# email) como etiqueta del titular a mostrar
            tipo = log.tipo_vehiculo.value if hasattr(log.tipo_vehiculo, "value") else str(log.tipo_vehiculo)
									# Normaliza el tipo de vehiculo a string tomando su
									# .value si es un enum, para serializarlo en el
									# payload
            payload = {							# Comienza a construir el diccionario payload con
									# los datos que consumira el popup de caja
                "patente": plate,					# Agrega la patente al payload
                "log_id": log.id,					# Agrega log_id (id del AccessLog de entrada) que
									# el operador usara para vincular la foto
									# capturada
                "deuda": deuda,						# Agrega la deuda calculada
                "usuario": usuario,					# Agrega el nombre del usuario titular (o None si
									# es invitado)
                "es_registrado": bool(usuario),				# Agrega es_registrado, booleano que indica si el
									# vehiculo tiene dueno registrado
                "tipo_vehiculo": tipo,					# Agrega el tipo de vehiculo
                "sucursal": sucursal,					# Agrega la sucursal donde ocurre la salida impaga
                "gate_id": getattr(data, "gate_id", None) or "SALIDA",	# Agrega el gate_id tomado de data (o 'SALIDA' como
									# fallback) para que el popup sepa por donde
									# egreso
            }								# Cierra el diccionario payload
            NotificationService.notify_pending_exit(cls._suc_key(sucursal), payload)
									# Envia el evento al dashboard mediante
									# NotificationService.notify_pending_exit usando la
									# clave de sucursal
        except Exception:						# Captura cualquier excepcion durante el calculo o
									# la emision del evento
            logger.warning("[ACCESS] Error emitiendo evento de salida impaga", exc_info=True)
									# Registra un warning con traceback si fallo la
									# emision del evento de salida impaga, sin
									# interrumpir el flujo

    @classmethod							# Decorador que marca validate_plate como metodo de
									# clase
    def validate_plate(cls, db: Session, data: schemas.PlateValidation, request: Request = None, organization_id: int = None) -> dict:
									# Define validate_plate(db, data, request,
									# organization_id): flujo completo de ingreso ALPR
									# (validaciones, cupo, alta de log y apertura de
									# barrera)

        # Log request for debugging ALPR integration
        try:								# Inicia un try para que el logueo defensivo nunca
									# rompa el flujo de validacion
            logger.debug(f"validate_plate called. gate_id={getattr(data, 'gate_id', None)} plate_present={'plate' in data.__dict__}")
									# Loguea en nivel debug el gate_id y la presencia
									# de la patente, para depurar la integracion del
									# nodo ALPR
        except Exception:						# Captura cualquier excepcion al momento de generar
									# el log de depuracion
            logger.warning("[ACCESS] Error logueando validate_plate", exc_info=True)
									# Registra un warning con traceback si fallo el
									# logueo de validate_plate
        p = normalize_plate(data.plate)					# Normaliza la patente recibida con normalize_plate
									# para tratarla de forma canonica (mayusculas, sin
									# espacios ni guiones)
        sede, org = cls._alcance_gate(db, data.gate_id, organization_id)
									# Deriva el par (sede, org) del gate usando
									# _alcance_gate, aplicando el binding de la
									# organizacion del nodo
        if organization_id is not None and sede is None:		# Si el nodo esta ligado a una empresa
									# (organization_id no None) pero el gate no
									# pertenece a ninguna de sus sedes, se deniega
            # Nodo ligado a una empresa: un gate que no pertenece a ninguna de sus sedes
            return {"status": "denied", "message": "Gate no habilitado para esta organización"}
									# Retorna status 'denied' con mensaje de gate no
									# habilitado para la organizacion (fail-closed
									# multiempresa)
        sucursal = sede.nombre if sede else None			# Fija el nombre de sucursal a partir de la sede
									# resuelta (o None si el gate no tiene sede
									# atribuible)

        # RECHAZAR PATENTES CON FORMATO NO RECONOCIDO (NO GENERA REGISTRO)
        if not is_valid_plate(p):					# Valida el formato de la patente con
									# is_valid_plate; si no es valido, se rechaza
            NotificationService.set_last_event(cls._suc_key(sucursal), "error", p, "Formato de patente inválido", "error")
									# Publica al dashboard el ultimo evento como
									# 'error' por formato de patente invalido
            return {"status": "denied", "message": "Formato de patente inválido. Ingreso denegado"}
									# Retorna status 'denied' indicando patente
									# invalida e ingreso denegado

        ultima_entrada = cls._unclosed_last_entry(db, p, sucursal, organization_id=org)
									# Verifica si la patente ya tiene un ingreso
									# abierto en la sede (_unclosed_last_entry) para
									# evitar duplicar entradas
        if ultima_entrada:						# Si ya existe un ingreso abierto (vehiculo ya
									# adentro):
            NotificationService.set_last_event(cls._suc_key(sucursal), "error", p, "Vehículo ya dentro de esta sede", "error")
									# Notifica al dashboard el evento 'error' indicando
									# que el vehiculo ya esta dentro de la sede
            return {"status": "denied", "message": "El vehículo ya figura dentro de esta sede"}
									# Retorna 'denied' porque el vehiculo ya figura
									# dentro de esta sede
        
        # DETERMINAR TIPO DE VEHICULO (normalizando espacios en ambos lados)
        vehiculo = VehicleRepository.get_by_normalized_patente(db, p)	# Busca el vehiculo registrado por patente
									# normalizada para conocer su tipo
        tipo_vehiculo = vehiculo.tipo if vehiculo else VehicleType.AUTO
									# Asigna el tipo del vehiculo registrado o AUTO por
									# defecto si la patente no esta en el padron

        now = TimeService.now()						# Obtiene la hora actual via TimeService (fuente
									# unica de tiempo) para el registro del acceso
        img_name = cls._save_image(p, data.image_base64)		# Guarda la imagen del nodo ALPR llamando a
									# _save_image y obtiene el nombre del archivo
                
        # BUSCAMOS RESERVA VIGENTE (PAGADA O IMPAGA) QUE ESTE EN EL RANGO DE TIEMPO ACTUAL
        now_str = now.strftime("%Y-%m-%d %H:%M")			# Formatea la hora actual a 'YYYY-MM-DD HH:MM' para
									# comparar contra el rango de la reserva
        reserva = ReservationRepository.get_active_in_range_by_normalized_patente(db, p, now_str, sucursal, organization_id=org)
									# Busca una reserva activa por patente dentro del
									# rango horario y sede, filtrando por organizacion
									# (org)
        
        aforo = cls._get_or_create_aforo(db, sucursal)			# Obtiene (o crea) el registro de aforo de la sede
									# para gestionar la ocupacion
        
        # VALIDAR CAPACIDAD SEGUN TIPO
        capacidad, ocupacion = cls._capacidad_por_tipo(aforo, tipo_vehiculo)
									# Calcula la capacidad y la ocupacion actual del
									# tipo de vehiculo del ingreso (helper del
									# AccessOccupancyMixin)

        if reserva:							# Si el vehiculo tiene una reserva vigente, el
									# ingreso se maneja por la via reservada
            if reserva.estado_reserva == ReservationStatus.PENDIENTE:	# Si la reserva estaba en estado PENDIENTE al
									# llegar el vehiculo, se marca como ACTIVA
                reserva.estado_reserva = ReservationStatus.ACTIVA	# Actualiza el estado de la reserva a ACTIVA
									# (consumo de la reserva)
            cls._asignar_plaza(aforo, tipo_vehiculo, es_reserva=True)	# Asigna plaza reservando cupo (es_reserva=True)
									# descontando del aforo reservado
        elif ocupacion < capacidad:					# Si no hay reserva pero queda cupo disponible
									# (ocupacion < capacidad), se permite ingreso por
									# cupo libre
            cls._asignar_plaza(aforo, tipo_vehiculo, es_reserva=False)	# Asigna plaza como no-reserva (es_reserva=False),
									# sumando a la ocupacion general
        else:								# Si no hay reserva y no hay cupo, el ingreso debe
									# rechazarse por capacidad
            NotificationService.set_last_event(cls._suc_key(sucursal), "error", p, "Capacidad máxima alcanzada", "error")
									# Notifica al dashboard el evento 'error' de
									# capacidad maxima alcanzada
            return {"status": "denied", "message": "Capacidad máxima alcanzada en esta sede"}
									# Retorna 'denied' con mensaje de capacidad maxima
									# alcanzada en la sede
            
        db.add(models.AccessLog(					# Inserta un nuevo AccessLog de ENTRADA para dejar
									# registro del ingreso autorizado
            patente_detectada=p,					# Registra la patente detectada (normalizada) en el
									# log
            normalized_patente=p,					# Registra tambien la patente normalizada en su
									# columna dedicada para consultas indexadas
            tipo_evento=AccessEventType.ENTRADA,			# Marca el evento como ENTRADA
									# (AccessEventType.ENTRADA)
            tipo_vehiculo=tipo_vehiculo,				# Guarda el tipo de vehiculo determinado
            fecha_hora=now.isoformat(),					# Guarda la marca de tiempo del acceso en formato
									# ISO
            imagen_path=img_name,					# Guarda el nombre del archivo de imagen capturado
									# por el nodo ALPR
            reserva_id=reserva.id if reserva else None,			# Vincula el id de la reserva si el ingreso fue por
									# reserva, o None si fue por cupo libre
            pago_confirmado=True if (reserva and reserva.estado_pago == PaymentStatus.PAGADO) else False,
									# Marca pago_confirmado segun si la reserva
									# asociada estaba PAGADA al momento del ingreso
            sucursal=sucursal,						# Guarda la sucursal del acceso
            ocr_time=data.ocr_time					# Guarda el tiempo de OCR medido por el nodo ALPR
									# (data.ocr_time) para metricas de rendimiento
        ))								# Cierra la construccion del AccessLog
        db.commit()							# Confirma la transaccion, persistiendo el log de
									# entrada en la base de datos
        logger.info(f"Notificando cambio de aforo para sucursal={sucursal}")
									# Loguea que se notificara el cambio de aforo para
									# la sucursal
        NotificationService.set_last_event(cls._suc_key(sucursal), "INGRESO", p, f"Bienvenido {p}", "ok")
									# Publica el ultimo evento 'INGRESO' con mensaje de
									# bienvenida en el canal de la sucursal
        NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
									# Notifica el cambio de ocupacion de la sede al
									# dashboard para refrescar el aforo en vivo
        
        from services.hardware_service import HardwareService		# Importa localmente HardwareService para disparar
									# la apertura de barrera sin dependencia circular
        HardwareService.trigger_barrier("ENTRADA", "OPEN", method="ALPR", details={"plate": p, "sucursal": sucursal}, request=request)
									# Ordena abrir la barrera de ENTRADA por metodo
									# ALPR, enviando patente y sucursal y propagando el
									# request (para MQTT)
            
        return {"status": "allowed", "action": "OPEN_GATE", "message": f"Acceso permitido en {sucursal or 'Global'}. Bienvenido {p}"}
									# Retorna 'allowed' con accion OPEN_GATE y mensaje
									# de bienvenida indicando la sede (o 'Global')

    @classmethod							# Decorador que marca exit_plate como metodo de
									# clase
    def exit_plate(cls, db: Session, data: schemas.PlateValidation, request: Request = None, organization_id: int = None) -> dict:
									# Define exit_plate(db, data, request,
									# organization_id): flujo de egreso ALPR, con
									# validacion de deuda y liberacion de plaza
        p = normalize_plate(data.plate)					# Normaliza la patente detectada en la salida
        sede, org = cls._alcance_gate(db, data.gate_id, organization_id)
									# Deriva (sede, org) del gate de salida con
									# _alcance_gate
        if organization_id is not None and sede is None:		# Si el nodo esta ligado a una empresa y el gate no
									# pertenece a sus sedes, se deniega la salida
									# (fail-closed)
            return {"status": "denied", "message": "Gate no habilitado para esta organización"}
									# Retorna 'denied' por gate no habilitado para la
									# organizacion
        sucursal = sede.nombre if sede else None			# Fija el nombre de sucursal desde la sede resuelta
									# (o None)

        ultimo = AccessRepository.get_last_by_patente_and_sucursal(db, p, sucursal, organization_id=cls._alcance_logs(sucursal, org))
									# Busca el ultimo evento de la patente en la sede,
									# acotando por organizacion con _alcance_logs
        
        if not ultimo or ultimo.tipo_evento != AccessEventType.ENTRADA:
									# Si no hay ultimo registro o el ultimo no fue
									# ENTRADA, no puede haber salida valida
            NotificationService.set_last_event(cls._suc_key(sucursal), "error", p, "Sin registro de ingreso", "error")
									# Notifica al dashboard el evento 'error' por
									# ausencia de registro de ingreso
            return {"status": "error", "message": "El vehículo no tiene registro de ingreso en esta sede"}
									# Retorna 'error' indicando que el vehiculo no
									# tiene registro de ingreso en la sede
        
        if not (ultimo.pago_confirmado or (ultimo.reservation and ultimo.reservation.estado_pago == PaymentStatus.PAGADO)):
									# Comprueba si el vehiculo debe pago: si no pago
									# confirmado ni tiene reserva PAGADA, se evalua la
									# cortesia
            entrada_dt = parse_fecha(ultimo.fecha_hora)
            minutos_transcurridos = (TimeService.now() - entrada_dt).total_seconds() / 60
									# Calcula los minutos transcurridos desde el
									# ingreso hasta ahora (segundos / 60)
            if minutos_transcurridos > 10:				# Si pasaron mas de 10 minutos (fuera de cortesia)
									# hay que cobrar antes de dejar salir
                NotificationService.set_last_event(cls._suc_key(sucursal), "error", p, f"Deuda pendiente ({int(minutos_transcurridos)} min)", "error")
									# Notifica al dashboard el evento 'error' de deuda
									# pendiente con los minutos transcurridos
                cls._emit_pending_exit(db, ultimo, p, sucursal, data)	# Emite al popup de caja el evento de salida impaga
									# (_emit_pending_exit) con la deuda y los datos del
									# vehiculo
                return {"status": "denied", "message": f"Deuda pendiente de pago en esta sede. Cortesía: 10 min, transcurridos: {int(minutos_transcurridos)} min"}
									# Retorna 'denied' con mensaje de deuda pendiente,
									# informando cortesia de 10 min y minutos
									# transcurridos
            
        now = TimeService.now()						# Obtiene la hora actual para fechar el registro de
									# salida
        aforo = cls._get_aforo(db, sucursal)				# Obtiene el aforo de la sede para liberar la plaza
									# ocupada
        if aforo:							# Si existe aforo registrado, se procede a liberar
									# cupo
            es_reserva = bool(ultimo.reserva_id or (ultimo.reservation and ultimo.reservation.estado_pago == PaymentStatus.PAGADO))
									# Determina si la plaza a liberar es de reserva
									# (reserva_id o reserva pagada previa)
            cls._liberar_plaza(aforo, ultimo.tipo_vehiculo, es_reserva)
									# Libera la plaza del aforo segun el tipo de
									# vehiculo y si era reserva (helper del mixin)
            
        db.add(models.AccessLog(					# Inserta el AccessLog de SALIDA para registrar el
									# egreso del vehiculo
            patente_detectada=p,					# Registra la patente detectada
            normalized_patente=p,					# Registra la patente normalizada
            tipo_evento=AccessEventType.SALIDA,				# Marca el evento como SALIDA
            tipo_vehiculo=ultimo.tipo_vehiculo,				# Reutiliza el tipo de vehiculo del ultimo registro
									# de entrada
            fecha_hora=now.isoformat(),					# Guarda la marca de tiempo (now) en formato ISO
            pago_confirmado=ultimo.pago_confirmado,			# Hereda el estado de pago del registro de entrada
            sucursal=sucursal,						# Guarda la sucursal de la salida
            ocr_time=data.ocr_time					# Guarda el tiempo de OCR reportado por el nodo
									# ALPR
        ))								# Cierra la construccion del AccessLog de salida
        db.commit()							# Confirma la transaccion persistiendo la salida
        NotificationService.set_last_event(cls._suc_key(sucursal), "SALIDA", p, f"Hasta luego {p}", "ok")
									# Publica el ultimo evento 'SALIDA' con mensaje de
									# despedida en el canal de la sucursal
        NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
									# Notifica el cambio de ocupacion al dashboard tras
									# liberar la plaza
        
        from services.hardware_service import HardwareService		# Importa localmente HardwareService para la
									# apertura de barrera de salida
        HardwareService.trigger_barrier("SALIDA", "OPEN", method="ALPR", details={"plate": p, "sucursal": sucursal}, request=request)
									# Ordena abrir la barrera de SALIDA por metodo ALPR
									# con los detalles del evento
            
        return {"status": "allowed", "action": "OPEN_GATE", "message": f"Salida autorizada en {sucursal or 'Global'}. Adiós {p}"}
									# Retorna 'allowed' con OPEN_GATE y mensaje de
									# salida autorizada indicando la sede

    @classmethod							# Decorador que marca validate_qr como metodo de
									# clase
    def validate_qr(cls, db: Session, data: schemas.QRValidation, request: Request = None, organization_id: int = None) -> dict:
									# Define validate_qr(db, data, request,
									# organization_id): flujo de acceso por QR de
									# reserva, entrada o salida
        # Log request for debugging QR integration
        try:								# Inicia un try para el logueo defensivo de la
									# peticion QR
            logger.debug(f"validate_qr called. gate_id={getattr(data, 'gate_id', None)} qr_len={len(getattr(data, 'qr_data',''))}")
									# Loguea en debug el gate_id y la longitud del
									# qr_data para depurar la integracion
        except Exception:						# Captura cualquier excepcion del logueo de
									# depuracion
            logger.warning("[ACCESS] Error logueando validate_qr", exc_info=True)
									# Registra un warning con traceback si fallo el
									# logueo de validate_qr
        sucursal = None							# Inicializa sucursal en None; se resolvera a
									# partir del gate_id
        org = None							# Inicializa org en None; se resolvera por binding
									# o por la sede
        try:								# Inicia un try que envuelve todo el procesamiento
									# del QR para capturar errores inesperados
            if data.gate_id and '_' in data.gate_id:			# Verifica si el gate_id tiene formato con '_' para
									# extraer el prefijo de sede
                suc_short = normalize_name(data.gate_id.split('_')[0])	# Extrae y normaliza el prefijo de sede (parte
									# antes del '_') desde el gate_id
            else:							# Si el gate_id no tiene el formato esperado, no
									# hay prefijo de sede
                suc_short = None					# Asigna None a suc_short (sin sede derivable del
									# gate)
            if suc_short and suc_short not in (AccessEventType.ENTRADA.value, AccessEventType.SALIDA.value):
									# Valida que el prefijo no sea una palabra
									# reservada de evento (ENTRADA/SALIDA) para
									# tratarlo como nombre de sede
                if organization_id is not None and cls._sede_desde_gate(db, data.gate_id, organization_id) is None:
									# Si el nodo tiene binding de empresa y el gate no
									# pertenece a ninguna sede suya, se deniega
                    # Binding del nodo ALPR: el gate no corresponde a ninguna sede de la empresa
                    return {"status": "denied", "message": "Gate no habilitado para esta organización"}
									# Retorna 'denied' por gate no habilitado para la
									# organizacion
                sucursal = suc_short					# Fija la sucursal como el prefijo normalizado del
									# gate
            if sucursal:						# Si se determino una sucursal, se resuelve su
									# nombre real
                try:							# Inicia un try para la resolucion del nombre
									# completo de la sucursal
                    branch = BranchRepository.get_by_name_like(db, sucursal, organization_id)
									# Busca la sucursal por coincidencia de nombre
									# (get_by_name_like) acotando por organizacion
                    if branch:						# Si se encontro la sucursal en la base:
                        sucursal = branch.nombre			# Reemplaza el prefijo por el nombre oficial de la
									# sucursal
                except Exception:					# Captura cualquier excepcion de la resolucion del
									# nombre de sucursal
                    logger.warning("[ACCESS] Error resolviendo sucursal por nombre", exc_info=True)
									# Registra un warning con traceback si fallo la
									# resolucion de la sucursal por nombre
            # ATRIBUCION gate -> sede -> empresa (para acotar logs y reserva)
            org = organization_id or (organization_of_sede(db, branch_name=sucursal) if sucursal else None)
									# Determina la organizacion: usa el binding del
									# nodo o la deriva de la sede
									# (organization_of_sede)
            org_log = cls._alcance_logs(sucursal, org)			# Calcula el alcance de organizacion para filtrar
									# logs (org_log) a partir de sucursal y org
            parts = data.qr_data.split('|')				# Divide el qr_data por el separador '|' para
									# parsear sus campos
            if len(parts) < 3 or parts[0] != "AUTOPASS":		# Valida que el QR tenga al menos 3 campos y
									# empiece con el prefijo 'AUTOPASS'
                return {"status": "error", "message": "Formato de QR inválido"}
									# Retorna 'error' si el formato del QR es invalido
            
            reserva_id = int(parts[1].split(':')[1])			# Extrae el id de reserva parseando el campo 1 del
									# QR (formato 'reserva:<id>')
            patente_qr = normalize_plate(parts[2].split(':')[1])	# Extrae y normaliza la patente del QR desde el
									# campo 2 (formato 'patente:<valor>')
            
            reserva = ReservationRepository.get_by_id(db, reserva_id)	# Recupera la reserva por id desde el repositorio
            if not reserva:						# Si la reserva no existe en la base, el QR es
									# invalido
                return {"status": "error", "message": "Reserva no encontrada"}
									# Retorna 'error' indicando reserva no encontrada
            
            if normalize_plate(reserva.patente) != patente_qr:		# Verifica que la patente del QR coincida con la
									# patente registrada de la reserva
                return {"status": "error", "message": "La patente del QR no coincide con la reserva"}
									# Retorna 'error' si la patente del QR no coincide
									# con la de la reserva

            if reserva.sucursal_nombre and sucursal and reserva.sucursal_nombre != sucursal:
									# Valida que, si la reserva tiene sede propia y hay
									# una sede de gate, ambas coincidan
                return {"status": "denied", "message": f"Esta reserva es válida únicamente para la sede {reserva.sucursal_nombre}"}
									# Retorna 'denied' indicando que la reserva solo
									# vale para su sede original

            # Aislamiento multiempresa: la reserva debe poder atribuirse a la empresa del gate
            if org is not None and organization_of_sede(db, branch_id=reserva.sucursal_id, branch_name=reserva.sucursal_nombre) != org:
									# Compara la organizacion derivada de la sede de la
									# reserva con la org del gate; si difieren, la
									# reserva no pertenece
                return {"status": "denied", "message": "Esta reserva no pertenece a esta organización"}
									# Retorna 'denied' indicando que la reserva no
									# pertenece a esta organizacion

            pagada = reserva.estado_pago == PaymentStatus.PAGADO	# Calcula pagada: True si el estado de pago de la
									# reserva es PAGADO

            vehiculo = VehicleRepository.get_by_normalized_patente(db, patente_qr)
									# Busca el vehiculo por patente normalizada para
									# conocer su tipo
            tipo_vehiculo = vehiculo.tipo if vehiculo else VehicleType.AUTO
									# Determina el tipo de vehiculo (o AUTO por defecto
									# si no esta registrado)

            now = TimeService.now()					# Obtiene la hora actual via TimeService
            gate_id = data.gate_id.upper() if data.gate_id else "ENTRADA"
									# Normaliza gate_id a mayusculas (o 'ENTRADA' por
									# defecto si no vino)
            is_entry = "EGRESO" not in gate_id and "SALIDA" not in gate_id
									# Determina is_entry: es entrada si el gate_id no
									# contiene 'EGRESO' ni 'SALIDA'
            
            ultimo = AccessRepository.get_last_detected_by_patente_and_sucursal(db, patente_qr, sucursal, organization_id=org_log)
									# Busca el ultimo evento de la patente en la sede
									# (get_last_detected) acotando por organizacion

            if is_entry:						# Si el QR corresponde a un ingreso, se evaluan las
									# reglas de entrada
                if ultimo and ultimo.tipo_evento == AccessEventType.ENTRADA:
									# Si la patente ya tiene una ENTRADA activa, no
									# puede volver a entrar
                    return {"status": "denied", "message": "El vehículo ya se encuentra dentro de esta sede"}
									# Retorna 'denied' indicando que el vehiculo ya se
									# encuentra dentro de la sede
                
                if reserva.estado_reserva in (ReservationStatus.COMPLETADA, ReservationStatus.CANCELADA):
									# Si la reserva ya esta COMPLETADA o CANCELADA, no
									# puede usarse para ingresar
                     return {"status": "denied", "message": "Esta reserva ya expiró o fue cancelada"}
									# Retorna 'denied' indicando que la reserva ya
									# expiro o fue cancelada
                
                now_str = now.strftime("%Y-%m-%d %H:%M:%S")		# Formatea la hora actual con segundos 'YYYY-MM-DD
									# HH:MM:SS' para comparar con el rango de vigencia
                if reserva.fecha_inicio > now_str or reserva.fecha_fin < now_str:
									# Verifica que la hora actual este dentro de la
									# ventana de la reserva (fecha_inicio <= now <=
									# fecha_fin)
                    return {"status": "denied", "message": "La reserva no está vigente en este horario"}
									# Retorna 'denied' si la reserva no esta vigente en
									# este horario

                aforo = cls._get_or_create_aforo(db, sucursal)		# Obtiene (o crea) el aforo de la sede para
									# gestionar la plaza del ingreso QR
                
                capacidad, ocupacion = cls._capacidad_por_tipo(aforo, tipo_vehiculo)
									# Calcula capacidad y ocupacion del tipo de
									# vehiculo (helper del mixin)
                    
                if not reserva and ocupacion >= capacidad:		# Si no hay reserva y la ocupacion alcanzo la
									# capacidad, el ingreso libre se rechaza
                    return {"status": "denied", "message": "Capacidad máxima alcanzada en esta sede"}
									# Retorna 'denied' por capacidad maxima alcanzada
									# en la sede

                if reserva:						# Si el vehiculo tiene reserva, se ingresa por la
									# via reservada
                    if reserva.estado_reserva == ReservationStatus.PENDIENTE:
									# Si la reserva estaba PENDIENTE, pasa a ACTIVA al
									# concretarse el ingreso
                        reserva.estado_reserva = ReservationStatus.ACTIVA
									# Actualiza el estado de la reserva a ACTIVA
                    cls._asignar_plaza(aforo, tipo_vehiculo, es_reserva=True)
									# Asigna plaza como reserva (es_reserva=True),
									# descontando cupo reservado
                else:							# Si no hay reserva, el ingreso es por cupo libre
                    cls._asignar_plaza(aforo, tipo_vehiculo, es_reserva=False)
									# Asigna plaza como no-reserva (es_reserva=False)

                db.add(models.AccessLog(				# Inserta el AccessLog de ENTRADA del ingreso por
									# QR
                    patente_detectada=normalize_plate(reserva.patente),
									# Registra la patente (normalizada desde la
									# reserva)
                    normalized_patente=normalize_plate(reserva.patente),
									# Registra la patente normalizada
                    tipo_evento=AccessEventType.ENTRADA,		# Marca el evento como ENTRADA
                    tipo_vehiculo=tipo_vehiculo,			# Guarda el tipo de vehiculo
                    fecha_hora=now.isoformat(),				# Guarda la marca de tiempo ISO del ingreso
                    reserva_id=reserva.id,				# Vincula el id de la reserva usada
                    pago_confirmado=pagada,				# Marca pago_confirmado segun si la reserva estaba
									# PAGADA
                    sucursal=sucursal					# Guarda la sucursal
                ))							# Cierra la construccion del AccessLog
                db.commit()						# Confirma la transaccion persistiendo el ingreso
									# por QR
                logger.info(f"Notificando cambio de aforo (QR) para sucursal={sucursal}")
									# Loguea que se notificara el cambio de aforo por
									# QR en la sucursal
                NotificationService.set_last_event(cls._suc_key(sucursal), "INGRESO", reserva.patente, f"QR - Bienvenido {reserva.patente}", "ok")
									# Publica el ultimo evento 'INGRESO' con prefijo
									# 'QR' en el canal de la sucursal
                NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
									# Notifica el cambio de ocupacion al dashboard
                
                from services.hardware_service import HardwareService	# Importa localmente HardwareService para abrir la
									# barrera
                HardwareService.trigger_barrier("ENTRADA", "OPEN", method="QR", details={"plate": reserva.patente, "sucursal": sucursal}, request=request)
									# Ordena abrir la barrera de ENTRADA por metodo QR
									# con los detalles del evento
                    
                return {"status": "allowed", "action": "OPEN_GATE", "message": f"QR Válido en {sucursal or 'Global'}. Bienvenido {reserva.patente}"}
									# Retorna 'allowed' con OPEN_GATE y mensaje de QR
									# valido para el ingreso
            else:							# Si el QR corresponde a una salida (gate con
									# EGRESO/SALIDA), se evaluan las reglas de egreso
                if not ultimo or ultimo.tipo_evento != AccessEventType.ENTRADA:
									# Si no hay ultimo registro de ENTRADA activo, no
									# se puede registrar la salida
                    return {"status": "error", "message": "No se registra un ingreso activo para esta patente"}
									# Retorna 'error' indicando que no hay ingreso
									# activo para esa patente

                if not (ultimo.pago_confirmado or reserva.estado_pago == PaymentStatus.PAGADO):
									# Verifica si hay deuda: sin pago confirmado ni
									# reserva PAGADA se aplica la cortesia de 10
									# minutos
                    entrada_dt = parse_fecha(ultimo.fecha_hora)
                    minutos_transcurridos = (now - entrada_dt).total_seconds() / 60
									# Calcula los minutos transcurridos desde el
									# ingreso hasta ahora
                    if minutos_transcurridos > 10:			# Si pasaron mas de 10 minutos (fuera de cortesia),
									# hay deuda pendiente
                        NotificationService.set_last_event(cls._suc_key(sucursal), "error", patente_qr, f"Deuda pendiente de reserva impaga ({int(minutos_transcurridos)} min)", "error")
									# Notifica al dashboard el evento 'error' por deuda
									# pendiente de reserva impaga
                        return {"status": "denied", "message": f"Deuda pendiente de pago en esta sede. Cortesía: 10 min, transcurridos: {int(minutos_transcurridos)} min"}
									# Retorna 'denied' con el detalle de cortesia y
									# minutos transcurridos

                aforo = cls._get_aforo(db, sucursal)			# Obtiene el aforo de la sede para liberar la plaza
									# del vehiculo
                if aforo:						# Si existe aforo, se procede a liberar
                    es_reserva = bool(ultimo.reserva_id or getattr(reserva, 'id', None))
									# Determina si la plaza era de reserva (reserva_id
									# previo o reserva actual del QR)
                    cls._liberar_plaza(aforo, ultimo.tipo_vehiculo, es_reserva)
									# Libera la plaza del aforo segun tipo de vehiculo
									# y si era reserva
                
                db.add(models.AccessLog(				# Inserta el AccessLog de SALIDA del egreso por QR
                    patente_detectada=normalize_plate(reserva.patente),
									# Registra la patente normalizada desde la reserva
                    normalized_patente=normalize_plate(reserva.patente),
									# Registra la patente normalizada
                    tipo_evento=AccessEventType.SALIDA,			# Marca el evento como SALIDA
                    tipo_vehiculo=ultimo.tipo_vehiculo,			# Reutiliza el tipo de vehiculo del ingreso
                    fecha_hora=now.isoformat(),				# Guarda la marca de tiempo ISO de la salida
                    reserva_id=reserva.id,				# Vincula el id de la reserva
                    pago_confirmado=ultimo.pago_confirmado,		# Hereda el estado de pago del ultimo registro
                    sucursal=sucursal					# Guarda la sucursal
                ))							# Cierra la construccion del AccessLog
                db.commit()						# Confirma la transaccion persistiendo la salida
									# por QR
                logger.info(f"Notificando cambio de aforo (QR SALIDA) para sucursal={sucursal}")
									# Loguea que se notificara el cambio de aforo por
									# QR SALIDA
                NotificationService.set_last_event(cls._suc_key(sucursal), "SALIDA", reserva.patente, f"QR - Hasta luego {reserva.patente}", "ok")
									# Publica el ultimo evento 'SALIDA' con prefijo
									# 'QR' en el canal de la sucursal
                NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
									# Notifica el cambio de ocupacion al dashboard tras
									# el egreso
                
                from services.hardware_service import HardwareService	# Importa localmente HardwareService para abrir la
									# barrera de salida
                HardwareService.trigger_barrier("SALIDA", "OPEN", method="QR", details={"plate": reserva.patente, "sucursal": sucursal}, request=request)
									# Ordena abrir la barrera de SALIDA por metodo QR
									# con los detalles del evento
                    
                return {"status": "allowed", "action": "OPEN_GATE", "message": f"QR Válido en {sucursal or 'Global'}. Adiós {reserva.patente}"}
									# Retorna 'allowed' con OPEN_GATE y mensaje de QR
									# valido para la salida
                
        except HTTPException:						# Captura primero las HTTPException para no
									# tragarlas con el catch generico
            raise							# Relanza la HTTPException para que FastAPI
									# devuelva su status/detail originales
        except Exception:						# Captura cualquier otra excepcion inesperada del
									# procesamiento del QR
            logger.error("[ACCESS] Error inesperado procesando el pase digital", exc_info=True)
									# Loguea en nivel error con traceback el fallo
									# inesperado procesando el pase digital
            return {"status": "error", "message": "Error interno procesando el pase digital"}
									# Retorna 'error' generico de error interno, sin
									# filtrar detalles al cliente

    @classmethod							# Decorador que marca manual_entry como metodo de
									# clase
    def manual_entry(cls, db: Session, plate: str, sucursal: str, tipo_vehiculo: str = "Auto", floor_id: int = None, request: Request = None, organization_id: int = None) -> dict:
									# Define manual_entry(db, plate, sucursal,
									# tipo_vehiculo, floor_id, request,
									# organization_id): registra un ingreso forzado por
									# staff/admin
        """Registra un ingreso manual forzado por personal staff/admin."""
        p = normalize_plate(plate)					# Normaliza la patente recibida manualmente
        if not is_valid_plate(p):					# Valida el formato de la patente antes de
									# registrar el ingreso manual
            raise HTTPException(status_code=400, detail="Formato de patente inválido.")
									# Si el formato es invalido, lanza HTTP 400 con
									# detalle (el operador puede ver el motivo)
        org = cls._alcance_logs(sucursal, organization_id)		# Calcula el alcance de organizacion para los logs
									# a partir de la sucursal y el organization_id
        now = TimeService.now()						# Obtiene la hora actual con TimeService para
									# fechar el ingreso manual
        
        # Buscar la última ENTRADA y verificar si el vehículo sigue adentro
        ultima_entrada = cls._unclosed_last_entry(db, p, sucursal, organization_id=org)
									# Verifica si la patente ya tiene un ingreso
									# abierto en la sede (_unclosed_last_entry)
        if ultima_entrada:						# Si ya esta adentro, no se duplica el registro
            return {"status": "ok", "message": "El vehículo ya figura como ingresado en esta sede; se reutilizó el registro", "access_log_id": ultima_entrada.id}
									# Retorna 'ok' reutilizando el registro existente
									# (access_log_id de la entrada abierta)
        
        # Buscar reserva vigente (pagada o impaga)
        now_str = now.strftime("%Y-%m-%d %H:%M")			# Formatea la hora actual 'YYYY-MM-DD HH:MM' para
									# la busqueda de reserva
        reserva = ReservationRepository.get_active_in_range_by_normalized_patente(db, p, now_str, sucursal, organization_id=org)
									# Busca una reserva activa por patente en el rango
									# horario y sede, acotando por organizacion

        floor = None							# Inicializa floor en None; puede indicarse un piso
									# especifico para el ingreso manual
        if floor_id:							# Si se especifico un floor_id, se ingresa a un
									# piso concreto
            floor = BranchRepository.get_floor_by_id(db, floor_id)	# Recupera el piso por id desde el repositorio de
									# sucursales
            if not floor:						# Si el piso no existe, se lanza HTTP 404 en vez de
									# continuar
                raise HTTPException(status_code=404, detail="Piso no encontrado")
									# Lanza HTTP 404 con detalle 'Piso no encontrado'
            cls._asignar_plaza(floor, tipo_vehiculo, bool(reserva))	# Asigna plaza en el piso indicado, marcando si es
									# reserva segun la reserva vigente
        else:								# Si no se indico piso, se usa el aforo general de
									# la sede
            aforo = cls._get_or_create_aforo(db, sucursal)		# Obtiene (o crea) el aforo de la sucursal
            cls._asignar_plaza(aforo, tipo_vehiculo, bool(reserva))	# Asigna plaza en el aforo general, marcando si es
									# reserva

        db.add(models.AccessLog(					# Inserta el AccessLog de ENTRADA del ingreso
									# manual
            patente_detectada=p,					# Registra la patente
            normalized_patente=p,					# Registra la patente normalizada
            tipo_evento=AccessEventType.ENTRADA,			# Marca el evento como ENTRADA
            tipo_vehiculo=tipo_vehiculo,				# Guarda el tipo de vehiculo indicado por el
									# operador
            fecha_hora=now.isoformat(),					# Guarda la marca de tiempo ISO del ingreso
            sucursal=sucursal,						# Guarda la sucursal
            floor_id=floor_id,						# Guarda el piso del ingreso manual (puede ser
									# None)
            reserva_id=reserva.id if reserva else None,			# Vincula el id de la reserva vigente si existe
            pago_confirmado=True if (reserva and reserva.estado_pago == PaymentStatus.PAGADO) else False
									# Marca pago_confirmado segun si la reserva estaba
									# PAGADA
        ))								# Cierra la construccion del AccessLog
        db.commit()							# Confirma la transaccion persistiendo el ingreso
									# manual

        try:								# Inicia un try para que la notificacion y la
									# apertura de barrera no rompan el ingreso ya
									# registrado
            from services.hardware_service import HardwareService	# Importa localmente HardwareService para abrir la
									# barrera
            norm = normalize_name(sucursal)				# Normaliza el nombre de la sucursal para la
									# notificacion de ocupacion
            logger.info(f"Notificando cambio de aforo (manual entry) para sucursal={sucursal} norm={norm}")
									# Loguea que se notificara el cambio de aforo por
									# ingreso manual
            NotificationService.notify_occupancy_change(db, norm)	# Notifica el cambio de ocupacion al dashboard
            HardwareService.trigger_barrier("ENTRADA", "OPEN", method="MANUAL_ENTRY", details={"plate": p, "sucursal": sucursal}, request=request)
									# Ordena abrir la barrera de ENTRADA por metodo
									# MANUAL_ENTRY con los detalles
        except Exception as e:						# Captura cualquier excepcion de la notificacion o
									# el hardware
            logger.error(f"Error notifying occupancy/hardware: {e}")	# Loguea en error si fallo la notificacion de
									# ocupacion o el disparo de hardware, dejando el
									# ingreso ya commitado

        return {"status": "ok", "message": f"Ingreso manual registrado en {floor.nombre if floor else 'Planta Baja'}: {p} ({tipo_vehiculo})"}
									# Retorna 'ok' con mensaje del ingreso manual,
									# indicando piso (o 'Planta Baja'), patente y tipo

    @classmethod							# Decorador que marca manual_exit como metodo de
									# clase
    def manual_exit(cls, db: Session, plate: str, sucursal: str, request: Request = None, organization_id: int = None) -> dict:
									# Define manual_exit(db, plate, sucursal, request,
									# organization_id): registra una salida forzada por
									# staff/admin
        """Registra una salida manual forzada por personal staff/admin."""
        p = normalize_plate(plate)					# Normaliza la patente de la salida manual
        
        ultimo = AccessRepository.get_last_by_patente_and_sucursal(db, p, sucursal, organization_id=cls._alcance_logs(sucursal, organization_id))
									# Busca el ultimo evento de la patente en la sede,
									# acotando por organizacion con _alcance_logs
        
        if not ultimo or ultimo.tipo_evento != AccessEventType.ENTRADA:
									# Si no hay ultimo registro o no fue ENTRADA, no
									# puede salir
            raise HTTPException(status_code=400, detail="El vehículo no figura en esta sede")
									# Lanza HTTP 400 indicando que el vehiculo no
									# figura en esta sede
        
        entrada_dt = parse_fecha(ultimo.fecha_hora)
        minutos_transcurridos = (TimeService.now() - entrada_dt).total_seconds() / 60
									# Calcula los minutos transcurridos desde el
									# ingreso
        dentro_cortesia = minutos_transcurridos <= 10			# Considera dentro de cortesia si pasaron 10
									# minutos o menos
        
        if not ultimo.pago_confirmado and not dentro_cortesia:		# Si no hay pago confirmado y ya excedio la
									# cortesia, hay deuda pendiente
            raise HTTPException(status_code=403, detail=f"DEUDA PENDIENTE en esta sede. Cortesía: 10 min, transcurridos: {int(minutos_transcurridos)} min")
									# Lanza HTTP 403 con detalle de DEUDA PENDIENTE,
									# cortesia y minutos transcurridos
        
        aforo = cls._get_aforo(db, sucursal)				# Obtiene el aforo de la sede para liberar la
									# plaza
        if aforo:							# Si existe aforo, se libera el cupo
            cls._liberar_plaza(aforo, ultimo.tipo_vehiculo, bool(ultimo.reserva_id))
									# Libera la plaza del aforo segun tipo de vehiculo
									# y si era reserva (reserva_id)

        if ultimo.floor_id:						# Si el ingreso manual habia ocupado un piso
									# especifico, tambien debe liberarse
            floor = BranchRepository.get_floor_by_id(db, ultimo.floor_id)
									# Recupera el piso desde el que se ingreso
            if floor:							# Si el piso existe:
                cls._liberar_plaza(floor, ultimo.tipo_vehiculo, bool(ultimo.reserva_id))
									# Libera la plaza del piso segun tipo de vehiculo y
									# si era reserva

        db.add(models.AccessLog(					# Inserta el AccessLog de SALIDA de la salida
									# manual
            patente_detectada=p,					# Registra la patente
            normalized_patente=p,					# Registra la patente normalizada
            tipo_evento=AccessEventType.SALIDA,				# Marca el evento como SALIDA
            tipo_vehiculo=ultimo.tipo_vehiculo,				# Reutiliza el tipo de vehiculo del ingreso
            fecha_hora=TimeService.now().isoformat(),			# Guarda la marca de tiempo ISO de la salida
            pago_confirmado=ultimo.pago_confirmado,			# Hereda el estado de pago del registro de entrada
            costo_estadia=MONEY_ZERO if dentro_cortesia else None,
									# None si corresponde cobro aparte)
            metodo_pago="CAJA" if not dentro_cortesia else None,	# Marca metodo_pago 'CAJA' si excedio cortesia
									# (cobro presencial), o None si fue cortesia
            sucursal=sucursal,						# Guarda la sucursal
            floor_id=ultimo.floor_id					# Guarda el piso asociado (el del ingreso) para
									# trazar la plaza liberada
        ))								# Cierra la construccion del AccessLog
        db.commit()							# Confirma la transaccion persistiendo la salida
									# manual

        try:								# Inicia un try para la notificacion y apertura de
									# barrera de la salida manual
            from services.hardware_service import HardwareService	# Importa localmente HardwareService para abrir la
									# barrera de salida
            norm = normalize_name(sucursal)				# Normaliza el nombre de la sucursal para la
									# notificacion
            logger.info(f"Notificando cambio de aforo (manual exit) para sucursal={sucursal} norm={norm}")
									# Loguea que se notificara el cambio de aforo por
									# salida manual
            NotificationService.notify_occupancy_change(db, norm)	# Notifica el cambio de ocupacion al dashboard
            HardwareService.trigger_barrier("SALIDA", "OPEN", method="MANUAL_EXIT", details={"plate": p, "sucursal": sucursal}, request=request)
									# Ordena abrir la barrera de SALIDA por metodo
									# MANUAL_EXIT con los detalles
        except Exception as e:						# Captura cualquier excepcion de notificacion o
									# hardware
            logger.error(f"Error notifying occupancy/hardware: {e}")	# Loguea en error si fallo la notificacion o el
									# disparo de hardware, sin revertir la salida

        msg = f"Salida manual registrada en {sucursal or 'Global'}: {p}" + (" (Cortesía)" if dentro_cortesia else "")
									# Construye el mensaje de salida manual, anexando
									# '(Cortesía)' cuando el egreso fue sin cargo
        return {"status": "ok", "message": msg}				# Retorna 'ok' con el mensaje de salida manual
									# registrada

    @classmethod							# Decorador que marca cancel_stay como metodo de
									# clase
    def cancel_stay(cls, db: Session, plate: str, sucursal: str, organization_id: int = None) -> dict:
									# Define cancel_stay(db, plate, sucursal,
									# organization_id): cancela una estadia activa (con
									# o sin cargo segun cortesia)
        """Cancela una estadía activa del vehículo."""
        from services.user_notification_service import UserNotificationService
									# Importa localmente UserNotificationService para
									# notificar al dueno si corresponde
        p = normalize_plate(plate)					# Normaliza la patente de la estadia a cancelar
        
        ultimo = AccessRepository.get_last_by_patente_and_sucursal(db, p, sucursal, organization_id=cls._alcance_logs(sucursal, organization_id))
									# Busca el ultimo evento de la patente en la sede,
									# acotando por organizacion
        
        if not ultimo or ultimo.tipo_evento != AccessEventType.ENTRADA:
									# Si no hay ultimo registro o no fue ENTRADA, no
									# hay estadia activa que cancelar
            raise HTTPException(status_code=400, detail="El vehículo no figura como ingresado")
									# Lanza HTTP 400 indicando que el vehiculo no
									# figura como ingresado
        
        entrada_dt = parse_fecha(ultimo.fecha_hora)
        minutos_transcurridos = (TimeService.now() - entrada_dt).total_seconds() / 60
									# Calcula los minutos transcurridos desde el
									# ingreso
        
        aforo = cls._get_aforo(db, sucursal)				# Obtiene el aforo de la sede para liberar la
									# plaza
        if aforo:							# Si existe aforo, se libera el cupo
            cls._liberar_plaza(aforo, ultimo.tipo_vehiculo, bool(ultimo.reserva_id))
									# Libera la plaza del aforo segun tipo de vehiculo
									# y si era reserva

        if ultimo.floor_id:						# Si el ingreso ocupo un piso especifico, tambien
									# se libera su plaza
            floor = BranchRepository.get_floor_by_id(db, ultimo.floor_id)
									# Recupera el piso desde el que se ingreso
            if floor:							# Si el piso existe:
                cls._liberar_plaza(floor, ultimo.tipo_vehiculo, bool(ultimo.reserva_id))
									# Libera la plaza del piso segun tipo de vehiculo y
									# si era reserva
        
        if minutos_transcurridos <= 10:					# Si la estadia duro 10 minutos o menos (dentro de
									# cortesia), se cancela sin cargo
            db.add(models.AccessLog(					# Inserta el AccessLog de SALIDA por cancelacion en
									# cortesia
                patente_detectada=p,					# Registra la patente
                normalized_patente=p,					# Registra la patente normalizada
                tipo_evento=AccessEventType.SALIDA,			# Marca el evento como SALIDA
                tipo_vehiculo=ultimo.tipo_vehiculo,			# Reutiliza el tipo de vehiculo del ingreso
                fecha_hora=TimeService.now().isoformat(),		# Guarda la marca de tiempo ISO de la salida
                pago_confirmado=False,					# Deja pago_confirmado en False (cancelacion en
									# cortesia, sin cobro)
                costo_estadia=MONEY_ZERO,
									# cortesia
                sucursal=sucursal					# Guarda la sucursal
            ))								# Cierra la construccion del AccessLog
            msg = f"Estadía cancelada (Cortesía: {int(minutos_transcurridos)} min). Sin cargo."
									# Construye el mensaje de estadia cancelada
									# indicando cortesia y minutos, sin cargo
        else:								# Si excedio la cortesia, la cancelacion tiene
									# implicancias de cobro
            if not ultimo.pago_confirmado:				# Si la estadia no tiene pago confirmado, hay que
									# calcular la deuda para exigirla
                from services.billing_service import BillingService	# Importa localmente BillingService para calcular
									# la deuda
                monto = BillingService.calculate_debt(ultimo.fecha_hora, db, sucursal=sucursal, tipo_vehiculo=ultimo.tipo_vehiculo)
									# Calcula el monto adeudado con
									# BillingService.calculate_debt segun fecha,
									# sucursal y tipo de vehiculo
                if monto is None:					# Si el monto es None (sucursal sin tarifario), no
									# se puede calcular el cobro
                    raise HTTPException(status_code=409, detail="La sucursal no tiene tarifario configurado. No se puede calcular el monto de la estadía.")
									# Lanza HTTP 409 indicando que la sucursal no tiene
									# tarifario configurado
                raise HTTPException(status_code=402, detail=f"Excedió cortesía ({int(minutos_transcurridos)} min). Debe abonar ${monto}")
									# Lanza HTTP 402 indicando que excedio cortesia y
									# debe abonar el monto calculado
            
            db.add(models.AccessLog(					# Si la estadia ya estaba paga, registra el
									# AccessLog de SALIDA con
									# `db.add(models.AccessLog(`
                patente_detectada=p,					# Registra la patente detectada
                normalized_patente=p,					# Registra la patente normalizada
                tipo_evento=AccessEventType.SALIDA,			# Marca el evento como SALIDA
                tipo_vehiculo=ultimo.tipo_vehiculo,			# Reutiliza el tipo de vehiculo del ingreso
                fecha_hora=TimeService.now().isoformat(),		# Guarda la marca de tiempo ISO de la salida
                pago_confirmado=True,					# Marca `pago_confirmado=True` (la estadia ya
									# estaba paga)
                sucursal=sucursal					# Guarda la sucursal
            ))								# Cierra la construccion del AccessLog
            msg = "Salida registrada con éxito."			# Construye el mensaje 'Salida registrada con
									# exito' para el caso pagado

        db.commit()							# Confirma la transaccion persistiendo la salida de
									# la cancelacion

        try:								# Inicia un try para notificar al dueno del
									# vehiculo, sin romper el flujo si falla
            vehicle = VehicleRepository.get_by_normalized_patente(db, p)
									# Busca el vehiculo por patente normalizada para
									# llegar a su dueno
            if vehicle and vehicle.user_id:				# Si el vehiculo existe y tiene `user_id` asociado,
									# continua
                owner = UserRepository.get_by_id(db, vehicle.user_id)	# Recupera el usuario dueno del vehiculo
                if owner and owner.rol == models.enums.UserRole.USER:	# Si el dueno tiene rol USER (cliente final), se le
									# notifica la cancelacion
                    UserNotificationService.create_notification(	# Crea la notificacion in-app mediante
									# `UserNotificationService.create_notification`
                        db, user_id=owner.id,				# Especifica el destinatario por id de usuario
                        tipo=models.enums.NotificationType.STAY_CANCELLED_ADMIN,
									# Define el tipo de notificacion
									# `STAY_CANCELLED_ADMIN` (estadia cancelada por
									# admin)
                        titulo="Estadía cancelada",			# Define el titulo de la notificacion 'Estadia
									# cancelada'
                        mensaje=f"Un administrador canceló tu estadía en {sucursal} para la patente {plate}."
									# Define el mensaje de la notificacion con sucursal
									# y patente afectadas
                    )							# Cierra la llamada de creacion de notificacion
        except Exception:						# Captura cualquier excepcion durante la
									# notificacion al dueno
            logger.warning("[ACCESS] Error notificando cancelación de estadía", exc_info=True)
									# Registra un warning con traceback si fallo la
									# notificacion de cancelacion

        return {"status": "ok", "message": msg}				# Devuelve el resultado con estado ok y el mensaje
									# final