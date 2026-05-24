import pandas as pd
import numpy as np

import app.domain.house as house
from app.infrastructure.database.dbconnect import Database

import logging
logger = logging.getLogger(__name__)

# Lädt das stabile Dictionary aus der YAML
STRUCTURE = house.load_house_yaml()

def load_timeseries(start, end, freq, period_name="", node="HOME"):
    return load_energy_data(start, end, freq, period_name, node)

def load_energy_data(start, end, freq, period_name="", node="HOME"):

    if Database._instance is None:
        raise RuntimeError("Database must be initialized before EnergyAggregator is created")

    db = Database._instance

    logger.debug(f"Zeitraum Datenfilter: {start} - {end}")

    # =====================================================
    # SAFE TIME HANDLING (NO AMBIGUOUS TZ BUGS)
    # =====================================================
    start_dt = pd.to_datetime(start, utc=True, errors="raise")
    end_dt = pd.to_datetime(end, utc=True, errors="raise")

    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    # EXTRAKTION ALLER BETROFFENEN JAHRE
    years_in_range = list(range(start_dt.year, end_dt.year + 1))
    logger.debug(f"📂 Abfrage betrifft folgende Datenbank-Jahre: {years_in_range}")

    query = """
        SELECT
            sensor_id,
            consumption,
            hour AS ts
        FROM hourly_values
        WHERE hour BETWEEN ? AND ?
        ORDER BY hour ASC
    """

    dataframes = []

    for current_year in years_in_range:
        conn = db.get_conn(year=current_year)
        try:
            with conn:
                df_year = pd.read_sql_query(query, conn, params=[start_ts, end_ts])
                if not df_year.empty:
                    dataframes.append(df_year)
        except Exception as e:
            logger.warning(f"⚠️ Datenbank-Datei für Jahr {current_year} konnte nicht ausgelesen werden: {e}")
        finally:
            conn.close()

    if not dataframes:
        logger.warning("Keine Daten in den abgefragten Zeiträumen gefunden!")
        return {
            "time": [], "series": {}, "labels": {}, "level": 1, "stats": {}
        }

    # Alle Jahres-DataFrames nahtlos verketten
    df = pd.concat(dataframes, ignore_index=True)

    # =====================================================
    # STATS-RETTER: Echte Stunden-Statistiken vor der Aggregation sichern
    # =====================================================
    hourly_stats_df = df.groupby("sensor_id").agg({
        "consumption": ["min", "max", "mean", "last"]
    })

    # 1. Zeitstempel als echte UTC-Zeit interpretieren
    df["dt_temp"] = pd.to_datetime(df["ts"], unit="s", utc=True)

    # 2. HIER präzise in lokale Berliner Zeit umrechnen (+ Sommer-/Winterzeit)
    df["dt_temp"] = df["dt_temp"].dt.tz_convert("Europe/Berlin")

    # 3. Zeitzonen-Stempel für das korrekte Resampling/Grouping entfernen
    df["dt_temp"] = df["dt_temp"].dt.tz_localize(None)

    # Berechnen der echten Zeitspanne im geladenen Stream (jetzt auf lokaler Basis)
    actual_days = (df["dt_temp"].max() - df["dt_temp"].min()).days

    # Weiche für das X-Achsen-Format festlegen
    time_format = "%Y-%m-%d %H:%M"

    # =====================================================
    # 🔧 INTERNE INTELLIGENTE SCHWELLENWERT-WEICHE
    # =====================================================
    if actual_days > 14:
        if actual_days > 365:
            freq_rule = "1MS"  # Über ein Jahr -> Monatlich
            time_format = "%Y-%m"
        elif actual_days > 60:
            freq_rule = "1W"   # Auf Wochenbasis aggregieren!
            time_format = "KW %V (%Y)"  # Formatierung als Kalenderwoche
        else:
            freq_rule = "1d"   # 15 bis 60 Tage -> Täglich
            time_format = "%Y-%m-%d"

        logger.debug(f"📊 Zeitraum im Datenbestand: {actual_days} Tage. Schalte Aggregation auf: {freq_rule}")

        # Gruppiert nach Sensor und dem neuen LOKALEN Zeitraster
        df = df.groupby(["sensor_id", pd.Grouper(key="dt_temp", freq=freq_rule)]).agg({
            "consumption": "sum"
        }).reset_index()

        # Sicherer Unix-Timestamp-Export (wieder zurück als numerischer Index für das Pivot)
        df["ts"] = df["dt_temp"].apply(lambda x: int(x.timestamp()))

    # =====================================================
    # PIVOT
    # =====================================================
    pivot = df.pivot_table(
        index="ts",
        columns="sensor_id",
        values="consumption",
        aggfunc="sum"
    ).fillna(0).sort_index()

    # X-Achsen-Beschriftung aus dem lokalen Timestamp generieren
    times = pd.to_datetime(pivot.index, unit="s", utc=True).tz_convert("Europe/Berlin").strftime(time_format).tolist()

    sensors = STRUCTURE["sensors"]
    rooms = STRUCTURE["rooms"]
    areas = STRUCTURE["areas"]

    # =====================================================
    # BUILD SERIES
    # =====================================================
    series = {}
    labels = {}
    level = 1

    if node == "HOME":
        keys = list(areas.keys())
        for area_id in keys:
            sensor_ids = [
                s_id for s_id, s in sensors.items()
                if rooms[s["room"]]["area"] == area_id and s_id in pivot.columns
            ]
            if sensor_ids:
                series[area_id] = pivot[sensor_ids].sum(axis=1).tolist()
            else:
                series[area_id] = [0.0] * len(times)
        labels = {a_id: areas[a_id]["name"] for a_id in keys}
        level = 1

    elif node in areas:
        keys = [r_id for r_id, r in rooms.items() if r["area"] == node]
        for room_id in keys:
            sensor_ids = [
                s_id for s_id, s in sensors.items()
                if s["room"] == room_id and s_id in pivot.columns
            ]
            if sensor_ids:
                series[room_id] = pivot[sensor_ids].sum(axis=1).tolist()
            else:
                series[room_id] = [0.0] * len(times)
        labels = {r_id: rooms[r_id]["name"] for r_id in keys}
        level = 2

    elif node in rooms:
        keys = [
            s_id for s_id, s in sensors.items()
            if s["room"] == node and s_id in pivot.columns
        ]
        series = {s_id: pivot[s_id].tolist() for s_id in keys}
        labels = {s_id: sensors[s_id]["name"] for s_id in keys}
        level = 3

    else:
        if node in pivot.columns:
            series = {node: pivot[node].tolist()}
        else:
            series = {node: [0.0] * len(times)}
        labels = {node: sensors.get(node, {}).get("name", node)}
        level = 4

    # =====================================================
    # SAFE STATS (Physikalisch korrekte Stunden-Statistiken)
    # =====================================================
    stats = {}

    for k, values in series.items():
        arr = np.asarray(values, dtype=float)

        if arr.size == 0:
            stats[k] = {"min": 0.0, "max": 0.0, "avg": 0.0, "current": 0.0, "delta": 0.0}
            continue

        current_val = float(arr[-1])
        prev_val = float(arr[-2]) if arr.size > 1 else current_val
        delta_val = ((current_val - prev_val) / prev_val * 100) if prev_val != 0 else 0.0

        if node == "HOME" and k in areas:
            s_ids = [sid for sid, s in sensors.items() if rooms[s["room"]]["area"] == k and sid in hourly_stats_df.index]
        elif node in areas and k in rooms:
            s_ids = [sid for sid, s in sensors.items() if s["room"] == k and sid in hourly_stats_df.index]
        else:
            s_ids = [k] if k in hourly_stats_df.index else []

        if s_ids:
            sub_stats = hourly_stats_df.loc[s_ids]
            min_hour = float(sub_stats["consumption"]["min"].sum())
            max_hour = float(sub_stats["consumption"]["max"].sum())
            avg_hour = float(sub_stats["consumption"]["mean"].sum())
            curr_hour = float(sub_stats["consumption"]["last"].sum())
        else:
            min_hour, max_hour, avg_hour, curr_hour = 0.0, 0.0, 0.0, 0.0

        stats[k] = {
            "min": min_hour,
            "max": max_hour,
            "avg": avg_hour,
            "current": curr_hour,
            "delta": delta_val
        }

    return {
        "time": times,
        "series": series,
        "labels": labels,
        "level": level,
        "stats": stats
    }


def get_raw_consumption_dataframe(start: str, end: str) -> pd.DataFrame:
    """Holt die rohen Verbrauchsdaten für den CSV-Export über mehrere Jahre."""
    if Database._instance is None:
        return pd.DataFrame()

    start_dt = pd.to_datetime(start, utc=True)
    end_dt = pd.to_datetime(end, utc=True)

    years = list(range(start_dt.year, end_dt.year + 1))
    query = """
        SELECT sensor_id, hour, consumption
        FROM hourly_values
        WHERE hour BETWEEN ? AND ?
        ORDER BY hour ASC, sensor_id ASC
    """

    dfs = []
    for y in years:
        conn = Database._instance.get_conn(year=y)
        try:
            with conn:
                df_year = pd.read_sql_query(query, conn, params=[int(start_dt.timestamp()), int(end_dt.timestamp())])
                if not df_year.empty:
                    dfs.append(df_year)
        except Exception:
            pass
        finally:
            conn.close()

    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    # Umrechnung von UTC Unix-Timestamps nach Europe/Berlin für das CSV
    utc_time = pd.to_datetime(df["hour"], unit="s", utc=True)
    berlin_time = utc_time.dt.tz_convert("Europe/Berlin").dt.tz_localize(None)

    df["zeitstempel"] = berlin_time.dt.strftime("%Y-%m-%d %H:%M:%S")
    return df[["zeitstempel", "sensor_id", "consumption"]]
