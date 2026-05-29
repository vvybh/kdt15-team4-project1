from __future__ import annotations

import urllib.parse
from typing import Any

import requests


def _clean_price(price_value: Any) -> int:
    if price_value is None:
        return 0
    digits = "".join(filter(str.isdigit, str(price_value)))
    return int(digits) if digits else 0


def search_bunjang(
    keyword: str,
    page: int = 1,
    limit: int = 30,
    headers: dict[str, str] | None = None,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    encoded_keyword = urllib.parse.quote(keyword)
    target_page = max(page - 1, 0)
    api_url = (
        "https://api.bunjang.co.kr/api/1/find_v2.json"
        f"?q={encoded_keyword}&n={limit}&page={target_page}&version=4"
    )
    client = session or requests.Session()
    results: list[dict[str, Any]] = []

    try:
        request_headers = dict(headers or {})
        request_headers["Referer"] = f"https://m.bunjang.co.kr/keywords/{encoded_keyword}"
        res = client.get(api_url, headers=request_headers, timeout=10)

        if res.status_code != 200:
            return results

        for product in res.json().get("list", []):
            product_id = product.get("pid", "")
            results.append(
                {
                    "platform": "번개장터",
                    "title": product.get("name", ""),
                    "price": _clean_price(product.get("price", "")),
                    "link": f"https://m.bunjang.co.kr/products/{product_id}",
                    "image": product.get("product_image", ""),
                }
            )
    except Exception as e:
        print(f"[번개장터] 수집 실패: {e}")

    return results[:limit]
