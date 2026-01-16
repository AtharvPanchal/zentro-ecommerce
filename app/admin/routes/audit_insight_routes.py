from flask import Blueprint, jsonify
from app.extensions import db
from app.models import AuditInsight
from app.admin.decorators import admin_required, super_admin_required

audit_insight_bp = Blueprint(
    "audit_insight",
    __name__,
    url_prefix="/admin/audit-insights"
)

# -----------------------------
# MARK INSIGHT AS SEEN (ADMIN ✅)
# -----------------------------
@audit_insight_bp.post("/<int:insight_id>/seen")
@admin_required
def mark_insight_seen(insight_id):
    insight = AuditInsight.query.get_or_404(insight_id)

    if insight.is_seen:
        return jsonify({"status": "already_seen"}), 200

    insight.is_seen = True
    db.session.commit()

    return jsonify({"status": "seen"}), 200


# -----------------------------
# ARCHIVE INSIGHT (SUPER ADMIN ✅)
# -----------------------------
@audit_insight_bp.post("/<int:insight_id>/archive")
@super_admin_required
def archive_insight(insight_id):
    insight = AuditInsight.query.get_or_404(insight_id)

    insight.is_archived = True
    db.session.commit()

    return jsonify({"status": "archived"}), 200
