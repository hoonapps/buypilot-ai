from datetime import UTC, datetime

from specpilot_ai.core.models import (
    ApprovalCopyVariant,
    ApprovalVoteOption,
    Category,
    CheckStatus,
    PublicPurchaseApprovalBriefKit,
    PurchaseApprovalBriefRequest,
)


def build_public_purchase_approval_brief_kit(
    request: PurchaseApprovalBriefRequest,
    generated_at: datetime | None = None,
) -> PublicPurchaseApprovalBriefKit:
    generated_at = generated_at or datetime.now(UTC)
    title = request.product_title.strip() or _category_label(request.category)
    priority = _priority(request)
    reasons = _key_reasons(request)
    missing = _missing_evidence(request)
    approve_conditions = _approve_conditions(request, priority, missing)
    reject_reasons = _reject_reasons(request, priority, missing)
    decision_rule = _decision_rule(request, priority)
    approval_question = _approval_question(request, title, priority)
    buyer_brief = _buyer_brief(request, title, reasons, missing, priority)
    analysis_prefill = _analysis_prefill(request, title, reasons, missing, decision_rule)
    share_copy = _share_copy(request, title, priority, approval_question)
    return PublicPurchaseApprovalBriefKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=title,
        verdict=_normalized_verdict(request.verdict),
        priority=priority,
        headline=_headline(title, priority),
        summary=_summary(request, priority),
        decision_rule=decision_rule,
        approval_question=approval_question,
        buyer_brief=buyer_brief,
        reject_reasons=reject_reasons,
        approve_conditions=approve_conditions,
        evidence_checklist=_evidence_checklist(missing),
        vote_options=_vote_options(priority),
        copy_variants=_copy_variants(request, title, buyer_brief, approval_question),
        analysis_prefill=analysis_prefill,
        share_copy=share_copy,
        next_actions=_next_actions(priority, missing),
    )


def _priority(request: PurchaseApprovalBriefRequest) -> CheckStatus:
    verdict = _normalized_verdict(request.verdict)
    if verdict == "hold" or request.blocker_count > 0:
        return CheckStatus.blocker
    if verdict == "verify" or request.warning_count > 0 or request.missing_evidence:
        return CheckStatus.warning
    return CheckStatus.ok


def _normalized_verdict(verdict: str) -> str:
    normalized = verdict.strip().lower()
    return normalized if normalized in {"ready", "verify", "hold"} else "verify"


def _category_label(category: Category) -> str:
    return "노트북" if category == Category.laptop else "데스크톱 PC"


def _money(value: int | None) -> str:
    return f"{value:,}원" if value is not None else "미입력"


def _audience_label(audience: str) -> str:
    labels = {
        "family": "가족",
        "team": "팀",
        "community": "커뮤니티",
        "self": "본인",
    }
    return labels.get(audience.strip().lower(), "검토자")


def _key_reasons(request: PurchaseApprovalBriefRequest) -> list[str]:
    reasons = [reason.strip() for reason in request.key_reasons if reason.strip()]
    if reasons:
        return reasons[:5]
    if request.blocker_count > 0:
        return ["blocker가 남아 있어 결제 전 반대 근거를 먼저 닫아야 합니다."]
    if request.warning_count > 0:
        return ["warning이 남아 있어 증거 확인 후 제한 승인으로 판단해야 합니다."]
    return ["예산, 핵심 사양, 결제 전 증거가 큰 충돌 없이 맞습니다."]


def _missing_evidence(request: PurchaseApprovalBriefRequest) -> list[str]:
    missing = [item.strip() for item in request.missing_evidence if item.strip()]
    return missing[:6]


def _headline(title: str, priority: CheckStatus) -> str:
    if priority == CheckStatus.blocker:
        return f"{title}는 승인 전에 반대 사유를 먼저 닫아야 합니다."
    if priority == CheckStatus.warning:
        return f"{title}는 조건부 승인으로 공유하세요."
    return f"{title}는 바로 승인 가능한 상태로 공유할 수 있습니다."


def _summary(request: PurchaseApprovalBriefRequest, priority: CheckStatus) -> str:
    price = _money(request.cart_total_krw)
    budget = _money(request.budget_krw)
    if priority == CheckStatus.blocker:
        return (
            f"총액 {price}, 예산 {budget} 기준 blocker {request.blocker_count}개가 있어 "
            "승인 투표 전에 반대 사유와 대체 후보를 함께 보여줘야 합니다."
        )
    if priority == CheckStatus.warning:
        return (
            f"총액 {price}, 예산 {budget} 기준 warning {request.warning_count}개와 "
            f"누락 증거 {len(request.missing_evidence)}개를 확인하면 제한 승인할 수 있습니다."
        )
    return f"총액 {price}, 예산 {budget} 기준 큰 충돌이 없어 승인 질문과 증거만 짧게 공유합니다."


def _decision_rule(request: PurchaseApprovalBriefRequest, priority: CheckStatus) -> str:
    deadline = request.decision_deadline.strip() or "결제 전"
    if priority == CheckStatus.blocker:
        return f"{deadline}까지 blocker를 닫지 못하면 결제를 보류하고 대체 후보를 비교합니다."
    if priority == CheckStatus.warning:
        return f"{deadline}까지 누락 증거를 캡처하면 승인, 하나라도 비면 결제를 미룹니다."
    return f"{deadline}까지 가격과 옵션명이 그대로면 승인하고 결제 전 캡처만 남깁니다."


def _approval_question(
    request: PurchaseApprovalBriefRequest,
    title: str,
    priority: CheckStatus,
) -> str:
    audience = _audience_label(request.audience)
    if priority == CheckStatus.blocker:
        return f"{audience} 기준으로 {title} 결제를 반대해야 할 치명적 이유가 남아 있나요?"
    if priority == CheckStatus.warning:
        return f"{audience} 기준으로 아래 증거를 확인하면 {title} 구매를 승인해도 될까요?"
    return f"{audience} 기준으로 {title}를 이 조건이면 바로 승인해도 될까요?"


def _buyer_brief(
    request: PurchaseApprovalBriefRequest,
    title: str,
    reasons: list[str],
    missing: list[str],
    priority: CheckStatus,
) -> str:
    risk = (
        "결제 보류"
        if priority == CheckStatus.blocker
        else "조건부 승인"
        if priority == CheckStatus.warning
        else "승인 가능"
    )
    return (
        f"{title} 검토 요청: 총액 {_money(request.cart_total_krw)}, "
        f"예산 {_money(request.budget_krw)}, 판단 {risk}. "
        f"핵심 근거는 {' / '.join(reasons)}. "
        f"남은 증거는 {', '.join(missing) if missing else '없음'}입니다."
    )


def _reject_reasons(
    request: PurchaseApprovalBriefRequest,
    priority: CheckStatus,
    missing: list[str],
) -> list[str]:
    reasons: list[str] = []
    if request.blocker_count:
        reasons.append(f"blocker {request.blocker_count}개가 남아 결제 실패 비용이 큽니다.")
    if request.cart_total_krw is not None and request.cart_total_krw > request.budget_krw:
        over = request.cart_total_krw - request.budget_krw
        reasons.append(f"예산을 {over:,}원 초과했습니다.")
    if missing:
        reasons.append(f"누락 증거가 남았습니다: {', '.join(missing[:3])}")
    if not reasons and priority == CheckStatus.ok:
        reasons.append("가격, 옵션명, AS 조건이 결제 직전 바뀌면 승인 취소가 필요합니다.")
    return reasons[:5]


def _approve_conditions(
    request: PurchaseApprovalBriefRequest,
    priority: CheckStatus,
    missing: list[str],
) -> list[str]:
    conditions = [
        "장바구니 옵션명과 최종 결제 금액을 캡처했습니다.",
        "판매자/제조사 AS와 반품 조건을 확인했습니다.",
    ]
    if missing:
        conditions.insert(0, f"누락 증거를 먼저 채웁니다: {', '.join(missing[:3])}")
    if priority == CheckStatus.blocker:
        conditions.insert(0, "blocker가 0개가 될 때까지 결제 버튼을 누르지 않습니다.")
    if request.cart_total_krw is not None:
        conditions.append(f"최종 총액이 {_money(request.cart_total_krw)}에서 바뀌지 않았습니다.")
    return conditions[:6]


def _evidence_checklist(missing: list[str]) -> list[str]:
    base = [
        "판매 페이지 모델명과 장바구니 옵션명",
        "최종 결제 금액, 배송비, 쿠폰, 카드 할인",
        "RAM/SSD/GPU/패널/OS 선택값",
        "배송 예정일, 반품, AS, 판매자 답변",
    ]
    return list(dict.fromkeys(missing + base))[:8]


def _vote_options(priority: CheckStatus) -> list[ApprovalVoteOption]:
    return [
        ApprovalVoteOption(
            option_id="approve_now",
            label="승인",
            status=CheckStatus.ok,
            description="가격과 옵션명이 그대로면 결제해도 됩니다.",
            when_to_choose="blocker가 없고 필수 증거가 모두 캡처됐을 때",
        ),
        ApprovalVoteOption(
            option_id="approve_after_evidence",
            label="증거 확인 후 승인",
            status=CheckStatus.warning,
            description="누락 증거를 채운 뒤 같은 조건이면 승인합니다.",
            when_to_choose="warning이나 미확인 조건만 남았을 때",
        ),
        ApprovalVoteOption(
            option_id="reject_or_compare",
            label="반대/대체 후보 비교",
            status=CheckStatus.blocker,
            description="현재 후보는 멈추고 대체 후보를 비교합니다.",
            when_to_choose="blocker, 예산 초과, 리퍼/해외/AS 불명확 조건이 있을 때",
        ),
    ] if priority != CheckStatus.blocker else [
        ApprovalVoteOption(
            option_id="reject_or_compare",
            label="반대/대체 후보 비교",
            status=CheckStatus.blocker,
            description="현재 후보는 멈추고 대체 후보를 비교합니다.",
            when_to_choose="blocker가 하나라도 남았을 때",
        ),
        ApprovalVoteOption(
            option_id="approve_after_evidence",
            label="증거 확인 후 재검토",
            status=CheckStatus.warning,
            description="판매자 답변과 옵션 캡처가 확보되면 다시 승인합니다.",
            when_to_choose="blocker를 해결할 수 있는 판매자 답변을 받을 때",
        ),
    ]


def _copy_variants(
    request: PurchaseApprovalBriefRequest,
    title: str,
    buyer_brief: str,
    approval_question: str,
) -> list[ApprovalCopyVariant]:
    deadline = request.decision_deadline.strip() or "오늘 결제 전"
    return [
        ApprovalCopyVariant(
            channel="kakao",
            label="가족/지인",
            copy_text=f"{buyer_brief}\n{approval_question}\n마감: {deadline}",
            cta_label="찬성/반대 한 줄 답장",
        ),
        ApprovalCopyVariant(
            channel="team",
            label="팀 승인",
            copy_text=(
                f"[구매 승인 요청] {title}\n{buyer_brief}\n"
                f"승인 기준: blocker 0개, 누락 증거 0개, 총액 {_money(request.cart_total_krw)} 유지"
            ),
            cta_label="승인 스레드에 투표",
        ),
        ApprovalCopyVariant(
            channel="community",
            label="커뮤니티 검토",
            copy_text=(
                f"SpecPilot AI 구매 승인 브리프\n후보: {title}\n"
                f"{buyer_brief}\n반대할 치명적 조건이 있으면 알려주세요."
            ),
            cta_label="반대 사유 받기",
        ),
    ]


def _analysis_prefill(
    request: PurchaseApprovalBriefRequest,
    title: str,
    reasons: list[str],
    missing: list[str],
    decision_rule: str,
) -> str:
    return (
        f"{_category_label(request.category)} 후보 '{title}' 구매 승인 브리프를 분석해줘. "
        f"예산 {_money(request.budget_krw)}, 총액 {_money(request.cart_total_krw)}, "
        f"판정 {_normalized_verdict(request.verdict)}, blocker {request.blocker_count}개, "
        f"warning {request.warning_count}개. 핵심 근거: {' / '.join(reasons)}. "
        f"누락 증거: {', '.join(missing) if missing else '없음'}. "
        f"승인 규칙: {decision_rule}"
    )


def _share_copy(
    request: PurchaseApprovalBriefRequest,
    title: str,
    priority: CheckStatus,
    approval_question: str,
) -> str:
    return (
        "SpecPilot AI 구매 승인 브리프\n"
        f"후보: {title}\n"
        f"우선순위: {priority.value}\n"
        f"총액/예산: {_money(request.cart_total_krw)} / {_money(request.budget_krw)}\n"
        f"질문: {approval_question}"
    )


def _next_actions(priority: CheckStatus, missing: list[str]) -> list[str]:
    if priority == CheckStatus.blocker:
        return [
            "현재 후보 결제를 보류하고 blocker별 판매자 질문을 먼저 보냅니다.",
            "같은 예산의 대체 후보 2개를 승인 브리프에 함께 붙입니다.",
            "blocker가 닫히면 옵션/사양 빠른 검수를 다시 실행합니다.",
        ]
    if priority == CheckStatus.warning:
        return [
            f"누락 증거를 채웁니다: {', '.join(missing[:3]) if missing else '최종가와 옵션명 캡처'}",
            "승인 질문을 가족/팀/커뮤니티 중 한 곳에 공유합니다.",
            "찬성/반대 답변을 받은 뒤 분석 prefill로 최종 리포트를 생성합니다.",
        ]
    return [
        "가격과 옵션명이 바뀌지 않았는지 결제 직전 다시 캡처합니다.",
        "승인 문구를 공유해 반대 사유가 없는지 짧게 확인합니다.",
        "구매 후 결과를 저장해 다음 추천 품질에 반영합니다.",
    ]
