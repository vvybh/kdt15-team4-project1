from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from crawlers.base import RawMarketItem, crawled_now, empty_result
from services.normalize_service import normalize_price, sanitize_public_text


BASE_URL = "https://web.joongna.com"
PRODUCT_RE = re.compile(r"/product/(\d+)")


@dataclass
class JoongnaCrawlerOptions:
    limit: int = 10
    delay_seconds: float = 0.7
    timeout_seconds: int = 20
    product_urls: list[str] | None = None


class JoongnaCrawler:
    source = "joongna"

    def __init__(self, options: JoongnaCrawlerOptions | None = None):
        self.options = options or JoongnaCrawlerOptions()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36"
                ),
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7",
            }
        )

    def crawl(self, keyword: str, category: str = "") -> list[RawMarketItem]:
        urls = self.options.product_urls or self._collect_product_urls(keyword, category)
        results: list[RawMarketItem] = []
        for index, url in enumerate(urls[: self.options.limit]):
            if index:
                time.sleep(self.options.delay_seconds)
            try:
                html = self._get(url)
                results.append(parse_product_html(html, url, keyword))
            except Exception:
                continue
        return results or empty_result(self.source, keyword)

    def _collect_product_urls(self, keyword: str, category: str = "") -> list[str]:
        direct_urls = extract_product_urls(keyword)
        if direct_urls:
            return direct_urls

        search_url = f"{BASE_URL}/search/{quote(keyword)}"
        if category.isdigit():
            search_url = f"{search_url}?category={category}"
        html = self._get(search_url)
        return extract_product_urls(html)

    def _get(self, url: str) -> str:
        response = self.session.get(url, timeout=self.options.timeout_seconds)
        response.raise_for_status()
        response.encoding = "utf-8"
        return response.text


def extract_product_urls(text: str) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for match in PRODUCT_RE.finditer(text or ""):
        url = urljoin(BASE_URL, f"/product/{match.group(1)}")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def parse_product_html(html: str, url: str, keyword: str = "") -> RawMarketItem:
    soup = BeautifulSoup(html, "html.parser")
    product = _extract_json_ld_product(soup)
    source_item_id = _source_item_id(url, product)
    title = product.get("name") or _meta_content(soup, "og:title") or _title_text(soup)
    price = _offer_value(product, "price") or normalize_price(_visible_price_text(soup))
    raw_status = _trade_status(product, soup)
    item_condition, components = _condition_and_components(product, soup)
    source_category = _source_category(soup)
    description = sanitize_public_text(product.get("description") or _meta_content(soup, "og:description"))
    image_url = _first_image(product) or _meta_content(soup, "og:image")
    shipping_fee = _shipping_fee(soup)
    trade_method = _trade_method(soup)
    crawled_at = crawled_now()

    payload = {
        "collected_keyword": keyword,
        "title": title,
        "price": price,
        "currency": _offer_value(product, "priceCurrency") or "KRW",
        "trade_status": raw_status,
        "source_category": source_category,
        "item_condition": item_condition,
        "components": components,
        "shipping_fee": shipping_fee,
        "trade_method": trade_method,
        "image_url": image_url,
        "description": description,
        "location": "",
    }
    return RawMarketItem(
        source="joongna",
        source_item_id=source_item_id,
        source_url=url,
        raw_title=title,
        raw_price=f"{price}원" if price else "",
        raw_status=raw_status,
        raw_location="",
        raw_date="",
        raw_payload=payload,
        crawled_at=crawled_at,
    )


def _extract_json_ld_product(soup: BeautifulSoup) -> dict:
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or script.get_text() or "{}")
        except json.JSONDecodeError:
            continue
        candidates = data if isinstance(data, list) else [data]
        for candidate in candidates:
            if isinstance(candidate, dict) and candidate.get("@type") == "Product":
                return candidate
    return {}


def _source_item_id(url: str, product: dict) -> str:
    match = PRODUCT_RE.search(url)
    return str(product.get("sku") or product.get("gtin") or (match.group(1) if match else ""))


def _offer_value(product: dict, key: str):
    offers = product.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    return offers.get(key) if isinstance(offers, dict) else None


def _trade_status(product: dict, soup: BeautifulSoup) -> str:
    text = _visible_text(soup)
    availability = str(_offer_value(product, "availability") or "")
    if "예약중" in text and "판매완료" not in text:
        return "예약중"
    if "SoldOut" in availability:
        return "판매완료"
    if "InStock" in availability:
        return "판매중"
    if "PreOrder" in availability:
        return "예약중"
    return "거래상태확인필요"


def _condition_and_components(product: dict, soup: BeautifulSoup) -> tuple[str, str]:
    value = _line_after(soup, "상품 상태")
    if not value:
        item_condition = str(product.get("itemCondition") or _offer_value(product, "itemCondition") or "")
        value = _schema_condition_label(item_condition)
    if "," in value:
        item_condition, components = [part.strip() for part in value.split(",", 1)]
        return item_condition, components
    return value, ""


def _schema_condition_label(value: str) -> str:
    if "NewCondition" in value:
        return "새상품"
    if "UsedCondition" in value:
        return "중고"
    return ""


def _source_category(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if not h1:
        return ""
    breadcrumbs = h1.find_previous("ul")
    if not breadcrumbs:
        return ""
    values = [
        link.get_text(strip=True)
        for link in breadcrumbs.find_all("a", href=re.compile(r"^/search\?category="))
        if link.get_text(strip=True) and link.get_text(strip=True) != "홈"
    ]
    return " > ".join(values[-3:])


def _shipping_fee(soup: BeautifulSoup) -> str:
    text = _visible_text(soup)
    match = re.search(r"배송비\s*([0-9,]+원|무료|별도)", text)
    return match.group(1) if match else ""


def _trade_method(soup: BeautifulSoup) -> str:
    text = _visible_text(soup)
    methods = []
    if "택배거래" in text:
        methods.append("택배거래")
    if "직거래" in text:
        methods.append("직거래")
    return ", ".join(methods)


def _visible_price_text(soup: BeautifulSoup) -> str:
    match = re.search(r"([0-9,]+원)", _visible_text(soup))
    return match.group(1) if match else ""


def _line_after(soup: BeautifulSoup, label: str) -> str:
    lines = _visible_lines(soup)
    for index, line in enumerate(lines):
        if line == label and index + 1 < len(lines):
            return lines[index + 1]
    return ""


def _visible_text(soup: BeautifulSoup) -> str:
    return "\n".join(_visible_lines(soup))


def _visible_lines(soup: BeautifulSoup) -> list[str]:
    return [line.strip() for line in soup.get_text("\n").splitlines() if line.strip()]


def _meta_content(soup: BeautifulSoup, property_name: str) -> str:
    tag = soup.find("meta", attrs={"property": property_name}) or soup.find("meta", attrs={"name": property_name})
    return tag.get("content", "").strip() if tag else ""


def _title_text(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.split("|")[0].strip()
    return ""


def _first_image(product: dict) -> str:
    image = product.get("image")
    if isinstance(image, list):
        return image[0] if image else ""
    return str(image or "")
