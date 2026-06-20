from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    GrowthEventType,
    LaunchCampaignKit,
    LaunchChannelPlaybook,
    LaunchCopyVariant,
)


def build_launch_campaign_kit(
    category: Category | None = None,
    audience: str = "creator",
) -> LaunchCampaignKit:
    category_label = _category_label(category)
    audience_label = _audience_label(audience)
    offer = f"{category_label} 구매 실패를 줄이는 무료 AI 구매 리포트"
    return LaunchCampaignKit(
        generated_at=datetime.now(UTC).isoformat(),
        category=category,
        audience=audience,
        offer=offer,
        positioning=(
            "최저가 링크가 아니라 예산, 용도, 호환성, 가격 타이밍, 출처 신뢰를 "
            "함께 검수하는 PC/노트북 구매 의사결정 에이전트"
        ),
        hero_message=(
            f"{_with_subject_particle(audience_label)} {_with_object_particle(category_label)} "
            "고를 때 놓치기 쉬운 옵션, "
            "실구매가, 리스크를 한 번의 리포트로 확인합니다."
        ),
        primary_cta="내 조건으로 무료 리포트 만들기",
        primary_cta_path="/#analysis",
        proof_points=[
            "TOP 3 추천과 제외 후보 2개를 같은 기준으로 비교합니다.",
            "배송비, 쿠폰, 카드 할인, 조립비를 반영한 실구매가를 봅니다.",
            "호환성 차단, 리뷰 반복 불만, 벤치마크 근거를 분리해 표시합니다.",
            "결제 전 검수, 가격 알림, 공개 공유 리포트로 구매 행동까지 연결합니다.",
            "Trust Center에서 제휴 고지와 개인정보 노출 범위를 먼저 공개합니다.",
        ],
        target_segments=_target_segments(category, audience),
        channel_playbooks=[
            _community_playbook(category_label, audience_label),
            _search_playbook(category_label),
            _referral_playbook(category_label),
        ],
        cta_experiments=[
            "내 예산으로 PC/노트북 후보 5개 비교",
            "결제 전에 옵션/호환성 검수하기",
            "공개 리포트로 친구에게 구매 검토 받기",
            "목표가 도달 알림과 구매 보류 사유 확인",
        ],
        launch_checklist=[
            "공개 카테고리 리포트 2개를 최신 후보와 리스크로 갱신",
            "Trust Center와 제휴/비제휴 링크 정책을 첫 화면에서 접근 가능하게 유지",
            "추천 대기열 CTA와 추천 코드 공유 문구를 모든 공개 페이지에 연결",
            "성장 퍼널에서 analysis_view, share_cta, alert_cta, subscription_cta를 추적",
            "피드백과 베타 리드가 launch gate와 개선 백로그로 들어가는지 확인",
        ],
        risk_disclosures=[
            "가격과 쿠폰은 변동될 수 있으므로 결제 직전 재확인이 필요합니다.",
            "벤치마크는 목적별 참고 근거이며 실제 체감 성능을 보장하지 않습니다.",
            "제휴 링크는 명확히 고지하고 추천 순위 계산에는 직접 반영하지 않습니다.",
        ],
        measurement_plan=[
            "첫 방문 대비 분석 실행률",
            "추천 카드 클릭률과 공유 CTA율",
            "가격 알림 CTA율과 요금제 관심 등록률",
            "추천 만족도와 구매 의향률",
            "추천 대기열 추천 유입 수와 리더보드 상위 코드",
        ],
    )


def _community_playbook(
    category_label: str,
    audience_label: str,
) -> LaunchChannelPlaybook:
    return LaunchChannelPlaybook(
        channel="community",
        audience=audience_label,
        angle="견적 질문 전에 자기 조건으로 리포트를 먼저 만들게 한다",
        post_timing="평일 저녁과 주말 오전",
        success_metric="공유 CTA율과 피드백 만족도",
        copy_variants=[
            LaunchCopyVariant(
                variant_id="community-before-question",
                channel="community",
                headline=f"{category_label} 견적 질문 전에 AI 리포트로 조건을 정리해보세요",
                body=(
                    "예산, 목적, 필수 조건을 넣으면 후보 5개를 TOP 3와 제외 후보로 나누고 "
                    "실구매가, 호환성, 리뷰 리스크, 결제 전 체크리스트를 보여줍니다."
                ),
                cta_label="무료 리포트 만들기",
                cta_path="/#analysis",
            ),
            LaunchCopyVariant(
                variant_id="community-checkout-risk",
                channel="community",
                headline="결제 직전에 옵션명과 가격이 달라지는 문제를 줄입니다",
                body=(
                    "추천 결과를 공개 리포트로 공유하고, 최종 결제 금액과 판매자 답변을 "
                    "검수해 구매 가능/보류 상태를 확인할 수 있습니다."
                ),
                cta_label="결제 전 검수 보기",
                cta_path="/#checkout-review",
                tracking_event=GrowthEventType.alert_cta,
            ),
        ],
        checklist=[
            "게시글 첫 문장에 최저가 도구가 아니라 구매 실패 방지 도구임을 명확히 쓰기",
            "데스크톱/노트북 예시 쿼리를 하나씩 포함하기",
            "제휴 고지와 Trust Center 링크를 함께 노출하기",
        ],
    )


def _search_playbook(category_label: str) -> LaunchChannelPlaybook:
    return LaunchChannelPlaybook(
        channel="seo",
        audience="검색 유입 사용자",
        angle="월간 공개 카테고리 리포트에서 분석 폼으로 전환",
        post_timing="월간 리포트 갱신 직후",
        success_metric="공개 리포트 조회수와 analysis_view 전환율",
        copy_variants=[
            LaunchCopyVariant(
                variant_id="seo-monthly-report",
                channel="seo",
                headline=f"이번 달 {category_label} 구매 구간과 추천 후보 정리",
                body=(
                    "가격대, 추천 역할, 재고/리뷰 리스크, 공개 체크리스트를 먼저 보고 "
                    "자기 예산과 용도에 맞는 리포트로 이어갑니다."
                ),
                cta_label="시장 리포트 보기",
                cta_path="/market/desktop-pc",
                tracking_event=GrowthEventType.analysis_view,
            )
        ],
        checklist=[
            "canonical path와 공유 문구 확인",
            "추천 픽의 가격 구간과 리스크 신호 갱신",
            "공개 체크리스트에서 결제 전 검수 CTA 연결",
        ],
    )


def _referral_playbook(category_label: str) -> LaunchChannelPlaybook:
    return LaunchChannelPlaybook(
        channel="referral",
        audience="친구에게 구매 조언을 자주 받는 사용자",
        angle="초대 링크와 공개 리포트로 검토 루프 만들기",
        post_timing="분석 완료 직후와 리포트 공유 직후",
        success_metric="추천 대기열 가입 수와 referred signup count",
        copy_variants=[
            LaunchCopyVariant(
                variant_id="referral-invite",
                channel="referral",
                headline=f"{category_label} 구매 리포트를 같이 검토할 사람을 초대하세요",
                body=(
                    "초대 링크로 들어온 사용자는 자기 조건으로 리포트를 만들고, "
                    "추천 유입은 리더보드와 우선순위 점수에 반영됩니다."
                ),
                cta_label="초대 링크 만들기",
                cta_path="/#conversion",
                tracking_event=GrowthEventType.share_cta,
            )
        ],
        checklist=[
            "추천 코드가 생성되는지 확인",
            "공유 URL과 공개 리포트 URL을 분리해서 안내",
            "추천 유입 수와 우선순위 점수를 리더보드에 표시",
        ],
    )


def _target_segments(category: Category | None, audience: str) -> list[str]:
    if category == Category.laptop:
        return [
            "이동이 잦은 영상 편집자",
            "발열/무게/포트 조건을 같이 보는 노트북 구매자",
            "팀 사무용 노트북을 반복 구매하는 운영자",
        ]
    if audience == "team_buyer":
        return [
            "표준 사무용 PC/노트북을 반복 구매하는 팀",
            "가격, 재고, AS 조건을 동시에 확인해야 하는 관리자",
            "구매 결과를 리포트로 남겨야 하는 소규모 사업자",
        ]
    return [
        "첫 게이밍/작업용 데스크톱 구매자",
        "영상 편집과 QHD 게임을 같이 고려하는 크리에이터",
        "주변 검토를 받기 위해 공개 리포트가 필요한 구매자",
    ]


def _category_label(category: Category | None) -> str:
    if category == Category.laptop:
        return "노트북"
    if category == Category.desktop_pc:
        return "데스크톱 PC"
    return "컴퓨터와 노트북"


def _audience_label(audience: str) -> str:
    return {
        "creator": "크리에이터",
        "team_buyer": "팀 구매 담당자",
        "first_buyer": "첫 PC 구매자",
        "gamer": "게이밍 사용자",
    }.get(audience, audience or "구매자")


def _with_subject_particle(value: str) -> str:
    return f"{value}{'이' if _has_final_consonant(value) else '가'}"


def _with_object_particle(value: str) -> str:
    return f"{value}{'을' if _has_final_consonant(value) else '를'}"


def _has_final_consonant(value: str) -> bool:
    for character in reversed(value.strip()):
        code_point = ord(character)
        if 0xAC00 <= code_point <= 0xD7A3:
            return (code_point - 0xAC00) % 28 != 0
        return False
    return False
