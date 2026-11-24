"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const copyButton = document.getElementById("kopieer-emailadressen");
    const result = document.getElementById("kopieer-resultaat");

    if (!copyButton || !result) {
        return;
    }

    function getEmailAddresses() {
        const elements = document.querySelectorAll(".deelnemer-email");

        return [
            ...new Set(
                Array.from(elements)
                    .map((element) => element.dataset.email?.trim())
                    .filter(Boolean)
            ),
        ];
    }

    function showResult(message) {
        result.textContent = message;

        window.setTimeout(() => {
            result.textContent = "";
        }, 3000);
    }

    async function copyEmailAddresses() {
        const emailAddresses = getEmailAddresses();

        if (emailAddresses.length === 0) {
            showResult("Geen e-mailadressen om te kopiëren.");
            return;
        }

        const text = emailAddresses.join("; ");

        try {
            await navigator.clipboard.writeText(text);

            showResult(
                `${emailAddresses.length} e-mailadressen gekopieerd.`
            );
        } catch (error) {
            console.error(
                "Kopiëren van e-mailadressen is mislukt:",
                error
            );

            showResult(
                "Kopiëren van e-mailadressen is mislukt."
            );
        }
    }

    copyButton.addEventListener("click", copyEmailAddresses);
});