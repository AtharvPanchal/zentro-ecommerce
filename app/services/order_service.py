from app.extensions import db
from app.models import Order, OrderTimeline
from app.utils.time_utils import utc_now


# ---------------------------------------------------
# ✅ Allowed Status Transitions (STATE MACHINE)
# ---------------------------------------------------

ALLOWED_TRANSITIONS = {
    "confirmed": ["shipped", "cancelled"],
    "shipped": ["out_for_delivery"],
    "out_for_delivery": ["delivered"],
    "delivered": ["return_requested"],
    "return_requested": ["returned"],
    "returned": [],
    "cancelled": []
}


# ---------------------------------------------------
# 🔒 Validate Transition
# ---------------------------------------------------

def validate_status_transition(current_status: str, new_status: str):
    if new_status not in ALLOWED_TRANSITIONS.get(current_status, []):
        raise ValueError(
            f"Invalid status transition from '{current_status}' to '{new_status}'"
        )


# ---------------------------------------------------
# 📦 Update Order Status (Main Engine)
# ---------------------------------------------------
def update_order_status(order: Order, new_status: str, note: str = None, commit: bool = False):
    """
    Production-safe order lifecycle update.

    - Validates state transition
    - Updates lifecycle timestamps
    - Inserts timeline event automatically
    - Optional commit control
    """

    current_status = order.status

    # 1️⃣ Validate state machine
    validate_status_transition(current_status, new_status)

    # 2️⃣ Update timestamps
    now = utc_now()

    if new_status == "shipped":
        order.shipped_at = now

    elif new_status == "out_for_delivery":
        order.out_for_delivery_at = now

    elif new_status == "delivered":
        order.delivered_at = now

        from datetime import timedelta
        order.return_window_until = now + timedelta(days=7)

    elif new_status == "cancelled":
        order.cancelled_at = now

    # 3️⃣ Update status
    order.status = new_status

    # 4️⃣ Insert timeline event
    timeline_event = OrderTimeline(
        order_id=order.id,
        status=new_status,
        note=note or f"Status updated to {new_status}"
    )

    db.session.add(timeline_event)

    # 5️⃣ Optional commit
    if commit:
        db.session.commit()

    return order

# ---------------------------------------------------
# 🔁 Request Return (Safe Guard)
# ---------------------------------------------------
def request_return(order: Order, note: str = None, commit: bool = False):

    if order.status != "delivered":
        raise ValueError("Return allowed only for delivered orders")

    if not order.return_window_until:
        raise ValueError("Return window not defined")

    if utc_now() > order.return_window_until:
        raise ValueError("Return window expired")

    update_order_status(order, "return_requested", note, commit=commit)


# ---------------------------------------------------
# ❌ Cancel Order Guard
# ---------------------------------------------------
def cancel_order(order: Order, note: str = None, commit: bool = False):

    if order.status not in ["confirmed"]:
        raise ValueError("Order cannot be cancelled at this stage")

    update_order_status(order, "cancelled", note, commit=commit)