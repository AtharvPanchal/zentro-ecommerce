from flask import render_template, redirect, url_for, request , flash
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Product, Wishlist, ProductRating, ProductReview
from app.main import main_bp
from sqlalchemy import func



#------------------------------------------------
#  MAIN INDEX ROUTE
#------------------------------------------------
@main_bp.route("/")
def index():
    products = (
        Product.query
        .filter(Product.status == "ACTIVE")
        .order_by(Product.created_at.desc())
        .limit(12)
        .all()
    )

    return render_template(
        "user/index.html",
        products=products
    )

#----------------------------------------------------
#   RELATED PRODUCT
#----------------------------------------------------
@main_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)

    related_products = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()

    is_wishlisted = False
    if current_user.is_authenticated:
        is_wishlisted = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product.id
        ).first() is not None

    reviews = ProductReview.query.filter(
        ProductReview.product_id == product_id,
        ProductReview.is_active == True
    ).order_by(ProductReview.created_at.desc()).all()

    return render_template(
        "user/product_detail.html",
        product=product,
        related_products=related_products,
        is_wishlisted=is_wishlisted,
        reviews=reviews
    )



#-------------------------------------------------------
#  RATE PRODUCT
#-------------------------------------------------------
@main_bp.route("/rate-product/<int:product_id>", methods=["POST"])
@login_required
def rate_product(product_id):
    rating_value = request.form.get("rating", type=int)

    if not rating_value or rating_value < 1 or rating_value > 5:
        flash("Invalid rating", "danger")
        return redirect(url_for("main.product_detail", product_id=product_id))

    product = Product.query.get_or_404(product_id)

    rating = ProductRating.query.filter_by(
        product_id=product_id,
        user_id=current_user.id
    ).first()

    if rating:
        rating.rating = rating_value
    else:
        rating = ProductRating(
            product_id=product_id,
            user_id=current_user.id,
            rating=rating_value
        )
        db.session.add(rating)

    db.session.commit()

    # ⭐ single source of truth
    product.update_avg_rating()
    db.session.commit()

    flash("Thanks for rating ⭐", "success")
    return redirect(url_for("main.product_detail", product_id=product_id))




# -------------------------------------------------------
#  ADD PRODUCT REVIEW
# -------------------------------------------------------
@main_bp.route("/add-review/<int:product_id>", methods=["POST"])
@login_required
def add_review(product_id):
    review_text = request.form.get("review_text", "").strip()

    if len(review_text) < 5:
        flash("Review must be at least 5 characters", "danger")
        return redirect(url_for("main.product_detail", product_id=product_id))

    # 🔒 CHECK: existing review by same user
    existing_review = ProductReview.query.filter_by(
        product_id=product_id,
        user_id=current_user.id
    ).first()

    if existing_review:
        # ✏️ UPDATE existing review
        existing_review.review_text = review_text
        existing_review.is_active = False      # re-approve by admin
        existing_review.is_reported = False
        existing_review.report_reason = None

        flash("Your Review Has Been Updated 📝 (Awaiting Approval)", "info")
    else:
        # ➕ ADD new review
        db.session.add(ProductReview(
            product_id=product_id,
            user_id=current_user.id,
            review_text=review_text,
            is_active=False
        ))

        flash("Review Submitted Successfully ✅ (Awaiting Approval)", "success")

    db.session.commit()
    return redirect(url_for("main.product_detail", product_id=product_id))


# -------------------------------------------------------
#  REPORT REVIEW
# -------------------------------------------------------
@main_bp.route("/report-review/<int:review_id>", methods=["POST"])
@login_required
def report_review(review_id):
    review = ProductReview.query.get_or_404(review_id)

    reason = request.form.get("reason")

    if not reason or len(reason.strip()) < 3:
        flash("Please provide a valid report reason", "danger")
        return redirect(url_for("main.product_detail", product_id=review.product_id))

    review.is_reported = True
    review.report_reason = reason.strip()

    db.session.commit()
    flash("Review reported successfully 🚩", "warning")

    return redirect(url_for("main.product_detail", product_id=review.product_id))


# -------------------------------------------------------
#  DELETE OWN REVIEW
# -------------------------------------------------------
@main_bp.route("/delete-review/<int:review_id>", methods=["POST"])
@login_required
def delete_review(review_id):
    review = ProductReview.query.get_or_404(review_id)

    if review.user_id != current_user.id:
        flash("Unauthorized action", "danger")
        return redirect(url_for("main.product_detail", product_id=review.product_id))

    db.session.delete(review)
    db.session.commit()

    flash("Review deleted successfully ❌", "success")
    return redirect(url_for("main.product_detail", product_id=review.product_id))

