import unittest

from crawlers.joongna import extract_product_urls, parse_product_html


HTML = """
<!doctype html>
<html lang="ko">
<head>
    <title>나이키 후드티 95 | 중고나라</title>
    <meta property="og:image" content="https://img.example/hoodie.jpg">
</head>
<body>
    <ul>
        <li><a href="/search?category=2">패션의류</a></li>
        <li><a href="/search?category=112">남성의류</a></li>
        <li><a href="/search?category=1062">티셔츠/캐쥬얼의류</a></li>
    </ul>
    <h1>나이키 후드티 95</h1>
    <span>13,000원</span>
    <p>배송비 2,000원</p>
    <p>택배거래</p>
    <dl>
        <dt>상품 상태</dt>
        <dd>중고, 구성품 전체 포함</dd>
    </dl>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "나이키 후드티 95",
        "image": ["https://img.example/hoodie.jpg"],
        "description": "상태 좋아요. 연락처 010-1234-5678",
        "sku": "227159992",
        "offers": {
            "price": 13000,
            "priceCurrency": "KRW",
            "availability": "https://schema.org/InStock"
        }
    }
    </script>
</body>
</html>
"""


class JoongnaCrawlerTest(unittest.TestCase):
    def test_extract_product_urls(self):
        urls = extract_product_urls('/product/123 <a href="/product/123"></a> /product/456')

        self.assertEqual(urls, ["https://web.joongna.com/product/123", "https://web.joongna.com/product/456"])

    def test_parse_product_html(self):
        item = parse_product_html(HTML, "https://web.joongna.com/product/227159992", "나이키 후드티")

        self.assertEqual(item.source, "joongna")
        self.assertEqual(item.source_item_id, "227159992")
        self.assertEqual(item.raw_title, "나이키 후드티 95")
        self.assertEqual(item.raw_price, "13000원")
        self.assertEqual(item.raw_status, "판매중")
        self.assertEqual(item.raw_payload["source_category"], "패션의류 > 남성의류 > 티셔츠/캐쥬얼의류")
        self.assertEqual(item.raw_payload["shipping_fee"], "2,000원")
        self.assertEqual(item.raw_payload["trade_method"], "택배거래")
        self.assertIn("[연락처 제외]", item.raw_payload["description"])


if __name__ == "__main__":
    unittest.main()
