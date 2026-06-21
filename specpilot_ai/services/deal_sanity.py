from datetime import UTC, datetime

from specpilot_ai.core.models import (
    CheckStatus,
    DealSanityFlag,
    DealSanityRequest,
    PriceBreakdownRequest,
    PublicDealSanityKit,
)


def build_public_deal_sanity_kit(
    request: DealSanityRequest,
    generated_at: datetime | None = None,
) -> PublicDealSanityKit:
    generated_at = generated_at or datetime.now(UTC)
    title = _title(request)
    seller = _seller(request)
    effective_price = _effective_price(request)
    savings = _savings(request, effective_price)
    savings_rate = _savings_rate(request, savings)
    flags = _sanity_flags(request, effective_price, savings, savings_rate)
    score = _sanity_score(request, flags, savings_rate)
    status = _deal_status(score, flags)
    price_prefill = _price_prefill(request)
    return PublicDealSanityKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=title,
        seller_name=seller,
        deal_status=status,
        sanity_score=score,
        effective_price_krw=effective_price,
        savings_krw=savings,
        savings_rate_percent=savings_rate,
        headline=_headline(title, status, score),
        summary=_summary(request, effective_price, savings, savings_rate, status),
        sanity_flags=flags,
        seller_questions=_seller_questions(request, flags),
        evidence_checklist=_evidence_checklist(request),
        checkout_stop_rules=_checkout_stop_rules(status, flags),
        price_prefill=price_prefill,
        analysis_prefill=_analysis_prefill(request, status, effective_price, flags),
        share_copy=_share_copy(request, status, score, effective_price, savings_rate),
        next_actions=_next_actions(status, flags),
    )


def _title(request: DealSanityRequest) -> str:
    return request.product_title.strip() or "특가 후보"


def _seller(request: DealSanityRequest) -> str:
    return request.seller_name.strip() or "판매자"


def _effective_price(request: DealSanityRequest) -> int:
    discounts = request.coupon_discount_krw + request.card_discount_krw + request.point_rebate_krw
    return max(0, request.listed_price_krw + request.shipping_fee_krw - discounts)


def _savings(request: DealSanityRequest, effective_price: int) -> int | None:
    if request.reference_price_krw is None:
        return None
    return request.reference_price_krw - effective_price


def _savings_rate(request: DealSanityRequest, savings: int | None) -> float | None:
    if savings is None or not request.reference_price_krw:
        return None
    return round(savings / request.reference_price_krw * 100, 1)


def _risk_text(request: DealSanityRequest) -> str:
    return " ".join([*request.risk_terms, request.evidence_text]).casefold()


def _sanity_flags(
    request: DealSanityRequest,
    effective_price: int,
    savings: int | None,
    savings_rate: float | None,
) -> list[DealSanityFlag]:
    flags: list[DealSanityFlag] = []
    text = _risk_text(request)
    if request.reference_price_krw is None:
        flags.append(
            _flag(
                "missing_reference_price",
                "기준가 부재",
                CheckStatus.warning,
                "정상가나 최근 평균가가 없어 할인율을 검증하기 어렵습니다.",
                "가격비교 최저가, 최근 평균가, 공식몰 가격 중 하나를 기준가로 캡처하세요.",
            )
        )
    elif savings is not None and savings <= 0:
        flags.append(
            _flag(
                "not_discounted",
                "실질 할인 없음",
                CheckStatus.warning,
                f"실구매가가 기준가보다 {abs(savings):,}원 높거나 같습니다.",
                "가격 타이밍 윈도우와 목표가 감시 기준을 먼저 확인하세요.",
            )
        )
    elif savings_rate is not None and savings_rate >= 28:
        flags.append(
            _flag(
                "too_deep_discount",
                "과도한 할인율",
                CheckStatus.warning,
                f"기준가 대비 {savings_rate}% 할인으로 조건 누락 가능성이 있습니다.",
                "리퍼, 해외 병행, 반품 불가, 청구 할인 조건을 결제 전 확인하세요.",
            )
        )
    elif savings_rate is not None and savings_rate >= 8:
        flags.append(
            _flag(
                "meaningful_discount",
                "유의미한 할인",
                CheckStatus.ok,
                f"기준가 대비 {savings_rate}% 절감입니다.",
                "같은 사양, 같은 AS, 같은 반품 조건인지 대조하면 비교할 가치가 있습니다.",
            )
        )

    if request.lowest_seen_price_krw is not None:
        delta = effective_price - request.lowest_seen_price_krw
        if delta > max(50_000, request.lowest_seen_price_krw * 0.04):
            flags.append(
                _flag(
                    "above_lowest_seen",
                    "최근 최저가보다 높음",
                    CheckStatus.warning,
                    f"최근 최저가보다 {delta:,}원 높습니다.",
                    "급하지 않으면 목표가 감시로 전환하고 대체 후보를 비교하세요.",
                )
            )

    hard_terms = ["반품 불가", "as 불가", "a/s 불가", "보증 없음", "해외", "리퍼", "전시", "중고"]
    matched_hard = [term for term in hard_terms if term in text]
    if matched_hard:
        flags.append(
            _flag(
                "hard_condition_terms",
                "강한 위험 조건",
                CheckStatus.blocker,
                f"위험 문구가 감지됐습니다: {', '.join(matched_hard[:4])}",
                "국내 AS, 반품 가능일, 새 제품 여부가 명확하지 않으면 결제를 멈추세요.",
            )
        )

    if any(term in text for term in ["청구 할인", "조건부", "앱전용", "회원전용", "선착순", "타임딜"]):
        flags.append(
            _flag(
                "conditional_discount",
                "조건부 할인",
                CheckStatus.warning,
                "카드, 앱, 회원 등급, 선착순 조건에 묶인 할인일 수 있습니다.",
                "실제 결제 화면에서 할인 적용 후 총액을 캡처하세요.",
            )
        )

    if request.warranty_months is not None and request.warranty_months < 12:
        flags.append(
            _flag(
                "short_warranty",
                "짧은 보증",
                CheckStatus.blocker if request.warranty_months == 0 else CheckStatus.warning,
                f"보증 기간이 {request.warranty_months}개월입니다.",
                "제조사/판매자 보증 주체와 보증 승계 가능 여부를 확인하세요.",
            )
        )

    if request.return_window_days is not None and request.return_window_days < 7:
        flags.append(
            _flag(
                "short_return_window",
                "짧은 반품 기간",
                CheckStatus.blocker if request.return_window_days == 0 else CheckStatus.warning,
                f"반품 가능 기간이 {request.return_window_days}일입니다.",
                "개봉 후 반품, 초기 불량 예외, 반품 비용을 판매자에게 확인하세요.",
            )
        )

    if request.seller_rating_percent is not None and request.seller_rating_percent < 92:
        flags.append(
            _flag(
                "seller_rating_low",
                "판매자 평점 낮음",
                CheckStatus.warning,
                f"판매자 평점이 {request.seller_rating_percent:.1f}%입니다.",
                "최근 불만 리뷰와 배송/교환 응답 이력을 확인하세요.",
            )
        )

    if request.stock_count is not None and request.stock_count <= 3:
        flags.append(
            _flag(
                "low_stock",
                "낮은 재고",
                CheckStatus.warning,
                f"재고가 {request.stock_count}개로 표시됩니다.",
                "결제 직전 옵션명, 판매자, 가격이 바뀌지 않았는지 체크아웃 잠금을 실행하세요.",
            )
        )

    if request.discount_expires_hours is not None and request.discount_expires_hours <= 6:
        flags.append(
            _flag(
                "expires_soon",
                "할인 임박",
                CheckStatus.warning,
                f"할인 만료까지 {request.discount_expires_hours}시간 남았습니다.",
                "충동 결제를 막기 위해 필수 증거 4개를 먼저 캡처하세요.",
            )
        )

    if request.budget_krw is not None and effective_price > request.budget_krw:
        flags.append(
            _flag(
                "over_budget",
                "예산 초과",
                CheckStatus.blocker,
                f"실구매가가 예산보다 {effective_price - request.budget_krw:,}원 높습니다.",
                "예산 초과 승인 없이는 결제를 보류하고 대체 후보를 비교하세요.",
            )
        )

    if not flags:
        flags.append(
            _flag(
                "sanity_clear",
                "기본 조건 통과",
                CheckStatus.ok,
                "입력된 특가 조건에서 즉시 차단할 위험 신호는 크지 않습니다.",
                "상품명, 옵션명, 총액, 보증/반품 증거를 캡처한 뒤 후보 비교로 넘어가세요.",
            )
        )
    return flags[:8]


def _flag(
    flag_id: str,
    label: str,
    status: CheckStatus,
    evidence: str,
    recommendation: str,
) -> DealSanityFlag:
    return DealSanityFlag(
        flag_id=flag_id,
        label=label,
        status=status,
        evidence=evidence,
        recommendation=recommendation,
    )


def _sanity_score(
    request: DealSanityRequest,
    flags: list[DealSanityFlag],
    savings_rate: float | None,
) -> int:
    score = 88
    if savings_rate is not None:
        if 5 <= savings_rate <= 22:
            score += 8
        elif savings_rate >= 35:
            score -= 10
    for flag in flags:
        score -= 22 if flag.status == CheckStatus.blocker else 9 if flag.status == CheckStatus.warning else 0
    if request.review_count is not None and request.review_count >= 100:
        score += 4
    return max(0, min(100, score))


def _deal_status(score: int, flags: list[DealSanityFlag]) -> CheckStatus:
    if score < 58 or any(flag.status == CheckStatus.blocker for flag in flags):
        return CheckStatus.blocker
    if score < 82 or any(flag.status == CheckStatus.warning for flag in flags):
        return CheckStatus.warning
    return CheckStatus.ok


def _price_prefill(request: DealSanityRequest) -> PriceBreakdownRequest:
    return PriceBreakdownRequest(
        category=request.category,
        product_title=_title(request),
        seller_name=_seller(request),
        listed_price_krw=request.listed_price_krw,
        quantity=1,
        shipping_fee_krw=request.shipping_fee_krw,
        coupon_discount_krw=request.coupon_discount_krw,
        card_discount_krw=request.card_discount_krw,
        point_rebate_krw=request.point_rebate_krw,
        budget_krw=request.budget_krw,
        expected_report_price_krw=request.reference_price_krw,
        discount_expires_hours=request.discount_expires_hours,
        stock_count=request.stock_count,
        risk_terms=request.risk_terms,
        source="deal_sanity",
    )


def _headline(title: str, status: CheckStatus, score: int) -> str:
    if status == CheckStatus.blocker:
        return f"{title} 특가는 {score}점, 결제 전에 차단 조건을 먼저 닫아야 합니다."
    if status == CheckStatus.warning:
        return f"{title} 특가는 {score}점, 할인 조건과 보증/반품 증거를 재확인하세요."
    return f"{title} 특가는 {score}점, 후보 비교에 올려볼 만합니다."


def _summary(
    request: DealSanityRequest,
    effective_price: int,
    savings: int | None,
    savings_rate: float | None,
    status: CheckStatus,
) -> str:
    saving_text = "기준가 미입력" if savings is None else f"기준가 대비 {savings:+,}원"
    rate_text = "" if savings_rate is None else f" ({savings_rate:+.1f}%)"
    return (
        f"{_seller(request)} 기준 실구매가 {effective_price:,}원, {saving_text}{rate_text}. "
        f"현재 특가 안전성 상태는 {status.value}입니다."
    )


def _seller_questions(
    request: DealSanityRequest,
    flags: list[DealSanityFlag],
) -> list[str]:
    questions = [
        "해당 가격이 최종 결제 화면에서도 같은 상품명, 같은 옵션, 같은 판매자로 유지되나요?",
        "쿠폰/카드/포인트 할인이 특정 카드, 앱, 회원 등급, 청구 할인 조건에 묶여 있나요?",
        "제조사 또는 판매자 보증 기간과 국내 AS 주체를 확인할 수 있나요?",
        "반품 가능 기간, 개봉 후 반품 제한, 초기 불량 예외가 어떻게 되나요?",
    ]
    if any(flag.flag_id == "hard_condition_terms" for flag in flags):
        questions.insert(0, "리퍼, 전시, 해외 병행, 중고, 반품 불가 조건이 맞는지 명확히 답변해 주세요.")
    if request.reference_price_krw is None:
        questions.append("비교 기준가로 볼 공식몰 가격 또는 최근 가격비교 최저가를 제시할 수 있나요?")
    return questions[:6]


def _evidence_checklist(request: DealSanityRequest) -> list[str]:
    return [
        "상품명, 모델명, 옵션명, 판매자명이 한 화면에 보이는 캡처",
        "최종 결제 금액, 배송비, 쿠폰/카드/포인트 적용 조건 캡처",
        "기준가 또는 최근 가격비교 최저가 캡처",
        "보증 기간, 국내 AS 주체, 반품 가능 기간 캡처",
        "재고 수량, 할인 만료 시각, 조건부 할인 문구 캡처",
    ]


def _checkout_stop_rules(
    status: CheckStatus,
    flags: list[DealSanityFlag],
) -> list[str]:
    rules = [
        "최종 결제 화면 총액이 검수 금액보다 오르면 결제를 멈춥니다.",
        "상품명/옵션명/판매자가 바뀌면 체크아웃 잠금을 다시 실행합니다.",
        "보증/반품 조건이 캡처되지 않으면 구매 승인 브리프로 넘기지 않습니다.",
    ]
    if status == CheckStatus.blocker:
        rules.insert(0, "blocker 플래그가 남아 있으면 특가라도 결제하지 않습니다.")
    if any(flag.flag_id == "conditional_discount" for flag in flags):
        rules.append("청구 할인은 카드 승인 전 최종 부담액이 확정되지 않으면 할인으로 보지 않습니다.")
    return rules[:6]


def _analysis_prefill(
    request: DealSanityRequest,
    status: CheckStatus,
    effective_price: int,
    flags: list[DealSanityFlag],
) -> str:
    return (
        "SpecPilot AI 특가 안전성 검수 기준으로 구매 후보를 분석해줘.\n"
        f"- 제품: {_title(request)}\n"
        f"- 판매자: {_seller(request)}\n"
        f"- 실구매가: {effective_price:,}원\n"
        f"- 기준가: {request.reference_price_krw if request.reference_price_krw is not None else '미입력'}\n"
        f"- 상태: {status.value}\n"
        f"- 위험 신호: {', '.join(flag.label for flag in flags) or '없음'}"
    )


def _share_copy(
    request: DealSanityRequest,
    status: CheckStatus,
    score: int,
    effective_price: int,
    savings_rate: float | None,
) -> str:
    rate = "기준가 미입력" if savings_rate is None else f"{savings_rate:+.1f}%"
    return (
        "SpecPilot AI 특가 안전성 검수\n"
        f"- 제품: {_title(request)}\n"
        f"- 판매자: {_seller(request)}\n"
        f"- 실구매가: {effective_price:,}원\n"
        f"- 할인율: {rate}\n"
        f"- 점수/상태: {score}점 / {status.value}"
    )


def _next_actions(status: CheckStatus, flags: list[DealSanityFlag]) -> list[str]:
    if status == CheckStatus.blocker:
        return [
            "blocker 플래그의 증거가 닫히기 전에는 결제하지 않습니다.",
            "판매자 증거 요청 키트로 보증/반품/리퍼 여부를 먼저 확인합니다.",
            "같은 예산의 대체 후보를 커스텀 후보 비교에 올립니다.",
        ]
    if status == CheckStatus.warning:
        return [
            flags[0].recommendation if flags else "할인 조건을 캡처하세요.",
            "실구매가 분해 키트로 최종 결제 금액을 다시 계산합니다.",
            "가격 타이밍/목표가 감시 기준과 비교해 지금 살지 대기할지 결정합니다.",
        ]
    return [
        "후보 비교 스냅샷에 올려 성능/AS/반품 조건까지 비교합니다.",
        "최종 결제 직전 체크아웃 잠금으로 상품명과 금액을 다시 대조합니다.",
        "공유 문구를 가족/커뮤니티에 보내 빠진 위험 조건을 확인받습니다.",
    ]
