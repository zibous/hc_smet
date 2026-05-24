import { $, state } from './constants.js';
import { initTheme, applyChartDefaults } from './theme.js';
import { fetchUsers, fetchDashboardData, exportToCSV } from './api.js';
import { renderInfoBar, renderCards, renderAllCharts } from './charts.js';

// Verknüpfung für das Theme-Modul, um bei Theme-Wechsel Diagramme neu zu zeichnen
window.triggerRender = () => {
  if (state.lastData) {
    applyChartDefaults();
    renderCards(state.lastData);
    renderAllCharts(state.lastData, state.lastPrev);
  }
};

/**
 * Setzt die Datumsfelder anhand der vordefinierten Tage (30d, 90d, etc.)
 */
function setDateRange(days) {
  const to = new Date();
  const from = new Date();
  from.setDate(to.getDate() - days);

  $('#dTo').value = to.toISOString().split('T')[0];
  $('#dFrom').value = from.toISOString().split('T')[0];
  loadDashboard();
}

/**
 * Holt die aktuellen Filterwerte und lädt die Ansicht neu
 */
async function loadDashboard() {
  $('#loadBox').style.display = 'block';
  $('#content').style.display = 'none';

  const userId = $('#uSel').value;
  const fromDate = $('#dFrom').value;
  const toDate = $('#dTo').value;

  const data = await fetchDashboardData(userId, fromDate, toDate);

  if (data) {
    state.lastData = data.current || [];
    state.lastPrev = data.previous || [];
    state.curSex = data.user?.sex || 'male';
    state.curTarget = data.user?.target || 70;

    renderInfoBar(data.user);
    renderCards(state.lastData);
    renderAllCharts(state.lastData, state.lastPrev);

    $('#loadBox').style.display = 'none';
    $('#content').style.display = 'block';
  } else {
    $('#loadBox').textContent = 'Fehler beim Laden der Daten.';
  }
}

// Haupt-Initialisierung beim Laden der Seite
document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  applyChartDefaults();

  // Benutzer dropdown befüllen
  const users = await fetchUsers();
  const uSel = $('#uSel');
  if (uSel) {
    uSel.innerHTML = users.map(u => `<option value="${u.id}">${u.name}</option>`).join('');
    uSel.addEventListener('change', loadDashboard);
  }

  // Zeitbereichs-Buttons Event Listener
  $('#p30')?.addEventListener('click', () => setDateRange(30));
  $('#p90')?.addEventListener('click', () => setDateRange(90));
  $('#p365')?.addEventListener('click', () => setDateRange(365));
  $('#pAll')?.addEventListener('click', () => {
    $('#dFrom').value = '';
    $('#dTo').value = '';
    loadDashboard();
  });

  $('#goBtn')?.addEventListener('click', loadDashboard);

  $('#csvBtn')?.addEventListener('click', () => {
    exportToCSV(state.lastData, `gewichtsexport_${$('#uSel').value}.csv`);
  });

  // Standardmäßig die letzten 30 Tage laden
  setDateRange(30);
});

// ─── App Info ───────────────────────────────────────────

console.info(
  '%c ⚡ BodyScale Dashboard %c ESM v1.2.0 ',
  'color:#fff;background:#e94560;padding:4px 8px;border-radius:4px 0 0 4px;font-size:11px',
  'color:#1a1a2e;background:#a8dadc;padding:4px 8px;border-radius:0 4px 4px 0;font-size:11px'
);
