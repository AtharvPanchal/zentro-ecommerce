from flask import current_app, url_for
from flask_mail import Message
from app.extensions import mail
from app.models import Admin



# --------------------------------------------------
# GENERIC EMAIL SENDER (ADMIN / USER)
# --------------------------------------------------
def send_email(to_email: str, subject: str, html: str) -> None:
    sender = current_app.config.get(
        "MAIL_DEFAULT_SENDER",
        "ZENTRO <no-reply@zentro.test>"
    )

    msg = Message(
        subject=subject,
        sender=sender,
        recipients=[to_email],
        html=html
    )

    mail.send(msg)


# --------------------------------------------------
# SEND OTP EMAIL (FORGOT PASSWORD)
# --------------------------------------------------
def send_otp_email(to_email: str, otp_code: str) -> None:
    subject = "🔐 ZENTRO | Your OTP for Password Reset"
    sender = current_app.config.get(
        "MAIL_DEFAULT_SENDER",
        "ZENTRO <no-reply@zentro.test>"
    )

    body = f"""
Hello,

Your One-Time Password (OTP) for resetting your ZENTRO account password is:

OTP: {otp_code}

⏳ This OTP is valid for 5 minutes.

If you did not request this, please ignore this email.

Regards,
ZENTRO Security Team
"""

    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:auto;
                background:#ffffff;border-radius:10px;padding:24px;border:1px solid #eee">
        <h2 style="color:#2d2a26;margin-bottom:10px;">ZENTRO Security Verification</h2>

        <p>Hello,</p>

        <p>You requested to reset your password. Use the OTP below:</p>

        <div style="font-size:26px;font-weight:bold;letter-spacing:4px;
                    background:#f8f6f2;padding:14px;text-align:center;
                    border-radius:8px;color:#2d2a26;margin:20px 0;">
            {otp_code}
        </div>

        <p style="color:#555;">
            ⏳ <b>This OTP is valid for 5 minutes.</b>
        </p>

        <p style="color:#777;font-size:13px;">
            If you did not request this password reset, please ignore this email.
        </p>

        <hr style="margin:24px 0;border:none;border-top:1px solid #eee;">

        <p style="font-size:13px;color:#999;">
            ZENTRO Security Team<br>
            This is an automated email — please do not reply.
        </p>
    </div>
    """

    msg = Message(
        subject=subject,
        sender=sender,
        recipients=[to_email],
        body=body,
        html=html
    )

    mail.send(msg)


# --------------------------------------------------
# SEND PASSWORD RESET SUCCESS EMAIL (IP + DEVICE)
# --------------------------------------------------
def send_password_reset_success_email(
    to_email: str,
    ip_address: str,
    device: str
) -> None:
    subject = "✅ ZENTRO | Password Reset Successful"
    sender = current_app.config.get(
        "MAIL_DEFAULT_SENDER",
        "ZENTRO <no-reply@zentro.test>"
    )

    body = f"""
Hello,

Your ZENTRO account password has been successfully reset.

Security details:
IP Address: {ip_address}
Device: {device}

If this was not you, please contact our support team immediately.

Regards,
ZENTRO Security Team
"""

    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:auto;
                background:#ffffff;border-radius:10px;padding:24px;border:1px solid #eee">

        <h2 style="color:#2d2a26;">Password Reset Successful</h2>

        <p>Your password has been updated successfully.</p>

        <div style="background:#f8f6f2;padding:14px;border-radius:8px;
                    font-size:14px;color:#333;margin:16px 0;">
            <b>Security Information</b><br>
            IP Address: {ip_address}<br>
            Device: {device}
        </div>

        <p style="color:#b91c1c;font-size:14px;">
            If this was not you, please contact our support team immediately.
        </p>

        <hr style="margin:24px 0;border:none;border-top:1px solid #eee;">

        <p style="font-size:13px;color:#999;">
            ZENTRO Security Team<br>
            This is an automated email — please do not reply.
        </p>
    </div>
    """

    msg = Message(
        subject=subject,
        sender=sender,
        recipients=[to_email],
        body=body,
        html=html
    )

    mail.send(msg)



# --------------------------------------------------
# SEND SIGNUP EMAIL VERIFICATION (NEW)
# --------------------------------------------------
def send_verification_email(
    to_email: str,
    verification_token: str
) -> None:
    subject = "📧 ZENTRO | Verify Your Email Address"
    sender = current_app.config.get(
        "MAIL_DEFAULT_SENDER",
        "ZENTRO <no-reply@zentro.test>"
    )

    verify_url = url_for(
        "auth.verify_email",
        token=verification_token,
        _external=True
    )

    body = f"""
Hello,

Thank you for creating a ZENTRO account.

Please verify your email address by clicking the link below:

{verify_url}

If you did not create this account, please ignore this email.

Regards,
ZENTRO Security Team
"""

    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:auto;
                background:#ffffff;border-radius:10px;padding:24px;border:1px solid #eee">

        <h2 style="color:#2d2a26;">Verify Your Email Address</h2>

        <p>Welcome to <b>ZENTRO</b> 👋</p>

        <p>Please confirm your email address to activate your account.</p>

        <div style="text-align:center;margin:24px 0;">
            <a href="{verify_url}"
               style="background:#2d2a26;color:#ffffff;
                      padding:12px 24px;border-radius:8px;
                      text-decoration:none;font-weight:bold;">
                Verify Email
            </a>
        </div>

        <p style="color:#777;font-size:13px;">
            If you did not create this account, you can safely ignore this email.
        </p>

        <hr style="margin:24px 0;border:none;border-top:1px solid #eee;">

        <p style="font-size:13px;color:#999;">
            ZENTRO Security Team<br>
            This is an automated email — please do not reply.
        </p>
    </div>
    """

    msg = Message(
        subject=subject,
        sender=sender,
        recipients=[to_email],
        body=body,
        html=html
    )

    mail.send(msg)

def send_user_account_lock_email(
    to_email: str,
    username: str,
    lock_minutes: int,
    ip_address: str,
    device: str
):
    subject = "🔒 ZENTRO | Account Temporarily Locked"

    html = f"""
    <div style="font-family:Arial;max-width:520px;margin:auto;
                background:#fff;padding:24px;border-radius:10px;border:1px solid #eee">
        <h2 style="color:#b91c1c;">Account Locked</h2>
        <p>Hello <b>{username}</b>,</p>

        <p>Multiple failed login attempts detected.</p>

        <div style="background:#f3f4f6;padding:14px;border-radius:8px;">
            <b>Lock duration:</b> {lock_minutes} minutes<br>
            <b>IP:</b> {ip_address}<br>
            <b>Device:</b> {device}
        </div>

        <p>If this wasn’t you, reset your password immediately.</p>
    </div>
    """

    send_email(to_email, subject, html)


def send_admin_otp_email(to_email: str, otp_code: str) -> None:
    subject = "🔐 ZENTRO Admin | Password Reset OTP"

    html = f"""
    <div style="font-family:Arial;max-width:520px;margin:auto;
                background:#ffffff;border-radius:10px;padding:24px;
                border:1px solid #eee">
        <h2>Admin Password Reset</h2>

        <p>Use the OTP below to reset the admin password:</p>

        <div style="font-size:28px;font-weight:bold;letter-spacing:4px;
                    background:#f3f4f6;padding:14px;text-align:center;
                    border-radius:8px;">
            {otp_code}
        </div>

        <p><b>Valid for 5 minutes.</b></p>

        <hr>
        <p style="font-size:12px;color:#6b7280;">
            ZENTRO Security • Automated message
        </p>
    </div>
    """

    send_email(to_email, subject, html)

def send_admin_password_reset_success_email(to_email: str) -> None:
    subject = "✅ ZENTRO Admin | Password Reset Successful"

    html = """
    <div style="font-family:Arial;max-width:520px;margin:auto;
                background:#ffffff;border-radius:10px;padding:24px;
                border:1px solid #eee">
        <h2>Password Updated Successfully</h2>

        <p>Your <b>admin account password</b> was changed.</p>

        <p style="color:#b91c1c;">
            If this was not you, contact the system owner immediately.
        </p>

        <hr>
        <p style="font-size:12px;color:#6b7280;">
            ZENTRO Security • Automated message
        </p>
    </div>
    """

    send_email(to_email, subject, html)

def send_admin_account_lock_email(
    to_email: str,
    lock_minutes: int,
    ip_address: str,
    device: str
) -> None:
    subject = "🚨 ZENTRO Admin | Account Temporarily Locked"

    html = f"""
    <div style="font-family:Arial;max-width:520px;margin:auto;
                background:#ffffff;border-radius:10px;padding:24px;
                border:1px solid #eee">
        <h2 style="color:#b91c1c;">Admin Account Locked</h2>

        <p>Multiple failed login attempts detected.</p>

        <div style="background:#f3f4f6;padding:14px;border-radius:8px;">
            <b>Lock duration:</b> {lock_minutes} minutes<br>
            <b>IP:</b> {ip_address}<br>
            <b>Device:</b> {device}
        </div>

        <hr>
        <p style="font-size:12px;color:#6b7280;">
            ZENTRO Security • Automated alert
        </p>
    </div>
    """

    send_email(to_email, subject, html)
