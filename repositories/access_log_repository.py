from sqlalchemy import func
from sqlalchemy.orm import Session

import models
from models.enums import AccessEventType

#--- REPOSITORIO DE LOGS DE ACCESO (INGRESOS/SALIDAS FISICAS) ---


class AccessRepository:
    @staticmethod
    def get_last_by_patente_and_sucursal(db: Session, normalized_patente: str, sucursal: str) -> models.AccessLog:
        """ULTIMO EVENTO FISICO (CUALQUIER TIPO) DE UNA PATENTE EN UNA SUCURSAL."""
        return (
            db.query(models.AccessLog)
            .filter(
                models.AccessLog.normalized_patente == normalized_patente,
                models.AccessLog.sucursal == sucursal
            )
            .order_by(models.AccessLog.id.desc())
            .first()
        )

    @staticmethod
    def get_entry_for_reserva(db: Session, reserva_id: int) -> models.AccessLog:
        """OBTIENE EL PRIMER REGISTRO DE INGRESO VINCULADO A UNA RESERVA."""
        return (
            db.query(models.AccessLog)
            .filter(
                models.AccessLog.reserva_id == reserva_id,
                models.AccessLog.tipo_evento == AccessEventType.ENTRADA
            )
            .first()
        )

    @staticmethod
    def get_en_predio_ids(db: Session, reserva_ids) -> set:
        """IDS DE RESERVAS CUYO ULTIMO EVENTO FISICO FUE UN INGRESO (VEHICULO DENTRO DEL PREDIO)."""
        if not reserva_ids:
            return set()
        latest = (
            db.query(models.AccessLog.reserva_id, func.max(models.AccessLog.id).label('max_id'))
            .filter(models.AccessLog.reserva_id.in_(list(reserva_ids)))
            .group_by(models.AccessLog.reserva_id)
            .subquery()
        )
        rows = (
            db.query(latest.c.reserva_id)
            .join(models.AccessLog, models.AccessLog.id == latest.c.max_id)
            .filter(models.AccessLog.tipo_evento == AccessEventType.ENTRADA)
            .all()
        )
        return {row[0] for row in rows}

    @staticmethod
    def get_last_entry(db: Session, normalized_patente: str, sucursal: str) -> models.AccessLog:
        """ULTIMO INGRESO FISICO DE UNA PATENTE NORMALIZADA EN UNA SUCURSAL."""
        return (
            db.query(models.AccessLog)
            .filter(
                models.AccessLog.normalized_patente == normalized_patente,
                models.AccessLog.tipo_evento == AccessEventType.ENTRADA,
                models.AccessLog.sucursal == sucursal
            )
            .order_by(models.AccessLog.id.desc())
            .first()
        )

    @staticmethod
    def get_exit_after(db: Session, patente_detectada: str, after_id: int, sucursal: str) -> models.AccessLog:
        """PRIMERA SALIDA DE UNA PATENTE DETECTADA POSTERIOR A UN EVENTO EN LA MISMA SUCURSAL."""
        return (
            db.query(models.AccessLog)
            .filter(
                models.AccessLog.patente_detectada == patente_detectada,
                models.AccessLog.tipo_evento == AccessEventType.SALIDA,
                models.AccessLog.id > after_id,
                models.AccessLog.sucursal == sucursal
            )
            .first()
        )