// Shared helpers used by every page.

const NAV_HTML = `
  <nav>
    <a href="/analyze" class="logo">Sentiment Analyzer</a>
    <div class="nav-links">
      <a href="/analyze">Analyze</a>
      <a href="/profile">Profile</a>
      <a href="#" id="logout-link">Logout</a>
    </div>
  </nav>
`;

/**
 * Wraps fetch() with JSON headers + same-origin cookies so the Flask
 * session cookie is sent/received automatically.
 * Returns the parsed JSON body. Throws an Error with .data on failure.
 */
// common.js

// common.js

async function apiFetch(url, options = {}) {
    const token = localStorage.getItem("token");
    
    // 1. Ensure options.headers exists
    const customHeaders = options.headers || {};

    // 2. Attach Authorization header if token exists
    const headers = {
        "Content-Type": "application/json",
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
        ...customHeaders,
    };

    const opts = {
        credentials: "same-origin",
        ...options,
        headers: headers,
    };

    if (opts.body && typeof opts.body !== "string") {
        opts.body = JSON.stringify(opts.body);
    }

    const response = await fetch(url, opts);
    let data = null;
    try {
        data = await response.json();
    } catch (e) {
        data = null;
    }

    if (!response.ok) {
        const err = new Error((data && data.error) || "Request failed");
        err.status = response.status;
        err.data = data;
        throw err;
    }
    return data;
}

function renderNav() {
    const target = document.getElementById("navbar");
    if (!target) return;
    target.innerHTML = NAV_HTML;

    const logoutLink = document.getElementById("logout-link");
    if (logoutLink) {
        logoutLink.addEventListener("click", async (e) => {
            e.preventDefault();
            try {
                await apiFetch("/api/logout", { method: "POST" });
            } finally {
                // Clear token on logout
                localStorage.removeItem("token");
                window.location.href = "/login";
            }
        });
    }
}

/**
 * Call at the top of protected pages. Redirects to /login if the
 * session isn't authenticated, otherwise resolves and renders the nav.
 */
async function requireAuth() {
    try {
        await apiFetch("/api/session");
        renderNav();
    } catch (e) {
        window.location.href = "/login";
        throw e;
    }
}

/** Shows a simple error/success message inside the given element. */
function showMessage(el, message, type = "error") {
    if (!el) return;
    el.textContent = message;
    el.className = `flash flash-${type}`;
    el.style.display = message ? "block" : "none";
}