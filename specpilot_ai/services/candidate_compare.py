from datetime import UTC, datetime

from specpilot_ai.core.models import (
    CandidateCompareAxis,
    CandidateCompareItem,
    CandidateCompareScenario,
    Category,
    CheckStatus,
    ProductCandidate,
    PublicCandidateCompare,
)
from specpilot_ai.data.catalog import desktop_candidates, laptop_candidates, price_snapshot_for
from specpilot_ai.services.evidence import benchmarks_for, review_for
from specpilot_ai.services.pricing import purchase_stability


def build_public_candidate_compare(
    *,
    category: Category | None = None,
    budget_krw: int | None = None,
    purpose: str = "qhd_creator",
    generated_at: datetime | None = None,
) -> PublicCandidateCompare:
    generated_at = generated_at or datetime.now(UTC)
    target_category = category or Category.desktop_pc
    target_budget = _normalize_budget(target_category, budget_krw)
    target_purpose = purpose.strip() or _default_purpose(target_category)
    captured_at = generated_at.isoformat()
    candidates = _candidates(target_category)
    ranked = sorted(
        candidates,
        key=lambda product: _score(product, target_budget, target_purpose, captured_at),
        reverse=True,
    )
    items = [
        _compare_item(
            product=product,
            budget_krw=target_budget,
            purpose=target_purpose,
            captured_at=captured_at,
            role_label=_role_label(index, product, target_purpose),
        )
        for index, product in enumerate(ranked[:5])
    ]
    winner = items[0] if items else None
    scenarios = _scenarios(items)
    label = _category_label(target_category)
    return PublicCandidateCompare(
        generated_at=generated_at.isoformat(),
        category=target_category,
        budget_krw=target_budget,
        purpose=target_purpose,
        headline=(
            f"{label} 후보 {len(items)}개를 가격, 리스크, 목적 적합도로 바로 비교합니다."
        ),
        summary=(
            "첫 방문자가 긴 분석을 시작하기 전에도 TOP 후보, 예산 방어 후보, "
            "성능 우선 후보, 안전 우선 후보의 차이를 한 화면에서 볼 수 있게 구성했습니다."
        ),
        winner_product_id=winner.product_id if winner else None,
        winner_reason=_winner_reason(winner),
        items=items,
        axes=_axes(items),
        scenarios=scenarios,
        analysis_prefill=_analysis_prefill(label, target_budget, target_purpose, items),
        share_copy=_share_copy(label, target_budget, winner, scenarios),
        next_actions=_next_actions(winner),
    )


def _candidates(category: Category) -> list[ProductCandidate]:
    return desktop_candidates() if category == Category.desktop_pc else laptop_candidates()


def _normalize_budget(category: Category, budget_krw: int | None) -> int:
    if budget_krw and budget_krw > 0:
        return min(30_000_000, max(300_000, budget_krw))
    return 2_000_000 if category == Category.laptop else 2_200_000


def _default_purpose(category: Category) -> str:
    return "portable_creator" if category == Category.laptop else "qhd_creator"


def _score(
    product: ProductCandidate,
    budget_krw: int,
    purpose: str,
    captured_at: str,
) -> float:
    price = price_snapshot_for(product, captured_at)
    review = review_for(product)
    fit = _purpose_fit(product, purpose)
    budget_score = _budget_score(price.effective_price_krw, budget_krw)
    stability = purchase_stability(price)
    source_bonus = 4 if product.source_type in {"official_store", "price_compare"} else 1
    return round(
        fit * 0.38
        + budget_score * 0.26
        + review.trust_score * 100 * 0.22
        + stability * 0.10
        + source_bonus,
        1,
    )


def _purpose_fit(product: ProductCandidate, purpose: str) -> float:
    tags = set(product.tags)
    normalized = purpose.lower()
    score = 48.0
    if any(word in normalized for word in ["qhd", "game", "게임"]):
        score += 18 if {"qhd_gaming", "qhd_entry"} & tags else -4
    if any(word in normalized for word in ["creator", "편집", "video"]):
        score += 18 if {"video_editing", "creator", "portable_creator"} & tags else -3
    if any(word in normalized for word in ["portable", "휴대", "출장"]):
        score += 18 if {"portable_creator", "lightweight", "student"} & tags else -5
    if any(word in normalized for word in ["team", "office", "사무"]):
        score += 14 if {"office", "business", "developer"} & tags else 0
    if "over_budget" in tags:
        score -= 10
    if "low_risk" in tags or "balanced" in tags:
        score += 6
    return max(0.0, min(100.0, score))


def _budget_score(price_krw: int, budget_krw: int) -> float:
    if price_krw <= budget_krw:
        room = min(0.3, (budget_krw - price_krw) / budget_krw)
        return round(82 + room * 60, 1)
    over = (price_krw - budget_krw) / budget_krw
    return round(max(15.0, 76 - over * 130), 1)


def _compare_item(
    *,
    product: ProductCandidate,
    budget_krw: int,
    purpose: str,
    captured_at: str,
    role_label: str,
) -> CandidateCompareItem:
    price = price_snapshot_for(product, captured_at)
    review = review_for(product)
    benchmarks = benchmarks_for(product)
    score = _score(product, budget_krw, purpose, captured_at)
    price_gap = price.effective_price_krw - budget_krw
    status = _status(product, price_gap, review.trust_score, price.stock_status, score)
    evidence = [
        f"{price.seller} 실구매가 {price.effective_price_krw:,}원",
        f"리뷰 신뢰도 {round(review.trust_score * 100)}점, 근거 {review.evidence_count}개",
    ]
    evidence.extend(benchmark.summary for benchmark in benchmarks[:2])
    return CandidateCompareItem(
        product_id=product.id,
        model_name=product.model_name,
        category=product.category,
        role_label=role_label,
        effective_price_krw=price.effective_price_krw,
        price_gap_krw=price_gap,
        score=score,
        status=status,
        option_summary=product.option_summary,
        fit_summary=_fit_summary(product, purpose, status),
        reasons=review.pros[:2],
        watchouts=[*review.risk_signals, *review.cons][:3],
        evidence=evidence[:4],
        cta_label="이 후보 조건으로 분석",
    )


def _status(
    product: ProductCandidate,
    price_gap_krw: int,
    trust_score: float,
    stock_status: str,
    score: float,
) -> CheckStatus:
    if price_gap_krw > 250_000 or score < 55:
        return CheckStatus.blocker
    if price_gap_krw > 0 or trust_score < 0.82 or stock_status == "limited":
        return CheckStatus.warning
    if "over_budget" in product.tags:
        return CheckStatus.warning
    return CheckStatus.ok


def _fit_summary(product: ProductCandidate, purpose: str, status: CheckStatus) -> str:
    label = _purpose_label(purpose)
    if status == CheckStatus.blocker:
        return f"{label}에는 매력적이지만 예산 또는 사양 조건에서 결제 전 보류가 필요합니다."
    if status == CheckStatus.warning:
        return f"{label}에 맞지만 재고, 옵션명, 가격 타이밍을 결제 직전에 확인해야 합니다."
    return f"{label} 기준으로 성능, 가격, 리스크 균형이 가장 안정적입니다."


def _role_label(index: int, product: ProductCandidate, purpose: str) -> str:
    if index == 0:
        return "현재 승자 후보"
    tags = set(product.tags)
    if "lowest_price" in tags or "budget_control" in tags:
        return "예산 방어 후보"
    if "over_budget" in tags or "4k_gaming" in tags or "heavy_creator" in tags:
        return "성능 우선 후보"
    if "low_risk" in tags or "official_store" == product.source_type:
        return "안전 우선 후보"
    if "portable" in purpose or "lightweight" in tags:
        return "휴대성 후보"
    return "대안 후보"


def _axes(items: list[CandidateCompareItem]) -> list[CandidateCompareAxis]:
    if not items:
        return []
    cheapest = min(items, key=lambda item: item.effective_price_krw)
    safest = max(items, key=lambda item: (item.status == CheckStatus.ok, item.score))
    performance = max(items, key=lambda item: item.score + max(0, item.price_gap_krw) / 100_000)
    return [
        CandidateCompareAxis(
            axis_id="winner",
            label="종합 승자",
            winner_product_id=items[0].product_id,
            summary=f"{items[0].model_name}이 목적 적합도와 리스크 균형이 가장 좋습니다.",
        ),
        CandidateCompareAxis(
            axis_id="budget",
            label="예산 방어",
            winner_product_id=cheapest.product_id,
            summary=f"{cheapest.model_name}은 최저 비용으로 비교 기준선을 만듭니다.",
        ),
        CandidateCompareAxis(
            axis_id="performance",
            label="성능 우선",
            winner_product_id=performance.product_id,
            summary=f"{performance.model_name}은 성능 여유가 가장 큰 선택지입니다.",
        ),
        CandidateCompareAxis(
            axis_id="risk",
            label="안전 우선",
            winner_product_id=safest.product_id,
            summary=f"{safest.model_name}은 결제 전 리스크가 가장 낮습니다.",
        ),
    ]


def _scenarios(items: list[CandidateCompareItem]) -> list[CandidateCompareScenario]:
    if not items:
        return []
    cheapest = min(items, key=lambda item: item.effective_price_krw)
    winner = items[0]
    safest = max(items, key=lambda item: (item.status == CheckStatus.ok, item.score))
    performance = max(items, key=lambda item: item.score + max(0, item.price_gap_krw) / 120_000)
    return [
        CandidateCompareScenario(
            scenario="balanced",
            label="균형 우선",
            product_id=winner.product_id,
            model_name=winner.model_name,
            why="목적 적합도, 가격, 리뷰 신뢰도, 구매 안정성의 합산 점수가 가장 높습니다.",
            tradeoff="최저가는 아닐 수 있어 목표가 알림과 최종가 캡처가 필요합니다.",
        ),
        CandidateCompareScenario(
            scenario="budget",
            label="예산 절감",
            product_id=cheapest.product_id,
            model_name=cheapest.model_name,
            why="비용을 가장 낮추면서 같은 카테고리의 비교 기준선을 제공합니다.",
            tradeoff="성능, 업그레이드, 장기 사용 여유를 일부 포기할 수 있습니다.",
        ),
        CandidateCompareScenario(
            scenario="performance",
            label="성능 우선",
            product_id=performance.product_id,
            model_name=performance.model_name,
            why="무거운 작업이나 장기 사용을 위해 성능 여유를 가장 크게 확보합니다.",
            tradeoff="예산 초과나 과투자 리스크를 별도로 승인해야 합니다.",
        ),
        CandidateCompareScenario(
            scenario="safe",
            label="안전 우선",
            product_id=safest.product_id,
            model_name=safest.model_name,
            why="리스크 상태와 리뷰 신뢰도를 우선해 결제 전 불확실성을 낮춥니다.",
            tradeoff="특가나 최고 성능보다 출처와 안정성을 우선합니다.",
        ),
    ]


def _winner_reason(winner: CandidateCompareItem | None) -> str:
    if not winner:
        return "비교 가능한 후보가 아직 없습니다."
    return (
        f"{winner.model_name}은 {winner.role_label}로, 점수 {winner.score}점과 "
        f"{winner.status.value} 상태를 기준으로 첫 비교의 기준 후보입니다."
    )


def _analysis_prefill(
    category_label: str,
    budget_krw: int,
    purpose: str,
    items: list[CandidateCompareItem],
) -> str:
    names = ", ".join(item.model_name for item in items[:3])
    return (
        f"{category_label}를 {budget_krw:,}원 예산으로 비교해줘. "
        f"목적은 {_purpose_label(purpose)}이고 우선 후보는 {names}야. "
        "TOP 3, 제외 후보, 대안 시나리오, 결제 전 옵션/가격 검수까지 같이 봐줘."
    )


def _share_copy(
    category_label: str,
    budget_krw: int,
    winner: CandidateCompareItem | None,
    scenarios: list[CandidateCompareScenario],
) -> str:
    lines = [
        "SpecPilot AI 공개 후보 비교",
        f"- 카테고리: {category_label}",
        f"- 예산: {budget_krw:,}원",
        f"- 현재 승자: {winner.model_name if winner else '후보 없음'}",
    ]
    lines.extend(f"- {scenario.label}: {scenario.model_name}" for scenario in scenarios[:4])
    lines.append("가격, 리스크, 목적 적합도 기준으로 결제 전 의견 부탁드립니다.")
    return "\n".join(lines)


def _next_actions(winner: CandidateCompareItem | None) -> list[str]:
    actions = [
        "승자 후보와 예산 방어 후보를 함께 공유해 반대 의견을 먼저 받으세요.",
        "결제 직전에는 옵션/사양 빠른 검수기로 장바구니 문구와 최종가를 대조하세요.",
        "점수 차이가 작으면 분석 리포트에서 제외 후보와 스트레스 테스트를 확인하세요.",
    ]
    if winner and winner.status != CheckStatus.ok:
        actions.insert(0, "현재 승자 후보도 warning/blocker가 있어 바로 결제하지 마세요.")
    return actions


def _category_label(category: Category) -> str:
    return "노트북" if category == Category.laptop else "데스크톱 PC"


def _purpose_label(purpose: str) -> str:
    normalized = purpose.lower()
    if "portable" in normalized or "휴대" in normalized:
        return "휴대형 크리에이터"
    if "team" in normalized or "office" in normalized or "사무" in normalized:
        return "팀/사무 구매"
    if "qhd" in normalized or "creator" in normalized or "편집" in normalized:
        return "QHD 게임과 영상 편집"
    return purpose.replace("_", " ")
