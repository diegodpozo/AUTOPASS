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
        """Hilo de fondo que limpia reservas impagas periódicamente."""
        print("[SYSTEM] Limpiador de reservas automáticas iniciado.")
        while True:
            try:
                db = SessionLocal()
                ReservationService.cleanup_overdue_reservations(db)
                db.close()
            except Exception as e:
                print(f"[ERROR] En el limpiador de reservas: {e}")
            time.sleep(300) # Ejecutar cada 5 minutos
