# database.py

import sqlite3
from datetime import datetime
from config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fares (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                fetched_at      TEXT NOT NULL,   -- UTC timestamp of this observation
                origin          TEXT NOT NULL,
                destination     TEXT NOT NULL,
                departure_date  TEXT NOT NULL,   -- the actual departure date searched
                days_ahead      INTEGER NOT NULL, -- 7, 30, or 90
                airline         TEXT,
                price_total     REAL,            -- total price in USD
                price_base      REAL,
                currency        TEXT,
                duration        TEXT,
                stops           INTEGER,
                raw_offer       TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fetch_log (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                fetched_at      TEXT NOT NULL,
                route           TEXT NOT NULL,
                days_ahead      INTEGER NOT NULL,
                status          TEXT NOT NULL,
                n_records       INTEGER DEFAULT 0,
                message         TEXT
            )
        """)
        conn.commit()
    print(f"[DB] Initialized database at '{DB_PATH}'")


def save_fares(fares: list[dict]):
    if not fares:
        return
    with get_connection() as conn:
        conn.executemany("""
            INSERT INTO fares
                (fetched_at, origin, destination, departure_date, days_ahead,
                 airline, price_total, price_base, currency, duration, stops, raw_offer)
            VALUES
                (:fetched_at, :origin, :destination, :departure_date, :days_ahead,
                 :airline, :price_total, :price_base, :currency, :duration, :stops, :raw_offer)
        """, fares)
        conn.commit()
    print(f"[DB] Saved {len(fares)} fare records.")


def log_fetch(route: str, days_ahead: int, status: str, n_records: int = 0, message: str = ""):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO fetch_log (fetched_at, route, days_ahead, status, n_records, message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.utcnow().isoformat(), route, days_ahead, status, n_records, message))
        conn.commit()
