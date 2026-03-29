// 🔒 Cart page guard (CRITICAL)
if (!document.body.classList.contains("cart-page")) {
  console.log("Not cart page, cart.js skipped");
} else {

const cartItemsEl   = document.getElementById("cartItems");   // ✅ MISSING LINE
const cartSubtotalEl = document.getElementById("cartSubtotal");
const emptyCartEl    = document.getElementById("emptyCart");
const cartSectionEl  = document.getElementById("cartSection");
const savedItemsEl = document.getElementById("savedItems");


const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
const fmtPrice = v => "₹" + Number(v).toLocaleString("en-IN");

function setQtyButtonsDisabled(disabled) {
  document.querySelectorAll(".qty-btn").forEach(btn => {
    btn.disabled = disabled;
  });
}

/* ==========================
   LOAD CART
========================== */
async function loadCart() {

  // 🔒 DOM safety (critical)
  if (!cartItemsEl || !cartSectionEl || !emptyCartEl || !cartSubtotalEl) {
    console.error("Cart DOM not ready");
    return;
  }

  try {
  const res = await fetch("/api/cart", { cache: "no-store" });

if (!res.ok) {
  throw new Error("Cart API error");
}

const data = await res.json();

    // RESET UI STATE
    cartItemsEl.innerHTML = "";
    cartSubtotalEl.textContent = fmtPrice(0);

    if (!data.success || !data.cart || data.cart.length === 0) {
      cartSectionEl.classList.add("d-none");
      emptyCartEl.classList.remove("d-none");
      return;
    }

    // SHOW CART
    emptyCartEl.classList.add("d-none");
    cartSectionEl.classList.remove("d-none");

    renderCart(data.cart, data.pricing);
loadSavedItems();

  } catch (e) {
    console.error("Cart load error", e);
  }
}

/* ==========================
   RENDER CART
========================== */
function renderCart(items = [], pricing = {}) {
  items.forEach(item => {

  const safeQty = Math.min(item.quantity, item.stock ?? item.quantity);



    const row = document.createElement("tr");

    if (item.stock === 0) {
  row.classList.add("table-danger");
}
row.dataset.stock = item.stock ?? safeQty;

    row.innerHTML = `
      <td>
        <div class="cart-product">
          <img src="${item.image}" alt="${item.name}">
          <div>
            <div class="fw-semibold">${item.name}</div>
${item.stock === 0 ? '<small class="text-danger">Out of stock</small>' : ''}
            <small class="text-muted">${fmtPrice(item.price)}</small>
          </div>
        </div>
      </td>

      <td class="text-center">
  <div class="qty-control">
    <button class="qty-btn minus" data-id="${item.id}" ${item.stock === 0 ? "disabled" : ""}>−</button>

    <span class="qty-text">${safeQty}</span>

    <button class="qty-btn plus" data-id="${item.id}" ${item.stock === 0 ? "disabled" : ""}>+</button>
  </div>
</td>

      <td class="text-end">
      ${fmtPrice(item.price * safeQty)}

      </td>

      <td class="text-end">
        <span class="remove-btn ${item.stock === 0 ? 'text-muted disabled' : ''}" data-id="${item.id}">Remove</span>
      </td>
    `;

    cartItemsEl.appendChild(row);
  });


  cartSubtotalEl.textContent = fmtPrice(pricing?.total || 0);
}


async function loadSavedItems() {

  if (!savedItemsEl) return;

  try {

    const res = await fetch("/api/saved-items");

    if (!res.ok) return;

    const data = await res.json();

    savedItemsEl.innerHTML = "";

    if (!data.items || data.items.length === 0) {

      savedItemsEl.innerHTML =
        '<div class="text-muted">No items saved yet</div>';

      return;
    }

    data.items.forEach(item => {

      const div = document.createElement("div");

      div.className = "saved-item d-flex justify-content-between align-items-center mb-2";

      div.innerHTML = `
        <div>
          <strong>${item.name}</strong>
          <div class="text-muted">${fmtPrice(item.price)}</div>
        </div>

        <span class="move-cart text-primary"
              data-id="${item.id}"
              style="cursor:pointer;">
          Move to cart
        </span>
      `;

      savedItemsEl.appendChild(div);

    });

  } catch (e) {
    console.error("Saved items load error", e);
  }

}

/* ==========================
   UPDATE QTY
========================== */
let qtyUpdating = false;

async function updateQty(cartId, newQty) {
  if (qtyUpdating) return;

  qtyUpdating = true;
  setQtyButtonsDisabled(true);

  try {
    const res = await fetch("/api/cart/update", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken
      },
      body: JSON.stringify({ cart_id: cartId, qty: newQty })
    });

    if (!res.ok) {
  throw new Error("API error");
}

const data = await res.json();

    if (!data.success) {
  showToast?.(data.message || "Update failed", "error");
  return loadCart();
}


    loadCart();

  } catch {
    showToast?.("Error updating quantity", "error");
    loadCart();
  } finally {
    qtyUpdating = false;
    setQtyButtonsDisabled(false);
  }
}

/* ==========================
   CLICK HANDLERS
========================== */
document.addEventListener("click", async e => {

  // REMOVE
  if (e.target.classList.contains("remove-btn")) {

    if (e.target.classList.contains("text-muted")) {
      return;
    }

    const res = await fetch("/api/cart/remove", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken
      },
      body: JSON.stringify({ cart_id: e.target.dataset.id })
    });

    if (!res.ok) {
      showToast?.("Failed to remove item", "error");
      return;
    }

    loadCart();
    return;
  }

  // SAVE FOR LATER
if (e.target.classList.contains("save-later")) {

  const cartId = e.target.dataset.id;

  const res = await fetch("/api/cart/save-for-later", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken
    },
    body: JSON.stringify({ cart_id: cartId })
  });

  if (!res.ok) {
    showToast?.("Failed to save item", "error");
    return;
  }

  loadCart();
  return;
}


// MOVE SAVED ITEM TO CART
if (e.target.classList.contains("move-cart")) {

  const savedId = e.target.dataset.id;

  const res = await fetch("/api/cart/move-to-cart", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken
    },
    body: JSON.stringify({ saved_id: savedId })
  });

  if (!res.ok) {
    showToast?.("Failed to move item", "error");
    return;
  }

  loadCart();
  return;
}

  // QTY CHANGE
  if (e.target.classList.contains("qty-btn")) {

    const qtySpan = e.target.parentElement.querySelector(".qty-text");
    let qty = parseInt(qtySpan.textContent, 10);

    if (e.target.classList.contains("plus")) {
      qty++;

      const row = e.target.closest("tr");

      if (row?.dataset?.stock) {
        const maxStock = parseInt(row.dataset.stock, 10);

        if (qty > maxStock) {
          showToast?.(`Only ${maxStock} item(s) available`, "warning");
          return;
        }
      }
    }

    if (e.target.classList.contains("minus")) {
      qty--;
    }

    if (qty < 1) {
      showToast?.("Minimum quantity is 1", "warning");
      return;
    }

    qtySpan.textContent = qty;
    updateQty(e.target.dataset.id, qty);
  }

});

/* ==========================
   INIT
========================== */
document.addEventListener("DOMContentLoaded", () => {
  loadCart();
  loadSavedItems();
});

/* ==========================
   DELIVERY PINCODE CHECK
========================== */

const pincodeInput = document.getElementById("pincodeInput");
const checkPincodeBtn = document.getElementById("checkPincodeBtn");
const deliveryResult = document.getElementById("deliveryResult");

checkPincodeBtn?.addEventListener("click", async () => {

  const pincode = pincodeInput.value.trim();

  if (!/^\d{6}$/.test(pincode)) {
    deliveryResult.textContent = "Enter valid 6 digit pincode";
    deliveryResult.className = "text-danger";
    return;
  }

  deliveryResult.textContent = "Checking delivery...";
  deliveryResult.className = "text-muted";

  try {

    const res = await fetch(`/api/delivery/check?pincode=${pincode}`);

    if (!res.ok) {
      throw new Error("Delivery API error");
    }

    const data = await res.json();

    if (!data.deliverable) {
      deliveryResult.textContent = "Delivery not available for this pincode";
      deliveryResult.className = "text-danger";
      return;
    }

    deliveryResult.textContent =
      `Delivery in ${data.estimated_days} days`;

    deliveryResult.className = "text-success";

  } catch {

    deliveryResult.textContent = "Unable to check delivery";
    deliveryResult.className = "text-danger";

  }

});

/* ==========================
   PLACE ORDER (PHASE-4 READY)
========================== */
document.getElementById("placeOrderBtn")?.addEventListener("click", () => {
  showToast?.("Checkout Coming Next 🚀", "info");
});
}