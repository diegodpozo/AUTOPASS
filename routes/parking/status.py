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
        """ENVIA EL ESTADO ACTUAL DE AFORO UN TODOS LOS INTERESADOS.
        Crea su propia sesión de DB si no se provee una, para evitar
        usar una sesión cerrada cuando se llama asincrónicamente."""
        from core.database import SessionLocal
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
                
            # ENVIAR A TODOS LOS SOCKETS DE ESTE TARGET
            disconnected = []
            for connection in self.active_connections[target]:
                try:
                    await connection.send_json(data)
                except:
                    disconnected.append(connection)
            
            for conn in disconnected:
                self.disconnect(conn, target)
        finally:
            if close_session:
                db.close()

    def _get_global_status(self, db: Session):
        branches = db.query(models.ParkingBranch).filter(models.ParkingBranch.activa == True).all()
        res = []
        for b in branches:
            if b.floors:
                cap_total = sum(f.capacidad_total for f in b.floors)
                occ_total = sum(f.ocupacion_actual for f in b.floors)
                cap_motos = sum(f.capacidad_motos for f in b.floors)
                occ_motos = sum(f.ocupacion_motos for f in b.floors)
                cap_camionetas = sum(f.capacidad_camionetas for f in b.floors)
                occ_camionetas = sum(f.ocupacion_camionetas for f in b.floors)
            else:
                a = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == b.nombre).first()
                cap_total = a.capacidad_total if a else 20
                occ_total = a.ocupacion_actual if a else 0
                cap_motos = a.capacidad_motos if a else 10
                occ_motos = a.ocupacion_motos if a else 0
                cap_camionetas = getattr(a, 'capacidad_camionetas', 5) if a else 5
                occ_camionetas = getattr(a, 'ocupacion_camionetas', 0) if a else 0
            res.append({"id": b.id, "nombre": b.nombre, "ocupacion": occ_total, "capacidad": cap_total})
        return {"type": "GLOBAL_UPDATE", "branches": res}

    def _get_branch_status(self, db: Session, sucursal_norm: str):
        # BUSCAR SUCURSAL POR NOMBRE NORMALIZADO
        # PRIMERO BUSCAMOS EN PARKINGBRANCH PARA VER SI TIENE PISOS
        branches = db.query(models.ParkingBranch).all()
        branch = None
        for b in branches:
            if normalize_name(b.nombre) == sucursal_norm:
                branch = b
                break
        
        if branch and branch.floors:
            cap_total = sum(f.capacidad_total for f in branch.floors)
            occ_total = sum(f.ocupacion_actual for f in branch.floors)
            cap_motos = sum(f.capacidad_motos for f in branch.floors)
            occ_motos = sum(f.ocupacion_motos for f in branch.floors)
            cap_camionetas = sum(f.capacidad_camionetas for f in branch.floors)
            occ_camionetas = sum(f.ocupacion_camionetas for f in branch.floors)
        else:
            #FALLBACK UN PARKINGAFORO SI NO HAY SUCURSAL O PISOS
            # PERO PARKINGAFORO.SUCURSAL NO ESTA NORMALIZADA, ASI QUE BUSCAMOS TODAS
            aforos = db.query(models.ParkingAforo).all()
            a = None
            for af in aforos:
                if normalize_name(af.sucursal) == sucursal_norm:
                    a = af
                    break
            
            if not a:
                return {"type": "BRANCH_UPDATE", "data": {"capacidad_total": 20, "ocupacion_actual": 0, "disponibilidad": 20, "capacidad_motos": 10, "ocupacion_motos": 0, "disponibilidad_motos": 10, "capacidad_camionetas": 5, "ocupacion_camionetas": 0, "disponibilidad_camionetas": 5, "last_event": NotificationService.get_last_event(sucursal_norm)}}
            
            cap_total = a.capacidad_total
            occ_total = a.ocupacion_actual
            cap_motos = a.capacidad_motos
            occ_motos = a.ocupacion_motos
            cap_camionetas = getattr(a, 'capacidad_camionetas', 5)
            occ_camionetas = getattr(a, 'ocupacion_camionetas', 0)

        return {
            "type": "BRANCH_UPDATE",
            "data": {
                "capacidad_total": cap_total, 
                "ocupacion_actual": occ_total, 
                "capacidad_motos": cap_motos,
                "ocupacion_motos": occ_motos,
                "capacidad_camionetas": cap_camionetas,
                "ocupacion_camionetas": occ_camionetas,
                "disponibilidad": cap_total - occ_total,
                "disponibilidad_motos": cap_motos - occ_motos,
                "disponibilidad_camionetas": cap_camionetas - occ_camionetas,
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
    branches = db.query(models.ParkingBranch).options(joinedload(models.ParkingBranch.floors)).filter(models.ParkingBranch.activa == True, models.ParkingBranch.latitude != None, models.ParkingBranch.longitude != None).all()
    
    res = []
    for b in branches:
        # SI TIENE PISOS, SUMAMOS SUS CAPACIDADES
        if b.floors:
            cap_total = sum(f.capacidad_total for f in b.floors)
            occ_total = sum(f.ocupacion_actual for f in b.floors)
            cap_motos = sum(f.capacidad_motos for f in b.floors)
            occ_motos = sum(f.ocupacion_motos for f in b.floors)
            cap_camionetas = sum(f.capacidad_camionetas for f in b.floors)
            occ_camionetas = sum(f.ocupacion_camionetas for f in b.floors)
            floors_data = [schemas.FloorResponse.from_orm(f) for f in b.floors]
        else:
            aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == b.nombre).first()
            cap_total = aforo.capacidad_total if aforo else 20
            occ_total = aforo.ocupacion_actual if aforo else 0
            cap_motos = aforo.capacidad_motos if aforo else 10
            occ_motos = aforo.ocupacion_motos if aforo else 0
            cap_camionetas = getattr(aforo, 'capacidad_camionetas', 5) if aforo else 5
            occ_camionetas = getattr(aforo, 'ocupacion_camionetas', 0) if aforo else 0
            floors_data = []

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
            "ocupacion_actual": occ_total,
            "capacidad_total": cap_total,
            "ocupacion_motos": occ_motos,
            "capacidad_motos": cap_motos,
            "ocupacion_camionetas": occ_camionetas,
            "capacidad_camionetas": cap_camionetas,
            "floors": floors_data
        })
    return res

@router.get("/parking/status", response_model=schemas.ParkingStatus)
def get_parking_status(db: Session = Depends(get_db), user: models.User = Depends(get_operational_user)):
    """RETORNA LA DISPONIBILIDAD ACTUAL DE PLAZAS. AISLAMIENTO POR SEDE Y SOPORTE PARA PISOS."""
    sucursal_nombre = user.sucursal if user.rol != "admin" else None
    
    # BUSCAR SUCURSAL POR NOMBRE PARA ACCEDER A SUS PISOS
    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == sucursal_nombre).first()
    
    if branch and branch.floors:
        cap_total = sum(f.capacidad_total for f in branch.floors)
        occ_total = sum(f.ocupacion_actual for f in branch.floors)
        cap_motos = sum(f.capacidad_motos for f in branch.floors)
        occ_motos = sum(f.ocupacion_motos for f in branch.floors)
        cap_camionetas = sum(f.capacidad_camionetas for f in branch.floors)
        occ_camionetas = sum(f.ocupacion_camionetas for f in branch.floors)
    else:
        a = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal_nombre).first()
        if not a: 
            return {
                "capacidad_total": 20, "ocupacion_actual": 0, "disponibilidad": 20,
                "capacidad_motos": 10, "ocupacion_motos": 0, "disponibilidad_motos": 10,
                "capacidad_camionetas": 5, "ocupacion_camionetas": 0, "disponibilidad_camionetas": 5
            }
        cap_total = a.capacidad_total
        occ_total = a.ocupacion_actual
        cap_motos = a.capacidad_motos
        occ_motos = a.ocupacion_motos
        cap_camionetas = getattr(a, 'capacidad_camionetas', 5)
        occ_camionetas = getattr(a, 'ocupacion_camionetas', 0)

    return {
        "capacidad_total": cap_total, 
        "ocupacion_actual": occ_total, 
        "capacidad_motos": cap_motos,
        "ocupacion_motos": occ_motos,
        "capacidad_camionetas": cap_camionetas,
        "ocupacion_camionetas": occ_camionetas,
        "disponibilidad": cap_total - occ_total,
        "disponibilidad_motos": cap_motos - occ_motos,
        "disponibilidad_camionetas": cap_camionetas - occ_camionetas
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
    RATE_CLAVES = {"Auto": "precio_hora", "Moto": "precio_hora_moto", "Camioneta": "precio_hora_camioneta"}
    sucursales = {e.sucursal for e in entradas if e.sucursal}
    rate_cond = models.Settings.clave.in_(list(RATE_CLAVES.values()))
    if sucursales:
        rate_cond = and_(
            models.Settings.clave.in_(list(RATE_CLAVES.values())),
            or_(models.Settings.sucursal.in_(sucursales), models.Settings.sucursal.is_(None))
        )
    else:
        rate_cond = and_(models.Settings.clave.in_(list(RATE_CLAVES.values())), models.Settings.sucursal.is_(None))
    rate_map = {
        (r.clave, r.sucursal): float(r.valor)
        for r in db.query(models.Settings).filter(rate_cond).all()
    }

    def rate_for(suc, tipo):
        clave = RATE_CLAVES.get(tipo, "precio_hora")
        if (clave, suc) in rate_map:
            return rate_map[(clave, suc)]
        if suc and (clave, None) in rate_map:
            return rate_map[(clave, None)]
        return settings.DEFAULT_HOURLY_RATE

    def calc_debt(entry_time_str, suc, tipo):
        delta = TimeService.now() - datetime.datetime.fromisoformat(entry_time_str)
        bloques = max(1, math.ceil(delta.total_seconds() / 3600))
        return float(bloques * rate_for(suc, tipo))

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
