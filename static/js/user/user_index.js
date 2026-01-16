/***********************
 * ZENTRO – User Index JS
 * Homepage logic only
 ***********************/

/* ----------------- Utilities ----------------- */
const $ = sel => document.querySelector(sel);
const $$ = sel => Array.from(document.querySelectorAll(sel));
const fmtPrice = v => '₹' + Number(v).toLocaleString('en-IN');

function debounce(fn, wait = 220) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), wait);
  };
}

/* ----------------- Storage Keys ----------------- */
const STORAGE = {
  CART: 'zentro_cart',
  WISHLIST: 'zentro_wishlist',
  CITY: 'zentro_city',
  COOKIE: 'zentro_cookie_accepted',
  NEWUSER: 'zentro_newuser_shown',
  MINI_OPEN: 'zentro_mini_open'
};

/* ----------------- Announcer + Toast ----------------- */
const announcer = $('#announcer');
const toastContainer = $('#toastContainer');

function announce(text) {
  if (announcer) announcer.textContent = text;
}

function showToast(msg, type = 'success', timeout = 2500) {
  announce(msg);
  const toast = document.createElement('div');
  toast.className = `toast ${type === 'error' ? 'bg-danger' : 'bg-success'} text-white`;
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${msg}</div>
      <button class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  toastContainer.appendChild(toast);
  const bsToast = new bootstrap.Toast(toast, { delay: timeout });
  bsToast.show();
  toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

/* ----------------- State ----------------- */
let state = {
  products: [],
  filtered: [],
  perPage: 8,
  shown: 8,
  cart: [],
  wishlist: [],
  currentCity: localStorage.getItem(STORAGE.CITY) || 'Delhi',
  page: 1,
  hasNext: true
};

/* ----------------- Storage Helpers ----------------- */
function safeParse(key, fallback = []) {
  try {
    const v = localStorage.getItem(key);
    return v ? JSON.parse(v) : fallback;
  } catch {
    return fallback;
  }
}

function saveWishlist() {
  localStorage.setItem(STORAGE.WISHLIST, JSON.stringify(state.wishlist));
}

/* ----------------- Badges ----------------- */
function updateBadges() {
  const cartCount = state.cart.reduce((s, i) => s + i.qty, 0);
  const wlCount = state.wishlist.length;

  if ($('#cartBadge')) {
    $('#cartBadge').style.display = cartCount ? 'inline-block' : 'none';
    $('#cartBadge').textContent = cartCount;
  }

  if ($('#wishlistBadge')) {
    $('#wishlistBadge').style.display = wlCount ? 'inline-block' : 'none';
    $('#wishlistBadge').textContent = wlCount;
  }
}

/* ----------------- API FETCH ----------------- */
async function fetchProducts(reset = false) {

  // ✅ SKELETON SHOW (CORRECT PLACE)
  if (reset && $('#productSkeleton')) {
    $('#productSkeleton').style.display = 'flex';
    $('#productsGrid').innerHTML = '';
  }

  if (reset) {
    state.page = 1;
    state.products = [];
    state.hasNext = true;
  }

  if (!state.hasNext) return;

  const params = new URLSearchParams({
    page: state.page,
    limit: state.perPage,
    category: $('#search-category')?.value || 'all',
    search: $('#search-input')?.value || '',
    sort: $('#sortSelect')?.value || ''
  });

  const res = await fetch(`/api/products?${params.toString()}`);
  const data = await res.json();

  if (!data.success) return;

  state.products.push(...data.products);
  state.hasNext = data.pagination.has_next;
  state.page++;

  renderDeals();
  renderProducts();
}

/* ----------------- Deals ----------------- */
function renderDeals() {
  const row = $('#dealsRow');
  if (!row) return;
  row.innerHTML = '';

  state.products.slice(0, 6).forEach(p => {
    const img = p.image || p.image_url || '/static/img/placeholders/product.png';

    row.innerHTML += `
      <div class="deal-card">
        <img src="${img}" style="width:100%;height:120px;object-fit:cover">
        <div class="fw-bold mt-1">${p.name}</div>
        <div>${fmtPrice(p.price)}</div>
        <button class="btn btn-sm btn-primary quick-view-btn" data-id="${p.id}">
          Quick View
        </button>
      </div>
    `;
  });
}

/*-------------------Filter --------------------------*/
function applyAdvancedFilters() {
  const minPrice = Number($('#minPrice')?.value) || 0;
  const maxPrice = Number($('#maxPrice')?.value) || Infinity;

  const categories = $$('.category-filter:checked').map(el => el.value);
  const brands = $$('.brand-filter:checked').map(el => el.value);
  const rating = Number(document.querySelector('.rating-filter:checked')?.value || 0);
  const stockOnly = $('#stockOnly')?.checked;

  state.filtered = state.products.filter(p => {
    if (p.price < minPrice || p.price > maxPrice) return false;
    if (categories.length && !categories.includes(p.category)) return false;
    if (brands.length && !brands.includes(p.brand)) return false;
    if (rating && (p.rating || 0) < rating) return false;
    if (stockOnly && p.stock <= 0) return false;
    return true;
  });

  applySort(true);
}


function applySort(fromFilter = false) {
  const sortVal = $('#sortSelect')?.value || '';
  let list = fromFilter || state.filtered.length
    ? [...state.filtered]
    : [...state.products];

  switch (sortVal) {
    case 'price_low':
      list.sort((a, b) => a.price - b.price);
      break;

    case 'price_high':
      list.sort((a, b) => b.price - a.price);
      break;

    case 'rating':
      list.sort((a, b) => (b.rating || 0) - (a.rating || 0));
      break;

    case 'newest':
      list.sort((a, b) => b.id - a.id);
      break;
  }

  renderList(list);
}


function renderList(list) {
  const grid = $('#productsGrid');
  if (!grid) return;

  grid.innerHTML = '';

  if (!list.length) {
    $('#noProducts')?.style.display = 'block';
    return;
  } else {
    $('#noProducts')?.style.display = 'none';
  }

  list.forEach(p => {
    const img = p.image || p.image_url || '/static/img/placeholders/product.png';
    const oldPrice = p.old_price || p.oldPrice;

    grid.innerHTML += `
      <div class="col-12 col-sm-6 col-lg-3">
        <div class="product-card">
          <div class="product-image">
            <img src="${img}" alt="${p.name}">
          </div>

          <h6>${p.name}</h6>

          ${p.rating ? `<div class="rating">⭐ ${p.rating}</div>` : ''}

          <div class="d-flex align-items-center gap-1">
            <span class="fw-bold text-success">₹${p.price}</span>
            ${oldPrice ? `<span class="old-price">₹${oldPrice}</span>` : ''}
          </div>

          <button class="btn btn-dark btn-sm w-100 mt-2 add-cart"
                  data-id="${p.id}">
            Add to Cart
          </button>
        </div>
      </div>
    `;
  });

  $('#shownCount') && ($('#shownCount').textContent = list.length);
  $('#totalCount') && ($('#totalCount').textContent = list.length);
}

// Apply Filters
$('#applyFilterBtn')?.addEventListener('click', applyAdvancedFilters);

// Sort Change
$('#sortSelect')?.addEventListener('change', () => applySort());


/* ----------------- Products Grid ----------------- */
function toggleWishlist(id, btn) {
  const idx = state.wishlist.indexOf(id);

  if (idx === -1) {
    state.wishlist.push(id);
    btn.classList.add("active");
    showToast("Added to wishlist ❤️");
  } else {
    state.wishlist.splice(idx, 1);
    btn.classList.remove("active");
    showToast("Removed from wishlist");
  }

  saveWishlist();
  updateBadges();
}


function renderProducts() {
if ($('#productSkeleton')) {
  $('#productSkeleton').style.display = 'none';
}

  const grid = $('#productsGrid');
  if (!grid) return;
  grid.innerHTML = '';

  if (!state.products.length) {
    if ($('#noProducts')) $('#noProducts').style.display = 'block';
    return;
  } else {
    if ($('#noProducts')) $('#noProducts').style.display = 'none';
  }

  state.products.forEach(p => {
    const saleBadge = oldPrice ? `<div class="product-badge">SALE</div>` : '';
    const stockBadge = p.stock === 0 ? `<div class="out-stock-badge">OUT</div>` : '';
    const img = p.image || p.image_url || '/static/img/placeholders/product.png';
    const oldPrice = p.old_price || p.oldPrice;
    const badge = oldPrice ? `<div class="product-badge">SALE</div>` : '';
    const liked = state.wishlist.includes(p.id);



    grid.innerHTML += `
      <div class="col-12 col-sm-6 col-lg-3">
        <div class="product-card">
          <div class="product-image position-relative">
  ${saleBadge}
  ${stockBadge}

  <div class="product-overlay">
    <button class="overlay-btn quick-view-btn" data-id="${p.id}">
      <i class="fa fa-eye"></i>
    </button>
    <button class="overlay-btn wishlist-btn ${liked ? 'active' : ''}" data-id="${p.id}">

      <i class="fa fa-heart"></i>
    </button>
  </div>

  <img src="${img}" alt="${p.name}" loading="lazy">

</div>



          <h6>${p.name}</h6>

          ${p.rating ? `<div class="rating">⭐ ${p.rating}</div>` : ''}

          <div class="d-flex align-items-center gap-1">
            <span class="fw-bold text-success">${fmtPrice(p.price)}</span>
            ${oldPrice ? `<span class="old-price">${fmtPrice(oldPrice)}</span>` : ''}
          </div>

          <button class="btn btn-dark btn-sm w-100 mt-2 add-cart"
                  data-id="${p.id}">
            Add to Cart
          </button>
        </div>
      </div>
    `;
  });

  if ($('#loadMoreBtn')) {
    $('#loadMoreBtn').style.display = state.hasNext ? 'inline-block' : 'none';
  }

  if ($('#shownCount')) $('#shownCount').textContent = state.products.length;
  if ($('#totalCount')) $('#totalCount').textContent = state.products.length;
}

/* ----------------- Cart ----------------- */
async function loadCartFromDB() {
  try {
    const res = await fetch("/api/cart");
    const data = await res.json();
    if (!data.success) return;

    state.cart = data.cart.map(i => ({
      id: i.product_id,
      qty: i.quantity
    }));

    updateBadges();
  } catch (e) {
    // not logged in
  }
}

async function addToCart(id, qty = 1) {
  try {
    const res = await fetch("/api/cart/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: id, qty })
    });

    const data = await res.json();
    if (!data.success) {
      showToast(data.message || "Error", "error");
      return;
    }

    showToast("Added to cart");
    loadCartFromDB();
  } catch {
    showToast("Please login first", "error");
  }
}

/* ----------------- Quick View ----------------- */
const quickModalEl = $('#quickViewModal');
const quickModal = quickModalEl ? new bootstrap.Modal(quickModalEl) : null;

function openQuickView(id) {
  if (!quickModal) return;
  const p = state.products.find(x => x.id == id);
  if (!p) return;

  $('#quickImage').src = p.image || p.image_url || '/static/img/placeholders/product.png';
  $('#quickName').textContent = p.name;
  $('#quickPrice').textContent = fmtPrice(p.price);
  quickModalEl.dataset.prodId = id;
  quickModal.show();
}

$('#quickAddCart')?.addEventListener('click', () => {
  const id = quickModalEl.dataset.prodId;
  addToCart(id, 1);
  quickModal.hide();
});

/* ----------------- Global Clicks ----------------- */
document.body.addEventListener('click', e => {
  if (e.target.closest('.add-cart')) {
    addToCart(e.target.dataset.id, 1);
  }

  if (e.target.closest('.quick-view-btn')) {
    openQuickView(e.target.dataset.id);
  }

  if (e.target.closest('.wishlist-btn')) {
  const btn = e.target.closest('.wishlist-btn');
  toggleWishlist(parseInt(btn.dataset.id), btn);
}

});


/* ----------------- City ----------------- */
function updateCity() {
  if ($('#cityText')) {
    $('#cityText').innerHTML = `Delivering to <strong>${state.currentCity}</strong>`;
  }
}
$$('.city-select').forEach(b =>
  b.addEventListener('click', () => {
    state.currentCity = b.textContent.trim();
    localStorage.setItem(STORAGE.CITY, state.currentCity);
    updateCity();
  })
);

/* ----------------- Cookie ----------------- */
if ($('#cookieBanner') && !localStorage.getItem(STORAGE.COOKIE)) {
  $('#cookieBanner').style.display = 'flex';
}
$('#acceptCookies')?.addEventListener('click', () => {
  localStorage.setItem(STORAGE.COOKIE, 'yes');
  $('#cookieBanner').style.display = 'none';
});

/* ----------------- Load More ----------------- */
$('#loadMoreBtn')?.addEventListener('click', () => {
  fetchProducts(false);
});

/* ----------------- Boot ----------------- */
function boot() {
state.wishlist = safeParse(STORAGE.WISHLIST, []);
  updateCity();
  fetchProducts(true);
  loadCartFromDB();
}

document.addEventListener('DOMContentLoaded', boot);
