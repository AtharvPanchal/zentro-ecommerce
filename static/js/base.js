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
   SAFE STORAGE
====================== */
function safeParse(key, fallback = []) {
  try {
    const v = localStorage.getItem(key);
    return v ? JSON.parse(v) : fallback;
  } catch {
    return fallback;
  }
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
   TOAST SYSTEM
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
      <button class="btn-close btn-close-white me-2 m-auto"></button>
    </div>
  `;

  toastContainer.appendChild(toast);

  if (typeof bootstrap !== "undefined") {
    const bsToast = new bootstrap.Toast(toast, { delay });
    bsToast.show();
  }

  toast.querySelector(".btn-close").onclick = () => toast.remove();
  toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

/* ======================
   FLASH TOAST AUTO REMOVE
====================== */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash-toast").forEach(toast => {
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(120%)";
      setTimeout(() => toast.remove(), 300);
    }, 4500);

    const closeBtn = toast.querySelector(".flash-close");
    if (closeBtn) closeBtn.onclick = () => toast.remove();
  });
});

/* ======================
   CITY SELECTOR
====================== */
function updateCityText() {
  const el = $('#cityText');
  if (el) el.innerHTML = `Delivering to <strong>${ZENTRO.city}</strong>`;
}

$$('.city-select').forEach(btn => {
  btn.addEventListener('click', () => {
    ZENTRO.city = btn.textContent.trim();
    localStorage.setItem(STORAGE.CITY, ZENTRO.city);
    updateCityText();
  });
});

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
  $('#cookieBanner')?.style.setProperty("display", "none");
  showToast('Cookies accepted');
});

/* ======================
   CHAT SUPPORT
====================== */
const chatModalEl = $('#chatModal');
const chatModal = chatModalEl && typeof bootstrap !== "undefined"
  ? new bootstrap.Modal(chatModalEl)
  : null;

$('#openChat')?.addEventListener('click', () => chatModal?.show());

$('#chatForm')?.addEventListener('submit', e => {
  e.preventDefault();
  const success = $('#chatSuccess');
  if (!success) return;

  success.style.display = 'block';

  setTimeout(() => {
    chatModal?.hide();
    e.target.reset();
    success.style.display = 'none';
  }, 1200);
});

/* ======================
   NEW USER MODAL
====================== */
const newUserModalEl = $('#newUserModal');
const newUserModal = newUserModalEl && typeof bootstrap !== "undefined"
  ? new bootstrap.Modal(newUserModalEl)
  : null;

function maybeShowNewUser() {
  if (!localStorage.getItem(STORAGE.NEWUSER)) {
    setTimeout(() => {
      newUserModal?.show();
      localStorage.setItem(STORAGE.NEWUSER, '1');
    }, 3000);
  }
}

/* ======================
   MINI CART
====================== */
const miniEl = $('#miniCartOffcanvas');
const miniInstance = miniEl && typeof bootstrap !== "undefined"
  ? new bootstrap.Offcanvas(miniEl)
  : null;

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
   WISHLIST
====================== */
document.addEventListener("click", function (e) {

  const btn = e.target.closest(".wishlist-btn");
  if (!btn) return;

  if (btn.dataset.loading === "1") return;
  btn.dataset.loading = "1";

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
      btn.classList.add("active","btn-danger");
      btn.classList.remove("btn-outline-danger");
      icon?.classList.replace("fa-regular","fa-solid");
      showToast("Added to wishlist ❤️");
    } else {
      btn.classList.remove("active","btn-danger");
      btn.classList.add("btn-outline-danger");
      icon?.classList.replace("fa-solid","fa-regular");
      showToast("Removed from wishlist");
    }

    refreshWishlistBadge();
  })
  .catch(console.error)
  .finally(() => btn.dataset.loading = "0");
});

/* ======================
   QUICK VIEW
====================== */
document.addEventListener("click", async (e) => {

  const btn = e.target.closest(".quick-view-btn");
  if (!btn) return;

  document.querySelectorAll(".quick-view-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");

  const productId = btn.dataset.id;
  if (!productId) return;

  try {
    const res = await fetch(`/api/product/${productId}`);
    if (!res.ok) return;

    const data = await res.json();

    $("#quickViewTitle").textContent = data.name;
    $("#quickName").textContent = data.name;
    $("#quickPrice").textContent = `₹${data.price}`;

    const img = $("#quickImage");
    img.src = data.image
      ? (data.image.startsWith("static/") ? `/${data.image}` : `/static/${data.image}`)
      : "/static/img/placeholders/product.png";

    const modal = new bootstrap.Modal($("#quickViewModal"));
    const qtyInput = $("#quickViewModal .qty-input");
    if (qtyInput) qtyInput.value = 1;

    modal.show();

  } catch (err) {
    console.error(err);
  }
});

/* ======================
   CART BADGE
====================== */
async function refreshCartBadge() {
  try {
    const res = await fetch("/api/cart");
    if (!res.ok) return;

    const data = await res.json();
    const badge = $("#cartCount");
    if (!badge) return;

    if (!data.success || !data.cart.length) {
      badge.classList.add("d-none");
      return;
    }

    badge.textContent = data.cart.reduce((s, i) => s + i.quantity, 0);
    badge.classList.remove("d-none");

  } catch {}
}
document.addEventListener("DOMContentLoaded", refreshCartBadge);

/* ======================
   WISHLIST BADGE
====================== */
async function refreshWishlistBadge() {
  try {
    const res = await fetch("/api/wishlist/count");
    if (!res.ok) return;

    const data = await res.json();
    const badge = $("#wishlistBadge");
    if (!badge) return;

    if (!data.success || !data.count) {
      badge.classList.add("d-none");
      return;
    }

    badge.textContent = data.count;
    badge.classList.remove("d-none");

  } catch {}
}
document.addEventListener("DOMContentLoaded", refreshWishlistBadge);

/* ======================
   GLOBAL ADD TO CART
====================== */
document.addEventListener("click", async function (e) {

  const btn = e.target.closest(".add-cart");
  if (!btn) return;

  const productId = btn.dataset.productId;
  if (!productId) return;

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
      body: JSON.stringify({ product_id: productId, quantity })
    });

    if (!res.ok) {
      showToast("Failed to add to cart", "error");
      return;
    }

    const data = await res.json();
    if (!data.success) {
      showToast(data.message || "Failed to add to cart", "error");
      return;
    }

    showToast("Added to cart 🛒");
    refreshCartBadge();

  } catch {
    showToast("Server error", "error");
  }
});

/* ======================
   LIVE SEARCH
====================== */
const searchInput = $("#search-input");
const suggestionsBox = $("#search-suggestions");
const searchBtn = $("#search-btn");

let searchTimer = null;

async function fetchSearchSuggestions(query) {
  if (!suggestionsBox) return;

  if (!query || query.length < 2) {
    suggestionsBox.style.display = "none";
    suggestionsBox.innerHTML = "";
    return;
  }

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    if (!res.ok) return;

    const data = await res.json();

    if (!data.success || !data.products.length) {
      suggestionsBox.innerHTML = `<div class="search-empty">No products found</div>`;
      suggestionsBox.style.display = "block";
      return;
    }

    suggestionsBox.innerHTML = "";

    data.products.forEach(p => {
      const item = document.createElement("div");
      item.className = "search-item";
      item.innerHTML = `
        <img src="${p.image || "/static/img/placeholders/product.png"}">
        <div>
          <div class="search-name">${p.name}</div>
          <div class="search-price">₹${p.price}</div>
        </div>
      `;
      item.onclick = () => window.location.href = `/product/${p.id}`;
      suggestionsBox.appendChild(item);
    });

    suggestionsBox.style.display = "block";

  } catch {}
}

searchInput?.addEventListener("input", e => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => fetchSearchSuggestions(e.target.value.trim()), 250);
});

searchInput?.addEventListener("keydown", e => {
  if (e.key === "Enter") {
    const q = searchInput.value.trim();
    if (q) window.location.href = `/search?q=${encodeURIComponent(q)}`;
  }
});

searchBtn?.addEventListener("click", () => {
  const q = searchInput?.value.trim();
  if (q) window.location.href = `/search?q=${encodeURIComponent(q)}`;
});

document.addEventListener("click", e => {
  if (!suggestionsBox) return;
  if (!e.target.closest(".search-box")) {
    suggestionsBox.style.display = "none";
  }
});