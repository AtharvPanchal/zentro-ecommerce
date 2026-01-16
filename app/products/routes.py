from flask import render_template, request
from . import products_bp
from app.models import Product, ProductReview


#--------------------------------------------------------
# PRODUCT LISTING
#--------------------------------------------------------
@products_bp.route("/products")
def listing():
    category = request.args.get("category")
    sort = request.args.get("sort")

    query = Product.query

    if category:
        query = query.filter(Product.category_id == int(category))

    if sort == "low":
        query = query.order_by(Product.price.asc())
    elif sort == "high":
        query = query.order_by(Product.price.desc())

    products = query.all()

    for p in products:
        if not p.images:
            p.images = []
        elif isinstance(p.images, str):
            # safety fallback
            p.images = [p.images]

    return render_template("products/listing.html", products=products)


#---------------------------------------------------------
# PRODUCT DETAIL (PUBLIC REVIEWS)
#---------------------------------------------------------
@products_bp.route("/product/<int:product_id>")
def product_detail(product_id):

    product = Product.query.get_or_404(product_id)

    reviews = (
        ProductReview.query
        .filter(
            ProductReview.product_id == product.id,
            ProductReview.is_active == True
        )
        .order_by(ProductReview.created_at.desc())
        .all()
    )

    return render_template(
        "product_detail.html",
        product=product,
        reviews=reviews
    )
