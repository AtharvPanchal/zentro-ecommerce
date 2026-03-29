from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db, csrf
from app.models import Category
from app.admin.decorators import admin_required
from slugify import slugify
import os
import uuid
from werkzeug.utils import secure_filename


category_bp = Blueprint(
    "category",
    __name__,
    url_prefix="/categories"
)

# 📂 CONFIG
UPLOAD_FOLDER = "static/uploads/categories"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


# --------------------------------------------------
# 🛡️ HELPER FUNCTIONS
# --------------------------------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file):
    if not file:
        return None

    if not allowed_file(file.filename):
        return "INVALID_TYPE"

    # ✅ ADD THIS
    if not file.mimetype.startswith("image/"):
        return "INVALID_TYPE"

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size > MAX_FILE_SIZE:
        return "FILE_TOO_LARGE"

    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"

    filepath = os.path.join(UPLOAD_FOLDER, filename)

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file.save(filepath)

    return f"uploads/categories/{filename}"


def delete_old_image(image_path):
    if not image_path:
        return

    full_path = os.path.join("app/static", image_path)

    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except Exception:
            pass


# --------------------------------------------------
# LIST CATEGORIES
# --------------------------------------------------
@category_bp.route("/", methods=["GET"])
@admin_required
def list_categories():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "")
    sort = request.args.get("sort", "newest")
    page = request.args.get("page", 1, type=int)

    query = Category.query.order_by(Category.created_at.desc())

    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))

    if status:
        query = query.filter(Category.status == status)

    if sort == "newest":
        query = query.order_by(Category.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Category.created_at.asc())
    elif sort == "name_asc":
        query = query.order_by(Category.name.asc())
    else:
        query = query.order_by(Category.created_at.desc())

    pagination = query.paginate(page=page, per_page=12, error_out=False)

    return render_template(
        "admin/categories/list.html",
        categories=pagination.items,
        pagination=pagination,
        search=search,
        status=status,
        sort=sort
    )


# --------------------------------------------------
# ADD CATEGORY
# --------------------------------------------------
@category_bp.route("/add", methods=["GET", "POST"])
@admin_required
@csrf.exempt
def add_category():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        status = request.form.get("status", "ACTIVE")
        image_file = request.files.get("image")

        if status not in ["ACTIVE", "INACTIVE"]:
            status = "ACTIVE"

        if not name:
            flash("Category name is required", "danger")
            return redirect(request.url)

        slug = slugify(name)

        if Category.query.filter_by(slug=slug).first():
            flash("Category already exists", "danger")
            return redirect(request.url)

        # 🖼 IMAGE HANDLE
        image_path = None
        if image_file and image_file.filename:
            result = save_image(image_file)

            if result == "INVALID_TYPE":
                flash("Only image files allowed (png, jpg, jpeg, webp)", "danger")
                return redirect(request.url)

            if result == "FILE_TOO_LARGE":
                flash("Image must be less than 2MB", "danger")
                return redirect(request.url)

            image_path = result

        category = Category(
            name=name,
            slug=slug,
            status=status,
            image=image_path
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
        name = request.form.get("name", "").strip()
        image_file = request.files.get("image")

        if not name:
            flash("Category name is required", "danger")
            return redirect(request.url)

        new_slug = slugify(name)

        existing = Category.query.filter(
            Category.slug == new_slug,
            Category.id != category.id
        ).first()

        if existing:
            flash("Category with same name already exists", "danger")
            return redirect(request.url)

        status = request.form.get("status")
        if status not in ["ACTIVE", "INACTIVE"]:
            status = "ACTIVE"

        # 🖼 IMAGE REPLACE LOGIC
        if image_file and image_file.filename:
            result = save_image(image_file)

            if result == "INVALID_TYPE":
                flash("Only image files allowed", "danger")
                return redirect(request.url)

            if result == "FILE_TOO_LARGE":
                flash("Image must be less than 2MB", "danger")
                return redirect(request.url)

            # delete old
            delete_old_image(category.image)

            category.image = result

        category.name = name
        category.slug = new_slug
        category.status = status

        db.session.commit()

        flash("Category updated successfully", "success")
        return redirect(url_for("admin.category.list_categories"))

    return render_template(
        "admin/categories/add_edit.html",
        mode="edit",
        category=category
    )


# --------------------------------------------------
# TOGGLE CATEGORY STATUS
# --------------------------------------------------
@category_bp.route("/<int:category_id>/toggle", methods=["POST"])
@admin_required
@csrf.exempt
def toggle_category(category_id):
    category = Category.query.get_or_404(category_id)

    if category.status == "ACTIVE":
        category.status = "INACTIVE"
        flash("Category deactivated", "warning")
    else:
        category.status = "ACTIVE"
        flash("Category activated", "success")

    db.session.commit()

    return redirect(url_for("admin.category.list_categories"))