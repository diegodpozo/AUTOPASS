"""Tests del envio SMTP de EmailService.

Verifican que SMTP_TLS dispare STARTTLS antes del login (necesario para
Gmail/Outlook en 587) y que sin credenciales no se intente autenticar.
Usa un SMTP falso: no abre conexiones de red.
"""
import services.email_service as email_service
from core.config import settings


class FakeSMTP:
    ultima = None

    def __init__(self, server, port, *args, **kwargs):
        self.server = server
        self.port = port
        self.calls = []
        FakeSMTP.ultima = self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self):
        self.calls.append("starttls")

    def login(self, usuario, password):
        self.calls.append("login")

    def sendmail(self, remitente, destino, mensaje):
        self.calls.append("sendmail")


def _configurar(monkeypatch, tls, con_credenciales=True):
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(settings, "SMTP_TLS", tls)
    monkeypatch.setattr(settings, "SMTP_USER", "cuenta@gmail.com" if con_credenciales else "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "app-password" if con_credenciales else "")
    monkeypatch.setattr(settings, "SMTP_FROM", "cuenta@gmail.com")


def test_starttls_antes_del_login_cuando_tls_activo(monkeypatch):
    _configurar(monkeypatch, tls=True)

    email_service.EmailService._send_email("cliente@mail.com", "Asunto", "<p>Hola</p>")

    assert FakeSMTP.ultima.calls == ["starttls", "login", "sendmail"]


def test_sin_tls_no_llama_starttls(monkeypatch):
    _configurar(monkeypatch, tls=False)

    email_service.EmailService._send_email("cliente@mail.com", "Asunto", "<p>Hola</p>")

    assert FakeSMTP.ultima.calls == ["login", "sendmail"]


def test_sin_credenciales_no_autentica(monkeypatch):
    _configurar(monkeypatch, tls=True, con_credenciales=False)

    email_service.EmailService._send_email("cliente@mail.com", "Asunto", "<p>Hola</p>")

    assert FakeSMTP.ultima.calls == ["starttls", "sendmail"]


def test_dominios_de_prueba_no_envian_email(monkeypatch):
    # VERIFICA QUE DIRECCIONES DE PRUEBA NO DISPAREN CONEXION SMTP
    _configurar(monkeypatch, tls=True)
    FakeSMTP.ultima = None

    email_service.EmailService._send_email("usuario@test.com", "Asunto", "<p>Hola</p>")
    email_service.EmailService._send_email("otro@example.com", "Asunto", "<p>Hola</p>")

    assert FakeSMTP.ultima is None


def test_notificacion_cancelacion_no_envia_email(monkeypatch):
    # VERIFICA QUE LA NOTIFICACION DE CANCELACION NO DISPARE ENVIO DE CORREO
    llamadas_async = []
    monkeypatch.setattr(email_service.EmailService, "send_async_email", lambda *a, **k: llamadas_async.append(a))

    datos_reserva = {
        "id": 99,
        "fecha_inicio": "2026-11-19 12:00",
        "fecha_fin": "2026-11-19 13:00"
    }
    email_service.EmailService.send_auto_cancelled_notification("usuario@mail.com", "Juan", datos_reserva)

    assert len(llamadas_async) == 0
