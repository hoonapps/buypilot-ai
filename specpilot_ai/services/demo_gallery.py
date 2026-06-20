from specpilot_ai.core.models import AnalyzeRequest, Category, DemoScenario, DemoScenarioGallery


def build_demo_scenario_gallery() -> DemoScenarioGallery:
    return DemoScenarioGallery(
        headline="첫 방문자가 10초 안에 구매 리포트를 체험합니다",
        subheadline=(
            "데스크톱, 크리에이터 노트북, 팀 구매 상황을 한 번의 클릭으로 채워 "
            "분석 실행 전에도 결과의 방향과 공유 포인트를 이해하게 합니다."
        ),
        primary_metric="3개 공개 데모 · 10초 조건 입력 · 공유 가능한 리포트",
        scenarios=[
            DemoScenario(
                scenario_id="creator-qhd-desktop",
                title="영상 편집 + QHD 게이밍 데스크톱",
                category=Category.desktop_pc,
                persona="크리에이터",
                one_liner="200만원 안에서 편집 성능, QHD 게임, 업그레이드 여지를 같이 봅니다.",
                request=AnalyzeRequest(
                    query=(
                        "영상 편집과 게임용 데스크톱 200만원 안에서 맞춰줘. "
                        "QHD 144Hz 모니터를 쓰고 업그레이드 여지도 있었으면 좋겠어."
                    ),
                    category=Category.desktop_pc,
                    budget_krw=2_000_000,
                    purpose="Premiere Pro, DaVinci Resolve, QHD gaming",
                    must_haves=["QHD 144Hz", "32GB RAM", "업그레이드 여지"],
                    exclusions=["중고", "리퍼", "출처 없는 가격"],
                    channels=["price_compare", "open_market", "official_store"],
                ),
                expected_outcome="TOP 3 추천과 제외 후보, 결제 전 체크리스트, 목표가 알림까지 생성",
                proof_points=[
                    "실구매가와 조립/OS 비용을 분리",
                    "GPU, RAM, 저장장치 업그레이드 여지 확인",
                    "QHD 144Hz와 편집 작업의 우선순위 충돌 표시",
                ],
                demo_cta="데스크톱 데모 적용",
                share_angle="견적 질문 전에 조건과 리스크를 정리한 공개 리포트로 공유",
                tags=["QHD", "영상 편집", "데스크톱"],
            ),
            DemoScenario(
                scenario_id="portable-creator-laptop",
                title="휴대형 크리에이터 노트북",
                category=Category.laptop,
                persona="이동이 잦은 작업자",
                one_liner="2kg 안팎의 휴대성, 외장 GPU, 발열/포트 리스크를 함께 검수합니다.",
                request=AnalyzeRequest(
                    query="영상 편집용 노트북 200만원 이하로 비교해줘. 무게와 발열도 중요해.",
                    category=Category.laptop,
                    budget_krw=2_000_000,
                    purpose="Premiere Pro, 외부 촬영 데이터 백업, 카페 작업",
                    must_haves=["32GB RAM 선호", "외장 GPU", "2kg 이하", "USB-C 충전"],
                    exclusions=["RAM 8GB", "리퍼", "포트 부족"],
                    channels=["price_compare", "open_market", "official_store"],
                ),
                expected_outcome="성능보다 발열/무게가 위험한 후보를 제외하고 구매 타이밍 제안",
                proof_points=[
                    "무게, 포트, 충전 조건을 성능 점수와 분리",
                    "리뷰 반복 불만과 벤치마크 근거를 같이 표시",
                    "휴대성과 편집 성능의 트레이드오프 설명",
                ],
                demo_cta="노트북 데모 적용",
                share_angle="팀원이나 지인에게 휴대성/성능 선택 기준을 검토받기 좋음",
                tags=["노트북", "휴대성", "발열"],
            ),
            DemoScenario(
                scenario_id="team-office-refresh",
                title="팀 사무용 노트북 반복 구매",
                category=Category.laptop,
                persona="팀 구매 담당자",
                one_liner="여러 대를 사기 전 AS, 재고, 보안 요구, 예산 상한을 표준화합니다.",
                request=AnalyzeRequest(
                    query=(
                        "팀에서 쓸 사무용 노트북 5대를 고르려고 해. "
                        "대당 120만원 이하, AS와 재고 안정성이 중요해."
                    ),
                    category=Category.laptop,
                    budget_krw=1_200_000,
                    purpose="문서 작업, 화상회의, SaaS 업무, 반복 구매",
                    must_haves=["5대 구매", "출장 AS", "16GB RAM", "재고 안정"],
                    exclusions=["보증 짧음", "배송 지연", "과한 게이밍 디자인"],
                    channels=["price_compare", "open_market", "official_store"],
                ),
                expected_outcome="팀 표준안, 구매 보류 사유, 완료 리포트 발송 준비까지 연결",
                proof_points=[
                    "대량 구매 시 재고와 AS 조건을 별도 검수",
                    "구매 완료 리포트와 수신자 그룹으로 내부 공유 가능",
                    "반복 구매 결과를 학습 인사이트로 회수",
                ],
                demo_cta="팀 구매 데모 적용",
                share_angle="구매 결재 전에 표준 후보와 보류 사유를 내부 공유",
                tags=["팀 구매", "사무용", "AS"],
            ),
        ],
    )
