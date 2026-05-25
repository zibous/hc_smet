# uvicorn main:app --host 0.0.0.0 --port 8020 --reload

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json

from manager import PoKeysManager  # <- deine bestehende Klasse

app = FastAPI()
manager = PoKeysManager()

ICON_MAP = {
    "kühlschrank": "🧊",
    "kuehlschrank": "🧊",
    "fridge": "🧊",
    "licht": "💡",
    "light": "💡",
    "herd": "🔥",
    "ofen": "🔥",
    "backofen": "🔥",
    "wasch": "🧺",
    "trock": "♨️",
    "server": "🖥️",
    "pumpe": "💧",
}


def get_icon(sensor):
    name = (sensor.name or "").lower()
    for key, icon in ICON_MAP.items():
        if key in name:
            return icon
    return "⚡"


@app.get("/", response_class=HTMLResponse)
def dashboard():
    # Sensoren aktualisieren (holt aktuelle Werte)
    manager.update_sensors()
    sensors = manager.sensors

    # Nur aktive Sensoren (Verbrauch > 0)
    active = [s for s in sensors.values() if s.verbrauch_kwh > 0]

    labels = [s.name for s in active]
    watts = [s.watt for s in active]

    html = f"""
    <html>
    <head>
        <title>Live Energie-Dashboard</title>
        <meta charset="utf-8" />
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        <script>
            // Auto-Refresh jede Minute
            setInterval(() => {{
                window.location.reload();
            }}, 60000);
        </script>

        <style>
            body {{
                background: #111;
                color: #eee;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 20px;
            }}

            h1, h2 {{
                color: #fff;
            }}

            h1 {{
                margin-bottom: 10px;
            }}

            .subtitle {{
                color: #888;
                font-size: 0.9rem;
                margin-bottom: 20px;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }}

            .card {{
                background: #1b1b1b;
                border-radius: 16px;
                padding: 20px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                transition: transform 0.2s, box-shadow 0.2s;
            }}

            .card:hover {{
                transform: scale(1.03);
                box-shadow: 0 6px 18px rgba(0,0,0,0.6);
            }}

            .icon {{
                font-size: 40px;
                margin-bottom: 10px;
            }}

            .card h3 {{
                margin: 0 0 10px 0;
            }}

            .row {{
                display: flex;
                justify-content: space-between;
                margin: 4px 0;
                font-size: 0.9rem;
            }}

            .label {{
                color: #aaa;
            }}

            .value-strong {{
                font-weight: 600;
            }}

            .badge-online {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 999px;
                background: #1f7a3a;
                color: #c8ffd9;
                font-size: 0.75rem;
                margin-left: 8px;
            }}

            .badge-off {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 999px;
                background: #7a1f1f;
                color: #ffd0d0;
                font-size: 0.75rem;
                margin-left: 8px;
            }}

            .chart-container {{
                background: #1b1b1b;
                border-radius: 16px;
                padding: 16px 16px 8px 16px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                margin-bottom: 20px;
            }}
        </style>
    </head>

    <body>

        <h1>Live Energie-Dashboard</h1>
        <div class="subtitle">Aktive Sensoren, aktualisiert jede Minute</div>

        <div class="chart-container">
            <canvas id="chart" height="120"></canvas>
        </div>

        <script>
            const labels = {json.dumps(labels)};
            const watts = {json.dumps(watts)};

            const ctx = document.getElementById('chart').getContext('2d');

            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'Watt',
                        data: watts,
                        backgroundColor: 'rgba(0, 200, 255, 0.4)',
                        borderColor: 'rgba(0, 200, 255, 1)',
                        borderWidth: 1,
                        borderRadius: 8,
                        borderSkipped: false
                    }}]
                }},
                options: {{
                    plugins: {{
                        legend: {{ display: false }}
                    }},
                    scales: {{
                        x: {{
                            ticks: {{ color: '#888' }},
                            grid: {{ display: false }}
                        }},
                        y: {{
                            ticks: {{ color: '#888' }},
                            grid: {{ color: '#222' }},
                            beginAtZero: true
                        }}
                    }}
                }}
            }});
        </script>

        <h2>Aktive Sensoren</h2>

        <div class="grid">
    """

    for s in active:
        icon = get_icon(s)
        badge = (
            '<span class="badge-online">ONLINE</span>'
            if s.online else
            '<span class="badge-off">OFFLINE</span>'
        )

        html += f"""
            <div class="card">
                <div class="icon">{icon}</div>
                <h3>{s.name} {badge}</h3>

                <div class="row">
                    <span class="label">Watt</span>
                    <span class="value-strong">{s.watt}</span>
                </div>
                <div class="row">
                    <span class="label">Δ kWh</span>
                    <span>{s.verbrauch_kwh:.4f}</span>
                </div>
                <div class="row">
                    <span class="label">Total kWh</span>
                    <span>{s.total_kwh:.3f}</span>
                </div>
                <div class="row">
                    <span class="label">Kosten</span>
                    <span>{s.kosten:.3f} €</span>
                </div>
                <div class="row">
                    <span class="label">CO₂</span>
                    <span>{s.co2:.1f} g</span>
                </div>
                <div class="row">
                    <span class="label">Trend</span>
                    <span>{s.kwh_pro_stunde:.4f} kWh/h</span>
                </div>
                <div class="row">
                    <span class="label">Prognose Tag</span>
                    <span>{s.prognose_tag:.2f} €</span>
                </div>
                <div class="row">
                    <span class="label">Prognose Jahr</span>
                    <span>{s.prognose_jahr:.2f} €</span>
                </div>
            </div>
        """

    html += """
        </div>
    </body>
    </html>
    """

    return html
