/**
 * Dashboard: Chart.js charts and Load data button.
 * Uses DASHBOARD_DATA from server (cost_trend, peak_hours, tool_usage, model_usage, usage_by_role, usage_by_department).
 */
(function () {
    var COLORS = [
        "#58a6ff",
        "#3fb950",
        "#d29922",
        "#f85149",
        "#a371f7",
        "#79c0ff",
        "#7ee787",
        "#ffa657",
    ];

    function chartOptions(opts) {
        var base = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: "#8b949e" } } },
        };
        if (opts && opts.scales) base.scales = opts.scales;
        return base;
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
                        borderColor: COLORS[0],
                        backgroundColor: COLORS[0] + "30",
                        fill: true,
                        tension: 0.2,
                    },
                ],
            },
            options: chartOptions({ scales: { y: { beginAtZero: true, ticks: { color: "#8b949e" } }, x: { ticks: { color: "#8b949e", maxRotation: 45 } } } }),
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
                datasets: [{ label: "Events", data: data.values, backgroundColor: COLORS[1] + "99" }],
            },
            options: chartOptions({ scales: { y: { beginAtZero: true, ticks: { color: "#8b949e" } }, x: { ticks: { color: "#8b949e" } } } }),
        });
    }

    function toolUsageChart() {
        var data = window.DASHBOARD_DATA.toolUsage;
        if (!data || !data.labels || !data.labels.length) return;
        var ctx = document.getElementById("chart-tool-usage");
        if (!ctx) return;
        new Chart(ctx.getContext("2d"), {
            type: "bar",
            data: {
                labels: data.labels,
                datasets: [{ label: "Events", data: data.values, backgroundColor: COLORS.slice(0, data.labels.length) }],
            },
            options: chartOptions({ scales: { y: { beginAtZero: true, ticks: { color: "#8b949e" } }, x: { ticks: { color: "#8b949e" } } } }),
        });
    }

    function modelUsageChart() {
        var data = window.DASHBOARD_DATA.modelUsage;
        if (!data || !data.labels || !data.labels.length) return;
        var ctx = document.getElementById("chart-model-usage");
        if (!ctx) return;
        new Chart(ctx.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: data.labels,
                datasets: [{ data: data.values, backgroundColor: COLORS.slice(0, data.labels.length) }],
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
                datasets: [{ label: "Events", data: values, backgroundColor: COLORS[2] + "99" }],
            },
            options: chartOptions({ scales: { y: { beginAtZero: true, ticks: { color: "#8b949e" } }, x: { ticks: { color: "#8b949e", maxRotation: 45 } } } }),
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

    if (typeof Chart !== "undefined") {
        costTrendChart();
        hourlyChart();
        toolUsageChart();
        modelUsageChart();
        rolePracticeChart();
    }
    initLoadButton();
})();
