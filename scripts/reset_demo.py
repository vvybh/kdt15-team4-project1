from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.load_market_items import load_market_items
from scripts.seed_demo_data import seed_demo_data


def main():
    load_market_items()
    seed_demo_data()
    print("demo data is ready")


if __name__ == "__main__":
    main()
