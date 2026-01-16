async function loadAuditTrends(days = 7) {
    const res = await fetch(`/admin/audit-logs/trends?days=${days}`);
    const data = await res.json();

    // Line chart (Daily activity)
    const labels = data.daily.map(d => d.date);
    const values = data.daily.map(d => d.count);

    new Chart(document.getElementById("auditTrendChart"), {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Audit Actions",
                data: values,
                borderWidth: 2,
                tension: 0.4
            }]
        }
    });

    // Severity pie
    new Chart(document.getElementById("severityChart"), {
        type: "doughnut",
        data: {
            labels: Object.keys(data.severity),
            datasets: [{
                data: Object.values(data.severity)
            }]
        }
    });

    // Actor pie
    new Chart(document.getElementById("actorChart"), {
        type: "pie",
        data: {
            labels: Object.keys(data.actors),
            datasets: [{
                data: Object.values(data.actors)
            }]
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    loadAuditTrends(7);
});
