from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import current_user, login_required
from app.utils.review_utils import should_auto_flag
from app.models import CartItem

from app.extensions import db
from app.models import (
    Product,
    Wishlist,
    ProductReview,
    Order,
    OrderItem,
    OrderStatus
)

from app.main import main_bp
from sqlalchemy import func
from app.models import Category
from app.models import AttributeType, ProductAttribute



# ------------------------------------------------
#  MAIN INDEX ROUTE
# ------------------------------------------------
@main_bp.route("/")
def index():
    products = (
        Product.query
        .filter(Product.status == "ACTIVE")
        .order_by(Product.created_at.desc())
        .limit(12)
        .all()
    )

    return render_template("user/index.html", products=products)


# ------------------------------------------------
#  PRODUCT LIST PAGE
# ------------------------------------------------
@main_bp.route("/products")
def product_list():
    page = request.args.get("page", 1, type=int)

    products = (
        Product.query
        .filter(Product.status == "ACTIVE")
        .order_by(Product.created_at.desc())
        .paginate(page=page, per_page=20)
    )

    return render_template("user/product_list.html", products=products)




# ------------------------------------------------
# SEARCH RESULTS PAGE
# ------------------------------------------------
@main_bp.route("/search")
def search_page():

    # -----------------------
    # Query parameters
    # -----------------------
    q = request.args.get("q", "").strip()

    price_range = request.args.get("price")
    min_price = None
    max_price = None

    if price_range:
        try:
            parts = price_range.split("-")
            min_price = float(parts[0])
            max_price = float(parts[1])
        except:
            pass

    rating = request.args.get("rating", type=int)

    category = request.args.get("category", type=int)

    brand = request.args.get("brand", "").strip()

    in_stock = request.args.get("stock")

    sort = request.args.get("sort")

    page = request.args.get("page", 1, type=int)

    # -----------------------
    # Base query
    # -----------------------
    query = Product.query.filter(Product.status == "ACTIVE")

    # -----------------------
    # Dynamic Attribute Filters (PHASE-7 PRO)
    # -----------------------

    # Load attribute types for selected category
    attributes = []

    if category:
        attributes = AttributeType.query.filter_by(category_id=category).all()

        # Load possible values for UI
        for attr in attributes:
            values = (
                db.session.query(ProductAttribute.value)
                .join(Product)
                .filter(
                    Product.category_id == category,
                    ProductAttribute.attribute_id == attr.id
                )
                .distinct()
                .all()
            )

            attr.values = [v[0] for v in values]

    # Apply dynamic filters
    for attr in attributes:

        value = request.args.get(attr.slug)

        if value:
            query = query.join(ProductAttribute).join(AttributeType).filter(
                AttributeType.id == attr.id,
                ProductAttribute.value == value
            )


        

    # -----------------------
    # Search keyword
    # -----------------------
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))

    # -----------------------
    # Price filter
    # -----------------------
    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # -----------------------
    # Rating filter
    # -----------------------
    if rating:
        query = query.filter(Product.avg_rating >= rating)

    # -----------------------
    # Category filter
    # -----------------------
    if category:
        query = query.filter(Product.category_id == category)

    # -----------------------
    # Brand filter
    # -----------------------
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))

    # -----------------------
    # Stock filter
    # -----------------------
    if in_stock:
        query = query.filter(Product.stock > 0)

    # -----------------------
    # Sorting Engine (PHASE 5)
    # -----------------------

    if sort == "popularity":
        query = query.order_by(Product.rating_count.desc())

    elif sort == "price_low":
        query = query.order_by(Product.price.asc())

    elif sort == "price_high":
        query = query.order_by(Product.price.desc())

    elif sort == "rating":
        query = query.order_by(Product.avg_rating.desc())

    elif sort == "newest":
        query = query.order_by(Product.created_at.desc())

    else:
        # default sorting
        query = query.order_by(Product.created_at.desc())

    # -----------------------
    # Categories for filter UI
    # -----------------------
    categories = Category.query.filter(
        Category.status == "ACTIVE"
    ).order_by(Category.name).all()

    # -----------------------
    # Pagination
    # -----------------------
    pagination = query.paginate(page=page, per_page=20)

    # -----------------------
    # Render page
    # -----------------------
    return render_template(
        "user/search_results.html",
        products=pagination.items,
        pagination=pagination,
        query=q,
        total=pagination.total,
        current_sort=sort,
        categories=categories,
        attributes=attributes
    )

# ----------------------------------------------------
#  PRODUCT DETAIL
# ----------------------------------------------------
@main_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.filter_by(
        id=product_id,
        status="ACTIVE"
    ).first_or_404()

    avg_rating = product.avg_rating or 0
    rating_count = product.rating_count or 0



    is_out_of_stock = product.stock is not None and product.stock <= 0

    # -----------------------------
    # Stock / Availability Guard
    # -----------------------------
    if product.stock is not None and product.stock <= 0:
        flash("Product currently out of stock", "warning")



    # -----------------------------
    # Related Products
    # -----------------------------
    related_products = (
        Product.query
        .filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.status == "ACTIVE"
        )
        .order_by(Product.created_at.desc())
        .limit(4)
        .all()
    )

    # -----------------------------
    # Wishlist Status
    # -----------------------------
    is_wishlisted = False
    if current_user.is_authenticated:
        is_wishlisted = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product.id
        ).first() is not None


    # -----------------------------
    # Verified Purchase Flag (SAFE for GET)
    # -----------------------------
    user_has_purchased = False

    if current_user.is_authenticated:
        user_has_purchased = (
                db.session.query(OrderItem.id)
                .join(OrderItem.order)
                .filter(
                    Order.user_id == current_user.id,
                    Order.status == OrderStatus.DELIVERED.value,
                    OrderItem.product_id == product_id
                )
                .first()
                is not None
        )

    # -----------------------------
    # Reviews (approved only)
    # -----------------------------
    reviews = ProductReview.query.filter(
        ProductReview.product_id == product.id,
        ProductReview.is_active == True,
        ProductReview.is_deleted == False,
        ProductReview.review_text.isnot(None)
    ).order_by(ProductReview.created_at.desc()).all()


    # -----------------------------
    # Rating Breakdown (Phase E)
    # -----------------------------
    rating_breakdown_raw = (
        db.session.query(
            ProductReview.rating,
            func.count(ProductReview.id)
        )
        .filter(
            ProductReview.product_id == product.id,
            ProductReview.is_active == True,
            ProductReview.is_deleted == False,
            ProductReview.rating.isnot(None)
        )
        .group_by(ProductReview.rating)
        .all()
    )

    # Convert to dict {5: 10, 4: 3, ...}
    rating_map = {rating: count for rating, count in rating_breakdown_raw}

    # Ensure all 1–5 stars exist (even if 0)
    rating_breakdown = [
        (star, rating_map.get(star, 0))
        for star in range(5, 0, -1)
    ]


    # -----------------------------
    # User specific flags
    # -----------------------------
    user_review = None

    if current_user.is_authenticated:
        user_review = ProductReview.query.filter(
            ProductReview.product_id == product.id,
            ProductReview.user_id == current_user.id,
            ProductReview.is_deleted == False
        ).first()

    return render_template(
        "user/product_detail.html",
        product=product,
        avg_rating=round(avg_rating, 1),
        rating_count=rating_count,
        related_products=related_products,
        is_wishlisted=is_wishlisted,
        reviews=reviews,
        user_review=user_review,
        is_out_of_stock=is_out_of_stock,
        user_has_purchased=user_has_purchased,
        rating_breakdown=rating_breakdown
    )


# -------------------------------------------------------
#  ADD PRODUCT REVIEW (PHASE-3 INTELLIGENCE)
# -------------------------------------------------------
@main_bp.route("/add-review/<int:product_id>", methods=["POST"])
@login_required
def add_review(product_id):

    review_text = request.form.get("review_text", "").strip()

    if len(review_text) < 5:
        flash("Review must be at least 5 characters", "danger")
        return redirect(url_for("main.product_detail", product_id=product_id))

    # --------------------------------------------------
    # ✅ VERIFIED PURCHASE CHECK (AMAZON RULE)
    # --------------------------------------------------
    order_item = (
        db.session.query(OrderItem)
        .join(OrderItem.order)
        .filter(
            Order.user_id == current_user.id,
            Order.status == OrderStatus.DELIVERED.value,
            OrderItem.product_id == product_id
        )
        .first()
    )

    if not order_item:
        flash("Only Verified Purchasers Can Write a Review", "danger")
        return redirect(url_for("main.product_detail", product_id=product_id))

    order_id = order_item.order_id


    # --------------------------------------------------
    # 🧠 AUTO-FLAGGING (BASIC NLP)
    # --------------------------------------------------
    auto_flag = should_auto_flag(review_text)

    # --------------------------------------------------
    # 🔒 EXISTING REVIEW CHECK
    # --------------------------------------------------
    existing_review = ProductReview.query.filter_by(
        product_id=product_id,
        user_id=current_user.id,
        is_deleted=False
    ).first()

    if existing_review:
        existing_review.review_text = review_text
        existing_review.is_active = False  # ALWAYS require admin approval
        existing_review.is_deleted = False
        existing_review.is_reported = auto_flag
        existing_review.report_reason = (
            "Auto-flagged content" if auto_flag else None
        )

        flash("Review Has Been Updated Successfully 📝 (Awaiting approval)", "info")

    else:
        db.session.add(ProductReview(
            product_id=product_id,
            user_id=current_user.id,
            order_id=order_id,
            review_text=review_text,
            is_active=False,
            is_reported=auto_flag,
            report_reason="Auto-flagged content" if auto_flag else None
        ))

        flash("Review Submitted Successfully ✅ (Awaiting approval)", "success")

    db.session.commit()

    # 🔁 Recalculate rating immediately after edit
    product = Product.query.get(product_id)
    if product:
        product.update_avg_rating()
        db.session.commit()

    return redirect(url_for("main.product_detail", product_id=product_id))


# -------------------------------------------------------
#  RATE PRODUCT (PHASE-3 TRUST SAFE)
# -------------------------------------------------------
@main_bp.route("/rate-product/<int:product_id>", methods=["POST"])
@login_required
def rate_product(product_id):

    rating_value = request.form.get("rating", type=int)

    if not rating_value or rating_value not in range(1, 6):
        flash("Invalid rating", "danger")
        return redirect(url_for("main.product_detail", product_id=product_id))

    # VERIFIED PURCHASE
    order_item = (
        db.session.query(OrderItem)
        .join(OrderItem.order)
        .filter(
            Order.user_id == current_user.id,
            Order.status == OrderStatus.DELIVERED.value,
            OrderItem.product_id == product_id
        )
        .first()
    )

    if not order_item:
        flash("Only verified buyers can rate this product", "danger")
        return redirect(url_for("main.product_detail", product_id=product_id))

    order_id = order_item.order_id

    review = ProductReview.query.filter_by(
        product_id=product_id,
        user_id=current_user.id,
        is_deleted=False
    ).first()

    if review:
        review.rating = rating_value
        review.is_deleted = False  # safety restore if previously deleted

    else:
        review = ProductReview(
            product_id=product_id,
            user_id=current_user.id,
            order_id=order_id,
            rating=rating_value,
            review_text=None,
            is_active=True
        )
        db.session.add(review)

    db.session.commit()

    product = Product.query.get(product_id)
    if product:
        product.update_avg_rating()
    db.session.commit()

    flash("Rating Submitted Successfully ⭐", "success")
    return redirect(url_for("main.product_detail", product_id=product_id))


# -------------------------------------------------------
#  REPORT REVIEW (USER)
# -------------------------------------------------------
@main_bp.route("/report-review/<int:review_id>", methods=["POST"])
@login_required
def report_review(review_id):
    review = ProductReview.query.get_or_404(review_id)

    if review.is_deleted:
        flash("Cannot Report Deleted Review", "danger")
        return redirect(url_for("main.product_detail", product_id=review.product_id))

    if review.user_id == current_user.id:
        flash("You Cannot Report Your Own Review", "danger")
        return redirect(url_for("main.product_detail", product_id=review.product_id))

    # Prevent duplicate reporting
    if review.is_reported:
        flash("This Review Is Already Reported", "info")
        return redirect(url_for("main.product_detail", product_id=review.product_id))

    reason = request.form.get("reason", "").strip()

    if len(reason) < 3:
        flash("Please Provide A Valid Reason", "danger")
        return redirect(url_for("main.product_detail", product_id=review.product_id))

    review.is_reported = True
    review.report_reason = reason

    db.session.commit()
    flash("Review Reported Successfully 🚩", "warning")
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

    review.is_deleted = True
    review.is_active = False

    product = Product.query.get(review.product_id)
    if product:
        product.update_avg_rating()

    db.session.commit()

    flash("Review Deleted Successfully ❌", "success")
    return redirect(url_for("main.product_detail", product_id=review.product_id))


# -------------------------------------------------------
#  TOGGLE WISHLIST (AJAX)
# -------------------------------------------------------
@main_bp.route("/wishlist/toggle/<int:product_id>", methods=["POST"])
@login_required
def toggle_wishlist(product_id):
    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return {"success": True, "added": False}

    db.session.add(Wishlist(
        user_id=current_user.id,
        product_id=product_id
    ))
    db.session.commit()

    return {"success": True, "added": True}


# --------------------------------------------------------
#  QUICK VIEW PRODUCT
# --------------------------------------------------------
@main_bp.route("/api/product/<int:product_id>")
def quick_view_product(product_id):
    product = Product.query.filter_by(
        id=product_id,
        status="ACTIVE"
    ).first_or_404()

    image = product.image_list[0] if product.image_list else None

    return jsonify({
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "description": product.description or "",
        "image": image,
        "url": url_for("main.product_detail", product_id=product.id)
    })


# -------------------------------------------------------
#  ADD TO CART (AJAX API)
# -------------------------------------------------------
@main_bp.route("/api/cart/add", methods=["POST"])
@login_required
def api_add_to_cart():

    data = request.get_json()

    product_id = data.get("product_id")
    quantity = int(data.get("quantity", 1))

    product = Product.query.filter_by(
        id=product_id,
        status="ACTIVE"
    ).first()

    if not product:
        return jsonify(success=False, message="Product not found")

    if quantity <= 0:
        return jsonify(success=False, message="Invalid quantity")

    if product.stock < quantity:
        return jsonify(success=False, message="Insufficient stock")

    existing = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    if existing:
        new_qty = existing.quantity + quantity

        if new_qty > product.stock:
            return jsonify(success=False, message="Stock limit exceeded")

        existing.quantity = new_qty

    else:
        db.session.add(CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity,
            price_at_add=product.price
        ))

    db.session.commit()

    return jsonify(success=True)


# -------------------------------------------------------
#  GET CART DATA (FOR BADGE & UI)
# -------------------------------------------------------
@main_bp.route("/api/cart")
@login_required
def api_get_cart():

    items = CartItem.query.filter_by(
        user_id=current_user.id
    ).all()

    cart_data = []

    for item in items:
        cart_data.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": float(item.price_at_add)
        })

    return jsonify(success=True, cart=cart_data)