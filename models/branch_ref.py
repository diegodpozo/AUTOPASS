"""Referencia de sede por ID con traduccion central de nombre->id.

El nombre de la sucursal vive UNICAMENTE en `parking_branches`. Todas las tablas
dependientes guardan solo `sucursal_id`. Para no romper a ningun llamador que
todavia entregue el NOMBRE (API, seeds, tests), este modulo ofrece:

- `branch_ref_property()`: hybrid que expone el nombre de la sede
  (`sucursal` / `sucursal_nombre`) para display y permite seguir haciendo
  `Modelo.sucursal == x` (se traduce a un subselect sobre parking_branches).
- un traductor central (`before_flush`) que resuelve el nombre pendiente a
  `sucursal_id` una sola vez por flush, con cache por flush.

NO propaga nada: renombrar una sede toca unicamente parking_branches.
"""
from sqlalchemy import event, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Session

_UNSET = object()

# Modelos con referencia de sede; se puebla desde models/__init__.py
_LINKED: set = set()


def branch_ref_property(default=None):
    """Hybrid de lectura del nombre de la sede, con setter que POSTERGA la
    traduccion a id (la resuelve el traductor central en el primer flush).

    `default` es el valor que se devuelve cuando la fila no apunta a ninguna
    sede (p.ej. "General" para tickets de soporte globales)."""

    def _get(self):
        pendiente = self.__dict__.get("_sucursal_input", _UNSET)
        if pendiente is not _UNSET:
            return pendiente
        try:
            branch = self.branch
        except Exception:
            branch = None
        if branch is not None:
            return branch.nombre
        # Nombre no resoluble a una sede (dato legacy name-only): se conserva en
        # memoria para display/comparacion. La BD solo persistio `sucursal_id`.
        fallback = self.__dict__.get("_sucursal_fallback")
        if fallback is not None:
            return fallback
        return default

    def _set(self, value):
        self.__dict__["_sucursal_input"] = value
        # La columna ya no es un atributo mapeado: forzamos a que SQLAlchemy
        # considere la instancia "dirty" para que el traductor la vea en updates.
        try:
            from sqlalchemy.orm.attributes import flag_dirty
            flag_dirty(self)
        except Exception:
            pass

    def _expr(cls):
        from sqlalchemy import func
        from models.parking import ParkingBranch
        col = (
            select(ParkingBranch.nombre)
            .where(ParkingBranch.id == cls.sucursal_id)
            .correlate(cls)
            .scalar_subquery()
        )
        return func.coalesce(col, default) if default is not None else col

    return hybrid_property(_get, _set, expr=_expr)


def register_branch_linked(*modelos):
    """Registra los modelos cuyo nombre de sede debe traducirse a `sucursal_id`."""
    _LINKED.update(modelos)


def _resolver_organizacion(session, obj):
    """Deduce la organizacion del objeto pendiente para acotar el nombre de sede.

    - Modelos con `organization_id` (User, Promotion, Settings, ParkingAforo): lo usan.
    - Modelos con `user_id` (Reservation, SupportTicket, RedemptionTicket): via el usuario.
    - AccessLog con `reservation_id`: via la reserva -> usuario.
    - Si no se puede deducir (p.ej. ParkingCamera), devuelve None (se resuelve solo
      si el nombre es globalmente unico, nunca cruzando de organizacion)."""
    org = getattr(obj, "organization_id", None)
    if org:
        return org

    from models.user import User
    from models.reservation import Reservation

    uid = getattr(obj, "user_id", None)
    if uid:
        org = session.execute(
            select(User.organization_id).where(User.id == uid)
        ).scalar()
        if org:
            return org

    rid = getattr(obj, "reservation_id", None)
    if rid:
        uid = session.execute(
            select(Reservation.user_id).where(Reservation.id == rid)
        ).scalar()
        if uid:
            return session.execute(
                select(User.organization_id).where(User.id == uid)
            ).scalar()

    return None


def _elegir_sede(session, candidatas, obj):
    """Elige la sede del MISMO origen que el objeto. Nunca cruza de organizacion.

    Si el objeto tiene organizacion conocida, exige una sede de ESA empresa (aunque
    el nombre sea unico en el sistema). Si no se conoce la organizacion, solo
    resuelve cuando el nombre es globalmente unico (comportamiento single-tenant)."""
    if not candidatas:
        return None
    org = _resolver_organizacion(session, obj)
    if org is not None:
        for branch in candidatas:
            if getattr(branch, "organization_id", None) == org:
                return branch
        return None
    if len(candidatas) == 1:
        return candidatas[0]
    return None


@event.listens_for(Session, "before_flush")
def _translate_branch_names(session, flush_context, instances):
    pendientes = [
        obj
        for obj in list(session.new) + list(session.dirty)
        if type(obj) in _LINKED and "_sucursal_input" in obj.__dict__
    ]
    if not pendientes:
        return

    from models.parking import ParkingBranch
    from core.normalize import normalize_branch_name

    por_nombre = {}
    for branch in session.execute(select(ParkingBranch)).scalars():
        clave = normalize_branch_name(branch.nombre)
        if clave:
            por_nombre.setdefault(clave, []).append(branch)
    # Las sedes nuevas del MISMO flush aun no tienen id: se resuelven por objeto.
    for obj in session.new:
        if isinstance(obj, ParkingBranch):
            clave = normalize_branch_name(obj.nombre)
            if clave:
                por_nombre.setdefault(clave, []).append(obj)

    for obj in pendientes:
        nombre = obj.__dict__.pop("_sucursal_input")
        clave = normalize_branch_name(nombre or "")
        branch = _elegir_sede(session, por_nombre.get(clave, []) if clave else [], obj)
        obj.branch = branch
        if branch is None and nombre:
            obj.__dict__["_sucursal_fallback"] = nombre
        else:
            obj.__dict__.pop("_sucursal_fallback", None)
