from __future__ import annotations

import re
from html import unescape


def normalize_price(value: str) -> int | None:
    digits = re.sub(r"[^0-9]", "", value or "")
    return int(digits) if digits else None


def normalize_text(value: str) -> str:
    text = unescape(value or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_title(value: str) -> str:
    text = normalize_text(value).lower()
    text = re.sub(r"[^0-9a-zA-Z가-힣\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def sanitize_public_text(value: str, max_length: int = 500) -> str:
    text = normalize_text(value)
    text = re.sub(r"01[016789][-\s.]?\d{3,4}[-\s.]?\d{4}", "[연락처 제외]", text)
    text = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[이메일 제외]", text)
    return text[:max_length]


def build_product_key(category: str, brand: str, product_name: str, model_name: str = "") -> str:
    parts = [category.strip(), brand.strip().lower(), product_name.strip().lower(), model_name.strip().lower()]
    cleaned = [re.sub(r"\s+", "", part) for part in parts if part]
    return ":".join(cleaned)
