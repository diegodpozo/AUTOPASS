import datetime
import pytest
from services.time_service import TimeService

def test_time_service_advance_and_rewind():
    TimeService.reset()
    assert TimeService.get_offset() == 0

    # Advance 1 hour (3600 seconds)
    TimeService.advance(hours=1)
    assert TimeService.get_offset() == 3600

    # Rewind 30 minutes (1800 seconds)
    TimeService.rewind(minutes=30)
    assert TimeService.get_offset() == 1800

    info = TimeService.get_info()
    assert info["offset_seconds"] == 1800
    assert info["active"] is True
    assert "+0h 30m" in info["offset_formatted"]

    # Reset
    TimeService.reset()
    assert TimeService.get_offset() == 0
    assert TimeService.is_active() is False

def test_time_service_set_target_datetime():
    TimeService.reset()
    target_dt = datetime.datetime.now() + datetime.timedelta(days=2, hours=3)
    TimeService.set_target_datetime(target_dt)

    # Offset should be roughly 2 days + 3 hours = 183600 seconds (+- 2s)
    offset = TimeService.get_offset()
    assert 183590 <= offset <= 183610

    info = TimeService.get_info()
    assert info["active"] is True
    assert "+2d 3h" in info["offset_formatted"] or "+2d 2h 59m" in info["offset_formatted"]

    TimeService.reset()
    assert TimeService.get_offset() == 0
