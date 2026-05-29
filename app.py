from collections import Counter
from datetime import datetime, timedelta

from flask import Flask, flash, redirect, render_template, request, session, url_for

from market_crawler import analyze_market


app = Flask(__name__)
app.secret_key = "panda-auction-dev-secret"


STATUS_LABELS = {
    "BIDDING": "경매 진행",
    "SOLD": "판매 완료",
    "PAYMENT_WAITING": "결제 대기",
    "SELLER_SHIPPING": "판매자 배송 요청",
    "INSPECTION_WAITING": "검수 대기",
    "DELIVERING": "배송 중",
    "COMPLETED": "거래 완료",
    "CANCELLED": "거래 취소",
}

DURATION_OPTIONS = [1, 3, 7, 15]


def seed_products():
    now = datetime.now()
    return [
        {
            "id": 1,
            "name": "아이폰 15 Pro 256GB",
            "brand": "Apple",
            "category": "디지털",
            "image": "images/product-phone.svg",
            "seller": "민준",
            "start_price": 850000,
            "current_bid": 980000,
            "buy_now_price": 1250000,
            "bid_count": 12,
            "ends_at": now + timedelta(hours=4, minutes=25),
            "description": "생활 기스가 적고 배터리 성능 91%인 자급제 모델입니다.",
            "status": "BIDDING",
            "buyer_state": "-",
            "seller_state": "경매 진행 중",
            "market": {"low": 920000, "avg": 1100000, "high": 1320000},
            "bids": [
                {"bidder": "지우", "amount": 980000, "time": now - timedelta(minutes=18)},
                {"bidder": "서연", "amount": 950000, "time": now - timedelta(hours=1)},
            ],
        },
        {
            "id": 2,
            "name": "WH-1000XM5 헤드폰",
            "brand": "Sony",
            "category": "음향",
            "image": "images/product-headphones.svg",
            "seller": "하린",
            "start_price": 210000,
            "current_bid": 276000,
            "buy_now_price": 340000,
            "bid_count": 9,
            "ends_at": now + timedelta(hours=1, minutes=12),
            "description": "정품 케이스와 케이블 포함, 실내 위주로 사용했습니다.",
            "status": "BIDDING",
            "buyer_state": "-",
            "seller_state": "경매 진행 중",
            "market": {"low": 250000, "avg": 310000, "high": 380000},
            "bids": [
                {"bidder": "도윤", "amount": 276000, "time": now - timedelta(minutes=7)},
                {"bidder": "유나", "amount": 260000, "time": now - timedelta(minutes=42)},
            ],
        },
        {
            "id": 3,
            "name": "X-T30 II 미러리스 바디",
            "brand": "Fujifilm",
            "category": "카메라",
            "image": "images/product-camera.svg",
            "seller": "서준",
            "start_price": 720000,
            "current_bid": 720000,
            "buy_now_price": 930000,
            "bid_count": 0,
            "ends_at": now + timedelta(days=2, hours=3),
            "description": "컷 수가 낮은 바디 단품입니다. 박스와 스트랩 포함입니다.",
            "status": "BIDDING",
            "buyer_state": "-",
            "seller_state": "경매 진행 중",
            "market": {"low": 760000, "avg": 860000, "high": 980000},
            "bids": [],
        },
        {
            "id": 4,
            "name": "애플워치 Series 8",
            "brand": "Apple",
            "category": "웨어러블",
            "image": "images/product-watch.svg",
            "seller": "나은",
            "start_price": 185000,
            "current_bid": 226000,
            "buy_now_price": 280000,
            "bid_count": 6,
            "ends_at": now + timedelta(hours=8, minutes=40),
            "description": "알루미늄 45mm 모델이며 스트랩 2종을 함께 드립니다.",
            "status": "BIDDING",
            "buyer_state": "-",
            "seller_state": "경매 진행 중",
            "market": {"low": 210000, "avg": 265000, "high": 330000},
            "bids": [
                {"bidder": "이안", "amount": 226000, "time": now - timedelta(minutes=29)}
            ],
        },
        {
            "id": 5,
            "name": "가죽 크로스백",
            "brand": "Coach",
            "category": "패션",
            "image": "images/product-bag.svg",
            "seller": "예린",
            "start_price": 90000,
            "current_bid": 116000,
            "buy_now_price": 160000,
            "bid_count": 15,
            "ends_at": now + timedelta(days=1, hours=7),
            "description": "스크래치가 적고 내부 오염 없이 보관 상태가 좋습니다.",
            "status": "BIDDING",
            "buyer_state": "-",
            "seller_state": "경매 진행 중",
            "market": {"low": 110000, "avg": 145000, "high": 190000},
            "bids": [
                {"bidder": "가온", "amount": 116000, "time": now - timedelta(minutes=13)}
            ],
        },
        {
            "id": 6,
            "name": "빈티지 턴테이블",
            "brand": "Technics",
            "category": "취미",
            "image": "images/product-turntable.svg",
            "seller": "태오",
            "start_price": 310000,
            "current_bid": 352000,
            "buy_now_price": 470000,
            "bid_count": 4,
            "ends_at": now + timedelta(days=5, hours=2),
            "description": "속도 보정 완료, 기본 카트리지 포함입니다.",
            "status": "BIDDING",
            "buyer_state": "-",
            "seller_state": "경매 진행 중",
            "market": {},
            "bids": [
                {"bidder": "재윤", "amount": 352000, "time": now - timedelta(hours=3)}
            ],
        },
    ]


products = seed_products()
market_query_counts = Counter()
users = {}


def refresh_product_statuses():
    current_time = datetime.now()
    for product in products:
        if product["status"] == "BIDDING" and current_time >= product["ends_at"]:
            if product["bid_count"] > 0:
                product["status"] = "PAYMENT_WAITING"
                product["buyer_state"] = "결제 대기"
                product["seller_state"] = "상품 배송 요청"
            else:
                product["status"] = "CANCELLED"
                product["buyer_state"] = "-"
                product["seller_state"] = "유찰"


def active_product(product):
    return product["status"] == "BIDDING" and datetime.now() < product["ends_at"]


def get_product(product_id):
    refresh_product_statuses()
    return next((product for product in products if product["id"] == product_id), None)


def parse_price(raw_value):
    try:
        return int(str(raw_value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def has_market_data(product):
    market = product.get("market") or {}
    return all(market.get(key) for key in ("low", "avg", "high")) and market["high"] > market["low"]


def market_position(product, value=None):
    if not has_market_data(product):
        return 50
    market = product["market"]
    price = value if value is not None else product["current_bid"]
    position = (price - market["low"]) / (market["high"] - market["low"]) * 100
    return max(0, min(100, round(position, 1)))


def analysis_position(analysis, value_key):
    if not analysis or not analysis.get("min_price") or not analysis.get("max_price"):
        return 50

    low = analysis["min_price"]
    high = analysis["max_price"]
    value = analysis.get(value_key, 0)
    if high <= low or value <= 0:
        return 50

    position = (value - low) / (high - low) * 100
    return max(0, min(100, round(position, 1)))


def update_matching_market_data(keyword, analysis):
    if not analysis or analysis.get("usable_count", 0) <= 0:
        return

    market = {
        "low": analysis["min_price"],
        "avg": analysis["average_price"],
        "high": analysis["max_price"],
    }
    for product in products:
        if product_matches(product, keyword):
            product["market"] = market


def market_from_analysis(analysis):
    if not analysis or analysis.get("usable_count", 0) <= 0:
        return {}
    return {
        "low": analysis["min_price"],
        "avg": analysis["average_price"],
        "high": analysis["max_price"],
    }


def draft_keyword(draft):
    return " ".join(part for part in [draft.get("brand", ""), draft.get("name", "")] if part).strip()


def load_product_draft():
    draft = session.get("product_draft") or {}
    if not draft.get("name") or not draft.get("brand"):
        return None
    draft.setdefault("image", "images/product-box.svg")
    return draft


def analyze_draft_market(draft, platform):
    keyword = draft_keyword(draft)
    analysis = analyze_market(keyword, platform)
    name_keyword = draft.get("name", "").strip()

    if analysis.get("usable_count", 0) == 0 and name_keyword and name_keyword != keyword:
        fallback = analyze_market(name_keyword, platform)
        if fallback.get("raw_count", 0) > analysis.get("raw_count", 0) or fallback.get("usable_count", 0) > 0:
            return fallback

    return analysis


def remaining_label(product):
    if product["status"] != "BIDDING":
        return STATUS_LABELS.get(product["status"], product["status"])

    remaining = product["ends_at"] - datetime.now()
    if remaining.total_seconds() <= 0:
        return "종료"

    days = remaining.days
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60

    if days:
        return f"{days}일 {hours}시간 남음"
    if hours:
        return f"{hours}시간 {minutes}분 남음"
    return f"{minutes}분 남음"


def below_market(product):
    return has_market_data(product) and product["current_bid"] < product["market"]["avg"]


def product_matches(product, keyword):
    if not keyword:
        return True
    target = f"{product['name']} {product['brand']} {product['category']}".lower()
    return all(token in target for token in keyword.lower().split())


def filtered_products(keyword=None, category=None, active_only=False):
    refresh_product_statuses()
    result = products
    if active_only:
        result = [product for product in result if active_product(product)]
    if keyword:
        result = [product for product in result if product_matches(product, keyword)]
    if category:
        result = [product for product in result if product["category"] == category]
    return result


def popular_product_groups(limit=4):
    current_products = filtered_products(active_only=True)
    closing_soon = sorted(current_products, key=lambda product: product["ends_at"])[:limit]
    most_bid = sorted(current_products, key=lambda product: product["bid_count"], reverse=True)[:limit]
    bargain_products = sorted(
        [product for product in current_products if below_market(product)],
        key=lambda product: product["market"]["avg"] - product["current_bid"],
        reverse=True,
    )[:limit]
    return [
        {"key": "closing", "title": "마감 임박 TOP", "products": closing_soon},
        {"key": "bids", "title": "입찰 많은 TOP", "products": most_bid},
        {"key": "bargain", "title": "시세보다 낮은 TOP", "products": bargain_products},
    ]


def record_market_query(keyword):
    normalized = " ".join(keyword.split())
    if normalized:
        market_query_counts[normalized] += 1


def market_query_rankings(limit=8):
    return [
        {"rank": index + 1, "keyword": keyword, "count": count}
        for index, (keyword, count) in enumerate(market_query_counts.most_common(limit))
    ]


@app.template_filter("won")
def won(value):
    return f"{int(value):,}원"


@app.template_filter("time_text")
def time_text(value):
    return value.strftime("%Y.%m.%d %H:%M")


@app.context_processor
def inject_template_helpers():
    return {
        "active_product": active_product,
        "analysis_position": analysis_position,
        "below_market": below_market,
        "duration_options": DURATION_OPTIONS,
        "has_market_data": has_market_data,
        "market_position": market_position,
        "remaining_label": remaining_label,
        "status_labels": STATUS_LABELS,
    }


@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    current_products = filtered_products(query, active_only=True)
    ranking_groups = popular_product_groups(limit=5)
    closing_soon = ranking_groups[0]["products"]
    most_bid = ranking_groups[1]["products"]
    bargain_products = ranking_groups[2]["products"]

    return render_template(
        "index.html",
        query=query,
        current_products=current_products,
        closing_soon=closing_soon,
        most_bid=most_bid,
        bargain_products=bargain_products,
        ranking_groups=ranking_groups,
    )


@app.route("/products")
def product_list():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    visible_products = filtered_products(query, category or None)
    categories = sorted({product["category"] for product in products})
    return render_template(
        "product_list.html",
        products=visible_products,
        query=query,
        category=category,
        categories=categories,
    )


@app.route("/products/create", methods=["GET", "POST"])
def product_create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        brand = request.form.get("brand", "").strip()
        image = request.form.get("image", "").strip() or "images/product-box.svg"

        if not name or not brand:
            flash("제품명과 브랜드명을 입력해 주세요.", "error")
            return redirect(url_for("product_create"))

        session["product_draft"] = {
            "name": name,
            "brand": brand,
            "image": image,
        }
        flash("상품 기본정보가 저장되었습니다. 시세를 확인한 뒤 금액을 입력해 주세요.", "success")
        return redirect(url_for("product_price"))

    return render_template("product_create.html", draft=load_product_draft())


@app.route("/products/create/price", methods=["GET", "POST"])
def product_price():
    draft = load_product_draft()
    if not draft:
        flash("상품 기본정보를 먼저 입력해 주세요.", "error")
        return redirect(url_for("product_create"))

    platform = request.values.get("platform", "all").strip() or "all"
    keyword = draft_keyword(draft)
    analysis = None
    analysis_error = ""

    try:
        analysis = analyze_draft_market(draft, platform)
    except Exception as exc:
        analysis_error = f"외부 시세 수집 중 오류가 발생했습니다: {exc}"

    if request.method == "POST":
        category = request.form.get("category", "").strip() or "기타"
        description = request.form.get("description", "").strip()
        start_price = parse_price(request.form.get("start_price"))
        buy_now_price = parse_price(request.form.get("buy_now_price"))
        duration = parse_price(request.form.get("duration"))

        if start_price is None or buy_now_price is None:
            flash("경매시작가와 즉시구매가를 입력해 주세요.", "error")
            return render_template(
                "product_price.html",
                draft=draft,
                keyword=keyword,
                platform=platform,
                analysis=analysis,
                analysis_error=analysis_error,
                form_data=request.form,
            )

        if duration not in DURATION_OPTIONS:
            flash("경매 마감 시간은 1일, 3일, 7일, 15일 중에서 선택해 주세요.", "error")
            return render_template(
                "product_price.html",
                draft=draft,
                keyword=keyword,
                platform=platform,
                analysis=analysis,
                analysis_error=analysis_error,
                form_data=request.form,
            )

        if buy_now_price <= start_price:
            flash("즉시구매가는 경매시작가보다 높아야 합니다.", "error")
            return render_template(
                "product_price.html",
                draft=draft,
                keyword=keyword,
                platform=platform,
                analysis=analysis,
                analysis_error=analysis_error,
                form_data=request.form,
            )

        next_id = max(product["id"] for product in products) + 1 if products else 1
        products.append(
            {
                "id": next_id,
                "name": draft["name"],
                "brand": draft["brand"],
                "category": category,
                "image": draft.get("image", "images/product-box.svg"),
                "seller": session.get("username", "판매자"),
                "start_price": start_price,
                "current_bid": start_price,
                "buy_now_price": buy_now_price,
                "bid_count": 0,
                "ends_at": datetime.now() + timedelta(days=duration),
                "description": description or "등록된 상품 설명이 없습니다.",
                "status": "BIDDING",
                "buyer_state": "-",
                "seller_state": "경매 진행 중",
                "market": market_from_analysis(analysis),
                "bids": [],
            }
        )
        session.pop("product_draft", None)
        flash("상품이 등록되었습니다. 시세 확인 결과가 상품 게이지에 반영되었습니다.", "success")
        return redirect(url_for("product_detail", product_id=next_id))

    return render_template(
        "product_price.html",
        draft=draft,
        keyword=keyword,
        platform=platform,
        analysis=analysis,
        analysis_error=analysis_error,
        form_data={},
    )


@app.route("/products/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        flash("상품을 찾을 수 없습니다.", "error")
        return redirect(url_for("product_list"))

    min_bid = product["current_bid"] + 1000
    return render_template("product_detail.html", product=product, min_bid=min_bid)


@app.route("/products/<int:product_id>/bid", methods=["POST"])
def place_bid(product_id):
    product = get_product(product_id)
    if not product:
        flash("상품을 찾을 수 없습니다.", "error")
        return redirect(url_for("product_list"))

    if not active_product(product):
        flash("종료된 경매에는 입찰할 수 없습니다.", "error")
        return redirect(url_for("product_detail", product_id=product_id))

    bidder = request.form.get("bidder", "").strip() or session.get("username", "익명")
    bid_price = parse_price(request.form.get("bid_price"))

    if bid_price is None:
        flash("입찰 금액을 숫자로 입력해 주세요.", "error")
        return redirect(url_for("product_detail", product_id=product_id))

    if bid_price <= product["current_bid"]:
        flash("현재 입찰가보다 높은 금액만 입찰할 수 있습니다.", "error")
        return redirect(url_for("product_detail", product_id=product_id))

    product["current_bid"] = bid_price
    product["bid_count"] += 1
    product["bids"].insert(0, {"bidder": bidder, "amount": bid_price, "time": datetime.now()})
    session["username"] = bidder
    flash("입찰이 완료되었습니다.", "success")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/products/<int:product_id>/buy-now", methods=["POST"])
def buy_now(product_id):
    product = get_product(product_id)
    if not product:
        flash("상품을 찾을 수 없습니다.", "error")
        return redirect(url_for("product_list"))

    if not active_product(product):
        flash("종료된 경매는 즉시구매할 수 없습니다.", "error")
        return redirect(url_for("product_detail", product_id=product_id))

    buyer = request.form.get("buyer", "").strip() or session.get("username", "구매자")
    product["current_bid"] = product["buy_now_price"]
    product["bid_count"] += 1
    product["status"] = "PAYMENT_WAITING"
    product["buyer_state"] = "결제 대기"
    product["seller_state"] = "상품 배송 요청"
    product["bids"].insert(0, {"bidder": buyer, "amount": product["buy_now_price"], "time": datetime.now()})
    session["username"] = buyer
    flash("즉시구매가 완료되었습니다. 구매자는 결제 대기, 판매자는 배송 요청 상태입니다.", "success")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/market")
def market_price():
    query = request.args.get("q", "").strip()
    brand = request.args.get("brand", "").strip()
    platform = request.args.get("platform", "all").strip() or "all"
    results = []
    analysis = None
    analysis_error = ""

    if query or brand:
        keyword = " ".join(part for part in [brand, query] if part).strip()
        record_market_query(keyword)
        results = [product for product in products if product_matches(product, keyword)]
        try:
            analysis = analyze_market(keyword, platform)
            update_matching_market_data(keyword, analysis)
        except Exception as exc:
            analysis_error = f"외부 시세 수집 중 오류가 발생했습니다: {exc}"

    return render_template(
        "market_price.html",
        query=query,
        brand=brand,
        platform=platform,
        results=results,
        analysis=analysis,
        analysis_error=analysis_error,
        query_rankings=market_query_rankings(),
        popular_groups=popular_product_groups(limit=10),
    )


@app.route("/popular")
def popular():
    return redirect(url_for("market_price", _anchor="popular-rankings"))


@app.route("/mypage")
def mypage():
    if not session.get("is_authenticated"):
        flash("마이페이지는 로그인 후 이용할 수 있습니다.", "error")
        return redirect(url_for("login"))

    username = session.get("username")
    my_listings = [product for product in products if product["seller"] == username]
    my_bids = [
        product
        for product in products
        if any(bid["bidder"] == username for bid in product["bids"])
    ]
    return render_template(
        "mypage.html",
        username=username,
        my_listings=my_listings,
        my_bids=my_bids,
        warning_count=1,
        points=1000,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("아이디와 비밀번호를 입력해 주세요.", "error")
            return redirect(url_for("login"))
        if users.get(username) != password:
            flash("아이디 또는 비밀번호가 올바르지 않습니다.", "error")
            return redirect(url_for("login"))
        session["username"] = username
        session["is_authenticated"] = True
        flash("로그인되었습니다.", "success")
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("아이디와 비밀번호를 입력해 주세요.", "error")
            return redirect(url_for("register"))
        if username in users:
            flash("이미 사용 중인 아이디입니다.", "error")
            return redirect(url_for("register"))
        users[username] = password
        session["username"] = username
        session["is_authenticated"] = True
        flash("회원가입이 완료되었습니다.", "success")
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    session.pop("is_authenticated", None)
    flash("로그아웃되었습니다.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
