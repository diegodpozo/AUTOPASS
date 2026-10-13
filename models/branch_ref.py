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
            por_nombre.setdefault(clave, branch)
    # Las sedes nuevas del MISMO flush aun no tienen id: se resuelven por objeto.
    for obj in session.new:
        if isinstance(obj, ParkingBranch):
            clave = normalize_branch_name(obj.nombre)
            if clave:
                por_nombre[clave] = obj

    for obj in pendientes:
        nombre = obj.__dict__.pop("_sucursal_input")
        clave = normalize_branch_name(nombre or "")
        branch = por_nombre.get(clave) if clave else None
        obj.branch = branch
        if branch is None and nombre:
            obj.__dict__["_sucursal_fallback"] = nombre
        else:
            obj.__dict__.pop("_sucursal_fallback", None)
