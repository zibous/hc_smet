/* ----------------------------------------------------
   FLOATING BREADCRUMB
   Self-contained component (Theme Aware)
---------------------------------------------------- */

import {
    sliceBreadcrumb,
    updateBreadcrumb,
    setCurrentNode,
    breadcrumb
} from "./state.js";

import { loadAll } from "./main.js";

/* ----------------------------------------------------
   INJECT STYLES
---------------------------------------------------- */

let stylesInjected = false;

function injectStyles() {

    if (stylesInjected) return;

    const style = document.createElement("style");

    style.innerHTML = `
        .breadcrumb {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.8rem;
        }

        .crumb {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.9rem 1.4rem;
            border-radius: 9px;
            cursor: pointer;
            user-select: none;
            font-size: 1.6rem;
            font-weight: 500;

            // ☀️🌙 NATIVE THEME VARIABLES (Ersetzt harte Farben)
            color: var(--text-main, rgba(255,255,255,0.92));
            background: var(--card-bg, rgba(255,255,255,0.08));
            border: 1px solid var(--border, rgba(255,255,255,0.10));

            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            box-shadow: 0 4px 14px rgba(0,0,0,0.15);
            transition: .25s ease;
        }

        .crumb:hover {
            transform: translateY(-2px);
            background: var(--border, rgba(255,255,255,0.14));
        }

        .crumb.active {
            background: linear-gradient(135deg, #3b82f6, #60a5fa);
            border-color: #3b82f6;
            color: white;
        }

        // Korrektur für aktiven Text im Light Mode, falls var(--text-main) dunkel ist
        [data-theme="light"] .crumb.active {
            color: #ffffff;
        }

        .crumb-icon {
            font-size: 1.4rem;
        }

        .crumb-divider {
            opacity: 0.5;
            font-size: 1.2rem;
            color: var(--text-muted, rgba(255,255,255,0.35));
        }

        @media (max-width: 768px) {
            .breadcrumb {
                gap: 0.5rem;
            }

            .crumb {
                padding: 0.8rem 1.1rem;
                font-size: 1.25rem;
            }
        }
    `;

    document.head.appendChild(style);
    stylesInjected = true;
}

/* ----------------------------------------------------
   DRILLDOWN
---------------------------------------------------- */

export function drillDown(id, name) {

    setCurrentNode(id);

    updateBreadcrumb(name, id);

    renderBreadcrumb();

    loadAll();
}

/* ----------------------------------------------------
   BACK
---------------------------------------------------- */

export function breadcrumbBack(index) {

    sliceBreadcrumb(index);

    renderBreadcrumb();

    loadAll();
}

/* ----------------------------------------------------
   RENDER
---------------------------------------------------- */

export function renderBreadcrumb() {

    injectStyles();

    const container = document.getElementById("breadcrumb");
    if (!container) return;

    container.className = "breadcrumb";
    container.innerHTML = "";

    breadcrumb.forEach((item, index) => {

        /* ITEM */
        const crumb = document.createElement("div");

        crumb.className =
            index === breadcrumb.length - 1
                ? "crumb active"
                : "crumb";

        /* OPTIONAL HOME ICON */
        const icon =
            index === 0
                ? `<span class="crumb-icon">🏠</span>`
                : "";

        crumb.innerHTML = `
            ${icon}
            <span>
                ${item}
            </span>
        `;

        /* CLICK */
        crumb.addEventListener("click", () => {
            breadcrumbBack(index);
        });

        container.appendChild(crumb);

        /* DIVIDER */
        if (index < breadcrumb.length - 1) {

            const divider = document.createElement("div");

            divider.className = "crumb-divider";
            divider.innerHTML = "→";

            container.appendChild(divider);
        }
    });
}
