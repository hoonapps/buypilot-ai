from datetime import UTC, datetime

from specpilot_ai.core.models import (
    CandidateCompareItem,
    Category,
    CheckStatus,
    PublicSpecRescueKit,
    SpecRescueAlternative,
    SpecRescueRequest,
)
from specpilot_ai.services.candidate_compare import build_public_candidate_compare


def build_public_spec_rescue_kit(
    request: SpecRescueRequest,
    *,
    generated_at: datetime | None = None,
) -> PublicSpecRescueKit:
    generated_at = generated_at or datetime.now(UTC)
    purpose = request.purpose.strip() or _default_purpose(request.category)
    compare = build_public_candidate_compare(
        category=request.category,
        budget_krw=request.budget_krw,
        purpose=purpose,
        generated_at=generated_at,
    )
    alternatives = _rescue_alternatives(request, compare.items)
    priority = _rescue_priority(request)
    category_label = _category_label(request.category)
    return PublicSpecRescueKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        product_title=request.product_title,
        verdict=request.verdict,
        rescue_priority=priority,
        headline=_headline(request, category_label, alternatives),
        summary=_summary(request, alternatives),
        decision_rule=_decision_rule(request),
        seller_message=_seller_message(request),
        alternatives=alternatives,
        analysis_prefill=_analysis_prefill(request, category_label, purpose, alternatives),
        share_copy=_share_copy(request, category_label, alternatives),
        next_actions=_next_actions(request, alternatives),
    )


def _rescue_alternatives(
    request: SpecRescueRequest,
    items: list[CandidateCompareItem],
) -> list[SpecRescueAlternative]:
    current_title = _normalize(request.product_title)
    filtered = [
        item
        for item in items
        if current_title not in _normalize(item.model_name)
        and _normalize(item.model_name) not in current_title
    ]
    if len(filtered) < 3:
        filtered = items
    ranked = sorted(
        filtered,
        key=lambda item: (
            item.status != CheckStatus.ok,
            item.status == CheckStatus.blocker,
            max(0, item.effective_price_krw - request.budget_krw),
            -item.score,
        ),
    )
    return [
        SpecRescueAlternative(
            alternative_id=f"rescue-{index + 1}",
            product_id=item.product_id,
            model_name=item.model_name,
            role_label=item.role_label,
            effective_price_krw=item.effective_price_krw,
            price_delta_krw=item.effective_price_krw - request.budget_krw,
            status=item.status,
            option_summary=item.option_summary,
            rescue_reason=_rescue_reason(request, item),
            tradeoff=_tradeoff(item),
            evidence=item.evidence[:3],
            search_query=_search_query(request.category, item),
        )
        for index, item in enumerate(ranked[:3])
    ]


def _rescue_priority(request: SpecRescueRequest) -> CheckStatus:
    verdict = request.verdict.lower()
    if verdict == "hold" or request.blocker_count > 0:
        return CheckStatus.blocker
    if verdict == "verify" or request.warning_count > 0 or request.missing_evidence:
        return CheckStatus.warning
    return CheckStatus.ok


def _headline(
    request: SpecRescueRequest,
    category_label: str,
    alternatives: list[SpecRescueAlternative],
) -> str:
    if _rescue_priority(request) == CheckStatus.blocker:
        return f"결제 보류 후보 대신 {category_label} 대체안 {len(alternatives)}개를 바로 제안합니다."
    if _rescue_priority(request) == CheckStatus.warning:
        return f"확인 필요 후보와 비교할 {category_label} 안전 대안을 준비했습니다."
    return f"결제 가능 후보도 {category_label} 대안과 한 번 더 비교하세요."


def _summary(request: SpecRescueRequest, alternatives: list[SpecRescueAlternative]) -> str:
    missing = ", ".join(request.missing_evidence[:2]) if request.missing_evidence else "옵션명/가격"
    best = alternatives[0].model_name if alternatives else "대체 후보"
    return (
        f"{request.product_title}의 blocker {request.blocker_count}개, warning "
        f"{request.warning_count}개와 누락 증거({missing})를 기준으로 {best}부터 "
        "예산, 출처, 리스크가 낮은 순서로 다시 정렬했습니다."
    )


def _decision_rule(request: SpecRescueRequest) -> str:
    if request.blocker_count > 0:
        return "blocker가 1개라도 남아 있으면 현재 장바구니는 결제하지 말고 대체 후보를 먼저 비교합니다."
    if request.warning_count > 0 or request.missing_evidence:
        return "warning과 누락 증거를 판매자 답변으로 해소하지 못하면 대체 후보로 전환합니다."
    return "현재 후보는 결제 가능하지만, 같은 예산에서 더 낮은 리스크 후보가 있는지 1회 비교합니다."


def _seller_message(request: SpecRescueRequest) -> str:
    missing = ", ".join(request.missing_evidence[:3]) if request.missing_evidence else "최종 옵션명, 배송/반품/AS 조건"
    return (
        f"{request.product_title} 결제 전 확인 요청입니다. {missing}을 결제 전 화면 기준으로 "
        "답변해 주세요. 답변이 불명확하면 동일 예산의 대체 후보로 전환하겠습니다."
    )


def _rescue_reason(request: SpecRescueRequest, item: CandidateCompareItem) -> str:
    price_label = "예산 안" if item.effective_price_krw <= request.budget_krw else "예산 초과 승인 필요"
    if item.status == CheckStatus.ok:
        return f"{price_label}에서 리스크 상태가 ok라 현재 장바구니의 보류 사유를 피하는 대안입니다."
    if item.status == CheckStatus.warning:
        return f"{price_label} 후보이며 warning만 확인하면 현재 장바구니보다 검수 부담이 낮습니다."
    return f"{price_label} 후보지만 성능 장점이 커서 승인 비교용으로만 둡니다."


def _tradeoff(item: CandidateCompareItem) -> str:
    if item.status == CheckStatus.ok:
        return "최고 성능이나 최저가보다 출처 안정성과 결제 가능성을 우선합니다."
    if item.status == CheckStatus.warning:
        return "결제 전 재고, 옵션명, 반품/AS 조건 캡처가 필요합니다."
    return "성능은 매력적이지만 예산 초과나 리스크 승인이 필요합니다."


def _search_query(category: Category, item: CandidateCompareItem) -> str:
    suffix = "견적 옵션명 최종가 반품 AS" if category == Category.desktop_pc else "최종가 보증 반품 무게 배터리"
    return f"{item.model_name} {suffix}"


def _analysis_prefill(
    request: SpecRescueRequest,
    category_label: str,
    purpose: str,
    alternatives: list[SpecRescueAlternative],
) -> str:
    names = ", ".join(item.model_name for item in alternatives)
    return (
        f"{category_label} 구매에서 {request.product_title}은 결제 전 검수 결과 "
        f"{request.verdict}입니다. 예산 {request.budget_krw:,}원, 목적 {purpose} 기준으로 "
        f"대체 후보 {names}를 비교하고 TOP 3, 제외 후보, 결제 전 질문을 다시 정리해줘."
    )


def _share_copy(
    request: SpecRescueRequest,
    category_label: str,
    alternatives: list[SpecRescueAlternative],
) -> str:
    lines = [
        "SpecPilot AI 대체 후보 rescue",
        f"- 기존 장바구니: {request.product_title}",
        f"- 카테고리: {category_label}",
        f"- 판정: {request.verdict} / blocker {request.blocker_count}개 / warning {request.warning_count}개",
    ]
    lines.extend(
        f"- 대체 {index + 1}: {item.model_name} ({item.effective_price_krw:,}원, {item.status.value})"
        for index, item in enumerate(alternatives)
    )
    lines.append("현재 장바구니를 결제할지, 대체 후보로 바꿀지 의견 부탁드립니다.")
    return "\n".join(lines)


def _next_actions(
    request: SpecRescueRequest,
    alternatives: list[SpecRescueAlternative],
) -> list[str]:
    actions = [
        "현재 장바구니 판매자에게 확인 메시지를 보내고 답변 시각을 남기세요.",
        "대체 후보 1순위의 옵션명, 최종가, 반품/AS 조건을 같은 기준으로 캡처하세요.",
        "대체 후보와 현재 장바구니를 공유 문구로 함께 보내 반대 의견을 먼저 받으세요.",
    ]
    if request.cart_total_krw and alternatives:
        delta = alternatives[0].effective_price_krw - request.cart_total_krw
        direction = "비쌉니다" if delta > 0 else "저렴합니다"
        actions.insert(
            1,
            f"대체 1순위는 현재 장바구니보다 {abs(delta):,}원 {direction}. 가격 차이 승인 기준을 정하세요.",
        )
    return actions


def _category_label(category: Category) -> str:
    return "노트북" if category == Category.laptop else "데스크톱 PC"


def _default_purpose(category: Category) -> str:
    return "portable_creator" if category == Category.laptop else "qhd_creator"


def _normalize(value: str) -> str:
    return "".join(value.lower().split())
