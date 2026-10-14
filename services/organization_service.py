"""Servicio de ORGANIZACIONES (multi-tenant).

Agrupa la creacion y consulta de organizaciones. Cada Admin General administra
una organizacion aislada; la marcada como `es_principal` es la unica visible en
el sitio publico.
"""
import models

PRINCIPAL_NOMBRE = "AUTOPASS"


class OrganizationService:
    @staticmethod
    def get_principal(db):
        """Devuelve la organizacion principal (la del sitio publico)."""
        return db.query(models.Organization).filter(models.Organization.es_principal == True).first()

    @staticmethod
    def get_by_id(db, organization_id):
        if organization_id is None:
            return None
        return db.query(models.Organization).filter(models.Organization.id == organization_id).first()

    @staticmethod
    def get_by_nombre(db, nombre: str):
        return db.query(models.Organization).filter(models.Organization.nombre == nombre).first()

    @staticmethod
    def create(db, nombre: str, principal: bool = False, commit: bool = True):
        """Crea una organizacion nueva (por defecto vacia de sucursales/usuarios)."""
        org = models.Organization(nombre=nombre, es_principal=principal, activa=True)
        db.add(org)
        if commit:
            db.commit()
            db.refresh(org)
        else:
            db.flush()
        return org

    @staticmethod
    def get_or_create_principal(db):
        org = OrganizationService.get_principal(db) or db.query(models.Organization).filter(
            models.Organization.nombre == "AUTOPASS"
        ).first()
        if not org:
            org = OrganizationService.create(db, "AUTOPASS", principal=True)
        return org
