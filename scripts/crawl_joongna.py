from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from crawlers.joongna import JoongnaCrawler, JoongnaCrawlerOptions
from services.db import DB_PATH, get_connection, init_database
from services.market_repository import (
    delete_market_items_for_product,
    insert_market_row,
    insert_raw_item,
    market_row_from_raw,
    write_market_csv,
)
from services.normalize_service import build_product_key


DEFAULT_OUTPUT = ROOT / "data" / "processed" / "joongna_market_items.csv"


def run_crawl(args: argparse.Namespace) -> tuple[int, Path]:
    init_database(DB_PATH)
    options = JoongnaCrawlerOptions(
        limit=args.limit,
        delay_seconds=args.delay,
        timeout_seconds=args.timeout,
        product_urls=args.product_url or None,
    )
    crawler = JoongnaCrawler(options)
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    product_key = build_product_key(args.category, args.brand, args.product_name, args.model_name)
    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT

    with get_connection(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO crawl_runs (source, keyword, category, started_at, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("joongna", args.keyword, args.category, started_at, "running"),
        )
        crawl_run_id = int(cursor.lastrowid)
        rows: list[dict] = []

        try:
            raw_items = crawler.crawl(args.keyword, args.search_category)
            if not args.keep_existing:
                delete_market_items_for_product(conn, "joongna", product_key)

            for raw in raw_items:
                if not raw.raw_price:
                    continue
                raw_item_id = insert_raw_item(conn, raw, crawl_run_id)
                row = market_row_from_raw(
                    raw,
                    raw_item_id=raw_item_id,
                    category=args.category,
                    brand=args.brand,
                    product_name=args.product_name,
                    model_name=args.model_name,
                )
                if args.source_category_contains and args.source_category_contains not in row["source_category"]:
                    continue
                market_item_id = insert_market_row(conn, row)
                row["id"] = market_item_id
                rows.append(row)

            conn.execute(
                """
                UPDATE crawl_runs
                SET finished_at = ?, status = ?, item_count = ?, error_message = NULL
                WHERE id = ?
                """,
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "success", len(rows), crawl_run_id),
            )
            conn.commit()
        except Exception as exc:
            conn.execute(
                """
                UPDATE crawl_runs
                SET finished_at = ?, status = ?, error_message = ?
                WHERE id = ?
                """,
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "failed", str(exc), crawl_run_id),
            )
            conn.commit()
            raise

    write_market_csv(rows, output_path)
    return len(rows), output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="중고나라 공개 상품 데이터를 수집해 CSV와 SQLite에 저장합니다.")
    parser.add_argument("--keyword", default="나이키 후드티", help="중고나라 검색어 또는 상품 URL이 들어간 문자열")
    parser.add_argument("--category", default="의류", help="프로젝트 공통 카테고리")
    parser.add_argument("--brand", default="Nike", help="브랜드")
    parser.add_argument("--product-name", default="후드티", help="같은 상품으로 묶을 대표 상품명")
    parser.add_argument("--model-name", default="", help="모델명")
    parser.add_argument("--search-category", default="", help="중고나라 검색 카테고리 ID. 모르면 비워 둡니다.")
    parser.add_argument("--source-category-contains", default="", help="원본 카테고리에 이 값이 들어간 상품만 저장")
    parser.add_argument("--limit", type=int, default=8, help="최대 수집 상품 수")
    parser.add_argument("--delay", type=float, default=0.7, help="상품 페이지 요청 사이 대기 시간")
    parser.add_argument("--timeout", type=int, default=20, help="요청 제한 시간")
    parser.add_argument("--product-url", action="append", default=[], help="검색 대신 직접 수집할 상품 URL. 여러 번 입력 가능")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="저장할 CSV 경로")
    parser.add_argument("--keep-existing", action="store_true", help="같은 source/product_key 기존 데이터를 지우지 않고 추가")
    return parser.parse_args()


def main() -> None:
    count, output_path = run_crawl(parse_args())
    print(f"saved {count} joongna items")
    print(f"csv: {output_path}")
    print(f"sqlite: {DB_PATH}")


if __name__ == "__main__":
    main()
