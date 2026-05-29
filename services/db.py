from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "app.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


MIGRATIONS = {
    "raw_items": {
        "collected_keyword": "TEXT",
        "raw_category": "TEXT",
        "raw_condition": "TEXT",
        "raw_components": "TEXT",
        "raw_shipping_fee": "TEXT",
        "raw_trade_method": "TEXT",
        "raw_image_url": "TEXT",
        "raw_description": "TEXT",
    },
    "market_items": {
        "collected_keyword": "TEXT",
        "normalized_title": "TEXT",
        "source_category": "TEXT",
        "source_status": "TEXT",
        "shipping_fee": "INTEGER",
        "trade_method": "TEXT",
    },
}


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database(db_path: Path | str = DB_PATH) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        apply_lightweight_migrations(conn)
        conn.commit()


def apply_lightweight_migrations(conn: sqlite3.Connection) -> None:
    for table_name, columns in MIGRATIONS.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})")}
        for column_name, column_type in columns.items():
            if column_name not in existing:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
