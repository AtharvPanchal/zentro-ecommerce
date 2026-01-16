"""
Safe Admin Creation Script
--------------------------
• Used to PRE-CREATE admin account
• Does NOT load full Flask app
• Only uses DB + config
• Production-safe approach

Run (from project root):
    .\venv\Scripts\python.exe .\scripts\add_admin.py
"""
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask
from werkzeug.security import generate_password_hash
from getpass import getpass

from app.extensions import db
from app.models import Admin


def create_script_app():
    """
    Minimal Flask app only for scripts.
    Avoids loading blueprints, limiter, login manager.
    """
    app = Flask(__name__)
    app.config.from_object("config.DevelopmentConfig")
    db.init_app(app)
    return app


def create_admin():
    app = create_script_app()

    with app.app_context():
        print("\n=== CREATE ADMIN ACCOUNT ===\n")

        email = input("Enter admin email: ").strip().lower()

        # Check if admin already exists
        existing_admin = Admin.query.filter_by(email=email).first()
        if existing_admin:
            print(f"\n❌ Admin with email '{email}' already exists.\n")
            return

        password = getpass("Enter admin password: ")
        confirm_password = getpass("Confirm admin password: ")

        if password != confirm_password:
            print("\n❌ Passwords do not match.\n")
            return

        if len(password) < 8:
            print("\n❌ Password must be at least 8 characters long.\n")
            return

        password_hash = generate_password_hash(password)

        admin = Admin(
            email=email,
            password_hash=password_hash,
            is_active=True
        )

        db.session.add(admin)
        db.session.commit()

        print("\n✅ Admin account created successfully!")
        print(f"📧 Email: {email}")
        print("🔐 Password: securely hashed & stored\n")


if __name__ == "__main__":
    create_admin()
