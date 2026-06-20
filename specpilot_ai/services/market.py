from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    CategoryMarketReport,
    CheckStatus,
    MarketPriceSegment,
    MarketReportPick,
    MarketRiskSignal,
    MarketTrendCard,
    OperationsMetrics,
    ProductCandidate,
)
from specpilot_ai.data.catalog import desktop_candidates, laptop_candidates, price_snapshot_for
from specpilot_ai.services.evidence import benchmarks_for, review_for
from specpilot_ai.services.pricing import purchase_stability


def build_category_market_report(
    *,
    workspace_id: str,
    metrics: OperationsMetrics,
    category_filter: Category | None = None,
    generated_at: datetime | None = None,
) -> CategoryMarketReport:
    generated_at = generated_at or datetime.now(UTC)
    candidates = _market_candidates(category_filter)
    picks = _market_picks(candidates, generated_at)
    price_segments = _price_segments(candidates, generated_at)
    risk_signals = _risk_signals(candidates, generated_at)
    trend_cards = _trend_cards(candidates, category_filter, metrics)
    return CategoryMarketReport(
        workspace_id=workspace_id,
        generated_at=generated_at.isoformat(),
        report_month=generated_at.strftime("%Y-%m"),
        category_filter=category_filter,
        headline=_headline(category_filter, generated_at),
        summary=_summary(category_filter, len(candidates), risk_signals, metrics),
        total_candidates=len(candidates),
        picks=picks,
        price_segments=price_segments,
        risk_signals=risk_signals,
        trend_cards=trend_cards,
        workspace_signals=_workspace_signals(metrics),
        publishing_checklist=_publishing_checklist(metrics, risk_signals),
    )


def _market_candidates(category_filter: Category | None) -> list[ProductCandidate]:
    if category_filter == Category.desktop_pc:
        return desktop_candidates()
    if category_filter == Category.laptop:
        return laptop_candidates()
    return [*desktop_candidates(), *laptop_candidates()]


def _market_picks(
    candidates: list[ProductCandidate],
    generated_at: datetime,
) -> list[MarketReportPick]:
    captured_at = generated_at.isoformat()
    ranked = sorted(
        candidates,
        key=lambda product: _market_score(product, captured_at),
        reverse=True,
    )
    return [
        _market_pick(
            product,
            captured_at,
            role_label=_role_label(index, product),
        )
        for index, product in enumerate(ranked[:6])
    ]


def _market_pick(
    product: ProductCandidate,
    captured_at: str,
    role_label: str,
) -> MarketReportPick:
    price = price_snapshot_for(product, captured_at)
    review = review_for(product)
    benchmarks = benchmarks_for(product)
    risk_status = _pick_risk_status(product, review.trust_score, price.stock_status)
    return MarketReportPick(
        category=product.category,
        product_id=product.id,
        model_name=product.model_name,
        role_label=role_label,
        effective_price_krw=price.effective_price_krw,
        target_price_krw=max(0, int(price.effective_price_krw * 0.96)),
        price_band=_price_band(product.category, price.effective_price_krw),
        stock_status=price.stock_status,
        source_type=price.source_type,
        benchmark_summary=benchmarks[0].summary if benchmarks else "벤치마크 보강 필요",
        risk_status=risk_status,
        fit_tags=product.tags[:4],
        reasons=review.pros[:2],
        watchouts=[*review.risk_signals[:2], *review.cons[:1]][:3],
    )


def _market_score(product: ProductCandidate, captured_at: str) -> float:
    price = price_snapshot_for(product, captured_at)
    review = review_for(product)
    stability = purchase_stability(price)
    price_score = 100 - min(55, price.effective_price_krw / 55_000)
    tag_bonus = min(10, len(product.tags) * 2)
    return round(review.trust_score * 45 + stability * 0.35 + price_score * 0.2 + tag_bonus, 2)


def _price_segments(
    candidates: list[ProductCandidate],
    generated_at: datetime,
) -> list[MarketPriceSegment]:
    captured_at = generated_at.isoformat()
    by_key: dict[tuple[Category, str], list[tuple[ProductCandidate, int]]] = {}
    for product in candidates:
        price = price_snapshot_for(product, captured_at)
        key = (product.category, _price_band(product.category, price.effective_price_krw))
        by_key.setdefault(key, []).append((product, price.effective_price_krw))
    segments: list[MarketPriceSegment] = []
    sorted_segments = sorted(
        by_key.items(),
        key=lambda item: (item[0][0].value, item[1][0][1]),
    )
    for (category, label), rows in sorted_segments:
        prices = [price for _, price in rows]
        segments.append(
            MarketPriceSegment(
                category=category,
                label=label,
                min_price_krw=min(prices),
                max_price_krw=max(prices),
                recommended_budget_krw=int(sum(prices) / len(prices) * 1.03),
                summary=_segment_summary(category, label, len(rows)),
                representative_product_ids=[product.id for product, _ in rows[:3]],
            )
        )
    return segments


def _risk_signals(
    candidates: list[ProductCandidate],
    generated_at: datetime,
) -> list[MarketRiskSignal]:
    captured_at = generated_at.isoformat()
    limited_stock = [
        product
        for product in candidates
        if price_snapshot_for(product, captured_at).stock_status == "limited"
    ]
    low_trust = [product for product in candidates if review_for(product).trust_score < 0.82]
    over_budget = [
        product
        for product in candidates
        if price_snapshot_for(product, captured_at).effective_price_krw >= 2_500_000
    ]
    signals = [
        MarketRiskSignal(
            title="재고/특가 변동",
            status=CheckStatus.warning if limited_stock else CheckStatus.ok,
            affected_product_ids=[product.id for product in limited_stock],
            evidence=(
                f"한정 재고 후보 {len(limited_stock)}개가 가격 재조회 대상입니다."
                if limited_stock
                else "한정 재고 후보가 없어 가격 변동 리스크가 낮습니다."
            ),
            action="특가 후보는 구매 링크 등록 전 URL 모니터 refresh를 실행하세요.",
        ),
        MarketRiskSignal(
            title="리뷰 신뢰 보강",
            status=CheckStatus.warning if low_trust else CheckStatus.ok,
            affected_product_ids=[product.id for product in low_trust],
            evidence=(
                f"리뷰 신뢰도 0.82 미만 후보 {len(low_trust)}개가 있습니다."
                if low_trust
                else "리뷰 신뢰도 차단 후보가 없습니다."
            ),
            action="반복 불만과 출처 수를 보강한 뒤 공개 리포트 추천 문구를 확정하세요.",
        ),
        MarketRiskSignal(
            title="고가 과투자",
            status=CheckStatus.warning if over_budget else CheckStatus.ok,
            affected_product_ids=[product.id for product in over_budget],
            evidence=(
                f"250만원 이상 후보 {len(over_budget)}개는 예산 초과 설명이 필요합니다."
                if over_budget
                else "250만원 이상 과투자 후보가 없습니다."
            ),
            action="고가 후보는 4K/대형 프로젝트 등 명확한 사용 조건에서만 노출하세요.",
        ),
    ]
    return signals


def _trend_cards(
    candidates: list[ProductCandidate],
    category_filter: Category | None,
    metrics: OperationsMetrics,
) -> list[MarketTrendCard]:
    categories = {product.category for product in candidates}
    cards: list[MarketTrendCard] = []
    if Category.desktop_pc in categories:
        cards.append(
            MarketTrendCard(
                title="QHD 크리에이터 PC sweet spot",
                category=Category.desktop_pc,
                signal="RTX 4070급과 32GB RAM 구간이 성능/가격 균형의 중심입니다.",
                evidence=(
                    "데스크톱 후보 중 QHD/영상 편집 태그가 붙은 구성의 "
                    "리뷰 신뢰도가 높습니다."
                ),
                recommendation="200만원 전후 예산에는 4070 SUPER/4070 후보를 먼저 노출하세요.",
            )
        )
    if Category.laptop in categories:
        cards.append(
            MarketTrendCard(
                title="휴대형 크리에이터 노트북 경쟁",
                category=Category.laptop,
                signal="1.5-1.9kg, 32GB RAM, RTX 4050/4060 구간이 구매 검토의 중심입니다.",
                evidence=(
                    "휴대성과 GPU 가속을 동시에 원하는 후보의 가격대가 "
                    "180-220만원에 몰려 있습니다."
                ),
                recommendation=(
                    "출장/편집 사용자는 무게와 발열 경고를 추천 카드 상단에 "
                    "같이 노출하세요."
                ),
            )
        )
    cards.append(
        MarketTrendCard(
            title="워크스페이스 전환 신호",
            category=category_filter,
            signal=(
                f"구매 전환율 {round(metrics.purchase_conversion_rate * 100)}%, "
                f"구매 의향 {round(metrics.purchase_intent_rate * 100)}%"
            ),
            evidence=(
                f"분석 {metrics.analysis_runs}건, 저장 리포트 {metrics.saved_reports}건, "
                f"구매 결과 {metrics.purchase_outcomes}건 기준입니다."
            ),
            recommendation=(
                "표본이 쌓일수록 카테고리 리포트의 추천 순서와 "
                "리스크 문구를 조정하세요."
            ),
        )
    )
    return cards


def _workspace_signals(metrics: OperationsMetrics) -> dict[str, int | float | str]:
    return {
        "analysis_runs": metrics.analysis_runs,
        "saved_reports": metrics.saved_reports,
        "shared_reports": metrics.shared_reports,
        "purchase_outcomes": metrics.purchase_outcomes,
        "purchase_conversion_rate": metrics.purchase_conversion_rate,
        "purchase_intent_rate": metrics.purchase_intent_rate,
        "average_satisfaction": metrics.average_satisfaction,
        "average_quality_score": metrics.average_quality_score,
    }


def _publishing_checklist(
    metrics: OperationsMetrics,
    risk_signals: list[MarketRiskSignal],
) -> list[str]:
    checklist = [
        "상위 추천 후보의 가격, 재고, 쿠폰 조건을 URL 모니터로 재확인하세요.",
        "제휴 구매 링크가 포함되면 같은 후보의 비제휴 대안을 함께 노출하세요.",
        "카테고리 리포트 공개 전 리뷰 신뢰도 warning 후보의 반복 불만 근거를 보강하세요.",
    ]
    if metrics.purchase_outcomes < 5:
        checklist.append(
            "실제 구매 결과 표본이 5건 미만이므로 리포트에 베타 표본 한계를 표시하세요."
        )
    if any(signal.status != CheckStatus.ok for signal in risk_signals):
        checklist.append("warning 리스크 신호는 공개 리포트 상단의 watchout으로 노출하세요.")
    return checklist[:5]


def _headline(category_filter: Category | None, generated_at: datetime) -> str:
    month = generated_at.strftime("%Y-%m")
    if category_filter == Category.desktop_pc:
        return f"{month} 데스크톱 PC 견적 구매 리포트"
    if category_filter == Category.laptop:
        return f"{month} 노트북 구매 리포트"
    return f"{month} 컴퓨터/노트북 구매 시장 리포트"


def _summary(
    category_filter: Category | None,
    candidate_count: int,
    risk_signals: list[MarketRiskSignal],
    metrics: OperationsMetrics,
) -> str:
    warning_count = sum(1 for signal in risk_signals if signal.status != CheckStatus.ok)
    if category_filter == Category.desktop_pc:
        category_label = "데스크톱 PC"
    elif category_filter == Category.laptop:
        category_label = "노트북"
    else:
        category_label = "컴퓨터/노트북"
    return (
        f"{category_label} 후보 {candidate_count}개를 가격대, 추천 역할, 리스크로 묶었습니다. "
        f"warning 리스크 {warning_count}개와 워크스페이스 구매 결과 "
        f"{metrics.purchase_outcomes}건을 함께 반영합니다."
    )


def _role_label(index: int, product: ProductCandidate) -> str:
    if index == 0:
        return "이번 달 우선 추천"
    if "lowest_price" in product.tags or "budget_control" in product.tags:
        return "예산 방어"
    if "creator" in product.tags or "video_editing" in product.tags:
        return "크리에이터"
    if "lightweight" in product.tags or "portable_creator" in product.tags:
        return "휴대성"
    if "premium" in product.tags or "4k_gaming" in product.tags:
        return "프리미엄"
    return "대안 후보"


def _pick_risk_status(
    product: ProductCandidate,
    trust_score: float,
    stock_status: str,
) -> CheckStatus:
    if "over_budget" in product.tags:
        return CheckStatus.warning
    if trust_score < 0.8:
        return CheckStatus.warning
    if stock_status == "limited":
        return CheckStatus.warning
    return CheckStatus.ok


def _price_band(category: Category, effective_price_krw: int) -> str:
    if category == Category.desktop_pc:
        if effective_price_krw < 1_400_000:
            return "입문형"
        if effective_price_krw < 2_150_000:
            return "균형형"
        return "고성능"
    if effective_price_krw < 1_800_000:
        return "휴대/사무형"
    if effective_price_krw < 2_250_000:
        return "크리에이터 균형형"
    return "프리미엄"


def _segment_summary(category: Category, label: str, count: int) -> str:
    if category == Category.desktop_pc and label == "균형형":
        return f"{count}개 후보가 QHD 게임과 영상 편집의 주력 가격대입니다."
    if category == Category.laptop and label == "크리에이터 균형형":
        return f"{count}개 후보가 휴대성과 GPU 가속을 함께 노리는 가격대입니다."
    return f"{count}개 후보가 {label} 구간에 있으며 조건별 타협점을 확인해야 합니다."
