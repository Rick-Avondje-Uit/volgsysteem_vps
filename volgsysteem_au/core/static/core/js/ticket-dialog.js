"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const openButton = document.getElementById(
        "ticketDatePickerBtn"
    );

    const dialog = document.getElementById(
        "ticketDatePickerDialog"
    );

    const form = document.getElementById(
        "ticketDatePickerForm"
    );

    const startDate = document.getElementById(
        "ticketStartDate"
    );

    const endDate = document.getElementById(
        "ticketEndDate"
    );

    const closeButton = document.getElementById(
        "ticketDatePickerClose"
    );

    const cancelButton = document.getElementById(
        "ticketDatePickerCancel"
    );

    if (
        !openButton ||
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

    /**
     * Zet een Nederlandse datum (dd-mm-jjjj)
     * om naar een JavaScript Date.
     *
     * Geeft null terug als het formaat of de datum ongeldig is.
     */
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

    openButton.addEventListener("click", () => {
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

        const startDateValue = startDate.value.trim();
        const endDateValue = endDate.value.trim();

        const parsedStartDate = parseDutchDate(
            startDateValue
        );

        if (!parsedStartDate) {
            startDate.setCustomValidity(
                "Voer een geldige startdatum in als dd-mm-jjjj."
            );

            startDate.reportValidity();
            return;
        }

        const parsedEndDate = parseDutchDate(
            endDateValue
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
                "Geen URL gevonden voor het bijwerken van tickets."
            );
            return;
        }

        const params = new URLSearchParams({
            start_date: startDateValue,
            end_date: endDateValue,
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