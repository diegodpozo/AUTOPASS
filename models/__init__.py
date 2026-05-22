from core.database import Base
from .user import User, Vehicle, PointsLog, Promotion
from .reservation import Reservation, Coupon
from .parking import ParkingAforo, Settings, AccessLog

# --- RE-EXPORTACIÓN PARA COMPATIBILIDAD ---
# Esto permite seguir usando 'from models import User'
