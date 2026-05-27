/**
 * Live Sensoren Komponente
 * Zeigt aktuelle Sensorwerte mit erweiterten Attributen:
 * Watt, CO₂, Kosten, Prognosen, Energieklasse, Model, Devices, Status
 */

// Absoluter Pfad — funktioniert auch hinter nginx/reverse-proxy
const API_URL = 'api/dashboard2/live/sensors';
const grid = document.getElementById('sensors-grid');
const refreshInfo = document.getElementById('sensors-refresh');

// Icon-Map für Geräte-Typen
const ICON_MAP = {
  licht: '💡', light: '💡', steckdosen: '🔌', netzteil: '🔋',
  kuehlschrank: '🧊', fridge: '🧊', tiefkuehltruhe: '❄️',
  geschirrspueler: '🍽️', spuelmaschine: '🍽️', kueche: '🍳', kuechenmoebel: '🪑',
  herd: '🔥', ofen: '🔥', backofen: '🔥', heizung: '♨️',
  heizungsgeraet: '♨️', heizungspumpe: '♨️', boiler: '🚿',
  pumpe: '💧', abwasserpumpe: '💧', dampfdusche: '🚿',
  waschmaschine: '🧺', trockner: '♨️',
  server: '🖥️', rechner: '🖥️', tv: '📺', soundanlage: '🔊',
  telefonanlage: '☎️', wlan: '📶', piko_wechselrichter: '🔆',
  wohnzimmer: '🛋️', schlafzimmer: '🛏️', kinderzimmer_1: '🧸', kinderzimmer_2: '🧸',
  fitnessraum: '🏋️', garage: '🚗', gang: '🚪', vorratsraum: '📦',
  wc: '🚽', bad: '🛁', rolladen: '🪟', zaehlerschrank: '⚡', reserve: '⭕'
};

const KLASSE_FARBEN = {
  A: '#009640', B: '#4cb123', C: '#c3d100',
  D: '#ffcc00', E: '#ff9900', F: '#ff3300', G: '#d3001e'
};

function getIcon(sensor) {
  const name = (sensor.name || '').toLowerCase()
    .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss');
  const devices = sensor.devices || [];

  // Zuerst nach Geräten suchen
  for (const dev of devices) {
    const key = dev.toLowerCase();
    if (ICON_MAP[key]) return ICON_MAP[key];
  }
  // Dann nach Name
  for (const [key, icon] of Object.entries(ICON_MAP)) {
    if (name.includes(key)) return icon;
  }
  return '⚡';
}

export async function initSensors() {
  await refreshSensors();
}

export async function refreshSensors() {
  try {
    const res = await fetch(API_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderSensors(data.sensors, data.mode);
    refreshInfo.textContent = `${data.count} Sensoren • ${data.mode || 'POST'} • ${formatTime(data.timestamp)}`;
  } catch (err) {
    grid.innerHTML = `<p style="color:var(--text-muted)">Fehler beim Laden: ${err.message}</p>`;
  }
}

function renderSensors(sensors, mode) {
  if (!sensors || sensors.length === 0) {
    grid.innerHTML = '<p style="color:var(--text-muted)">Keine Sensordaten vorhanden.</p>';
    return;
  }

  // Gruppiere nach area_id
  const byArea = {};
  sensors.forEach(s => {
    const areaId = s.area_id || 'unknown';
    if (!byArea[areaId]) {
      byArea[areaId] = { name: s.area || 'Unbekannt', sensors: [] };
    }
    byArea[areaId].sensors.push(s);
  });

  // Sortiere Areas
  const areaOrder = ['EG', 'WG', 'OG', 'DG', 'OS', 'NU'];
  const sortedAreas = Object.keys(byArea).sort((a, b) => {
    const idxA = areaOrder.indexOf(a);
    const idxB = areaOrder.indexOf(b);
    if (idxA === -1 && idxB === -1) return a.localeCompare(b);
    if (idxA === -1) return 1;
    if (idxB === -1) return -1;
    return idxA - idxB;
  });

  // Render
  grid.innerHTML = sortedAreas.map(areaId => {
    const area = byArea[areaId];
    const sensorCards = area.sensors.map(s => renderCard(s, mode)).join('');

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

function renderCard(s, mode) {
  const icon = getIcon(s);
  const isGET = mode === 'GET';

  // Status Badge
  const isOnline = s.online !== undefined ? s.online : true;
  const statusBadge = isOnline
    ? '<span class="badge-online">ONLINE</span>'
    : '<span class="badge-off">OFFLINE</span>';

  // Energieklasse
  const klasse = s.energieklasse || 'A';
  const klasseColor = KLASSE_FARBEN[klasse] || '#777';

  // Geräte
  const devices = (s.devices || []).map(d => d.charAt(0).toUpperCase() + d.slice(1)).join(', ');

  // Watt-Anzeige
  const watt = s.watt !== undefined ? s.watt : 0;
  const wattClass = watt > 0 ? 'watt-active' : 'watt-idle';

  // Erweiterte Karte im GET-Modus
  if (isGET) {
    return `
      <div class="sensor-card">
        <div class="sensor-card-header">
          <div>
            <div class="sensor-card-id">${icon} ${s.id} ${statusBadge}</div>
            <div class="sensor-card-name">${s.name}</div>
            <div class="sensor-card-room">${s.room}</div>
          </div>
          <div class="sensor-watt ${wattClass}">${watt} W</div>
        </div>

        <div class="sensor-card-details">
          <div class="detail-row">
            <span class="detail-label">Geräte</span>
            <span class="detail-value">${devices || '—'}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Energieklasse</span>
            <span class="energieklasse-badge" style="background-color:${klasseColor}">${klasse}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Verbrauch</span>
            <span class="detail-value">${(s.delta || 0).toFixed(3)} kWh</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Kosten</span>
            <span class="detail-value">${(s.kosten || 0).toFixed(3)} €</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">CO₂</span>
            <span class="detail-value">${(s.co2 || 0).toFixed(1)} g</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Prognose Tag</span>
            <span class="detail-value">${(s.prognose_tag || 0).toFixed(2)} €</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Prognose Jahr</span>
            <span class="detail-value">${(s.prognose_jahr || 0).toFixed(2)} €</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Model</span>
            <span class="detail-value">${s.model || '—'}</span>
          </div>
        </div>
      </div>
    `;
  }

  // Einfache Karte im POST-Modus (Legacy)
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
          <span class="sensor-val-number ${s.delta > 0 ? 'delta-positive' : 'delta-zero'}">${s.delta.toFixed(4)}</span>
        </div>
      </div>
    </div>
  `;
}

function formatTime(ts) {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
