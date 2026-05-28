import { $, state } from './constants.js';
// Importiere die schlanken Konfigurationen
import * as configs from './chart-configs.js';

// Speicher für aktive Chart-Instanzen, um sie vor dem Neuzeichnen zu zerstören
const activeCharts = {};

/**
 * Zerstört ein existierendes Chart, falls vorhanden
 */
function destroyChart(id) {
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
  const infoTextEl = $('#infoText');

  if (avatarEl) avatarEl.src = user.avatar || 'https://placeholder.com';
  if (infoTextEl) {
    infoTextEl.innerHTML = `<strong>${user.name}</strong> &bull; Ziel: ${user.target || state.curTarget}kg &bull; ${user.sex === 'female' ? 'Weiblich' : 'Männlich'}`;
  }
}

/**
 * Erstellt die kleinen Info-Karten (BMI, Fett etc.)
 */
export function renderCards(data) {
  const container = $('#cards');
  if (!container || !data) return;

  const latest = data[data.length - 1];
  if (!latest) return;

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

/**
 * Universelle Hilfsfunktion zum Erstellen der Diagramme
 */
function createChart(id, configFactory, data, extraData = null) {
  destroyChart(id);
  const ctx = $(`#${id}`)?.getContext('2d');
  if (!ctx || !data || data.length === 0) return;

  // Instanziiere das Chart mit der ausgelagerten Konfiguration
  activeCharts[id] = new Chart(ctx, configFactory(data, extraData));
}

/**
 * Master-Funktion zum Zeichnen aller Diagramme
 */
export function renderAllCharts(data, prevData) {
  // Alle 7 Diagramme (c1 bis c7) werden über die Hilfsmethode generiert
  createChart('c1', configs.getWeightConfig, data);
  createChart('c2', configs.getSummaryConfig, data);
  createChart('c3', configs.getFatVisceralConfig, data);
  createChart('c4', configs.getMuscleProteinConfig, data);
  createChart('c5', configs.getNormalizedConfig, data);
  createChart('c6', configs.getNutritionConfig, data);
  createChart('c7', configs.getDeltaConfig, data, prevData); // Reicht prevData als vierten Parameter weiter

  // Text-Zusammenfassungen (s1 bis s7) unter den Charts mit Werten befüllen
  const latest = data[data.length - 1];
  if (!latest) return;

  if ($('#s1')) $('#s1').innerHTML = `<span>Letzter Wert: <span class="sl">${latest.weight?.toFixed(1)} kg</span></span>`;
  if ($('#s2')) $('#s2').innerHTML = `<span>Gewicht: <span class="sl">${latest.weight?.toFixed(1)} kg</span> &bull; BMI: <span class="sl">${latest.bmi?.toFixed(1)}</span></span>`;
  if ($('#s3')) $('#s3').innerHTML = `<span>Fett: <span class="sl">${latest.fat?.toFixed(1)} %</span> &bull; Viszeralfett: <span class="sl">${latest.visceral || '--'}</span></span>`;
  if ($('#s4')) $('#s4').innerHTML = `<span>Muskeln: <span class="sl">${latest.muscle?.toFixed(1)} kg</span> &bull; Protein: <span class="sl">${latest.protein?.toFixed(1)} %</span></span>`;
  if ($('#s5')) $('#s5').innerHTML = `<span>Basis: 100% am ersten Tag des ausgewählten Zeitraums</span>`;
  if ($('#s6')) $('#s6').innerHTML = `<span>Energieaufnahme im Schnitt: <span class="sl">${latest.kcal || '--'} kcal</span></span>`;

  console.log('Alle Diagramme wurden gerendert.');
}
