from __future__ import annotations

from datetime import datetime


INSPECTION_STATUSES = [
    "판매자 발송 대기",
    "관리자 수령 완료",
    "검수 중",
    "검수 통과",
    "검수 보류",
    "검수 실패",
    "구매자 발송 완료",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace(" ", "T"))


def status_label(status: str) -> str:
    labels = {
        "active": "진행중",
        "closed": "낙찰 완료",
        "closed_no_bid": "입찰 없이 마감",
    }
    return labels.get(status, status)


def close_finished_auctions(conn, force_auction_id: int | None = None) -> None:
    now = now_text()
    if force_auction_id is None:
        rows = conn.execute(
            "SELECT * FROM auctions WHERE status = 'active' AND end_at <= ?",
            (now,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM auctions WHERE status = 'active' AND id = ?",
            (force_auction_id,),
        ).fetchall()

    for auction in rows:
        top_bid = conn.execute(
            """
            SELECT bidder_name, bid_amount
            FROM bids
            WHERE auction_id = ?
            ORDER BY bid_amount DESC, created_at ASC
            LIMIT 1
            """,
            (auction["id"],),
        ).fetchone()
        if top_bid:
            conn.execute(
                """
                UPDATE auctions
                SET status = 'closed',
                    winner_name = ?,
                    winning_bid = ?,
                    current_price = ?
                WHERE id = ?
                """,
                (top_bid["bidder_name"], top_bid["bid_amount"], top_bid["bid_amount"], auction["id"]),
            )
            ensure_inspection_status(conn, auction["id"])
        else:
            conn.execute(
                "UPDATE auctions SET status = 'closed_no_bid' WHERE id = ?",
                (auction["id"],),
            )
    conn.commit()


def ensure_inspection_status(conn, auction_id: int) -> None:
    existing = conn.execute(
        "SELECT id FROM inspection_statuses WHERE auction_id = ?",
        (auction_id,),
    ).fetchone()
    if existing:
        return
    conn.execute(
        """
        INSERT INTO inspection_statuses (auction_id, status, note, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (auction_id, INSPECTION_STATUSES[0], "", now_text()),
    )


def list_auctions(conn, filters=None):
    close_finished_auctions(conn)
    filters = filters or {}
    sql = [
        """
        SELECT
            a.*,
            COUNT(b.id) AS bid_count
        FROM auctions a
        LEFT JOIN bids b ON b.auction_id = a.id
        WHERE 1 = 1
        """
    ]
    params = []

    query = (filters.get("query") or "").strip()
    if query:
        sql.append("AND (a.title LIKE ? OR a.product_name LIKE ?)")
        params.extend([f"%{query}%", f"%{query}%"])

    category = (filters.get("category") or "").strip()
    if category:
        sql.append("AND a.category = ?")
        params.append(category)

    status = (filters.get("status") or "").strip()
    if status:
        sql.append("AND a.status = ?")
        params.append(status)

    min_price = filters.get("min_price")
    if min_price:
        sql.append("AND a.current_price >= ?")
        params.append(int(min_price))

    max_price = filters.get("max_price")
    if max_price:
        sql.append("AND a.current_price <= ?")
        params.append(int(max_price))

    sql.append("GROUP BY a.id ORDER BY CASE a.status WHEN 'active' THEN 0 ELSE 1 END, a.end_at ASC")
    rows = conn.execute("\n".join(sql), params).fetchall()
    return [dict(row) | {"status_label": status_label(row["status"])} for row in rows]


def get_auction(conn, auction_id: int):
    close_finished_auctions(conn)
    row = conn.execute(
        """
        SELECT
            a.*,
            COUNT(b.id) AS bid_count
        FROM auctions a
        LEFT JOIN bids b ON b.auction_id = a.id
        WHERE a.id = ?
        GROUP BY a.id
        """,
        (auction_id,),
    ).fetchone()
    if not row:
        return None
    return dict(row) | {"status_label": status_label(row["status"])}


def get_bids(conn, auction_id: int):
    rows = conn.execute(
        """
        SELECT *
        FROM bids
        WHERE auction_id = ?
        ORDER BY bid_amount DESC, created_at ASC
        """,
        (auction_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def create_auction(conn, form):
    start_price = int(form["start_price"])
    bid_unit = int(form.get("bid_unit") or 1000)
    cursor = conn.execute(
        """
        INSERT INTO auctions (
            title, product_name, category, brand, model_name, product_key,
            description, image_url, seller_name, start_price, current_price,
            bid_unit, end_at, status, item_condition, components, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
        """,
        (
            form["title"].strip(),
            form.get("product_name", "").strip() or form["title"].strip(),
            form["category"].strip(),
            form.get("brand", "").strip(),
            form.get("model_name", "").strip(),
            form["product_key"].strip(),
            form.get("description", "").strip(),
            form.get("image_url", "").strip(),
            form["seller_name"].strip(),
            start_price,
            start_price,
            bid_unit,
            form["end_at"],
            form.get("item_condition", "").strip(),
            form.get("components", "").strip(),
            now_text(),
        ),
    )
    conn.commit()
    return cursor.lastrowid


def place_bid(conn, auction_id: int, bidder_name: str, bid_amount: int):
    close_finished_auctions(conn)
    auction = get_auction(conn, auction_id)
    if not auction:
        return False, "경매를 찾을 수 없습니다."
    if auction["status"] != "active":
        return False, "이미 마감된 경매입니다."
    if parse_datetime(auction["end_at"]) <= datetime.now():
        close_finished_auctions(conn)
        return False, "경매 마감 시간이 지났습니다."
    if bidder_name.strip() == auction["seller_name"]:
        return False, "판매자와 같은 이름으로는 입찰할 수 없습니다."

    min_bid = auction["current_price"] + auction["bid_unit"]
    if bid_amount < min_bid:
        return False, f"최소 입찰가는 {min_bid:,}원입니다."

    conn.execute(
        """
        INSERT INTO bids (auction_id, bidder_name, bid_amount, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (auction_id, bidder_name.strip(), bid_amount, now_text()),
    )
    conn.execute(
        "UPDATE auctions SET current_price = ? WHERE id = ?",
        (bid_amount, auction_id),
    )
    conn.commit()
    return True, "입찰이 등록되었습니다."


def get_inspection_rows(conn):
    close_finished_auctions(conn)
    rows = conn.execute(
        """
        SELECT
            a.id AS auction_id,
            a.title,
            a.winner_name,
            a.winning_bid,
            i.status,
            i.note,
            i.updated_at
        FROM auctions a
        JOIN inspection_statuses i ON i.auction_id = a.id
        WHERE a.status = 'closed'
        ORDER BY i.updated_at DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_inspection(conn, auction_id: int):
    row = conn.execute(
        "SELECT * FROM inspection_statuses WHERE auction_id = ?",
        (auction_id,),
    ).fetchone()
    return dict(row) if row else None


def update_inspection(conn, auction_id: int, status: str, note: str) -> None:
    if status not in INSPECTION_STATUSES:
        raise ValueError("지원하지 않는 검수 상태입니다.")
    ensure_inspection_status(conn, auction_id)
    conn.execute(
        """
        UPDATE inspection_statuses
        SET status = ?, note = ?, updated_at = ?
        WHERE auction_id = ?
        """,
        (status, note.strip(), now_text(), auction_id),
    )
    conn.commit()
