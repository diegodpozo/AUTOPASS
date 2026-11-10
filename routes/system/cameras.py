'''Gestiona el inventario de camaras por sucursal, estado de salud, tipo de carril asociado y WebSocket de estado'''


import os								# Importa `os` para leer variables de entorno y
									# detectar el sistema operativo (Windows vs Linux)
import sys								# Importa `sys` para usar `sys.executable` al
									# lanzar el subproceso del servicio ALPR
import subprocess							# Importa `subprocess` para arrancar y detener el
									# proceso `alpr_service.py` de cada camara
import threading							# Importa `threading` para leer la salida de
									# consola del subproceso en un hilo aparte
from typing import List							# Importa `List` de typing para tipar la respuesta
									# con lista de camaras
from fastapi import APIRouter, Depends, HTTPException, Request		# Importa de FastAPI `APIRouter`, `Depends`,
									# `HTTPException` y `Request` para definir los
									# endpoints
from sqlalchemy.orm import Session					# Importa `Session` de SQLAlchemy como tipo de la
									# sesion de base de datos
import models								# Importa el paquete `models` con las entidades del
									# dominio
import schemas								# Importa el paquete `schemas` con los contratos de
									# entrada/salida
from models.enums import UserRole					# Importa `UserRole` para comparar roles de usuario
									# (por ejemplo ADMIN)
from core.database import get_db					# Importa `get_db`, la dependencia que provee la
									# sesion de base de datos por peticion
from core.security import get_operational_user, enforce_organization_scope
									# Importa helpers de seguridad:
									# `get_operational_user` y
									# `enforce_organization_scope`
from core.alpr_security import require_alpr_node			# Importa `require_alpr_node` de seguridad para
									# exigir que el nodo ALPR este autorizado
from core.logger import get_logger					# Importa `get_logger` para obtener el logger del
									# modulo `Cameras`
from routes.system.common import CAMERA_PROCESSES, CameraConfig, normalize_system_name, misma_sucursal
									# Importa de `routes/system/common` el registro de
									# procesos de camara, el schema de config y helpers
									# de nombre/sede
from routes.system.common import manager as video_manager		# Importa el `manager` de video de `common` como
									# `video_manager` para transmitir la consola al
									# front
from repositories.camera_repository import CameraRepository		# Importa `CameraRepository` para el acceso a datos
									# de camaras
from repositories.settings_repository import SettingsRepository		# Importa `SettingsRepository` para leer/guardar la
									# fuente de cada camara en settings
from repositories.branch_repository import BranchRepository		# Importa `BranchRepository` para resolver sedes
									# por nombre

logger = get_logger("Cameras")						# Crea el logger `Cameras` del modulo

try:									# Abre un `try` para detectar la codificacion de
									# consola preferida del sistema
    import locale							# Importa `locale` para consultar la codificacion
									# preferida del sistema
    _console_encoding = locale.getpreferredencoding(False) or "utf-8"	# Obtiene la codificacion preferida (o 'utf-8' por
									# defecto) para decodificar la salida del
									# subproceso
except Exception:							# Captura cualquier error al detectar la
									# codificacion
    _console_encoding = "utf-8"						# Fija `_console_encoding` en 'utf-8' como
									# respaldo

def _schedule_async(coro):						# Define `_schedule_async(coro)`: programa una
									# corutina en el loop principal de Uvicorn
    """PROGRAMA UNA COROUTINA EN EL LOOP PRINCIPAL DE UVICORN DESDE UN HILO SECUNDARIO."""
    try:								# Abre un `try` para obtener el loop de
									# notificaciones
        from services.notification_service import NotificationService	# Importa `NotificationService`, que guarda el loop
									# principal del servidor
        loop = NotificationService._loop				# Obtiene el loop de eventos guardado en
									# `NotificationService._loop`
        if loop and loop.is_running():					# Comprueba que exista un loop y este en ejecucion
            import asyncio						# Importa `asyncio` para programar la corutina de
									# forma thread-safe
            asyncio.run_coroutine_threadsafe(coro, loop)		# Programa la corutina en el loop principal desde
									# este hilo secundario
            return True							# Devuelve True indicando que la corutina se agendo
									# correctamente
    except Exception:							# Captura cualquier error al programar la corutina
        pass								# Ignora el error con `pass`
    return False							# Devuelve False cuando no se pudo programar la
									# corutina

def _stream_console_output(proc: subprocess.Popen, camera_id: str):	# Define `_stream_console_output(proc, camera_id)`:
									# lee el stdout del subproceso ALPR en un hilo
    """LEE EL STDOUT DEL SUBPROCESO ALPR EN UN HILO Y REENVIA CADA LINEA AL FRONT
    POR EL WEBSOCKET DE VIDEO DE ESA CAMARA. NO ALTERA EL FLUJO DE FRAMES NI LOS
    MENSAJES DE EVENTO EXISTENTES (ruta paralela puramente aditiva)."""
    try:								# Abre un `try` para tolerar el fin de la lectura
        for raw in iter(proc.stdout.readline, b""):			# Itera linea por linea leyendo el stdout binario
									# hasta el fin (b'')
            line = raw.decode(_console_encoding, errors="replace").rstrip("\n").rstrip("\r")
									# Decodifica cada linea con la codificacion de
									# consola y le quita saltos de linea
            if line.strip():						# Solo procesa lineas con contenido (ignora las
									# vacias)
                _schedule_async(video_manager.broadcast_console(camera_id, line))
									# Programa el broadcast de la linea al front por el
									# WebSocket de video de esa camara
        proc.stdout.close()						# Cierra el stdout del subproceso al terminar la
									# lectura
    except Exception as e:						# Captura cualquier error de la lectura de consola
        logger.debug(f"Fin del stream de consola {camera_id}: {e}")	# Registra en debug el fin del stream de consola de
									# la camara
    finally:								# Bloque `finally` que corre siempre al terminar
        try:								# Abre un `try` para soltar la referencia al
									# stdout
            proc.stdout = None						# Suelta `proc.stdout` para liberar el pipe
        except Exception:						# Captura cualquier error al soltar el stdout
            pass							# Ignora el error con `pass`

router = APIRouter()							# Crea el `router` de FastAPI con las rutas de
									# camaras

def _enforce_camera_org(staff: models.User, camera: models.ParkingCamera, db: Session = None):
									# Define `_enforce_camera_org(staff, camera, db)`:
									# aplica el aislamiento multiempresa de la camara
    """AISLAMIENTO MULTIEMPRESA: un Admin General solo opera camaras de sedes de SU empresa."""
    enforce_organization_scope(staff, getattr(camera.branch, "organization_id", None), db=db)
									# Delega la verificacion en
									# `enforce_organization_scope` con la organizacion
									# de la sede de la camara

@router.get("/camera-config/{gate_id}")					# Decorador que registra GET
									# `/camera-config/{gate_id}` (leer config de una
									# camara por porton)
def get_camera_config(gate_id: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
									# Define `get_camera_config` con el staff operativo
									# autenticado y la sesion de base de datos
    gate_id = gate_id.upper()						# Pasa el `gate_id` a mayusculas para uniformar la
									# clave de busqueda
    if staff.rol != UserRole.ADMIN and staff.sucursal:			# Si el usuario no es ADMIN y tiene sede, restringe
									# el acceso a su propia sede
        branch_prefix = gate_id.split('_')[0]				# Obtiene el prefijo de sede del gate_id (lo
									# anterior al primer '_')
        if branch_prefix != normalize_system_name(staff.sucursal):	# Comprueba que el prefijo de sede coincida con la
									# sede normalizada del staff
            raise HTTPException(status_code=403, detail="No tenés acceso a esta configuración")
									# Lanza 403 si el usuario intenta ver la config de
									# otra sede
             
    setting = SettingsRepository.get_by_clave(db, f"CAMERA_SOURCE_{gate_id}")
									# Busca en settings la clave de fuente de la camara
									# (`CAMERA_SOURCE_<gate_id>`)
    
    source = setting.valor_str if setting else "0"			# Usa el `valor_str` configurado como fuente, o '0'
									# por defecto
    is_running = gate_id in CAMERA_PROCESSES and CAMERA_PROCESSES[gate_id].poll() is None
									# Determina si el proceso de esa camara existe y
									# sigue vivo (`poll()` None)
    
    return {"gate_id": gate_id, "source": source, "is_running": is_running}
									# Devuelve el gate_id, la fuente y si el servicio
									# esta corriendo

@router.post("/camera-config")						# Decorador que registra POST `/camera-config`
									# (guardar config de camara)
def set_camera_config(config: CameraConfig, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
									# Define `set_camera_config` con el schema
									# `CameraConfig`, la sesion y el staff operativo
    gate_id = config.gate_id.upper()					# Normaliza el gate_id recibido a mayusculas
    if staff.rol != UserRole.ADMIN:					# Si el usuario no es ADMIN, se restringe a su
									# sede
        branch_prefix = normalize_system_name(staff.sucursal)		# Normaliza el nombre de la sede del staff como
									# prefijo esperado
        if not gate_id.startswith(branch_prefix):			# Comprueba que el gate_id empiece con el prefijo
									# de su sede
            raise HTTPException(status_code=403, detail="No tenés acceso a esta configuración")
									# Lanza 403 si intenta configurar una camara de
									# otra sede
            
    setting = SettingsRepository.get_by_clave(db, f"CAMERA_SOURCE_{gate_id}")
									# Busca el setting de fuente de la camara por su
									# clave
    
    if not setting:							# Si no existe el setting, hay que crearlo
        setting = models.Settings(clave=f"CAMERA_SOURCE_{gate_id}", valor_str=config.source, sucursal=staff.sucursal)
									# Crea un nuevo `Settings` con la clave de fuente,
									# la fuente y la sede del staff
        db.add(setting)							# Agrega el nuevo setting a la sesion
    else:								# Rama `else`: el setting ya existia
        setting.valor_str = config.source				# Actualiza el `valor_str` con la nueva fuente
    
    db.commit()								# Confirma (commit) el cambio en base de datos
    return {"status": "ok", "message": "Configuración guardada"}	# Devuelve 'ok' con el mensaje de configuracion
									# guardada

@router.post("/camera-service/{gate_id}/{action}")			# Decorador que registra POST
									# `/camera-service/{gate_id}/{action}`
									# (iniciar/detener proceso por porton)
def control_camera_service(gate_id: str, action: str, request: Request, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
									# Define `control_camera_service` con gate_id,
									# accion, request, sesion y staff operativo
    gate_id = gate_id.upper()						# Normaliza el gate_id a mayusculas
    if staff.rol != UserRole.ADMIN:					# Si no es ADMIN, se restringe a camaras de su
									# sede
        branch_prefix = normalize_system_name(staff.sucursal)		# Normaliza el nombre de su sede como prefijo
        if not gate_id.startswith(branch_prefix):			# Comprueba que el gate_id empiece con su prefijo
									# de sede
            raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")
									# Lanza 403 si intenta controlar una camara de otra
									# sede

    if action == "start":						# Rama `if` para la accion 'start'
        if gate_id in CAMERA_PROCESSES and CAMERA_PROCESSES[gate_id].poll() is None:
									# Comprueba si el proceso ya esta corriendo para no
									# lanzar uno duplicado
            return {"status": "error", "message": "Ya está en ejecución"}
									# Devuelve error 'Ya esta en ejecucion' si el
									# proceso sigue vivo
            
        setting = SettingsRepository.get_by_clave(db, f"CAMERA_SOURCE_{gate_id}")
									# Busca el setting de fuente de la camara
        source = setting.valor_str if setting else "0"			# Usa el `valor_str` o '0' por defecto
        # El ALPR corre en la misma máquina que el backend: conectar por localhost
        # (no a través de un túnel) para evitar el doble-hop de los frames de video
        base_url = f"http://127.0.0.1:{request.url.port or 8000}"	# Construye la URL base apuntando a 127.0.0.1 con
									# el puerto del request o 8000
        
        env = os.environ.copy()						# Copia el entorno actual del proceso para pasarlo
									# al subproceso
        env["GATE_ID"] = gate_id					# Inyecta `GATE_ID` en el entorno del subproceso
        env["VIDEO_SOURCE"] = source					# Inyecta `VIDEO_SOURCE` con la fuente configurada
        if "QR" in gate_id.upper():					# Si el gate_id contiene 'QR', configura el tipo de
									# porton QR
            env["GATE_TYPE"] = "qr"					# Asigna `GATE_TYPE` = 'qr'
        else:								# Rama `else`: para portones de patente
            env["GATE_TYPE"] = "entrada" if "ENTRADA" in gate_id else "salida"
									# Asigna 'entrada' o 'salida' segun si el gate_id
									# contiene 'ENTRADA'
        env["BACKEND_URL"] = base_url					# Inyecta `BACKEND_URL` con la URL base local
        env["PYTHONUNBUFFERED"] = "1"					# Activa `PYTHONUNBUFFERED` para que la salida del
									# subproceso llegue sin buffering
        
        try:								# Abre un `try` para lanzar el subproceso
            logger.info(f"Iniciando ALPR para {gate_id} con fuente: {source}")
									# Registra en log el inicio del ALPR con su fuente
            proc = subprocess.Popen(					# Lanza el subproceso `alpr_service.py` con el
									# entorno preparado
                [sys.executable, "alpr_service.py"],			# Usa el interprete Python actual
									# (`sys.executable`)
                env=env,						# Pasa el entorno con las variables inyectadas
                stdout=subprocess.PIPE,					# Captura el stdout del subproceso en un pipe
                stderr=subprocess.STDOUT,				# Redirige stderr al mismo pipe para unificar la
									# salida
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
									# En Windows crea un nuevo grupo de procesos (para
									# poder matar el arbol completo)
            )								# Cierra la llamada al constructor del subproceso
            CAMERA_PROCESSES[gate_id] = proc				# Registra el proceso en `CAMERA_PROCESSES` bajo el
									# gate_id
            threading.Thread(target=_stream_console_output, args=(proc, gate_id), daemon=True).start()
									# Lanza el hilo daemon que reenvia la consola del
									# subproceso al front
            return {"status": "ok", "message": "Servicio iniciado"}	# Devuelve 'ok' con el mensaje 'Servicio iniciado'
        except Exception as e:						# Captura cualquier error al lanzar el subproceso
            return {"status": "error", "message": str(e)}		# Devuelve error con el mensaje de la excepcion
            
    elif action == "stop":						# Rama `elif` para la accion 'stop'
        if gate_id not in CAMERA_PROCESSES:				# Comprueba que exista un proceso registrado para
									# ese gate
            return {"status": "error", "message": "No está en ejecución"}
									# Devuelve error 'No esta en ejecucion' si no hay
									# proceso
            
        proc = CAMERA_PROCESSES[gate_id]				# Obtiene el objeto de proceso registrado
        try:								# Abre un `try` para detenerlo
            if proc.poll() is None:					# Comprueba si el proceso sigue vivo antes de
									# matarlo
                if os.name == 'nt':					# Si el sistema es Windows, usa `taskkill`
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
									# Mata el arbol de procesos completo con `/F /T
									# /PID`, descartando su salida
                else:							# Rama `else` para sistemas no Windows
                    proc.terminate()					# Envia la senal de terminacion con
									# `proc.terminate()`
            if gate_id in CAMERA_PROCESSES:				# Comprueba que el proceso siga registrado
                del CAMERA_PROCESSES[gate_id]				# Elimina la entrada del gate en
									# `CAMERA_PROCESSES`
            return {"status": "ok", "message": "Servicio detenido"}	# Devuelve 'ok' con el mensaje 'Servicio detenido'
        except Exception as e:						# Captura cualquier error al detener el proceso
            return {"status": "error", "message": str(e)}		# Devuelve error con el mensaje de la excepcion
            
    return {"status": "error", "message": "Acción no válida"}		# Devuelve error si la accion no fue ni 'start' ni
									# 'stop'

@router.get("/cameras", response_model=List[schemas.CameraResponse])	# Decorador que registra GET `/cameras` con
									# respuesta lista de `CameraResponse`
def get_cameras(db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
									# Define `get_cameras` con la sesion y el staff
									# operativo
    query = CameraRepository.get_all(db)				# Trae todas las camaras desde
									# `CameraRepository.get_all`
    if staff.rol == UserRole.ADMIN:					# Si el usuario es ADMIN, filtra por su
									# organizacion
        org = getattr(staff, "organization_id", None)			# Obtiene la organizacion del staff
        if org is not None:						# Comprueba que la organizacion este definida (no
									# None)
            org_ids = {b.id for b in BranchRepository.get_all(db, org)}
									# Reune los ids de las sedes de esa organizacion
            query = [c for c in query if c.sucursal_id in org_ids]	# Filtra las camaras dejando solo las de sedes de
									# su organizacion
    elif staff.sucursal:						# Rama `elif`: si el usuario no es ADMIN y tiene
									# sede
        query = [c for c in query if misma_sucursal(c, staff)]		# Filtra las camaras dejando solo las de la misma
									# sede que el staff
    cameras = query							# Guarda el resultado filtrado en `cameras`
    res = []								# Inicializa la lista de respuestas
    for c in cameras:							# Recorre cada camara filtrada
        norm_suc = normalize_system_name(c.sucursal) if c.sucursal else "GLOBAL"
									# Calcula el nombre de sede normalizado de la
									# camara (o 'GLOBAL')
        proc_id = f"{norm_suc}_{c.tipo}_{c.id}".upper()			# Construye el `proc_id` de la camara como
									# `SEDE_TIPO_ID` en mayusculas
        is_running = proc_id in CAMERA_PROCESSES and CAMERA_PROCESSES[proc_id].poll() is None
									# Determina si el proceso de esa camara esta
									# corriendo
        res.append(schemas.CameraResponse(				# Empieza a armar la respuesta `CameraResponse`
            id=c.id,							# Incluye el id de la camara
            nombre=c.nombre,						# Incluye el nombre de la camara
            tipo=c.tipo,						# Incluye el tipo de camara
            source=c.source,						# Incluye la fuente (URL/dispositivo) configurada
            activa=c.activa,						# Incluye si la camara esta activa
            sucursal=c.sucursal,					# Incluye la sede de la camara
            orden=c.orden,						# Incluye el orden en la grilla
            is_running=is_running					# Incluye si el servicio esta corriendo
        ))								# Cierra la construccion de la respuesta y la
									# agrega a `res`
    return res								# Devuelve la lista de camaras visibles para el
									# usuario

@router.post("/cameras", response_model=schemas.CameraResponse)		# Decorador que registra POST `/cameras` con
									# respuesta `CameraResponse` (alta de camara)
def create_camera(data: schemas.CameraCreate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
									# Define `create_camera` con el schema
									# `CameraCreate`, la sesion y el staff operativo
    sucursal = staff.sucursal if staff.rol != UserRole.ADMIN else data.sucursal
									# Determina la sede: la del staff si no es ADMIN, o
									# la indicada en los datos si es ADMIN
    org_id = getattr(staff, "organization_id", None)			# Obtiene la organizacion del staff
    branch_id = BranchRepository.get_id_by_name(db, sucursal, org_id) if sucursal else None
									# Resuelve el id de sede por nombre dentro de la
									# organizacion del staff
    if staff.rol == UserRole.ADMIN and org_id is not None and sucursal and branch_id is None:
									# Si es ADMIN con organizacion y la sede indicada
									# no existe en su empresa, rechaza
        raise HTTPException(status_code=403, detail="No tenés acceso a esa sucursal")
									# Lanza 403 advirtiendo que no tiene acceso a esa
									# sucursal
    new_cam = models.ParkingCamera(					# Crea el objeto `ParkingCamera` con los datos
									# recibidos
        nombre=data.nombre,						# Asigna el nombre de la camara
        tipo=data.tipo.upper(),						# Asigna el tipo en mayusculas
        source=data.source,						# Asigna la fuente
        sucursal_id=branch_id,						# Asigna el id de sede resuelto
        activa=data.activa						# Asigna el estado activa
    )									# Cierra la construccion del modelo
    if branch_id is None and sucursal:					# Si no se resolvio branch_id pero hay nombre de
									# sede, guarda un fallback
        new_cam.__dict__["_sucursal_fallback"] = sucursal		# Guarda el nombre de sede como
									# `_sucursal_fallback` en el objeto
    db.add(new_cam)							# Agrega la camara a la sesion
    db.commit()								# Confirma el alta con commit
    db.refresh(new_cam)							# Refresca el objeto para obtener el id generado y
									# otros campos
    return schemas.CameraResponse(					# Empieza a armar la respuesta `CameraResponse` de
									# la camara creada
        id=new_cam.id,							# Incluye el id asignado
        nombre=new_cam.nombre,						# Incluye el nombre
        tipo=new_cam.tipo,						# Incluye el tipo
        source=new_cam.source,						# Incluye la fuente
        activa=new_cam.activa,						# Incluye el estado activa
        sucursal=new_cam.sucursal,					# Incluye la sede
        orden=new_cam.orden,						# Incluye el orden
        is_running=False						# Marca `is_running` en False (recien creada, aun
									# no corre)
    )									# Cierra la respuesta y la devuelve

@router.put("/cameras/order")						# Decorador que registra PUT `/cameras/order`
									# (guardar orden manual de la grilla)
def reorder_cameras(data: schemas.CameraOrderUpdate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
									# Define `reorder_cameras` con el schema
									# `CameraOrderUpdate`, la sesion y el staff
									# operativo
    """GUARDA EL ORDEN MANUAL DE LAS CÁMARAS EN LA GRILLA DE MONITOREO.

    Recibe la lista de ids en el orden deseado y asigna `orden` secuencial (1..N).
    Un usuario no-admin solo puede reordenar cámaras de su sucursal.
    """
    cameras = []							# Inicializa `cameras` con los objetos a reordenar
    for camera_id in data.ids:						# Recorre cada id de camara en el orden pedido
        camera = CameraRepository.get_by_id(db, camera_id)		# Busca la camara por id en el repositorio
        if not camera:							# Si no existe, corta con error
            raise HTTPException(status_code=404, detail=f"Cámara {camera_id} no encontrada")
									# Lanza 404 indicando que la camara no fue
									# encontrada
        _enforce_camera_org(staff, camera, db=db)			# Aplica el aislamiento multiempresa sobre la
									# camara
        if staff.rol != UserRole.ADMIN and not misma_sucursal(camera, staff):
									# Si no es ADMIN y la camara no es de su sede,
									# rechaza
            raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")
									# Lanza 403 sin acceso a esa camara
        cameras.append(camera)						# Agrega la camara validada a la lista
    for index, camera in enumerate(cameras):				# Recorre las camaras validadas con su indice
        camera.orden = index + 1					# Asigna el `orden` secuencial empezando en 1
    db.commit()								# Confirma todos los cambios con commit
    return {"status": "ok", "message": "Orden actualizado"}		# Devuelve 'ok' con el mensaje de orden
									# actualizado

@router.put("/cameras/{camera_id}", response_model=schemas.CameraResponse)
									# Decorador que registra PUT `/cameras/{camera_id}`
									# (actualizar camara)
def update_camera(camera_id: int, data: schemas.CameraCreate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
									# Define `update_camera` con el id, los datos, la
									# sesion y el staff operativo
    camera = CameraRepository.get_by_id(db, camera_id)			# Busca la camara por id
    if not camera:							# Si no existe, corta con error
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
									# Lanza 404 de camara no encontrada
    _enforce_camera_org(staff, camera, db=db)				# Aplica el aislamiento multiempresa
    if staff.rol != UserRole.ADMIN and not misma_sucursal(camera, staff):
									# Si no es ADMIN y no es de su sede, rechaza
        raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")
									# Lanza 403 sin acceso a esa camara
    camera.nombre = data.nombre						# Actualiza el nombre de la camara
    camera.tipo = data.tipo.upper()					# Actualiza el tipo en mayusculas
    camera.source = data.source						# Actualiza la fuente
    camera.activa = data.activa						# Actualiza el estado activa
    if staff.rol == UserRole.ADMIN:					# Solo si el usuario es ADMIN puede cambiar la sede
									# de la camara
        camera.sucursal = data.sucursal					# Actualiza la sede de la camara
    db.commit()								# Confirma los cambios con commit
    db.refresh(camera)							# Refresca el objeto tras el commit
    
    norm_suc = normalize_system_name(camera.sucursal) if camera.sucursal else "GLOBAL"
									# Calcula el nombre de sede normalizado (o
									# 'GLOBAL')
    proc_id = f"{norm_suc}_{camera.tipo}_{camera.id}".upper()		# Construye el `proc_id` de la camara
    is_running = proc_id in CAMERA_PROCESSES and CAMERA_PROCESSES[proc_id].poll() is None
									# Determina si su proceso sigue corriendo
    
    return schemas.CameraResponse(					# Empieza a armar la respuesta `CameraResponse`
									# actualizada
        id=camera.id,							# Incluye el id
        nombre=camera.nombre,						# Incluye el nombre
        tipo=camera.tipo,						# Incluye el tipo
        source=camera.source,						# Incluye la fuente
        activa=camera.activa,						# Incluye el estado activa
        sucursal=camera.sucursal,					# Incluye la sede
        orden=camera.orden,						# Incluye el orden
        is_running=is_running						# Incluye si esta corriendo
    )									# Cierra la respuesta y la devuelve

@router.delete("/cameras/{camera_id}")					# Decorador que registra DELETE
									# `/cameras/{camera_id}` (eliminar camara)
def delete_camera(camera_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
									# Define `delete_camera` con el id, la sesion y el
									# staff operativo
    camera = CameraRepository.get_by_id(db, camera_id)			# Busca la camara por id
    if not camera:							# Si no existe, corta con error
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
									# Lanza 404 de camara no encontrada
    _enforce_camera_org(staff, camera, db=db)				# Aplica el aislamiento multiempresa
    if staff.rol != UserRole.ADMIN and not misma_sucursal(camera, staff):
									# Si no es ADMIN y no es de su sede, rechaza
        raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")
									# Lanza 403 sin acceso a esa camara
        
    norm_suc = normalize_system_name(camera.sucursal) if camera.sucursal else "GLOBAL"
									# Calcula el nombre de sede normalizado (o
									# 'GLOBAL')
    proc_id = f"{norm_suc}_{camera.tipo}_{camera.id}".upper()		# Construye el `proc_id` de la camara
    if proc_id in CAMERA_PROCESSES:					# Si hay un proceso corriendo para esa camara, hay
									# que detenerlo antes de borrar
        proc = CAMERA_PROCESSES[proc_id]				# Obtiene el objeto de proceso
        try:								# Abre un `try` para detener el proceso
            if proc.poll() is None:					# Comprueba si el proceso sigue vivo
                if os.name == 'nt':					# Si es Windows, usa `taskkill`
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
									# Mata el arbol de procesos completo, descartando
									# su salida
                else:							# Rama `else` para otros sistemas
                    proc.terminate()					# Envia la senal de terminacion con `terminate()`
        except Exception:						# Captura cualquier error al detener el proceso
            pass							# Ignora el error con `pass`
        del CAMERA_PROCESSES[proc_id]					# Elimina la entrada del proceso del registro
        
    db.delete(camera)							# Elimina la camara de la base de datos
    db.commit()								# Confirma el borrado con commit
    return {"status": "ok", "message": "Cámara eliminada"}		# Devuelve 'ok' con el mensaje de camara eliminada

@router.post("/cameras/{camera_id}/control/{action}")			# Decorador que registra POST
									# `/cameras/{camera_id}/control/{action}` (control
									# dinamico por id)
def control_dynamic_camera_service(camera_id: int, action: str, request: Request, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
									# Define `control_dynamic_camera_service` con id,
									# accion, request, sesion y staff operativo
    camera = CameraRepository.get_by_id(db, camera_id)			# Busca la camara por id
    if not camera:							# Si no existe, corta con error
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
									# Lanza 404 de camara no encontrada
    _enforce_camera_org(staff, camera, db=db)				# Aplica el aislamiento multiempresa
    if staff.rol != UserRole.ADMIN and not misma_sucursal(camera, staff):
									# Si no es ADMIN y no es de su sede, rechaza
        raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")
									# Lanza 403 sin acceso a esa camara
        
    norm_suc = normalize_system_name(camera.sucursal) if camera.sucursal else "GLOBAL"
									# Calcula el nombre de sede normalizado (o
									# 'GLOBAL')
    proc_id = f"{norm_suc}_{camera.tipo}_{camera.id}".upper()		# Construye el `proc_id` de la camara
    
    if action == "start":						# Rama `if` para la accion 'start'
        if proc_id in CAMERA_PROCESSES and CAMERA_PROCESSES[proc_id].poll() is None:
									# Comprueba si el proceso ya esta corriendo
            return {"status": "error", "message": "Ya está en ejecución"}
									# Devuelve error 'Ya esta en ejecucion'
            
        # El ALPR corre en la misma máquina que el backend: conectar por localhost
        # (no a través de un túnel) para evitar el doble-hop de los frames de video
        base_url = f"http://127.0.0.1:{request.url.port or 8000}"	# Construye la URL base en 127.0.0.1 con el puerto
									# del request o 8000
        env = os.environ.copy()						# Copia el entorno del proceso actual
        env["GATE_ID"] = proc_id					# Inyecta `GATE_ID` con el `proc_id` de la camara
        env["VIDEO_SOURCE"] = camera.source				# Inyecta `VIDEO_SOURCE` con la fuente de la
									# camara
        gt = camera.tipo.lower()					# Toma el tipo de camara en minusculas como base
									# del tipo de porton
        if "qr" in gt:							# Si el tipo contiene 'qr', configura el tipo QR
            env["GATE_TYPE"] = "qr"					# Asigna `GATE_TYPE` = 'qr'
        elif "egreso" in gt or "salida" in gt:				# Si el tipo indica egreso o salida, configura el
									# tipo salida
            env["GATE_TYPE"] = "salida"					# Asigna `GATE_TYPE` = 'salida'
        elif "patente" in gt or "entrada" in gt:			# Si el tipo indica patente o entrada, configura el
									# tipo entrada
            env["GATE_TYPE"] = "entrada"				# Asigna `GATE_TYPE` = 'entrada'
        else:								# Rama `else`: usa el tipo tal cual como GATE_TYPE
            env["GATE_TYPE"] = gt					# Asigna `GATE_TYPE` con el tipo en minusculas
        env["BACKEND_URL"] = base_url					# Inyecta `BACKEND_URL` con la URL base local
        env["PYTHONUNBUFFERED"] = "1"					# Activa `PYTHONUNBUFFERED`
        
        try:								# Abre un `try` para lanzar el subproceso
            logger.info(f"Iniciando ALPR para {camera.nombre} ({proc_id}) con fuente: {camera.source}")
									# Registra en log el inicio del ALPR con nombre y
									# proc_id
            proc = subprocess.Popen(					# Lanza el subproceso `alpr_service.py` con el
									# entorno preparado
                [sys.executable, "alpr_service.py"],			# Usa el interprete Python actual
                env=env,						# Pasa el entorno con las variables inyectadas
                stdout=subprocess.PIPE,					# Captura el stdout en un pipe
                stderr=subprocess.STDOUT,				# Redirige stderr al mismo pipe
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
									# En Windows crea un nuevo grupo de procesos
            )								# Cierra la llamada al constructor del subproceso
            CAMERA_PROCESSES[proc_id] = proc				# Registra el proceso en `CAMERA_PROCESSES` bajo el
									# proc_id
            threading.Thread(target=_stream_console_output, args=(proc, proc_id), daemon=True).start()
									# Lanza el hilo daemon que reenvia la consola de la
									# camara al front
            return {"status": "ok", "message": f"Servicio para {camera.nombre} iniciado"}
									# Devuelve 'ok' indicando que el servicio de esa
									# camara se inicio
        except Exception as e:						# Captura cualquier error al lanzar el subproceso
            return {"status": "error", "message": str(e)}		# Devuelve error con el mensaje de la excepcion
            
    elif action == "stop":						# Rama `elif` para la accion 'stop'
        if proc_id not in CAMERA_PROCESSES:				# Comprueba que exista un proceso registrado
            return {"status": "error", "message": "No está en ejecución"}
									# Devuelve error 'No esta en ejecucion'
            
        proc = CAMERA_PROCESSES[proc_id]				# Obtiene el objeto de proceso
        try:								# Abre un `try` para detenerlo
            if proc.poll() is None:					# Comprueba si el proceso sigue vivo
                if os.name == 'nt':					# Si es Windows, usa `taskkill`
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
									# Mata el arbol de procesos completo, descartando
									# su salida
                else:							# Rama `else` para otros sistemas
                    proc.terminate()					# Envia la senal de terminacion con `terminate()`
            if proc_id in CAMERA_PROCESSES:				# Comprueba que el proceso siga registrado
                del CAMERA_PROCESSES[proc_id]				# Elimina la entrada del proceso del registro
            return {"status": "ok", "message": f"Servicio para {camera.nombre} detenido"}
									# Devuelve 'ok' indicando que el servicio de esa
									# camara se detuvo
        except Exception as e:						# Captura cualquier error al detener el proceso
            return {"status": "error", "message": str(e)}		# Devuelve error con el mensaje de la excepcion
            
    return {"status": "error", "message": "Acción no válida"}		# Devuelve error si la accion no fue valida

@router.post("/camera-reading/{gate_id}", dependencies=[Depends(require_alpr_node)])
									# Registra POST `/camera-reading/{gate_id}`
									# exigiendo un nodo ALPR autorizado como
									# dependencia
def notify_camera_reading(gate_id: str, db: Session = Depends(get_db)):
									# Define `notify_camera_reading` con el gate_id y
									# la sesion de base de datos
    """NOTIFICA AL DASHBOARD QUE LA CAMARA ESTA LEYENDO ACTIVAMENTE UNA PATENTE.
    Solo nodos ALPR autorizados (secret o red local): evita spoofing del estado operativo."""
    from core.normalize import normalize_user_name as normalize_name	# Importa `normalize_user_name` como
									# `normalize_name` para normalizar nombres de sede
    from services.notification_service import NotificationService	# Importa `NotificationService` para publicar el
									# estado de lectura
    sucursal = None							# Inicializa `sucursal` en None; se resolvera a
									# partir del gate_id
    if '_' in gate_id:							# Comprueba si el gate_id contiene '_' para extraer
									# el prefijo de sede
        suc_short = normalize_name(gate_id.split('_')[0])		# Toma la parte anterior al '_' y la normaliza como
									# nombre corto de sede
        try:								# Abre un `try` para buscar la sede por nombre
            branches = BranchRepository.get_all(db)			# Trae todas las sedes registradas
            for b in branches:						# Recorre cada sede
                if normalize_name(b.nombre) == suc_short:		# Si el nombre normalizado de la sede coincide con
									# el prefijo del gate, la encuentra
                    sucursal = b.nombre					# Guarda el nombre real de la sede
                    break						# Corta el bucle al encontrar la sede
        except Exception:						# Captura errores al buscar la sede
            pass							# Ignora el error y deja la sucursal como None
    suc_norm = normalize_name(sucursal) if sucursal else "GLOBAL"	# Normaliza el nombre de sede para el evento,
									# usando 'GLOBAL' si no se resolvio
    NotificationService.set_last_event(suc_norm, "READING", "", "LEYENDO PATENTE...", "reading")
									# Publica el ultimo evento de tipo 'READING' con el
									# texto 'LEYENDO PATENTE...'
    return {"status": "ok"}						# Devuelve 'ok' confirmando que se registro el
									# estado de lectura
