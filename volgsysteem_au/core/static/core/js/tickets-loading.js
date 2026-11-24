"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const statusElement = document.getElementById(
        "report-status"
    );

    if (!statusElement) {
        return;
    }

    const statusUrl = statusElement.dataset.statusUrl;
    const continueUrl = statusElement.dataset.continueUrl;

    if (!statusUrl || !continueUrl) {
        console.error(
            "De status-URL of vervolg-URL ontbreekt."
        );
        return;
    }

    const pollInterval = 2000;

    async function checkReportStatus() {
        try {
            const response = await fetch(
                statusUrl,
                {
                    method: "GET",
                    headers: {
                        "Accept": "application/json",
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    `HTTP-fout ${response.status}`
                );
            }

            const data = await response.json();

            if (data.finished) {
                showContinueLink();
                return;
            }

            statusElement.textContent =
                "Tickets aan het laden, een ogenblik geduld.";

            scheduleNextCheck();
        } catch (error) {
            console.error(
                "Controleren van ticketstatus mislukt:",
                error
            );

            statusElement.textContent =
                "Tickets worden nog geladen. Nieuwe poging volgt automatisch.";

            scheduleNextCheck();
        }
    }

    function scheduleNextCheck() {
        window.setTimeout(
            checkReportStatus,
            pollInterval
        );
    }

    function showContinueLink() {
        statusElement.replaceChildren();

        const link = document.createElement("a");

        link.href = continueUrl;
        link.className = "btn btn-primary";
        link.textContent = "Ga verder";

        statusElement.appendChild(link);
    }

    checkReportStatus();
});