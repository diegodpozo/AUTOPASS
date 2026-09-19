from sqlalchemy import or_
from sqlalchemy.orm import Session

import models

#--- REPOSITORIO DE CONFIGURACIONES GLOBALES (PRECIOS, PARAMETROS) ---


class SettingsRepository:
    @staticmethod
    def get_by_clave(db: Session, clave: str, sucursal: str = None) -> models.Settings:
        """OBTIENE UN SETTING POR CLAVE; PREFIERE LA VARIANTE POR SUCURSAL Y FALLA A LA GLOBAL."""
        if sucursal:
            setting = db.query(models.Settings).filter(
                models.Settings.clave == clave,
                models.Settings.sucursal == sucursal
            ).first()
            if setting:
                return setting
            return db.query(models.Settings).filter(
                models.Settings.clave == clave,
                models.Settings.sucursal == None
            ).first()
        return db.query(models.Settings).filter(
            models.Settings.clave == clave,
            models.Settings.sucursal == None
        ).first()

    @staticmethod
    def get_by_clave_global(db: Session, clave: str) -> models.Settings:
        """OBTIENE UN SETTING GLOBAL (SIN SUCURSAL) POR CLAVE."""
        return db.query(models.Settings).filter(
            models.Settings.clave == clave,
            models.Settings.sucursal == None
        ).first()

    @staticmethod
    def get_by_clave_and_sucursal(db: Session, clave: str, sucursal: str = None) -> models.Settings:
        """OBTIENE UN SETTING POR CLAVE Y SUCURSAL EXACTA (SIN FALLBACK A GLOBAL)."""
        return db.query(models.Settings).filter(
            models.Settings.clave == clave,
            models.Settings.sucursal == sucursal
        ).first()

    @staticmethod
    def get_all_by_sucursal(db: Session, sucursal: str = None) -> list:
        """OBTIENE TODOS LOS SETTINGS DE UNA SUCURSAL (None = GLOBALES)."""
        return db.query(models.Settings).filter(
            models.Settings.sucursal == sucursal
        ).all()

    @staticmethod
    def get_rates_by_claves(db: Session, claves, sucursales=None) -> list:
        """OBTIENE LOS SETTINGS DE UN CONJUNTO DE CLAVES, INCLUYENDO LAS VARIANTES POR SUCURSAL Y LAS GLOBALES."""
        conds = [models.Settings.clave.in_(claves)]
        if sucursales:
            conds.append(or_(models.Settings.sucursal.in_(sucursales), models.Settings.sucursal.is_(None)))
        else:
            conds.append(models.Settings.sucursal.is_(None))
        return db.query(models.Settings).filter(*conds).all()

    @staticmethod
    def get_camera_sources_by_prefix(db: Session, prefix: str) -> list:
        """OBTIENE LOS SETTINGS DE CANALES ALPR (CAMERA_SOURCE_) DE UN PREFIJO DE SUCURSAL."""
        return db.query(models.Settings).filter(
            models.Settings.clave.like(f"CAMERA_SOURCE_{prefix}_%")
        ).all()