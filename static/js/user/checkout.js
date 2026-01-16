// Checkout flow placeholder. Integrate Razorpay or other provider here.
const { $, showToast } = window.zentro || {};
if($('#payBtn')){
  $('#payBtn').addEventListener('click', ()=>{
    showToast('Initiating payment flow (demo)');
    // Example placeholder flow: on success -> redirect to order success
    setTimeout(()=> {
      window.location.href = '/order-success';
    }, 900);
  });
}
