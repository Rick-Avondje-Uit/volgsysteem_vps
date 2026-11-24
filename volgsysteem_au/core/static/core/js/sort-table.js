"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const tables = document.querySelectorAll(
        "table.js-sort-table"
    );

    tables.forEach((table) => {
        initialiseTable(table);
    });


    function initialiseTable(table) {
        const headers = table.querySelectorAll(
            "thead th"
        );

        headers.forEach((header, columnIndex) => {
            if (
                header.classList.contains(
                    "js-sort-none"
                )
            ) {
                return;
            }

            header.classList.add(
                "js-sortable"
            );

            header.tabIndex = 0;
            header.setAttribute(
                "role",
                "button"
            );

            header.setAttribute(
                "aria-sort",
                "none"
            );

            header.addEventListener("click", () => {
                sortTable(
                    table,
                    header,
                    columnIndex
                );
            });

            header.addEventListener(
                "keydown",
                (event) => {
                    if (
                        event.key !== "Enter" &&
                        event.key !== " "
                    ) {
                        return;
                    }

                    event.preventDefault();

                    sortTable(
                        table,
                        header,
                        columnIndex
                    );
                }
            );
        });
    }


    function sortTable(
        table,
        activeHeader,
        columnIndex
    ) {
        const tbody = table.tBodies[0];

        if (!tbody) {
            return;
        }

        const headers = table.querySelectorAll(
            "thead th"
        );

        const previousDirection =
            activeHeader.dataset.sortDirection;

        const direction =
            previousDirection === "asc"
                ? "desc"
                : "asc";

        headers.forEach((header) => {
            header.removeAttribute(
                "data-sort-direction"
            );

            header.setAttribute(
                "aria-sort",
                "none"
            );
        });

        activeHeader.dataset.sortDirection =
            direction;

        activeHeader.setAttribute(
            "aria-sort",
            direction === "asc"
                ? "ascending"
                : "descending"
        );

        const rows = Array.from(
            tbody.rows
        );

        const sortType = getSortType(
            activeHeader
        );

        rows.sort((rowA, rowB) => {
            const cellA =
                rowA.cells[columnIndex];

            const cellB =
                rowB.cells[columnIndex];

            const valueA = getComparableValue(
                cellA,
                sortType
            );

            const valueB = getComparableValue(
                cellB,
                sortType
            );

            const result = compareValues(
                valueA,
                valueB
            );

            return direction === "asc"
                ? result
                : -result;
        });

        rows.forEach((row) => {
            tbody.appendChild(row);
        });
    }


    function getSortType(header) {
        if (
            header.classList.contains(
                "js-sort-date"
            )
        ) {
            return "date";
        }

        if (
            header.classList.contains(
                "js-sort-number"
            )
        ) {
            return "number";
        }

        return "string";
    }


    function getComparableValue(
        cell,
        sortType
    ) {
        if (!cell) {
            return "";
        }

        const value = cell.textContent.trim();

        switch (sortType) {
            case "date":
                return parseDutchDate(value);

            case "number":
                return parseNumber(value);

            default:
                return value.toLocaleLowerCase(
                    "nl-NL"
                );
        }
    }


    function parseDutchDate(value) {
        const match = value.match(
            /^(\d{2})-(\d{2})-(\d{4})$/
        );

        if (!match) {
            return 0;
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
            return 0;
        }

        return date.getTime();
    }


    function parseNumber(value) {
        const normalizedValue = value
            .replace(/\s/g, "")
            .replace(",", ".")
            .replace(/[^\d.-]/g, "");

        const number = Number(
            normalizedValue
        );

        return Number.isNaN(number)
            ? 0
            : number;
    }


    function compareValues(
        valueA,
        valueB
    ) {
        if (
            typeof valueA === "number" &&
            typeof valueB === "number"
        ) {
            return valueA - valueB;
        }

        return String(valueA).localeCompare(
            String(valueB),
            "nl-NL",
            {
                numeric: true,
                sensitivity: "base",
            }
        );
    }
});