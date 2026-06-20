import re
from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    CheckStatus,
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
        next_actions=_next_actions(verdict, missing_evidence),
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


def _category_label(category: Category) -> str:
    return "노트북" if category == Category.laptop else "데스크톱 PC"
