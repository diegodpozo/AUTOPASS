import smtplib
import qrcode
import io
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from core.config import settings
import threading
import os

# Configuración de Jinja2 para emails
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "emails")
jinja_env = Environment(loader=FileSystemLoader(template_dir))

class EmailService:
    @staticmethod
    def _render_template(template_name: str, **context):
        """Renderiza un template de Jinja2 con el contexto provisto."""
        template = jinja_env.get_template(template_name)
        return template.render(**context)

    @staticmethod
    def _get_logo_base64():
        """Lee el logo desde el sistema de archivos (configurado en settings) y lo convierte a base64."""
        try:
            if os.path.exists(settings.LOGO_PATH):
                with open(settings.LOGO_PATH, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8')
            return ""
        except Exception as e:
            print(f"[MAIL ERROR] No se pudo cargar el logo desde {settings.LOGO_PATH}: {e}")
            return ""

    @staticmethod
    def _send_email(to_email: str, subject: str, html_content: str):
        """Método interno para envío sincrónico (ejecutado en un hilo)."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.PROJECT_NAME} <{settings.SMTP_FROM}>"
            msg["To"] = to_email

            part = MIMEText(html_content, "html")
            msg.attach(part)

            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
            print(f"[MAIL] Correo enviado exitosamente a {to_email}")
        except Exception as e:
            print(f"[MAIL ERROR] No se pudo enviar el correo a {to_email}: {e}")

    @staticmethod
    def send_async_email(to_email: str, subject: str, html_content: str):
        """Envía un correo de forma asíncrona para no bloquear la respuesta de la API."""
        thread = threading.Thread(
            target=EmailService._send_email, 
            args=(to_email, subject, html_content),
            daemon=True
        )
        thread.start()

    @staticmethod
    def send_recovery_email(to_email: str, user_name: str, recovery_url: str):
        """Envía el correo de recuperación de contraseña."""
        subject = "Recuperá tu contraseña - AutoPass"
        html_content = EmailService._render_template(
            "recovery.html", 
            user_name=user_name, 
            recovery_url=recovery_url
        )
        EmailService.send_async_email(to_email, subject, html_content)

    @staticmethod
    def send_reservation_confirmation(to_email: str, user_name: str, res_data: dict):
        """Envía la confirmación de reserva con el logo cargado dinámicamente."""
        subject = f"Tu Pase Digital - Reserva #{res_data['id']} - AUTOPASS"
        
        # Generar código QR
        qr_content = f"AUTOPASS|ID:{res_data['id']}|PLATE:{res_data['patente']}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
        qr_data_url = f"data:image/png;base64,{qr_base64}"

        # Logo dinámico desde archivo físico
        logo_base64 = EmailService._get_logo_base64()

        html_content = EmailService._render_template(
            "reservation_confirmation.html",
            user_name=user_name,
            res_data=res_data,
            logo_base64=logo_base64,
            qr_data_url=qr_data_url
        )
        EmailService.send_async_email(to_email, subject, html_content)
