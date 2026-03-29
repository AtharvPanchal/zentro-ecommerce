from decimal import Decimal


class PriceService:
    """
    Cart Price Engine
    Handles all cart price calculations
    """

    # --------------------------------------------------
    # SUBTOTAL
    # --------------------------------------------------
    @staticmethod
    def calculate_subtotal(cart_items):
        """
        Sum of all cart item totals
        """

        subtotal = Decimal("0.00")

        for item in cart_items:
            subtotal += Decimal(item.price_at_add) * item.quantity

        return subtotal

    # --------------------------------------------------
    # DISCOUNT
    # --------------------------------------------------
    @staticmethod
    def calculate_discount(subtotal):
        """
        Placeholder discount engine
        Production systems use coupon / campaign rules
        """

        discount = Decimal("0.00")

        # Example rule (temporary)
        if subtotal >= Decimal("5000"):
            discount = subtotal * Decimal("0.05")

        return discount

    # --------------------------------------------------
    # PLATFORM FEE
    # --------------------------------------------------
    @staticmethod
    def calculate_platform_fee(subtotal):
        """
        Small handling fee
        """

        if subtotal == 0:
            return Decimal("0.00")

        return Decimal("10.00")

    # --------------------------------------------------
    # TOTAL
    # --------------------------------------------------
    @staticmethod
    def calculate_total(cart_items):
        """
        Full cart price calculation
        """

        subtotal = PriceService.calculate_subtotal(cart_items)

        discount = PriceService.calculate_discount(subtotal)

        platform_fee = PriceService.calculate_platform_fee(subtotal)

        total = subtotal - discount + platform_fee

        return {
            "subtotal": float(subtotal),
            "discount": float(discount),
            "platform_fee": float(platform_fee),
            "total": float(total)
        }