"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("datePickerBtn");
    const dialog = document.getElementById("datePickerDialog");
    const form = document.getElementById("datePickerForm");
    const startDate = document.getElementById("startDate");
    const endDate = document.getElementById("endDate");
    const closeButton = document.getElementById("datePickerClose");
    const cancelButton = document.getElementById("datePickerCancel");

    if (
        !button ||
        !dialog ||
        !form ||
        !startDate ||
        !endDate
    ) {
        return;
    }

    function closeDialog() {
        dialog.close();
    }

    function parseDutchDate(value) {
        const match = value.match(
            /^(\d{2})-(\d{2})-(\d{4})$/
        );

        if (!match) {
            return null;
        }

        const day = Number(match[1]);
        const month = Number(match[2]);
        const year = Number(match[3]);

        const date = new Date(
            year,
            month - 1,
            day
        );

        if (
            date.getFullYear() !== year ||
            date.getMonth() !== month - 1 ||
            date.getDate() !== day
        ) {
            return null;
        }

        return date;
    }

    function clearDateErrors() {
        startDate.setCustomValidity("");
        endDate.setCustomValidity("");
    }

    button.addEventListener("click", () => {
        clearDateErrors();
        dialog.showModal();
    });

    closeButton?.addEventListener(
        "click",
        closeDialog
    );

    cancelButton?.addEventListener(
        "click",
        closeDialog
    );

    startDate.addEventListener(
        "input",
        clearDateErrors
    );

    endDate.addEventListener(
        "input",
        clearDateErrors
    );

    form.addEventListener("submit", (event) => {
        event.preventDefault();

        clearDateErrors();

        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const parsedStartDate = parseDutchDate(
            startDate.value.trim()
        );

        if (!parsedStartDate) {
            startDate.setCustomValidity(
                "Voer een geldige startdatum in als dd-mm-jjjj."
            );

            startDate.reportValidity();
            return;
        }

        const parsedEndDate = parseDutchDate(
            endDate.value.trim()
        );

        if (!parsedEndDate) {
            endDate.setCustomValidity(
                "Voer een geldige einddatum in als dd-mm-jjjj."
            );

            endDate.reportValidity();
            return;
        }

        if (parsedEndDate < parsedStartDate) {
            endDate.setCustomValidity(
                "De einddatum mag niet vóór de startdatum liggen."
            );

            endDate.reportValidity();
            return;
        }

        const targetUrl = form.dataset.actionUrl;

        if (!targetUrl) {
            console.error(
                "Geen URL gevonden voor het toevoegen van activiteiten."
            );
            return;
        }

        const params = new URLSearchParams({
            start_date: startDate.value.trim(),
            end_date: endDate.value.trim(),
        });

        window.location.href =
            `${targetUrl}?${params.toString()}`;
    });

    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) {
            closeDialog();
        }
    });
});