/**
 * Live Dashboard - Entry Point
 * Steuert Tabs und initialisiert die Komponenten
 */

import { initSensors, refreshSensors } from './sensors.js';
import { initHourly, refreshHourly } from './hourly.js';
import { initAnalytics, refreshAnalytics } from './analytics.js';

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
}, 30000);

init();
