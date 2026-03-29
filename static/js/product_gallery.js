document.addEventListener("DOMContentLoaded", () => {

  const gallery = document.querySelector(".pdp-gallery");
  const mainImage = document.getElementById("pdpMainImage");
  const stopPoint = document.querySelector(".pdp-description");

  if (!gallery || !mainImage) return;

  // ===============================
  // THUMBNAIL CLICK (EVENT DELEGATION)
  // ===============================
  gallery.addEventListener("click", (e) => {
    const thumb = e.target.closest(".pdp-thumb");
    if (!thumb) return;

    const newSrc = thumb.dataset.img;
    if (!newSrc) return;

    // Update main image
    mainImage.src = newSrc;

    // Active state update
    gallery.querySelectorAll(".pdp-thumb").forEach(t =>
      t.classList.remove("active")
    );
    thumb.classList.add("active");
  });

  // ===============================
  // STICKY GALLERY (DESKTOP ONLY)
  // ===============================
  window.addEventListener("scroll", () => {
    if (!stopPoint) return;

    const rect = stopPoint.getBoundingClientRect();

    if (window.scrollY > 120 && rect.top > 500) {
      gallery.classList.add("pdp-fixed");
    } else {
      gallery.classList.remove("pdp-fixed");
    }
  });

});
