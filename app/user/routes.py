from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, logout_user
from app.extensions import db
from . import user_bp
from app.models import Order
from app.models import UserAddress
from app.models import Wishlist, Product




# ============================
# 👤 MY PROFILE
# ============================
@user_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        phone = request.form.get("phone", "").strip()
        gender = request.form.get("gender", "").strip()

        if not username:
            flash("❌ Name cannot be empty", "danger")
            return redirect(url_for("user.account"))

        if phone and not phone.isdigit():
            flash("❌ Phone must be numeric", "danger")
            return redirect(url_for("user.account"))

        current_user.username = username
        current_user.phone = phone or None
        current_user.gender = gender or None

        db.session.commit()
        flash("✅ Profile updated successfully", "success")

        return redirect(url_for("user.account"))

    return render_template("user/account.html")


# ============================
# 📦 MY ORDERS
# ============================
@user_bp.route("/orders")
@login_required
def orders():
    from app.models import Order

    orders = (
        Order.query
        .filter_by(customer_name=current_user.username)
        .order_by(Order.created_at.desc())
        .all()
    )

    return render_template(
        "user/order_history.html",
        orders=orders
    )


# ============================
# 📄 ORDER DETAIL
# ============================
@user_bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)

    # 🔐 Security: order belongs to current user
    if order.customer_name != current_user.username:
        flash("❌ Unauthorized access", "danger")
        return redirect(url_for("user.orders"))

    return render_template(
        "user/order_detail.html",
        order=order
    )



# ============================
# ❤️ WISHLIST PAGE
# ============================
@user_bp.route("/wishlist")
@login_required
def wishlist():

    search = request.args.get("search", "").strip()
    sort = request.args.get("sort", "")
    status = request.args.get("status", "all")

    query = (
        db.session.query(Wishlist, Product)
        .join(Product, Wishlist.product_id == Product.id)
        .filter(Wishlist.user_id == current_user.id)
    )

    # 🔍 Search
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    # 👁 Status filter
    if status == "purchased":
        query = query.filter(Wishlist.is_purchased.is_(True))
    elif status == "unpurchased":
        query = query.filter(Wishlist.is_purchased.is_(False))

    # ↕ Sorting
    if sort == "low":
        query = query.order_by(Product.price.asc())
    elif sort == "high":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Wishlist.created_at.desc())

    items = query.all()

    return render_template(
        "user/wishlist.html",
        items=items,
        search=search,
        sort=sort,
        status=status
    )


# ============================
# ❤️ ADD / REMOVE WISHLIST
# ============================
@user_bp.route("/wishlist/toggle/<int:product_id>", methods=["POST"])
@login_required
def toggle_wishlist(product_id):

    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    if existing:
        db.session.delete(existing)
        flash("❌ Removed from wishlist", "info")
    else:
        db.session.add(
            Wishlist(
                user_id=current_user.id,
                product_id=product_id
            )
        )
        flash("❤️ Added to wishlist", "success")

    db.session.commit()
    return redirect(request.referrer or url_for("user.wishlist"))


# ============================
# USER ADDRESSES
# ============================
@user_bp.route("/addresses", methods=["GET", "POST"])
@login_required
def addresses():

    if request.method == "POST":
        full_name = request.form.get("full_name")
        phone = request.form.get("phone")
        house_no = request.form.get("house_no")
        area = request.form.get("area")
        landmark = request.form.get("landmark")
        city = request.form.get("city")
        state = request.form.get("state")
        pincode = request.form.get("pincode")
        address_type = request.form.get("address_type")
        is_default = bool(request.form.get("is_default"))

        if not all([full_name, phone, house_no, area, city, state, pincode]):
            flash("❌ Please fill all required fields", "danger")
            return redirect(url_for("user.addresses"))

        if is_default:
            UserAddress.query.filter_by(
                user_id=current_user.id,
                is_default=True
            ).update({"is_default": False})

        address = UserAddress(
            user_id=current_user.id,
            full_name=full_name,
            phone=phone,
            house_no=house_no,
            area=area,
            landmark=landmark,
            city=city,
            state=state,
            pincode=pincode,
            address_type=address_type,
            is_default=is_default
        )

        db.session.add(address)
        db.session.commit()

        flash("✅ Address Saved successfully", "success")
        return redirect(url_for("user.addresses"))

    addresses = UserAddress.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template("user/addresses.html", addresses=addresses)



# ============================
# USER ADDRESSES EDIT
# ============================
@user_bp.route("/addresses/edit/<int:address_id>", methods=["GET", "POST"])
@login_required
def edit_address(address_id):
    address = UserAddress.query.filter_by(
        id=address_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        house_no = request.form.get("house_no", "").strip()
        area = request.form.get("area", "").strip()
        landmark = request.form.get("landmark", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        pincode = request.form.get("pincode", "").strip()
        address_type = request.form.get("address_type", "").strip()

        # 🔐 REQUIRED VALIDATION
        if not all([full_name, phone, house_no, area, city, state, pincode]):
            flash("❌ Please fill all required fields", "danger")
            return redirect(url_for("user.edit_address", address_id=address_id))

        address.full_name = full_name
        address.phone = phone
        address.house_no = house_no
        address.area = area
        address.landmark = landmark
        address.city = city
        address.state = state
        address.pincode = pincode
        address.address_type = address_type

        db.session.commit()
        flash("✅ Address Updated Successfully", "success")
        return redirect(url_for("user.addresses"))

    return render_template("user/edit_address.html", address=address)


# ============================
# ❌ DELETE ADDRESS
# ============================
@user_bp.route("/addresses/delete/<int:address_id>")
@login_required
def delete_address(address_id):

    address = UserAddress.query.filter_by(
        id=address_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(address)
    db.session.commit()

    flash("🗑 Address deleted", "info")
    return redirect(url_for("user.addresses"))



# ============================
# 🔐 CHANGE PASSWORD
# ============================
@user_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        # 🔐 VALIDATIONS
        if not old_password or not new_password or not confirm_password:
            flash("❌ All fields are required", "danger")
            return redirect(url_for("user.change_password"))

        from app.utils.utils import verify_password, hash_password

        if not verify_password(old_password, current_user.password_hash):
            flash("❌ Old password is incorrect", "danger")
            return redirect(url_for("user.change_password"))

        if new_password != confirm_password:
            flash("❌ New passwords do not match", "danger")
            return redirect(url_for("user.change_password"))

        if len(new_password) < 8:
            flash("❌ Password must be at least 8 characters", "danger")
            return redirect(url_for("user.change_password"))

        # ✅ UPDATE PASSWORD
        current_user.password_hash = hash_password(new_password)

        # 🔐 INVALIDATE ALL SESSIONS
        current_user.session_version += 1
        db.session.commit()

        flash("✅ Password changed successfully. Please login again.", "success")
        return redirect(url_for("auth.logout"))

    return render_template("user/change_password.html")
