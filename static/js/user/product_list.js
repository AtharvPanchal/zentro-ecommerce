// static/js/product_list.js
let page = 1;
let perPage = 8;

async function loadProducts(reset=false){
  if(reset){
    page = 1;
    document.getElementById('productsGrid').innerHTML = '';
  }

  const sort = document.getElementById('sortSelect').value;
  const res = await fetch(`/api/products?page=${page}&limit=${perPage}&sort=${sort}`);
  const data = await res.json();

  renderProducts(data.products);

  document.getElementById('loadMoreBtn').style.display =
    data.has_more ? 'inline-block' : 'none';

  page++;
}

function renderProducts(list){
  const grid = document.getElementById('productsGrid');

  list.forEach(p=>{
    const col = document.createElement('div');
    col.className = 'col-12 col-md-6 col-lg-3';

    col.innerHTML = `
      <div class="product-card">
        <img src="${p.image_url}" class="img-fluid mb-2">
        <h6>${p.name}</h6>
        <div class="text-muted small">${p.category}</div>
        <strong>₹${p.price}</strong>
        <div class="d-grid gap-2 mt-2">
          <a href="/product/${p.id}" class="btn btn-sm btn-outline-secondary">View</a>
        </div>
      </div>
    `;
    grid.appendChild(col);
  });
}

document.getElementById('loadMoreBtn').addEventListener('click', ()=>loadProducts());
document.getElementById('sortSelect').addEventListener('change', ()=>loadProducts(true));

document.addEventListener('DOMContentLoaded', loadProducts);
