"""Configuracion global de la suite de tests.

Blinda el hardware serial (Arduino Uno) durante los tests: si hay un puerto
COM presente pero sin dispositivo respondiendo, `serial.Serial.write()` puede
bloquearse indefinidamente y colgar la corrida de pytest. Los tests de barrera
ya mockean `HardwareService.trigger_barrier`/`send_serial_command`; este guard
evita cualquier intento de abrir un puerto real.

Los tests que necesiten el serial real deben reactivarlo dentro del propio test
(`settings.SERIAL_ENABLED = True`) y limpiar `HardwareService._serial_port`.

Blinda ademas el correo: `EmailService` habla SMTP real (Gmail), asi que toda
prueba que llegue a enviar (recordatorios del worker, confirmaciones de pago)
mandaria un correo a las direcciones ficticias de los tests (`@test.com`,
`@example.com`) y verias el rebote de Gmail. Se reemplaza `smtplib.SMTP` por un
sustituto sin red; los tests que quieran verificar la logica de envio vuelven a
parchear `email_service.smtplib.SMTP` dentro del propio test (ver
`tests/test_email_service.py`).
"""

import pytest

import services.email_service as email_service
from core.config import settings

settings.SERIAL_ENABLED = False


class _SinRedSMTP:
    """Reemplazo de `smtplib.SMTP` que no abre ninguna conexion real."""

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, *args, **kwargs):
        pass

    def login(self, *args, **kwargs):
        pass

    def sendmail(self, *args, **kwargs):
        pass

    def quit(self, *args, **kwargs):
        pass


@pytest.fixture(autouse=True)
def _sin_correo_real(monkeypatch):
    """Los tests jamas envian correo real por SMTP."""
    monkeypatch.setattr(email_service.smtplib, "SMTP", _SinRedSMTP)

