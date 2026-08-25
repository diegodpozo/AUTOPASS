import os
import sys
import subprocess
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import models
import schemas
from core.database import get_db
from core.security import get_operational_user
from core.logger import get_logger
from routes.system.common import CAMERA_PROCESSES, CameraConfig, normalize_system_name

logger = get_logger("Cameras")

router = APIRouter()

@router.get("/camera-config/{gate_id}")
def get_camera_config(gate_id: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    gate_id = gate_id.upper()
    if staff.rol != "admin" and staff.sucursal:
        branch_prefix = gate_id.split('_')[0]
        if branch_prefix != normalize_system_name(staff.sucursal):
            raise HTTPException(status_code=403, detail="No tenés acceso a esta configuración")
             
    setting = db.query(models.Settings).filter(
        models.Settings.clave == f"CAMERA_SOURCE_{gate_id}"
    ).first()
    
    source = setting.valor_str if setting else "0"
    is_running = gate_id in CAMERA_PROCESSES and CAMERA_PROCESSES[gate_id].poll() is None
    
    return {"gate_id": gate_id, "source": source, "is_running": is_running}

@router.post("/camera-config")
def set_camera_config(config: CameraConfig, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    gate_id = config.gate_id.upper()
    if staff.rol != "admin":
        branch_prefix = normalize_system_name(staff.sucursal)
        if not gate_id.startswith(branch_prefix):
            raise HTTPException(status_code=403, detail="No tenés acceso a esta configuración")
            
    setting = db.query(models.Settings).filter(
        models.Settings.clave == f"CAMERA_SOURCE_{gate_id}"
    ).first()
    
    if not setting:
        setting = models.Settings(clave=f"CAMERA_SOURCE_{gate_id}", valor_str=config.source, sucursal=staff.sucursal)
        db.add(setting)
    else:
        setting.valor_str = config.source
    
    db.commit()
    return {"status": "ok", "message": "Configuración guardada"}

@router.post("/camera-service/{gate_id}/{action}")
def control_camera_service(gate_id: str, action: str, request: Request, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    gate_id = gate_id.upper()
    if staff.rol != "admin":
        branch_prefix = normalize_system_name(staff.sucursal)
        if not gate_id.startswith(branch_prefix):
            raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")

    if action == "start":
        if gate_id in CAMERA_PROCESSES and CAMERA_PROCESSES[gate_id].poll() is None:
            return {"status": "error", "message": "Ya está en ejecución"}
            
        setting = db.query(models.Settings).filter(models.Settings.clave == f"CAMERA_SOURCE_{gate_id}").first()
        source = setting.valor_str if setting else "0"
        base_url = str(request.base_url).rstrip("/")
        
        env = os.environ.copy()
        env["GATE_ID"] = gate_id
        env["VIDEO_SOURCE"] = source
        if "QR" in gate_id.upper():
            env["GATE_TYPE"] = "qr"
        else:
            env["GATE_TYPE"] = "entrada" if "ENTRADA" in gate_id else "salida"
        env["BACKEND_URL"] = base_url
        
        try:
            logger.info(f"Iniciando ALPR para {gate_id} con fuente: {source}")
            proc = subprocess.Popen(
                [sys.executable, "alpr_service.py"],
                env=env,
                stdout=None,
                stderr=None,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            CAMERA_PROCESSES[gate_id] = proc
            return {"status": "ok", "message": "Servicio iniciado"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    elif action == "stop":
        if gate_id not in CAMERA_PROCESSES:
            return {"status": "error", "message": "No está en ejecución"}
            
        proc = CAMERA_PROCESSES[gate_id]
        try:
            if proc.poll() is None:
                if os.name == 'nt':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc.terminate()
            if gate_id in CAMERA_PROCESSES:
                del CAMERA_PROCESSES[gate_id]
            return {"status": "ok", "message": "Servicio detenido"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    return {"status": "error", "message": "Acción no válida"}

@router.get("/cameras", response_model=List[schemas.CameraResponse])
def get_cameras(db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    query = db.query(models.ParkingCamera)
    if staff.rol != "admin" and staff.sucursal:
        query = query.filter(models.ParkingCamera.sucursal == staff.sucursal)
    cameras = query.all()
    res = []
    for c in cameras:
        norm_suc = normalize_system_name(c.sucursal) if c.sucursal else "GLOBAL"
        proc_id = f"{norm_suc}_{c.tipo}_{c.id}".upper()
        is_running = proc_id in CAMERA_PROCESSES and CAMERA_PROCESSES[proc_id].poll() is None
        res.append(schemas.CameraResponse(
            id=c.id,
            nombre=c.nombre,
            tipo=c.tipo,
            source=c.source,
            activa=c.activa,
            sucursal=c.sucursal,
            is_running=is_running
        ))
    return res

@router.post("/cameras", response_model=schemas.CameraResponse)
def create_camera(data: schemas.CameraCreate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    sucursal = staff.sucursal if staff.rol != "admin" else data.sucursal
    new_cam = models.ParkingCamera(
        nombre=data.nombre,
        tipo=data.tipo.upper(),
        source=data.source,
        sucursal=sucursal,
        activa=data.activa
    )
    db.add(new_cam)
    db.commit()
    db.refresh(new_cam)
    return schemas.CameraResponse(
        id=new_cam.id,
        nombre=new_cam.nombre,
        tipo=new_cam.tipo,
        source=new_cam.source,
        activa=new_cam.activa,
        sucursal=new_cam.sucursal,
        is_running=False
    )

@router.put("/cameras/{camera_id}", response_model=schemas.CameraResponse)
def update_camera(camera_id: int, data: schemas.CameraCreate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    camera = db.query(models.ParkingCamera).filter(models.ParkingCamera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    if staff.rol != "admin" and camera.sucursal != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")
    camera.nombre = data.nombre
    camera.tipo = data.tipo.upper()
    camera.source = data.source
    camera.activa = data.activa
    if staff.rol == "admin":
        camera.sucursal = data.sucursal
    db.commit()
    db.refresh(camera)
    
    norm_suc = normalize_system_name(camera.sucursal) if camera.sucursal else "GLOBAL"
    proc_id = f"{norm_suc}_{camera.tipo}_{camera.id}".upper()
    is_running = proc_id in CAMERA_PROCESSES and CAMERA_PROCESSES[proc_id].poll() is None
    
    return schemas.CameraResponse(
        id=camera.id,
        nombre=camera.nombre,
        tipo=camera.tipo,
        source=camera.source,
        activa=camera.activa,
        sucursal=camera.sucursal,
        is_running=is_running
    )

@router.delete("/cameras/{camera_id}")
def delete_camera(camera_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    camera = db.query(models.ParkingCamera).filter(models.ParkingCamera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    if staff.rol != "admin" and camera.sucursal != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")
        
    norm_suc = normalize_system_name(camera.sucursal) if camera.sucursal else "GLOBAL"
    proc_id = f"{norm_suc}_{camera.tipo}_{camera.id}".upper()
    if proc_id in CAMERA_PROCESSES:
        proc = CAMERA_PROCESSES[proc_id]
        try:
            if proc.poll() is None:
                if os.name == 'nt':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc.terminate()
        except Exception:
            pass
        del CAMERA_PROCESSES[proc_id]
        
    db.delete(camera)
    db.commit()
    return {"status": "ok", "message": "Cámara eliminada"}

@router.post("/cameras/{camera_id}/control/{action}")
def control_dynamic_camera_service(camera_id: int, action: str, request: Request, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    camera = db.query(models.ParkingCamera).filter(models.ParkingCamera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    if staff.rol != "admin" and camera.sucursal != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")
        
    norm_suc = normalize_system_name(camera.sucursal) if camera.sucursal else "GLOBAL"
    proc_id = f"{norm_suc}_{camera.tipo}_{camera.id}".upper()
    
    if action == "start":
        if proc_id in CAMERA_PROCESSES and CAMERA_PROCESSES[proc_id].poll() is None:
            return {"status": "error", "message": "Ya está en ejecución"}
            
        base_url = str(request.base_url).rstrip("/")
        env = os.environ.copy()
        env["GATE_ID"] = proc_id
        env["VIDEO_SOURCE"] = camera.source
        gt = camera.tipo.lower()
        if "qr" in gt:
            env["GATE_TYPE"] = "qr"
        elif "egreso" in gt or "salida" in gt:
            env["GATE_TYPE"] = "salida"
        elif "patente" in gt or "entrada" in gt:
            env["GATE_TYPE"] = "entrada"
        else:
            env["GATE_TYPE"] = gt
        env["BACKEND_URL"] = base_url
        
        try:
            logger.info(f"Iniciando ALPR para {camera.nombre} ({proc_id}) con fuente: {camera.source}")
            proc = subprocess.Popen(
                [sys.executable, "alpr_service.py"],
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            CAMERA_PROCESSES[proc_id] = proc
            return {"status": "ok", "message": f"Servicio para {camera.nombre} iniciado"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    elif action == "stop":
        if proc_id not in CAMERA_PROCESSES:
            return {"status": "error", "message": "No está en ejecución"}
            
        proc = CAMERA_PROCESSES[proc_id]
        try:
            if proc.poll() is None:
                if os.name == 'nt':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc.terminate()
            if proc_id in CAMERA_PROCESSES:
                del CAMERA_PROCESSES[proc_id]
            return {"status": "ok", "message": f"Servicio para {camera.nombre} detenido"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    return {"status": "error", "message": "Acción no válida"}
