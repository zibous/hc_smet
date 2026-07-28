/**
 * Live Dashboard - Entry Point
 * Steuert Tabs und initialisiert die Komponenten
 */

import { refreshAnalytics } from './analytics.js';
import { refreshHourly } from './hourly.js';
import { refreshSensors } from './sensors.js';

// =================================================================
// HILFSFUNKTION: Header-Timestamp aktualisieren
// =================================================================
function updateHeaderTimestamp() {
  const el = document.getElementById('header-update');
  if (!el) return;
  const now = new Date();
  const dateStr = now.toLocaleDateString('sv-SE');
  const timeStr = now.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  el.textContent = `${dateStr} um ${timeStr} Uhr`;
}

// =================================================================
// TAB NAVIGATION
// =================================================================
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

let activeTab = localStorage.getItem('liveTab') || 'sensors';

tabButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    activateTab(tab);
  });
});

function activateTab(tab) {
  activeTab = tab;
  localStorage.setItem('liveTab', tab);

  tabButtons.forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  tabContents.forEach(c => c.classList.toggle('active', c.id === `tab-${tab}`));

  // Daten laden beim Tab-Wechsel
  if (tab === 'sensors') refreshSensors();
  if (tab === 'hourly') refreshHourly();
  if (tab === 'analytics') refreshAnalytics();
}

// =================================================================
// INIT
// =================================================================
async function init() {
  activateTab(activeTab);
}

// Auto-Refresh alle 30 Sekunden für den aktiven Tab
setInterval(() => {
  if (activeTab === 'sensors') refreshSensors();
  if (activeTab === 'hourly') refreshHourly();
  updateHeaderTimestamp();
}, 30000);

init();
updateHeaderTimestamp();
