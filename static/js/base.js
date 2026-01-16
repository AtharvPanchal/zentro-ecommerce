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
   STORAGE KEYS
====================== */
const STORAGE = {
  CART: 'zentro_cart',
  WISHLIST: 'zentro_wishlist',
  CITY: 'zentro_city',
  COOKIE: 'zentro_cookie_accepted',
  NEWUSER: 'zentro_newuser_shown',
  MINI_OPEN: 'zentro_mini_open'
};

/* ======================
   GLOBAL STATE (SHARED)
====================== */
window.ZENTRO = {
  cart: [],
  wishlist: [],
  city: localStorage.getItem(STORAGE.CITY) || 'Delhi'
};

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

function saveCart() {
  localStorage.setItem(STORAGE.CART, JSON.stringify(ZENTRO.cart));
}
function saveWishlist() {
  localStorage.setItem(STORAGE.WISHLIST, JSON.stringify(ZENTRO.wishlist));
}
function loadCart() {
  ZENTRO.cart = safeParse(STORAGE.CART, []);
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

/* ======================
   BADGES (CART / WISHLIST)
====================== */
function updateBadges() {
  const cartCount = ZENTRO.cart.reduce((s, i) => s + (i.qty || 1), 0);
  const wlCount = ZENTRO.wishlist.length;

  const cartBadge = $('#cartBadge');
  const wlBadge = $('#wishlistBadge');

  if (cartBadge) {
    cartBadge.style.display = cartCount ? 'inline-block' : 'none';
    cartBadge.textContent = cartCount;
  }

  if (wlBadge) {
    wlBadge.style.display = wlCount ? 'inline-block' : 'none';
    wlBadge.textContent = wlCount;
  }
}

/* ======================
   CART CORE (NO PRODUCTS LOGIC)
====================== */
function removeFromCart(id) {
  const idx = ZENTRO.cart.findIndex(i => i.id === id);
  if (idx !== -1) {
    ZENTRO.cart.splice(idx, 1);
    saveCart();
    updateBadges();
    showToast('Removed from cart');
  }
}

/* ======================
   WISHLIST CORE
====================== */
function toggleWishlist(id) {
  const i = ZENTRO.wishlist.indexOf(id);
  if (i === -1) {
    ZENTRO.wishlist.push(id);
    showToast('Added to wishlist');
  } else {
    ZENTRO.wishlist.splice(i, 1);
    showToast('Removed from wishlist');
  }
  saveWishlist();
  updateBadges();
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
  loadCart();
  loadWishlist();
  updateCityText();
  updateBadges();
  checkCookieBanner();
  maybeShowNewUser();

  if (localStorage.getItem(STORAGE.MINI_OPEN)) {
    setTimeout(() => miniInstance?.show(), 300);
  }
}

document.addEventListener('DOMContentLoaded', bootBase);
window.addEventListener('beforeunload', () => {
  saveCart();
  saveWishlist();
});


document.addEventListener("DOMContentLoaded", () => {
  loadProducts();
});

function loadProducts() {
  fetch("/api/products")
    .then(res => res.json())
    .then(data => {
      if (!data.success) return;

      const grid = document.getElementById("productsGrid");
      if (!grid) return;

      grid.innerHTML = "";

      data.products.forEach(p => {
        grid.innerHTML += `
          <div class="col-md-4 col-lg-3">
            <div class="card h-100 shadow-sm">
              <img src="${p.image}" class="card-img-top" style="height:200px;object-fit:cover">
              <div class="card-body">
                <h6 class="fw-bold">${p.name}</h6>
                <div class="mb-1">⭐ ${p.rating}</div>
                <div>
                  <span class="fw-bold text-success">₹${p.price}</span>
                  ${
                    p.old_price
                      ? `<small class="text-muted text-decoration-line-through ms-2">₹${p.old_price}</small>`
                      : ""
                  }
                </div>
              </div>
              <div class="card-footer bg-white border-0">
                <button class="btn btn-dark w-100">
                  Add to Cart
                </button>
              </div>
            </div>
          </div>
        `;
      });
    })
    .catch(err => console.error(err));
}

