/**
 * Dashboard: Chart.js charts and Load data button.
 * Single main color + lighter shades; no random bright colors.
 */
(function () {
    var COLORS = {
        primary: "#3b82f6",
        primaryLight: "#60a5fa",
        primaryLighter: "#93c5fd",
        neutral: "#94a3b8",
        danger: "#ef4444",
    };
    var PIE_PALETTE = [COLORS.primary, COLORS.primaryLight, COLORS.primaryLighter];
    var GRID_COLOR = "rgba(148,163,184,0.2)";

    function chartOptions(opts) {
        var base = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: COLORS.neutral } } },
        };
        if (opts && opts.scales) base.scales = opts.scales;
        return base;
    }

    function scaleOptions(maxRotation) {
        return {
            y: {
                beginAtZero: true,
                grid: { color: GRID_COLOR },
                ticks: { color: COLORS.neutral },
            },
            x: {
                grid: { color: GRID_COLOR },
                ticks: { color: COLORS.neutral, maxRotation: maxRotation || 0 },
            },
        };
    }

    function costTrendChart() {
        var data = window.DASHBOARD_DATA.costTrend;
        if (!data || !data.labels || !data.labels.length) return;
        var ctx = document.getElementById("chart-cost-trend");
        if (!ctx) return;
        new Chart(ctx.getContext("2d"), {
            type: "line",
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: "Events",
                        data: data.event_counts,
                        borderColor: COLORS.primary,
                        backgroundColor: COLORS.primary + "20",
                        fill: true,
                        tension: 0.2,
                    },
                ],
            },
            options: chartOptions({ scales: scaleOptions(45) }),
        });
    }

    function hourlyChart() {
        var data = window.DASHBOARD_DATA.peakHours;
        if (!data || !data.values) return;
        var ctx = document.getElementById("chart-hourly");
        if (!ctx) return;
        var labels = data.labels || data.values.map(function (_, i) { return i + ":00"; });
        new Chart(ctx.getContext("2d"), {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{ label: "Events", data: data.values, backgroundColor: COLORS.primaryLight }],
            },
            options: chartOptions({ scales: scaleOptions() }),
        });
    }

    function toolUsageChart() {
        var data = window.DASHBOARD_DATA.toolUsage;
        if (!data || !data.labels || !data.labels.length) return;
        var ctx = document.getElementById("chart-tool-usage");
        if (!ctx) return;
        var colors = data.labels.map(function (_, i) { return PIE_PALETTE[i % PIE_PALETTE.length]; });
        new Chart(ctx.getContext("2d"), {
            type: "bar",
            data: {
                labels: data.labels,
                datasets: [{ label: "Events", data: data.values, backgroundColor: colors }],
            },
            options: chartOptions({ scales: scaleOptions() }),
        });
    }

    function modelUsageChart() {
        var data = window.DASHBOARD_DATA.modelUsage;
        if (!data || !data.labels || !data.labels.length) return;
        var ctx = document.getElementById("chart-model-usage");
        if (!ctx) return;
        var colors = data.labels.map(function (_, i) { return PIE_PALETTE[i % PIE_PALETTE.length]; });
        new Chart(ctx.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: data.labels,
                datasets: [{ data: data.values, backgroundColor: colors }],
            },
            options: chartOptions(),
        });
    }

    function rolePracticeChart() {
        var byRole = window.DASHBOARD_DATA.usageByRole || [];
        var byDept = window.DASHBOARD_DATA.usageByDepartment || [];
        var labels = [];
        var values = [];
        byRole.forEach(function (r) {
            labels.push("Role: " + r.role);
            values.push(r.event_count);
        });
        byDept.forEach(function (d) {
            labels.push("Dept: " + d.department);
            values.push(d.event_count);
        });
        if (!labels.length) return;
        var ctx = document.getElementById("chart-role-practice");
        if (!ctx) return;
        new Chart(ctx.getContext("2d"), {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{ label: "Events", data: values, backgroundColor: COLORS.primaryLight }],
            },
            options: chartOptions({ scales: scaleOptions(45) }),
        });
    }

    function initLoadButton() {
        var btn = document.getElementById("load-data");
        var status = document.getElementById("load-status");
        if (!btn || !status) return;
        btn.addEventListener("click", function () {
            status.textContent = "Loading…";
            status.classList.remove("success");
            fetch("/api/analytics/load-data", { method: "POST" })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    status.textContent = "Loaded: " + (data.telemetry_loaded || 0) + " events, " + (data.employees_loaded || 0) + " employees.";
                    status.classList.add("success");
                    setTimeout(function () { window.location.reload(); }, 800);
                })
                .catch(function () {
                    status.textContent = "Load failed.";
                });
        });
    }

    function formatNumber(n) {
        if (typeof n !== "number" || isNaN(n)) return "0";
        return n >= 1000 ? n.toLocaleString() : String(n);
    }

    function updateLiveSummary(data) {
        var eventsEl = document.getElementById("kpi-events");
        var costEl = document.getElementById("kpi-cost");
        var tokensEl = document.getElementById("kpi-tokens");
        var usersEl = document.getElementById("kpi-users");
        if (eventsEl) eventsEl.textContent = formatNumber(data.total_events || 0);
        if (costEl) costEl.textContent = "$" + (typeof data.estimated_cost_usd === "number" ? data.estimated_cost_usd.toFixed(2) : "0.00");
        if (tokensEl) tokensEl.textContent = formatNumber(data.total_tokens || 0);
        if (usersEl) usersEl.textContent = formatNumber(data.active_users || 0);
        var list = document.querySelector(".insights-list");
        if (list && Array.isArray(data.bullets)) {
            list.innerHTML = "";
            if (data.bullets.length) {
                data.bullets.forEach(function (bullet) {
                    var li = document.createElement("li");
                    li.textContent = bullet;
                    list.appendChild(li);
                });
            } else {
                var fallback = document.createElement("li");
                fallback.innerHTML = "Run data ingestion (<code>python -m scripts.ingest_data</code>) and refresh the page to see insights.";
                list.appendChild(fallback);
            }
        }
        var updatedEl = document.getElementById("live-updated");
        if (updatedEl) {
            var now = new Date();
            var t = now.getHours().toString().padStart(2, "0") + ":" + now.getMinutes().toString().padStart(2, "0") + ":" + now.getSeconds().toString().padStart(2, "0");
            updatedEl.textContent = "Last updated " + t;
        }
    }

    function initLiveRefresh() {
        var data = window.DASHBOARD_DATA;
        if (!data || typeof data.days !== "number") return;
        var days = data.days;
        var LIVE_INTERVAL_MS = 30000;

        function poll() {
            fetch("/api/live-summary?days=" + days)
                .then(function (r) { return r.json(); })
                .then(updateLiveSummary)
                .catch(function () {});
        }

        setTimeout(function () {
            poll();
            setInterval(poll, LIVE_INTERVAL_MS);
        }, LIVE_INTERVAL_MS);
    }

    if (typeof Chart !== "undefined") {
        costTrendChart();
        hourlyChart();
        toolUsageChart();
        modelUsageChart();
        rolePracticeChart();
    }
    initLoadButton();
    initLiveRefresh();
})();
