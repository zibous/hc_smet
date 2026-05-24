import { $, state, tc, gc } from './constants.js';

export function applyBgColor(c) {
  if (c) {
    document.documentElement.style.setProperty('--bg', c);
    localStorage.setItem('dash_bg', c);
    $('#bgColor').value = c;
  } else {
    document.documentElement.style.removeProperty('--bg');
    localStorage.removeItem('dash_bg');
  }
}

export function applyChartDefaults() {
  if (typeof Chart !== 'undefined') {
    Chart.defaults.color = tc();
    Chart.defaults.borderColor = gc();
  }
}

export function setTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('theme', t);
  $('#thBtn').textContent = t === 'dark' ? '\u2600' : '\u263E';
  applyChartDefaults();

  const bg = localStorage.getItem('dash_bg');
  if (bg) applyBgColor(bg);

  // Trigger Rerender falls Platzhalterfunktionen im Hauptskript definiert sind
  if (state.lastData && window.triggerRender) {
    window.triggerRender();
  }
}

export function initTheme() {
  $('#bgColor').oninput = function() { applyBgColor(this.value); };
  $('#bgReset').onclick = () => {
    applyBgColor(null);
    $('#bgColor').value = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();
  };

  const savedBg = localStorage.getItem('dash_bg');
  if (savedBg) applyBgColor(savedBg);

  $('#thBtn').onclick = () => setTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
  setTheme(localStorage.getItem('theme') || (matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light'));
}
