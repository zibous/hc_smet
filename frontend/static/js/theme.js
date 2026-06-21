import { state, tc, gc } from './constants.js';

export function applyChartDefaults() {
  if (typeof Chart !== 'undefined') {
    Chart.defaults.color = tc();
    Chart.defaults.borderColor = gc();
  }
}

export function setTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('theme', t);

  // Synchronisation für alle Dashboards im Projekt
  localStorage.setItem('health-theme', t);

  // Aktualisiert das Element im Footer
  const footerBtn = document.getElementById('themeToggleFooter');
  if (footerBtn) {
    footerBtn.innerHTML = t === 'dark' ? '☀️ Helles Design' : '🌙 Dunkles Design';
  }

  applyChartDefaults();

  // Trigger Rerender falls Platzhalterfunktionen im Hauptskript definiert sind
  if (state.lastData && window.triggerRender) {
    window.triggerRender();
  }
}

export function initTheme() {
  // Globaler Klick-Abfänger für den neuen Footer-Link
  document.addEventListener('click', (event) => {
    if (event.target && event.target.id === 'themeToggleFooter') {
      const currentTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      setTheme(currentTheme);
    }
  });

  // Theme initial setzen (Prüft 'theme', 'health-theme' oder System-Präferenz)
  const defaultTheme = localStorage.getItem('theme') || localStorage.getItem('health-theme') || (matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light');
  setTheme(defaultTheme);
}
