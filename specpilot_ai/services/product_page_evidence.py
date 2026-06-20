from datetime import UTC, datetime
from html import escape
from urllib.parse import urlparse

from specpilot_ai.core.models import (
    CheckStatus,
    PriceBreakdownRequest,
    ProductPageEvidenceRequest,
    ProductPageEvidenceSignal,
    PublicProductPageEvidenceKit,
    SellerEvidenceRequest,
    SourceKind,
    SourceUrlIngestRequest,
    SpecRiskScannerRequest,
)
from specpilot_ai.sources.url_ingestion import ingest_source_url


def build_public_product_page_evidence_kit(
    request: ProductPageEvidenceRequest,
    generated_at: datetime | None = None,
) -> PublicProductPageEvidenceKit:
    generated_at = generated_at or datetime.now(UTC)
    title = request.product_title.strip() or request.expected_model.strip() or "구매 후보"
    expected_model = request.expected_model.strip() or title
    response = ingest_source_url(
        SourceUrlIngestRequest(
            url=request.url,
            category=request.category,
            kind=SourceKind.price,
            expected_model=expected_model,
            source_name="public_product_page_evidence",
            seller=request.seller_name.strip() or None,
            html=_html_snapshot(request, title),
        )
    )
    candidate = response.candidate
    effective_price = candidate.effective_price_krw
    budget_delta = effective_price - request.budget_krw if effective_price is not None else None
    combined_risks = _combined_risks(request, candidate.risk_flags)
    score = _evidence_score(request, combined_risks, budget_delta)
    priority = _priority(candidate.model_match_status, candidate.availability_status, score, budget_delta)
    seller = request.seller_name.strip() or candidate.seller or _host(request.url)
    return PublicProductPageEvidenceKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        url=request.url,
        host=_host(request.url),
        product_title=title,
        seller_name=seller,
        priority=priority,
        evidence_score=score,
        extracted_price_krw=candidate.extracted_price_krw,
        shipping_fee_krw=candidate.shipping_fee_krw,
        discount_krw=candidate.coupon_or_card_benefit_krw,
        effective_price_krw=effective_price,
        budget_delta_krw=budget_delta,
        availability_status=candidate.availability_status,
        model_match_status=candidate.model_match_status,
        headline=_headline(title, priority, effective_price, budget_delta),
        summary=_summary(candidate, priority, budget_delta),
        source_signals=_source_signals(request, candidate.model_match_status, candidate.availability_status, budget_delta),
        risk_flags=combined_risks,
        extraction_notes=[
            *response.extraction_notes,
            "공개 키트는 live fetch 없이 사용자가 붙여 넣은 상품 페이지 문구/HTML만 분석합니다.",
            "추천 반영 전에는 내부 source review queue 또는 판매자 답변으로 다시 검수해야 합니다.",
        ],
        evidence_checklist=_evidence_checklist(),
        seller_questions=_seller_questions(request, candidate.availability_status, combined_risks),
        scanner_prefill=_scanner_prefill(request, title, candidate.evidence_text, effective_price),
        price_prefill=_price_prefill(request, title, seller, candidate),
        seller_evidence_prefill=_seller_evidence_prefill(
            request,
            title,
            seller,
            priority,
            effective_price,
            combined_risks,
        ),
        analysis_prefill=_analysis_prefill(request, title, priority, effective_price, budget_delta),
        share_copy=_share_copy(request, title, priority, candidate.availability_status, effective_price, budget_delta),
        next_actions=_next_actions(priority),
    )


def _html_snapshot(request: ProductPageEvidenceRequest, title: str) -> str:
    html = request.html_snapshot.strip()
    if html:
        return html
    body = request.page_text.strip()
    if not body:
        body = (
            f"{title} 상품 페이지 문구 미입력. 가격, 배송비, 할인, 재고, 반품/AS 조건을 "
            "붙여 넣어야 근거 점수가 올라갑니다."
        )
    return f"<html><title>{escape(title)}</title><body>{escape(body)}</body></html>"


def _host(url: str) -> str:
    return urlparse(url).hostname or "unknown-host"


def _combined_risks(request: ProductPageEvidenceRequest, source_risks: list[str]) -> list[str]:
    risks = list(dict.fromkeys([*source_risks, *[risk.strip() for risk in request.risk_terms if risk.strip()]]))
    text = f"{request.page_text} {request.html_snapshot} {' '.join(request.risk_terms)}".lower()
    for keyword, label in [
        ("리퍼", "리퍼 조건"),
        ("전시", "전시 상품 조건"),
        ("중고", "중고 조건"),
        ("해외", "해외/병행 수입 조건"),
        ("병행", "해외/병행 수입 조건"),
        ("반품 불가", "반품 불가 조건"),
        ("as 불가", "AS 불가 조건"),
        ("보증 없음", "보증 없음"),
        ("freedos", "FreeDOS OS 비용 확인 필요"),
        ("free dos", "FreeDOS OS 비용 확인 필요"),
    ]:
        if keyword in text and label not in risks:
            risks.append(label)
    return risks[:10]


def _evidence_score(
    request: ProductPageEvidenceRequest,
    risk_flags: list[str],
    budget_delta: int | None,
) -> float:
    text = f"{request.page_text} {request.html_snapshot}".lower()
    score = 100.0
    if "가격 추출 실패" in risk_flags:
        score -= 22
    if "배송비 확인 필요" in risk_flags:
        score -= 8
    if any("모델명 부분" in risk or "검수 필요" in risk for risk in risk_flags):
        score -= 10
    if any("불일치" in risk for risk in risk_flags):
        score -= 32
    if any("품절" in risk or "판매 종료" in risk for risk in risk_flags):
        score -= 30
    if any("재고 부족" in risk for risk in risk_flags):
        score -= 10
    if any("미확인" in risk for risk in risk_flags):
        score -= 6
    if any(term in " ".join(risk_flags) for term in ("리퍼", "전시", "중고", "해외", "반품 불가", "AS 불가", "보증 없음")):
        score -= 16
    if budget_delta is not None and budget_delta > 0:
        score -= 20 if budget_delta > max(80_000, request.budget_krw * 0.05) else 10
    if not text.strip():
        score -= 20
    return round(max(0.0, min(100.0, score)), 1)


def _priority(
    model_match: CheckStatus,
    availability: str,
    score: float,
    budget_delta: int | None,
) -> CheckStatus:
    if model_match == CheckStatus.blocker or availability == "sold_out" or score < 60:
        return CheckStatus.blocker
    if score < 84 or model_match == CheckStatus.warning or availability in {"unknown", "low_stock"}:
        return CheckStatus.warning
    if budget_delta is not None and budget_delta > 0:
        return CheckStatus.warning
    return CheckStatus.ok


def _source_signals(
    request: ProductPageEvidenceRequest,
    model_match: CheckStatus,
    availability: str,
    budget_delta: int | None,
) -> list[ProductPageEvidenceSignal]:
    signals = [
        ProductPageEvidenceSignal(
            signal_id="url_safety",
            label="URL 안전성",
            status=CheckStatus.ok,
            evidence=f"{_host(request.url)} 공개 URL 형식 통과",
            recommendation="사용자 정보가 들어간 URL이나 내부망 URL은 공개 키트에서도 차단합니다.",
        ),
        ProductPageEvidenceSignal(
            signal_id="model_match",
            label="모델명 일치",
            status=model_match,
            evidence=request.expected_model or request.product_title,
            recommendation="기대 모델명과 페이지 제목/본문의 CPU, GPU, 모델 토큰이 맞는지 캡처하세요.",
        ),
        ProductPageEvidenceSignal(
            signal_id="availability",
            label="재고 상태",
            status=CheckStatus.ok if availability == "in_stock" else CheckStatus.warning,
            evidence=availability,
            recommendation="재고 있음, 품절, 마감 임박 문구를 결제 전 화면 기준으로 다시 확인하세요.",
        ),
    ]
    if budget_delta is not None:
        signals.append(
            ProductPageEvidenceSignal(
                signal_id="budget_fit",
                label="예산 적합",
                status=CheckStatus.ok if budget_delta <= 0 else CheckStatus.warning,
                evidence=f"예산 대비 {budget_delta:+,}원",
                recommendation="실구매가가 예산보다 높으면 가격 협상 또는 대체 후보 비교로 넘기세요.",
            )
        )
    return signals


def _headline(
    title: str,
    priority: CheckStatus,
    effective_price: int | None,
    budget_delta: int | None,
) -> str:
    price = "가격 미확인" if effective_price is None else f"추정 실구매가 {effective_price:,}원"
    if priority == CheckStatus.blocker:
        return f"{title} 상품 페이지는 {price} 기준으로 결제 전 근거 보강이 필요합니다."
    if priority == CheckStatus.warning:
        return f"{title} 상품 페이지는 {price}와 판매자 조건을 다시 확인하세요."
    if budget_delta is not None and budget_delta <= 0:
        return f"{title} 상품 페이지는 예산 안에서 검수 흐름으로 넘길 수 있습니다."
    return f"{title} 상품 페이지 근거를 분석 흐름으로 넘길 수 있습니다."


def _summary(candidate, priority: CheckStatus, budget_delta: int | None) -> str:
    budget = "예산 차이 미확인" if budget_delta is None else f"예산 대비 {budget_delta:+,}원"
    return (
        f"가격 {candidate.extracted_price_krw}, 배송비 {candidate.shipping_fee_krw}, "
        f"할인 {candidate.coupon_or_card_benefit_krw}, 재고 {candidate.availability_status}, "
        f"모델 일치 {candidate.model_match_status.value}, {budget}. 상태 {priority.value}."
    )


def _evidence_checklist() -> list[str]:
    return [
        "상품 페이지 URL과 판매자명 캡처",
        "상품명, 옵션명, CPU/GPU/RAM/SSD/OS 문구 캡처",
        "표시가, 배송비, 쿠폰/카드 할인, 최종 결제 금액 캡처",
        "재고, 출고 예정일, 품절/마감 임박 문구 캡처",
        "반품/교환/AS 정책과 리퍼/전시/해외/FreeDOS 조건 캡처",
    ]


def _seller_questions(
    request: ProductPageEvidenceRequest,
    availability: str,
    risk_flags: list[str],
) -> list[str]:
    questions = [
        "상품 페이지의 실제 출고 사양이 옵션명과 동일한가요?",
        "최종 결제 금액에 배송비, 조립비, OS 비용, 쿠폰/카드 할인이 모두 반영되나요?",
        "현재 재고와 실제 출고 예정일을 확인할 수 있나요?",
        "개봉 전/개봉 후 반품, 초기 불량 교환, 제조사/판매자 AS 기준은 무엇인가요?",
    ]
    if availability in {"unknown", "low_stock", "sold_out"}:
        questions.append("재고 상태가 바뀌면 같은 가격과 같은 옵션으로 주문이 유지되나요?")
    if request.expected_os.lower() in {"", "freedos", "free dos"} or any("FreeDOS" in risk for risk in risk_flags):
        questions.append("Windows 포함 여부와 OS 설치/라이선스 비용을 최종가에 포함했나요?")
    if any(term in " ".join(risk_flags) for term in ("리퍼", "전시", "중고", "해외", "병행")):
        questions.append("리퍼/전시/중고/해외 조건이면 보증, 반품, 추가 비용 예외를 항목별로 알려주세요.")
    return questions[:7]


def _scanner_prefill(
    request: ProductPageEvidenceRequest,
    title: str,
    evidence_text: str,
    effective_price: int | None,
) -> SpecRiskScannerRequest:
    return SpecRiskScannerRequest(
        category=request.category,
        product_title=title,
        option_text=request.expected_model or title,
        cart_total_krw=effective_price,
        budget_krw=request.budget_krw,
        expected_cpu=request.expected_cpu,
        expected_gpu=request.expected_gpu,
        expected_ram_gb=request.expected_ram_gb,
        expected_storage_gb=request.expected_storage_gb,
        expected_os=request.expected_os,
        evidence_text=evidence_text[:500],
        source="product_page_evidence",
    )


def _price_prefill(request: ProductPageEvidenceRequest, title: str, seller: str, candidate) -> PriceBreakdownRequest:
    return PriceBreakdownRequest(
        category=request.category,
        product_title=title,
        seller_name=seller,
        listed_price_krw=candidate.extracted_price_krw or request.budget_krw,
        quantity=1,
        shipping_fee_krw=candidate.shipping_fee_krw or 0,
        coupon_discount_krw=candidate.coupon_or_card_benefit_krw or 0,
        budget_krw=request.budget_krw,
        expected_report_price_krw=candidate.effective_price_krw,
        risk_terms=request.risk_terms,
        source="product_page_evidence",
    )


def _seller_evidence_prefill(
    request: ProductPageEvidenceRequest,
    title: str,
    seller: str,
    priority: CheckStatus,
    effective_price: int | None,
    risk_flags: list[str],
) -> SellerEvidenceRequest:
    verdict = "hold" if priority == CheckStatus.blocker else "verify" if priority == CheckStatus.warning else "ready"
    return SellerEvidenceRequest(
        category=request.category,
        product_title=title,
        seller_name=seller,
        verdict=verdict,
        budget_krw=request.budget_krw,
        cart_total_krw=effective_price,
        risk_terms=risk_flags[:6],
        missing_evidence=["실제 출고 사양", "배송 예정일", "반품 조건", "AS 조건"],
        must_confirm=["페이지 가격과 최종 결제 금액 일치", "재고와 출고 예정일"],
        source="product_page_evidence",
    )


def _analysis_prefill(
    request: ProductPageEvidenceRequest,
    title: str,
    priority: CheckStatus,
    effective_price: int | None,
    budget_delta: int | None,
) -> str:
    return (
        f"상품 페이지 근거 인입 결과를 기준으로 '{title}' 구매 가능 여부를 분석해줘. "
        f"URL {request.url}, 예산 {request.budget_krw:,}원, 추정 실구매가 {effective_price}, "
        f"예산 차이 {budget_delta}, 상태 {priority.value}. "
        "상품명/옵션명/가격/배송/재고/반품/AS 근거를 검수하고 TOP 3 대체 후보도 비교해줘."
    )


def _share_copy(
    request: ProductPageEvidenceRequest,
    title: str,
    priority: CheckStatus,
    availability: str,
    effective_price: int | None,
    budget_delta: int | None,
) -> str:
    price = "미확인" if effective_price is None else f"{effective_price:,}원"
    budget = "미확인" if budget_delta is None else f"{budget_delta:+,}원"
    return (
        "SpecPilot AI 상품 페이지 근거 인입 키트\n"
        f"제품: {title}\n"
        f"URL: {request.url}\n"
        f"상태: {priority.value}\n"
        f"추정 실구매가: {price}\n"
        f"예산 차이: {budget}\n"
        f"재고: {availability}"
    )


def _next_actions(priority: CheckStatus) -> list[str]:
    if priority == CheckStatus.blocker:
        return [
            "가격, 모델명, 재고, 반품/AS 근거가 닫히기 전 결제하지 마세요.",
            "판매자 증거 요청 키트로 실제 출고 사양과 조건 답변을 먼저 받으세요.",
            "대체 후보 rescue 키트로 같은 예산의 안전 후보를 비교하세요.",
        ]
    if priority == CheckStatus.warning:
        return [
            "최종 결제 화면 캡처와 판매자 답변을 추가해 warning을 줄이세요.",
            "실구매가 분해와 판매자 조건 협상 키트로 가격/조건을 분리하세요.",
            "분석 prefill로 전체 구매 리포트를 생성하세요.",
        ]
    return [
        "상품 페이지 캡처를 저장하고 옵션/사양 빠른 검수로 넘기세요.",
        "실구매가 분해 키트로 결제 화면 금액을 다시 대조하세요.",
        "구매 실행 패키지로 결제 전 마지막 중단 조건을 확인하세요.",
    ]
