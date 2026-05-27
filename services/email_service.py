import smtplib
import qrcode
import io
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings
import threading

class EmailService:
    @staticmethod
    def _send_email(to_email: str, subject: str, html_content: str):
        """Método interno para envío sincrónico (ejecutado en un hilo)."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"AutoPass <{settings.SMTP_FROM}>"
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
        """Envía el correo de recuperación de contraseña con diseño premium y responsive."""
        subject = "Recuperá tu contraseña - AutoPass"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                @media only screen and (max-width: 620px) {{
                    .container {{ width: 100% !important; border-radius: 0 !important; }}
                    .content {{ padding: 20px !important; }}
                }}
            </style>
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #000; color: #fff; margin: 0; padding: 0;">
            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #000;">
                <tr>
                    <td align="center" style="padding: 20px 0;">
                        <table class="container" border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #111; border: 1px solid #C5A059; border-radius: 10px; overflow: hidden;">
                            <!-- HEADER -->
                            <tr>
                                <td align="center" style="background-color: #C5A059; padding: 25px;">
                                    <h1 style="color: #000; margin: 0; font-size: 28px; letter-spacing: 4px; font-weight: 900;">AUTOPASS</h1>
                                </td>
                            </tr>
                            <!-- CONTENT -->
                            <tr>
                                <td class="content" style="padding: 40px; line-height: 1.6;">
                                    <h2 style="color: #C5A059; margin-top: 0;">¡Hola, {user_name}!</h2>
                                    <p style="color: #ccc; font-size: 16px;">Recibimos una solicitud para restablecer tu contraseña en <strong>AUTOPASS</strong>.</p>
                                    <p style="color: #ccc; font-size: 16px;">Si no hiciste esta solicitud, podés ignorar este correo de forma segura.</p>
                                    
                                    <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                        <tr>
                                            <td align="center" style="padding: 40px 0;">
                                                <a href="{recovery_url}" style="background-color: #C5A059; color: #000; padding: 18px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; display: inline-block; text-transform: uppercase;">Restablecer Contraseña</a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="font-size: 14px; color: #666; text-align: center; margin-bottom: 0;">Este enlace expirará en 30 minutos por tu seguridad.</p>
                                </td>
                            </tr>
                            <!-- FOOTER -->
                            <tr>
                                <td align="center" style="background-color: #000; padding: 25px; border-top: 1px solid #222;">
                                    <p style="font-size: 12px; color: #444; margin: 0;">&copy; 2026 AutoPass Professional.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        EmailService.send_async_email(to_email, subject, html_content)

    @staticmethod
    def send_reservation_confirmation(to_email: str, user_name: str, res_data: dict):
        """Envía la confirmación de reserva con la estética exacta del Pase Digital (Ticket Físico)."""
        subject = f"Tu Pase Digital - Reserva #{res_data['id']} - AUTOPASS"
        
        # Generar código QR real
        qr_content = f"AUTOPASS|ID:{res_data['id']}|PLATE:{res_data['patente']}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
        qr_data_url = f"data:image/png;base64,{qr_base64}"

        # Logo AutoPass (Base64 real)
        logo_base64 = "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"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: 'Montserrat', 'Segoe UI', Arial, sans-serif; }}
                @media only screen and (max-width: 620px) {{
                    .ticket {{ width: 340px !important; padding: 25px !important; }}
                }}
            </style>
        </head>
        <body style="background-color: #000; color: #fff; margin: 0; padding: 0;">
            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #000;">
                <tr>
                    <td align="center" style="padding: 50px 0;">
                        
                        <!-- TICKET WRAPPER -->
                        <div style="position: relative; display: inline-block;">
                            
                            <!-- EL TICKET -->
                            <table class="ticket" border="0" cellpadding="0" cellspacing="0" width="360" style="background-color: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 28px; padding: 35px; box-shadow: 0 40px 80px rgba(0,0,0,0.9); position: relative; overflow: hidden;">
                                <!-- HEADER -->
                                <tr>
                                    <td style="padding-bottom: 25px; border-bottom: 1px dashed rgba(255, 255, 255, 0.1);">
                                        <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                            <tr>
                                                <td width="55" style="vertical-align: middle;">
                                                    <img src="data:image/png;base64,{logo_base64}" alt="AutoPass" width="45" style="display: block; filter: drop-shadow(0 0 5px rgba(197, 160, 89, 0.5));">
                                                </td>
                                                <td style="vertical-align: middle; padding-left: 10px;">
                                                    <div style="font-weight: 900; font-size: 22px; letter-spacing: 5px; color: #C5A059; text-transform: uppercase; line-height: 1;">AUTOPASS</div>
                                                    <div style="font-size: 10px; font-weight: 800; color: #666; text-transform: uppercase; letter-spacing: 2px; margin-top: 4px;">PASE DIGITAL</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>

                                <!-- QR SECTION -->
                                <tr>
                                    <td align="center" style="padding: 40px 0;">
                                        <div style="background-color: #fff; padding: 15px; border-radius: 20px; display: inline-block; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                                            <img src="{qr_data_url}" alt="Código QR" width="180" height="180" style="display: block;">
                                        </div>
                                        <div style="margin-top: 20px; font-family: 'JetBrains Mono', monospace; font-size: 14px; color: #444; font-weight: 700; letter-spacing: 1px;">#{str(res_data['id']).zfill(6)}</div>
                                    </td>
                                </tr>

                                <!-- INFO GRID -->
                                <tr>
                                    <td>
                                        <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                            <tr>
                                                <td width="50%" style="padding-bottom: 25px;">
                                                    <div style="font-size: 10px; font-weight: 800; color: #C5A059; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; opacity: 0.6;">PATENTE</div>
                                                    <div style="background: #000; color: #C5A059; padding: 6px 14px; border-radius: 10px; width: fit-content; font-family: monospace; font-weight: 900; font-size: 18px; border: 1.5px solid rgba(197, 160, 89, 0.4);">{res_data['patente']}</div>
                                                </td>
                                                <td width="50%" style="padding-bottom: 25px;">
                                                    <div style="font-size: 10px; font-weight: 800; color: #C5A059; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; opacity: 0.6;">VENCE</div>
                                                    <div style="font-size: 15px; color: #fff; font-weight: 700;">{res_data['fecha_fin'].split(' ')[0]}</div>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td colspan="2" style="padding-bottom: 20px;">
                                                    <div style="font-size: 10px; font-weight: 800; color: #C5A059; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; opacity: 0.6;">SUCURSAL</div>
                                                    <div style="font-size: 15px; color: #fff; font-weight: 700;">{res_data['sucursal']}</div>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td colspan="2" style="padding-bottom: 30px;">
                                                    <div style="font-size: 10px; font-weight: 800; color: #C5A059; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; opacity: 0.6;">DIRECCIÓN</div>
                                                    <div style="font-size: 12px; color: #888; font-weight: 400; line-height: 1.4;">{res_data['direccion']}</div>
                                                </td>
                                            </tr>
                                            <!-- DIVIDER -->
                                            <tr>
                                                <td colspan="2" style="padding-top: 25px; border-top: 1px dashed rgba(255, 255, 255, 0.1);">
                                                    <div style="font-size: 11px; color: #555; text-align: center; font-style: italic; line-height: 1.5;">Presentá este código en el lector de la entrada si el reconocimiento de patente falla.</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>

                            <!-- LOS MORDISCOS (Side Cutouts) - Simulados con círculos absolutos (solo funcionan en algunos clientes, pero dan el toque pro) -->
                            <!-- En email es mejor usar una tabla con celdas de fondo negro a los costados si se quiere fidelidad extrema, pero esto es un buen compromiso -->
                        </div>
                        
                        <p style="font-size: 12px; color: #333; margin-top: 40px; font-weight: bold; letter-spacing: 1px;">&copy; 2026 AUTOPASS PROFESSIONAL.</p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        EmailService.send_async_email(to_email, subject, html_content)
