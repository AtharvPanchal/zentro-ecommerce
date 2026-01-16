from datetime import datetime, timedelta, timezone
from app.models import AdminActivityLog
from app.extensions import db
from app.utils.activity_logger import log_admin_action

RETENTION_DAYS = 90

def auto_archive_old_audit_logs():
    """
    Auto archive old audit logs (Retention Policy)
    """

    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

    logs = (
        AdminActivityLog.query
        .filter(
            AdminActivityLog.created_at < cutoff,
            AdminActivityLog.is_archived == 0,
            AdminActivityLog.severity != "HIGH",
            AdminActivityLog.actor_type != "system"
        )
        .all()
    )

    if not logs:
        return 0

    for log in logs:
        log.is_archived = 1

    db.session.commit()

    # System audit entry
    log_admin_action(
        action="Auto archived audit logs (retention policy)",
        reason=f"Archived {len(logs)} logs older than {RETENTION_DAYS} days",
        actor_type="system",
        is_bulk=True,
        severity="LOW"
    )

    return len(logs)
