from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    MistakeCostCalculatorRequest,
    MistakeCostCalculatorResult,
    MistakeCostLineItem,
    MistakeCostRiskOption,
    PublicMistakeCostCalculator,
)


def build_public_mistake_cost_calculator(
    generated_at: datetime | None = None,
) -> PublicMistakeCostCalculator:
    generated_at = generated_at or datetime.now(UTC)
    return PublicMistakeCostCalculator(
        generated_at=generated_at.isoformat(),
        headline="잘못 산 컴퓨터의 숨은 비용을 먼저 계산합니다.",
        summary=(
            "예산, 수량, 구매 긴급도, 걱정되는 실패 유형을 고르면 반품·재구매·승인 지연·"
            "성능 부족으로 생길 수 있는 손실을 금액으로 보여줍니다."
        ),
        default_category=Category.desktop_pc,
        default_budget_krw=2_200_000,
        risk_options=_risk_options(),
        next_actions=[
            "예상 손실이 예산의 20%를 넘으면 결제 전 검수와 공유 리포트를 먼저 만드세요.",
            "팀 구매는 수량을 넣어 승인 지연과 재구매 비용까지 함께 계산하세요.",
            "계산 결과의 분석 prefill로 첫 구매 리포트를 생성하세요.",
        ],
    )


def estimate_mistake_cost(
    request: MistakeCostCalculatorRequest,
    generated_at: datetime | None = None,
) -> MistakeCostCalculatorResult:
    generated_at = generated_at or datetime.now(UTC)
    category = request.category
    budget = _normalize_budget(request.budget_krw)
    quantity = max(1, min(200, request.quantity))
    urgency = _normalize_urgency(request.urgency)
    selected = request.selected_risks or _default_risks(category, quantity)
    line_items = _line_items(
        category=category,
        budget_krw=budget,
        quantity=quantity,
        urgency=urgency,
        selected_risks=selected,
    )
    estimated_cost = sum(item.estimated_cost_krw for item in line_items)
    protected_value = budget * quantity
    risk_score = _risk_score(estimated_cost, protected_value, quantity, urgency)
    risk_level = _risk_level(risk_score)
    label = "데스크톱 PC" if category == Category.desktop_pc else "노트북"
    return MistakeCostCalculatorResult(
        generated_at=generated_at.isoformat(),
        category=category,
        budget_krw=budget,
        quantity=quantity,
        urgency=urgency,
        estimated_mistake_cost_krw=estimated_cost,
        protected_value_krw=protected_value,
        risk_score=risk_score,
        risk_level=risk_level,
        headline=_headline(risk_level, estimated_cost),
        summary=(
            f"{label} {quantity}대 기준으로 예산 {protected_value:,}원 중 "
            f"{estimated_cost:,}원 규모의 구매 실패 비용을 막아야 합니다."
        ),
        line_items=line_items,
        analysis_prefill=_analysis_prefill(category, budget, quantity, selected, urgency),
        share_copy=_share_copy(label, estimated_cost, risk_level),
        next_actions=_next_actions(risk_level, quantity),
    )


def _risk_options() -> list[MistakeCostRiskOption]:
    return [
        MistakeCostRiskOption(
            risk_id="performance_mismatch",
            label="성능 부족·과투자",
            default_weight=0.18,
            description="CPU/GPU/RAM 병목, 필요 없는 고성능 옵션, 업그레이드 한계를 금액화합니다.",
        ),
        MistakeCostRiskOption(
            risk_id="compatibility_blocker",
            label="호환성·옵션 불일치",
            default_weight=0.22,
            description="소켓, 파워, 케이스 간섭, 노트북 옵션명 불일치로 재구매하는 비용입니다.",
        ),
        MistakeCostRiskOption(
            risk_id="price_timing_loss",
            label="특가 착시·가격 타이밍",
            default_weight=0.08,
            description=(
                "쿠폰 종료, 배송비, 카드 조건, 목표가 미확인으로 더 비싸게 사는 차이입니다."
            ),
        ),
        MistakeCostRiskOption(
            risk_id="return_delay",
            label="반품·교환 시간 손실",
            default_weight=0.1,
            description="반품 배송, 재주문, 업무 지연, 세팅 시간을 금액으로 환산합니다.",
        ),
        MistakeCostRiskOption(
            risk_id="approval_rework",
            label="승인 지연·내부 재검토",
            default_weight=0.12,
            description=(
                "팀 구매에서 승인자와 실사용자가 같은 근거를 보지 못해 생기는 재작업입니다."
            ),
        ),
    ]


def _line_items(
    *,
    category: Category,
    budget_krw: int,
    quantity: int,
    urgency: str,
    selected_risks: list[str],
) -> list[MistakeCostLineItem]:
    option_map = {option.risk_id: option for option in _risk_options()}
    urgency_multiplier = {
        "low": 0.86,
        "normal": 1.0,
        "urgent": 1.18,
        "team_rollout": 1.35,
    }[urgency]
    category_multiplier = 1.08 if category == Category.desktop_pc else 1.0
    quantity_multiplier = 1 + min(0.75, (quantity - 1) * 0.035)
    items: list[MistakeCostLineItem] = []
    for risk_id in selected_risks:
        option = option_map.get(risk_id)
        if not option:
            continue
        raw_cost = (
            budget_krw
            * quantity
            * option.default_weight
            * urgency_multiplier
            * category_multiplier
            * quantity_multiplier
        )
        items.append(
            MistakeCostLineItem(
                item_id=risk_id,
                label=option.label,
                estimated_cost_krw=_round_cost(raw_cost),
                prevention=_prevention(risk_id, category, quantity),
            )
        )
    if items:
        return items
    return _line_items(
        category=category,
        budget_krw=budget_krw,
        quantity=quantity,
        urgency=urgency,
        selected_risks=_default_risks(category, quantity),
    )


def _normalize_budget(budget_krw: int) -> int:
    return min(30_000_000, max(300_000, budget_krw))


def _normalize_urgency(urgency: str) -> str:
    normalized = urgency.strip().lower()
    if normalized in {"low", "normal", "urgent", "team_rollout"}:
        return normalized
    return "normal"


def _default_risks(category: Category, quantity: int) -> list[str]:
    risks = ["performance_mismatch", "price_timing_loss", "return_delay"]
    if category == Category.desktop_pc:
        risks.insert(1, "compatibility_blocker")
    if quantity >= 3:
        risks.append("approval_rework")
    return risks


def _round_cost(value: float) -> int:
    return int(round(value / 10_000) * 10_000)


def _risk_score(
    estimated_cost: int,
    protected_value: int,
    quantity: int,
    urgency: str,
) -> float:
    if protected_value <= 0:
        return 0.0
    base = min(88.0, estimated_cost / protected_value * 100)
    quantity_boost = min(8.0, max(0, quantity - 1) * 0.9)
    urgency_boost = {"low": 0.0, "normal": 4.0, "urgent": 8.0, "team_rollout": 10.0}[urgency]
    return round(min(100.0, base + quantity_boost + urgency_boost), 1)


def _risk_level(score: float) -> str:
    if score >= 55:
        return "blocker"
    if score >= 32:
        return "warning"
    return "ok"


def _headline(risk_level: str, estimated_cost: int) -> str:
    if risk_level == "blocker":
        return f"그대로 사면 약 {estimated_cost:,}원 규모의 실패 비용이 생길 수 있습니다."
    if risk_level == "warning":
        return f"결제 전 약 {estimated_cost:,}원 규모의 리스크를 줄여야 합니다."
    return f"현재 입력 기준 예상 실패 비용은 약 {estimated_cost:,}원입니다."


def _prevention(risk_id: str, category: Category, quantity: int) -> str:
    label = "데스크톱 호환성" if category == Category.desktop_pc else "노트북 옵션·발열"
    return {
        "performance_mismatch": (
            "용도, 해상도, 필수 조건을 먼저 고정하고 TOP 3와 제외 후보를 같이 비교합니다."
        ),
        "compatibility_blocker": f"{label} 체크리스트와 결제 전 옵션명 대조를 실행합니다.",
        "price_timing_loss": (
            "실구매가, 배송비, 쿠폰 종료, 목표가 알림을 분리해 가격 타이밍을 판단합니다."
        ),
        "return_delay": "판매자 질문, 반품 조건, 캡처할 증거를 구매 실행 패키지로 남깁니다.",
        "approval_rework": (
            "공유 리포트와 Team 상담 키트로 승인자, 실사용자, 구매 담당자가 같은 근거를 봅니다."
            if quantity >= 3
            else "공유 리포트로 주변 검토를 먼저 받아 재검토 시간을 줄입니다."
        ),
    }[risk_id]


def _analysis_prefill(
    category: Category,
    budget_krw: int,
    quantity: int,
    selected_risks: list[str],
    urgency: str,
) -> str:
    label = "데스크톱 PC" if category == Category.desktop_pc else "노트북"
    risk_labels = [option.label for option in _risk_options() if option.risk_id in selected_risks]
    risk_text = ", ".join(risk_labels[:4]) or "구매 실패 리스크"
    if quantity >= 3:
        return (
            f"팀에 지급할 {label} {quantity}대를 대당 {budget_krw:,}원 안에서 추천해줘. "
            f"긴급도는 {urgency}이고 {risk_text}를 줄이는 공유 리포트와 결제 전 검수까지 같이 봐줘."
        )
    return (
        f"{label}을 {budget_krw:,}원 안에서 추천해줘. "
        f"{risk_text} 때문에 잘못 살까 걱정돼서 가격 타이밍, 호환성, 결제 전 검수를 같이 봐줘."
    )


def _share_copy(label: str, estimated_cost: int, risk_level: str) -> str:
    risk_label = {"ok": "낮음", "warning": "주의", "blocker": "높음"}[risk_level]
    return (
        f"SpecPilot AI 구매 실패 비용 계산 결과: {label} 구매에서 약 {estimated_cost:,}원 "
        f"규모의 리스크가 있습니다. 위험도는 {risk_label}이고, 분석 리포트로 가격·호환성·"
        "결제 전 검수를 먼저 확인해보려 합니다."
    )


def _next_actions(risk_level: str, quantity: int) -> list[str]:
    actions = [
        "분석 prefill로 TOP 3와 제외 후보를 생성하세요.",
        "구매 실패 비용 항목을 공유해 주변 검토를 받으세요.",
        "결제 전 체크리스트에서 캡처할 증거를 먼저 확인하세요.",
    ]
    if risk_level == "blocker":
        actions.insert(0, "즉시 결제하지 말고 검수 후 구매 판정을 먼저 받으세요.")
    if quantity >= 3:
        actions.append("Team 상담 키트로 승인 자료와 롤아웃 체크리스트를 만드세요.")
    return actions
