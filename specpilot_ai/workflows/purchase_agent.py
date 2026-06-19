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
    CriterionMatchItem,
    ExcludedProduct,
    OptionAuditItem,
    PriceAlertPlan,
    PriceSnapshot,
    ProductCandidate,
    ProductCriteriaMatch,
    ProductEvidencePack,
    ProductOptionAudit,
    PurchaseCriteria,
    PurchaseDecision,
    PurchaseExecutionPlan,
    PurchaseReport,
    PurchaseStressTest,
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
    criteria_matches = _criteria_matches(ranked[:5], products, state["criteria"])
    stress_tests = _stress_tests(
        recommendations,
        comparison_table,
        state["criteria"],
        criteria_matches,
    )
    evidence_packs = _evidence_packs(
        ranked[:5],
        products,
        prices,
        reviews,
        benchmarks_by_product,
        checks_by_product,
        source_trust,
    )
    option_audits = _option_audits(ranked[:5], products, checks_by_product)
    execution_plan = _execution_plan(
        recommendations,
        purchase_decision,
        price_alerts,
        criteria_matches,
    )
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
        criteria_matches=criteria_matches,
        stress_tests=stress_tests,
        evidence_packs=evidence_packs,
        option_audits=option_audits,
        execution_plan=execution_plan,
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


def _criteria_matches(
    ranked: list[ScoreCard],
    products: dict[str, ProductCandidate],
    criteria: PurchaseCriteria,
) -> list[ProductCriteriaMatch]:
    matches: list[ProductCriteriaMatch] = []
    for card in ranked:
        product = products[card.product_id]
        items = [
            _criterion_match("must_have", condition, product)
            for condition in criteria.must_haves
        ]
        items.extend(
            _criterion_match("exclusion", condition, product)
            for condition in criteria.exclusions
        )
        ok_count = sum(item.status == CheckStatus.ok for item in items)
        warning_count = sum(item.status == CheckStatus.warning for item in items)
        blocker_count = sum(item.status == CheckStatus.blocker for item in items)
        denominator = max(1, len(items))
        coverage_score = round(((ok_count + warning_count * 0.5) / denominator) * 100, 1)
        if not items:
            summary = "입력된 필수/제외 조건이 없어 목적 적합도와 호환성 중심으로 평가했습니다."
        elif blocker_count:
            summary = f"{blocker_count}개 조건은 결제 전 확인이 필요합니다."
        elif warning_count:
            summary = f"{ok_count}개 조건 충족, {warning_count}개 조건은 부분 확인이 필요합니다."
        else:
            summary = "입력 조건을 모두 충족하거나 제외 조건에 걸리지 않습니다."
        matches.append(
            ProductCriteriaMatch(
                product_id=product.id,
                model_name=product.model_name,
                coverage_score=coverage_score,
                matched_count=ok_count,
                warning_count=warning_count,
                blocker_count=blocker_count,
                summary=summary,
                items=items,
            )
        )
    return matches


def _stress_tests(
    recommendations: list[Recommendation],
    comparison_table: list[ComparisonRow],
    criteria: PurchaseCriteria,
    criteria_matches: list[ProductCriteriaMatch],
) -> list[PurchaseStressTest]:
    if not recommendations:
        return [
            PurchaseStressTest(
                scenario="candidate_shortage",
                label="후보 부족",
                assumption="비교 가능한 후보가 충분하지 않은 상태",
                status=CheckStatus.blocker,
                impact="예산이나 조건을 바꿔도 신뢰할 수 있는 선택지를 확정할 수 없습니다.",
                recommendation="예산, 용도, 필수 조건을 구체화하고 후보 수집을 다시 실행하세요.",
            )
        ]

    top = recommendations[0]
    top_match = next(
        (match for match in criteria_matches if match.product_id == top.product.id),
        None,
    )
    base_budget = criteria.budget_krw or top.price.effective_price_krw
    reduced_budget = int(base_budget * 0.9)
    expanded_budget = int(base_budget * 1.1)
    ranked_rows = sorted(
        comparison_table,
        key=lambda row: (row.rank is None, row.rank or 99, row.effective_price_krw),
    )

    def best_under(budget: int) -> ComparisonRow | None:
        affordable = [row for row in ranked_rows if row.effective_price_krw <= budget]
        return affordable[0] if affordable else None

    def premium_under(budget: int) -> ComparisonRow:
        premium = [
            row
            for row in ranked_rows
            if row.effective_price_krw <= budget
            and row.effective_price_krw >= top.price.effective_price_krw
        ]
        if not premium:
            return ranked_rows[0]
        return sorted(premium, key=lambda row: (row.rank or 99, -row.effective_price_krw))[0]

    reduced_pick = best_under(reduced_budget)
    if reduced_pick is None:
        reduced = PurchaseStressTest(
            scenario="budget_minus_10",
            label="예산 10% 절감",
            assumption=f"실사용 예산을 {reduced_budget:,}원으로 낮춘 경우",
            status=CheckStatus.blocker,
            budget_krw=reduced_budget,
            price_gap_krw=top.price.effective_price_krw - reduced_budget,
            impact="TOP 5 후보 중 절감 예산 안에서 바로 결제 가능한 선택지가 없습니다.",
            recommendation=(
                "예산을 회복하거나 RAM/SSD/그래픽카드 체급 중 하나를 낮춰 "
                "다시 비교하세요."
            ),
        )
    else:
        changed = reduced_pick.product_id != top.product.id
        reduced = PurchaseStressTest(
            scenario="budget_minus_10",
            label="예산 10% 절감",
            assumption=f"실사용 예산을 {reduced_budget:,}원으로 낮춘 경우",
            status=CheckStatus.warning if changed else CheckStatus.ok,
            budget_krw=reduced_budget,
            selected_product_id=reduced_pick.product_id,
            selected_model_name=reduced_pick.model_name,
            price_gap_krw=max(0, reduced_pick.effective_price_krw - reduced_budget),
            impact=(
                f"1순위 대신 {reduced_pick.model_name}로 변경해야 예산을 맞출 수 있습니다."
                if changed
                else "1순위 후보가 절감 예산 안에서도 유지됩니다."
            ),
            recommendation=(
                "절감 모드에서는 성능 여유나 업그레이드 폭이 줄어드는지 다시 확인하세요."
                if changed
                else "가격이 유지된다면 절감 예산에서도 결제를 진행할 수 있습니다."
            ),
        )

    expanded_pick = premium_under(expanded_budget)
    expanded = PurchaseStressTest(
        scenario="budget_plus_10",
        label="예산 10% 여유",
        assumption=f"실사용 예산을 {expanded_budget:,}원까지 늘릴 수 있는 경우",
        status=CheckStatus.ok,
        budget_krw=expanded_budget,
        selected_product_id=expanded_pick.product_id,
        selected_model_name=expanded_pick.model_name,
        price_gap_krw=max(0, expanded_pick.effective_price_krw - expanded_budget),
        impact=(
            f"{expanded_pick.model_name}까지 검토 범위에 들어옵니다."
            if expanded_pick.product_id != top.product.id
            else "추가 예산을 넣어도 현재 1순위의 균형 점수가 가장 좋습니다."
        ),
        recommendation=(
            "예산을 늘릴 때는 체감 성능 상승이 소음, 발열, 전력 리스크보다 큰지 확인하세요."
        ),
    )

    if top_match is None:
        strict_status = CheckStatus.warning
        strict_impact = "입력 조건 매트릭스가 없어 엄격 조건 적용 결과를 확정하기 어렵습니다."
        strict_recommendation = "필수 조건과 제외 조건을 추가한 뒤 다시 분석하세요."
    elif top_match.blocker_count:
        strict_status = CheckStatus.blocker
        strict_impact = f"차단 조건 {top_match.blocker_count}개 때문에 1순위 결제를 멈춰야 합니다."
        strict_recommendation = "차단 항목을 해소하거나 다른 후보로 전환하세요."
    elif top_match.warning_count:
        strict_status = CheckStatus.warning
        strict_impact = (
            f"확인 필요 조건 {top_match.warning_count}개가 남아 "
            "판매자 확인이 필요합니다."
        )
        strict_recommendation = "판매자 확인 질문으로 옵션명과 구성표를 받아 조건을 확정하세요."
    else:
        strict_status = CheckStatus.ok
        strict_impact = "입력한 필수 조건과 제외 조건을 엄격하게 적용해도 1순위가 유지됩니다."
        strict_recommendation = "가격과 재고만 마지막으로 확인하면 결제 판단이 가능합니다."

    strict_conditions = PurchaseStressTest(
        scenario="strict_conditions",
        label="조건 강화",
        assumption="필수 조건과 제외 조건을 보수적으로 모두 적용한 경우",
        status=strict_status,
        budget_krw=base_budget,
        selected_product_id=top.product.id,
        selected_model_name=top.product.model_name,
        price_gap_krw=max(0, top.price.effective_price_krw - base_budget),
        impact=strict_impact,
        recommendation=strict_recommendation,
    )

    return [reduced, expanded, strict_conditions]


def _evidence_packs(
    ranked: list[ScoreCard],
    products: dict[str, ProductCandidate],
    prices: dict[str, PriceSnapshot],
    reviews: dict[str, ReviewInsight],
    benchmarks_by_product: dict[str, list[BenchmarkEvidence]],
    checks_by_product: dict[str, list[CompatibilityCheck]],
    source_trust: list[SourceTrustAssessment],
) -> list[ProductEvidencePack]:
    trust_by_type = {source.source_type: source for source in source_trust}
    review_trust = trust_by_type.get("review_signal")
    benchmark_trust = trust_by_type.get("benchmark")
    packs: list[ProductEvidencePack] = []

    for card in ranked:
        product = products[card.product_id]
        price = prices[card.product_id]
        review = reviews[card.product_id]
        price_trust = trust_by_type.get(price.source_type)
        product_benchmarks = benchmarks_by_product.get(product.id, [])
        product_checks = checks_by_product.get(product.id, [])
        non_ok_checks = [check for check in product_checks if check.status != CheckStatus.ok]
        benchmark_lines = [
            f"{item.workload}: {item.score_label} - {item.summary}"
            for item in product_benchmarks[:3]
        ]
        compatibility_lines = [
            f"{check.component}: {check.status.value} - {check.message}"
            for check in product_checks[:4]
        ]
        citation_urls = [
            product.source_url,
            price.url,
            *[item.evidence_url for item in product_benchmarks[:3]],
        ]
        review_required = any(
            [
                bool(non_ok_checks),
                bool(review.risk_signals),
                price_trust.requires_human_review if price_trust else True,
                review_trust.requires_human_review if review_trust else False,
                benchmark_trust.requires_human_review if benchmark_trust else False,
            ]
        )
        trust_parts = []
        if price_trust:
            trust_parts.append(
                f"가격 {price_trust.trust_grade}({round(price_trust.confidence * 100)}%)"
            )
        if review_trust:
            trust_parts.append(
                f"리뷰 {review_trust.trust_grade}({review.evidence_count}건)"
            )
        if benchmark_trust and product_benchmarks:
            trust_parts.append(f"벤치마크 {len(product_benchmarks)}건")
        trust_parts.append("검수 필요" if review_required else "자동 공개 가능")

        packs.append(
            ProductEvidencePack(
                product_id=product.id,
                model_name=product.model_name,
                price_evidence=(
                    f"{price.seller} 기준 실구매가 {price.effective_price_krw:,}원 "
                    f"(배송 {price.shipping_fee_krw:,}원, 조립 {price.assembly_fee_krw:,}원, "
                    f"쿠폰 {price.coupon_krw:,}원, 카드 할인 {price.card_discount_krw:,}원)"
                ),
                review_evidence=(
                    f"리뷰 근거 {review.evidence_count}건, 신뢰도 "
                    f"{round(review.trust_score * 100)}%. "
                    f"장점: {', '.join(review.pros[:2]) or '확인 필요'}. "
                    f"리스크: {', '.join(review.risk_signals[:2]) or '중대 신호 없음'}."
                ),
                benchmark_evidence=benchmark_lines,
                compatibility_evidence=compatibility_lines,
                trust_summary=" / ".join(trust_parts),
                citation_urls=[url for url in citation_urls if url],
                review_required=review_required,
            )
        )
    return packs


def _option_audits(
    ranked: list[ScoreCard],
    products: dict[str, ProductCandidate],
    checks_by_product: dict[str, list[CompatibilityCheck]],
) -> list[ProductOptionAudit]:
    audits: list[ProductOptionAudit] = []
    for card in ranked:
        product = products[card.product_id]
        checks = checks_by_product.get(product.id, [])
        items = _option_audit_items(product)
        blockers = [
            check.message for check in checks if check.status == CheckStatus.blocker
        ]
        warnings = [
            check.message for check in checks if check.status == CheckStatus.warning
        ]
        mismatch_risks = _option_mismatch_risks(product, warnings)
        if blockers:
            summary = f"구매 차단 가능 항목 {len(blockers)}개를 먼저 해소해야 합니다."
        elif mismatch_risks:
            summary = f"옵션명과 구성표 대조가 필요한 항목 {len(mismatch_risks)}개가 있습니다."
        else:
            summary = "판매 페이지 옵션명이 검수표와 같으면 결제 가능성이 높습니다."
        audits.append(
            ProductOptionAudit(
                product_id=product.id,
                model_name=product.model_name,
                summary=summary,
                critical_items=items,
                mismatch_risks=mismatch_risks,
                purchase_blockers=blockers,
            )
        )
    return audits


def _option_audit_items(product: ProductCandidate) -> list[OptionAuditItem]:
    if product.category == Category.desktop_pc:
        fields = [
            ("CPU", "cpu", "CPU 모델명이 리포트와 같은지 확인하세요."),
            ("GPU", "gpu", "그래픽카드 칩셋과 VRAM 표기가 같은지 확인하세요."),
            ("메인보드", "motherboard", "보드 칩셋과 폼팩터가 같은지 확인하세요."),
            ("RAM", "ram_gb", "용량과 DDR 규격을 함께 확인하세요."),
            ("SSD", "ssd_tb", "저장장치 용량과 NVMe 여부를 확인하세요."),
            ("파워", "psu_watt", "정격 출력과 인증 등급을 확인하세요."),
            (
                "GPU 장착 여유",
                "case_gpu_clearance_mm",
                "케이스 장착 가능 길이가 GPU 길이보다 큰지 확인하세요.",
            ),
            (
                "CPU 쿨러 여유",
                "case_cooler_clearance_mm",
                "케이스 쿨러 허용 높이가 쿨러 높이보다 큰지 확인하세요.",
            ),
        ]
    else:
        fields = [
            ("CPU", "cpu", "프로세서 세대와 모델명이 같은지 확인하세요."),
            ("GPU", "gpu", "외장 GPU 여부와 모델명을 확인하세요."),
            ("RAM", "ram_gb", "용량과 온보드/교체 가능 여부를 확인하세요."),
            ("SSD", "ssd_tb", "저장장치 용량과 추가 슬롯 여부를 확인하세요."),
            ("디스플레이", "display", "화면 크기, 해상도, 주사율, 패널 종류를 확인하세요."),
            ("무게", "weight_kg", "본체 무게와 충전기 무게를 구분해 확인하세요."),
            ("배터리", "battery_wh", "Wh 용량과 실제 사용 시간을 확인하세요."),
            ("외장 GPU", "external_gpu", "GPU 가속 작업에 필요한 외장 GPU 여부를 확인하세요."),
        ]

    return [
        OptionAuditItem(
            field=label,
            expected_value=_format_spec_value(product, key),
            status=CheckStatus.ok,
            verification_hint=hint,
        )
        for label, key, hint in fields
    ]


def _option_mismatch_risks(
    product: ProductCandidate,
    compatibility_warnings: list[str],
) -> list[str]:
    risks = [
        "판매 페이지의 옵션명, 장바구니 구성표, 최종 결제 화면의 모델명이 모두 같은지 확인하세요.",
        "쿠폰 적용 후 대체 부품으로 바뀌는 자동 옵션 변경이 없는지 확인하세요.",
    ]
    if product.category == Category.desktop_pc:
        risks.extend(
            [
                "GPU 길이, 케이스 장착 여유, CPU 쿨러 높이는 숫자로 대조하세요.",
                "파워 정격 출력과 그래픽카드 권장 파워가 맞는지 확인하세요.",
            ]
        )
    else:
        risks.extend(
            [
                "RAM/SSD가 온보드인지 교체 가능한지 판매자 답변으로 남기세요.",
                "같은 모델명의 디스플레이 패널 옵션이 여러 개인지 확인하세요.",
            ]
        )
    return [*risks, *compatibility_warnings[:2]]


def _format_spec_value(product: ProductCandidate, key: str) -> str:
    value = product.specs.get(key, "확인 필요")
    if key == "ram_gb":
        return f"{value}GB {product.specs.get('ram_type', '')}".strip()
    if key == "ssd_tb":
        return f"{value}TB"
    if key == "psu_watt":
        return f"{value}W"
    if key.endswith("_mm"):
        return f"{value}mm"
    if key == "weight_kg":
        return f"{value}kg"
    if key == "battery_wh":
        return f"{value}Wh"
    if key in {"external_gpu", "upgradeable_ram"}:
        return "예" if value else "아니오"
    return str(value)


def _execution_plan(
    recommendations: list[Recommendation],
    decision: PurchaseDecision,
    price_alerts: list[PriceAlertPlan],
    criteria_matches: list[ProductCriteriaMatch],
) -> PurchaseExecutionPlan:
    if not recommendations:
        return PurchaseExecutionPlan(
            headline="비교 가능한 후보를 더 모아야 합니다.",
            primary_action="예산, 목적, 필수 조건을 구체화한 뒤 다시 분석하세요.",
            urgency="분석 보강",
            price_recheck_required=True,
            checkout_steps=["요청 조건을 보강하고 후보 수집을 다시 실행하세요."],
            seller_questions=["판매 페이지 옵션명과 실제 구성표를 확인할 수 있나요?"],
            share_message="비교 가능한 후보가 부족해 조건을 보강한 뒤 다시 검토해야 합니다.",
        )

    top = recommendations[0]
    top_alert = next(
        (alert for alert in price_alerts if alert.product_id == top.product.id),
        price_alerts[0] if price_alerts else None,
    )
    criteria_match = next(
        (item for item in criteria_matches if item.product_id == top.product.id),
        None,
    )
    blocker_count = criteria_match.blocker_count if criteria_match else 0
    warning_count = criteria_match.warning_count if criteria_match else 0
    price_gap = (
        top.price.effective_price_krw - top_alert.target_price_krw
        if top_alert is not None
        else 0
    )
    price_recheck_required = decision.verdict != "buy_now" or price_gap > 0

    if decision.verdict == "buy_now" and blocker_count == 0:
        urgency = "오늘 결제 가능"
        primary_action = "최종 판매 페이지에서 옵션명, 배송비, 카드 혜택을 확인한 뒤 결제하세요."
    elif decision.verdict == "wait_for_price":
        urgency = "가격 대기"
        primary_action = "목표가 알림을 켜고 현재가가 목표가에 가까워질 때 결제하세요."
    else:
        urgency = "검수 필요"
        primary_action = "조건 충족 매트릭스와 출처 신뢰도를 먼저 검수한 뒤 결제 여부를 결정하세요."

    checkout_steps = [
        f"1순위 모델명을 판매 페이지와 대조하세요: {top.product.model_name}",
        (
            f"실구매가 {top.price.effective_price_krw:,}원에 배송비, "
            "조립비, OS 포함 여부가 반영됐는지 확인하세요."
        ),
        "필수 조건과 제외 조건의 충족/확인/차단 상태를 다시 확인하세요.",
        *top.before_buy_checklist[:3],
    ]
    if top_alert is not None:
        checkout_steps.append(
            f"목표가 {top_alert.target_price_krw:,}원과 현재가 차이를 확인하세요."
        )
    if warning_count or blocker_count:
        checkout_steps.append(
            f"조건 매트릭스의 확인 {warning_count}개, "
            f"차단 {blocker_count}개 항목을 먼저 해소하세요."
        )

    seller_questions = [
        "판매 페이지의 CPU/GPU/RAM/SSD 옵션명이 리포트와 동일한가요?",
        "조립비, OS 포함 여부, 배송비, 카드 할인 적용 후 최종 결제 금액은 얼마인가요?",
        "재고가 실제 보유 재고인지, 품절 시 대체 부품으로 바뀌는지 확인 가능한가요?",
    ]
    if top.product.category == Category.desktop_pc:
        seller_questions.append(
            "케이스 GPU 길이, CPU 쿨러 높이, 파워 용량 호환성을 다시 확인해 주실 수 있나요?"
        )
    else:
        seller_questions.append(
            "RAM/SSD가 온보드인지, 교체나 추가 장착이 가능한지 확인해 주실 수 있나요?"
        )

    share_message = (
        f"{top.product.model_name}을 1순위로 검토 중입니다. "
        f"총점 {top.score.total_score}점, 실구매가 {top.price.effective_price_krw:,}원, "
        f"구매 판정은 {decision.label}입니다. "
        "조건 충족 매트릭스와 결제 전 체크리스트 기준으로 한 번 더 봐주세요."
    )

    return PurchaseExecutionPlan(
        product_id=top.product.id,
        model_name=top.product.model_name,
        headline=f"{top.product.model_name} 구매 실행 패키지",
        primary_action=primary_action,
        urgency=urgency,
        price_recheck_required=price_recheck_required,
        checkout_steps=checkout_steps,
        seller_questions=seller_questions,
        share_message=share_message,
    )


def _criterion_match(
    check_type: str,
    condition: str,
    product: ProductCandidate,
) -> CriterionMatchItem:
    normalized = condition.strip()
    if check_type == "exclusion":
        status, evidence = _exclusion_status(normalized, product)
    else:
        status, evidence = _must_have_status(normalized, product)
    return CriterionMatchItem(
        check_type=check_type,
        criterion=normalized,
        status=status,
        evidence=evidence,
    )


def _must_have_status(condition: str, product: ProductCandidate) -> tuple[CheckStatus, str]:
    text = _product_text(product)
    lowered = condition.lower()
    ram = float(product.specs.get("ram_gb", 0))
    gpu = str(product.specs.get("gpu", "")).lower()

    if "32" in lowered and "ram" in lowered:
        if ram >= 32:
            return CheckStatus.ok, f"RAM {int(ram)}GB 구성입니다."
        return CheckStatus.blocker, f"RAM {int(ram)}GB라 32GB 조건에 부족합니다."
    if "qhd" in lowered or "144" in lowered:
        if any(token in gpu for token in ["4070", "4080", "4070 super"]):
            return CheckStatus.ok, f"{product.specs.get('gpu')} 기준 QHD 고주사율 여유가 있습니다."
        if any(token in gpu for token in ["4060", "7600", "m4"]):
            return CheckStatus.warning, f"{product.specs.get('gpu')}는 옵션 타협 시 적합합니다."
        return CheckStatus.warning, "해상도와 주사율은 실제 게임/작업 벤치마크를 추가 확인하세요."
    if "업그레이드" in condition or "upgrade" in lowered:
        slots = float(product.specs.get("upgrade_slots", 0))
        if slots >= 2:
            return CheckStatus.ok, f"업그레이드 여지 {int(slots)}개가 있습니다."
        if slots >= 1:
            return CheckStatus.warning, "일부 저장장치나 메모리 업그레이드만 가능합니다."
        return CheckStatus.blocker, "업그레이드 여지가 제한적입니다."
    if "휴대" in condition or "가벼" in condition:
        weight = float(product.specs.get("weight_kg", 9))
        if product.category == Category.laptop and weight <= 1.8:
            return CheckStatus.ok, f"무게 {weight:g}kg로 휴대 조건에 맞습니다."
        if product.category == Category.laptop and weight <= 2.2:
            return CheckStatus.warning, f"무게 {weight:g}kg라 휴대성은 보통입니다."
        return CheckStatus.blocker, "휴대성을 우선하는 조건과 맞지 않습니다."
    if "외장" in condition and "gpu" in lowered:
        if "rtx" in gpu or "radeon" in gpu:
            return CheckStatus.ok, f"{product.specs.get('gpu')} 외장 GPU 구성입니다."
        return (
            CheckStatus.warning,
            f"{product.specs.get('gpu')} 구성이라 외장 GPU 조건은 확인이 필요합니다.",
        )
    if condition and condition.lower() in text:
        return CheckStatus.ok, "제품명, 태그, 옵션 설명에서 조건이 확인됩니다."
    return (
        CheckStatus.warning,
        "데모 카탈로그 기준 직접 일치 근거가 부족해 상세 옵션명을 확인하세요.",
    )


def _exclusion_status(condition: str, product: ProductCandidate) -> tuple[CheckStatus, str]:
    lowered = condition.lower()
    text = _product_text(product)
    ram = float(product.specs.get("ram_gb", 0))
    if "중고" in condition or "리퍼" in condition or "refurb" in lowered:
        return CheckStatus.ok, "데모 카탈로그는 신품 판매 후보만 사용합니다."
    if "출처" in condition and ("없는" in condition or "없" in condition):
        if product.source_url:
            return CheckStatus.ok, "출처 URL이 연결된 후보입니다."
        return CheckStatus.blocker, "출처 URL이 없어 제외 조건에 걸립니다."
    if "8gb" in lowered or "8 gb" in lowered:
        if ram <= 8:
            return CheckStatus.blocker, f"RAM {int(ram)}GB라 제외 조건에 걸립니다."
        return CheckStatus.ok, f"RAM {int(ram)}GB라 8GB 제외 조건에 걸리지 않습니다."
    if condition and lowered in text:
        return CheckStatus.blocker, "제외 키워드가 제품 설명에서 발견됐습니다."
    return CheckStatus.ok, "제외 조건과 직접 충돌하지 않습니다."


def _product_text(product: ProductCandidate) -> str:
    specs = " ".join(str(value) for value in product.specs.values())
    return " ".join(
        [
            product.brand,
            product.model_name,
            product.normalized_model,
            product.form_factor,
            product.option_summary,
            *product.tags,
            specs,
        ]
    ).lower()
