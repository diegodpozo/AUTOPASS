from core.database import Base
from .organization import Organization
from .user import User, Vehicle, PointsLog, Promotion, RedemptionTicket
from .reservation import Reservation
from .parking import ParkingAforo, Settings, AccessLog, ParkingBranch, ParkingFloor, ParkingCamera
from .notification import UserNotification
from .user_session import UserSession
from .support import SupportTicket, SupportTicketMessage
from .mercadopago import MercadoPagoPayment
from .enums import NotificationType

# TRADUCTOR CENTRAL NOMBRE->ID DE SEDE (el nombre vive solo en parking_branches)
from .branch_ref import register_branch_linked

register_branch_linked(
    User, Reservation, AccessLog, SupportTicket, RedemptionTicket,
    ParkingAforo, Settings, ParkingCamera, Promotion,
)

# --- RE-EXPORTACION PARA COMPATIBILIDAD ---
# ESTO PERMITE SEGUIR USANDO 'FROM MODELS IMPORT USER'
