/**
 * Analytics Komponente
 * Zeigt Cluster-Profile und Lastanalyse der Sensoren
 */

const API_URL = 'api/dashboard2/analytics';
const grid = document.getElementById('analytics-grid');
const refreshInfo = document.getElementById('analytics-refresh');

let loaded = false;

export async function initAnalytics() {
  // Lazy
}

export async function refreshAnalytics() {
  try {
    const res = await fetch(API_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderAnalytics(data.sensors);
    refreshInfo.textContent = `${data.count} Profile • ${formatTime(data.timestamp)}`;
    loaded = true;
  } catch (err) {
    grid.innerHTML = `<p style="color:var(--text-muted)">Fehler: ${err.message}</p>`;
  }
}

function renderAnalytics(sensors) {
  if (!sensors || sensors.length === 0) {
    grid.innerHTML = '<p style="color:var(--text-muted)">Keine Analytics-Daten vorhanden. Wurde der Analytics-Daemon bereits ausgeführt?</p>';
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
      const clusterClass = getClusterClass(s.cluster);
      const loadPct = (s.load_factor * 100).toFixed(1);

      return `
        <div class="sensor-card">
          <div class="sensor-card-header">
            <div>
              <div class="sensor-card-id">${s.id}</div>
              <div class="sensor-card-name">${s.name}</div>
              <div class="sensor-card-room">${s.room}</div>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">Samples</span>
              <span class="sensor-val-number">${s.samples}</span>
            </div>
          </div>
          <span class="cluster-badge ${clusterClass}">Energieverbrauch ${s.cluster}</span>
          <div class="sensor-card-values" style="margin-top:1.2rem;">
            <div class="sensor-val">
              <span class="sensor-val-label">Total kWh</span>
              <span class="sensor-val-number">${s.total.toFixed(1)}</span>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">Grundlast</span>
              <span class="sensor-val-number">${s.base.toFixed(1)}</span>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">Spitze</span>
              <span class="sensor-val-number">${s.peak.toFixed(1)}</span>
            </div>
          </div>
          <div class="sensor-card-values">
            <div class="sensor-val">
              <span class="sensor-val-label">Ø kWh/h</span>
              <span class="sensor-val-number">${s.average.toFixed(3)}</span>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">Load Factor</span>
              <span class="sensor-val-number">${loadPct}%</span>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">&nbsp;</span>
              <span class="sensor-val-number">&nbsp;</span>
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

function getClusterClass(cluster) {
  if (!cluster) return 'cluster-standard';
  const lower = cluster.toLowerCase();
  if (lower.includes('hoch')) return 'cluster-peak';
  if (lower.includes('niedrig')) return 'cluster-base';
  return 'cluster-standard';
}

function formatTime(ts) {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
