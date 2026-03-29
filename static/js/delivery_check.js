document.addEventListener("DOMContentLoaded", function () {

  const btn = document.getElementById("checkDeliveryBtn");
  const input = document.getElementById("pincodeInput");
  const result = document.getElementById("deliveryResult");

  if (!btn || !input || !result) return;

  btn.addEventListener("click", function () {

    const pincode = input.value.trim();
    const productId = btn.dataset.productId;

    if (!/^\d{6}$/.test(pincode)) {
      result.textContent = "Please enter a valid 6-digit pincode";
      result.classList.remove("text-success");
      result.classList.add("text-danger");
      return;
    }

    result.textContent = "Checking delivery...";
    result.classList.remove("text-danger");
    result.classList.add("text-muted");

    fetch(`/api/delivery/check?pincode=${pincode}&product_id=${productId}`)
      .then(res => res.json())
      .then(data => {

        if (!data.success) {
          result.textContent = data.message || "Delivery not available";
          result.classList.add("text-danger");
          return;
        }

        result.textContent = `Delivered in ${data.estimated_days} days • ${data.return_policy}`;
        result.classList.remove("text-danger");
        result.classList.add("text-success");
      })
      .catch(() => {
        result.textContent = "Something went wrong. Try again.";
        result.classList.add("text-danger");
      });

  });

});
