from flask import (
    render_template, request,
    redirect, url_for, flash,
    session, current_app
)
from flask_login import (
    login_user, logout_user,
    login_required
)

from datetime import datetime, timezone
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import requests

from app.extensions import db, limiter
from app.models import User
from app.models import LoginActivity
from app.utils.utils import verify_password, hash_password
from app.services.otp_service import (
    generate_otp, verify_otp, invalidate_otp
)
from app.services.email_service import (
    send_otp_email,
    send_password_reset_success_email,
    send_verification_email,
    send_user_account_lock_email     # ✅ ADDED
)

from . import auth_bp
from datetime import timedelta
from app.utils.time_utils import utc_now




# ==================================================
# reCAPTCHA v3
# ==================================================
def verify_recaptcha_v3(expected_action: str) -> bool:
    if current_app.config.get("RECAPTCHA_DISABLED"):
        return True

    token = request.form.get("g-recaptcha-response")
    if not token:
        return False

    payload = {
        "secret": current_app.config["RECAPTCHA_SECRET_KEY"],
        "response": token,
        "remoteip": request.remote_addr
    }

    try:
        r = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data=payload,
            timeout=5
        )
        result = r.json()

        if not result.get("success"):
            return False
        if result.get("action") != expected_action:
            return False

        score = result.get("score", 0)
        threshold = current_app.config.get("RECAPTCHA_SCORE_THRESHOLD", 0.5)
        return score >= threshold

    except Exception:
        return False


# ==================================================
# EMAIL TOKEN
# ==================================================
def generate_email_token(email: str) -> str:
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="email-verify")


def confirm_email_token(token: str, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return s.loads(token, salt="email-verify", max_age=expiration)
    except (SignatureExpired, BadSignature):
        return None


# ==================================================
# LOGIN ACTIVITY LOGGER
# ==================================================
def log_login_attempt(user, status):
    activity = LoginActivity(
        user_id=user.id if user else None,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
        device=request.user_agent.platform or "unknown",
        login_status=status,
        created_at=utc_now().replace(tzinfo=None)
    )
    db.session.add(activity)



# ==================================================
# LOGIN
# ==================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    # ---------- GET (LOCK COUNTDOWN) ----------
    email = request.args.get("email")
    lock_seconds = None

    if email:
        u = User.query.filter_by(email=email.lower()).first()
        if u and u.lock_until and u.lock_until > utc_now().replace(tzinfo=None):
            lock_seconds = int(
                (u.lock_until - utc_now().replace(tzinfo=None)).total_seconds()
            )

    if request.method == "GET":
        return render_template(
            "auth/login.html",
            lock_active=bool(lock_seconds),
            lock_seconds=lock_seconds or 0
        )

    # ---------- CAPTCHA ----------
    if not verify_recaptcha_v3("login"):
        flash("⚠️ Suspicious Activity Detected.", "danger")
        return redirect(url_for("auth.login"))

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    remember = bool(request.form.get("remember"))

    user = User.query.filter_by(email=email).first()

    # ---------- USER NOT FOUND ----------
    if not user:
        flash("❌ Invalid Email or Password", "danger")
        return redirect(url_for("auth.login"))

    # ---------- ACCOUNT LOCKED (CHECK FIRST) ----------
    if user.lock_until and utc_now().replace(tzinfo=None) < user.lock_until:
        log_login_attempt(user, "locked")
        return redirect(url_for("auth.login", email=email))

    # ---------- WRONG PASSWORD ----------
    if not verify_password(password, user.password_hash):
        log_login_attempt(user, "failed")

        user.failed_login_attempts += 1

        if user.failed_login_attempts >= 5:
            user.lock_until = utc_now().replace(tzinfo=None) + timedelta(minutes=15)
            db.session.commit()

            send_user_account_lock_email(
                to_email=user.email,
                username=user.username,
                lock_minutes=15,
                ip_address=request.remote_addr,
                device=request.headers.get("User-Agent")
            )
            return redirect(url_for("auth.login", email=email))

        db.session.commit()
        flash("❌ Invalid Email or Password", "danger")
        return redirect(url_for("auth.login"))

    # ---------- ACCOUNT DISABLED ----------
    if not user.is_active:
        log_login_attempt(user, "disabled")
        flash("🚫 Your account has been disabled by admin.", "danger")
        return redirect(url_for("auth.login"))

    # ---------- EMAIL NOT VERIFIED ----------
    if not user.email_verified:
        log_login_attempt(user, "email_not_verified")
        flash("📧 Please verify your email.", "warning")
        return redirect(url_for("auth.login"))

    # ---------- SUCCESS ----------
    user.failed_login_attempts = 0
    user.lock_until = None
    db.session.commit()

    login_user(user, remember=remember)
    session["session_version"] = user.session_version

    log_login_attempt(user, "success")
    flash("✅ Login Successful", "success")
    return redirect(url_for("main.index"))



# ==================================================
# SIGNUP
# ==================================================
@auth_bp.route("/signup", methods=["POST"])
@limiter.limit("5 per hour")
def signup():

    if not verify_recaptcha_v3("signup"):
        flash("⚠️ Suspicious Activity Detected.", "danger")
        return redirect(url_for("auth.login"))

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password")
    confirm = request.form.get("confirm_password")

    if not all([username, email, password, confirm]):
        flash("❌ All Fields Are Required.", "danger")
        return redirect(url_for("auth.login"))

    if password != confirm:
        flash("❌ Passwords Do Not Match.", "danger")
        return redirect(url_for("auth.login"))

    if User.query.filter_by(email=email).first():
        flash("❌ Email Already Registered.", "danger")
        return redirect(url_for("auth.login"))

    if User.query.filter_by(username=username).first():
        flash("❌ Username Already Taken.", "danger")
        return redirect(url_for("auth.login"))

    user = User(
        username=username,
        email=email,
        notification_email=email,
        password_hash=hash_password(password),
        email_verified=False
    )

    db.session.add(user)
    db.session.commit()

    token = generate_email_token(user.email)
    send_verification_email(user.email, token)

    flash("📧 Account Created! Please Verify Your Email.", "success")
    return redirect(url_for("auth.login"))


# ==================================================
# VERIFY EMAIL
# ==================================================
@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    email = confirm_email_token(token)
    if not email:
        flash("❌ Verification Link Invalid or Expired.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("❌ Invalid Verification Request.", "danger")
        return redirect(url_for("auth.login"))

    if user.email_verified:
        flash("✅ Email Already Verified.", "success")
        return redirect(url_for("auth.login"))

    user.email_verified = True
    db.session.commit()

    flash("✅ Email Verified Successfully. You Can Now Log In.", "success")
    return redirect(url_for("auth.login"))

# ==================================================
# LOGOUT
# ==================================================
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("👋 Logged Out", "info")
    return redirect(url_for("auth.login"))

# ==================================================
# FORGOT PASSWORD
# ==================================================
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def forgot_password():
    if request.method == "POST":

        if not verify_recaptcha_v3("forgot"):
            flash("⚠️ Suspicious Activity Detected.", "danger")
            return redirect(url_for("auth.forgot_password"))

        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("❌ No Account Found", "danger")
            return redirect(url_for("auth.forgot_password"))

        otp_code = generate_otp(user.id)
        send_otp_email(user.email, otp_code)

        flash("📩 OTP Sent To Your Email", "success")
        return redirect(url_for("auth.verify_otp_route", email=email))

    return render_template("auth/forgot_password.html")


# ==================================================
# VERIFY OTP
# ==================================================
@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp_route():
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()

    if not user:
        flash("❌ Invalid Request", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        otp_input = request.form.get("otp", "")
        if not verify_otp(user.id, otp_input):
            flash("❌ Invalid or Expired OTP", "danger")
            return redirect(url_for("auth.verify_otp_route", email=email))

        return redirect(url_for("auth.reset_password", email=email))

    return render_template("auth/verify_otp.html", email=email)


# ==================================================
# RESET PASSWORD
# ==================================================
@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()

    if not user:
        flash("❌ Invalid Request", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if password != confirm:
            flash("❌ Passwords Do Not Match", "danger")
            return redirect(url_for("auth.reset_password", email=email))

        user.password_hash = hash_password(password)
        user.session_version += 1
        db.session.commit()

        invalidate_otp(user.id)

        send_password_reset_success_email(
            user.email,
            request.remote_addr,
            request.headers.get("User-Agent")
        )

        flash("🔐 Password Reset Successful", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", email=email)


# ==================================================
# RESEND EMAIL VERIFICATION
# ==================================================
@auth_bp.route("/resend-verification", methods=["POST"])
@limiter.limit("3 per hour")
def resend_verification():
    email = request.form.get("email", "").strip().lower()

    if not email:
        flash("❌ Email Is Required.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("❌ No Account Found.", "danger")
        return redirect(url_for("auth.login"))

    if user.email_verified:
        flash("✅ Email Already Verified.", "success")
        return redirect(url_for("auth.login"))

    token = generate_email_token(user.email)
    send_verification_email(user.email, token)

    flash("📧 Verification Email Resent.", "info")
    return redirect(url_for("auth.login"))
