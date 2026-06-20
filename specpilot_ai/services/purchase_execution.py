from datetime import UTC, datetime

from specpilot_ai.core.models import (
    CheckStatus,
    PublicPurchaseExecutionKit,
    PurchaseExecutionGate,
    PurchaseExecutionKitRequest,
    PurchaseExecutionShareMessage,
    PurchaseExecutionStep,
)


def build_public_purchase_execution_kit(
    request: PurchaseExecutionKitRequest,
    generated_at: datetime | None = None,
) -> PublicPurchaseExecutionKit:
    generated_at = generated_at or datetime.now(UTC)
    priority = _priority(request)
    score = _score(request, priority)
    delta = (
        request.final_price_krw - request.budget_krw
        if request.final_price_krw is not None and request.budget_krw is not None
        else None
    )
    questions = _seller_questions(request, priority)
    return PublicPurchaseExecutionKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=_title(request),
        seller_name=_seller(request),
        priority=priority,
        execution_score=score,
        headline=_headline(request, priority),
        summary=_summary(request, priority, score, delta),
        primary_action=_primary_action(request, priority),
        decision_checkpoint=_decision_checkpoint(request, priority),
        price_delta_krw=delta,
        checkout_steps=_checkout_steps(request, priority),
        evidence_gates=_evidence_gates(request, priority, delta),
        seller_questions=questions,
        stop_conditions=_stop_conditions(request, priority, delta),
        share_messages=_share_messages(request, priority, questions),
        analysis_prefill=_analysis_prefill(request, priority, score, delta),
        share_copy=_share_copy(request, priority, score, delta),
        next_actions=_next_actions(request, priority),
    )


def _title(request: PurchaseExecutionKitRequest) -> str:
    return request.product_title.strip() or "구매 후보"


def _seller(request: PurchaseExecutionKitRequest) -> str:
    return request.seller_name.strip() or "판매자"


def _normalized_verdict(verdict: str) -> str:
    normalized = verdict.strip().lower()
    return normalized if normalized in {"ready", "verify", "hold"} else "verify"


def _missing(request: PurchaseExecutionKitRequest) -> list[str]:
    return [item.strip() for item in request.missing_evidence if item.strip()][:8]


def _ready_evidence(request: PurchaseExecutionKitRequest) -> list[str]:
    return [item.strip() for item in request.evidence_ready if item.strip()][:8]


def _priority(request: PurchaseExecutionKitRequest) -> CheckStatus:
    verdict = _normalized_verdict(request.verdict)
    if verdict == "hold" or request.blocker_count > 0:
        return CheckStatus.blocker
    if verdict == "verify" or request.warning_count > 0 or _missing(request):
        return CheckStatus.warning
    if (
        request.final_price_krw is not None
        and request.budget_krw is not None
        and request.final_price_krw > request.budget_krw
    ):
        return CheckStatus.warning
    return CheckStatus.ok


def _score(request: PurchaseExecutionKitRequest, priority: CheckStatus) -> int:
    score = 100
    score -= request.blocker_count * 22
    score -= request.warning_count * 8
    score -= len(_missing(request)) * 7
    if _normalized_verdict(request.verdict) == "hold":
        score -= 25
    elif _normalized_verdict(request.verdict) == "verify":
        score -= 8
    if (
        request.final_price_krw is not None
        and request.budget_krw is not None
        and request.final_price_krw > request.budget_krw
    ):
        over = request.final_price_krw - request.budget_krw
        score -= 24 if over > max(100_000, request.budget_krw * 0.05) else 12
    if priority == CheckStatus.blocker:
        score -= 8
    return max(0, min(100, score))


def _money(value: int | None) -> str:
    return f"{value:,}원" if value is not None else "미입력"


def _audience_label(audience: str) -> str:
    labels = {
        "family": "가족/지인",
        "team": "팀 승인자",
        "community": "커뮤니티 검토자",
        "self": "본인",
    }
    return labels.get(audience.strip().lower(), "검토자")


def _headline(request: PurchaseExecutionKitRequest, priority: CheckStatus) -> str:
    if priority == CheckStatus.blocker:
        return f"{_title(request)}는 실행 전에 결제 중단 조건을 먼저 닫아야 합니다."
    if priority == CheckStatus.warning:
        return f"{_title(request)}는 증거 게이트를 통과한 뒤 제한 실행하세요."
    return f"{_title(request)}는 결제 실행 순서까지 준비됐습니다."


def _summary(
    request: PurchaseExecutionKitRequest,
    priority: CheckStatus,
    score: int,
    delta: int | None,
) -> str:
    delta_text = "예산 차이 미입력" if delta is None else f"예산 대비 {delta:+,}원"
    if priority == CheckStatus.blocker:
        return (
            f"실행 점수 {score}점, 최종가 {_money(request.final_price_krw)}, {delta_text}. "
            "blocker 또는 보류 판정이 있어 결제 버튼보다 판매자 답변과 대체 후보 비교가 먼저입니다."
        )
    if priority == CheckStatus.warning:
        return (
            f"실행 점수 {score}점, 최종가 {_money(request.final_price_krw)}, {delta_text}. "
            "누락 증거와 warning을 캡처한 뒤 같은 조건일 때만 결제합니다."
        )
    return (
        f"실행 점수 {score}점, 최종가 {_money(request.final_price_krw)}, {delta_text}. "
        "가격, 옵션, 보증 증거를 남기고 구매 후 케어로 이어가면 됩니다."
    )


def _primary_action(request: PurchaseExecutionKitRequest, priority: CheckStatus) -> str:
    if priority == CheckStatus.blocker:
        return "결제를 멈추고 blocker 해결 또는 대체 후보 비교를 먼저 실행하세요."
    if priority == CheckStatus.warning:
        return "누락 증거를 캡처하고 판매자 답변을 받은 뒤 같은 총액이면 결제하세요."
    return "최종 결제 화면을 캡처한 뒤 같은 옵션명과 같은 총액이면 결제하세요."


def _decision_checkpoint(request: PurchaseExecutionKitRequest, priority: CheckStatus) -> str:
    deadline = request.decision_deadline.strip() or "결제 전"
    if priority == CheckStatus.blocker:
        return f"{deadline}까지 blocker가 0개가 아니면 결제하지 않습니다."
    if priority == CheckStatus.warning:
        return f"{deadline}까지 누락 증거와 warning 답변이 채워지면 제한 승인합니다."
    return f"{deadline}까지 판매자, 옵션명, 최종가가 그대로면 실행합니다."


def _status_for_missing(item: str, missing: list[str], priority: CheckStatus) -> CheckStatus:
    if any(item in evidence or evidence in item for evidence in missing):
        return CheckStatus.blocker if priority == CheckStatus.blocker else CheckStatus.warning
    return CheckStatus.ok


def _checkout_steps(
    request: PurchaseExecutionKitRequest,
    priority: CheckStatus,
) -> list[PurchaseExecutionStep]:
    missing = _missing(request)
    stop_status = CheckStatus.blocker if priority == CheckStatus.blocker else CheckStatus.ok
    return [
        PurchaseExecutionStep(
            step_id="price_recheck",
            label="최종가 재확인",
            status=_status_for_missing("최종 결제 금액", missing, priority),
            owner="buyer",
            timing="결제 버튼 1분 전",
            instruction="표시가가 아니라 배송비, 조립비, OS, 쿠폰, 카드 할인까지 반영된 최종가를 확인합니다.",
            evidence_required="최종 결제 화면 총액 캡처",
            fail_condition="최종가가 예산 또는 리포트 예상가보다 설명 없이 높아짐",
        ),
        PurchaseExecutionStep(
            step_id="option_capture",
            label="옵션/사양 캡처",
            status=_status_for_missing("옵션", missing, priority),
            owner="buyer",
            timing="결제 버튼 1분 전",
            instruction="상품명, 옵션명, CPU/GPU/RAM/SSD/OS, 수량이 리포트와 같은지 캡처합니다.",
            evidence_required="장바구니 옵션명과 사양 캡처",
            fail_condition="옵션명, 저장장치, RAM, OS, 그래픽카드가 리포트와 다름",
        ),
        PurchaseExecutionStep(
            step_id="seller_answer",
            label="판매자 답변 확인",
            status=_status_for_missing("판매자", missing, priority),
            owner="seller",
            timing="결제 전 답변 확보",
            instruction="AS, 반품, 배송 예정일, 실제 출고 사양에 대한 답변을 받습니다.",
            evidence_required="판매자 문의 답변 캡처",
            fail_condition="AS/반품/출고 사양이 모호하거나 답변 없음",
        ),
        PurchaseExecutionStep(
            step_id="approval_share",
            label="검토자 공유",
            status=CheckStatus.warning if priority == CheckStatus.warning else priority,
            owner=_audience_label(request.share_audience),
            timing="결제 전 마지막 확인",
            instruction="가족, 팀, 커뮤니티에 승인 브리프와 남은 리스크를 공유합니다.",
            evidence_required="공유한 승인 문구 또는 답변",
            fail_condition="검토자가 blocker를 지적했는데 해결하지 않음",
        ),
        PurchaseExecutionStep(
            step_id="payment_execute",
            label="결제 실행/보류",
            status=stop_status,
            owner="buyer",
            timing=request.decision_deadline.strip() or "오늘 결제 전",
            instruction=_primary_action(request, priority),
            evidence_required=f"{request.payment_method.strip() or '결제 수단'} 결제 전 확인 화면",
            fail_condition="중단 조건 중 하나라도 발생",
        ),
        PurchaseExecutionStep(
            step_id="aftercare_record",
            label="구매 후 케어 기록",
            status=CheckStatus.ok,
            owner="buyer",
            timing="결제 직후",
            instruction="주문번호 일부 마스킹, 결제 금액, 반품 마감, 보증 시작일을 저장합니다.",
            evidence_required="주문 완료 화면과 영수증 캡처",
            fail_condition="구매 결과를 남기지 않아 가격/추천 품질 학습이 끊김",
        ),
    ]


def _evidence_gates(
    request: PurchaseExecutionKitRequest,
    priority: CheckStatus,
    delta: int | None,
) -> list[PurchaseExecutionGate]:
    missing = _missing(request)
    ready = _ready_evidence(request)

    def gate_status(label: str) -> CheckStatus:
        if any(label in item or item in label for item in missing):
            return CheckStatus.blocker if priority == CheckStatus.blocker else CheckStatus.warning
        if any(label in item or item in label for item in ready):
            return CheckStatus.ok
        return CheckStatus.warning if priority != CheckStatus.ok else CheckStatus.ok

    price_status = CheckStatus.warning if delta is not None and delta > 0 else gate_status("최종 결제 금액")
    return [
        PurchaseExecutionGate(
            gate_id="final_price",
            label="최종 결제 금액",
            status=price_status,
            pass_rule="배송비, 조립비, OS, 쿠폰, 카드 할인을 반영한 최종가가 예산 규칙 안에 있음",
            block_rule="총액이 예산을 넘거나 리포트 예상가와 차이가 큰데 설명이 없음",
        ),
        PurchaseExecutionGate(
            gate_id="option_spec",
            label="옵션/사양 일치",
            status=gate_status("옵션"),
            pass_rule="CPU/GPU/RAM/SSD/OS/패널/수량이 리포트와 장바구니에서 동일함",
            block_rule="옵션명이 애매하거나 핵심 사양이 낮아짐",
        ),
        PurchaseExecutionGate(
            gate_id="warranty_return",
            label="보증/반품",
            status=gate_status("AS"),
            pass_rule="반품 기간, 개봉 후 반품, 초기 불량, 보증 주체를 확인함",
            block_rule="반품 불가, 해외 AS, 보증 승계 불명확, 높은 반품 비용",
        ),
        PurchaseExecutionGate(
            gate_id="seller_answer",
            label="판매자 답변",
            status=gate_status("판매자"),
            pass_rule="출고 사양, 배송일, AS, 할인 조건에 대한 답변을 캡처함",
            block_rule="답변 없음 또는 실제 출고 사양이 불명확함",
        ),
        PurchaseExecutionGate(
            gate_id="reviewer_approval",
            label="검토자 승인",
            status=CheckStatus.ok if priority == CheckStatus.ok else CheckStatus.warning,
            pass_rule="공유한 승인 브리프에 반대 사유가 새로 나오지 않음",
            block_rule="가족/팀/커뮤니티 검토자가 예산, AS, 사양 문제를 지적함",
        ),
    ]


def _seller_questions(
    request: PurchaseExecutionKitRequest,
    priority: CheckStatus,
) -> list[str]:
    provided = [item.strip() for item in request.seller_questions if item.strip()]
    defaults = [
        "최종 결제 금액에 배송비, 조립비, OS 비용, 쿠폰, 카드 할인이 모두 반영된 것이 맞나요?",
        "실제 출고 사양이 장바구니 옵션명과 동일한가요?",
        "초기 불량, 개봉 후 반품, 제조사/판매자 AS 조건은 어떻게 되나요?",
        "할인 또는 재고가 결제 직전 바뀌면 같은 가격으로 유지되나요?",
    ]
    if priority == CheckStatus.blocker:
        defaults.insert(0, "현재 blocker를 해결할 수 있는 공식 답변 또는 대체 옵션을 제시할 수 있나요?")
    return list(dict.fromkeys(provided + defaults))[:8]


def _stop_conditions(
    request: PurchaseExecutionKitRequest,
    priority: CheckStatus,
    delta: int | None,
) -> list[str]:
    conditions = [
        "장바구니 옵션명이나 핵심 사양이 리포트와 다르면 중단",
        "최종 결제 금액이 캡처한 금액보다 올라가면 중단",
        "AS/반품 조건이 확인되지 않으면 중단",
        "판매자 답변이 실제 출고 사양을 보장하지 않으면 중단",
    ]
    if delta is not None and delta > 0:
        conditions.insert(0, f"예산을 {delta:,}원 초과하면 중단")
    if priority == CheckStatus.blocker:
        conditions.insert(0, "blocker가 1개라도 남아 있으면 중단")
    return list(dict.fromkeys(conditions))[:8]


def _share_messages(
    request: PurchaseExecutionKitRequest,
    priority: CheckStatus,
    questions: list[str],
) -> list[PurchaseExecutionShareMessage]:
    title = _title(request)
    action = _primary_action(request, priority)
    price = _money(request.final_price_krw)
    return [
        PurchaseExecutionShareMessage(
            channel="kakao",
            label="가족/지인 공유",
            copy_text=(
                f"{title} 구매 직전 확인 부탁해요.\n"
                f"최종가: {price}\n"
                f"상태: {priority.value}\n"
                f"실행 원칙: {action}\n"
                f"확인 질문: {questions[0]}"
            ),
            cta_label="구매 전 검토 요청",
        ),
        PurchaseExecutionShareMessage(
            channel="team",
            label="팀 승인 공유",
            copy_text=(
                f"[구매 실행 검토] {title}\n"
                f"판매자: {_seller(request)}\n"
                f"최종가: {price}\n"
                f"마감: {request.decision_deadline}\n"
                f"승인 조건: 모든 증거 게이트 통과 후 결제"
            ),
            cta_label="팀 승인 요청",
        ),
        PurchaseExecutionShareMessage(
            channel="community",
            label="커뮤니티 검토",
            copy_text=(
                f"{title} 결제 직전입니다. 최종가 {price}, 상태 {priority.value}. "
                "옵션/AS/반품/가격 조건에서 놓친 blocker가 있는지 봐주세요."
            ),
            cta_label="커뮤니티 검토 요청",
        ),
    ]


def _analysis_prefill(
    request: PurchaseExecutionKitRequest,
    priority: CheckStatus,
    score: int,
    delta: int | None,
) -> str:
    delta_text = "예산 차이 미입력" if delta is None else f"예산 차이 {delta:+,}원"
    return (
        f"'{_title(request)}' 구매 실행 직전 상태를 분석해줘. "
        f"판매자 {_seller(request)}, 최종가 {_money(request.final_price_krw)}, "
        f"예산 {_money(request.budget_krw)}, {delta_text}, "
        f"blocker {request.blocker_count}개, warning {request.warning_count}개, "
        f"누락 증거 {', '.join(_missing(request)) or '없음'}, "
        f"실행 상태 {priority.value}, 실행 점수 {score}점."
    )


def _share_copy(
    request: PurchaseExecutionKitRequest,
    priority: CheckStatus,
    score: int,
    delta: int | None,
) -> str:
    delta_text = "미입력" if delta is None else f"{delta:+,}원"
    return (
        "SpecPilot AI 구매 실행 패키지\n"
        f"제품: {_title(request)}\n"
        f"판매자: {_seller(request)}\n"
        f"상태: {priority.value}\n"
        f"실행 점수: {score}점\n"
        f"최종가: {_money(request.final_price_krw)}\n"
        f"예산 차이: {delta_text}\n"
        f"1차 행동: {_primary_action(request, priority)}"
    )


def _next_actions(
    request: PurchaseExecutionKitRequest,
    priority: CheckStatus,
) -> list[str]:
    if priority == CheckStatus.blocker:
        return [
            "결제를 멈추고 blocker 해결 답변을 판매자 증거 요청 키트에 붙이세요.",
            "대체 후보 rescue 또는 후보 비교 스냅샷에서 같은 예산의 후보를 확인하세요.",
            "승인 브리프에는 반대 사유와 중단 조건을 먼저 공유하세요.",
        ]
    if priority == CheckStatus.warning:
        return [
            "누락 증거를 캡처한 뒤 구매 승인 브리프를 다시 생성하세요.",
            "최종가와 옵션명이 그대로인지 결제 직전 1회 더 대조하세요.",
            "구매 후 케어 키트에 주문 완료 화면과 반품 마감을 바로 저장하세요.",
        ]
    return [
        "최종 결제 화면과 옵션명을 캡처하고 결제하세요.",
        "구매 후 케어 키트로 반품/보증/초기 불량 마감을 등록하세요.",
        "실제 결제 금액을 구매 결과로 남겨 추천 품질을 닫힌 루프로 검증하세요.",
    ]
