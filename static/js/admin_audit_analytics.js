// ===================================
// GLOBAL FIX — BLUR / DPI ISSUE
// ===================================
Chart.defaults.devicePixelRatio = window.devicePixelRatio || 1;

// ===================================
// CSRF TOKEN (DECLARE ONCE ❗)
// ===================================
const csrfToken = document
  .querySelector('meta[name="csrf-token"]')
  ?.getAttribute('content');

// ===================================
// DOM READY (CHARTS ONLY)
// ===================================
document.addEventListener("DOMContentLoaded", () => {

  const trendCtx = document.getElementById("auditTrendChart");
  const severityCtx = document.getElementById("severityChart");
  const topActionsCtx = document.getElementById("topActionsChart");
  const actorTrendCtx = document.getElementById("actorTrendChart");

  if (!trendCtx || !severityCtx) return;

  loadAnalytics(7);
  loadTopActions();
  loadActorTrend(7);

  const rangeSelect = document.getElementById("daysRange");
  if (rangeSelect) {
    rangeSelect.addEventListener("change", () => {
      const days = rangeSelect.value;
      loadAnalytics(days);
      loadActorTrend(days);
    });
  }

  function loadAnalytics(days) {
    fetch(`/admin/audit-logs/trends?days=${days}`)
      .then(r => r.json())
      .then(d => {
        renderTrendChart(d.daily);
        renderSeverityChart(d.severity);
      });
  }

  let trendChart;
  function renderTrendChart(daily) {
    if (trendChart) trendChart.destroy();
    trendChart = new Chart(trendCtx, {
      type: "line",
      data: {
        labels: daily.map(d => d.date),
        datasets: [{
          data: daily.map(d => d.count),
          label: "Audit Actions",
          borderColor: "#1d4ed8",
          backgroundColor: "rgba(29,78,216,.2)",
          fill: true,
          tension: .35
        }]
      }
    });
  }

  let severityChart;
  function renderSeverityChart(severity) {
    if (severityChart) severityChart.destroy();
    severityChart = new Chart(severityCtx, {
      type: "doughnut",
      data: {
        labels: Object.keys(severity),
        datasets: [{
          data: Object.values(severity),
          backgroundColor: ["#dc2626","#f59e0b","#16a34a"]
        }]
      }
    });
  }

  function loadTopActions() {
    if (!topActionsCtx) return;
    fetch("/admin/audit-analytics/top-actions")
      .then(r => r.json())
      .then(d => {
        new Chart(topActionsCtx, {
          type: "bar",
          data: {
            labels: d.labels,
            datasets: [{ data: d.counts }]
          },
          options: { indexAxis: "y" }
        });
      });
  }

  function loadActorTrend(days) {
    if (!actorTrendCtx) return;
    fetch(`/admin/audit-analytics/actor-trend?days=${days}`)
      .then(r => r.json())
      .then(d => {
        new Chart(actorTrendCtx, {
          type: "line",
          data: {
            labels: d.labels,
            datasets: [
              { label: "Admin", data: d.admin },
              { label: "System", data: d.system }
            ]
          }
        });
      });
  }
});

// ===================================
// INSIGHT GOVERNANCE (GLOBAL FUNCTIONS ❗)
// ===================================

function markInsightSeen(id) {
  fetch(`/admin/audit-insights/${id}/seen`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken
    }
  })
  .then(res => {
    if (!res.ok) throw new Error();
    location.reload();
  })
  .catch(() => alert("Failed to mark insight as seen"));
}

function archiveInsight(id) {
  if (!confirm("Archive this insight?")) return;

  fetch(`/admin/audit-insights/${id}/archive`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken
    }
  })
  .then(res => {
    if (!res.ok) throw new Error();
    location.reload();
  })
  .catch(() => alert("Super Admin permission required"));
}
