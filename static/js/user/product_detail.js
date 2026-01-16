// Quick interactions for product detail (qty, add to cart, wishlist)
const { $, $$, fmtPrice, showToast } = window.zentro || {};

document.addEventListener('click', (e)=>{
  if(e.target.closest('.qty-plus')){
    const container = e.target.closest('.qty-group') || document;
    const input = (container).querySelector('.qty-input');
    if(input) input.value = Math.min(999, Number(input.value||1)+1);
  }
  if(e.target.closest('.qty-minus')){
    const container = e.target.closest('.qty-group') || document;
    const input = (container).querySelector('.qty-input');
    if(input) input.value = Math.max(1, Number(input.value||1)-1);
  }
  if(e.target.closest('#detailAddCart')){
    const id = e.target.closest('#detailAddCart').dataset.id;
    const qty = Number($('#detailQty').value || 1);
    // use cart.js addToCart function if available
    if(window.zCart && window.zCart.addToCart) {
      window.zCart.addToCart(id, qty);
    } else {
      showToast('Added to cart (demo)', 'success');
    }
  }
  if(e.target.closest('#detailWishlist')){
    const id = e.target.closest('#detailWishlist').dataset.id;
    if(window.zCart && window.zCart.toggleWishlist) window.zCart.toggleWishlist(id);
    else showToast('Wishlist toggled (demo)');
  }
});

// ===============================
// Product Detail Quantity Control
// ===============================
document.addEventListener('click', (e) => {

  if (e.target.classList.contains('qty-plus')) {
    const input = document.querySelector('#detailQty');
    if (input) input.value = Math.min(99, Number(input.value) + 1);
  }

  if (e.target.classList.contains('qty-minus')) {
    const input = document.querySelector('#detailQty');
    if (input) input.value = Math.max(1, Number(input.value) - 1);
  }

});

//---------------------------------------
// PRODUCT STAR HOVER + SELECT EFFECT
//---------------------------------------
document.querySelectorAll('.user-stars label').forEach((label, idx, all) => {
  label.addEventListener('mouseenter', () => {
    all.forEach((l, i) => {
      l.querySelector('.star')
       .classList.toggle('filled', i <= idx);
    });
  });

  label.addEventListener('mouseleave', () => {
    all.forEach(l => {
      l.querySelector('.star').classList.remove('filled');
    });
  });

  label.addEventListener('click', () => {
    all.forEach((l, i) => {
      l.querySelector('.star')
       .classList.toggle('filled', i <= idx);
    });
  });
});
