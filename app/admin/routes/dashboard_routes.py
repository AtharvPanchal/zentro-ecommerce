from datetime import datetime
from sqlalchemy import func
from sqlalchemy import or_
from flask import render_template, redirect, url_for, flash
from flask import request
from app.admin import admin_bp
from app.admin.decorators import admin_required
from app.extensions import db
from app.models import User, Order, Product, Admin, ProductReview


# ==================================================
# ADMIN DASHBOARD
# ==================================================
@admin_bp.route("/dashboard")
@admin_required
def dashboard():

    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    month_start = datetime(now.year, now.month, 1)

    # -----------------------------
    # USERS
    # -----------------------------
    total_users = db.session.query(func.count(User.id)).scalar()
    active_users = db.session.query(func.count(User.id)).filter(User.is_active == True).scalar()
    locked_users = db.session.query(func.count(User.id)).filter(User.lock_until > now).scalar()
    new_users_today = db.session.query(func.count(User.id)).filter(User.created_at >= today_start).scalar()

    # -----------------------------
    # ORDERS
    # -----------------------------
    total_orders = db.session.query(func.count(Order.id)).scalar()
    today_orders = db.session.query(func.count(Order.id)).filter(Order.created_at >= today_start).scalar()

    pending_orders = db.session.query(func.count(Order.id)).filter(Order.status == "pending").scalar()
    packed_orders = db.session.query(func.count(Order.id)).filter(Order.status == "packed").scalar()
    shipped_orders = db.session.query(func.count(Order.id)).filter(Order.status == "shipped").scalar()
    delivered_orders = db.session.query(func.count(Order.id)).filter(Order.status == "delivered").scalar()
    cancelled_orders = db.session.query(func.count(Order.id)).filter(Order.status == "cancelled").scalar()

    # -----------------------------
    # REVENUE
    # -----------------------------
    total_revenue = (
        db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(Order.payment_status == "paid")
        .scalar()
    )

    today_revenue = (
        db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(Order.payment_status == "paid", Order.created_at >= today_start)
        .scalar()
    )

    monthly_revenue = (
        db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(Order.payment_status == "paid", Order.created_at >= month_start)
        .scalar()
    )

    # -----------------------------
    # PRODUCTS
    # -----------------------------
    total_products = db.session.query(func.count(Product.id)).scalar()

    active_products = (
        db.session.query(func.count(Product.id))
        .filter(Product.status == "ACTIVE")
        .scalar()
    )

    inactive_products = (
        db.session.query(func.count(Product.id))
        .filter(Product.status == "INACTIVE")
        .scalar()
    )



    # -----------------------------
    # RECENT ORDERS
    # -----------------------------
    recent_orders_query = (
        Order.query
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )

    recent_orders = []
    for order in recent_orders_query:
        recent_orders.append({
            "order_id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "total_amount": order.total_amount,
            "status": order.status,
            "created_at": order.created_at
        })

    # -----------------------------
    # ALERTS
    # -----------------------------
    locked_admins_query = Admin.query.filter(Admin.lock_until > now).all()

    locked_admins = []
    for admin in locked_admins_query:
        locked_admins.append({
            "email": admin.email,
            "lock_until": admin.lock_until
        })


    # -----------------------------
    # REVIEW MODERATION COUNTS ✅
    # -----------------------------
    pending_review_count = db.session.query(
        func.count(ProductReview.id)
    ).filter(ProductReview.is_active == False).scalar()

    reported_review_count = db.session.query(
        func.count(ProductReview.id)
    ).filter(ProductReview.is_reported == True).scalar()

    # -----------------------------
    # FINAL DASHBOARD DATA
    # -----------------------------
    dashboard_data = {
        "users": {
            "total": total_users,
            "active": active_users,
            "locked": locked_users,
            "new_today": new_users_today
        },
        "orders": {
            "total": total_orders,
            "today": today_orders,
            "pending": pending_orders,
            "packed": packed_orders,
            "shipped": shipped_orders,
            "delivered": delivered_orders,
            "cancelled": cancelled_orders
        },
        "revenue": {
            "total": total_revenue,
            "today": today_revenue,
            "this_month": monthly_revenue
        },
        "products": {
            "total": total_products,
            "active": active_products,
            "inactive": inactive_products
        },
        "reviews": {
            "pending": pending_review_count,
            "reported": reported_review_count
        },
        "recent_orders": recent_orders,
        "alerts": {
            "locked_admins": locked_admins
        }
    }

    return render_template(
        "admin/dashboard.html",
        dashboard=dashboard_data
    )




# ==================================================
# REVIEW MODERATION (FILTER + SEARCH + SORT + PAGINATION)
# ==================================================
@admin_bp.route("/reviews")
@admin_required
def review_moderation():

    filter_by = request.args.get("filter", "all")
    search = request.args.get("search", "").strip()
    sort = request.args.get("sort", "")
    page = request.args.get("page", 1, type=int)

    query = (
        ProductReview.query
        .join(User)
        .join(Product)
    )

    # ---------------- FILTER ----------------
    if filter_by == "pending":
        query = query.filter(
            ProductReview.is_active == False,
            ProductReview.is_reported == False
        )

    elif filter_by == "reported":
        query = query.filter(
            ProductReview.is_reported == True
        )

    # ---------------- SEARCH ----------------
    if search:
        query = query.filter(
            or_(
                User.email.ilike(f"%{search}%"),
                Product.name.ilike(f"%{search}%")
            )
        )

    # ---------------- SORT ----------------
    if sort == "rating_high":
        query = query.order_by(ProductReview.rating.desc())
    elif sort == "rating_low":
        query = query.order_by(ProductReview.rating.asc())
    else:
        query = query.order_by(ProductReview.created_at.desc())

    # ---------------- PAGINATION ----------------
    pagination = query.paginate(
        page=page,
        per_page=20,
        error_out=False
    )

    return render_template(
        "admin/reviews.html",
        reviews=pagination.items,
        pagination=pagination,
        active_filter=filter_by,
        search=search,
        sort=sort
    )



# ==================================================
# ADMIN REVIEW APPROVE
# ==================================================
@admin_bp.route("/review/approve/<int:review_id>", methods=["POST"])
@admin_required
def approve_review(review_id):
    review = ProductReview.query.get_or_404(review_id)
    review.is_active = True
    review.is_reported = False
    review.report_reason = None
    db.session.commit()

    flash("Review approved ✅", "success")
    return redirect(url_for("admin.review_moderation"))

# ==================================================
# ADMIN REVIEW HIDE
# ==================================================
@admin_bp.route("/review/hide/<int:review_id>", methods=["POST"])
@admin_required
def hide_review(review_id):
    review = ProductReview.query.get_or_404(review_id)
    review.is_active = False
    db.session.commit()

    flash("Review hidden ❌", "warning")
    return redirect(url_for("admin.review_moderation"))

# ==================================================
# ADMIN REVIEW DELETE
# ==================================================
@admin_bp.route("/review/delete/<int:review_id>", methods=["POST"])
@admin_required
def delete_review_admin(review_id):
    review = ProductReview.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()

    flash("Review deleted permanently 🗑️", "danger")
    return redirect(url_for("admin.review_moderation"))
