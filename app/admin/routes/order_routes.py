from flask import render_template, request
from flask_login import login_required
from app.admin.decorators import admin_required
from app.admin.routes import admin_bp
from datetime import datetime
from app.models import Order, OrderItem, OrderTimeline, User
from app.services.order_service import update_order_status
from flask import redirect, url_for, flash
from flask_login import current_user  # ADD THIS IMPORT

# -------------------------------------------------------
# 🔥 ADMIN ORDER LISTING (FLIPKART LEVEL)
# -------------------------------------------------------

@admin_bp.route("/orders")
@login_required
@admin_required
def admin_order_list():

    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    payment_status = request.args.get("payment_status", "").strip()
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = Order.query

    # --------------------------------------------------
    # 🔎 SEARCH BY ORDER NUMBER
    # --------------------------------------------------
    if search:
        query = query.filter(Order.order_number.ilike(f"%{search}%"))

    # --------------------------------------------------
    # 📦 FILTER BY STATUS
    # --------------------------------------------------
    if status:
        query = query.filter(Order.status == status)

    # --------------------------------------------------
    # 💳 FILTER BY PAYMENT STATUS
    # --------------------------------------------------
    if payment_status:
        query = query.filter(Order.payment_status == payment_status)

    # --------------------------------------------------
    # 📅 DATE RANGE FILTER
    # --------------------------------------------------
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Order.created_at >= start)
        except:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Order.created_at <= end)
        except:
            pass

    # --------------------------------------------------
    # 📊 DEFAULT SORT (LATEST FIRST)
    # --------------------------------------------------
    query = query.order_by(Order.created_at.desc())

    orders = query.paginate(page=page, per_page=20)

    return render_template(
        "admin/orders/order_list.html",
        orders=orders,
        search=search,
        status=status,
        payment_status=payment_status,
        start_date=start_date,
        end_date=end_date
    )


# -------------------------------------------------------
# 🔥 ADMIN ORDER DETAIL (DEEP VIEW)
# -------------------------------------------------------

@admin_bp.route("/orders/<int:order_id>")
@login_required
@admin_required
def order_detail(order_id):

    order = Order.query.get_or_404(order_id)

    # Load related data
    items = OrderItem.query.filter_by(order_id=order.id).all()
    timeline = OrderTimeline.query.filter_by(order_id=order.id)\
        .order_by(OrderTimeline.created_at.asc()).all()

    user = User.query.get(order.user_id)

    return render_template(
        "admin/orders/order_detail.html",
        order=order,
        items=items,
        timeline=timeline,
        user=user
    )



# -------------------------------------------------------
# 🔥 ADMIN UPDATE ORDER STATUS
# -------------------------------------------------------
@admin_bp.route("/orders/<int:order_id>/update-status", methods=["POST"])
@login_required
@admin_required
def update_order_status_admin(order_id):

    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("new_status")

    if not new_status:
        flash("Please select a valid status", "danger")
        return redirect(url_for("admin.order_detail", order_id=order.id))

    try:
        update_order_status(
            order,
            new_status,
            note=f"Updated by Admin ID {current_user.id}",
            commit=True
        )

        flash("Order status updated successfully ✅", "success")

    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("admin.order_detail", order_id=order.id))