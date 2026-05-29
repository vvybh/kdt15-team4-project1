from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.db import DB_PATH, init_database


def main():
    init_database(DB_PATH)
    print(f"created schema: {DB_PATH}")


if __name__ == "__main__":
    main()
