/**
 * Live Sensoren Komponente
 * Zeigt aktuelle Sensorwerte aus dem RAM-Speicher
 */

const API_URL = '../api/dashboard2/live/sensors';
const grid = document.getElementById('sensors-grid');
const refreshInfo = document.getElementById('sensors-refresh');

export async function initSensors() {
  await refreshSensors();
}

export async function refreshSensors() {
  try {
    const res = await fetch(API_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderSensors(data.sensors);
    refreshInfo.textContent = `${data.count} Sensoren • ${formatTime(data.timestamp)}`;
  } catch (err) {
    grid.innerHTML = `<p style="color:var(--text-muted)">Fehler beim Laden: ${err.message}</p>`;
  }
}

function renderSensors(sensors) {
  if (!sensors || sensors.length === 0) {
    grid.innerHTML = '<p style="color:var(--text-muted)">Keine Sensordaten vorhanden.</p>';
    return;
  }

  // Gruppiere nach area_id
  const byArea = {};
  sensors.forEach(s => {
    const areaId = s.area_id || 'unknown';
    if (!byArea[areaId]) {
      byArea[areaId] = {
        name: s.area || 'Unbekannt',
        sensors: []
      };
    }
    byArea[areaId].sensors.push(s);
  });

  // Sortiere Areas (EG, WG, OG, DG, OS, NU)
  const areaOrder = ['EG', 'WG', 'OG', 'DG', 'OS', 'NU'];
  const sortedAreas = Object.keys(byArea).sort((a, b) => {
    const idxA = areaOrder.indexOf(a);
    const idxB = areaOrder.indexOf(b);
    if (idxA === -1 && idxB === -1) return a.localeCompare(b);
    if (idxA === -1) return 1;
    if (idxB === -1) return -1;
    return idxA - idxB;
  });

  // Render gruppiert
  grid.innerHTML = sortedAreas.map(areaId => {
    const area = byArea[areaId];
    const sensorCards = area.sensors.map(s => {
      const deltaClass = s.delta > 0 ? 'delta-positive' : 'delta-zero';
      const age = Math.round((Date.now() / 1000) - s.timestamp);
      const ageStr = age < 60 ? `${age}s` : `${Math.round(age / 60)}m`;

      return `
        <div class="sensor-card">
          <div class="sensor-card-header">
            <div>
              <div class="sensor-card-id">${s.id}</div>
              <div class="sensor-card-name">${s.name}</div>
              <div class="sensor-card-room">${s.room}</div>
            </div>
            <div class="sensor-card-id" title="Alter">${ageStr}</div>
          </div>
          <div class="sensor-card-values">
            <div class="sensor-val">
              <span class="sensor-val-label">Aktuell</span>
              <span class="sensor-val-number">${s.current.toFixed(2)}</span>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">Letzter</span>
              <span class="sensor-val-number">${s.last.toFixed(2)}</span>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">Delta</span>
              <span class="sensor-val-number ${deltaClass}">${s.delta.toFixed(4)}</span>
            </div>
          </div>
        </div>
      `;
    }).join('');

    return `
      <div class="area-group">
        <h3 class="area-group-title">${area.name} <span style="opacity:0.6;font-size:0.85em">(${area.sensors.length})</span></h3>
        <div class="sensor-grid">
          ${sensorCards}
        </div>
      </div>
    `;
  }).join('');
}

function formatTime(ts) {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
