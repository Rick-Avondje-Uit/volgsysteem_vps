"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const toggleButtons = document.querySelectorAll(
        "[data-target-id]"
    );

    toggleButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const targetId = button.dataset.targetId;

            if (!targetId) {
                return;
            }

            const target = document.getElementById(targetId);

            if (!target) {
                console.warn(
                    `Doelelement niet gevonden: ${targetId}`
                );
                return;
            }

            const shouldOpen = target.hidden;

            target.hidden = !shouldOpen;

            button.setAttribute(
                "aria-expanded",
                String(shouldOpen)
            );
        });
    });
});