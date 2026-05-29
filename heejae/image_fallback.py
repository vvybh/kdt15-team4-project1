from __future__ import annotations

from typing import Any


PHOTO_SIZE_QUERY = "?auto=format&fit=crop&w=640&q=80"

DEFAULT_PHOTO = (
    "https://images.unsplash.com/photo-1523275335684-37898b6baf30" + PHOTO_SIZE_QUERY
)

PRODUCT_PHOTO_RULES: list[tuple[tuple[str, ...], str]] = [
    (
        ("아이폰", "iphone", "갤럭시", "galaxy", "스마트폰", "휴대폰", "핸드폰", "z플립", "z폴드"),
        "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9" + PHOTO_SIZE_QUERY,
    ),
    (
        ("아이패드", "ipad", "갤럭시탭", "tablet", "태블릿"),
        "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0" + PHOTO_SIZE_QUERY,
    ),
    (
        ("노트북", "맥북", "macbook", "그램", "갤럭시북", "thinkpad", "laptop"),
        "https://images.unsplash.com/photo-1496181133206-80ce9b88a853" + PHOTO_SIZE_QUERY,
    ),
    (
        ("닌텐도", "스위치", "switch", "플스", "ps5", "ps4", "xbox", "게임기"),
        "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3" + PHOTO_SIZE_QUERY,
    ),
    (
        ("조던", "덩크", "나이키", "아디다스", "이지", "스니커즈", "운동화", "신발", "sneaker"),
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff" + PHOTO_SIZE_QUERY,
    ),
    (
        ("시계", "워치", "watch", "애플워치", "갤럭시워치"),
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30" + PHOTO_SIZE_QUERY,
    ),
    (
        ("가방", "백팩", "토트", "숄더백", "크로스백", "bag"),
        "https://images.unsplash.com/photo-1590874103328-eac38a683ce7" + PHOTO_SIZE_QUERY,
    ),
    (
        ("헤드폰", "이어폰", "에어팟", "버즈", "headphone", "earphone"),
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e" + PHOTO_SIZE_QUERY,
    ),
    (
        ("카메라", "렌즈", "dslr", "미러리스", "camera"),
        "https://images.unsplash.com/photo-1516035069371-29a1b244cc32" + PHOTO_SIZE_QUERY,
    ),
    (
        ("책", "도서", "고서", "문헌", "book"),
        "https://images.unsplash.com/photo-1512820790803-83ca734da794" + PHOTO_SIZE_QUERY,
    ),
    (
        ("그림", "회화", "미술", "서예", "액자", "art", "painting"),
        "https://images.unsplash.com/photo-1578301978693-85fa9c0320b9" + PHOTO_SIZE_QUERY,
    ),
    (
        ("청자", "백자", "도자기", "골동품", "antique", "pottery"),
        "https://images.unsplash.com/photo-1610701596007-11502861dcfa" + PHOTO_SIZE_QUERY,
    ),
    (
        ("소파", "의자", "테이블", "책상", "가구", "furniture"),
        "https://images.unsplash.com/photo-1555041469-a586c61ea9bc" + PHOTO_SIZE_QUERY,
    ),
]


def normalize_image_url(image_url: str | None) -> str:
    if not image_url:
        return ""

    image_url = str(image_url).strip()
    if not image_url or image_url.startswith("data:"):
        return ""
    if image_url.startswith("//"):
        return "https:" + image_url
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return image_url
    return ""


def guess_product_photo(title: str, platform: str = "") -> str:
    searchable = f"{title} {platform}".lower().replace(" ", "")

    for keywords, image_url in PRODUCT_PHOTO_RULES:
        if any(keyword.lower().replace(" ", "") in searchable for keyword in keywords):
            return image_url

    return DEFAULT_PHOTO


def ensure_product_image(item: dict[str, Any]) -> dict[str, Any]:
    copied = dict(item)
    normalized = normalize_image_url(copied.get("image"))
    copied["image"] = normalized or guess_product_photo(
        copied.get("title", ""),
        copied.get("platform", ""),
    )
    return copied


def ensure_product_images(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [ensure_product_image(item) for item in items]
