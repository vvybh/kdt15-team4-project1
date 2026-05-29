from __future__ import annotations

import urllib.parse
from typing import Any

import requests
from bs4 import BeautifulSoup


def _clean_price(price_value: Any) -> int:
    if price_value is None:
        return 0
    digits = "".join(filter(str.isdigit, str(price_value)))
    return int(digits) if digits else 0


def search_joongna(
    keyword: str,
    page: int = 1,
    limit: int = 30,
    headers: dict[str, str] | None = None,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://web.joongna.com/search/{encoded_keyword}?page={page}"
    client = session or requests.Session()
    results: list[dict[str, Any]] = []

    try:
        res = client.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select('a[href*="/product/"]')

        for item in items:
            if len(results) >= limit:
                break

            href = item.get("href", "")
            if "/form" in href or "type=regist" in href:
                continue

            title_tag = item.select_one('span[class*="text-14"]')
            price_tag = item.select_one('span[class*="text-18"]')
            img_tag = item.select_one("img")

            if not title_tag:
                continue

            link = href if href.startswith("http") else "https://web.joongna.com" + href
            results.append(
                {
                    "platform": "중고나라",
                    "title": title_tag.get_text(strip=True),
                    "price": _clean_price(price_tag.get_text(" ", strip=True) if price_tag else ""),
                    "link": link,
                    "image": img_tag.get("src", "") if img_tag else "",
                }
            )
    except Exception as e:
        print(f"[중고나라] 수집 실패: {e}")

    return results
