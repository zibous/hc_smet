# -*- coding: utf-8 -*-
"""SQLite DB Manager für MiScale Messdaten."""

import csv
import logging
import os
import sqlite3

from app.core.config import cfg

log = logging.getLogger(__name__)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS daily_miscale (
    id INTEGER,
    name TEXT,
    timestamp TEXT,
    date TEXT,
    weight REAL,
    impedance REAL,
    fat REAL,
    visceral REAL,
    water REAL,
    muscle REAL,
    bmi REAL,
    protein REAL,
    lbm REAL,
    poi REAL,
    PRIMARY KEY (id, date)
)
"""

CSV_FIELDS = [
    "id",
    "name",
    "timestamp",
    "date",
    "weight",
    "impedance",
    "fat",
    "visceral",
    "water",
    "muscle",
    "bmi",
    "protein",
    "lbm",
    "poi",
]


class DBManager:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or cfg.db_path
        self._data_dir = os.path.dirname(self.db_path)
        os.makedirs(self._data_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(CREATE_TABLE)
            conn.commit()
        log.info("DB initialisiert: %s", self.db_path)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def upsert(self, user_id: int, data: dict) -> bool:
        try:
            timestamp = data.get("timestamp", "")
            if " " in timestamp and "T" in timestamp:
                timestamp = timestamp.split(" ")[0]
            if len(timestamp) > 19:
                timestamp = timestamp[:19]
            date_str = timestamp[:10] if len(timestamp) >= 10 else ""

            row = (
                user_id,
                data.get("user", ""),
                timestamp,
                date_str,
                data.get("weight"),
                data.get("impedance"),
                data.get("fat"),
                data.get("visceral"),
                data.get("water"),
                data.get("muscle"),
                data.get("bmi"),
                data.get("protein"),
                data.get("lbm"),
                data.get("poi"),
            )

            sql = """
            INSERT INTO daily_miscale
                (id, name, timestamp, date, weight, impedance, fat, visceral,
                 water, muscle, bmi, protein, lbm, poi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id, date) DO UPDATE SET
                timestamp = excluded.timestamp,
                weight = excluded.weight, impedance = excluded.impedance,
                fat = excluded.fat, visceral = excluded.visceral,
                water = excluded.water, muscle = excluded.muscle,
                bmi = excluded.bmi, protein = excluded.protein,
                lbm = excluded.lbm, poi = excluded.poi
            WHERE excluded.timestamp >= daily_miscale.timestamp
            """

            with self._connect() as conn:
                conn.execute(sql, row)
                conn.commit()

            log.info("DB upsert: user=%s date=%s", data.get("user"), date_str)
            self._write_csv_backup(user_id, data.get("user", ""), timestamp, date_str, data)
            return True
        except Exception:
            log.exception("DB upsert fehlgeschlagen")
            return False

    def _write_csv_backup(self, user_id: int, name: str, timestamp: str, date_str: str, data: dict):
        try:
            if not name or len(date_str) < 7:
                return
            month = date_str[:7]
            history_dir = os.path.join(self._data_dir, "history", name.lower())
            os.makedirs(history_dir, exist_ok=True)
            csv_path = os.path.join(history_dir, f"{month}.csv")
            is_new = not os.path.isfile(csv_path)

            row_dict = {
                "id": user_id,
                "name": name,
                "timestamp": timestamp,
                "date": date_str,
                "weight": data.get("weight"),
                "impedance": data.get("impedance"),
                "fat": data.get("fat"),
                "visceral": data.get("visceral"),
                "water": data.get("water"),
                "muscle": data.get("muscle"),
                "bmi": data.get("bmi"),
                "protein": data.get("protein"),
                "lbm": data.get("lbm"),
                "poi": data.get("poi"),
            }

            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, delimiter=";")
                if is_new:
                    writer.writeheader()
                writer.writerow(row_dict)
        except Exception:
            log.exception("CSV-Backup fehlgeschlagen")

    def get_history(self, user_id: int, limit: int = 365) -> list[dict]:
        sql = """
        SELECT name, timestamp, date, weight, impedance, fat, visceral,
               water, muscle, bmi, protein, lbm, poi
        FROM daily_miscale WHERE id = ? ORDER BY date DESC LIMIT ?
        """
        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(sql, (user_id, limit)).fetchall()
                return [dict(r) for r in rows]
        except Exception:
            log.exception("DB get_history fehlgeschlagen")
            return []
