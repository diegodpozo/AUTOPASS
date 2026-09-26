"""Pagos de reservas: abono manual/saldo/Mercado Pago, descuentos por canje, simulación y ejecución de reembolsos."""

import datetime
import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.logger import get_logger
import models
from models.enums import PaymentStatus, ReservationStatus
from repositories.access_log_repository import AccessRepository
from repositories.redemption_repository import RedemptionRepository
from repositories.reservation_repository import ReservationRepository
from services.availability import _liberar_plaza_en_aforo, _reservar_plaza_en_aforo

logger = get_logger("Payments")
from services.billing_service import BillingService
from services.branch_service import BranchService
from services.email_service import EmailService
from services.time_service import TimeService
from repositories.reservation_repository import ReservationRepository


class ReservationPaymentsMixin:

    @staticmethod
    def get_available_redemption_discounts(db: Session, user_id: int, sucursal: str = None):
        """LISTA LOS DESCUENTOS DE RESERVA (%) VIGENTES DE UN USUARIO APLICABLES A UNA SUCURSAL.
        Se usa en caja (admin) para detectar el descuento que corresponde aplicar al cobrar.
        Si no hay usuario vinculado, devuelve lista vacía."""
        if not user_id:
            return []
        return RedemptionRepository.list_discounts_by_user(db, user_id, sucursal)

    @staticmethod
    def pay_reservation_manual(db: Session, res: "models.Reservation", metodo_pago: str = None, redemption_ticket_id: int = None):
        """MARCA UNA RESERVA COMO PAGADA (PAGO MANUAL ADMIN) SIN DESCONTAR SALDO NI USAR MERCADO PAGO.
        Si se indica un redemption_ticket_id (descuento % de reserva) vigente del usuario
        y de la misma sucursal (o global) se aplica el descuento sobre el monto total
        y la reserva queda pagada por el valor final descontado."""
        if res.estado_pago == PaymentStatus.PAGADO:
            return {"status": "ok", "message": "La reserva ya se encuentra pagada", "monto": res.monto_total, "monto_a_cobrar": res.monto_total, "descuento": 0.0, "metodo_pago": res.metodo_pago}

        # --- APLICAR DESCUENTO POR CANJE (% de descuento en estacionamiento) ---
        descuento = 0.0
        monto_a_cobrar = res.monto_total or 0.0
        if redemption_ticket_id:
            if not res.user_id:
                raise HTTPException(status_code=400, detail="La reserva no tiene un usuario vinculado para aplicar el descuento")
            ticket_redencion = ReservationPaymentsMixin.validate_redemption_ticket(db, res.user_id, redemption_ticket_id, res.sucursal_nombre)
            porc = ticket_redencion.valor_descuento or 0
            descuento = round(monto_a_cobrar * porc / 100.0, 2)
            monto_a_cobrar = round(monto_a_cobrar - descuento, 2)
            res.monto_total = monto_a_cobrar
            res.monto_reembolsado = 0.0
            ticket_redencion.estado = "USADO"
            ticket_redencion.fecha_uso = datetime.datetime.now().isoformat()
            ticket_redencion.reserva_id = res.id

        res.estado_pago = PaymentStatus.PAGADO
        res.estado_reserva = ReservationStatus.ACTIVA
        res.fecha_pago = datetime.datetime.now().isoformat()
        res.metodo_pago = metodo_pago

        if res.user:
            puntos_ganados = BillingService.calculate_points(monto_a_cobrar)
            res.user.puntos_acumulados += puntos_ganados
            db.add(models.PointsLog(
                user_id=res.user.id,
                cantidad=puntos_ganados,
                motivo=f"Abono Manual Reserva: {res.patente}",
                fecha=datetime.datetime.now().isoformat()
            ))
            if puntos_ganados > 0:
                try:
                    from services.user_notification_service import UserNotificationService
                    UserNotificationService.create_notification(
                        db, res.user.id,
                        tipo=models.NotificationType.POINTS_EARNED,
                        titulo="¡Puntos AutoPass!",
                        mensaje=f"¡Ganaste {puntos_ganados} puntos por abonar la reserva #{res.id} ({res.patente})!",
                        reserva_id=res.id
                    )
                except Exception:
                    logger.warning(f"[PAYMENTS] Error notificando puntos ganados en reserva #{res.id}", exc_info=True)

        db.commit()
        db.refresh(res)
        return {"status": "ok", "message": "Pago registrado", "monto": res.monto_total, "monto_a_cobrar": monto_a_cobrar, "descuento": descuento, "metodo_pago": res.metodo_pago}

    @staticmethod
    def redemption_sucursal_clause(sucursal):
        """CLÁUSULA DE FILTRADO DE REDEMPTION TICKET POR SUCURSAL (delegada al repositorio)."""
        return RedemptionRepository.redemption_sucursal_clause(sucursal)

    @staticmethod
    def validate_redemption_ticket(db: Session, user_id: int, redemption_ticket_id: int, sucursal: str = None) -> models.RedemptionTicket:
        """Valida y obtiene un ticket de descuento por canje para un usuario y sucursal."""
        if not redemption_ticket_id:
            return None
        ticket = RedemptionRepository.get_valid_discount(db, redemption_ticket_id, user_id, sucursal)
        if not ticket:
            raise HTTPException(status_code=400, detail="El descuento seleccionado no es válido para esta reserva o sucursal")
        return ticket

    @staticmethod
    def pay_reservation(db: Session, user: models.User, res_id: int, redemption_ticket_id: int = None):
        """ABONA UNA RESERVA UTILIZANDO EL SALDO DISPONIBLE DEL USUARIO.
        Si se indica un redemption_ticket_id (descuento % de reserva) vigente del usuario
        y de la misma sucursal (o global), se aplica el descuento sobre el monto total
        y el resto se paga con saldo."""
        res = ReservationRepository.get_by_user_and_id(db, user.id, res_id)

        if not res:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")

        if res.estado_reserva in [ReservationStatus.CANCELADA, ReservationStatus.COMPLETADA]:
            raise HTTPException(status_code=400, detail=f"No se puede abonar una reserva en estado '{res.estado_reserva}'")

        if res.estado_pago == PaymentStatus.PAGADO:
            return {"status": "ok", "message": "La reserva ya ha sido abonada"}

        # --- APLICAR DESCUENTO POR CANJE (% de descuento en estacionamiento) ---
        descuento = 0.0
        ticket_redencion = None
        monto_a_cobrar = res.monto_total

        if redemption_ticket_id:
            ticket_redencion = ReservationPaymentsMixin.validate_redemption_ticket(db, user.id, redemption_ticket_id, res.sucursal_nombre)
            porc = ticket_redencion.valor_descuento or 0
            descuento = round(res.monto_total * porc / 100.0, 2)
            monto_a_cobrar = round(res.monto_total - descuento, 2)

        if user.saldo < monto_a_cobrar:
            raise HTTPException(status_code=400, detail=f"Saldo insuficiente en su cuenta AutoPass (necesita ${monto_a_cobrar:,.2f})")

        # DEDUCCION DE SALDO Y ACTUALIZACION DE ESTADO
        user.saldo -= monto_a_cobrar
        res.estado_pago = PaymentStatus.PAGADO
        res.estado_reserva = ReservationStatus.ACTIVA
        res.fecha_pago = datetime.datetime.now().isoformat()
        res.metodo_pago = "SALDO"
        # SI SE APLICO DESCUENTO, LA RESERVA QUEDA CON SU VALOR FINAL
        if ticket_redencion:
            res.monto_total = monto_a_cobrar
            res.monto_reembolsado = 0.0

        # ACREDITACION DE PUNTOS POR LEALTAD (SOBRE LO EFECTIVAMENTE ABONADO)
        puntos_ganados = BillingService.calculate_points(monto_a_cobrar)
        user.puntos_acumulados += puntos_ganados

        db.add(models.PointsLog(
            user_id=user.id,
            cantidad=puntos_ganados,
            motivo=f"Reserva: {res.patente}",
            fecha=datetime.datetime.now().isoformat()
        ))

        # MARCAR EL TICKET DE DESCUENTO COMO USADO (si aplico descuento)
        if ticket_redencion:
            ticket_redencion.estado = "USADO"
            ticket_redencion.fecha_uso = datetime.datetime.now().isoformat()
            ticket_redencion.reserva_id = res.id

        db.commit()

        # RESERVAR PLAZA EN AFORO PARA RESERVAS NO HORARIAS (DIA/SEMANA/QUINCENA/MES)
        # SOLO SI LA RESERVA YA COMENZO; SI ES FUTURA, LO HARA EL WORKER AL INICIAR
        if res.tipo_estadia != "hora" and res.sucursal_nombre:
            now_str = TimeService.now_str()
            if res.fecha_inicio <= now_str:
                _reservar_plaza_en_aforo(db, res)

        # ENVIAR MAIL DE CONFIRMACION
        dir_info = res.sucursal_info
        if not dir_info or dir_info == "Sede no especificada." or dir_info.startswith("Sede no especificada"):
            dir_info = BranchService.get_branch_info_str(db, res.sucursal_nombre)
        res_info = {
            "id": res.id,
            "sucursal": res.sucursal_nombre,
            "direccion": dir_info,
            "patente": res.patente,
            "fecha_inicio": res.fecha_inicio,
            "fecha_fin": res.fecha_fin,
            "costo": res.monto_total
        }
        EmailService.send_reservation_confirmation(user.email, user.nombre, res_info)

        try:
            from services.user_notification_service import UserNotificationService
            UserNotificationService.create_notification(
                db, user.id, "RESERVATION_CONFIRMED",
                f"Reserva #{res.id} confirmada",
                f"Se abonó con éxito tu reserva en {res.sucursal_nombre} por ${res.monto_total:,.2f}.",
                res.id
            )
            if puntos_ganados > 0:
                UserNotificationService.create_notification(
                    db, user.id, "POINTS_EARNED",
                    "¡Puntos AutoPass!",
                    f"¡Ganaste {puntos_ganados} puntos por abonar la reserva #{res.id} ({res.patente}).",
                    res.id
                )
        except Exception as e:
            print(f"[ERROR NOTIF] No se pudo notificar pago de reserva: {e}")

        return {"status": "ok", "message": "Reserva abonada con éxito", "puntos_ganados": puntos_ganados}

    @staticmethod
    def pay_reservation_mp(db: Session, user: models.User, res: models.Reservation, monto_a_cobrar: float, redemption_ticket_id: int = None):
        """MARCA UNA RESERVA COMO PAGADA POR MERCADO PAGO (CHECKOUT PRO) SIN DESCONTAR SALDO.
        El monto confirmado por Mercado Pago ya incluye el descuento por canje si correspondía."""
        if res.estado_reserva in [ReservationStatus.CANCELADA, ReservationStatus.COMPLETADA]:
            raise HTTPException(status_code=400, detail=f"No se puede abonar una reserva en estado '{res.estado_reserva}'")

        if res.estado_pago == PaymentStatus.PAGADO:
            return {"status": "ok", "message": "La reserva ya ha sido abonada", "aplicado": False}

        # VALIDAR Y CONSUMIR DESCUENTO POR CANJE (si aplicó)
        ticket_redencion = None
        if redemption_ticket_id:
            ticket_redencion = ReservationPaymentsMixin.validate_redemption_ticket(db, user.id, redemption_ticket_id, res.sucursal_nombre)

        # ACTUALIZACION DE ESTADO
        res.estado_pago = PaymentStatus.PAGADO
        res.estado_reserva = ReservationStatus.ACTIVA
        res.fecha_pago = datetime.datetime.now().isoformat()
        res.metodo_pago = "MERCADOPAGO"
        if ticket_redencion:
            res.monto_total = monto_a_cobrar
            res.monto_reembolsado = 0.0
            ticket_redencion.estado = "USADO"
            ticket_redencion.fecha_uso = datetime.datetime.now().isoformat()
            ticket_redencion.reserva_id = res.id

        # ACREDITACION DE PUNTOS POR LEALTAD (SOBRE LO EFECTIVAMENTE ABONADO)
        puntos_ganados = BillingService.calculate_points(monto_a_cobrar)
        user.puntos_acumulados += puntos_ganados

        db.add(models.PointsLog(
            user_id=user.id,
            cantidad=puntos_ganados,
            motivo=f"Reserva (Mercado Pago): {res.patente}",
            fecha=datetime.datetime.now().isoformat()
        ))

        db.commit()

        # RESERVAR PLAZA EN AFORO PARA RESERVAS NO HORARIAS YA INICIADAS (NO-OP desde v9.5)
        if res.tipo_estadia != "hora" and res.sucursal_nombre:
            now_str = TimeService.now_str()
            if res.fecha_inicio <= now_str:
                _reservar_plaza_en_aforo(db, res)

        # ENVIAR MAIL DE CONFIRMACION
        dir_info = res.sucursal_info
        if not dir_info or dir_info == "Sede no especificada." or dir_info.startswith("Sede no especificada"):
            dir_info = BranchService.get_branch_info_str(db, res.sucursal_nombre)
        res_info = {
            "id": res.id,
            "sucursal": res.sucursal_nombre,
            "direccion": dir_info,
            "patente": res.patente,
            "fecha_inicio": res.fecha_inicio,
            "fecha_fin": res.fecha_fin,
            "costo": res.monto_total
        }
        EmailService.send_reservation_confirmation(user.email, user.nombre, res_info)

        try:
            from services.user_notification_service import UserNotificationService
            UserNotificationService.create_notification(
                db, user.id, "RESERVATION_CONFIRMED",
                f"Reserva #{res.id} confirmada",
                f"Se abonó con Mercado Pago tu reserva en {res.sucursal_nombre} por ${res.monto_total:,.2f}.",
                res.id
            )
            if puntos_ganados > 0:
                UserNotificationService.create_notification(
                    db, user.id, "POINTS_EARNED",
                    "¡Puntos AutoPass!",
                    f"¡Ganaste {puntos_ganados} puntos por abonar la reserva #{res.id} ({res.patente}).",
                    res.id
                )
        except Exception as e:
            print(f"[ERROR NOTIF] No se pudo notificar pago de reserva MP: {e}")

        return {"status": "ok", "message": "Reserva abonada con éxito", "puntos_ganados": puntos_ganados, "aplicado": True}

    @staticmethod
    def simulate_refund(db: Session, res: models.Reservation):
        """CALCULA EL REEMBOLSO POTENCIAL SIN EJECUTAR LA CANCELACION."""
        # 1. VERIFICACION DE PRESENCIA FISICA
        norm_pat = re.sub(r'[^A-Z0-9]', '', (res.patente or '').upper())
        vinc_log = AccessRepository.get_last_entry(db, norm_pat, res.sucursal_nombre)

        es_presencial = False
        if vinc_log:
            salida = AccessRepository.get_exit_after(db, vinc_log.patente_detectada, vinc_log.id, vinc_log.sucursal)
            if not salida:
                es_presencial = True

        if es_presencial:
            return {"reembolso": 0.0, "error": "Vehículo en el predio"}

        # 2. CALCULO DE REEMBOLSO
        monto_a_reembolsar = 0.0
        if res.estado_pago == PaymentStatus.PAGADO:
            now = datetime.datetime.now()
            start = datetime.datetime.fromisoformat(res.fecha_inicio)
            end = datetime.datetime.fromisoformat(res.fecha_fin)

            if now < start:
                monto_a_reembolsar = res.monto_total
            elif now > end:
                monto_a_reembolsar = 0.0
            else:
                if res.tipo_estadia == "hora" and vinc_log:
                    monto_a_reembolsar = 0.0
                else:
                    duracion_total = (end - start).total_seconds()
                    tiempo_restante = (end - now).total_seconds()
                    if duracion_total > 0:
                        porcentaje_restante = max(0, tiempo_restante / duracion_total)
                        monto_a_reembolsar = round(res.monto_total * porcentaje_restante, 2)

        return {"reembolso": monto_a_reembolsar, "error": None}

    @staticmethod
    def cancel_reservation(db: Session, user: models.User, res_id: int):
        """CANCELA UNA RESERVA Y GESTIONA REEMBOLSOS PROPORCIONALES."""
        res = ReservationRepository.get_by_id(db, res_id)

        if not res:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")

        if res.estado_reserva == ReservationStatus.CANCELADA:
            return {"status": "ok", "message": "La reserva ya se encuentra cancelada"}

        if res.estado_reserva == ReservationStatus.COMPLETADA:
            return {"status": "error", "message": "La reserva ya finalizó y no puede cancelarse"}

        # USAMOS LA SIMULACION PARA OBTENER EL MONTO
        sim = ReservationPaymentsMixin.simulate_refund(db, res)
        if sim["error"]:
            raise HTTPException(status_code=400, detail=sim["error"])

        monto_a_reembolsar = sim["reembolso"]

        # 3. EJECUCION DEL REEMBOLSO
        target_user = user or res.user
        if monto_a_reembolsar > 0 and target_user:
            target_user.saldo += monto_a_reembolsar

            # AJUSTE DE PUNTOS (SOLO SOBRE LO REEMBOLSADO)
            puntos_a_descontar = BillingService.calculate_points(monto_a_reembolsar)
            target_user.puntos_acumulados = max(0, target_user.puntos_acumulados - puntos_a_descontar)

            db.add(models.PointsLog(
                user_id=target_user.id,
                cantidad=-puntos_a_descontar,
                motivo=f"Reembolso por Cancelación (Proporcional): {res.patente}",
                fecha=datetime.datetime.now().isoformat()
            ))

        res.estado_reserva = ReservationStatus.CANCELADA
        res.estado_pago = PaymentStatus.REEMBOLSADO if monto_a_reembolsar > 0 else PaymentStatus.CANCELADO
        res.monto_reembolsado = float(monto_a_reembolsar)

        if monto_a_reembolsar > 0:
            res.fecha_pago = datetime.datetime.now().isoformat()

        db.commit()

        if res.tipo_estadia != "hora" and res.sucursal_nombre:
            _liberar_plaza_en_aforo(db, res)

        msg = f"Reserva cancelada. Reembolso: ${monto_a_reembolsar}" if monto_a_reembolsar > 0 else "Reserva cancelada sin reembolso."

        try:
            from services.user_notification_service import UserNotificationService
            if target_user:
                notif_msg = f"Tu reserva #{res.id} en {res.sucursal_nombre} fue cancelada."
                if monto_a_reembolsar > 0:
                    notif_msg += f" Se reembolsaron ${monto_a_reembolsar:,.2f} a tu saldo."
                UserNotificationService.create_notification(
                    db, target_user.id, "RESERVATION_CANCELLED",
                    f"Reserva #{res.id} cancelada",
                    notif_msg,
                    res.id
                )
        except Exception as e:
            print(f"[ERROR NOTIF] No se pudo notificar cancelacion de reserva: {e}")

        return {"status": "ok", "message": msg, "reembolso": monto_a_reembolsar}