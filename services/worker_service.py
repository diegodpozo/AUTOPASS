import threading
import time
import datetime
from core.database import SessionLocal
from core.config import settings
from services.reservation_service import ReservationService
from services.user_notification_service import UserNotificationService
from services.email_service import EmailService
from services.time_service import TimeService
import models
from models.enums import PaymentStatus, ReservationStatus, AccessEventType

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
        """HILO DE FONDO QUE LIMPIA Y FINALIZA RESERVAS PERIODICAMENTE."""
        print("[SYSTEM] Hilo de mantenimiento de reservas iniciado.")
        while True:
            db = None
            try:
                db = SessionLocal()
                ReservationService.cleanup_overdue_reservations(db)
                ReservationService.auto_finalize_all_reservations(db)
            except Exception as e:
                print(f"[ERROR] En el trabajador de reservas: {e}")
            finally:
                if db:
                    try:
                        db.close()
                    except Exception:
                        pass
            time.sleep(settings.MAINTENANCE_INTERVAL_SECONDS)

    @staticmethod
    def _notification_worker():
        """HILO DE FONDO QUE MANEJA RECORDATORIOS Y CANCELACION AUTOMATICA."""
        print("[SYSTEM] Hilo de notificaciones de reservas iniciado.")
        while True:
            db = None
            try:
                db = SessionLocal()
                WorkerService._process_reminders(db)
                WorkerService._process_started_reservations(db)
                WorkerService._process_auto_cancellations(db)
            except Exception as e:
                print(f"[ERROR] En el trabajador de notificaciones: {e}")
            finally:
                if db:
                    try:
                        db.close()
                    except Exception:
                        pass
            time.sleep(NOTIFICATION_CHECK_INTERVAL)

    @staticmethod
    def _process_reminders(db):
        """ENVIA RECORDATORIOS A RESERVAS QUE FALTAN HASTA 31 MIN PARA INICIAR."""
        now = TimeService.now()
        corte = now + datetime.timedelta(minutes=31)
        fmt_corte = corte.strftime("%Y-%m-%d %H:%M")
        fmt_ahora = now.strftime("%Y-%m-%d %H:%M")

        candidatas = db.query(models.Reservation).filter(
            models.Reservation.estado_reserva == ReservationStatus.PENDIENTE,
            models.Reservation.fecha_inicio >= fmt_ahora,
            models.Reservation.fecha_inicio <= fmt_corte,
            models.Reservation.recordatorio_confirmado == False
        ).all()

        for res in candidatas:
            try:
                user = res.user
                if not user or not user.email:
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
                print(f"[NOTIF] Recordatorio enviado a {user.email} para reserva #{res.id}")
            except Exception as e:
                print(f"[ERROR NOTIF] Procesando recordatorio reserva #{res.id}: {e}")

    @staticmethod
    def _process_started_reservations(db):
        """PASA A ACTIVA LAS RESERVAS PAGADAS CUYO HORARIO INICIO, NOTIFICA EN AMBOS CASOS."""
        now_str = TimeService.now_str()
        iniciadas = db.query(models.Reservation).filter(
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA]),
            models.Reservation.fecha_inicio <= now_str,
            models.Reservation.fecha_fin >= now_str
        ).all()

        for res in iniciadas:
            try:
                notif_existente = db.query(models.UserNotification).filter(
                    models.UserNotification.reserva_id == res.id,
                    models.UserNotification.tipo == "RESERVATION_STARTED"
                ).first()
                if notif_existente:
                    continue

                user = res.user
                if not user:
                    continue

                pagada = res.estado_pago == PaymentStatus.PAGADO

                # PASAR A ACTIVA SI SIGUE PENDIENTE (ESTE PAGA O NO)
                if res.estado_reserva == ReservationStatus.PENDIENTE:
                    res.estado_reserva = ReservationStatus.ACTIVA
                    db.commit()

                # RESERVAR PLAZA EN AFORO PARA RESERVAS NO HORARIAS PAGADAS QUE INICIAN AHORA
                if pagada and res.tipo_estadia != "hora" and res.sucursal_nombre:
                    from services.reservation_service import _reservar_plaza_en_aforo
                    _reservar_plaza_en_aforo(db, res)

                titulo = "Tu reserva ya comenzó!"
                mensaje = f"Reserva #{res.id} en {res.sucursal_nombre} - Patente {res.patente}. "
                if pagada:
                    mensaje += "Presentá tu QR en la entrada."
                else:
                    mensaje += "Aboná para evitar la cancelación automática."

                UserNotificationService.create_notification(
                    db, user.id, "RESERVATION_STARTED", titulo, mensaje, res.id
                )
                print(f"[NOTIF] Aviso de inicio enviado para reserva #{res.id}")
            except Exception as e:
                print(f"[ERROR NOTIF] Procesando inicio de reserva #{res.id}: {e}")

    @staticmethod
    def _process_auto_cancellations(db):
        """CANCELA AUTOMATICAMENTE RESERVAS IMPAGAS 30 MIN DESPUES DEL INICIO SIN INGRESO."""
        now = TimeService.now()
        grace = now - datetime.timedelta(minutes=30)
        fmt_grace = grace.strftime("%Y-%m-%d %H:%M")

        candidatas = db.query(models.Reservation).filter(
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA]),
            models.Reservation.estado_pago == PaymentStatus.PENDIENTE,
            models.Reservation.fecha_inicio < fmt_grace
        ).all()

        for res in candidatas:
            try:
                # VERIFICAR SI EL VEHICULO INGRESO
                entry = db.query(models.AccessLog).filter(
                    models.AccessLog.reserva_id == res.id,
                    models.AccessLog.tipo_evento == AccessEventType.ENTRADA
                ).first()

                if entry:
                    continue  # YA INGRESO, NO CANCELAR

                # CANCELAR LA RESERVA
                res.estado_reserva = ReservationStatus.CANCELADA
                res.estado_pago = PaymentStatus.FALLIDO

                # LIBERAR PLAZA EN AFORO SI ES NO HORARIA
                if res.tipo_estadia != "hora" and res.sucursal_nombre:
                    from services.reservation_service import _liberar_plaza_en_aforo
                    _liberar_plaza_en_aforo(db, res)

                db.commit()

                # NOTIFICAR AL USUARIO
                user = db.query(models.User).filter(models.User.id == res.user_id).first()
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

                print(f"[NOTIF] Reserva #{res.id} cancelada automaticamente por falta de pago/ingreso")
            except Exception as e:
                print(f"[ERROR NOTIF] Cancelando reserva #{res.id}: {e}")
