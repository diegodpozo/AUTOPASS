"""Configuracion global de la suite de tests.

Blinda el hardware serial (Arduino Uno) durante los tests: si hay un puerto
COM presente pero sin dispositivo respondiendo, `serial.Serial.write()` puede
bloquearse indefinidamente y colgar la corrida de pytest. Los tests de barrera
ya mockean `HardwareService.trigger_barrier`/`send_serial_command`; este guard
evita cualquier intento de abrir un puerto real.

Los tests que necesiten el serial real deben reactivarlo dentro del propio test
(`settings.SERIAL_ENABLED = True`) y limpiar `HardwareService._serial_port`.
"""

from core.config import settings

settings.SERIAL_ENABLED = False
