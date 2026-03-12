/**
 * Dashboard: wire Load data button and render Chart.js charts from DASHBOARD_DATA.
 */
(function () {
    const COLORS = [
        "#58a6ff",
        "#3fb950",
        "#d29922",
        "#f85149",
        "#a371f7",
        "#79c0ff",
        "#7ee787",
        "#ffa657",
    ];

    function byTypeChart() {
        const data = window.DASHBOARD_DATA.byType || {};
        const ctx = document.getElementById("chart-by-type");
        if (!ctx) return;
        const labels = Object.keys(data);
        const values = Object.values(data);
        new Chart(ctx.getContext("2d"), {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Events",
                        data: values,
                        backgroundColor: COLORS.slice(0, labels.length),
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true },
                },
            },
        });
    }

    function overTimeChart() {
        const buckets = window.DASHBOARD_DATA.overTime || [];
        const ctx = document.getElementById("chart-over-time");
        if (!ctx) return;
        const labels = buckets.map(function (b) {
            return b.date;
        });
        const values = buckets.map(function (b) {
            return b.count;
        });
        new Chart(ctx.getContext("2d"), {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Events",
                        data: values,
                        borderColor: COLORS[0],
                        backgroundColor: COLORS[0] + "20",
                        fill: true,
                        tension: 0.2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true },
                },
            },
        });
    }

    function byDepartmentChart() {
        const data = window.DASHBOARD_DATA.byDepartment || [];
        const ctx = document.getElementById("chart-by-department");
        if (!ctx) return;
        const labels = data.map(function (d) {
            return d.department;
        });
        const values = data.map(function (d) {
            return d.count;
        });
        new Chart(ctx.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [
                    {
                        data: values,
                        backgroundColor: COLORS.slice(0, labels.length),
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
            },
        });
    }

    function initLoadButton() {
        const btn = document.getElementById("load-data");
        const status = document.getElementById("load-status");
        if (!btn || !status) return;
        btn.addEventListener("click", function () {
            status.textContent = "Loading…";
            status.classList.remove("success");
            fetch("/api/analytics/load-data", { method: "POST" })
                .then(function (r) {
                    return r.json();
                })
                .then(function (data) {
                    status.textContent =
                        "Loaded: " +
                        (data.telemetry_loaded || 0) +
                        " events, " +
                        (data.employees_loaded || 0) +
                        " employees.";
                    status.classList.add("success");
                    setTimeout(function () {
                        window.location.reload();
                    }, 800);
                })
                .catch(function () {
                    status.textContent = "Load failed.";
                });
        });
    }

    if (typeof Chart !== "undefined") {
        byTypeChart();
        overTimeChart();
        byDepartmentChart();
    }
    initLoadButton();
})();
