document.addEventListener("DOMContentLoaded", async () => {
    const response = await fetch("/api/dashboard_data");
    const sessions = await response.json();

    const tbody = document.getElementById("sessions-tbody");
    const emptyState = document.getElementById("empty-state");
    const table = document.getElementById("sessions-table");

    if (!sessions.length) {
        table.style.display = "none";
        emptyState.style.display = "block";
        return;
    }

    sessions.forEach((s) => {
        const row = document.createElement("tr");
        const date = new Date(s.created_at).toLocaleDateString();
        row.innerHTML = `
            <td>#${s.id}</td>
            <td>${s.role}</td>
            <td>${date}</td>
            <td>${s.question_count}</td>
            <td>${s.avg_score ? s.avg_score.toFixed(1) : "--"}</td>
        `;
        tbody.appendChild(row);
    });

    // Chart expects chronological order (oldest first)
    const chronological = [...sessions].reverse();
    const labels = chronological.map((s) => `#${s.id}`);
    const scores = chronological.map((s) => s.avg_score || 0);

    const ctx = document.getElementById("trend-chart").getContext("2d");
    new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Average score per session",
                data: scores,
                borderColor: "#E8A33D",
                backgroundColor: "rgba(232, 163, 61, 0.12)",
                tension: 0.35,
                fill: true,
                pointBackgroundColor: "#E8A33D",
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: "#F1ECE1", font: { family: "Inter" } } },
            },
            scales: {
                x: { ticks: { color: "#A8A398" }, grid: { color: "rgba(241,236,225,0.08)" } },
                y: { ticks: { color: "#A8A398" }, grid: { color: "rgba(241,236,225,0.08)" }, min: 0, max: 100 },
            },
        },
    });
});
