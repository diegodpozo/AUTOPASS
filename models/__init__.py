from core.database import Base
from .user import User, Vehicle, PointsLog, Promotion
from .reservation import Reservation, Coupon
from .parking import ParkingAforo, Settings, AccessLog, ParkingBranch, ParkingFloor, ParkingCamera
from .notification import UserNotification
from .support import SupportTicket

# --- RE-EXPORTACION PARA COMPATIBILIDAD ---
# ESTO PERMITE SEGUIR USANDO 'FROM MODELS IMPORT USER'
