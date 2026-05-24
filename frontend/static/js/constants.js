export const $ = s => document.querySelector(s);

export const BASE = window.BASE_URL || "";

export let state = {
  CH: {},
  curSex: 'male',
  curTarget: 70,
  curAvatar: '',
  lastData: null,
  lastPrev: null
};

// Vollständige Grenzwert-Tabelle für die dynamische Bewertung
export const RANGES = {
  male: {
    bmi:      { good: [18.5, 25], ok: [25, 28] },
    fat:      { good: [8, 20],    ok: [20, 25] },
    muscle:   { good: [49, 60],   ok: [44, 49] },
    water:    { good: [55, 65],   ok: [50, 55] },
    visceral: { good: [1, 10],    ok: [10, 15] },
    protein:  { good: [16, 22],   ok: [14, 16] },
    lbm:      { good: [50, 62],   ok: [45, 50] },
    poi:      { good: [11, 15],   ok: [15, 17] }
  },
  female: {
    bmi:      { good: [18.5, 25], ok: [25, 28] },
    fat:      { good: [21, 33],   ok: [33, 39] },
    muscle:   { good: [34, 40],   ok: [30, 34] },
    water:    { good: [45, 60],   ok: [40, 45] },
    visceral: { good: [1, 10],    ok: [10, 15] },
    protein:  { good: [14, 18],   ok: [12, 14] },
    lbm:      { good: [38, 45],   ok: [34, 38] },
    poi:      { good: [11, 15],   ok: [15, 17] }
  }
};

/**
 * Ermittelt die CSS-Klasse (good, ok, bad) basierend auf Geschlecht, Typ und Wert
 */
export function getRatingClass(type, value) {
  if (value === undefined || value === null) return 'neutral';

  const userSex = state.curSex || 'male';
  const limits = RANGES[userSex]?.[type];

  if (!limits) return 'neutral';

  const [goodMin, goodMax] = limits.good;
  const [okMin, okMax] = limits.ok;

  // Innerhalb der optimalen Werte
  if (value >= goodMin && value <= goodMax) return 'good';

  // Innerhalb der Toleranzgrenze (über oder unter "good")
  if ((value >= okMin && value < goodMin) || (value > goodMax && value <= okMax)) return 'ok';

  // Außerhalb aller Grenzwerte
  return 'bad';
}

export const gc = () => document.documentElement.getAttribute('data-theme') === 'dark' ? 'rgba(255,255,255,.07)' : 'rgba(0,0,0,.05)';
export const tc = () => document.documentElement.getAttribute('data-theme') === 'dark' ? '#ccc' : '#666';
