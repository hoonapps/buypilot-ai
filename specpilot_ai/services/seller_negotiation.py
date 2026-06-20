from datetime import UTC, datetime

from specpilot_ai.core.models import (
    CheckStatus,
    PublicSellerNegotiationKit,
    SellerNegotiationLever,
    SellerNegotiationMessage,
    SellerNegotiationRequest,
)


def build_public_seller_negotiation_kit(
    request: SellerNegotiationRequest,
    generated_at: datetime | None = None,
) -> PublicSellerNegotiationKit:
    generated_at = generated_at or datetime.now(UTC)
    fair_offer = _fair_offer(request)
    expected_saving = max(0, request.current_price_krw - fair_offer)
    score = _score(request, expected_saving)
    priority = _priority(request, score)
    levers = _levers(request, fair_offer)
    return PublicSellerNegotiationKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=_title(request),
        seller_name=_seller(request),
        priority=priority,
        negotiation_score=score,
        expected_saving_krw=expected_saving,
        fair_offer_krw=fair_offer,
        max_acceptable_price_krw=_max_acceptable_price(request, fair_offer),
        headline=_headline(request, priority, expected_saving),
        summary=_summary(request, priority, fair_offer, expected_saving),
        levers=levers,
        message_variants=_message_variants(request, priority, fair_offer, levers),
        guardrails=_guardrails(request, priority),
        evidence_checklist=_evidence_checklist(request),
        seller_questions=_seller_questions(request),
        analysis_prefill=_analysis_prefill(request, priority, fair_offer, expected_saving),
        share_copy=_share_copy(request, priority, fair_offer, expected_saving),
        next_actions=_next_actions(priority),
    )


def _title(request: SellerNegotiationRequest) -> str:
    return request.product_title.strip() or "구매 후보"


def _seller(request: SellerNegotiationRequest) -> str:
    return request.seller_name.strip() or "판매자"


def _risk_text(request: SellerNegotiationRequest) -> str:
    return " ".join(request.risk_terms).lower()


def _has_hard_risk(request: SellerNegotiationRequest) -> bool:
    text = _risk_text(request)
    return any(term in text for term in ("반품 불가", "as 불가", "보증 없음", "해외", "리퍼", "전시", "중고"))


def _target_anchor(request: SellerNegotiationRequest) -> int:
    anchors = [
        value
        for value in (request.target_price_krw, request.budget_krw, request.competing_price_krw)
        if value is not None and value > 0
    ]
    return min(anchors) if anchors else request.current_price_krw


def _fair_offer(request: SellerNegotiationRequest) -> int:
    anchor = _target_anchor(request)
    removable_cost = request.shipping_fee_krw + request.assembly_fee_krw + request.os_fee_krw
    condition_discount = min(
        max(0, request.current_price_krw - anchor),
        max(20_000, round(request.current_price_krw * 0.06)),
    )
    fee_discount = min(removable_cost, max(0, round(request.current_price_krw * 0.04)))
    urgency_buffer = 0 if request.urgency in {"today", "within_24h"} else 20_000
    offer = request.current_price_krw - condition_discount - fee_discount - urgency_buffer
    if request.target_price_krw is not None:
        offer = min(offer, request.target_price_krw)
    if request.budget_krw is not None:
        offer = min(offer, request.budget_krw)
    return max(0, offer)


def _max_acceptable_price(request: SellerNegotiationRequest, fair_offer: int) -> int:
    candidates = [request.current_price_krw]
    if request.budget_krw is not None:
        candidates.append(request.budget_krw)
    if request.target_price_krw is not None:
        candidates.append(request.target_price_krw + max(20_000, round(request.current_price_krw * 0.02)))
    return max(fair_offer, min(candidates))


def _score(request: SellerNegotiationRequest, expected_saving: int) -> int:
    score = 55
    if expected_saving >= max(50_000, request.current_price_krw * 0.03):
        score += 18
    if request.competing_price_krw is not None and request.competing_price_krw < request.current_price_krw:
        score += 12
    if request.shipping_fee_krw + request.assembly_fee_krw + request.os_fee_krw > 0:
        score += 8
    if request.stock_count is not None and request.stock_count <= 3:
        score -= 10
    if request.urgency in {"today", "within_24h"}:
        score -= 8
    if _has_hard_risk(request):
        score -= 24
    if not request.must_keep_conditions:
        score -= 5
    return max(0, min(100, score))


def _priority(request: SellerNegotiationRequest, score: int) -> CheckStatus:
    if _has_hard_risk(request):
        return CheckStatus.blocker
    if score < 60 or (request.stock_count is not None and request.stock_count <= 3):
        return CheckStatus.warning
    return CheckStatus.ok


def _money(value: int | None) -> str:
    return f"{value:,}원" if value is not None else "미입력"


def _headline(
    request: SellerNegotiationRequest,
    priority: CheckStatus,
    expected_saving: int,
) -> str:
    if priority == CheckStatus.blocker:
        return f"{_title(request)}는 가격 협상보다 조건 확정이 먼저입니다."
    if priority == CheckStatus.warning:
        return f"{_title(request)}는 {expected_saving:,}원 절감 요청과 조건 고정을 함께 보내세요."
    return f"{_title(request)}는 근거 있는 조건 협상 메시지를 보낼 수 있습니다."


def _summary(
    request: SellerNegotiationRequest,
    priority: CheckStatus,
    fair_offer: int,
    expected_saving: int,
) -> str:
    return (
        f"{_seller(request)} 기준 현재가 {_money(request.current_price_krw)}, "
        f"제안가 {_money(fair_offer)}, 예상 절감 {_money(expected_saving)}. "
        f"상태 {priority.value}. 가격보다 출고 사양, 배송, AS, 반품 조건을 문서화해야 합니다."
    )


def _levers(request: SellerNegotiationRequest, fair_offer: int) -> list[SellerNegotiationLever]:
    levers: list[SellerNegotiationLever] = []
    if request.competing_price_krw is not None and request.competing_price_krw < request.current_price_krw:
        levers.append(
            SellerNegotiationLever(
                lever_id="price_match",
                label="가격 매칭",
                priority=CheckStatus.ok,
                ask=f"동일 사양 경쟁가 {_money(request.competing_price_krw)}에 맞출 수 있나요?",
                expected_value_krw=request.current_price_krw - request.competing_price_krw,
                proof_to_attach="경쟁 상품 가격, 판매자, 옵션명 캡처",
                fallback=f"불가하면 {_money(fair_offer)} 이하 대체 후보와 비교",
            )
        )
    if request.shipping_fee_krw > 0:
        levers.append(
            SellerNegotiationLever(
                lever_id="shipping_waiver",
                label="배송비 조정",
                priority=CheckStatus.warning,
                ask="결제 전 확정 시 배송비 면제 또는 일부 조정이 가능한가요?",
                expected_value_krw=request.shipping_fee_krw,
                proof_to_attach="최종 결제 화면 배송비 캡처",
                fallback="배송비 포함 총액 기준으로 목표가 감시",
            )
        )
    bundle_fee = request.assembly_fee_krw + request.os_fee_krw
    if bundle_fee > 0:
        levers.append(
            SellerNegotiationLever(
                lever_id="assembly_os_bundle",
                label="조립/OS 번들",
                priority=CheckStatus.warning,
                ask="조립비 또는 OS 비용을 번들 할인으로 조정할 수 있나요?",
                expected_value_krw=bundle_fee,
                proof_to_attach="조립/OS 선택 비용 캡처",
                fallback="OS 미포함 또는 직접 설치 시 총액을 다시 계산",
            )
        )
    levers.append(
        SellerNegotiationLever(
            lever_id="condition_lock",
            label="조건 고정",
            priority=CheckStatus.ok if not _has_hard_risk(request) else CheckStatus.blocker,
            ask="가격 조정 후에도 출고 사양, 반품, AS, 배송일 조건이 동일하게 유지되나요?",
            expected_value_krw=0,
            proof_to_attach="판매자 답변과 정책 페이지 캡처",
            fallback="조건이 흐려지면 가격 협상 성공으로 보지 않고 결제 보류",
        )
    )
    if request.stock_count is not None and request.stock_count <= 5:
        levers.append(
            SellerNegotiationLever(
                lever_id="stock_hold",
                label="재고 고정",
                priority=CheckStatus.warning,
                ask="답변 후 결제까지 현재 옵션과 가격으로 재고를 유지할 수 있나요?",
                expected_value_krw=0,
                proof_to_attach="재고 수량과 판매자 답변 캡처",
                fallback="재고가 바뀌면 대체 후보 rescue로 이동",
            )
        )
    return levers[:6]


def _message_variants(
    request: SellerNegotiationRequest,
    priority: CheckStatus,
    fair_offer: int,
    levers: list[SellerNegotiationLever],
) -> list[SellerNegotiationMessage]:
    title = _title(request)
    seller = _seller(request)
    conditions = _conditions_text(request)
    lever_summary = " / ".join(lever.label for lever in levers[:3])
    blocker_note = (
        "\n단, 반품/AS/출고 사양 조건이 명확하지 않으면 결제하지 않겠습니다."
        if priority == CheckStatus.blocker
        else ""
    )
    return [
        SellerNegotiationMessage(
            channel="seller_chat",
            label="판매자 채팅",
            tone="polite",
            copy_text=(
                f"안녕하세요, {seller}님. {title} 결제 전 문의드립니다.\n"
                f"현재 최종가가 {_money(request.current_price_krw)}인데, "
                f"{_money(fair_offer)} 조건으로 결제 가능한지 확인 부탁드립니다.\n"
                f"요청 항목: {lever_summary}\n"
                f"유지 조건: {conditions}{blocker_note}"
            ),
            cta_label="판매자에게 보내기",
        ),
        SellerNegotiationMessage(
            channel="team_approval",
            label="팀/가족 승인",
            tone="brief",
            copy_text=(
                f"{title} 구매 전 판매자에게 {_money(fair_offer)} 조건과 "
                f"{conditions} 유지 여부를 확인하겠습니다. "
                "조건이 하나라도 바뀌면 결제를 보류합니다."
            ),
            cta_label="승인자에게 공유",
        ),
        SellerNegotiationMessage(
            channel="community_check",
            label="커뮤니티 검토",
            tone="neutral",
            copy_text=(
                f"{title} 현재가 {_money(request.current_price_krw)}, 제안가 {_money(fair_offer)}입니다. "
                f"{conditions}을 유지한다는 답변을 받으면 결제해도 되는 조건인지 봐주세요."
            ),
            cta_label="검토 요청",
        ),
    ]


def _conditions_text(request: SellerNegotiationRequest) -> str:
    conditions = [item.strip() for item in request.must_keep_conditions if item.strip()]
    if not conditions:
        conditions = ["장바구니와 동일한 출고 사양", "반품/AS 조건", "배송 예정일"]
    return ", ".join(conditions[:5])


def _guardrails(
    request: SellerNegotiationRequest,
    priority: CheckStatus,
) -> list[str]:
    guardrails = [
        "가격을 낮추는 대신 사양, 보증, 반품, 배송 조건이 약해지면 협상 성공으로 보지 않습니다.",
        "판매자 답변은 결제 전 캡처하고 구매 실행 패키지의 증거 게이트에 붙입니다.",
        "최종 결제 화면 총액이 제안가보다 높으면 결제를 보류합니다.",
    ]
    if _has_hard_risk(request):
        guardrails.insert(0, "리퍼/전시/해외/AS 불가 조건은 가격 협상보다 공식 조건 답변이 먼저입니다.")
    if priority == CheckStatus.warning:
        guardrails.append("재고가 적거나 결제 마감이 가까우면 대체 후보를 동시에 열어 둡니다.")
    return guardrails[:6]


def _evidence_checklist(request: SellerNegotiationRequest) -> list[str]:
    evidence = [
        "현재 최종가와 배송비/조립비/OS 비용 캡처",
        "경쟁 상품 가격과 옵션명 캡처",
        "판매자 조건 협상 답변 캡처",
        "반품/AS/초기 불량 정책 캡처",
        "최종 결제 화면 총액 캡처",
    ]
    if request.stock_count is not None:
        evidence.append("재고 수량 캡처")
    return evidence


def _seller_questions(request: SellerNegotiationRequest) -> list[str]:
    return [
        f"{_money(_fair_offer(request))} 조건으로 결제할 수 있나요?",
        "가격 조정 후에도 실제 출고 사양이 장바구니 옵션과 동일한가요?",
        "배송 예정일, 반품 가능 기간, AS 접수 경로가 기존 조건과 동일한가요?",
        "쿠폰/카드 할인, 배송비, 조립비, OS 비용이 최종 결제 화면에서 어떻게 반영되나요?",
        "답변 후 결제까지 같은 가격과 재고를 유지할 수 있나요?",
    ]


def _analysis_prefill(
    request: SellerNegotiationRequest,
    priority: CheckStatus,
    fair_offer: int,
    expected_saving: int,
) -> str:
    return (
        f"'{_title(request)}'를 판매자 {_seller(request)}와 판매자 조건 협상해도 되는지 분석해줘. "
        f"현재가 {_money(request.current_price_krw)}, 제안가 {_money(fair_offer)}, "
        f"예상 절감 {_money(expected_saving)}, 예산 {_money(request.budget_krw)}, "
        f"경쟁가 {_money(request.competing_price_krw)}, 유지 조건 {_conditions_text(request)}, "
        f"위험 조건 {', '.join(request.risk_terms) or '없음'}, 상태 {priority.value}."
    )


def _share_copy(
    request: SellerNegotiationRequest,
    priority: CheckStatus,
    fair_offer: int,
    expected_saving: int,
) -> str:
    return (
        "SpecPilot AI 판매자 조건 협상 키트\n"
        f"제품: {_title(request)}\n"
        f"판매자: {_seller(request)}\n"
        f"상태: {priority.value}\n"
        f"현재가: {_money(request.current_price_krw)}\n"
        f"제안가: {_money(fair_offer)}\n"
        f"예상 절감: {_money(expected_saving)}\n"
        f"유지 조건: {_conditions_text(request)}"
    )


def _next_actions(priority: CheckStatus) -> list[str]:
    if priority == CheckStatus.blocker:
        return [
            "가격 조정 요청보다 반품/AS/출고 사양 답변을 먼저 받으세요.",
            "답변이 모호하면 판매자 증거 요청 키트로 pass/fail을 다시 판정하세요.",
            "조건이 닫히지 않으면 대체 후보 rescue로 이동하세요.",
        ]
    if priority == CheckStatus.warning:
        return [
            "제안가와 유지 조건을 판매자에게 보내고 답변을 캡처하세요.",
            "답변 후 구매 실행 패키지의 증거 게이트를 다시 확인하세요.",
            "재고/할인 만료가 가까우면 목표가 감시와 대체 후보를 동시에 열어 두세요.",
        ]
    return [
        "판매자에게 조건 협상 메시지를 보내고 답변을 캡처하세요.",
        "제안가가 받아들여지면 실구매가 분해 키트로 최종 총액을 다시 계산하세요.",
        "구매 실행 패키지에서 결제 전 중단 조건을 마지막으로 확인하세요.",
    ]
