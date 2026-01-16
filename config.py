import os


class DevelopmentConfig:
    # --------------------------------------------------
    # CORE
    # --------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-secret-key")
    DEBUG = True

    # --------------------------------------------------
    # DATABASE CONFIG (MYSQL)
    # --------------------------------------------------
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "zentro")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --------------------------------------------------
    # MAIL CONFIG (GMAIL SMTP)
    # --------------------------------------------------
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False") == "True"

    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    # --------------------------------------------------
    # CAPTCHA (Google reCAPTCHA v3)
    # --------------------------------------------------
    RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")
    RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
    RECAPTCHA_SCORE_THRESHOLD = float(
        os.getenv("RECAPTCHA_SCORE_THRESHOLD", 0.5)
    )

    # --------------------------------------------------
    # DEV FLAGS
    # --------------------------------------------------
    RECAPTCHA_DISABLED = os.getenv("RECAPTCHA_DISABLED", "True") == "True"
