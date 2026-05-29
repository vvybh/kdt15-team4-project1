from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.db import DB_PATH, get_connection, init_database
from services.market_repository import clear_market_data, insert_market_row


CSV_PATH = ROOT / "data" / "sample" / "market_items.csv"


def load_market_items(csv_path: Path = CSV_PATH):
    init_database(DB_PATH)
    with get_connection(DB_PATH) as conn:
        clear_market_data(conn)
        with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                insert_market_row(conn, row)
        conn.commit()


def main():
    load_market_items()
    print(f"loaded sample CSV: {CSV_PATH}")


if __name__ == "__main__":
    main()
