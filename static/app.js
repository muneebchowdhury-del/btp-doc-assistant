document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("question-form");
    const textarea = document.getElementById("question");
    const submitButton = document.getElementById("submit-button");
    const submitLabel = document.getElementById("submit-label");

    document.querySelectorAll(".example").forEach((button) => {
        button.addEventListener("click", () => {
            textarea.value = button.dataset.prompt || "";
            textarea.focus();
        });
    });

    textarea?.addEventListener("keydown", (event) => {
        if (
            event.ctrlKey &&
            event.key === "Enter"
        ) {
            event.preventDefault();
            form.requestSubmit();
        }
    });

    form?.addEventListener("submit", () => {
        form.classList.add("is-loading");

        submitButton.disabled = true;

        submitLabel.textContent =
            "Working…";
    });
});
