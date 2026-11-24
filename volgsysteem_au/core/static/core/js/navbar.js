"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const mobileMenuButton = document.querySelector("[data-menu-button]");
    const mainNavigation = document.querySelector("[data-main-navigation]");
    const submenuButtons = Array.from(
        document.querySelectorAll("[data-submenu-toggle]")
    );

    const desktopMediaQuery = window.matchMedia("(min-width: 56.3125rem)");

    /**
     * Geeft het submenu terug dat bij een knop hoort.
     *
     * @param {HTMLElement} button
     * @returns {HTMLElement|null}
     */
    function getControlledSubmenu(button) {
        const submenuId = button.getAttribute("aria-controls");

        if (!submenuId) {
            return null;
        }

        return document.getElementById(submenuId);
    }

    /**
     * Sluit één submenu.
     *
     * @param {HTMLElement} button
     */
    function closeSubmenu(button) {
        const submenu = getControlledSubmenu(button);

        button.setAttribute("aria-expanded", "false");

        if (submenu) {
            submenu.hidden = true;
        }
    }

    /**
     * Opent één submenu.
     *
     * @param {HTMLElement} button
     */
    function openSubmenu(button) {
        const submenu = getControlledSubmenu(button);

        button.setAttribute("aria-expanded", "true");

        if (submenu) {
            submenu.hidden = false;
        }
    }

    /**
     * Sluit submenu's die op hetzelfde niveau staan.
     *
     * @param {HTMLElement} currentButton
     */
    function closeSiblingSubmenus(currentButton) {
        const currentItem = currentButton.closest("li");

        if (!currentItem) {
            return;
        }

        const parentList = currentItem.parentElement;

        if (!parentList) {
            return;
        }

        Array.from(parentList.children).forEach((item) => {
            if (item === currentItem) {
                return;
            }

            const button = item.querySelector(
                ":scope > [data-submenu-toggle]"
            );

            if (button) {
                closeSubmenuTree(button);
            }
        });
    }

    /**
     * Sluit een submenu en alle geneste submenu's.
     *
     * @param {HTMLElement} button
     */
    function closeSubmenuTree(button) {
        const submenu = getControlledSubmenu(button);

        if (submenu) {
            submenu
                .querySelectorAll("[data-submenu-toggle]")
                .forEach((nestedButton) => {
                    closeSubmenu(nestedButton);
                });
        }

        closeSubmenu(button);
    }

    /**
     * Sluit alle submenu's.
     */
    function closeAllSubmenus() {
        submenuButtons.forEach((button) => {
            closeSubmenu(button);
        });
    }

    /**
     * Zet het mobiele hoofdmenu open of dicht.
     *
     * @param {boolean} shouldOpen
     */
    function setMobileMenuState(shouldOpen) {
        if (!mobileMenuButton || !mainNavigation) {
            return;
        }

        mobileMenuButton.setAttribute(
            "aria-expanded",
            String(shouldOpen)
        );

        mobileMenuButton.setAttribute(
            "aria-label",
            shouldOpen
                ? "Navigatiemenu sluiten"
                : "Navigatiemenu openen"
        );

        mainNavigation.classList.toggle("is-open", shouldOpen);

        if (!shouldOpen) {
            closeAllSubmenus();
        }
    }

    /**
     * Geeft de zichtbare, focusbare onderdelen van een submenu terug.
     *
     * @param {HTMLElement} submenu
     * @returns {HTMLElement[]}
     */
    function getFocusableItems(submenu) {
        return Array.from(
            submenu.querySelectorAll(
                [
                    ":scope > li > a:not([aria-disabled='true'])",
                    ":scope > li > button:not([disabled])"
                ].join(",")
            )
        ).filter((item) => !item.hidden);
    }

    if (mobileMenuButton && mainNavigation) {
        mobileMenuButton.addEventListener("click", () => {
            const isOpen =
                mobileMenuButton.getAttribute("aria-expanded") === "true";

            setMobileMenuState(!isOpen);
        });
    }

    submenuButtons.forEach((button) => {
        const submenu = getControlledSubmenu(button);

        if (!submenu) {
            return;
        }

        button.setAttribute("aria-expanded", "false");
        submenu.hidden = true;

        button.addEventListener("click", (event) => {
            event.preventDefault();

            const isOpen =
                button.getAttribute("aria-expanded") === "true";

            if (isOpen) {
                closeSubmenuTree(button);
                return;
            }

            closeSiblingSubmenus(button);
            openSubmenu(button);
        });

        button.addEventListener("keydown", (event) => {
            const focusableItems = getFocusableItems(submenu);

            if (
                event.key === "ArrowDown" ||
                event.key === "Enter" ||
                event.key === " "
            ) {
                event.preventDefault();

                closeSiblingSubmenus(button);
                openSubmenu(button);

                if (event.key === "ArrowDown") {
                    focusableItems[0]?.focus();
                }
            }

            if (event.key === "Escape") {
                event.preventDefault();
                closeSubmenuTree(button);
                button.focus();
            }
        });

        submenu.addEventListener("keydown", (event) => {
            const focusableItems = getFocusableItems(submenu);
            const currentIndex = focusableItems.indexOf(
                document.activeElement
            );

            if (event.key === "ArrowDown") {
                event.preventDefault();

                const nextIndex =
                    currentIndex < focusableItems.length - 1
                        ? currentIndex + 1
                        : 0;

                focusableItems[nextIndex]?.focus();
            }

            if (event.key === "ArrowUp") {
                event.preventDefault();

                const previousIndex =
                    currentIndex > 0
                        ? currentIndex - 1
                        : focusableItems.length - 1;

                focusableItems[previousIndex]?.focus();
            }

            if (event.key === "Home") {
                event.preventDefault();
                focusableItems[0]?.focus();
            }

            if (event.key === "End") {
                event.preventDefault();
                focusableItems.at(-1)?.focus();
            }

            if (event.key === "Escape") {
                event.preventDefault();
                closeSubmenuTree(button);
                button.focus();
            }
        });
    });

    document.addEventListener("click", (event) => {
        if (
            mainNavigation &&
            !mainNavigation.contains(event.target) &&
            mobileMenuButton &&
            !mobileMenuButton.contains(event.target)
        ) {
            closeAllSubmenus();

            if (!desktopMediaQuery.matches) {
                setMobileMenuState(false);
            }
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") {
            return;
        }

        closeAllSubmenus();

        if (!desktopMediaQuery.matches) {
            setMobileMenuState(false);
            mobileMenuButton?.focus();
        }
    });

    mainNavigation?.addEventListener("click", (event) => {
        const link = event.target.closest("a");

        if (!link || desktopMediaQuery.matches) {
            return;
        }

        setMobileMenuState(false);
    });

    desktopMediaQuery.addEventListener("change", (event) => {
        closeAllSubmenus();

        if (event.matches) {
            mainNavigation?.classList.remove("is-open");

            mobileMenuButton?.setAttribute(
                "aria-expanded",
                "false"
            );

            mobileMenuButton?.setAttribute(
                "aria-label",
                "Navigatiemenu openen"
            );
        } else {
            setMobileMenuState(false);
        }
    });
});