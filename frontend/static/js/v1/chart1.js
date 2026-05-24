import { chart, setChart, getCurrentTitle } from "./state.js";

/* --------------------------------------------------
   CHART MODE
-------------------------------------------------- */
let chartMode = "area"; // "bar" | "line" | "area"

/* --------------------------------------------------
   LEVEL → ICON
-------------------------------------------------- */
const LEVEL_MAP = {
    1: "haus",
    2: "etage",
    3: "raum",
    4: "sensor"
};

/* --------------------------------------------------
   OPTIONS (Dynamische Farbanpassung für Tag/Nacht)
-------------------------------------------------- */
function getOptions(_title, theme) {
    const isDark = theme === "dark";

    const titleColor = isDark ? "#ffffff" : "#1e293b";
    const tickColor = isDark ? "#94a3b8" : "#475569";
    const legendColor = isDark ? "#cbd5e1" : "#334155";
    const gridColor = isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.04)";
    const tooltipBg = isDark ? "rgba(15,23,42,0.94)" : "rgba(255,255,255,0.96)";
    const tooltipBorder = isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)";
    const titleFontColor = isDark ? "#ffffff" : "#1e293b";
    const bodyFontColor = isDark ? "#e2e8f0" : "#475569";

    // Stacked nur im Bar-Modus (da Area jetzt mathematisch im Code summiert wird!)
    const isBar = chartMode === "bar";

    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        interaction: {
            intersect: false,
            mode: "index"
        },
        layout: {
            padding: {
                left: 30,
                right: 20,
                top: 0,
                bottom: 0
            }
        },
        plugins: {
            legend: {
                display: chartMode !== "area", // Versteckt die Einzel-Legenden im Gesamt-Summen-Modus
                position: "bottom",
                labels: {
                    color: legendColor,
                    usePointStyle: true,
                    padding: 24,
                    font: { size: 12 }
                }
            },
            title: {
                display: true,
                text: _title,
                align: "start",
                color: titleColor,
                fullSize: false,
                font: {
                    size: 18,
                    weight: "600"
                },
                padding: {
                    top: 10,
                    bottom: 30
                }
            },
            tooltip: {
                backgroundColor: tooltipBg,
                borderColor: tooltipBorder,
                borderWidth: 1,
                titleColor: titleFontColor,
                bodyColor: bodyFontColor,
                padding: 12,
                displayColors: chartMode !== "area",
                boxBorderRadius: 4
            }
        },
        scales: {
            x: {
                stacked: isBar,
                ticks: {
                    color: tickColor,
                    autoSkip: true,
                    maxTicksLimit: 6,
                    font: { size: 11 }
                },
                grid: {
                    display: false
                }
            },
            y: {
                stacked: isBar,
                beginAtZero: true,
                ticks: {
                    color: tickColor,
                    font: { size: 11 }
                },
                grid: {
                    color: gridColor,
                    drawBorder: false
                }
            }
        }
    };
}

/* --------------------------------------------------
   RENDER PIPELINE
-------------------------------------------------- */
export function renderChart(data, theme = "light") {
    const canvas = document.getElementById("energyChart");
    if (!data?.current) return;
    const ctx = canvas.getContext("2d");
    const _title = "Verbrauch für " + getCurrentTitle();

    const activeTheme = localStorage.getItem("theme") || theme;
    const isDark = activeTheme === "dark";

    /* --------------------------------------------------
       CARD STYLING
    -------------------------------------------------- */
    const card = document.getElementById("dashboardCard");
    if (card) {
        card.style.position = "relative";
        card.style.padding = "1.5rem";
        card.style.borderRadius = "1.4rem";
        card.style.background = "var(--card-bg)";
        card.style.border = "1px solid var(--border)";
        card.style.backdropFilter = "blur(18px)";
        card.style.webkitBackdropFilter = "blur(18px)";
        card.style.boxShadow = "0 10px 30px rgba(0,0,0,0.15)";
    }

    /* --------------------------------------------------
       MODE BUTTON
    -------------------------------------------------- */
    let modeBtn = document.getElementById("chartModeBtn");
    const icons = {
        bar: "📊",
        line: "📈",
        area: "🌈"
    };
    if (!modeBtn && card) {
        modeBtn = document.createElement("button");
        modeBtn.id = "chartModeBtn";
        modeBtn.textContent = icons[chartMode];
        modeBtn.style.position = "absolute";
        modeBtn.style.top = "1.2rem";
        modeBtn.style.left = "12px";
        modeBtn.style.width = "42px";
        modeBtn.style.height = "42px";
        modeBtn.style.display = "flex";
        modeBtn.style.alignItems = "center";
        modeBtn.style.justifyContent = "center";
        modeBtn.style.fontSize = "1.3rem";
        modeBtn.style.padding = "0";
        modeBtn.style.borderRadius = "999px";
        modeBtn.style.border ="1px solid var(--border)";
        modeBtn.style.background = "rgba(128,128,128,0.06)";
        modeBtn.style.color = "var(--text-main)";
        modeBtn.style.cursor = "pointer";
        modeBtn.style.backdropFilter = "blur(10px)";
        modeBtn.style.transition = "all .2s ease";

        modeBtn.onclick = () => {
            chartMode = chartMode === "bar" ? "line" : chartMode === "line" ? "area" : "bar";
            modeBtn.textContent = icons[chartMode];
            renderChart(data, activeTheme);
        };
        card.appendChild(modeBtn);
    } else if (modeBtn) {
        modeBtn.textContent = icons[chartMode];
        modeBtn.style.color = "var(--text-main)";
        modeBtn.style.borderColor = "var(--border)";
    }

    /* --------------------------------------------------
       CANVAS SIZE
    -------------------------------------------------- */
    canvas.style.width = "100%";
    canvas.style.height = "420px";

    /* --------------------------------------------------
       DATA & LABELS
    -------------------------------------------------- */
    const labels = data.current.time || [];
    const seriesData = data.current.series || {};
    const keys = Object.keys(seriesData);
    const apiLabels = data.current.labels || {};

    const compareSeries = data.compare?.series || data.previous?.series || null;

    /* --------------------------------------------------
       AREA GRADIENT
    -------------------------------------------------- */
    function makeAreaGradient(context) {
        const chartObj = context.chart;
        const { ctx: chartCtx, chartArea } = chartObj;
        if (!chartArea) {
            return "rgba(0,255,140,0.08)";
        }
        const gradient = chartCtx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
        if (isDark) {
            gradient.addColorStop(0, "rgba(255, 90, 90, 0.22)");
            gradient.addColorStop(0.5, "rgba(255, 210, 0, 0.08)");
            gradient.addColorStop(1, "rgba(0, 255, 140, 0.00)");
        } else {
            gradient.addColorStop(0, "rgba(255, 90, 90, 0.22)");
            gradient.addColorStop(0.5, "rgba(255, 210, 0, 0.08)");
            gradient.addColorStop(1, "rgba(0, 255, 140, 0.01)");
        }
        return gradient;
    }

    /* --------------------------------------------------
       BUILD DATASETS
    -------------------------------------------------- */
    const datasets = [];

    // ✨ DEINE ORIGINAL-LOGIK FÜR DEN AREA-MODUS (Mathematische Vor-Summierung)
    if (chartMode === "area") {
        let sumData = [];
        let prevSumData = [];

        // 1. Gegenwart aufsummieren
        if (keys.length > 0) {
            sumData = [...(seriesData[keys[0]] || [])];
            for (let i = 1; i < keys.length; i++) {
                const nextData = seriesData[keys[i]] || [];
                for (let j = 0; j < sumData.length; j++) {
                    sumData[j] += (nextData[j] || 0);
                }
            }
        }

        // 2. Vorperiode aufsummieren
        if (compareSeries && keys.length > 0) {
            prevSumData = [...(compareSeries[keys[0]] || [])];
            for (let i = 1; i < keys.length; i++) {
                const nextData = compareSeries[keys[i]] || [];
                for (let j = 0; j < prevSumData.length; j++) {
                    prevSumData[j] += (nextData[j] || 0);
                }
            }
        }

        const areaColor = isDark ? "hsla(140, 100%, 63%, " : "hsla(140, 90%, 45%, ";
        const compareAreaColor = isDark ? "hsla(0, 0%, 100%, " : "hsla(0, 0%, 40%, ";

        // Gegenwart Dataset (Regenbogen/Gradient-Verlauf)
        datasets.push({
            label: "Gesamtverbrauch (Aktuell)",
            data: sumData,
            type: "line",
            backgroundColor: makeAreaGradient,
            borderColor: areaColor + "1)",
            borderWidth: 2,
            fill: "origin",
            tension: 0.22,
            pointRadius: 0,
            pointHoverRadius: 4,
            order: 1
        });

        // Vorperiode Dataset (Weiß/Grau gestrichelter Trendverlauf)
        if (compareSeries && prevSumData.length > 0) {
            datasets.push({
                label: "Gesamtverbrauch (Vorperiode)",
                data: prevSumData,
                type: "line",
                backgroundColor: "transparent",
                borderColor: compareAreaColor + (isDark ? "0.40)" : "0.55)"),
                borderWidth: 1.5,
                borderDash: [5, 5],
                fill: false,
                tension: 0.22,
                pointRadius: 0,
                pointHoverRadius: 3,
                order: 2
            });
        }

    } else {
        // 📊 STANDARD-MODUS FÜR BAR & LINE (Einzelne Sensoren behalten ihre Farben)
        keys.forEach((key, index) => {
            const labelName = apiLabels[key] || key;
            const baseHue = (index * (360 / Math.max(1, keys.length))) % 360;

            const currentBaseColor = isDark
                ? `hsla(${baseHue}, 100%, 63%, `
                : `hsla(${baseHue}, 90%, 55%, `;

            const currentSum = seriesData[key] || [];
            const isBar = chartMode === "bar";

            const compareBaseColor = isDark
                ? (isBar ? `hsla(${baseHue}, 85%, 55%, ` : `hsla(0, 0%, 100%, `)
                : `hsla(${baseHue}, 20%, 45%, `;

            // 1. DATASET: Aktuelle Periode
            datasets.push({
                label: labelName,
                data: currentSum,
                type: isBar ? "bar" : "line",
                backgroundColor: isBar ? currentBaseColor + "0.85)" : currentBaseColor + "0.05)",
                borderColor: currentBaseColor + "1)",
                borderWidth: isBar ? 1 : 1.75,
                borderRadius: isBar ? 6 : 0,
                borderSkipped: isBar ? "middle" : false,
                fill: false,
                tension: isBar ? 0 : 0.22,
                pointRadius: 0,
                pointHoverRadius: isBar ? 0 : 4,
                stack: "current",
                barPercentage: 0.80,
                categoryPercentage: 0.70,
                order: 1
            });

            // 2. DATASET: Vorperiode
            if (compareSeries && compareSeries[key]) {
                const compareSum = compareSeries[key] || [];
                const lineOpacity = isDark ? (isBar ? "0.30)" : "0.40)") : "0.55)";
                const lineWidth = isBar ? 1 : 1.25;

                datasets.push({
                    label: `${labelName} (Vorperiode)`,
                    data: compareSum,
                    type: isBar ? "bar" : "line",
                    backgroundColor: isBar ? compareBaseColor + "0.30)" : "transparent",
                    borderColor: isBar
                        ? (isDark ? "rgba(15,23,42,0.4)" : "rgba(255,255,255,0.5)")
                        : compareBaseColor + lineOpacity,
                    borderWidth: lineWidth,
                    borderRadius: isBar ? 6 : 0,
                    borderSkipped: isBar ? "middle" : false,
                    borderDash: isBar ? [] : [4, 4],
                    fill: false,
                    tension: isBar ? 0 : 0.22,
                    pointRadius: 0,
                    pointHoverRadius: isBar ? 0 : 3,
                    stack: "compare",
                    barPercentage: 0.80,
                    categoryPercentage: 0.70,
                    order: 2
                });
            }
        });
    }

    /* --------------------------------------------------
       RENDER CHART
    -------------------------------------------------- */
    if (chart) {
        chart.destroy();
    }

    const newChart = new Chart(ctx, {
        type: chartMode === "bar" ? "bar" : "line",
        data: {
            labels: labels,
            datasets: datasets
        },
        options: getOptions(_title, activeTheme)
    });

    setChart(newChart);
}
