new Chart(document.getElementById('salesChart'), {
  type: 'line',
  data: {
    labels: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
    datasets: [
      {
        label: 'Revenue',
        data: [1200, 1900, 1500, 2200, 3000, 2800, 3500],
        borderColor: '#22c55e'
      },
      {
        label: 'Orders',
        data: [30, 50, 45, 70, 90, 85, 110],
        borderColor: '#3b82f6'
      }
    ]
  }
});
