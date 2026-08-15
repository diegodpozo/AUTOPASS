from sqlalchemy.orm import Session
from fastapi import HTTPException
import models
import schemas
from core.security import get_password_hash
from models.enums import UserRole

class UserService:
    @staticmethod
    def create_user(db: Session, user_data: schemas.UserCreate, rol: UserRole = UserRole.USER, sucursal: str = None) -> models.User:
        """CREA UN NUEVO USUARIO EN EL SISTEMA."""
        from routes.parking.utils import normalize_name, normalize_dni
        
        existing = db.query(models.User).filter(models.User.email == user_data.email.lower().strip()).first()
        if existing:
            raise HTTPException(status_code=400, detail="El correo ya está registrado")
        
        new_user = models.User(
            nombre=normalize_name(user_data.nombre),
            apellido=normalize_name(user_data.apellido),
            dni=normalize_dni(user_data.dni),
            telefono=user_data.telefono,
            email=user_data.email.lower().strip(),
            password_hash=get_password_hash(user_data.password),
            rol=rol,
            sucursal=sucursal
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def update_user(db: Session, user_id: int, user_data: schemas.UserAdminUpdate) -> models.User:
        """ACTUALIZA LOS DATOS DE UN USUARIO VALIDANDO UNICIDAD DE EMAIL Y DNI."""
        from routes.parking.utils import normalize_name, normalize_dni
        
        user = db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()
        if not user:
            return None

        if user_data.email:
            new_email = user_data.email.lower().strip()
            if new_email != user.email:
                existing_email = db.query(models.User).filter(
                    models.User.email == new_email,
                    models.User.id != user_id,
                    models.User.is_deleted == False
                ).first()
                if existing_email:
                    raise HTTPException(status_code=400, detail="El correo ya está registrado por otro usuario.")
                user.email = new_email

        if user_data.dni:
            new_dni = normalize_dni(user_data.dni)
            if new_dni != user.dni:
                existing_dni = db.query(models.User).filter(
                    models.User.dni == new_dni,
                    models.User.id != user_id,
                    models.User.is_deleted == False
                ).first()
                if existing_dni:
                    raise HTTPException(status_code=400, detail="El DNI ya está registrado por otro usuario.")
                user.dni = new_dni

        if user_data.nombre: user.nombre = normalize_name(user_data.nombre)
        if user_data.apellido: user.apellido = normalize_name(user_data.apellido)
        if user_data.telefono: user.telefono = user_data.telefono
        if user_data.sucursal is not None: user.sucursal = user_data.sucursal
        if user_data.rol: user.rol = user_data.rol

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int):
        """MARCA UN USUARIO COMO ELIMINADO Y ANONIMIZA SUS DATOS PERSONALES TRAS VALIDAR ESTADIAS Y RESERVAS."""
        import datetime
        from sqlalchemy import func

        user = db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()
        if not user:
            return False

        # 1. VALIDAR SI TIENE RESERVAS ACTIVAS O PENDIENTES
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        active_res = db.query(models.Reservation).filter(
            models.Reservation.user_id == user_id,
            models.Reservation.estado_reserva.in_(["Pendiente", "Activa"]),
            models.Reservation.fecha_fin >= now_str
        ).first()
        if active_res:
            raise HTTPException(
                status_code=400, 
                detail="No se puede eliminar un usuario con reservas activas o pendientes."
            )

        # 2. VALIDAR SI ALGUNO DE SUS VEHICULOS ESTA DENTRO DEL ESTACIONAMIENTO
        user_vehicles = db.query(models.Vehicle.patente).filter(models.Vehicle.user_id == user_id).all()
        pats = [v.patente.upper().replace(' ', '') for v in user_vehicles if v.patente]
        if user.patente and user.patente.upper().replace(' ', '') not in pats:
            pats.append(user.patente.upper().replace(' ', ''))

        for p in pats:
            last_entry = db.query(models.AccessLog).filter(
                func.replace(func.upper(models.AccessLog.patente_detectada), ' ', '') == p,
                models.AccessLog.tipo_evento == "ENTRADA"
            ).order_by(models.AccessLog.id.desc()).first()

            if last_entry:
                subsequent_exit = db.query(models.AccessLog).filter(
                    func.replace(func.upper(models.AccessLog.patente_detectada), ' ', '') == p,
                    models.AccessLog.tipo_evento == "SALIDA",
                    models.AccessLog.id > last_entry.id
                ).first()
                if not subsequent_exit:
                    raise HTTPException(
                        status_code=400, 
                        detail="No se puede eliminar un usuario con vehículos físicamente dentro del estacionamiento."
                    )

        anon_suffix = str(user_id)
        user.nombre = "Usuario"
        user.apellido = "Eliminado"
        user.dni = f"eliminado-{anon_suffix}"
        user.email = f"eliminado-{anon_suffix}@autopass.com"
        user.telefono = ""
        user.patente = None
        user.direccion = None
        user.is_deleted = True
        db.commit()
        return True
