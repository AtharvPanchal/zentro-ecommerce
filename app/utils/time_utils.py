from datetime import datetime, timezone
import pytz

IST = pytz.timezone("Asia/Kolkata")

# 🔹 ALWAYS use this for DB + logic (UTC only)
def utc_now():
    # ALWAYS return naive UTC datetime (DB-safe)
    return datetime.utcnow()


# 🔹 Convert any datetime to IST safely
def to_ist(dt):
    if not dt:
        return None

    # Treat naive datetime as UTC (DB stores UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(IST)


# 🔹 FORMAT helper 
def format_ist(dt, fmt):
    ist_dt = to_ist(dt)
    return ist_dt.strftime(fmt) if ist_dt else ""

# 🔹 Timeago (for UI only)
def timeago_ist(dt):
    if not dt:
        return ""

    dt = to_ist(dt)
    now = datetime.now(IST)

    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        return f"{int(seconds // 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    else:
        return f"{int(seconds // 86400)} days ago"

# 🔹 Convert IST date (from UI) → UTC range start
def ist_date_to_utc(dt):
    """
    Input: datetime (IST date at 00:00)
    Output: datetime UTC
    """
    if dt.tzinfo is None:
        dt = IST.localize(dt)
    return dt.astimezone(timezone.utc)
