import { $, gc, tc } from './constants.js';
import { activeCharts, destroyChart } from './charts-base.js';

/**
 * Zeichnet das Basis-Gewichtsdiagramm (c1)
 */
export function renderWeightChart(data) {
  destroyChart('c1');
  const ctx = $('#c1')?.getContext('2d');
  if (!ctx || !data || data.length === 0) return;

  activeCharts['c1'] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.date),
      datasets: [{
        label: 'Gewicht (kg)',
        data: data.map(d => d.weight),
        borderColor: '#4361ee',
        tension: 0.2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { type: 'time', grid: { color: gc() } },
        y: { grid: { color: gc() } }
      }
    }
  });
}

/**
 * Zeichnet die Zusammenfassung (c2) mit Multi-Achsen
 */
export function renderSummaryChart(data) {
  destroyChart('c2');
  const ctx = $('#c2')?.getContext('2d');
  if (!ctx || !data || data.length === 0) return;

  activeCharts['c2'] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.date),
      datasets: [
        { label: 'Gewicht (kg)', data: data.map(d => d.weight), borderColor: '#4361ee', backgroundColor: 'rgba(66, 97, 238, 0.1)', yAxisID: 'yKg', tension: 0.15, fill: true },
        { label: 'Muskelmasse (kg)', data: data.map(d => d.muscle), borderColor: '#2ec4b6', yAxisID: 'yKg', tension: 0.15 },
        { label: 'BMI', data: data.map(d => d.bmi), borderColor: '#f4a261', borderDash: [5, 5], yAxisID: 'yBmi', tension: 0.1 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { type: 'time', grid: { color: gc() } },
        yKg: { type: 'linear', position: 'left', grid: { color: gc() }, title: { display: true, text: 'Masse (kg)', color: tc() } },
        yBmi: { type: 'linear', position: 'right', grid: { drawOnChartArea: false }, title: { display: true, text: 'BMI Wert', color: tc() } }
      }
    }
  });

  const latest = data[data.length - 1];
  $('#s2').innerHTML = `<span>Aktuell: <span class="sl">${latest.weight?.toFixed(1)} kg</span></span> <span>BMI: <span class="sl">${latest.bmi?.toFixed(1)}</span></span>`;
}

/**
 * Zeichnet die normalisierten Trends (c5) im Verhältnis zum ersten Tag (100%)
 */
export function renderNormalizedChart(data) {
  destroyChart('c5');
  const ctx = $('#c5')?.getContext('2d');
  if (!ctx || !data || data.length === 0) return;

  const base = data[0];
  const calcPct = (current, baseVal) => baseVal ? (current / baseVal) * 100 : 100;

  activeCharts['c5'] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.date),
      datasets: [
        { label: 'Körperfett % (relativ)', data: data.map(d => calcPct(d.fat, base.fat)), borderColor: '#e63946', tension: 0.2 },
        { label: 'Muskeln % (relativ)', data: data.map(d => calcPct(d.muscle, base.muscle)), borderColor: '#2ec4b6', tension: 0.2 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { type: 'time', grid: { color: gc() } },
        y: {
          grid: { color: gc() },
          ticks: { callback: (value) => `${value - 100 > 0 ? '+' : ''}${(value - 100).toFixed(1)}%` }
        }
      }
    }
  });

  $('#s5').innerHTML = `<span>Basis: <span class="sl">${new Date(base.date).toLocaleDateString('de-DE')}</span></span>`;
}
