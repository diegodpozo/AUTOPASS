"""
Punto de entrada independiente para el Servicio ALPR (Reconocimiento de Patentes).
Delegado al paquete modularizado `alpr`.
"""
import sys								# Importa `sys` para poder terminar el proceso con
									# `sys.exit(0)` cuando el usuario corta el servicio
									# con Ctrl+C
from alpr.runner import run_alpr_service				# Importa `run_alpr_service` desde
									# `alpr/runner.py`: es la funcion que arranca
									# realmente todo el pipeline ALPR (captura, OCR y
									# envio de eventos)

if __name__ == "__main__":						# Condicion de guarda: solo ejecuta el bloque si el
									# archivo se corre directamente (`python
									# alpr_service.py`) y no si se importa como modulo
    try:								# Abre un `try` para envolver el arranque del
									# servicio y poder manejar la interrupcion por
									# teclado sin dejar una traza de error
        run_alpr_service()						# Llama a `run_alpr_service()`, que inicia el bucle
									# principal del nodo ALPR (lectura de camaras,
									# deteccion de patentes y notificacion al backend)
    except KeyboardInterrupt:						# Captura `KeyboardInterrupt`, la excepcion que
									# Python lanza cuando el operador presiona Ctrl+C
									# para detener el servicio
        sys.exit(0)							# Cierra el proceso con codigo de salida 0,
									# tratando la parada manual como terminacion normal
									# y no como error
