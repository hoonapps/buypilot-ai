import re
from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    CheckStatus,
    PublicPurchaseQuestionTriageKit,
    PurchaseQuestionTriageRequest,
    QuestionTriageSignal,
    SpecRiskScannerRequest,
)

QUESTION_TYPES = {
    "checkout": {
        "keywords": ["결제", "장바구니", "최종가", "오늘", "지금 사", "주문", "구매해도"],
        "label": "결제 전 검수",
        "kits": ["spec-risk-scanner", "purchase-execution-kit", "checkout-lock-kit"],
    },
    "price": {
        "keywords": ["가격", "특가", "할인", "쿠폰", "카드", "최저가", "비싼", "싼가", "예산"],
        "label": "가격 신뢰",
        "kits": ["price-trust-kit", "deal-sanity-kit", "budget-stress-kit"],
    },
    "spec": {
        "keywords": ["사양", "스펙", "cpu", "gpu", "ram", "ssd", "프리도스", "freedos", "tgp", "온보드"],
        "label": "사양 이해",
        "kits": ["spec-term-decoder-kit", "listing-decoder-kit", "setup-compatibility-kit"],
    },
    "warranty": {
        "keywords": ["as", "보증", "반품", "교환", "리퍼", "전시", "중고", "해외", "병행"],
        "label": "보증/반품",
        "kits": ["warranty-return-kit", "seller-evidence-kit", "deal-sanity-kit"],
    },
    "aftercare": {
        "keywords": ["도착", "수령", "꺼짐", "불량", "온도", "소음", "스로틀", "느림", "고장"],
        "label": "수령 후 점검",
        "kits": ["first-boot-setup-kit", "benchmark-validation-kit", "defect-claim-kit"],
    },
}

BLOCKER_TERMS = ["반품불가", "반품 불가", "리퍼", "전시", "중고", "해외", "병행", "꺼짐", "불량"]
WARNING_TERMS = ["freedos", "프리도스", "tgp", "온보드", "카드 할인", "쿠폰", "재고", "배송"]


def build_public_purchase_question_triage_kit(
    request: PurchaseQuestionTriageRequest,
    generated_at: datetime | None = None,
) -> PublicPurchaseQuestionTriageKit:
    generated_at = generated_at or datetime.now(UTC)
    title = request.product_title.strip() or _category_label(request.category)
    question = request.buyer_question.strip()
    combined_text = " ".join([question, title, request.listing_text]).strip()
    question_type = _question_type(combined_text, request.purchase_stage)
    signals = _triage_signals(request, combined_text, question_type)
    status = _status(signals)
    urgency_score = _urgency_score(request, signals, combined_text)
    missing_inputs = _missing_inputs(request, combined_text, question_type)
    routed_kits = _routed_kits(question_type, missing_inputs, status)
    scanner_prefill = _scanner_prefill(request, title, combined_text)
    recommended_next_step = _recommended_next_step(
        status=status,
        question_type=question_type,
        routed_kits=routed_kits,
        missing_inputs=missing_inputs,
    )
    return PublicPurchaseQuestionTriageKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=title,
        purchase_stage=request.purchase_stage,
        question_type=question_type,
        triage_status=status,
        urgency_score=urgency_score,
        headline=_headline(title, question_type, status),
        summary=(
            f"질문을 {_question_label(question_type)} 흐름으로 분류했습니다. "
            f"위험 신호 {sum(1 for signal in signals if signal.status == CheckStatus.blocker)}개, "
            f"확인 신호 {sum(1 for signal in signals if signal.status == CheckStatus.warning)}개를 기준으로 "
            "다음 공개 검수 키트와 복사용 질문을 만들었습니다."
        ),
        routed_kits=routed_kits,
        triage_signals=signals,
        missing_inputs=missing_inputs,
        recommended_next_step=recommended_next_step,
        buyer_reply=_buyer_reply(question, status, recommended_next_step),
        seller_questions=_seller_questions(question_type, missing_inputs, status),
        community_post=_community_post(request, title, question_type, missing_inputs),
        scanner_prefill=scanner_prefill,
        analysis_prefill=_analysis_prefill(request, title, question_type, signals, scanner_prefill),
        share_copy=_share_copy(title, question_type, status),
        primary_cta_label=_primary_cta_label(question_type, status),
        primary_cta_path=_primary_cta_path(question_type),
        next_actions=_next_actions(status, routed_kits, missing_inputs),
    )


def _question_type(text: str, purchase_stage: str) -> str:
    lowered = text.lower()
    if purchase_stage in {"checkout", "cart"}:
        return "checkout"
    if purchase_stage in {"after_purchase", "received"}:
        return "aftercare"
    scores = {
        key: sum(1 for keyword in config["keywords"] if keyword in lowered)
        for key, config in QUESTION_TYPES.items()
    }
    best_type, best_score = max(scores.items(), key=lambda item: item[1])
    return best_type if best_score else "checkout"


def _triage_signals(
    request: PurchaseQuestionTriageRequest,
    text: str,
    question_type: str,
) -> list[QuestionTriageSignal]:
    lowered = text.lower()
    signals = [
        QuestionTriageSignal(
            signal_id="question_type",
            label="질문 유형",
            status=CheckStatus.ok,
            evidence=_question_label(question_type),
            next_step=f"{_question_label(question_type)}에 맞는 공개 키트로 라우팅합니다.",
        )
    ]
    blockers = [term for term in BLOCKER_TERMS if term in lowered or term in text]
    if blockers:
        signals.append(
            QuestionTriageSignal(
                signal_id="risk_terms",
                label="위험 문구",
                status=CheckStatus.blocker,
                evidence=", ".join(blockers[:5]),
                next_step="판매자 답변과 반품/AS 증거 전에는 결제를 보류하세요.",
            )
        )
    warnings = [term for term in WARNING_TERMS if term in lowered or term in text]
    if warnings:
        signals.append(
            QuestionTriageSignal(
                signal_id="ambiguous_terms",
                label="확인 용어",
                status=CheckStatus.warning,
                evidence=", ".join(warnings[:5]),
                next_step="용어 해석과 상품명 해석으로 장바구니 검수 전 사양을 확정하세요.",
            )
        )
    if request.cart_total_krw is None:
        signals.append(
            QuestionTriageSignal(
                signal_id="missing_total",
                label="최종가 누락",
                status=CheckStatus.warning,
                evidence="최종 결제 금액 없음",
                next_step="배송비, 쿠폰, 카드 할인이 반영된 결제 화면 총액을 입력하세요.",
            )
        )
    elif request.cart_total_krw > request.budget_krw:
        signals.append(
            QuestionTriageSignal(
                signal_id="budget_over",
                label="예산 초과",
                status=CheckStatus.blocker,
                evidence=f"최종가 {request.cart_total_krw:,}원 / 예산 {request.budget_krw:,}원",
                next_step="예산 증액 승인 또는 대체 후보 비교 전까지 결제를 멈추세요.",
            )
        )
    if len(request.listing_text.strip()) < 30:
        signals.append(
            QuestionTriageSignal(
                signal_id="thin_context",
                label="상품 문구 부족",
                status=CheckStatus.warning,
                evidence="상품명/옵션명/상세 조건이 짧음",
                next_step="상품명, 옵션명, 보증/반품 문구를 그대로 붙여 넣으세요.",
            )
        )
    return signals


def _status(signals: list[QuestionTriageSignal]) -> CheckStatus:
    if any(signal.status == CheckStatus.blocker for signal in signals):
        return CheckStatus.blocker
    if any(signal.status == CheckStatus.warning for signal in signals):
        return CheckStatus.warning
    return CheckStatus.ok


def _urgency_score(
    request: PurchaseQuestionTriageRequest,
    signals: list[QuestionTriageSignal],
    text: str,
) -> float:
    blocker_count = sum(1 for signal in signals if signal.status == CheckStatus.blocker)
    warning_count = sum(1 for signal in signals if signal.status == CheckStatus.warning)
    base = 35 + blocker_count * 28 + warning_count * 11
    if any(token in text for token in ["오늘", "마감", "품절", "재고", "특가"]):
        base += 12
    if request.purchase_stage in {"checkout", "cart"}:
        base += 10
    return round(min(98, max(20, base)), 1)


def _missing_inputs(
    request: PurchaseQuestionTriageRequest,
    text: str,
    question_type: str,
) -> list[str]:
    missing: list[str] = []
    if request.cart_total_krw is None:
        missing.append("배송비/쿠폰/카드 할인이 반영된 최종 결제 금액")
    if len(request.listing_text.strip()) < 30:
        missing.append("판매 페이지 상품명과 장바구니 옵션명 원문")
    if question_type in {"warranty", "checkout"} and not any(
        token in text for token in ["반품", "교환", "as", "AS", "보증"]
    ):
        missing.append("반품, 교환, 국내 AS, 보증 기간 문구")
    if question_type in {"price", "checkout"} and not any(
        token in text for token in ["캡처", "공식", "가격비교", "결제"]
    ):
        missing.append("가격 출처와 캡처 시각")
    return missing[:5]


def _routed_kits(
    question_type: str,
    missing_inputs: list[str],
    status: CheckStatus,
) -> list[str]:
    kits = list(QUESTION_TYPES[question_type]["kits"])
    if missing_inputs:
        kits.append("product-page-evidence-kit")
    if status != CheckStatus.ok and "seller-evidence-kit" not in kits:
        kits.append("seller-evidence-kit")
    return list(dict.fromkeys(kits))[:5]


def _scanner_prefill(
    request: PurchaseQuestionTriageRequest,
    title: str,
    text: str,
) -> SpecRiskScannerRequest:
    return SpecRiskScannerRequest(
        category=request.category,
        product_title=title,
        option_text=request.listing_text or title,
        cart_total_krw=request.cart_total_krw,
        budget_krw=request.budget_krw,
        expected_cpu=_find_spec(text, ["ryzen", "intel", "core", "ultra"]),
        expected_gpu=_find_spec(text, ["rtx", "radeon", "그래픽"]),
        expected_ram_gb=_capacity(text, ["ram", "램", "메모리"]),
        expected_storage_gb=_storage_capacity(text),
        expected_os="Windows 11" if any(token in text.lower() for token in ["windows 11", "win 11", "윈도우 11"]) else "",
        evidence_text="구매 질문 라우팅 키트 기반 prefill",
        source="purchase_question_triage",
    )


def _find_spec(text: str, anchors: list[str]) -> str:
    words = text.replace("/", " ").replace("|", " ").split()
    lowered = [word.lower() for word in words]
    for index, word in enumerate(lowered):
        if any(anchor in word for anchor in anchors):
            return " ".join(words[index : index + 3])[:48]
    return ""


def _capacity(text: str, anchors: list[str]) -> int | None:
    lowered = text.lower()
    for anchor in anchors:
        patterns = [
            rf"{anchor}\s*([0-9]{{1,3}})\s*gb",
            rf"([0-9]{{1,3}})\s*gb\s*{anchor}",
        ]
        for pattern in patterns:
            match = re.search(pattern, lowered)
            if match:
                value = int(match.group(1))
                return value if value <= 256 else None
    for anchor in anchors:
        index = lowered.find(anchor)
        if index >= 0:
            window = lowered[max(0, index - 12) : index + 20]
            digits = "".join(char for char in window if char.isdigit())
            if digits:
                value = int(digits[:3])
                return value if value <= 256 else None
    return None


def _storage_capacity(text: str) -> int | None:
    lowered = text.lower()
    if "1tb" in lowered or "1 tb" in lowered:
        return 1000
    if "2tb" in lowered or "2 tb" in lowered:
        return 2000
    return _capacity(text, ["ssd", "nvme", "저장"])


def _recommended_next_step(
    *,
    status: CheckStatus,
    question_type: str,
    routed_kits: list[str],
    missing_inputs: list[str],
) -> str:
    first_kit = routed_kits[0] if routed_kits else "analysis"
    if status == CheckStatus.blocker:
        return f"바로 결제하지 말고 {first_kit}로 blocker를 먼저 닫으세요."
    if missing_inputs:
        return f"누락 입력 {missing_inputs[0]}을 확보한 뒤 {first_kit}로 검수하세요."
    return f"{_question_label(question_type)} 질문은 {first_kit}로 바로 검수해도 됩니다."


def _buyer_reply(question: str, status: CheckStatus, next_step: str) -> str:
    verdict = "보류" if status == CheckStatus.blocker else "확인 필요" if status == CheckStatus.warning else "진행 가능"
    return f"질문: {question}\n판정: {verdict}\n다음 행동: {next_step}"


def _seller_questions(
    question_type: str,
    missing_inputs: list[str],
    status: CheckStatus,
) -> list[str]:
    questions = [
        "장바구니 옵션명 기준 실제 출고 CPU/GPU/RAM/SSD/OS가 상품명과 같은가요?",
        "배송비, 쿠폰, 카드 할인이 반영된 최종 결제 금액을 문장으로 확인해 주세요.",
    ]
    if question_type in {"warranty", "checkout"} or status != CheckStatus.ok:
        questions.append("초기 불량, 오배송, 단순 변심, 개봉 후 반품/교환 조건을 각각 알려 주세요.")
        questions.append("국내 AS 가능 여부, 보증 주체, 보증 기간, 접수 경로를 알려 주세요.")
    if missing_inputs:
        questions.append(f"누락된 정보인 '{missing_inputs[0]}'를 확인할 수 있는 상세 문구를 보내 주세요.")
    return questions[:6]


def _community_post(
    request: PurchaseQuestionTriageRequest,
    title: str,
    question_type: str,
    missing_inputs: list[str],
) -> str:
    missing = "\n".join(f"- {item}" for item in missing_inputs) or "- 현재 입력 기준 누락 없음"
    total = f"{request.cart_total_krw:,}원" if request.cart_total_krw is not None else "최종가 미입력"
    return (
        f"[{_category_label(request.category)} 구매 질문] {title}\n\n"
        f"질문: {request.buyer_question}\n"
        f"유형: {_question_label(question_type)}\n"
        f"예산/최종가: {request.budget_krw:,}원 / {total}\n\n"
        f"추가로 확인할 정보:\n{missing}\n\n"
        "가격, 사양, 반품/AS 기준에서 놓친 부분이 있는지 봐주세요."
    )


def _analysis_prefill(
    request: PurchaseQuestionTriageRequest,
    title: str,
    question_type: str,
    signals: list[QuestionTriageSignal],
    scanner_prefill: SpecRiskScannerRequest,
) -> str:
    signal_text = ", ".join(f"{signal.label}:{signal.status.value}" for signal in signals)
    return (
        f"{_category_label(request.category)} 구매 질문: 후보 '{title}'에 대해 사용자가 '{request.buyer_question}'라고 물었어. "
        f"질문 유형은 {_question_label(question_type)}, 예산은 {request.budget_krw:,}원, "
        f"최종가는 {request.cart_total_krw or '미입력'}원이야. "
        f"신호는 {signal_text}. "
        f"검수 prefill은 CPU {scanner_prefill.expected_cpu or '미확인'}, "
        f"GPU {scanner_prefill.expected_gpu or '미확인'}, RAM {scanner_prefill.expected_ram_gb or '미확인'}GB, "
        f"SSD {scanner_prefill.expected_storage_gb or '미확인'}GB야. "
        "결제해도 되는지 가격, 사양, 보증/반품, 대체 후보, 판매자 질문까지 정리해줘."
    )


def _share_copy(title: str, question_type: str, status: CheckStatus) -> str:
    verdict = "보류" if status == CheckStatus.blocker else "확인 필요" if status == CheckStatus.warning else "진행 가능"
    return f"SpecPilot AI 구매 질문 라우팅: {title} 질문은 {_question_label(question_type)} 유형이고 판정은 {verdict}입니다."


def _primary_cta_label(question_type: str, status: CheckStatus) -> str:
    if status == CheckStatus.blocker:
        return "보류 사유로 분석 시작"
    if question_type == "price":
        return "가격 질문으로 분석 시작"
    if question_type == "spec":
        return "사양 질문으로 분석 시작"
    return "질문 결과로 분석 시작"


def _primary_cta_path(question_type: str) -> str:
    return "#spec-scanner" if question_type in {"checkout", "spec"} else "#analysis"


def _next_actions(
    status: CheckStatus,
    routed_kits: list[str],
    missing_inputs: list[str],
) -> list[str]:
    actions = [f"{routed_kits[0]}로 첫 검수를 실행하세요."] if routed_kits else ["분석 리포트를 먼저 만드세요."]
    if missing_inputs:
        actions.append(f"{missing_inputs[0]}을 캡처해 질문에 붙이세요.")
    if status == CheckStatus.blocker:
        actions.append("판매자 답변과 대체 후보 비교 전까지 결제를 보류하세요.")
    actions.append("커뮤니티에 물을 때는 예산, 최종가, 상품명, 반품/AS 조건을 함께 올리세요.")
    return actions[:4]


def _headline(title: str, question_type: str, status: CheckStatus) -> str:
    if status == CheckStatus.blocker:
        return f"{title} 질문은 결제 전 보류 신호가 있습니다."
    if status == CheckStatus.warning:
        return f"{title} 질문은 {_question_label(question_type)} 확인이 먼저 필요합니다."
    return f"{title} 질문을 다음 검수 단계로 라우팅했습니다."


def _question_label(question_type: str) -> str:
    return QUESTION_TYPES[question_type]["label"]


def _category_label(category: Category) -> str:
    return "노트북" if category == Category.laptop else "데스크톱 PC"
