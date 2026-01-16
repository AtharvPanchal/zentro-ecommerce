"""
Product Validators
==================
Priority-1 Step-3

Request-level validation for admin product routes.
"""


def validate_product_create(data):
    """
    Validate payload for product creation
    """

    if not data:
        return False, "Request body is missing"

    required_fields = ["name", "sku", "category_id", "price"]

    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"

        if data[field] in [None, ""]:
            return False, f"Field '{field}' cannot be empty"

    # SKU validation
    if not isinstance(data["sku"], str):
        return False, "SKU must be a string"

    if len(data["sku"]) < 3:
        return False, "SKU must be at least 3 characters long"

    # Price validation
    try:
        price = float(data["price"])
        if price <= 0:
            return False, "Price must be greater than 0"
    except (ValueError, TypeError):
        return False, "Invalid price value"

    # Images validation (optional)
    images = data.get("images")
    if images is not None:
        if not isinstance(images, list):
            return False, "Images must be a list"
        for img in images:
            if not isinstance(img, str):
                return False, "Each image must be a string"

    return True, None


def validate_product_update(data):
    """
    Validate payload for product update
    """

    if not data:
        return False, "Request body is missing"

    # SKU update forbidden
    if "sku" in data:
        return False, "SKU cannot be updated"

    # Price validation (if present)
    if "price" in data:
        try:
            price = float(data["price"])
            if price <= 0:
                return False, "Price must be greater than 0"
        except (ValueError, TypeError):
            return False, "Invalid price value"

    # Images validation (if present)
    if "images" in data:
        if not isinstance(data["images"], list):
            return False, "Images must be a list"

    return True, None
