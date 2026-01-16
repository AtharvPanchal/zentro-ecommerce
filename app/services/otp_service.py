import random
from datetime import datetime, timedelta

from sqlalchemy import func
from app.extensions import db
from app.models import OTP


# --------------------------------------------------
# CONFIG
# --------------------------------------------------
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
MAX_RESEND_LIMIT = 3


# --------------------------------------------------
# GENERATE OTP
# --------------------------------------------------
def generate_otp(user_id: int) -> str:
    invalidate_otp(user_id)

    otp_code = _generate_code()

    otp = OTP(
        user_id=user_id,
        code=otp_code,
        expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        resend_count=0,
        is_used=False
    )

    db.session.add(otp)
    db.session.commit()
    return otp_code


# --------------------------------------------------
# VERIFY OTP
# --------------------------------------------------
def verify_otp(user_id: int, otp_input: str) -> bool:
    otp = (
        OTP.query
        .filter_by(
            user_id=user_id,
            code=otp_input,
            is_used=False
        )
        .order_by(OTP.created_at.desc())
        .first()
    )

    if not otp:
        return False

    # ✅ SAFE & CORRECT (MySQL + Windows)
    if otp.expires_at < datetime.utcnow():
        return False

    otp.is_used = True
    db.session.commit()
    return True


# --------------------------------------------------
# RESEND OTP
# --------------------------------------------------
def resend_otp(user_id: int) -> str | None:
    latest_otp = (
        OTP.query
        .filter_by(user_id=user_id)
        .order_by(OTP.created_at.desc())
        .first()
    )

    if latest_otp and latest_otp.resend_count >= MAX_RESEND_LIMIT:
        return None

    otp_code = _generate_code()

    if latest_otp:
        latest_otp.code = otp_code
        latest_otp.expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        latest_otp.resend_count += 1
        latest_otp.is_used = False
    else:
        latest_otp = OTP(
            user_id=user_id,
            code=otp_code,
            expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
            resend_count=1,
            is_used=False
        )
        db.session.add(latest_otp)

    db.session.commit()
    return otp_code


# --------------------------------------------------
# INVALIDATE OTPs
# --------------------------------------------------
def invalidate_otp(user_id: int) -> None:
    OTP.query.filter_by(
        user_id=user_id,
        is_used=False
    ).update({"is_used": True})

    db.session.commit()


# --------------------------------------------------
# AUTO OTP CLEANUP JOB (CRON SAFE)
# --------------------------------------------------
def cleanup_otps() -> int:
    """
    Delete:
    - Expired OTPs
    - Used OTPs older than 10 minutes
    Returns number of deleted rows
    """

    now = datetime.utcnow()

    deleted = (
        OTP.query
        .filter(
            (OTP.expires_at < now) |
            (
                (OTP.is_used == True) &
                (OTP.created_at < now - timedelta(minutes=10))
            )
        )
        .delete(synchronize_session=False)
    )

    db.session.commit()
    return deleted


# --------------------------------------------------
# INTERNAL HELPER
# --------------------------------------------------
def _generate_code() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(OTP_LENGTH))
