from flask import request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Product
from . import api_bp


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
            "images": p.images or [],
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
@login_required
def add_to_cart():
    return jsonify({
        "success": False,
        "message": "Cart service is under development"
    }), 503


# =====================================================
# GET CART
# =====================================================
@api_bp.route("/cart", methods=["GET"])
@login_required
def get_cart():
    return jsonify({
        "success": False,
        "message": "Cart service is under development"
    }), 503



# =====================================================
# REMOVE FROM CART
# =====================================================
@api_bp.route("/cart/remove", methods=["POST"])
@login_required
def remove_from_cart():
    return jsonify({
        "success": False,
        "message": "Cart service is under development"
    }), 503




# =====================================================
# UPDATE CART QUANTITY
# =====================================================
@api_bp.route("/cart/update", methods=["POST"])
@login_required
def update_cart_qty():
    return jsonify({
        "success": False,
        "message": "Cart service is under development"
    }), 503



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
