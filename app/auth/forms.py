from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from app.auth.validators import is_strong_password


# --------------------------------------------------
# LOGIN FORM
# --------------------------------------------------
class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )

    submit = SubmitField("Login")


# --------------------------------------------------
# FORGOT PASSWORD FORM
# --------------------------------------------------
class ForgotPasswordForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    submit = SubmitField("Send OTP")


# --------------------------------------------------
# RESET PASSWORD FORM
# --------------------------------------------------
class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=6, message="Password must be at least 6 characters")
        ]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match")
        ]
    )

    submit = SubmitField("Reset Password")

    def validate_password(self, field):
        if not is_strong_password(field.data):
            raise ValueError(
                "Password must contain 1 uppercase letter and 1 number"
            )
