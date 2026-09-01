from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
from core.time import localnow

class UserNotification(Base):
    __tablename__ = "user_notifications"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tipo           = Column(String, nullable=False)        # 'REMINDER_PAID', 'REMINDER_UNPAID', 'AUTO_CANCELLED'
    titulo         = Column(String, nullable=False)
    mensaje        = Column(String, nullable=False)
    leido          = Column(Boolean, default=False)
    reserva_id     = Column(Integer, ForeignKey("reservations.id"), nullable=True)
    ticket_id      = Column(Integer, ForeignKey("support_tickets.id"), nullable=True)
    created_at     = Column(DateTime, default=localnow)

    user           = relationship("User", backref="notifications")
    reserva        = relationship("Reservation", backref="notifications")
    ticket         = relationship("SupportTicket", backref="notifications")
