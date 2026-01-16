from flask import Blueprint

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)

# --------------------------------------------------
# IMPORT & REGISTER ROUTE BLUEPRINTS
# --------------------------------------------------

from app.admin.routes.audit_insight_routes import audit_insight_bp
from app.admin.routes.product_routes import product_bp
from app.admin.routes.category_routes import category_bp

admin_bp.register_blueprint(audit_insight_bp)
admin_bp.register_blueprint(product_bp)
admin_bp.register_blueprint(category_bp)
