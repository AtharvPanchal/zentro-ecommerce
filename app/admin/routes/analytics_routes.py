from flask import render_template
from app.admin import admin_bp
from app.admin.decorators import admin_required


# --------------------------------------------------
# ADMIN ANALYTICS PAGE
# --------------------------------------------------
@admin_bp.route("/analytics")
@admin_required
def analytics():
    return render_template("admin/analytics.html")
