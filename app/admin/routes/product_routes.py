"""
Admin Product Routes
====================
Priority-1 : Core Product Catalogue

This file handles:
- Create product (admin only)
- Update product (admin only, SKU immutable)
- List products (internal admin table view)

NOT included here:
- Inventory / stock
- Visibility lifecycle
- Analytics
- Delete operations
"""

from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Product
from app.admin.decorators import admin_required
from app.admin.validators.product_validators import (
    validate_product_create,
    validate_product_update
)

from flask import render_template, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
from flask import current_app
from app.extensions import csrf
from app.models import Category



# --------------------------------------------------
# Blueprint registration
# --------------------------------------------------
product_bp = Blueprint(
    "admin_products",
    __name__
)


# --------------------------------------------------
# CREATE PRODUCT (ADMIN ONLY)
# --------------------------------------------------
@product_bp.route("/products", methods=["POST"])
@admin_required
def create_product():
    """
    ADMIN: Create a new product
    --------------------------
    Required fields:
    - name
    - sku (immutable)
    - category_id
    - price

    Optional:
    - description
    - images (list)
    """

    data = request.get_json()

    # STEP-3 : REQUEST VALIDATION
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
            images=data.get("images", [])
        )

        db.session.add(product)
        db.session.commit()

        return jsonify({
            "message": "Product created successfully",
            "product_id": product.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": str(e)
        }), 400


# --------------------------------------------------
# UPDATE PRODUCT (ADMIN ONLY)
# --------------------------------------------------
@product_bp.route("/products/<int:product_id>", methods=["PUT"])
@admin_required
def update_product(product_id):
    """
    ADMIN: Update product metadata
    ------------------------------
    - SKU update NOT allowed
    - Safe fields only
    """

    product = Product.query.get_or_404(product_id)
    data = request.get_json()

    # STEP-3 : REQUEST VALIDATION
    is_valid, error = validate_product_update(data)
    if not is_valid:
        return jsonify({"error": error}), 400

    try:
        product.update(
            name=data.get("name", product.name),
            price=data.get("price", product.price),
            description=data.get("description", product.description),
            images=data.get("images", product.images),
            category_id=data.get("category_id", product.category_id)
        )

        db.session.commit()

        return jsonify({
            "message": "Product updated successfully"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": str(e)
        }), 400


# --------------------------------------------------
# LIST PRODUCTS (ADMIN TABLE VIEW)
# --------------------------------------------------
@product_bp.route("/products", methods=["GET"])
@admin_required
def list_products():
    """
    ADMIN: List all products
    -----------------------
    - Shows ACTIVE & INACTIVE
    - Internal admin usage only
    """

    products = Product.query.order_by(
        Product.created_at.desc()
    ).all()

    result = []

    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "price": float(p.price),
            "status": p.status,
            "created_at": p.created_at.isoformat()
        })

    return jsonify(result), 200





# --------------------------------------------------
# PRODUCT LISTING UI (ADMIN TABLE VIEW)
# --------------------------------------------------
@product_bp.route("/products/list", methods=["GET"])
@admin_required
def product_list_ui():
    """
    ADMIN UI: Product Listing Table
    -------------------------------
    - HTML table view
    - Internal admin usage
    - Read-only (no actions here)
    """

    products = Product.query.order_by(
        Product.created_at.desc()
    ).all()

    return render_template(
        "admin/products/list.html",
        products=products
    )

# --------------------------------------------------
# ADD PRODUCT (ADMIN UI)
# --------------------------------------------------
@product_bp.route("/products/add", methods=["GET", "POST"])
@admin_required
@csrf.exempt
def add_product_ui():
    """
    ADMIN UI: Add Product Form
    --------------------------
    - Renders add_edit.html
    - Handles form submit
    """

    if request.method == "POST":
        name = request.form.get("name")
        sku = request.form.get("sku")
        category_id_raw = request.form.get("category_id")
        price_raw = request.form.get("price")

        if not category_id_raw or not price_raw:
            flash("Please fill all required fields", "danger")
            return redirect(request.url)

        category_id = int(category_id_raw)
        price = float(price_raw)

        # CATEGORY VALIDATION
        category = Category.query.filter_by(id=category_id, status="ACTIVE").first()
        if not category:
            flash("Invalid category selected", "danger")
            return redirect(request.url)

        description = request.form.get("description")
        status = request.form.get("status", "ACTIVE")

        image_file = request.files.get("image")
        image_path = None

        # BASIC VALIDATION
        if not name or not sku or not category_id or not price:
            flash("Please fill all required fields", "danger")
            return redirect(request.url)

        # SKU UNIQUE CHECK
        if Product.query.filter_by(sku=sku).first():
            flash("SKU already exists", "danger")
            return redirect(request.url)

        # IMAGE UPLOAD (LOCAL)
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            upload_dir = os.path.join(
                current_app.root_path, "..", "static", "uploads", "products"
            )

            os.makedirs(upload_dir, exist_ok=True)
            image_file.save(os.path.join(upload_dir, filename))
            image_path = f"/static/uploads/products/{filename}"

        product = Product(
            name=name,
            sku=sku,
            category_id=category_id,
            price=price,
            description=description,
            status=status,
            images=[image_path] if image_path else []
        )

        db.session.add(product)
        db.session.commit()

        flash("New product added successfully", "success")
        return redirect(url_for("admin.admin_products.product_list_ui"))

    categories = Category.query.filter_by(status="ACTIVE").all()

    return render_template(
        "admin/products/add_edit.html",
        product=None,
        categories=categories,
        mode="add"
    )



# --------------------------------------------------
# EDIT PRODUCT (ADMIN UI)
# --------------------------------------------------
@product_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
@csrf.exempt
def edit_product_ui(product_id):
    """
    ADMIN UI: Edit Product Form
    ---------------------------
    - Pre-filled form
    - SKU immutable
    """

    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.name = request.form.get("name")

        # PRICE VALIDATION
        price_raw = request.form.get("price")
        if not price_raw:
            flash("Price is required", "danger")
            return redirect(request.url)

        product.price = float(price_raw)

        category_id = int(request.form.get("category_id"))

        # CATEGORY VALIDATION
        category = Category.query.filter_by(id=category_id, status="ACTIVE").first()
        if not category:
            flash("Invalid category selected", "danger")
            return redirect(request.url)

        product.category_id = category_id

        product.description = request.form.get("description")
        product.status = request.form.get("status")

        image_file = request.files.get("image")
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            upload_dir = os.path.join(
                current_app.root_path, "..", "static", "uploads", "products"
            )

            os.makedirs(upload_dir, exist_ok=True)
            image_file.save(os.path.join(upload_dir, filename))
            product.images = [f"/static/uploads/products/{filename}"]

        db.session.commit()

        flash("Product updated successfully", "success")
        return redirect(url_for("admin.admin_products.product_list_ui"))


    categories = Category.query.filter_by(status="ACTIVE").all()

    return render_template(
        "admin/products/add_edit.html",
        product=product,
        categories=categories,
        mode="edit"
    )





