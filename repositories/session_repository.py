from sqlalchemy.orm import Session

import models

#--- REPOSITORIO DE SESIONES DE USUARIO (MULTIDISPOSITIVO) ---


class SessionRepository:
    @staticmethod
    def get_by_device(db: Session, user_id: int, device_id: str) -> models.UserSession:
        """SESION DEL USUARIO EN UN DISPOSITIVO ESPECIFICO."""
        return db.query(models.UserSession).filter(
            models.UserSession.user_id == user_id,
            models.UserSession.device_id == device_id
        ).first()

    @staticmethod
    def get_recent_by_user_agent(db: Session, user_id: int, user_agent: str, since: object) -> models.UserSession:
        """SESION MAS RECIENTE DEL USUARIO CON MISMO NAVEGADOR (USER-AGENT) DENTRO DE LA VENTANA."""
        return (
            db.query(models.UserSession)
            .filter(
                models.UserSession.user_id == user_id,
                models.UserSession.user_agent == user_agent,
                models.UserSession.last_login_at >= since
            )
            .order_by(models.UserSession.last_login_at.desc())
            .first()
        )

    @staticmethod
    def count_other_devices(db: Session, user_id: int, device_id: str, since: object, user_agent: str = None) -> int:
        """CANTIDAD DE OTROS DISPOSITIVOS CON SESION ACTIVA, IGNORANDO EL MISMO NAVEGADOR."""
        q = db.query(models.UserSession.device_id).filter(
            models.UserSession.user_id == user_id,
            models.UserSession.device_id != device_id,
            models.UserSession.last_login_at >= since
        )
        if user_agent:
            q = q.filter(models.UserSession.user_agent != user_agent)
        return q.distinct().count()