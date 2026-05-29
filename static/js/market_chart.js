(function () {
    function money(value) {
        if (value === null || value === undefined) return "-";
        return `${Number(value).toLocaleString("ko-KR")}원`;
    }

    function sourceLabel(source) {
        const labels = {
            daangn: "당근마켓",
            joongna: "중고나라",
            bunjang: "번개장터",
            kream: "KREAM",
        };
        return labels[source] || source;
    }

    function shippingFee(value) {
        if (value === null || value === undefined || value === "") return "-";
        return money(value);
    }

    function renderSummary(target, summary) {
        target.innerHTML = `
            <div class="summary-grid">
                <div class="summary-item">
                    <span>참고 시세</span>
                    <strong>${money(summary.reference_price)}</strong>
                </div>
                <div class="summary-item">
                    <span>일반 시세 범위</span>
                    <strong>${money(summary.price_range_low)} ~ ${money(summary.price_range_high)}</strong>
                </div>
                <div class="summary-item">
                    <span>추천 시작가</span>
                    <strong>${money(summary.recommended_start_price)}</strong>
                </div>
                <div class="summary-item ${summary.status === "insufficient" ? "warning" : ""}">
                    <span>데이터 기준</span>
                    <strong>${summary.period}, ${summary.sample_count}건</strong>
                </div>
                ${summary.current_bid_label ? `
                    <div class="summary-item">
                        <span>현재 입찰가 판단</span>
                        <strong>${summary.current_bid_label}</strong>
                    </div>
                ` : ""}
                <div class="summary-item">
                    <span>출처</span>
                    <strong>${summary.sources.map(sourceLabel).join(", ") || "-"}</strong>
                </div>
            </div>
        `;
    }

    function renderTable(target, items) {
        if (!target) return;
        if (!items.length) {
            target.innerHTML = `<p class="empty">표시할 가격 데이터가 없습니다.</p>`;
            return;
        }
        const rows = items.map((item) => `
            <tr>
                <td>${item.observed_at}</td>
                <td>${sourceLabel(item.source)}</td>
                <td>${money(item.price)}</td>
                <td>${item.trade_status || "-"}</td>
                <td>${item.item_condition || "-"}</td>
                <td>${item.trade_method || "-"}</td>
                <td>${shippingFee(item.shipping_fee)}</td>
                <td>${item.source_category || "-"}</td>
            </tr>
        `).join("");
        target.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>날짜</th>
                        <th>출처</th>
                        <th>가격</th>
                        <th>상태</th>
                        <th>상품 상태</th>
                        <th>거래 방식</th>
                        <th>배송비</th>
                        <th>원본 카테고리</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    }

    function drawFallback(canvas, items, summary) {
        const context = canvas.getContext("2d");
        const width = canvas.clientWidth || 640;
        const height = canvas.height || 260;
        canvas.width = width;
        canvas.height = height;
        context.clearRect(0, 0, width, height);

        if (!items.length) {
            context.fillStyle = "#69707a";
            context.fillText("데이터가 부족합니다.", 20, 40);
            return;
        }

        const prices = items.map((item) => Number(item.price));
        const min = Math.min(...prices, summary.price_range_low || prices[0]);
        const max = Math.max(...prices, summary.price_range_high || prices[0]);
        const gap = Math.max(max - min, 1);
        const left = 36;
        const right = width - 18;
        const top = 22;
        const bottom = height - 34;

        context.strokeStyle = "#d9dee7";
        context.beginPath();
        context.moveTo(left, top);
        context.lineTo(left, bottom);
        context.lineTo(right, bottom);
        context.stroke();

        context.strokeStyle = "#13795b";
        context.lineWidth = 2;
        context.beginPath();
        items.forEach((item, index) => {
            const x = left + ((right - left) * index) / Math.max(items.length - 1, 1);
            const y = bottom - ((Number(item.price) - min) / gap) * (bottom - top);
            if (index === 0) context.moveTo(x, y);
            else context.lineTo(x, y);
        });
        context.stroke();

        items.forEach((item, index) => {
            const x = left + ((right - left) * index) / Math.max(items.length - 1, 1);
            const y = bottom - ((Number(item.price) - min) / gap) * (bottom - top);
            context.fillStyle = "#2563eb";
            context.beginPath();
            context.arc(x, y, 4, 0, Math.PI * 2);
            context.fill();
        });
    }

    async function renderMarketWidget(widget) {
        const productKey = widget.dataset.productKey;
        if (!productKey) return;

        const currentBid = widget.dataset.currentBid;
        const canvas = widget.querySelector(".market-chart");
        const summaryTarget = widget.querySelector(".market-summary");
        const tableTarget = widget.querySelector(".market-table");
        const params = currentBid ? `?current_bid=${encodeURIComponent(currentBid)}` : "";
        const response = await fetch(`/api/market-price/${encodeURIComponent(productKey)}${params}`);
        const payload = await response.json();
        const items = payload.items || [];
        const summary = payload.summary || {};

        renderSummary(summaryTarget, summary);
        renderTable(tableTarget, items);

        if (widget._chart) {
            widget._chart.destroy();
            widget._chart = null;
        }

        if (window.Chart) {
            widget._chart = new Chart(canvas, {
                type: "line",
                data: {
                    labels: items.map((item) => item.observed_at),
                    datasets: [
                        {
                            label: "가격",
                            data: items.map((item) => item.price),
                            borderColor: "#13795b",
                            backgroundColor: "rgba(19, 121, 91, 0.12)",
                            tension: 0.25,
                            pointRadius: 4,
                        },
                        {
                            label: "참고 시세",
                            data: items.map(() => summary.reference_price),
                            borderColor: "#dc2626",
                            borderDash: [6, 5],
                            pointRadius: 0,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: "bottom" },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => `${ctx.dataset.label}: ${money(ctx.raw)}`,
                            },
                        },
                    },
                    scales: {
                        y: {
                            ticks: {
                                callback: (value) => money(value),
                            },
                        },
                    },
                },
            });
        } else {
            drawFallback(canvas, items, summary);
        }
    }

    window.renderMarketWidget = renderMarketWidget;

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll(".chart-widget").forEach((widget) => {
            renderMarketWidget(widget).catch(() => {
                const target = widget.querySelector(".market-summary");
                if (target) target.innerHTML = `<p class="empty">시세 데이터를 불러오지 못했습니다.</p>`;
            });
        });
    });
})();
