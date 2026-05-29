from __future__ import annotations

from crawlers.base import RawMarketItem


class BunjangCrawler:
    source = "bunjang"

    def crawl(self, keyword: str, category: str = "") -> list[RawMarketItem]:
        raise NotImplementedError("번개장터 크롤링은 사이트 정책 최종 확인 뒤 구현합니다.")
