// dateselector.js

import { setCurrentRange, setCompareActive } from "./state.js";

let stylesInjected = false;

/* ----------------------------------------------------
   STYLES
---------------------------------------------------- */
function injectStyles() {
  if (stylesInjected) return;

  const style = document.createElement("style");
  style.innerHTML = `
    .header {
      position: relative !important;
      z-index: 1000 !important;
    }

    .period-container {
      position: relative;
      display: inline-flex;
      align-items: center;
    }

    .period-btn {
      padding: 0.8rem 1.4rem;
      border-radius: 999px;
      border: 1px solid var(--border, rgba(255,255,255,0.15));
      background: var(--card-bg, rgba(255,255,255,0.08));
      color: var(--text-main, #ffffff);
      cursor: pointer;
      font-size: 1.35rem;
      font-weight: 500;
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
    }

    .period-btn::after {
      content: " ▾";
      opacity: 0.7;
    }

    /* ✨ NEU: Mattiertes, blickdichtes VisionOS-Glas für das Dropdown gegen Durchscheinen */
    .period-dropdown {
      position: absolute !important;
      top: calc(100% + 0.5rem);
      right: 0;
      min-width: 240px;
      border-radius: 1.2rem;
      padding: 0.5rem;
      z-index: 99999 !important;
      max-height: 450px;
      overflow-y: auto;

      /* Starke Unschärfe und massiver Schatten für räumliche Abhebung */
      backdrop-filter: blur(35px) saturate(160%);
      -webkit-backdrop-filter: blur(35px) saturate(160%);
      box-shadow: 0 20px 50px rgba(0,0,0,0.35);

      /* Theme-Weiche: Sattes Dunkelblau nachts, deckendes Milchweiß tagsüber */
      background: rgba(255, 255, 255, 0.88);
      border: 1px solid rgba(0, 0, 0, 0.08);
    }

    [data-theme="dark"] .period-dropdown {
      background: rgba(13, 20, 38, 0.94);
      border: 1px solid rgba(255, 255, 255, 0.12);
      box-shadow: 0 25px 60px rgba(0,0,0,0.65);
    }

    .period-dropdown.hidden {
      display: none;
    }

    .dropdown-section {
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--text-muted, #718096);
      padding: 0.6rem 1.2rem 0.2rem 1.2rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    /* Textfarbe der Einträge an dein natives CSS-Theme gekoppelt */
    .period-item {
      padding: 0.8rem 1.2rem;
      border-radius: 0.8rem;
      font-size: 1.35rem;
      color: var(--text-main, #2d3748);
      cursor: pointer;
    }

    .period-item:hover {
      background: rgba(128, 128, 128, 0.12);
    }

    .archive-select-box {
      padding: 0.4rem 1.2rem 0.8rem 1.2rem;
      border-bottom: 1px dashed var(--border, #edf2f7);
      margin-bottom: 0.4rem;
    }

    .archive-select {
      width: 100%;
      padding: 0.6rem;
      border-radius: 0.6rem;
      border: 1px solid var(--border, #cbd5e1);
      background: var(--bg-color, #ffffff);
      color: var(--text-main, #2d3748);
      font-size: 1.3rem;
      outline: none;
      cursor: pointer;
    }

    .period-item.custom-toggle {
      border-top: 1px dashed var(--border, #edf2f7);
      margin-top: 0.4rem;
      padding-top: 0.8rem;
      color: var(--primary, #3182ce);
      font-weight: 600;
    }

    .inline-range-box {
      padding: 0.8rem;
      margin-top: 0.4rem;
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }

    .inline-range-box.hidden {
      display: none;
    }

    .inline-field {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
    }

    .inline-field label {
      font-size: 1.2rem;
      font-weight: 600;
      color: var(--text-muted, #718096);
    }

    .inline-range-box input[type="date"] {
      padding: 0.5rem;
      border-radius: 0.6rem;
      border: 1px solid var(--border, #cbd5e1);
      background-color: var(--bg-color, #f7fafc) !important;
      color: var(--text-main, #2d3748) !important;
      font-size: 1.25rem;
      outline: none;
      font-family: inherit;
    }

    [data-theme="dark"] .inline-range-box input[type="date"],
    [data-theme="dark"] .archive-select {
      background-color: #020617 !important;
      color: #f8fafc !important;
      border-color: #334155 !important;
      color-scheme: dark !important;
    }

    [data-theme="dark"] .inline-range-box input[type="date"]::-webkit-calendar-picker-indicator {
      filter: invert(1) !important;
      cursor: pointer;
      opacity: 0.8;
    }

    .inline-action-btn {
      width: 100%;
      padding: 0.7rem;
      border-radius: 0.6rem;
      border: none;
      background: var(--primary, #3182ce);
      color: #ffffff;
      font-size: 1.3rem;
      font-weight: 600;
      cursor: pointer;
    }

    .toggle { display: flex; align-items: center; gap: 0.7rem; cursor: pointer; font-size: 1.3rem; color: var(--text-main); }
    .toggle input { display: none; }
    .slider { position: relative; width: 3.6rem; height: 2rem; border-radius: 999px; background: #cbd5e1; transition: .2s ease; }
    .slider::before { content: ""; position: absolute; top: 0.2rem; left: 0.2rem; width: 1.6rem; height: 1.6rem; border-radius: 50%; background: #ffffff; transition: .2s ease; }
    .toggle input:checked + .slider { background: var(--primary, #3182ce); }
    .toggle input:checked + .slider::before { transform: translateX(1.6rem); }
  `;
  document.head.appendChild(style);
  stylesInjected = true;
}

/* ----------------------------------------------------
   DATUMS-BERECHNUNGEN
---------------------------------------------------- */
function getPeriodRange(periodKey) {
  const now = new Date();
  let fromDate = new Date();
  let toDate = new Date();

  fromDate.setHours(0, 0, 0, 0);
  toDate.setHours(23, 59, 59, 999);

  if (periodKey && periodKey.startsWith("jahr_")) {
    const targetYear = parseInt(periodKey.split("_")[1]);
    fromDate.setFullYear(targetYear, 0, 1);
    toDate.setFullYear(targetYear, 11, 31);
  } else {
    switch (periodKey) {
      case "heute": break;
      case "gestern":
        fromDate.setDate(now.getDate() - 1);
        toDate.setDate(now.getDate() - 1);
        break;
      case "woche": {
        const day = now.getDay();
        const diff = now.getDate() - day + (day === 0 ? -6 : 1);
        fromDate.setDate(diff);
        break;
      }
      case "7tage": fromDate.setDate(now.getDate() - 6); break;
      case "30tage": fromDate.setDate(now.getDate() - 29); break;
      case "monat": fromDate.setDate(1); break;
      case "jahr": fromDate.setMonth(0, 1); break;
    }
  }

  const formatISO = (d) => {
    const pad = (num) => String(num).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  };

  return { from: formatISO(fromDate), to: formatISO(toDate) };
}

/* ----------------------------------------------------
   RENDER PIPELINE
---------------------------------------------------- */
export function renderPeriodStrip(onRangeChanged) {
  injectStyles();

  const container = document.querySelector(".controls");
  if (!container) return;

  const savedRangeStr = localStorage.getItem("dash_range");
  const savedRange = savedRangeStr ? JSON.parse(savedRangeStr) : null;
  const savedCompare = localStorage.getItem("dash_compare") !== "false";

  let selectedLabel = localStorage.getItem("dash_btn_label") || "Heute";

  // Relative Zeiträume immer neu berechnen (nicht den alten Timestamp verwenden)
  const relativePeriods = { "Heute": "heute", "Gestern": "gestern", "Diese Woche": "woche",
    "Letzte 7 Tage": "7tage", "Letzte 30 Tage": "30tage", "Dieser Monat": "monat" };
  let activeRange;
  if (relativePeriods[selectedLabel]) {
    activeRange = getPeriodRange(relativePeriods[selectedLabel]);
  } else {
    activeRange = savedRange || getPeriodRange("heute");
  }

  const currentYear = new Date().getFullYear();
  let optionsHtml = `<option value="" disabled selected>Jahr auswählen...</option>`;
  for (let year = currentYear; year >= 2013; year--) {
    optionsHtml += `<option value="jahr_${year}">Jahr ${year}</option>`;
  }

  container.innerHTML = `
    <div class="period-container">
      <button class="period-btn" id="periodBtn">${selectedLabel}</button>

      <div class="period-dropdown hidden" id="periodDropdown">
        <div class="dropdown-section">Zeitraum</div>
        <div class="period-item" data-key="heute">Heute</div>
        <div class="period-item" data-key="gestern">Gestern</div>
        <div class="period-item" data-key="woche">Diese Woche</div>
        <div class="period-item" data-key="7tage">Letzte 7 Tage</div>
        <div class="period-item" data-key="30tage">Letzte 30 Tage</div>
        <div class="period-item" data-key="monat">Dieser Monat</div>

        <div class="dropdown-section">Archiv</div>
        <div class="archive-select-box">
          <select class="archive-select" id="archiveSelect">
            ${optionsHtml}
          </select>
        </div>

        <div class="period-item custom-toggle" id="customToggleItem">Benutzerdefiniert…</div>

        <div class="inline-range-box hidden" id="inlineRangeBox">
          <div class="inline-field">
            <label>Von</label>
            <input type="date" id="inlineFromDate">
          </div>
          <div class="inline-field">
            <label>Bis</label>
            <input type="date" id="inlineToDate">
          </div>
          <button class="inline-action-btn" id="inlineApplyBtn">Anwenden</button>
        </div>
      </div>
    </div>

    <label class="toggle">
      <input type="checkbox" id="compareToggle" ${savedCompare ? "checked" : ""}>
      <span class="slider"></span>
      <span>Vergleich Vorperiode</span>
    </label>
  `;

  const btn = document.getElementById("periodBtn");
  const dropdown = document.getElementById("periodDropdown");
  const archiveSelect = document.getElementById("archiveSelect");
  const customToggle = document.getElementById("customToggleItem");
  const rangeBox = document.getElementById("inlineRangeBox");
  const applyBtn = document.getElementById("inlineApplyBtn");
  const compareToggle = document.getElementById("compareToggle");
  const fromInput = document.getElementById("inlineFromDate");
  const toInput = document.getElementById("inlineToDate");

  const syncInputFields = (range) => {
    if (range && range.from && range.to) {
        fromInput.value = range.from.split("T")[0];
        toInput.value = range.to.split("T")[0];
    }
  };

  const savedCustomFrom = localStorage.getItem("dash_custom_from");
  const savedCustomTo = localStorage.getItem("dash_custom_to");
  if (selectedLabel === "Individuell" && savedCustomFrom && savedCustomTo) {
      fromInput.value = savedCustomFrom;
      toInput.value = savedCustomTo;
  } else {
      syncInputFields(activeRange);
  }

  btn.onclick = (e) => {
    e.stopPropagation();
    dropdown.classList.toggle("hidden");
  };

  document.addEventListener("click", () => {
    dropdown.classList.add("hidden");
  });
  dropdown.onclick = (e) => e.stopPropagation();

  const buildPayloadObject = (range) => {
    return {
      from: range.from,
      to: range.to,
      compare: compareToggle.checked ? 1 : 0
    };
  };

  const updatePeriod = (label, range) => {
    selectedLabel = label;
    activeRange = range;
    btn.textContent = label;

    setCurrentRange(range, label);
    dropdown.classList.add("hidden");

    if (label !== "Individuell") {
        syncInputFields(range);
    }

    if (onRangeChanged) {
        onRangeChanged(buildPayloadObject(range));
    }
  };

  dropdown.querySelectorAll(".period-item:not(.custom-toggle)").forEach(item => {
    item.onclick = () => {
      const key = item.getAttribute("data-key");
      const range = getPeriodRange(key);
      archiveSelect.value = "";
      rangeBox.classList.add("hidden");
      updatePeriod(item.textContent, range);
    };
  });

  archiveSelect.onchange = () => {
    const key = archiveSelect.value;
    if (!key) return;
    const range = getPeriodRange(key);
    rangeBox.classList.add("hidden");
    updatePeriod(`Jahr ${key.split("_")[1]}`, range);
  };

  customToggle.onclick = () => {
    rangeBox.classList.toggle("hidden");
  };

  applyBtn.onclick = () => {
    const fromVal = fromInput.value;
    const toVal = toInput.value;
    if (!fromVal || !toVal) return;

    localStorage.setItem("dash_custom_from", fromVal);
    localStorage.setItem("dash_custom_to", toVal);

    const range = { from: `${fromVal}T00:00:00`, to: `${toVal}T23:59:59` };
    archiveSelect.value = "";
    updatePeriod("Individuell", range);
  };

  compareToggle.onchange = () => {
    const active = compareToggle.checked;
    setCompareActive(active);

    if (onRangeChanged) {
        onRangeChanged(buildPayloadObject(activeRange));
    }
  };

  setCurrentRange(activeRange, selectedLabel);
  setCompareActive(savedCompare);

  if (onRangeChanged) {
     onRangeChanged(buildPayloadObject(activeRange));
  }
}
