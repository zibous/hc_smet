import { $, state } from './constants.js';
import { initTheme, applyChartDefaults } from './theme.js';
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
  const userId = $('#uSel').value;

  // Abbrechen, falls noch kein Benutzer geladen/ausgewählt wurde
  if (!userId) {
    console.warn("⚠️ loadDashboard abgebrochen: Keine user_id vorhanden.");
    return;
  }

  $('#loadBox').style.display = 'block';
  $('#content').style.display = 'none';

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

  // 1. Benutzer laden
  const users = await fetchUsers();
  const uSel = $('#uSel');

  if (uSel && users && users.length > 0) {
    // Dropdown befüllen
    uSel.innerHTML = users.map(u => `<option value="${u.id || u.name}">${u.name}</option>`).join('');
    uSel.addEventListener('change', loadDashboard);

    // 2. Erst wenn Benutzer da sind, den Datumsbereich und das Dashboard triggern
    setDateRange(30);
  } else {
    if (uSel) uSel.innerHTML = '<option value="">Keine Benutzer gefunden</option>';
    $('#loadBox').textContent = 'Konnte keine Benutzer vom Server laden. Bitte Backend prüfen.';
    $('#loadBox').style.display = 'block';
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
    if (state.lastData) {
      exportToCSV(state.lastData, `gewichtsexport_${$('#uSel').value}.csv`);
    }
  });
});

/**
 * Holt die Benutzerliste vom FastAPI-Backend
 */
async function fetchUsers() {
  try {
    const response = await fetch('/api/appstatus');
    if (!response.ok) throw new Error(`HTTP Fehler! Status: ${response.status}`);

    const data = await response.json();
    console.log("📥 Empfangene User-Daten:", data);

    // Flexibel auswerten: Falls Objekt mit .users-Attribut, sonst reines Array, sonst leere Liste
    if (data && data.users) return data.users;
    if (Array.isArray(data)) return data;
    return [];
  } catch (error) {
    console.error('❌ Fehler beim Laden der Benutzer:', error);
    return [];
  }
}

/**
 * Holt die Dashboard-Daten für einen spezifischen Benutzer und Zeitraum
 */
async function fetchDashboardData(userId, fromDate, toDate) {
  try {
    let url = `/api/dashboard?user_id=${userId}`;
    if (fromDate) url += `&from=${fromDate}`;
    if (toDate) url += `&to=${toDate}`;

    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP Fehler! Status: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('❌ Fehler beim Laden der Dashboard-Daten:', error);
    return null;
  }
}

/**
 * Exportiert die aktuellen Tabellendaten als CSV-Datei
 */
function exportToCSV(data, filename) {
  if (!data || data.length === 0) return;

  const headers = Object.keys(data[0]).join(',');
  const rows = data.map(row =>
    Object.values(row).map(val => `"${String(val).replace(/"/g, '""')}"`).join(',')
  );

  const csvContent = 'data:text/csv;charset=utf-8,\uFEFF' + [headers, ...rows].join('\n');
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export { fetchUsers, fetchDashboardData, exportToCSV };

// ─── App Info ───────────────────────────────────────────

console.info(
  '%c ⚡ BodyScale Dashboard %c ESM v1.2.0 ',
  'color:#fff;background:#e94560;padding:4px 8px;border-radius:4px 0 0 4px;font-size:11px',
  'color:#1a1a2e;background:#a8dadc;padding:4px 8px;border-radius:0 4px 4px 0;font-size:11px'
);
