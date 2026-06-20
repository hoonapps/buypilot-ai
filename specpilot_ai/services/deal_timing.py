from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    CheckStatus,
    ProductCandidate,
    ProductDealWindow,
    PublicDealTimingWindow,
)
from specpilot_ai.data.catalog import desktop_candidates, laptop_candidates, price_snapshot_for
from specpilot_ai.services.evidence import review_for
from specpilot_ai.services.pricing import purchase_stability


def build_public_deal_timing_window(
    *,
    category: Category | None = None,
    budget_krw: int | None = None,
    purpose: str = "qhd_creator",
    generated_at: datetime | None = None,
) -> PublicDealTimingWindow:
    generated_at = generated_at or datetime.now(UTC)
    target_category = category or Category.desktop_pc
    target_budget = _normalize_budget(target_category, budget_krw)
    target_purpose = purpose.strip() or _default_purpose(target_category)
    captured_at = generated_at.isoformat()
    products = _ranked_candidates(target_category, target_purpose, captured_at)
    windows = [
        _deal_window(
            product=product,
            budget_krw=target_budget,
            purpose=target_purpose,
            captured_at=captured_at,
        )
        for product in products[:5]
    ]
    lead = _lead_window(windows)
    label = _category_label(target_category)
    return PublicDealTimingWindow(
        generated_at=generated_at.isoformat(),
        category=target_category,
        budget_krw=target_budget,
        purpose=target_purpose,
        headline=f"{label} 후보별 지금 결제와 가격 대기를 분리합니다.",
        summary=(
            "현재가, 목표가, 적정가 밴드, 재고/쿠폰 변동 리스크를 한 화면에 묶어 "
            "충동 결제와 의미 있는 대기를 구분합니다."
        ),
        lead_product_id=lead.product_id if lead else None,
        lead_label=lead.label if lead else "타이밍 확인 필요",
        buy_now_count=sum(1 for window in windows if window.status == CheckStatus.ok),
        wait_count=sum(1 for window in windows if window.status == CheckStatus.warning),
        hold_count=sum(1 for window in windows if window.status == CheckStatus.blocker),
        target_savings_krw=sum(
            max(0, window.current_price_krw - window.target_price_krw)
            for window in windows
        ),
        windows=windows,
        analysis_prefill=_analysis_prefill(label, target_budget, target_purpose, windows),
        share_copy=_share_copy(label, target_budget, lead, windows),
        next_actions=_next_actions(lead, windows),
    )


def _ranked_candidates(
    category: Category,
    purpose: str,
    captured_at: str,
) -> list[ProductCandidate]:
    candidates = desktop_candidates() if category == Category.desktop_pc else laptop_candidates()
    return sorted(
        candidates,
        key=lambda product: _rank_score(product, purpose, captured_at),
        reverse=True,
    )


def _rank_score(product: ProductCandidate, purpose: str, captured_at: str) -> float:
    price = price_snapshot_for(product, captured_at)
    review = review_for(product)
    score = review.trust_score * 52 + purchase_stability(price) * 0.34
    tags = set(product.tags)
    normalized = purpose.lower()
    if "qhd" in normalized and {"qhd_gaming", "qhd_entry"} & tags:
        score += 10
    if any(word in normalized for word in ["creator", "편집", "video"]) and {
        "video_editing",
        "creator",
        "portable_creator",
    } & tags:
        score += 10
    if any(word in normalized for word in ["portable", "휴대"]) and {
        "portable_creator",
        "lightweight",
        "student",
    } & tags:
        score += 9
    if "over_budget" in tags:
        score -= 12
    return round(score, 2)


def _deal_window(
    *,
    product: ProductCandidate,
    budget_krw: int,
    purpose: str,
    captured_at: str,
) -> ProductDealWindow:
    price = price_snapshot_for(product, captured_at)
    effective = price.effective_price_krw
    target = _target_price(effective, budget_krw)
    status = _status(effective, budget_krw, price.stock_status)
    label = _label(status, effective, budget_krw)
    urgency = _urgency(status, price.stock_status)
    volatility = _volatility(
        price.stock_status,
        price.source_type,
        price.coupon_krw,
        price.card_discount_krw,
    )
    return ProductDealWindow(
        product_id=product.id,
        model_name=product.model_name,
        status=status,
        label=label,
        current_price_krw=effective,
        target_price_krw=target,
        fair_price_band_krw=_fair_price_band(effective, budget_krw, status),
        urgency=urgency,
        volatility_risk=volatility,
        wait_reason=_wait_reason(status, product, purpose, effective, budget_krw),
        buy_trigger=_buy_trigger(status, target, product),
        monitoring_plan=_monitoring_plan(status, price.stock_status, price.source_type),
    )


def _target_price(effective_price_krw: int, budget_krw: int) -> int:
    if effective_price_krw <= budget_krw:
        return max(0, min(int(effective_price_krw * 0.96), int(budget_krw * 0.97)))
    return max(0, min(int(effective_price_krw * 0.94), budget_krw))


def _status(effective_price_krw: int, budget_krw: int, stock_status: str) -> CheckStatus:
    if effective_price_krw > int(budget_krw * 1.12):
        return CheckStatus.blocker
    if effective_price_krw > budget_krw or stock_status == "limited":
        return CheckStatus.warning
    return CheckStatus.ok


def _label(status: CheckStatus, effective_price_krw: int, budget_krw: int) -> str:
    if status == CheckStatus.ok:
        return "현재 결제 가능"
    if effective_price_krw <= budget_krw:
        return "특가/재고 재확인"
    if status == CheckStatus.warning:
        return "목표가 근접 대기"
    return "가격 대기"


def _urgency(status: CheckStatus, stock_status: str) -> str:
    if status == CheckStatus.ok and stock_status == "in_stock":
        return "오늘 결제 가능"
    if status == CheckStatus.warning:
        return "24-48시간 재확인"
    return "목표가 알림 후 대기"


def _volatility(
    stock_status: str,
    source_type: str,
    coupon_krw: int,
    card_discount_krw: int,
) -> str:
    risks: list[str] = []
    if stock_status == "limited":
        risks.append("한정 재고")
    if coupon_krw or card_discount_krw:
        risks.append("쿠폰/카드 조건")
    if source_type in {"open_market", "price_compare"}:
        risks.append("판매처 변동")
    return ", ".join(risks) if risks else "낮음"


def _wait_reason(
    status: CheckStatus,
    product: ProductCandidate,
    purpose: str,
    effective_price_krw: int,
    budget_krw: int,
) -> str:
    if status == CheckStatus.ok:
        return "예산 안에 들어와 있어 옵션명과 최종 결제 금액만 맞으면 구매 후보입니다."
    if status == CheckStatus.warning and effective_price_krw <= budget_krw:
        return "예산 안이지만 재고나 쿠폰 조건이 흔들릴 수 있어 결제 직전 재확인이 필요합니다."
    if status == CheckStatus.warning:
        gap = effective_price_krw - budget_krw
        return f"{_purpose_label(purpose)}에는 맞지만 예산보다 {gap:,}원 높습니다."
    if "over_budget" in product.tags:
        return "성능 여유는 크지만 이번 예산 기준에서는 과투자 리스크가 큽니다."
    return "예산 대비 가격 차이가 커 목표가 알림 없이 바로 결제하기 어렵습니다."


def _buy_trigger(status: CheckStatus, target_price_krw: int, product: ProductCandidate) -> str:
    if status == CheckStatus.ok:
        return "장바구니 옵션명, 배송비, 반품/AS 조건 캡처가 모두 맞으면 결제합니다."
    if status == CheckStatus.warning:
        return f"{target_price_krw:,}원 이하 또는 공식/가격비교 출처가 안정되면 결제 검토합니다."
    return (
        f"{target_price_krw:,}원 이하로 내려오고 "
        "사용 목적이 고성능 작업으로 확정될 때만 검토합니다."
    )


def _monitoring_plan(status: CheckStatus, stock_status: str, source_type: str) -> list[str]:
    plan = ["목표가 알림을 설정하고 현재가를 3일 주기로 재확인합니다."]
    if stock_status == "limited":
        plan.append("재고 한정 문구가 사라지거나 가격이 바뀌면 장바구니를 다시 캡처합니다.")
    if source_type in {"open_market", "price_compare"}:
        plan.append("판매자, 배송비, 쿠폰/카드 할인 조건을 결제 직전에 다시 대조합니다.")
    if status == CheckStatus.ok:
        plan.append("결제 전 옵션/사양 빠른 검수기로 최종 화면을 확인합니다.")
    return plan


def _fair_price_band(effective_price_krw: int, budget_krw: int, status: CheckStatus) -> str:
    lower = int(effective_price_krw * 0.94)
    upper = min(int(effective_price_krw * 1.03), int(budget_krw * 1.04))
    if status == CheckStatus.blocker:
        upper = min(upper, budget_krw)
    return f"{lower:,}원 ~ {max(lower, upper):,}원"


def _lead_window(windows: list[ProductDealWindow]) -> ProductDealWindow | None:
    if not windows:
        return None
    return sorted(
        windows,
        key=lambda window: (
            _status_rank(window.status),
            window.current_price_krw - window.target_price_krw,
        ),
    )[0]


def _status_rank(status: CheckStatus) -> int:
    if status == CheckStatus.ok:
        return 0
    if status == CheckStatus.warning:
        return 1
    return 2


def _analysis_prefill(
    category_label: str,
    budget_krw: int,
    purpose: str,
    windows: list[ProductDealWindow],
) -> str:
    names = ", ".join(window.model_name for window in windows[:3])
    return (
        f"{category_label}를 {budget_krw:,}원 예산으로 살지 기다릴지 판단해줘. "
        f"목적은 {_purpose_label(purpose)}이고 비교 후보는 {names}야. "
        "현재가, 목표가, 적정가 밴드, 재고/쿠폰 리스크, 결제 트리거를 같이 봐줘."
    )


def _share_copy(
    category_label: str,
    budget_krw: int,
    lead: ProductDealWindow | None,
    windows: list[ProductDealWindow],
) -> str:
    lines = [
        "SpecPilot AI 공개 구매 타이밍",
        f"- 카테고리: {category_label}",
        f"- 예산: {budget_krw:,}원",
        (
            f"- 우선 판단: {lead.model_name if lead else '후보 없음'} / "
            f"{lead.label if lead else '확인 필요'}"
        ),
    ]
    lines.extend(
        (
            f"- {window.model_name}: 현재 {window.current_price_krw:,}원, "
            f"목표 {window.target_price_krw:,}원"
        )
        for window in windows[:4]
    )
    lines.append("지금 결제할지, 목표가 알림 후 기다릴지 의견 부탁드립니다.")
    return "\n".join(lines)


def _next_actions(
    lead: ProductDealWindow | None,
    windows: list[ProductDealWindow],
) -> list[str]:
    actions = [
        "현재 결제 가능 후보도 장바구니 옵션명과 최종 결제 금액을 다시 캡처하세요.",
        "가격 대기 후보는 목표가 알림을 설정하고 판매자/쿠폰 조건 변동을 같이 보세요.",
        "타이밍 판단이 갈리면 후보 비교 스냅샷과 함께 공유해 반대 의견을 먼저 받으세요.",
    ]
    if lead and lead.status != CheckStatus.ok:
        actions.insert(0, "우선 후보가 대기 상태라면 오늘 결제보다 목표가 알림이 먼저입니다.")
    if any(window.status == CheckStatus.blocker for window in windows):
        actions.append("blocker 후보는 예산 승인 또는 사용 목적 강화 없이는 제외 후보로 두세요.")
    return actions


def _normalize_budget(category: Category, budget_krw: int | None) -> int:
    if budget_krw and budget_krw > 0:
        return min(30_000_000, max(300_000, budget_krw))
    return 2_000_000 if category == Category.laptop else 2_200_000


def _default_purpose(category: Category) -> str:
    return "portable_creator" if category == Category.laptop else "qhd_creator"


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
