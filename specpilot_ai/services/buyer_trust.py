from specpilot_ai.core.models import (
    BuyerTrustBadge,
    CheckStatus,
    PublicBuyerTrustKit,
    TrustCenterDashboard,
)
from specpilot_ai.services.trust import build_trust_center


def build_public_buyer_trust_kit(
    *,
    limit: int = 4,
    trust_center: TrustCenterDashboard | None = None,
) -> PublicBuyerTrustKit:
    dashboard = trust_center or build_trust_center()
    badges = _badges(dashboard, limit=max(3, min(6, limit)))
    return PublicBuyerTrustKit(
        generated_at=dashboard.generated_at,
        status=dashboard.overall_status,
        headline="구매 추천보다 먼저 신뢰 기준을 확인하세요.",
        summary=(
            "SpecPilot AI는 컴퓨터와 노트북 추천에서 가격 출처, 제휴 고지, "
            "개인정보 최소화, 사람 검수 기준을 구매자 언어로 먼저 공개합니다."
        ),
        trust_badges=badges,
        buyer_rights=dashboard.buyer_rights[:4],
        risk_disclosures=dashboard.risk_disclosures[:4],
        plain_language_guarantee=_plain_language_guarantee(dashboard),
        proof_strip=_proof_strip(dashboard, badges),
        next_actions=[
            "분석 결과의 가격과 장바구니 최종가가 다르면 결제 전 검수를 먼저 실행하세요.",
            "제휴 링크가 보이면 비제휴 대안과 추천 점수 기준을 함께 확인하세요.",
            "연락처를 남기기 전에는 공개 리포트 공유 범위와 보존 기준을 확인하세요.",
        ],
    )


def _badges(
    dashboard: TrustCenterDashboard,
    *,
    limit: int,
) -> list[BuyerTrustBadge]:
    priority = [
        "recommendation_fairness",
        "source_verification",
        "privacy",
        "human_review",
    ]
    gates_by_area = {gate.area: gate for gate in dashboard.operational_gates}
    selected = [gates_by_area[area] for area in priority if area in gates_by_area]
    if len(selected) < limit:
        selected.extend(
            gate
            for gate in dashboard.operational_gates
            if gate.area not in {item.area for item in selected}
        )
    return [
        BuyerTrustBadge(
            badge_id=gate.area,
            label=gate.label,
            status=gate.status,
            summary=gate.public_message,
            evidence=gate.evidence[:3],
            buyer_impact=gate.buyer_impact,
        )
        for gate in selected[:limit]
    ]


def _plain_language_guarantee(dashboard: TrustCenterDashboard) -> str:
    commitments = dashboard.public_commitments[:3]
    return (
        "최저가 하나만 밀지 않고, "
        f"{' / '.join(commitments)} "
        "이 기준을 어기는 후보는 결제 가능이 아니라 확인 필요 또는 보류로 표시합니다."
    )


def _proof_strip(
    dashboard: TrustCenterDashboard,
    badges: list[BuyerTrustBadge],
) -> list[str]:
    ok_count = sum(1 for badge in badges if badge.status == CheckStatus.ok)
    warning_count = sum(1 for badge in badges if badge.status == CheckStatus.warning)
    return [
        f"신뢰 배지 {len(badges)}개 공개",
        f"ok {ok_count}개 · warning {warning_count}개",
        f"구매자 권리 {len(dashboard.buyer_rights[:4])}개",
        "가격·제휴·개인정보 기준 분리",
    ]
