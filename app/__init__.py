from flask import Flask, redirect, url_for, flash, request
from flask_limiter.errors import RateLimitExceeded

from app.extensions import db, migrate, login_manager, mail, limiter, scheduler, csrf


from app.services.audit_retention import auto_archive_old_audit_logs
from app.services.audit_cleanup_service import cleanup_old_archived_audit_logs
from app.services.system_jobs import cleanup_expired_otps

from app.utils.time_utils import (
    timeago_ist,
    to_ist,
    format_ist,
    IST
)

import os


# --------------------------------------------------
# CREATE APP
# --------------------------------------------------
def create_app():
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "..", "templates"),
        static_folder=os.path.join(BASE_DIR, "..", "static"),
    )

    # --------------------------------------------------
    # LOAD CONFIG
    # --------------------------------------------------
    app.config.from_object("config.DevelopmentConfig")

    # --------------------------------------------------
    # INIT EXTENSIONS
    # --------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    # --------------------------------------------------
    # INIT SCHEDULER
    # --------------------------------------------------
    scheduler.init_app(app)

    # 🔁 90 DAYS → AUTO ARCHIVE AUDIT LOGS (01:30 AM)
    scheduler.add_job(
        id="audit_auto_archive_90_days",
        func=auto_archive_old_audit_logs,
        trigger="cron",
        hour=1,
        minute=30,
        replace_existing=True
    )

    # 🔁 180 DAYS → AUTO DELETE ARCHIVED LOGS (02:00 AM)
    scheduler.add_job(
        id="audit_cleanup_180_days",
        func=lambda: cleanup_old_archived_audit_logs(days=180),
        trigger="cron",
        hour=2,
        minute=0,
        replace_existing=True
    )

    # 🔁 CLEANUP EXPIRED OTPS (EVERY 6 HOURS)
    scheduler.add_job(
        id="cleanup_expired_otps",
        func=cleanup_expired_otps,
        trigger="interval",
        hours=6,
        replace_existing=True
    )

    if not scheduler.running:
        scheduler.start()

    # --------------------------------------------------
    # RATE LIMIT ERROR HANDLER
    # --------------------------------------------------
    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(e):
        flash(
            "⏳ Too many requests. Please wait a few minutes before trying again.",
            "danger"
        )

        path = request.path

        if path.startswith("/forgot-password"):
            return redirect(url_for("auth.forgot_password"))

        if path.startswith("/auth"):
            return redirect(url_for("auth.login"))

        if path.startswith("/admin"):
            return redirect(url_for("admin.login"))

        return redirect(url_for("auth.login"))

    # --------------------------------------------------
    # REGISTER BLUEPRINTS
    # --------------------------------------------------
    from app.auth import auth_bp
    from app.main import main_bp
    from app.admin import admin_bp
    from app.user import user_bp
    from app.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    csrf.exempt(api_bp)
    app.register_blueprint(api_bp)

    #  AUDIT INSIGHT ROUTES (MISSING FIX)
    from app.admin.routes.audit_insight_routes import audit_insight_bp
    app.register_blueprint(audit_insight_bp)

    # --------------------------------------------------
    # JINJA FILTERS
    # --------------------------------------------------
    app.jinja_env.filters["timeago"] = timeago_ist
    app.jinja_env.filters["to_ist"] = to_ist
    app.jinja_env.filters["format_ist"] = format_ist

    # --------------------------------------------------
    # CLI COMMANDS
    # --------------------------------------------------
    from app.commands import cleanup_otps_command
    app.cli.add_command(cleanup_otps_command)

    return app
