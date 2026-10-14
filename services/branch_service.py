import os
import subprocess
from fastapi import HTTPException
from sqlalchemy.orm import Session
import models
from services.billing_service import BillingService
from models.enums import VehicleType
from core.logger import get_logger
from repositories.branch_repository import BranchRepository
from repositories.settings_repository import SettingsRepository
from repositories.user_repository import UserRepository

logger = get_logger("BranchService")

class BranchService:
    @staticmethod
    def get_branch_info_str(db: Session, sucursal_nombre: str) -> str:
        """OBTIENE EL TEXTO CON LA DIRECCIÓN Y HORARIO DE LA SUCURSAL."""
        if not sucursal_nombre:
            return "Dirección no disponible"

        branch = BranchRepository.get_by_name(db, sucursal_nombre)
        if not branch:
            branch = BranchRepository.get_by_name_like(db, sucursal_nombre)
        if not branch:
            all_b = BranchRepository.get_all(db)
            branch = next((b for b in all_b if b.nombre.lower() in sucursal_nombre.lower() or sucursal_nombre.lower() in b.nombre.lower()), None)

        if branch and branch.direccion and branch.direccion.strip():
            horario_str = "Abierto 24hs" if branch.is_24h else (branch.horario or "Horario no especificado")
            return f"{branch.direccion.strip()}. {horario_str}."

        return "Dirección no disponible"

    @staticmethod
    def get_branch_tariffs(db: Session, branch_name: str) -> dict:
        """TARIFAS DE LA SUCURSAL POR MODALIDAD Y TIPO DE VEHICULO."""
        buckets = {
            "": VehicleType.AUTO,
            "_moto": VehicleType.MOTO,
            "_camioneta": VehicleType.CAMIONETA,
        }
        tipos = {"hora": "hora", "dia": "dia", "semana": "semana", "quincena": "quincena", "mes": "mes"}
        out = {}
        for tipo_key, estadia in tipos.items():
            for suffix, vtype in buckets.items():
                out[f"tarifa_{tipo_key}{suffix}"] = BillingService.get_rate(
                    db, estadia, sucursal=branch_name, tipo_vehiculo=vtype
                )
        return out

    @staticmethod
    def get_branch_capacity_summary(db: Session, branch: models.ParkingBranch) -> dict:
        """CALCULA LOS TOTALES DE CAPACIDAD Y OCUPACION (PB + PISOS)."""
        pb_settings = BranchRepository.get_aforo_by_branch_id(db, branch.id)
        
        cap_autos_pb = pb_settings.capacidad_total if pb_settings else 20
        cap_motos_pb = pb_settings.capacidad_motos if pb_settings else 10
        cap_camionetas_pb = getattr(pb_settings, 'capacidad_camionetas', 5) if pb_settings else 5
        cap_res_autos_pb = getattr(pb_settings, 'capacidad_reservas_autos', 5) if pb_settings else 5
        cap_res_motos_pb = getattr(pb_settings, 'capacidad_reservas_motos', 3) if pb_settings else 3
        cap_res_camionetas_pb = getattr(pb_settings, 'capacidad_reservas_camionetas', 2) if pb_settings else 2
        cap_reservas_pb = getattr(pb_settings, 'capacidad_reservas', cap_res_autos_pb + cap_res_motos_pb + cap_res_camionetas_pb) if pb_settings else 10

        occ_autos_pb = pb_settings.ocupacion_actual if pb_settings else 0
        occ_motos_pb = pb_settings.ocupacion_motos if pb_settings else 0
        occ_camionetas_pb = getattr(pb_settings, 'ocupacion_camionetas', 0) if pb_settings else 0
        occ_res_autos_pb = getattr(pb_settings, 'ocupacion_reservas_autos', 0) if pb_settings else 0
        occ_res_motos_pb = getattr(pb_settings, 'ocupacion_reservas_motos', 0) if pb_settings else 0
        occ_res_camionetas_pb = getattr(pb_settings, 'ocupacion_reservas_camionetas', 0) if pb_settings else 0
        occ_reservas_pb = getattr(pb_settings, 'ocupacion_reservas', occ_res_autos_pb + occ_res_motos_pb + occ_res_camionetas_pb) if pb_settings else 0

        floors_cap_autos = sum(f.capacidad_total for f in branch.floors)
        floors_cap_motos = sum(f.capacidad_motos for f in branch.floors)
        floors_cap_camionetas = sum(getattr(f, 'capacidad_camionetas', 5) for f in branch.floors)
        floors_cap_res_autos = sum(getattr(f, 'capacidad_reservas_autos', 5) for f in branch.floors)
        floors_cap_res_motos = sum(getattr(f, 'capacidad_reservas_motos', 3) for f in branch.floors)
        floors_cap_res_camionetas = sum(getattr(f, 'capacidad_reservas_camionetas', 2) for f in branch.floors)
        floors_cap_reservas = sum(getattr(f, 'capacidad_reservas', 10) for f in branch.floors)

        floors_occ_autos = sum(f.ocupacion_actual for f in branch.floors)
        floors_occ_motos = sum(f.ocupacion_motos for f in branch.floors)
        floors_occ_camionetas = sum(getattr(f, 'ocupacion_camionetas', 0) for f in branch.floors)
        floors_occ_res_autos = sum(getattr(f, 'ocupacion_reservas_autos', 0) for f in branch.floors)
        floors_occ_res_motos = sum(getattr(f, 'ocupacion_reservas_motos', 0) for f in branch.floors)
        floors_occ_res_camionetas = sum(getattr(f, 'ocupacion_reservas_camionetas', 0) for f in branch.floors)
        floors_occ_reservas = sum(getattr(f, 'ocupacion_reservas', 0) for f in branch.floors)

        return {
            "capacidad_autos_total": cap_autos_pb + floors_cap_autos,
            "capacidad_motos_total": cap_motos_pb + floors_cap_motos,
            "capacidad_camionetas_total": cap_camionetas_pb + floors_cap_camionetas,
            "capacidad_reservas_autos_total": cap_res_autos_pb + floors_cap_res_autos,
            "capacidad_reservas_motos_total": cap_res_motos_pb + floors_cap_res_motos,
            "capacidad_reservas_camionetas_total": cap_res_camionetas_pb + floors_cap_res_camionetas,
            "capacidad_reservas_total": cap_reservas_pb + floors_cap_reservas,
            "ocupacion_autos_total": occ_autos_pb + floors_occ_autos,
            "ocupacion_motos_total": occ_motos_pb + floors_occ_motos,
            "ocupacion_camionetas_total": occ_camionetas_pb + floors_occ_camionetas,
            "ocupacion_reservas_autos_total": occ_res_autos_pb + floors_occ_res_autos,
            "ocupacion_reservas_motos_total": occ_res_motos_pb + floors_occ_res_motos,
            "ocupacion_reservas_camionetas_total": occ_res_camionetas_pb + floors_occ_res_camionetas,
            "ocupacion_reservas_total": occ_reservas_pb + floors_occ_reservas
        }

    @staticmethod
    def has_physical_occupancy(db: Session, branch: models.ParkingBranch) -> bool:
        """RETORNA TRUE SI HAY VEHICULOS ESTACIONADOS FISICAMENTE EN LA SUCURSAL (PB + PISOS)."""
        aforo = BranchRepository.get_aforo_by_branch_id(db, branch.id)
        if aforo and ((aforo.ocupacion_actual or 0) > 0 or (aforo.ocupacion_motos or 0) > 0 or (aforo.ocupacion_camionetas or 0) > 0 or (getattr(aforo, 'ocupacion_reservas', 0) or 0) > 0):
            return True
        if branch.floors:
            total_occ = sum((f.ocupacion_actual or 0) + (f.ocupacion_motos or 0) + (f.ocupacion_camionetas or 0) + (getattr(f, 'ocupacion_reservas', 0) or 0) for f in branch.floors)
            if total_occ > 0:
                return True
        return False

    @staticmethod
    def rename_branch(db: Session, branch: models.ParkingBranch, new_nombre: str) -> None:
        """RENOMBRA UNA SUCURSAL PROPAGANDO EL CAMBIO A TABLAS DEPENDIENTES Y REMAPEA CANALES ALPR."""
        from core.normalize import normalize_name as normalize_system_name

        old_nombre = branch.nombre
        if old_nombre == new_nombre:
            return

        existing = BranchRepository.get_other_by_name(db, new_nombre, branch.id, branch.organization_id)
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe una sucursal con ese nombre")

        old_prefix = normalize_system_name(old_nombre)
        new_prefix = normalize_system_name(new_nombre)

        # El nombre vive SOLO en parking_branches; las tablas dependientes referencian
        # por `sucursal_id` (no cambia), asi que basta con renombrar la sede.
        branch.nombre = new_nombre
        db.flush()

        # El gate_id/WS de cada cámara se compone con el prefijo normalizado del nombre
        # de sucursal. Si el prefijo cambia, remapear las claves legacy CAMERA_SOURCE_* y
        # detener los subprocesos ALPR del prefijo viejo para que espectador y proceso
        # converjan al mismo canal (si no, la cámara queda en negro).
        if old_prefix and old_prefix != new_prefix:
            source_rows = SettingsRepository.get_camera_sources_by_prefix(db, old_prefix)
            for row in source_rows:
                row.clave = row.clave.replace(f"CAMERA_SOURCE_{old_prefix}", f"CAMERA_SOURCE_{new_prefix}", 1)

            from routes.system.common import CAMERA_PROCESSES
            stale_gates = [g for g in list(CAMERA_PROCESSES.keys()) if g.startswith(f"{old_prefix}_")]
            for gate_id in stale_gates:
                proc = CAMERA_PROCESSES.get(gate_id)
                if proc and proc.poll() is None:
                    try:
                        if os.name == 'nt':
                            subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        else:
                            proc.terminate()
                    except Exception:
                        logger.warning("[BRANCH] Error deteniendo proceso de cámara", exc_info=True)
                CAMERA_PROCESSES.pop(gate_id, None)

    @staticmethod
    def list_branches_with_summary(db: Session, organization_id=None):
        """LISTA LAS SUCURSALES CON SU RESUMEN ADMINISTRATIVO (FILTRADAS POR ORGANIZACION)."""
        branches = BranchRepository.get_all(db, organization_id=organization_id)
        for b in branches:
            # ADMINISTRADOR
            admin_sede = UserRepository.get_local_admin_by_sucursal(db, b.nombre, b.organization_id)
            b.admin_name = f"{admin_sede.nombre} {admin_sede.apellido}" if admin_sede else "Sin asignar"

            # RESUMEN
            summary = BranchService.get_branch_capacity_summary(db, b)
            for key, val in summary.items():
                setattr(b, key, val)

            # TARIFAS
            tariffs = BranchService.get_branch_tariffs(db, b.nombre)
            for key, val in tariffs.items():
                setattr(b, key, val)
        return branches
