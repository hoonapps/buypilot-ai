from collections import Counter
from datetime import UTC, datetime

from specpilot_ai.core.models import (
    BuyerPersonaQuizOption,
    BuyerPersonaQuizQuestion,
    BuyerPersonaQuizRequest,
    BuyerPersonaQuizResult,
    Category,
    PublicBuyerPersonaQuiz,
)


def build_public_buyer_persona_quiz(
    generated_at: datetime | None = None,
) -> PublicBuyerPersonaQuiz:
    generated_at = generated_at or datetime.now(UTC)
    return PublicBuyerPersonaQuiz(
        generated_at=generated_at.isoformat(),
        headline="30초 구매 성향 진단으로 첫 분석 조건을 자동으로 고릅니다.",
        summary=(
            "용도, 우선순위, 구매 시점, 예산 압박을 고르면 데스크톱/노트북/팀 구매 "
            "persona와 분석 prefill을 바로 제안합니다."
        ),
        questions=_quiz_questions(),
        next_actions=[
            "결과의 분석 prefill로 첫 리포트를 생성하세요.",
            "결과 공유 문구를 커뮤니티나 팀 채팅에 붙여 주변 검토를 받으세요.",
            "예산이 낮게 나온 경우 가격 알림과 대안 시나리오를 먼저 확인하세요.",
        ],
    )


def score_buyer_persona_quiz(
    request: BuyerPersonaQuizRequest,
    generated_at: datetime | None = None,
) -> BuyerPersonaQuizResult:
    generated_at = generated_at or datetime.now(UTC)
    weights = _option_weights()
    scores: Counter[str] = Counter()
    valid_answers = 0
    for answer in request.answers:
        for persona, weight in weights.get(answer.option_id, {}).items():
            scores[persona] += weight
            valid_answers += 1
    persona_id = _winner(scores)
    profile = _persona_profiles()[persona_id]
    confidence = _confidence_score(scores, persona_id, valid_answers)
    category = profile["category"]
    budget = profile["budget_krw"]
    return BuyerPersonaQuizResult(
        generated_at=generated_at.isoformat(),
        persona_id=persona_id,
        persona_label=profile["label"],
        category=category,
        recommended_plan_id=profile["plan_id"],
        recommended_budget_krw=budget,
        confidence_score=confidence,
        headline=_result_headline(profile["label"], confidence),
        summary=profile["summary"],
        analysis_prefill=_analysis_prefill(persona_id, category, budget),
        checklist_path=(
            f"/public/buyer-checklist?category={category.value}"
            f"&budget_krw={budget}&persona={persona_id}"
        ),
        primary_cta_label="이 조건으로 분석 시작",
        primary_cta_path="#analysis",
        proof_points=profile["proof_points"],
        share_copy=_share_copy(profile["label"], category, budget, confidence),
        next_actions=_next_actions(persona_id),
    )


def _quiz_questions() -> list[BuyerPersonaQuizQuestion]:
    return [
        BuyerPersonaQuizQuestion(
            question_id="use_case",
            title="가장 가까운 구매 상황은 무엇인가요?",
            helper="첫 분석의 카테고리와 비교 기준을 정합니다.",
            options=[
                BuyerPersonaQuizOption(
                    option_id="creator_work",
                    label="영상 편집·게임",
                    description="성능, 업그레이드, 가격 타이밍을 같이 봅니다.",
                ),
                BuyerPersonaQuizOption(
                    option_id="portable_work",
                    label="휴대형 작업",
                    description="무게, 배터리, 발열, 화면 품질을 중시합니다.",
                ),
                BuyerPersonaQuizOption(
                    option_id="team_refresh",
                    label="팀 장비 교체",
                    description="재고, AS, 승인 리포트, 반복 구매 기준이 중요합니다.",
                ),
            ],
        ),
        BuyerPersonaQuizQuestion(
            question_id="priority",
            title="이번 구매에서 가장 무서운 실패는 무엇인가요?",
            helper="추천 결과의 리스크 설명 우선순위를 정합니다.",
            options=[
                BuyerPersonaQuizOption(
                    option_id="performance_gap",
                    label="성능 부족",
                    description="CPU/GPU/RAM 병목과 업그레이드 여지를 확인합니다.",
                ),
                BuyerPersonaQuizOption(
                    option_id="portability_regret",
                    label="무게·발열 후회",
                    description="휴대성과 장시간 사용 리스크를 먼저 봅니다.",
                ),
                BuyerPersonaQuizOption(
                    option_id="approval_delay",
                    label="내부 승인 지연",
                    description="공유 리포트와 결제 전 검수 증거를 준비합니다.",
                ),
                BuyerPersonaQuizOption(
                    option_id="budget_overrun",
                    label="예산 초과",
                    description="목표가 알림, 대안 시나리오, 실구매가를 우선합니다.",
                ),
            ],
        ),
        BuyerPersonaQuizQuestion(
            question_id="timing",
            title="구매 시점은 어느 쪽인가요?",
            helper="즉시 구매, 가격 대기, 팀 일정 중 어디에 맞출지 결정합니다.",
            options=[
                BuyerPersonaQuizOption(
                    option_id="buy_now",
                    label="이번 주 안",
                    description="결제 전 체크리스트와 판매자 질문이 중요합니다.",
                ),
                BuyerPersonaQuizOption(
                    option_id="can_wait",
                    label="목표가까지 대기 가능",
                    description="가격 알림과 대안 후보를 먼저 설정합니다.",
                ),
                BuyerPersonaQuizOption(
                    option_id="rollout_schedule",
                    label="팀 지급 일정 있음",
                    description="납기, 수량, AS 정책을 함께 고정합니다.",
                ),
            ],
        ),
        BuyerPersonaQuizQuestion(
            question_id="budget",
            title="예산 감각은 어디에 가깝나요?",
            helper="추천 예산대와 요금제 CTA 강도를 조정합니다.",
            options=[
                BuyerPersonaQuizOption(
                    option_id="budget_tight",
                    label="100만원대 초반",
                    description="가성비와 가격 대기가 중요합니다.",
                ),
                BuyerPersonaQuizOption(
                    option_id="budget_balanced",
                    label="150만~220만원",
                    description="성능과 안정성 균형을 맞출 수 있습니다.",
                ),
                BuyerPersonaQuizOption(
                    option_id="budget_premium",
                    label="220만원 이상",
                    description="고성능 후보의 과투자 여부를 검수합니다.",
                ),
                BuyerPersonaQuizOption(
                    option_id="budget_team",
                    label="팀 예산으로 여러 대",
                    description="총액, 승인자, 반복 구매 기준이 중요합니다.",
                ),
            ],
        ),
    ]


def _option_weights() -> dict[str, dict[str, int]]:
    return {
        "creator_work": {"creator_gamer": 3, "budget_guard": 1},
        "portable_work": {"portable_creator": 3, "budget_guard": 1},
        "team_refresh": {"team_buyer": 4},
        "performance_gap": {"creator_gamer": 3, "team_buyer": 1},
        "portability_regret": {"portable_creator": 3},
        "approval_delay": {"team_buyer": 4},
        "budget_overrun": {"budget_guard": 4, "portable_creator": 1},
        "buy_now": {"creator_gamer": 2, "portable_creator": 1},
        "can_wait": {"budget_guard": 3, "creator_gamer": 1},
        "rollout_schedule": {"team_buyer": 4},
        "budget_tight": {"budget_guard": 4},
        "budget_balanced": {"portable_creator": 2, "creator_gamer": 2},
        "budget_premium": {"creator_gamer": 3, "portable_creator": 1},
        "budget_team": {"team_buyer": 4},
    }


def _persona_profiles() -> dict[str, dict]:
    return {
        "creator_gamer": {
            "label": "성능 검수형 데스크톱 구매자",
            "category": Category.desktop_pc,
            "plan_id": "premium",
            "budget_krw": 2_200_000,
            "summary": (
                "QHD 게임, 영상 편집, 로컬 AI 실험처럼 성능 체감이 큰 구매입니다. "
                "GPU/RAM/파워/케이스 호환성과 가격 타이밍을 함께 봐야 합니다."
            ),
            "proof_points": [
                "성능 부족과 과투자 리스크를 동시에 줄입니다.",
                "결제 직전 옵션명과 최종 금액을 대조합니다.",
                "공유 브리프로 주변 검토를 빠르게 받을 수 있습니다.",
            ],
        },
        "portable_creator": {
            "label": "휴대 리스크 방어형 노트북 구매자",
            "category": Category.laptop,
            "plan_id": "premium",
            "budget_krw": 2_000_000,
            "summary": (
                "성능표만 보면 놓치기 쉬운 무게, 발열, 배터리, 포트, AS 조건이 "
                "구매 만족도를 좌우합니다."
            ),
            "proof_points": [
                "발열·팬소음 반복 불만을 먼저 확인합니다.",
                "RAM 온보드/확장 가능 여부를 결제 전 대조합니다.",
                "목표가 알림으로 특가를 기다릴 수 있습니다.",
            ],
        },
        "team_buyer": {
            "label": "팀 장비 승인형 구매 담당자",
            "category": Category.laptop,
            "plan_id": "team",
            "budget_krw": 1_500_000,
            "summary": (
                "여러 명에게 지급할 장비는 개별 성능보다 재고, 납기, AS, 승인자용 "
                "공유 리포트가 핵심입니다."
            ),
            "proof_points": [
                "팀 기준 검수표로 반복 구매 기준을 고정합니다.",
                "공유 리포트로 승인자와 실사용자가 같은 근거를 봅니다.",
                "Team 상담 키트로 결제 전 검수와 구매 결과 회수를 설계합니다.",
            ],
        },
        "budget_guard": {
            "label": "예산 방어형 실속 구매자",
            "category": Category.laptop,
            "plan_id": "free",
            "budget_krw": 1_200_000,
            "summary": (
                "예산 초과와 특가 착시를 막는 것이 우선입니다. 표시가보다 배송비, "
                "쿠폰, 카드 혜택 반영 후 실구매가가 중요합니다."
            ),
            "proof_points": [
                "목표가와 대안 시나리오를 먼저 잡습니다.",
                "표시가와 최종 결제 금액 차이를 분리합니다.",
                "AS 불명, 리퍼, 단종 임박 후보를 제외합니다.",
            ],
        },
    }


def _winner(scores: Counter[str]) -> str:
    if not scores:
        return "creator_gamer"
    order = ["team_buyer", "creator_gamer", "portable_creator", "budget_guard"]
    return max(order, key=lambda persona: (scores[persona], -order.index(persona)))


def _confidence_score(
    scores: Counter[str],
    persona_id: str,
    valid_answers: int,
) -> float:
    if not valid_answers:
        return 55.0
    top = scores[persona_id]
    total = max(1, sum(scores.values()))
    return round(min(96, 52 + (top / total) * 44 + min(valid_answers, 4) * 2), 1)


def _result_headline(label: str, confidence: float) -> str:
    return f"당신은 {label}에 가깝습니다. 진단 확신도 {round(confidence)}점입니다."


def _analysis_prefill(persona_id: str, category: Category, budget_krw: int) -> str:
    if persona_id == "team_buyer":
        return (
            f"팀에 지급할 노트북을 1대당 {budget_krw:,}원 안에서 비교해줘. "
            "재고, 납기, AS, 보안 업데이트, 공유 리포트, 결제 전 검수까지 같이 봐줘."
        )
    if persona_id == "portable_creator":
        return (
            f"휴대하면서 작업할 노트북을 {budget_krw:,}원 안에서 추천해줘. "
            "무게, 발열, 배터리, USB-C 충전, 32GB RAM 가능 여부를 같이 봐줘."
        )
    if persona_id == "budget_guard":
        return (
            f"예산을 최대 {budget_krw:,}원으로 잡고 노트북을 추천해줘. "
            "실구매가, 가격 대기, AS 불명 후보 제외, 대안 시나리오를 같이 봐줘."
        )
    label = "노트북" if category == Category.laptop else "데스크톱 PC"
    return (
        f"{label}을 {budget_krw:,}원 안에서 추천해줘. QHD 게임, 영상 편집, "
        "32GB RAM, RTX 4070급, 가격 타이밍, 결제 전 검수까지 같이 봐줘."
    )


def _share_copy(
    label: str,
    category: Category,
    budget_krw: int,
    confidence: float,
) -> str:
    category_label = "노트북" if category == Category.laptop else "데스크톱 PC"
    return (
        f"SpecPilot AI 구매 성향 진단 결과: {label}. "
        f"{category_label} {budget_krw:,}원 예산으로 분석하면 좋고, "
        f"진단 확신도는 {round(confidence)}점입니다."
    )


def _next_actions(persona_id: str) -> list[str]:
    common = [
        "분석 prefill을 복사해 첫 구매 리포트를 생성하세요.",
        "결과 공유 문구를 지인 또는 팀 채팅에 보내 검토를 받으세요.",
    ]
    if persona_id == "team_buyer":
        return [
            "Team 구매 상담 키트에서 승인자 브리프와 상담 안건을 확인하세요.",
            *common,
            "팀 예산, 지급 일정, AS 정책을 먼저 고정하세요.",
        ]
    if persona_id == "budget_guard":
        return [
            "가격 알림과 대안 시나리오를 먼저 설정하세요.",
            *common,
            "리퍼, 단종 임박, AS 불명 후보를 제외 조건에 넣으세요.",
        ]
    return [
        "구매 실패 방지 체크리스트에서 결제 전 증거를 확인하세요.",
        *common,
        "공개 리포트로 주변 검토를 받은 뒤 결제 전 검수를 실행하세요.",
    ]
