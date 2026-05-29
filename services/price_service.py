from __future__ import annotations

from statistics import median


def list_product_options(conn):
    rows = conn.execute(
        """
        SELECT
            product_key,
            MIN(product_name) AS product_name,
            MIN(category) AS category,
            MIN(brand) AS brand,
            COUNT(*) AS sample_count
        FROM market_items
        GROUP BY product_key
        ORDER BY category, product_name
        """
    ).fetchall()
    return [dict(row) for row in rows]


def fetch_price_items(conn, product_key: str):
    rows = conn.execute(
        """
        SELECT
            ps.price,
            ps.observed_at,
            ps.source,
            ps.trade_status,
            ps.item_condition,
            mi.title,
            mi.source_url,
            mi.location,
            mi.source_category,
            mi.shipping_fee,
            mi.trade_method
        FROM price_snapshots ps
        JOIN market_items mi ON mi.id = ps.market_item_id
        WHERE ps.product_key = ?
        ORDER BY ps.observed_at ASC, ps.price ASC
        """,
        (product_key,),
    ).fetchall()
    return [dict(row) for row in rows]


def percentile(values: list[int], ratio: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * ratio
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * weight)


def compare_bid_to_market(current_bid: int | None, low: int | None, high: int | None) -> str | None:
    if current_bid is None or low is None or high is None:
        return None
    if current_bid < low:
        return "시세보다 낮은 편"
    if current_bid > high:
        return "시세보다 높은 편"
    return "일반적인 시세 범위"


def calculate_price_summary(items, current_bid: int | None = None):
    prices = sorted(int(item["price"]) for item in items if item.get("price") is not None)
    sample_count = len(prices)

    if sample_count <= 2:
        status = "insufficient"
        status_label = "데이터 부족"
    elif sample_count <= 4:
        status = "reference_only"
        status_label = "참고용"
    else:
        status = "enough"
        status_label = "시세 범위 표시"

    reference_price = round(median(prices)) if prices else None
    price_range_low = percentile(prices, 0.25) if sample_count >= 5 else None
    price_range_high = percentile(prices, 0.75) if sample_count >= 5 else None
    recommended_start_price = price_range_low or reference_price

    sources = sorted({item["source"] for item in items if item.get("source")})
    current_bid_label = compare_bid_to_market(current_bid, price_range_low, price_range_high)

    return {
        "sample_count": sample_count,
        "status": status,
        "status_label": status_label,
        "reference_price": reference_price,
        "price_range_low": price_range_low,
        "price_range_high": price_range_high,
        "recommended_start_price": recommended_start_price,
        "current_bid_label": current_bid_label,
        "sources": sources,
        "period": "최근 수집 데이터 기준",
    }


def build_chart_data(items):
    return [
        {
            "observed_at": item["observed_at"],
            "price": item["price"],
            "source": item["source"],
            "trade_status": item["trade_status"],
            "item_condition": item["item_condition"],
            "title": item["title"],
            "location": item["location"],
            "source_category": item["source_category"],
            "shipping_fee": item["shipping_fee"],
            "trade_method": item["trade_method"],
        }
        for item in items
    ]


def build_price_response(conn, product_key: str, current_bid: int | None = None):
    items = fetch_price_items(conn, product_key)
    summary = calculate_price_summary(items, current_bid=current_bid)
    return {
        "product_key": product_key,
        "summary": summary,
        "items": build_chart_data(items),
    }
