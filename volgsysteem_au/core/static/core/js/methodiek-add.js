"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("methodiekForm");
    const participantField = document.getElementById("id_deelnemer");
    const warning = document.getElementById("duplicateWarning");

    if (!form || !participantField || !warning) {
        return;
    }

    const duplicateCheckUrl = form.dataset.duplicateCheckUrl;

    if (!duplicateCheckUrl) {
        console.error(
            "URL voor de duplicaatcontrole ontbreekt."
        );
        return;
    }

    const csrfToken = form.querySelector(
        "input[name='csrfmiddlewaretoken']"
    )?.value;

    if (!csrfToken) {
        console.error(
            "CSRF-token ontbreekt in het methodiekformulier."
        );
        return;
    }

    let controller = null;

    participantField.addEventListener("change", async () => {
        warning.hidden = true;

        const selectedValue = participantField.value;

        if (!selectedValue) {
            return;
        }

        controller?.abort();

        controller = new AbortController();

        const formData = new FormData();

        formData.append(
            "selected_value",
            selectedValue
        );

        try {
            const response = await fetch(
                duplicateCheckUrl,
                {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken,
                        "Accept": "application/json",
                    },
                    body: formData,
                    signal: controller.signal,
                }
            );

            if (!response.ok) {
                throw new Error(
                    `HTTP-fout ${response.status}`
                );
            }

            const data = await response.json();

            warning.hidden = !data.duplicate;
        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            console.error(
                "Duplicaatcontrole mislukt:",
                error
            );
        }
    });
});