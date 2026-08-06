const SENTIMENT_CLASS = {
    positive: "sentiment-positive",
    negative: "sentiment-negative",
    neutral: "sentiment-neutral",
};

document.addEventListener("DOMContentLoaded", async () => {
    await requireAuth();

    const form = document.getElementById("analyze-form");
    const textarea = document.getElementById("input_text");
    const charCount = document.getElementById("char-count");
    const flash = document.getElementById("flash");
    const analyzeBtn = document.getElementById("analyze-btn");

    textarea.addEventListener("input", () => {
        charCount.textContent = textarea.value.length;
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        showMessage(flash, "");

        const input_text = textarea.value.trim();
        if (!input_text) {
            showMessage(flash, "Please enter some text to analyze.", "error");
            return;
        }

        analyzeBtn.disabled = true;
        analyzeBtn.textContent = "Analyzing...";

        try {
            const result = await apiFetch("/api/analyze", {
                method: "POST",
                body: { input_text },
            });
            renderResult(result);
        } catch (err) {
            showMessage(flash, err.message, "error");
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = "Analyze";
        }
    });

function renderResult(result) {
    const resultBox = document.getElementById("result-box");
    const label = document.getElementById("sentiment-label");

    label.textContent = result.sentiment_label;
    label.className = "sentiment-label " + (SENTIMENT_CLASS[result.sentiment_label] || "");

    // REMOVED: confidence-pct and confidence-bar-fill updates

    const tbody = document.getElementById("matched-words-body");
    const table = document.getElementById("matched-words-table");
    const noMatchesMsg = document.getElementById("no-matches-msg");
    tbody.innerHTML = "";

    if (result.matched_words && result.matched_words.length > 0) {
        table.style.display = "";
        noMatchesMsg.style.display = "none";
        result.matched_words.forEach((m) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${escapeHtml(m.word)}</td><td>${escapeHtml(m.category)}</td><td>${m.contribution}</td>`;
            tbody.appendChild(tr);
        });
    } else {
        table.style.display = "none";
        noMatchesMsg.style.display = "";
    }

    resultBox.style.display = "";
    resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
 }
    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }
});