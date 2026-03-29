from flask import Blueprint

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)

# --------------------------------------------------
# REGISTER SUB-BLUEPRINTS
# --------------------------------------------------
from app.admin.routes.audit_insight_routes import audit_insight_bp
from app.admin.routes.product_routes import product_bp
from app.admin.routes.category_routes import category_bp

admin_bp.register_blueprint(audit_insight_bp)
admin_bp.register_blueprint(product_bp)
admin_bp.register_blueprint(category_bp)

# --------------------------------------------------
# IMPORT DIRECT ADMIN ROUTES (VERY IMPORTANT)
# --------------------------------------------------
from app.admin.routes import activity_routes
from app.admin.routes import audit_analytics
