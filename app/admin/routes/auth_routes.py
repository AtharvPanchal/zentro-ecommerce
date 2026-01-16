from datetime import datetime, timedelta

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.admin import admin_bp
from app.models import Admin, AdminOTP
from app.services.email_service import (
    send_admin_otp_email,
    send_admin_password_reset_success_email,
    send_admin_account_lock_email
)


# --------------------------------------------------
# ADMIN LOGIN
# --------------------------------------------------
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(email=email).first()

        # Generic error (do not reveal which part failed)
        error_msg = "Invalid admin credentials."

        if not admin or not admin.is_active:
            flash(error_msg, "danger")
            return redirect(url_for("admin.login"))

        # Account lock check
        if admin.lock_until and admin.lock_until > datetime.utcnow():
            remaining_seconds = int(
                (admin.lock_until - datetime.utcnow()).total_seconds()
            )

            return render_template(
                "admin/login.html",
                lock_remaining=remaining_seconds
            )

        if not check_password_hash(admin.password_hash, password):
            admin.failed_login_attempts += 1

            if admin.failed_login_attempts >= 5:
                admin.lock_until = datetime.utcnow() + timedelta(minutes=15)
                admin.failed_login_attempts = 0

                send_admin_account_lock_email(
                    to_email=admin.notification_email,
                    lock_minutes=15,
                    ip_address=request.remote_addr,
                    device=request.headers.get("User-Agent")
                )

            db.session.commit()
            flash(error_msg, "danger")
            return redirect(url_for("admin.login"))

        # ✅ SUCCESS
        admin.failed_login_attempts = 0
        admin.lock_until = None
        admin.last_login = datetime.utcnow()
        admin.session_version += 1

        db.session.commit()

        session.clear()
        session["admin_id"] = admin.id
        session["admin_session_version"] = admin.session_version
        session["is_super_admin"] = admin.is_super_admin

        return redirect(url_for("admin.dashboard"))

    return render_template("admin/login.html")


# --------------------------------------------------
# ADMIN LOGOUT
# --------------------------------------------------
@admin_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("admin.login"))


# --------------------------------------------------
# FORGOT PASSWORD
# --------------------------------------------------
@admin_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        admin = Admin.query.filter_by(email=email).first()

        # Always show same message (security)
        flash("If the admin account exists, an OTP has been sent.", "info")

        if admin and admin.is_active:

            if not admin.notification_email:
                flash("Admin notification email not configured. Contact system owner.", "danger")
                return redirect(url_for("admin.login"))

            otp_code = _generate_otp()

            otp = AdminOTP(
                admin_id=admin.id,
                code=otp_code,
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )

            db.session.add(otp)
            db.session.commit()

            send_admin_otp_email(
                to_email=admin.notification_email,
                otp_code=otp_code
            )

        return redirect(url_for("admin.verify_otp", email=email))

    return render_template("admin/forgot_password.html")


# --------------------------------------------------
# VERIFY OTP
# --------------------------------------------------
@admin_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        code = request.form.get("otp", "").strip()

        admin = Admin.query.filter_by(email=email).first()
        if not admin:
            flash("Invalid OTP.", "danger")
            return redirect(url_for("admin.verify_otp", email=email))

        otp = (
            AdminOTP.query
            .filter_by(admin_id=admin.id, code=code, is_used=False)
            .order_by(AdminOTP.created_at.desc())
            .first()
        )

        if not otp or otp.expires_at < datetime.utcnow():
            flash("OTP expired or invalid.", "danger")
            return redirect(url_for("admin.verify_otp", email=email))

        otp.is_used = True
        db.session.commit()

        session["reset_admin_id"] = admin.id
        return redirect(url_for("admin.reset_password"))

    # ✅ GET request (THIS WAS MISSING)
    email = request.args.get("email", "").strip().lower()
    if not email:
        return redirect(url_for("admin.forgot_password"))

    return render_template("admin/verify_otp.html", email=email)


# --------------------------------------------------
# RESET PASSWORD
# --------------------------------------------------
@admin_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    admin_id = session.get("reset_admin_id")
    if not admin_id:
        return redirect(url_for("admin.login"))

    admin = Admin.query.get(admin_id)
    if not admin:
        return redirect(url_for("admin.login"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if password != confirm or len(password) < 8:
            flash("Passwords must match and be at least 8 characters.", "danger")
            return redirect(url_for("admin.reset_password"))

        admin.password_hash = generate_password_hash(password)
        admin.session_version += 1
        db.session.commit()

        send_admin_password_reset_success_email(
            to_email=admin.notification_email
        )

        session.pop("reset_admin_id", None)

        flash("Password Reset Successful. Please Login.", "success")
        return redirect(url_for("admin.login"))

    return render_template("admin/reset_password.html")


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def _is_admin_logged_in():
    admin_id = session.get("admin_id")
    version = session.get("admin_session_version")

    if not admin_id or not version:
        return False

    admin = Admin.query.get(admin_id)
    return bool(admin and admin.session_version == version)


def _generate_otp():
    from random import randint
    return str(randint(100000, 999999))