from datetime import UTC, date, datetime, timedelta

from specpilot_ai.core.models import (
    AftercareDeadline,
    AftercareMessage,
    Category,
    CheckStatus,
    PublicPurchaseAftercareKit,
    PurchaseAftercareRequest,
)


def build_public_purchase_aftercare_kit(
    request: PurchaseAftercareRequest,
    generated_at: datetime | None = None,
) -> PublicPurchaseAftercareKit:
    generated_at = generated_at or datetime.now(UTC)
    today = generated_at.date()
    purchase_date = _parse_date(request.purchase_date, today)
    delivered_date = _parse_date(request.delivered_date, purchase_date)
    return_deadline = delivered_date + timedelta(days=request.return_window_days)
    warranty_deadline = _add_months(purchase_date, request.warranty_months)
    issues = _issues(request)
    price_delta = _price_delta(request)
    priority = _priority(today, return_deadline, warranty_deadline, issues, price_delta)
    deadlines = _deadlines(request, today, return_deadline, warranty_deadline, issues)
    outcome_prefill = _outcome_prefill(request, priority, price_delta, return_deadline)
    return PublicPurchaseAftercareKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=_title(request),
        seller_name=request.seller_name.strip() or "판매자",
        priority=priority,
        headline=_headline(request, priority, return_deadline),
        summary=_summary(request, today, return_deadline, warranty_deadline, price_delta),
        return_deadline=return_deadline.isoformat(),
        warranty_deadline=warranty_deadline.isoformat(),
        price_delta_krw=price_delta,
        deadlines=deadlines,
        capture_checklist=_capture_checklist(request),
        issue_triage=_issue_triage(issues, priority),
        outcome_prefill=outcome_prefill,
        messages=_messages(request, priority, return_deadline, warranty_deadline),
        analysis_prefill=_analysis_prefill(request, priority, price_delta, return_deadline, warranty_deadline),
        share_copy=_share_copy(request, priority, return_deadline, warranty_deadline),
        next_actions=_next_actions(priority, issues),
    )


def _parse_date(value: str, fallback: date) -> date:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return fallback


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    last_day = _last_day(year, month)
    return date(year, month, min(value.day, last_day))


def _last_day(year: int, month: int) -> int:
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day


def _title(request: PurchaseAftercareRequest) -> str:
    return request.product_title.strip() or ("노트북 구매" if request.category == Category.laptop else "컴퓨터 구매")


def _issues(request: PurchaseAftercareRequest) -> list[str]:
    return [issue.strip() for issue in request.issues if issue.strip()][:8]


def _price_delta(request: PurchaseAftercareRequest) -> int | None:
    if request.final_paid_price_krw is None or request.expected_price_krw is None:
        return None
    return request.final_paid_price_krw - request.expected_price_krw


def _priority(
    today: date,
    return_deadline: date,
    warranty_deadline: date,
    issues: list[str],
    price_delta: int | None,
) -> CheckStatus:
    if any(_severe_issue(issue) for issue in issues):
        return CheckStatus.blocker
    if return_deadline < today and issues:
        return CheckStatus.blocker
    if warranty_deadline < today:
        return CheckStatus.blocker
    if issues or return_deadline <= today + timedelta(days=2):
        return CheckStatus.warning
    if price_delta is not None and price_delta > 0:
        return CheckStatus.warning
    return CheckStatus.ok


def _severe_issue(issue: str) -> bool:
    lowered = issue.lower()
    severe_terms = (
        "불량",
        "파손",
        "부팅 안",
        "화면 안",
        "상이",
        "누락",
        "오배송",
        "dead",
        "broken",
        "defect",
    )
    return any(term in lowered for term in severe_terms)


def _deadlines(
    request: PurchaseAftercareRequest,
    today: date,
    return_deadline: date,
    warranty_deadline: date,
    issues: list[str],
) -> list[AftercareDeadline]:
    return_status = CheckStatus.blocker if return_deadline < today and issues else (
        CheckStatus.warning if return_deadline <= today + timedelta(days=2) else CheckStatus.ok
    )
    warranty_status = CheckStatus.blocker if warranty_deadline < today else CheckStatus.ok
    return [
        AftercareDeadline(
            deadline_id="return_window",
            label="반품/교환 마감",
            status=return_status,
            due_date=return_deadline.isoformat(),
            action="초기 불량, 사양 불일치, 구성품 누락을 마감 전 캡처하고 접수하세요.",
            reminder_copy=(
                f"{_title(request)} 반품/교환 마감이 {return_deadline.isoformat()}입니다. "
                "문제가 있으면 사진/영상/판매자 답변을 오늘 정리하세요."
            ),
        ),
        AftercareDeadline(
            deadline_id="warranty_end",
            label="보증 만료",
            status=warranty_status,
            due_date=warranty_deadline.isoformat(),
            action="보증 만료 전 제조사 등록, 영수증, 시리얼 번호를 보관하세요.",
            reminder_copy=(
                f"{_title(request)} 보증 만료 예정일은 {warranty_deadline.isoformat()}입니다. "
                "영수증과 시리얼 번호를 저장해두세요."
            ),
        ),
        AftercareDeadline(
            deadline_id="outcome_capture",
            label="구매 결과 회수",
            status=CheckStatus.warning,
            due_date=(today + timedelta(days=3)).isoformat(),
            action="실제 구매, 지연, 반품/취소 여부와 만족도를 저장해 다음 추천 품질에 반영하세요.",
            reminder_copy="구매 결과를 저장하면 다음 PC/노트북 추천에서 같은 실수를 줄일 수 있습니다.",
        ),
    ]


def _capture_checklist(request: PurchaseAftercareRequest) -> list[str]:
    checklist = [
        "최종 결제 영수증과 카드/쿠폰 할인 내역",
        "상품명, 장바구니 옵션명, 실제 배송 라벨",
        "박스 외관, 시리얼 번호, 구성품 사진",
        "전원/화면/키보드/포트/소음/발열 초기 점검 영상",
        "판매자 답변과 반품/AS 정책 캡처",
    ]
    if request.order_reference:
        checklist.insert(0, "주문번호 마스킹값")
    return checklist


def _issue_triage(issues: list[str], priority: CheckStatus) -> list[str]:
    if not issues:
        return [
            "수령 당일 외관, 구성품, 전원, 화면, 네트워크, 저장장치 인식을 확인하세요.",
            "문제가 없어도 영수증, 시리얼 번호, 보증 등록 화면을 보관하세요.",
        ]
    actions = [f"이슈 확인: {issue}" for issue in issues]
    if priority == CheckStatus.blocker:
        actions.insert(0, "초기 불량/사양 불일치 가능성이 있으니 반품 마감 전 교환/환불 접수를 우선하세요.")
    else:
        actions.insert(0, "증상이 반복되는지 영상으로 남기고 판매자 답변을 받아두세요.")
    return actions[:8]


def _outcome_prefill(
    request: PurchaseAftercareRequest,
    priority: CheckStatus,
    price_delta: int | None,
    return_deadline: date,
) -> str:
    status = "returned" if priority == CheckStatus.blocker else "purchased"
    delta = "미입력" if price_delta is None else f"{price_delta:+,}원"
    return (
        f"구매 결과 상태={status}, 제품={_title(request)}, 최종가={request.final_paid_price_krw or '미입력'}, "
        f"예상가 대비 차이={delta}, 반품 마감={return_deadline.isoformat()}, "
        f"이슈={', '.join(_issues(request)) if _issues(request) else '없음'}"
    )


def _messages(
    request: PurchaseAftercareRequest,
    priority: CheckStatus,
    return_deadline: date,
    warranty_deadline: date,
) -> list[AftercareMessage]:
    return [
        AftercareMessage(
            channel="self",
            label="내 체크리스트",
            copy_text=(
                f"{_title(request)} 구매 후 체크\n"
                f"- 반품/교환 마감: {return_deadline.isoformat()}\n"
                f"- 보증 만료: {warranty_deadline.isoformat()}\n"
                "- 영수증, 시리얼, 초기 점검 사진/영상을 저장"
            ),
            cta_label="내 기록에 저장",
        ),
        AftercareMessage(
            channel="seller",
            label="판매자 문의",
            copy_text=(
                f"{request.seller_name or '판매자'}님, {_title(request)} 수령 후 확인 중입니다. "
                "초기 불량/구성품 누락/사양 불일치가 있을 경우 반품 또는 교환 접수 절차를 안내해주세요."
            ),
            cta_label="판매자에게 보내기",
        ),
        AftercareMessage(
            channel="team",
            label="팀 구매 기록",
            copy_text=(
                f"[구매 결과 회수] {_title(request)} · 상태 {priority.value} · "
                f"반품 마감 {return_deadline.isoformat()} · 보증 만료 {warranty_deadline.isoformat()}"
            ),
            cta_label="팀 기록 공유",
        ),
    ]


def _headline(
    request: PurchaseAftercareRequest,
    priority: CheckStatus,
    return_deadline: date,
) -> str:
    if priority == CheckStatus.blocker:
        return f"{_title(request)}는 반품/교환 접수를 먼저 확인해야 합니다."
    if priority == CheckStatus.warning:
        return f"{_title(request)}는 {return_deadline.isoformat()} 전까지 증거를 정리하세요."
    return f"{_title(request)} 구매 후속 기록을 닫을 수 있습니다."


def _summary(
    request: PurchaseAftercareRequest,
    today: date,
    return_deadline: date,
    warranty_deadline: date,
    price_delta: int | None,
) -> str:
    days_left = (return_deadline - today).days
    delta = "최종가 차이 미입력" if price_delta is None else f"예상가 대비 {price_delta:+,}원"
    return (
        f"반품/교환 마감까지 {days_left}일, 보증 만료일은 {warranty_deadline.isoformat()}입니다. "
        f"{delta}. 구매 결과와 초기 점검 증거를 저장해 다음 추천 품질로 되돌립니다."
    )


def _analysis_prefill(
    request: PurchaseAftercareRequest,
    priority: CheckStatus,
    price_delta: int | None,
    return_deadline: date,
    warranty_deadline: date,
) -> str:
    delta = "미입력" if price_delta is None else f"{price_delta:+,}원"
    return (
        f"{_category_label(request.category)} '{_title(request)}' 구매 후 케어를 분석해줘. "
        f"최종가 {request.final_paid_price_krw or '미입력'}, 예상가 대비 {delta}, "
        f"반품 마감 {return_deadline.isoformat()}, 보증 만료 {warranty_deadline.isoformat()}, "
        f"우선순위 {priority.value}, 이슈 {', '.join(_issues(request)) if _issues(request) else '없음'}."
    )


def _category_label(category: Category) -> str:
    return "노트북" if category == Category.laptop else "컴퓨터"


def _share_copy(
    request: PurchaseAftercareRequest,
    priority: CheckStatus,
    return_deadline: date,
    warranty_deadline: date,
) -> str:
    return (
        "SpecPilot AI 구매 후 케어\n"
        f"제품: {_title(request)}\n"
        f"우선순위: {priority.value}\n"
        f"반품/교환 마감: {return_deadline.isoformat()}\n"
        f"보증 만료: {warranty_deadline.isoformat()}"
    )


def _next_actions(priority: CheckStatus, issues: list[str]) -> list[str]:
    if priority == CheckStatus.blocker:
        return [
            "사진/영상/영수증/시리얼 번호를 모아 반품 또는 교환 접수를 먼저 진행하세요.",
            "판매자 답변과 접수 번호를 캡처해 구매 결과에 저장하세요.",
            "같은 문제를 다음 추천에서 제외 조건으로 추가하세요.",
        ]
    if issues:
        return [
            "증상이 반복되는지 영상으로 남기고 판매자에게 문의 문구를 보내세요.",
            "반품 마감 전까지 구매 결과를 지연 또는 반품 검토 상태로 저장하세요.",
            "문제가 해결되면 만족도와 최종가 차이를 기록하세요.",
        ]
    return [
        "영수증, 시리얼 번호, 보증 등록 화면을 저장하세요.",
        "3일 안에 만족도와 최종가 차이를 구매 결과로 남기세요.",
        "다음 구매자를 위해 실제 사용 후기 한 줄을 공유 문구로 남기세요.",
    ]
