import threading
import time
from core.database import SessionLocal
from core.config import settings
from services.reservation_service import ReservationService

class WorkerService:
    @staticmethod
    def start_reservation_cleanup():
        """INICIA EL HILO DE LIMPIEZA DE RESERVAS."""
        thread = threading.Thread(target=WorkerService._reservation_cleanup_worker, daemon=True)
        thread.start()
        return thread

    @staticmethod
    def _reservation_cleanup_worker():
        """HILO DE FONDO QUE LIMPIA Y FINALIZA RESERVAS PERIODICAMENTE."""
        print("[SYSTEM] Hilo de mantenimiento de reservas iniciado.")
        while True:
            try:
                db = SessionLocal()
                # 1. CANCELAR IMPAGAS QUE NUNCA INICIARON
                ReservationService.cleanup_overdue_reservations(db)
                # 2. FINALIZAR (COMPLETAR) RESERVAS CUYO TIEMPO YA EXPIRO
                ReservationService.auto_finalize_all_reservations(db)
                db.close()
            except Exception as e:
                print(f"[ERROR] En el trabajador de reservas: {e}")
            time.sleep(settings.MAINTENANCE_INTERVAL_SECONDS)
