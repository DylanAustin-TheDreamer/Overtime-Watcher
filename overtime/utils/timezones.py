from zoneinfo import available_timezones, ZoneInfo
from datetime import datetime, timezone


def timezone_choices():
    """Return a list of (zone_name, label) pairs sorted by offset then name.
    Labels include the current UTC offset so users can pick easier.
    """
    now_utc = datetime.now(timezone.utc)
    zones = []
    for name in sorted(available_timezones()):
        try:
            tz = ZoneInfo(name)
            offset = now_utc.astimezone(tz).utcoffset() or timezone.utc.utcoffset(now_utc)
            total_minutes = int(offset.total_seconds() // 60)
            sign = '+' if total_minutes >= 0 else '-'
            hh = abs(total_minutes) // 60
            mm = abs(total_minutes) % 60
            label = f"UTC{sign}{hh:02d}:{mm:02d} — {name}"
            zones.append((total_minutes, name, label))
        except Exception:
            continue

    zones.sort(key=lambda x: (x[0], x[1]))
    return [(name, label) for (_, name, label) in zones]
from zoneinfo import available_timezones, ZoneInfo
from datetime import datetime, timezone

def timezone_choices():
    now_utc = datetime.now(timezone.utc)
    zones = []
    for name in sorted(available_timezones()):
        try:
            tz = ZoneInfo(name)
            offset = now_utc.astimezone(tz).utcoffset() or timezone.utc.utcoffset(now_utc)
            total_minutes = int(offset.total_seconds() // 60)
            sign = '+' if total_minutes >= 0 else '-'
            hh = abs(total_minutes) // 60
            mm = abs(total_minutes) % 60
            label = f"UTC{sign}{hh:02d}:{mm:02d} — {name}"
            zones.append((name, label))
        except Exception:
            continue
    return zones