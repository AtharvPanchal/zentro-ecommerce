// ===============================
// GLOBAL QTY HANDLER (PDP + CARD + QUICK VIEW)
// ===============================

document.addEventListener("click", function (e) {

  // -------- PLUS ----------
  const plusBtn = e.target.closest(".qty-plus, .pdp-qty-plus");
  if (plusBtn) {

    const container =
      plusBtn.closest(".qty-group") ||
      plusBtn.closest(".pdp-qty-box");

    if (!container) return;

    const input =
      container.querySelector(".qty-input") ||
      container.querySelector(".pdp-qty-input");

    if (!input) return;

    let current = parseInt(input.value) || 1;
    const max = parseInt(input.getAttribute("max")) || 99;

    if (current < max) {
      input.value = current + 1;
    }

    return;
  }

  // -------- MINUS ----------
  const minusBtn = e.target.closest(".qty-minus, .pdp-qty-minus");
  if (minusBtn) {

    const container =
      minusBtn.closest(".qty-group") ||
      minusBtn.closest(".pdp-qty-box");

    if (!container) return;

    const input =
      container.querySelector(".qty-input") ||
      container.querySelector(".pdp-qty-input");

    if (!input) return;

    let current = parseInt(input.value) || 1;

    if (current > 1) {
      input.value = current - 1;
    }

    return;
  }

});

// ===============================
// ADD TO CART – CENTRALIZED HANDLER
// ===============================

let isProcessing = false;

document.addEventListener("click", async (e) => {
  if (isProcessing) return;

  const btn = e.target.closest(".add-cart, #addToCartBtn");
  if (!btn) return;

  const productId = btn.dataset.productId;
  if (!productId) {
    showToast("Product ID missing", "error");
    return;
  }

  isProcessing = true;
  btn.disabled = true;

  let qty = 1;

  // -----------------------------
  // PRODUCT CARD QTY
  // -----------------------------
  const card = btn.closest(".product-card");
  if (card) {
    const qtyInput = card.querySelector(".qty-input");
    if (qtyInput) qty = parseInt(qtyInput.value, 10) || 1;
  }

  // -----------------------------
  // PDP QTY (READ ONLY)
  // -----------------------------
  // PDP QTY
const pdpContainer = btn.closest(".pdp-buy-box");
if (pdpContainer) {
  const pdpQtyInput = pdpContainer.querySelector(".pdp-qty-input");
  if (pdpQtyInput) {
    qty = parseInt(pdpQtyInput.value, 10) || 1;
  }
}


  // Sanity guard
  if (!Number.isInteger(qty) || qty < 1) qty = 1;

  // -----------------------------
  // API CALL
  // -----------------------------
  try {
    const res = await fetch("/api/cart/add", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": getCSRFToken()
      },
      body: new URLSearchParams({
        product_id: productId,
        quantity: qty
      })
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      throw new Error(data.message || "Unable to add to cart");
    }

    await refreshCartBadge();
    showToast("Added to cart 🛒", "success");

  } catch (err) {
    console.error(err);
    showToast(err.message || "Please login first", "error");
  } finally {
    isProcessing = false;
    btn.disabled = false;
  }
});
