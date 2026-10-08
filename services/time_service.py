import json
import os
import datetime
from core.logger import get_logger

logger = get_logger("TimeService")

_VIRTUAL_TIME_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "virtual_time_offset.json")

class TimeService:
    _offset_seconds = 0

    @classmethod
    def _load_offset(cls):
        try:
            if os.path.exists(_VIRTUAL_TIME_FILE):
                with open(_VIRTUAL_TIME_FILE) as f:
                    cls._offset_seconds = json.load(f).get("offset_seconds", 0)
            else:
                cls._offset_seconds = 0
        except Exception as e:
            logger.warn(f"No se pudo cargar offset de tiempo virtual: {e}")
            cls._offset_seconds = 0

    @classmethod
    def _save_offset(cls):
        try:
            os.makedirs(os.path.dirname(_VIRTUAL_TIME_FILE), exist_ok=True)
            with open(_VIRTUAL_TIME_FILE, "w") as f:
                json.dump({"offset_seconds": cls._offset_seconds}, f)
        except Exception as e:
            logger.error(f"No se pudo guardar offset de tiempo virtual: {e}")

    @classmethod
    def now(cls):
        cls._load_offset()
        return datetime.datetime.now() + datetime.timedelta(seconds=cls._offset_seconds)

    @classmethod
    def now_str(cls):
        return cls.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def set_offset(cls, seconds: int):
        cls._offset_seconds = seconds
        cls._save_offset()

    @classmethod
    def advance(cls, **kwargs):
        td = datetime.timedelta(**kwargs)
        cls._offset_seconds += int(td.total_seconds())
        cls._save_offset()

    @classmethod
    def rewind(cls, **kwargs):
        """RETRASAR EL TIEMPO VIRTUAL SEGUN DIAS, HORAS O MINUTOS."""
        td = datetime.timedelta(**kwargs)
        cls._offset_seconds -= int(td.total_seconds())
        cls._save_offset()

    @classmethod
    def set_target_datetime(cls, target_dt: datetime.datetime):
        """FIJAR EL TIEMPO VIRTUAL A UNA FECHA/HORA EXACTA."""
        real_now = datetime.datetime.now()
        diff = target_dt - real_now
        cls._offset_seconds = int(diff.total_seconds())
        cls._save_offset()

    @classmethod
    def reset(cls):
        cls.set_offset(0)

    @classmethod
    def get_offset(cls):
        cls._load_offset()
        return cls._offset_seconds

    @classmethod
    def get_virtual_now(cls):
        cls._load_offset()
        return cls.now()

    @classmethod
    def is_active(cls):
        return cls.get_offset() != 0

    @classmethod
    def get_info(cls):
        off = cls.get_offset()
        abs_off = abs(off)
        h = abs_off // 3600
        m = (abs_off % 3600) // 60
        d = h // 24
        rh = h % 24
        sign = "+" if off >= 0 else "-"
        fmt_offset = "0h 0m" if off == 0 else f"{sign}{f'{d}d ' if d > 0 else ''}{rh}h {m}m"

        return {
            "offset_seconds": off,
            "offset_formatted": fmt_offset,
            "real_now": datetime.datetime.now().isoformat(),
            "virtual_now": cls.now().isoformat(),
            "virtual_now_formatted": cls.now().strftime("%d/%m/%Y %H:%M:%S"),
            "active": cls.is_active(),
        }
