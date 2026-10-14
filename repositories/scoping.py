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
"""
from sqlalchemy.orm import Query

import models


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
