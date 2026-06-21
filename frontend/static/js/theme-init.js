// theme-init.js – Inline Theme-Logik (läuft vor DOM-ready)

document.getElementById('currentYear').textContent = new Date().getFullYear();

/* Background Color Picker */
function applyBg(c) {
  document.documentElement.style.setProperty('--bg', c);
  document.body.style.setProperty('background', c);
  var r = parseInt(c.slice(1, 3), 16), g = parseInt(c.slice(3, 5), 16), b = parseInt(c.slice(5, 7), 16);
  var s1 = '#' + [r, g, b].map(function (v) { return Math.min(255, v + 15).toString(16).padStart(2, '0'); }).join('');
  var s2 = '#' + [r, g, b].map(function (v) { return Math.min(255, v + 25).toString(16).padStart(2, '0'); }).join('');
  document.documentElement.style.setProperty('--surface', s1);
  document.documentElement.style.setProperty('--surface2', s2);
  localStorage.setItem('smet-bg', c);
  document.getElementById('bgReset').style.display = '';
}

function resetBg() {
  document.documentElement.style.removeProperty('--bg');
  document.documentElement.style.removeProperty('--surface');
  document.documentElement.style.removeProperty('--surface2');
  document.body.style.removeProperty('background');
  localStorage.removeItem('smet-bg');
  document.getElementById('bgReset').style.display = 'none';
}

(function () {
  var c = localStorage.getItem('smet-bg');
  if (c) {
    applyBg(c);
    document.addEventListener('DOMContentLoaded', function () {
      document.getElementById('bgReset').style.display = '';
    });
  }
})();

const btn = document.getElementById('themeToggle');
const icon = document.getElementById('themeIcon');
const text = document.getElementById('themeText');

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  if (theme === 'dark') {
    if (icon) icon.textContent = '🌙';    
  } else {
    if (icon) icon.textContent = '☀️';    
  }
  window.dispatchEvent(new CustomEvent('themeChanged', { detail: theme }));
}

const savedTheme = localStorage.getItem('theme');
const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

if (savedTheme) {
  setTheme(savedTheme);
} else if (systemPrefersDark) {
  setTheme('dark');
} else {
  setTheme('dark');
}

btn.addEventListener('click', () => {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  setTheme(newTheme);
});
