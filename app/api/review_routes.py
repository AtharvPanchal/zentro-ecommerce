from flask import request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import ProductReview, Product, Order

from . import api_bp


# =====================================================
# SUBMIT REVIEW (VERIFIED PURCHASE ONLY)
# =====================================================
@api_bp.route("/reviews/submit", methods=["POST"])
@login_required
def submit_review():

    data = request.get_json() or {}

    product_id = data.get("product_id")
    order_id = data.get("order_id")
    rating = data.get("rating")
    review_text = data.get("review_text", "").strip()

    # 1️⃣ BASIC VALIDATION
    if not all([product_id, order_id, rating, review_text]):
        return jsonify(
            success=False,
            message="Missing required fields"
        ), 400

    # 2️⃣ CHECK ORDER OWNERSHIP
    order = Order.query.filter_by(
        id=order_id,
        user_id=current_user.id,
        status="delivered"
    ).first()

    if not order:
        return jsonify(
            success=False,
            message="Invalid or unauthorized order"
        ), 403

    # 3️⃣ CHECK PRODUCT EXISTS
    product = Product.query.get(product_id)
    if not product:
        return jsonify(
            success=False,
            message="Invalid product"
        ), 404

    # 4️⃣ CREATE REVIEW (ADMIN APPROVAL REQUIRED)
    review = ProductReview(
        user_id=current_user.id,
        product_id=product_id,
        order_id=order_id,
        rating=int(rating),
        review_text=review_text,
        is_active=False  # 🔒 ADMIN MUST APPROVE
    )

    db.session.add(review)
    db.session.commit()

    return jsonify(
        success=True,
        message="Review submitted. Pending approval."
    )
