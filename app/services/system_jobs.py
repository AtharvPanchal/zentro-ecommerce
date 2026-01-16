
from datetime import datetime
from app.extensions import db
from app.models import OTP
from app.services.audit_logger import log_system_action


def cleanup_expired_otps():
    """
    Remove expired & used OTPs
    Runs via scheduler
    """

    now = datetime.utcnow()

    expired_otps = (
        OTP.query
        .filter(
            (OTP.expires_at < now) | (OTP.is_used == True)
        )
        .all()
    )

    if not expired_otps:
        return

    count = len(expired_otps)

    for otp in expired_otps:
        db.session.delete(otp)

    db.session.commit()

    # 🔒 SYSTEM AUDIT LOG
    log_system_action(
        action="System cleanup: expired OTPs",
        severity="LOW",
        reason=f"Removed {count} expired/used OTP records",
        is_bulk=True
    )
