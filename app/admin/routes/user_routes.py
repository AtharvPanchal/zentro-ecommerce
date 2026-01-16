from flask import render_template, redirect, url_for, flash, request
from datetime import datetime
from sqlalchemy import or_
from app.admin import admin_bp
from app.admin.decorators import admin_required
from app.extensions import db
from app.models import User
from app.models import UserStatusReason, AdminActivityLog
from flask import session

from app.models import LoginActivity

import csv
from io import StringIO
from flask import Response
from datetime import timedelta
from app.utils.time_utils import utc_now
from app.utils.activity_logger import log_admin_action
from app.utils.time_utils import IST





# --------------------------------------------------
# HELPER: LOG ADMIN ACTION INTO USER LOGIN ACTIVITY
# --------------------------------------------------
def log_admin_user_login_activity(user, status):
    activity = LoginActivity(
        user_id=user.id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
        device="admin-action",
        login_status=status,
        created_at=utc_now().replace(tzinfo=None)
    )
    db.session.add(activity)


# --------------------------------------------------
# ADMIN - USER MANAGEMENT
# --------------------------------------------------
@admin_bp.route("/users")
@admin_required
def admin_users():

    # -----------------------------
    # FILTER PARAMS
    # -----------------------------
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")

    # -----------------------------
    # BASE QUERY
    # -----------------------------
    query = User.query

    # -----------------------------
    # SEARCH: EMAIL / ID
    # -----------------------------
    if q:
        if q.isdigit():
            query = query.filter(User.id == int(q))
        else:
            query = query.filter(User.email.ilike(f"%{q}%"))

    # -----------------------------
    # STATUS FILTER
    # -----------------------------
    if status == "active":
        query = query.filter(User.is_active == True, User.lock_until == None)

    elif status == "disabled":
        query = query.filter(User.is_active == False)

    elif status == "locked":
        query = query.filter(
            User.lock_until != None,
            User.lock_until > utc_now()
        )

    # -----------------------------
    # FINAL RESULT
    # -----------------------------
    users = query.order_by(User.created_at.desc()).all()

    return render_template(
        "admin/users.html",
        users=users,
        now=utc_now()
    )


# --------------------------------------------------
# LOCK USER (ADMIN FORCE LOCK – 24 HOURS)
# --------------------------------------------------
@admin_bp.route("/users/lock/<int:user_id>", methods=["POST"])
@admin_required
def lock_user(user_id):
    admin_id = session.get("admin_id")
    if not admin_id:
        flash("Admin session expired. Please login again.", "danger")
        return redirect(url_for("admin.login"))

    user = User.query.get_or_404(user_id)

    # ❌ Prevent locking a disabled user
    if not user.is_active:
        flash("Disabled user cannot be locked.", "danger")
        return redirect(url_for("admin.admin_users"))

    now = utc_now()

    # 🔐 FORCE ADMIN LOCK (24 HOURS)
    user.lock_until = now + timedelta(hours=24)
    user.is_active = True

    # 🆕 SAVE REASON
    admin_id = session.get("admin_id")

    reason = UserStatusReason(
        user_id=user.id,
        admin_id=admin_id,
        action="lock",
        reason="Security",
        note="Locked by admin due to security concerns"
    )

    db.session.add(reason)

    log_admin_action(
        action="Locked user account",
        target_user_id=user.id,
        reason="Locked by admin due to security concerns"

    )
    log_admin_user_login_activity(user, "locked")

    try:
        db.session.commit()
        flash("User locked for 24 hours 🔒", "warning")
    except Exception:
        db.session.rollback()
        flash("Something went wrong. Try again.", "danger")

    return redirect(url_for("admin.admin_users"))



# ==================================================
# ENABLE / DISABLE USER (SOFT BAN)
# ==================================================
@admin_bp.route("/users/toggle-status/<int:user_id>", methods=["POST"])
@admin_required
def toggle_user_status(user_id):
    admin_id = session.get("admin_id")
    if not admin_id:
        flash("Admin session expired. Please login again.", "danger")
        return redirect(url_for("admin.login"))

    user = User.query.get_or_404(user_id)

    # 🔐 SAFETY CHECK
   # if user.id == current_user.id:
    #    flash("You cannot modify your own account.", "danger")
     #   return redirect(url_for("admin.admin_users"))

    # no early return here
    # disabled user SHOULD be allowed to enable

    # TOGGLE STATUS
    user.is_active = not user.is_active

    action = "enable" if user.is_active else "disable"
    action_text = "Enabled" if user.is_active else "Disabled"
    status = "success" if user.is_active else "disabled"

    # CLEAR LOCK IF DISABLED
    if not user.is_active:
        user.lock_until = None

    # 🆕 SAVE REASON
    reason = UserStatusReason(
        user_id=user.id,
        admin_id=admin_id,
        action=action,
        reason="Policy",
        note=f"User account {action_text.lower()} by admin"
    )
    db.session.add(reason)

    log_admin_action(
        action=f"{action_text} user account",
        target_user_id=user.id,
        reason=f"User account {action_text.lower()} by admin"
    )

    log_admin_user_login_activity(user, status)

    db.session.commit()

    flash(f"User account {action_text} successfully.", "success")
    return redirect(url_for("admin.admin_users"))


# --------------------------------------------------
# UNLOCK USER
# --------------------------------------------------
@admin_bp.route("/users/unlock/<int:user_id>", methods=["POST"])
@admin_required
def unlock_user(user_id):
    admin_id = session.get("admin_id")
    if not admin_id:
        flash("Admin session expired. Please login again.", "danger")
        return redirect(url_for("admin.login"))

    user = User.query.get_or_404(user_id)

    if not user.lock_until:
        flash("User account is not locked.", "info")
        return redirect(url_for("admin.admin_users"))

    # ✅ FORCE UNLOCK (ADMIN OVERRIDE)
    keep_disabled = request.form.get("keep_disabled")

    user.lock_until = None

    if keep_disabled == "1":
        user.is_active = False
    else:
        user.is_active = True

    reason = UserStatusReason(
        user_id=user.id,
        admin_id=admin_id,
        action="unlock",
        reason="Admin Override",
        note="Admin force unlocked account"
    )
    db.session.add(reason)

    log_admin_action(
        action="Unlocked user account",
        target_user_id=user.id,
        reason="Admin force unlocked account"
    )


    log_admin_user_login_activity(user, "success")

    db.session.commit()

    flash("User unlocked and activated successfully ✅", "success")
    return redirect(url_for("admin.admin_users"))




# ==================================================
# USER LOGIN ACTIVITY (ADMIN VIEW)
# ==================================================
@admin_bp.route("/users/<int:user_id>/login-history")
@admin_required
def user_login_history(user_id):

    user = User.query.get_or_404(user_id)

    # -----------------------------
    # PAGINATION PARAMS
    # -----------------------------
    page = request.args.get("page", 1, type=int)
    per_page = 10   # records per page

    # -----------------------------
    # FILTER PARAMS
    # -----------------------------
    q = request.args.get("q", "").strip()
    status = request.args.get("status")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    # -----------------------------
    # BASE QUERY
    # -----------------------------
    logs_query = LoginActivity.query.filter_by(user_id=user.id)

    # SEARCH
    if q:
        logs_query = logs_query.filter(
            or_(
                LoginActivity.ip_address.ilike(f"%{q}%"),
                LoginActivity.user_agent.ilike(f"%{q}%"),
                LoginActivity.login_status.ilike(f"%{q}%")
            )
        )

    # STATUS FILTER
    if status:
        logs_query = logs_query.filter(
            LoginActivity.login_status == status
        )


    # DATE RANGE
    if from_date:
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        start_date = start_date.replace(hour=0, minute=0, second=0)
        logs_query = logs_query.filter(
            LoginActivity.created_at >= start_date
        )

    if to_date:
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        end_date = end_date.replace(hour=23, minute=59, second=59)
        logs_query = logs_query.filter(
            LoginActivity.created_at <= end_date
        )

    # -----------------------------
    # PAGINATE
    # -----------------------------
    pagination = logs_query.order_by(
        LoginActivity.created_at.desc()
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return render_template(
        "admin/user_login_logs.html",
        user=user,
        logs=pagination.items,
        pagination=pagination,

    )

# ==================================================
# USER LOGIN ACTIVITY - CSV EXPORT
# ==================================================
@admin_bp.route("/users/<int:user_id>/login-history/export")
@admin_required
def export_user_login_history_csv(user_id):
    admin_id = session.get("admin_id")
    if not admin_id:
        flash("Admin session expired. Please login again.", "danger")
        return redirect(url_for("admin.login"))

    user = User.query.get_or_404(user_id)

    # SAME FILTER PARAMS
    q = request.args.get("q", "").strip()
    status = request.args.get("status")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    # BASE QUERY
    logs_query = LoginActivity.query.filter_by(user_id=user.id)

    if q:
        logs_query = logs_query.filter(
            or_(
                LoginActivity.ip_address.ilike(f"%{q}%"),
                LoginActivity.user_agent.ilike(f"%{q}%"),
                LoginActivity.login_status.ilike(f"%{q}%")
            )
        )

    if status:
        logs_query = logs_query.filter(
            LoginActivity.login_status == status
        )

    # DATE RANGE (FULL DAY – UTC SAFE)
    if from_date:
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        start_date = start_date.replace(hour=0, minute=0, second=0)
        logs_query = logs_query.filter(
            LoginActivity.created_at >= start_date
        )

    if to_date:
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        end_date = end_date.replace(hour=23, minute=59, second=59)
        logs_query = logs_query.filter(
            LoginActivity.created_at <= end_date
        )

    logs = logs_query.order_by(
        LoginActivity.created_at.desc()
    ).all()

    if not logs:
        flash("No login activity found for export.", "warning")
        return redirect(
            url_for("admin.user_login_history", user_id=user.id)
        )



    # CREATE CSV
    output = StringIO()
    writer = csv.writer(output)

    # CSV HEADER
    writer.writerow([
        "Date",
        "Time",
        "IP Address",
        "Device",
        "Status"
    ])

    # CSV ROWS
    for log in logs:
        ist_time = log.created_at.astimezone(IST)
        writer.writerow([
            ist_time.strftime("%d %b %Y"),
            ist_time.strftime("%I:%M %p"),
            log.ip_address,
            log.user_agent,
            log.login_status
        ])

    # RESPONSE
    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )
    response.headers["Content-Disposition"] = (
        f"attachment; filename=login_activity_user_{user.id}.csv"
    )

    log_admin_action(
        action="Exported login activity CSV",
        target_user_id=user.id,
        reason="Admin exported login activity"
    )

    return response
