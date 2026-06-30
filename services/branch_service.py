from sqlalchemy.orm import Session
import models

class BranchService:
    @staticmethod
    def get_branch_capacity_summary(db: Session, branch: models.ParkingBranch) -> dict:
        """CALCULA LOS TOTALES DE CAPACIDAD Y OCUPACION (PB + PISOS)."""
        pb_settings = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == branch.nombre).first()
        
        cap_autos_pb = pb_settings.capacidad_total if pb_settings else 20
        cap_motos_pb = pb_settings.capacidad_motos if pb_settings else 10
        cap_camionetas_pb = getattr(pb_settings, 'capacidad_camionetas', 5) if pb_settings else 5
        occ_autos_pb = pb_settings.ocupacion_actual if pb_settings else 0
        occ_motos_pb = pb_settings.ocupacion_motos if pb_settings else 0
        occ_camionetas_pb = getattr(pb_settings, 'ocupacion_camionetas', 0) if pb_settings else 0

        floors_cap_autos = sum(f.capacidad_total for f in branch.floors)
        floors_cap_motos = sum(f.capacidad_motos for f in branch.floors)
        floors_cap_camionetas = sum(f.capacidad_camionetas for f in branch.floors)
        floors_occ_autos = sum(f.ocupacion_actual for f in branch.floors)
        floors_occ_motos = sum(f.ocupacion_motos for f in branch.floors)
        floors_occ_camionetas = sum(f.ocupacion_camionetas for f in branch.floors)

        return {
            "capacidad_autos_total": cap_autos_pb + floors_cap_autos,
            "capacidad_motos_total": cap_motos_pb + floors_cap_motos,
            "capacidad_camionetas_total": cap_camionetas_pb + floors_cap_camionetas,
            "ocupacion_autos_total": occ_autos_pb + floors_occ_autos,
            "ocupacion_motos_total": occ_motos_pb + floors_occ_motos,
            "ocupacion_camionetas_total": occ_camionetas_pb + floors_occ_camionetas
        }

    @staticmethod
    def list_branches_with_summary(db: Session):
        """LISTA TODAS LAS SUCURSALES CON SU RESUMEN ADMINISTRATIVO."""
        branches = db.query(models.ParkingBranch).all()
        for b in branches:
            # ADMINISTRADOR
            admin_sede = db.query(models.User).filter(
                models.User.sucursal == b.nombre,
                models.User.rol == "local_admin"
            ).first()
            b.admin_name = f"{admin_sede.nombre} {admin_sede.apellido}" if admin_sede else "Sin asignar"

            # RESUMEN
            summary = BranchService.get_branch_capacity_summary(db, b)
            for key, val in summary.items():
                setattr(b, key, val)
        return branches
