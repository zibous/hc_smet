/**
 * Stundenwerte Komponente
 * Zeigt die letzten 24h als Chart und Tabelle
 */

const API_URL = 'api/dashboard2/hourly';
const chartCanvas = document.getElementById('hourlyChart');
const tableWrap = document.getElementById('hourly-table-wrap');
const refreshInfo = document.getElementById('hourly-refresh');

let chartInstance = null;
let loaded = false;

export async function initHourly() {
  // Lazy - wird erst bei Tab-Wechsel geladen
}

export async function refreshHourly() {
  try {
    const res = await fetch(API_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderChart(data.data);
    renderTable(data.data);
    refreshInfo.textContent = `${data.hours_count} Stunden • ${formatTime(data.timestamp)}`;
    loaded = true;
  } catch (err) {
    tableWrap.innerHTML = `<p style="color:var(--text-muted)">Fehler: ${err.message}</p>`;
  }
}

function renderChart(hourlyData) {
  if (!hourlyData || hourlyData.length === 0) return;

  // Chronologisch sortieren (älteste zuerst)
  const sorted = [...hourlyData].reverse();

  const labels = sorted.map(h => {
    const d = new Date(h.hour * 1000);
    return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  });

  const totals = sorted.map(h => h.total);

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const barColor = isDark ? 'rgba(56, 189, 248, 0.7)' : 'rgba(37, 99, 235, 0.7)';
  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
  const textColor = isDark ? '#94a3b8' : '#475569';

  if (chartInstance) {
    chartInstance.destroy();
  }

  chartInstance = new Chart(chartCanvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Verbrauch (kWh)',
        data: totals,
        backgroundColor: barColor,
        borderRadius: 4,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { size: 11 } }
        },
        y: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { size: 11 } },
          beginAtZero: true
        }
      }
    }
  });

  // Chart-Höhe setzen
  chartCanvas.parentElement.style.height = '280px';
}

function renderTable(hourlyData) {
  if (!hourlyData || hourlyData.length === 0) {
    tableWrap.innerHTML = '<p style="color:var(--text-muted)">Keine Stundenwerte vorhanden.</p>';
    return;
  }

  // API liefert bereits die letzten 24 Stunden (neueste zuerst)
  // Wir nehmen alle Daten die das API liefert
  const last24 = hourlyData;

  // Top-Sensoren ermitteln (die mit dem höchsten Gesamtverbrauch in diesen 24h)
  const sensorTotals = {};
  last24.forEach(h => {
    Object.entries(h.sensors).forEach(([id, val]) => {
      sensorTotals[id] = (sensorTotals[id] || 0) + val;
    });
  });

  // Top 10 Sensoren nach Gesamtverbrauch
  const topSensors = Object.entries(sensorTotals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([id]) => id);

  // Zeige Tabelle mit neuesten Einträgen zuerst (wie API liefert)
  const rows = last24.map(h => {
    const d = new Date(h.hour * 1000);
    const timeStr = d.toLocaleString('de-DE', {
      day: '2-digit', month: '2-digit',
      hour: '2-digit', minute: '2-digit'
    });

    const sensorCells = topSensors.map(id => {
      const val = h.sensors[id];
      return `<td>${val !== undefined ? val.toFixed(3) : '-'}</td>`;
    }).join('');

    return `<tr><td>${timeStr}</td><td><strong>${h.total.toFixed(3)}</strong></td>${sensorCells}</tr>`;
  }).join('');

  const headerCells = topSensors.map(id => `<th>${id}</th>`).join('');

  tableWrap.innerHTML = `
    <table class="hourly-table">
      <thead>
        <tr><th>Zeit</th><th>Gesamt</th>${headerCells}</tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function formatTime(ts) {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
