import json
import os
import datetime

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
        except Exception:
            cls._offset_seconds = 0

    @classmethod
    def _save_offset(cls):
        os.makedirs(os.path.dirname(_VIRTUAL_TIME_FILE), exist_ok=True)
        with open(_VIRTUAL_TIME_FILE, "w") as f:
            json.dump({"offset_seconds": cls._offset_seconds}, f)

    @classmethod
    def now(cls):
        cls._load_offset()
        return datetime.datetime.now() + datetime.timedelta(seconds=cls._offset_seconds)

    @classmethod
    def now_str(cls):
        return cls.now().strftime("%Y-%m-%d %H:%M")

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
        return {
            "offset_seconds": cls.get_offset(),
            "real_now": datetime.datetime.now().isoformat(),
            "virtual_now": cls.now().isoformat(),
            "active": cls.is_active(),
        }
