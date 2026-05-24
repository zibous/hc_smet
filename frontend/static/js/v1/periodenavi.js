/* ----------------------------------------------------
   PERIODEN-NAVIGATION (eine Zeile)
---------------------------------------------------- */

let stylesInjected = false;

/* ----------------------------------------------------
   STYLES
---------------------------------------------------- */
function injectStyles() {
  if (stylesInjected) return;

  const style = document.createElement("style");
  style.innerHTML = `
    .period-nav {
        display: flex;
        align-items: center;
        border-radius: 0.8rem;
        overflow: hidden;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        backdrop-filter: blur(14px);
    }
    .period-nav button {
        background: transparent;
        border: none;
        color: #fff;
        padding: 0.8rem 1.4rem;
        cursor: pointer;
        font-size: 1.1rem;
        transition: 0.2s ease;
    }
    .period-nav button:hover {
        background: rgba(255,255,255,0.12);
    }
    .period-label {
        padding: 0.8rem 2rem;
        font-weight: 600;
        font-size: 1.5rem;
        color: #fff;
        text-align: center;
        min-width: 160px;
        border-left: 1px solid rgba(255,255,255,0.15);
        border-right: 1px solid rgba(255,255,255,0.15);
    }
    .btn {
        padding: 0.8rem 1.8rem;
        border: none;
        border-radius: 1.4rem;
        cursor: pointer;
        color: white;
        background: #3b82f6;
        transition: .25s ease;
    }
    .btn:hover {
        background: #60a5fa;
        transform: translateY(-1px);
    }
    .toggle {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        cursor: pointer;
    }
    .toggle input {
        display: none;
    }
    .slider {
        position: relative;
        width: 4.6rem;
        height: 2.6rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.25);
        transition: .25s ease;
    }
    .slider::before {
        content: "";
        position: absolute;
        top: 0.2rem;
        left: 0.2rem;
        width: 2.2rem;
        height: 2.2rem;
        border-radius: 50%;
        background: white;
        transition: .25s ease;
    }
    .toggle input:checked + .slider {
        background: #3b82f6;
    }
    .toggle input:checked + .slider::before {
        transform: translateX(2rem);
    }
  `;
  document.head.appendChild(style);
  stylesInjected = true;
}

/* ----------------------------------------------------
   PERIODEN MIT RANGE-FUNKTIONEN
---------------------------------------------------- */
const PERIODS = [
  {
    label: "Heute",
    range: () => {
      const now = new Date();
      const start = new Date(now);
      start.setHours(0, 0, 0, 0);
      return { from: start, to: now };
    }
  },
  {
    label: "Gestern",
    range: () => {
      const now = new Date();
      const end = new Date(now);
      end.setHours(0, 0, 0, 0);
      const start = new Date(end);
      start.setDate(start.getDate() - 1);
      return { from: start, to: end };
    }
  },
  {
    label: "Diese Woche",
    range: () => {
      const now = new Date();
      const start = new Date(now);
      start.setDate(now.getDate() - now.getDay() + 1);
      start.setHours(0, 0, 0, 0);
      return { from: start, to: now };
    }
  },
  {
    label: "Letzte Woche",
    range: () => {
      const now = new Date();
      const mondayThisWeek = new Date(now);
      mondayThisWeek.setDate(now.getDate() - now.getDay() + 1);
      mondayThisWeek.setHours(0, 0, 0, 0);

      const end = new Date(mondayThisWeek);
      end.setDate(end.getDate() - 1);
      end.setHours(23, 59, 59, 999);

      const start = new Date(end);
      start.setDate(start.getDate() - 6);
      start.setHours(0, 0, 0, 0);

      return { from: start, to: end };
    }
  },
  {
    label: "Dieser Monat",
    range: () => {
      const now = new Date();
      const start = new Date(now.getFullYear(), now.getMonth(), 1);
      return { from: start, to: now };
    }
  },
  {
    label: "Letzter Monat",
    range: () => {
      const now = new Date();
      const firstThisMonth = new Date(now.getFullYear(), now.getMonth(), 1);
      const end = new Date(firstThisMonth - 1);
      const start = new Date(end.getFullYear(), end.getMonth(), 1);
      return { from: start, to: end };
    }
  }
];

let index = 0;

/* ----------------------------------------------------
   RENDER
---------------------------------------------------- */
export function renderPeriodStrip(onChange) {
  injectStyles();

  const controls = document.querySelector(".controls");
  controls.innerHTML = "";

  const strip = document.createElement("div");
  strip.className = "period-nav";

  const btnPrev = document.createElement("button");
  btnPrev.textContent = "◀";

  const label = document.createElement("div");
  label.className = "period-label";
  label.textContent = PERIODS[index].label;

  const btnNext = document.createElement("button");
  btnNext.textContent = "▶";

  strip.appendChild(btnPrev);
  strip.appendChild(label);
  strip.appendChild(btnNext);

  const toggle = document.createElement("label");
  toggle.className = "toggle";
  toggle.innerHTML = `
    <input type="checkbox" id="compareToggle" checked>
    <span class="slider"></span>
    <span class="label">Vergleich</span>
  `;

  const apply = document.createElement("button");
  apply.id = "applyBtn";
  apply.className = "btn";
  apply.textContent = "Apply";

  function getCompare() {
    return document.getElementById("compareToggle").checked;
  }

  function update() {
    label.textContent = PERIODS[index].label;

    const { from, to } = PERIODS[index].range();

    onChange?.({
      from: from.toISOString(),
      to: to.toISOString(),
      compare: getCompare(),
    });
  }

  btnPrev.addEventListener("click", () => {
    index = (index - 1 + PERIODS.length) % PERIODS.length;
    update();
  });

  btnNext.addEventListener("click", () => {
    index = (index + 1) % PERIODS.length;
    update();
  });

  toggle.addEventListener("change", update);
  apply.addEventListener("click", update);

  controls.appendChild(strip);
  controls.appendChild(toggle);
  controls.appendChild(apply);

  update();
}
