from sqlalchemy.orm import Session
import models
from services.billing_service import BillingService
from models.enums import VehicleType

class BranchService:
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
        pb_settings = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == branch.nombre).first()
        
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
    def list_branches_with_summary(db: Session):
        """LISTA TODAS LAS SUCURSALES CON SU RESUMEN ADMINISTRATIVO."""
        branches = db.query(models.ParkingBranch).all()
        for b in branches:
            # ADMINISTRADOR
            admin_sede = db.query(models.User).filter(
                models.User.sucursal == b.nombre,
                models.User.rol == "local_admin",
                models.User.is_deleted == False
            ).first()
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
