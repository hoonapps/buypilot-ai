from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    CheckStatus,
    PublicSellerEvidenceKit,
    PurchaseApprovalBriefRequest,
    SellerAnswerRubric,
    SellerEvidenceQuestion,
    SellerEvidenceRequest,
)


def build_public_seller_evidence_kit(
    request: SellerEvidenceRequest,
    generated_at: datetime | None = None,
) -> PublicSellerEvidenceKit:
    generated_at = generated_at or datetime.now(UTC)
    title = request.product_title.strip() or _category_label(request.category)
    seller = request.seller_name.strip() or "판매자"
    risks = _risks(request)
    missing = _missing_evidence(request)
    questions = _questions(request, title, risks, missing)
    priority = _priority(request, risks, missing)
    answer_status = _answer_status(request.answer_text, questions)
    approval_prefill = _approval_prefill(request, title, priority, answer_status, missing)
    return PublicSellerEvidenceKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=title,
        seller_name=seller,
        priority=priority,
        answer_status=answer_status,
        headline=_headline(title, priority, answer_status),
        summary=_summary(request, priority, answer_status, len(questions)),
        seller_message=_seller_message(seller, title, questions),
        questions=questions,
        answer_rubric=_answer_rubric(risks, missing),
        evidence_checklist=_evidence_checklist(missing),
        approval_prefill=approval_prefill,
        analysis_prefill=_analysis_prefill(request, title, priority, answer_status, questions),
        share_copy=_share_copy(request, title, priority, answer_status),
        next_actions=_next_actions(priority, answer_status),
    )


def _category_label(category: Category) -> str:
    return "노트북" if category == Category.laptop else "컴퓨터 세팅"


def _risks(request: SellerEvidenceRequest) -> list[str]:
    risks = [risk.strip() for risk in request.risk_terms if risk.strip()]
    text = f"{request.product_title} {request.answer_text}".lower()
    for keyword in ("리퍼", "전시", "중고", "해외", "병행", "freedos", "free dos"):
        if keyword in text and keyword not in risks:
            risks.append(keyword)
    return risks[:8]


def _missing_evidence(request: SellerEvidenceRequest) -> list[str]:
    defaults = ["실제 출고 사양", "배송 예정일", "반품 조건", "AS 조건"]
    given = [item.strip() for item in request.missing_evidence if item.strip()]
    must = [item.strip() for item in request.must_confirm if item.strip()]
    return list(dict.fromkeys(given + must + defaults))[:10]


def _priority(
    request: SellerEvidenceRequest,
    risks: list[str],
    missing: list[str],
) -> CheckStatus:
    verdict = request.verdict.strip().lower()
    if verdict == "hold" or any(_is_hard_risk(risk) for risk in risks):
        return CheckStatus.blocker
    if verdict == "verify" or missing or risks:
        return CheckStatus.warning
    return CheckStatus.ok


def _is_hard_risk(risk: str) -> bool:
    lowered = risk.lower()
    return any(term in lowered for term in ("해외", "병행", "리퍼", "전시", "중고"))


def _answer_status(answer_text: str, questions: list[SellerEvidenceQuestion]) -> CheckStatus:
    answer = answer_text.strip().lower()
    if not answer:
        return CheckStatus.warning
    fail_terms = ("불가", "모름", "확인 불가", "반품 불가", "as 불가", "보증 없음", "상이")
    if any(term in answer for term in fail_terms):
        return CheckStatus.blocker
    pass_terms = ("동일", "가능", "확인", "보증", "as", "반품", "배송")
    if sum(1 for term in pass_terms if term in answer) >= min(3, len(questions)):
        return CheckStatus.ok
    return CheckStatus.warning


def _questions(
    request: SellerEvidenceRequest,
    title: str,
    risks: list[str],
    missing: list[str],
) -> list[SellerEvidenceQuestion]:
    questions = [
        SellerEvidenceQuestion(
            question_id="ship_spec",
            label="실제 출고 사양",
            status=CheckStatus.warning if "실제 출고 사양" in missing else CheckStatus.ok,
            question=f"{title}의 실제 출고 CPU/GPU/RAM/SSD/OS가 장바구니 옵션명과 동일한가요?",
            required_answer="모델명, RAM/SSD 용량, OS 포함 여부를 텍스트로 명시한 답변",
            why_it_matters="상품명과 실제 옵션이 다르면 리포트가 맞아도 결제 실패가 납니다.",
        ),
        SellerEvidenceQuestion(
            question_id="shipping",
            label="배송 예정일",
            status=CheckStatus.warning if "배송 예정일" in missing else CheckStatus.ok,
            question="결제 후 실제 출고 예정일과 지연 시 취소 가능 여부를 알려주세요.",
            required_answer="출고 예정일 또는 지연 시 취소/환불 가능 조건",
            why_it_matters="재고와 배송 지연은 가격 타이밍과 구매 실패 비용에 직접 영향을 줍니다.",
        ),
        SellerEvidenceQuestion(
            question_id="return_policy",
            label="반품 조건",
            status=CheckStatus.warning if "반품 조건" in missing else CheckStatus.ok,
            question="개봉 전/개봉 후 반품 가능 기간과 제외 조건을 알려주세요.",
            required_answer="반품 가능 기간, 단순 변심/초기 불량/개봉 후 처리 기준",
            why_it_matters="리퍼, 전시, 해외 조건은 반품 예외가 많아 결제 전 확인이 필요합니다.",
        ),
        SellerEvidenceQuestion(
            question_id="warranty",
            label="AS 조건",
            status=CheckStatus.warning if "AS 조건" in missing else CheckStatus.ok,
            question="제조사 보증과 판매자 AS 기간, 접수 경로를 알려주세요.",
            required_answer="제조사/판매자 보증 기간과 AS 접수 방법",
            why_it_matters="AS가 불명확하면 가격이 싸도 구매 안정성이 크게 낮아집니다.",
        ),
    ]
    if request.category == Category.desktop_pc:
        questions.append(
            SellerEvidenceQuestion(
                question_id="compatibility",
                label="조립/호환",
                status=CheckStatus.warning,
                question="파워 용량, 케이스 장착, BIOS 업데이트가 현재 부품 조합에 맞나요?",
                required_answer="파워 W, 케이스 호환, BIOS 업데이트 필요 여부",
                why_it_matters="조립 PC는 사양보다 호환성 누락이 더 큰 결제 후 문제를 만듭니다.",
            )
        )
    if risks:
        questions.append(
            SellerEvidenceQuestion(
                question_id="risk_terms",
                label="위험 조건",
                status=CheckStatus.blocker if any(_is_hard_risk(risk) for risk in risks) else CheckStatus.warning,
                question=f"{', '.join(risks[:4])} 조건이 있다면 보증/반품/추가 비용 예외가 있나요?",
                required_answer="위험 조건별 보증 예외, 반품 예외, 추가 비용 여부",
                why_it_matters="조건부 상품은 표시가보다 사후 비용과 반품 리스크가 큽니다.",
            )
        )
    return questions[:7]


def _seller_message(
    seller: str,
    title: str,
    questions: list[SellerEvidenceQuestion],
) -> str:
    question_lines = "\n".join(
        f"{index}. {question.question}" for index, question in enumerate(questions, start=1)
    )
    return (
        f"안녕하세요, {seller}님. {title} 결제 전 실제 출고 조건 확인 부탁드립니다.\n"
        f"{question_lines}\n"
        "답변은 결제 전 캡처해서 보관할 예정이라 항목별로 명확히 남겨주세요."
    )


def _answer_rubric(
    risks: list[str],
    missing: list[str],
) -> list[SellerAnswerRubric]:
    rubric = [
        SellerAnswerRubric(
            rubric_id="exact_spec",
            label="사양 일치",
            status=CheckStatus.ok,
            pass_signal="CPU/GPU/RAM/SSD/OS가 옵션명과 동일하다고 명시",
            fail_signal="동급, 랜덤, 재고에 따라 변경, 정확히 모름",
        ),
        SellerAnswerRubric(
            rubric_id="return_as",
            label="반품/AS",
            status=CheckStatus.warning if missing else CheckStatus.ok,
            pass_signal="반품 가능 기간과 제조사/판매자 AS 경로를 명시",
            fail_signal="반품 불가, AS 불가, 보증 없음, 판매자 확인 불가",
        ),
        SellerAnswerRubric(
            rubric_id="shipping",
            label="배송/재고",
            status=CheckStatus.warning,
            pass_signal="출고 예정일과 지연 시 취소 가능 여부를 명시",
            fail_signal="재고 미확정, 출고일 미정, 취소/환불 조건 불명확",
        ),
    ]
    if risks:
        rubric.append(
            SellerAnswerRubric(
                rubric_id="risk_exception",
                label="위험 조건 예외",
                status=CheckStatus.blocker if any(_is_hard_risk(risk) for risk in risks) else CheckStatus.warning,
                pass_signal="리퍼/전시/해외/FreeDOS 조건별 예외와 추가 비용을 명시",
                fail_signal="예외 조건을 답하지 않거나 일반 상품과 같다고만 답변",
            )
        )
    return rubric


def _evidence_checklist(missing: list[str]) -> list[str]:
    base = [
        "판매자 답변 전체 캡처",
        "상품명과 장바구니 옵션명 캡처",
        "최종 결제 금액, 배송비, 쿠폰/카드 할인 캡처",
        "반품/AS 정책 페이지 캡처",
    ]
    return list(dict.fromkeys(base + missing))[:10]


def _approval_prefill(
    request: SellerEvidenceRequest,
    title: str,
    priority: CheckStatus,
    answer_status: CheckStatus,
    missing: list[str],
) -> PurchaseApprovalBriefRequest:
    blocker_count = int(priority == CheckStatus.blocker) + int(answer_status == CheckStatus.blocker)
    warning_count = int(priority == CheckStatus.warning) + int(answer_status == CheckStatus.warning)
    verdict = "hold" if blocker_count else "verify" if warning_count else "ready"
    return PurchaseApprovalBriefRequest(
        category=request.category,
        product_title=title,
        verdict=verdict,
        budget_krw=request.budget_krw,
        cart_total_krw=request.cart_total_krw,
        blocker_count=blocker_count,
        warning_count=warning_count,
        key_reasons=[
            f"판매자 증거 우선순위 {priority.value}",
            f"답변 판정 {answer_status.value}",
        ],
        missing_evidence=missing[:6],
        audience="family",
        decision_deadline="결제 전",
        source="seller_evidence",
    )


def _headline(title: str, priority: CheckStatus, answer_status: CheckStatus) -> str:
    if priority == CheckStatus.blocker or answer_status == CheckStatus.blocker:
        return f"{title}는 판매자 답변이 닫히기 전 결제 보류입니다."
    if answer_status == CheckStatus.ok:
        return f"{title} 판매자 답변을 승인 증거로 쓸 수 있습니다."
    return f"{title}는 판매자 답변을 받은 뒤 조건부 승인하세요."


def _summary(
    request: SellerEvidenceRequest,
    priority: CheckStatus,
    answer_status: CheckStatus,
    question_count: int,
) -> str:
    total = f"{request.cart_total_krw:,}원" if request.cart_total_krw is not None else "총액 미입력"
    return (
        f"총액 {total}, 예산 {request.budget_krw:,}원 기준 질문 {question_count}개를 만들었습니다. "
        f"증거 우선순위는 {priority.value}, 현재 답변 판정은 {answer_status.value}입니다."
    )


def _analysis_prefill(
    request: SellerEvidenceRequest,
    title: str,
    priority: CheckStatus,
    answer_status: CheckStatus,
    questions: list[SellerEvidenceQuestion],
) -> str:
    return (
        f"{_category_label(request.category)} '{title}' 판매자 답변을 분석해줘. "
        f"예산 {request.budget_krw:,}원, 총액 {request.cart_total_krw or '미입력'}, "
        f"증거 우선순위 {priority.value}, 답변 판정 {answer_status.value}. "
        f"확인 질문: {' / '.join(question.label for question in questions)}. "
        f"판매자 답변: {request.answer_text.strip() or '아직 없음'}"
    )


def _share_copy(
    request: SellerEvidenceRequest,
    title: str,
    priority: CheckStatus,
    answer_status: CheckStatus,
) -> str:
    return (
        "SpecPilot AI 판매자 증거 요청\n"
        f"후보: {title}\n"
        f"판매자: {request.seller_name or '판매자'}\n"
        f"증거 우선순위: {priority.value}\n"
        f"답변 판정: {answer_status.value}"
    )


def _next_actions(priority: CheckStatus, answer_status: CheckStatus) -> list[str]:
    if priority == CheckStatus.blocker or answer_status == CheckStatus.blocker:
        return [
            "판매자 답변이 명확해질 때까지 결제를 보류하세요.",
            "반품/AS 불가 답변이 있으면 대체 후보 rescue로 전환하세요.",
            "답변 캡처를 구매 승인 브리프에 붙여 반대 사유를 확인하세요.",
        ]
    if answer_status == CheckStatus.ok:
        return [
            "판매자 답변 캡처를 보관하고 옵션/사양 빠른 검수에 반영하세요.",
            "구매 승인 브리프로 공유해 최종 반대 사유만 확인하세요.",
            "결제 직전 최종가와 옵션명이 그대로인지 다시 캡처하세요.",
        ]
    return [
        "판매자에게 복사 문구를 보내 답변을 먼저 받으세요.",
        "답변이 오면 같은 화면에 붙여 answer_status를 확인하세요.",
        "배송/반품/AS 중 하나라도 불명확하면 조건부 승인으로 처리하세요.",
    ]
