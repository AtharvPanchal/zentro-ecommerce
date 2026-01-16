from app.extensions import db
from app.models import AdminActivityLog


def log_system_action(
    action: str,
    severity: str = "LOW",
    reason: str | None = None,
    is_bulk: bool = False
):
    """
    System-level audit logger
    No admin involved
    """

    log = AdminActivityLog(
        admin_id=None,
        target_user_id=None,
        action=action,
        severity=severity,
        reason=reason,
        actor_type="system",
        is_bulk=is_bulk
    )

    db.session.add(log)
    db.session.commit()
