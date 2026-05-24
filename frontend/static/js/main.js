// ES6-Module - ESM

import { renderKPIs } from "./kpis.js";
import { renderCards } from "./cards.js";
import { renderChart } from "./chart.js";
import { renderBreadcrumb } from "./breadcrumb.js";
import { currentNode } from "./state.js";
import { renderPeriodStrip } from "./dateselector.js";

let currentFrom = null;
let currentTo = null;
let currentCompare = 1;

// Zwischenspeicher für die letzten API-Daten, um das Chart live umzufärben
let lastTimelineData = null;

/* ----------------------------------------------------
   DASHBOARD LOADER (Unterstützt wahlweise GET oder POST)
---------------------------------------------------- */
export async function loadAll() {
  try {
    if (!currentFrom || !currentTo) {
      console.warn("loadAll() called before from/to set");
      return;
    }

    // 🔧 WAHLWEISE METHODEN-STEUERUNG ("GET" oder "POST")
    // Kannst du fliegend austauschen. Das Backend verarbeitet beide Endpoints synchron!
    const requestMethod = "POST";

    let url = "api/dashboard";
    let fetchOptions = {};

    if (requestMethod === "POST") {
      // Sensationell clean: Keine ewig langen URL-Parameter bei Langzeitabfragen
      fetchOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          node: currentNode,
          from_ts: currentFrom,
          to_ts: currentTo,
          compare: currentCompare
        })
      };
    } else {
      // Klassischer GET-Fallback mit URL-Parametern
      const queryParams = new URLSearchParams({
        node: currentNode,
        from: currentFrom,
        to: currentTo,
        compare: currentCompare
      });
      url += `?${queryParams.toString()}`;
      fetchOptions = {
        method: "GET"
      };
    }

    const res = await fetch(url, fetchOptions);
    if (!res.ok) throw new Error("API error");

    const data = await res.json();

    console.log(data);

    // Daten für Live-Theme-Wechsel zwischenspeichern
    lastTimelineData = data.timeseries;

    renderKPIs(data.kpis);

    // Karten rendern (Greift fehlerfrei auf dein optimiertes Datenmodell zu)
    renderCards({
      level: data.cards.level, // 🔧 Übergibt das numerische Level für den Klick-Schutz!
      node: data.cards.node,
      items: data.cards.items,
      stats: data.timeseries.current.stats,
      series: data.timeseries.current.series
    });

    // Das aktuelle Theme aus dem HTML-Tag auslesen ('light' oder 'dark')
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    renderChart(data.timeseries, currentTheme);

    renderBreadcrumb();

  } catch (err) {
    console.error("Dashboard load failed:", err);
  }
}

/* ----------------------------------------------------
   APP INIT
---------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {

  // Perioden-Navigation initialisieren
  renderPeriodStrip(({ from, to, compare }) => {
    currentFrom = from;
    currentTo = to;
    currentCompare = compare ? 1 : 0;
    loadAll();
  });

  // Event-Listener für den Live-Wechsel des Day/Night Modes
  window.addEventListener('themeChanged', (e) => {
    const newTheme = e.detail; // 'light' oder 'dark'

    // Wenn bereits Daten geladen wurden, zeichnen wir das Diagramm sofort mit den neuen Farben neu
    if (lastTimelineData) {
      renderChart(lastTimelineData, newTheme);
    }
  });

  // Automatischer Minuten-Refresh (Zieht alle 60 Sekunden frische Daten vom FastAPI-Server)
  setInterval(loadAll, 60000);
});

/* ----------------------------------------------------
   INFO
---------------------------------------------------- */
const appinfo = {
  name: "✓ smartmeter-dashboard ",
  app: "hc_smet",
  version: "1.6.0"
};

console.info(
  "%c " + appinfo.name + "    %c ▪︎▪︎▪︎▪︎ Version: " + appinfo.version + " ▪︎▪︎▪︎▪︎ ",
  "color:#FFFFFF; background:#3498db;display:inline-block;font-size:12px;font-weight:200;padding: 4px 0 4px 0",
  "color:#2c3e50; background:#ecf0f1;display:inline-block;font-size:12px;font-weight:200;padding: 4px 0 4px 0"
);
console.log("[cards-layout] loaded — version:", appinfo.version);
