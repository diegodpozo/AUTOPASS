from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import text, and_, or_
from typing import List, Dict
import math
import datetime
import models, schemas
from core.database import get_db
from core.config import settings
from core.security import get_operational_user, decode_access_token
from core.logger import get_logger
from services.billing_service import BillingService
from services.notification_service import NotificationService
from services.time_service import TimeService
from models.enums import ReservationStatus
from core.normalize import normalize_name

logger = get_logger("WS")

router = APIRouter()

class OccupancyManager:
    def __init__(self):
        #SUCURSAL_NAME (NORMALIZADO) -> LISTA DE WEBSOCKETS ACTIVOS
        #ADMIN GLOBAL USA "GLOBAL"
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user: models.User):
        await websocket.accept()
        sucursal = normalize_name(user.sucursal) if user.rol != "admin" else "GLOBAL"
        
        if sucursal not in self.active_connections:
            self.active_connections[sucursal] = []
        self.active_connections[sucursal].append(websocket)
        try:
            logger.info(f"Conexión establecida: user={user.email} sucursal={sucursal}")
        except Exception:
            pass
        return sucursal

    def disconnect(self, websocket: WebSocket, sucursal: str):
        if sucursal in self.active_connections:
            try:
                self.active_connections[sucursal].remove(websocket)
            except ValueError: pass

    async def broadcast_update(self, db: Session = None, sucursal_norm: str = None):
        """ENVIA EL ESTADO ACTUAL DE AFORO A TODOS LOS INTERESADOS.
        Crea su propia sesión de DB si no se provee una, para evitar
        usar una sesión cerrada cuando se llama asincrónicamente."""
        from core.database import SessionLocal
        from core.cache import ttl_cache
        import asyncio
        ttl_cache.invalidate("occupancy_")
        close_session = False
        if db is None:
            db = SessionLocal()
            close_session = True
        try:
            targets = ["GLOBAL"]
            if sucursal_norm and sucursal_norm != "GLOBAL":
                targets.append(sucursal_norm)
                
            for target in targets:
                if target not in self.active_connections or not self.active_connections[target]:
                    continue
                    
                # OBTENER DATOS DE AFORO PARA EL TARGET
                if target == "GLOBAL":
                    data = self._get_global_status(db)
                else:
                    data = self._get_branch_status(db, target)
                
                # ENVIAR A TODOS LOS SOCKETS DE ESTE TARGET DE FORMA CONCURRENTE
                disconnected = []
                async def _send(conn):
                    try:
                        await conn.send_json(data)
                    except Exception:
                        disconnected.append(conn)

                await asyncio.gather(*(_send(c) for c in list(self.active_connections[target])))
                
                for conn in disconnected:
                    self.disconnect(conn, target)
        finally:
            if close_session:
                db.close()

def _calculate_branch_capacities(db: Session, branch: models.ParkingBranch):
    """CALCULA CAPACIDAD Y OCUPACION DE SUCURSAL UNIFICANDO PLANTA BAJA (ParkingAforo) Y PISOS ELEVADOS."""
    a = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == branch.nombre).first()
    if not a and branch.nombre:
        b_norm = normalize_name(branch.nombre)
        for af in db.query(models.ParkingAforo).all():
            if af.sucursal and normalize_name(af.sucursal) == b_norm:
                a = af
                break
    
    cap_autos_pb = a.capacidad_total if (a and a.capacidad_total is not None) else 20
    occ_autos_pb = a.ocupacion_actual if (a and a.ocupacion_actual is not None) else 0
    cap_motos_pb = a.capacidad_motos if (a and a.capacidad_motos is not None) else 10
    occ_motos_pb = a.ocupacion_motos if (a and a.ocupacion_motos is not None) else 0
    cap_camionetas_pb = getattr(a, 'capacidad_camionetas', 5) if (a and getattr(a, 'capacidad_camionetas', None) is not None) else 5
    occ_camionetas_pb = getattr(a, 'ocupacion_camionetas', 0) if (a and getattr(a, 'ocupacion_camionetas', None) is not None) else 0
    cap_res_autos_pb = getattr(a, 'capacidad_reservas_autos', 5) if (a and getattr(a, 'capacidad_reservas_autos', None) is not None) else 5
    occ_res_autos_pb = getattr(a, 'ocupacion_reservas_autos', 0) if (a and getattr(a, 'ocupacion_reservas_autos', None) is not None) else 0
    cap_res_motos_pb = getattr(a, 'capacidad_reservas_motos', 3) if (a and getattr(a, 'capacidad_reservas_motos', None) is not None) else 3
    occ_res_motos_pb = getattr(a, 'ocupacion_reservas_motos', 0) if (a and getattr(a, 'ocupacion_reservas_motos', None) is not None) else 0
    cap_res_camionetas_pb = getattr(a, 'capacidad_reservas_camionetas', 2) if (a and getattr(a, 'capacidad_reservas_camionetas', None) is not None) else 2
    occ_res_camionetas_pb = getattr(a, 'ocupacion_reservas_camionetas', 0) if (a and getattr(a, 'ocupacion_reservas_camionetas', None) is not None) else 0
    cap_reservas_pb = getattr(a, 'capacidad_reservas', cap_res_autos_pb + cap_res_motos_pb + cap_res_camionetas_pb) if (a and getattr(a, 'capacidad_reservas', None) is not None) else (cap_res_autos_pb + cap_res_motos_pb + cap_res_camionetas_pb)
    occ_reservas_pb = getattr(a, 'ocupacion_reservas', occ_res_autos_pb + occ_res_motos_pb + occ_res_camionetas_pb) if (a and getattr(a, 'ocupacion_reservas', None) is not None) else (occ_res_autos_pb + occ_res_motos_pb + occ_res_camionetas_pb)

    floors = branch.floors if (branch and branch.floors) else []

    floors_cap_autos = sum(f.capacidad_total or 0 for f in floors)
    floors_occ_autos = sum(f.ocupacion_actual or 0 for f in floors)
    floors_cap_motos = sum(f.capacidad_motos or 0 for f in floors)
    floors_occ_motos = sum(f.ocupacion_motos or 0 for f in floors)
    floors_cap_camionetas = sum((getattr(f, 'capacidad_camionetas', 5) or 0) for f in floors)
    floors_occ_camionetas = sum((getattr(f, 'ocupacion_camionetas', 0) or 0) for f in floors)
    floors_cap_res_autos = sum((getattr(f, 'capacidad_reservas_autos', 0) or 0) for f in floors)
    floors_occ_res_autos = sum((getattr(f, 'ocupacion_reservas_autos', 0) or 0) for f in floors)
    floors_cap_res_motos = sum((getattr(f, 'capacidad_reservas_motos', 0) or 0) for f in floors)
    floors_occ_res_motos = sum((getattr(f, 'ocupacion_reservas_motos', 0) or 0) for f in floors)
    floors_cap_res_camionetas = sum((getattr(f, 'capacidad_reservas_camionetas', 0) or 0) for f in floors)
    floors_occ_res_camionetas = sum((getattr(f, 'ocupacion_reservas_camionetas', 0) or 0) for f in floors)
    floors_cap_reservas = sum((getattr(f, 'capacidad_reservas', 0) or 0) for f in floors)
    floors_occ_reservas = sum((getattr(f, 'ocupacion_reservas', 0) or 0) for f in floors)

    cap_total = cap_autos_pb + floors_cap_autos
    occ_total = occ_autos_pb + floors_occ_autos
    cap_motos = cap_motos_pb + floors_cap_motos
    occ_motos = occ_motos_pb + floors_occ_motos
    cap_camionetas = cap_camionetas_pb + floors_cap_camionetas
    occ_camionetas = occ_camionetas_pb + floors_occ_camionetas

    cap_res_autos = cap_res_autos_pb + floors_cap_res_autos
    occ_res_autos = occ_res_autos_pb + floors_occ_res_autos
    cap_res_motos = cap_res_motos_pb + floors_cap_res_motos
    occ_res_motos = occ_res_motos_pb + floors_occ_res_motos
    cap_res_camionetas = cap_res_camionetas_pb + floors_cap_res_camionetas
    occ_res_camionetas = occ_res_camionetas_pb + floors_occ_res_camionetas
    cap_reservas = cap_reservas_pb + floors_cap_reservas
    occ_reservas = occ_reservas_pb + floors_occ_reservas

    return {
        "capacidad_total": cap_total,
        "ocupacion_actual": occ_total,
        "capacidad_motos": cap_motos,
        "ocupacion_motos": occ_motos,
        "capacidad_camionetas": cap_camionetas,
        "ocupacion_camionetas": occ_camionetas,
        "capacidad_reservas": cap_reservas,
        "ocupacion_reservas": occ_reservas,
        "capacidad_reservas_autos": cap_res_autos,
        "ocupacion_reservas_autos": occ_res_autos,
        "capacidad_reservas_motos": cap_res_motos,
        "ocupacion_reservas_motos": occ_res_motos,
        "capacidad_reservas_camionetas": cap_res_camionetas,
        "ocupacion_reservas_camionetas": occ_res_camionetas,
        "disponibilidad": max(0, cap_total - occ_total),
        "disponibilidad_motos": max(0, cap_motos - occ_motos),
        "disponibilidad_camionetas": max(0, cap_camionetas - occ_camionetas),
        "disponibilidad_reservas": max(0, cap_reservas - occ_reservas),
        "disponibilidad_reservas_autos": max(0, cap_res_autos - occ_res_autos),
        "disponibilidad_reservas_motos": max(0, cap_res_motos - occ_res_motos),
        "disponibilidad_reservas_camionetas": max(0, cap_res_camionetas - occ_res_camionetas),
    }

class OccupancyManager:
    def __init__(self):
        #SUCURSAL_NAME (NORMALIZADO) -> LISTA DE WEBSOCKETS ACTIVOS
        #ADMIN GLOBAL USA "GLOBAL"
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user: models.User):
        await websocket.accept()
        sucursal = normalize_name(user.sucursal) if user.rol != "admin" else "GLOBAL"
        
        if sucursal not in self.active_connections:
            self.active_connections[sucursal] = []
        self.active_connections[sucursal].append(websocket)
        try:
            logger.info(f"Conexión establecida: user={user.email} sucursal={sucursal}")
        except Exception:
            pass
        return sucursal

    def disconnect(self, websocket: WebSocket, sucursal: str):
        if sucursal in self.active_connections:
            try:
                self.active_connections[sucursal].remove(websocket)
            except ValueError: pass

    async def broadcast_update(self, db: Session = None, sucursal_norm: str = None):
        """ENVIA EL ESTADO ACTUAL DE AFORO A TODOS LOS INTERESADOS.
        Crea su propia sesión de DB si no se provee una, para evitar
        usar una sesión cerrada cuando se llama asincrónicamente."""
        from core.database import SessionLocal
        from core.cache import ttl_cache
        import asyncio
        ttl_cache.invalidate("occupancy_")
        close_session = False
        if db is None:
            db = SessionLocal()
            close_session = True
        try:
            targets = ["GLOBAL"]
            if sucursal_norm and sucursal_norm != "GLOBAL":
                targets.append(sucursal_norm)
                
            for target in targets:
                if target not in self.active_connections or not self.active_connections[target]:
                    continue
                    
                # OBTENER DATOS DE AFORO PARA EL TARGET
                if target == "GLOBAL":
                    data = self._get_global_status(db)
                else:
                    data = self._get_branch_status(db, target)
                
                # ENVIAR A TODOS LOS SOCKETS DE ESTE TARGET DE FORMA CONCURRENTE
                disconnected = []
                async def _send(conn):
                    try:
                        await conn.send_json(data)
                    except Exception:
                        disconnected.append(conn)

                await asyncio.gather(*(_send(c) for c in list(self.active_connections[target])))
                
                for conn in disconnected:
                    self.disconnect(conn, target)
        finally:
            if close_session:
                db.close()

    def _get_global_status(self, db: Session):
        branches = db.query(models.ParkingBranch).filter(models.ParkingBranch.activa == True).all()
        res = []
        for b in branches:
            caps = _calculate_branch_capacities(db, b)
            res.append({
                "id": b.id, "nombre": b.nombre, 
                "ocupacion": caps["ocupacion_actual"], "capacidad": caps["capacidad_total"], 
                "ocupacion_reservas": caps["ocupacion_reservas"], "capacidad_reservas": caps["capacidad_reservas"],
                "capacidad_reservas_autos": caps["capacidad_reservas_autos"], "ocupacion_reservas_autos": caps["ocupacion_reservas_autos"],
                "capacidad_reservas_motos": caps["capacidad_reservas_motos"], "ocupacion_reservas_motos": caps["ocupacion_reservas_motos"],
                "capacidad_reservas_camionetas": caps["capacidad_reservas_camionetas"], "ocupacion_reservas_camionetas": caps["ocupacion_reservas_camionetas"]
            })
        return {"type": "GLOBAL_UPDATE", "branches": res}

    def _get_branch_status(self, db: Session, sucursal_norm: str):
        # BUSCAR SUCURSAL POR NOMBRE NORMALIZADO
        branches = db.query(models.ParkingBranch).all()
        branch = None
        for b in branches:
            if normalize_name(b.nombre) == sucursal_norm:
                branch = b
                break
        
        if branch:
            data = _calculate_branch_capacities(db, branch)
            data["last_event"] = NotificationService.get_last_event(sucursal_norm)
            return {
                "type": "BRANCH_UPDATE",
                "data": data
            }
        else:
            aforos = db.query(models.ParkingAforo).all()
            a = None
            for af in aforos:
                if normalize_name(af.sucursal) == sucursal_norm:
                    a = af
                    break
            
            if not a:
                return {
                    "type": "BRANCH_UPDATE", 
                    "data": {
                        "capacidad_total": 20, "ocupacion_actual": 0, "disponibilidad": 20, 
                        "capacidad_motos": 10, "ocupacion_motos": 0, "disponibilidad_motos": 10, 
                        "capacidad_camionetas": 5, "ocupacion_camionetas": 0, "disponibilidad_camionetas": 5, 
                        "capacidad_reservas": 0, "ocupacion_reservas": 0, "disponibilidad_reservas": 0,
                        "capacidad_reservas_autos": 0, "ocupacion_reservas_autos": 0, "disponibilidad_reservas_autos": 0,
                        "capacidad_reservas_motos": 0, "ocupacion_reservas_motos": 0, "disponibilidad_reservas_motos": 0,
                        "capacidad_reservas_camionetas": 0, "ocupacion_reservas_camionetas": 0, "disponibilidad_reservas_camionetas": 0,
                        "last_event": NotificationService.get_last_event(sucursal_norm)
                    }
                }
            
            cap_total = a.capacidad_total
            occ_total = a.ocupacion_actual
            cap_motos = a.capacidad_motos
            occ_motos = a.ocupacion_motos
            cap_camionetas = getattr(a, 'capacidad_camionetas', 5)
            occ_camionetas = getattr(a, 'ocupacion_camionetas', 0)
            cap_reservas = getattr(a, 'capacidad_reservas', 0)
            occ_reservas = getattr(a, 'ocupacion_reservas', 0)
            cap_res_autos = getattr(a, 'capacidad_reservas_autos', 0)
            occ_res_autos = getattr(a, 'ocupacion_reservas_autos', 0)
            cap_res_motos = getattr(a, 'capacidad_reservas_motos', 0)
            occ_res_motos = getattr(a, 'ocupacion_reservas_motos', 0)
            cap_res_camionetas = getattr(a, 'capacidad_reservas_camionetas', 0)
            occ_res_camionetas = getattr(a, 'ocupacion_reservas_camionetas', 0)

            return {
                "type": "BRANCH_UPDATE",
                "data": {
                    "capacidad_total": cap_total, 
                    "ocupacion_actual": occ_total, 
                    "capacidad_motos": cap_motos,
                    "ocupacion_motos": occ_motos,
                    "capacidad_camionetas": cap_camionetas,
                    "ocupacion_camionetas": occ_camionetas,
                    "capacidad_reservas": cap_reservas,
                    "ocupacion_reservas": occ_reservas,
                    "capacidad_reservas_autos": cap_res_autos,
                    "ocupacion_reservas_autos": occ_res_autos,
                    "capacidad_reservas_motos": cap_res_motos,
                    "ocupacion_reservas_motos": occ_res_motos,
                    "capacidad_reservas_camionetas": cap_res_camionetas,
                    "ocupacion_reservas_camionetas": occ_res_camionetas,
                    "disponibilidad": cap_total - occ_total,
                    "disponibilidad_motos": cap_motos - occ_motos,
                    "disponibilidad_camionetas": cap_camionetas - occ_camionetas,
                    "disponibilidad_reservas": max(0, cap_reservas - occ_reservas),
                    "disponibilidad_reservas_autos": max(0, cap_res_autos - occ_res_autos),
                    "disponibilidad_reservas_motos": max(0, cap_res_motos - occ_res_motos),
                    "disponibilidad_reservas_camionetas": max(0, cap_res_camionetas - occ_res_camionetas),
                    "last_event": NotificationService.get_last_event(sucursal_norm)
                }
            }

occupancy_manager = OccupancyManager()
NotificationService.set_occupancy_manager(occupancy_manager)

@router.websocket("/parking/ws")
async def occupancy_websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    if not token:
        await websocket.close(code=4008)
        return

    try:
        payload = decode_access_token(token)
        db = next(get_db())
        user = db.query(models.User).filter(models.User.email == payload.get("sub")).first()
        if not user:
            await websocket.close(code=4008)
            return
            
        sucursal = await occupancy_manager.connect(websocket, user)
        
        # Registrar el event loop principal para permitir notificaciones desde hilos sincrónicos
        try:
            import services.notification_service as notif
            notif.NotificationService.set_event_loop(asyncio.get_running_loop())
        except Exception:
            pass
        
        # ENVIAR PRIMER ESTADO INMEDIATAMENTE
        await occupancy_manager.broadcast_update(db, sucursal if sucursal != "GLOBAL" else None)
        
        try:
            while True:
                await websocket.receive_text() #MANTENER VIVA
        except WebSocketDisconnect:
            occupancy_manager.disconnect(websocket, sucursal)
    except:
        await websocket.close(code=4008)

@router.get("/parking/branches", response_model=List[schemas.BranchPublicResponse])
def list_public_branches(db: Session = Depends(get_db)):
    """RETORNA LA LISTA DE SUCURSALES ACTIVAS CON SU OCUPACION REAL PARA EL MAPA PUBLICO."""
    from core.cache import ttl_cache
    cached = ttl_cache.get("occupancy_public_branches")
    if cached is not None:
        return cached

    branches = db.query(models.ParkingBranch).options(joinedload(models.ParkingBranch.floors)).filter(models.ParkingBranch.activa == True, models.ParkingBranch.latitude != None, models.ParkingBranch.longitude != None).all()
    
    res = []
    for b in branches:
        caps = _calculate_branch_capacities(db, b)
        floors_data = [schemas.FloorResponse.from_orm(f) for f in b.floors] if b.floors else []

        res.append({
            "id": b.id,
            "nombre": b.nombre,
            "direccion": b.direccion,
            "telefono": b.telefono,
            "horario": b.horario,
            "is_24h": b.is_24h,
            "logo_url": b.logo_url,
            "activa": b.activa,
            "latitude": b.latitude,
            "longitude": b.longitude,
            "ocupacion_actual": caps["ocupacion_actual"],
            "capacidad_total": caps["capacidad_total"],
            "ocupacion_motos": caps["ocupacion_motos"],
            "capacidad_motos": caps["capacidad_motos"],
            "ocupacion_camionetas": caps["ocupacion_camionetas"],
            "capacidad_camionetas": caps["capacidad_camionetas"],
            "ocupacion_reservas": caps["ocupacion_reservas"],
            "capacidad_reservas": caps["capacidad_reservas"],
            "ocupacion_reservas_autos": caps["ocupacion_reservas_autos"],
            "capacidad_reservas_autos": caps["capacidad_reservas_autos"],
            "ocupacion_reservas_motos": caps["ocupacion_reservas_motos"],
            "capacidad_reservas_motos": caps["capacidad_reservas_motos"],
            "ocupacion_reservas_camionetas": caps["ocupacion_reservas_camionetas"],
            "capacidad_reservas_camionetas": caps["capacidad_reservas_camionetas"],
            "floors": floors_data
        })
    ttl_cache.set("occupancy_public_branches", res, ttl=3.0)
    return res

@router.get("/parking/status", response_model=schemas.ParkingStatus)
def get_parking_status(db: Session = Depends(get_db), user: models.User = Depends(get_operational_user)):
    """RETORNA LA DISPONIBILIDAD ACTUAL DE PLAZAS. AISLAMIENTO POR SEDE Y SOPORTE PARA PISOS."""
    sucursal_nombre = user.sucursal if user.rol != "admin" else None
    
    branch = None
    if sucursal_nombre:
        branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == sucursal_nombre).first()
    if not branch:
        branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.activa == True).first()

    if branch:
        return _calculate_branch_capacities(db, branch)
    
    a = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal_nombre).first() if sucursal_nombre else None
    if not a: 
        return {
            "capacidad_total": 20, "ocupacion_actual": 0, "disponibilidad": 20,
            "capacidad_motos": 10, "ocupacion_motos": 0, "disponibilidad_motos": 10,
            "capacidad_camionetas": 5, "ocupacion_camionetas": 0, "disponibilidad_camionetas": 5,
            "capacidad_reservas": 0, "ocupacion_reservas": 0, "disponibilidad_reservas": 0,
            "capacidad_reservas_autos": 0, "ocupacion_reservas_autos": 0, "disponibilidad_reservas_autos": 0,
            "capacidad_reservas_motos": 0, "ocupacion_reservas_motos": 0, "disponibilidad_reservas_motos": 0,
            "capacidad_reservas_camionetas": 0, "ocupacion_reservas_camionetas": 0, "disponibilidad_reservas_camionetas": 0,
        }

    cap_total = a.capacidad_total
    occ_total = a.ocupacion_actual
    cap_motos = a.capacidad_motos
    occ_motos = a.ocupacion_motos
    cap_camionetas = getattr(a, 'capacidad_camionetas', 5)
    occ_camionetas = getattr(a, 'ocupacion_camionetas', 0)
    cap_reservas = getattr(a, 'capacidad_reservas', 0)
    occ_reservas = getattr(a, 'ocupacion_reservas', 0)
    cap_res_autos = getattr(a, 'capacidad_reservas_autos', 0)
    occ_res_autos = getattr(a, 'ocupacion_reservas_autos', 0)
    cap_res_motos = getattr(a, 'capacidad_reservas_motos', 0)
    occ_res_motos = getattr(a, 'ocupacion_reservas_motos', 0)
    cap_res_camionetas = getattr(a, 'capacidad_reservas_camionetas', 0)
    occ_res_camionetas = getattr(a, 'ocupacion_reservas_camionetas', 0)

    return {
        "capacidad_total": cap_total, 
        "ocupacion_actual": occ_total, 
        "capacidad_motos": cap_motos,
        "ocupacion_motos": occ_motos,
        "capacidad_camionetas": cap_camionetas,
        "ocupacion_camionetas": occ_camionetas,
        "capacidad_reservas": cap_reservas,
        "ocupacion_reservas": occ_reservas,
        "capacidad_reservas_autos": cap_res_autos,
        "ocupacion_reservas_autos": occ_res_autos,
        "capacidad_reservas_motos": cap_res_motos,
        "ocupacion_reservas_motos": occ_res_motos,
        "capacidad_reservas_camionetas": cap_res_camionetas,
        "ocupacion_reservas_camionetas": occ_res_camionetas,
        "disponibilidad": cap_total - occ_total,
        "disponibilidad_motos": cap_motos - occ_motos,
        "disponibilidad_camionetas": cap_camionetas - occ_camionetas,
        "disponibilidad_reservas": max(0, cap_reservas - occ_reservas),
        "disponibilidad_reservas_autos": max(0, cap_res_autos - occ_res_autos),
        "disponibilidad_reservas_motos": max(0, cap_res_motos - occ_res_motos),
        "disponibilidad_reservas_camionetas": max(0, cap_res_camionetas - occ_res_camionetas)
    }

@router.get("/parking/current-occupancy")
def current_occupancy(db: Session = Depends(get_db), user: models.User = Depends(get_operational_user)):
    """LISTA VEHICULOS ESTACIONADOS EN LA SEDE DEL USUARIO CON DEUDA CALCULADA. OPTIMIZADO PARA UNICIDAD Y ORDEN."""
    sucursal = user.sucursal if user.rol != "admin" else None

    # 1. OBTENEMOS LAS ENTRADAS MAS RECIENTES POR PATENTE EN LA SEDE
    # USAMOS UNA SUBCONSULTA PARA ENCONTRAR EL ID MAXIMO DE ENTRADA POR PATENTE
    from sqlalchemy import func
    subq = db.query(
        models.AccessLog.patente_detectada,
        func.max(models.AccessLog.id).label("max_id")
    ).filter(models.AccessLog.tipo_evento == "ENTRADA")

    if sucursal:
        subq = subq.filter(models.AccessLog.sucursal == sucursal)

    subq = subq.group_by(models.AccessLog.patente_detectada).subquery()

    # 2. CONSULTAMOS LOS DETALLES DE ESAS ENTRADAS (CON EL PISO CARGADO EN LA MISMA QUERY)
    entradas = db.query(models.AccessLog).options(
        selectinload(models.AccessLog.floor)
    ).join(
        subq, models.AccessLog.id == subq.c.max_id
    ).order_by(models.AccessLog.fecha_hora.desc()).all()

    # 3. SALIDAS POSTERIORES POR (PATENTE, SUCURSAL): 1 SOLA QUERY AGRUPADA
    salida_max = {}
    if entradas:
        patentes = {e.patente_detectada for e in entradas}
        sucursales = {e.sucursal for e in entradas if e.sucursal}
        rows = db.query(
            models.AccessLog.patente_detectada,
            models.AccessLog.sucursal,
            func.max(models.AccessLog.id).label("max_salida_id")
        ).filter(
            models.AccessLog.tipo_evento == "SALIDA",
            models.AccessLog.patente_detectada.in_(patentes),
            models.AccessLog.sucursal.in_(sucursales)
        ).group_by(models.AccessLog.patente_detectada, models.AccessLog.sucursal).all()
        salida_max = {(p, s): m for p, s, m in rows}

    # 4. RESERVAS DE LAS ENTRADAS: 1 SOLA QUERY
    reservas = {}
    res_ids = [e.reserva_id for e in entradas if e.reserva_id]
    if res_ids:
        reservas = {
            r.id: r for r in db.query(models.Reservation).filter(models.Reservation.id.in_(res_ids)).all()
        }

    # 5. TARIFAS HORARIAS PRECARGADAS (EVITA 1 QUERY A SETTINGS POR VEHICULO)
    RATE_CLAVES = {
        "Auto": ("precio_30min", "precio_hora"), 
        "Moto": ("precio_30min_moto", "precio_hora_moto"), 
        "Camioneta": ("precio_30min_camioneta", "precio_hora_camioneta")
    }
    sucursales = {e.sucursal for e in entradas if e.sucursal}
    todas_claves = [c for pair in RATE_CLAVES.values() for c in pair]
    rate_cond = models.Settings.clave.in_(todas_claves)
    if sucursales:
        rate_cond = and_(
            models.Settings.clave.in_(todas_claves),
            or_(models.Settings.sucursal.in_(sucursales), models.Settings.sucursal.is_(None))
        )
    else:
        rate_cond = and_(models.Settings.clave.in_(todas_claves), models.Settings.sucursal.is_(None))
    rate_map = {
        (r.clave, r.sucursal): float(r.valor)
        for r in db.query(models.Settings).filter(rate_cond).all()
    }

    def rate30_for(suc, tipo):
        clave30, clave_hora = RATE_CLAVES.get(tipo, ("precio_30min", "precio_hora"))
        if (clave30, suc) in rate_map:
            return rate_map[(clave30, suc)]
        if suc and (clave30, None) in rate_map:
            return rate_map[(clave30, None)]
        # FALLBACK: MITAD DE LA TARIFA HORA
        for c in (clave_hora,):
            if (c, suc) in rate_map:
                return rate_map[(c, suc)] / 2
            if suc and (c, None) in rate_map:
                return rate_map[(c, None)] / 2
        return settings.DEFAULT_HOURLY_RATE / 2

    def calc_debt(entry_time_str, suc, tipo):
        delta = TimeService.now() - datetime.datetime.fromisoformat(entry_time_str)
        bloques = max(1, math.ceil(delta.total_seconds() / 1800))
        return float(bloques * rate30_for(suc, tipo))

    res = []
    for e in entradas:
        # 6. VERIFICAMOS SI ESA ENTRADA ESPECIFICA YA TIENE UNA SALIDA POSTERIOR
        if salida_max.get((e.patente_detectada, e.sucursal), 0) > e.id:
            continue

        floor_name = e.floor.nombre if e.floor else None

        deuda = 0.0
        ya_pago = e.pago_confirmado
        reserva_info = None
        en_cortesia = False

        if e.reserva_id:
            r = reservas.get(e.reserva_id)
            if r:
                reserva_info = {"id": r.id, "tipo_estadia": r.tipo_estadia, "estado_pago": r.estado_pago}
                now_str = TimeService.now_str()
                # SI LA RESERVA EXPIRÓ (COMPLETADA/CANCELADA O FECHA_FIN YA PASÓ), CALCULAR DEUDA DESDE ESE MOMENTO
                if r.estado_reserva in [ReservationStatus.COMPLETADA, ReservationStatus.CANCELADA] or r.fecha_fin < now_str:
                    deuda = calc_debt(r.fecha_fin, e.sucursal, e.tipo_vehiculo)
                    deuda = max(0, deuda - (e.costo_estadia or 0))
                    ya_pago = deuda == 0
                else:
                    deuda = 0.0
                    ya_pago = True
        elif not e.pago_confirmado:
            deuda = calc_debt(e.fecha_hora, e.sucursal, e.tipo_vehiculo)
            entrada_dt = datetime.datetime.fromisoformat(e.fecha_hora)
            minutos_transcurridos = (TimeService.now() - entrada_dt).total_seconds() / 60
            if minutos_transcurridos <= 10:
                en_cortesia = True

        res.append({
            "patente": e.patente_detectada,
            "tipo_vehiculo": e.tipo_vehiculo,
            "ingreso": e.fecha_hora,
            "deuda": deuda,
            "ya_pago": ya_pago,
            "en_cortesia": en_cortesia,
            "es_reserva": e.reserva_id is not None,
            "reserva": reserva_info,
            "sucursal": e.sucursal,
            "floor_nombre": floor_name
        })
    return res
