from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    CheckStatus,
    OwnershipCostLine,
    OwnershipCostRequest,
    OwnershipCostScenario,
    PublicOwnershipCostKit,
)


def build_public_ownership_cost_kit(
    request: OwnershipCostRequest,
    generated_at: datetime | None = None,
) -> PublicOwnershipCostKit:
    generated_at = generated_at or datetime.now(UTC)
    months = request.expected_years * 12
    resale_rate = _resale_rate(request)
    resale_value = round(request.purchase_price_krw * resale_rate / 100)
    maintenance_total = request.yearly_maintenance_krw * request.expected_years
    downtime_cost = request.downtime_days * request.daily_value_krw
    net_cost = max(
        0,
        request.purchase_price_krw
        + maintenance_total
        + request.planned_upgrade_cost_krw
        + downtime_cost
        - resale_value,
    )
    monthly_cost = round(net_cost / months) if months else net_cost
    risk_flags = _risk_flags(request, resale_rate, monthly_cost)
    score = _score(request, resale_rate, monthly_cost, risk_flags)
    priority = _priority(score, risk_flags)
    return PublicOwnershipCostKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=_title(request),
        priority=priority,
        ownership_score=score,
        expected_resale_value_krw=resale_value,
        net_cost_krw=net_cost,
        monthly_cost_krw=monthly_cost,
        headline=_headline(request, priority, monthly_cost),
        summary=_summary(request, priority, resale_rate, net_cost, monthly_cost),
        cost_lines=_cost_lines(request, resale_value, maintenance_total, downtime_cost),
        scenarios=_scenarios(request, resale_rate, maintenance_total, downtime_cost, months),
        risk_flags=risk_flags,
        seller_questions=_seller_questions(request),
        analysis_prefill=_analysis_prefill(request, priority, resale_rate, net_cost, monthly_cost),
        share_copy=_share_copy(request, priority, resale_value, monthly_cost),
        next_actions=_next_actions(priority, risk_flags),
    )


def _title(request: OwnershipCostRequest) -> str:
    return request.product_title.strip() or ("노트북 구매 후보" if request.category == Category.laptop else "컴퓨터 구매 후보")


def _resale_rate(request: OwnershipCostRequest) -> int:
    if request.resale_rate_percent is not None:
        return request.resale_rate_percent
    signal = request.brand_resale_signal.lower()
    if any(token in signal for token in ("high", "높", "맥", "mac", "thinkpad", "legion", "gram")):
        base = 48 if request.category == Category.laptop else 42
    elif any(token in signal for token in ("low", "낮", "무명", "unknown", "whitebox")):
        base = 28 if request.category == Category.laptop else 24
    else:
        base = 38 if request.category == Category.laptop else 32
    base -= max(0, request.expected_years - 3) * 5
    if any(_severe_risk(risk) for risk in request.condition_risks):
        base -= 10
    return max(5, min(70, base))


def _severe_risk(risk: str) -> bool:
    lowered = risk.lower()
    return any(
        token in lowered
        for token in (
            "리퍼",
            "전시",
            "중고",
            "해외",
            "병행",
            "보증 없음",
            "as 불가",
            "파손",
            "refurb",
            "scratch",
        )
    )


def _risk_flags(
    request: OwnershipCostRequest,
    resale_rate: int,
    monthly_cost: int,
) -> list[str]:
    flags: list[str] = []
    if resale_rate < 25:
        flags.append("예상 재판매율이 낮아 실질 비용이 커질 수 있습니다.")
    if request.warranty_months < min(24, request.expected_years * 12):
        flags.append("목표 보유 기간 대비 보증 기간이 짧습니다.")
    if request.planned_upgrade_cost_krw > request.purchase_price_krw * 0.18:
        flags.append("구매 후 업그레이드 비용이 초기 구매가 대비 큽니다.")
    if request.downtime_days and request.daily_value_krw:
        flags.append("다운타임 비용이 총소유비용에 반영되었습니다.")
    for risk in request.condition_risks[:4]:
        if risk.strip():
            flags.append(f"조건 리스크: {risk.strip()}")
    if monthly_cost > 120_000 and request.category == Category.desktop_pc:
        flags.append("월 실질 비용이 데스크톱 공개 기준보다 높습니다.")
    if monthly_cost > 150_000 and request.category == Category.laptop:
        flags.append("월 실질 비용이 노트북 공개 기준보다 높습니다.")
    if not flags:
        flags.append("현재 입력 기준 총소유비용 리스크는 크지 않습니다.")
    return flags[:8]


def _score(
    request: OwnershipCostRequest,
    resale_rate: int,
    monthly_cost: int,
    risk_flags: list[str],
) -> int:
    score = 100
    if resale_rate < 25:
        score -= 24
    elif resale_rate < 35:
        score -= 12
    if request.warranty_months < 12:
        score -= 16
    elif request.warranty_months < min(24, request.expected_years * 12):
        score -= 8
    if request.planned_upgrade_cost_krw > request.purchase_price_krw * 0.18:
        score -= 12
    if any("조건 리스크" in flag for flag in risk_flags):
        score -= 10
    if monthly_cost > 150_000:
        score -= 12
    elif monthly_cost > 120_000:
        score -= 6
    return max(0, min(100, score))


def _priority(score: int, risk_flags: list[str]) -> CheckStatus:
    if score < 60 or any("보증 없음" in flag or "AS 불가" in flag for flag in risk_flags):
        return CheckStatus.blocker
    if score < 82 or any("리스크" in flag or "짧" in flag for flag in risk_flags):
        return CheckStatus.warning
    return CheckStatus.ok


def _cost_lines(
    request: OwnershipCostRequest,
    resale_value: int,
    maintenance_total: int,
    downtime_cost: int,
) -> list[OwnershipCostLine]:
    return [
        OwnershipCostLine(
            line_id="purchase_price",
            label="구매가",
            amount_krw=request.purchase_price_krw,
            explanation="최종 결제 예정 금액입니다.",
        ),
        OwnershipCostLine(
            line_id="maintenance",
            label="유지/소모품",
            amount_krw=maintenance_total,
            explanation=f"{request.expected_years}년 동안 예상한 연간 유지비입니다.",
        ),
        OwnershipCostLine(
            line_id="planned_upgrade",
            label="계획 업그레이드",
            amount_krw=request.planned_upgrade_cost_krw,
            explanation="RAM, SSD, 파워, 배터리 등 구매 후 추가 비용입니다.",
        ),
        OwnershipCostLine(
            line_id="downtime",
            label="다운타임 비용",
            amount_krw=downtime_cost,
            explanation="세팅 지연, 반품, 업무 중단을 금액화한 값입니다.",
        ),
        OwnershipCostLine(
            line_id="resale_value",
            label="예상 재판매 회수",
            amount_krw=-resale_value,
            explanation="목표 보유 기간 후 회수 가능한 중고 판매 예상액입니다.",
        ),
    ]


def _scenarios(
    request: OwnershipCostRequest,
    resale_rate: int,
    maintenance_total: int,
    downtime_cost: int,
    months: int,
) -> list[OwnershipCostScenario]:
    scenarios = []
    for scenario_id, label, delta in (
        ("conservative", "보수적 재판매", -10),
        ("expected", "기준 재판매", 0),
        ("optimistic", "낙관적 재판매", 8),
    ):
        rate = max(5, min(80, resale_rate + delta))
        resale_value = round(request.purchase_price_krw * rate / 100)
        net_cost = max(
            0,
            request.purchase_price_krw
            + maintenance_total
            + request.planned_upgrade_cost_krw
            + downtime_cost
            - resale_value,
        )
        monthly = round(net_cost / months) if months else net_cost
        scenarios.append(
            OwnershipCostScenario(
                scenario_id=scenario_id,
                label=f"{label} {rate}%",
                resale_value_krw=resale_value,
                net_cost_krw=net_cost,
                monthly_cost_krw=monthly,
                status=CheckStatus.warning if monthly > 140_000 else CheckStatus.ok,
            )
        )
    return scenarios


def _seller_questions(request: OwnershipCostRequest) -> list[str]:
    questions = [
        "제조사 보증 기간, AS 접수 경로, 양도 시 보증 승계 가능 여부를 확인해 주세요.",
        "리퍼/전시/해외/병행 조건이 있으면 중고 판매와 보증에 불리한 예외가 있나요?",
        "배터리, 어댑터, 파워, 저장장치 같은 소모/교체 부품 비용을 확인해 주세요.",
    ]
    if request.category == Category.laptop:
        questions.append("배터리 교체 비용과 공식 교체 가능 기간을 알려주세요.")
    else:
        questions.append("케이스/파워/메인보드 모델명을 중고 판매 문구에 명시할 수 있나요?")
    return questions


def _headline(
    request: OwnershipCostRequest,
    priority: CheckStatus,
    monthly_cost: int,
) -> str:
    if priority == CheckStatus.blocker:
        return f"{_title(request)}는 실질 월 비용을 다시 계산해야 합니다."
    if priority == CheckStatus.warning:
        return f"{_title(request)}는 월 {monthly_cost:,}원 수준의 보유 비용을 확인하세요."
    return f"{_title(request)}는 총소유비용 기준으로도 설득 가능합니다."


def _summary(
    request: OwnershipCostRequest,
    priority: CheckStatus,
    resale_rate: int,
    net_cost: int,
    monthly_cost: int,
) -> str:
    return (
        f"{request.expected_years}년 보유, 예상 재판매율 {resale_rate}%, "
        f"순비용 {net_cost:,}원, 월 실질 비용 {monthly_cost:,}원. 상태 {priority.value}."
    )


def _analysis_prefill(
    request: OwnershipCostRequest,
    priority: CheckStatus,
    resale_rate: int,
    net_cost: int,
    monthly_cost: int,
) -> str:
    return (
        f"{_category_label(request.category)} '{_title(request)}' 총소유비용을 분석해줘. "
        f"구매가 {request.purchase_price_krw}, 보유 {request.expected_years}년, "
        f"예상 재판매율 {resale_rate}%, 순비용 {net_cost}, 월 비용 {monthly_cost}, 상태 {priority.value}."
    )


def _category_label(category: Category) -> str:
    return "노트북" if category == Category.laptop else "컴퓨터"


def _share_copy(
    request: OwnershipCostRequest,
    priority: CheckStatus,
    resale_value: int,
    monthly_cost: int,
) -> str:
    return (
        "SpecPilot AI 총소유비용 검수\n"
        f"제품: {_title(request)}\n"
        f"상태: {priority.value}\n"
        f"예상 재판매가: {resale_value:,}원\n"
        f"월 실질 비용: {monthly_cost:,}원"
    )


def _next_actions(priority: CheckStatus, risk_flags: list[str]) -> list[str]:
    if priority == CheckStatus.blocker:
        return [
            "재판매율, 보증 승계, 리퍼/해외 조건을 판매자에게 확인하기 전 결제를 보류하세요.",
            "초기 구매가가 낮아도 업그레이드/다운타임 비용을 포함해 대체 후보와 비교하세요.",
            "월 실질 비용이 높은 후보는 후보 비교 스냅샷에서 안전 우선 대안과 비교하세요.",
        ]
    if priority == CheckStatus.warning:
        return [
            risk_flags[0],
            "보증 기간과 중고 판매에 불리한 조건을 구매 승인 브리프에 포함하세요.",
            "재판매가 보수적 시나리오에서도 예산에 맞는지 확인하세요.",
        ]
    return [
        "총소유비용 요약을 가족/팀 승인 문구에 붙이세요.",
        "첫 부팅 세팅 검수에서 실제 상태를 저장해 재판매 증거로 남기세요.",
        "보증 등록과 영수증 보관으로 잔존 가치를 유지하세요.",
    ]
