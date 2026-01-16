from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db, csrf
from app.models import Category
from app.admin.decorators import admin_required
from slugify import slugify


category_bp = Blueprint(
    "category",
    __name__,
    url_prefix="/categories"
)




# --------------------------------------------------
# LIST CATEGORIES
# --------------------------------------------------
@category_bp.route("/", methods=["GET"])
@admin_required
def list_categories():
    categories = Category.query.order_by(Category.created_at.desc()).all()
    return render_template(
        "admin/categories/list.html",
        categories=categories
    )

# --------------------------------------------------
# ADD CATEGORY
# --------------------------------------------------
@category_bp.route("/add", methods=["GET", "POST"])
@admin_required
@csrf.exempt
def add_category():
    if request.method == "POST":
        name = request.form.get("name")
        status = request.form.get("status", "ACTIVE")

        if not name:
            flash("Category name is required", "danger")
            return redirect(request.url)

        slug = slugify(name)

        if Category.query.filter_by(slug=slug).first():
            flash("Category already exists", "danger")
            return redirect(request.url)

        category = Category(
            name=name,
            slug=slug,
            status=status
        )

        db.session.add(category)
        db.session.commit()

        flash("Category added successfully", "success")
        return redirect(url_for("admin.category.list_categories"))

    return render_template(
        "admin/categories/add_edit.html",
        mode="add",
        category=None
    )

# --------------------------------------------------
# EDIT CATEGORY
# --------------------------------------------------
@category_bp.route("/<int:category_id>/edit", methods=["GET", "POST"])
@admin_required
@csrf.exempt
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)

    if request.method == "POST":
        name = request.form.get("name")
        status = request.form.get("status")

        if not name:
            flash("Category name is required", "danger")
            return redirect(request.url)

        category.name = name
        category.slug = slugify(name)
        category.status = status

        db.session.commit()

        flash("Category updated successfully", "success")
        return redirect(url_for("admin.category.list_categories"))

    return render_template(
        "admin/categories/add_edit.html",
        mode="edit",
        category=category
    )
