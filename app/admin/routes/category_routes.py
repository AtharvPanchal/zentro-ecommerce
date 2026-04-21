from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.category_service import build_category_tree, flatten_tree
from app.extensions import db, csrf
from app.models import Category, Product
from app.admin.decorators import admin_required
from slugify import slugify
import os
import uuid
from werkzeug.utils import secure_filename
from sqlalchemy import func, case
from app.services.category_service import (
    is_circular,
    get_depth,
    get_all_subcategories
)



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

    categories = pagination.items



    # --------------------------------------------------
    # 📊 CATEGORY STATS (OPTIMIZED)
    # --------------------------------------------------
    stats_query = db.session.query(
        Product.category_id,
        func.count(Product.id).label("total_products"),
        func.sum(Product.stock).label("total_stock"),
        func.avg(Product.price).label("avg_price"),
        func.sum(
            case((Product.status == "ACTIVE", 1), else_=0)
        ).label("active_products"),
        func.sum(
            case((Product.stock == 0, 1), else_=0)
        ).label("out_of_stock")
    ).group_by(Product.category_id).all()

    stats_dict = {
        stat.category_id: stat for stat in stats_query
    }

    for category in categories:
        stat = stats_dict.get(category.id)

        category.total_products = stat.total_products if stat else 0
        category.total_stock = stat.total_stock if stat and stat.total_stock else 0
        category.avg_price = round(stat.avg_price, 2) if stat and stat.avg_price else 0
        category.active_products = stat.active_products if stat else 0
        category.out_of_stock = stat.out_of_stock if stat else 0

    return render_template(
        "admin/categories/list.html",
        categories=categories,
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

        parent_id = request.form.get("parent_id")
        parent_id = int(parent_id) if parent_id else None

        image_file = request.files.get("image")

        if status not in ["ACTIVE", "INACTIVE"]:
            status = "ACTIVE"

        if not name:
            flash("Category name is required", "danger")
            return redirect(request.url)

        slug = slugify(name)

        # ❗ DEPTH LIMIT (MAX 3)
        if parent_id:
            parent = Category.query.get(parent_id)

            if not parent:
                flash("Invalid parent category", "danger")
                return redirect(request.url)

            depth = get_depth(parent_id)
            if depth >= 3:
                flash("Maximum category depth reached (3 levels only)", "danger")
                return redirect(request.url)

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
            image=image_path,
            parent_id=parent_id
        )

        db.session.add(category)
        db.session.commit()

        flash("Category added successfully", "success")
        return redirect(url_for("admin.category.list_categories"))

    categories = Category.query.all()
    tree = build_category_tree(categories)
    flat_categories = flatten_tree(tree)
    blocked_ids = []

    return render_template(
        "admin/categories/add_edit.html",
        mode="add",
        category=None,
        categories=flat_categories,
        blocked_ids=blocked_ids  # PARENT_CATEGORY_IDS
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
        parent_id = request.form.get("parent_id")
        parent_id = int(parent_id) if parent_id else None
        image_file = request.files.get("image")

        if not name:
            flash("Category name is required", "danger")
            return redirect(request.url)

        new_slug = slugify(name)

        # ❗ SELF PARENT CHECK
        if parent_id == category.id:
            flash("Category cannot be its own parent", "danger")
            return redirect(request.url)

        # ❗ CIRCULAR CHECK
        # ❗ PARENT VALIDATION + CIRCULAR + DEPTH (OPTIMIZED FLOW)
        if parent_id:
            parent = Category.query.get(parent_id)

            if not parent:
                flash("Invalid parent category", "danger")
                return redirect(request.url)

            # ❗ CIRCULAR CHECK
            if is_circular(parent_id, category.id):
                flash("Invalid parent (circular hierarchy detected)", "danger")
                return redirect(request.url)

            # ❗ DEPTH LIMIT
            depth = get_depth(parent_id)
            if depth >= 3:
                flash("Maximum category depth reached (3 levels only)", "danger")
                return redirect(request.url)



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
        category.parent_id = parent_id

        db.session.commit()

        flash("Category updated successfully", "success")
        return redirect(url_for("admin.category.list_categories"))

    categories = Category.query.all()
    tree = build_category_tree(categories)
    flat_categories = flatten_tree(tree)
    blocked_ids = get_all_subcategories(category.id)

    return render_template(
        "admin/categories/add_edit.html",
        mode="edit",
        category=category,
        categories=flat_categories,
        blocked_ids=blocked_ids  #  MUST
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