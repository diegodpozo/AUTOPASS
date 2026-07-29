"""
Punto de entrada independiente para el Servicio ALPR (Reconocimiento de Patentes).
Delegado al paquete modularizado `alpr`.
"""
import sys
from alpr.runner import run_alpr_service

if __name__ == "__main__":
    try:
        run_alpr_service()
    except KeyboardInterrupt:
        sys.exit(0)
