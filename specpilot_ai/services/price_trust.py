from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    CheckStatus,
    PriceTrustCandidate,
    PriceTrustCandidateInput,
    PriceTrustCheck,
    PriceTrustMessage,
    PriceTrustRequest,
    PublicPriceTrustKit,
)


def build_public_price_trust_kit(
    request: PriceTrustRequest,
    generated_at: datetime | None = None,
) -> PublicPriceTrustKit:
    generated_at = generated_at or datetime.now(UTC)
    title = request.product_title.strip() or _fallback_title(request.category)
    raw_candidates = request.candidates or [_fallback_candidate(title)]
    candidates = [_candidate(item, index) for index, item in enumerate(raw_candidates[:6], start=1)]
    selected = _selected_candidate(request, candidates)
    checks = _checks(request, candidates, selected)
    status = _status(checks, candidates)
    score = _score(checks, candidates)
    delta = None
    if selected and request.report_price_krw is not None:
        delta = selected.effective_price_krw - request.report_price_krw
    buyer_warning = _buyer_warning(status, selected, delta)
    return PublicPriceTrustKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=title,
        trust_status=status,
        trust_score=score,
        selected_effective_price_krw=selected.effective_price_krw if selected else None,
        report_price_delta_krw=delta,
        headline=_headline(title, status),
        summary=_summary(status, score, selected, delta),
        candidates=candidates,
        checks=checks,
        evidence_checklist=_evidence_checklist(),
        disclosure_notes=_disclosure_notes(candidates),
        buyer_warning=buyer_warning,
        messages=_messages(title, status, buyer_warning, checks),
        analysis_prefill=_analysis_prefill(request, title, status, selected, delta),
        share_copy=_share_copy(title, status, score, selected, delta, checks),
        next_actions=_next_actions(status, checks),
    )


def _fallback_title(category: Category) -> str:
    return "노트북 가격 후보" if category == Category.laptop else "컴퓨터 가격 후보"


def _fallback_candidate(title: str) -> PriceTrustCandidateInput:
    return PriceTrustCandidateInput(
        source_name="가격비교",
        product_title=title,
        screenshot_captured=False,
        checkout_price_verified=False,
        url_verified=False,
    )


def _effective_price(item: PriceTrustCandidateInput) -> int:
    discounts = item.coupon_discount_krw + item.card_discount_krw + item.point_rebate_krw
    return max(0, item.listed_price_krw + item.shipping_fee_krw - discounts)


def _freshness_status(minutes: int | None) -> CheckStatus:
    if minutes is None:
        return CheckStatus.warning
    if minutes > 180:
        return CheckStatus.blocker
    if minutes > 45:
        return CheckStatus.warning
    return CheckStatus.ok


def _freshness_label(minutes: int | None) -> str:
    if minutes is None:
        return "캡처 시각 미입력"
    if minutes < 60:
        return f"{minutes}분 전"
    hours = minutes / 60
    return f"{hours:.1f}시간 전"


def _candidate(item: PriceTrustCandidateInput, index: int) -> PriceTrustCandidate:
    status = _candidate_status(item)
    notes = _clean(item.condition_notes, 3)
    evidence_parts = [
        f"표시가 {item.listed_price_krw:,}원",
        f"배송비 {item.shipping_fee_krw:,}원",
        f"캡처 {_freshness_label(item.captured_minutes_ago)}",
    ]
    if notes:
        evidence_parts.append(f"조건: {', '.join(notes)}")
    return PriceTrustCandidate(
        candidate_id=f"price_source_{index}",
        source_name=item.source_name.strip() or "가격 출처",
        seller_name=item.seller_name.strip() or "판매자",
        effective_price_krw=_effective_price(item),
        freshness_label=_freshness_label(item.captured_minutes_ago),
        status=status,
        evidence=" · ".join(evidence_parts),
        recommendation=_candidate_recommendation(item, status),
        affiliate_link=item.affiliate_link,
        non_affiliate_available=item.non_affiliate_available,
    )


def _candidate_status(item: PriceTrustCandidateInput) -> CheckStatus:
    blockers = [
        _freshness_status(item.captured_minutes_ago) == CheckStatus.blocker,
        item.stock_count == 0,
        item.affiliate_link and not item.non_affiliate_available,
    ]
    if any(blockers):
        return CheckStatus.blocker
    warnings = [
        _freshness_status(item.captured_minutes_ago) == CheckStatus.warning,
        not item.screenshot_captured,
        not item.checkout_price_verified,
        not item.url_verified,
        item.stock_count is not None and item.stock_count <= 3,
        bool(_risk_terms(item.condition_notes)),
    ]
    if any(warnings):
        return CheckStatus.warning
    return CheckStatus.ok


def _candidate_recommendation(item: PriceTrustCandidateInput, status: CheckStatus) -> str:
    if item.affiliate_link and not item.non_affiliate_available:
        return "제휴 링크만 있으면 추천 근거로 쓰지 말고 같은 후보의 비제휴 판매처를 함께 확보하세요."
    if _freshness_status(item.captured_minutes_ago) == CheckStatus.blocker:
        return "3시간 넘은 가격은 결제 판단에서 제외하고 현재 장바구니 금액을 다시 캡처하세요."
    if item.stock_count == 0:
        return "품절 후보는 가격 비교에서 제외하고 대체 판매자 또는 대체 후보를 찾으세요."
    if status == CheckStatus.warning:
        return "결제 화면 총액, 판매자, 배송비, 쿠폰 적용 후 금액을 다시 캡처하세요."
    return "가격, 출처, 캡처 증거가 결제 전 공유 가능한 상태입니다."


def _selected_candidate(
    request: PriceTrustRequest,
    candidates: list[PriceTrustCandidate],
) -> PriceTrustCandidate | None:
    if not candidates:
        return None
    seller = request.selected_seller_name.strip().casefold()
    if seller:
        for item in candidates:
            if item.seller_name.casefold() == seller:
                return item
    return sorted(candidates, key=lambda item: (item.status != CheckStatus.ok, item.effective_price_krw))[0]


def _checks(
    request: PriceTrustRequest,
    candidates: list[PriceTrustCandidate],
    selected: PriceTrustCandidate | None,
) -> list[PriceTrustCheck]:
    checks = [
        _freshness_check(candidates),
        _source_diversity_check(candidates),
        _affiliate_neutrality_check(candidates),
        _evidence_check(candidates),
    ]
    if selected:
        checks.append(_selected_price_check(request, selected))
    return checks


def _freshness_check(candidates: list[PriceTrustCandidate]) -> PriceTrustCheck:
    stale = [item for item in candidates if item.status == CheckStatus.blocker and "3시간" in item.recommendation]
    warning = [item for item in candidates if "다시 캡처" in item.recommendation]
    if stale:
        return _check(
            "freshness",
            "가격 캡처 시각",
            CheckStatus.blocker,
            f"{len(stale)}개 출처가 3시간을 넘었거나 현재가 확인이 부족합니다.",
            "결제 전 45분 이내 캡처로 교체하세요.",
        )
    if warning:
        return _check(
            "freshness",
            "가격 캡처 시각",
            CheckStatus.warning,
            f"{len(warning)}개 출처는 결제 화면 재확인이 필요합니다.",
            "장바구니 총액 캡처와 상품 페이지 캡처를 함께 저장하세요.",
        )
    return _check("freshness", "가격 캡처 시각", CheckStatus.ok, "모든 후보가 최신 가격 근거를 갖췄습니다.", "현재 스냅샷을 공유 기준으로 저장하세요.")


def _source_diversity_check(candidates: list[PriceTrustCandidate]) -> PriceTrustCheck:
    source_names = {item.source_name.casefold() for item in candidates}
    seller_names = {item.seller_name.casefold() for item in candidates}
    if len(candidates) < 2 or len(source_names) < 2:
        return _check(
            "source_diversity",
            "출처 다양성",
            CheckStatus.warning,
            "가격 출처가 2개 미만이라 가격 비교 근거가 약합니다.",
            "가격비교, 공식몰, 판매자 장바구니 중 최소 2개를 캡처하세요.",
        )
    if len(seller_names) < 2:
        return _check(
            "source_diversity",
            "판매자 다양성",
            CheckStatus.warning,
            "판매자가 하나뿐이라 재고/정책 리스크를 분산하지 못합니다.",
            "동일 후보의 다른 판매자 또는 공식몰 가격을 함께 확인하세요.",
        )
    return _check("source_diversity", "출처 다양성", CheckStatus.ok, "복수 출처와 판매자 비교가 가능합니다.", "최저가와 공식/비제휴 대안을 함께 보관하세요.")


def _affiliate_neutrality_check(candidates: list[PriceTrustCandidate]) -> PriceTrustCheck:
    affiliate = [item for item in candidates if item.affiliate_link]
    blocked = [item for item in affiliate if not item.non_affiliate_available]
    if blocked:
        return _check(
            "affiliate_neutrality",
            "제휴 중립성",
            CheckStatus.blocker,
            "제휴 링크 후보에 비제휴 대안이 없습니다.",
            "추천 순위 근거에서 제외하거나 같은 후보의 비제휴 판매처를 함께 제시하세요.",
        )
    if affiliate:
        return _check(
            "affiliate_neutrality",
            "제휴 중립성",
            CheckStatus.warning,
            "제휴 링크가 포함되어 있어 고지가 필요합니다.",
            "제휴 여부는 추천 순위에 반영하지 않는다는 문구와 비제휴 대안을 같이 노출하세요.",
        )
    return _check("affiliate_neutrality", "제휴 중립성", CheckStatus.ok, "제휴 링크 없이 가격 근거를 검토했습니다.", "공유 문구에 출처 기준을 함께 남기세요.")


def _evidence_check(candidates: list[PriceTrustCandidate]) -> PriceTrustCheck:
    weak = [item for item in candidates if item.status != CheckStatus.ok]
    if any(item.status == CheckStatus.blocker for item in weak):
        return _check(
            "evidence",
            "증거 완성도",
            CheckStatus.blocker,
            "결제 판단에 쓰기 어려운 가격 근거가 포함되어 있습니다.",
            "품절, 오래된 캡처, 제휴 단독 링크를 제거하고 다시 비교하세요.",
        )
    if weak:
        return _check(
            "evidence",
            "증거 완성도",
            CheckStatus.warning,
            "일부 후보는 캡처/URL/결제 화면 검증이 부족합니다.",
            "상품 페이지, 장바구니, 결제 직전 총액을 같은 시각에 캡처하세요.",
        )
    return _check("evidence", "증거 완성도", CheckStatus.ok, "가격 증거가 공유 가능한 수준입니다.", "개인정보를 가리고 공유하세요.")


def _selected_price_check(
    request: PriceTrustRequest,
    selected: PriceTrustCandidate,
) -> PriceTrustCheck:
    if request.report_price_krw is None:
        return _check(
            "selected_price",
            "리포트 가격 대조",
            CheckStatus.warning,
            "기존 리포트 가격이 없어 변동 폭을 계산하지 못했습니다.",
            "추천 리포트 가격 또는 목표가를 함께 입력하세요.",
        )
    delta = selected.effective_price_krw - request.report_price_krw
    threshold = max(30_000, int(request.report_price_krw * 0.03))
    if delta > threshold:
        return _check(
            "selected_price",
            "리포트 가격 대조",
            CheckStatus.blocker,
            f"선택 후보가 리포트 가격보다 {delta:,}원 높습니다.",
            "가격 타이밍 윈도우와 예산 스트레스 테스트로 대기/대체를 다시 판단하세요.",
        )
    if delta < -threshold:
        return _check(
            "selected_price",
            "리포트 가격 대조",
            CheckStatus.ok,
            f"선택 후보가 리포트 가격보다 {abs(delta):,}원 낮습니다.",
            "조건이 같은지 확인한 뒤 결제 전 잠금 검수로 이동하세요.",
        )
    return _check(
        "selected_price",
        "리포트 가격 대조",
        CheckStatus.ok,
        f"선택 후보가 리포트 가격과 {abs(delta):,}원 차이입니다.",
        "가격 변동이 작으므로 판매자/옵션/AS 조건만 마지막으로 잠그세요.",
    )


def _status(checks: list[PriceTrustCheck], candidates: list[PriceTrustCandidate]) -> CheckStatus:
    if any(check.status == CheckStatus.blocker for check in checks) or any(
        item.status == CheckStatus.blocker for item in candidates
    ):
        return CheckStatus.blocker
    if any(check.status == CheckStatus.warning for check in checks) or any(
        item.status == CheckStatus.warning for item in candidates
    ):
        return CheckStatus.warning
    return CheckStatus.ok


def _score(checks: list[PriceTrustCheck], candidates: list[PriceTrustCandidate]) -> int:
    score = 100
    score -= sum(20 for check in checks if check.status == CheckStatus.blocker)
    score -= sum(8 for check in checks if check.status == CheckStatus.warning)
    score -= sum(12 for item in candidates if item.status == CheckStatus.blocker)
    score -= sum(5 for item in candidates if item.status == CheckStatus.warning)
    if len(candidates) >= 3:
        score += 4
    if any(item.non_affiliate_available for item in candidates):
        score += 3
    return max(0, min(100, score))


def _headline(title: str, status: CheckStatus) -> str:
    if status == CheckStatus.blocker:
        return f"{title} 가격 근거는 결제 전에 다시 캡처해야 합니다."
    if status == CheckStatus.warning:
        return f"{title} 가격은 쓸 수 있지만 출처/증거 보강이 필요합니다."
    return f"{title} 가격 근거는 공유와 결제 전 검수에 사용할 수 있습니다."


def _summary(
    status: CheckStatus,
    score: int,
    selected: PriceTrustCandidate | None,
    delta: int | None,
) -> str:
    selected_text = f"선택 후보 {selected.seller_name} {selected.effective_price_krw:,}원" if selected else "선택 후보 없음"
    delta_text = "리포트 가격 미입력" if delta is None else f"리포트 대비 {delta:+,}원"
    return f"가격 신뢰 점수 {score}점, 상태 {status.value}. {selected_text}, {delta_text}. 최신성, 출처 다양성, 제휴 중립성, 결제 화면 증거를 함께 검수했습니다."


def _buyer_warning(
    status: CheckStatus,
    selected: PriceTrustCandidate | None,
    delta: int | None,
) -> str:
    if status == CheckStatus.blocker:
        return "오래된 가격, 제휴 단독 링크, 품절, 리포트 대비 급등 중 하나라도 있으면 결제를 멈추세요."
    if status == CheckStatus.warning:
        return "가격 자체보다 최종 결제 화면 총액과 판매자/AS 조건이 같은지가 더 중요합니다."
    if selected and delta is not None and delta < 0:
        return "가격은 유리하지만 조건이 달라졌을 수 있으니 옵션명과 반품/AS 조건을 마지막으로 잠그세요."
    return "공유할 때 가격 출처, 캡처 시각, 제휴 여부를 함께 남기세요."


def _evidence_checklist() -> list[str]:
    return [
        "상품 페이지 가격과 옵션명 캡처",
        "장바구니 또는 결제 직전 총액 캡처",
        "배송비, 쿠폰, 카드 할인, 포인트 적용 내역",
        "판매자명, 재고, 반품/AS 조건",
        "가격 캡처 시각과 출처 URL",
        "제휴 링크라면 비제휴 대안과 제휴 고지",
    ]


def _disclosure_notes(candidates: list[PriceTrustCandidate]) -> list[str]:
    notes = [
        "추천 순위는 가격, 목적 적합도, 호환성, 리뷰 신뢰도 기준으로 계산하고 제휴 여부를 직접 반영하지 않습니다.",
        "결제 전 최종 가격은 사용자의 장바구니와 카드/쿠폰 조건에서 달라질 수 있습니다.",
    ]
    if any(item.affiliate_link for item in candidates):
        notes.append("제휴 링크가 포함된 후보는 같은 후보의 비제휴 판매처를 함께 확인해야 합니다.")
    if any(item.status != CheckStatus.ok for item in candidates):
        notes.append("주의 또는 차단 후보는 캡처를 보강하기 전까지 공유 proof로 쓰지 않습니다.")
    return notes


def _messages(
    title: str,
    status: CheckStatus,
    buyer_warning: str,
    checks: list[PriceTrustCheck],
) -> list[PriceTrustMessage]:
    review_copy = (
        f"{title} 가격 근거 검토 요청\n"
        f"- 상태: {status.value}\n"
        f"- 주의: {buyer_warning}\n"
        + "\n".join(f"- {check.label}: {check.finding}" for check in checks[:4])
    )
    return [
        PriceTrustMessage(
            channel="self",
            label="내 결제 전 체크",
            copy_text=review_copy,
            cta_label="체크 문구 복사",
        ),
        PriceTrustMessage(
            channel="community",
            label="커뮤니티 검토",
            copy_text=review_copy + "\n가격 출처와 캡처 시각 기준으로 바로 사도 되는지 검토 부탁드립니다.",
            cta_label="검토 요청 복사",
        ),
        PriceTrustMessage(
            channel="seller",
            label="판매자 확인",
            copy_text=f"{title} 결제 전 최종가, 재고, 반품/AS 조건, 쿠폰 적용 기준이 현재 상품 페이지와 같은지 확인 부탁드립니다.",
            cta_label="판매자 질문 복사",
        ),
    ]


def _analysis_prefill(
    request: PriceTrustRequest,
    title: str,
    status: CheckStatus,
    selected: PriceTrustCandidate | None,
    delta: int | None,
) -> str:
    category = "노트북" if request.category == Category.laptop else "컴퓨터"
    selected_text = (
        f"{selected.seller_name} {selected.effective_price_krw:,}원"
        if selected
        else "선택 후보 없음"
    )
    delta_text = "리포트 가격 미입력" if delta is None else f"리포트 대비 {delta:+,}원"
    return (
        f"가격 신뢰 검증: {category} '{title}' 가격 근거를 검수해줘. 상태 {status.value}, "
        f"선택 후보 {selected_text}, {delta_text}. "
        "가격 최신성, 출처 다양성, 제휴/비제휴 대안, 결제 화면 총액 캡처 기준으로 결제 가능 여부를 판단해줘."
    )


def _share_copy(
    title: str,
    status: CheckStatus,
    score: int,
    selected: PriceTrustCandidate | None,
    delta: int | None,
    checks: list[PriceTrustCheck],
) -> str:
    lines = [
        "SpecPilot AI 가격 신뢰 검증",
        f"제품: {title}",
        f"상태: {status.value}",
        f"가격 신뢰 점수: {score}점",
    ]
    if selected:
        lines.append(f"선택 후보: {selected.seller_name} {selected.effective_price_krw:,}원")
    if delta is not None:
        lines.append(f"리포트 대비: {delta:+,}원")
    lines.extend(f"- {check.label}: {check.status.value}" for check in checks[:4])
    return "\n".join(lines)


def _next_actions(status: CheckStatus, checks: list[PriceTrustCheck]) -> list[str]:
    if status == CheckStatus.blocker:
        return [
            "오래된 가격과 품절 후보를 제외하고 결제 직전 총액을 다시 캡처하세요.",
            "제휴 링크만 있는 후보는 비제휴 판매처를 함께 확보하기 전까지 추천 proof에서 제외하세요.",
            "리포트 가격보다 크게 올랐다면 가격 타이밍 윈도우와 예산 스트레스 테스트를 다시 실행하세요.",
        ]
    if status == CheckStatus.warning:
        return [
            "상품 페이지, 장바구니, 결제 직전 총액을 같은 시각에 다시 캡처하세요.",
            "제휴 여부와 비제휴 대안을 공유 문구에 함께 남기세요.",
            "출처가 하나뿐이면 공식몰 또는 다른 판매자 가격을 추가하세요.",
        ]
    return [
        "현재 가격 근거를 체크아웃 잠금 검수와 구매 실행 패키지에 연결하세요.",
        "공유할 때 캡처 시각과 제휴 여부를 함께 공개하세요.",
        "결제 직전 가격이 바뀌면 이 검증을 다시 실행하세요.",
    ]


def _check(
    check_id: str,
    label: str,
    status: CheckStatus,
    finding: str,
    action: str,
) -> PriceTrustCheck:
    return PriceTrustCheck(
        check_id=check_id,
        label=label,
        status=status,
        finding=finding,
        action=action,
    )


def _clean(values: list[str], limit: int) -> list[str]:
    return [value.strip() for value in values if value.strip()][:limit]


def _risk_terms(values: list[str]) -> list[str]:
    text = " ".join(values).casefold()
    terms = ["반품 불가", "해외", "리퍼", "전시", "중고", "조건부", "앱전용", "회원전용", "선착순"]
    return [term for term in terms if term in text]
