from sqlalchemy import or_, false
from sqlalchemy.orm import Session

import models
from repositories.branch_repository import BranchRepository

#--- REPOSITORIO DE CONFIGURACIONES GLOBALES (PRECIOS, PARAMETROS) ---


class SettingsRepository:
    @staticmethod
    def _sucursal_predicate(db: Session, sucursal: str, organization_id=None):
        """PREDICADO SQL DE UN SETTING POR `sucursal_id` (None = global).

        Si se indica organizacion se acota la busqueda de la sede a esa empresa
        (necesario al permitir nombres de sede repetidos entre organizaciones).
        Si se pide una sucursal concreta que no existe, no matchea nada
        (no se hereda el tarifario global)."""
        if not sucursal:
            return models.Settings.sucursal_id.is_(None)
        branch_id = BranchRepository.get_id_by_name(db, sucursal, organization_id)
        if branch_id is None:
            return false()
        return models.Settings.sucursal_id == branch_id

    @staticmethod
    def get_by_clave(db: Session, clave: str, sucursal: str = None, organization_id=None) -> models.Settings:
        """OBTIENE UN SETTING POR CLAVE; PREFIERE LA VARIANTE POR SUCURSAL Y FALLA A LA GLOBAL."""
        if sucursal:
            q = db.query(models.Settings).filter(
                models.Settings.clave == clave,
                SettingsRepository._sucursal_predicate(db, sucursal, organization_id)
            )
            if organization_id is not None:
                q = q.filter(models.Settings.organization_id == organization_id)
            setting = q.first()
            if setting:
                return setting
            return SettingsRepository.get_by_clave(db, clave, sucursal=None, organization_id=organization_id)
        q = db.query(models.Settings).filter(
            models.Settings.clave == clave,
            models.Settings.sucursal_id.is_(None),
        )
        if organization_id is not None:
            q = q.filter(models.Settings.organization_id == organization_id)
        return q.first()

    @staticmethod
    def get_by_clave_global(db: Session, clave: str) -> models.Settings:
        """OBTIENE UN SETTING GLOBAL (SIN SUCURSAL) POR CLAVE."""
        return db.query(models.Settings).filter(
            models.Settings.clave == clave,
            models.Settings.sucursal_id.is_(None)
        ).first()

    @staticmethod
    def get_by_clave_and_sucursal(db: Session, clave: str, sucursal: str = None, organization_id=None) -> models.Settings:
        """OBTIENE UN SETTING POR CLAVE Y SEDE (OPCIONALMENTE ACOTADO A UNA ORGANIZACION)."""
        q = db.query(models.Settings).filter(
            models.Settings.clave == clave,
            SettingsRepository._sucursal_predicate(db, sucursal, organization_id),
        )
        if organization_id is not None:
            q = q.filter(models.Settings.organization_id == organization_id)
        return q.first()

    @staticmethod
    def get_all_by_sucursal(db: Session, sucursal: str = None, organization_id=None) -> list:
        """OBTIENE LOS SETTINGS DE UNA SEDE (OPCIONALMENTE ACOTADOS A UNA ORGANIZACION)."""
        q = db.query(models.Settings).filter(
            SettingsRepository._sucursal_predicate(db, sucursal, organization_id)
        )
        if organization_id is not None:
            q = q.filter(models.Settings.organization_id == organization_id)
        return q.all()

    @staticmethod
    def get_rates_by_claves(db: Session, claves, sucursales=None, organization_id=None) -> list:
        """OBTIENE LOS SETTINGS DE UN CONJUNTO DE CLAVES, INCLUYENDO LAS VARIANTES POR SUCURSAL Y LAS GLOBALES."""
        conds = [models.Settings.clave.in_(claves)]
        if sucursales:
            ids = [BranchRepository.get_id_by_name(db, s, organization_id) for s in sucursales]
            ids = [i for i in ids if i]
            conds.append(or_(models.Settings.sucursal_id.in_(ids), models.Settings.sucursal_id.is_(None)))
        else:
            conds.append(models.Settings.sucursal_id.is_(None))
        if organization_id is not None:
            conds.append(models.Settings.organization_id == organization_id)
        return db.query(models.Settings).filter(*conds).all()

    @staticmethod
    def get_camera_sources_by_prefix(db: Session, prefix: str) -> list:
        """OBTIENE LOS SETTINGS DE CANALES ALPR (CAMERA_SOURCE_) DE UN PREFIJO DE SUCURSAL."""
        return db.query(models.Settings).filter(
            models.Settings.clave.like(f"CAMERA_SOURCE_{prefix}_%")
        ).all()