import os
import threading
import time
import datetime
from core.database import SessionLocal
from core.config import settings
from core.logger import get_logger, mask_email
from services.reservation_service import ReservationService
from services.user_notification_service import UserNotificationService
from services.email_service import EmailService
from services.time_service import TimeService
from models.enums import PaymentStatus, ReservationStatus
from repositories.access_log_repository import AccessRepository
from repositories.notification_repository import NotificationRepository
from repositories.reservation_repository import ReservationRepository

logger = get_logger("WorkerService")

NOTIFICATION_CHECK_INTERVAL = 30  # SEGUNDOS

class WorkerService:
    @staticmethod
    def start_reservation_cleanup():
        """INICIA EL HILO DE LIMPIEZA DE RESERVAS."""
        thread = threading.Thread(target=WorkerService._reservation_cleanup_worker, daemon=True)
        thread.start()
        return thread

    @staticmethod
    def start_notification_worker():
        """INICIA EL HILO DE RECORDATORIOS Y AUTO-CANCELACION."""
        thread = threading.Thread(target=WorkerService._notification_worker, daemon=True)
        thread.start()
        return thread

    @staticmethod
    def _reservation_cleanup_worker():
        """HILO DE FONDO QUE LIMPIA Y FINALIZA RESERVAS Y PURGA IMAGENES ALPR PERIODICAMENTE."""
        logger.info("Hilo de mantenimiento de reservas iniciado.")
        while True:
            db = None
            try:
                db = SessionLocal()
                ReservationService.cleanup_overdue_reservations(db)
                ReservationService.auto_finalize_all_reservations(db)
                WorkerService._cleanup_old_alpr_images()
            except Exception as e:
                logger.error(f"En el trabajador de reservas: {e}")
            finally:
                if db:
                    try:
                        db.close()
                    except Exception:
                        logger.warning("[WORKER] Error cerrando sesión en mantenedor de reservas", exc_info=True)
            time.sleep(settings.MAINTENANCE_INTERVAL_SECONDS)

    @staticmethod
    def _cleanup_old_alpr_images():
        """PURGA IMAGENES DE ALPR MAS ANTIGUAS QUE ALPR_IMAGE_RETENTION_DAYS."""
        try:
            image_dir = settings.IMAGE_DIR
            retention_days = getattr(settings, 'ALPR_IMAGE_RETENTION_DAYS', 30)
            if not os.path.exists(image_dir) or retention_days <= 0:
                return

            cutoff_seconds = time.time() - (retention_days * 86400)
            purged_count = 0
            for filename in os.listdir(image_dir):
                file_path = os.path.join(image_dir, filename)
                if os.path.isfile(file_path):
                    mtime = os.path.getmtime(file_path)
                    if mtime < cutoff_seconds:
                        try:
                            os.unlink(file_path)
                            purged_count += 1
                        except Exception as err:
                            logger.warn(f"No se pudo eliminar imagen antigua {filename}: {err}")

            if purged_count > 0:
                logger.info(f"Purga ALPR: Se eliminaron {purged_count} imágenes más antiguas a {retention_days} días.")
        except Exception as e:
            logger.error(f"Error purgando imágenes ALPR antiguas: {e}")

    @staticmethod
    def _notification_worker():
        """HILO DE FONDO QUE MANEJA RECORDATORIOS Y CANCELACION AUTOMATICA."""
        logger.info("Hilo de notificaciones de reservas iniciado.")
        while True:
            db = None
            try:
                db = SessionLocal()
                WorkerService._process_reminders(db)
                WorkerService._process_started_reservations(db)
                WorkerService._process_auto_cancellations(db)
            except Exception as e:
                logger.error(f"En el trabajador de notificaciones: {e}")
            finally:
                if db:
                    try:
                        db.close()
                    except Exception:
                        logger.warning("[WORKER] Error cerrando sesión en trabajador de notificaciones", exc_info=True)
            time.sleep(NOTIFICATION_CHECK_INTERVAL)

    @staticmethod
    def _process_reminders(db):
        """ENVIA RECORDATORIOS A RESERVAS QUE FALTAN HASTA 31 MIN PARA INICIAR."""
        now = TimeService.now()
        corte = now + datetime.timedelta(minutes=31)
        fmt_corte = corte.strftime("%Y-%m-%d %H:%M")
        fmt_ahora = now.strftime("%Y-%m-%d %H:%M")

        candidatas = ReservationRepository.get_pending_reminders(db, fmt_ahora, fmt_corte)

        for res in candidatas:
            try:
                # Marcar recordatorio_confirmado como True para evitar re-procesamiento en loops subsecuentes
                res.recordatorio_confirmado = True
                db.commit()

                user = res.user
                if not user or not user.email:
                    continue

                # Evitar notificaciones duplicadas si ya fue notificado previamente
                notif_existente = NotificationRepository.get_by_reserva_and_types(
                    db, res.id, ["REMINDER_PAID", "REMINDER_UNPAID"]
                )
                if notif_existente:
                    continue

                pagada = res.estado_pago == PaymentStatus.PAGADO

                # CREAR NOTIFICACION IN-APP
                if pagada:
                    titulo = "Tu reserva comienza en 30 minutos"
                    mensaje = f"Reserva #{res.id} en {res.sucursal_nombre} lista para ingresar. Presentá tu QR en la entrada."
                    tipo_notif = "REMINDER_PAID"
                else:
                    titulo = "Recordatorio de pago"
                    mensaje = f"Reserva #{res.id} en {res.sucursal_nombre} aún no está pagada. Aboná antes del inicio para no perder tu lugar."
                    tipo_notif = "REMINDER_UNPAID"

                UserNotificationService.create_notification(
                    db, user.id, tipo_notif, titulo, mensaje, res.id
                )

                # ENVIAR EMAIL
                res_data = {
                    "id": res.id,
                    "sucursal": res.sucursal_nombre,
                    "patente": res.patente,
                    "fecha_inicio": res.fecha_inicio,
                    "fecha_fin": res.fecha_fin,
                    "pagada": pagada
                }
                EmailService.send_reservation_reminder(user.email, user.nombre, res_data)
                logger.info(f"Recordatorio enviado a {mask_email(user.email)} para reserva #{res.id}")
            except Exception as e:
                logger.error(f"Procesando recordatorio reserva #{res.id}: {e}")

    @staticmethod
    def _process_started_reservations(db):
        """PASA A ACTIVA LAS RESERVAS PENDIENTES CUYO HORARIO INICIO Y NOTIFICA EL INICIO (UNA SOLA VEZ)."""
        now_str = TimeService.now_str()
        iniciadas = ReservationRepository.get_pending_started(db, now_str)

        for res in iniciadas:
            try:
                user = res.user
                if not user:
                    continue

                # PASAR A ACTIVA Y MARCAR RECORDATORIO COMO PROCESADO
                res.estado_reserva = ReservationStatus.ACTIVA
                res.recordatorio_confirmado = True
                db.commit()

                pagada = res.estado_pago == PaymentStatus.PAGADO

                notif_existente = NotificationRepository.get_by_reserva_and_types(
                    db, res.id, ["RESERVATION_STARTED"]
                )
                if notif_existente:
                    continue

                titulo = "Tu reserva ya comenzó!"
                mensaje = f"Reserva #{res.id} en {res.sucursal_nombre} - Patente {res.patente}. "
                if pagada:
                    mensaje += "Presentá tu QR en la entrada."
                else:
                    mensaje += "Aboná para evitar la cancelación automática."

                UserNotificationService.create_notification(
                    db, user.id, "RESERVATION_STARTED", titulo, mensaje, res.id
                )
                logger.info(f"Aviso de inicio enviado para reserva #{res.id}")
            except Exception as e:
                logger.error(f"Procesando inicio de reserva #{res.id}: {e}")

    @staticmethod
    def _process_auto_cancellations(db):
        """CANCELA AUTOMATICAMENTE RESERVAS IMPAGAS 30 MIN DESPUES DEL INICIO SIN INGRESO."""
        now = TimeService.now()
        grace = now - datetime.timedelta(minutes=30)
        fmt_grace = grace.strftime("%Y-%m-%d %H:%M")

        candidatas = ReservationRepository.get_unpaid_overdue(db, fmt_grace)

        # BATCH: una sola query con todos los ids (rutas A5) en vez de 1 query por reserva
        ingresaron = AccessRepository.get_reserva_ids_with_entry(db, [res.id for res in candidatas])

        for res in candidatas:
            try:
                # VERIFICAR SI EL VEHICULO INGRESO
                if res.id in ingresaron:
                    continue  # YA INGRESO, NO CANCELAR

                # CANCELAR LA RESERVA
                res.estado_reserva = ReservationStatus.CANCELADA
                res.estado_pago = PaymentStatus.FALLIDO

                db.commit()

                # NOTIFICAR AL USUARIO
                user = res.user
                if user:
                    UserNotificationService.create_notification(
                        db, user.id, "AUTO_CANCELLED",
                        "Reserva cancelada por falta de pago e ingreso",
                        f"Reserva #{res.id} en {res.sucursal_nombre} fue cancelada porque no se abonó ni se detectó el ingreso del vehículo.",
                        res.id
                    )
                    res_data = {
                        "id": res.id,
                        "sucursal": res.sucursal_nombre,
                        "patente": res.patente,
                        "fecha_inicio": res.fecha_inicio
                    }
                    EmailService.send_auto_cancelled_notification(user.email, user.nombre, res_data)

                logger.info(f"Reserva #{res.id} cancelada automaticamente por falta de pago/ingreso")
            except Exception as e:
                logger.error(f"Cancelando reserva #{res.id}: {e}")
