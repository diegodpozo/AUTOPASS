'''Endpoints /validate-plate (ingreso) y /exit-plate (egreso). Punto de entrada oficial de las lecturas ALPR al sistema central'''


from typing import Optional						# Importa `Optional` para tipar que la organizacion
									# del nodo puede o no venir (None)

from fastapi import APIRouter, Depends, HTTPException, Request		# Importa de FastAPI `APIRouter` (para agrupar
									# rutas), `Depends` (inyeccion), `HTTPException` y
									# `Request`
from sqlalchemy.orm import Session					# Importa `Session` de SQLAlchemy, el tipo de la
									# sesion de base de datos
import models, schemas							# Importa los paquetes `models` (entidades) y
									# `schemas` (contratos de entrada/salida)
from core.database import get_db					# Importa `get_db`, la dependencia que abre y
									# cierra la sesion de base de datos por peticion
from core.limiter import limiter					# Importa `limiter`, el limitador de tasa que
									# aplica los `@limiter.limit` de cada endpoint
from core.security import get_operational_user, resolve_actor_organization_id
									# Importa `get_operational_user` y
									# `resolve_actor_organization_id` de seguridad para
									# autorizar staff operativo
from core.alpr_security import require_alpr_node_org			# Importa `require_alpr_node_org`, la dependencia
									# que valida el nodo ALPR y devuelve su
									# organizacion
from models.enums import UserRole					# Importa `UserRole` para comparar roles (por
									# ejemplo, si es ADMIN global)
from repositories.branch_repository import BranchRepository		# Importa `BranchRepository` para resolver la sede
									# del staff a partir de su nombre
from services.billing_service import BillingService			# Importa `BillingService`, que contiene la logica
									# de cobro de estadias
from services.access_service import AccessService			# Importa `AccessService`, el servicio con la
									# logica de validacion de accesos por patente/QR
from .utils import normalize_plate					# Importa `normalize_plate` del helper local
									# `.utils` para normalizar patentes antes de
									# cobrar
 
router = APIRouter()							# Crea el `router` de FastAPI que agrupa los
									# endpoints de acceso

@router.post("/access/validate-plate", response_model=schemas.AccessResponse)
									# Decorador que registra POST
									# `/access/validate-plate` con respuesta
									# `AccessResponse` (alta por patente)
@limiter.limit("120/minute")						# Aplica limite de 120 peticiones por minuto al
									# endpoint de validacion de patente, evitando abuso
									# del nodo
def validate_plate(request: Request, data: schemas.PlateValidation, db: Session = Depends(get_db), node_org: Optional[int] = Depends(require_alpr_node_org)):
									# Define `validate_plate` con la peticion, el
									# schema `PlateValidation`, la sesion y la
									# organizacion del nodo inyectada
    """VALIDA UNA PATENTE DETECTADA (SOLO NODO ALPR AUTORIZADO, CON SU ORGANIZACION)."""
    return AccessService.validate_plate(db, data, request, organization_id=node_org)
									# Delega la logica a `AccessService.validate_plate`
									# pasando la sesion, los datos, la request y la
									# organizacion del nodo

@router.post("/access/exit-plate", response_model=schemas.AccessResponse)
									# Decorador que registra POST `/access/exit-plate`
									# con respuesta `AccessResponse` (egreso por
									# patente)
@limiter.limit("120/minute")						# Aplica el limite de 120 peticiones por minuto al
									# endpoint de egreso por patente - esto me da una lectura cada medio segundo
def exit_plate(request: Request, data: schemas.PlateValidation, db: Session = Depends(get_db), node_org: Optional[int] = Depends(require_alpr_node_org)):
									# Define `exit_plate` con las mismas dependencias
									# que la validacion de ingreso
    """VALIDA LA SALIDA DE UN VEHICULO (SOLO NODO ALPR AUTORIZADO, CON SU ORGANIZACION)."""
    return AccessService.exit_plate(db, data, request, organization_id=node_org)
									# Delega la logica a `AccessService.exit_plate` con
									# las mismas entradas

@router.post("/access/validate-qr", response_model=schemas.AccessResponse)
									# Decorador que registra POST `/access/validate-qr`
									# (validacion de pase digital)
@limiter.limit("60/minute")						# Aplica un limite mas estricto de 60 peticiones
									# por minuto al endpoint de QR
def validate_qr(request: Request, data: schemas.QRValidation, db: Session = Depends(get_db), node_org: Optional[int] = Depends(require_alpr_node_org)):
									# Define `validate_qr` con la peticion, el schema
									# `QRValidation`, la sesion y la organizacion del
									# nodo
    """VALIDA UN PASE DIGITAL (QR) (SOLO NODO ALPR AUTORIZADO, CON SU ORGANIZACION)."""
    return AccessService.validate_qr(db, data, request, organization_id=node_org)
									# Delega la logica a `AccessService.validate_qr`

@router.post("/access/pay-stay")					# Decorador que registra POST `/access/pay-stay`
									# (cobro de una estadia en curso)
@limiter.limit("10/minute")						# Aplica un limite muy bajo de 10 peticiones por
									# minuto al cobro, que es una operacion sensible
def pay_stay(request: Request, plate: str, metodo: str = "DIGITAL", db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
									# Define `pay_stay` con patente, metodo de pago
									# (por defecto DIGITAL), sesion y el staff
									# operativo autenticado
    """PROCESA EL PAGO DE UNA ESTADIA EN CURSO (SOLO PERSONAL OPERATIVO).

    El cobro queda acotado a la organizacion del staff (y a su sede si no es ADMIN
    global): nunca se cobra una estadia registrada por otra empresa."""
    organizacion = resolve_actor_organization_id(db, staff)		# Resuelve la organizacion del staff autenticado
									# con `resolve_actor_organization_id`
    sucursal_id = None							# Inicializa `sucursal_id` en None; se acotara a la
									# sede solo cuando corresponda
    if staff.rol != UserRole.ADMIN:					# Comprueba si el staff NO es ADMIN global
									# (entonces el cobro debe acotarse a su sede)
        sucursal_id = staff.sucursal_id or BranchRepository.get_id_by_name(db, staff.sucursal, organizacion)
									# Resuelve la sede del staff (por id o por nombre)
									# dentro de su organizacion, acotando el alcance
    result = BillingService.process_payment(				# Llama a `BillingService.process_payment` para
									# procesar el cobro de la estadia
        db, normalize_plate(plate), metodo=metodo.upper(),		# Pasa la patente normalizada y el metodo en
									# mayusculas como parametros del cobro
        organization_id=organizacion, sucursal_id=sucursal_id,		# Pasa la organizacion y la sede resueltas para
									# aislar el cobro al contexto correcto
    )									# Cierra la llamada a `process_payment`
    if result["status"] == "ok": return result				# Si el resultado es 'ok', devuelve el resultado
									# del cobro al cliente
    raise HTTPException(status_code=400, detail=result["message"])	# Si el cobro no fue exitoso, lanza un
									# `HTTPException 400` con el mensaje del servicio
