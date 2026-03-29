from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from app.extensions import db
from app.admin.decorators import admin_required

from app.models import AttributeType, Category
from app.admin import admin_bp


# -----------------------------------------------------
# ATTRIBUTE LIST PAGE
# -----------------------------------------------------
@admin_bp.route("/attributes")
@admin_required
def attributes_list():

    attributes = (
        AttributeType.query
        .join(Category, AttributeType.category_id == Category.id)
        .add_columns(
            AttributeType.id,
            AttributeType.name,
            AttributeType.slug,
            Category.name.label("category_name")
        )
        .order_by(AttributeType.name.asc())
        .all()
    )

    categories = Category.query.filter(
        Category.status == "ACTIVE"
    ).order_by(Category.name.asc()).all()

    return render_template(
        "admin/attributes.html",
        attributes=attributes,
        categories=categories
    )


# -----------------------------------------------------
# CREATE ATTRIBUTE
# -----------------------------------------------------
@admin_bp.route("/attributes/create", methods=["POST"])
@admin_required
def create_attribute():

    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip()
    category_id = request.form.get("category_id")

    # ---------------------------
    # VALIDATION
    # ---------------------------
    if not name or not slug or not category_id:
        flash("All fields are required", "danger")
        return redirect(url_for("admin.attributes_list"))

    # ensure category exists
    category = Category.query.get(category_id)

    if not category:
        flash("Invalid category", "danger")
        return redirect(url_for("admin.attributes_list"))

    # check duplicate slug
    existing = AttributeType.query.filter_by(slug=slug).first()

    if existing:
        flash("Attribute slug already exists", "warning")
        return redirect(url_for("admin.attributes_list"))

    # ---------------------------
    # CREATE ATTRIBUTE
    # ---------------------------
    attribute = AttributeType(
        name=name,
        slug=slug,
        category_id=category_id
    )

    db.session.add(attribute)
    db.session.commit()

    flash("Attribute created successfully", "success")

    return redirect(url_for("admin.attributes_list"))


# -----------------------------------------------------
# DELETE ATTRIBUTE
# -----------------------------------------------------
@admin_bp.route("/attributes/delete/<int:attribute_id>", methods=["POST"])
@admin_required
def delete_attribute(attribute_id):

    attribute = AttributeType.query.get_or_404(attribute_id)

    db.session.delete(attribute)
    db.session.commit()

    flash("Attribute deleted successfully", "success")

    return redirect(url_for("admin.attributes_list"))