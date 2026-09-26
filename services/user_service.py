from sqlalchemy.orm import Session
from fastapi import HTTPException
import models
import schemas
from core.security import get_password_hash
from core.logger import get_logger
from core.normalize import normalize_user_name as normalize_name, normalize_dni, normalize_plate, format_plate
from models.enums import UserRole
from repositories.user_repository import UserRepository
from repositories.vehicle_repository import VehicleRepository
from repositories.access_log_repository import AccessRepository
from repositories.reservation_repository import ReservationRepository

logger = get_logger("UserService")

class UserService:
    @staticmethod
    def get_by_email(db: Session, email: str) -> models.User:
        """BUSCA UN USUARIO POR CORREO USANDO EL REPOSITORIO."""
        return UserRepository.get_by_email(db, email)

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> models.User:
        """OBTIENE UN USUARIO POR SU ID USANDO EL REPOSITORIO."""
        return UserRepository.get_by_id(db, user_id)

    @staticmethod
    def create_user(db: Session, user_data: schemas.UserCreate, rol: UserRole = UserRole.USER, sucursal: str = None) -> models.User:
        """CREA UN NUEVO USUARIO EN EL SISTEMA."""
        existing = UserRepository.get_by_email(db, user_data.email)
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
        user = UserRepository.get_active_by_id(db, user_id)
        if not user:
            return None

        if user_data.email:
            new_email = user_data.email.lower().strip()
            if new_email != user.email:
                existing_email = UserRepository.get_other_by_email(db, new_email, user_id)
                if existing_email:
                    raise HTTPException(status_code=400, detail="El correo ya está registrado por otro usuario.")
                user.email = new_email

        if user_data.dni:
            new_dni = normalize_dni(user_data.dni)
            if new_dni != user.dni:
                existing_dni = UserRepository.get_other_by_dni(db, new_dni, user_id)
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

        user = UserRepository.get_active_by_id(db, user_id)
        if not user:
            return False

        # 1. VALIDAR SI TIENE RESERVAS ACTIVAS O PENDIENTES
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        active_res = ReservationRepository.get_active_by_user(db, user_id, now_str)
        if active_res:
            raise HTTPException(status_code=400, detail="No se puede eliminar un usuario con reservas activas o pendientes.")

        # 2. VALIDAR SI ALGUNO DE SUS VEHICULOS ESTA DENTRO DEL ESTACIONAMIENTO
        patentes_usuario = VehicleRepository.get_plates_by_user(db, user_id)
        pats = [v.upper().replace(' ', '') for v in patentes_usuario if v]
        if user.patente and user.patente.upper().replace(' ', '') not in pats:
            pats.append(user.patente.upper().replace(' ', ''))

        for p in pats:
            entry = UserService._last_entry_active(db, p)
            if entry and not entry[1]:
                raise HTTPException(status_code=400, detail="No se puede eliminar un usuario con vehículos físicamente dentro del estacionamiento.")

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

    # --- HELPERS DE ESTADÍA ---

    @staticmethod
    def _last_entry_active(db: Session, patente_clean: str):
        """RETORNA (last_entry, subsequent_exit) SI HAY ESTADÍA ABIERTA, None CASO CONTRARIO."""
        last_entry = AccessRepository.get_last_entry_clean(db, patente_clean)
        if not last_entry:
            return None
        subsequent_exit = AccessRepository.get_exit_after_clean(db, patente_clean, last_entry.id)
        return (last_entry, subsequent_exit)

    # --- VEHÍCULOS ---

    @staticmethod
    def list_vehicles(db: Session, user_id: int):
        """LISTA TODOS LOS VEHÍCULOS VINCULADOS A LA CUENTA."""
        return VehicleRepository.get_by_user(db, user_id)

    @staticmethod
    def add_vehicle(db: Session, user, patente, marca_modelo, tipo="Auto"):
        """VINCULA UN NUEVO VEHÍCULO VALIDANDO BLOQUEO, TIPO Y FORMATO DE PATENTE."""
        import re

        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")

        if tipo not in ["Auto", "Moto", "Camioneta"]:
            raise HTTPException(status_code=400, detail="Tipo de vehículo inválido. Use 'Auto', 'Moto' o 'Camioneta'.")

        p_clean = normalize_plate(patente)
        old_format   = re.match(r'^[A-Z]{3}[0-9]{3}$', p_clean)
        new_format   = re.match(r'^[A-Z]{2}[0-9]{3}[A-Z]{2}$', p_clean)
        moto_format  = re.match(r'^[0-9]{3}[A-Z]{3}$', p_clean) or re.match(r'^[A-Z]{1}[0-9]{3}[A-Z]{3}$', p_clean)
        if not old_format and not new_format and not moto_format:
            raise HTTPException(status_code=400, detail="Formato de patente inválido.")

        existing = VehicleRepository.get_by_normalized_patente(db, p_clean)
        if existing:
            raise HTTPException(status_code=400, detail="Esta patente ya se encuentra registrada en el sistema")

        new_vehicle = models.Vehicle(
            user_id=user.id,
            patente=format_plate(patente),
            marca_modelo=normalize_name(marca_modelo),
            tipo=tipo
        )
        db.add(new_vehicle)
        db.commit()

        try:
            from services.user_notification_service import UserNotificationService
            UserNotificationService.create_notification(
                db, user.id,
                tipo=models.NotificationType.VEHICLE_REGISTERED,
                titulo="Vehículo registrado",
                mensaje=f"Se vinculó exitosamente el vehículo {new_vehicle.marca_modelo} ({new_vehicle.patente}) a tu flota."
            )
        except Exception:
            logger.warning(f"[USERS] Error notificando alta de vehículo {new_vehicle.patente}", exc_info=True)

        return {"status": "ok"}

    @staticmethod
    def set_favorite_vehicle(db: Session, user, patente):
        """MARCA UN VEHÍCULO COMO FAVORITO (TOGGLE: SI YA ESTÁ MARCADO LO DESMARCA)."""
        p_clean = normalize_plate(patente)

        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")

        vehicle = VehicleRepository.get_by_user_and_normalized_patente(db, user.id, p_clean)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado en su flota")

        if vehicle.is_favorite:
            vehicle.is_favorite = False
        else:
            VehicleRepository.unset_favorite_for_user(db, user.id)
            vehicle.is_favorite = True

        db.commit()
        return {"status": "ok", "patente": vehicle.patente, "is_favorite": vehicle.is_favorite}

    @staticmethod
    def delete_vehicle(db: Session, user, patente):
        """DESVINCULA UN VEHÍCULO VALIDANDO RESERVAS, ESTADÍAS Y DEUDAS."""
        import datetime
        p_clean = normalize_plate(patente)

        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")

        vehicle = VehicleRepository.get_by_user_and_normalized_patente(db, user.id, p_clean)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado en su flota")

        # 1. VALIDAR RESERVAS ACTIVAS O PENDIENTES
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        active_res = ReservationRepository.get_active_by_clean_patente(db, p_clean, now_str)
        if active_res:
            raise HTTPException(status_code=400, detail="No se puede eliminar un vehículo que posee reservas activas o pendientes.")

        # 2. VALIDAR SI EL VEHÍCULO SE ENCUENTRA FÍSICAMENTE DENTRO DEL ESTACIONAMIENTO
        entry = UserService._last_entry_active(db, p_clean)
        if entry:
            last_entry, subsequent_exit = entry
            if not subsequent_exit:
                raise HTTPException(status_code=400, detail="No se puede eliminar un vehículo que se encuentra físicamente ingresado en el estacionamiento.")
            # 3. VALIDAR DEUDAS / ESTADÍAS IMPAGAS PENDIENTES
            if not last_entry.pago_confirmado:
                raise HTTPException(status_code=400, detail="No se puede eliminar un vehículo con deudas o estadías impagas pendientes.")

        # REASIGNAR FAVORITO O PATENTE PRINCIPAL SI CORRESPONDE
        other = VehicleRepository.get_other_by_user(db, user.id, vehicle.id)
        if vehicle.is_favorite and other:
            other.is_favorite = True

        if user.patente and normalize_plate(user.patente) == p_clean:
            user.patente = other.patente if other else None

        patente_borrada = vehicle.patente
        db.delete(vehicle)
        db.commit()

        try:
            from services.user_notification_service import UserNotificationService
            UserNotificationService.create_notification(
                db, user.id,
                tipo=models.NotificationType.VEHICLE_REMOVED,
                titulo="Vehículo desvinculado",
                mensaje=f"Se eliminó el vehículo con patente {patente_borrada} de tu flota."
            )
        except Exception:
            logger.warning(f"[USERS] Error notificando baja de vehículo {patente_borrada}", exc_info=True)

        return {"status": "ok"}
