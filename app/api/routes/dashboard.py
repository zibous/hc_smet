# -*- coding: utf-8 -*-
"""Dashboard API Routes – Gewichtsverlauf und Körperdaten."""

import csv
import logging
import os
import sqlite3
from io import StringIO

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse, JSONResponse, Response

from app.models.user_service import UserService
from app.services.db_manager import DBManager

log = logging.getLogger(__name__)

router = APIRouter()

_db: DBManager | None = None
_AVATAR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "frontend")


def init_dashboard(db: DBManager):
    global _db
    _db = db


@router.get("/dashboard/api/data")
async def dashboard_data(
    user: str = "peter",
    date_from: str = Query("", alias="from"),
    date_to: str = Query("", alias="to"),
    before: str = "",
    limit: str = "",
):
    if not _db:
        return JSONResponse({"error": "DB not available"}, status_code=500)

    user = user.lower()
    try:
        conn = sqlite3.connect(_db.db_path)
        conn.row_factory = sqlite3.Row

        if before:
            n = int(limit) if limit else 30
            rows = conn.execute(
                "SELECT * FROM daily_miscale WHERE LOWER(name)=? AND date<? ORDER BY date DESC LIMIT ?",
                (user, before, n),
            ).fetchall()
            rows = list(reversed(rows))
        elif date_from and date_to:
            rows = conn.execute(
                "SELECT * FROM daily_miscale WHERE LOWER(name)=? AND date>=? AND date<=? ORDER BY date",
                (user, date_from, date_to),
            ).fetchall()
        elif date_from:
            rows = conn.execute(
                "SELECT * FROM daily_miscale WHERE LOWER(name)=? AND date>=? ORDER BY date",
                (user, date_from),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM daily_miscale WHERE LOWER(name)=? ORDER BY date DESC LIMIT 365",
                (user,),
            ).fetchall()
            rows = list(reversed(rows))

        conn.close()

        seen = {}
        for r in [dict(r) for r in rows]:
            d = r["date"]
            if d not in seen or r["timestamp"] > seen[d]["timestamp"]:
                seen[d] = r
        deduped = sorted(seen.values(), key=lambda x: x["date"])

        return {"user": user, "count": len(deduped), "data": deduped}
    except Exception:
        log.exception("Fehler beim Laden der Daten")
        return JSONResponse({"error": "DB error"}, status_code=500)


@router.get("/dashboard/api/users")
async def dashboard_users():
    if not _db:
        return JSONResponse({"error": "DB not available"}, status_code=500)
    try:
        conn = sqlite3.connect(_db.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT id, name, COUNT(*) as count, MIN(date) as first, MAX(date) as last
            FROM daily_miscale GROUP BY name ORDER BY id
        """).fetchall()
        conn.close()
        result = [dict(r) for r in rows]

        try:
            us = UserService()
            for r in result:
                user = us.find_by_name(r["name"])
                if user:
                    r["target_weight"] = user.scores.get("WEIGHT", 0)
                    r["weight_threshold"] = user.weight_threshold
                    r["sex"] = user.sex
                r["avatar"] = f"/dashboard/avatar/{r['name'].lower()}"
        except Exception:
            pass

        return result
    except Exception:
        log.exception("Fehler beim Laden der User-Liste")
        return []


@router.get("/dashboard/api/export")
async def dashboard_export(
    user: str = "peter",
    date_from: str = Query("", alias="from"),
    date_to: str = Query("", alias="to"),
):
    if not _db:
        return JSONResponse({"error": "DB not available"}, status_code=500)

    user = user.lower()
    try:
        conn = sqlite3.connect(_db.db_path)
        conn.row_factory = sqlite3.Row

        if date_from and date_to:
            rows = conn.execute(
                "SELECT * FROM daily_miscale WHERE LOWER(name)=? AND date>=? AND date<=? ORDER BY date",
                (user, date_from, date_to),
            ).fetchall()
        elif date_from:
            rows = conn.execute(
                "SELECT * FROM daily_miscale WHERE LOWER(name)=? AND date>=? ORDER BY date",
                (user, date_from),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM daily_miscale WHERE LOWER(name)=? ORDER BY date",
                (user,),
            ).fetchall()
        conn.close()

        fields = [
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

        buf = StringIO()
        writer = csv.DictWriter(buf, fieldnames=fields, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(dict(r))

        filename = f"miscale-{user}.csv"
        if date_from:
            filename = f"miscale-{user}-{date_from}.csv"

        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception:
        log.exception("CSV-Export fehlgeschlagen")
        return JSONResponse({"error": "export error"}, status_code=500)


@router.get("/dashboard/avatar/{name}")
async def dashboard_avatar(name: str):
    for ext in ("png", "jpg", "jpeg", "webp"):
        path = os.path.join(_AVATAR_DIR, f"{name.lower()}.{ext}")
        if os.path.isfile(path):
            return FileResponse(path)
    # Fallback: 1x1 transparent PNG
    import struct
    import zlib

    sig = b"\x89PNG\r\n\x1a\n"

    def chunk(ctype, data):
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    idat = zlib.compress(b"\x00\x00\x00\x00\x00")
    png = sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    return Response(content=png, media_type="image/png")
