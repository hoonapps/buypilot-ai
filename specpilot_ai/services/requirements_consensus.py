from collections import defaultdict
from datetime import UTC, datetime

from specpilot_ai.core.models import (
    AnalyzeRequest,
    ApprovalCopyVariant,
    Category,
    CheckStatus,
    PublicRequirementsConsensusKit,
    RequirementsConflict,
    RequirementsConsensusRequest,
    RequirementStakeholderInput,
    StakeholderConsensusSummary,
)


def build_public_requirements_consensus_kit(
    request: RequirementsConsensusRequest,
    generated_at: datetime | None = None,
) -> PublicRequirementsConsensusKit:
    generated_at = generated_at or datetime.now(UTC)
    stakeholders = _stakeholders(request)
    budget = _budget_krw(request, stakeholders)
    purpose = _purpose(request, stakeholders)
    agreed_must_haves = _weighted_terms(stakeholders, "must_haves", minimum_weight=2)[:10]
    agreed_nice_to_haves = _weighted_terms(stakeholders, "nice_to_haves", minimum_weight=1)[:8]
    agreed_exclusions = _unique_terms(
        term
        for stakeholder in stakeholders
        for term in _clean_lines(stakeholder.deal_breakers)
    )[:10]
    conflicts = _conflicts(request, stakeholders, budget)
    score = _consensus_score(stakeholders, conflicts, agreed_must_haves, budget)
    status = _consensus_status(score, conflicts)
    recommended_request = _recommended_request(
        request=request,
        budget=budget,
        purpose=purpose,
        must_haves=agreed_must_haves,
        exclusions=agreed_exclusions,
    )
    analysis_prefill = _analysis_prefill(
        request=request,
        status=status,
        recommended_request=recommended_request,
        conflicts=conflicts,
    )
    return PublicRequirementsConsensusKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        consensus_status=status,
        consensus_score=score,
        headline=_headline(request, status, score),
        summary=_summary(request, stakeholders, budget, status, conflicts),
        budget_krw=budget,
        purpose=purpose,
        agreed_must_haves=agreed_must_haves,
        agreed_nice_to_haves=agreed_nice_to_haves,
        agreed_exclusions=agreed_exclusions,
        conflict_count=len(conflicts),
        conflicts=conflicts,
        stakeholders=_stakeholder_summaries(stakeholders, conflicts),
        decision_rules=_decision_rules(status, budget, conflicts, agreed_exclusions),
        recommended_request=recommended_request,
        copy_variants=_copy_variants(request, status, score, analysis_prefill),
        analysis_prefill=analysis_prefill,
        share_copy=_share_copy(request, status, score, analysis_prefill),
        next_actions=_next_actions(status, conflicts),
    )


def _stakeholders(request: RequirementsConsensusRequest) -> list[RequirementStakeholderInput]:
    if request.stakeholders:
        return request.stakeholders[:8]
    return [
        RequirementStakeholderInput(
            name="구매자",
            role="buyer",
            priority="high",
            max_budget_krw=request.shared_budget_krw,
            use_cases=[request.purchase_context or "컴퓨터 구매"],
            must_haves=["목적에 맞는 성능", "국내 AS"],
            deal_breakers=["반품 불가", "모델명 불일치"],
            timeline=request.target_timing,
            risk_tolerance="medium",
        )
    ]


def _category_label(category: Category) -> str:
    return "노트북" if category == Category.laptop else "데스크톱 PC"


def _clean_lines(values: list[str]) -> list[str]:
    return [value.strip() for value in values if value.strip()]


def _unique_terms(values: object) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(cleaned)
    return output


def _priority_weight(priority: str) -> int:
    normalized = priority.strip().lower()
    if normalized in {"high", "owner", "critical", "높음"}:
        return 3
    if normalized in {"low", "optional", "낮음"}:
        return 1
    return 2


def _budget_krw(
    request: RequirementsConsensusRequest,
    stakeholders: list[RequirementStakeholderInput],
) -> int:
    if request.shared_budget_krw:
        return request.shared_budget_krw
    weighted: list[int] = []
    for stakeholder in stakeholders:
        if stakeholder.max_budget_krw:
            weighted.extend([stakeholder.max_budget_krw] * _priority_weight(stakeholder.priority))
    if weighted:
        weighted.sort()
        return weighted[len(weighted) // 2]
    return 1_600_000 if request.category == Category.laptop else 2_200_000


def _purpose(
    request: RequirementsConsensusRequest,
    stakeholders: list[RequirementStakeholderInput],
) -> str:
    context = request.purchase_context.strip()
    use_cases = _unique_terms(
        use_case
        for stakeholder in stakeholders
        for use_case in _clean_lines(stakeholder.use_cases)
    )
    if context and use_cases:
        return f"{context}: {', '.join(use_cases[:4])}"
    if context:
        return context
    if use_cases:
        return ", ".join(use_cases[:4])
    return f"{_category_label(request.category)} 구매 조건 합의"


def _weighted_terms(
    stakeholders: list[RequirementStakeholderInput],
    field_name: str,
    minimum_weight: int,
) -> list[str]:
    scores: dict[str, int] = defaultdict(int)
    labels: dict[str, str] = {}
    for stakeholder in stakeholders:
        terms = _clean_lines(getattr(stakeholder, field_name))
        for term in terms:
            key = term.casefold()
            scores[key] += _priority_weight(stakeholder.priority)
            labels.setdefault(key, term)
    ranked = sorted(scores.items(), key=lambda item: (-item[1], labels[item[0]].casefold()))
    return [labels[key] for key, score in ranked if score >= minimum_weight]


def _conflicts(
    request: RequirementsConsensusRequest,
    stakeholders: list[RequirementStakeholderInput],
    budget: int,
) -> list[RequirementsConflict]:
    conflicts: list[RequirementsConflict] = []
    budgets = [
        stakeholder.max_budget_krw
        for stakeholder in stakeholders
        if stakeholder.max_budget_krw is not None and stakeholder.max_budget_krw > 0
    ]
    if budgets:
        low = min(budgets)
        high = max(budgets)
        spread = high - low
        if spread >= max(200_000, int(budget * 0.18)):
            conflicts.append(
                RequirementsConflict(
                    conflict_id="budget_spread",
                    status=CheckStatus.blocker if high > low * 1.35 else CheckStatus.warning,
                    owners=_budget_owners(stakeholders, low, high),
                    issue=f"이해관계자 예산 상한이 {low:,}원~{high:,}원으로 벌어져 있습니다.",
                    resolution_rule="공유 예산을 먼저 확정하고 초과 사양은 nice-to-have로 내립니다.",
                )
            )

    urgent = [s.name for s in stakeholders if _urgent_timeline(s.timeline)]
    waiting = [s.name for s in stakeholders if _wait_timeline(s.timeline)]
    if urgent and waiting:
        conflicts.append(
            RequirementsConflict(
                conflict_id="timing_mismatch",
                status=CheckStatus.warning,
                owners=_unique_terms(urgent + waiting),
                issue="즉시 구매와 할인 대기 의견이 동시에 있습니다.",
                resolution_rule="필수 일정이 있는 사람을 기준으로 구매 마감일과 목표가 알림 기준을 나눕니다.",
            )
        )

    low_risk = [s.name for s in stakeholders if _low_risk(s.risk_tolerance)]
    risky_terms = [
        term
        for stakeholder in stakeholders
        for term in _clean_lines(stakeholder.must_haves + stakeholder.nice_to_haves)
        if _risky_term(term)
    ]
    if low_risk and risky_terms:
        conflicts.append(
            RequirementsConflict(
                conflict_id="risk_tolerance",
                status=CheckStatus.blocker,
                owners=low_risk,
                issue=f"낮은 리스크 선호와 충돌하는 조건이 있습니다: {', '.join(_unique_terms(risky_terms)[:3])}",
                resolution_rule="해외/리퍼/중고/보증 불명 조건은 제외 조건으로 올리거나 명시 승인자를 지정합니다.",
            )
        )

    must_terms = _unique_terms(
        term
        for stakeholder in stakeholders
        for term in _clean_lines(stakeholder.must_haves)
    )
    blockers = _unique_terms(
        term
        for stakeholder in stakeholders
        for term in _clean_lines(stakeholder.deal_breakers)
    )
    overlaps = [must for must in must_terms if any(_term_conflict(must, blocker) for blocker in blockers)]
    if overlaps:
        conflicts.append(
            RequirementsConflict(
                conflict_id="must_have_exclusion_overlap",
                status=CheckStatus.blocker,
                owners=[stakeholder.name for stakeholder in stakeholders],
                issue=f"필수 조건과 제외 조건이 충돌합니다: {', '.join(overlaps[:3])}",
                resolution_rule="충돌 조건은 후보 검색 전에 제외 조건을 우선 적용하고 예외 승인 조건을 따로 둡니다.",
            )
        )

    if len(stakeholders) == 1:
        conflicts.append(
            RequirementsConflict(
                conflict_id="single_stakeholder",
                status=CheckStatus.warning,
                owners=[stakeholders[0].name],
                issue="검토자가 한 명뿐이라 가족/팀/커뮤니티 반대 질문이 아직 반영되지 않았습니다.",
                resolution_rule="구매 전 한 명 이상에게 예산, AS, 반품 조건을 확인받습니다.",
            )
        )

    return conflicts[:6]


def _budget_owners(
    stakeholders: list[RequirementStakeholderInput],
    low: int,
    high: int,
) -> list[str]:
    return [
        stakeholder.name
        for stakeholder in stakeholders
        if stakeholder.max_budget_krw in {low, high}
    ]


def _urgent_timeline(value: str) -> bool:
    lowered = value.casefold()
    return any(term in lowered for term in ["today", "urgent", "immediate", "within_7", "오늘", "즉시"])


def _wait_timeline(value: str) -> bool:
    lowered = value.casefold()
    return any(term in lowered for term in ["wait", "discount", "month", "대기", "할인"])


def _low_risk(value: str) -> bool:
    return value.strip().casefold() in {"low", "safe", "보수", "낮음"}


def _risky_term(value: str) -> bool:
    lowered = value.casefold()
    return any(term in lowered for term in ["리퍼", "refurb", "중고", "used", "해외", "overseas", "병행"])


def _term_conflict(must: str, blocker: str) -> bool:
    must_lower = must.casefold()
    blocker_lower = blocker.casefold()
    exact_overlap = must_lower in blocker_lower or blocker_lower in must_lower
    gpu_conflict = "gpu" in must_lower and any(term in blocker_lower for term in ["gpu", "그래픽", "게이밍"])
    os_conflict = any(term in must_lower for term in ["windows", "윈도우"]) and any(
        term in blocker_lower for term in ["freedos", "os 미포함", "윈도우 없음"]
    )
    return exact_overlap or gpu_conflict or os_conflict


def _consensus_score(
    stakeholders: list[RequirementStakeholderInput],
    conflicts: list[RequirementsConflict],
    agreed_must_haves: list[str],
    budget: int | None,
) -> int:
    score = 88
    if len(stakeholders) >= 3:
        score += 5
    elif len(stakeholders) == 1:
        score -= 10
    if agreed_must_haves:
        score += min(6, len(agreed_must_haves) * 2)
    if not budget:
        score -= 8
    for conflict in conflicts:
        score -= 18 if conflict.status == CheckStatus.blocker else 9
    return max(0, min(100, score))


def _consensus_status(score: int, conflicts: list[RequirementsConflict]) -> CheckStatus:
    if score < 58 or any(conflict.status == CheckStatus.blocker for conflict in conflicts):
        return CheckStatus.blocker
    if score < 82 or conflicts:
        return CheckStatus.warning
    return CheckStatus.ok


def _stakeholder_summaries(
    stakeholders: list[RequirementStakeholderInput],
    conflicts: list[RequirementsConflict],
) -> list[StakeholderConsensusSummary]:
    blocker_owners = {
        owner
        for conflict in conflicts
        if conflict.status == CheckStatus.blocker
        for owner in conflict.owners
    }
    warning_owners = {owner for conflict in conflicts for owner in conflict.owners}
    summaries: list[StakeholderConsensusSummary] = []
    for stakeholder in stakeholders:
        status = (
            CheckStatus.blocker
            if stakeholder.name in blocker_owners
            else CheckStatus.warning
            if stakeholder.name in warning_owners
            else CheckStatus.ok
        )
        accepted_terms = _unique_terms(
            _clean_lines(stakeholder.must_haves)[:3] + _clean_lines(stakeholder.deal_breakers)[:2]
        )
        questions: list[str] = []
        if stakeholder.max_budget_krw is None:
            questions.append("예산 상한을 숫자로 확정해야 합니다.")
        if not stakeholder.deal_breakers:
            questions.append("반품/AS/해외/리퍼 제외 조건을 확인해야 합니다.")
        summaries.append(
            StakeholderConsensusSummary(
                name=stakeholder.name,
                role=stakeholder.role,
                priority=stakeholder.priority,
                status=status,
                accepted_terms=accepted_terms,
                open_questions=questions[:3],
            )
        )
    return summaries


def _decision_rules(
    status: CheckStatus,
    budget: int | None,
    conflicts: list[RequirementsConflict],
    exclusions: list[str],
) -> list[str]:
    rules = [
        f"최종 후보는 예산 {_money(budget)} 안에서만 비교합니다.",
        "필수 조건은 검색어와 옵션명 검수 기준에 그대로 넣습니다.",
        "제외 조건이 상품명/상세페이지/판매자 답변에 보이면 후보에서 제외합니다.",
    ]
    if exclusions:
        rules.append(f"우선 제외 조건: {', '.join(exclusions[:4])}")
    if conflicts:
        rules.append("warning/blocker 충돌은 추천 후보를 보기 전에 먼저 닫습니다.")
    if status == CheckStatus.blocker:
        rules.insert(0, "blocker가 남아 있으면 결제·승인 브리프로 넘어가지 않습니다.")
    return rules[:6]


def _recommended_request(
    request: RequirementsConsensusRequest,
    budget: int,
    purpose: str,
    must_haves: list[str],
    exclusions: list[str],
) -> AnalyzeRequest:
    category_label = _category_label(request.category)
    query = f"{category_label} {purpose} 예산 {budget:,}원 조건 합의 기반 추천"
    return AnalyzeRequest(
        query=query[:240],
        category=request.category,
        budget_krw=budget,
        purpose=purpose,
        must_haves=must_haves,
        exclusions=exclusions,
        purchase_timing=request.target_timing or "within_30_days",
        channels=["price_compare", "open_market", "community"],
    )


def _headline(
    request: RequirementsConsensusRequest,
    status: CheckStatus,
    score: int,
) -> str:
    label = _category_label(request.category)
    if status == CheckStatus.blocker:
        return f"{label} 구매 조건 합의 점수 {score}점, 후보 검색 전에 충돌을 닫아야 합니다."
    if status == CheckStatus.warning:
        return f"{label} 구매 조건은 거의 모였고, 남은 충돌만 확인하면 됩니다."
    return f"{label} 구매 조건이 분석 가능한 수준으로 합의됐습니다."


def _summary(
    request: RequirementsConsensusRequest,
    stakeholders: list[RequirementStakeholderInput],
    budget: int,
    status: CheckStatus,
    conflicts: list[RequirementsConflict],
) -> str:
    conflict_text = "충돌 없음" if not conflicts else f"충돌 {len(conflicts)}개"
    status_text = "바로 분석 가능" if status == CheckStatus.ok else "조건 확인 필요"
    return (
        f"{len(stakeholders)}명의 조건을 {_category_label(request.category)} 예산 {_money(budget)} 기준으로 "
        f"정리했습니다. 현재 상태는 {status_text}, {conflict_text}입니다."
    )


def _analysis_prefill(
    request: RequirementsConsensusRequest,
    status: CheckStatus,
    recommended_request: AnalyzeRequest,
    conflicts: list[RequirementsConflict],
) -> str:
    conflict_lines = [f"- {conflict.issue} 해결: {conflict.resolution_rule}" for conflict in conflicts]
    status_label = "합의 완료" if status == CheckStatus.ok else "조건부 합의"
    return (
        "SpecPilot AI 구매 조건 합의\n"
        f"- 상태: {status_label}\n"
        f"- 카테고리: {_category_label(request.category)}\n"
        f"- 예산: {_money(recommended_request.budget_krw)}\n"
        f"- 목적: {recommended_request.purpose}\n"
        f"- 필수 조건: {', '.join(recommended_request.must_haves) or '미입력'}\n"
        f"- 제외 조건: {', '.join(recommended_request.exclusions) or '미입력'}\n"
        + ("\n".join(conflict_lines) if conflict_lines else "- 충돌: 없음")
    )


def _copy_variants(
    request: RequirementsConsensusRequest,
    status: CheckStatus,
    score: int,
    analysis_prefill: str,
) -> list[ApprovalCopyVariant]:
    label = _category_label(request.category)
    status_text = "합의 완료" if status == CheckStatus.ok else "확인 필요"
    base = (
        f"{label} 구매 조건 합의 점수 {score}점, 상태 {status_text}입니다.\n"
        f"{analysis_prefill}"
    )
    return [
        ApprovalCopyVariant(
            channel="kakao",
            label="카카오톡 공유",
            copy_text=f"우리 {label} 구매 조건 이렇게 정리했어.\n{base}",
            cta_label="합의 조건 확인",
        ),
        ApprovalCopyVariant(
            channel="team",
            label="팀/가족 승인",
            copy_text=f"[SpecPilot AI 구매 조건 합의]\n{base}\n이 조건으로 후보를 좁혀도 될까요?",
            cta_label="승인 요청",
        ),
        ApprovalCopyVariant(
            channel="community",
            label="커뮤니티 검토",
            copy_text=f"{label} 구매 전 조건 합의표입니다.\n{base}\n빠진 조건이나 과한 조건이 있으면 알려주세요.",
            cta_label="검토 요청",
        ),
    ]


def _share_copy(
    request: RequirementsConsensusRequest,
    status: CheckStatus,
    score: int,
    analysis_prefill: str,
) -> str:
    status_text = "통과" if status == CheckStatus.ok else "확인 필요"
    return (
        "SpecPilot AI 구매 조건 합의\n"
        f"- 카테고리: {_category_label(request.category)}\n"
        f"- 점수: {score}점 / {status_text}\n"
        f"{analysis_prefill}"
    )


def _next_actions(
    status: CheckStatus,
    conflicts: list[RequirementsConflict],
) -> list[str]:
    if status == CheckStatus.blocker:
        return [
            "blocker 충돌의 승인자와 예외 조건을 먼저 정합니다.",
            "예산 상한과 제외 조건을 다시 공유한 뒤 후보 검색을 시작합니다.",
            "충돌이 닫히기 전에는 결제/승인 브리프로 넘어가지 않습니다.",
        ]
    if status == CheckStatus.warning:
        return [
            "warning 충돌을 구매 마감일, 목표가, 제외 조건으로 변환합니다.",
            "합의 조건으로 분석을 시작하고 후보별 예외를 따로 표시합니다.",
            "가족/팀/커뮤니티에 공유 문구를 보내 빠진 조건을 회수합니다.",
        ]
    return [
        "합의된 조건으로 바로 분석을 시작합니다.",
        "후보 비교 후 체크아웃 잠금과 결정 방어 브리프로 이어갑니다.",
        "공유 문구를 보내 결제 전 반대 질문을 미리 회수합니다.",
    ]


def _money(value: int | None) -> str:
    return f"{value:,}원" if value is not None else "미입력"
