from datetime import datetime
import json
import logging
from pathlib import Path
import sys
import html

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from manager import PoKeysManager

# Projektwurzel ermitteln
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from app.core.app_config import settings
from app.core.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()
manager = PoKeysManager()

# --- KONSTANTEN ---
KLASSE_FARBEN = {
    "A": "#009640", "B": "#4cb123", "C": "#c3d100",
    "D": "#ffcc00", "E": "#ff9900", "F": "#ff3300", "G": "#d3001e"
}

ICON_MAP = {
    "licht": "💡", "light": "💡", "steckdosen": "🔌", "netzteil": "🔋",
    "kühlschrank": "🧊", "kuehlschrank": "🧊", "fridge": "🧊", "tiefkuehltruhe": "❄️",
    "geschirrspueler": "🍽️", "spuelmaschine": "🍽️", "kueche": "🍳", "kuechenmoebel": "🪑",
    "herd": "🔥", "ofen": "🔥", "backofen": "🔥", "heizung": "♨️",
    "heizungsgeraet": "♨️", "heizungspumpe": "♨️", "boiler": "🚿",
    "pumpe": "💧", "abwasserpumpe": "💧", "dampfdusche": "🚿",
    "wasch": "🧺", "waschmaschine": "🧺", "trock": "♨️", "trockner": "♨️",
    "server": "🖥️", "rechner": "🖥️", "tv": "📺", "soundanlage": "🔊",
    "telefonanlage": "☎️", "wlan": "📶", "piko_wechselrichter": "🔆",
    "wohnzimmer": "🛋️", "schlafzimmer": "🛏️", "kinderzimmer 1": "🧸", "kinderzimmer 2": "🧸",
    "fitnessraum": "🏋️", "garage": "🚗", "gang": "🚪", "vorratsraum": "📦", "wc": "🚽", "bad": "🛁",
    "rolladen": "🪟", "zaehlerschrank": "⚡", "reserve": "⭕",
}

# --- HILFSFUNKTIONEN ---
def normalize(text: str) -> str:
    return text.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss").strip()

def get_icon(sensor) -> str:
    name = normalize(sensor.name or "")
    for key, icon in ICON_MAP.items():
        if key in name:
            return icon
    return "⚡"

def safe_float(v, default=0.0):
    try:
        return float(v)
    except:
        return default

def render_sensor_card(s) -> str:

    ts = s.update_ts
    online_time = datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M") if ts and ts != "--" and ts != 0 else "--"
    badge = '<span class="badge-online">ONLINE</span>' if s.online else '<span class="badge-off">OFFLINE</span>'
    farbe = KLASSE_FARBEN.get(getattr(s, "energieklasse", "A"), "#777")
    icon = get_icon(s)

    return f"""
    <div class="card">
        <div class="icon">{icon} {badge}</div>
        <h3>{html.escape(str(s.id))}: {html.escape(s.name)}</h3>

        <div class="row"><span class="label">Geräte:</span>
            <span class="value-strong">{", ".join(html.escape(d.capitalize()) for d in s.devices)}</span>
        </div>

        <div class="row"><span class="label">Energieklasse</span>
            <span class="value-strong" style="background-color:{farbe};color:white;padding:2px 8px;border-radius:4px;">
                {getattr(s, "energieklasse", "A")}
            </span>
        </div>

        <div class="row"><span class="label">Aktuelle Leistung</span><span class="value-strong">{s.watt} W</span></div>
        <div class="row"><span class="label">Aktueller Verbrauch</span><span>{safe_float(s.verbrauch_kwh):.3f} kWh</span></div>
        <div class="row"><span class="label">Kosten</span><span>{safe_float(s.kosten):.3f} €</span></div>
        <div class="row"><span class="label">CO₂</span><span>{safe_float(s.co2):.1f} g</span></div>
        <div class="row"><span class="label">Trend</span><span>{safe_float(s.kwh_pro_stunde):.3f} kWh/h</span></div>
        <div class="row"><span class="label">Prognose Tag</span><span>{safe_float(s.prognose_tag):.2f} €</span></div>
        <div class="row"><span class="label">Prognose Jahr</span><span>{safe_float(s.prognose_jahr):.2f} €</span></div>
        <div class="row"><span class="label">Raum</span><span>{html.escape(s.room)}</span></div>
        <div class="row"><span class="label">Sensor</span><span>{html.escape(s.model)} Pin:{s.pin}</span></div>
        <div class="row"><span class="label">Online</span><span>{online_time}</span></div>
    </div>
    """

# --- ROUTE ---
@app.get("/", response_class=HTMLResponse)
def dashboard():
    logger.info("Dashboard ready")

    try:
        manager.update_sensors()
    except Exception as e:
        logger.exception("Fehler beim Sensor-Update")
        return HTMLResponse("<h1>Fehler beim Sensor-Update</h1>")

    active = [
        s for s in manager.sensors.values()
        if safe_float(s.total_kwh) > 0
    ]

    # KPIs
    total_watt = sum(s.watt for s in active)
    total_kwh = sum(safe_float(s.verbrauch_kwh) for s in active)
    total_cost = sum(safe_float(s.kosten) for s in active)
    total_co2 = sum(safe_float(s.co2) for s in active)
    online_count = sum(1 for s in active if s.online)
    offline_count = len(active) - online_count

    # Charts
    chart_data = {
        "labels": [html.escape(s.name or f"Sensor {s.id}") for s in active],
        "values": [s.watt for s in active]
    }

    top_s = sorted(active, key=lambda s: s.watt, reverse=True)[:5]
    top_data = {"labels": [html.escape(s.name) for s in top_s], "values": [s.watt for s in top_s]}

    cards_html = "".join(render_sensor_card(s) for s in active)

    html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>Live Energie-Dashboard</title>

        <!-- FIXED: Chart.js -->
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        <style>
            body {{ background:#111;color:#eee;font-family:sans-serif;margin:20px; }}
            .chart-container {{ background:#1b1b1b;padding:16px;border-radius:16px;margin-bottom:20px; }}
            .grid {{ display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;margin-top:30px; }}
            .card {{ background:#1b1b1b;padding:20px;border-radius:16px; }}
            .row {{ display:flex;justify-content:space-between;margin:4px 0; }}
            .badge-online {{ background:#1f7a3a;padding:2px 8px;border-radius:999px; }}
            .badge-off {{ background:#7a1f1f;padding:2px 8px;border-radius:999px; }}
            .kpi-grid {{display: grid;grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));gap: 10px;margin-top: 10px;margin-bottom: 10px;}}
            .kpi {{background: #222;padding: 12px;border-radius: 12px;text-align: center;}}
            .kpi-value {{font-size: 18px;font-weight: bold;}}
        </style>
    </head>
    <body>

        <h1>⚡ Energie Dashboard</h1>

        <div class="chart-container">
            <canvas id="chart"></canvas>
        </div>

        <div class="chart-container">
            <canvas id="topChart"></canvas>
        </div>

        <div class="chart-container">
            <h2>📊 Gesamtübersicht</h2>

            <div class="kpi-grid">
                <div class="kpi">⚡ Verbrauch<div class="kpi-value">{total_watt:.0f} W</div></div>
                <div class="kpi">🔋 Energie<div class="kpi-value">{total_kwh:.2f} kWh</div></div>
                <div class="kpi">💰 Kosten<div class="kpi-value">{total_cost:.2f} €</div></div>
                <div class="kpi">🌍 CO2<div class="kpi-value">{total_co2:.1f} g</div></div>
                <div class="kpi">🟢 Online<div class="kpi-value">{online_count}</div></div>
                <div class="kpi">🔴 Offline<div class="kpi-value">{offline_count}</div></div>
            </div>
        </div>


        <div class="grid">{cards_html}</div>

        <script>

            const mainData = {json.dumps(chart_data, ensure_ascii=False)};
            const topData = {json.dumps(top_data, ensure_ascii=False)};

            new Chart(document.getElementById('chart'), {{
                type: 'bar',
                data: {{
                    labels: mainData.labels,
                    datasets: [{{
                        label: 'Verbrauch Watt',
                        data: mainData.values,
                        backgroundColor: 'rgba(0,200,255,0.4)'
                    }}]
                }}
            }});

            new Chart(document.getElementById('topChart'), {{
                type: 'bar',
                data: {{
                    labels: topData.labels,
                    datasets: [{{
                        label: 'Top Geräte Verbrauch Watt',
                        data: topData.values,
                        backgroundColor: 'rgba(255,99,132,0.4)'
                    }}]
                }}
            }});

</script>



    </body>
    </html>
    """

    return HTMLResponse(html_page)
