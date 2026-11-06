from sqlalchemy import Numeric, bindparam, inspect, text
from sqlalchemy.orm import Session
import models
from models.types import to_money
from models.enums import UserRole
from repositories.scoping import scope_by_organization

#--- REPOSITORIO DE USUARIOS (ACCESO UN DATOS) ---

# --- ARITMETICA ATOMICA DE LA CUENTA (FASE 1: SALDO Y PUNTOS) ------------------
# El saldo y los puntos se ajustan SIEMPRE con UN solo UPDATE en la base, nunca
# leyendo en Python, sumando y volviendo a escribir. Dos requests simultaneos que
# hagan "leer -> sumar -> escribir" se pisan: los dos leen el mismo valor viejo y
# el ultimo commit borra el ajuste del otro (lost update), asi que se cobra de
# menos o se acreditan puntos de mas (carrera R3 del informe de concurrencia).
#
# Cada sentencia devuelve el valor NUEVO ya persistido con RETURNING. Las
# variantes con condicion (`AND saldo >= :monto`) devuelven None cuando no alcanza,
# lo que reemplaza el "chequear y despues descontar" (check-then-act) por UNA sola
# operacion indivisible que no necesita lock.
#
# OJO: ninguna de estas funciones hace commit: el commit lo decide el flujo de
# negocio, que suele estar dentro de una seccion critica de `bloqueo_transaccional`
# (Fase 2). Agregar un punto de escritura nuevo = usar uno de estos helpers.
_SQL_SUMAR_SALDO = (
    "UPDATE users SET saldo = COALESCE(saldo, 0) + :monto "
    "WHERE id = :uid RETURNING saldo"
)
_SQL_DESCONTAR_SALDO = (
    "UPDATE users SET saldo = COALESCE(saldo, 0) - :monto "
    "WHERE id = :uid AND COALESCE(saldo, 0) >= :monto RETURNING saldo"
)
_SQL_FIJAR_SALDO = (
    "UPDATE users SET saldo = :monto WHERE id = :uid RETURNING saldo"
)
_SQL_SUMAR_PUNTOS = (
    "UPDATE users SET puntos_acumulados = COALESCE(puntos_acumulados, 0) + :cantidad "
    "WHERE id = :uid RETURNING puntos_acumulados"
)
_SQL_CANJEAR_PUNTOS = (
    "UPDATE users SET puntos_acumulados = COALESCE(puntos_acumulados, 0) - :costo "
    "WHERE id = :uid AND COALESCE(puntos_acumulados, 0) >= :costo "
    "RETURNING puntos_acumulados"
)
# Equivale al viejo `max(0, puntos - cantidad)`: nunca deja puntos negativos.
_SQL_DESCONTAR_PUNTOS_TOPE_CERO = (
    "UPDATE users SET puntos_acumulados = CASE "
    "WHEN COALESCE(puntos_acumulados, 0) < :cantidad THEN 0 "
    "ELSE COALESCE(puntos_acumulados, 0) - :cantidad END "
    "WHERE id = :uid RETURNING puntos_acumulados"
)


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> models.User:
        """OBTIENE UN USUARIO POR SU IDENTIFICADOR UNICO."""
        return db.query(models.User).filter(models.User.id == user_id).first()

    @staticmethod
    def get_active_by_id(db: Session, user_id: int) -> models.User:
        """OBTIENE UN USUARIO NO ELIMINADO POR SU IDENTIFICADOR UNICO."""
        return db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()

    @staticmethod
    def get_all_active(db: Session, organization_id=None) -> list:
        """OBTIENE LOS USUARIOS NO ELIMINADOS (FILTRADOS POR ORGANIZACION SI SE INDICA)."""
        query = db.query(models.User).filter(models.User.is_deleted == False)
        return scope_by_organization(query, models.User, organization_id).all()

    @staticmethod
    def get_by_email(db: Session, email: str) -> models.User:
        """BUSCA UN USUARIO POR SU DIRECCION DE CORREO ELECTRONICO."""
        return db.query(models.User).filter(models.User.email == email.lower().strip()).first()

    @staticmethod
    def get_active_by_email(db: Session, email: str) -> models.User:
        """BUSCA UN USUARIO NO ELIMINADO POR SU DIRECCION DE CORREO ELECTRONICO."""
        return db.query(models.User).filter(
            models.User.email == email.lower().strip(), models.User.is_deleted == False
        ).first()

    @staticmethod
    def get_active_by_dni(db: Session, dni: str) -> models.User:
        """BUSCA UN USUARIO NO ELIMINADO POR SU DNI."""
        return db.query(models.User).filter(
            models.User.dni == dni, models.User.is_deleted == False
        ).first()

    @staticmethod
    def get_other_by_email(db: Session, email: str, user_id: int) -> models.User:
        """BUSCA UN USUARIO NO ELIMINADO CON ESE CORREO, DISTINTO AL INDICADO."""
        return db.query(models.User).filter(
            models.User.email == email.lower().strip(),
            models.User.id != user_id,
            models.User.is_deleted == False
        ).first()

    @staticmethod
    def get_other_by_dni(db: Session, dni: str, user_id: int) -> models.User:
        """BUSCA UN USUARIO NO ELIMINADO CON ESE DNI, DISTINTO AL INDICADO."""
        return db.query(models.User).filter(
            models.User.dni == dni,
            models.User.id != user_id,
            models.User.is_deleted == False
        ).first()

    @staticmethod
    def get_staff(db: Session) -> list:
        """OBTIENE LOS USUARIOS DE STAFF (ADMIN Y LOCAL_ADMIN) NO ELIMINADOS."""
        return db.query(models.User).filter(
            models.User.rol.in_([UserRole.ADMIN, UserRole.LOCAL_ADMIN]),
            models.User.is_deleted == False
        ).all()

    @staticmethod
    def get_by_ids(db: Session, user_ids) -> list:
        """OBTIENE LOS USUARIOS CUYOS IDENTIFICADORES ESTAN EN LA LISTA."""
        if not user_ids:
            return []
        return db.query(models.User).filter(models.User.id.in_(user_ids)).all()

    @staticmethod
    def get_local_admin_by_sucursal(db: Session, sucursal: str, organization_id=None) -> models.User:
        """OBTIENE EL LOCAL_ADMIN NO ELIMINADO ASIGNADO A UNA SUCURSAL (OPCIONALMENTE POR ORGANIZACION)."""
        query = db.query(models.User).filter(
            models.User.sucursal == sucursal,
            models.User.rol == UserRole.LOCAL_ADMIN,
            models.User.is_deleted == False
        )
        return scope_by_organization(query, models.User, organization_id).first()

    # --- AJUSTES ATOMICOS DE LA CUENTA (FASE 1) --------------------------------

    @staticmethod
    def _ajuste_atomico(db: Session, user: models.User, sentencia: str, columna: str, parametros: dict):
        """EJECUTA EL UPDATE ATOMICO DE UNA COLUMNA DE LA CUENTA DE UN USUARIO.

        Devuelve el valor NUEVO ya persistido, o None si la sentencia no afecto
        ninguna fila (por ejemplo: saldo o puntos insuficientes). Sincroniza el
        objeto para que la proxima lectura (respuesta HTTP, mail, notificacion,
        test) vea el valor real de la base y no el viejo.
        NO hace commit."""
        statement = text(sentencia)
        if "monto" in parametros:
            statement = statement.bindparams(bindparam("monto", type_=Numeric(12, 2)))
            parametros = {**parametros, "monto": to_money(parametros["monto"])}
        fila = db.execute(statement, {"uid": user.id, **parametros}).fetchone()
        if fila is None:
            return None
        valor_nuevo = to_money(fila[0]) if columna == "saldo" else fila[0]
        if inspect(user, raiseerr=False) is None:
            # Objeto plano (no es una fila: mocks de tests) -> se copia el valor devuelto.
            setattr(user, columna, valor_nuevo)
        else:
            # Fila real -> se expira la columna: la re-lee de la base en el proximo
            # acceso (mas barato que volver a escribir el mismo valor).
            db.expire(user, [columna])
        return valor_nuevo

    @staticmethod
    def sumar_saldo(db: Session, user: models.User, monto):
        """ACREDITA `monto` AL SALDO (UPDATE atomico). Devuelve el saldo nuevo."""
        return UserRepository._ajuste_atomico(
            db, user, _SQL_SUMAR_SALDO, "saldo", {"monto": monto}
        )

    @staticmethod
    def descontar_saldo(db: Session, user: models.User, monto):
        """DESCUENTA `monto` SOLO SI EL SALDO ALCANZA, en la misma sentencia.

        Devuelve el saldo nuevo, o None si no alcanzaba (y entonces NO descontó).
        Reemplaza el clasico `if user.saldo < monto: raise` + `user.saldo -= monto`."""
        return UserRepository._ajuste_atomico(
            db, user, _SQL_DESCONTAR_SALDO, "saldo", {"monto": monto}
        )

    @staticmethod
    def fijar_saldo(db: Session, user: models.User, monto):
        """FIJA EL SALDO A UN VALOR ABSOLUTO (ajuste del admin). Devuelve el saldo nuevo."""
        return UserRepository._ajuste_atomico(
            db, user, _SQL_FIJAR_SALDO, "saldo", {"monto": monto}
        )

    @staticmethod
    def sumar_puntos(db: Session, user: models.User, cantidad: int):
        """ACREDITA `cantidad` PUNTOS (UPDATE atomico). Devuelve los puntos nuevos."""
        return UserRepository._ajuste_atomico(
            db, user, _SQL_SUMAR_PUNTOS, "puntos_acumulados", {"cantidad": cantidad}
        )

    @staticmethod
    def canjear_puntos(db: Session, user: models.User, costo: int):
        """DESCUENTA `costo` PUNTOS SOLO SI ALCANZAN. None = puntos insuficientes."""
        return UserRepository._ajuste_atomico(
            db, user, _SQL_CANJEAR_PUNTOS, "puntos_acumulados", {"costo": costo}
        )

    @staticmethod
    def descontar_puntos_tope_cero(db: Session, user: models.User, cantidad: int):
        """DESCUENTA PUNTOS SIN BAJAR DE CERO (`max(0, puntos - cantidad)`). Devuelve los nuevos."""
        return UserRepository._ajuste_atomico(
            db, user, _SQL_DESCONTAR_PUNTOS_TOPE_CERO, "puntos_acumulados",
            {"cantidad": cantidad}
        )

    @staticmethod
    def update_balance(db: Session, user: models.User, amount):
        """ACTUALIZA EL SALDO DE LA CUENTA DE UN USUARIO (atomico) y commitea."""
        saldo = UserRepository.sumar_saldo(db, user, amount)
        db.commit()
        return saldo

    @staticmethod
    def add_points(db: Session, user: models.User, points: int):
        """INCREMENTA EL PUNTAJE ACUMULADO DE FIDELIZACION (atomico) y commitea."""
        puntos = UserRepository.sumar_puntos(db, user, points)
        db.commit()
        return puntos
