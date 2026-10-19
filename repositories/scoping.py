"""Helper central de aislamiento por ORGANIZACION (multi-tenant).

Cada Admin General ve solo los datos de su organizacion. Para no repetir el
predicado en cada repositorio, este modulo ofrece una unica funcion que aplica
el filtro segun como esté ligado el modelo a la organizacion:

- modelos "raiz" con columna `organization_id` (users, parking_branches,
  settings, parking_aforo, promotions) -> filtro directo.
- modelos ligados a una sede via `sucursal_id` (reservations, access_logs,
  support_tickets, redemption_tickets, parking_cameras) -> join a
  parking_branches y filtro por la organizacion de la sede.

Es TOLERANTE: si `organization_id` es None, no filtra (comportamiento
single-tenant, usado por tests y por datos previos a la migracion).

Ofrece ademas las atribuciones de sede que usan seguridad/services:
`organization_of_sede` (sede -> organizacion) y `sede_ids_and_names`
(organizacion -> ids y nombres de sedes atribuibles), mas el umbral
`multi_organization_active` que decide si el modo estricto esta activo.
"""
from typing import Optional

from sqlalchemy.orm import Query

import models
from core.normalize import normalize_branch_name


def scope_by_organization(query: Query, model, organization_id) -> Query:
    """Aplica el filtro de organizacion a `query` sobre `model`."""
    if organization_id is None:
        return query
    if hasattr(model, "organization_id"):
        return query.filter(model.organization_id == organization_id)
    if hasattr(model, "sucursal_id"):
        return query.join(
            models.ParkingBranch, model.sucursal_id == models.ParkingBranch.id
        ).filter(models.ParkingBranch.organization_id == organization_id)
    return query


def multi_organization_active(db) -> bool:
    """True si hay mas de una organizacion: multi-tenant ACTIVO (modo estricto).

    Con menos de una empresa en la base no existe riesgo cruzado, asi que se
    conserva el comportamiento tolerante (datos legacy y tests single-tenant)."""
    try:
        return (db.query(models.Organization).count() or 0) > 1
    except Exception:
        return False


def organization_of_sede(db, branch_id=None, branch_name=None) -> Optional[int]:
    """ORGANIZACION A LA QUE PERTENECE UNA SEDE REFERENCIADA POR ID O POR NOMBRE.

    - Con `branch_id`: devuelve la organizacion de esa sucursal (None si no existe
      o si la sucursal no tiene organizacion asignada).
    - Con `branch_name`: busca por nombre normalizado; solo devuelve organizacion
      si TODAS las sedes con ese nombre pertenecen a la misma empresa. Si el
      nombre se repite entre organizaciones es AMBIGUO y devuelve None: una fila
      legacy sin `sucursal_id` no puede atribuirse a nadie en ese caso.
    """
    if branch_id:
        branch = db.query(models.ParkingBranch).filter(
            models.ParkingBranch.id == branch_id
        ).first()
        if branch is not None:
            return branch.organization_id
    if not branch_name:
        return None
    clave = normalize_branch_name(branch_name)
    if not clave:
        return None
    candidatas = [
        b for b in db.query(models.ParkingBranch).all()
        if normalize_branch_name(b.nombre) == clave
    ]
    if not candidatas:
        return None
    orgs = {b.organization_id for b in candidatas}
    return orgs.pop() if len(orgs) == 1 else None


def sede_ids_and_names(db, organization_id) -> tuple:
    """(IDS, NOMBRES) DE LAS SEDES ATRIBUIBLES A UNA ORGANIZACION.

    Los nombres solo se devuelven si NO se repiten en otra organizacion: son el
    fallback legacy (filas sin `sucursal_id`) y con un nombre ambigu no seria
    posible decidir de quien es la fila. Con `organization_id` None no hay nada
    atribuible."""
    if organization_id is None:
        return [], []
    todas = db.query(models.ParkingBranch).all()
    propias = [b for b in todas if b.organization_id == organization_id]
    ajenas = {
        normalize_branch_name(b.nombre)
        for b in todas
        if b.organization_id != organization_id
    }
    ids = [b.id for b in propias]
    nombres = [
        b.nombre for b in propias
        if normalize_branch_name(b.nombre) not in ajenas
    ]
    return ids, nombres
