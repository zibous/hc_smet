#!/usr/bin/env python3
import sqlite3
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path

###############################################################################
# 1) Datenbank laden
###############################################################################

def load_db(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("""
        SELECT sensor_id,
               hour,
               datetime(hour, 'unixepoch') AS dt,
               consumption,
               total
        FROM hourly_values
        ORDER BY hour ASC
    """, conn)
    conn.close()
    return df

###############################################################################
# 2) Zeitspalten erzeugen
###############################################################################

def enrich(df):
    df["dt"] = pd.to_datetime(df["dt"])
    df["year"] = df["dt"].dt.year
    df["month"] = df["dt"].dt.to_period("M")
    df["day"] = df["dt"].dt.to_period("D")
    df["hour_of_day"] = df["dt"].dt.hour
    return df

###############################################################################
# 3) Summen (gesamt)
###############################################################################

def yearly_sum(df):
    return df.groupby("year")["consumption"].sum()

def monthly_sum(df):
    return df.groupby("month")["consumption"].sum()

def daily_sum(df):
    return df.groupby("day")["consumption"].sum()

###############################################################################
# 4) Summen pro Sensor
###############################################################################

def yearly_sum_per_sensor(df):
    return df.groupby(["sensor_id", "year"])["consumption"].sum()

def monthly_sum_per_sensor(df):
    return df.groupby(["sensor_id", "month"])["consumption"].sum()

def daily_sum_per_sensor(df):
    return df.groupby(["sensor_id", "day"])["consumption"].sum()

###############################################################################
# Jahr aus Dateiname extrahieren
###############################################################################

def extract_year_from_filename(path):
    name = Path(path).stem
    for part in name.split("_"):
        if part.isdigit() and len(part) == 4:
            return part
    return "unknown"

###############################################################################
# 5) Heatmap (Stunde → Verbrauch)
###############################################################################

def heatmap(df):
    return df.groupby("hour_of_day")["consumption"].sum()

###############################################################################
# 6) Top‑Sensoren
###############################################################################

def top_sensors(df, year=None, limit=10):
    if year:
        df = df[df["year"] == year]
    return df.groupby("sensor_id")["consumption"].sum().sort_values(ascending=False).head(limit)

###############################################################################
# 7) Datenlücken finden
###############################################################################

def find_gaps(df):
    df = df.sort_values("hour")
    df["diff"] = df["hour"].diff()
    gaps = df[df["diff"] > 3600]
    return gaps[["hour", "diff"]]

###############################################################################
# 8) CSV‑Export
###############################################################################

def export_csv(df, name, year_tag):
    out_dir = Path("./export/csv")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"{name}_{year_tag}.csv"
    df.to_csv(out_file, sep=";", decimal=",")
    print(f"[OK] CSV gespeichert: {out_file}")

###############################################################################
# 9) Plots erzeugen
###############################################################################

def plot_series(series, title, filename):
    if series is None or series.empty:
        print(f"[SKIP] {title}: keine Daten.")
        return

    out_dir = Path("export/img/series")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / filename

    fig, ax = plt.subplots(figsize=(12, 5))
    series.plot(kind="bar", ax=ax, color="#4C72B0")
    ax.set_title(title)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()
    fig.savefig(out_file, dpi=150)
    plt.close(fig)

    print(f"[OK] Plot gespeichert: {out_file}")

###############################################################################
# 10) Jahresvergleichs‑Plot
###############################################################################

def plot_year_comparison(yearly_data_dict):
    if not yearly_data_dict:
        print("[SKIP] Jahresvergleich: keine Daten.")
        return

    out_dir = Path("export/img/yearly")
    out_dir.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(14, 6))

    for year, series in yearly_data_dict.items():
        if series.empty:
            continue
        ax.plot(series.index.astype(str), series.values, marker="o", label=str(year))

    ax.set_title("Jahresvergleich – Gesamtverbrauch")
    ax.set_xlabel("Jahr")
    ax.set_ylabel("kWh")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()

    out_file = out_dir / "compare_years.png"
    fig.tight_layout()
    fig.savefig(out_file, dpi=150)
    plt.close(fig)

    print(f"[OK] Jahresvergleich gespeichert: {out_file}")

###############################################################################
# 11) Sensorvergleichs‑Plot pro Jahr
###############################################################################

def plot_sensor_comparison(df, year_tag):
    out_dir = Path("export/img/compare")
    out_dir.mkdir(exist_ok=True)

    df_year = df[df["year"] == int(year_tag)]
    if df_year.empty:
        print(f"[SKIP] Sensorvergleich {year_tag}: keine Daten.")
        return

    sensor_totals = df_year.groupby("sensor_id")["consumption"].sum()

    fig, ax = plt.subplots(figsize=(14, 6))
    sensor_totals.plot(kind="bar", ax=ax, color="#55A868")

    ax.set_title(f"Sensorvergleich – Jahr {year_tag}")
    ax.set_xlabel("Sensor")
    ax.set_ylabel("kWh")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    out_file = out_dir / f"compare_sensors_{year_tag}.png"
    fig.tight_layout()
    fig.savefig(out_file, dpi=150)
    plt.close(fig)

    print(f"[OK] Sensorvergleich gespeichert: {out_file}")

###############################################################################
# 12) Bereichs-Parsing (2013-2018)
###############################################################################

def expand_year_range(arg):
    if "-" not in arg:
        return None
    start, end = arg.split("-")
    if start.isdigit() and end.isdigit():
        return list(range(int(start), int(end) + 1))
    return None

###############################################################################
# 13) Heatmap
###############################################################################
def build_day_hour_heatmap(df, year_tag):
    """
    Erzeugt eine 2D-Matrix:
    Zeilen = Tage (1–365)
    Spalten = Stunden (0–23)
    Werte = Verbrauch (NaN für fehlende Daten)
    """
    df_year = df[df["year"] == int(year_tag)].copy()
    if df_year.empty:
        return None

    df_year["day_of_year"] = df_year["dt"].dt.dayofyear

    pivot = df_year.pivot_table(
        index="day_of_year",
        columns="hour_of_day",
        values="consumption",
        aggfunc="sum",
    )

    # Vollständiges Grid: alle 365 Tage × 24 Stunden
    full_index = range(1, 367)
    full_columns = range(24)
    pivot = pivot.reindex(index=full_index, columns=full_columns)

    return pivot

def plot_heatmap_2d(pivot, year_tag):
    """Faceted Heatmap: 12 Monats-Kacheln — Durchschnittsprofil Wochentag × Stunde."""
    if pivot is None or pivot.empty:
        print(f"[SKIP] 2D-Heatmap {year_tag}: keine Daten.")
        return

    import numpy as np
    import calendar

    out_dir = Path("export/img/heatmap")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"heatmap_2d_{year_tag}.png"

    year = int(year_tag)

    # Pro Monat: Durchschnitt pro Wochentag × Stunde (7 × 24)
    month_names = ["Januar", "Februar", "März", "April", "Mai", "Juni",
                   "Juli", "August", "September", "Oktober", "November", "Dezember"]
    weekday_labels = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    # DataFrame aus Pivot rekonstruieren
    df_pivot = pivot.copy()
    df_pivot.index.name = "day_of_year"

    # Wochentag berechnen
    from datetime import date
    day_to_weekday = {}
    for doy in range(1, 367):
        try:
            d = date(year, 1, 1) + pd.Timedelta(days=doy - 1)
            if d.year == year:
                day_to_weekday[doy] = d.weekday()  # 0=Mo, 6=So
        except:
            pass

    # Monat berechnen
    day_to_month = {}
    for doy in range(1, 367):
        try:
            d = date(year, 1, 1) + pd.Timedelta(days=doy - 1)
            if d.year == year:
                day_to_month[doy] = d.month
        except:
            pass

    # Globale Farbskala berechnen
    all_means = []

    month_grids = {}
    for m in range(1, 13):
        # Tage dieses Monats
        days_in_month = [doy for doy, mon in day_to_month.items() if mon == m]
        if not days_in_month:
            month_grids[m] = None
            continue

        # Grid: 7 Wochentage × 24 Stunden (Durchschnitt)
        grid = np.full((7, 24), np.nan)
        counts = np.zeros((7, 24))

        for doy in days_in_month:
            if doy not in day_to_weekday or doy > len(pivot):
                continue
            wd = day_to_weekday[doy]
            row = pivot.iloc[doy - 1].values
            for h in range(24):
                val = row[h] if h < len(row) else np.nan
                if not np.isnan(val):
                    if np.isnan(grid[wd, h]):
                        grid[wd, h] = val
                    else:
                        grid[wd, h] += val
                    counts[wd, h] += 1

        # Durchschnitt
        with np.errstate(divide="ignore", invalid="ignore"):
            grid = np.where(counts > 0, grid / counts, np.nan)

        month_grids[m] = grid
        valid = grid[~np.isnan(grid)]
        if len(valid) > 0:
            all_means.extend(valid.tolist())

    # Farbskala
    if not all_means:
        print(f"[SKIP] 2D-Heatmap {year_tag}: keine gültigen Werte.")
        return

    all_means = np.array(all_means)
    vmax = np.percentile(all_means[all_means > 0], 95) if np.any(all_means > 0) else 1.0

    # Plot: 4×3 Grid
    fig, axes = plt.subplots(4, 3, figsize=(15, 14))
    fig.suptitle(f"Ø Energieverbrauch – Wochentag × Stunde – {year_tag}",
                 fontsize=15, y=0.995)

    for idx in range(12):
        row = idx // 3
        col = idx % 3
        ax = axes[row, col]
        m = idx + 1
        grid = month_grids[m]

        if grid is None or np.all(np.isnan(grid)):
            ax.set_facecolor("#f5f5f5")
            ax.text(12, 3.5, "Keine Daten", ha="center", va="center",
                    fontsize=10, color="#999")
        else:
            im = ax.pcolormesh(
                np.arange(25),
                np.arange(8),
                grid,
                cmap="RdYlGn_r",
                vmin=0,
                vmax=vmax,
                shading="flat",
            )

        ax.set_title(month_names[idx], fontsize=11, fontweight="bold", pad=4)
        ax.set_xlim(0, 24)
        ax.set_ylim(0, 7)

        # X: Stunden
        ax.set_xticks([0, 4, 8, 12, 16, 20, 24])
        ax.set_xticklabels(["0", "4", "8", "12", "16", "20", "24"], fontsize=8)

        # Y: Wochentage
        ax.set_yticks(np.arange(0.5, 7, 1))
        ax.set_yticklabels(weekday_labels, fontsize=9)

        if row == 3:
            ax.set_xlabel("Stunde", fontsize=9)

    # Farblegende
    fig.subplots_adjust(right=0.91, hspace=0.35, wspace=0.25)
    cbar_ax = fig.add_axes([0.93, 0.15, 0.015, 0.7])
    sm = plt.cm.ScalarMappable(cmap="RdYlGn_r", norm=plt.Normalize(vmin=0, vmax=vmax))
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax)
    cbar.set_label("Ø kWh", fontsize=11)

    fig.savefig(out_file, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(f"[OK] Faceted Heatmap gespeichert: {out_file}")


###############################################################################
# 14) Main
###############################################################################

def main():
    if len(sys.argv) < 2:
        print("Usage: python dbcheck.py <dbfile> | <year-range> | <*.db>")
        sys.exit(1)

    args = sys.argv[1:]
    db_files = []

    # Bereich wie 2013-2018
    if len(args) == 1:
        years = expand_year_range(args[0])
        if years:
            for y in years:
                f = f"sensors_{y}.db"
                if Path(f).exists():
                    db_files.append(f)
                else:
                    print(f"[WARN] Datei fehlt: {f}")
        else:
            db_files = [args[0]]
    else:
        db_files = args

    # Wildcards (*.db)
    expanded = []
    for f in db_files:
        expanded.extend(Path().glob(f))
    db_files = [str(f) for f in expanded]

    if not db_files:
        print("Keine passenden Datenbanken gefunden.")
        sys.exit(1)

    yearly_compare_dict = {}

    # Jede DB einzeln verarbeiten
    for db_path in db_files:
        print("\n========================================")
        print(f"Analysiere Datenbank: {db_path}")
        print("========================================")

        year_tag = extract_year_from_filename(db_path)

        df = load_db(db_path)
        df = enrich(df)

        # Summaries
        y = yearly_sum(df)
        m = monthly_sum(df)
        d = daily_sum(df)

        # Für Jahresvergleich sammeln
        if not y.empty:
            yearly_compare_dict[year_tag] = y

        # CSV
        # export_csv(y, "yearly", year_tag)
        export_csv(m, "monthly", year_tag)
        export_csv(d, "daily", year_tag)

        # Einzelplots
        # plot_series(y, "Jahresverbrauch", f"yearly_{year_tag}.png")
        plot_series(m, "Monatsverbrauch", f"monthly_{year_tag}.png")
        plot_series(heatmap(df), "Heatmap Stundenverbrauch", f"heatmap_hours_{year_tag}.png")

        # Sensorvergleich
        plot_sensor_comparison(df, year_tag)

        # 2D Heatmap (Tag × Stunde)
        pivot = build_day_hour_heatmap(df, year_tag)
        plot_heatmap_2d(pivot, year_tag)


    # Jahresvergleich über alle geladenen DBs
    plot_year_comparison(yearly_compare_dict)

    print("\nFertig! Alle Analysen wurden erzeugt.")

if __name__ == "__main__":
    main()
