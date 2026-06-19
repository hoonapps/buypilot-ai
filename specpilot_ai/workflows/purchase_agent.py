from datetime import UTC, datetime
from typing import TypedDict
from uuid import uuid4

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph

from specpilot_ai.core.models import (
    AgentStep,
    AnalyzeRequest,
    AnalyzeResponse,
    BenchmarkEvidence,
    Category,
    CheckStatus,
    ComparisonRow,
    CompatibilityCheck,
    ExcludedProduct,
    PriceAlertPlan,
    PriceSnapshot,
    ProductCandidate,
    PurchaseCriteria,
    PurchaseDecision,
    PurchaseReport,
    Recommendation,
    ReviewInsight,
    ScenarioOption,
    ScoreCard,
    SourceTrustAssessment,
    TraceEvent,
)
from specpilot_ai.data.catalog import desktop_candidates, laptop_candidates, price_snapshot_for
from specpilot_ai.services.compatibility import (
    build_compatibility_checks,
    compatibility_score,
    compatibility_summary,
)
from specpilot_ai.services.evidence import benchmarks_for, main_risk, review_for, strongest_reason
from specpilot_ai.services.pricing import (
    build_price_alerts,
    price_competitiveness,
    price_timing_message,
    purchase_stability,
)
from specpilot_ai.services.quality import build_quality_audit
from specpilot_ai.services.tracing import trace_event
from specpilot_ai.services.trust import build_source_trust, build_trust_policy


class PurchaseState(TypedDict, total=False):
    request: AnalyzeRequest
    criteria: PurchaseCriteria
    search_plan: list[str]
    candidates: list[ProductCandidate]
    normalized_products: list[ProductCandidate]
    compatibility_notes: list[str]
    compatibility_checks: list[CompatibilityCheck]
    price_snapshots: list[PriceSnapshot]
    review_insights: list[ReviewInsight]
    benchmark_evidence: list[BenchmarkEvidence]
    scorecards: list[ScoreCard]
    citations: list[str]
    verification_flags: list[str]
    report: PurchaseReport
    steps: list[AgentStep]
    trace_events: list[TraceEvent]
    graph_trace_id: str


def _record(state: PurchaseState, step: AgentStep) -> None:
    state.setdefault("steps", []).append(step)


def _trace(
    state: PurchaseState,
    step: AgentStep,
    title: str,
    detail: str,
    *,
    status: CheckStatus = CheckStatus.ok,
    evidence_count: int = 0,
) -> None:
    state.setdefault("trace_events", []).append(
        trace_event(
            step,
            title,
            detail,
            status=status,
            evidence_count=evidence_count,
        )
    )


def intent_parser(state: PurchaseState) -> PurchaseState:
    _record(state, AgentStep.intent_parser)
    request = state["request"]
    state["criteria"] = PurchaseCriteria(
        category=request.category,
        budget_krw=request.budget_krw,
        purpose=request.purpose,
        must_haves=request.must_haves,
        exclusions=request.exclusions,
        purchase_timing=request.purchase_timing,
        channels=request.channels,
    )
    state["graph_trace_id"] = f"trace_{uuid4().hex[:12]}"
    _trace(
        state,
        AgentStep.intent_parser,
        "요청 구조화",
        (
            f"{request.category.value}, 예산 {request.budget_krw or '미입력'}, "
            f"조건 {len(request.must_haves)}개"
        ),
        evidence_count=len(request.must_haves) + len(request.exclusions),
    )
    return state


def clarifier(state: PurchaseState) -> PurchaseState:
    _record(state, AgentStep.clarifier)
    criteria = state["criteria"]
    flags = []
    if criteria.budget_krw is None:
        flags.append("예산이 없어 가격 점수는 기본 200만원 기준으로 계산했습니다.")
    if criteria.category == Category.desktop_pc and not criteria.must_haves:
        flags.append(
            "데스크톱 견적의 필수 부품/해상도 조건이 없어 "
            "범용 게이밍 기준을 적용했습니다."
        )
    state["verification_flags"] = flags
    _trace(
        state,
        AgentStep.clarifier,
        "모호성 점검",
        "추가 질문 없이 분석 가능" if not flags else " / ".join(flags),
        status=CheckStatus.ok if not flags else CheckStatus.warning,
        evidence_count=len(flags),
    )
    return state


def query_planner(state: PurchaseState) -> PurchaseState:
    _record(state, AgentStep.query_planner)
    criteria = state["criteria"]
    channel_list = criteria.channels or ["price_compare", "open_market"]
    state["search_plan"] = [
        f"{criteria.category.value} {criteria.purpose}",
        "cpu gpu motherboard ram ssd psu case compatibility",
        *[f"{condition} {criteria.category.value}" for condition in criteria.must_haves],
        *[f"source:{channel}" for channel in channel_list],
    ]
    _trace(
        state,
        AgentStep.query_planner,
        "검색 계획 생성",
        f"가격/스펙/리뷰/벤치마크 축으로 {len(state['search_plan'])}개 쿼리를 준비했습니다.",
        evidence_count=len(state["search_plan"]),
    )
    return state


def product_collector(state: PurchaseState) -> PurchaseState:
    _record(state, AgentStep.product_collector)
    criteria = state["criteria"]
    state["candidates"] = (
        desktop_candidates()
        if criteria.category == Category.desktop_pc
        else laptop_candidates()
    )
    _trace(
        state,
        AgentStep.product_collector,
        "후보 수집",
        f"{criteria.category.value} 후보 {len(state['candidates'])}개를 수집했습니다.",
        evidence_count=len(state["candidates"]),
    )
    return state


def deduplicator(state: PurchaseState) -> PurchaseState:
    _record(state, AgentStep.deduplicator)
    seen: set[str] = set()
    normalized: list[ProductCandidate] = []
    for candidate in state["candidates"]:
        if candidate.normalized_model in seen:
            continue
        normalized.append(candidate)
        seen.add(candidate.normalized_model)
    state["normalized_products"] = normalized
    _trace(
        state,
        AgentStep.deduplicator,
        "모델 정규화",
        f"중복 제거 후 {len(normalized)}개 후보가 남았습니다.",
        evidence_count=len(normalized),
    )
    return state


def compatibility_checker(state: PurchaseState) -> PurchaseState:
    _record(state, AgentStep.compatibility_checker)
    checks: list[CompatibilityCheck] = []
    notes = []
    for product in state["normalized_products"]:
        product_checks = build_compatibility_checks(product)
        checks.extend(product_checks)
        notes.append(f"{product.model_name}: {compatibility_summary(product_checks)}")
    state["compatibility_checks"] = checks
    state["compatibility_notes"] = notes
    warning_count = sum(check.status != CheckStatus.ok for check in checks)
    _trace(
        state,
        AgentStep.compatibility_checker,
        "호환성 검증",
        f"총 {len(checks)}개 규칙을 확인했고 경고/차단은 {warning_count}개입니다.",
        status=CheckStatus.ok if warning_count == 0 else CheckStatus.warning,
        evidence_count=len(checks),
    )
    return state


def price_tracker(state: PurchaseState) -> PurchaseState:
    _record(state, AgentStep.price_tracker)
    now = datetime.now(UTC).isoformat()
    state["price_snapshots"] = [
        price_snapshot_for(product, now) for product in state["normalized_products"]
    ]
    _trace(
        state,
        AgentStep.price_tracker,
        "실구매가 계산",
        "배송비, 조립비, 쿠폰, 카드 할인까지 반영했습니다.",
        evidence_count=len(state["price_snapshots"]),
    )
    return state


def review_analyzer(state: PurchaseState) -> PurchaseState:
    _record(state, AgentStep.review_analyzer)
    state["review_insights"] = [review_for(product) for product in state["normalized_products"]]
    state["benchmark_evidence"] = [
        item
        for product in state["normalized_products"]
        for item in benchmarks_for(product)
    ]
    state["citations"] = [
        *[product.source_url for product in state["normalized_products"]],
        *[evidence.evidence_url for evidence in state["benchmark_evidence"]],
    ]
    _trace(
        state,
        AgentStep.review_analyzer,
        "리뷰/벤치마크 근거 분석",
        (
            f"리뷰 {len(state['review_insights'])}개와 "
            f"벤치마크 {len(state['benchmark_evidence'])}개를 연결했습니다."
        ),
        evidence_count=sum(review.evidence_count for review in state["review_insights"]),
    )
    return state


def scoring_engine(state: PurchaseState) -> PurchaseState:
    _record(state, AgentStep.scoring_engine)
    prices = {price.product_id: price for price in state["price_snapshots"]}
    reviews = {review.product_id: review for review in state["review_insights"]}
    checks_by_product = _group_by_product(state["compatibility_checks"])
    budget = state["criteria"].budget_krw or 2_000_000
    cards: list[ScoreCard] = []

    for product in state["normalized_products"]:
        price = prices[product.id]
        review = reviews[product.id]
        purpose_fit = _purpose_fit(product, state["criteria"])
        price_score = price_competitiveness(price, budget)
        review_score = review.trust_score * 100
        stability = purchase_stability(price)
        preference = 78 + min(12, len(state["criteria"].must_haves) * 3)
        compatibility = compatibility_score(checks_by_product.get(product.id, []))
        total = (
            purpose_fit * 0.35
            + price_score * 0.22
            + review_score * 0.15
            + stability * 0.1
            + preference * 0.08
            + compatibility * 0.1
        )
        cards.append(
            ScoreCard(
                product_id=product.id,
                purpose_fit=round(purpose_fit, 1),
                price_competitiveness=round(price_score, 1),
                review_trust=round(review_score, 1),
                purchase_stability=round(stability, 1),
                personal_preference=round(preference, 1),
                compatibility=round(compatibility, 1),
                total_score=round(total, 1),
                rationale=(
                    "목적 적합도, 가격, 리뷰 신뢰도, 구매 안정성, "
                    "호환성을 가중 평균했습니다."
                ),
            )
        )
    state["scorecards"] = cards
    _trace(
        state,
        AgentStep.scoring_engine,
        "가중 점수화",
        "목적 35%, 가격 22%, 리뷰 15%, 안정성 10%, 호환성 10%, 선호 8%를 반영했습니다.",
        evidence_count=len(cards),
    )
    return state


def verifier(state: PurchaseState) -> PurchaseState:
    _record(state, AgentStep.verifier)
    flags = state.get("verification_flags", [])
    if len(state["citations"]) < len(state["normalized_products"]):
        flags.append("일부 후보의 출처 링크가 부족합니다.")
    if not state.get("compatibility_notes"):
        flags.append("호환성 검증 결과가 없습니다.")
    if not state.get("benchmark_evidence"):
        flags.append("벤치마크 근거가 부족합니다.")
    stale_or_weak = [
        price
        for price in state["price_snapshots"]
        if price.stock_status not in {"in_stock", "limited"}
    ]
    if stale_or_weak:
        flags.append("일부 가격의 재고 상태가 불명확합니다.")
    state["verification_flags"] = flags or [
        "데모 데이터 기준 가격/출처/호환성/벤치마크 검증을 통과했습니다."
    ]
    _trace(
        state,
        AgentStep.verifier,
        "검증 게이트",
        " / ".join(state["verification_flags"]),
        status=CheckStatus.ok if not flags else CheckStatus.warning,
        evidence_count=len(state["verification_flags"]),
    )
    return state


def report_writer(state: PurchaseState) -> PurchaseState:
    _record(state, AgentStep.report_writer)
    products = {product.id: product for product in state["normalized_products"]}
    prices = {price.product_id: price for price in state["price_snapshots"]}
    reviews = {review.product_id: review for review in state["review_insights"]}
    checks_by_product = _group_by_product(state["compatibility_checks"])
    benchmarks_by_product = _group_by_product(state["benchmark_evidence"])
    ranked = sorted(state["scorecards"], key=lambda card: card.total_score, reverse=True)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Write concise Korean PC purchase recommendations."),
            ("human", "Purpose: {purpose}\nCategory: {category}\nTop option: {top_product}"),
        ]
    )
    writer = RunnableLambda(
        lambda _: (
            f"{state['criteria'].purpose} 목적에는 예산, 부품 호환성, 성능 병목, "
            "업그레이드 여지를 함께 본 TOP 3 비교가 적합합니다."
        )
    )
    summary_chain = prompt | writer

    recommendations = [
        Recommendation(
            rank=index + 1,
            product=products[card.product_id],
            price=prices[card.product_id],
            review=reviews[card.product_id],
            score=card,
            fit_summary=_fit_summary(products[card.product_id], card),
            before_buy_checklist=[
                *_checklist_for(products[card.product_id]),
                "최종 결제 화면의 배송비, 조립비, OS 포함 여부, 카드 혜택을 다시 확인하세요.",
            ],
            benchmark_evidence=benchmarks_by_product.get(card.product_id, []),
            compatibility_checks=checks_by_product.get(card.product_id, []),
        )
        for index, card in enumerate(ranked[:3])
    ]
    excluded = [
        ExcludedProduct(
            product=products[card.product_id],
            reason="예산 대비 성능, 호환성 또는 업그레이드 여지가 TOP 3보다 낮습니다.",
        )
        for card in ranked[3:5]
    ]
    comparison_table = [
        ComparisonRow(
            product_id=card.product_id,
            rank=index + 1 if index < 3 else None,
            model_name=products[card.product_id].model_name,
            effective_price_krw=prices[card.product_id].effective_price_krw,
            purpose_fit=card.purpose_fit,
            compatibility=card.compatibility,
            review_trust=card.review_trust,
            strongest_reason=strongest_reason(products[card.product_id], reviews[card.product_id]),
            main_risk=main_risk(reviews[card.product_id]),
        )
        for index, card in enumerate(ranked[:5])
    ]
    ranked_ids = [card.product_id for card in ranked]
    price_alerts = build_price_alerts(state["price_snapshots"], state["criteria"], ranked_ids)
    source_trust = build_source_trust(
        state["price_snapshots"],
        state["review_insights"],
        state["benchmark_evidence"],
    )
    trust_policy = build_trust_policy(source_trust)
    purchase_decision = _purchase_decision(
        recommendations,
        price_alerts,
        source_trust,
        state["verification_flags"],
        state["criteria"],
    )
    scenario_options = _scenario_options(ranked[:5], products, prices, reviews)
    state["report"] = PurchaseReport(
        summary=summary_chain.invoke(
            {
                "purpose": state["criteria"].purpose,
                "category": state["criteria"].category.value,
                "top_product": recommendations[0].product.model_name,
            }
        ),
        top_recommendations=recommendations,
        excluded_products=excluded,
        purchase_timing=price_timing_message(
            state["price_snapshots"],
            state["criteria"].budget_krw,
        ),
        compatibility_notes=state["compatibility_notes"],
        citations=state["citations"],
        verification_flags=state["verification_flags"],
        comparison_table=comparison_table,
        benchmark_evidence=state["benchmark_evidence"],
        compatibility_checks=state["compatibility_checks"],
        price_alerts=price_alerts,
        source_health=_source_health(state["price_snapshots"], state["citations"]),
        decision_matrix=_decision_matrix(recommendations, excluded),
        source_trust=source_trust,
        trust_policy=trust_policy,
        purchase_decision=purchase_decision,
        scenario_options=scenario_options,
        final_pick_id=recommendations[0].product.id if recommendations else None,
    )
    _trace(
        state,
        AgentStep.report_writer,
        "구매 리포트 작성",
        (
            f"TOP {len(recommendations)}개와 제외 {len(excluded)}개, "
            f"가격 알림 {len(price_alerts)}개를 생성했습니다."
        ),
        evidence_count=len(comparison_table),
    )
    return state


def build_graph():
    workflow = StateGraph(PurchaseState)
    for step, fn in [
        (AgentStep.intent_parser, intent_parser),
        (AgentStep.clarifier, clarifier),
        (AgentStep.query_planner, query_planner),
        (AgentStep.product_collector, product_collector),
        (AgentStep.deduplicator, deduplicator),
        (AgentStep.compatibility_checker, compatibility_checker),
        (AgentStep.price_tracker, price_tracker),
        (AgentStep.review_analyzer, review_analyzer),
        (AgentStep.scoring_engine, scoring_engine),
        (AgentStep.verifier, verifier),
        (AgentStep.report_writer, report_writer),
    ]:
        workflow.add_node(step.value, fn)

    workflow.set_entry_point(AgentStep.intent_parser.value)
    ordered = [
        AgentStep.intent_parser,
        AgentStep.clarifier,
        AgentStep.query_planner,
        AgentStep.product_collector,
        AgentStep.deduplicator,
        AgentStep.compatibility_checker,
        AgentStep.price_tracker,
        AgentStep.review_analyzer,
        AgentStep.scoring_engine,
        AgentStep.verifier,
        AgentStep.report_writer,
    ]
    for before, after in zip(ordered, ordered[1:], strict=False):
        workflow.add_edge(before.value, after.value)
    workflow.add_edge(AgentStep.report_writer.value, END)
    return workflow.compile()


def run_analysis(request: AnalyzeRequest) -> AnalyzeResponse:
    state = build_graph().invoke({"request": request})
    response = AnalyzeResponse(
        criteria=state["criteria"],
        steps=state["steps"],
        report=state["report"],
        graph_trace_id=state["graph_trace_id"],
        trace_events=state["trace_events"],
    )
    response.quality_audit = build_quality_audit(response)
    return response


def _purpose_fit(product: ProductCandidate, criteria: PurchaseCriteria) -> float:
    score = 70.0
    purpose = criteria.purpose.lower()
    ram = float(product.specs.get("ram_gb", 0))
    gpu = str(product.specs.get("gpu", "")).lower()
    if "game" in purpose or "게임" in purpose:
        score += 14 if "4070" in gpu or "4080" in gpu else 8
    if "video" in purpose or "편집" in purpose or "premiere" in purpose:
        score += 12 if ram >= 32 else 3
        score += 10 if "rtx" in gpu or "m4" in gpu else 2
    if product.category == Category.laptop and float(product.specs.get("weight_kg", 9)) <= 1.8:
        score += 6
    if product.category == Category.desktop_pc and float(product.specs.get("psu_watt", 0)) >= 650:
        score += 5
    if any("업그레이드" in item or "upgrade" in item.lower() for item in criteria.must_haves):
        score += float(product.specs.get("upgrade_slots", 0)) * 2
    if any("휴대" in item or "가벼" in item for item in criteria.must_haves):
        if product.category == Category.laptop and float(product.specs.get("weight_kg", 9)) <= 1.6:
            score += 8
    return min(100, score)


def _group_by_product(items):
    grouped = {}
    for item in items:
        grouped.setdefault(item.product_id, []).append(item)
    return grouped


def _fit_summary(product: ProductCandidate, card: ScoreCard) -> str:
    return (
        f"{product.model_name}은 총점 {card.total_score}점으로 목적 적합도, "
        "가격, 호환성의 균형이 좋은 후보입니다."
    )


def _checklist_for(product: ProductCandidate) -> list[str]:
    if product.category == Category.desktop_pc:
        return [
            "CPU 소켓, 메인보드 칩셋, RAM 규격, 파워 용량을 확인하세요.",
            "케이스 GPU 길이와 CPU 쿨러 높이 여유를 확인하세요.",
            "모니터 해상도와 주사율 기준으로 GPU 체급이 과하거나 부족하지 않은지 확인하세요.",
        ]
    return [
        "RAM/SSD 옵션명이 실제 판매 페이지와 같은지 확인하세요.",
        "장시간 고부하 작업의 발열과 팬 소음 후기를 확인하세요.",
        "무게, 충전기, 배터리 용량이 이동 패턴과 맞는지 확인하세요.",
    ]


def _source_health(prices: list[PriceSnapshot], citations: list[str]) -> list[str]:
    source_types = sorted({price.source_type for price in prices})
    limited = [price for price in prices if price.stock_status == "limited"]
    return [
        f"가격 출처 {len(source_types)}종: {', '.join(source_types)}",
        f"출처 링크 {len(citations)}개 연결",
        f"재고 한정 후보 {len(limited)}개",
        "제휴 여부와 무관하게 가격/호환성/리뷰 점수 기준으로 정렬합니다.",
    ]


def _decision_matrix(
    recommendations: list[Recommendation],
    excluded: list[ExcludedProduct],
) -> list[str]:
    lines = [
        f"최종 1순위: {recommendations[0].product.model_name} - {recommendations[0].fit_summary}"
        if recommendations
        else "추천 후보가 없습니다.",
        "TOP 3는 예산, 목적 적합도, 호환성, 리뷰 신뢰도 균형으로 선정했습니다.",
    ]
    if excluded:
        lines.append(
            "제외 후보는 구매하지 말라는 의미가 아니라 "
            "이번 요청 조건에서 우선순위가 낮다는 뜻입니다."
        )
    return lines


def _purchase_decision(
    recommendations: list[Recommendation],
    price_alerts: list[PriceAlertPlan],
    source_trust: list[SourceTrustAssessment],
    verification_flags: list[str],
    criteria: PurchaseCriteria,
) -> PurchaseDecision:
    if not recommendations:
        return PurchaseDecision(
            verdict="review_required",
            label="추천 불가",
            confidence=0,
            reason="비교 가능한 추천 후보가 충분하지 않습니다.",
            risk_flags=["추천 후보 부족"],
            next_steps=["예산, 용도, 필수 조건을 더 구체화한 뒤 다시 분석하세요."],
        )

    top = recommendations[0]
    top_alert = next(
        (alert for alert in price_alerts if alert.product_id == top.product.id),
        price_alerts[0] if price_alerts else None,
    )
    blocker_checks = [
        check.message
        for check in top.compatibility_checks
        if check.status == CheckStatus.blocker
    ]
    warning_checks = [
        check.message
        for check in top.compatibility_checks
        if check.status == CheckStatus.warning
    ]
    review_required_sources = [
        source.source_name for source in source_trust if source.requires_human_review
    ]
    target_gap = (
        top.price.effective_price_krw - top_alert.target_price_krw
        if top_alert is not None
        else 0
    )
    budget_gap = (
        top.price.effective_price_krw - criteria.budget_krw
        if criteria.budget_krw is not None
        else 0
    )
    risk_flags = [
        *blocker_checks,
        *warning_checks[:2],
        *[f"검수 필요 출처: {name}" for name in review_required_sources[:2]],
        *top.review.risk_signals[:2],
    ]

    next_steps = [
        *top.before_buy_checklist[:3],
        "공개 리포트를 공유해 가족, 동료, 커뮤니티에서 한 번 더 검토받으세요.",
    ]
    confidence = min(98.0, max(35.0, top.score.total_score - len(risk_flags) * 4))

    if blocker_checks or review_required_sources:
        return PurchaseDecision(
            verdict="review_required",
            label="검수 후 구매",
            confidence=round(confidence, 1),
            reason=(
                "상위 후보의 점수는 높지만 호환성 또는 출처 검수 신호가 있어 "
                "결제 전 확인이 필요합니다."
            ),
            risk_flags=risk_flags or verification_flags,
            next_steps=[
                "검수 플래그와 출처 신뢰도를 먼저 확인하세요.",
                *next_steps,
            ],
        )

    if budget_gap > 0 or target_gap > max(30_000, int(top.price.effective_price_krw * 0.025)):
        wait_reason = (
            f"현재 실구매가가 목표가보다 {target_gap:,}원 높습니다."
            if target_gap > 0
            else "현재 실구매가가 입력 예산을 초과합니다."
        )
        return PurchaseDecision(
            verdict="wait_for_price",
            label="가격 대기",
            confidence=round(confidence, 1),
            reason=wait_reason,
            risk_flags=risk_flags,
            next_steps=[
                "1순위 가격 알림을 설정하고 목표가 도달 후 다시 확인하세요.",
                *next_steps,
            ],
        )

    return PurchaseDecision(
        verdict="buy_now",
        label="구매 진행 가능",
        confidence=round(confidence, 1),
        reason=(
            "목적 적합도, 가격, 호환성, 리뷰 신뢰도가 균형을 이루고 "
            "중대한 차단 신호가 없습니다."
        ),
        risk_flags=risk_flags,
        next_steps=next_steps,
    )


def _scenario_options(
    ranked: list[ScoreCard],
    products: dict[str, ProductCandidate],
    prices: dict[str, PriceSnapshot],
    reviews: dict[str, ReviewInsight],
) -> list[ScenarioOption]:
    if not ranked:
        return []

    def value_key(card: ScoreCard) -> tuple[float, float]:
        return (
            card.price_competitiveness - prices[card.product_id].effective_price_krw / 100_000,
            card.total_score,
        )

    def performance_key(card: ScoreCard) -> tuple[float, float]:
        return (card.purpose_fit + card.total_score, card.compatibility)

    def safety_key(card: ScoreCard) -> tuple[float, float]:
        return (card.purchase_stability + card.review_trust + card.compatibility, card.total_score)

    scenario_specs = [
        ("value", "예산 절감", value_key),
        ("performance", "성능 우선", performance_key),
        ("safe", "안전 우선", safety_key),
    ]

    options: list[ScenarioOption] = []
    used_product_ids: set[str] = set()
    for scenario, label, key_fn in scenario_specs:
        sorted_cards = sorted(ranked, key=key_fn, reverse=True)
        card = next(
            (
                candidate
                for candidate in sorted_cards
                if candidate.product_id not in used_product_ids
            ),
            sorted_cards[0],
        )
        product = products[card.product_id]
        price = prices[card.product_id]
        review = reviews[card.product_id]
        used_product_ids.add(card.product_id)
        options.append(
            ScenarioOption(
                scenario=scenario,
                label=label,
                product_id=card.product_id,
                model_name=product.model_name,
                effective_price_krw=price.effective_price_krw,
                total_score=card.total_score,
                why=_scenario_why(scenario, card, product),
                tradeoff=_scenario_tradeoff(scenario, card, review),
            )
        )
    return options


def _scenario_why(scenario: str, card: ScoreCard, product: ProductCandidate) -> str:
    if scenario == "value":
        return (
            f"{product.model_name}은 가격 경쟁력 {card.price_competitiveness}점으로 "
            "예산을 아끼면서도 핵심 조건을 유지하는 선택입니다."
        )
    if scenario == "performance":
        return (
            f"{product.model_name}은 목적 적합도 {card.purpose_fit}점으로 "
            "작업 성능과 체감 속도를 우선할 때 적합합니다."
        )
    return (
        f"{product.model_name}은 구매 안정성 {card.purchase_stability}점과 "
        f"리뷰 신뢰도 {card.review_trust}점이 균형적입니다."
    )


def _scenario_tradeoff(scenario: str, card: ScoreCard, review: ReviewInsight) -> str:
    if scenario == "value":
        return "최고 성능 후보보다 렌더링, 고주사율 게임 여유는 낮을 수 있습니다."
    if scenario == "performance":
        return "예산 여유와 발열, 소음 리스크를 결제 전 한 번 더 확인해야 합니다."
    risk = review.risk_signals[0] if review.risk_signals else "가격 변동"
    return f"보수적인 선택이지만 {risk} 신호는 확인해야 합니다."
