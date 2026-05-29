from __future__ import annotations

import csv
import json
from pathlib import Path
from sqlite3 import Connection

from crawlers.base import RawMarketItem
from services.normalize_service import build_product_key, normalize_price, normalize_title


MARKET_CSV_FIELDS = [
    "id",
    "raw_item_id",
    "source",
    "collected_keyword",
    "source_item_id",
    "source_url",
    "title",
    "normalized_title",
    "product_name",
    "category",
    "source_category",
    "brand",
    "model_name",
    "product_key",
    "item_condition",
    "components",
    "price",
    "currency",
    "trade_status",
    "source_status",
    "listed_at",
    "sold_at",
    "location",
    "shipping_fee",
    "trade_method",
    "image_url",
    "description",
    "crawled_at",
]


def observed_at(row: dict) -> str:
    return row.get("sold_at") or row.get("listed_at") or row["crawled_at"][:10]


def clear_market_data(conn: Connection) -> None:
    conn.execute("DELETE FROM price_snapshots")
    conn.execute("DELETE FROM market_items")
    conn.execute("DELETE FROM sqlite_sequence WHERE name = 'price_snapshots'")


def delete_market_items_for_product(conn: Connection, source: str, product_key: str) -> int:
    rows = conn.execute(
        "SELECT id FROM market_items WHERE source = ? AND product_key = ?",
        (source, product_key),
    ).fetchall()
    ids = [row["id"] for row in rows]
    if not ids:
        return 0

    placeholders = ",".join("?" for _ in ids)
    conn.execute(f"DELETE FROM price_snapshots WHERE market_item_id IN ({placeholders})", ids)
    conn.execute(f"DELETE FROM market_items WHERE id IN ({placeholders})", ids)
    return len(ids)


def insert_raw_item(conn: Connection, raw: RawMarketItem, crawl_run_id: int | None = None) -> int:
    payload = raw.raw_payload or {}
    cursor = conn.execute(
        """
        INSERT INTO raw_items (
            crawl_run_id, source, collected_keyword, source_item_id, source_url,
            raw_title, raw_price, raw_status, raw_location, raw_date,
            raw_category, raw_condition, raw_components, raw_shipping_fee,
            raw_trade_method, raw_image_url, raw_description, raw_payload, crawled_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            crawl_run_id,
            raw.source,
            payload.get("collected_keyword", ""),
            raw.source_item_id,
            raw.source_url,
            raw.raw_title,
            raw.raw_price,
            raw.raw_status,
            raw.raw_location,
            raw.raw_date,
            payload.get("source_category", ""),
            payload.get("item_condition", ""),
            payload.get("components", ""),
            payload.get("shipping_fee", ""),
            payload.get("trade_method", ""),
            payload.get("image_url", ""),
            payload.get("description", ""),
            json.dumps(payload, ensure_ascii=False),
            raw.crawled_at,
        ),
    )
    return int(cursor.lastrowid)


def market_row_from_raw(
    raw: RawMarketItem,
    *,
    raw_item_id: int | None = None,
    category: str,
    brand: str = "",
    product_name: str,
    model_name: str = "",
) -> dict:
    payload = raw.raw_payload or {}
    title = payload.get("title") or raw.raw_title
    price = payload.get("price") or normalize_price(raw.raw_price)
    if price is None:
        raise ValueError(f"가격을 숫자로 바꿀 수 없습니다: {raw.raw_price}")

    normalized = normalize_title(title)
    product_key = build_product_key(category, brand, product_name, model_name)
    return {
        "raw_item_id": raw_item_id or "",
        "source": raw.source,
        "collected_keyword": payload.get("collected_keyword", ""),
        "source_item_id": raw.source_item_id,
        "source_url": raw.source_url,
        "title": title,
        "normalized_title": normalized,
        "product_name": product_name,
        "category": category,
        "source_category": payload.get("source_category", ""),
        "brand": brand,
        "model_name": model_name,
        "product_key": product_key,
        "item_condition": payload.get("item_condition", ""),
        "components": payload.get("components", ""),
        "price": int(price),
        "currency": payload.get("currency", "KRW"),
        "trade_status": payload.get("trade_status") or raw.raw_status,
        "source_status": raw.raw_status,
        "listed_at": payload.get("listed_at") or raw.raw_date,
        "sold_at": payload.get("sold_at", ""),
        "location": payload.get("location") or raw.raw_location,
        "shipping_fee": normalize_price(str(payload.get("shipping_fee", ""))) or "",
        "trade_method": payload.get("trade_method", ""),
        "image_url": payload.get("image_url", ""),
        "description": payload.get("description", ""),
        "crawled_at": raw.crawled_at,
    }


def coerce_csv_row(row: dict) -> dict:
    coerced = {field: row.get(field, "") for field in MARKET_CSV_FIELDS}
    if not coerced["normalized_title"]:
        coerced["normalized_title"] = normalize_title(coerced["title"])
    return coerced


def insert_market_row(conn: Connection, row: dict) -> int:
    normalized = coerce_csv_row(row)
    insert_fields = [field for field in MARKET_CSV_FIELDS if field != "id"]
    values = [_db_value(field, normalized[field]) for field in insert_fields]

    if str(normalized.get("id", "")).strip():
        insert_fields = ["id", *insert_fields]
        values = [int(normalized["id"]), *values]

    placeholders = ", ".join("?" for _ in insert_fields)
    conn.execute(
        f"""
        INSERT INTO market_items ({", ".join(insert_fields)})
        VALUES ({placeholders})
        """,
        values,
    )
    market_item_id = int(normalized["id"]) if str(normalized.get("id", "")).strip() else int(
        conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    )
    conn.execute(
        """
        INSERT INTO price_snapshots (
            market_item_id, product_key, price, observed_at,
            source, trade_status, item_condition
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            market_item_id,
            normalized["product_key"],
            int(normalized["price"]),
            observed_at(normalized),
            normalized["source"],
            normalized["trade_status"],
            normalized["item_condition"],
        ),
    )
    return market_item_id


def _db_value(field: str, value):
    if field in {"raw_item_id", "shipping_fee"} and value == "":
        return None
    return value


def write_market_csv(rows: list[dict], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=MARKET_CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(coerce_csv_row(row))
