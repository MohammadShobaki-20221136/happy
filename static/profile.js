const SENTIMENT_CLASS = {
    positive: "sentiment-positive",
    negative: "sentiment-negative",
    neutral: "sentiment-neutral",
};

document.addEventListener("DOMContentLoaded", async () => {
    await requireAuth();

    const flash = document.getElementById("flash");

    await Promise.all([loadProfile(), loadHistory()]);

    // ---- profile + stats ----

    async function loadProfile() {
        try {
            const data = await apiFetch("/api/profile");
            renderProfile(data);
        } catch (err) {
            showMessage(flash, err.message, "error");
        }
    }
function renderProfile({ user, stats }) {
    document.getElementById("profile-name").textContent = user.name;
    document.getElementById("profile-email").textContent = user.email;
    document.getElementById("profile-created").textContent = user.created_at
        ? new Date(user.created_at).toLocaleDateString()
        : "-";
    document.getElementById("profile-last-login").textContent = user.last_login
        ? new Date(user.last_login).toLocaleString()
        : "-";

    document.getElementById("stat-total").textContent = stats.total_analyses;
    document.getElementById("stat-common").textContent = stats.most_common || "-";
    // REMOVED: document.getElementById("stat-confidence").textContent = stats.avg_confidence;
}

// 2. In renderHistory(): remove the confidence table data cell <td>
function renderHistory(rows) {
    const table = document.getElementById("history-table");
    const body = document.getElementById("history-body");
    const emptyMsg = document.getElementById("empty-msg");
    body.innerHTML = "";

    if (!rows || rows.length === 0) {
        table.style.display = "none";
        emptyMsg.style.display = "";
        return;
    }

    table.style.display = "";
    emptyMsg.style.display = "none";

    rows.forEach((row) => {
        const tr = document.createElement("tr");
        const date = row.created_at ? new Date(row.created_at).toLocaleString() : "";
        const preview = row.input_text.length > 60 ? row.input_text.slice(0, 60) + "..." : row.input_text;
        const sentimentClass = SENTIMENT_CLASS[row.sentiment_label] || "";

        // REMOVED: <td>${confidencePct}%</td> from row string
        tr.innerHTML = `
            <td>${escapeHtml(date)}</td>
            <td>${escapeHtml(preview)}</td>
            <td><span class="sentiment-label ${sentimentClass}">${escapeHtml(row.sentiment_label)}</span></td>
            <td><button class="btn-danger delete-btn" data-id="${row.id}" style="margin-top:0;">Delete</button></td>
        `;
        body.appendChild(tr);
    });

    body.querySelectorAll(".delete-btn").forEach((btn) => {
        btn.addEventListener("click", () => handleDelete(btn.dataset.id));
    });
}

    // ---- history table ----

    async function loadHistory() {
        try {
            const rows = await apiFetch("/api/history");
            renderHistory(rows);
        } catch (err) {
            showMessage(flash, err.message, "error");
        }
    }



    async function handleDelete(id) {
        if (!confirm("Delete this entry?")) return;
        try {
            await apiFetch(`/api/history/${id}`, { method: "DELETE" });
            // deleting changes both the table and the stats (total/avg/most-common)
            await Promise.all([loadHistory(), loadProfile()]);
        } catch (err) {
            showMessage(flash, err.message, "error");
        }
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }
});