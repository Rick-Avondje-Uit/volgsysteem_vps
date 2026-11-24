"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById(
        "methodiekFilterForm"
    );

    if (!form) {
        return;
    }

    const autoSubmitFields = [
        "id_begeleider_keuze",
        "id_toon_afgeronde_trajecten",
        "id_toon_gepauzeerde_trajecten",
    ];

    autoSubmitFields.forEach((fieldId) => {
        const field = document.getElementById(fieldId);

        field?.addEventListener("change", () => {
            form.requestSubmit();
        });
    });
});