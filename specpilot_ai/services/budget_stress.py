from datetime import UTC, datetime

from specpilot_ai.core.models import (
    BudgetStressRequest,
    BudgetStressScenario,
    CheckStatus,
    PublicBudgetStressKit,
)


def build_public_budget_stress_kit(
    request: BudgetStressRequest,
    generated_at: datetime | None = None,
) -> PublicBudgetStressKit:
    generated_at = generated_at or datetime.now(UTC)
    title = _title(request)
    gap = request.target_price_krw - request.current_budget_krw
    scenarios = _scenarios(request, gap)
    recommended = _recommended_scenario_id(scenarios)
    status = _baseline_status(request, gap)
    return PublicBudgetStressKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=title,
        baseline_status=status,
        gap_krw=gap,
        headline=_headline(title, gap, status),
        summary=_summary(request, gap, status),
        recommended_scenario_id=recommended,
        scenarios=scenarios,
        decision_rules=_decision_rules(request, gap, scenarios),
        analysis_prefill=_analysis_prefill(request, gap, recommended),
        share_copy=_share_copy(request, gap, recommended, scenarios),
        next_actions=_next_actions(status, scenarios),
    )


def _title(request: BudgetStressRequest) -> str:
    return request.product_title.strip() or "구매 후보"


def _baseline_status(request: BudgetStressRequest, gap: int) -> CheckStatus:
    if gap <= 0:
        return CheckStatus.ok
    gap_rate = gap / max(request.current_budget_krw, 1)
    if gap_rate <= 0.08 and request.risk_tolerance != "낮음":
        return CheckStatus.warning
    return CheckStatus.blocker


def _scenarios(request: BudgetStressRequest, gap: int) -> list[BudgetStressScenario]:
    required = _required_text(request)
    flexible = _flexible_text(request)
    small_raise = _round_budget(max(80_000, request.current_budget_krw * 0.05))
    larger_raise = _round_budget(max(150_000, request.current_budget_krw * 0.1))
    scenarios = [
        BudgetStressScenario(
            scenario_id="hold_budget",
            label="예산 유지",
            status=CheckStatus.ok if gap <= 0 else CheckStatus.warning,
            budget_krw=request.current_budget_krw,
            delta_krw=0,
            expected_gap_krw=max(0, gap),
            expected_tradeoff=(
                "현재 후보를 그대로 살 수 있습니다."
                if gap <= 0
                else f"{required}는 유지하되 가격이 내려오거나 대체 후보가 필요합니다."
            ),
            likely_outcome=(
                "바로 결제 검수로 넘어갈 수 있습니다."
                if gap <= 0
                else "동일 조건 후보는 예산 밖일 가능성이 높습니다."
            ),
            recommended_action=(
                "체크아웃 잠금으로 최종 결제 금액을 확인합니다."
                if gap <= 0
                else "목표가 감시와 후보 비교를 함께 열어 가격 대기 기준을 잡습니다."
            ),
            search_terms=_search_terms(request, "예산 내"),
            checks=["최종 결제 금액", "배송비/OS/조립비 포함 여부", "보증/반품 조건"],
        ),
        BudgetStressScenario(
            scenario_id="raise_small",
            label=f"예산 +{small_raise:,}원",
            status=CheckStatus.ok if gap <= small_raise else CheckStatus.warning,
            budget_krw=request.current_budget_krw + small_raise,
            delta_krw=small_raise,
            expected_gap_krw=max(0, gap - small_raise),
            expected_tradeoff=f"{required}를 유지하면서 가격 선택지를 넓힙니다.",
            likely_outcome=(
                "현재 후보가 결제권에 들어옵니다."
                if gap <= small_raise
                else "아직 일부 특가나 쿠폰 조건을 기다려야 합니다."
            ),
            recommended_action=(
                "증액 승인을 받으면 특가 안전성 검수 후 결제 실행으로 넘깁니다."
                if gap <= small_raise
                else "소폭 증액과 목표가 알림을 같이 설정합니다."
            ),
            search_terms=_search_terms(request, "소폭 예산 상향"),
            checks=["증액 승인 근거", "동일 사양 최저가", "카드/쿠폰 조건 확정"],
        ),
        BudgetStressScenario(
            scenario_id="raise_quality",
            label=f"예산 +{larger_raise:,}원",
            status=CheckStatus.ok,
            budget_krw=request.current_budget_krw + larger_raise,
            delta_krw=larger_raise,
            expected_gap_krw=max(0, gap - larger_raise),
            expected_tradeoff="성능, 보증, 반품 조건을 동시에 지킬 확률을 높입니다.",
            likely_outcome="같은 용도에서 리스크 낮은 후보를 고를 여지가 생깁니다.",
            recommended_action="증액 이유를 구매 승인 브리프로 공유하고 후보 2~3개를 비교합니다.",
            search_terms=_search_terms(request, "안전 우선"),
            checks=["국내 AS", "새상품 여부", "반품 가능 기간", "판매자 평점"],
        ),
        BudgetStressScenario(
            scenario_id="relax_condition",
            label="조건 하나 완화",
            status=CheckStatus.warning if request.flexible_specs else CheckStatus.blocker,
            budget_krw=request.current_budget_krw,
            delta_krw=0,
            expected_gap_krw=max(0, gap - _condition_savings(request)),
            expected_tradeoff=(
                f"{flexible} 중 하나를 낮춰 예산 안 후보를 찾습니다."
                if request.flexible_specs
                else "완화 가능한 조건이 없어 품질 손상이 커질 수 있습니다."
            ),
            likely_outcome=(
                "성능이나 편의 조건 일부를 낮추면 예산 내 후보가 늘어납니다."
                if request.flexible_specs
                else "무리하게 낮추면 구매 실패 비용이 커질 수 있습니다."
            ),
            recommended_action=(
                "완화 가능한 조건을 하나만 낮추고 필수 조건은 유지합니다."
                if request.flexible_specs
                else "필수 조건을 낮추기 전에 실패 비용 계산을 먼저 확인합니다."
            ),
            search_terms=_search_terms(request, "조건 완화"),
            checks=["포기한 조건의 영향", "업그레이드 가능 여부", "반품/AS 리스크"],
        ),
        BudgetStressScenario(
            scenario_id="wait_target",
            label=f"{request.can_wait_days}일 대기",
            status=CheckStatus.ok if request.can_wait_days >= 7 else CheckStatus.warning,
            budget_krw=request.current_budget_krw,
            delta_krw=0,
            expected_gap_krw=max(0, gap - _wait_savings(request)),
            expected_tradeoff="구매 시점을 늦추고 목표가 도달 또는 쿠폰 갱신을 기다립니다.",
            likely_outcome=(
                "대기 여유가 있어 목표가 알림과 대체 후보 비교가 유효합니다."
                if request.can_wait_days >= 7
                else "기한이 짧아 대기만으로는 후보 개선 가능성이 낮습니다."
            ),
            recommended_action="목표가 감시 기준과 결제 트리거를 먼저 설정합니다.",
            search_terms=_search_terms(request, "목표가 대기"),
            checks=["할인 만료", "재고 변동", "쿠폰 갱신 주기", "대체 후보 현재가"],
        ),
    ]
    return scenarios


def _round_budget(value: float) -> int:
    return int(round(value / 10_000) * 10_000)


def _condition_savings(request: BudgetStressRequest) -> int:
    if not request.flexible_specs:
        return 0
    return max(80_000, min(350_000, int(request.current_budget_krw * 0.08)))


def _wait_savings(request: BudgetStressRequest) -> int:
    if request.can_wait_days >= 21:
        return max(120_000, int(request.current_budget_krw * 0.08))
    if request.can_wait_days >= 7:
        return max(70_000, int(request.current_budget_krw * 0.045))
    return max(30_000, int(request.current_budget_krw * 0.02))


def _required_text(request: BudgetStressRequest) -> str:
    return ", ".join(request.required_specs[:3]) if request.required_specs else "필수 용도"


def _flexible_text(request: BudgetStressRequest) -> str:
    return ", ".join(request.flexible_specs[:3]) if request.flexible_specs else "조정 가능 조건"


def _search_terms(request: BudgetStressRequest, suffix: str) -> list[str]:
    category = "데스크톱 PC" if request.category.value == "desktop_pc" else "노트북"
    specs = [*request.required_specs[:2], *request.flexible_specs[:1]]
    core = " ".join(specs) if specs else request.use_case
    return [
        f"{category} {core} {suffix}",
        f"{request.current_budget_krw // 10_000}만원대 {category} {core}",
        f"{category} {core} 보증 반품 안전",
    ]


def _recommended_scenario_id(scenarios: list[BudgetStressScenario]) -> str:
    for scenario in scenarios:
        if scenario.scenario_id in {"raise_small", "hold_budget"} and scenario.status == CheckStatus.ok:
            return scenario.scenario_id
    for scenario in scenarios:
        if scenario.scenario_id == "wait_target" and scenario.status == CheckStatus.ok:
            return scenario.scenario_id
    for scenario in scenarios:
        if scenario.status == CheckStatus.ok:
            return scenario.scenario_id
    return scenarios[0].scenario_id


def _headline(title: str, gap: int, status: CheckStatus) -> str:
    if gap <= 0:
        return f"{title}는 현재 예산 안에서 결제 검수로 넘어갈 수 있습니다."
    if status == CheckStatus.warning:
        return f"{title}는 예산보다 {gap:,}원 높아 소폭 증액 또는 대기 기준이 필요합니다."
    return f"{title}는 예산보다 {gap:,}원 높아 조건 조정 없이는 결제하면 안 됩니다."


def _summary(request: BudgetStressRequest, gap: int, status: CheckStatus) -> str:
    good_price = (
        "미입력"
        if request.reference_good_price_krw is None
        else f"{request.reference_good_price_krw:,}원"
    )
    return (
        f"현재 예산 {request.current_budget_krw:,}원, 후보가 {request.target_price_krw:,}원, "
        f"기준 적정가 {good_price}. 상태는 {status.value}이며 "
        f"{request.urgency} 조건에서 예산/조건/대기 시나리오를 비교합니다."
    )


def _decision_rules(
    request: BudgetStressRequest,
    gap: int,
    scenarios: list[BudgetStressScenario],
) -> list[str]:
    recommended = next(item for item in scenarios if item.scenario_id == _recommended_scenario_id(scenarios))
    rules = [
        "필수 조건은 낮추지 않고 flexible 조건만 하나씩 조정합니다.",
        "예산을 올릴 때는 같은 금액으로 보증/반품 조건이 더 좋은 후보를 같이 비교합니다.",
        "최종 결제 금액이 선택한 시나리오 예산을 넘으면 구매 실행으로 넘기지 않습니다.",
        f"우선 시나리오는 {recommended.label}이며 예상 잔여 차이는 {recommended.expected_gap_krw:,}원입니다.",
    ]
    if gap > 0:
        rules.insert(0, f"예산 차이 {gap:,}원이 닫히기 전에는 현재 후보를 바로 결제하지 않습니다.")
    if request.blocked_conditions:
        rules.append(f"제외 조건({', '.join(request.blocked_conditions[:3])})이 보이면 후보에서 제외합니다.")
    return rules[:6]


def _analysis_prefill(
    request: BudgetStressRequest,
    gap: int,
    recommended: str,
) -> str:
    return (
        "SpecPilot AI 예산/조건 스트레스 테스트 기준으로 구매 후보를 분석해줘.\n"
        f"- 제품: {_title(request)}\n"
        f"- 예산: {request.current_budget_krw:,}원\n"
        f"- 후보 가격: {request.target_price_krw:,}원\n"
        f"- 예산 차이: {gap:+,}원\n"
        f"- 필수 조건: {_required_text(request)}\n"
        f"- 조정 가능 조건: {_flexible_text(request)}\n"
        f"- 추천 시나리오: {recommended}"
    )


def _share_copy(
    request: BudgetStressRequest,
    gap: int,
    recommended: str,
    scenarios: list[BudgetStressScenario],
) -> str:
    scenario = next(item for item in scenarios if item.scenario_id == recommended)
    return (
        "SpecPilot AI 예산/조건 스트레스 테스트\n"
        f"- 제품: {_title(request)}\n"
        f"- 예산/후보가: {request.current_budget_krw:,}원 / {request.target_price_krw:,}원\n"
        f"- 예산 차이: {gap:+,}원\n"
        f"- 추천: {scenario.label}\n"
        f"- 다음 행동: {scenario.recommended_action}"
    )


def _next_actions(
    status: CheckStatus,
    scenarios: list[BudgetStressScenario],
) -> list[str]:
    recommended = next(item for item in scenarios if item.scenario_id == _recommended_scenario_id(scenarios))
    if status == CheckStatus.ok:
        return [
            "추천 시나리오 예산으로 체크아웃 잠금을 실행합니다.",
            "특가 안전성 검수로 보증/반품/판매자 조건을 확인합니다.",
            "구매 승인 브리프로 증거를 공유합니다.",
        ]
    if recommended.scenario_id == "wait_target":
        return [
            "목표가 감시 키트로 대기 기준을 등록합니다.",
            "같은 예산의 대체 후보를 후보 비교표에서 확인합니다.",
            "대기 기한이 지나면 조건 완화 또는 증액 시나리오로 재검토합니다.",
        ]
    return [
        recommended.recommended_action,
        "대체 후보 rescue로 예산 내 후보 3개를 확인합니다.",
        "조건을 낮추기 전 구매 실패 비용을 다시 계산합니다.",
    ]
