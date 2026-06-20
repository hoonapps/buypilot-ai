from datetime import UTC, datetime

from specpilot_ai.core.models import (
    BuyerChecklistItem,
    BuyerChecklistSection,
    Category,
    CheckStatus,
    PublicBuyerChecklist,
)
from specpilot_ai.data.catalog import desktop_candidates, laptop_candidates, price_snapshot_for
from specpilot_ai.services.onboarding import purchase_onboarding_playbooks


def build_public_buyer_checklist(
    *,
    category: Category | None = None,
    budget_krw: int | None = None,
    persona: str = "first_pc_buyer",
    generated_at: datetime | None = None,
) -> PublicBuyerChecklist:
    generated_at = generated_at or datetime.now(UTC)
    target_category = category or Category.desktop_pc
    target_budget = _normalized_budget(target_category, budget_krw)
    playbook = _matched_playbook(target_category, persona)
    market = _budget_market_state(target_category, target_budget, generated_at)
    sections = _sections(target_category, persona, market["status"])
    readiness_score = _readiness_score(sections, market["status"])
    return PublicBuyerChecklist(
        generated_at=generated_at.isoformat(),
        category=target_category,
        persona=persona.strip() or playbook.persona,
        budget_krw=target_budget,
        headline=_headline(target_category, target_budget, market["status"]),
        summary=_summary(playbook.title, market["fit"], market["candidate_count"]),
        readiness_score=readiness_score,
        budget_fit=market["fit"],
        analysis_prefill=_analysis_prefill(target_category, target_budget, playbook),
        sections=sections,
        red_flags=_red_flags(target_category, market["status"]),
        evidence_to_capture=_evidence_to_capture(target_category),
        share_copy=_share_copy(target_category, target_budget, readiness_score),
        next_actions=_next_actions(market["status"], readiness_score),
    )


def _normalized_budget(category: Category, budget_krw: int | None) -> int:
    if budget_krw and budget_krw > 0:
        return min(10_000_000, max(300_000, budget_krw))
    if category == Category.laptop:
        return 2_000_000
    return 2_200_000


def _matched_playbook(category: Category, persona: str):
    playbooks = purchase_onboarding_playbooks(category=category)
    normalized = persona.strip().lower()
    if normalized:
        for playbook in playbooks:
            if normalized in {playbook.persona.lower(), playbook.playbook_id.lower()}:
                return playbook
    return playbooks[0]


def _budget_market_state(
    category: Category,
    budget_krw: int,
    generated_at: datetime,
) -> dict[str, int | str | CheckStatus]:
    candidates = desktop_candidates() if category == Category.desktop_pc else laptop_candidates()
    captured_at = generated_at.isoformat()
    prices = [
        price_snapshot_for(product, captured_at).effective_price_krw
        for product in candidates
    ]
    affordable = [price for price in prices if price <= budget_krw]
    if not affordable:
        return {
            "status": CheckStatus.blocker,
            "candidate_count": 0,
            "fit": "예산 안에 안정적으로 들어오는 후보가 거의 없습니다.",
        }
    if len(affordable) < 2:
        return {
            "status": CheckStatus.warning,
            "candidate_count": len(affordable),
            "fit": "예산 안 후보가 적어 대안 시나리오와 가격 알림이 필요합니다.",
        }
    if budget_krw >= int(sorted(prices)[len(prices) // 2] * 1.08):
        fit = "예산 여유가 있어 성능·AS·재고 안정성을 함께 비교할 수 있습니다."
    else:
        fit = "예산은 맞지만 쿠폰 종료, 배송비, 옵션 변경을 결제 직전 확인해야 합니다."
    return {
        "status": CheckStatus.ok,
        "candidate_count": len(affordable),
        "fit": fit,
    }


def _sections(
    category: Category,
    persona: str,
    market_status: CheckStatus,
) -> list[BuyerChecklistSection]:
    return [
        BuyerChecklistSection(
            section_id="fit",
            title="용도와 필수 조건",
            summary="성능보다 먼저 사용 목적과 제외 조건을 고정합니다.",
            items=[
                BuyerChecklistItem(
                    item_id="purpose",
                    label="주 사용 목적을 한 문장으로 고정",
                    status=CheckStatus.ok,
                    why_it_matters=(
                        "게임, 개발, 영상 편집, 사무용은 같은 예산에서도 "
                        "우선순위가 다릅니다."
                    ),
                    user_input_hint=_purpose_hint(category, persona),
                    failure_if_missing="필요 없는 성능에 과투자하거나 화면·무게·포트를 놓칩니다.",
                ),
                BuyerChecklistItem(
                    item_id="must_haves",
                    label="절대 포기할 수 없는 조건 3개 선택",
                    status=CheckStatus.ok,
                    why_it_matters="후보 비교에서 양보 가능한 조건과 차단 조건을 분리합니다.",
                    user_input_hint=_must_have_hint(category),
                    failure_if_missing=(
                        "좋아 보이는 특가가 실제 사용 조건을 충족하지 못할 수 있습니다."
                    ),
                ),
                BuyerChecklistItem(
                    item_id="exclusions",
                    label="중고, 리퍼, AS 불명, 재고 불안정 제외 여부",
                    status=CheckStatus.warning,
                    why_it_matters="가격만 낮은 후보가 구매 실패 원인이 되는 상황을 줄입니다.",
                    user_input_hint="제외할 판매 조건과 브랜드/AS 정책을 적어 주세요.",
                    failure_if_missing="반품 조건이나 AS 문제가 생겨도 비교표에서 늦게 발견됩니다.",
                ),
            ],
        ),
        BuyerChecklistSection(
            section_id="price",
            title="실구매가와 가격 타이밍",
            summary="표시가가 아니라 배송비, 쿠폰, 카드 혜택 적용 후 금액으로 판단합니다.",
            items=[
                BuyerChecklistItem(
                    item_id="budget",
                    label="월/총 예산과 10% 초과 허용 여부",
                    status=market_status,
                    why_it_matters="예산 초과 후보를 성능 이유로 살릴지 바로 제외할지 결정합니다.",
                    user_input_hint="최대 예산, 기다릴 수 있는 기간, 목표가를 입력하세요.",
                    failure_if_missing="특가 종료나 쿠폰 조건 변화로 최종 결제 금액이 달라집니다.",
                ),
                BuyerChecklistItem(
                    item_id="price_components",
                    label="배송비, 조립비, 쿠폰, 카드 할인 분리",
                    status=CheckStatus.warning,
                    why_it_matters=(
                        "판매 페이지마다 혜택 표시 방식이 달라 최종가 비교가 흔들립니다."
                    ),
                    user_input_hint="최종 결제 화면의 금액 구성 요소를 캡처하세요.",
                    failure_if_missing=(
                        "표시가 기준으로는 최저가였지만 결제 단계에서 역전될 수 있습니다."
                    ),
                ),
            ],
        ),
        BuyerChecklistSection(
            section_id="checkout",
            title="결제 전 검수",
            summary="주문 직전에는 모델명, 옵션명, 판매자 답변, 리스크 승인을 대조합니다.",
            items=[
                BuyerChecklistItem(
                    item_id="option_name",
                    label="리포트 후보와 주문 옵션명 일치 확인",
                    status=CheckStatus.blocker,
                    why_it_matters="동일 시리즈라도 RAM, SSD, GPU, 패널 옵션이 다를 수 있습니다.",
                    user_input_hint="장바구니 옵션명과 판매 페이지 모델명을 그대로 붙여 넣으세요.",
                    failure_if_missing="비슷한 이름의 하위 옵션을 주문할 수 있습니다.",
                ),
                BuyerChecklistItem(
                    item_id="seller_questions",
                    label="판매자 확인 질문 답변 확보",
                    status=CheckStatus.warning,
                    why_it_matters=(
                        "배송 일정, AS, 구성품, 반품 조건은 구매 후 되돌리기 어렵습니다."
                    ),
                    user_input_hint="판매자 답변 또는 고객센터 안내를 저장하세요.",
                    failure_if_missing="재고 지연, AS 제외, 구성품 누락을 결제 후 알게 됩니다.",
                ),
            ],
        ),
    ]


def _readiness_score(
    sections: list[BuyerChecklistSection],
    market_status: CheckStatus,
) -> float:
    items = [item for section in sections for item in section.items]
    if not items:
        return 0
    penalties = {CheckStatus.ok: 0, CheckStatus.warning: 8, CheckStatus.blocker: 18}
    score = 100 - sum(penalties[item.status] for item in items)
    if market_status == CheckStatus.warning:
        score -= 8
    if market_status == CheckStatus.blocker:
        score -= 18
    return round(max(0, min(100, score)), 1)


def _purpose_hint(category: Category, persona: str) -> str:
    if "team" in persona:
        return "예: 10명 팀 지급용, 화상회의와 문서 작업, AS와 재고 안정성 우선"
    if category == Category.laptop:
        return "예: 이동 중 영상 편집, 2kg 이하, 발열/소음 낮은 모델"
    return "예: QHD 게임과 영상 편집, 32GB RAM, RTX 4070급"


def _must_have_hint(category: Category) -> str:
    if category == Category.laptop:
        return "예: 32GB RAM, 2kg 이하, USB-C 충전, AS 1년 이상"
    return "예: GPU 등급, RAM 용량, 저장장치, 파워/케이스 호환성"


def _headline(category: Category, budget_krw: int, status: CheckStatus) -> str:
    label = "노트북" if category == Category.laptop else "데스크톱 PC"
    if status == CheckStatus.blocker:
        return f"{budget_krw:,}원 예산의 {label} 구매는 조건 조정이 먼저입니다."
    if status == CheckStatus.warning:
        return f"{label} 후보는 있지만 가격 알림과 대안 비교가 필요합니다."
    return f"{label} 구매 전 7개 항목만 확인하면 실패 가능성을 크게 줄일 수 있습니다."


def _summary(playbook_title: str, budget_fit: str, candidate_count: int | str) -> str:
    return (
        f"{playbook_title} 흐름을 기준으로 예산 적합도, 실구매가, 결제 전 검수를 "
        f"한 장으로 정리했습니다. {budget_fit} 예산 안 후보 {candidate_count}개를 기준으로 합니다."
    )


def _analysis_prefill(
    category: Category,
    budget_krw: int,
    playbook,
) -> str:
    label = "노트북" if category == Category.laptop else "데스크톱"
    must_haves = ", ".join(playbook.must_haves[:3])
    exclusions = ", ".join(playbook.exclusions[:2])
    return (
        f"{label}을 {budget_krw:,}원 안에서 추천해줘. 목적은 {playbook.purpose}이고 "
        f"필수 조건은 {must_haves}, 제외 조건은 {exclusions}야. "
        "가격 타이밍과 결제 전 검수까지 같이 봐줘."
    )


def _red_flags(category: Category, status: CheckStatus) -> list[str]:
    flags = [
        "최종 결제 금액이 리포트 가격보다 높아졌는데 이유를 설명할 수 없음",
        "판매 페이지 모델명과 장바구니 옵션명이 다름",
        "리뷰 반복 불만이나 AS 조건을 확인하지 않음",
    ]
    if status != CheckStatus.ok:
        flags.insert(0, "예산 안 후보가 부족한데 성능 조건을 줄이지 않음")
    if category == Category.laptop:
        flags.append("무게, 배터리, 발열 후기를 확인하지 않고 GPU만 비교함")
    else:
        flags.append("파워 용량, 케이스 GPU 길이, 쿨링 여유를 확인하지 않음")
    return flags


def _evidence_to_capture(category: Category) -> list[str]:
    evidence = [
        "최종 결제 화면의 총액, 배송비, 쿠폰/카드 혜택",
        "장바구니 옵션명과 판매 페이지 모델명",
        "판매자 답변, 배송 예정일, 반품/AS 조건",
    ]
    if category == Category.laptop:
        evidence.append("RAM 온보드/확장 가능 여부와 무게/배터리 스펙")
    else:
        evidence.append("GPU 길이, 파워 용량, 케이스 호환성 표기")
    return evidence


def _share_copy(category: Category, budget_krw: int, readiness_score: float) -> str:
    label = "노트북" if category == Category.laptop else "데스크톱 PC"
    return (
        f"{label} {budget_krw:,}원 예산으로 사기 전에 SpecPilot AI 체크리스트를 봤습니다. "
        f"준비도 {round(readiness_score)}점 기준으로 실구매가, 옵션명, 판매자 답변, "
        "결제 전 검수 항목을 확인한 뒤 구매하려고 합니다."
    )


def _next_actions(status: CheckStatus, readiness_score: float) -> list[str]:
    actions = [
        "체크리스트의 user_input_hint를 그대로 분석 요청에 붙여 넣으세요.",
        "상위 후보가 나오면 공개 리포트로 주변 검토를 먼저 받으세요.",
        "결제 직전에는 checkout-review로 최종 금액과 옵션명을 대조하세요.",
    ]
    if status != CheckStatus.ok or readiness_score < 70:
        actions.insert(0, "예산, 필수 조건, 제외 조건을 먼저 줄여서 후보 폭을 넓히세요.")
    return actions[:4]
