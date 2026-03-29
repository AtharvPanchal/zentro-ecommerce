/* ======================
   STORAGE KEYS
====================== */
const STORAGE = {
  WISHLIST: 'zentro_wishlist',
  CITY: 'zentro_city',
  COOKIE: 'zentro_cookie_accepted',
  NEWUSER: 'zentro_newuser_shown',
  MINI_OPEN: 'zentro_mini_open'
};

/* ======================
   GLOBAL STATE
====================== */
window.ZENTRO = {
  wishlist: [],
  city: localStorage.getItem(STORAGE.CITY) || 'Delhi'
};


// AUTO DISMISS FLASH TOASTS
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash-toast").forEach(toast => {

    // Auto remove after 4.5s
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(120%)";
      setTimeout(() => toast.remove(), 300);
    }, 4500);

    // Manual close
    toast.querySelector(".flash-close").onclick = () => toast.remove();
  });
});


/*************************************************
 * ZENTRO – BASE JS (GLOBAL)
 * File: static/js/base.js
 * Used by ALL pages (navbar, cart, toast, modals)
 *************************************************/

/* ======================
   BASIC HELPERS
====================== */
const $ = sel => document.querySelector(sel);
const $$ = sel => Array.from(document.querySelectorAll(sel));
const fmtPrice = v => '₹' + Number(v).toLocaleString('en-IN');

/* ======================
   CSRF TOKEN HELPER
====================== */
function getCSRFToken() {
  return document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute("content");
}




/* ======================
   SAFE STORAGE HELPERS
====================== */
function safeParse(key, fallback = []) {
  try {
    const v = localStorage.getItem(key);
    return v ? JSON.parse(v) : fallback;
  } catch {
    return fallback;
  }
}


function saveWishlist() {
  localStorage.setItem(STORAGE.WISHLIST, JSON.stringify(ZENTRO.wishlist));
}

function loadWishlist() {
  ZENTRO.wishlist = safeParse(STORAGE.WISHLIST, []);
}

/* ======================
   ACCESSIBILITY ANNOUNCER
====================== */
const announcer = $('#announcer');
function announce(msg) {
  if (announcer) announcer.textContent = msg;
}

/* ======================
   TOAST SYSTEM (GLOBAL)
====================== */
const toastContainer = $('#toastContainer');

function showToast(msg, type = 'success', delay = 2500) {
  announce(msg);
  if (!toastContainer) return;

  const toast = document.createElement('div');
  toast.className = `toast text-white ${type === 'error' ? 'bg-danger' : 'bg-success'}`;
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${msg}</div>
      <button class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  toastContainer.appendChild(toast);

  const bsToast = new bootstrap.Toast(toast, { delay });
  bsToast.show();

  toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

/* ======================
   CITY SELECTOR
====================== */
function updateCityText() {
  const el = $('#cityText');
  if (el) el.innerHTML = `Delivering to <strong>${ZENTRO.city}</strong>`;
}

$$('.city-select').forEach(btn => {
  btn.addEventListener('click', e => {
    ZENTRO.city = e.target.textContent.trim();
    localStorage.setItem(STORAGE.CITY, ZENTRO.city);
    updateCityText();
  });
});


/* =========================
update badge
=========================*/
function updateBadges() {
  const wlBadge = document.getElementById("wishlistBadge");
  if (wlBadge) {
    wlBadge.textContent = ZENTRO.wishlist.length;
    wlBadge.style.display = ZENTRO.wishlist.length ? "inline-block" : "none";
  }
}


/* ======================
   COOKIE BANNER
====================== */
function checkCookieBanner() {
  if (!localStorage.getItem(STORAGE.COOKIE)) {
    const b = $('#cookieBanner');
    if (b) b.style.display = 'flex';
  }
}

$('#acceptCookies')?.addEventListener('click', () => {
  localStorage.setItem(STORAGE.COOKIE, '1');
  $('#cookieBanner').style.display = 'none';
  showToast('Cookies accepted');
});

/* ======================
   CHAT SUPPORT
====================== */
const chatModalEl = $('#chatModal');
const chatModal = chatModalEl ? new bootstrap.Modal(chatModalEl) : null;

$('#openChat')?.addEventListener('click', () => chatModal?.show());

$('#chatForm')?.addEventListener('submit', e => {
  e.preventDefault();
  $('#chatSuccess').style.display = 'block';
  setTimeout(() => {
    chatModal.hide();
    e.target.reset();
    $('#chatSuccess').style.display = 'none';
  }, 1200);
});

/* ======================
   NEW USER MODAL
====================== */
const newUserModalEl = $('#newUserModal');
const newUserModal = newUserModalEl ? new bootstrap.Modal(newUserModalEl) : null;

function maybeShowNewUser() {
  if (!localStorage.getItem(STORAGE.NEWUSER)) {
    setTimeout(() => {
      newUserModal?.show();
      localStorage.setItem(STORAGE.NEWUSER, '1');
    }, 3000);
  }
}

/* ======================
   MINI CART OFFCANVAS
====================== */
const miniEl = $('#miniCartOffcanvas');
const miniInstance = miniEl ? new bootstrap.Offcanvas(miniEl) : null;

$('#mobileCart')?.addEventListener('click', () => miniInstance?.show());

miniEl?.addEventListener('shown.bs.offcanvas', () => {
  localStorage.setItem(STORAGE.MINI_OPEN, '1');
});
miniEl?.addEventListener('hidden.bs.offcanvas', () => {
  localStorage.removeItem(STORAGE.MINI_OPEN);
});

/* ======================
   BOOT
====================== */
function bootBase() {
  loadWishlist();
  updateCityText();
  checkCookieBanner();
  maybeShowNewUser();

  if (localStorage.getItem(STORAGE.MINI_OPEN)) {
    setTimeout(() => miniInstance?.show(), 300);
  }
}

document.addEventListener('DOMContentLoaded', bootBase);




/* ======================
   WISHLIST (PRODUCT CARD)
====================== */
document.addEventListener("click", function (e) {

  const btn = e.target.closest(".wishlist-btn");
  if (!btn) return;

  const productId = btn.dataset.id;
  if (!productId) return;

  fetch(`/wishlist/toggle/${productId}`, {
  method: "POST",
  headers: {
    "X-CSRFToken": getCSRFToken(),
    "X-Requested-With": "XMLHttpRequest"
  }
})


  .then(res => {
    // 🔒 Not logged in
    if (res.status === 401) {
      window.location.href = "/login";
      return;
    }
    return res.json();
  })
  .then(data => {
    if (!data || !data.success) return;

    const icon = btn.querySelector("i");

    if (data.added) {
  btn.classList.add("active");
  btn.classList.remove("btn-outline-danger");
  btn.classList.add("btn-danger");

  icon.classList.remove("fa-regular");
  icon.classList.add("fa-solid");

  showToast("Added to wishlist ❤️");
} else {
  btn.classList.remove("active");
  btn.classList.remove("btn-danger");
  btn.classList.add("btn-outline-danger");

  icon.classList.remove("fa-solid");
  icon.classList.add("fa-regular");

  showToast("Removed from wishlist");
}
refreshWishlistBadge();

  })
  .catch(err => console.error(err));

});


/*=============================================
 QUICK VIEW PRODUCT MODAL
=============================================*/
document.addEventListener("click", async (e) => {

  const btn = e.target.closest(".quick-view-btn");
  if (!btn) return;

  // mark active button
  document
    .querySelectorAll(".quick-view-btn")
    .forEach(b => b.classList.remove("active"));

  btn.classList.add("active");

  const productId = btn.dataset.id;
  if (!productId) return;

  try {
    const res = await fetch(`/api/product/${productId}`);
    const data = await res.json();

    // Fill modal
    document.getElementById("quickViewTitle").textContent = data.name;
    document.getElementById("quickName").textContent = data.name;
    document.getElementById("quickPrice").textContent = `₹${data.price}`;

    const img = document.getElementById("quickImage");
    if (data.image) {
      img.src = data.image.startsWith("static/")
        ? `/${data.image}`
        : `/static/${data.image}`;
    } else {
      img.src = "/static/img/placeholders/product.png";
    }

    const modal = new bootstrap.Modal(
      document.getElementById("quickViewModal")
    );

    const qtyInput = document.querySelector("#quickViewModal .qty-input");
if (qtyInput) qtyInput.value = 1;

    modal.show();

  } catch (err) {
    console.error("Quick view error", err);
  }
});



/* ======================
   QUICK VIEW BUTTON RESET ON CLOSE
====================== */
const qvModalEl = document.getElementById("quickViewModal");

if (qvModalEl) {
  qvModalEl.addEventListener("hidden.bs.modal", () => {
    document
      .querySelectorAll(".quick-view-btn.active")
      .forEach(btn => btn.classList.remove("active"));
  });
}


/* ======================
   UPDATE CART BADGE
====================== */
async function refreshCartBadge() {
  try {
    const res = await fetch("/api/cart");
    const data = await res.json();

    const badge = document.getElementById("cartCount");
    if (!badge) return;

    if (!data.success || data.cart.length === 0) {
      badge.classList.add("d-none");
      return;
    }

    const totalQty = data.cart.reduce((s, i) => s + i.quantity, 0);
    badge.textContent = totalQty;
    badge.classList.remove("d-none");

  } catch (e) {
    console.error("Cart badge error");
  }
}

document.addEventListener("DOMContentLoaded", refreshCartBadge);

/* ======================
   UPDATE WISHLIST BADGE (BACKEND TRUTH)
====================== */
async function refreshWishlistBadge() {
  try {
    const res = await fetch("/api/wishlist/count");
    if (!res.ok) return;

    const data = await res.json();
    const badge = document.getElementById("wishlistBadge");
    if (!badge) return;

    if (!data.success || data.count === 0) {
      badge.classList.add("d-none");
      return;
    }

    badge.textContent = data.count;
    badge.classList.remove("d-none");

  } catch (e) {
    console.error("Wishlist badge error", e);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  refreshWishlistBadge();
});

/* ======================
   GLOBAL QTY HANDLER (PDP + CARD + MODAL)
====================== */

document.addEventListener("click", function (e) {

  const minusBtn = e.target.closest(".qty-minus");
  const plusBtn = e.target.closest(".qty-plus");

  if (!minusBtn && !plusBtn) return;

  // Find closest container that has qty input
  const container = e.target.closest(".qty-group, .pdp-qty-box, #quickViewModal");
  if (!container) return;

  const input = container.querySelector(".qty-input");
  if (!input) return;

  let current = parseInt(input.value || 1, 10);
  const stock = parseInt(input.dataset.stock || 9999, 10);

  if (minusBtn) {
    if (current > 1) {
      input.value = current - 1;
    }
  }

  if (plusBtn) {
    if (current < stock) {
      input.value = current + 1;
    } else {
      showToast("Maximum stock reached", "error");
    }
  }

});

/* ======================
   GLOBAL ADD TO CART
====================== */

document.addEventListener("click", async function (e) {

  const btn = e.target.closest(".add-cart");
  if (!btn) return;

  const productId = btn.dataset.productId;
  if (!productId) {
    showToast("Product ID missing", "error");
    return;
  }

  // Find qty input in same container
  const container = btn.closest(".pdp-buy-box, .qty-group, #quickViewModal, .card");
  const qtyInput = container?.querySelector(".qty-input");

  const quantity = qtyInput ? parseInt(qtyInput.value, 10) : 1;

  try {
    const res = await fetch("/api/cart/add", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken()
      },
      body: JSON.stringify({
        product_id: productId,
        quantity: quantity
      })
    });

    const data = await res.json();

    if (!data.success) {
      showToast(data.message || "Failed to add to cart", "error");
      return;
    }

    showToast("Added to cart 🛒");
    refreshCartBadge();

  } catch (err) {
    console.error(err);
    showToast("Server error", "error");
  }

});



/* ======================
   LIVE SEARCH SYSTEM
====================== */

const searchInput = document.getElementById("search-input");
const suggestionsBox = document.getElementById("search-suggestions");
const searchBtn = document.getElementById("search-btn");

let searchTimer = null;

async function fetchSearchSuggestions(query) {

  if (!query || query.length < 2) {
    suggestionsBox.style.display = "none";
    suggestionsBox.innerHTML = "";
    return;
  }

  try {

    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();

    if (!data.success || !data.products.length) {
      suggestionsBox.innerHTML = `
        <div class="search-empty">
          No products found
        </div>`;
      suggestionsBox.style.display = "block";
      return;
    }

    suggestionsBox.innerHTML = "";

    data.products.forEach(p => {

      const img = p.image || "/static/img/placeholders/product.png";

      const item = document.createElement("div");
      item.className = "search-item";

      item.innerHTML = `
        <img src="${img}">
        <div>
          <div class="search-name">${p.name}</div>
          <div class="search-price">₹${p.price}</div>
        </div>
      `;

      item.addEventListener("click", () => {
        window.location.href = `/product/${p.id}`;
      });

      suggestionsBox.appendChild(item);
    });

    suggestionsBox.style.display = "block";

  } catch (err) {
    console.error("Search error", err);
  }
}


/* Debounce typing */
searchInput?.addEventListener("input", e => {

  const q = e.target.value.trim();

  clearTimeout(searchTimer);

  searchTimer = setTimeout(() => {
    fetchSearchSuggestions(q);
  }, 250);

});


/* Enter key search */
searchInput?.addEventListener("keypress", e => {

  if (e.key === "Enter") {

    const q = searchInput.value.trim();

    if (!q) return;

    window.location.href = `/search?q=${encodeURIComponent(q)}`;
  }

});


/* Search button click */
searchBtn?.addEventListener("click", () => {

  const q = searchInput.value.trim();

  if (!q) return;

  window.location.href = `/search?q=${encodeURIComponent(q)}`;
});


/* Click outside close dropdown */
document.addEventListener("click", e => {

  if (!e.target.closest(".search-box")) {
    suggestionsBox.style.display = "none";
  }

});