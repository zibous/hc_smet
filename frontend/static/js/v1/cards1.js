/* ----------------------------------------------------
   CARDS COMPONENT (Compact Modern Glass UI - Theme Aware)
---------------------------------------------------- */

import { drillDown } from "./breadcrumb.js";

/* ----------------------------------------------------
   STYLE INJECTION
---------------------------------------------------- */

let stylesInjected = false;

function injectStyles() {

    if (stylesInjected) return;

    const style = document.createElement("style");

    style.innerHTML = `
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(22rem, 1fr));
            gap: 1.4rem;
        }

        .card {
            position: relative;
            overflow: hidden;
            padding: 1.4rem;
            border-radius: 1.8rem;
            cursor: pointer;

            // ☀️🌙 NATIVE THEME VARIABLES (Ersetzt harte Farben)
            color: var(--text-main, #ffffff);
            background: var(--card-bg, rgba(255,255,255,0.10));
            border: 1px solid var(--border, rgba(255,255,255,0.10));

            backdrop-filter: blur(22px);
            -webkit-backdrop-filter: blur(22px);

            box-shadow:
                0 8px 24px rgba(0,0,0,0.12),
                inset 0 1px 0 rgba(255,255,255,0.05);

            transition:
                transform .25s ease,
                box-shadow .25s ease,
                background .25s ease;
        }

        .card:hover {
            transform: translateY(-4px);
            border-color: var(--primary, #3182ce);
            box-shadow: 0 12px 28px rgba(0,0,0,0.18);
        }

        // Deaktiviert Effekte auf der Sensor-Endebene
        .card.no-click {
            cursor: default;
        }
        .card.no-click:hover {
            transform: none;
            border-color: var(--border, rgba(255,255,255,0.10));
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.8rem;
        }

        .card-title {
            font-size: 1.4rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            color: var(--text-main, #ffffff);
        }

        .card-value {
            font-size: 2.1rem;
            font-weight: 800;
            line-height: 1;
            margin-top: 0.35rem;
            color: var(--text-main, #ffffff);
        }

        .card-unit {
            color: var(--text-muted, rgba(255, 255, 255, 0.7));
            font-size: 1rem;
            margin-left: 0.2rem;
        }

        .card-delta {
            font-size: 1.1rem;
            font-weight: 700;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: rgba(128,128,128,0.08);
            backdrop-filter: blur(10px);
        }

        .sparkline-wrapper {
            position: relative;
            height: 60px;
            margin: 1rem -0.3rem 1rem -0.3rem;
        }

        .sparkline {
            width: 100%;
            height: 100%;
            display: block;
        }

        .card-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.7rem;
        }

        .stat {
            padding: 0.7rem;
            border-radius: 1rem;
            background: rgba(128,128,128,0.05);
            border: 1px solid var(--border, rgba(255,255,255,0.06));
            text-align: center;
        }

        .stat-label {
            font-size: 1rem;
            color: var(--text-muted, rgba(255,255,255,0.65));
            margin-bottom: 0.25rem;
        }

        .stat-value {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--text-main, #ffffff);
        }
    `;

    document.head.appendChild(style);
    stylesInjected = true;
}

/* ----------------------------------------------------
   SPARKLINE (Dynamische Kurven-Farben)
---------------------------------------------------- */

function drawSparkline(canvas, values) {

    if (!values || values.length < 2) return;

    const ctx = canvas.getContext("2d");
    const width = canvas.offsetWidth;
    const height = canvas.offsetHeight;
    const dpr = window.devicePixelRatio || 1;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    // Downsampling
    const maxPoints = Math.floor(width / 3);
    let sampled = values;

    if (values.length > maxPoints) {
        sampled = [];
        const bucketSize = values.length / maxPoints;
        for (let i = 0; i < maxPoints; i++) {
            const start = Math.floor(i * bucketSize);
            const end = Math.floor((i + 1) * bucketSize);
            let sum = 0;
            let count = 0;
            for (let j = start; j < end; j++) {
                sum += values[j];
                count++;
            }
            sampled.push(sum / count);
        }
    }

    // Normalize
    const min = Math.min(...sampled);
    const max = Math.max(...sampled);
    const range = max - min || 1;
    const normalized = sampled.map(v => (v - min) / range);
    const stepX = width / (normalized.length - 1);

    // 🔧 DYNAMISCHE CURVEN-FARBEN (Tag/Nacht Erkennung)
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    const lineColor = isDark ? "#ff7700" : "#2b6cb0"; // Orange bei Nacht, Blau bei Tag
    const shadowColor = isDark ? "#ffb700" : "#4299e1";
    const gradientStart = isDark ? "rgba(255, 191, 0, 0.22)" : "rgba(66, 153, 225, 0.25)";

    // AREA GRADIENT
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, gradientStart);
    gradient.addColorStop(1, "rgba(0, 0, 0, 0)");

    ctx.beginPath();
    normalized.forEach((v, i) => {
        const x = i * stepX;
        const y = height - (v * (height - 10)) - 5;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // LINE
    ctx.beginPath();
    normalized.forEach((v, i) => {
        const x = i * stepX;
        const y = height - (v * (height - 10)) - 5;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    ctx.lineWidth = 1.4;
    ctx.strokeStyle = lineColor;
    ctx.shadowColor = shadowColor;
    ctx.shadowBlur = isDark ? 8 : 2; // Dezenterer Glow bei Tag
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    ctx.stroke();
}

/* ----------------------------------------------------
   RENDER
---------------------------------------------------- */

export function renderCards(data) {

    injectStyles();

    const container = document.getElementById("cards");
    if (!container) return;

    container.innerHTML = "";

    const stats = data.stats || {};
    const series = data.series || {};
    const items = data.items || [];

    items.forEach(item => {
        // Nutzt deinen genialen Detektor-Fix auf Item-Ebene
        const isSelfNode = item.level == 4;

        const s = stats[item.id] || { current: 0, delta: 0, min: 0, max: 0, avg: 0 };
        const values = Array.isArray(series[item.id]) ? series[item.id] : [];

        const card = document.createElement("div");

        if (isSelfNode) {
            card.className = "card no-click";
        } else {
            card.className = "card";
        }

        const positive = s.delta >= 0;

        card.innerHTML = `
            <div class="card-header">
                <div>
                    <div class="card-title">${item.name}</div>
                    <div class="card-value">
                        ${(item.value ?? 0).toFixed(1)}
                        <span class="card-unit">kWh</span>
                    </div>
                </div>
                <div class="card-delta" style="color: ${positive ? "#00FFC2" : "#FF7A7A"};">
                    ${positive ? "+" : ""}${(item.delta ?? 0).toFixed(1)}%
                </div>
            </div>

            <div class="sparkline-wrapper">
                <canvas class="sparkline"></canvas>
            </div>

            <div class="card-stats">
                <div class="stat">
                    <div class="stat-label">Min</div>
                    <div class="stat-value">${s.min.toFixed(1)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Max</div>
                    <div class="stat-value">${s.max.toFixed(1)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Schnitt</div>
                    <div class="stat-value">${s.avg.toFixed(1)}</div>
                </div>
            </div>
        `;

        if (!isSelfNode) {
            card.addEventListener("click", () => {
                drillDown(item.id, item.name);
            });
        }

        container.appendChild(card);

        const canvas = card.querySelector(".sparkline");
        if (canvas && values.length > 0) {
            drawSparkline(canvas, values);
        }
    });

    // 🔧 LIVE-THEME INTERACTION: Zeichent die Minigrafiken bei Klick auf den Umschalter sofort neu um
    if (!window.cardsThemeBound) {
        window.addEventListener('themeChanged', () => {
            setTimeout(() => { renderCards(data); }, 50);
        });
        window.cardsThemeBound = true;
    }
}
