"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const autoSubmitFields = [
        "id_actief",
        "id_in_methodiek",
        "id_is_uitgestroomd",
    ];

    autoSubmitFields.forEach((id) => {
        const field = document.getElementById(id);

        field?.addEventListener("change", () => {
            field.form?.requestSubmit();
        });
    });

    const locationInput = document.getElementById(
        "woonplaats_zoek"
    );

    if (!locationInput) {
        return;
    }

    let timeout = null;

    locationInput.addEventListener("input", () => {
        clearTimeout(timeout);

        timeout = setTimeout(() => {
            locationInput.form?.requestSubmit();
        }, 500);
    });
});