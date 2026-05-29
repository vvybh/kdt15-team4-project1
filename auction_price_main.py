from __future__ import annotations

import json
import math
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any

import requests

from bunjang_scraper import search_bunjang
from daangn_scraper import search_daangn
from joongna_scraper import search_joongna
from kream_scraper import search_kream


@dataclass
class ProductItem:
    platform: str
    title: str
    price: int
    link: str
    image: str = ""
    relevance_score: float = 0.0


@dataclass
class PriceAnalysis:
    keyword: str
    category: str
    raw_count: int
    usable_count: int
    outlier_removed_count: int
    confidence: str
    market_price: int
    average_price: int
    min_price: int
    max_price: int
    q1_price: int
    q3_price: int
    expected_bid_low: int
    expected_bid_high: int
    quick_start_price: int
    balanced_start_price: int
    profit_start_price: int
    buy_now_price: int
    best_price_range: str
    platform_summary: dict[str, dict[str, int]]
    price_bins: list[dict[str, Any]]
    sample_items: list[dict[str, Any]]
    seller_message: str
    buyer_message: str


class IntegratedScraper:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        self.exclude_keywords = [
            "삽니다",
            "구합니다",
            "매입",
            "교환",
            "대차",
            "렌탈",
            "대여",
            "수리",
            "부품용",
            "고장",
            "파손",
            "액정깨짐",
            "케이스",
            "필름",
            "충전기",
            "거치대",
            "파우치",
            "박스만",
            "공기계 매입",
        ]

        self.category_profiles = {
            "smartphone": {
                "label": "스마트폰",
                "aliases": ["아이폰", "갤럭시", "iphone", "galaxy", "z플립", "z폴드"],
                "exclude": ["케이스", "필름", "충전기", "카드지갑", "스트랩"],
            },
            "tablet": {
                "label": "태블릿",
                "aliases": ["아이패드", "갤럭시탭", "ipad", "tablet", "탭"],
                "exclude": ["펜촉", "케이스", "필름", "키보드만", "거치대"],
            },
            "laptop": {
                "label": "노트북",
                "aliases": ["노트북", "맥북", "그램", "갤럭시북", "thinkpad", "macbook"],
                "exclude": ["파우치", "거치대", "충전기", "키보드", "마우스", "부품"],
            },
            "game_console": {
                "label": "게임기",
                "aliases": ["닌텐도", "스위치", "플스", "ps5", "ps4", "xbox"],
                "exclude": ["칩만", "타이틀만", "케이스", "보호필름", "스틱커버"],
            },
            "sneakers": {
                "label": "스니커즈",
                "aliases": ["조던", "덩크", "나이키", "아디다스", "이지", "air jordan"],
                "exclude": ["박스만", "끈", "슈트리", "깔창"],
            },
            "general": {
                "label": "일반",
                "aliases": [],
                "exclude": [],
            },
        }

    def get_combined_results(
        self,
        keyword: str,
        page: int = 1,
        platform: str = "all",
        sort: str = "price_asc",
        limit_per_platform: int = 30,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        if platform in ["all", "joongna"]:
            results.extend(search_joongna(keyword, page, limit_per_platform, self.headers, self.session))
        if platform in ["all", "bunjang"]:
            results.extend(search_bunjang(keyword, page, limit_per_platform, self.headers, self.session))
        if platform in ["all", "daangn"]:
            results.extend(search_daangn(keyword, page, limit_per_platform, self.headers, self.session))
        if platform in ["all", "kream"]:
            results.extend(search_kream(keyword, page, limit_per_platform, self.headers, self.session))

        if sort == "price_asc":
            results.sort(key=lambda x: x["price"] if x["price"] > 0 else 999999999)
        elif sort == "price_desc":
            results.sort(key=lambda x: x["price"], reverse=True)

        return results

    def analyze_for_auction(
        self,
        keyword: str,
        category: str = "auto",
        platform: str = "all",
        page: int = 1,
        limit_per_platform: int = 30,
    ) -> dict[str, Any]:
        detected_category = self.detect_category(keyword) if category == "auto" else category
        raw_items = [
            ProductItem(**item)
            for item in self.get_combined_results(
                keyword=keyword,
                page=page,
                platform=platform,
                sort="price_asc",
                limit_per_platform=limit_per_platform,
            )
        ]
        usable_items = self.filter_usable_items(raw_items, keyword, detected_category)
        analysis = self.build_price_analysis(keyword, detected_category, raw_items, usable_items)
        return asdict(analysis)

    def filter_usable_items(
        self,
        items: list[ProductItem],
        keyword: str,
        category: str = "general",
        min_relevance: float = 0.5,
    ) -> list[ProductItem]:
        filtered: list[ProductItem] = []
        category_excludes = self.category_profiles.get(category, self.category_profiles["general"])["exclude"]

        for item in items:
            if item.price <= 0:
                continue
            if self._should_filter(item.title, category_excludes):
                continue

            score = self._relevance_score(keyword, item.title)
            if score < min_relevance:
                continue

            item.relevance_score = score
            filtered.append(item)

        return filtered

    def build_price_analysis(
        self,
        keyword: str,
        category: str,
        raw_items: list[ProductItem],
        usable_items: list[ProductItem],
    ) -> PriceAnalysis:
        cleaned_items = self._remove_price_outliers(usable_items)
        prices = [item.price for item in cleaned_items]

        if not prices:
            return PriceAnalysis(
                keyword=keyword,
                category=self._category_label(category),
                raw_count=len(raw_items),
                usable_count=0,
                outlier_removed_count=len(usable_items),
                confidence="부족",
                market_price=0,
                average_price=0,
                min_price=0,
                max_price=0,
                q1_price=0,
                q3_price=0,
                expected_bid_low=0,
                expected_bid_high=0,
                quick_start_price=0,
                balanced_start_price=0,
                profit_start_price=0,
                buy_now_price=0,
                best_price_range="분석 불가",
                platform_summary={},
                price_bins=[],
                sample_items=[],
                seller_message="유사 상품 데이터가 부족해 추천가를 계산할 수 없습니다.",
                buyer_message="시세 판단에 필요한 외부 데이터가 부족합니다.",
            )

        q1 = self._percentile(prices, 25)
        q3 = self._percentile(prices, 75)
        median = int(statistics.median(prices))
        average = int(statistics.mean(prices))
        best_range, price_bins = self._build_price_bins(prices)

        confidence = self._confidence_label(len(prices))
        quick_start = self._round_price(median * 0.65)
        balanced_start = self._round_price(median * 0.75)
        profit_start = self._round_price(median * 0.85)
        buy_now = self._round_price(median * 1.05)

        return PriceAnalysis(
            keyword=keyword,
            category=self._category_label(category),
            raw_count=len(raw_items),
            usable_count=len(prices),
            outlier_removed_count=max(len(usable_items) - len(cleaned_items), 0),
            confidence=confidence,
            market_price=self._round_price(median),
            average_price=self._round_price(average),
            min_price=min(prices),
            max_price=max(prices),
            q1_price=self._round_price(q1),
            q3_price=self._round_price(q3),
            expected_bid_low=self._round_price(q1),
            expected_bid_high=self._round_price(q3),
            quick_start_price=quick_start,
            balanced_start_price=balanced_start,
            profit_start_price=profit_start,
            buy_now_price=buy_now,
            best_price_range=best_range,
            platform_summary=self._platform_summary(cleaned_items),
            price_bins=price_bins,
            sample_items=[asdict(item) for item in cleaned_items[:10]],
            seller_message=(
                f"'{keyword}' 유사 상품은 {best_range}에 가장 많이 분포합니다. "
                f"균형 판매 전략 기준 시작가는 {balanced_start:,}원, "
                f"예상 낙찰가는 {self._round_price(q1):,}원~{self._round_price(q3):,}원입니다."
            ),
            buyer_message=(
                f"외부 시세 중앙값은 {self._round_price(median):,}원입니다. "
                f"{self._round_price(q3):,}원 이하라면 일반 시세 범위 안의 입찰로 볼 수 있습니다."
            ),
        )

    def evaluate_bid(self, current_bid: int, analysis: dict[str, Any]) -> dict[str, Any]:
        market_price = analysis.get("market_price", 0)
        q1 = analysis.get("q1_price", 0)
        q3 = analysis.get("q3_price", 0)

        if not market_price:
            return {
                "attractiveness": "판단 불가",
                "price_gap_rate": 0,
                "message": "시세 데이터가 부족해 현재 입찰가를 평가할 수 없습니다.",
            }

        gap_rate = round((market_price - current_bid) / market_price * 100, 1)

        if current_bid <= q1:
            attractiveness = "높음"
            message = "현재 입찰가는 유사 상품 시세보다 낮은 편입니다."
        elif current_bid <= q3:
            attractiveness = "보통"
            message = "현재 입찰가는 일반적인 시세 범위 안에 있습니다."
        else:
            attractiveness = "낮음"
            message = "현재 입찰가는 시세 상단보다 높아 신중한 입찰이 필요합니다."

        return {
            "attractiveness": attractiveness,
            "price_gap_rate": gap_rate,
            "message": message,
        }

    def detect_category(self, keyword: str) -> str:
        normalized = keyword.lower()
        for category, profile in self.category_profiles.items():
            if category == "general":
                continue
            if any(alias.lower() in normalized for alias in profile["aliases"]):
                return category
        return "general"

    def _should_filter(self, title: str, extra_excludes: list[str] | None = None) -> bool:
        words = self.exclude_keywords + (extra_excludes or [])
        normalized = title.replace(" ", "").lower()
        return any(word.replace(" ", "").lower() in normalized for word in words)

    def _tokenize(self, text: str) -> list[str]:
        normalized = re.sub(r"[^0-9a-zA-Z가-힣]+", " ", text.lower())
        return [token for token in normalized.split() if len(token) >= 2]

    def _relevance_score(self, keyword: str, title: str) -> float:
        keyword_tokens = self._tokenize(keyword)
        title_tokens = self._tokenize(title)
        title_text = " ".join(title_tokens)

        if not keyword_tokens:
            return 0.0

        matched = 0
        for token in keyword_tokens:
            if token in title_tokens or token in title_text:
                matched += 1

        return matched / len(keyword_tokens)

    def _remove_price_outliers(self, items: list[ProductItem]) -> list[ProductItem]:
        if len(items) < 5:
            return items

        prices = [item.price for item in items]
        q1 = self._percentile(prices, 25)
        q3 = self._percentile(prices, 75)
        iqr = q3 - q1

        if iqr <= 0:
            return items

        lower = max(q1 - 1.5 * iqr, 1000)
        upper = q3 + 1.5 * iqr
        return [item for item in items if lower <= item.price <= upper]

    def _percentile(self, values: list[int], percentile: int) -> int:
        if not values:
            return 0

        sorted_values = sorted(values)
        index = (len(sorted_values) - 1) * percentile / 100
        lower = math.floor(index)
        upper = math.ceil(index)

        if lower == upper:
            return int(sorted_values[int(index)])

        weight = index - lower
        return int(sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight)

    def _round_price(self, price: float) -> int:
        if price <= 0:
            return 0
        if price >= 100000:
            unit = 10000
        elif price >= 10000:
            unit = 1000
        else:
            unit = 100
        return int(round(price / unit) * unit)

    def _build_price_bins(self, prices: list[int]) -> tuple[str, list[dict[str, Any]]]:
        if not prices:
            return "분석 불가", []

        median = statistics.median(prices)
        if median >= 1000000:
            unit = 100000
        elif median >= 100000:
            unit = 50000
        elif median >= 10000:
            unit = 10000
        else:
            unit = 1000

        counter: Counter[int] = Counter((price // unit) * unit for price in prices)
        bins = []

        for start, count in sorted(counter.items()):
            end = start + unit - 1
            bins.append(
                {
                    "range": f"{start:,}원~{end:,}원",
                    "start": start,
                    "end": end,
                    "count": count,
                }
            )

        best = max(bins, key=lambda x: x["count"])
        return best["range"], bins

    def _platform_summary(self, items: list[ProductItem]) -> dict[str, dict[str, int]]:
        grouped: dict[str, list[int]] = defaultdict(list)
        for item in items:
            grouped[item.platform].append(item.price)

        summary = {}
        for platform, prices in grouped.items():
            summary[platform] = {
                "count": len(prices),
                "median": self._round_price(statistics.median(prices)),
                "average": self._round_price(statistics.mean(prices)),
                "min": min(prices),
                "max": max(prices),
            }

        return summary

    def _confidence_label(self, usable_count: int) -> str:
        if usable_count >= 30:
            return "높음"
        if usable_count >= 15:
            return "보통"
        if usable_count >= 7:
            return "낮음"
        if usable_count >= 3:
            return "참고용"
        return "부족"

    def _category_label(self, category: str) -> str:
        return self.category_profiles.get(category, self.category_profiles["general"])["label"]


def print_analysis(analysis: dict[str, Any]) -> None:
    print("\n" + "=" * 70)
    print(f"[{analysis['keyword']}] 경매 가격 분석 결과")
    print("=" * 70)
    print(f"카테고리: {analysis['category']}")
    print(f"수집 상품 수: {analysis['raw_count']}개")
    print(f"분석 사용 상품 수: {analysis['usable_count']}개")
    print(f"이상치 제외 수: {analysis['outlier_removed_count']}개")
    print(f"신뢰도: {analysis['confidence']}")

    if analysis["usable_count"] == 0:
        print(analysis["seller_message"])
        return

    print("\n[시세 요약]")
    print(f"시세 중앙값: {analysis['market_price']:,}원")
    print(f"평균 가격: {analysis['average_price']:,}원")
    print(f"일반 거래 구간: {analysis['q1_price']:,}원~{analysis['q3_price']:,}원")
    print(f"가장 많이 분포한 가격대: {analysis['best_price_range']}")

    print("\n[판매자 추천]")
    print(f"빠른 판매 시작가: {analysis['quick_start_price']:,}원")
    print(f"균형 판매 시작가: {analysis['balanced_start_price']:,}원")
    print(f"수익 우선 시작가: {analysis['profit_start_price']:,}원")
    print(f"예상 낙찰가: {analysis['expected_bid_low']:,}원~{analysis['expected_bid_high']:,}원")
    print(f"즉시구매 추천가: {analysis['buy_now_price']:,}원")
    print(f"설명: {analysis['seller_message']}")

    print("\n[구매자 정보]")
    print(analysis["buyer_message"])

    print("\n[플랫폼별 요약]")
    for platform, summary in analysis["platform_summary"].items():
        print(
            f"- {platform}: {summary['count']}개, "
            f"중앙값 {summary['median']:,}원, "
            f"범위 {summary['min']:,}원~{summary['max']:,}원"
        )

    print("\n[분석에 사용된 유사 상품 예시]")
    for idx, item in enumerate(analysis["sample_items"][:5], 1):
        print(f"{idx}. [{item['platform']}] {item['price']:,}원 | {item['title']}")


if __name__ == "__main__":
    scraper = IntegratedScraper()

    print("=" * 70)
    print("중고 경매 적정가 추천용 통합 스크래퍼")
    print("예시 검색어: 아이폰 14 128GB, 아이패드 에어 5세대, 닌텐도 스위치 OLED")
    print("종료하려면 q 또는 quit 입력")
    print("=" * 70)

    while True:
        user_keyword = input("\n검색할 상품명을 입력하세요: ").strip()

        if user_keyword.lower() in ["q", "quit", "exit", "종료"]:
            print("검색을 종료합니다.")
            break

        if not user_keyword:
            print("검색어를 입력해야 합니다.")
            continue

        print(f"\n'{user_keyword}' 외부 중고거래 데이터를 수집하고 가격을 분석합니다...")
        result = scraper.analyze_for_auction(user_keyword, category="auto", platform="all")
        print_analysis(result)

        save = input("\n분석 결과를 JSON으로 저장할까요? (y/N): ").strip().lower()
        if save == "y":
            filename = f"auction_price_analysis_{re.sub(r'[^0-9a-zA-Z가-힣]+', '_', user_keyword)}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"저장 완료: {filename}")
