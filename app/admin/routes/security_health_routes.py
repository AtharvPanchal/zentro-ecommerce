from flask import render_template
from app.admin.decorators import admin_required
from app.services.security_health_service import SecurityHealthService
from app.extensions import db
from app.admin import admin_bp   

@admin_bp.route("/security-health/")
@admin_required
def security_health():
    data = SecurityHealthService.analyze_last_24h(db)
    return render_template(
        "admin/security_health.html",
        health=data
    )

# STEP-5: Export compliance report as JSON (read-only)
@admin_bp.route("/security-health/report")
@admin_required
def security_health_report():
    data = SecurityHealthService.analyze_last_24h(db)
    return data["compliance_report"]
