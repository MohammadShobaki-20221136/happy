// login.js
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("login-form");
    const flash = document.getElementById("flash");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        showMessage(flash, "");

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        try {
            // MUST assign to a variable to get the token
            const data = await apiFetch("/api/login", {
                method: "POST",
                body: { email, password },
            });
            
            // MUST save the token to localStorage
            if (data && data.token) {
                localStorage.setItem("token", data.token);
            }
            
            window.location.href = "/analyze";
        } catch (err) {
            showMessage(flash, err.message, "error");
        }
    });
});

// login.js
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showMessage(flash, "");

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    try {
        const data = await apiFetch("/api/login", {
            method: "POST",
            body: { email, password },
        });

        // Store the returned JWT token
        if (data.token) {
            localStorage.setItem("token", data.token);
        }

        window.location.href = "/analyze";
    } catch (err) {
        showMessage(flash, err.message, "error");
    }
});