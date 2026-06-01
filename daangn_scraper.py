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


def _guess_title_from_text(text: str, price_text: str) -> str:
    title = text.split(price_text)[0].strip()
    if not title:
        title = text[:80].strip()
    return title[:100]


def search_daangn(
    keyword: str,
    page: int = 1,
    limit: int = 30,
    headers: dict[str, str] | None = None,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://www.daangn.com/search/{encoded_keyword}"
    client = session or requests.Session()
    results: list[dict[str, Any]] = []

    try:
        res = client.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")

        candidates = soup.select("article, a[href*='/articles/'], div")
        seen_links: set[str] = set()

        for item in candidates:
            if len(results) >= limit:
                break

            text = item.get_text(" ", strip=True)
            if not text or keyword.split()[0] not in text:
                continue

            price_match = re.search(r"(\d[\d,]*)\s*원", text)
            if not price_match:
                continue

            link_tag = item if item.name == "a" else item.select_one("a[href]")
            href = link_tag.get("href", "") if link_tag else ""
            link = href if href.startswith("http") else "https://www.daangn.com" + href

            if link in seen_links:
                continue
            seen_links.add(link)

            img_tag = item.select_one("img")
            price_text = price_match.group(0)
            results.append(
                {
                    "platform": "당근마켓",
                    "title": _guess_title_from_text(text, price_text),
                    "price": _clean_price(price_text),
                    "link": link,
                    "image": img_tag.get("src", "") if img_tag else "",
                }
            )
    except Exception as e:
        print(f"[당근마켓] 수집 실패: {e}")

    return results
