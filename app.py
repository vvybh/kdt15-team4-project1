from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for

from services.auction_service import (
    INSPECTION_STATUSES,
    close_finished_auctions,
    create_auction,
    get_auction,
    get_bids,
    get_inspection,
    get_inspection_rows,
    list_auctions,
    place_bid,
    update_inspection,
)
from services.db import DB_PATH, get_connection, init_database
from services.price_service import build_price_response, list_product_options


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=DB_PATH,
    )
    if test_config:
        app.config.update(test_config)

    init_database(app.config["DATABASE"])

    @app.template_filter("money")
    def money(value):
        if value is None:
            return "-"
        return f"{int(value):,}원"

    @app.template_filter("status_label")
    def status_label(value):
        labels = {
            "active": "진행중",
            "closed": "낙찰 완료",
            "closed_no_bid": "입찰 없이 마감",
        }
        return labels.get(value, value)

    def connect():
        return get_connection(app.config["DATABASE"])

    @app.get("/")
    def index():
        with connect() as conn:
            auctions = list_auctions(conn)[:6]
            products = list_product_options(conn)
        return render_template("index.html", auctions=auctions, products=products)

    @app.get("/market")
    def market_check():
        with connect() as conn:
            products = list_product_options(conn)
        selected_key = request.args.get("product_key") or (products[0]["product_key"] if products else "")
        return render_template("market/check.html", products=products, selected_key=selected_key)

    @app.get("/api/market-price/<path:product_key>")
    def market_price_api(product_key):
        current_bid = request.args.get("current_bid", type=int)
        with connect() as conn:
            payload = build_price_response(conn, product_key, current_bid=current_bid)
        return jsonify(payload)

    @app.get("/auctions")
    def auction_list():
        filters = {
            "query": request.args.get("query", ""),
            "category": request.args.get("category", ""),
            "status": request.args.get("status", ""),
            "min_price": request.args.get("min_price", ""),
            "max_price": request.args.get("max_price", ""),
        }
        with connect() as conn:
            auctions = list_auctions(conn, filters)
            categories = [row["category"] for row in conn.execute("SELECT DISTINCT category FROM auctions ORDER BY category")]
        return render_template("auctions/list.html", auctions=auctions, filters=filters, categories=categories)

    @app.route("/auctions/new", methods=["GET", "POST"])
    def auction_new():
        with connect() as conn:
            products = list_product_options(conn)

        if request.method == "GET":
            selected_key = request.args.get("product_key") or (products[0]["product_key"] if products else "")
            return render_template("auctions/form.html", products=products, selected_key=selected_key, form={})

        required = ["title", "category", "product_key", "seller_name", "start_price", "end_at"]
        missing = [field for field in required if not request.form.get(field)]
        if missing:
            flash("필수 입력값을 확인해 주세요.")
            return render_template(
                "auctions/form.html",
                products=products,
                selected_key=request.form.get("product_key", ""),
                form=request.form,
            ), 400

        try:
            int(request.form["start_price"])
            int(request.form.get("bid_unit") or 1000)
        except ValueError:
            flash("가격과 입찰 단위는 숫자로 입력해 주세요.")
            return render_template(
                "auctions/form.html",
                products=products,
                selected_key=request.form.get("product_key", ""),
                form=request.form,
            ), 400

        with connect() as conn:
            auction_id = create_auction(conn, request.form)
        flash("경매 물품이 등록되었습니다.")
        return redirect(url_for("auction_detail", auction_id=auction_id))

    @app.get("/auctions/<int:auction_id>")
    def auction_detail(auction_id):
        with connect() as conn:
            auction = get_auction(conn, auction_id)
            if not auction:
                abort(404)
            bids = get_bids(conn, auction_id)
            inspection = get_inspection(conn, auction_id)
        return render_template("auctions/detail.html", auction=auction, bids=bids, inspection=inspection)

    @app.post("/auctions/<int:auction_id>/bids")
    def auction_bid(auction_id):
        bidder_name = request.form.get("bidder_name", "").strip()
        bid_amount = request.form.get("bid_amount", type=int)
        if not bidder_name or bid_amount is None:
            flash("입찰자 이름과 입찰가를 입력해 주세요.")
            return redirect(url_for("auction_detail", auction_id=auction_id))

        with connect() as conn:
            ok, message = place_bid(conn, auction_id, bidder_name, bid_amount)
        flash(message)
        return redirect(url_for("auction_detail", auction_id=auction_id))

    @app.post("/auctions/<int:auction_id>/close")
    def auction_close(auction_id):
        with connect() as conn:
            auction = get_auction(conn, auction_id)
            if not auction:
                abort(404)
            close_finished_auctions(conn)
            updated = get_auction(conn, auction_id)
        if updated and updated["status"] == "active":
            flash("아직 경매 마감 시간이 지나지 않았습니다.")
        else:
            flash("경매 마감 상태를 확인했습니다.")
        return redirect(url_for("auction_result", auction_id=auction_id))

    @app.get("/auctions/<int:auction_id>/result")
    def auction_result(auction_id):
        with connect() as conn:
            auction = get_auction(conn, auction_id)
            if not auction:
                abort(404)
            inspection = get_inspection(conn, auction_id)
        return render_template("auctions/result.html", auction=auction, inspection=inspection)

    @app.route("/admin/inspections", methods=["GET", "POST"])
    def admin_inspections():
        with connect() as conn:
            if request.method == "POST":
                auction_id = request.form.get("auction_id", type=int)
                status = request.form.get("status", "")
                note = request.form.get("note", "")
                if auction_id is None:
                    flash("검수 대상이 올바르지 않습니다.")
                else:
                    try:
                        update_inspection(conn, auction_id, status, note)
                        flash("검수 상태가 수정되었습니다.")
                    except ValueError as exc:
                        flash(str(exc))
                return redirect(url_for("admin_inspections"))

            rows = get_inspection_rows(conn)
        return render_template("admin/inspections.html", rows=rows, statuses=INSPECTION_STATUSES)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.context_processor
    def inject_config():
        return {"app_name": "중고 경매 시세 서비스"}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
