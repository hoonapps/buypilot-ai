from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    CheckStatus,
    PriceWatchCandidate,
    ProductDealWindow,
    PublicPriceWatchKit,
)
from specpilot_ai.services.deal_timing import build_public_deal_timing_window


def build_public_price_watch_kit(
    *,
    category: Category | None = None,
    budget_krw: int | None = None,
    purpose: str = "qhd_creator",
    generated_at: datetime | None = None,
) -> PublicPriceWatchKit:
    generated_at = generated_at or datetime.now(UTC)
    timing = build_public_deal_timing_window(
        category=category,
        budget_krw=budget_krw,
        purpose=purpose,
        generated_at=generated_at,
    )
    watch_candidates = [_watch_candidate(window) for window in timing.windows[:5]]
    primary = _primary_watch(watch_candidates)
    category_label = "노트북" if timing.category == Category.laptop else "데스크톱 PC"
    return PublicPriceWatchKit(
        generated_at=timing.generated_at,
        category=timing.category,
        budget_krw=timing.budget_krw,
        purpose=timing.purpose,
        headline=f"{category_label} 목표가를 놓치지 않도록 대기 조건을 알림으로 바꿉니다.",
        summary=(
            "가격 비교 후 '조금 더 기다릴까'에서 멈추지 않도록 후보별 목표가, 알림 기준, "
            "재확인 주기, 결제 판단 문구를 한 번에 제공합니다."
        ),
        watched_count=sum(1 for item in watch_candidates if item.status != CheckStatus.ok),
        immediate_buy_count=sum(1 for item in watch_candidates if item.status == CheckStatus.ok),
        total_target_savings_krw=sum(item.target_gap_krw for item in watch_candidates),
        primary_watch_product_id=primary.product_id if primary else None,
        primary_watch_label=_primary_label(primary),
        candidates=watch_candidates,
        alert_script=_alert_script(category_label, primary, watch_candidates),
        analysis_prefill=_analysis_prefill(category_label, timing.budget_krw, timing.purpose, primary),
        share_copy=_share_copy(category_label, timing.budget_krw, primary, watch_candidates),
        next_actions=_next_actions(primary, watch_candidates),
    )


def _watch_candidate(window: ProductDealWindow) -> PriceWatchCandidate:
    gap = max(0, window.current_price_krw - window.target_price_krw)
    alert_threshold = _alert_threshold(window)
    return PriceWatchCandidate(
        product_id=window.product_id,
        model_name=window.model_name,
        status=window.status,
        current_price_krw=window.current_price_krw,
        target_price_krw=window.target_price_krw,
        target_gap_krw=gap,
        alert_threshold_krw=alert_threshold,
        cadence=_cadence(window),
        alert_reason=_alert_reason(window, gap),
        notification_copy=_notification_copy(window, alert_threshold),
        decision_rule=_decision_rule(window),
        fallback_action=_fallback_action(window),
    )


def _alert_threshold(window: ProductDealWindow) -> int:
    if window.status == CheckStatus.ok:
        return window.current_price_krw
    return min(window.current_price_krw, int(window.target_price_krw * 1.01))


def _cadence(window: ProductDealWindow) -> str:
    if window.status == CheckStatus.ok:
        return "결제 전 1회 최종 확인"
    if window.status == CheckStatus.warning:
        return "매일 오전 1회, 쿠폰/카드 조건 변동 시 즉시 확인"
    return "3일마다 확인, 목표가 도달 알림만 즉시 확인"


def _alert_reason(window: ProductDealWindow, gap: int) -> str:
    if window.status == CheckStatus.ok:
        return "이미 예산권이라 옵션명과 최종 결제 금액만 틀어지지 않으면 됩니다."
    if window.status == CheckStatus.warning:
        return f"목표가까지 {gap:,}원 차이라 쿠폰/카드 조건 한 번으로 결제권에 들어올 수 있습니다."
    return f"목표가까지 {gap:,}원 이상 차이가 있어 대기 없이는 과소비 가능성이 큽니다."


def _notification_copy(window: ProductDealWindow, alert_threshold_krw: int) -> str:
    if window.status == CheckStatus.ok:
        return f"{window.model_name} 최종가가 {window.current_price_krw:,}원입니다. 옵션/AS 조건 확인 후 결제하세요."
    return (
        f"{window.model_name}이 {alert_threshold_krw:,}원 이하로 내려왔습니다. "
        f"결제 전 조건: {window.buy_trigger}"
    )


def _decision_rule(window: ProductDealWindow) -> str:
    if window.status == CheckStatus.ok:
        return "장바구니 가격, 배송비, 판매자, 반품/AS 조건이 현재 스냅샷과 같으면 결제합니다."
    if window.status == CheckStatus.warning:
        return "목표가 이하이면서 판매자/배송비/쿠폰 조건이 바뀌지 않았을 때만 결제 검토합니다."
    return "목표가 이하로 내려와도 예산 승인 또는 고성능 작업 목적이 확정되지 않으면 보류합니다."


def _fallback_action(window: ProductDealWindow) -> str:
    if window.status == CheckStatus.ok:
        return "조건이 달라졌다면 공개 후보 비교표로 같은 예산대 대체 후보를 다시 확인합니다."
    if window.status == CheckStatus.warning:
        return "48시간 안에 목표가가 오지 않으면 현재 결제 가능 후보와 다시 비교합니다."
    return "7일 안에 목표가가 오지 않으면 예산을 유지하고 상위 후보를 제외합니다."


def _primary_watch(candidates: list[PriceWatchCandidate]) -> PriceWatchCandidate | None:
    if not candidates:
        return None
    waiting = [item for item in candidates if item.status != CheckStatus.ok]
    pool = waiting or candidates
    return sorted(
        pool,
        key=lambda item: (
            0 if item.status == CheckStatus.warning else 1,
            item.target_gap_krw,
            item.current_price_krw,
        ),
    )[0]


def _primary_label(primary: PriceWatchCandidate | None) -> str:
    if primary is None:
        return "감시 후보 없음"
    if primary.status == CheckStatus.ok:
        return "즉시 결제 전 최종 확인"
    if primary.status == CheckStatus.warning:
        return "목표가 근접 알림"
    return "고가 후보 보류 알림"


def _alert_script(
    category_label: str,
    primary: PriceWatchCandidate | None,
    candidates: list[PriceWatchCandidate],
) -> str:
    if primary is None:
        return f"{category_label} 후보가 비어 있습니다. 예산과 목적을 다시 입력하세요."
    watch_count = sum(1 for item in candidates if item.status != CheckStatus.ok)
    return (
        f"{category_label} {watch_count}개 후보를 목표가 알림에 등록합니다. "
        f"1순위는 {primary.model_name}, 기준가는 {primary.alert_threshold_krw:,}원입니다. "
        "알림이 오면 옵션명, 판매자, 배송비, 쿠폰/카드 조건을 캡처한 뒤 결제 판단으로 이동하세요."
    )


def _analysis_prefill(
    category_label: str,
    budget_krw: int,
    purpose: str,
    primary: PriceWatchCandidate | None,
) -> str:
    if primary is None:
        return f"{category_label}를 {budget_krw:,}원 예산으로 살 수 있게 목표가 후보를 다시 찾아줘."
    return (
        f"{category_label}를 {budget_krw:,}원 예산으로 구매하려고 해. 목적은 {purpose}이고 "
        f"{primary.model_name}을 {primary.alert_threshold_krw:,}원 이하 목표가로 감시하려고 해. "
        "알림이 왔을 때 바로 결제해도 되는지 옵션/판매자/배송비/AS 조건까지 검수해줘."
    )


def _share_copy(
    category_label: str,
    budget_krw: int,
    primary: PriceWatchCandidate | None,
    candidates: list[PriceWatchCandidate],
) -> str:
    lines = [
        "SpecPilot AI 공개 목표가 감시",
        f"- 카테고리: {category_label}",
        f"- 예산: {budget_krw:,}원",
        f"- 1순위 알림: {primary.model_name if primary else '후보 없음'}",
    ]
    lines.extend(
        (
            f"- {item.model_name}: 현재 {item.current_price_krw:,}원, "
            f"알림 {item.alert_threshold_krw:,}원"
        )
        for item in candidates[:4]
    )
    lines.append("목표가가 오면 바로 결제할지, 대체 후보로 갈지 의견 부탁드립니다.")
    return "\n".join(lines)


def _next_actions(
    primary: PriceWatchCandidate | None,
    candidates: list[PriceWatchCandidate],
) -> list[str]:
    actions = [
        "목표가 후보는 가격만 보지 말고 판매자, 배송비, 쿠폰/카드 조건까지 같은 알림 메모에 남기세요.",
        "알림이 오면 장바구니 캡처를 먼저 만들고 옵션/사양 빠른 검수기로 마지막 오구매를 막으세요.",
        "48시간 이상 목표가가 오지 않으면 현재 결제 가능 후보와 가격 차이를 다시 비교하세요.",
    ]
    if primary and primary.status == CheckStatus.blocker:
        actions.insert(0, "1순위가 고가 보류 후보라면 예산 승인 없이 결제하지 않는 규칙을 먼저 고정하세요.")
    if any(item.status == CheckStatus.ok for item in candidates):
        actions.append("즉시 결제 후보는 목표가 알림이 아니라 결제 전 조건 변경 감시로 분리하세요.")
    return actions
