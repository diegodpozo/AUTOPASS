import threading
import time
from core.database import SessionLocal
from services.reservation_service import ReservationService

class WorkerService:
    @staticmethod
    def start_reservation_cleanup():
        """Inicia el hilo de limpieza de reservas."""
        thread = threading.Thread(target=WorkerService._reservation_cleanup_worker, daemon=True)
        thread.start()
        return thread

    @staticmethod
    def _reservation_cleanup_worker():
        """Hilo de fondo que limpia y finaliza reservas periódicamente."""
        print("[SYSTEM] Hilo de mantenimiento de reservas iniciado.")
        while True:
            try:
                db = SessionLocal()
                # 1. Cancelar impagas que nunca iniciaron
                ReservationService.cleanup_overdue_reservations(db)
                # 2. Finalizar (Completar) reservas cuyo tiempo ya expiró
                ReservationService.auto_finalize_all_reservations(db)
                db.close()
            except Exception as e:
                print(f"[ERROR] En el trabajador de reservas: {e}")
            time.sleep(settings.MAINTENANCE_INTERVAL_SECONDS)
