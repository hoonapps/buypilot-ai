from datetime import UTC, datetime

from specpilot_ai.core.models import (
    CandidateCompareAxis,
    CandidateCompareItem,
    CandidateCompareScenario,
    Category,
    CheckStatus,
    CustomCandidateDecisionRequest,
    CustomCandidateInput,
    PublicCustomCandidateDecisionKit,
)


def build_public_custom_candidate_decision_kit(
    request: CustomCandidateDecisionRequest,
    generated_at: datetime | None = None,
) -> PublicCustomCandidateDecisionKit:
    generated_at = generated_at or datetime.now(UTC)
    purpose = request.purpose.strip() or _default_purpose(request.category)
    items = sorted(
        [
            _item(index, candidate, request.category, request.budget_krw, purpose)
            for index, candidate in enumerate(request.candidates)
        ],
        key=lambda item: item.score,
        reverse=True,
    )
    winner = items[0] if items else None
    decision = _decision(items)
    confidence = _confidence(items)
    label = _category_label(request.category)
    return PublicCustomCandidateDecisionKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        budget_krw=request.budget_krw,
        purpose=purpose,
        decision=decision,
        winner_candidate_id=winner.product_id if winner else None,
        winner_title=winner.model_name if winner else None,
        confidence_score=confidence,
        headline=_headline(label, winner, decision),
        summary=_summary(request, items, decision),
        items=items,
        axes=_axes(items),
        scenarios=_scenarios(items),
        decision_rules=_decision_rules(request, items),
        seller_questions=_seller_questions(request, items),
        evidence_checklist=_evidence_checklist(request),
        analysis_prefill=_analysis_prefill(request, label, purpose, items, decision),
        share_copy=_share_copy(label, request, items, decision),
        next_actions=_next_actions(decision, winner),
    )


def _item(
    index: int,
    candidate: CustomCandidateInput,
    category: Category,
    budget_krw: int,
    purpose: str,
) -> CandidateCompareItem:
    effective_price = _effective_price(candidate)
    price_gap = effective_price - budget_krw
    risk_flags = _risk_flags(candidate)
    score = _score(candidate, effective_price, budget_krw, purpose, risk_flags)
    status = _status(score, price_gap, candidate.stock_status, risk_flags)
    candidate_id = candidate.candidate_id.strip() or f"custom_{index + 1}"
    return CandidateCompareItem(
        product_id=candidate_id,
        model_name=candidate.title.strip(),
        category=category,
        role_label=_role_label(index, candidate, score, price_gap, risk_flags),
        effective_price_krw=effective_price,
        price_gap_krw=price_gap,
        score=score,
        status=status,
        option_summary=_option_summary(candidate),
        fit_summary=_fit_summary(candidate, purpose, status),
        reasons=_reasons(candidate, effective_price, budget_krw, purpose),
        watchouts=_watchouts(candidate, risk_flags, price_gap),
        evidence=_evidence(candidate, effective_price),
        cta_label="이 실제 후보로 분석",
    )


def _effective_price(candidate: CustomCandidateInput) -> int:
    return max(
        0,
        candidate.listed_price_krw
        + candidate.shipping_fee_krw
        + candidate.assembly_fee_krw
        + candidate.os_fee_krw
        - candidate.discount_krw,
    )


def _score(
    candidate: CustomCandidateInput,
    effective_price: int,
    budget_krw: int,
    purpose: str,
    risk_flags: list[str],
) -> float:
    score = (
        _purpose_fit(candidate, purpose) * 0.34
        + _budget_score(effective_price, budget_krw) * 0.28
        + _evidence_score(candidate) * 0.18
        + _protection_score(candidate) * 0.12
        + _stock_score(candidate.stock_status) * 0.08
    )
    if risk_flags:
        score -= min(26, len(risk_flags) * 7)
    if any(_hard_risk(risk) for risk in risk_flags):
        score -= 18
    return round(max(0.0, min(100.0, score)), 1)


def _purpose_fit(candidate: CustomCandidateInput, purpose: str) -> float:
    text = f"{candidate.title} {candidate.cpu} {candidate.gpu} {candidate.evidence_text}".lower()
    score = 44.0
    if any(term in purpose.lower() for term in ("qhd", "game", "게임")):
        if any(gpu in text for gpu in ("4070", "4080", "5070", "5080", "rx 7800", "rx 7900")):
            score += 30
        elif any(gpu in text for gpu in ("4060", "3060", "7600")):
            score += 16
        else:
            score -= 8
    if any(term in purpose.lower() for term in ("creator", "편집", "video", "4k")):
        if candidate.ram_gb and candidate.ram_gb >= 32:
            score += 14
        if candidate.storage_gb and candidate.storage_gb >= 1000:
            score += 10
        if any(gpu in text for gpu in ("4070", "4080", "4060", "5070", "5080")):
            score += 12
    if any(term in purpose.lower() for term in ("portable", "휴대", "student")):
        if "노트북" in text or "laptop" in text or "book" in text:
            score += 22
        if candidate.ram_gb and candidate.ram_gb >= 16:
            score += 8
    if any(term in purpose.lower() for term in ("team", "office", "사무")):
        if candidate.warranty_months and candidate.warranty_months >= 24:
            score += 14
        if candidate.return_window_days and candidate.return_window_days >= 7:
            score += 8
    return max(0.0, min(100.0, score))


def _budget_score(effective_price: int, budget_krw: int) -> float:
    if effective_price <= budget_krw:
        room = min(0.28, (budget_krw - effective_price) / budget_krw)
        return 82 + room * 55
    over = (effective_price - budget_krw) / budget_krw
    return max(12.0, 76 - over * 150)


def _evidence_score(candidate: CustomCandidateInput) -> float:
    score = 35.0
    if candidate.url.strip():
        score += 12
    if candidate.seller_name.strip():
        score += 8
    if candidate.cpu.strip():
        score += 8
    if candidate.gpu.strip():
        score += 8
    if candidate.ram_gb:
        score += 7
    if candidate.storage_gb:
        score += 7
    if candidate.os_name.strip():
        score += 5
    if candidate.evidence_text.strip():
        score += 10
    return min(100.0, score)


def _protection_score(candidate: CustomCandidateInput) -> float:
    score = 45.0
    if candidate.warranty_months is not None:
        score += 22 if candidate.warranty_months >= 24 else 12 if candidate.warranty_months >= 12 else -8
    if candidate.return_window_days is not None:
        score += 18 if candidate.return_window_days >= 7 else -8
    if not candidate.risk_terms:
        score += 10
    return max(0.0, min(100.0, score))


def _stock_score(stock_status: str) -> float:
    status = stock_status.lower()
    if any(term in status for term in ("in_stock", "판매중", "재고 있음", "available")):
        return 90.0
    if any(term in status for term in ("low", "부족", "임박", "limited")):
        return 55.0
    if any(term in status for term in ("sold", "품절", "ended")):
        return 10.0
    return 42.0


def _risk_flags(candidate: CustomCandidateInput) -> list[str]:
    flags = [risk.strip() for risk in candidate.risk_terms if risk.strip()]
    text = f"{candidate.title} {candidate.evidence_text} {' '.join(flags)}".lower()
    for keyword, label in [
        ("리퍼", "리퍼 조건"),
        ("전시", "전시 상품"),
        ("중고", "중고 조건"),
        ("해외", "해외/병행 수입"),
        ("병행", "해외/병행 수입"),
        ("반품 불가", "반품 불가"),
        ("as 불가", "AS 불가"),
        ("보증 없음", "보증 없음"),
        ("freedos", "FreeDOS OS 비용"),
        ("free dos", "FreeDOS OS 비용"),
    ]:
        if keyword in text and label not in flags:
            flags.append(label)
    if candidate.stock_status.lower() in {"sold_out", "품절"}:
        flags.append("품절 또는 판매 종료")
    return flags[:8]


def _hard_risk(risk: str) -> bool:
    return any(term in risk.lower() for term in ("반품 불가", "as 불가", "보증 없음", "리퍼", "전시", "중고", "해외"))


def _status(score: float, price_gap: int, stock_status: str, risk_flags: list[str]) -> CheckStatus:
    if score < 58 or any(_hard_risk(risk) for risk in risk_flags) or stock_status.lower() in {"sold_out", "품절"}:
        return CheckStatus.blocker
    if score < 82 or price_gap > 0 or risk_flags:
        return CheckStatus.warning
    return CheckStatus.ok


def _role_label(
    index: int,
    candidate: CustomCandidateInput,
    score: float,
    price_gap: int,
    risk_flags: list[str],
) -> str:
    if index == 0:
        return "입력 후보"
    if any(_hard_risk(risk) for risk in risk_flags):
        return "리스크 검수 후보"
    if price_gap <= -100_000:
        return "예산 방어 후보"
    if score >= 84:
        return "종합 우위 후보"
    return "비교 후보"


def _option_summary(candidate: CustomCandidateInput) -> str:
    specs = [
        candidate.cpu.strip(),
        candidate.gpu.strip(),
        f"RAM {candidate.ram_gb}GB" if candidate.ram_gb else "",
        f"SSD {candidate.storage_gb}GB" if candidate.storage_gb else "",
        candidate.os_name.strip(),
    ]
    seller = candidate.seller_name.strip() or "판매자 미입력"
    return " · ".join([part for part in [seller, *specs] if part])


def _fit_summary(candidate: CustomCandidateInput, purpose: str, status: CheckStatus) -> str:
    purpose_label = _purpose_label(purpose)
    if status == CheckStatus.blocker:
        return f"{purpose_label} 기준으로 가격보다 조건/증거 리스크가 먼저 닫혀야 합니다."
    if status == CheckStatus.warning:
        return f"{purpose_label}에는 가능성이 있지만 최종가, 재고, 보증/반품 답변이 필요합니다."
    return f"{purpose_label} 기준으로 가격, 사양, 보호 조건 균형이 가장 안정적입니다."


def _reasons(
    candidate: CustomCandidateInput,
    effective_price: int,
    budget_krw: int,
    purpose: str,
) -> list[str]:
    reasons: list[str] = []
    if effective_price <= budget_krw:
        reasons.append(f"예산 안 실구매가 {effective_price:,}원")
    if candidate.gpu.strip():
        reasons.append(f"목적 {purpose}에 GPU {candidate.gpu.strip()} 확인")
    if candidate.ram_gb and candidate.ram_gb >= 32:
        reasons.append("RAM 32GB 이상으로 작업 여유")
    if candidate.warranty_months and candidate.warranty_months >= 24:
        reasons.append("보증 24개월 이상")
    if not reasons:
        reasons.append("비교 후보로 필요한 기본 가격 정보가 있습니다.")
    return reasons[:3]


def _watchouts(candidate: CustomCandidateInput, risk_flags: list[str], price_gap: int) -> list[str]:
    watchouts = list(risk_flags)
    if price_gap > 0:
        watchouts.append(f"예산보다 {price_gap:,}원 높음")
    if not candidate.url.strip():
        watchouts.append("상품 URL 미입력")
    if candidate.return_window_days is None:
        watchouts.append("반품 기간 미확인")
    if candidate.warranty_months is None:
        watchouts.append("보증 기간 미확인")
    if not watchouts:
        watchouts.append("결제 전 최종 옵션명과 총액 캡처 필요")
    return watchouts[:4]


def _evidence(candidate: CustomCandidateInput, effective_price: int) -> list[str]:
    evidence = [
        f"표시가 {candidate.listed_price_krw:,}원, 실구매가 {effective_price:,}원",
        f"재고 상태 {candidate.stock_status}",
    ]
    if candidate.url.strip():
        evidence.append(candidate.url.strip())
    if candidate.evidence_text.strip():
        evidence.append(candidate.evidence_text.strip()[:140])
    return evidence[:4]


def _axes(items: list[CandidateCompareItem]) -> list[CandidateCompareAxis]:
    if not items:
        return []
    cheapest = min(items, key=lambda item: item.effective_price_krw)
    safest = max(items, key=lambda item: (item.status == CheckStatus.ok, item.score))
    performance = max(items, key=lambda item: item.score + max(0, item.effective_price_krw) / 2_000_000)
    return [
        CandidateCompareAxis(
            axis_id="winner",
            label="종합 승자",
            winner_product_id=items[0].product_id,
            summary=f"{items[0].model_name}이 입력 후보 중 점수와 리스크 균형이 가장 좋습니다.",
        ),
        CandidateCompareAxis(
            axis_id="budget",
            label="예산 방어",
            winner_product_id=cheapest.product_id,
            summary=f"{cheapest.model_name}은 실구매가가 가장 낮아 가격 기준선을 만듭니다.",
        ),
        CandidateCompareAxis(
            axis_id="performance",
            label="성능/목적 우선",
            winner_product_id=performance.product_id,
            summary=f"{performance.model_name}은 목적 적합 점수가 가장 강합니다.",
        ),
        CandidateCompareAxis(
            axis_id="risk",
            label="안전 우선",
            winner_product_id=safest.product_id,
            summary=f"{safest.model_name}은 결제 전 blocker 가능성이 가장 낮습니다.",
        ),
    ]


def _scenarios(items: list[CandidateCompareItem]) -> list[CandidateCompareScenario]:
    if not items:
        return []
    cheapest = min(items, key=lambda item: item.effective_price_krw)
    safest = max(items, key=lambda item: (item.status == CheckStatus.ok, item.score))
    return [
        CandidateCompareScenario(
            scenario="balanced",
            label="균형 우선",
            product_id=items[0].product_id,
            model_name=items[0].model_name,
            why="입력 후보 중 점수와 리스크 균형이 가장 좋습니다.",
            tradeoff="최종 결제 화면 가격과 판매자 답변은 별도로 닫아야 합니다.",
        ),
        CandidateCompareScenario(
            scenario="budget",
            label="예산 우선",
            product_id=cheapest.product_id,
            model_name=cheapest.model_name,
            why="실구매가가 가장 낮아 예산 초과 가능성을 줄입니다.",
            tradeoff="성능, 보증, 재고 조건이 약하면 장기 비용이 커질 수 있습니다.",
        ),
        CandidateCompareScenario(
            scenario="safe",
            label="안전 우선",
            product_id=safest.product_id,
            model_name=safest.model_name,
            why="blocker가 적고 증거/보호 조건이 상대적으로 안정적입니다.",
            tradeoff="최저가나 최고 성능이 아닐 수 있습니다.",
        ),
    ]


def _decision(items: list[CandidateCompareItem]) -> str:
    if not items:
        return "hold"
    if items[0].status == CheckStatus.blocker:
        return "hold"
    if items[0].status == CheckStatus.warning or any(item.status == CheckStatus.blocker for item in items):
        return "verify"
    return "ready"


def _confidence(items: list[CandidateCompareItem]) -> float:
    if not items:
        return 0.0
    top = items[0].score
    gap = top - items[1].score if len(items) > 1 else 12
    blocker_penalty = sum(1 for item in items if item.status == CheckStatus.blocker) * 5
    return round(max(35.0, min(96.0, top + min(12, gap) - blocker_penalty)), 1)


def _decision_rules(
    request: CustomCandidateDecisionRequest,
    items: list[CandidateCompareItem],
) -> list[str]:
    return [
        "blocker 후보는 가격이 낮아도 최종 결제 전 제외하거나 판매자 답변으로 해소합니다.",
        f"예산 {request.budget_krw:,}원 초과 후보는 실구매가 분해와 조건 협상을 먼저 통과해야 합니다.",
        "승자 후보도 상품 URL, 옵션명, 최종 결제 금액, 반품/AS 조건 캡처가 없으면 구매 실행 패키지로 넘기지 않습니다.",
        f"현재 1순위는 {items[0].model_name if items else '없음'}입니다.",
    ]


def _seller_questions(
    request: CustomCandidateDecisionRequest,
    items: list[CandidateCompareItem],
) -> list[str]:
    questions = [
        "각 후보의 실제 출고 사양이 페이지/장바구니 옵션명과 동일한가요?",
        "최종 결제 금액에 배송비, 조립비, OS 비용, 쿠폰/카드 할인이 모두 반영되나요?",
        "현재 재고와 실제 출고 예정일을 후보별로 확인할 수 있나요?",
        "반품 기간, 초기 불량 교환, 제조사/판매자 AS 기준이 후보별로 어떻게 다른가요?",
    ]
    if any(item.price_gap_krw > 0 for item in items):
        questions.append("예산 초과 후보의 가격 조정 또는 배송/조립/OS 비용 차감이 가능한가요?")
    if request.category == Category.laptop:
        questions.append("노트북 후보별 무게, 배터리, 온보드 RAM/SSD 업그레이드 가능 여부를 확인해 주세요.")
    return questions[:6]


def _evidence_checklist(request: CustomCandidateDecisionRequest) -> list[str]:
    checklist = [
        "후보별 상품 URL과 판매자명",
        "후보별 상품명/옵션명/CPU/GPU/RAM/SSD/OS 캡처",
        "후보별 최종 결제 금액, 배송비, 쿠폰/카드 할인 캡처",
        "후보별 재고, 출고 예정일, 반품/AS 조건 캡처",
    ]
    if request.must_haves:
        checklist.append(f"필수 조건 충족 증거: {', '.join(request.must_haves[:4])}")
    return checklist


def _headline(label: str, winner: CandidateCompareItem | None, decision: str) -> str:
    if winner is None:
        return f"{label} 후보 비교를 위해 최소 2개 후보가 필요합니다."
    if decision == "hold":
        return f"{label} 입력 후보는 아직 결제하지 말고 blocker를 먼저 닫아야 합니다."
    if decision == "verify":
        return f"{winner.model_name}이 앞서지만 결제 전 증거 확인이 필요합니다."
    return f"{winner.model_name}을 현재 입력 후보의 1순위로 둘 수 있습니다."


def _summary(
    request: CustomCandidateDecisionRequest,
    items: list[CandidateCompareItem],
    decision: str,
) -> str:
    blockers = sum(1 for item in items if item.status == CheckStatus.blocker)
    warnings = sum(1 for item in items if item.status == CheckStatus.warning)
    return (
        f"예산 {request.budget_krw:,}원, 후보 {len(items)}개, blocker {blockers}개, "
        f"warning {warnings}개 기준 decision={decision}. "
        "가격, 목적 적합도, 증거, 보증/반품, 재고를 함께 점수화했습니다."
    )


def _analysis_prefill(
    request: CustomCandidateDecisionRequest,
    label: str,
    purpose: str,
    items: list[CandidateCompareItem],
    decision: str,
) -> str:
    lines = "; ".join(
        f"{index + 1}. {item.model_name} {item.effective_price_krw:,}원 {item.status.value} {round(item.score)}점"
        for index, item in enumerate(items)
    )
    return (
        f"{label} 실제 후보 비교 결과 decision={decision}. 예산 {request.budget_krw:,}원, "
        f"목적 {purpose}, 후보: {lines}. TOP 3 추천, 제외 후보, 판매자 질문, 결제 전 체크리스트를 정리해줘."
    )


def _share_copy(
    label: str,
    request: CustomCandidateDecisionRequest,
    items: list[CandidateCompareItem],
    decision: str,
) -> str:
    ranked = "\n".join(
        f"{index + 1}. {item.model_name} · {item.effective_price_krw:,}원 · {item.status.value} · {round(item.score)}점"
        for index, item in enumerate(items[:4])
    )
    return (
        "SpecPilot AI 커스텀 후보 비교\n"
        f"카테고리: {label}\n"
        f"예산: {request.budget_krw:,}원\n"
        f"판정: {decision}\n"
        f"{ranked}"
    )


def _next_actions(decision: str, winner: CandidateCompareItem | None) -> list[str]:
    if decision == "hold":
        return [
            "blocker 후보는 결제하지 말고 판매자 증거 요청 또는 대체 후보 rescue로 넘기세요.",
            "가격이 낮아도 리퍼/해외/반품 불가/AS 불가 조건이 있으면 제외 후보로 표시하세요.",
            "상품 페이지 근거 인입 키트로 각 후보의 URL/가격/재고 증거를 보강하세요.",
        ]
    if decision == "verify":
        return [
            f"{winner.model_name if winner else '1순위 후보'}의 최종 결제 금액과 판매자 답변을 먼저 캡처하세요.",
            "실구매가 분해와 판매자 조건 협상 키트로 가격과 조건을 분리하세요.",
            "구매 실행 패키지로 결제 전 중단 조건을 확인하세요.",
        ]
    return [
        f"{winner.model_name if winner else '1순위 후보'}를 구매 실행 패키지로 넘기세요.",
        "2순위 후보는 가격 대기 또는 협상 대안으로 남기세요.",
        "결제 후 구매 후 케어와 첫 부팅 세팅 검수로 결과를 닫으세요.",
    ]


def _category_label(category: Category) -> str:
    return "노트북" if category == Category.laptop else "데스크톱 PC"


def _purpose_label(purpose: str) -> str:
    normalized = purpose.lower()
    if "portable" in normalized or "휴대" in normalized:
        return "휴대형 사용"
    if "team" in normalized or "office" in normalized or "사무" in normalized:
        return "팀/사무 구매"
    if "4k" in normalized:
        return "4K 고성능 작업"
    return "QHD 게임·크리에이터"


def _default_purpose(category: Category) -> str:
    return "portable_creator" if category == Category.laptop else "qhd_creator"
