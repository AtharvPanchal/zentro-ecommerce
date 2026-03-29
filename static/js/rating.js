document.addEventListener("DOMContentLoaded", () => {

  const stars = document.querySelectorAll(".rating-stars .star");
  const ratingInput = document.getElementById("rating-input");
  const ratingForm = ratingInput ? ratingInput.closest("form") : null;


  if (!stars.length || !ratingInput || !ratingForm) return;

  // ---------- STAR CLICK ----------
  stars.forEach((star) => {
    star.addEventListener("click", () => {
      const rating = parseInt(star.dataset.rating);

      ratingInput.value = rating;

      stars.forEach(s => s.classList.remove("selected"));

      stars.forEach(s => {
        if (parseInt(s.dataset.rating) <= rating) {
          s.classList.add("selected");
        }
      });
    });
  });

  // ---------- SUBMIT GUARD ----------
  ratingForm.addEventListener("submit", (e) => {
    if (!ratingInput.value) {
      e.preventDefault();
      showToast?.("Please select a rating before submitting", "warning");
      stars[0]?.scrollIntoView({ behavior: "smooth", block: "center" });

      return;
    }
  });

});
