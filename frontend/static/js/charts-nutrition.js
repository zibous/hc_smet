import { $, gc } from './constants.js';
import { activeCharts, destroyChart } from './charts-base.js';

/**
 * Zeichnet die Nährstoff- / kcal-Verteilung (c6)
 */
export function renderNutritionChart(data) {
  destroyChart('c6');
  const ctx = $('#c6')?.getContext('2d');
  if (!ctx || !data || data.length === 0) return;

  activeCharts['c6'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.date),
      datasets: [{ label: 'Energie (kcal)', data: data.map(d => d.kcal), backgroundColor: '#f4a261' }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { x: { type: 'time', grid: { color: gc() } }, y: { grid: { color: gc() } } }
    }
  });
}

/**
 * Zeichnet die Veränderung im Vergleich zur Vorperiode (c7)
 */
export function renderDeltaChart(data, prevData) {
  destroyChart('c7');
  const ctx = $('#c7')?.getContext('2d');
  if (!ctx || !data || prevData.length === 0) return;

  // Berechnung des Durchschnitts-Gewichtsunterschieds der beiden Zeiträume
  const avgCurrent = data.reduce((acc, d) => acc + (d.weight || 0), 0) / data.length;
  const avgPrev = prevData.reduce((acc, d) => acc + (d.weight || 0), 0) / prevData.length;
  const delta = avgCurrent - avgPrev;

  activeCharts['c7'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Gewichts-Delta zur Vorperiode'],
      datasets: [{
        label: 'Differenz (kg)',
        data: [delta],
        backgroundColor: delta > 0 ? '#e63946' : '#2ec4b6'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { grid: { color: gc() } } }
    }
  });

  $('#s7').innerHTML = `<span>Veränderung: <span class="sl ${delta > 0 ? 'up' : 'dn'}">${delta > 0 ? '+' : ''}${delta.toFixed(2)} kg</span> im Vergleich zum vorherigen Zeitraum</span>`;
}
