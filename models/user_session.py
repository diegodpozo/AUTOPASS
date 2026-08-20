from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
from core.time import utcnow

class UserSession(Base):
    __tablename__ = "user_sessions"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id      = Column(String, nullable=False, index=True)
    user_agent     = Column(String, nullable=True)
    ip_address     = Column(String, nullable=True)
    created_at     = Column(DateTime, default=utcnow)
    last_login_at  = Column(DateTime, default=utcnow, index=True)

    user           = relationship("User", backref="sessions")
