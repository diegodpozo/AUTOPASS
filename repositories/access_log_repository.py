from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

import models
from models.enums import AccessEventType

#--- REPOSITORIO DE LOGS DE ACCESO (INGRESOS/SALIDAS FISICAS) ---


class AccessRepository:
    @staticmethod
    def get_by_id(db: Session, log_id: int) -> models.AccessLog:
        """OBTIENE UN LOG DE ACCESO POR SU IDENTIFICADOR UNICO."""
        return db.query(models.AccessLog).filter(models.AccessLog.id == log_id).first()

    @staticmethod
    def get_last_by_patente_and_sucursal(db: Session, normalized_patente: str, sucursal: str) -> models.AccessLog:
        """ULTIMO EVENTO FISICO (CUALQUIER TIPO) DE UNA PATENTE NORMALIZADA EN UNA SUCURSAL."""
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
    def get_last_detected_by_patente_and_sucursal(db: Session, patente_detectada: str, sucursal: str) -> models.AccessLog:
        """ULTIMO EVENTO FISICO (CUALQUIER TIPO) DE UNA PATENTE DETECTADA EN UNA SUCURSAL."""
        return (
            db.query(models.AccessLog)
            .filter(
                models.AccessLog.patente_detectada == patente_detectada,
                models.AccessLog.sucursal == sucursal
            )
            .order_by(models.AccessLog.id.desc())
            .first()
        )

    @staticmethod
    def get_reserva_ids_with_entry(db: Session, reserva_ids) -> set:
        """IDS DE RESERVAS QUE TIENEN ALGUN INGRESO FISICO.

        Alternativa batch a un get_entry_for_reserva por fila (patron N+1
        eliminado en rutas A5): 1 query total en vez de 1 query por reserva.
        """
        if not reserva_ids:
            return set()
        rows = db.query(models.AccessLog.reserva_id).filter(
            models.AccessLog.reserva_id.in_(list(reserva_ids)),
            models.AccessLog.tipo_evento == AccessEventType.ENTRADA
        ).all()
        return {row[0] for row in rows}

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
    def get_last_entry_by_patente(db: Session, patente_detectada: str) -> models.AccessLog:
        """ULTIMO INGRESO FISICO (ENTRADA) DE UNA PATENTE DETECTADA, SIN FILTRO DE SUCURSAL."""
        return (
            db.query(models.AccessLog)
            .filter(
                models.AccessLog.patente_detectada == patente_detectada,
                models.AccessLog.tipo_evento == AccessEventType.ENTRADA
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

    @staticmethod
    def get_paid_logs_by_patentes(db: Session, patentes: list) -> list:
        """LOGS DE ACCESO PAGADOS (PAGO CONFIRMADO CON COSTO) DE UN CONJUNTO DE PATENTES, MAS RECIENTES PRIMERO."""
        return (
            db.query(models.AccessLog)
            .filter(
                models.AccessLog.patente_detectada.in_(patentes),
                models.AccessLog.pago_confirmado == True,
                models.AccessLog.costo_estadia > 0
            )
            .order_by(models.AccessLog.id.desc())
            .all()
        )

    @staticmethod
    def get_last_entries_by_patentes(db: Session, patentes: list) -> list:
        """ULTIMA ENTRADA DE CADA PATENTE DE LA LISTA EN UNA SOLA CONSULTA (SUBCONSULTA DE ID MAXIMO)."""
        subq = (
            db.query(
                models.AccessLog.patente_detectada,
                func.max(models.AccessLog.id).label("max_id")
            )
            .filter(
                models.AccessLog.patente_detectada.in_(patentes),
                models.AccessLog.tipo_evento == AccessEventType.ENTRADA
            )
            .group_by(models.AccessLog.patente_detectada)
            .subquery()
        )
        return db.query(models.AccessLog).join(subq, models.AccessLog.id == subq.c.max_id).all()

    @staticmethod
    def get_exit_times_by_patentes(db: Session, patentes: list) -> list:
        """PARES (PATENTE_DETECTADA, FECHA_HORA) DE TODAS LAS SALIDAS DE UN CONJUNTO DE PATENTES."""
        return (
            db.query(models.AccessLog.patente_detectada, models.AccessLog.fecha_hora)
            .filter(
                models.AccessLog.patente_detectada.in_(patentes),
                models.AccessLog.tipo_evento == AccessEventType.SALIDA
            )
            .all()
        )

    @staticmethod
    def get_current_entries(db: Session, sucursal: str = None) -> list:
        """ENTRADAS MAS RECIENTES POR PATENTE EN LA SEDE (O TODAS SI `sucursal` ES None),
        CON EL PISO CARGADO, ORDENADAS POR FECHA DESCENDENTE (SUBCONSULTA ID MAXIMO DE ENTRADA)."""
        subq = (
            db.query(
                models.AccessLog.patente_detectada,
                func.max(models.AccessLog.id).label("max_id")
            )
            .filter(models.AccessLog.tipo_evento == AccessEventType.ENTRADA)
        )
        if sucursal:
            subq = subq.filter(models.AccessLog.sucursal == sucursal)
        subq = subq.group_by(models.AccessLog.patente_detectada).subquery()

        return (
            db.query(models.AccessLog)
            .options(selectinload(models.AccessLog.floor))
            .join(subq, models.AccessLog.id == subq.c.max_id)
            .order_by(models.AccessLog.fecha_hora.desc())
            .all()
        )

    @staticmethod
    def get_exit_max_by_patente_sucursal(db: Session, patentes, sucursales) -> dict:
        """MAPA (patente_detectada, sucursal) -> id MAXIMO DE SALIDA PARA EXCLUIR ENTRADAS YA CERRADAS."""
        rows = (
            db.query(
                models.AccessLog.patente_detectada,
                models.AccessLog.sucursal,
                func.max(models.AccessLog.id).label("max_salida_id")
            )
            .filter(
                models.AccessLog.tipo_evento == AccessEventType.SALIDA,
                models.AccessLog.patente_detectada.in_(patentes),
                models.AccessLog.sucursal.in_(sucursales)
            )
            .group_by(models.AccessLog.patente_detectada, models.AccessLog.sucursal)
            .all()
        )
        return {(p, s): m for p, s, m in rows}

    @staticmethod
    def get_last_entry_clean(db: Session, patente_clean: str) -> models.AccessLog:
        """ULTIMO INGRESO FISICO DE UNA PATENTE COMPARADA SIN ESPACIOS NI MAYUSCULAS."""
        return (
            db.query(models.AccessLog)
            .filter(
                func.replace(func.upper(models.AccessLog.patente_detectada), ' ', '') == patente_clean,
                models.AccessLog.tipo_evento == AccessEventType.ENTRADA
            )
            .order_by(models.AccessLog.id.desc())
            .first()
        )

    @staticmethod
    def get_exit_after_clean(db: Session, patente_clean: str, after_id: int) -> models.AccessLog:
        """PRIMERA SALIDA FISICA DE UNA PATENTE (SIN ESPACIOS/MAYUSCULAS) POSTERIOR A UN EVENTO."""
        return (
            db.query(models.AccessLog)
            .filter(
                func.replace(func.upper(models.AccessLog.patente_detectada), ' ', '') == patente_clean,
                models.AccessLog.tipo_evento == AccessEventType.SALIDA,
                models.AccessLog.id > after_id
            )
            .first()
        )