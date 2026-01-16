from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models import AdminActivityLog
from app.utils.activity_logger import log_admin_action


def cleanup_old_archived_audit_logs(days=180):
    """
    Deletes archived audit logs older than `days`.
    Runs via scheduler (system task).
    """

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    old_logs = (
        AdminActivityLog.query
        .filter(
            AdminActivityLog.is_archived == 1,
            AdminActivityLog.created_at < cutoff_date
        )
        .all()
    )

    if not old_logs:
        return 0

    deleted_count = len(old_logs)

    for log in old_logs:
        db.session.delete(log)

    db.session.commit()

    # ✅ SYSTEM AUDIT ENTRY
    log_admin_action(
        action="Auto cleanup archived audit logs",
        actor_type="system",
        is_bulk=True,
        reason=f"Deleted {deleted_count} archived logs older than {days} days"
    )

    return deleted_count
