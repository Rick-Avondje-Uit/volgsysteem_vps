"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const tables = document.querySelectorAll(
        ".vragenlijst-resultaten table"
    );

    if (!tables.length) {
        return;
    }

    const answerClasses = {
        "nooit": "vragenlijst-score--nooit",
        "bijna nooit": "vragenlijst-score--bijna-nooit",
        "soms": "vragenlijst-score--soms",
        "bijna altijd": "vragenlijst-score--bijna-altijd",
        "altijd": "vragenlijst-score--altijd",
    };

    function convertTextAnswers(table) {
        const rows = table.querySelectorAll("tbody tr");

        rows.forEach((row) => {
            const typeCell = row.querySelector(
                "td:nth-child(2)"
            );

            if (!typeCell) {
                return;
            }

            const questionType = typeCell
                .textContent
                .trim()
                .toLowerCase();

            if (questionType !== "text") {
                return;
            }

            const answerCells = row.querySelectorAll(
                "td:nth-child(n+3)"
            );

            answerCells.forEach((cell) => {
                const answer = cell.textContent.trim();

                cell.replaceChildren();

                cell.classList.add(
                    "vragenlijst-tekstreactie"
                );

                const label = document.createElement("span");

                label.className =
                    "vragenlijst-tekstreactie__label";

                label.textContent = "Reactie";

                const content = document.createElement("span");

                content.className =
                    "vragenlijst-tekstreactie__content";

                content.textContent = answer;

                cell.append(label, content);
            });
        });
    }

    function removeQuestionTypeColumn(table) {
        const rows = table.querySelectorAll("tr");

        rows.forEach((row) => {
            const typeCell = row.children[1];

            typeCell?.remove();
        });
    }

    function applyAnswerColors(table) {
        const rows = table.querySelectorAll("tbody tr");

        rows.forEach((row) => {
            const answerCells = row.querySelectorAll(
                "td:nth-child(n+2)"
            );

            answerCells.forEach((cell) => {
                if (
                    cell.classList.contains(
                        "vragenlijst-tekstreactie"
                    )
                ) {
                    return;
                }

                const answer = cell
                    .textContent
                    .trim()
                    .toLowerCase();

                const className = answerClasses[answer];

                if (className) {
                    cell.classList.add(className);
                }
            });
        });
    }

    tables.forEach((table) => {
        convertTextAnswers(table);
        removeQuestionTypeColumn(table);
        applyAnswerColors(table);
    });
});