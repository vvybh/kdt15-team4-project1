from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.auction_service import close_finished_auctions, ensure_inspection_status
from services.db import DB_PATH, get_connection, init_database


def dt(minutes: int) -> str:
    return (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M")


def seed_demo_data():
    init_database(DB_PATH)
    with get_connection(DB_PATH) as conn:
        conn.execute("DELETE FROM inspection_statuses")
        conn.execute("DELETE FROM bids")
        conn.execute("DELETE FROM auctions")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('inspection_statuses', 'bids', 'auctions')")

        auctions = [
            {
                "title": "나이키 후드티 L 블랙",
                "product_name": "나이키 후드티",
                "category": "의류",
                "brand": "Nike",
                "model_name": "",
                "product_key": "의류:nike:후드티",
                "description": "착용 횟수가 적은 후드티입니다. 시세 그래프를 보고 시작가를 낮게 잡았습니다.",
                "image_url": "/static/img/hoodie.svg",
                "seller_name": "판매자A",
                "start_price": 30000,
                "current_price": 30000,
                "bid_unit": 1000,
                "end_at": dt(240),
                "status": "active",
                "item_condition": "사용감 적음",
                "components": "단품",
            },
            {
                "title": "크리넥스 휴지 24롤 미개봉",
                "product_name": "크리넥스 휴지 24롤",
                "category": "생필품",
                "brand": "크리넥스",
                "model_name": "",
                "product_key": "생필품:크리넥스:휴지:24롤",
                "description": "미개봉 생필품입니다. 당일 수령 가능합니다.",
                "image_url": "/static/img/tissue.svg",
                "seller_name": "판매자B",
                "start_price": 15000,
                "current_price": 15000,
                "bid_unit": 500,
                "end_at": dt(90),
                "status": "active",
                "item_condition": "새상품",
                "components": "풀세트",
            },
            {
                "title": "나이키 후드티 그레이",
                "product_name": "나이키 후드티",
                "category": "의류",
                "brand": "Nike",
                "model_name": "",
                "product_key": "의류:nike:후드티",
                "description": "시연용으로 이미 마감된 경매입니다.",
                "image_url": "/static/img/hoodie.svg",
                "seller_name": "판매자C",
                "start_price": 28000,
                "current_price": 39000,
                "bid_unit": 1000,
                "end_at": dt(-60),
                "status": "active",
                "item_condition": "사용감 있음",
                "components": "단품",
            },
        ]

        auction_ids = []
        for auction in auctions:
            cursor = conn.execute(
                """
                INSERT INTO auctions (
                    title, product_name, category, brand, model_name, product_key,
                    description, image_url, seller_name, start_price, current_price,
                    bid_unit, end_at, status, item_condition, components, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    auction["title"],
                    auction["product_name"],
                    auction["category"],
                    auction["brand"],
                    auction["model_name"],
                    auction["product_key"],
                    auction["description"],
                    auction["image_url"],
                    auction["seller_name"],
                    auction["start_price"],
                    auction["current_price"],
                    auction["bid_unit"],
                    auction["end_at"],
                    auction["status"],
                    auction["item_condition"],
                    auction["components"],
                    dt(-120),
                ),
            )
            auction_ids.append(cursor.lastrowid)

        bids = [
            (auction_ids[0], "구매자1", 32000, dt(-50)),
            (auction_ids[0], "구매자2", 35000, dt(-30)),
            (auction_ids[1], "구매자3", 16000, dt(-20)),
            (auction_ids[2], "구매자4", 34000, dt(-80)),
            (auction_ids[2], "구매자5", 39000, dt(-70)),
        ]
        for auction_id, bidder_name, bid_amount, created_at in bids:
            conn.execute(
                """
                INSERT INTO bids (auction_id, bidder_name, bid_amount, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (auction_id, bidder_name, bid_amount, created_at),
            )
            conn.execute(
                "UPDATE auctions SET current_price = ? WHERE id = ? AND current_price < ?",
                (bid_amount, auction_id, bid_amount),
            )

        conn.commit()
        close_finished_auctions(conn)
        ensure_inspection_status(conn, auction_ids[2])
        conn.execute(
            """
            UPDATE inspection_statuses
            SET status = '검수 중', note = '시연용 검수 상태입니다.', updated_at = ?
            WHERE auction_id = ?
            """,
            (dt(-10), auction_ids[2]),
        )
        conn.commit()


def main():
    seed_demo_data()
    print("seeded demo auctions and bids")


if __name__ == "__main__":
    main()
