import unittest
from urllib.parse import quote

from app import create_app


class AppSmokeTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True})
        self.client = self.app.test_client()

    def test_core_pages_load(self):
        for path in ["/", "/auctions", "/auctions/new", "/market", "/admin/inspections"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)

    def test_market_price_api_returns_sample_data(self):
        product_key = quote("의류:nike:후드티")

        response = self.client.get(f"/api/market-price/{product_key}")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(payload["summary"]["sample_count"], 5)
        self.assertEqual(payload["summary"]["status"], "enough")
        self.assertGreaterEqual(len(payload["items"]), 5)

    def test_auction_detail_loads(self):
        response = self.client.get("/auctions/1")

        self.assertEqual(response.status_code, 200)
        self.assertIn("현재 입찰가".encode("utf-8"), response.data)

    def test_homepage_is_demo_dashboard(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("경매 웹사이트 데모".encode("utf-8"), response.data)
        self.assertIn("시연 흐름".encode("utf-8"), response.data)
        self.assertIn(b"/static/vendor/chart.umd.min.js", response.data)

    def test_auction_list_uses_website_list_layout(self):
        response = self.client.get("/auctions")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"auction-board", response.data)
        self.assertIn("새 물품 등록".encode("utf-8"), response.data)


if __name__ == "__main__":
    unittest.main()
