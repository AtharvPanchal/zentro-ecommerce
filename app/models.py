from datetime import datetime
from flask_login import UserMixin
from app.extensions import db
from sqlalchemy.sql import func
import uuid
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import get_history
from app.utils.time_utils import utc_now


# --------------------------------------------------
# USER MODEL
# --------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True, nullable=False, index=True)

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)

    notification_email = db.Column(db.String(255), nullable=False, index=True)

    # 🆕 PROFILE
    phone = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(10), nullable=True)

    password_hash = db.Column(db.String(255), nullable=False)

    session_version = db.Column(db.Integer, default=1, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    lock_until = db.Column(db.DateTime, nullable=True)

    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(255), nullable=True, index=True)

    is_active = db.Column(db.Boolean, default=True)

    role = db.Column(
        db.String(20),
        nullable=False,
        default="user"
    )



    created_at = db.Column(db.DateTime, default=db.func.now())

    # ==================================================
    # 🟢 DERIVED STATUS (INDUSTRY STANDARD)
    # ==================================================
    @property
    def status(self):
        """
        Returns one of: active / locked / disabled
        Single source of truth for user state
        """
        if not self.is_active:
            return "disabled"

        if self.lock_until and self.lock_until > utc_now().replace(tzinfo=None):
            return "locked"

        return "active"

    @property
    def is_locked(self):
        return self.status == "locked"


# --------------------------------------------------
# USER OTP MODEL (FORGOT PASSWORD)
# --------------------------------------------------
class OTP(db.Model):
    __tablename__ = "otps"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    code = db.Column(db.String(6), nullable=False)

    expires_at = db.Column(db.DateTime, nullable=False)

    is_used = db.Column(db.Boolean, default=False)

    resend_count = db.Column(db.Integer, default=0)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "otps",
            lazy="dynamic",
            cascade="all, delete"
        )
    )

    def __repr__(self):
        return f"<OTP user_id={self.user_id} code={self.code}>"


# --------------------------------------------------
# ADMIN MODEL (PRE-CREATED ACCOUNT)
# --------------------------------------------------
class Admin(UserMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)

    # 🔐 ADMIN LOGIN ID (fake / internal)
    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )

    # 📧 REAL ADMIN INBOX (OTP / reset / alerts)
    notification_email = db.Column(
        db.String(255),
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # 🔐 SESSION VERSION
    session_version = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    # 🔐 ACCOUNT LOCKOUT
    failed_login_attempts = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    lock_until = db.Column(
        db.DateTime,
        nullable=True
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    is_super_admin = db.Column(db.Boolean, default=False)

    last_login = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=db.func.now()
    )

    def __repr__(self):
        return f"<Admin id={self.id} email={self.email}>"


# --------------------------------------------------
# ADMIN OTP MODEL (FORGOT / RESET PASSWORD)
# --------------------------------------------------
class AdminOTP(db.Model):
    __tablename__ = "admin_otps"

    id = db.Column(db.Integer, primary_key=True)

    admin_id = db.Column(
        db.Integer,
        db.ForeignKey("admins.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    code = db.Column(
        db.String(6),
        nullable=False
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    is_used = db.Column(
        db.Boolean,
        default=False
    )

    resend_count = db.Column(
        db.Integer,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    admin = db.relationship(
        "Admin",
        backref=db.backref(
            "otps",
            lazy="dynamic",
            cascade="all, delete"
        )
    )

    def __repr__(self):
        return f"<AdminOTP admin_id={self.admin_id} code={self.code}>"





# ------------------------------------------------------------
#   CATEGORY MODEL (PRIORITY-2 : STEP-1)
# ------------------------------------------------------------
class Category(db.Model):
    """
    Category = Product grouping entity
    ----------------------------------
    Priority-2 rules:
    - Soft control only (ACTIVE / INACTIVE)
    - No hard delete
    - Used by Product as FK
    """

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)

    # 🏷 Human readable name
    name = db.Column(
        db.String(150),
        nullable=False,
        unique=True,
        index=True
    )

    # 🔗 URL / system safe identifier
    slug = db.Column(
        db.String(160),
        nullable=False,
        unique=True,
        index=True
    )

    # 🟢 ACTIVE / INACTIVE
    status = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVE"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.now(),
        onupdate=db.func.now()
    )

    # --------------------------------------------------
    # 🔒 HARD DELETE BLOCK
    # --------------------------------------------------
    def delete(self):
        raise Exception("Hard delete is not allowed for Category")

    def __repr__(self):
        return f"<Category id={self.id} name={self.name}>"



# ------------------------------------------------------------
#   PRODUCT MODEL (PRIORITY-1 : CORE PRODUCT CATALOGUE)
# ------------------------------------------------------------
class Product(db.Model):
    """
    Product = core business entity
    --------------------------------
    Priority-1 rules:
    - No inventory logic
    - No analytics fields
    - No hard delete
    - SKU is immutable & unique
    """

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    # 📦 CORE PRODUCT DATA
    name = db.Column(db.String(255), nullable=False)

    # 🔑 BUSINESS IDENTIFIER (IMMUTABLE)
    sku = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True
    )

    # 🔗 CATEGORY (FK – table may exist later)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=False
    )

    price = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    # 🖼 store multiple image URLs
    images = db.Column(
        db.JSON,
        nullable=True
    )

    # 🟢 ACTIVE / INACTIVE (SOFT CONTROL)
    status = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVE"
    )

    created_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False
    )

    # --------------------------------------------------
    # 🔒 HARD DELETE BLOCK
    # --------------------------------------------------
    def delete(self):
        raise Exception("Hard delete is not allowed for Product")


    # --------------------------------------------------
    # 🖼 SAFE IMAGE ACCESSOR (FIXES TEMPLATE BUG)
    # --------------------------------------------------
    @property
    def image_list(self):
        """
        Always returns a python list of image URLs.
        Fixes JSON / string mismatch issues.
        """
        if not self.images:
            return []

        if isinstance(self.images, list):
            return self.images

        # fallback safety (in case DB returns string)
        try:
            import json
            return json.loads(self.images)
        except Exception:
            return []




#----------------------------------------------------------
#   PRODUCT RATING MODEL
#----------------------------------------------------------
class ProductRating(db.Model):
    __tablename__ = "product_ratings"

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    rating = db.Column(db.Integer, nullable=False)

    def update_avg_rating(self):
        avg = (
            db.session.query(func.avg(ProductRating.rating))
            .filter(ProductRating.product_id == self.id)
            .scalar()
        )

        self.rating = round(avg or 0, 1)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("product_id", "user_id", name="uq_user_product_rating"),
    )


# ----------------------------------------------------------
#   PRODUCT REVIEW MODEL
# ----------------------------------------------------------
class ProductReview(db.Model):
        __tablename__ = "product_reviews"

        id = db.Column(db.Integer, primary_key=True)
        product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

        rating = db.Column(db.Integer, nullable=False, default=0)  # ⭐ ADDED
        review_text = db.Column(db.Text, nullable=False)

        is_active = db.Column(db.Boolean, default=False)
        is_reported = db.Column(db.Boolean, default=False)
        report_reason = db.Column(db.String(255))

        created_at = db.Column(db.DateTime, default=datetime.utcnow)

        # relationships
        product = db.relationship("Product", backref="reviews")
        user = db.relationship("User", backref="product_reviews")






#-----------------------------------------------------------
#    ORDER MODEL
#-----------------------------------------------------------
class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    total_amount = db.Column(db.Numeric(10, 2), nullable=False)

    status = db.Column(db.String(20), default="confirmed")  # confirmed / shipped / delivered
    payment_method = db.Column(db.String(20), default="COD")
    payment_status = db.Column(db.String(20), default="pending")

    created_at = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship("User", backref="orders")



#----------------------------------------------------------------
#  ORDER ITEM
#----------------------------------------------------------------
class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship("Order", backref="items")
    product = db.relationship("Product")



#----------------------------------------------------------------
# USER ADDRESS MODEL
#----------------------------------------------------------------
class UserAddress(db.Model):
    __tablename__ = "user_addresses"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15), nullable=False)

    house_no = db.Column(db.String(100), nullable=False)
    area = db.Column(db.String(150), nullable=False)
    landmark = db.Column(db.String(150), nullable=True)

    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)

    address_type = db.Column(db.String(20), default="home")  # home / work
    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship(
        "User",
        backref=db.backref(
            "addresses",
            cascade="all, delete",
            lazy="dynamic"
        )
    )


#----------------------------------------------------------
# WISHLIST MODEL
#----------------------------------------------------------
class Wishlist(db.Model):
    __tablename__ = "wishlists"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    is_purchased = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    user = db.relationship("User", backref="wishlist_items")
    product = db.relationship("Product", backref="wishlisted_by")


#-------------------------------------------------------------
#    CART ITEM
#------------------------------------------------------------
class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    created_at = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship("User", backref="cart_items")
    product = db.relationship("Product")


# --------------------------------------------------
# LOGIN ACTIVITY (AUDIT / SECURITY)
# --------------------------------------------------
class LoginActivity(db.Model):
    __tablename__ = "login_activities"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    device = db.Column(db.String(100), nullable=True)

    login_status = db.Column(
        db.String(20),
        nullable=False
    )  # success / failed / locked / disabled

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        index=True,
        default=lambda: utc_now().replace(tzinfo=None)
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "login_activities",
            lazy="dynamic",
            cascade="all, delete"
        )
    )

    def __repr__(self):
        return f"<LoginActivity user_id={self.user_id} status={self.login_status}>"



# --------------------------------------------------
# USER STATUS REASON (ADMIN ACTION REASONS)
# --------------------------------------------------
class UserStatusReason(db.Model):
    __tablename__ = "user_status_reasons"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    admin_id = db.Column(
        db.Integer,
        db.ForeignKey("admins.id"),
        nullable=False,
        index=True
    )

    action = db.Column(
        db.String(20),
        nullable=False
    )
    # disable / lock / unlock / enable

    reason = db.Column(
        db.String(100),
        nullable=False
    )
    # Security / Policy / HR / Compliance

    note = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user = db.relationship("User", backref="status_reasons")
    admin = db.relationship("Admin")

    def __repr__(self):
        return f"<UserStatusReason user_id={self.user_id} action={self.action}>"




# --------------------------------------------------
# ADMIN ACTIVITY LOG (SECURITY AUDIT)
# --------------------------------------------------
class AdminActivityLog(db.Model):
    __tablename__ = "admin_activity_logs"

    # 🔑 PRIMARY KEY
    id = db.Column(db.Integer, primary_key=True)

    # 🔗 RELATIONS
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # 🧾 ACTION DETAILS
    action = db.Column(db.String(255), nullable=False)

    # 🆔 HUMAN READABLE LOG ID
    log_ref = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # 🌐 CONTEXT INFO
    ip_address = db.Column(db.String(45))   # IPv4 / IPv6 safe
    user_agent = db.Column(db.Text)

    # 🚨 SEVERITY LEVEL
    severity = db.Column(
        db.String(20),
        nullable=False,
        default="LOW"
    )
    # LOW | MEDIUM | HIGH | CRITICAL

    # 📝 OPTIONAL COMMENT / REASON
    reason = db.Column(db.Text)

    # 🆕 STARTUP GRADE FIELDS
    actor_type = db.Column(
        db.String(20),
        nullable=False,
        default="admin"
    )  # admin / system

    is_bulk = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    is_archived = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    # ⏱ TIME (UTC ONLY – INDUSTRY STANDARD)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    # 🔁 RELATIONSHIP HELPERS
    admin = db.relationship("Admin", backref="activity_logs")
    user = db.relationship("User", backref="activity_logs")

    # 🛠 AUTO GENERATE LOG REF
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.log_ref:
            self.log_ref = f"AL-{uuid.uuid4().hex[:10].upper()}"




# --------------------------------------------------
# AI AUDIT INSIGHT MODEL (PRIORITY-3 STEP-5)
# --------------------------------------------------
class AuditInsight(db.Model):
    __tablename__ = "audit_insights"

    id = db.Column(db.Integer, primary_key=True)

    # SECURITY / OPERATIONAL / AUTOMATION / IMPROVEMENT
    insight_type = db.Column(db.String(50), nullable=False)

    # HIGH / MEDIUM / INFO
    severity = db.Column(db.String(20), nullable=False)

    message = db.Column(db.Text, nullable=False)

    recommendation = db.Column(db.Text, nullable=True)

    confidence = db.Column(db.Float, default=0.0)

    # 🔁 GOVERNANCE FLAGS
    is_seen = db.Column(db.Boolean, default=False, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)

    # ⏱ GENERATED TIME (UTC)
    generated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<AuditInsight {self.severity} {self.insight_type}>"



# ==================================================
# 🔒 IMMUTABLE AUDIT LOG PROTECTION (ENTERPRISE)
# ==================================================
@event.listens_for(AdminActivityLog, "before_update")
def protect_audit_log(mapper, connection, target):
    """
    Prevent modification of audit logs.
    Only is_archived field is allowed to change.
    """

    allowed_fields = {"is_archived"}

    for attr in target.__mapper__.attrs:
        history = get_history(target, attr.key)

        if history.has_changes():
            if attr.key not in allowed_fields:
                raise ValueError(
                    f"Audit log is immutable. Field '{attr.key}' cannot be modified."
                )




@event.listens_for(AdminActivityLog, "before_delete")
def prevent_admin_activity_log_delete(mapper, connection, target):
    if target.is_archived:
        return  # allow cleanup service
    raise IntegrityError(
        "Active AdminActivityLog records cannot be deleted.",
        params=None,
        orig=None
    )

