from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from core.database import Base
import datetime

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    categoria   = Column(String, nullable=False)
    sucursal    = Column(String, default="General", index=True)
    asunto      = Column(String, nullable=False)
    mensaje     = Column(Text, nullable=False)
    estado      = Column(String, default="Pendiente", index=True)
    respuesta      = Column(Text, nullable=True)
    user_response  = Column(Text, nullable=True)
    created_at     = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user        = relationship("User", backref="tickets")


class SupportTicketMessage(Base):
    __tablename__ = "support_ticket_messages"

    id          = Column(Integer, primary_key=True, index=True)
    ticket_id   = Column(Integer, ForeignKey("support_tickets.id"), nullable=False, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    mensaje     = Column(Text, nullable=False)
    created_at  = Column(DateTime, default=datetime.datetime.utcnow)

    ticket      = relationship("SupportTicket", backref="messages")
    user        = relationship("User")
