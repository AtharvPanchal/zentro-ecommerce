from flask import render_template, request, Response
from app.admin import admin_bp
from app.admin.decorators import admin_required
from app.models import AdminActivityLog
from datetime import datetime, timezone, timedelta
from app.utils.time_utils import to_ist, ist_date_to_utc
import csv
from io import StringIO
from flask import session
from app.utils.activity_logger import log_admin_action
from app.extensions import db
from sqlalchemy import func
from app.extensions import csrf


#---------------------------------------------
#    ADMIN AUDIT LOGS
#---------------------------------------------
@admin_bp.route("/audit-logs")
@admin_required
def admin_audit_logs():

    q = request.args.get("q", "").strip()
    action = request.args.get("action")
    severity = request.args.get("severity")
    archived = request.args.get("archived")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    query = AdminActivityLog.query

    # 🔒 RBAC HARDENING
    is_super_admin = session.get("is_super_admin", False)

    if not is_super_admin:
        # Normal admins CANNOT see system or bulk logs
        query = query.filter(
            AdminActivityLog.actor_type == "admin",
            AdminActivityLog.is_bulk == 0
        )

    # 🔍 SEARCH (admin_id / target_user_id)
    if q:
        if q.isdigit():
            query = query.filter(
                (AdminActivityLog.admin_id == int(q)) |
                (AdminActivityLog.target_user_id == int(q))
            )
        else:
            query = query.join(AdminActivityLog.admin).filter(
                AdminActivityLog.admin.has(email=q)
            )

    # 🔍 ACTION FILTER
    if action:
        query = query.filter(AdminActivityLog.action.ilike(f"%{action}%"))

    # SEVERITY FILTER (PURE)
    if severity:
        query = query.filter(AdminActivityLog.severity == severity)

    # 🗄️ ARCHIVE FILTER (GLOBAL)
    if archived == "1":
        query = query.filter(AdminActivityLog.is_archived.is_(True))
    else:
        query = query.filter(AdminActivityLog.is_archived.is_(False))

    # 📅 DATE FILTER (IST DAY RANGE – AUDIT SAFE)
    if from_date:
        ist_start = datetime.strptime(from_date, "%Y-%m-%d")
        utc_start = ist_date_to_utc(ist_start)

        # 🔒 subtract 1 second buffer for boundary safety
        utc_start = utc_start - timedelta(seconds=1)

        query = query.filter(AdminActivityLog.created_at >= utc_start)

    if to_date:
        ist_end = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
        utc_end = ist_date_to_utc(ist_end)
        query = query.filter(AdminActivityLog.created_at < utc_end)



    page = request.args.get("page", 1, type=int)
    per_page = 20

    pagination = (
        query
        .order_by(AdminActivityLog.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    logs = pagination.items

    for log in logs:
        log.ist_time = to_ist(log.created_at)

    return render_template(
        "admin/admin_activity_logs.html",
        logs=logs,
        pagination=pagination,

    )


#---------------------------------------------
#   ARCHIVE AUDIT LOG (SOFT)
#---------------------------------------------
@admin_bp.route("/audit-logs/archive/<int:log_id>", methods=["POST"])
@admin_required
def archive_audit_log(log_id):
    try:
        updated = (
            AdminActivityLog.query
            .filter(
                AdminActivityLog.id == log_id,
                AdminActivityLog.is_archived.is_(False)
            )
            .update(
                {"is_archived": True},
                synchronize_session=False
            )
        )

        if updated == 0:
            return {"status": "already_archived"}, 200

        db.session.commit()
        return {"status": "archived"}, 200

    except Exception as e:
        db.session.rollback()
        print("ARCHIVE ERROR:", e)
        return {"error": "archive_failed"}, 500





#---------------------------------------------
#   BULK ARCHIVE AUDIT LOGS (SUPER ADMIN)
#---------------------------------------------
@admin_bp.route("/audit-logs/archive-bulk", methods=["POST"])
@admin_required
@csrf.exempt
def bulk_archive_audit_logs():

    if not session.get("is_super_admin", False):
        return {"error": "Unauthorized"}, 403

    data = request.get_json(silent=True) or {}
    log_ids = data.get("log_ids", [])

    if not log_ids:
        return {"error": "No logs selected"}, 400

    try:
        updated = (
            AdminActivityLog.query
            .filter(
                AdminActivityLog.id.in_(log_ids),
                AdminActivityLog.is_archived.is_(False)
            )
            .update(
                {"is_archived": True},
                synchronize_session=False
            )
        )

        if updated == 0:
            return {"status": "nothing_to_archive"}, 200

        db.session.commit()

        log_admin_action(
            action="Bulk archived audit logs",
            reason=f"Bulk archived {updated} logs",
            actor_type="system",
            is_bulk=True
        )

        return {"status": "archived", "count": updated}, 200

    except Exception as e:
        db.session.rollback()
        print("BULK ARCHIVE ERROR:", e)
        return {"error": "archive_failed"}, 500


#---------------------------------------------
#   UNARCHIVE AUDIT LOG (SUPER ADMIN)
#---------------------------------------------
@admin_bp.route("/audit-logs/unarchive/<int:log_id>", methods=["POST"])
@admin_required
def unarchive_audit_log(log_id):
    if not session.get("is_super_admin", False):
        return {"error": "Unauthorized"}, 403

    try:
        updated = (
            AdminActivityLog.query
            .filter(
                AdminActivityLog.id == log_id,
                AdminActivityLog.is_archived.is_(True)
            )
            .update(
                {"is_archived": False},
                synchronize_session=False
            )
        )

        if updated == 0:
            return {"status": "already_active"}, 200

        db.session.commit()
        return {"status": "unarchived"}, 200

    except Exception as e:
        db.session.rollback()
        print("UNARCHIVE ERROR:", e)
        return {"error": "unarchive_failed"}, 500




#-----------------------------------------------
#  EXPORT AUDIT LOGS
#----------------------------------------------
@admin_bp.route("/audit-logs/export")
@admin_required
def export_audit_logs():
    logs = AdminActivityLog.query.filter(
        # export_audit_logs()
        AdminActivityLog.is_archived.is_(False)

    ).order_by(
        AdminActivityLog.created_at.desc()
    ).all()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Date",
        "Time",
        "Admin ID",
        "Action",
        "Target User ID"
    ])

    for log in logs:
        ist_time = to_ist(log.created_at)
        writer.writerow([
            ist_time.strftime("%d %b %Y"),
            ist_time.strftime("%I:%M %p"),
            log.admin_id,
            log.action,
            log.target_user_id
        ])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = (
        "attachment; filename=audit_logs.csv"
    )

    return response



# ---------------------------------------------
#   AUDIT LOG ANALYTICS (TRENDS)
# ---------------------------------------------
@admin_bp.route("/audit-logs/trends")
@admin_required
def audit_log_trends():

    # 🔒 Super Admin only
    if not session.get("is_super_admin", False):
        return {"error": "Unauthorized"}, 403

    days = int(request.args.get("days", 7))

    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)

    logs = (
        db.session.query(
            func.date(AdminActivityLog.created_at).label("day"),
            func.count(AdminActivityLog.id).label("count")
        )
        .filter(AdminActivityLog.created_at >= start_date)
        .group_by(func.date(AdminActivityLog.created_at))
        .order_by(func.date(AdminActivityLog.created_at))
        .all()
    )

    severity_data = (
        db.session.query(
            AdminActivityLog.severity,
            func.count(AdminActivityLog.id)
        )
        .filter(AdminActivityLog.created_at >= start_date)
        .group_by(AdminActivityLog.severity)
        .all()
    )

    actor_data = (
        db.session.query(
            AdminActivityLog.actor_type,
            func.count(AdminActivityLog.id)
        )
        .filter(AdminActivityLog.created_at >= start_date)
        .group_by(AdminActivityLog.actor_type)
        .all()
    )

    return {
        "days": days,
        "daily": [
            {"date": str(row.day), "count": row.count}
            for row in logs
        ],
        "severity": {
            severity: count for severity, count in severity_data
        },
        "actors": {
            actor: count for actor, count in actor_data
        }
    }

# ---------------------------------------------
#   TOP ADMIN ACTIONS (ANALYTICS)
# ---------------------------------------------
@admin_bp.route("/audit-analytics/top-actions")
@admin_required
def audit_top_actions():

    # 🔒 Super Admin only
    if not session.get("is_super_admin", False):
        return {"error": "Unauthorized"}, 403

    limit = int(request.args.get("limit", 5))

    results = (
        db.session.query(
            AdminActivityLog.action,
            func.count(AdminActivityLog.id).label("count")
        )
        .group_by(AdminActivityLog.action)
        .order_by(func.count(AdminActivityLog.id).desc())
        .limit(limit)
        .all()
    )

    return {
        "labels": [row.action for row in results],
        "counts": [row.count for row in results]
    }


