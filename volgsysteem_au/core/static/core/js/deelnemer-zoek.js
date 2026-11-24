"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById(
        "deelnemerZoekForm"
    );

    const input = document.getElementById(
        "deelnemer-zoekveld"
    );

    const dataList = document.getElementById(
        "deelnemers-lijst"
    );

    const results = document.getElementById(
        "deelnemers-resultaten"
    );

    if (!form || !input || !dataList || !results) {
        return;
    }

    const searchUrl = form.dataset.searchUrl;

    if (!searchUrl) {
        console.error(
            "De URL voor het zoeken naar deelnemers ontbreekt."
        );
        return;
    }

    let controller = null;
    let timeout = null;

    async function fetchParticipants(searchTerm) {
        controller?.abort();

        controller = new AbortController();

        const params = new URLSearchParams({
            zoekterm: searchTerm,
        });

        const response = await fetch(
            `${searchUrl}?${params.toString()}`,
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

        return response.json();
    }

    function getSuggestions(data) {
        return Array.isArray(data.suggesties)
            ? data.suggesties
            : [];
    }

    function renderSuggestions(suggestions) {
        dataList.replaceChildren();

        suggestions.forEach((suggestion) => {
            if (!suggestion.naam) {
                return;
            }

            const option = document.createElement(
                "option"
            );

            option.value = suggestion.naam;

            dataList.appendChild(option);
        });
    }

    function renderResults(suggestions) {
        results.replaceChildren();

        const validSuggestions = suggestions.filter(
            (suggestion) =>
                suggestion.naam &&
                suggestion.detail_url
        );

        if (!validSuggestions.length) {
            const message = document.createElement(
                "p"
            );

            message.textContent =
                "Geen deelnemers gevonden.";

            results.appendChild(message);
            return;
        }

        const list = document.createElement("ul");

        list.classList.add("list-group");

        validSuggestions.forEach((suggestion) => {
            const item = document.createElement("li");
            const link = document.createElement("a");

            item.classList.add("list-group-item");

            link.href = suggestion.detail_url;
            link.textContent = suggestion.naam;
            link.classList.add(
                "list-group-item-action"
            );

            item.appendChild(link);
            list.appendChild(item);
        });

        results.appendChild(list);
    }

    input.addEventListener("input", () => {
        window.clearTimeout(timeout);

        const searchTerm = input.value.trim();

        if (!searchTerm) {
            controller?.abort();

            dataList.replaceChildren();
            results.replaceChildren();

            return;
        }

        timeout = window.setTimeout(
            async () => {
                try {
                    const data = await fetchParticipants(
                        searchTerm
                    );

                    renderSuggestions(
                        getSuggestions(data)
                    );
                } catch (error) {
                    if (error.name === "AbortError") {
                        return;
                    }

                    console.error(
                        "Ophalen van suggesties mislukt:",
                        error
                    );
                }
            },
            300
        );
    });

    form.addEventListener(
        "submit",
        async (event) => {
            event.preventDefault();

            window.clearTimeout(timeout);

            const searchTerm = input.value.trim();

            if (!searchTerm) {
                dataList.replaceChildren();
                results.replaceChildren();

                return;
            }

            try {
                const data = await fetchParticipants(
                    searchTerm
                );

                renderResults(
                    getSuggestions(data)
                );
            } catch (error) {
                if (error.name === "AbortError") {
                    return;
                }

                console.error(
                    "Zoeken van deelnemers mislukt:",
                    error
                );
            }
        }
    );
});