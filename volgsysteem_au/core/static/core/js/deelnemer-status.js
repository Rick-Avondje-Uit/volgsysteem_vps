"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(
        "form[data-status-url]"
    );

    const refreshButton = document.getElementById(
        "refreshStatusButton"
    );

    const dateField = document.getElementById(
        "id_date_field"
    );

    if (!form) {
        return;
    }

    const statusUrl = form.dataset.statusUrl;

    if (!statusUrl) {
        console.error("De URL voor de deelnemerstatus ontbreekt");
        return;
    }

    refreshButton?.addEventListener("click", () => {
        const url = new URL(
            window.location.href
        );

        url.searchParams.set("ververs", "true");

        window.location.href = url.toString();
    });

    dateField?.addEventListener("change", () => {
        const url = new URL(statusUrl, window.location.origin);
        url.searchParams.set("date_field", dateField.value);
        window.location.href = url.toString();
    });
});