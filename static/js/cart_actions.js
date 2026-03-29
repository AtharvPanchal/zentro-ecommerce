// ==========================================
// CART & PDP QUANTITY + UI SYNC (STABLE)
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

  // -------------------------------
  // PDP BUY BOX (PRODUCT DETAIL PAGE)
  // -------------------------------
  const buyBox = document.querySelector(".pdp-buy-box");

  if (buyBox) {
    const stock = parseInt(buyBox.dataset.stock, 10) || 0;

    const minusBtn  = buyBox.querySelector(".pdp-qty-minus");
    const plusBtn   = buyBox.querySelector(".pdp-qty-plus");
    const qtyInput  = buyBox.querySelector(".pdp-qty-input");

    if (minusBtn && plusBtn && qtyInput) {

      const updatePdpState = () => {
        const qty = parseInt(qtyInput.value, 10) || 1;

        minusBtn.disabled = qty <= 1;
        plusBtn.disabled  = stock > 0 && qty >= stock;
      };

      minusBtn.addEventListener("click", () => {
        let qty = parseInt(qtyInput.value, 10) || 1;
        if (qty > 1) {
          qtyInput.value = qty - 1;
          updatePdpState();
        }
      });

      plusBtn.addEventListener("click", () => {
        let qty = parseInt(qtyInput.value, 10) || 1;
        if (stock === 0 || qty < stock) {
          qtyInput.value = qty + 1;
          updatePdpState();
        }
      });

      updatePdpState();
    }
  }

  // -------------------------------
  // CART PAGE ACTIONS
  // -------------------------------
  document.addEventListener("click", async (e) => {

    // ➕ Increase qty
    const incBtn = e.target.closest(".cart-qty-plus");
    if (incBtn) {
      const itemId = incBtn.dataset.itemId;
      await updateCartQty(itemId, "inc");
      return;
    }

    // ➖ Decrease qty
    const decBtn = e.target.closest(".cart-qty-minus");
    if (decBtn) {
      const itemId = decBtn.dataset.itemId;
      await updateCartQty(itemId, "dec");
      return;
    }

    // ❌ Remove item
    const removeBtn = e.target.closest(".cart-remove");
    if (removeBtn) {
      const itemId = removeBtn.dataset.itemId;
      await removeCartItem(itemId);
      return;
    }
  });
});

// ==========================================
// CART API HELPERS (SINGLE SOURCE OF TRUTH)
// ==========================================

async function updateCartQty(itemId, action) {
  try {
    const res = await fetch("/api/cart/update", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": getCSRFToken()
      },
      body: new URLSearchParams({
        item_id: itemId,
        action: action
      })
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      showToast(data.message || "Cart update failed", "error");
      return;
    }

    await syncCartUI();
    refreshCartPage();

  } catch (e) {
    console.error(e);
    showToast("Cart update error", "error");
  }
}

async function removeCartItem(itemId) {
  try {
    const res = await fetch("/api/cart/remove", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": getCSRFToken()
      },
      body: new URLSearchParams({
        item_id: itemId
      })
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      showToast(data.message || "Remove failed", "error");
      return;
    }

    await syncCartUI();
    refreshCartPage();
    showToast("Item removed", "success");

  } catch (e) {
    console.error(e);
    showToast("Remove error", "error");
  }
}

// ==========================================
// UI REFRESH HELPERS
// ==========================================

function refreshCartPage() {
  if (document.body.classList.contains("cart-page")) {
    window.location.reload();
  }
}
