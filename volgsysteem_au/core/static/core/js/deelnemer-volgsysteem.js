"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const refreshButton = document.getElementById(
        "refreshVolgsysteemButton"
    );

    refreshButton?.addEventListener("click", () => {
        const url = new URL(
            window.location.href
        );

        url.searchParams.set("ververs", "true");

        window.location.href = url.toString();
    });
});