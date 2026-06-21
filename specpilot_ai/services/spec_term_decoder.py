import re
from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    CheckStatus,
    PublicSpecTermDecoderKit,
    SpecRiskScannerRequest,
    SpecTermDecoderRequest,
    SpecTermExplanation,
)

TERM_GUIDE: dict[str, tuple[str, str, CheckStatus, str]] = {
    "cpu": (
        "프로그램 계산을 맡는 부품입니다.",
        "영상 편집, 개발, 여러 창을 동시에 쓰는 작업의 체감 속도를 좌우합니다.",
        CheckStatus.ok,
        "CPU 모델명과 세대가 실제 장바구니 옵션에도 같은지 확인해 주세요.",
    ),
    "gpu": (
        "그래픽, 게임, 영상 효과, AI 가속을 맡는 부품입니다.",
        "게임 해상도와 프리미어/다빈치 같은 작업 성능을 크게 바꿉니다.",
        CheckStatus.ok,
        "GPU 모델명, 노트북이면 TGP 전력, 데스크톱이면 제조사와 보증 기간을 알려 주세요.",
    ),
    "ram": (
        "작업 중인 파일과 앱을 동시에 올려 두는 임시 작업 공간입니다.",
        "16GB는 기본, 영상 편집이나 긴 사용 수명은 32GB 이상이 안전합니다.",
        CheckStatus.ok,
        "RAM 용량, 온보드 여부, 추가 슬롯과 업그레이드 가능 여부를 확인해 주세요.",
    ),
    "ssd": (
        "운영체제, 프로그램, 파일을 저장하는 빠른 저장장치입니다.",
        "512GB는 금방 부족할 수 있고, 작업용은 1TB 이상이 편합니다.",
        CheckStatus.ok,
        "SSD 용량, NVMe 여부, 추가 슬롯과 교체 가능 여부를 알려 주세요.",
    ),
    "freedos": (
        "Windows가 설치되지 않은 상태로 출고된다는 뜻입니다.",
        "초보 구매자는 Windows 구매/설치 비용과 정품 인증 때문에 결제 후 막힐 수 있습니다.",
        CheckStatus.warning,
        "Windows 포함 여부, 설치 비용, 정품 인증 방식, 설치 지원 범위를 알려 주세요.",
    ),
    "내장그래픽": (
        "CPU 안에 들어 있는 기본 그래픽입니다.",
        "문서/웹은 충분하지만 최신 게임, 3D, 영상 효과 작업에는 부족할 수 있습니다.",
        CheckStatus.warning,
        "사용 목적 기준으로 외장 GPU가 필요한지, 연결 가능한 모니터 수는 몇 개인지 알려 주세요.",
    ),
    "외장그래픽": (
        "CPU와 별도로 들어간 전용 그래픽 카드입니다.",
        "게임, 영상 편집, 3D 작업 성능을 올리지만 가격, 발열, 전력 조건을 같이 봐야 합니다.",
        CheckStatus.ok,
        "정확한 GPU 모델명, 전력 제한, 보증 기간, 실제 장착 여부를 확인해 주세요.",
    ),
    "tgp": (
        "노트북 GPU가 쓸 수 있는 전력 한도입니다.",
        "같은 RTX 4060이어도 TGP가 낮으면 게임/작업 성능이 크게 낮아질 수 있습니다.",
        CheckStatus.warning,
        "GPU TGP, 쿨링 모드, 전원 연결 시 성능 제한 여부를 알려 주세요.",
    ),
    "온보드": (
        "부품이 메인보드에 납땜되어 교체가 어렵다는 뜻입니다.",
        "RAM이 온보드면 나중에 업그레이드가 안 되거나 제한될 수 있습니다.",
        CheckStatus.warning,
        "온보드 용량과 추가 슬롯 유무, 최대 RAM 용량을 알려 주세요.",
    ),
    "리퍼": (
        "반품, 수리, 재검수된 제품입니다.",
        "신품보다 저렴할 수 있지만 상태, 보증, 반품 조건이 다르면 초보자에게 위험합니다.",
        CheckStatus.blocker,
        "리퍼 사유, 사용 흔적, 보증 기간, 초기 불량/단순 변심 반품 가능 여부를 알려 주세요.",
    ),
    "전시": (
        "매장이나 행사에서 이미 개봉/사용된 제품입니다.",
        "배터리, 외관, 보증 시작일이 신품과 다를 수 있어 바로 결제하면 위험합니다.",
        CheckStatus.blocker,
        "전시 기간, 외관 사진, 배터리 상태, 보증 시작일, 반품 가능 여부를 알려 주세요.",
    ),
    "병행": (
        "공식 유통사가 아닌 경로로 들어온 제품입니다.",
        "가격은 낮을 수 있지만 국내 AS, 교환, 반품 조건이 제한될 수 있습니다.",
        CheckStatus.warning,
        "국내 공식 AS 가능 여부, 수리 접수처, 보증 기간, 반품 조건을 알려 주세요.",
    ),
    "해외": (
        "해외 구매 또는 해외 배송 조건이 섞여 있다는 뜻입니다.",
        "배송 지연, 반품 비용, 국내 AS 제한 때문에 급한 구매에는 위험합니다.",
        CheckStatus.warning,
        "배송 기간, 관부가세 포함 여부, 국내 AS와 반품 배송비 조건을 알려 주세요.",
    ),
    "반품불가": (
        "구매 후 단순 변심이나 일부 사유로 반품이 제한된다는 뜻입니다.",
        "초보자는 옵션 실수나 호환성 문제를 되돌리기 어려워 결제 전 차단 신호입니다.",
        CheckStatus.blocker,
        "초기 불량, 오배송, 사양 불일치 시 교환/환불 가능 범위를 문장으로 알려 주세요.",
    ),
    "썬더볼트": (
        "고속 데이터, 충전, 외부 모니터 연결을 한 포트로 처리하는 규격입니다.",
        "노트북 도킹, 외장 저장장치, 모니터 연결을 자주 하면 중요합니다.",
        CheckStatus.ok,
        "해당 USB-C 포트가 Thunderbolt인지, PD 충전과 디스플레이 출력도 되는지 알려 주세요.",
    ),
    "pd충전": (
        "USB-C 충전기로 노트북을 충전할 수 있다는 뜻입니다.",
        "출장이나 학교에서 충전기 무게를 줄일 수 있지만 필요한 와트 수를 확인해야 합니다.",
        CheckStatus.ok,
        "PD 충전 지원 와트, 동봉 충전기, 고성능 작업 중 충전 유지 여부를 알려 주세요.",
    ),
    "oled": (
        "명암과 색 표현이 강한 디스플레이 방식입니다.",
        "영상 감상은 좋지만 번인, 밝기, 글자 가독성, 보증 조건을 같이 봐야 합니다.",
        CheckStatus.warning,
        "OLED 번인 보증, 최대 밝기, 무상 패널 보증 조건을 알려 주세요.",
    ),
}

ALIASES: dict[str, str] = {
    "processor": "cpu",
    "프로세서": "cpu",
    "그래픽": "gpu",
    "그래픽카드": "gpu",
    "vga": "gpu",
    "메모리": "ram",
    "램": "ram",
    "storage": "ssd",
    "저장장치": "ssd",
    "free dos": "freedos",
    "os 미포함": "freedos",
    "운영체제 미포함": "freedos",
    "윈도우 미포함": "freedos",
    "refurb": "리퍼",
    "전시품": "전시",
    "병행수입": "병행",
    "직구": "해외",
    "해외배송": "해외",
    "반품 불가": "반품불가",
    "thunderbolt": "썬더볼트",
    "usb4": "썬더볼트",
    "pd": "pd충전",
}


def build_public_spec_term_decoder_kit(
    request: SpecTermDecoderRequest,
    generated_at: datetime | None = None,
) -> PublicSpecTermDecoderKit:
    generated_at = generated_at or datetime.now(UTC)
    title = request.product_title.strip() or _category_label(request.category)
    text = " ".join([title, request.listing_text, " ".join(request.terms)]).strip()
    terms = _extract_terms(text, request.terms)
    explanations = [_explain_term(term, text) for term in terms]
    explanations = explanations or [_unknown_explanation(text or title)]
    blocker_count = sum(1 for item in explanations if item.status == CheckStatus.blocker)
    warning_count = sum(1 for item in explanations if item.status == CheckStatus.warning)
    decoder_status = _decoder_status(blocker_count, warning_count)
    risk_terms = [item.term for item in explanations if item.status != CheckStatus.ok]
    clarity_score = _clarity_score(explanations, blocker_count, warning_count, text)
    scanner_prefill = _scanner_prefill(request, title, text)
    return PublicSpecTermDecoderKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=title,
        buyer_level=request.buyer_level,
        primary_purpose=request.primary_purpose,
        decoder_status=decoder_status,
        clarity_score=clarity_score,
        headline=_headline(title, decoder_status),
        summary=(
            f"{_category_label(request.category)} 상품 문구에서 구매자가 헷갈리기 쉬운 용어 "
            f"{len(explanations)}개를 쉬운 말로 바꿨습니다. "
            f"blocker {blocker_count}개, warning {warning_count}개를 먼저 확인하세요."
        ),
        explanations=explanations,
        risk_terms=risk_terms,
        seller_questions=_seller_questions(explanations),
        beginner_checklist=_beginner_checklist(request.category, risk_terms),
        plain_language_brief=_plain_language_brief(
            title=title,
            purpose=request.primary_purpose,
            explanations=explanations,
        ),
        scanner_prefill=scanner_prefill,
        analysis_prefill=_analysis_prefill(request, title, explanations, scanner_prefill),
        share_copy=_share_copy(title, decoder_status, risk_terms),
        next_actions=_next_actions(decoder_status, risk_terms),
    )


def _extract_terms(text: str, requested_terms: list[str]) -> list[str]:
    candidates: list[str] = []
    lowered = text.lower()
    for term in requested_terms:
        normalized = _canonical_term(term)
        if normalized and normalized not in candidates:
            candidates.append(normalized)
    for token in [*TERM_GUIDE, *ALIASES]:
        if token in lowered or token in text:
            normalized = _canonical_term(token)
            if normalized and normalized not in candidates:
                candidates.append(normalized)
    for pattern, term in [
        (r"rtx\s*[0-9]{4}", "gpu"),
        (r"ryzen|intel|core\s*i[3579]|ultra\s*[579]", "cpu"),
        (r"\b[0-9]{2,3}\s*gb\b|[0-9]{2,3}\s*기가", "ram"),
        (r"\b[0-9](?:\.[0-9])?\s*tb\b|\b[0-9]{3,4}\s*gb\b", "ssd"),
    ]:
        if re.search(pattern, lowered, flags=re.IGNORECASE) and term not in candidates:
            candidates.append(term)
    return candidates[:8]


def _canonical_term(term: str) -> str:
    cleaned = term.strip().lower().replace("-", "").replace(" ", "")
    original = term.strip()
    if cleaned in TERM_GUIDE:
        return cleaned
    if original in TERM_GUIDE:
        return original
    for alias, canonical in ALIASES.items():
        alias_key = alias.replace(" ", "")
        if cleaned == alias_key or alias in term.lower():
            return canonical
    return original if original else ""


def _explain_term(term: str, text: str) -> SpecTermExplanation:
    guide = TERM_GUIDE.get(term)
    if guide is None:
        return _unknown_explanation(term)
    meaning, impact, status, question = guide
    return SpecTermExplanation(
        term=_display_term(term),
        plain_meaning=meaning,
        purchase_impact=impact,
        status=status,
        evidence=_evidence_for(term, text),
        seller_question=question,
    )


def _display_term(term: str) -> str:
    if term in {"cpu", "gpu", "ram", "ssd", "tgp"}:
        return term.upper()
    if term == "freedos":
        return "FreeDOS"
    return term


def _unknown_explanation(term: str) -> SpecTermExplanation:
    label = term.strip() or "상품 문구"
    return SpecTermExplanation(
        term=label,
        plain_meaning="상품 문구만으로는 의미를 확정하기 어렵습니다.",
        purchase_impact="정확한 모델명, 옵션명, 보증 조건을 확인해야 잘못된 결제를 줄일 수 있습니다.",
        status=CheckStatus.warning,
        evidence="해석 가능한 표준 용어가 부족함",
        seller_question=f"{label} 문구가 실제 사양과 구매 조건에서 어떤 의미인지 풀어서 알려 주세요.",
    )


def _evidence_for(term: str, text: str) -> str:
    lowered = text.lower()
    related = [term, *[alias for alias, canonical in ALIASES.items() if canonical == term]]
    for token in related:
        if token in lowered or token in text:
            return f"상품 문구에서 '{token}' 확인"
    return "상품명과 입력 용어에서 추정"


def _decoder_status(blocker_count: int, warning_count: int) -> CheckStatus:
    if blocker_count:
        return CheckStatus.blocker
    if warning_count:
        return CheckStatus.warning
    return CheckStatus.ok


def _clarity_score(
    explanations: list[SpecTermExplanation],
    blocker_count: int,
    warning_count: int,
    text: str,
) -> float:
    known_count = sum(1 for item in explanations if item.evidence != "해석 가능한 표준 용어가 부족함")
    base = 48 + known_count * 7 - warning_count * 5 - blocker_count * 15
    if len(text) >= 80:
        base += 8
    return round(min(98, max(15, base)), 1)


def _scanner_prefill(
    request: SpecTermDecoderRequest,
    title: str,
    text: str,
) -> SpecRiskScannerRequest:
    return SpecRiskScannerRequest(
        category=request.category,
        product_title=title,
        option_text=text or title,
        cart_total_krw=None,
        budget_krw=request.budget_krw,
        expected_cpu=_first_match(text, [r"(ryzen\s*[0-9]\s*[0-9a-z]+)", r"(core\s*i[3579][-\s]?[0-9a-z]+)"]),
        expected_gpu=_first_match(text, [r"(rtx\s*[0-9]{4}(?:\s*super)?)", r"(radeon\s*[a-z0-9\s]+)"]),
        expected_ram_gb=_capacity(text, [r"([0-9]{2,3})\s*gb\s*(?:ram|memory|메모리|램)?"]),
        expected_storage_gb=_storage_capacity(text),
        expected_os="Windows 11" if re.search(r"windows?\s*11|윈도우\s*11", text, flags=re.I) else "",
        evidence_text="사양 용어 해석 키트 기반 prefill",
        source="spec_term_decoder",
    )


def _first_match(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _capacity(text: str, patterns: list[str]) -> int | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _storage_capacity(text: str) -> int | None:
    tb = re.search(r"([0-9](?:\.[0-9])?)\s*tb", text, flags=re.IGNORECASE)
    if tb:
        return int(float(tb.group(1)) * 1000)
    return _capacity(text, [r"([0-9]{3,4})\s*gb\s*(?:ssd|nvme|저장|스토리지)?"])


def _headline(title: str, status: CheckStatus) -> str:
    if status == CheckStatus.blocker:
        return f"{title} 문구에서 결제 전 멈춰야 할 용어를 찾았습니다."
    if status == CheckStatus.warning:
        return f"{title} 용어는 쉬운 설명과 판매자 확인이 필요합니다."
    return f"{title} 상품 문구를 초보 구매자용 설명으로 바꿨습니다."


def _seller_questions(explanations: list[SpecTermExplanation]) -> list[str]:
    questions = [item.seller_question for item in explanations]
    questions.append("장바구니 옵션명과 실제 출고 사양이 위 설명과 같은지 확인해 주세요.")
    questions.append("반품, 초기 불량 교환, 국내 AS 조건을 결제 전 문장으로 남겨 주세요.")
    return list(dict.fromkeys(questions))[:7]


def _beginner_checklist(category: Category, risk_terms: list[str]) -> list[str]:
    checklist = [
        "상품명, 옵션명, 결제 화면 총액을 각각 캡처합니다.",
        "CPU/GPU/RAM/SSD/OS가 장바구니 옵션에도 같은지 확인합니다.",
        "Windows 포함 여부와 정품 인증 방식을 확인합니다.",
        "국내 AS, 반품 가능 기간, 초기 불량 교환 조건을 확인합니다.",
    ]
    if category == Category.laptop:
        checklist.append("무게, 배터리, 화면 밝기, USB-C 충전/모니터 출력 조건을 확인합니다.")
    if risk_terms:
        checklist.insert(0, f"위험 용어({', '.join(risk_terms[:4])})는 판매자 답변 전 결제하지 않습니다.")
    return checklist[:6]


def _plain_language_brief(
    *,
    title: str,
    purpose: str,
    explanations: list[SpecTermExplanation],
) -> str:
    impacts = "; ".join(f"{item.term}: {item.purchase_impact}" for item in explanations[:4])
    return f"{title}는 {purpose} 용도로 보기 전에 {impacts}를 확인해야 합니다."


def _analysis_prefill(
    request: SpecTermDecoderRequest,
    title: str,
    explanations: list[SpecTermExplanation],
    scanner_prefill: SpecRiskScannerRequest,
) -> str:
    terms = ", ".join(f"{item.term}({item.status.value})" for item in explanations)
    return (
        f"{_category_label(request.category)} 후보 '{title}'의 상품 문구를 초보자 기준으로 해석했어. "
        f"예산은 {request.budget_krw:,}원, 목적은 {request.primary_purpose}, "
        f"해석 용어는 {terms}야. "
        f"검수 prefill은 CPU {scanner_prefill.expected_cpu or '미확인'}, "
        f"GPU {scanner_prefill.expected_gpu or '미확인'}, "
        f"RAM {scanner_prefill.expected_ram_gb or '미확인'}GB, "
        f"SSD {scanner_prefill.expected_storage_gb or '미확인'}GB야. "
        "이 상품 문구를 그대로 믿고 결제해도 되는지 사양, 보증, 반품, 대체 후보까지 검토해줘."
    )


def _share_copy(title: str, status: CheckStatus, risk_terms: list[str]) -> str:
    risk = f" 위험 용어: {', '.join(risk_terms)}." if risk_terms else ""
    label = "통과" if status == CheckStatus.ok else "확인 필요"
    return f"SpecPilot AI 사양 용어 해석: {title} 문구는 {label}.{risk}"


def _next_actions(status: CheckStatus, risk_terms: list[str]) -> list[str]:
    if status == CheckStatus.blocker:
        return [
            "리퍼/전시/반품 불가 같은 blocker 용어는 판매자 답변 전 결제하지 마세요.",
            "판매자 답변을 캡처한 뒤 옵션/사양 빠른 검수로 다시 확인하세요.",
            "신품/국내 AS 조건의 대체 후보를 하나 이상 비교하세요.",
        ]
    if risk_terms:
        return [
            "warning 용어는 판매자 질문을 복사해 답변을 받은 뒤 결제하세요.",
            "장바구니 옵션명과 최종 결제 금액을 붙여 넣어 빠른 검수를 이어가세요.",
            "Windows, 업그레이드, 반품 조건은 캡처로 남기세요.",
        ]
    return [
        "해석된 사양을 옵션/사양 빠른 검수에 적용하세요.",
        "최종 결제 금액과 판매자 보증 조건을 함께 확인하세요.",
        "결제 전 공유 문구로 가족/팀 검토를 받으세요.",
    ]


def _category_label(category: Category) -> str:
    return "노트북" if category == Category.laptop else "데스크톱 PC"
