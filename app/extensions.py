from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask import session

# 🔐 RATE LIMITER
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_apscheduler import APScheduler
from flask_wtf import CSRFProtect

csrf = CSRFProtect()


scheduler = APScheduler()


# --------------------------------------------------
# DATABASE
# --------------------------------------------------
db = SQLAlchemy()
migrate = Migrate()


# --------------------------------------------------
# AUTHENTICATION (Flask-Login)
# --------------------------------------------------
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "🔐 Please login to continue"
login_manager.login_message_category = "warning"
login_manager.refresh_view = "auth.login"
login_manager.needs_refresh_message = "🔒 Session expired. Please login again."
login_manager.needs_refresh_message_category = "info"



# --------------------------------------------------
# RATE LIMITER (GLOBAL)
# --------------------------------------------------
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://"
)


# NOTE: init_app(app) will be called in app/__init__.py


# --------------------------------------------------
# MAIL
# --------------------------------------------------
mail = Mail()


# --------------------------------------------------
# USER LOADER (SESSION VERSION SAFE CHECK)
# --------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    """
    Loads user from session.
    If session_version mismatch is detected, user is treated as logged out.
    """
    from app.models import User

    try:
        user = User.query.get(int(user_id))
    except Exception:
        return None

    if not user:
        return None

    session_version = session.get("session_version")
    if session_version is not None and session_version != user.session_version:
        return None

    return user
