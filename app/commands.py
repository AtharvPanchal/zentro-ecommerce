import click
from flask.cli import with_appcontext

from app.services.otp_service import cleanup_otps


@click.command("cleanup-otps")
@with_appcontext
def cleanup_otps_command():
    deleted = cleanup_otps()
    click.echo(f"✅ OTP cleanup completed. Deleted {deleted} rows.")
