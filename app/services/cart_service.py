from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import CartItem, Product, SavedForLater

class CartValidationError(ValueError):
    """Raised when cart validation fails"""
    pass


class CartService:
    """
    Cart business logic layer
    Used by routes / APIs / checkout
    """

    # --------------------------------------------------
    # PHASE 5 — CART VALIDATION ENGINE
    # --------------------------------------------------
    @staticmethod
    def validate_product(product, quantity, price_snapshot=None):
        """
        Central validation for cart operations
        """

        # PRODUCT ACTIVE CHECK
        if not product or not product.is_active_product:
            raise CartValidationError("Product is not available")

        # MAX QUANTITY RULE
        MAX_QTY = 10
        if quantity > MAX_QTY:
            raise CartValidationError(f"Maximum {MAX_QTY} items allowed")

        # STOCK AVAILABILITY
        if product.stock <= 0:
            raise CartValidationError("Product is out of stock")

        if quantity > product.stock:
            raise CartValidationError("Requested quantity exceeds stock")

        # PRICE MISMATCH CHECK
        if price_snapshot is not None:
            if float(product.price) != float(price_snapshot):
                raise CartValidationError(
                    "Product price changed. Please refresh cart."
                )


    # --------------------------------------------------
    # ADD TO CART
    # --------------------------------------------------
    @staticmethod
    def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
        """
        Adds product to user's cart
        """

        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")

        product = Product.query.get(product_id)

        if not product:
            raise CartValidationError("Product not found")

        CartService.validate_product(product, quantity)

        cart_item = CartItem.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()

        # --------------------------------------------------
        # ITEM ALREADY IN CART
        # --------------------------------------------------
        if cart_item:
            new_qty = cart_item.quantity + quantity

            CartService.validate_product(product, new_qty)

            cart_item.quantity = new_qty

        else:
            cart_item = CartItem(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
                price_at_add=product.price
            )

            db.session.add(cart_item)

        db.session.commit()

        return cart_item

    # --------------------------------------------------
    # REMOVE FROM CART
    # --------------------------------------------------
    @staticmethod
    def remove_from_cart(user_id: int, product_id: int):
        cart_item = CartItem.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()

        if not cart_item:
            return False

        db.session.delete(cart_item)
        db.session.commit()

        return True

    # --------------------------------------------------
    # UPDATE QUANTITY
    # --------------------------------------------------
    @staticmethod
    def update_quantity(user_id: int, product_id: int, quantity: int):

        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")

        cart_item = CartItem.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()

        if not cart_item:
            raise ValueError("Cart item not found")

        product = cart_item.product

        CartService.validate_product(
            product,
            quantity,
            cart_item.price_at_add
        )

        cart_item.quantity = quantity

        db.session.commit()

        return cart_item

    # --------------------------------------------------
    # GET CART ITEMS
    # --------------------------------------------------
    @staticmethod
    def get_cart_items(user_id: int):
        return CartItem.query.filter_by(user_id=user_id).all()

    # --------------------------------------------------
    # CLEAR CART
    # --------------------------------------------------
    @staticmethod
    def clear_cart(user_id: int):

        CartItem.query.filter_by(user_id=user_id).delete()

        db.session.commit()

        return True

    # --------------------------------------------------
    # SAVE ITEM FOR LATER (PHASE-9)
    # --------------------------------------------------
    @staticmethod
    def save_for_later(user_id: int, cart_id: int):

        cart_item = CartItem.query.filter_by(
            id=cart_id,
            user_id=user_id
        ).first()

        if not cart_item:
            raise ValueError("Cart item not found")

        saved = SavedForLater(
            user_id=user_id,
            product_id=cart_item.product_id
        )

        db.session.add(saved)
        db.session.delete(cart_item)

        db.session.commit()

        return saved


    # --------------------------------------------------
    # MOVE SAVED ITEM BACK TO CART (PHASE-9)
    # --------------------------------------------------
    @staticmethod
    def move_saved_to_cart(user_id: int, saved_id: int):

        saved_item = SavedForLater.query.filter_by(
            id=saved_id,
            user_id=user_id
        ).first()

        if not saved_item:
            raise ValueError("Saved item not found")

        product = saved_item.product

        CartService.validate_product(product, 1)

        existing = CartItem.query.filter_by(
            user_id=user_id,
            product_id=product.id
        ).first()

        if existing:
            existing.quantity += 1
        else:
            existing = CartItem(
                user_id=user_id,
                product_id=product.id,
                quantity=1,
                price_at_add=product.price
            )
            db.session.add(existing)

        db.session.add(cart_item)
        db.session.delete(saved_item)

        db.session.commit()

        return cart_item