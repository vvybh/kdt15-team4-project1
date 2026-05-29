from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class RawMarketItem:
    source: str
    source_item_id: str
    source_url: str
    raw_title: str
    raw_price: str
    raw_status: str
    raw_location: str
    raw_date: str
    raw_payload: dict
    crawled_at: str


class MarketCrawler(Protocol):
    source: str

    def crawl(self, keyword: str, category: str = "") -> list[RawMarketItem]:
        ...


def crawled_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def empty_result(source: str, keyword: str) -> list[RawMarketItem]:
    return [
        RawMarketItem(
            source=source,
            source_item_id="",
            source_url="",
            raw_title=keyword,
            raw_price="",
            raw_status="수집 결과 없음",
            raw_location="",
            raw_date="",
            raw_payload={},
            crawled_at=crawled_now(),
        )
    ]
