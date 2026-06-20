import re
from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    CheckoutNudgeRequest,
    CheckoutNudgeStep,
    CheckStatus,
    ListingDecoderRequest,
    ListingSpecFact,
    PublicCheckoutNudgeKit,
    PublicListingDecoderKit,
    PublicSpecRiskScanner,
    SpecRiskCheck,
    SpecRiskScannerRequest,
    SpecRiskScannerResult,
)


def build_public_spec_risk_scanner(
    generated_at: datetime | None = None,
) -> PublicSpecRiskScanner:
    generated_at = generated_at or datetime.now(UTC)
    return PublicSpecRiskScanner(
        generated_at=generated_at.isoformat(),
        headline="결제 직전 옵션명과 사양을 30초 안에 대조합니다.",
        summary=(
            "판매 페이지 제목, 장바구니 옵션명, 최종 결제 금액을 붙여 넣으면 "
            "예산 초과, CPU/GPU/RAM/SSD/OS 불일치, 캡처해야 할 증거 누락을 "
            "결제 가능·확인 필요·보류로 판정합니다."
        ),
        example_request={
            "category": "desktop_pc",
            "product_title": "Creator RTX 4070 SUPER Build",
            "budget_krw": 2_200_000,
            "cart_total_krw": 2_185_000,
            "expected_cpu": "Ryzen 7 7800X3D",
            "expected_gpu": "RTX 4070 SUPER",
            "expected_ram_gb": 32,
            "expected_storage_gb": 1000,
        },
        required_evidence=[
            "판매 페이지 모델명과 장바구니 옵션명",
            "최종 결제 금액, 배송비, 쿠폰, 카드 할인",
            "RAM/SSD/GPU/패널/OS 옵션 선택 상태",
            "배송 예정일, 반품, AS, 판매자 답변",
        ],
        next_actions=[
            "blocker가 있으면 바로 결제하지 말고 옵션명과 최종가 캡처를 먼저 확보하세요.",
            "warning만 남으면 분석 prefill로 SpecPilot AI 리포트를 만들어 대체 후보와 비교하세요.",
            "팀 구매는 검수 결과를 승인 채널에 공유해 실사용자 확인을 먼저 받으세요.",
        ],
    )


def scan_spec_risk(
    request: SpecRiskScannerRequest,
    generated_at: datetime | None = None,
) -> SpecRiskScannerResult:
    generated_at = generated_at or datetime.now(UTC)
    title = request.product_title.strip() or _category_label(request.category)
    option_text = request.option_text.strip()
    evidence_text = request.evidence_text.strip()
    combined_text = " ".join([title, option_text, evidence_text])
    checks = [
        _price_check(request),
        _text_presence_check(
            check_id="option_name",
            label="옵션명 원문",
            expected="판매 페이지 모델명과 장바구니 옵션명이 함께 있어야 합니다.",
            observed=option_text or "옵션명 원문 없음",
            ok=bool(option_text) and len(option_text) >= 18,
            recommendation="장바구니 옵션명, 색상, RAM/SSD/GPU/패널 선택값을 그대로 붙여 넣으세요.",
        ),
        _spec_check("cpu", "CPU", request.expected_cpu, combined_text),
        _spec_check("gpu", "GPU", request.expected_gpu, combined_text),
        _capacity_check("ram", "RAM", request.expected_ram_gb, combined_text, "GB"),
        _capacity_check("storage", "저장장치", request.expected_storage_gb, combined_text, "GB"),
        _spec_check("os", "OS", request.expected_os, combined_text),
    ]
    missing_evidence = _missing_evidence(option_text, evidence_text)
    if missing_evidence:
        checks.append(
            SpecRiskCheck(
                check_id="evidence",
                label="결제 전 증거",
                status=CheckStatus.warning,
                expected="최종가, 배송, 반품, AS, 판매자 답변을 확인해야 합니다.",
                observed=", ".join(missing_evidence),
                recommendation="누락된 증거를 캡처한 뒤 같은 문구로 다시 검수하세요.",
            )
        )
    blocker_count = sum(1 for check in checks if check.status == CheckStatus.blocker)
    warning_count = sum(1 for check in checks if check.status == CheckStatus.warning)
    readiness_score = _readiness_score(blocker_count, warning_count)
    verdict = _verdict(blocker_count, warning_count)
    label = _category_label(request.category)
    return SpecRiskScannerResult(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=title,
        budget_krw=request.budget_krw,
        cart_total_krw=request.cart_total_krw,
        verdict=verdict,
        readiness_score=readiness_score,
        headline=_headline(verdict, title),
        summary=(
            f"{label} 결제 전 검수에서 blocker {blocker_count}개, "
            f"warning {warning_count}개를 찾았습니다. "
            "사양과 증거가 맞아야 공개 리포트 없이도 결제 리스크를 낮출 수 있습니다."
        ),
        checks=checks,
        blocker_count=blocker_count,
        warning_count=warning_count,
        missing_evidence=missing_evidence,
        analysis_prefill=_analysis_prefill(request, verdict, checks),
        share_copy=_share_copy(title, verdict, blocker_count, warning_count),
        purchase_safety_brief=_purchase_safety_brief(
            request=request,
            verdict=verdict,
            blocker_count=blocker_count,
            warning_count=warning_count,
            missing_evidence=missing_evidence,
        ),
        seller_questions=_seller_questions(request, checks, missing_evidence),
        approval_brief=_approval_brief(
            title=title,
            verdict=verdict,
            readiness_score=readiness_score,
            blocker_count=blocker_count,
            warning_count=warning_count,
            missing_evidence=missing_evidence,
        ),
        capture_checklist=_capture_checklist(verdict, missing_evidence),
        checkout_next_step=_checkout_next_step(verdict, missing_evidence),
        next_actions=_next_actions(verdict, missing_evidence),
    )


def build_public_listing_decoder_kit(
    request: ListingDecoderRequest,
    generated_at: datetime | None = None,
) -> PublicListingDecoderKit:
    generated_at = generated_at or datetime.now(UTC)
    title = request.product_title.strip() or _category_label(request.category)
    option_text = request.option_text.strip()
    combined_text = " ".join([title, option_text]).strip()
    facts = _decode_listing_facts(request.category, combined_text)
    blocker_count = sum(1 for fact in facts if fact.status == CheckStatus.blocker)
    warning_count = sum(1 for fact in facts if fact.status == CheckStatus.warning)
    confidence_score = _decoder_confidence_score(facts, blocker_count, warning_count)
    scanner_prefill = _scanner_prefill(request, title, option_text, facts)
    category_label = _category_label(request.category)
    return PublicListingDecoderKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=title,
        option_text=option_text,
        normalized_title=_normalized_listing_title(title, facts),
        confidence_score=confidence_score,
        headline=_decoder_headline(category_label, title, blocker_count, warning_count),
        summary=(
            f"{category_label} 상품명에서 CPU/GPU/RAM/SSD/OS와 구매 조건 신호를 구조화했습니다. "
            f"blocker {blocker_count}개, warning {warning_count}개를 먼저 확인하고 "
            "장바구니 검수로 이어가세요."
        ),
        decoded_specs=facts,
        blocker_count=blocker_count,
        warning_count=warning_count,
        ambiguity_notes=_ambiguity_notes(request.category, facts),
        seller_questions=_decoder_seller_questions(facts),
        scanner_prefill=scanner_prefill,
        analysis_prefill=_decoder_analysis_prefill(
            request=request,
            title=title,
            facts=facts,
            scanner_prefill=scanner_prefill,
        ),
        share_copy=_decoder_share_copy(title, confidence_score, facts),
        next_actions=_decoder_next_actions(blocker_count, warning_count),
    )


def build_checkout_nudge_kit(
    request: CheckoutNudgeRequest,
    generated_at: datetime | None = None,
) -> PublicCheckoutNudgeKit:
    generated_at = generated_at or datetime.now(UTC)
    title = request.product_title.strip() or _category_label(request.category)
    verdict = request.verdict if request.verdict in {"ready", "verify", "hold"} else "verify"
    priority = _nudge_priority(verdict, request.blocker_count, request.warning_count)
    next_best_action = _nudge_next_best_action(verdict, request.missing_evidence)
    return PublicCheckoutNudgeKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=title,
        verdict=verdict,
        priority=priority,
        headline=_nudge_headline(verdict, title),
        summary=_nudge_summary(request, verdict),
        next_best_action=next_best_action,
        reminder_copy=_nudge_reminder_copy(request, verdict, next_best_action),
        analysis_prefill=_nudge_analysis_prefill(request, verdict),
        waitlist_prefill=_nudge_waitlist_prefill(request, next_best_action),
        nudges=_nudge_steps(request, verdict),
        proof_points=_nudge_proof_points(request, verdict),
    )


def _price_check(request: SpecRiskScannerRequest) -> SpecRiskCheck:
    budget = request.budget_krw
    total = request.cart_total_krw
    if total is None:
        return SpecRiskCheck(
            check_id="price",
            label="최종 결제 금액",
            status=CheckStatus.warning,
            expected=f"예산 {budget:,}원 이하의 최종 결제 금액",
            observed="최종 결제 금액 없음",
            recommendation="배송비, 쿠폰, 카드 할인 적용 후 최종 결제 금액을 입력하세요.",
        )
    if total > budget:
        return SpecRiskCheck(
            check_id="price",
            label="최종 결제 금액",
            status=CheckStatus.blocker,
            expected=f"예산 {budget:,}원 이하",
            observed=f"최종가 {total:,}원",
            recommendation="예산 초과분을 승인하거나 대체 후보와 가격 대기를 먼저 비교하세요.",
        )
    if total > int(budget * 0.97):
        status = CheckStatus.warning
        recommendation = "예산 여유가 작으니 배송비와 쿠폰 만료 조건을 캡처하세요."
    else:
        status = CheckStatus.ok
        recommendation = "예산 안에 들어오지만 결제 화면 총액 캡처는 남겨 두세요."
    return SpecRiskCheck(
        check_id="price",
        label="최종 결제 금액",
        status=status,
        expected=f"예산 {budget:,}원 이하",
        observed=f"최종가 {total:,}원",
        recommendation=recommendation,
    )


def _text_presence_check(
    *,
    check_id: str,
    label: str,
    expected: str,
    observed: str,
    ok: bool,
    recommendation: str,
) -> SpecRiskCheck:
    return SpecRiskCheck(
        check_id=check_id,
        label=label,
        status=CheckStatus.ok if ok else CheckStatus.blocker,
        expected=expected,
        observed=observed,
        recommendation=recommendation,
    )


def _spec_check(
    check_id: str,
    label: str,
    expected: str,
    text: str,
) -> SpecRiskCheck:
    expected = expected.strip()
    if not expected:
        return SpecRiskCheck(
            check_id=check_id,
            label=label,
            status=CheckStatus.warning,
            expected=f"{label} 기대값",
            observed="기대값 없음",
            recommendation=f"{label} 기대 사양을 입력해야 옵션명 불일치를 잡을 수 있습니다.",
        )
    tokens = _meaningful_tokens(expected)
    matched = [token for token in tokens if token in _compact(text)]
    if len(matched) >= max(1, min(2, len(tokens))):
        status = CheckStatus.ok
        observed = f"일치 토큰: {', '.join(matched)}"
        recommendation = f"{label} 표기는 기대값과 맞습니다."
    else:
        status = CheckStatus.blocker
        observed = "옵션명에서 기대 사양을 찾지 못함"
        recommendation = f"{expected}가 장바구니 옵션명에 보이는지 결제 전에 확인하세요."
    return SpecRiskCheck(
        check_id=check_id,
        label=label,
        status=status,
        expected=expected,
        observed=observed,
        recommendation=recommendation,
    )


def _capacity_check(
    check_id: str,
    label: str,
    expected_value: int | None,
    text: str,
    unit: str,
) -> SpecRiskCheck:
    if not expected_value:
        return SpecRiskCheck(
            check_id=check_id,
            label=label,
            status=CheckStatus.warning,
            expected=f"{label} 기대 용량",
            observed="기대값 없음",
            recommendation=f"{label} 용량을 입력해야 하위 옵션 주문을 막을 수 있습니다.",
        )
    observed_numbers = [
        int(value)
        for value in re.findall(r"(\d+)\s*(?:GB|TB|기가|테라)", text, re.I)
    ]
    normalized_numbers = []
    for value in observed_numbers:
        normalized_numbers.append(value * 1000 if value in {1, 2, 4, 8, 16} else value)
    if expected_value in normalized_numbers:
        status = CheckStatus.ok
        observed = f"{expected_value}{unit} 확인"
        recommendation = f"{label} 용량은 기대값과 맞습니다."
    else:
        status = CheckStatus.blocker
        observed = "옵션명에서 기대 용량을 찾지 못함"
        recommendation = f"{expected_value}{unit} 옵션이 실제 장바구니에 선택됐는지 확인하세요."
    return SpecRiskCheck(
        check_id=check_id,
        label=label,
        status=status,
        expected=f"{expected_value}{unit}",
        observed=observed,
        recommendation=recommendation,
    )


def _missing_evidence(option_text: str, evidence_text: str) -> list[str]:
    text = f"{option_text} {evidence_text}"
    checks = {
        "최종 결제 금액 캡처": ["최종", "결제", "총액", "쿠폰", "카드"],
        "배송 예정일": ["배송", "납기", "도착", "출고"],
        "반품 조건": ["반품", "교환", "환불"],
        "AS 조건": ["as", "a/s", "보증", "서비스"],
        "판매자 답변": ["판매자", "문의", "답변", "고객센터"],
    }
    compact = text.lower()
    return [
        label
        for label, keywords in checks.items()
        if not any(keyword in compact for keyword in keywords)
    ]


def _meaningful_tokens(value: str) -> list[str]:
    compact = _compact(value)
    raw_tokens = re.findall(r"[a-z0-9]+", compact)
    return [token for token in raw_tokens if len(token) >= 2]


def _compact(value: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", "", value.lower())


def _readiness_score(blocker_count: int, warning_count: int) -> float:
    return round(max(0, min(100, 100 - blocker_count * 22 - warning_count * 8)), 1)


def _verdict(blocker_count: int, warning_count: int) -> str:
    if blocker_count:
        return "hold"
    if warning_count:
        return "verify"
    return "ready"


def _headline(verdict: str, title: str) -> str:
    if verdict == "hold":
        return f"{title}은 결제 보류가 필요합니다."
    if verdict == "verify":
        return f"{title}은 증거 보강 후 결제 가능합니다."
    return f"{title}은 결제 전 핵심 검수를 통과했습니다."


def _analysis_prefill(
    request: SpecRiskScannerRequest,
    verdict: str,
    checks: list[SpecRiskCheck],
) -> str:
    issues = [
        f"{check.label}: {check.observed}"
        for check in checks
        if check.status != CheckStatus.ok
    ]
    label = _category_label(request.category)
    return (
        f"{label} '{request.product_title}' 결제 전 검수를 해줘. "
        f"예산은 {request.budget_krw:,}원, 최종가는 "
        f"{request.cart_total_krw:,}원이고 판정은 {verdict}야. "
        f"확인 이슈: {'; '.join(issues[:5]) or '핵심 사양 일치'}."
    )


def _share_copy(
    title: str,
    verdict: str,
    blocker_count: int,
    warning_count: int,
) -> str:
    return (
        "SpecPilot AI 옵션/사양 빠른 검수 결과\n"
        f"- 상품: {title}\n"
        f"- 판정: {verdict}\n"
        f"- blocker {blocker_count}개, warning {warning_count}개\n"
        "결제 전 옵션명, 최종가, 배송/반품/AS 증거를 같이 확인해 주세요."
    )


def _next_actions(verdict: str, missing_evidence: list[str]) -> list[str]:
    if verdict == "hold":
        return [
            "blocker 항목을 캡처하거나 판매자에게 확인하기 전에는 결제하지 마세요.",
            "같은 예산의 대체 후보와 가격 대기 시나리오를 SpecPilot AI 리포트로 비교하세요.",
            "검수 결과를 가족·팀 승인 채널에 공유해 반대 의견을 먼저 받으세요.",
        ]
    if missing_evidence:
        return [
            f"누락 증거를 먼저 확보하세요: {', '.join(missing_evidence[:3])}.",
            "증거를 붙여 다시 검수한 뒤 리포트 생성 또는 결제 판단으로 이동하세요.",
        ]
    return [
        "현재 옵션명과 최종가는 통과했지만 결제 화면 캡처를 저장하세요.",
        "공개 리포트로 추천 이유와 제외 후보를 함께 공유하세요.",
    ]


def _purchase_safety_brief(
    *,
    request: SpecRiskScannerRequest,
    verdict: str,
    blocker_count: int,
    warning_count: int,
    missing_evidence: list[str],
) -> str:
    total = (
        f"{request.cart_total_krw:,}원"
        if request.cart_total_krw is not None
        else "최종가 미입력"
    )
    if verdict == "hold":
        return (
            f"결제 보류입니다. 최종가 {total}, blocker {blocker_count}개가 있어 "
            "옵션명·사양·예산 중 하나라도 실제 주문과 다를 가능성이 큽니다."
        )
    if verdict == "verify":
        missing = ", ".join(missing_evidence[:2]) if missing_evidence else "warning 항목"
        return (
            f"조건부 결제 가능입니다. 최종가 {total}, warning {warning_count}개가 남아 "
            f"{missing}를 보강한 뒤 결제하세요."
        )
    return (
        f"결제 가능 후보입니다. 최종가 {total} 기준 핵심 옵션과 증거가 맞지만, "
        "결제 화면 캡처와 주문번호는 구매 결과 회수용으로 저장하세요."
    )


def _seller_questions(
    request: SpecRiskScannerRequest,
    checks: list[SpecRiskCheck],
    missing_evidence: list[str],
) -> list[str]:
    questions: list[str] = []
    failed_labels = [check.label for check in checks if check.status == CheckStatus.blocker]
    if failed_labels:
        questions.append(
            "장바구니 옵션명이 실제 출고 사양과 같은지 확인 부탁드립니다: "
            + ", ".join(failed_labels[:4])
        )
    if request.cart_total_krw is None:
        questions.append("배송비, 쿠폰, 카드 할인이 반영된 최종 결제 금액이 얼마인가요?")
    elif request.cart_total_krw > request.budget_krw:
        questions.append(
            f"최종 결제 금액 {request.cart_total_krw:,}원이 예산 {request.budget_krw:,}원을 넘는데 "
            "할인/대체 옵션이 있나요?"
        )
    if any("배송" in item for item in missing_evidence):
        questions.append("오늘 결제하면 실제 출고일과 도착 예정일은 언제인가요?")
    if any("반품" in item for item in missing_evidence):
        questions.append("개봉 후 초기 불량, 옵션 오배송, 단순 변심의 반품/교환 조건이 어떻게 되나요?")
    if any("AS" in item for item in missing_evidence):
        questions.append("제조사/판매자 AS 기간과 접수 경로를 주문 전에 확인할 수 있나요?")
    if not questions:
        questions.append("현재 옵션명 그대로 주문하면 CPU/GPU/RAM/SSD/OS가 모두 표시 사양대로 출고되나요?")
    return questions[:5]


def _approval_brief(
    *,
    title: str,
    verdict: str,
    readiness_score: float,
    blocker_count: int,
    warning_count: int,
    missing_evidence: list[str],
) -> str:
    label = {"ready": "결제 가능", "verify": "확인 후 결제", "hold": "결제 보류"}[verdict]
    evidence = (
        f"누락 증거: {', '.join(missing_evidence[:3])}"
        if missing_evidence
        else "필수 증거 확보"
    )
    return (
        f"{title} 검수 결과는 {label}입니다. 준비도 {round(readiness_score)}점, "
        f"blocker {blocker_count}개, warning {warning_count}개, {evidence}. "
        "승인 전에는 판매 페이지 제목, 장바구니 옵션명, 최종 결제 금액 캡처를 함께 확인하세요."
    )


def _capture_checklist(verdict: str, missing_evidence: list[str]) -> list[str]:
    base = [
        "판매 페이지 제목과 모델명",
        "장바구니 옵션명 전체",
        "배송비·쿠폰·카드 할인이 반영된 최종 결제 금액",
    ]
    if verdict == "hold":
        base.append("판매자 답변 또는 대체 후보 비교 리포트")
    if missing_evidence:
        base.extend(missing_evidence)
    else:
        base.extend(["배송 예정일", "반품/교환 조건", "AS 또는 보증 조건"])
    return list(dict.fromkeys(base))[:7]


def _checkout_next_step(verdict: str, missing_evidence: list[str]) -> str:
    if verdict == "hold":
        return "결제하지 말고 blocker 항목을 판매자에게 확인하거나 대체 후보 분석으로 이동하세요."
    if missing_evidence:
        return "누락 증거를 캡처한 뒤 같은 장바구니 문구로 다시 검수하세요."
    if verdict == "verify":
        return "warning 항목을 승인 채널에 공유하고 확인 답변을 받은 뒤 결제하세요."
    return "결제 화면 캡처를 저장하고 구매 결과를 리포트에 회수할 준비를 하세요."


def _category_label(category: Category) -> str:
    return "노트북" if category == Category.laptop else "데스크톱 PC"


def _decode_listing_facts(category: Category, text: str) -> list[ListingSpecFact]:
    normalized = _normalize_listing_text(text)
    facts = [
        _pattern_fact(
            slot="cpu",
            label="CPU",
            value=_first_match(
                normalized,
                [
                    r"ryzen\s*[3579]\s*[0-9]{4}[a-z0-9]*",
                    r"i[3579]\s*-?\s*[0-9]{4,5}[a-z0-9]*",
                    r"core\s+ultra\s+[3579]\s*[0-9]{3}[a-z]*",
                    r"m[1234]\s*(?:pro|max|air)?",
                ],
            ),
            missing_recommendation="CPU 세대와 등급이 상품명/옵션명에 보이는지 확인하세요.",
        ),
        _pattern_fact(
            slot="gpu",
            label="GPU",
            value=_first_match(
                normalized,
                [
                    r"rtx\s*[2345]0[56789]0\s*(?:ti|super)?",
                    r"gtx\s*16[0-9]{2}\s*(?:ti|super)?",
                    r"rx\s*[67][0-9]{3}\s*(?:xt)?",
                    r"iris\s*xe|arc\s*[a-z]?[0-9]{3}|radeon\s*graphics",
                ],
            ),
            missing_recommendation="외장 GPU가 필요한 목적이면 그래픽 옵션명을 판매자에게 확인하세요.",
        ),
        _capacity_fact("ram", "RAM", normalized, r"(?:ram|메모리|ddr[45]?)?\s*([0-9]{1,3})\s*(?:gb|g)\s*(?:ram|메모리)?"),
        _capacity_fact(
            "storage",
            "저장장치",
            normalized,
            r"(?:(?:ssd|nvme|m\.2)\s*)?([0-9]{3,4}|[12])\s*(tb|gb|g)\s*(?:ssd|nvme|m\.2)?",
        ),
        _os_fact(normalized),
        _condition_fact(normalized),
    ]
    if category == Category.laptop:
        facts.append(_display_fact(normalized))
    return facts


def _pattern_fact(
    *,
    slot: str,
    label: str,
    value: str,
    missing_recommendation: str,
) -> ListingSpecFact:
    if value:
        return ListingSpecFact(
            slot=slot,
            label=label,
            value=_pretty_spec_value(value),
            status=CheckStatus.ok,
            evidence=value,
            recommendation=f"{label} 표기를 옵션/장바구니에서도 같은지 확인하세요.",
        )
    return ListingSpecFact(
        slot=slot,
        label=label,
        value="확인 필요",
        status=CheckStatus.warning,
        evidence="상품명에서 명확한 표기를 찾지 못함",
        recommendation=missing_recommendation,
    )


def _capacity_fact(slot: str, label: str, text: str, pattern: str) -> ListingSpecFact:
    matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
    values: list[int] = []
    for match in matches:
        raw_value = int(match.group(1))
        unit = match.group(2).lower() if match.lastindex and match.lastindex >= 2 else "gb"
        value_gb = raw_value * 1000 if unit == "tb" else raw_value
        if 4 <= value_gb <= 8192:
            values.append(value_gb)
    if values:
        selected = max(values)
        return ListingSpecFact(
            slot=slot,
            label=label,
            value=f"{selected:,}GB",
            status=CheckStatus.ok,
            evidence=f"{selected:,}GB",
            recommendation=f"{label} 용량이 실제 선택 옵션과 같은지 장바구니에서 다시 대조하세요.",
        )
    return ListingSpecFact(
        slot=slot,
        label=label,
        value="확인 필요",
        status=CheckStatus.warning,
        evidence="상품명에서 용량 표기를 찾지 못함",
        recommendation=f"{label} 용량은 옵션 변경으로 자주 달라지므로 장바구니 옵션명을 확인하세요.",
    )


def _os_fact(text: str) -> ListingSpecFact:
    if any(token in text for token in ["free dos", "freedos", "os 미포함", "운영체제 미포함", "윈도우 미포함"]):
        return ListingSpecFact(
            slot="os",
            label="OS",
            value="OS 미포함",
            status=CheckStatus.warning,
            evidence="FreeDOS/OS 미포함 표기",
            recommendation="Windows가 필요하면 OS 포함 여부와 추가 비용을 결제 전에 확인하세요.",
        )
    if re.search(r"windows?\s*11|윈도우\s*11|win\s*11", text, flags=re.IGNORECASE):
        return ListingSpecFact(
            slot="os",
            label="OS",
            value="Windows 11",
            status=CheckStatus.ok,
            evidence="Windows 11 표기",
            recommendation="Home/Pro 에디션과 정품 인증 조건을 확인하세요.",
        )
    return ListingSpecFact(
        slot="os",
        label="OS",
        value="확인 필요",
        status=CheckStatus.warning,
        evidence="OS 표기를 찾지 못함",
        recommendation="운영체제 포함 여부와 설치/라이선스 비용을 판매자에게 확인하세요.",
    )


def _condition_fact(text: str) -> ListingSpecFact:
    blocker_tokens = ["중고", "리퍼", "refurb", "전시", "반품", "스크래치"]
    warning_tokens = ["벌크", "해외", "병행", "직구", "무상 as 1년", "미개봉"]
    blocker = [token for token in blocker_tokens if token in text]
    warning = [token for token in warning_tokens if token in text]
    if blocker:
        return ListingSpecFact(
            slot="condition",
            label="상품 상태",
            value=", ".join(blocker),
            status=CheckStatus.blocker,
            evidence=", ".join(blocker),
            recommendation="신품 구매가 목표라면 중고/리퍼/전시 조건은 결제 전 제외하거나 명시 승인하세요.",
        )
    if warning:
        return ListingSpecFact(
            slot="condition",
            label="상품 상태",
            value=", ".join(warning),
            status=CheckStatus.warning,
            evidence=", ".join(warning),
            recommendation="정품 AS, 국내 배송, 반품 가능 여부를 판매자 답변으로 남기세요.",
        )
    return ListingSpecFact(
        slot="condition",
        label="상품 상태",
        value="신품 표기 위험 신호 없음",
        status=CheckStatus.ok,
        evidence="중고/리퍼/전시/해외 위험어 없음",
        recommendation="결제 전 판매자와 반품/AS 조건은 별도 캡처하세요.",
    )


def _display_fact(text: str) -> ListingSpecFact:
    size = _first_match(text, [r"([0-9]{2}(?:\.[0-9])?)\s*(?:인치|inch|\")"])
    refresh = _first_match(text, [r"([0-9]{2,3})\s*hz"])
    if size or refresh:
        value = " / ".join(part for part in [size, refresh.upper() if refresh else ""] if part)
        return ListingSpecFact(
            slot="display",
            label="디스플레이",
            value=value,
            status=CheckStatus.ok,
            evidence=value,
            recommendation="패널 종류, 해상도, 밝기, 무게는 상세 페이지에서 추가 확인하세요.",
        )
    return ListingSpecFact(
        slot="display",
        label="디스플레이",
        value="확인 필요",
        status=CheckStatus.warning,
        evidence="크기/주사율 표기를 찾지 못함",
        recommendation="노트북은 화면 크기, 해상도, 밝기, 무게가 구매 만족도에 직접 영향을 줍니다.",
    )


def _scanner_prefill(
    request: ListingDecoderRequest,
    title: str,
    option_text: str,
    facts: list[ListingSpecFact],
) -> SpecRiskScannerRequest:
    by_slot = {fact.slot: fact for fact in facts}
    return SpecRiskScannerRequest(
        category=request.category,
        product_title=title,
        option_text=option_text or title,
        cart_total_krw=request.cart_total_krw,
        budget_krw=request.budget_krw,
        expected_cpu=_prefill_value(by_slot.get("cpu")),
        expected_gpu=_prefill_value(by_slot.get("gpu")),
        expected_ram_gb=_prefill_capacity(by_slot.get("ram")),
        expected_storage_gb=_prefill_capacity(by_slot.get("storage")),
        expected_os=_prefill_value(by_slot.get("os"), ignore_values={"OS 미포함"}),
        evidence_text="상품명 디코더 결과 기반 prefill",
        source="listing_decoder",
    )


def _prefill_value(
    fact: ListingSpecFact | None,
    *,
    ignore_values: set[str] | None = None,
) -> str:
    if fact is None or fact.status != CheckStatus.ok:
        return ""
    if ignore_values and fact.value in ignore_values:
        return ""
    return fact.value


def _prefill_capacity(fact: ListingSpecFact | None) -> int | None:
    if fact is None or fact.status != CheckStatus.ok:
        return None
    match = re.search(r"([0-9,]+)", fact.value)
    return int(match.group(1).replace(",", "")) if match else None


def _decoder_confidence_score(
    facts: list[ListingSpecFact],
    blocker_count: int,
    warning_count: int,
) -> float:
    ok_count = sum(1 for fact in facts if fact.status == CheckStatus.ok)
    base = 42 + ok_count * 10 - warning_count * 6 - blocker_count * 18
    return round(min(98, max(12, base)), 1)


def _normalized_listing_title(title: str, facts: list[ListingSpecFact]) -> str:
    spec_values = [
        fact.value
        for fact in facts
        if fact.status == CheckStatus.ok and fact.slot in {"cpu", "gpu", "ram", "storage", "os"}
    ]
    return " / ".join([title, *spec_values[:5]])


def _decoder_headline(
    category_label: str,
    title: str,
    blocker_count: int,
    warning_count: int,
) -> str:
    if blocker_count:
        return f"{title} 상품명에서 결제 전 차단 신호를 먼저 찾았습니다."
    if warning_count:
        return f"{title} 상품명은 {category_label} 구매 전 추가 확인이 필요합니다."
    return f"{title} 상품명을 장바구니 검수용 사양으로 정리했습니다."


def _ambiguity_notes(category: Category, facts: list[ListingSpecFact]) -> list[str]:
    notes = [
        f"{fact.label}: {fact.recommendation}"
        for fact in facts
        if fact.status != CheckStatus.ok
    ]
    if category == Category.laptop and not any(fact.slot == "display" for fact in facts):
        notes.append("노트북은 무게, 패널, 배터리 조건을 별도 증거로 남기세요.")
    return notes[:5]


def _decoder_seller_questions(facts: list[ListingSpecFact]) -> list[str]:
    questions = [
        "장바구니 옵션명 기준 CPU/GPU/RAM/SSD/OS가 상품명과 동일한가요?",
        "최종 결제 금액에 배송비, 설치비, OS 비용, 카드 할인 조건이 모두 반영됐나요?",
    ]
    if any(fact.slot == "condition" and fact.status != CheckStatus.ok for fact in facts):
        questions.insert(0, "신품/중고/리퍼/전시/해외 구매 조건과 국내 AS 가능 여부를 확인해 주세요.")
    if any(fact.slot == "os" and fact.status != CheckStatus.ok for fact in facts):
        questions.append("Windows 포함 여부, 에디션, 정품 인증 방식, 추가 설치 비용을 알려 주세요.")
    return questions


def _decoder_analysis_prefill(
    *,
    request: ListingDecoderRequest,
    title: str,
    facts: list[ListingSpecFact],
    scanner_prefill: SpecRiskScannerRequest,
) -> str:
    specs = ", ".join(
        f"{fact.label} {fact.value}" for fact in facts if fact.status == CheckStatus.ok
    )
    total = (
        f"{request.cart_total_krw:,}원"
        if request.cart_total_krw is not None
        else "최종가 미입력"
    )
    return (
        f"{_category_label(request.category)} 상품명 '{title}'을 해석했어. "
        f"목적은 {request.purpose}, 예산은 {request.budget_krw:,}원, 현재 최종가는 {total}야. "
        f"해석된 사양은 {specs or '명확하지 않음'}이고 "
        f"검수 prefill은 CPU {scanner_prefill.expected_cpu or '미확인'}, "
        f"GPU {scanner_prefill.expected_gpu or '미확인'}, "
        f"RAM {scanner_prefill.expected_ram_gb or '미확인'}GB, "
        f"SSD {scanner_prefill.expected_storage_gb or '미확인'}GB야. "
        "이 상품명을 그대로 결제해도 되는지 옵션명, 판매자, AS, 대체 후보까지 검토해줘."
    )


def _decoder_share_copy(
    title: str,
    confidence_score: float,
    facts: list[ListingSpecFact],
) -> str:
    lines = [
        "SpecPilot AI 상품명 해석",
        f"- 상품: {title}",
        f"- 해석 신뢰도: {confidence_score}점",
    ]
    lines.extend(
        f"- {fact.label}: {fact.value} / {fact.status.value}"
        for fact in facts[:6]
    )
    lines.append("이 옵션명 그대로 결제해도 되는지 확인 부탁드립니다.")
    return "\n".join(lines)


def _decoder_next_actions(blocker_count: int, warning_count: int) -> list[str]:
    actions = [
        "해석 결과를 장바구니 옵션명과 다시 대조한 뒤 옵션/사양 빠른 검수기로 넘기세요.",
        "상품명에 없는 사양은 상세 페이지 캡처나 판매자 답변으로 증거를 남기세요.",
        "CPU/GPU/RAM/SSD/OS 중 하나라도 불명확하면 같은 예산의 공개 후보 비교표로 대체 후보를 확인하세요.",
    ]
    if blocker_count:
        actions.insert(0, "중고/리퍼/전시/해외 조건이 보이면 신품 구매 목표에서는 바로 결제하지 마세요.")
    elif warning_count:
        actions.insert(0, "warning 항목은 결제 전 판매자 질문으로 먼저 닫으세요.")
    return actions


def _first_match(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return ""


def _pretty_spec_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().upper().replace("RYZEN", "Ryzen")


def _normalize_listing_text(value: str) -> str:
    normalized = value.lower()
    normalized = normalized.replace("기가", "gb").replace("테라", "tb")
    normalized = normalized.replace("지포스", "rtx").replace("라이젠", "ryzen")
    normalized = normalized.replace("윈도우", "windows")
    return re.sub(r"[\[\]()/,+|]", " ", normalized)


def _nudge_priority(
    verdict: str,
    blocker_count: int,
    warning_count: int,
) -> CheckStatus:
    if verdict == "hold" or blocker_count:
        return CheckStatus.blocker
    if verdict == "verify" or warning_count:
        return CheckStatus.warning
    return CheckStatus.ok


def _nudge_headline(verdict: str, title: str) -> str:
    if verdict == "hold":
        return f"{title}은 결제 전 확인 답변을 받아야 합니다."
    if verdict == "verify":
        return f"{title}은 24시간 안에 한 번 더 확인하세요."
    return f"{title}은 구매 결과 회수까지 연결할 수 있습니다."


def _nudge_summary(request: CheckoutNudgeRequest, verdict: str) -> str:
    total = (
        f"{request.cart_total_krw:,}원"
        if request.cart_total_krw is not None
        else "최종가 미입력"
    )
    if verdict == "hold":
        return (
            f"최종가 {total}, blocker {request.blocker_count}개입니다. "
            "판매자 답변, 대체 후보 비교, 승인 공유 중 하나가 끝나기 전에는 결제를 미룹니다."
        )
    if verdict == "verify":
        return (
            f"최종가 {total}, warning {request.warning_count}개입니다. "
            "오늘 캡처, 내일 가격 재확인, 결제 후 결과 회수까지 이어지게 만듭니다."
        )
    return (
        f"최종가 {total} 기준 핵심 검수를 통과했습니다. "
        "결제 화면 캡처와 구매 결과 회수를 예약하면 추천 품질 학습까지 닫힙니다."
    )


def _nudge_next_best_action(verdict: str, missing_evidence: list[str]) -> str:
    if verdict == "hold":
        return "판매자에게 옵션/최종가 확인 질문을 보내고 답변 전까지 결제를 보류하세요."
    if missing_evidence:
        return f"누락 증거를 먼저 캡처하세요: {', '.join(missing_evidence[:2])}."
    if verdict == "verify":
        return "24시간 뒤 같은 장바구니 최종가와 옵션명을 다시 확인하세요."
    return "결제 화면 캡처를 저장하고 구매 결과를 남길 시간을 예약하세요."


def _nudge_reminder_copy(
    request: CheckoutNudgeRequest,
    verdict: str,
    next_best_action: str,
) -> str:
    label = {"ready": "결제 가능", "verify": "확인 후 결제", "hold": "결제 보류"}[verdict]
    total = (
        f"{request.cart_total_krw:,}원"
        if request.cart_total_krw is not None
        else "최종가 미입력"
    )
    return (
        "SpecPilot AI 장바구니 후속 알림\n"
        f"- 상품: {request.product_title}\n"
        f"- 판정: {label}\n"
        f"- 최종가: {total}\n"
        f"- 다음 행동: {next_best_action}\n"
        "결제 전 옵션명, 최종가, 배송/반품/AS 증거를 다시 확인합니다."
    )


def _nudge_analysis_prefill(request: CheckoutNudgeRequest, verdict: str) -> str:
    total = (
        f"{request.cart_total_krw:,}원"
        if request.cart_total_krw is not None
        else "최종가 미입력"
    )
    return (
        f"{_category_label(request.category)} '{request.product_title}' 장바구니를 "
        f"{verdict} 판정 이후 다시 검토해줘. 예산 {request.budget_krw:,}원, "
        f"현재 최종가 {total}, blocker {request.blocker_count}개, "
        f"warning {request.warning_count}개야."
    )


def _nudge_waitlist_prefill(
    request: CheckoutNudgeRequest,
    next_best_action: str,
) -> str:
    return (
        f"{request.product_title} 구매를 놓치지 않도록 후속 알림을 받고 싶습니다. "
        f"다음 행동: {next_best_action}"
    )


def _nudge_steps(
    request: CheckoutNudgeRequest,
    verdict: str,
) -> list[CheckoutNudgeStep]:
    first = (
        CheckoutNudgeStep(
            step_id="seller_answer",
            label="판매자 답변 확인",
            timing="1시간 안",
            trigger="옵션명·최종가·AS 중 하나라도 blocker",
            message="판매자 답변을 받기 전에는 결제하지 말고 답변 문구를 캡처하세요.",
            cta_label="질문 복사",
            cta_path="#spec-scanner",
            event_name="checkout_nudge_seller_answer",
        )
        if verdict == "hold"
        else CheckoutNudgeStep(
            step_id="capture_now",
            label="결제 화면 캡처",
            timing="지금",
            trigger="결제 가능 또는 warning만 남은 장바구니",
            message="최종 결제 금액, 옵션명, 배송/반품/AS 조건을 한 번에 캡처하세요.",
            cta_label="캡처 체크",
            cta_path="#spec-scanner",
            event_name="checkout_nudge_capture_now",
        )
    )
    return [
        first,
        CheckoutNudgeStep(
            step_id="price_recheck",
            label="가격 재확인",
            timing="24시간 뒤",
            trigger="쿠폰·카드 할인·재고 변동 가능성",
            message="같은 옵션으로 최종가가 바뀌었는지 확인하고, 오르면 대체 후보 분석으로 이동하세요.",
            cta_label="가격 타이밍 보기",
            cta_path="#deal-timing",
            event_name="checkout_nudge_price_recheck",
        ),
        CheckoutNudgeStep(
            step_id="outcome_capture",
            label="구매 결과 회수",
            timing="구매 후 3일",
            trigger="결제 완료 또는 구매 보류 결정",
            message="실제 구매/지연/이탈 결과와 최종 결제 금액을 남겨 다음 추천 품질에 반영하세요.",
            cta_label="구매 결과 남기기",
            cta_path="/#outcomes",
            event_name="checkout_nudge_outcome_capture",
        ),
    ]


def _nudge_proof_points(
    request: CheckoutNudgeRequest,
    verdict: str,
) -> list[str]:
    points = [
        f"blocker {request.blocker_count}개 / warning {request.warning_count}개 기준",
        "결제 전 캡처와 판매자 답변을 후속 행동으로 분리",
        "24시간 가격 재확인과 구매 결과 회수까지 연결",
    ]
    if verdict == "hold":
        points.append("보류 장바구니는 대체 후보 비교로 이탈을 줄임")
    return points
