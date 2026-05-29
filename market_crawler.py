from __future__ import annotations

import math
import re
import statistics
import urllib.parse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any

import requests
from bs4 import BeautifulSoup


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


def _clean_price(price_value: Any) -> int:
    if price_value is None:
        return 0
    digits = "".join(filter(str.isdigit, str(price_value)))
    return int(digits) if digits else 0


def search_bunjang(
    keyword: str,
    page: int = 1,
    limit: int = 12,
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
        response = client.get(api_url, headers=request_headers, timeout=8)
        if response.status_code != 200:
            return results

        for product in response.json().get("list", []):
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
    except Exception:
        return results

    return results[:limit]


def search_joongna(
    keyword: str,
    page: int = 1,
    limit: int = 12,
    headers: dict[str, str] | None = None,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://web.joongna.com/search/{encoded_keyword}?page={page}"
    client = session or requests.Session()
    results: list[dict[str, Any]] = []

    try:
        response = client.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(response.text, "html.parser")

        for item in soup.select('a[href*="/product/"]'):
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
    except Exception:
        return results

    return results


def _guess_daangn_title(text: str, price_text: str) -> str:
    title = text.split(price_text)[0].strip()
    return (title or text[:80].strip())[:100]


def search_daangn(
    keyword: str,
    page: int = 1,
    limit: int = 12,
    headers: dict[str, str] | None = None,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://www.daangn.com/search/{encoded_keyword}"
    client = session or requests.Session()
    results: list[dict[str, Any]] = []

    try:
        response = client.get(url, headers=headers, timeout=8)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        seen_links: set[str] = set()

        for item in soup.select("article, a[href*='/articles/'], div"):
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

            price_text = price_match.group(0)
            img_tag = item.select_one("img")
            results.append(
                {
                    "platform": "당근마켓",
                    "title": _guess_daangn_title(text, price_text),
                    "price": _clean_price(price_text),
                    "link": link,
                    "image": img_tag.get("src", "") if img_tag else "",
                }
            )
    except Exception:
        return results

    return results


def search_kream(
    keyword: str,
    page: int = 1,
    limit: int = 12,
    headers: dict[str, str] | None = None,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://kream.co.kr/search?keyword={encoded_keyword}"
    client = session or requests.Session()
    results: list[dict[str, Any]] = []

    try:
        response = client.get(url, headers=headers, timeout=8)
        if response.status_code != 200:
            return results

        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.select('a[href*="/products/"]'):
            if len(results) >= limit:
                break

            text = item.get_text(" ", strip=True)
            if not text:
                continue

            price_match = re.search(r"(\d[\d,]*)\s*원", text)
            p_tags = [p.get_text(" ", strip=True) for p in item.find_all("p")]
            title_parts = [part for part in p_tags[:3] if part and "원" not in part]
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
    except Exception:
        return results

    return results


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
            "general": {"label": "일반", "aliases": [], "exclude": []},
        }

    def get_combined_results(
        self,
        keyword: str,
        page: int = 1,
        platform: str = "all",
        limit_per_platform: int = 12,
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

        results.sort(key=lambda item: item["price"] if item["price"] > 0 else 999999999)
        return results

    def analyze_for_auction(
        self,
        keyword: str,
        category: str = "auto",
        platform: str = "all",
        limit_per_platform: int = 12,
    ) -> dict[str, Any]:
        detected_category = self.detect_category(keyword) if category == "auto" else category
        raw_items = [
            ProductItem(**item)
            for item in self.get_combined_results(
                keyword=keyword,
                platform=platform,
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
        profile = self.category_profiles.get(category, self.category_profiles["general"])

        for item in items:
            if item.price <= 0:
                continue
            if self._should_filter(item.title, profile["exclude"]):
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
            confidence=self._confidence_label(len(prices)),
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
                f"균형 판매 전략 기준 시작가는 {balanced_start:,}원입니다."
            ),
            buyer_message=(
                f"외부 시세 중앙값은 {self._round_price(median):,}원입니다. "
                f"{self._round_price(q3):,}원 이하라면 일반 시세 범위 안의 입찰로 볼 수 있습니다."
            ),
        )

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
        title_text = " ".join(self._tokenize(title))

        if not keyword_tokens:
            return 0.0

        matched = sum(1 for token in keyword_tokens if token in title_text)
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
        bins = [
            {
                "range": f"{start:,}원~{start + unit - 1:,}원",
                "start": start,
                "end": start + unit - 1,
                "count": count,
            }
            for start, count in sorted(counter.items())
        ]
        best = max(bins, key=lambda item: item["count"])
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


@lru_cache(maxsize=32)
def analyze_market(keyword: str, platform: str = "all") -> dict[str, Any]:
    scraper = IntegratedScraper()
    return scraper.analyze_for_auction(keyword, platform=platform, limit_per_platform=12)
