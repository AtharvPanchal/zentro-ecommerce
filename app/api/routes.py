from flask import request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Product, DeliveryPincode, SavedForLater
from . import api_bp
from flask import url_for
from app.models import CartItem
from flask import session
from app.services.price_service import PriceService
from app.services.cart_service import CartService

# =====================================================
# PRODUCTS LIST
# =====================================================
@api_bp.route("/products", methods=["GET"])
def get_products():
    page = request.args.get("page", 1, type=int)
    limit = min(request.args.get("limit", 8, type=int), 50)
    category = request.args.get("category")
    search = request.args.get("search")
    sort = request.args.get("sort")



    query = Product.query.filter(Product.status == "ACTIVE")

    if category and category.isdigit():
        query = query.filter(Product.category_id == int(category))

    if search and isinstance(search, str):
        query = query.filter(Product.name.ilike(f"%{search}%"))

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    products = []
    for p in pagination.items:
        products.append({
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "price": float(p.price),

            # ✅ SAFE IMAGE URL FOR FRONTEND
            "images": [
                url_for("static", filename=img)
                for img in (p.images or [])
                if img
            ],

            "status": p.status
        })

    return jsonify({
        "success": True,
        "products": products,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_items": pagination.total,
            "total_pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    })


# =====================================================
# ADD TO CART
# =====================================================
@api_bp.route("/cart/add", methods=["POST"])
def add_to_cart():

    product_id = (
            request.form.get("product_id", type=int)
            or request.args.get("product_id", type=int)
    )

    qty = int(request.form.get("quantity", 1))

    if not product_id:
        return jsonify(success=False, message="Product ID missing"), 400

    product = Product.query.get_or_404(product_id)

    if product.status != "ACTIVE":
        return jsonify(success=False, message="Product unavailable"), 400

    # ❗ VALIDATIONS
    if qty < 1:
        return jsonify(success=False, message="Invalid quantity"), 400

    if qty > product.stock:
        return jsonify(success=False, message="Quantity exceeds stock"), 400

    # =====================================================
    # GUEST CART (SESSION-BASED)
    # =====================================================
    if not current_user.is_authenticated:
        cart = session.get("cart", {})

        existing_qty = int(cart.get(str(product_id), 0))
        new_qty = min(existing_qty + qty, product.stock)

        cart[str(product_id)] = new_qty
        session["cart"] = cart

        return jsonify(
            success=True,
            message="Product added to cart",
            cart_count=sum(cart.values()),
            guest=True
        )

    # =====================================================
    # LOGGED-IN USER CART (DB)
    # =====================================================
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product.id
    ).first()

    if cart_item:
        # PDP behaviour: overwrite quantity
        if qty > product.stock:
            return jsonify(success=False, message="Stock limit exceeded"), 400
        cart_item.quantity = qty

    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product.id,
            quantity=qty
        )
        db.session.add(cart_item)

    db.session.commit()

    cart_count = CartItem.query.filter_by(
        user_id=current_user.id
    ).count()

    return jsonify(
        success=True,
        message="Product added to cart successfully",
        cart_count=cart_count,
        product_id=product.id
    )

# ================================================
# GET CART 
# ================================================
@api_bp.route("/cart", methods=["GET"])
@login_required
def get_cart():

    items = CartItem.query.filter_by(user_id=current_user.id).all()

    cart_items = []
    total = 0
    changes_made = False  # 🔥 Track any auto adjustments

    for item in items:

        product = item.product

        # 🚫 Remove inactive products
        if product.status != "ACTIVE":
            db.session.delete(item)
            changes_made = True
            continue

        # 🔴 Remove if stock is zero
        if product.stock <= 0:
            db.session.delete(item)
            changes_made = True
            continue

        # 🟠 Auto-adjust quantity if stock reduced
        if item.quantity > product.stock:
            item.quantity = product.stock
            changes_made = True

        # ✅ Safe subtotal calculation AFTER adjustments
        subtotal = item.item_total
        total += subtotal

        cart_items.append({
            "id": item.id,
            "product_id": product.id,
            "name": product.name,
            "price": float(item.price_at_add),
            "quantity": item.quantity,
            "image": (
                url_for("static", filename=product.images[0])
                if product.images else
                url_for("static", filename="img/placeholders/product.png")
            ),
            "subtotal": float(subtotal)
        })

    # ✅ Commit only if adjustments happened
    if changes_made:
        db.session.commit()

    pricing = PriceService.calculate_total(items)

    return jsonify(
        success=True,
        cart=cart_items,
        pricing=pricing
    )


# =====================================================
# REMOVE FROM CART
# =====================================================
@api_bp.route("/cart/remove", methods=["POST"])
@login_required
def remove_from_cart():
    from app.models import CartItem

    cart_id = (
        request.json.get("cart_id") if request.is_json
        else request.form.get("cart_id")
    )

    item = CartItem.query.filter_by(
        id=cart_id,
        user_id=current_user.id
    ).first()

    if not item:
        return jsonify(success=False, message="Item not found"), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify(success=True)





# =====================================================
# SAVE FOR LATER (PHASE-9)
# =====================================================
@api_bp.route("/cart/save-for-later", methods=["POST"])
@login_required
def save_for_later():

    cart_id = request.json.get("cart_id")

    item = CartItem.query.filter_by(
        id=cart_id,
        user_id=current_user.id
    ).first()

    if not item:
        return jsonify(success=False, message="Item not found"), 404

    saved = SavedForLater(
        user_id=current_user.id,
        product_id=item.product_id
    )

    db.session.add(saved)
    db.session.delete(item)

    db.session.commit()

    return jsonify(success=True)



# =====================================================
# MOVE SAVED ITEM BACK TO CART (PHASE-9)
# =====================================================
@api_bp.route("/cart/move-to-cart", methods=["POST"])
@login_required
def move_saved_to_cart():

    saved_id = request.json.get("saved_id")

    item = SavedForLater.query.filter_by(
        id=saved_id,
        user_id=current_user.id
    ).first()

    if not item:
        return jsonify(success=False, message="Saved item not found"), 404

    product = item.product

    if product.status != "ACTIVE":
        return jsonify(success=False, message="Product unavailable"), 400

    existing = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product.id
    ).first()

    if existing:
        existing.quantity += 1
    else:
        existing = CartItem(
            user_id=current_user.id,
            product_id=product.id,
            quantity=1,
            price_at_add=product.price
        )
        db.session.add(existing)

    db.session.add(existing)
    db.session.delete(item)

    db.session.commit()

    return jsonify(success=True)




# =====================================================
# WISHLIST COUNT (HEADER BADGE)
# =====================================================
@api_bp.route("/wishlist/count", methods=["GET"])
@login_required
def wishlist_count():
    from app.models import Wishlist

    count = Wishlist.query.filter_by(
        user_id=current_user.id
    ).count()

    return jsonify(
        success=True,
        count=count
    )


# =====================================================
# UPDATE CART QUANTITY
# =====================================================
@api_bp.route("/cart/update", methods=["POST"])
@login_required
def update_cart_qty():
    from app.models import CartItem

    if request.is_json:
        data = request.get_json() or {}
        cart_id = data.get("cart_id")
        qty = data.get("qty")
    else:
        cart_id = request.form.get("cart_id", type=int)
        qty = request.form.get("qty", type=int)

    if not cart_id or not isinstance(qty, int) or qty < 1:
        return jsonify(success=False, message="Invalid quantity"), 400

    item = CartItem.query.filter_by(
        id=cart_id,
        user_id=current_user.id
    ).first()

    if not item:
        return jsonify(success=False, message="Cart item not found"), 404

    if item.product.status != "ACTIVE":
        return jsonify(success=False, message="Product unavailable"), 400

    if qty > item.product.stock:
        return jsonify(success=False, message="Stock limit exceeded"), 400

    item.quantity = qty
    db.session.commit()

    return jsonify(success=True)




# =====================================================
# CREATE ORDER (COD)
# =====================================================
@api_bp.route("/order/create", methods=["POST"])
@login_required
def create_order():
    return jsonify({
        "success": False,
        "message": "Order service is under development"
    }), 503




# =====================================================
# GET SAVED ITEMS
# =====================================================
@api_bp.route("/saved-items", methods=["GET"])
@login_required
def get_saved_items():

    items = SavedForLater.query.filter_by(
        user_id=current_user.id
    ).all()

    result = []

    for item in items:

        product = item.product

        result.append({
            "id": item.id,
            "name": product.name,
            "price": float(product.price)
        })

    return jsonify(
        success=True,
        items=result
    )



# =====================================================
# CHECK DELIVERY BY PINCODE (PHASE-6 DB ENABLED)
# =====================================================
@api_bp.route("/delivery/check", methods=["GET"])
def check_delivery():
    pincode = request.args.get("pincode", "").strip()
    product_id = request.args.get("product_id", type=int)

    # 1️⃣ BASIC VALIDATION
    if not pincode.isdigit() or len(pincode) != 6:
        return jsonify(
            success=False,
            message="Please enter a valid 6-digit pincode"
        ), 400

    # 2️⃣ OPTIONAL PRODUCT CHECK
    if product_id:
        product = Product.query.get(product_id)
        if not product:
            return jsonify(
                success=False,
                message="Invalid product"
            ), 404

    # 3️⃣ CHECK PINCODE IN DB
    record = DeliveryPincode.query.filter_by(pincode=pincode).first()

    # 4️⃣ IF NOT FOUND → AUTO INSERT
    if not record:
        record = DeliveryPincode(
            pincode=pincode,
            is_serviceable=True,
            delivery_days="3-5"
        )
        db.session.add(record)
        db.session.commit()

    # 5️⃣ RESPONSE
    if not record.is_serviceable:
        return jsonify(
            success=True,
            deliverable=False,
            message="Delivery not available for this pincode"
        )

    return jsonify(
        success=True,
        deliverable=True,
        estimated_days=record.delivery_days,
        return_policy="7 Days Replacement",
        seller="Zentro Retail"
    )



# =====================================================
# LIVE SEARCH SUGGESTIONS (FLIPKART STYLE)
# =====================================================
@api_bp.route("/search", methods=["GET"])
def live_search():

    q = request.args.get("q", "").strip()

    if not q or len(q) < 2:
        return jsonify(success=True, results=[])

    products = (
        Product.query
        .filter(
            Product.status == "ACTIVE",
            Product.name.ilike(f"%{q}%")
        )
        .order_by(Product.created_at.desc())
        .limit(6)
        .all()
    )

    results = []

    for p in products:

        image = None
        if p.image_list:
            image = url_for("static", filename=p.image_list[0])

        results.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "image": image
        })

    return jsonify(
        success=True,
        results=results
    )