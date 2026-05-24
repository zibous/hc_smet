// kpis.js

let stylesInjected = false;

export function renderKPIs(kpis) {

    /* ----------------------------------------------------
       Inject CSS once (Unterstützt Hell- und Dunkel-Theme)
    ---------------------------------------------------- */

    if (!stylesInjected) {

        const style = document.createElement("style");

        style.innerHTML = `
            #summary {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
                gap: 1.5rem;
                margin-top: 2rem;
            }

            .kpi {
                padding: 1.4rem;
                border-radius: 1.0rem;
                transition: .25s ease;

                // ☀️🌙 NATIVE THEME VARIABLES (Ersetzt harte Farben)
                color: var(--text-main, #ffffff);
                background: var(--card-bg, rgba(255,255,255,0.08));
                border: 1px solid var(--border, rgba(255,255,255,0.10));

                backdrop-filter: blur(18px);
                -webkit-backdrop-filter: blur(18px);
                box-shadow: 0 6px 18px rgba(0,0,0,0.15);
            }

            .kpi:hover {
                transform: translateY(-2px);
                background: var(--border, rgba(255,255,255,0.12));
            }

            .kpi-label {
                margin-bottom: 0.6rem;
                opacity: 0.7;
                font-size: 1.2rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                color: var(--text-main, #ffffff);
            }

            .kpi-value {
                font-size: 1.5rem;
                font-weight: 700;
                letter-spacing: -0.02em;
            }

            /* 🎨 Optimierte KPI-Farben für perfekten Kontrast in beiden Themes */
            .kpi.total .kpi-value { color: #3b82f6; }
            [data-theme="dark"] .kpi.total .kpi-value { color: #60a5fa; }

            .kpi.avg .kpi-value { color: #10b981; }
            [data-theme="dark"] .kpi.avg .kpi-value { color: #34d399; }

            .kpi.peak .kpi-value { color: #d97706; }
            [data-theme="dark"] .kpi.peak .kpi-value { color: #f59e0b; }

            .kpi.cost .kpi-value { color: #db2777; }
            [data-theme="dark"] .kpi.cost .kpi-value { color: #f472b6; }

            .kpi.delta .kpi-value { color: #7c3aed; }
            [data-theme="dark"] .kpi.delta .kpi-value { color: #a78bfa; }
        `;

        document.head.appendChild(style);
        stylesInjected = true;
    }

    /* ----------------------------------------------------
       Render (Krisensichere Fallbacks für leere Werte)
    ---------------------------------------------------- */

    const total = kpis && kpis.total !== undefined ? kpis.total : 0.0;
    const avg = kpis && kpis.avg !== undefined ? kpis.avg : 0.0;
    const peak = kpis && kpis.peak !== undefined ? kpis.peak : 0.0;
    const cost = kpis && kpis.cost !== undefined ? kpis.cost : 0.0;
    const delta = kpis && kpis.delta !== undefined ? kpis.delta : 0.0;

    document.getElementById("summary").innerHTML = `

        <div class="kpi total">
            <div class="kpi-label">Verbrauch</div>
            <div class="kpi-value">${total.toFixed(1)} kWh</div>
        </div>

        <div class="kpi avg">
            <div class="kpi-label">Mittelwert</div>
            <div class="kpi-value">${avg.toFixed(2)} kW</div>
        </div>

        <div class="kpi peak">
            <div class="kpi-label">Lastspitzen</div>
            <div class="kpi-value">${peak.toFixed(1)} kW</div>
        </div>

        <div class="kpi cost">
            <div class="kpi-label">Kosten</div>
            <div class="kpi-value">${cost.toFixed(2)} €</div>
        </div>

        <div class="kpi delta">
            <div class="kpi-label">Differenz</div>
            <div class="kpi-value">${delta >= 0 ? "+" : ""}${delta.toFixed(1)} %</div>
        </div>

    `;
}
