from specpilot_ai.core.models import (
    CheckStatus,
    IntakeDiagnosisRequest,
    PurchaseOnboardingPlaybook,
    PurchaseStartConcierge,
    StartConciergeAction,
    StartConciergeMilestone,
)
from specpilot_ai.services.intake import diagnose_intake
from specpilot_ai.services.onboarding import purchase_onboarding_playbooks


def build_start_concierge(
    request: IntakeDiagnosisRequest,
) -> PurchaseStartConcierge:
    diagnosis = diagnose_intake(request)
    playbook = _match_playbook(request)
    status = _readiness_status(diagnosis.readiness_score, diagnosis.missing_slots)
    primary_action = _primary_action(status)

    return PurchaseStartConcierge(
        category=request.category,
        readiness_score=diagnosis.readiness_score,
        headline=_headline(status, diagnosis.readiness_score, playbook),
        summary=_summary(status, diagnosis, playbook),
        primary_action=primary_action,
        matched_playbook=playbook,
        diagnosis=diagnosis,
        milestones=_milestones(status, diagnosis),
        quick_actions=_quick_actions(status),
        proof_points=_proof_points(playbook, diagnosis),
        conversion_prompt=_conversion_prompt(status, playbook),
    )


def _match_playbook(request: IntakeDiagnosisRequest) -> PurchaseOnboardingPlaybook:
    playbooks = purchase_onboarding_playbooks(category=request.category)
    if not playbooks:
        return purchase_onboarding_playbooks()[0]

    haystack = " ".join(
        [
            request.query,
            request.purpose,
            " ".join(request.must_haves),
            " ".join(request.exclusions),
        ]
    ).lower()

    def score(playbook: PurchaseOnboardingPlaybook) -> int:
        signals = [
            playbook.persona,
            playbook.title,
            playbook.purpose,
            playbook.hero_query,
            *playbook.must_haves,
            *playbook.readiness_slots,
        ]
        return sum(1 for signal in signals if _signal_hit(signal, haystack))

    return max(playbooks, key=score)


def _signal_hit(signal: str, haystack: str) -> bool:
    tokens = [
        token.strip().lower()
        for token in signal.replace("/", " ").replace(",", " ").split()
        if len(token.strip()) >= 2
    ]
    return any(token in haystack for token in tokens)


def _readiness_status(score: float, missing_slots: list[str]) -> CheckStatus:
    if missing_slots:
        return CheckStatus.blocker
    if score < 78:
        return CheckStatus.warning
    return CheckStatus.ok


def _primary_action(status: CheckStatus) -> StartConciergeAction:
    if status == CheckStatus.blocker:
        return StartConciergeAction(
            label="질문에 답하고 조건 보강",
            target="#analysis",
            action_type="complete_intake",
            reason=(
                "예산, 목적, 구매 요청 중 일부가 비어 있어 "
                "바로 추천하면 오추천 가능성이 큽니다."
            ),
        )
    if status == CheckStatus.warning:
        return StartConciergeAction(
            label="진단 조건 적용 후 분석",
            target="#analysis",
            action_type="apply_and_analyze",
            reason="분석은 가능하지만 필수 조건과 제외 조건을 보강하면 비교표 정확도가 올라갑니다.",
        )
    return StartConciergeAction(
        label="바로 분석 실행",
        target="#analysis",
        action_type="run_analysis",
        reason="현재 입력으로 후보 수집, 가격 비교, 호환성 검수까지 시작할 수 있습니다.",
    )


def _headline(
    status: CheckStatus,
    score: float,
    playbook: PurchaseOnboardingPlaybook,
) -> str:
    if status == CheckStatus.ok:
        return f"{playbook.title} 흐름으로 바로 분석 가능합니다."
    if status == CheckStatus.warning:
        return f"{playbook.title} 흐름에 맞지만 {score}점 보강이 필요합니다."
    return f"{playbook.title} 흐름으로 시작하되 핵심 조건을 먼저 채워야 합니다."


def _summary(
    status: CheckStatus,
    diagnosis,
    playbook: PurchaseOnboardingPlaybook,
) -> str:
    if status == CheckStatus.ok:
        return (
            f"준비도 {diagnosis.readiness_score}점입니다. "
            f"{playbook.readiness_slots[0]}부터 결제 전 검수까지 이어지는 플레이북을 적용하세요."
        )
    if status == CheckStatus.warning:
        return (
            f"준비도 {diagnosis.readiness_score}점입니다. "
            "분석은 가능하지만 추천 질문에 답하면 "
            "가격 타이밍과 조건 충족 매트릭스가 더 선명해집니다."
        )
    missing = ", ".join(diagnosis.missing_slots[:3])
    return (
        f"준비도 {diagnosis.readiness_score}점입니다. "
        f"{missing} 항목을 먼저 채우면 첫 분석 이탈을 줄일 수 있습니다."
    )


def _milestones(
    status: CheckStatus,
    diagnosis,
) -> list[StartConciergeMilestone]:
    return [
        StartConciergeMilestone(
            step="01",
            title="구매 조건 확정",
            status=status,
            detail=diagnosis.next_action,
            next_action=(
                diagnosis.clarifying_questions[0]
                if diagnosis.clarifying_questions
                else "현재 조건으로 분석을 실행하세요."
            ),
        ),
        StartConciergeMilestone(
            step="02",
            title="추천 리포트 생성",
            status=CheckStatus.ok if status != CheckStatus.blocker else CheckStatus.warning,
            detail="후보 수집, 가격 비교, 리뷰 리스크, 호환성 검수를 한 리포트로 묶습니다.",
            next_action="진단된 조건을 분석 폼에 적용하고 분석을 실행하세요.",
        ),
        StartConciergeMilestone(
            step="03",
            title="공유와 가격 대기",
            status=(
                CheckStatus.warning
                if diagnosis.normalized_request.budget_krw is None
                else CheckStatus.ok
            ),
            detail="공개 리포트와 목표가 알림으로 구매 결정을 놓치지 않게 합니다.",
            next_action="최종 후보가 나오면 공유 링크와 가격 알림을 생성하세요.",
        ),
        StartConciergeMilestone(
            step="04",
            title="결제 전 검수",
            status=CheckStatus.ok,
            detail=(
                "판매 페이지 옵션명, 최종가, 배송비, AS, "
                "반품 조건을 구매 직전에 다시 확인합니다."
            ),
            next_action="결제 전 검수 질문을 저장 리포트에 남기세요.",
        ),
    ]


def _quick_actions(status: CheckStatus) -> list[StartConciergeAction]:
    actions = [_primary_action(status)]
    actions.extend(
        [
            StartConciergeAction(
                label="맞춤 플레이북 보기",
                target="#onboarding",
                action_type="review_playbook",
                reason="비슷한 구매자의 입력 슬롯과 검수 게이트를 먼저 확인합니다.",
            ),
            StartConciergeAction(
                label="Trust Center 확인",
                target="#trust-center",
                action_type="review_trust",
                reason="가격 출처, 제휴 고지, 공개 리포트 정책을 구매 전에 확인합니다.",
            ),
        ]
    )
    return actions


def _proof_points(
    playbook: PurchaseOnboardingPlaybook,
    diagnosis,
) -> list[str]:
    proof = [
        f"매칭 플레이북: {playbook.title}",
        f"준비도: {diagnosis.readiness_score}점 / {diagnosis.readiness_label}",
        f"필수 입력 슬롯: {', '.join(playbook.readiness_slots[:4])}",
    ]
    proof.extend(playbook.trust_gates[:2])
    return proof


def _conversion_prompt(
    status: CheckStatus,
    playbook: PurchaseOnboardingPlaybook,
) -> str:
    if status == CheckStatus.blocker:
        return "첫 분석 전에 질문 1~2개만 더 채우면 추천 실패 가능성을 크게 줄일 수 있습니다."
    if status == CheckStatus.warning:
        return "조건을 적용하고 바로 분석하면 공유 리포트와 가격 알림까지 이어집니다."
    return (
        f"{playbook.recommended_plan_id} 플랜 흐름에 맞춰 "
        "분석, 공유, 결제 전 검수까지 진행하세요."
    )
