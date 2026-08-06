
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("register-form");
    const flash = document.getElementById("flash");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        showMessage(flash, "");

        const name = document.getElementById("name").value.trim();
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        try {
            // 1. Capture the API response object
            const data = await apiFetch("/api/register", {
                method: "POST",
                body: { name, email, password },
            });

            // 2. Save the token to local storage
            if (data && data.token) {
                localStorage.setItem("token", data.token);
            }

            // 3. Navigate to the protected page
            window.location.href = "/analyze";
        } catch (err) {
            showMessage(flash, err.message, "error");
        }
    });
});

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showMessage(flash, "");

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    try {
        const data = await apiFetch("/api/register", {
            method: "POST",
            body: { name, email, password },
        });

        // Store token immediately upon registration
        if (data && data.token) {
            localStorage.setItem("token", data.token);
        }

        window.location.href = "/analyze";
    } catch (err) {
        showMessage(flash, err.message, "error");
    }
});