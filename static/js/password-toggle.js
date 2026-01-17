document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".toggle-password").forEach(button => {
        button.addEventListener("click", () => {
            const wrapper = button.closest(".password-field");
            const input = wrapper.querySelector("input");
            const img = button.querySelector("img");

            if (!input || !img) return;

            const isHidden = input.type === "password";

            input.type = isHidden ? "text" : "password";
            img.src = isHidden
                ? "/static/icons/hide.png"
                : "/static/icons/show.png";
            img.alt = isHidden ? "Hide password" : "Show password";
        });
    });
});

// Django → HTML → Browser → JavaScript → User interaction