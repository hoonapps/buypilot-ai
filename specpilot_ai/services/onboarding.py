from specpilot_ai.core.models import (
    Category,
    PurchaseOnboardingPlaybook,
    PurchaseOnboardingStep,
)


def purchase_onboarding_playbooks(
    category: Category | None = None,
) -> list[PurchaseOnboardingPlaybook]:
    playbooks = [
        PurchaseOnboardingPlaybook(
            playbook_id="creator-desktop-qhd",
            category=Category.desktop_pc,
            persona="creator_gamer",
            title="영상 편집과 QHD 게임용 데스크톱",
            description=(
                "200만원 전후 예산에서 GPU, RAM, 저장장치, 업그레이드 여지를 "
                "동시에 확인해야 하는 구매자용 시작 흐름입니다."
            ),
            hero_query=(
                "영상 편집과 QHD 게임용 데스크톱 200만원 안에서 맞춰줘. "
                "32GB RAM과 RTX 4070급 GPU, 업그레이드 여지가 필요해."
            ),
            purpose="Premiere Pro, DaVinci Resolve, QHD 144Hz gaming",
            budget_hint_krw=2_000_000,
            must_haves=["RTX 4070급", "32GB RAM", "NVMe 1TB", "업그레이드 여지"],
            exclusions=["중고", "리퍼", "출처 없는 가격", "파워 용량 불명"],
            readiness_slots=["예산", "해상도", "주요 작업", "필수 부품", "제외 조건"],
            steps=[
                PurchaseOnboardingStep(
                    title="목적과 해상도 고정",
                    description="QHD 게임, 영상 편집, 렌더링 비중을 먼저 분리합니다.",
                    required_inputs=["사용 프로그램", "모니터 해상도", "게임/작업 비율"],
                    output="성능 우선순위와 과투자 차단 기준",
                ),
                PurchaseOnboardingStep(
                    title="가격대와 대안 시나리오 비교",
                    description="현재가, 목표가, 10% 예산 증감 시나리오를 같이 봅니다.",
                    required_inputs=["최대 예산", "구매 시점", "기다릴 수 있는 기간"],
                    output="즉시 결제, 가격 대기, 검수 후 구매 판정",
                ),
                PurchaseOnboardingStep(
                    title="결제 전 검수 준비",
                    description="주문 옵션명, 배송비, 카드 할인, 파워/케이스 호환성을 대조합니다.",
                    required_inputs=["판매 페이지 URL", "최종 결제 금액", "판매자 답변"],
                    output="결제 가능 여부와 판매자 확인 질문",
                ),
            ],
            trust_gates=[
                "GPU/CPU/파워/케이스 호환성 검수",
                "쿠폰/카드 할인 적용 후 실구매가 재확인",
                "리뷰 반복 불만과 출처 신뢰도 0.8 이상 확인",
            ],
            recommended_plan_id="premium",
        ),
        PurchaseOnboardingPlaybook(
            playbook_id="portable-creator-laptop",
            category=Category.laptop,
            persona="portable_creator",
            title="휴대형 크리에이터 노트북",
            description=(
                "이동이 잦지만 GPU 가속과 32GB 메모리가 필요한 사용자에게 "
                "무게, 발열, 포트, 가격 타이밍을 함께 검수하게 합니다."
            ),
            hero_query=(
                "출장이 많은 영상 편집자용 노트북을 골라줘. 2kg 이하, "
                "32GB RAM, GPU 가속, USB-C 충전과 좋은 화면이 필요해."
            ),
            purpose="출장 편집, Lightroom, Premiere Pro, 외부 미팅",
            budget_hint_krw=2_200_000,
            must_haves=["2kg 이하", "32GB RAM", "RTX 4050급 이상", "USB-C 충전"],
            exclusions=["8GB RAM", "발열 반복 불만", "AS 근거 부족"],
            readiness_slots=["무게 제한", "필수 포트", "작업 앱", "배터리 우선순위", "AS 조건"],
            steps=[
                PurchaseOnboardingStep(
                    title="휴대성과 성능 균형 설정",
                    description="무게, 화면, 배터리, GPU 가속 중 포기할 수 없는 조건을 정합니다.",
                    required_inputs=["최대 무게", "화면 크기", "GPU 필요도"],
                    output="휴대성 우선 후보와 성능 우선 후보 분리",
                ),
                PurchaseOnboardingStep(
                    title="발열/소음 리스크 확인",
                    description="리뷰 반복 불만과 벤치마크 유지 성능을 함께 확인합니다.",
                    required_inputs=["주 사용 장소", "소음 허용도", "장시간 작업 여부"],
                    output="리뷰 리스크와 구매 전 확인 질문",
                ),
                PurchaseOnboardingStep(
                    title="가격 알림 기준 생성",
                    description="목표가와 구매 가능 시점을 정해 가격 대기 여부를 판단합니다.",
                    required_inputs=["희망 구매일", "목표가", "대체 후보 허용 여부"],
                    output="목표가 알림과 대안 후보",
                ),
            ],
            trust_gates=[
                "RAM 온보드/확장 가능 여부 확인",
                "발열·팬소음 반복 불만 보강",
                "AS/반품 조건과 배송 일정 확인",
            ],
            recommended_plan_id="premium",
        ),
        PurchaseOnboardingPlaybook(
            playbook_id="team-office-laptop-refresh",
            category=Category.laptop,
            persona="team_buyer",
            title="팀 사무용 노트북 반복 구매",
            description=(
                "여러 명에게 지급할 노트북을 가격, 재고, AS, 보안 조건으로 "
                "반복 비교하는 운영자용 구매 흐름입니다."
            ),
            hero_query=(
                "10명 팀에 지급할 사무용 노트북을 비교해줘. 화상회의, 문서 작업, "
                "보안 업데이트, AS, 재고 안정성이 중요해."
            ),
            purpose="팀 지급, 화상회의, 문서 작업, 브라우저 멀티태스킹",
            budget_hint_krw=1_500_000,
            must_haves=["16GB RAM 이상", "1.4kg 전후", "AS 근거", "재고 안정성"],
            exclusions=["리퍼", "단종 임박", "AS 불명", "낮은 배터리 후기"],
            readiness_slots=["구매 수량", "지급 일정", "AS 정책", "보안 요구", "예산 상한"],
            steps=[
                PurchaseOnboardingStep(
                    title="수량과 지급 일정 고정",
                    description=(
                        "재고 부족과 가격 변동을 피하기 위해 구매 수량과 "
                        "마감일을 먼저 둡니다."
                    ),
                    required_inputs=["구매 수량", "지급일", "예산 상한"],
                    output="재고 리스크와 구매 일정",
                ),
                PurchaseOnboardingStep(
                    title="팀 기준 검수표 생성",
                    description="AS, 보안, 배터리, 포트 조건을 공통 검수표로 만듭니다.",
                    required_inputs=["필수 포트", "보안 요구", "AS 기간"],
                    output="팀 구매 검수 항목",
                ),
                PurchaseOnboardingStep(
                    title="공유 리포트로 승인 받기",
                    description=(
                        "최종 후보와 제외 후보를 공개 리포트로 공유해 "
                        "내부 승인을 받습니다."
                    ),
                    required_inputs=["승인자", "검토 마감일", "비교 기준"],
                    output="공유 리포트와 완료 리포트 발송 준비",
                ),
            ],
            trust_gates=[
                "동일 모델 재고와 납기 확인",
                "팀 예산 대비 총액과 AS 조건 검수",
                "승인자용 공개 리포트와 구매 결과 회수",
            ],
            recommended_plan_id="team",
        ),
    ]
    if category is None:
        return playbooks
    return [playbook for playbook in playbooks if playbook.category == category]
