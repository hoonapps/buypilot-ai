from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    CheckStatus,
    GrowthEventType,
    LaunchCampaignKit,
    LaunchChannelPlaybook,
    LaunchCopyVariant,
    LaunchDistributionPlan,
    LaunchDistributionSlot,
    LaunchExperimentDashboard,
    LaunchPulseDashboard,
    PublicAcquisitionSurface,
    PublicConversionBoard,
    WaitlistReferralDashboard,
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


def build_launch_distribution_plan(
    *,
    workspace_id: str,
    kit: LaunchCampaignKit,
    board: PublicConversionBoard,
    pulse: LaunchPulseDashboard,
    experiments: LaunchExperimentDashboard,
    referrals: WaitlistReferralDashboard,
) -> LaunchDistributionPlan:
    distribution_score = round(
        board.conversion_score * 0.42
        + pulse.pulse_score * 0.28
        + min(100.0, experiments.total_impressions * 1.5 + experiments.total_conversions * 16)
        * 0.16
        + min(100.0, referrals.total_referrals * 12 + referrals.referred_signup_count * 22)
        * 0.14,
        1,
    )
    status = _distribution_status(distribution_score, board.status, pulse.status)
    priority_channels = _priority_channels(board, kit)
    slots = _distribution_slots(
        kit=kit,
        board=board,
        priority_channels=priority_channels,
        best_variant_label=experiments.best_variant_label,
    )
    experiment_to_promote = experiments.best_variant_label or (
        experiments.recommended_experiments[0].name
        if experiments.recommended_experiments
        else ""
    )
    return LaunchDistributionPlan(
        workspace_id=workspace_id,
        generated_at=datetime.now(UTC).isoformat(),
        category=kit.category,
        audience=kit.audience,
        launch_window="D-day부터 D+7까지",
        status=status,
        distribution_score=distribution_score,
        headline=_distribution_headline(status, distribution_score),
        summary=(
            f"전환 보드 {board.conversion_score}점, Pulse {pulse.pulse_score}점, "
            f"추천 대기열 {referrals.total_referrals}명, CTA 실험 전환 "
            f"{experiments.total_conversions}건을 기준으로 첫 주 배포 순서를 정했습니다."
        ),
        primary_cta=kit.primary_cta,
        priority_channels=priority_channels,
        experiment_to_promote=experiment_to_promote,
        slots=slots,
        measurement_events=_distribution_measurement_events(kit, board),
        risk_controls=[
            "가격과 쿠폰 변동 가능성을 모든 외부 문구 하단에 고지",
            "제휴 링크와 추천 순위 계산 기준을 Trust Center로 연결",
            "커뮤니티 반응은 성장 이벤트와 피드백으로만 기록하고 원문 연락처는 저장하지 않기",
        ],
        next_actions=_distribution_next_actions(
            status=status,
            board=board,
            pulse=pulse,
            experiments=experiments,
            referrals=referrals,
        ),
    )


def _distribution_slots(
    *,
    kit: LaunchCampaignKit,
    board: PublicConversionBoard,
    priority_channels: list[str],
    best_variant_label: str,
) -> list[LaunchDistributionSlot]:
    phases = ["D-day 오전", "D-day 저녁", "D+1", "D+3", "D+7"]
    surface_by_channel = {surface.channel: surface for surface in board.priority_surfaces}
    slots: list[LaunchDistributionSlot] = []
    ordered_playbooks = sorted(
        kit.channel_playbooks,
        key=lambda playbook: (
            priority_channels.index(playbook.channel)
            if playbook.channel in priority_channels
            else 99
        ),
    )
    for index, playbook in enumerate(ordered_playbooks[:5]):
        variant = _slot_variant(playbook)
        if variant is None:
            continue
        surface = surface_by_channel.get(playbook.channel)
        cta_path = surface.path if surface else variant.cta_path
        priority = max(1, 10 - index * 2)
        status = surface.status if surface else CheckStatus.warning
        headline = (
            f"{best_variant_label}: {variant.headline}"
            if best_variant_label and index == 0
            else variant.headline
        )
        copy_text = (
            f"{headline}\n\n{variant.body}\n\n"
            f"{variant.cta_label}: {cta_path}\n"
            f"측정 이벤트: {variant.tracking_event.value}"
        )
        slots.append(
            LaunchDistributionSlot(
                slot_id=f"{playbook.channel}-{index + 1}",
                phase=phases[index],
                channel=playbook.channel,
                timing=playbook.post_timing,
                audience=playbook.audience,
                priority=priority,
                status=status,
                headline=headline,
                body=variant.body,
                cta_label=variant.cta_label,
                cta_path=cta_path,
                copy_text=copy_text,
                tracking_event=variant.tracking_event,
                success_metric=playbook.success_metric,
                proof_to_attach=_slot_proof(kit, surface),
                checklist=playbook.checklist[:3],
            )
        )
    return slots


def _slot_variant(playbook: LaunchChannelPlaybook) -> LaunchCopyVariant | None:
    if not playbook.copy_variants:
        return None
    return playbook.copy_variants[0]


def _slot_proof(
    kit: LaunchCampaignKit,
    surface: PublicAcquisitionSurface | None,
) -> list[str]:
    proof = kit.proof_points[:2]
    if surface is not None:
        proof.append(f"{surface.label}: {surface.metric}")
        proof.append(surface.proof)
    return list(dict.fromkeys(proof))[:4]


def _priority_channels(
    board: PublicConversionBoard,
    kit: LaunchCampaignKit,
) -> list[str]:
    channels = [surface.channel for surface in board.priority_surfaces]
    channels.extend(playbook.channel for playbook in kit.channel_playbooks)
    return list(dict.fromkeys(channels))


def _distribution_status(
    score: float,
    board_status: CheckStatus,
    pulse_status: CheckStatus,
) -> CheckStatus:
    if score >= 72 and board_status != CheckStatus.blocker and pulse_status != CheckStatus.blocker:
        return CheckStatus.ok
    if score >= 45 and board_status != CheckStatus.blocker:
        return CheckStatus.warning
    return CheckStatus.blocker


def _distribution_headline(status: CheckStatus, score: float) -> str:
    if status == CheckStatus.ok:
        return f"출시 배포 플랜 {score}점, 첫 주 채널 배포를 시작할 수 있습니다."
    if status == CheckStatus.warning:
        return f"출시 배포 플랜 {score}점, 우선 채널부터 제한 배포하세요."
    return f"출시 배포 플랜 {score}점, 공개 배포 전 증거 보강이 필요합니다."


def _distribution_measurement_events(
    kit: LaunchCampaignKit,
    board: PublicConversionBoard,
) -> list[str]:
    events = [
        f"{playbook.channel}: {variant.tracking_event.value}"
        for playbook in kit.channel_playbooks
        for variant in playbook.copy_variants[:1]
    ]
    events.extend(f"stage:{stage.key}={stage.metric}" for stage in board.stages[:3])
    return list(dict.fromkeys(events))[:8]


def _distribution_next_actions(
    *,
    status: CheckStatus,
    board: PublicConversionBoard,
    pulse: LaunchPulseDashboard,
    experiments: LaunchExperimentDashboard,
    referrals: WaitlistReferralDashboard,
) -> list[str]:
    actions: list[str] = []
    if experiments.best_variant_label:
        actions.append(f"{experiments.best_variant_label} CTA를 첫 번째 배포 슬롯에 적용하세요.")
    else:
        actions.append("출시 실험 허브에서 커뮤니티 CTA variant를 먼저 seed 하세요.")
    actions.extend(board.next_actions[:2])
    actions.extend(pulse.top_actions[:1])
    if referrals.total_referrals < 5:
        actions.append("추천 초대 공유 키트를 대기열 가입 직후 화면에 노출해 첫 5명을 확보하세요.")
    if status == CheckStatus.blocker:
        actions.append(
            "공개 채널 배포 전 Trust Center, 공개 리포트, 추천 대기열 CTA를 먼저 점검하세요."
        )
    return list(dict.fromkeys(actions))[:6]


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
