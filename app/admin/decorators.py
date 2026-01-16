from functools import wraps
from flask import session, redirect, url_for, flash
from app.models import Admin
from flask_login import current_user


# --------------------------------------------------
# ADMIN LOGIN REQUIRED
# --------------------------------------------------
def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        admin_id = session.get("admin_id")
        session_version = session.get("admin_session_version")

        if not admin_id or not session_version:
            flash("Please login as admin.", "warning")
            return redirect(url_for("admin.login"))

        admin = Admin.query.get(admin_id)
        if not admin or admin.session_version != session_version:
            session.clear()
            flash("Session expired. Please login again.", "warning")
            return redirect(url_for("admin.login"))

        return view_func(*args, **kwargs)

    return wrapped_view


# --------------------------------------------------
# SUPER ADMIN REQUIRED (AUDIT / GOVERNANCE)
# --------------------------------------------------
def super_admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        admin_id = session.get("admin_id")
        session_version = session.get("admin_session_version")

        if not admin_id or not session_version:
            flash("Please login as admin.", "warning")
            return redirect(url_for("admin.login"))

        admin = Admin.query.get(admin_id)
        if not admin or admin.session_version != session_version:
            session.clear()
            flash("Session expired. Please login again.", "warning")
            return redirect(url_for("admin.login"))

        # 🔐 SUPER ADMIN CHECK
        if not admin.is_super_admin:
            flash("Unauthorized: Super Admin access required.", "danger")
            return redirect(url_for("admin.dashboard"))

        return view_func(*args, **kwargs)

    return wrapped_view
