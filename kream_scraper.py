from __future__ import annotations

import re
import urllib.parse
from typing import Any

import requests
from bs4 import BeautifulSoup


def _clean_price(price_value: Any) -> int:
    if price_value is None:
        return 0
    digits = "".join(filter(str.isdigit, str(price_value)))
    return int(digits) if digits else 0


def search_kream(
    keyword: str,
    page: int = 1,
    limit: int = 30,
    headers: dict[str, str] | None = None,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://kream.co.kr/search?keyword={encoded_keyword}"
    client = session or requests.Session()
    results: list[dict[str, Any]] = []

    try:
        res = client.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return results

        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select('a[href*="/products/"]')

        for item in items:
            if len(results) >= limit:
                break

            text = item.get_text(" ", strip=True)
            if not text:
                continue

            price_match = re.search(r"(\d[\d,]*)\s*원", text)
            p_tags = [p.get_text(" ", strip=True) for p in item.find_all("p")]
            title_parts = [p for p in p_tags[:3] if p and "원" not in p]
            title = " ".join(title_parts) if title_parts else text[:80]
            href = item.get("href", "")
            img_tag = item.select_one("img")

            results.append(
                {
                    "platform": "KREAM",
                    "title": title,
                    "price": _clean_price(price_match.group(0)) if price_match else 0,
                    "link": "https://kream.co.kr" + href,
                    "image": img_tag.get("src", "") if img_tag else "",
                }
            )
    except Exception as e:
        print(f"[KREAM] 수집 실패: {e}")

    return results
