from core.database import Base
from .user import User, Vehicle, PointsLog, Promotion, RedemptionTicket
from .reservation import Reservation, Coupon
from .parking import ParkingAforo, Settings, AccessLog, ParkingBranch, ParkingFloor, ParkingCamera
from .notification import UserNotification
from .user_session import UserSession
from .support import SupportTicket, SupportTicketMessage
from .mercadopago import MercadoPagoPayment

# --- RE-EXPORTACION PARA COMPATIBILIDAD ---
# ESTO PERMITE SEGUIR USANDO 'FROM MODELS IMPORT USER'
