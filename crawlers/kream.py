from __future__ import annotations

from crawlers.base import RawMarketItem


class KreamCrawler:
    source = "kream"

    def crawl(self, keyword: str, category: str = "") -> list[RawMarketItem]:
        raise NotImplementedError("KREAM 크롤링은 사이트 정책 최종 확인 뒤 구현합니다.")
