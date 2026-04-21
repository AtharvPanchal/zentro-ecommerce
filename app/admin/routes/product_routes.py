"""
Admin Product Routes
====================
Priority-1 : Core Product Catalogue
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from app.extensions import db, csrf
from app.models import Product, Category
from app.admin.decorators import admin_required
from app.admin.validators.product_validators import (
    validate_product_create,
    validate_product_update
)

from app.services.category_service import build_category_tree
from app.services.category_service import get_all_subcategories
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime
import os
import uuid




# --------------------------------------------------
# Blueprint
# --------------------------------------------------
product_bp = Blueprint("admin_products", __name__)


# --------------------------------------------------
# CREATE PRODUCT (API)
# --------------------------------------------------
@product_bp.route("/products", methods=["POST"])
@admin_required
def create_product():

    data = request.get_json()

    is_valid, error = validate_product_create(data)
    if not is_valid:
        return jsonify({"error": error}), 400

    try:
        product = Product(
            name=data["name"],
            sku=data["sku"],
            category_id=data["category_id"],
            price=data["price"],
            description=data.get("description"),
            images=data.get("images", []),
            stock=data.get("stock", 0)
        )

        db.session.add(product)
        db.session.commit()

        return jsonify({
            "message": "Product created successfully",
            "product_id": product.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# --------------------------------------------------
# UPDATE PRODUCT (API)
# --------------------------------------------------
@product_bp.route("/products/<int:product_id>", methods=["PUT"])
@admin_required
def update_product(product_id):

    product = Product.query.get_or_404(product_id)
    data = request.get_json()

    is_valid, error = validate_product_update(data)
    if not is_valid:
        return jsonify({"error": error}), 400

    try:
        product.name = data.get("name", product.name)
        product.price = data.get("price", product.price)
        product.description = data.get("description", product.description)
        product.images = data.get("images", product.images)
        product.stock = data.get("stock", product.stock)

        if "category_id" in data:
            category = Category.query.get(data["category_id"])
            if not category:
                return jsonify({"error": "Invalid category"}), 400
            product.category_id = data["category_id"]

        db.session.commit()

        return jsonify({"message": "Product updated successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# --------------------------------------------------
# LIST PRODUCTS (API)
# --------------------------------------------------
@product_bp.route("/products", methods=["GET"])
@admin_required
def list_products():

    products = (
        Product.query
        .outerjoin(Category)  # FIXED
        .order_by(Product.created_at.desc())
        .all()
    )

    result = []

    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "price": float(p.price),
            "status": p.status,
            "stock": p.stock,
            "category_id": p.category_id,
            "category_name": p.category.name if p.category else None,
            "created_at": p.created_at.isoformat()
        })

    return jsonify(result), 200


# --------------------------------------------------
# PRODUCT LIST UI
# --------------------------------------------------
@product_bp.route("/products/list", methods=["GET"])
@admin_required
def product_list_ui():

    search = request.args.get("search")
    category_id = request.args.get("category")
    sort = request.args.get("sort")
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status")

    query = Product.query

    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )

    if status:
        query = query.filter(Product.status == status)

    if category_id:
        try:
            category_id = int(category_id)

            #MAIN LOGIC
            all_ids = [category_id] + get_all_subcategories(category_id)

            query = query.filter(Product.category_id.in_(all_ids))

        except ValueError:
            pass

    if sort == "price_low":
        query = query.order_by(Product.price.asc(), Product.id.desc())
    elif sort == "price_high":
        query = query.order_by(Product.price.desc(), Product.id.desc())
    else:
        query = query.order_by(Product.created_at.desc(), Product.id.desc())

    pagination = query.paginate(page=page, per_page=5, error_out=False)

    # BUILD CATEGORY TREE
    all_categories = Category.query.filter_by(status="ACTIVE").all()
    category_tree = build_category_tree(all_categories)

    return render_template(
        "admin/products/list.html",
        products=pagination.items,
        categories=category_tree,  # TREE PASS
        pagination=pagination,
        now=datetime.utcnow()
    )

# --------------------------------------------------
# ADD PRODUCT UI
# --------------------------------------------------
@product_bp.route("/products/add", methods=["GET", "POST"])
@admin_required
@csrf.exempt
def add_product_ui():

    if request.method == "POST":

        name = request.form.get("name")
        sku = request.form.get("sku")
        category_id_raw = request.form.get("category_id")
        price_raw = request.form.get("price")
        stock_raw = request.form.get("stock", 0)

        if not category_id_raw or not price_raw:
            flash("Please fill all required fields", "danger")
            return redirect(request.url)

        category_id = int(category_id_raw)
        price = float(price_raw)
        stock = int(stock_raw)

        if stock < 0:
            flash("Stock cannot be negative", "danger")
            return redirect(request.url)

        # PRICE VALIDATION
        if price <= 0:
            flash("Price must be greater than 0", "danger")
            return redirect(request.url)

        if price > 10000000:
            flash("Max ₹1 Cr allowed", "danger")
            return redirect(request.url)

        # CATEGORY VALIDATION
        category = Category.query.filter_by(id=category_id, status="ACTIVE").first()
        if not category:
            flash("Invalid category selected", "danger")
            return redirect(request.url)

        if Product.query.filter_by(sku=sku).first():
            flash("SKU already exists", "danger")
            return redirect(request.url)

        description = request.form.get("description")
        if stock <= 0:
            status = "INACTIVE"
        else:
            status = request.form.get("status", "ACTIVE")

        image_file = request.files.get("image")
        image_path = None

        if image_file and image_file.filename:
            filename = f"{uuid.uuid4().hex}_{secure_filename(image_file.filename)}"
            upload_dir = os.path.join(current_app.static_folder, "uploads", "products")

            os.makedirs(upload_dir, exist_ok=True)
            image_file.save(os.path.join(upload_dir, filename))
            image_path = f"uploads/products/{filename}"

        product = Product(
            name=name,
            sku=sku,
            category_id=category_id,
            price=price,
            description=description,
            status=status,
            stock=stock,
            images=[image_path] if image_path else []
        )

        db.session.add(product)
        db.session.commit()

        flash("Product added successfully", "success")
        return redirect(url_for("admin.admin_products.product_list_ui"))

    return render_template(
        "admin/products/add_edit.html",
        product=None,
        categories=Category.query.filter_by(status="ACTIVE").all(),
        mode="add"
    )


# --------------------------------------------------
# EDIT PRODUCT UI
# --------------------------------------------------
@product_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
@csrf.exempt
def edit_product_ui(product_id):

    product = Product.query.get_or_404(product_id)

    if request.method == "POST":

        product.name = request.form.get("name")

        price = float(request.form.get("price"))
        stock = int(request.form.get("stock", product.stock))

        if price <= 0:
            flash("Price must be greater than 0", "danger")
            return redirect(request.url)

        if price > 10000000:
            flash("Max ₹1 Cr allowed", "danger")
            return redirect(request.url)

        product.price = price
        product.stock = stock

        category_id = int(request.form.get("category_id"))

        category = Category.query.filter_by(id=category_id, status="ACTIVE").first()
        if not category:
            flash("Invalid category selected", "danger")
            return redirect(request.url)

        product.category_id = category_id
        product.description = request.form.get("description")

        if product.stock <= 0:
            product.status = "INACTIVE"
        else:
            product.status = request.form.get("status")

        image_file = request.files.get("image")

        if image_file and image_file.filename:
            filename = f"{uuid.uuid4().hex}_{secure_filename(image_file.filename)}"
            upload_dir = os.path.join(current_app.static_folder, "uploads", "products")

            os.makedirs(upload_dir, exist_ok=True)
            image_file.save(os.path.join(upload_dir, filename))
            product.images = [f"uploads/products/{filename}"]

        db.session.commit()

        flash("Product updated successfully", "success")
        return redirect(url_for("admin.admin_products.product_list_ui"))

    return render_template(
        "admin/products/add_edit.html",
        product=product,
        categories=Category.query.filter_by(status="ACTIVE").all(),
        mode="edit"
    )




# --------------------------------------------------
# TOGGLE PRODUCT STATUS
# --------------------------------------------------
@product_bp.route("/products/<int:product_id>/toggle", methods=["POST"])
@admin_required
@csrf.exempt
def toggle_product(product_id):

    product = Product.query.get_or_404(product_id)

    if product.status == "ACTIVE":
        product.status = "INACTIVE"
        flash("Product deactivated", "warning")
    else:
        product.status = "ACTIVE"
        flash("Product activated", "success")

    db.session.commit()

    return redirect(url_for("admin.admin_products.product_list_ui"))