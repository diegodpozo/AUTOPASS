import asyncio
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict
import models, schemas
from models.enums import UserRole
from core.database import get_db
from core.security import get_operational_user, decode_access_token
from core.logger import get_logger
from services.notification_service import NotificationService
from services.occupancy_service import OccupancyService
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
        sucursal = normalize_name(user.sucursal) if user.rol != UserRole.ADMIN else "GLOBAL"
        
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
            caps = OccupancyService.calculate_branch_capacities(db, b)
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
        branch = OccupancyService.branch_by_normalized_name(db, sucursal_norm)
        
        if branch:
            data = OccupancyService.calculate_branch_capacities(db, branch)
            data["last_event"] = NotificationService.get_last_event(sucursal_norm)
            return {
                "type": "BRANCH_UPDATE",
                "data": data
            }
        else:
            a = OccupancyService.aforo_by_normalized_name(db, sucursal_norm)
            
            if not a:
                data = OccupancyService.default_capacities()
                data["last_event"] = NotificationService.get_last_event(sucursal_norm)
                return {
                    "type": "BRANCH_UPDATE", 
                    "data": data
                }
            
            data = OccupancyService.capacities_from_aforo(a)
            data["last_event"] = NotificationService.get_last_event(sucursal_norm)
            return {
                "type": "BRANCH_UPDATE",
                "data": data
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
        caps = OccupancyService.calculate_branch_capacities(db, b)
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
    sucursal_nombre = user.sucursal if user.rol != UserRole.ADMIN else None
    
    branch = None
    if sucursal_nombre:
        branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == sucursal_nombre).first()
    if not branch:
        branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.activa == True).first()

    if branch:
        return OccupancyService.calculate_branch_capacities(db, branch)
    
    a = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal_nombre).first() if sucursal_nombre else None
    if not a: 
        return OccupancyService.default_capacities()

    return OccupancyService.capacities_from_aforo(a)

@router.get("/parking/current-occupancy")
def current_occupancy(db: Session = Depends(get_db), user: models.User = Depends(get_operational_user)):
    """LISTA VEHICULOS ESTACIONADOS EN LA SEDE DEL USUARIO CON DEUDA CALCULADA."""
    sucursal = user.sucursal if user.rol != UserRole.ADMIN else None
    return OccupancyService.current_occupancy(db, sucursal)