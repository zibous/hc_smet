import { $, state } from './constants.js';

// Zentraler, modulübergreifender Speicher für aktive Chart-Instanzen
export const activeCharts = {};

/**
 * Zerstört ein existierendes Chart, falls vorhanden
 */
export function destroyChart(id) {
  if (activeCharts[id]) {
    activeCharts[id].destroy();
    delete activeCharts[id];
  }
}

/**
 * Aktualisiert die Info-Bar (Avatar und Text) oben
 */
export function renderInfoBar(user) {
  if (!user) return;
  const avatarEl = $('#avatar');
  const infoEl = $('#infoText');

  if (avatarEl) avatarEl.src = user.avatar || 'https://placeholder.com';
  if (infoEl) infoEl.innerHTML = `<strong>${user.name}</strong> &bull; Ziel: ${user.target || state.curTarget}kg &bull; ${user.sex === 'female' ? 'Weiblich' : 'Männlich'}`;
}

/**
 * Erstellt die kleinen Info-Karten (BMI, Fett etc.)
 */
export function renderCards(data) {
  const container = $('#cards');
  if (!container || !data || data.length === 0) return;

  const latest = data[data.length - 1];

  container.innerHTML = `
    <div class="card good">
      <div class="lb">Gewicht</div>
      <div class="vl">${latest.weight?.toFixed(1) || '--'}</div>
      <div class="un">kg</div>
    </div>
    <div class="card ok">
      <div class="lb">Körperfett</div>
      <div class="vl">${latest.fat?.toFixed(1) || '--'}</div>
      <div class="un">%</div>
    </div>
  `;
}
