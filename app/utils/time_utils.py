from datetime import datetime, timezone
import pytz

IST = pytz.timezone("Asia/Kolkata")

# 🔹 ALWAYS use this for DB + logic (UTC only)
def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

# 🔹 Convert any datetime to IST safely
def to_ist(dt):
    if not dt:
        return None

    if dt.tzinfo is None:
        # assume UTC (DB standard)
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        # normalize first
        dt = dt.astimezone(timezone.utc)

    return dt.astimezone(IST)



# 🔹 FORMAT helper (SAFE DEFAULT)
def format_ist(dt, fmt="%d %b %Y %I:%M %p"):
    try:
        ist_dt = to_ist(dt)
        return ist_dt.strftime(fmt) if ist_dt else ""
    except Exception:
        return ""

# 🔹 Timeago (for UI only)
def timeago_ist(dt):
    if not dt:
        return ""

    dt = to_ist(dt)
    now = datetime.now(IST)

    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return "just now"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"

    hours = seconds // 3600
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"

    days = seconds // 86400
    return f"{days} day{'s' if days != 1 else ''} ago"



# 🔹 Convert IST date (from UI) → UTC range start
def ist_date_to_utc(dt):
    if dt.tzinfo is None:
        dt = IST.localize(dt)

    return dt.astimezone(timezone.utc).replace(tzinfo=None)