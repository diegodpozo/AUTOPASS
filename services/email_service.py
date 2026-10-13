import smtplib
import qrcode
import io
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from core.config import settings
from core.logger import get_logger, mask_email
import threading
import os

logger = get_logger("EmailService")

# CONFIGURACION DE JINJA2 PARA EMAILS
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "emails")
jinja_env = Environment(loader=FileSystemLoader(template_dir))

class EmailService:
    @staticmethod
    def _render_template(template_name: str, **context):
        """RENDERIZA UN TEMPLATE DE JINJA2 CON EL CONTEXTO PROVISTO."""
        template = jinja_env.get_template(template_name)
        return template.render(**context)

    @staticmethod
    def _get_logo_base64():
        """LEE EL LOGO DESDE EL SISTEMA DE ARCHIVOS (CONFIGURADO EN SETTINGS) Y LO CONVIERTE A BASE64."""
        try:
            if os.path.exists(settings.LOGO_PATH):
                with open(settings.LOGO_PATH, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8')
            return ""
        except Exception as e:
            logger.error(f"No se pudo cargar el logo desde {settings.LOGO_PATH}: {e}")
            return ""

    @staticmethod
    def _send_email(to_email: str, subject: str, html_content: str):
        """METODO INTERNO PARA ENVIO SINCRONICO (EJECUTADO EN UN HILO)."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.PROJECT_NAME} <{settings.SMTP_FROM}>"
            msg["To"] = to_email

            part = MIMEText(html_content, "html")
            msg.attach(part)

            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
            logger.info(f"Correo enviado exitosamente a {mask_email(to_email)}")
        except Exception as e:
            logger.error(f"No se pudo enviar el correo a {mask_email(to_email)}: {e}")

    @staticmethod
    def send_async_email(to_email: str, subject: str, html_content: str):
        """ENVIA UN CORREO DE FORMA ASINCRONA PARA NO BLOQUEAR LA RESPUESTA DE LA API."""
        thread = threading.Thread(
            target=EmailService._send_email, 
            args=(to_email, subject, html_content),
            daemon=True
        )
        thread.start()

    @staticmethod
    def send_recovery_email(to_email: str, user_name: str, recovery_url: str):
        """ENVIA EL CORREO DE RECUPERACION DE CONTRASENA."""
        subject = "Recuperá tu contraseña - AutoPass"
        html_content = EmailService._render_template(
            "recovery.html", 
            user_name=user_name, 
            recovery_url=recovery_url
        )
        EmailService.send_async_email(to_email, subject, html_content)

    @staticmethod
    def send_reservation_confirmation(to_email: str, user_name: str, res_data: dict):
        """ENVIA LA CONFIRMACION DE RESERVA CON EL LOGO CARGADO DINAMICAMENTE."""
        subject = f"Tu Pase Digital - Reserva #{res_data['id']} - AUTOPASS"
        
        # GENERAR CODIGO QR
        qr_content = f"AUTOPASS|ID:{res_data['id']}|PLATE:{res_data['patente']}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
        qr_data_url = f"data:image/png;base64,{qr_base64}"

        # LOGO DINAMICO DESDE ARCHIVO FISICO
        logo_base64 = EmailService._get_logo_base64()

        html_content = EmailService._render_template(
            "reservation_confirmation.html",
            user_name=user_name,
            res_data=res_data,
            logo_base64=logo_base64,
            qr_data_url=qr_data_url
        )
        EmailService.send_async_email(to_email, subject, html_content)

    @staticmethod
    def send_reservation_reminder(to_email: str, user_name: str, res_data: dict):
        """ENVIA RECORDATORIO 30 MIN ANTES DE UNA RESERVA."""
        pagada = res_data.get('pagada', False)
        if pagada:
            subject = f"Tu reserva #{
                res_data['id']} comienza en 30 minutos - AUTOPASS"
        else:
            subject = f"Recordatorio de pago - Reserva #{
                res_data['id']} - AUTOPASS"
        html_content = EmailService._render_template(
            "reservation_reminder.html",
            user_name=user_name,
            res_data=res_data,
            pagada=pagada
        )
        EmailService.send_async_email(to_email, subject, html_content)

    @staticmethod
    def send_auto_cancelled_notification(to_email: str, user_name: str, res_data: dict):
        """AVISA AL USUARIO QUE SU RESERVA FUE CANCELADA POR NO INGRESAR A TIEMPO."""
        subject = f"Reserva #{res_data['id']} cancelada - AUTOPASS"
        html_content = EmailService._render_template(
            "reservation_auto_cancelled.html",
            user_name=user_name,
            res_data=res_data
        )
        EmailService.send_async_email(to_email, subject, html_content)
