from __future__ import annotations

from crawlers.base import RawMarketItem


class DaangnCrawler:
    source = "daangn"

    def crawl(self, keyword: str, category: str = "") -> list[RawMarketItem]:
        raise NotImplementedError("당근마켓 크롤링은 사이트 정책 최종 확인 뒤 구현합니다.")
