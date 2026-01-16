from flask import request, session
from datetime import timezone
import uuid

from app.extensions import db
from app.models import AdminActivityLog


# ==================================================
# AUTO SEVERITY MAPPING (NORMALIZED)
# ==================================================
SEVERITY_MAP = {
    "Locked user account": "HIGH",
    "Disabled user account": "HIGH",

    "Unlocked user account": "MEDIUM",
    "Enabled user account": "MEDIUM",

    "Archived audit log": "LOW",
    "Unarchived audit log": "LOW",
    "Bulk archived audit logs": "LOW",

    "Exported User Login CSV": "LOW",
    "Exported Audit Logs CSV": "LOW",

    "Admin Login": "LOW",
    "Admin Logout": "LOW",

    "Auto cleanup archived audit logs": "LOW",
}


# ==================================================
# CENTRAL ADMIN ACTIVITY LOGGER (IMMUTABLE SAFE)
# ==================================================
def log_admin_action(
    action: str,
    target_user_id: int | None = None,
    reason: str | None = None,
    *,
    actor_type: str = "admin",   # admin | system
    is_bulk: bool = False
):
    """
    ✔ Immutable-safe
    ✔ No timezone conflict
    ✔ Model-driven defaults
    ✔ UI / analytics consistent
    """

    try:
        admin_id = session.get("admin_id")
    except RuntimeError:
        admin_id = None

    # 🔒 Admin action requires admin session
    if actor_type == "admin" and not admin_id:
        return

    # Normalize actor_type
    if actor_type not in ("admin", "system"):
        actor_type = "system"

    try:
        severity = SEVERITY_MAP.get(action, "LOW")

        log = AdminActivityLog(
            admin_id=admin_id if actor_type == "admin" else None,
            action=action,
            target_user_id=target_user_id,
            actor_type=actor_type,
            is_bulk=is_bulk,
            ip_address=request.remote_addr if actor_type == "admin" else None,
            user_agent=request.headers.get("User-Agent") if actor_type == "admin" else None,
            severity=severity,
            reason=reason,
            # ❌ DO NOT pass created_at
            # ❌ DO NOT pass log_ref
        )

        db.session.add(log)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print("⚠️ Admin Activity Log Error:", e)
