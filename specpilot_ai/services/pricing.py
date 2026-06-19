from specpilot_ai.core.models import PriceAlertPlan, PriceSnapshot, PurchaseCriteria


def price_competitiveness(price: PriceSnapshot, budget_krw: int) -> float:
    gap_ratio = (price.effective_price_krw - budget_krw) / max(budget_krw, 1)
    if gap_ratio <= -0.12:
        return 100.0
    if gap_ratio <= 0:
        return 92.0 + abs(gap_ratio) * 40
    return max(30.0, 90.0 - gap_ratio * 140)


def purchase_stability(price: PriceSnapshot) -> float:
    base_by_source = {
        "official_store": 92.0,
        "price_compare": 86.0,
        "pc_builder": 84.0,
        "open_market": 78.0,
    }
    score = base_by_source.get(price.source_type, 76.0)
    if price.stock_status == "limited":
        score -= 8.0
    if price.coupon_krw or price.card_discount_krw:
        score -= 2.0
    return max(50.0, score)


def build_price_alerts(
    prices: list[PriceSnapshot],
    criteria: PurchaseCriteria,
    ranked_product_ids: list[str],
) -> list[PriceAlertPlan]:
    budget = criteria.budget_krw or 2_000_000
    price_map = {price.product_id: price for price in prices}
    alerts: list[PriceAlertPlan] = []
    for product_id in ranked_product_ids[:3]:
        price = price_map[product_id]
        target = min(int(budget * 0.97), int(price.effective_price_krw * 0.96))
        if price.effective_price_krw <= budget:
            reason = "예산 안 후보지만 4% 이상 하락하면 즉시 구매 타이밍으로 봅니다."
        else:
            reason = "예산 초과 후보라 목표 예산 근처로 내려올 때만 알림을 보냅니다."
        alerts.append(
            PriceAlertPlan(
                product_id=product_id,
                current_price_krw=price.effective_price_krw,
                target_price_krw=max(0, target),
                recheck_interval_days=3 if criteria.purchase_timing == "within_7_days" else 7,
                channels=["email", "kakao", "webhook"],
                trigger_reason=reason,
            )
        )
    return alerts


def price_timing_message(prices: list[PriceSnapshot], budget_krw: int | None) -> str:
    budget = budget_krw or 2_000_000
    best = min(prices, key=lambda price: price.effective_price_krw)
    within_budget = [price for price in prices if price.effective_price_krw <= budget]
    if within_budget:
        return (
            f"현재 {len(within_budget)}개 후보가 예산 안입니다. "
            "재고 한정/쿠폰 조건은 결제 직전에 다시 확인하세요."
        )
    return (
        f"가장 낮은 실구매가도 {best.effective_price_krw:,}원이라 "
        "목표가 알림을 먼저 설정하는 편이 좋습니다."
    )
