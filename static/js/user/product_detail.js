document.addEventListener("DOMContentLoaded", () => {

  const root = document.getElementById("pdpRoot");
  if (!root) return;

  const qtyInput = document.querySelector(".pdp-qty-input");
  const plusBtn = document.querySelector(".pdp-qty-plus");
  const minusBtn = document.querySelector(".pdp-qty-minus");
  const addBtn = document.querySelector(".add-cart");

  const stock = parseInt(root.dataset.stock, 10) || 0;

  if (!qtyInput || !addBtn) return;

  if (stock <= 0) {
    plusBtn?.setAttribute("disabled", true);
    minusBtn?.setAttribute("disabled", true);
    addBtn.setAttribute("disabled", true);
    qtyInput.value = 0;
  }

  /* USER EXISTING RATING */

  const existingRating = root.dataset.userRating;
  if (existingRating) {

    const stars = document.querySelectorAll(".rating-stars .star");

    stars.forEach(star => {
      if (parseInt(star.dataset.rating) <= parseInt(existingRating)) {
        star.classList.add("selected");
      }
    });

    const input = document.getElementById("rating-input");
    if (input) input.value = existingRating;

  }

});