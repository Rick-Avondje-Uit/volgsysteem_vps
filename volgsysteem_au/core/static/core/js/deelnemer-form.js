"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".deelnemer-form");
    const nameInput = document.getElementById("id_naam");
    const warning = document.getElementById("naamWarning");

    if (!form || !nameInput || !warning) {
        return;
    }

    const checkUrl = form.dataset.nameCheckUrl;

    if (!checkUrl) {
        return;
    }

    let timeout = null;
    let controller = null;

    nameInput.addEventListener("input", () => {
        clearTimeout(timeout);

        warning.hidden = true;

        const name = nameInput.value.trim();

        if (!name) {
            return;
        }

        timeout = setTimeout(async () => {
            controller?.abort();
            controller = new AbortController();

            const params = new URLSearchParams({
                naam: name,
            });

            try {
                const response = await fetch(
                    `${checkUrl}?${params.toString()}`,
                    {
                        signal: controller.signal,
                        headers: {
                            Accept: "application/json",
                        },
                    }
                );

                if (!response.ok) {
                    throw new Error(
                        `HTTP-fout ${response.status}`
                    );
                }

                const data = await response.json();

                warning.hidden = !data.exists;
            } catch (error) {
                if (error.name !== "AbortError") {
                    console.error(
                        "Naamcontrole mislukt:",
                        error
                    );
                }
            }
        }, 400);
    });
});