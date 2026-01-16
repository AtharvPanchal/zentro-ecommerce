const cartItemsEl = document.getElementById("cartItems");
const cartSubtotalEl = document.getElementById("cartSubtotal");
const emptyCartEl = document.getElementById("emptyCart");
const cartSectionEl = document.getElementById("cartSection");

const fmtPrice = v => "₹" + Number(v).toLocaleString("en-IN");

function setQtyButtonsDisabled(disabled) {
  document.querySelectorAll('.qty-btn').forEach(btn => {
    btn.disabled = disabled;
  });
}

async function loadCart() {
  try {
    const res = await fetch("/api/cart");
    const data = await res.json();

    if (!data.success || data.cart.length === 0) {
      cartSectionEl.classList.add("d-none");
      emptyCartEl.classList.remove("d-none");
      return;
    }

    renderCart(data.cart);
  } catch (e) {
    console.error("Cart load error");
  }
}

function renderCart(items) {
  cartItemsEl.innerHTML = "";
  let subtotal = 0;

  items.forEach(item => {
    const row = document.createElement("tr");
    subtotal += item.price * item.quantity;

    row.innerHTML = `
      <td>
        <div class="cart-product">
          <img src="${item.image}" alt="${item.name}">
          <div>
            <div class="fw-semibold">${item.name}</div>
            <small class="text-muted">${fmtPrice(item.price)}</small>
          </div>
        </div>
      </td>

      <td class="text-center">
        <div class="qty-control">
  <button class="qty-btn minus" aria-label="Decrease quantity" data-id="${item.id}">−</button>
  <span class="qty-text">${item.quantity}</span>
  <button class="qty-btn plus" aria-label="Increase quantity" data-id="${item.id}">+</button>


</div>

      </td>

      <td class="text-end">
        ${fmtPrice(item.price * item.quantity)}
      </td>

      <td class="text-end">
        <span class="remove-btn" data-id="${item.id}">Remove</span>
      </td>
    `;

    cartItemsEl.appendChild(row);
  });

  cartSubtotalEl.textContent = fmtPrice(subtotal);
}

let qtyUpdating = false;

async function updateQty(cartId, newQty) {
  if (qtyUpdating) return;
qtyUpdating = true;
setQtyButtonsDisabled(true);


  try {
    const res = await fetch("/api/cart/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        cart_id: cartId,
        qty: newQty
      })
    });

    const data = await res.json();

    if (!data.success) {
      showToast?.(data.message || "Error", "error");
      return;
    }

    loadCart();
  } catch (e) {
    showToast?.("Error updating quantity", "error");
  } finally {
    qtyUpdating = false;
    setQtyButtonsDisabled(false);
  }
}

document.addEventListener("click", async e => {
  if (e.target.classList.contains("remove-btn")) {
    const cartId = e.target.dataset.id;

    await fetch("/api/cart/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cart_id: cartId })
    });

    loadCart();
  }
});

document.addEventListener("click", e => {
  if (e.target.classList.contains("qty-btn")) {
    const cartId = e.target.dataset.id;
    const qtySpan = e.target.parentElement.querySelector(".qty-text");
    let qty = parseInt(qtySpan.textContent);

    if (e.target.classList.contains("plus")) qty++;
    if (e.target.classList.contains("minus")) qty--;

    if (qty < 1) return;   // ❗ prevent invalid qty

   qtySpan.textContent = qty;   // instant UI update
   updateQty(cartId, qty);


  }
});


document.addEventListener("DOMContentLoaded", loadCart);

document.getElementById("placeOrderBtn")?.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/order/create", {
      method: "POST"
    });

    const data = await res.json();

    if (!data.success) {
      showToast?.(data.message || "Order failed", "error");
      return;
    }

    showToast("Order placed successfully 🎉");
    window.location.href = "/orders";
  } catch (e) {
    showToast?.("Please login first", "error");
  }
});
