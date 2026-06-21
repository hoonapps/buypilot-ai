from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    CheckStatus,
    PublicReviewRiskKit,
    ReviewRiskRequest,
    ReviewRiskSignal,
    SpecRiskScannerRequest,
)

RISK_TOPICS = {
    "thermal": {
        "label": "발열/스로틀링",
        "terms": ["발열", "뜨거", "온도", "스로틀", "thermal", "throttle"],
        "impact": "장시간 게임, 영상 편집, 개발 빌드에서 성능 저하와 소음 증가로 이어질 수 있습니다.",
        "question": "동일 사양 장시간 부하 시 온도, 클럭 유지, 쿨링 정책을 확인할 수 있나요?",
    },
    "noise": {
        "label": "팬 소음",
        "terms": ["소음", "팬", "고주파", "시끄", "coil", "noise"],
        "impact": "기숙사, 사무실, 야간 작업에서 체감 만족도를 크게 낮출 수 있습니다.",
        "question": "일반 작업과 게임/렌더링 부하 시 팬 소음 기준이나 교환 조건이 있나요?",
    },
    "defect": {
        "label": "초기 불량/꺼짐",
        "terms": ["초기불량", "불량", "꺼짐", "재부팅", "블루스크린", "화면 깜빡", "고장"],
        "impact": "수령 직후 반품/교환 타이밍을 놓치면 AS 절차가 길어질 수 있습니다.",
        "question": "초기 불량 판정 기간, 교환 방식, 접수 번호 발급 기준을 알려 주세요.",
    },
    "display": {
        "label": "화면/패널",
        "terms": ["빛샘", "멍", "불량화소", "패널", "밝기", "색감", "번인"],
        "impact": "노트북과 모니터 포함 세팅에서 작업 품질과 반품 가능성에 직접 영향을 줍니다.",
        "question": "불량화소, 빛샘, OLED 번인, 패널 교환 기준을 알려 주세요.",
    },
    "battery": {
        "label": "배터리/휴대성",
        "terms": ["배터리", "무게", "휴대", "충전", "PD", "어댑터"],
        "impact": "노트북 이동 사용 시간이 짧거나 충전 조건이 제한되면 구매 목적과 어긋날 수 있습니다.",
        "question": "실사용 배터리 시간, PD 충전 와트, 동봉 어댑터 무게를 알려 주세요.",
    },
    "support": {
        "label": "AS/판매자 대응",
        "terms": ["as", "a/s", "보증", "교환", "반품", "판매자", "고객센터", "응대"],
        "impact": "문제 발생 시 해결 속도와 비용을 좌우하므로 가격보다 우선 확인해야 합니다.",
        "question": "국내 AS 가능 여부, 보증 주체, 반품 배송비, 접수 경로를 문장으로 확인해 주세요.",
    },
}

POSITIVE_TERMS = ["조용", "만족", "빠르", "가성비", "성능 좋", "배송 빠", "양품", "추천"]


def build_public_review_risk_kit(
    request: ReviewRiskRequest,
    generated_at: datetime | None = None,
) -> PublicReviewRiskKit:
    generated_at = generated_at or datetime.now(UTC)
    title = request.product_title.strip() or _category_label(request.category)
    snippets = [item.strip() for item in request.review_snippets if item.strip()]
    combined_text = " ".join([title, *snippets]).lower()
    signals = _review_signals(combined_text)
    repeated_complaints = [signal.label for signal in signals if signal.status != CheckStatus.ok]
    positive_signals = _positive_signals(combined_text)
    status = _status(signals, request.rating, request.review_count, snippets)
    risk_score = _risk_score(signals, request.rating, request.review_count, snippets)
    scanner_prefill = _scanner_prefill(request, title, snippets)
    return PublicReviewRiskKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=title,
        review_status=status,
        review_risk_score=risk_score,
        headline=_headline(title, status, repeated_complaints),
        summary=(
            f"후기 {len(snippets)}개에서 반복 불만 {len(repeated_complaints)}개를 추출했습니다. "
            f"평점 {request.rating if request.rating is not None else '미입력'}, "
            f"리뷰 수 {request.review_count if request.review_count is not None else '미입력'} 기준으로 "
            "리뷰를 확정 판단이 아니라 리스크 신호로만 표시합니다."
        ),
        repeated_complaints=repeated_complaints,
        positive_signals=positive_signals,
        review_signals=signals,
        source_quality_notes=_source_quality_notes(request, snippets),
        seller_questions=_seller_questions(signals),
        evidence_checklist=_evidence_checklist(signals, snippets),
        scanner_prefill=scanner_prefill,
        analysis_prefill=_analysis_prefill(request, title, signals, scanner_prefill),
        share_copy=_share_copy(title, status, repeated_complaints),
        next_actions=_next_actions(status, repeated_complaints),
    )


def _review_signals(text: str) -> list[ReviewRiskSignal]:
    signals: list[ReviewRiskSignal] = []
    for signal_id, config in RISK_TOPICS.items():
        hits = [term for term in config["terms"] if term in text]
        frequency = sum(text.count(term) for term in config["terms"])
        if frequency >= 2:
            status = CheckStatus.blocker if signal_id in {"defect", "support"} else CheckStatus.warning
        elif frequency == 1:
            status = CheckStatus.warning
        else:
            status = CheckStatus.ok
        signals.append(
            ReviewRiskSignal(
                signal_id=signal_id,
                label=config["label"],
                status=status,
                evidence=", ".join(hits[:4]) if hits else "반복 언급 없음",
                frequency=frequency,
                buyer_impact=config["impact"],
                next_step=config["question"],
            )
        )
    return signals


def _positive_signals(text: str) -> list[str]:
    signals = [term for term in POSITIVE_TERMS if term in text]
    return signals[:6]


def _status(
    signals: list[ReviewRiskSignal],
    rating: float | None,
    review_count: int | None,
    snippets: list[str],
) -> CheckStatus:
    if any(signal.status == CheckStatus.blocker for signal in signals):
        return CheckStatus.blocker
    if rating is not None and rating < 3.7 and (review_count or 0) >= 20:
        return CheckStatus.blocker
    if any(signal.status == CheckStatus.warning for signal in signals):
        return CheckStatus.warning
    if len(snippets) < 3 or (review_count is not None and review_count < 10):
        return CheckStatus.warning
    return CheckStatus.ok


def _risk_score(
    signals: list[ReviewRiskSignal],
    rating: float | None,
    review_count: int | None,
    snippets: list[str],
) -> float:
    blocker_count = sum(1 for signal in signals if signal.status == CheckStatus.blocker)
    warning_count = sum(1 for signal in signals if signal.status == CheckStatus.warning)
    base = 84 - blocker_count * 22 - warning_count * 8
    if rating is not None:
        base += (rating - 4.0) * 8
    if review_count is not None:
        base += min(8, review_count / 50)
    if len(snippets) < 3:
        base -= 10
    return round(min(98, max(10, base)), 1)


def _source_quality_notes(request: ReviewRiskRequest, snippets: list[str]) -> list[str]:
    notes = []
    if len(snippets) < 3:
        notes.append("후기 문구가 3개 미만이라 반복 불만 판단은 약합니다.")
    if request.rating is None:
        notes.append("평점이 없어 후기 문구 중심으로만 판정했습니다.")
    if request.review_count is None:
        notes.append("리뷰 수가 없어 대표성은 별도 확인이 필요합니다.")
    if request.review_count is not None and request.review_count < 10:
        notes.append("리뷰 수가 적어 초기 구매자 편향이 있을 수 있습니다.")
    return notes or ["평점, 리뷰 수, 후기 문구가 함께 있어 공개 검수에 사용할 수 있습니다."]


def _seller_questions(signals: list[ReviewRiskSignal]) -> list[str]:
    risky = [signal for signal in signals if signal.status != CheckStatus.ok]
    questions = [signal.next_step for signal in risky]
    questions.append("후기에서 반복된 불만이 초기 불량 교환 또는 무상 AS 대상인지 확인해 주세요.")
    questions.append("같은 모델의 최근 생산분에서도 동일 이슈가 반복되는지 확인할 수 있나요?")
    return list(dict.fromkeys(questions))[:6]


def _evidence_checklist(signals: list[ReviewRiskSignal], snippets: list[str]) -> list[str]:
    checklist = [
        "후기 원문과 작성 시점, 구매 옵션을 함께 캡처합니다.",
        "평점, 리뷰 수, 낮은 별점 후기의 반복 키워드를 함께 저장합니다.",
    ]
    if any(signal.signal_id == "thermal" and signal.status != CheckStatus.ok for signal in signals):
        checklist.append("온도, 팬 소음, 성능 저하 후기를 부하 작업 기준으로 분리합니다.")
    if any(signal.signal_id == "defect" and signal.status != CheckStatus.ok for signal in signals):
        checklist.append("초기 불량 후기는 반품 가능 기간과 교환 절차 캡처를 함께 남깁니다.")
    if len(snippets) < 3:
        checklist.append("같은 모델의 다른 판매처 후기 2개 이상을 추가로 확인합니다.")
    return checklist[:6]


def _scanner_prefill(
    request: ReviewRiskRequest,
    title: str,
    snippets: list[str],
) -> SpecRiskScannerRequest:
    return SpecRiskScannerRequest(
        category=request.category,
        product_title=title,
        option_text=title,
        cart_total_krw=None,
        budget_krw=request.budget_krw,
        expected_cpu="",
        expected_gpu="",
        expected_ram_gb=None,
        expected_storage_gb=None,
        expected_os="",
        evidence_text="리뷰 리스크 스캐너 기반 prefill: " + " / ".join(snippets[:2]),
        source="review_risk",
    )


def _analysis_prefill(
    request: ReviewRiskRequest,
    title: str,
    signals: list[ReviewRiskSignal],
    scanner_prefill: SpecRiskScannerRequest,
) -> str:
    signal_text = ", ".join(
        f"{signal.label}:{signal.status.value}:{signal.frequency}회"
        for signal in signals
        if signal.status != CheckStatus.ok
    )
    return (
        f"{_category_label(request.category)} 후보 '{title}'의 후기 리스크를 검토했어. "
        f"사용 맥락은 {request.usage_context}, 평점은 {request.rating or '미입력'}, "
        f"리뷰 수는 {request.review_count or '미입력'}이야. "
        f"반복 불만 신호는 {signal_text or '뚜렷하지 않음'}이고, "
        f"검수 prefill source는 {scanner_prefill.source}야. "
        "리뷰를 단정하지 말고 가격, 사양, 보증/반품, 대체 후보와 함께 구매 가능 여부를 정리해줘."
    )


def _share_copy(title: str, status: CheckStatus, repeated_complaints: list[str]) -> str:
    verdict = "보류" if status == CheckStatus.blocker else "확인 필요" if status == CheckStatus.warning else "통과"
    complaints = f" 반복 불만: {', '.join(repeated_complaints)}." if repeated_complaints else ""
    return f"SpecPilot AI 리뷰 리스크 검수: {title} 후기 판정은 {verdict}.{complaints}"


def _next_actions(status: CheckStatus, repeated_complaints: list[str]) -> list[str]:
    if status == CheckStatus.blocker:
        return [
            "반복 불만이 AS/초기 불량에 걸리면 판매자 답변 전 결제를 보류하세요.",
            "같은 모델의 다른 판매처 후기와 낮은 별점 후기를 추가 확인하세요.",
            "보증/반품 키트와 판매자 증거 키트로 문의 문구를 먼저 만드세요.",
        ]
    if repeated_complaints:
        return [
            "반복 불만은 구매 목적과 직접 충돌하는지 먼저 확인하세요.",
            "판매자 질문을 복사해 최근 생산분과 교환 조건을 확인하세요.",
            "결제 전 검수에서 후기 리스크를 누락 증거로 남기세요.",
        ]
    return [
        "후기 리스크는 낮지만 평점과 낮은 별점 원문은 캡처하세요.",
        "가격, 사양, 반품 조건과 함께 최종 분석을 실행하세요.",
    ]


def _headline(title: str, status: CheckStatus, repeated_complaints: list[str]) -> str:
    if status == CheckStatus.blocker:
        return f"{title} 후기에 결제 전 보류할 반복 불만이 있습니다."
    if status == CheckStatus.warning:
        return f"{title} 후기는 {', '.join(repeated_complaints[:2]) or '대표성'} 확인이 필요합니다."
    return f"{title} 후기는 공개 검수 기준에서 큰 반복 불만이 보이지 않습니다."


def _category_label(category: Category) -> str:
    return "노트북" if category == Category.laptop else "데스크톱 PC"
