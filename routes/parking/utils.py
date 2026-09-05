"""
Fachada de utilidades de normalización.
Re-exporta las funciones centralizadas de core.normalize para mantener retrocompatibilidad.
"""

from core.normalize import (
    normalize_plate,
    format_plate,
    normalize_dni,
    normalize_name,
    normalize_user_name,
    normalize_branch_name,
)

__all__ = [
    "normalize_plate",
    "format_plate",
    "normalize_dni",
    "normalize_name",
    "normalize_user_name",
    "normalize_branch_name",
]

