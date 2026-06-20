from uuid import uuid4

from fastapi.testclient import TestClient

from specpilot_ai.api.main import app
from specpilot_ai.core.config import Settings
from specpilot_ai.core.models import WaitlistReferralRequest
from specpilot_ai.storage.sqlite_store import SpecPilotStore

client = TestClient(app)
WORKSPACE_A = {"X-SpecPilot-Key": "pytest-workspace-a"}
WORKSPACE_B = {"X-SpecPilot-Key": "pytest-workspace-b"}


def test_launch_page_exposes_product_ui() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "SpecPilot AI" in response.text
    assert "온보딩 플레이북" in response.text
    assert "분석 실행" in response.text
    assert "조건 진단" in response.text
    assert "목표가 도달 테스트" in response.text
    assert "공유 링크 생성" in response.text
    assert "공유용 검토 브리프" in response.text
    assert "구매 판정" in response.text
    assert "대안 시나리오" in response.text
    assert "구매 타이밍 윈도우" in response.text
    assert "예산/조건 스트레스 테스트" in response.text
    assert "후보별 근거 팩" in response.text
    assert "옵션/사양 검수표" in response.text
    assert "조건 충족 매트릭스" in response.text
    assert "구매 실행 패키지" in response.text
    assert "판매자 확인 질문" in response.text
    assert "피드백 보내기" in response.text
    assert "베타 신청" in response.text
    assert "요금제 관심" in response.text


def test_health_and_ready_endpoints_expose_operations_state() -> None:
    health = client.get("/health")
    ready = client.get("/ready")

    assert health.status_code == 200
    assert ready.status_code == 200
    assert health.json()["storage_ready"] is True
    assert health.json()["source_adapters"] >= 4
    assert ready.json()["ready"] is True
    assert ready.json()["source_adapters_ready"] is True


def test_workspace_context_uses_api_key_scope() -> None:
    demo = client.get("/me")
    workspace = client.get("/me", headers=WORKSPACE_A)

    assert demo.status_code == 200
    assert workspace.status_code == 200
    assert demo.json()["workspace_id"] == "demo"
    assert workspace.json()["workspace_id"].startswith("workspace_")
    assert workspace.json()["workspace_id"] != demo.json()["workspace_id"]


def test_admin_page_exposes_review_console() -> None:
    response = client.get("/admin")

    assert response.status_code == 200
    assert "SpecPilot AI Admin" in response.text
    assert "소스 수집" in response.text
    assert "URL 인입" in response.text
    assert "모니터 등록" in response.text
    assert "due refresh" in response.text
    assert "수집 refresh 이력" in response.text
    assert "provider 정책 저장" in response.text
    assert "Source Provider 정책" in response.text
    assert "발송 큐" in response.text
    assert "알림 발송 채널" in response.text
    assert "발송 시도" in response.text
    assert "Trace 저장소" in response.text
    assert "Observability export outbox" in response.text
    assert "export 큐 적재" in response.text
    assert "observability dispatch" in response.text
    assert "완료 리포트 배치" in response.text
    assert "템플릿 저장" in response.text
    assert "수신자 그룹 저장" in response.text
    assert "완료 리포트 발송" in response.text
    assert "열람/클릭 이벤트" in response.text
    assert "tracking_pixel_path" in response.text
    assert "provider webhook 이벤트" in response.text
    assert "구매 상담 Q&A" in response.text
    assert "advisor-questions" in response.text
    assert "결제 전 검수" in response.text
    assert "checkout-reviews" in response.text
    assert "구매 결과" in response.text
    assert "purchase-outcomes" in response.text
    assert "학습 인사이트" in response.text
    assert "learning-insights" in response.text
    assert "출시 게이트" in response.text
    assert "launch-gate" in response.text
    assert "요금제/구독 의향" in response.text
    assert "pricing-dashboard" in response.text
    assert "subscription-intents" in response.text
    assert "외부 연동 준비도" in response.text
    assert "integration-readiness" in response.text
    assert "핵심 연동 등록" in response.text
    assert "품질/비용 감사" in response.text
    assert "품질 회귀 모니터" in response.text
    assert "사용자 피드백" in response.text
    assert "베타 리드" in response.text
    assert "베타 출시 준비도" in response.text
    assert "베타 cohort" in response.text
    assert "개선 백로그" in response.text
    assert "SLA 상태" in response.text
    assert "cohort 리포트 export" in response.text
    assert "운영 상태" in response.text


def test_demo_scenario_gallery_exposes_launch_ready_presets() -> None:
    response = client.get("/demo/scenarios")

    assert response.status_code == 200
    payload = response.json()
    assert payload["gallery_version"] == "specpilot.demo_gallery.v1"
    assert "10초" in payload["headline"]
    assert "공유 가능한 리포트" in payload["primary_metric"]
    assert len(payload["scenarios"]) >= 3
    scenario_ids = {item["scenario_id"] for item in payload["scenarios"]}
    assert {"creator-qhd-desktop", "portable-creator-laptop", "team-office-refresh"} <= (
        scenario_ids
    )
    desktop = next(
        item for item in payload["scenarios"] if item["scenario_id"] == "creator-qhd-desktop"
    )
    assert desktop["request"]["category"] == "desktop_pc"
    assert desktop["request"]["budget_krw"] == 2_000_000
    assert "QHD 144Hz" in desktop["request"]["must_haves"]
    assert desktop["demo_cta"] == "데스크톱 데모 적용"
    assert desktop["proof_points"]
    assert "공개 리포트" in desktop["share_angle"]


def test_pricing_plans_subscription_intents_and_dashboard() -> None:
    workspace_a = {"X-SpecPilot-Key": f"pytest-pricing-a-{uuid4().hex}"}
    workspace_b = {"X-SpecPilot-Key": f"pytest-pricing-b-{uuid4().hex}"}

    plans = client.get("/pricing/plans")
    assert plans.status_code == 200
    plan_ids = {item["plan_id"] for item in plans.json()}
    assert {"free", "premium", "team"} <= plan_ids

    premium_intent = client.post(
        "/billing/subscription-intents",
        headers=workspace_a,
        json={
            "email": "premium-buyer@example.com",
            "plan_id": "premium",
            "billing_cycle": "monthly",
            "persona": "individual_buyer",
            "use_case": "게이밍 PC 가격 알림과 결제 전 검수",
            "team_size": 1,
            "max_budget_krw": 20_000,
            "feature_priorities": ["가격 알림", "저장 견적 비교"],
            "purchase_timing": "within_7_days",
            "source": "pytest-pricing",
        },
    )
    assert premium_intent.status_code == 200
    premium_payload = premium_intent.json()
    assert premium_payload["plan_id"] == "premium"
    assert premium_payload["estimated_mrr_krw"] == 9900
    assert premium_payload["readiness_status"] == "ok"
    assert premium_payload["email_masked"] == "pr***@example.com"

    team_intent = client.post(
        "/billing/subscription-intents",
        headers=workspace_a,
        json={
            "email": "it-admin@example.com",
            "plan_id": "team",
            "billing_cycle": "monthly",
            "persona": "it_admin",
            "use_case": "사무용 노트북 반복 구매와 팀 리포트",
            "team_size": 3,
            "max_budget_krw": 200_000,
            "feature_priorities": ["팀 공유 리포트", "구매 결과 학습"],
            "purchase_timing": "within_30_days",
            "source": "pytest-pricing",
        },
    )
    assert team_intent.status_code == 200
    assert team_intent.json()["plan_id"] == "team"
    assert team_intent.json()["estimated_mrr_krw"] == 147_000

    invalid_plan = client.post(
        "/billing/subscription-intents",
        headers=workspace_a,
        json={"email": "buyer@example.com", "plan_id": "enterprise"},
    )
    assert invalid_plan.status_code == 404

    intents = client.get("/billing/subscription-intents", headers=workspace_a)
    assert intents.status_code == 200
    assert {item["intent_id"] for item in intents.json()} >= {
        premium_payload["intent_id"],
        team_intent.json()["intent_id"],
    }

    isolated_intents = client.get("/billing/subscription-intents", headers=workspace_b)
    assert isolated_intents.status_code == 200
    assert all(item["source"] != "pytest-pricing" for item in isolated_intents.json())

    dashboard = client.get("/ops/pricing-dashboard", headers=workspace_a)
    assert dashboard.status_code == 200
    dashboard_payload = dashboard.json()
    assert dashboard_payload["intent_count"] == 2
    assert dashboard_payload["premium_intent_count"] == 1
    assert dashboard_payload["team_intent_count"] == 1
    assert dashboard_payload["estimated_mrr_krw"] == 156_900
    assert dashboard_payload["annualized_revenue_krw"] == 1_882_800
    assert dashboard_payload["recent_intents"]
    assert dashboard_payload["readiness_status"] in {"ok", "warning"}
    assert dashboard_payload["next_actions"]

    consult = client.get("/ops/team-purchase-consult-kit", headers=workspace_a)
    assert consult.status_code == 200
    consult_payload = consult.json()
    assert consult_payload["kit_version"] == "specpilot.team_purchase_consult_kit.v1"
    assert consult_payload["team_intent_count"] == 1
    assert consult_payload["estimated_team_mrr_krw"] == 147_000
    assert consult_payload["recommended_team_size"] == 3
    assert consult_payload["target_plan"]["plan_id"] == "team"
    assert consult_payload["decision_maker_brief"]
    assert consult_payload["consultation_agenda"]
    assert consult_payload["required_inputs"]
    assert consult_payload["roi_points"]
    assert consult_payload["rollout_steps"]
    assert "it***@example.com" in consult_payload["email_copy"]
    assert consult_payload["recent_team_intents"][0]["plan_id"] == "team"
    assert consult_payload["next_actions"]

    isolated_consult = client.get("/ops/team-purchase-consult-kit", headers=workspace_b)
    assert isolated_consult.status_code == 200
    assert isolated_consult.json()["team_intent_count"] == 0
    assert isolated_consult.json()["status"] == "blocker"

    metrics = client.get("/ops/metrics", headers=workspace_a)
    assert metrics.status_code == 200
    metrics_payload = metrics.json()
    assert metrics_payload["subscription_intents"] == 2
    assert metrics_payload["premium_subscription_intents"] == 2
    assert metrics_payload["estimated_mrr_krw"] == 156_900


def test_category_market_report_exposes_monthly_picks_and_risks() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-market-{uuid4().hex}"}

    report = client.get(
        "/market/category-reports?category=laptop",
        headers=workspace,
    )

    assert report.status_code == 200
    payload = report.json()
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["report_month"]
    assert payload["category_filter"] == "laptop"
    assert "노트북" in payload["headline"]
    assert payload["total_candidates"] == 5
    assert payload["picks"]
    assert all(item["category"] == "laptop" for item in payload["picks"])
    assert all(item["effective_price_krw"] > 0 for item in payload["picks"])
    assert all(item["target_price_krw"] > 0 for item in payload["picks"])
    assert payload["price_segments"]
    assert payload["risk_signals"]
    assert payload["trend_cards"]
    assert payload["workspace_signals"]["analysis_runs"] >= 0
    assert payload["publishing_checklist"]

    combined = client.get("/market/category-reports", headers=workspace)
    assert combined.status_code == 200
    combined_payload = combined.json()
    assert combined_payload["category_filter"] is None
    assert combined_payload["total_candidates"] == 10
    assert {item["category"] for item in combined_payload["picks"]} <= {
        "desktop_pc",
        "laptop",
    }


def test_public_category_market_report_is_shareable_without_workspace_key() -> None:
    response = client.get("/public/market/category-reports/desktop_pc")

    assert response.status_code == 200
    payload = response.json()
    assert payload["category"] == "desktop_pc"
    assert payload["slug"] == "desktop-pc"
    assert payload["canonical_path"] == "/market/desktop-pc"
    assert "데스크톱 PC" in payload["title"]
    assert payload["description"]
    assert payload["share_text"]
    assert "SpecPilot AI" in payload["seo_keywords"]
    assert payload["cta_cards"]
    assert payload["report"]["workspace_id"] == "public-market"
    assert payload["report"]["category_filter"] == "desktop_pc"
    assert payload["report"]["picks"]
    assert payload["report"]["price_segments"]
    assert payload["report"]["risk_signals"]


def test_public_onboarding_playbooks_guide_first_purchase_flow() -> None:
    response = client.get("/public/onboarding/playbooks?category=laptop")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert all(item["category"] == "laptop" for item in payload)
    assert {item["recommended_plan_id"] for item in payload} <= {"free", "premium", "team"}
    first = payload[0]
    assert first["playbook_id"]
    assert first["title"]
    assert first["hero_query"]
    assert first["purpose"]
    assert first["budget_hint_krw"] > 0
    assert first["must_haves"]
    assert first["exclusions"]
    assert first["readiness_slots"]
    assert first["steps"]
    assert first["steps"][0]["required_inputs"]
    assert first["trust_gates"]
    assert first["cta_anchor"] == "#analysis"

    all_playbooks = client.get("/public/onboarding/playbooks")
    assert all_playbooks.status_code == 200
    categories = {item["category"] for item in all_playbooks.json()}
    assert {"desktop_pc", "laptop"} <= categories


def test_public_buyer_checklist_turns_budget_and_category_into_lead_magnet() -> None:
    response = client.get(
        "/public/buyer-checklist?category=laptop&budget_krw=900000&persona=portable_creator"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["checklist_version"] == "specpilot.public_buyer_checklist.v1"
    assert payload["category"] == "laptop"
    assert payload["persona"] == "portable_creator"
    assert payload["budget_krw"] == 900_000
    assert payload["headline"]
    assert payload["summary"]
    assert 0 <= payload["readiness_score"] <= 100
    assert payload["budget_fit"]
    assert payload["primary_cta_anchor"] == "#analysis"
    assert "노트북" in payload["analysis_prefill"]
    assert payload["sections"]
    assert {section["section_id"] for section in payload["sections"]} >= {
        "fit",
        "price",
        "checkout",
    }
    assert any(
        item["status"] == "blocker"
        for section in payload["sections"]
        for item in section["items"]
    )
    assert payload["red_flags"]
    assert payload["evidence_to_capture"]
    assert "결제 전 검수" in payload["share_copy"]
    assert payload["next_actions"]

    default_checklist = client.get("/public/buyer-checklist")
    assert default_checklist.status_code == 200
    assert default_checklist.json()["category"] == "desktop_pc"


def test_public_buyer_persona_quiz_recommends_path_and_prefill() -> None:
    quiz = client.get("/public/buyer-persona-quiz")

    assert quiz.status_code == 200
    quiz_payload = quiz.json()
    assert quiz_payload["quiz_version"] == "specpilot.public_buyer_persona_quiz.v1"
    assert quiz_payload["headline"]
    assert quiz_payload["summary"]
    assert quiz_payload["result_endpoint"] == "/public/buyer-persona-quiz/result"
    assert len(quiz_payload["questions"]) >= 4
    assert all(question["options"] for question in quiz_payload["questions"])

    result = client.post(
        "/public/buyer-persona-quiz/result",
        json={
            "answers": [
                {"question_id": "use_case", "option_id": "team_refresh"},
                {"question_id": "priority", "option_id": "approval_delay"},
                {"question_id": "timing", "option_id": "rollout_schedule"},
                {"question_id": "budget", "option_id": "budget_team"},
            ],
            "source": "pytest",
        },
    )

    assert result.status_code == 200
    payload = result.json()
    assert payload["result_version"] == "specpilot.buyer_persona_quiz_result.v1"
    assert payload["persona_id"] == "team_buyer"
    assert payload["category"] == "laptop"
    assert payload["recommended_plan_id"] == "team"
    assert payload["recommended_budget_krw"] == 1_500_000
    assert payload["confidence_score"] >= 80
    assert "팀" in payload["analysis_prefill"]
    assert payload["checklist_path"].startswith("/public/buyer-checklist")
    assert payload["primary_cta_path"] == "#analysis"
    assert payload["proof_points"]
    assert "SpecPilot AI 구매 성향 진단 결과" in payload["share_copy"]
    assert payload["next_actions"]

    default_result = client.post("/public/buyer-persona-quiz/result", json={})
    assert default_result.status_code == 200
    assert default_result.json()["persona_id"] == "creator_gamer"


def test_public_mistake_cost_calculator_quantifies_launch_risk() -> None:
    calculator = client.get("/public/mistake-cost-calculator")

    assert calculator.status_code == 200
    calculator_payload = calculator.json()
    assert (
        calculator_payload["calculator_version"]
        == "specpilot.public_mistake_cost_calculator.v1"
    )
    assert calculator_payload["headline"]
    assert calculator_payload["summary"]
    assert calculator_payload["default_category"] == "desktop_pc"
    assert calculator_payload["result_endpoint"] == "/public/mistake-cost-calculator/result"
    assert len(calculator_payload["risk_options"]) >= 5
    assert calculator_payload["next_actions"]

    result = client.post(
        "/public/mistake-cost-calculator/result",
        json={
            "category": "laptop",
            "budget_krw": 1_500_000,
            "quantity": 12,
            "urgency": "team_rollout",
            "selected_risks": [
                "performance_mismatch",
                "approval_rework",
                "return_delay",
            ],
            "source": "pytest",
        },
    )

    assert result.status_code == 200
    payload = result.json()
    assert payload["result_version"] == "specpilot.mistake_cost_calculator_result.v1"
    assert payload["category"] == "laptop"
    assert payload["budget_krw"] == 1_500_000
    assert payload["quantity"] == 12
    assert payload["urgency"] == "team_rollout"
    assert payload["estimated_mistake_cost_krw"] > 0
    assert payload["protected_value_krw"] == 18_000_000
    assert payload["risk_score"] >= 40
    assert payload["risk_level"] in {"warning", "blocker"}
    assert len(payload["line_items"]) == 3
    assert all(item["prevention"] for item in payload["line_items"])
    assert "팀에 지급할 노트북" in payload["analysis_prefill"]
    assert payload["primary_cta_path"] == "#analysis"
    assert "SpecPilot AI 구매 실패 비용 계산 결과" in payload["share_copy"]
    assert payload["next_actions"]


def test_public_buyer_challenge_kit_packages_shareable_launch_loop() -> None:
    response = client.get(
        "/public/buyer-challenge-kit"
        "?category=desktop_pc&budget_krw=2200000&persona=creator_gamer"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kit_version"] == "specpilot.public_buyer_challenge_kit.v1"
    assert payload["category"] == "desktop_pc"
    assert payload["budget_krw"] == 2_200_000
    assert payload["persona"] == "creator_gamer"
    assert "구매 실패 방지 챌린지" in payload["challenge_title"]
    assert len(payload["challenge_steps"]) == 3
    assert payload["analysis_prefill"].startswith("데스크톱 PC를 2,200,000원")
    assert payload["checklist_path"].startswith("/public/buyer-checklist")
    assert "persona=creator_gamer" in payload["checklist_path"]
    assert payload["mistake_cost_path"].startswith(
        "/public/mistake-cost-calculator/result"
    )
    assert payload["persona_quiz_path"] == "/public/buyer-persona-quiz"
    assert "#SpecPilotAI" in payload["hashtags"]
    assert "#PC견적" in payload["hashtags"]
    assert payload["proof_points"]

    variants = {variant["channel"]: variant for variant in payload["share_variants"]}
    assert {"kakao", "community", "team"} <= set(variants)
    assert "SpecPilot AI" in variants["community"]["copy_text"]
    assert "2,200,000원" in variants["community"]["copy_text"]
    assert "데스크톱 PC" in variants["kakao"]["copy_text"]
    assert "승인 전 조건 검토 요청" in variants["team"]["copy_text"]
    assert payload["primary_cta_path"] == "#analysis"
    assert payload["next_actions"]


def test_public_spec_risk_scanner_checks_checkout_options_before_purchase() -> None:
    scanner = client.get("/public/spec-risk-scanner")

    assert scanner.status_code == 200
    scanner_payload = scanner.json()
    assert scanner_payload["scanner_version"] == "specpilot.public_spec_risk_scanner.v1"
    assert scanner_payload["result_endpoint"] == "/public/spec-risk-scanner/result"
    assert scanner_payload["example_request"]["category"] == "desktop_pc"
    assert scanner_payload["required_evidence"]
    assert scanner_payload["next_actions"]

    ok_result = client.post(
        "/public/spec-risk-scanner/result",
        json={
            "category": "desktop_pc",
            "product_title": "Creator RTX 4070 SUPER Build",
            "option_text": (
                "장바구니 옵션: Ryzen 7 7800X3D / RTX 4070 SUPER / "
                "RAM 32GB / SSD 1TB / Windows 11 Pro"
            ),
            "cart_total_krw": 2_185_000,
            "budget_krw": 2_200_000,
            "expected_cpu": "Ryzen 7 7800X3D",
            "expected_gpu": "RTX 4070 SUPER",
            "expected_ram_gb": 32,
            "expected_storage_gb": 1000,
            "expected_os": "Windows 11 Pro",
            "evidence_text": (
                "최종 결제 총액 2,185,000원, 배송 내일 출고, 반품 7일, "
                "AS 1년, 판매자 문의 답변 확보"
            ),
            "source": "pytest",
        },
    )

    assert ok_result.status_code == 200
    ok_payload = ok_result.json()
    assert ok_payload["result_version"] == "specpilot.spec_risk_scanner_result.v1"
    assert ok_payload["verdict"] in {"ready", "verify"}
    assert ok_payload["blocker_count"] == 0
    assert ok_payload["readiness_score"] >= 80
    assert not ok_payload["missing_evidence"]
    assert {check["check_id"] for check in ok_payload["checks"]} >= {
        "price",
        "option_name",
        "cpu",
        "gpu",
        "ram",
        "storage",
        "os",
    }
    assert "Creator RTX 4070 SUPER Build" in ok_payload["analysis_prefill"]
    assert "SpecPilot AI 옵션/사양 빠른 검수 결과" in ok_payload["share_copy"]

    hold_result = client.post(
        "/public/spec-risk-scanner/result",
        json={
            "category": "desktop_pc",
            "product_title": "Creator RTX 4070 SUPER Build",
            "option_text": "장바구니 옵션: Ryzen 5 7500F / RTX 4070 / RAM 16GB / SSD 512GB",
            "cart_total_krw": 2_340_000,
            "budget_krw": 2_200_000,
            "expected_cpu": "Ryzen 7 7800X3D",
            "expected_gpu": "RTX 4070 SUPER",
            "expected_ram_gb": 32,
            "expected_storage_gb": 1000,
            "expected_os": "Windows 11 Pro",
            "source": "pytest",
        },
    )

    assert hold_result.status_code == 200
    hold_payload = hold_result.json()
    assert hold_payload["verdict"] == "hold"
    assert hold_payload["blocker_count"] >= 4
    assert hold_payload["warning_count"] >= 1
    assert hold_payload["readiness_score"] < 50
    assert "결제 보류" in hold_payload["headline"]
    assert "배송 예정일" in hold_payload["missing_evidence"]
    assert any(
        check["check_id"] == "price" and check["status"] == "blocker"
        for check in hold_payload["checks"]
    )
    assert "검수 결과로 분석 시작" == hold_payload["primary_cta_label"]
    assert hold_payload["next_actions"]


def test_public_candidate_compare_exposes_top_candidates_and_scenarios() -> None:
    response = client.get(
        "/public/candidate-compare"
        "?category=desktop_pc&budget_krw=2200000&purpose=qhd_creator"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["compare_version"] == "specpilot.public_candidate_compare.v1"
    assert payload["category"] == "desktop_pc"
    assert payload["budget_krw"] == 2_200_000
    assert payload["purpose"] == "qhd_creator"
    assert "후보" in payload["headline"]
    assert payload["winner_product_id"]
    assert payload["winner_reason"]
    assert len(payload["items"]) >= 4
    first = payload["items"][0]
    assert first["product_id"] == payload["winner_product_id"]
    assert first["score"] >= payload["items"][-1]["score"]
    assert first["effective_price_krw"] > 0
    assert first["option_summary"]
    assert first["reasons"]
    assert first["watchouts"]
    assert first["evidence"]
    assert {axis["axis_id"] for axis in payload["axes"]} >= {
        "winner",
        "budget",
        "performance",
        "risk",
    }
    assert {scenario["scenario"] for scenario in payload["scenarios"]} == {
        "balanced",
        "budget",
        "performance",
        "safe",
    }
    assert "TOP 3" in payload["analysis_prefill"]
    assert "SpecPilot AI 공개 후보 비교" in payload["share_copy"]
    assert payload["primary_cta_path"] == "#analysis"
    assert payload["next_actions"]

    laptop = client.get(
        "/public/candidate-compare"
        "?category=laptop&budget_krw=2000000&purpose=portable_creator"
    )
    assert laptop.status_code == 200
    laptop_payload = laptop.json()
    assert laptop_payload["category"] == "laptop"
    assert any(item["category"] == "laptop" for item in laptop_payload["items"])
    assert "노트북" in laptop_payload["analysis_prefill"]


def test_public_deal_timing_window_separates_buy_now_and_wait() -> None:
    response = client.get(
        "/public/deal-timing-window"
        "?category=desktop_pc&budget_krw=2200000&purpose=qhd_creator"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["timing_version"] == "specpilot.public_deal_timing_window.v1"
    assert payload["category"] == "desktop_pc"
    assert payload["budget_krw"] == 2_200_000
    assert payload["purpose"] == "qhd_creator"
    assert "결제" in payload["headline"]
    assert payload["lead_product_id"]
    assert payload["lead_label"]
    assert payload["buy_now_count"] >= 1
    assert payload["wait_count"] >= 1
    assert payload["hold_count"] >= 1
    assert payload["target_savings_krw"] > 0
    assert len(payload["windows"]) >= 5
    first = payload["windows"][0]
    assert first["product_id"]
    assert first["current_price_krw"] > 0
    assert first["target_price_krw"] > 0
    assert first["current_price_krw"] >= first["target_price_krw"]
    assert "원" in first["fair_price_band_krw"]
    assert first["urgency"]
    assert first["volatility_risk"]
    assert first["wait_reason"]
    assert first["buy_trigger"]
    assert first["monitoring_plan"]
    assert "목표가" in payload["analysis_prefill"]
    assert "SpecPilot AI 공개 구매 타이밍" in payload["share_copy"]
    assert payload["primary_cta_path"] == "#analysis"
    assert payload["next_actions"]

    laptop = client.get(
        "/public/deal-timing-window"
        "?category=laptop&budget_krw=2000000&purpose=portable_creator"
    )
    assert laptop.status_code == 200
    laptop_payload = laptop.json()
    assert laptop_payload["category"] == "laptop"
    assert any(window["product_id"].startswith("laptop-") for window in laptop_payload["windows"])
    assert "노트북" in laptop_payload["analysis_prefill"]


def test_growth_funnel_tracks_product_reaction_events() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-growth-{uuid4().hex}"}
    other_workspace = {"X-SpecPilot-Key": f"pytest-growth-other-{uuid4().hex}"}

    analysis = client.post(
        "/analyze",
        headers=workspace,
        json={
            "query": "QHD 게임과 영상 편집용 PC를 220만원 안에서 추천해줘",
            "category": "desktop_pc",
            "budget_krw": 2_200_000,
            "purpose": "QHD gaming, Premiere Pro",
            "must_haves": ["RTX 4070급", "32GB RAM", "업그레이드"],
        },
    ).json()
    trace_id = analysis["graph_trace_id"]
    product_id = analysis["report"]["top_recommendations"][0]["product"]["id"]
    saved = client.post(
        "/reports/save",
        headers=workspace,
        json={
            "trace_id": trace_id,
            "title": "성장 퍼널 테스트 리포트",
            "owner_label": "pytest-growth",
        },
    ).json()

    event_types = [
        "analysis_view",
        "recommendation_click",
        "recommendation_click",
        "alternative_click",
        "share_cta",
        "alert_cta",
        "subscription_cta",
    ]
    created_ids: list[str] = []
    for event_type in event_types:
        response = client.post(
            "/growth/events",
            headers=workspace,
            json={
                "event_type": event_type,
                "trace_id": trace_id,
                "report_id": saved["report_id"],
                "product_id": product_id,
                "source": "pytest",
                "surface": "result",
                "label": f"{event_type} button",
                "metadata": {"rank": 1, "category": "desktop_pc"},
            },
        )
        assert response.status_code == 200
        created_ids.append(response.json()["event_id"])

    events = client.get("/growth/events", headers=workspace)
    assert events.status_code == 200
    event_payload = events.json()
    assert {item["event_id"] for item in event_payload} >= set(created_ids)
    assert event_payload[0]["workspace_id"].startswith("workspace_")
    assert event_payload[0]["metadata"]["category"] == "desktop_pc"

    funnel = client.get("/growth/funnel", headers=workspace)
    assert funnel.status_code == 200
    funnel_payload = funnel.json()
    assert funnel_payload["total_events"] == len(event_types)
    assert funnel_payload["unique_traces"] == 1
    assert funnel_payload["activation_rate"] >= 1
    assert funnel_payload["share_rate"] >= 1
    assert funnel_payload["paid_intent_rate"] >= 1
    assert any(step["key"] == "recommendation_click" for step in funnel_payload["steps"])
    assert "result" in funnel_payload["top_surfaces"][0]

    metrics = client.get("/ops/metrics", headers=workspace)
    assert metrics.status_code == 200
    metrics_payload = metrics.json()
    assert metrics_payload["growth_events"] == len(event_types)
    assert metrics_payload["recommendation_card_clicks"] == 2
    assert metrics_payload["alternative_scenario_clicks"] == 1
    assert metrics_payload["share_cta_clicks"] == 1
    assert metrics_payload["alert_cta_clicks"] == 1
    assert metrics_payload["subscription_cta_clicks"] == 1

    launch_gate = client.get("/beta/launch-gate", headers=workspace)
    assert launch_gate.status_code == 200
    launch_payload = launch_gate.json()
    assert "growth" in {check["area"] for check in launch_payload["checks"]}
    assert launch_payload["metric_cards"]["growth_events"] == len(event_types)
    assert launch_payload["metric_cards"]["recommendation_click_rate"] >= 1

    isolated = client.get("/growth/funnel", headers=other_workspace)
    assert isolated.status_code == 200
    assert isolated.json()["total_events"] == 0


def test_waitlist_referrals_create_share_loop_and_dashboard() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-referral-{uuid4().hex}"}
    other_workspace = {"X-SpecPilot-Key": f"pytest-referral-other-{uuid4().hex}"}

    first = client.post(
        "/growth/waitlist-referrals",
        headers=workspace,
        json={
            "email": "creator@example.com",
            "persona": "creator",
            "use_case": "QHD 영상 편집 PC를 빠르게 비교하고 싶습니다.",
            "source": "pytest-referral",
        },
    )
    assert first.status_code == 200
    first_payload = first.json()
    assert first_payload["email_masked"] == "cr***@example.com"
    assert first_payload["referral_code"]
    assert first_payload["referral_url"].endswith(first_payload["referral_code"])
    assert first_payload["priority_score"] >= 40

    referred = client.post(
        "/growth/waitlist-referrals",
        headers=workspace,
        json={
            "email": "friend@example.com",
            "persona": "gamer",
            "use_case": "게이밍 PC 추천을 받고 싶습니다.",
            "referred_by_code": first_payload["referral_code"],
            "source": "pytest-referral",
        },
    )
    assert referred.status_code == 200
    assert referred.json()["referred_by_code"] == first_payload["referral_code"]

    referrals = client.get("/growth/waitlist-referrals", headers=workspace)
    assert referrals.status_code == 200
    referral_payload = referrals.json()
    parent = next(
        item
        for item in referral_payload
        if item["referral_code"] == first_payload["referral_code"]
    )
    assert parent["referred_signup_count"] == 1
    assert parent["priority_score"] > first_payload["priority_score"]

    dashboard = client.get("/growth/referral-dashboard", headers=workspace)
    assert dashboard.status_code == 200
    dashboard_payload = dashboard.json()
    assert dashboard_payload["total_referrals"] == 2
    assert dashboard_payload["referred_signup_count"] == 1
    assert dashboard_payload["share_rate_hint"] == 0.5
    assert dashboard_payload["top_referrers"][0]["referral_code"] == first_payload["referral_code"]
    assert dashboard_payload["next_actions"]

    share_kit = client.get(
        f"/growth/referral-share-kit/{first_payload['referral_code']}",
        headers=workspace,
    )
    assert share_kit.status_code == 200
    share_kit_payload = share_kit.json()
    assert share_kit_payload["kit_version"] == "specpilot.referral_share_kit.v1"
    assert share_kit_payload["referral_code"] == first_payload["referral_code"]
    assert share_kit_payload["referral_url"].endswith(first_payload["referral_code"])
    assert {variant["channel"] for variant in share_kit_payload["variants"]} == {
        "kakao",
        "community",
        "email",
    }
    assert all(
        share_kit_payload["referral_url"] in variant["copy_text"]
        for variant in share_kit_payload["variants"]
    )
    assert share_kit_payload["next_actions"]

    rewards = client.get(
        f"/growth/referral-rewards/{first_payload['referral_code']}",
        headers=workspace,
    )
    assert rewards.status_code == 200
    rewards_payload = rewards.json()
    assert rewards_payload["reward_version"] == "specpilot.referral_rewards.v1"
    assert rewards_payload["referral_code"] == first_payload["referral_code"]
    assert rewards_payload["referred_signup_count"] == 1
    assert rewards_payload["current_tier"]["tier_id"] == "first-share"
    assert rewards_payload["next_tier"]["tier_id"] == "early-access"
    assert rewards_payload["progress_percent"] > 0
    assert {tier["status"] for tier in rewards_payload["tiers"]} >= {
        "achieved",
        "next",
    }
    assert rewards_payload["next_actions"]

    leaderboard = client.get(
        f"/growth/referral-leaderboard?referral_code={first_payload['referral_code']}",
        headers=workspace,
    )
    assert leaderboard.status_code == 200
    leaderboard_payload = leaderboard.json()
    assert (
        leaderboard_payload["leaderboard_version"]
        == "specpilot.public_referral_leaderboard.v1"
    )
    assert leaderboard_payload["current_rank"] == 1
    assert leaderboard_payload["current_entry"]["referral_code"] == first_payload["referral_code"]
    assert leaderboard_payload["current_entry"]["status"] == "current"
    assert leaderboard_payload["current_entry"]["referred_signup_count"] == 1
    assert leaderboard_payload["entries"][0]["rank"] == 1
    assert leaderboard_payload["entries"][0]["reward_label"]
    assert leaderboard_payload["next_actions"]

    launch_kit = client.get("/growth/referral-launch-kit?limit=8", headers=workspace)
    assert launch_kit.status_code == 200
    launch_kit_payload = launch_kit.json()
    assert launch_kit_payload["kit_version"] == "specpilot.public_referral_launch_kit.v1"
    assert launch_kit_payload["dashboard"]["total_referrals"] == 2
    assert (
        launch_kit_payload["leaderboard"]["entries"][0]["referral_code"]
        == first_payload["referral_code"]
    )
    assert {tier["required_referrals"] for tier in launch_kit_payload["reward_tiers"]} == {
        1,
        3,
        5,
        10,
    }
    assert {variant["channel"] for variant in launch_kit_payload["share_examples"]} == {
        "kakao",
        "community",
        "email",
    }
    assert launch_kit_payload["cta_cards"]
    assert launch_kit_payload["next_actions"]

    isolated_kit = client.get(
        f"/growth/referral-share-kit/{first_payload['referral_code']}",
        headers=other_workspace,
    )
    assert isolated_kit.status_code == 404

    isolated_rewards = client.get(
        f"/growth/referral-rewards/{first_payload['referral_code']}",
        headers=other_workspace,
    )
    assert isolated_rewards.status_code == 404

    isolated_leaderboard = client.get(
        f"/growth/referral-leaderboard?referral_code={first_payload['referral_code']}",
        headers=other_workspace,
    )
    assert isolated_leaderboard.status_code == 200
    assert isolated_leaderboard.json()["current_rank"] is None

    isolated = client.get("/growth/referral-dashboard", headers=other_workspace)
    assert isolated.status_code == 200
    assert isolated.json()["total_referrals"] == 0


def test_waitlist_referral_url_uses_public_site_url_when_configured(tmp_path) -> None:
    relative_store = SpecPilotStore(
        Settings(storage_path=str(tmp_path / "relative.sqlite3")),
    )
    relative = relative_store.create_waitlist_referral_for_workspace(
        "pytest-url-relative",
        WaitlistReferralRequest(
            email="relative@example.com",
            persona="creator",
            source="pytest-referral-url",
        ),
    )
    assert relative.referral_url == f"/join?ref={relative.referral_code}"

    absolute_store = SpecPilotStore(
        Settings(
            storage_path=str(tmp_path / "absolute.sqlite3"),
            public_site_url="https://specpilot.example.com/",
        ),
    )
    absolute = absolute_store.create_waitlist_referral_for_workspace(
        "pytest-url-absolute",
        WaitlistReferralRequest(
            email="absolute@example.com",
            persona="team_purchase",
            source="pytest-referral-url",
        ),
    )
    assert absolute.referral_url == (
        f"https://specpilot.example.com/join?ref={absolute.referral_code}"
    )


def test_trust_policy_endpoint_exposes_cache_and_fairness_rules() -> None:
    response = client.get("/policy/trust")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_policy"]
    assert payload["affiliate_disclosure"]
    assert payload["fairness_rules"]
    assert payload["review_rules"]
    assert payload["source_assessments"]


def test_growth_launch_kit_exposes_campaign_copy_and_measurement_plan() -> None:
    response = client.get("/growth/launch-kit?category=laptop&audience=team_buyer")

    assert response.status_code == 200
    payload = response.json()
    assert payload["kit_version"] == "specpilot.launch_kit.v1"
    assert payload["category"] == "laptop"
    assert payload["audience"] == "team_buyer"
    assert "무료 AI 구매 리포트" in payload["offer"]
    assert payload["primary_cta_path"] == "/#analysis"
    assert len(payload["proof_points"]) >= 4
    assert len(payload["target_segments"]) >= 3
    assert {item["channel"] for item in payload["channel_playbooks"]} >= {
        "community",
        "seo",
        "referral",
    }
    community = next(
        item for item in payload["channel_playbooks"] if item["channel"] == "community"
    )
    assert community["copy_variants"]
    assert any("리포트" in variant["body"] for variant in community["copy_variants"])
    assert any("Trust Center" in item for item in payload["launch_checklist"])
    assert payload["risk_disclosures"]
    assert "추천 만족도와 구매 의향률" in payload["measurement_plan"]


def test_growth_launch_distribution_plan_prioritizes_launch_channels() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-launch-plan-{uuid4().hex}"}
    other_workspace = {"X-SpecPilot-Key": f"pytest-launch-plan-other-{uuid4().hex}"}

    client.post(
        "/growth/events",
        headers=workspace,
        json={
            "event_type": "share_cta",
            "source": "pytest-launch-plan",
            "surface": "public-report",
            "label": "공유 리포트 CTA",
        },
    )
    client.post(
        "/growth/waitlist-referrals",
        headers=workspace,
        json={
            "email": "launch-plan@example.com",
            "persona": "creator",
            "use_case": "출시 배포 전 추천 링크를 공유합니다.",
            "source": "pytest-launch-plan",
        },
    )

    response = client.get(
        "/growth/launch-distribution-plan?category=desktop_pc&audience=creator",
        headers=workspace,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["plan_version"] == "specpilot.launch_distribution_plan.v1"
    assert payload["category"] == "desktop_pc"
    assert payload["audience"] == "creator"
    assert payload["workspace_id"] != "demo"
    assert payload["distribution_score"] > 0
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert {"community", "seo", "referral"} <= set(payload["priority_channels"])
    assert {slot["channel"] for slot in payload["slots"]} >= {
        "community",
        "seo",
        "referral",
    }
    assert all(slot["copy_text"] and slot["cta_path"] for slot in payload["slots"])
    assert any("share_cta" in item for item in payload["measurement_events"])
    assert payload["risk_controls"]
    assert payload["next_actions"]

    isolated = client.get(
        "/growth/launch-distribution-plan?category=desktop_pc&audience=creator",
        headers=other_workspace,
    )
    assert isolated.status_code == 200
    assert isolated.json()["workspace_id"] != payload["workspace_id"]


def test_growth_launch_pulse_summarizes_public_reaction_signals() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-pulse-{uuid4().hex}"}

    analysis = client.post(
        "/analyze",
        headers=workspace,
        json={
            "query": "크리에이터 노트북 200만원 이하로 추천해줘",
            "category": "laptop",
            "budget_krw": 2_000_000,
            "purpose": "Premiere Pro, 외부 촬영 데이터 백업",
            "must_haves": ["32GB RAM", "외장 GPU", "가벼운 무게"],
        },
    )
    assert analysis.status_code == 200
    analysis_payload = analysis.json()
    trace_id = analysis_payload["graph_trace_id"]
    product_id = analysis_payload["report"]["top_recommendations"][0]["product"]["id"]

    for event_type in [
        "analysis_view",
        "recommendation_click",
        "share_cta",
        "subscription_cta",
    ]:
        event = client.post(
            "/growth/events",
            headers=workspace,
            json={
                "event_type": event_type,
                "trace_id": trace_id,
                "product_id": product_id,
                "source": "pytest",
                "surface": "demo-gallery",
                "label": f"{event_type} pulse seed",
            },
        )
        assert event.status_code == 200

    feedback = client.post(
        "/feedback",
        headers=workspace,
        json={
            "trace_id": trace_id,
            "rating": 5,
            "purchase_intent": True,
            "selected_product_id": product_id,
            "reason": "데모 preset으로 바로 조건을 넣고 결과를 이해했습니다.",
            "improvement_requests": ["실제 쇼핑몰 링크 확대"],
            "contact": "pulse@example.com",
        },
    )
    assert feedback.status_code == 200

    referral = client.post(
        "/growth/waitlist-referrals",
        headers=workspace,
        json={
            "email": "pulse@example.com",
            "persona": "creator",
            "use_case": "친구와 구매 리포트를 공유하고 싶습니다.",
            "source": "pytest-pulse",
        },
    )
    assert referral.status_code == 200

    subscription = client.post(
        "/billing/subscription-intents",
        headers=workspace,
        json={
            "email": "pulse@example.com",
            "plan_id": "premium",
            "billing_cycle": "monthly",
            "persona": "creator",
            "use_case": "가격 알림과 결제 전 검수",
            "team_size": 1,
            "max_budget_krw": 20_000,
            "feature_priorities": ["가격 알림", "공유 리포트"],
            "purchase_timing": "within_30_days",
            "source": "pytest-pulse",
        },
    )
    assert subscription.status_code == 200

    lead = client.post(
        "/beta/leads",
        headers=workspace,
        json={
            "email": "pulse@example.com",
            "persona": "creator",
            "use_case": "노트북 구매 전 검수",
            "company_size": "freelancer",
            "contact_consent": True,
            "source": "pytest-pulse",
        },
    )
    assert lead.status_code == 200

    pulse = client.get("/growth/launch-pulse?limit=8", headers=workspace)
    assert pulse.status_code == 200
    payload = pulse.json()
    assert payload["pulse_version"] == "specpilot.launch_pulse.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["pulse_score"] > 0
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert "Pulse" in payload["headline"]
    assert {signal["area"] for signal in payload["signals"]} >= {
        "activation",
        "love",
        "sharing",
        "monetization",
        "reliability",
    }
    assert {metric["key"] for metric in payload["metrics"]} >= {
        "pulse_score",
        "purchase_intent_rate",
        "estimated_mrr",
        "referrals",
    }
    assert any("demo-gallery" in item for item in payload["hot_surfaces"])
    assert payload["top_actions"]
    assert payload["recent_feedback"][0]["feedback_id"] == feedback.json()["feedback_id"]
    assert payload["recent_growth_events"]


def test_growth_acquisition_hub_maps_public_launch_surfaces() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-acquisition-{uuid4().hex}"}

    analysis = client.post(
        "/analyze",
        headers=workspace,
        json={
            "query": "QHD 게이밍과 영상 편집용 PC를 220만원 안에서 추천해줘",
            "category": "desktop_pc",
            "budget_krw": 2_200_000,
            "purpose": "QHD gaming, Premiere Pro",
            "must_haves": ["QHD 144Hz", "32GB RAM", "업그레이드 여지"],
        },
    )
    assert analysis.status_code == 200
    analysis_payload = analysis.json()
    trace_id = analysis_payload["graph_trace_id"]
    product_id = analysis_payload["report"]["top_recommendations"][0]["product"]["id"]

    saved = client.post(
        "/reports/save",
        headers=workspace,
        json={"trace_id": trace_id, "title": "공개 유입 테스트 리포트"},
    )
    assert saved.status_code == 200
    report_id = saved.json()["report_id"]
    share = client.post(f"/reports/{report_id}/share", headers=workspace)
    assert share.status_code == 200
    public_report = client.get(f"/public/reports/{share.json()['share_token']}")
    assert public_report.status_code == 200

    for event_type, surface in [
        ("analysis_view", "demo-gallery"),
        ("recommendation_click", "recommendation-card"),
        ("share_cta", "share-assets"),
        ("subscription_cta", "pricing"),
    ]:
        event = client.post(
            "/growth/events",
            headers=workspace,
            json={
                "event_type": event_type,
                "trace_id": trace_id,
                "report_id": report_id,
                "product_id": product_id,
                "source": "pytest",
                "surface": surface,
                "label": f"{event_type} acquisition seed",
            },
        )
        assert event.status_code == 200

    referral = client.post(
        "/growth/waitlist-referrals",
        headers=workspace,
        json={
            "email": "acquisition@example.com",
            "persona": "team_buyer",
            "use_case": "팀 장비 구매 비교 리포트를 공유하고 싶습니다.",
        },
    )
    assert referral.status_code == 200

    intent = client.post(
        "/billing/subscription-intents",
        headers=workspace,
        json={
            "email": "buyer@example.com",
            "plan_id": "team",
            "persona": "team_buyer",
            "team_size": 4,
            "use_case": "반복 PC 구매 비교",
            "feature_priorities": ["팀 공유 리포트", "구매 결과 학습"],
        },
    )
    assert intent.status_code == 200

    hub = client.get("/growth/acquisition-hub?limit=10", headers=workspace)
    assert hub.status_code == 200
    payload = hub.json()
    assert payload["hub_version"] == "specpilot.public_acquisition_hub.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["launch_score"] > 0
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["primary_cta_path"] == "/#demo-gallery"
    assert set(payload["seo_paths"]) >= {"/", "/market/desktop-pc", "/market/laptop"}
    surface_keys = {surface["key"] for surface in payload["surfaces"]}
    assert {
        "demo_gallery",
        "market_desktop",
        "market_laptop",
        "public_report",
        "referral_waitlist",
        "trust_center",
        "pricing_interest",
    } <= surface_keys
    public_report_surface = next(
        surface for surface in payload["surfaces"] if surface["key"] == "public_report"
    )
    assert public_report_surface["path"] == "/r/{share_token}"
    assert "공유 리포트" in public_report_surface["label"]
    assert payload["channel_actions"]
    assert payload["next_actions"]
    assert payload["recent_growth_events"]

    board = client.get("/growth/public-conversion-board?limit=10", headers=workspace)
    assert board.status_code == 200
    board_payload = board.json()
    assert board_payload["board_version"] == "specpilot.public_conversion_board.v1"
    assert board_payload["workspace_id"] == payload["workspace_id"]
    assert board_payload["conversion_score"] > 0
    assert board_payload["status"] in {"ok", "warning", "blocker"}
    assert board_payload["metric_cards"]["public_share_views"] >= 1
    assert board_payload["metric_cards"]["referral_waitlist"] >= 1
    assert board_payload["metric_cards"]["pricing_intents"] >= 1
    stage_keys = {stage["key"] for stage in board_payload["stages"]}
    assert {
        "traffic",
        "activation",
        "sharing",
        "referral",
        "monetization",
        "reliability",
    } <= stage_keys
    assert any(
        surface["key"] == "public_report"
        for surface in board_payload["priority_surfaces"]
    )
    assert board_payload["channel_actions"]
    assert board_payload["next_actions"]
    assert board_payload["recent_growth_events"]

    isolated_board = client.get(
        "/growth/public-conversion-board?limit=10",
        headers={"X-SpecPilot-Key": f"pytest-acquisition-isolated-{uuid4().hex}"},
    )
    assert isolated_board.status_code == 200
    assert isolated_board.json()["metric_cards"]["public_share_views"] == 0


def test_launch_experiment_hub_tracks_variant_winner() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-launch-exp-{uuid4().hex}"}
    created = client.post(
        "/growth/launch-experiments",
        headers=workspace,
        json={
            "name": "커뮤니티 첫 분석 CTA",
            "channel": "community",
            "audience": "desktop_pc_buyer",
            "hypothesis": "구매 실패 방지 메시지가 빠른 진단 메시지보다 전환이 높다.",
            "primary_metric": "subscription_cta",
            "target_surface": "community-post",
            "category": "desktop_pc",
            "variants": [
                {
                    "label": "구매 실패 방지",
                    "headline": "200만원 PC 견적, 결제 전에 실패 가능성을 줄이세요",
                    "body": "가격 타이밍, 호환성, 결제 전 검수까지 한 번에 확인합니다.",
                    "cta_label": "구매 전 검수하기",
                    "cta_path": "/#start-concierge",
                    "allocation_percent": 50,
                },
                {
                    "label": "3분 빠른 진단",
                    "headline": "컴퓨터 견적 고민을 3분 안에 줄이세요",
                    "body": "용도와 예산을 넣으면 후보와 가격 대기 여부를 보여줍니다.",
                    "cta_label": "3분 진단 시작",
                    "cta_path": "/",
                    "allocation_percent": 50,
                },
            ],
        },
    )
    assert created.status_code == 200
    experiment = created.json()
    assert experiment["experiment_id"].startswith("lexp_")
    assert len(experiment["variants"]) == 2
    winner_variant = experiment["variants"][0]["variant_id"]
    slower_variant = experiment["variants"][1]["variant_id"]

    for index in range(12):
        response = client.post(
            f"/growth/launch-experiments/{experiment['experiment_id']}/events",
            headers=workspace,
            json={
                "variant_id": winner_variant,
                "event_type": "impression",
                "source": "pytest",
                "surface": "community-post",
                "label": f"winner impression {index}",
            },
        )
        assert response.status_code == 200
    for index in range(2):
        response = client.post(
            f"/growth/launch-experiments/{experiment['experiment_id']}/events",
            headers=workspace,
            json={
                "variant_id": winner_variant,
                "event_type": "conversion",
                "source": "pytest",
                "surface": "community-post",
                "label": f"winner conversion {index}",
            },
        )
        assert response.status_code == 200
    for index in range(10):
        response = client.post(
            f"/growth/launch-experiments/{experiment['experiment_id']}/events",
            headers=workspace,
            json={
                "variant_id": slower_variant,
                "event_type": "impression",
                "source": "pytest",
                "surface": "community-post",
                "label": f"slower impression {index}",
            },
        )
        assert response.status_code == 200

    missing = client.post(
        f"/growth/launch-experiments/{experiment['experiment_id']}/events",
        headers=workspace,
        json={"variant_id": "missing_variant", "event_type": "conversion"},
    )
    assert missing.status_code == 404

    dashboard = client.get(
        "/growth/launch-experiment-dashboard?limit=10",
        headers=workspace,
    )
    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert payload["dashboard_version"] == "specpilot.launch_experiment_hub.v1"
    assert payload["experiment_count"] == 1
    assert payload["total_impressions"] == 22
    assert payload["total_conversions"] == 2
    assert payload["best_variant_label"] == "구매 실패 방지"
    assert payload["experiments"][0]["winning_variant_id"] == winner_variant
    assert payload["recommended_experiments"]
    assert payload["recent_events"]

    funnel = client.get("/growth/funnel", headers=workspace)
    assert funnel.status_code == 200
    assert funnel.json()["paid_intent_rate"] > 0


def test_public_proof_hub_publishes_trust_and_conversion_evidence() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-proof-hub-{uuid4().hex}"}
    analysis = client.post(
        "/analyze",
        headers=workspace,
        json={
            "query": "영상 편집용 데스크톱 200만원 안에서 구매 실패 줄이게 추천해줘",
            "category": "desktop_pc",
            "budget_krw": 2_000_000,
            "purpose": "Premiere Pro, QHD gaming",
            "must_haves": ["32GB RAM", "QHD 144Hz"],
            "exclusions": ["중고"],
        },
    )
    assert analysis.status_code == 200
    analysis_payload = analysis.json()
    trace_id = analysis_payload["graph_trace_id"]
    top = analysis_payload["report"]["top_recommendations"][0]

    saved = client.post(
        "/reports/save",
        headers=workspace,
        json={"trace_id": trace_id, "title": "공개 검증 허브 테스트"},
    )
    assert saved.status_code == 200
    report_id = saved.json()["report_id"]

    share = client.post(f"/reports/{report_id}/share", headers=workspace)
    assert share.status_code == 200
    public_report = client.get(f"/public/reports/{share.json()['share_token']}")
    assert public_report.status_code == 200

    feedback = client.post(
        "/feedback",
        headers=workspace,
        json={
            "trace_id": trace_id,
            "rating": 5,
            "purchase_intent": True,
            "selected_product_id": top["product"]["id"],
            "reason": "근거와 결제 전 체크가 명확해서 공유하기 좋았습니다.",
            "improvement_requests": ["실제 구매 링크 더 보기"],
            "contact": "proof@example.com",
        },
    )
    assert feedback.status_code == 200

    experiment = client.post(
        "/growth/launch-experiments",
        headers=workspace,
        json={
            "name": "공개 proof CTA",
            "channel": "landing",
            "audience": "desktop_pc_buyer",
            "hypothesis": "신뢰 proof CTA가 유료 관심 전환을 만든다.",
            "primary_metric": "subscription_cta",
            "target_surface": "proof-hub",
        },
    )
    assert experiment.status_code == 200
    experiment_payload = experiment.json()
    variant_id = experiment_payload["variants"][0]["variant_id"]
    for event_type in ["impression", "conversion"]:
        event = client.post(
            f"/growth/launch-experiments/{experiment_payload['experiment_id']}/events",
            headers=workspace,
            json={
                "variant_id": variant_id,
                "event_type": event_type,
                "source": "pytest",
                "surface": "proof-hub",
                "label": f"proof {event_type}",
            },
        )
        assert event.status_code == 200

    proof = client.get("/public/proof-hub?limit=10", headers=workspace)
    assert proof.status_code == 200
    payload = proof.json()
    assert payload["proof_version"] == "specpilot.public_proof_hub.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["proof_score"] > 0
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["metric_cards"]["feedback_count"] >= 1
    assert payload["metric_cards"]["public_share_views"] >= 1
    assert payload["hero_proof_strip"]
    assert payload["trust_badges"]
    assert payload["evidence_kit"]
    asset_keys = {asset["key"] for asset in payload["proof_assets"]}
    assert {
        "trust_center",
        "market_reports",
        "share_review",
        "buyer_feedback",
        "cta_experiment",
        "public_surfaces",
    } <= asset_keys
    assert any(path == "/policy/trust-center" for path in payload["public_paths"])
    assert payload["objection_answers"]
    assert payload["cta_cards"]
    assert payload["recent_feedback"]
    assert payload["next_actions"]


def test_public_proof_hub_has_launch_evidence_for_empty_workspace() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-empty-proof-{uuid4().hex}"}
    proof = client.get("/public/proof-hub?limit=4", headers=workspace)
    assert proof.status_code == 200
    payload = proof.json()
    assert payload["metric_cards"]["analysis_runs"] == 0
    assert payload["hero_proof_strip"]
    assert "제휴 여부와 추천 순위를 분리합니다" in payload["hero_proof_strip"]
    evidence_titles = {item["title"] for item in payload["evidence_kit"]}
    assert {
        "추천 공정성 공개",
        "시장 리포트형 시작점",
        "공유 검토 루프",
        "실구매 실패 방어선",
    } <= evidence_titles
    assert all(item["source_path"] for item in payload["evidence_kit"])
    assert payload["objection_answers"]


def test_public_social_proof_wall_masks_feedback_and_purchase_evidence() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-social-proof-{uuid4().hex}"}
    analysis = client.post(
        "/analyze",
        headers=workspace,
        json={
            "query": "AI 개발용 데스크톱 230만원 안에서 실패 없이 추천해줘",
            "category": "desktop_pc",
            "budget_krw": 2_300_000,
            "purpose": "local LLM, QHD gaming",
            "must_haves": ["32GB RAM", "RTX 4070급"],
            "exclusions": ["중고"],
        },
    )
    assert analysis.status_code == 200
    analysis_payload = analysis.json()
    trace_id = analysis_payload["graph_trace_id"]
    top = analysis_payload["report"]["top_recommendations"][0]

    saved = client.post(
        "/reports/save",
        headers=workspace,
        json={"trace_id": trace_id, "title": "공개 소셜 proof 테스트"},
    )
    assert saved.status_code == 200
    report_id = saved.json()["report_id"]

    feedback = client.post(
        "/feedback",
        headers=workspace,
        json={
            "trace_id": trace_id,
            "rating": 5,
            "purchase_intent": True,
            "selected_product_id": top["product"]["id"],
            "reason": (
                "proof@example.com에게도 공유했습니다. "
                "010-1234-5678 연락처 없이 근거가 명확했습니다."
            ),
            "improvement_requests": ["팀 구매 비교"],
            "contact": "proof@example.com",
        },
    )
    assert feedback.status_code == 200

    outcome = client.post(
        f"/reports/{report_id}/purchase-outcomes",
        headers=workspace,
        json={
            "product_id": top["product"]["id"],
            "status": "purchased",
            "final_paid_price_krw": top["price"]["effective_price_krw"],
            "source_channel": "pytest",
            "reason": "가격과 옵션을 재확인하고 구매했습니다.",
            "satisfaction": 5,
            "order_reference": "ORDER-123456",
        },
    )
    assert outcome.status_code == 200

    first_referral = client.post(
        "/growth/waitlist-referrals",
        headers=workspace,
        json={
            "email": "social-proof@example.com",
            "persona": "developer",
            "use_case": "친구에게 구매 리포트를 공유",
            "contact_consent": True,
            "source": "pytest",
        },
    )
    assert first_referral.status_code == 200
    referred = client.post(
        "/growth/waitlist-referrals",
        headers=workspace,
        json={
            "email": "friend-social-proof@example.com",
            "persona": "creator",
            "use_case": "추천받은 구매 검토",
            "referred_by_code": first_referral.json()["referral_code"],
            "contact_consent": True,
            "source": "pytest",
        },
    )
    assert referred.status_code == 200

    wall = client.get("/public/social-proof-wall?limit=8", headers=workspace)
    assert wall.status_code == 200
    payload = wall.json()
    assert payload["wall_version"] == "specpilot.public_social_proof_wall.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["proof_score"] > 0
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["metric_cards"]["feedback_count"] >= 1
    assert payload["metric_cards"]["completed_purchase_outcomes"] >= 1
    assert payload["metric_cards"]["referred_signup_count"] >= 1
    kinds = {item["kind"] for item in payload["items"]}
    assert {"feedback", "purchase_outcome", "referral"} <= kinds
    bodies = "\n".join(item["body"] for item in payload["items"])
    assert "proof@example.com" not in bodies
    assert "010-1234-5678" not in bodies
    assert "[이메일 마스킹]" in bodies
    assert payload["trust_notes"]
    assert payload["cta_cards"]
    assert payload["next_actions"]

    empty = client.get(
        "/public/social-proof-wall?limit=4",
        headers={"X-SpecPilot-Key": f"pytest-empty-social-proof-{uuid4().hex}"},
    )
    assert empty.status_code == 200
    empty_payload = empty.json()
    assert empty_payload["items"]
    assert empty_payload["items"][0]["kind"] == "trust"
    assert empty_payload["metric_cards"]["feedback_count"] == 0


def test_public_launch_objection_kit_answers_first_visitor_doubts() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-objection-kit-{uuid4().hex}"}

    response = client.get("/public/launch-objection-kit?limit=5", headers=workspace)
    assert response.status_code == 200
    payload = response.json()
    assert payload["kit_version"] == "specpilot.public_launch_objection_kit.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["objection_score"] > 0
    assert payload["primary_cta_path"] == "/#analysis"
    objection_keys = {item["key"] for item in payload["objections"]}
    assert {
        "vs_price_comparison",
        "affiliate_bias",
        "fresh_price",
        "privacy",
        "first_buyer",
        "team_purchase",
    } <= objection_keys
    assert any(
        "최저가 비교 사이트" in item["question"] for item in payload["objections"]
    )
    assert len(payload["comparisons"]) >= 4
    assert payload["trust_badges"]
    assert payload["channel_replies"]
    assert payload["next_actions"]


def test_public_launch_share_pack_packages_visitor_share_copy() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-share-pack-{uuid4().hex}"}
    event = client.post(
        "/growth/events",
        headers=workspace,
        json={
            "event_type": "share_cta",
            "source": "pytest-share-pack",
            "surface": "launch-share-pack",
            "label": "공유 확산팩 복사",
        },
    )
    assert event.status_code == 200

    response = client.get("/public/launch-share-pack?limit=6", headers=workspace)
    assert response.status_code == 200
    payload = response.json()
    assert payload["pack_version"] == "specpilot.public_launch_share_pack.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["share_score"] > 0
    assert payload["primary_url"].startswith("/launch")
    channels = {variant["channel"] for variant in payload["variants"]}
    assert {"kakao", "community", "team", "email"} <= channels
    assert all("source=share-pack" in variant["share_url"] for variant in payload["variants"])
    assert all(variant["copy_text"] for variant in payload["variants"])
    assert "launch_share_copy_click" in payload["measurement_events"]
    assert payload["trust_disclosures"]
    assert payload["next_actions"]


def test_public_launch_action_router_prioritizes_visitor_next_steps() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-action-router-{uuid4().hex}"}
    client.post(
        "/growth/events",
        headers=workspace,
        json={
            "event_type": "subscription_cta",
            "source": "pytest-action-router",
            "surface": "launch-action-router",
            "label": "요금제 관심 CTA",
        },
    )

    response = client.get("/public/launch-action-router?limit=6", headers=workspace)
    assert response.status_code == 200
    payload = response.json()
    assert payload["router_version"] == "specpilot.public_launch_action_router.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["routing_score"] > 0
    route_keys = {route["key"] for route in payload["routes"]}
    assert {
        "first_purchase_analysis",
        "shared_review",
        "waitlist_referral",
        "team_purchase",
        "paid_intent",
    } <= route_keys
    assert payload["default_route_key"] in route_keys
    assert all(route["cta_path"].startswith("/#") for route in payload["routes"])
    assert "launch_action_route_click" in payload["measurement_events"]
    assert payload["quick_filters"]
    assert payload["next_actions"]


def test_public_launch_smoke_dashboard_checks_publish_surfaces() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-launch-smoke-{uuid4().hex}"}
    event = client.post(
        "/growth/events",
        headers=workspace,
        json={
            "event_type": "analysis_view",
            "source": "pytest-launch-smoke",
            "surface": "launch-smoke",
            "label": "런칭 스모크 분석 CTA",
            "metadata": {"route_key": "first_purchase_analysis"},
        },
    )
    assert event.status_code == 200

    response = client.get("/public/launch-smoke?limit=6", headers=workspace)
    assert response.status_code == 200
    payload = response.json()
    assert payload["smoke_version"] == "specpilot.public_launch_smoke.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["smoke_score"] > 0
    assert payload["ok_count"] + payload["warning_count"] + payload["blocker_count"] == len(
        payload["checks"],
    )
    check_keys = {check["key"] for check in payload["checks"]}
    assert {
        "launch_room",
        "market_reports",
        "proof_hub",
        "objection_kit",
        "share_pack",
        "action_router",
        "conversion_board",
        "launch_gate",
        "seo_distribution",
        "measurement",
    } <= check_keys
    assert any(check["public_path"].endswith("/launch") for check in payload["checks"])
    assert "launch_smoke_view" in payload["measurement_events"]
    assert payload["publish_ready_paths"]
    assert payload["next_actions"]


def test_growth_launch_war_room_prioritizes_first_day_actions() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-war-room-{uuid4().hex}"}
    client.post(
        "/growth/events",
        headers=workspace,
        json={
            "event_type": "share_cta",
            "source": "pytest-war-room",
            "surface": "launch",
            "label": "워룸 공유 CTA",
        },
    )
    client.post(
        "/growth/waitlist-referrals",
        headers=workspace,
        json={
            "email": "war-room@example.com",
            "persona": "creator",
            "use_case": "첫 24시간 공개 반응을 보고 싶습니다.",
            "contact_consent": True,
            "source": "pytest-war-room",
        },
    )

    response = client.get("/growth/launch-war-room?limit=8", headers=workspace)
    assert response.status_code == 200
    payload = response.json()
    assert payload["war_room_version"] == "specpilot.launch_war_room.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["decision"] in {
        "scale",
        "limited_push",
        "hold_and_fix",
        "collect_more_signal",
    }
    assert payload["command_score"] > 0
    signal_keys = {signal["key"] for signal in payload["signals"]}
    assert {
        "reaction_pulse",
        "publish_surface",
        "conversion",
        "launch_gate",
        "quality_regression",
        "experiment_velocity",
        "share_referral",
        "paid_intent",
        "measurement_feed",
    } <= signal_keys
    play_ids = {play["play_id"] for play in payload["plays"]}
    assert {"amplify_hot_surface", "fix_publish_warning", "rescue_activation"} <= play_ids
    assert payload["metric_cards"]["growth_events"] >= 1
    assert payload["escalation_paths"]
    assert payload["next_actions"]


def test_growth_launch_incident_center_builds_release_runbook() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-incident-center-{uuid4().hex}"}
    analysis = client.post(
        "/analyze",
        headers=workspace,
        json={
            "query": "영상 편집과 QHD 게임용 데스크톱을 180만원 안에서 추천해줘",
            "category": "desktop_pc",
            "budget_krw": 1800000,
            "purpose": "qhd_creator",
            "must_haves": ["RTX 4070", "32GB RAM"],
        },
    )
    assert analysis.status_code == 200
    trace_id = analysis.json()["graph_trace_id"]
    event = client.post(
        "/growth/events",
        headers=workspace,
        json={
            "event_type": "share_cta",
            "trace_id": trace_id,
            "source": "pytest-incident-center",
            "surface": "launch",
            "label": "인시던트 센터 공유 CTA",
        },
    )
    assert event.status_code == 200
    export = client.post(
        "/ops/observability/exports",
        headers=workspace,
        json={
            "trace_id": trace_id,
            "destination": "opentelemetry",
            "include_payload": True,
        },
    )
    assert export.status_code == 200

    response = client.get("/growth/launch-incident-center?limit=8", headers=workspace)
    assert response.status_code == 200
    payload = response.json()
    assert payload["center_version"] == "specpilot.launch_incident_center.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["incident_level"] in {
        "green_scale",
        "sev3_watch",
        "sev2_limited_launch",
        "sev1_hold_launch",
    }
    assert payload["incident_score"] > 0
    signal_keys = {signal["key"] for signal in payload["signals"]}
    assert {
        "public_surface",
        "readiness_gate",
        "quality_regression",
        "integration_blockers",
        "data_governance",
        "observability_outbox",
        "measurement_feed",
    } <= signal_keys
    assert payload["metric_cards"]["queued_observability_exports"] >= 1
    assert payload["metric_cards"]["growth_events"] >= 1
    assert payload["commander_brief"]
    assert payload["runbook"]
    assert payload["escalation_paths"]
    assert "launch_incident_center_view" in payload["tracking_events"]
    assert payload["next_actions"]


def test_growth_launch_week_recap_summarizes_first_week_response() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-week-recap-{uuid4().hex}"}
    for event_type in ["analysis_view", "share_cta", "subscription_cta"]:
        response = client.post(
            "/growth/events",
            headers=workspace,
            json={
                "event_type": event_type,
                "source": "pytest-week-recap",
                "surface": "launch",
                "label": f"D+7 {event_type}",
            },
        )
        assert response.status_code == 200
    referral = client.post(
        "/growth/waitlist-referrals",
        headers=workspace,
        json={
            "email": "week-recap@example.com",
            "persona": "creator",
            "use_case": "첫 주 공개 반응을 주변에 공유하고 싶습니다.",
            "contact_consent": True,
            "source": "pytest-week-recap",
        },
    )
    assert referral.status_code == 200
    intent = client.post(
        "/billing/subscription-intents",
        headers=workspace,
        json={
            "email": "week-recap@example.com",
            "plan_id": "premium",
            "billing_cycle": "monthly",
            "persona": "creator",
            "use_case": "가격 알림과 결제 전 검수를 첫 주에 써보고 싶습니다.",
            "team_size": 1,
            "max_budget_krw": 50_000,
            "feature_priorities": ["가격 알림", "결제 전 검수"],
            "purchase_timing": "within_7_days",
            "source": "pytest-week-recap",
        },
    )
    assert intent.status_code == 200
    experiment = client.post(
        "/growth/launch-experiments",
        headers=workspace,
        json={
            "name": "D+7 공개 후속 CTA",
            "channel": "community",
            "audience": "desktop_pc_buyer",
            "hypothesis": "첫 주 성과 리포트가 다시 공유를 만든다.",
            "primary_metric": "share_cta",
            "target_surface": "week-recap",
            "category": "desktop_pc",
            "variants": [
                {
                    "label": "첫 주 리포트",
                    "headline": "SpecPilot AI 첫 주 공개 리포트",
                    "body": "실제 반응과 다음 개선 항목을 공개합니다.",
                    "cta_label": "첫 주 리포트 보기",
                    "cta_path": "/launch#launch-week-recap",
                    "allocation_percent": 100,
                },
            ],
        },
    )
    assert experiment.status_code == 200
    variant_id = experiment.json()["variants"][0]["variant_id"]
    event = client.post(
        f"/growth/launch-experiments/{experiment.json()['experiment_id']}/events",
        headers=workspace,
        json={
            "variant_id": variant_id,
            "event_type": "conversion",
            "source": "pytest-week-recap",
            "surface": "week-recap",
            "label": "첫 주 리포트 전환",
        },
    )
    assert event.status_code == 200

    response = client.get("/growth/launch-week-recap?limit=8", headers=workspace)
    assert response.status_code == 200
    payload = response.json()
    assert payload["recap_version"] == "specpilot.launch_week_recap.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["recap_score"] > 0
    assert payload["metric_cards"]["growth_events"] >= 3
    assert payload["metric_cards"]["pricing_intents"] >= 1
    win_keys = {win["key"] for win in payload["wins"]}
    assert {
        "reaction_learning",
        "conversion_surface",
        "referral_loop",
        "paid_demand",
        "retention_loop",
        "experiment_learning",
    } <= win_keys
    risk_keys = {risk["key"] for risk in payload["risks"]}
    assert {
        "measurement_gap",
        "publish_surface",
        "conversion_bottleneck",
        "quality_regression",
    } <= risk_keys
    assert "SpecPilot AI 첫 주 공개 리포트" in payload["founder_update"]
    assert payload["channel_moves"]
    assert payload["next_actions"]


def test_growth_launch_community_kit_prepares_reply_templates() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-community-kit-{uuid4().hex}"}
    for event_type in ["analysis_view", "share_cta", "share_cta", "subscription_cta"]:
        response = client.post(
            "/growth/events",
            headers=workspace,
            json={
                "event_type": event_type,
                "source": "pytest-community-kit",
                "surface": "community-thread",
                "label": f"커뮤니티 대응 {event_type}",
            },
        )
        assert response.status_code == 200
    referral = client.post(
        "/growth/waitlist-referrals",
        headers=workspace,
        json={
            "email": "community-kit@example.com",
            "persona": "creator",
            "use_case": "커뮤니티 댓글에 답하면서 초대 링크를 공유하고 싶습니다.",
            "contact_consent": True,
            "source": "pytest-community-kit",
        },
    )
    assert referral.status_code == 200

    response = client.get("/growth/launch-community-kit?limit=8", headers=workspace)
    assert response.status_code == 200
    payload = response.json()
    assert payload["kit_version"] == "specpilot.launch_community_kit.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["response_score"] > 0
    assert payload["metric_cards"]["reply_templates"] >= 6
    assert "SpecPilot AI 첫 주 공개 리포트" in payload["pinned_update"]
    template_keys = {template["key"] for template in payload["reply_templates"]}
    assert {
        "reply_pinned_context",
        "reply_vs_price_comparison",
        "reply_affiliate_bias",
        "reply_fresh_price",
        "reply_privacy",
        "reply_first_buyer",
        "reply_team_purchase",
    } <= template_keys
    assert all(template["copy_text"] for template in payload["reply_templates"])
    assert all(template["tracking_event"] for template in payload["reply_templates"])
    risk_keys = {risk["key"] for risk in payload["risks"]}
    assert {
        "reply_latency",
        "objection_gap",
        "share_context_loss",
        "broken_public_surface",
        "overclaim",
    } <= risk_keys
    assert "launch_community_reply_copy" in payload["tracking_events"]
    assert payload["next_actions"]


def test_growth_launch_media_kit_packages_external_launch_assets() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-media-kit-{uuid4().hex}"}
    for event_type in ["analysis_view", "share_cta", "subscription_cta"]:
        response = client.post(
            "/growth/events",
            headers=workspace,
            json={
                "event_type": event_type,
                "source": "pytest-media-kit",
                "surface": "media-kit",
                "label": f"미디어 키트 {event_type}",
            },
        )
        assert response.status_code == 200
    referral = client.post(
        "/growth/waitlist-referrals",
        headers=workspace,
        json={
            "email": "media-kit@example.com",
            "persona": "creator",
            "use_case": "뉴스레터와 커뮤니티에 공개 런칭룸을 소개하고 싶습니다.",
            "contact_consent": True,
            "source": "pytest-media-kit",
        },
    )
    assert referral.status_code == 200

    response = client.get("/growth/launch-media-kit?limit=8", headers=workspace)
    assert response.status_code == 200
    payload = response.json()
    assert payload["kit_version"] == "specpilot.launch_media_kit.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["media_score"] > 0
    assert payload["hero_statement"]
    asset_keys = {asset["key"] for asset in payload["assets"]}
    assert {
        "product_workbench",
        "launch_room",
        "proof_hub",
        "social_proof",
    } <= asset_keys
    pitch_channels = {pitch["channel"] for pitch in payload["pitches"]}
    assert {"newsletter", "creator", "community", "team"} <= pitch_channels
    assert all(pitch["copy_text"] for pitch in payload["pitches"])
    assert payload["proof_points"]
    assert "launch_media_pitch_copy" in payload["tracking_events"]
    assert payload["usage_guidelines"]
    assert payload["next_actions"]


def test_growth_launch_activation_offer_prioritizes_public_ctas() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-activation-offer-{uuid4().hex}"}
    for event_type in ["analysis_view", "share_cta", "subscription_cta"]:
        response = client.post(
            "/growth/events",
            headers=workspace,
            json={
                "event_type": event_type,
                "source": "pytest-activation-offer",
                "surface": "launch",
                "label": f"전환 오퍼 {event_type}",
            },
        )
        assert response.status_code == 200
    referral = client.post(
        "/growth/waitlist-referrals",
        headers=workspace,
        json={
            "email": "activation-offer@example.com",
            "persona": "team_purchase",
            "use_case": "팀 노트북 구매 기준을 같이 검토하고 싶습니다.",
            "contact_consent": True,
            "source": "pytest-activation-offer",
        },
    )
    assert referral.status_code == 200
    pricing = client.post(
        "/billing/subscription-intents",
        headers=workspace,
        json={
            "email": "activation-offer@example.com",
            "plan_id": "team",
            "billing_cycle": "monthly",
            "persona": "team_purchase_owner",
            "use_case": "회사 장비 구매 표준안을 만들고 싶습니다.",
            "team_size": 12,
            "max_budget_krw": 18000000,
            "feature_priorities": ["team_consult", "checkout_review"],
            "purchase_timing": "within_30_days",
            "contact_consent": True,
            "source": "pytest-activation-offer",
        },
    )
    assert pricing.status_code == 200

    response = client.get("/growth/launch-activation-offer?limit=8", headers=workspace)
    assert response.status_code == 200
    payload = response.json()
    assert payload["offer_version"] == "specpilot.launch_activation_offer.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["activation_score"] > 0
    assert payload["primary_offer"]["key"] in {offer["key"] for offer in payload["offers"]}
    offer_keys = {offer["key"] for offer in payload["offers"]}
    assert {
        "quick_purchase_analysis",
        "waitlist_referral_pass",
        "premium_trial_signal",
        "team_purchase_consult",
        "community_reply_to_analysis",
    } <= offer_keys
    assert all(offer["cta_path"].startswith("/") for offer in payload["offers"])
    assert payload["handoff_prompts"]
    assert payload["proof_points"]
    assert "launch_activation_primary_click" in payload["tracking_events"]
    assert payload["metric_cards"]["pricing_intents"] >= 1
    assert payload["next_actions"]


def test_growth_launch_activation_offer_does_not_regenerate_heavy_launch_kits(
    monkeypatch,
) -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-activation-fast-{uuid4().hex}"}

    def fail_heavy_launch_kit(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("activation offer must use the fast launch signal path")

    monkeypatch.setattr(
        SpecPilotStore,
        "launch_media_kit_for_workspace",
        fail_heavy_launch_kit,
    )
    monkeypatch.setattr(
        SpecPilotStore,
        "launch_community_kit_for_workspace",
        fail_heavy_launch_kit,
    )

    response = client.get("/growth/launch-activation-offer?limit=4", headers=workspace)

    assert response.status_code == 200
    payload = response.json()
    assert payload["offer_version"] == "specpilot.launch_activation_offer.v1"
    assert payload["metric_cards"]["media_score"] >= 0
    assert payload["metric_cards"]["response_score"] >= 0
    assert payload["offers"]


def test_public_launch_room_packages_demo_proof_and_growth_ctas() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-launch-room-{uuid4().hex}"}
    referral = client.post(
        "/growth/waitlist-referrals",
        headers=workspace,
        json={
            "email": "launch-room@example.com",
            "persona": "creator",
            "use_case": "친구에게 공개 구매 리포트를 공유하고 싶습니다.",
            "contact_consent": True,
            "source": "launch-room-test",
        },
    )
    assert referral.status_code == 200
    intent = client.post(
        "/billing/subscription-intents",
        headers=workspace,
        json={
            "email": "launch-room@example.com",
            "plan_id": "premium",
            "persona": "creator",
            "use_case": "가격 알림과 결제 전 검수를 쓰고 싶습니다.",
            "feature_priorities": ["가격 알림", "공유 리포트"],
            "source": "launch-room-test",
        },
    )
    assert intent.status_code == 200

    room = client.get("/public/launch-room?limit=6", headers=workspace)
    assert room.status_code == 200
    payload = room.json()
    assert payload["room_version"] == "specpilot.public_launch_room.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["headline"]
    assert payload["primary_cta_path"] == "/#analysis"
    assert payload["proof_strip"]
    assert len(payload["demo_cards"]) >= 3
    demo_keys = {card["key"] for card in payload["demo_cards"]}
    assert "creator-qhd-desktop" in demo_keys
    launch_keys = {card["key"] for card in payload["launch_cards"]}
    assert {
        "proof_hub",
        "acquisition_hub",
        "objection_kit",
        "share_pack",
        "action_router",
        "launch_pulse",
        "referral_waitlist",
        "pricing_interest",
    } <= launch_keys
    assert {item["path"] for item in payload["market_links"]} == {
        "/market/desktop-pc",
        "/market/laptop",
    }
    assert payload["secondary_ctas"]
    assert payload["channel_posts"]
    assert payload["next_actions"]


def test_growth_retention_hub_prioritizes_reengagement_loops() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-retention-{uuid4().hex}"}
    analysis = client.post(
        "/analyze",
        headers=workspace,
        json={
            "query": "QHD 게임과 영상 편집용 데스크톱 210만원 안에서 추천해줘",
            "category": "desktop_pc",
            "budget_krw": 2_100_000,
            "purpose": "QHD gaming, Premiere Pro",
            "must_haves": ["QHD 144Hz", "32GB RAM", "업그레이드 여지"],
            "exclusions": ["중고", "리퍼"],
        },
    )
    assert analysis.status_code == 200
    analysis_payload = analysis.json()
    trace_id = analysis_payload["graph_trace_id"]
    top = analysis_payload["report"]["top_recommendations"][0]
    first_alert = analysis_payload["report"]["price_alerts"][0]

    saved = client.post(
        "/reports/save",
        headers=workspace,
        json={"trace_id": trace_id, "title": "리텐션 허브 테스트 리포트"},
    )
    assert saved.status_code == 200
    report_id = saved.json()["report_id"]

    share = client.post(f"/reports/{report_id}/share", headers=workspace)
    assert share.status_code == 200
    public_report = client.get(f"/public/reports/{share.json()['share_token']}")
    assert public_report.status_code == 200

    subscribed = client.post(
        "/alerts/subscribe",
        headers=workspace,
        json={
            "trace_id": trace_id,
            "product_id": first_alert["product_id"],
            "target_price_krw": first_alert["target_price_krw"],
            "channels": ["email"],
            "contact": "retention@example.com",
            "owner_label": "pytest",
        },
    )
    assert subscribed.status_code == 200

    advisor = client.post(
        f"/reports/{report_id}/advisor-questions",
        headers=workspace,
        json={
            "question": "지금 결제해도 돼, 아니면 목표가까지 기다릴까?",
            "context": "일주일 안에 구매하고 싶지만 가격 타이밍이 중요합니다.",
            "selected_product_id": top["product"]["id"],
            "contact": "retention@example.com",
        },
    )
    assert advisor.status_code == 200

    outcome = client.post(
        f"/reports/{report_id}/purchase-outcomes",
        headers=workspace,
        json={
            "product_id": top["product"]["id"],
            "status": "delayed",
            "reason": "목표가 알림까지 기다리기로 했습니다.",
            "satisfaction": 4,
        },
    )
    assert outcome.status_code == 200

    event = client.post(
        "/growth/events",
        headers=workspace,
        json={
            "event_type": "alert_cta",
            "trace_id": trace_id,
            "report_id": report_id,
            "product_id": top["product"]["id"],
            "source": "pytest",
            "surface": "retention-hub",
            "label": "리텐션 허브 가격 알림 클릭",
        },
    )
    assert event.status_code == 200

    hub = client.get("/growth/retention-hub?limit=10", headers=workspace)
    assert hub.status_code == 200
    payload = hub.json()
    assert payload["hub_version"] == "specpilot.retention_hub.v1"
    assert payload["workspace_id"].startswith("workspace_")
    assert payload["retention_score"] > 0
    assert payload["status"] in {"ok", "warning", "blocker"}
    assert payload["metric_cards"]["saved_reports"] >= 1
    assert payload["metric_cards"]["active_alerts"] >= 1
    signal_keys = {signal["key"] for signal in payload["signals"]}
    assert {
        "saved_to_alert",
        "share_revisit",
        "decision_followup",
        "advisor_loop",
        "purchase_learning",
        "delivery_engagement",
    } <= signal_keys
    play_ids = {play["play_id"] for play in payload["plays"]}
    assert {"price_wait_alert", "outcome_capture", "advisor_rescue"} <= play_ids
    assert payload["next_actions"]
    assert payload["recent_events"]
    assert payload["recent_advisor_answers"]
    assert payload["recent_purchase_outcomes"]


def test_privacy_policy_endpoint_exposes_retention_and_controls() -> None:
    response = client.get("/policy/privacy")

    assert response.status_code == 200
    payload = response.json()
    assert payload["policy_version"] == "specpilot.privacy.v1"
    assert payload["data_minimization"]
    assert payload["public_report_policy"]
    assert payload["contact_policy"]
    assert payload["retention_policy"]
    assert payload["user_controls"]
    assert payload["prohibited_data"]
    assert {item["category"] for item in payload["data_categories"]} >= {
        "analysis",
        "contact",
        "delivery",
    }


def test_trust_center_combines_public_policy_and_launch_gates() -> None:
    response = client.get("/policy/trust-center")

    assert response.status_code == 200
    payload = response.json()
    assert payload["policy_version"] == "specpilot.trust_center.v1"
    assert payload["generated_at"]
    assert payload["headline"]
    assert payload["overall_status"] in {"ok", "warning", "blocker"}
    assert payload["trust_policy"]["fairness_rules"]
    assert payload["privacy_policy"]["public_report_policy"]
    assert len(payload["public_commitments"]) >= 4
    assert any("제휴" in item for item in payload["public_commitments"])
    assert any("공개 리포트" in item for item in payload["buyer_rights"])
    assert {gate["area"] for gate in payload["operational_gates"]} >= {
        "recommendation_fairness",
        "source_verification",
        "privacy",
        "human_review",
    }
    assert all(gate["public_message"] for gate in payload["operational_gates"])
    assert payload["risk_disclosures"]
    assert payload["escalation_paths"]
    assert payload["next_actions"]


def test_intake_diagnosis_returns_questions_and_normalized_request() -> None:
    weak = client.post(
        "/intake/diagnose",
        json={
            "query": "PC 추천",
            "category": "desktop_pc",
            "budget_krw": None,
            "purpose": "",
            "must_haves": [],
            "exclusions": [],
        },
    )

    assert weak.status_code == 200
    weak_payload = weak.json()
    assert weak_payload["readiness_label"] == "분석 전 질문 필요"
    assert "budget_krw" in weak_payload["missing_slots"]
    assert "purpose" in weak_payload["missing_slots"]
    assert weak_payload["clarifying_questions"]
    assert "중고" in weak_payload["suggested_exclusions"]
    assert weak_payload["normalized_request"]["channels"] == [
        "price_compare",
        "open_market",
        "official_store",
    ]

    strong = client.post(
        "/intake/diagnose",
        json={
            "query": "영상 편집과 QHD 144Hz 게임용 데스크톱 220만원 안에서 맞춰줘",
            "category": "desktop_pc",
            "budget_krw": 2_200_000,
            "purpose": "Premiere Pro, QHD gaming",
            "must_haves": ["32GB RAM", "QHD 144Hz"],
            "exclusions": ["중고", "리퍼"],
        },
    )

    assert strong.status_code == 200
    strong_payload = strong.json()
    assert strong_payload["readiness_score"] >= 78
    assert strong_payload["readiness_label"] == "바로 분석 가능"
    assert not strong_payload["missing_slots"]
    assert strong_payload["normalized_request"]["purpose"] == "Premiere Pro, QHD gaming"
    assert "출처 없는 가격" in strong_payload["normalized_request"]["exclusions"]


def test_public_start_concierge_combines_intake_and_playbook() -> None:
    weak = client.post(
        "/public/start-concierge",
        json={
            "query": "PC 추천",
            "category": "desktop_pc",
            "budget_krw": None,
            "purpose": "",
            "must_haves": [],
            "exclusions": [],
        },
    )

    assert weak.status_code == 200
    weak_payload = weak.json()
    assert weak_payload["concierge_version"] == "specpilot.start_concierge.v1"
    assert weak_payload["category"] == "desktop_pc"
    assert weak_payload["readiness_score"] == weak_payload["diagnosis"]["readiness_score"]
    assert weak_payload["matched_playbook"]["category"] == "desktop_pc"
    assert weak_payload["primary_action"]["action_type"] == "complete_intake"
    assert any(
        item["status"] == "blocker" for item in weak_payload["milestones"]
    )
    assert weak_payload["quick_actions"]
    assert weak_payload["proof_points"]

    strong = client.post(
        "/public/start-concierge",
        json={
            "query": "출장이 많은 영상 편집자용 노트북을 골라줘. 2kg 이하, 32GB RAM, GPU 가속",
            "category": "laptop",
            "budget_krw": 2_200_000,
            "purpose": "출장 편집, Premiere Pro",
            "must_haves": ["2kg 이하", "32GB RAM", "외장 GPU"],
            "exclusions": ["중고", "리퍼", "발열 반복 불만"],
        },
    )

    assert strong.status_code == 200
    strong_payload = strong.json()
    assert strong_payload["category"] == "laptop"
    assert strong_payload["readiness_score"] >= 78
    assert strong_payload["primary_action"]["action_type"] == "run_analysis"
    assert strong_payload["matched_playbook"]["playbook_id"] == "portable-creator-laptop"
    assert strong_payload["diagnosis"]["normalized_request"]["category"] == "laptop"
    assert any(action["target"] == "#trust-center" for action in strong_payload["quick_actions"])


def test_purchase_decision_board_tracks_saved_report_next_actions() -> None:
    workspace = {"X-SpecPilot-Key": f"pytest-board-{uuid4().hex}"}
    other_workspace = {"X-SpecPilot-Key": f"pytest-board-other-{uuid4().hex}"}

    empty_board = client.get("/reports/decision-board", headers=workspace)
    assert empty_board.status_code == 200
    assert empty_board.json()["report_count"] == 0
    assert empty_board.json()["status"] == "warning"

    analysis = client.post(
        "/analyze",
        headers=workspace,
        json={
            "query": "출장과 영상 편집용 노트북 180만원 안에서 추천해줘",
            "category": "laptop",
            "budget_krw": 1_800_000,
            "purpose": "출장, 영상 편집, 발표",
            "must_haves": ["가벼운 무게", "32GB RAM", "긴 배터리"],
        },
    ).json()
    saved = client.post(
        "/reports/save",
        headers=workspace,
        json={
            "trace_id": analysis["graph_trace_id"],
            "title": "출장 편집 노트북 구매 보드",
            "owner_label": "pytest-board",
        },
    ).json()

    board = client.get("/reports/decision-board", headers=workspace)
    assert board.status_code == 200
    board_payload = board.json()
    assert board_payload["report_count"] == 1
    assert board_payload["missing_outcome_count"] == 1
    assert board_payload["items"][0]["report_id"] == saved["report_id"]
    assert board_payload["items"][0]["has_purchase_outcome"] is False
    assert board_payload["items"][0]["has_purchase_links"] is False
    assert board_payload["items"][0]["category"] == "laptop"
    assert board_payload["next_actions"]

    isolated_board = client.get("/reports/decision-board", headers=other_workspace)
    assert isolated_board.status_code == 200
    assert all(
        item["report_id"] != saved["report_id"]
        for item in isolated_board.json()["items"]
    )

    top = analysis["report"]["top_recommendations"][0]
    blocked_checkout = client.post(
        f"/reports/{saved['report_id']}/checkout-review",
        headers=workspace,
        json={
            "product_id": top["product"]["id"],
            "confirmed_price_krw": top["price"]["effective_price_krw"],
            "seller_answers": {},
        },
    ).json()
    blocked_board = client.get("/reports/decision-board", headers=workspace).json()
    assert blocked_board["checkout_blocked_count"] == 1
    assert blocked_board["items"][0]["checkout_blocked"] is True
    assert blocked_board["items"][0]["board_status"] == "blocker"

    acknowledged_checkout = client.post(
        f"/reports/{saved['report_id']}/checkout-review",
        headers=workspace,
        json={
            "product_id": top["product"]["id"],
            "confirmed_price_krw": top["price"]["effective_price_krw"],
            "acknowledged_risks": blocked_checkout["missing_acknowledgements"],
            "seller_answers": {
                question: "판매자 확인 완료"
                for question in blocked_checkout["seller_questions"]
            },
        },
    ).json()
    unblocked_board = client.get("/reports/decision-board", headers=workspace).json()
    assert unblocked_board["checkout_blocked_count"] == 0
    assert unblocked_board["items"][0]["checkout_blocked"] is False

    link = client.post(
        f"/reports/{saved['report_id']}/purchase-links",
        headers=workspace,
        json={
            "product_id": top["product"]["id"],
            "seller_name": "Pytest 공식몰",
            "url": "https://official.example.com/board-laptop",
            "is_affiliate": False,
            "price_krw": top["price"]["effective_price_krw"],
            "rank": 1,
        },
    )
    assert link.status_code == 200
    outcome = client.post(
        f"/reports/{saved['report_id']}/purchase-outcomes",
        headers=workspace,
        json={
            "product_id": top["product"]["id"],
            "checkout_review_id": acknowledged_checkout["review_id"],
            "status": "purchased",
            "final_paid_price_krw": top["price"]["effective_price_krw"],
            "satisfaction": 5,
            "reason": "구매 보드 테스트 완료",
        },
    )
    assert outcome.status_code == 200

    completed_board = client.get("/reports/decision-board", headers=workspace).json()
    assert completed_board["missing_outcome_count"] == 0
    assert completed_board["items"][0]["has_purchase_links"] is True
    assert completed_board["items"][0]["has_purchase_outcome"] is True
    assert "구매 결과 기록 완료" in completed_board["items"][0]["recommended_action"]


def test_analyze_endpoint_returns_trace_and_alerts() -> None:
    response = client.post(
        "/analyze",
        json={
            "query": "영상 편집과 게임용 데스크톱 200만원 안에서 맞춰줘",
            "category": "desktop_pc",
            "budget_krw": 2_000_000,
            "purpose": "Premiere Pro, DaVinci Resolve, QHD gaming",
            "must_haves": ["QHD 144Hz", "32GB RAM", "업그레이드 여지"],
            "channels": ["price_compare", "open_market", "official_store"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["report"]["top_recommendations"]) == 3
    assert len(payload["report"]["comparison_table"]) == 5
    assert payload["report"]["price_alerts"]
    assert payload["report"]["source_trust"]
    assert payload["report"]["trust_policy"]["fairness_rules"]
    assert payload["report"]["purchase_decision"]["next_steps"]
    assert len(payload["report"]["scenario_options"]) == 3
    assert len(payload["report"]["criteria_matches"]) == 5
    assert payload["report"]["criteria_matches"][0]["coverage_score"] > 0
    assert len(payload["report"]["stress_tests"]) == 3
    assert payload["report"]["stress_tests"][0]["impact"]
    assert len(payload["report"]["deal_windows"]) == 3
    assert payload["report"]["deal_windows"][0]["target_price_krw"] > 0
    assert payload["report"]["deal_windows"][0]["buy_trigger"]
    assert payload["report"]["deal_windows"][0]["monitoring_plan"]
    assert len(payload["report"]["evidence_packs"]) == 5
    assert payload["report"]["evidence_packs"][0]["price_evidence"]
    assert payload["report"]["evidence_packs"][0]["citation_urls"]
    assert len(payload["report"]["option_audits"]) == 5
    assert payload["report"]["option_audits"][0]["critical_items"]
    assert payload["report"]["option_audits"][0]["mismatch_risks"]
    assert payload["report"]["share_brief"]["key_reasons"]
    assert payload["report"]["share_brief"]["reviewer_questions"]
    assert "SpecPilot AI 검토 요청" in payload["report"]["share_brief"]["copy_text"]
    assert payload["report"]["execution_plan"]["checkout_steps"]
    assert payload["report"]["execution_plan"]["seller_questions"]
    assert payload["report"]["top_recommendations"][0]["price"]["effective_price_krw"] > 0
    assert payload["quality_audit"]["quality_score"] > 0
    assert payload["quality_audit"]["estimated_cost_krw"] > 0
    assert payload["trace_events"]

    trace_response = client.get(f"/traces/{payload['graph_trace_id']}")
    assert trace_response.status_code == 200
    assert trace_response.json()

    trace_runs = client.get("/ops/traces")
    assert trace_runs.status_code == 200
    assert any(item["trace_id"] == payload["graph_trace_id"] for item in trace_runs.json())

    trace_spans = client.get(f"/ops/traces/{payload['graph_trace_id']}/spans")
    assert trace_spans.status_code == 200
    span_payload = trace_spans.json()
    assert len(span_payload) == len(payload["trace_events"])
    assert span_payload[0]["sequence"] == 1
    assert span_payload[0]["step"] == payload["trace_events"][0]["step"]


def test_report_save_alert_subscription_and_metrics_flow() -> None:
    analysis = client.post(
        "/analyze",
        headers=WORKSPACE_A,
        json={
            "query": "영상 편집과 게임용 데스크톱 200만원 안에서 맞춰줘",
            "category": "desktop_pc",
            "budget_krw": 2_000_000,
            "purpose": "Premiere Pro, DaVinci Resolve, QHD gaming",
            "must_haves": ["QHD 144Hz", "32GB RAM", "업그레이드 여지"],
        },
    ).json()
    trace_id = analysis["graph_trace_id"]
    first_alert = analysis["report"]["price_alerts"][0]

    saved = client.post(
        "/reports/save",
        headers=WORKSPACE_A,
        json={
            "trace_id": trace_id,
            "title": "테스트 구매 리포트",
            "owner_label": "pytest",
            "notes": "회귀 테스트 저장",
        },
    )
    assert saved.status_code == 200
    saved_payload = saved.json()
    assert saved_payload["trace_id"] == trace_id
    assert saved_payload["workspace_id"].startswith("workspace_")

    reports = client.get("/reports", headers=WORKSPACE_A)
    assert reports.status_code == 200
    assert any(item["report_id"] == saved_payload["report_id"] for item in reports.json())

    isolated_reports = client.get("/reports", headers=WORKSPACE_B)
    assert all(item["report_id"] != saved_payload["report_id"] for item in isolated_reports.json())

    detail = client.get(f"/reports/{saved_payload['report_id']}", headers=WORKSPACE_A)
    assert detail.status_code == 200
    assert detail.json()["response"]["graph_trace_id"] == trace_id

    blocked_detail = client.get(f"/reports/{saved_payload['report_id']}", headers=WORKSPACE_B)
    assert blocked_detail.status_code == 404

    advisor_answer = client.post(
        f"/reports/{saved_payload['report_id']}/advisor-questions",
        headers=WORKSPACE_A,
        json={
            "question": "지금 결제해도 돼, 아니면 목표가까지 기다리는 게 좋아?",
            "context": "이번 주 안에는 구매 가능하지만 가격이 중요합니다.",
            "selected_product_id": analysis["report"]["final_pick_id"],
            "buyer_stage": "pre_checkout",
            "contact": "buyer@example.com",
        },
    )
    assert advisor_answer.status_code == 200
    advisor_payload = advisor_answer.json()
    assert advisor_payload["report_id"] == saved_payload["report_id"]
    assert advisor_payload["workspace_id"] == saved_payload["workspace_id"]
    assert advisor_payload["question"].startswith("지금 결제")
    assert advisor_payload["selected_product_id"] == analysis["report"]["final_pick_id"]
    assert advisor_payload["selected_model_name"]
    assert advisor_payload["answer"]
    assert advisor_payload["grounded_evidence"]
    assert advisor_payload["next_actions"]
    assert advisor_payload["contact_masked"] == "bu***@example.com"
    assert advisor_payload["status"] in {"ok", "warning", "blocker"}

    report_advisor_answers = client.get(
        f"/reports/{saved_payload['report_id']}/advisor-questions",
        headers=WORKSPACE_A,
    )
    assert report_advisor_answers.status_code == 200
    assert any(
        item["answer_id"] == advisor_payload["answer_id"]
        for item in report_advisor_answers.json()
    )

    workspace_advisor_answers = client.get("/advisor-questions", headers=WORKSPACE_A)
    assert any(
        item["answer_id"] == advisor_payload["answer_id"]
        for item in workspace_advisor_answers.json()
    )

    isolated_advisor_answer = client.post(
        f"/reports/{saved_payload['report_id']}/advisor-questions",
        headers=WORKSPACE_B,
        json={"question": "다른 워크스페이스에서 볼 수 있나?"},
    )
    assert isolated_advisor_answer.status_code == 404
    isolated_advisor_answers = client.get("/advisor-questions", headers=WORKSPACE_B)
    assert all(
        item["answer_id"] != advisor_payload["answer_id"]
        for item in isolated_advisor_answers.json()
    )

    top_recommendation = analysis["report"]["top_recommendations"][0]
    checkout_review = client.post(
        f"/reports/{saved_payload['report_id']}/checkout-review",
        headers=WORKSPACE_A,
        json={
            "product_id": top_recommendation["product"]["id"],
            "confirmed_price_krw": top_recommendation["price"]["effective_price_krw"],
            "seller_answers": {},
            "notes": "pytest 결제 직전 검수",
        },
    )
    assert checkout_review.status_code == 200
    checkout_payload = checkout_review.json()
    assert checkout_payload["report_id"] == saved_payload["report_id"]
    assert checkout_payload["trace_id"] == trace_id
    assert checkout_payload["workspace_id"] == saved_payload["workspace_id"]
    assert checkout_payload["product_id"] == top_recommendation["product"]["id"]
    assert checkout_payload["items"]
    assert checkout_payload["checkout_blocked"] is True
    assert checkout_payload["missing_acknowledgements"]

    acknowledged_checkout = client.post(
        f"/reports/{saved_payload['report_id']}/checkout-review",
        headers=WORKSPACE_A,
        json={
            "product_id": top_recommendation["product"]["id"],
            "confirmed_price_krw": top_recommendation["price"]["effective_price_krw"],
            "acknowledged_risks": checkout_payload["missing_acknowledgements"],
            "seller_answers": {
                question: "판매자 확인 완료"
                for question in checkout_payload["seller_questions"]
            },
            "notes": "pytest 리스크 승인 후 검수",
        },
    )
    assert acknowledged_checkout.status_code == 200
    acknowledged_payload = acknowledged_checkout.json()
    assert acknowledged_payload["checkout_blocked"] is False
    assert acknowledged_payload["missing_acknowledgements"] == []
    assert acknowledged_payload["readiness_score"] >= checkout_payload["readiness_score"]

    checkout_reviews = client.get(
        f"/reports/{saved_payload['report_id']}/checkout-reviews",
        headers=WORKSPACE_A,
    )
    assert checkout_reviews.status_code == 200
    assert len(checkout_reviews.json()) >= 2

    all_checkout_reviews = client.get("/checkout-reviews", headers=WORKSPACE_A)
    assert any(
        item["review_id"] == acknowledged_payload["review_id"]
        for item in all_checkout_reviews.json()
    )

    purchase_outcome = client.post(
        f"/reports/{saved_payload['report_id']}/purchase-outcomes",
        headers=WORKSPACE_A,
        json={
            "product_id": top_recommendation["product"]["id"],
            "checkout_review_id": acknowledged_payload["review_id"],
            "status": "purchased",
            "final_paid_price_krw": top_recommendation["price"]["effective_price_krw"] + 10_000,
            "source_channel": "checkout_review",
            "reason": "pytest 실제 구매 완료",
            "satisfaction": 5,
            "order_reference": "ORDER-2026-000123",
            "notes": "pytest 구매 결과",
        },
    )
    assert purchase_outcome.status_code == 200
    outcome_payload = purchase_outcome.json()
    assert outcome_payload["report_id"] == saved_payload["report_id"]
    assert outcome_payload["trace_id"] == trace_id
    assert outcome_payload["workspace_id"] == saved_payload["workspace_id"]
    assert outcome_payload["product_id"] == top_recommendation["product"]["id"]
    assert outcome_payload["checkout_review_id"] == acknowledged_payload["review_id"]
    assert outcome_payload["status"] == "purchased"
    assert (
        outcome_payload["expected_price_krw"]
        == top_recommendation["price"]["effective_price_krw"]
    )
    assert outcome_payload["price_delta_krw"] == 10_000
    assert outcome_payload["conversion_value_krw"] == outcome_payload["final_paid_price_krw"]
    assert outcome_payload["order_reference_masked"] == "ORD***123"
    assert "실제 구매" in outcome_payload["learning_signal"]

    delayed_outcome = client.post(
        f"/reports/{saved_payload['report_id']}/purchase-outcomes",
        headers=WORKSPACE_A,
        json={
            "product_id": top_recommendation["product"]["id"],
            "status": "delayed",
            "source_channel": "follow_up",
            "reason": "다음 할인까지 대기",
            "satisfaction": 4,
        },
    )
    assert delayed_outcome.status_code == 200
    assert delayed_outcome.json()["status"] == "delayed"
    assert delayed_outcome.json()["conversion_value_krw"] == 0

    report_outcomes = client.get(
        f"/reports/{saved_payload['report_id']}/purchase-outcomes",
        headers=WORKSPACE_A,
    )
    assert report_outcomes.status_code == 200
    assert len(report_outcomes.json()) >= 2

    all_purchase_outcomes = client.get("/purchase-outcomes", headers=WORKSPACE_A)
    assert any(
        item["outcome_id"] == outcome_payload["outcome_id"]
        for item in all_purchase_outcomes.json()
    )

    isolated_checkout = client.post(
        f"/reports/{saved_payload['report_id']}/checkout-review",
        headers=WORKSPACE_B,
        json={"product_id": top_recommendation["product"]["id"]},
    )
    assert isolated_checkout.status_code == 404

    invalid_checkout = client.post(
        f"/reports/{saved_payload['report_id']}/checkout-review",
        headers=WORKSPACE_A,
        json={"product_id": "unknown_product"},
    )
    assert invalid_checkout.status_code == 404

    isolated_outcome = client.post(
        f"/reports/{saved_payload['report_id']}/purchase-outcomes",
        headers=WORKSPACE_B,
        json={"product_id": top_recommendation["product"]["id"]},
    )
    assert isolated_outcome.status_code == 404

    invalid_outcome = client.post(
        f"/reports/{saved_payload['report_id']}/purchase-outcomes",
        headers=WORKSPACE_A,
        json={"product_id": "unknown_product", "status": "purchased"},
    )
    assert invalid_outcome.status_code == 404

    invalid_checkout_outcome = client.post(
        f"/reports/{saved_payload['report_id']}/purchase-outcomes",
        headers=WORKSPACE_A,
        json={
            "product_id": top_recommendation["product"]["id"],
            "checkout_review_id": "checkout_missing",
            "status": "purchased",
        },
    )
    assert invalid_checkout_outcome.status_code == 404

    affiliate_link = client.post(
        f"/reports/{saved_payload['report_id']}/purchase-links",
        headers=WORKSPACE_A,
        json={
            "product_id": top_recommendation["product"]["id"],
            "seller_name": "Pytest 제휴몰",
            "url": "https://shop.example.com/specpilot-top",
            "is_affiliate": True,
            "affiliate_network": "pytest-partner",
            "price_krw": top_recommendation["price"]["effective_price_krw"],
            "shipping_fee_krw": 3_000,
            "coupon_krw": 5_000,
            "rank": 1,
            "notes": "pytest 제휴 링크",
        },
    )
    assert affiliate_link.status_code == 200
    affiliate_payload = affiliate_link.json()
    assert affiliate_payload["is_affiliate"] is True
    assert affiliate_payload["click_path"].startswith("/buy/plink_")
    assert "제휴 링크" in affiliate_payload["disclosure"]

    governance_after_affiliate = client.get(
        f"/reports/{saved_payload['report_id']}/purchase-link-governance",
        headers=WORKSPACE_A,
    )
    assert governance_after_affiliate.status_code == 200
    assert governance_after_affiliate.json()["status"] == "blocker"
    assert governance_after_affiliate.json()["required_actions"]

    non_affiliate_link = client.post(
        f"/reports/{saved_payload['report_id']}/purchase-links",
        headers=WORKSPACE_A,
        json={
            "product_id": top_recommendation["product"]["id"],
            "seller_name": "Pytest 공식몰",
            "url": "https://official.example.com/specpilot-top",
            "is_affiliate": False,
            "price_krw": top_recommendation["price"]["effective_price_krw"] + 8_000,
            "rank": 2,
            "notes": "pytest 비제휴 대안",
        },
    )
    assert non_affiliate_link.status_code == 200
    assert non_affiliate_link.json()["is_affiliate"] is False

    purchase_links = client.get(
        f"/reports/{saved_payload['report_id']}/purchase-links",
        headers=WORKSPACE_A,
    )
    assert purchase_links.status_code == 200
    assert len(purchase_links.json()) >= 2
    assert {item["is_affiliate"] for item in purchase_links.json()} == {True, False}

    governance_after_alternative = client.get(
        f"/reports/{saved_payload['report_id']}/purchase-link-governance",
        headers=WORKSPACE_A,
    )
    assert governance_after_alternative.status_code == 200
    assert governance_after_alternative.json()["status"] in {"ok", "warning"}
    assert governance_after_alternative.json()["non_affiliate_link_count"] >= 1

    invalid_purchase_link = client.post(
        f"/reports/{saved_payload['report_id']}/purchase-links",
        headers=WORKSPACE_A,
        json={
            "product_id": top_recommendation["product"]["id"],
            "seller_name": "internal",
            "url": "http://127.0.0.1/private",
        },
    )
    assert invalid_purchase_link.status_code == 400

    isolated_purchase_link = client.post(
        f"/reports/{saved_payload['report_id']}/purchase-links",
        headers=WORKSPACE_B,
        json={
            "product_id": top_recommendation["product"]["id"],
            "seller_name": "other workspace",
            "url": "https://other.example.com/specpilot",
        },
    )
    assert isolated_purchase_link.status_code == 404

    share = client.post(
        f"/reports/{saved_payload['report_id']}/share",
        headers=WORKSPACE_A,
    )
    assert share.status_code == 200
    share_payload = share.json()
    assert share_payload["is_public"] is True
    assert share_payload["share_token"].startswith("share_")
    assert share_payload["public_path"].startswith("/r/share_")

    share_assets = client.get(
        f"/reports/{saved_payload['report_id']}/share-assets",
        headers=WORKSPACE_A,
    )
    assert share_assets.status_code == 200
    share_assets_payload = share_assets.json()
    assert share_assets_payload["asset_version"] == "specpilot.share_assets.v1"
    assert share_assets_payload["share_token"] == share_payload["share_token"]
    assert share_assets_payload["public_path"] == share_payload["public_path"]
    assert top_recommendation["product"]["model_name"] in share_assets_payload["headline"]
    assert share_assets_payload["og_title"]
    assert share_assets_payload["og_description"]
    assert len(share_assets_payload["visual_card_text"]) >= 4
    assert "#SpecPilotAI" in share_assets_payload["hashtags"]
    assert share_assets_payload["reviewer_questions"]
    assert {item["channel"] for item in share_assets_payload["variants"]} == {
        "blog",
        "community",
        "kakao",
    }
    assert all(
        share_payload["public_path"] in item["copy_text"]
        for item in share_assets_payload["variants"]
    )
    assert share_assets_payload["next_actions"]

    blocked_share = client.post(
        f"/reports/{saved_payload['report_id']}/share",
        headers=WORKSPACE_B,
    )
    assert blocked_share.status_code == 404

    public_report = client.get(f"/public/reports/{share_payload['share_token']}")
    assert public_report.status_code == 200
    assert public_report.json()["response"]["graph_trace_id"] == trace_id
    assert public_report.json()["share_views"] == 1
    assert len(public_report.json()["purchase_links"]) >= 2
    assert any(item["is_affiliate"] for item in public_report.json()["purchase_links"])
    conversion_cta = public_report.json()["conversion_cta"]
    assert conversion_cta["primary_path"].startswith("/?source=public-report")
    assert conversion_cta["secondary_path"].startswith("/join?source=public-report")
    assert conversion_cta["report_ref"]
    assert "추천 코드" in " ".join(conversion_cta["proof_points"])

    public_page = client.get(f"/r/{share_payload['share_token']}")
    assert public_page.status_code == 200
    assert "테스트 구매 리포트" in public_page.text
    assert "Public report conversion" in public_page.text
    assert "내 조건으로 분석 시작" in public_page.text
    assert "공개 베타 대기열 등록" in public_page.text
    assert "공유용 검토 브리프" in public_page.text
    assert "후보 비교표" in public_page.text
    assert "결제 전 체크리스트" in public_page.text
    assert "대안 시나리오" in public_page.text
    assert "구매 타이밍 윈도우" in public_page.text
    assert "예산/조건 스트레스 테스트" in public_page.text
    assert "후보별 근거 팩" in public_page.text
    assert "옵션/사양 검수표" in public_page.text
    assert "조건 충족 매트릭스" in public_page.text
    assert "구매 실행 패키지" in public_page.text
    assert "판매자 확인 질문" in public_page.text
    assert "구매 링크" in public_page.text
    assert "Pytest 제휴몰" in public_page.text
    assert "비제휴" in public_page.text

    click = client.get(
        affiliate_payload["click_path"],
        headers={"referer": f"http://testserver/r/{share_payload['share_token']}"},
        follow_redirects=False,
    )
    assert click.status_code == 302
    assert click.headers["location"] == "https://shop.example.com/specpilot-top"

    report_after_share = client.get(
        f"/reports/{saved_payload['report_id']}",
        headers=WORKSPACE_A,
    )
    assert report_after_share.json()["share_token"] == share_payload["share_token"]
    assert report_after_share.json()["share_views"] >= 2

    metrics_after_share = client.get("/ops/metrics", headers=WORKSPACE_A).json()
    assert metrics_after_share["shared_reports"] >= 1
    assert metrics_after_share["public_share_views"] >= 2
    assert metrics_after_share["report_advisor_answers"] >= 1
    assert metrics_after_share["checkout_reviews"] >= 2
    assert metrics_after_share["checkout_blocked_reviews"] >= 1
    assert metrics_after_share["purchase_outcomes"] >= 2
    assert metrics_after_share["completed_purchase_outcomes"] >= 1
    assert metrics_after_share["delayed_purchase_outcomes"] >= 1
    assert metrics_after_share["purchase_links"] >= 2
    assert metrics_after_share["affiliate_purchase_links"] >= 1
    assert metrics_after_share["purchase_link_clicks"] >= 1
    assert metrics_after_share["purchase_conversion_rate"] > 0
    assert metrics_after_share["average_final_price_delta_krw"] >= 0
    assert (
        metrics_after_share["purchase_outcome_value_krw"]
        >= outcome_payload["final_paid_price_krw"]
    )

    learning = client.get("/ops/learning-insights", headers=WORKSPACE_A)
    assert learning.status_code == 200
    learning_payload = learning.json()
    assert learning_payload["workspace_id"] == saved_payload["workspace_id"]
    assert learning_payload["insight_count"] >= 1
    assert learning_payload["summary"]
    assert learning_payload["top_actions"]
    top_insight = next(
        item
        for item in learning_payload["insights"]
        if item["product_id"] == top_recommendation["product"]["id"]
    )
    assert top_insight["outcome_count"] >= 2
    assert top_insight["purchase_count"] >= 1
    assert top_insight["delayed_count"] >= 1
    assert top_insight["checkout_review_count"] >= 2
    assert top_insight["conversion_rate"] > 0
    assert top_insight["recommended_action"]

    isolated_learning = client.get("/ops/learning-insights", headers=WORKSPACE_B)
    assert isolated_learning.status_code == 200
    assert all(
        item["product_id"] != top_recommendation["product"]["id"]
        for item in isolated_learning.json()["insights"]
    )

    completion_dry_run = client.post(
        "/reports/completion-batches",
        headers=WORKSPACE_A,
        json={
            "report_ids": [saved_payload["report_id"]],
            "channel": "email",
            "target": "ops@example.com",
            "dry_run": True,
            "note": "pytest 완료 리포트 리허설",
        },
    )
    assert completion_dry_run.status_code == 200
    assert completion_dry_run.json()["selected_count"] == 1
    assert completion_dry_run.json()["dry_run"] is True
    assert completion_dry_run.json()["deliveries"][0]["status"] == "dry_run"

    completion_batch = client.post(
        "/reports/completion-batches",
        headers=WORKSPACE_A,
        json={
            "report_ids": [saved_payload["report_id"]],
            "channel": "email",
            "target": "ops@example.com",
            "note": "pytest 완료 리포트 발송",
        },
    )
    assert completion_batch.status_code == 200
    completion_payload = completion_batch.json()
    assert completion_payload["selected_count"] == 1
    assert completion_payload["sent_count"] == 1
    assert completion_payload["status"] == "sent"
    assert completion_payload["deliveries"][0]["report_id"] == saved_payload["report_id"]
    assert completion_payload["deliveries"][0]["target_masked"] == "op***@example.com"

    completion_batches = client.get("/reports/completion-batches", headers=WORKSPACE_A)
    assert completion_batches.status_code == 200
    assert any(
        item["batch_id"] == completion_payload["batch_id"]
        and item["deliveries"][0]["status"] == "sent"
        for item in completion_batches.json()
    )

    completion_template = client.post(
        "/reports/completion-templates",
        headers=WORKSPACE_A,
        json={
            "name": "pytest 완료 리포트",
            "channel": "email",
            "subject": "[SpecPilot] {title}",
            "body": "{title}\n추천 1순위: {top_model_name}\n공개 리포트: {public_path}",
            "enabled": True,
        },
    )
    assert completion_template.status_code == 200
    template_payload = completion_template.json()
    assert template_payload["name"] == "pytest 완료 리포트"
    assert template_payload["subject"] == "[SpecPilot] {title}"

    completion_templates = client.get("/reports/completion-templates", headers=WORKSPACE_A)
    assert completion_templates.status_code == 200
    assert any(
        item["template_id"] == template_payload["template_id"]
        for item in completion_templates.json()
    )

    completion_group = client.post(
        "/reports/completion-recipient-groups",
        headers=WORKSPACE_A,
        json={
            "name": "pytest 운영 수신자",
            "channel": "email",
            "recipients": ["ops@example.com", "blocked@example.com", "ops@example.com"],
            "unsubscribed_recipients": ["blocked@example.com"],
            "unsubscribe_policy": "exclude_unsubscribed",
            "enabled": True,
            "description": "pytest 수신자 그룹",
        },
    )
    assert completion_group.status_code == 200
    group_payload = completion_group.json()
    assert group_payload["recipient_count"] == 2
    assert group_payload["unsubscribed_count"] == 1

    completion_groups = client.get(
        "/reports/completion-recipient-groups",
        headers=WORKSPACE_A,
    )
    assert completion_groups.status_code == 200
    assert any(item["group_id"] == group_payload["group_id"] for item in completion_groups.json())

    completion_preview = client.post(
        "/reports/completion-preview",
        headers=WORKSPACE_A,
        json={
            "report_id": saved_payload["report_id"],
            "template_id": template_payload["template_id"],
            "recipient_group_id": group_payload["group_id"],
            "respect_unsubscribe": True,
        },
    )
    assert completion_preview.status_code == 200
    preview_payload = completion_preview.json()
    assert preview_payload["subject"] == "[SpecPilot] 테스트 구매 리포트"
    assert preview_payload["target_count"] == 1
    assert preview_payload["excluded_count"] == 1
    assert preview_payload["targets_masked"] == ["op***@example.com"]
    assert preview_payload["excluded_targets_masked"] == ["bl***@example.com"]

    templated_batch = client.post(
        "/reports/completion-batches",
        headers=WORKSPACE_A,
        json={
            "report_ids": [saved_payload["report_id"]],
            "template_id": template_payload["template_id"],
            "recipient_group_id": group_payload["group_id"],
            "respect_unsubscribe": True,
            "note": "pytest 템플릿 그룹 발송",
        },
    )
    assert templated_batch.status_code == 200
    templated_payload = templated_batch.json()
    assert templated_payload["template_id"] == template_payload["template_id"]
    assert templated_payload["recipient_group_id"] == group_payload["group_id"]
    assert templated_payload["target_count"] == 2
    assert templated_payload["sent_count"] == 1
    assert any(delivery["status"] == "skipped" for delivery in templated_payload["deliveries"])
    assert any(
        delivery["subject"] == "[SpecPilot] 테스트 구매 리포트"
        for delivery in templated_payload["deliveries"]
    )
    sent_delivery = next(
        delivery
        for delivery in templated_payload["deliveries"]
        if delivery["status"] == "sent"
    )
    assert sent_delivery["tracking_token"].startswith("trk_")
    assert sent_delivery["tracking_pixel_path"].endswith(".png")
    assert sent_delivery["tracking_click_path"].startswith("/t/c/")
    assert "tracking_pixel=" in sent_delivery["provider_message"]

    opened = client.post(
        f"/reports/completion-deliveries/{sent_delivery['delivery_id']}/engagement",
        headers=WORKSPACE_A,
        json={"event_type": "opened", "metadata": {"user_agent": "pytest"}},
    )
    assert opened.status_code == 200
    assert opened.json()["event_type"] == "open"
    assert opened.json()["target_masked"] == "op***@example.com"

    clicked = client.post(
        f"/reports/completion-deliveries/{sent_delivery['delivery_id']}/engagement",
        headers=WORKSPACE_A,
        json={"event_type": "clicked", "metadata": {"href": "/r/share_test"}},
    )
    assert clicked.status_code == 200
    assert clicked.json()["event_type"] == "click"

    pixel = client.get(
        sent_delivery["tracking_pixel_path"],
        headers={"User-Agent": "pytest-pixel"},
    )
    assert pixel.status_code == 200
    assert pixel.headers["content-type"] == "image/png"
    assert pixel.headers["cache-control"] == "no-store, max-age=0"

    redirect = client.get(
        f"{sent_delivery['tracking_click_path']}?to=/r/share_test",
        follow_redirects=False,
        headers={"User-Agent": "pytest-click"},
    )
    assert redirect.status_code == 302
    assert redirect.headers["location"] == "/r/share_test"

    unsafe_redirect = client.get(
        f"{sent_delivery['tracking_click_path']}?to=https://evil.example",
        follow_redirects=False,
    )
    assert unsafe_redirect.status_code == 302
    assert unsafe_redirect.headers["location"] == "/"

    rejected_webhook = client.post(
        "/reports/completion-deliveries/provider-webhooks",
        json={
            "tracking_token": sent_delivery["tracking_token"],
            "provider_name": "pytest-mailer",
            "event_type": "bounced",
        },
    )
    assert rejected_webhook.status_code == 401

    bounced_webhook = client.post(
        "/reports/completion-deliveries/provider-webhooks",
        headers={"X-SpecPilot-Webhook-Secret": "specpilot-webhook-secret"},
        json={
            "tracking_token": sent_delivery["tracking_token"],
            "provider_name": "pytest-mailer",
            "event_type": "hard_bounce",
            "provider_message": "mailbox unavailable",
            "metadata": {"smtp_code": "550"},
        },
    )
    assert bounced_webhook.status_code == 200
    assert bounced_webhook.json()["event_type"] == "bounced"
    assert bounced_webhook.json()["delivery_status"] == "failed"

    provider_events = client.get("/reports/completion-provider-events", headers=WORKSPACE_A)
    assert provider_events.status_code == 200
    assert any(
        item["provider_event_id"] == bounced_webhook.json()["provider_event_id"]
        for item in provider_events.json()
    )
    isolated_provider_events = client.get(
        "/reports/completion-provider-events",
        headers=WORKSPACE_B,
    )
    assert all(
        item["provider_event_id"] != bounced_webhook.json()["provider_event_id"]
        for item in isolated_provider_events.json()
    )

    completion_engagement = client.get("/reports/completion-engagement", headers=WORKSPACE_A)
    assert completion_engagement.status_code == 200
    assert {item["event_type"] for item in completion_engagement.json()} >= {"open", "click"}

    completion_batches_with_engagement = client.get(
        "/reports/completion-batches",
        headers=WORKSPACE_A,
    )
    sent_delivery_after_engagement = next(
        delivery
        for batch_item in completion_batches_with_engagement.json()
        if batch_item["batch_id"] == templated_payload["batch_id"]
        for delivery in batch_item["deliveries"]
        if delivery["delivery_id"] == sent_delivery["delivery_id"]
    )
    assert sent_delivery_after_engagement["open_count"] == 2
    assert sent_delivery_after_engagement["click_count"] == 3
    assert sent_delivery_after_engagement["engagement_count"] == 5
    assert sent_delivery_after_engagement["status"] == "failed"
    assert "provider_webhook=pytest-mailer:bounced" in sent_delivery_after_engagement[
        "provider_message"
    ]

    metrics_after_completion = client.get("/ops/metrics", headers=WORKSPACE_A).json()
    assert metrics_after_completion["completion_report_batches"] >= 2
    assert metrics_after_completion["completion_report_deliveries"] >= 3
    assert metrics_after_completion["completion_delivery_opens"] >= 2
    assert metrics_after_completion["completion_delivery_clicks"] >= 3
    assert metrics_after_completion["completion_delivery_bounces"] >= 1

    isolated_completion_batch = client.post(
        "/reports/completion-batches",
        headers=WORKSPACE_B,
        json={"report_ids": [saved_payload["report_id"]], "target": "ops@example.com"},
    )
    assert isolated_completion_batch.status_code == 200
    assert isolated_completion_batch.json()["selected_count"] == 0

    isolated_completion_templates = client.get(
        "/reports/completion-templates",
        headers=WORKSPACE_B,
    )
    assert all(
        item["template_id"] != template_payload["template_id"]
        for item in isolated_completion_templates.json()
    )

    isolated_completion_groups = client.get(
        "/reports/completion-recipient-groups",
        headers=WORKSPACE_B,
    )
    assert all(
        item["group_id"] != group_payload["group_id"]
        for item in isolated_completion_groups.json()
    )

    blocked_completion_preview = client.post(
        "/reports/completion-preview",
        headers=WORKSPACE_B,
        json={
            "report_id": saved_payload["report_id"],
            "template_id": template_payload["template_id"],
            "recipient_group_id": group_payload["group_id"],
        },
    )
    assert blocked_completion_preview.status_code == 404

    blocked_engagement = client.post(
        f"/reports/completion-deliveries/{sent_delivery['delivery_id']}/engagement",
        headers=WORKSPACE_B,
        json={"event_type": "open"},
    )
    assert blocked_engagement.status_code == 404

    missing_pixel = client.get("/t/o/trk_missing.png")
    assert missing_pixel.status_code == 200
    assert missing_pixel.headers["content-type"] == "image/png"

    revoked_share = client.delete(
        f"/reports/{saved_payload['report_id']}/share",
        headers=WORKSPACE_A,
    )
    assert revoked_share.status_code == 200
    assert revoked_share.json()["is_public"] is False
    assert client.get(f"/public/reports/{share_payload['share_token']}").status_code == 404

    subscribed = client.post(
        "/alerts/subscribe",
        headers=WORKSPACE_A,
        json={
            "trace_id": trace_id,
            "product_id": first_alert["product_id"],
            "target_price_krw": first_alert["target_price_krw"],
            "channels": ["email"],
            "contact": "buyer@example.com",
            "owner_label": "pytest",
        },
    )
    assert subscribed.status_code == 200
    assert subscribed.json()["status"] == "active"
    assert subscribed.json()["workspace_id"] == saved_payload["workspace_id"]
    assert subscribed.json()["contact_masked"] == "bu***@example.com"
    assert "contact" not in subscribed.json()
    subscription_id = subscribed.json()["subscription_id"]

    evaluated = client.post(
        "/alerts/evaluate",
        headers=WORKSPACE_A,
        json={
            "price_overrides_krw": {
                first_alert["product_id"]: first_alert["target_price_krw"] - 1
            },
            "dry_run": False,
        },
    )
    assert evaluated.status_code == 200
    evaluated_payload = evaluated.json()
    assert evaluated_payload["triggered_count"] >= 1
    event_id = next(
        event["event_id"]
        for event in evaluated_payload["events"]
        if event["subscription_id"] == subscription_id
    )
    assert any(
        event["subscription_id"] == subscription_id
        and event["delivery_status"] == "queued"
        for event in evaluated_payload["events"]
    )

    events = client.get("/alerts/events", headers=WORKSPACE_A)
    assert events.status_code == 200
    assert any(event["subscription_id"] == subscription_id for event in events.json())

    channel = client.post(
        "/alerts/channels",
        headers=WORKSPACE_A,
        json={
            "channel": "email",
            "display_name": "pytest 이메일 outbox",
            "target": "ops@example.com",
            "enabled": True,
            "retry_limit": 2,
        },
    )
    assert channel.status_code == 200
    assert channel.json()["channel"] == "email"
    assert channel.json()["target_masked"] == "op***@example.com"

    channels = client.get("/alerts/channels", headers=WORKSPACE_A)
    assert any(item["channel"] == "email" for item in channels.json())

    isolated_channels = client.get("/alerts/channels", headers=WORKSPACE_B)
    assert all(item["channel"] != "email" for item in isolated_channels.json())

    dispatched = client.post(
        "/alerts/dispatch",
        headers=WORKSPACE_A,
        json={"event_ids": [event_id], "dry_run": False, "limit": 20},
    )
    assert dispatched.status_code == 200
    dispatch_payload = dispatched.json()
    assert dispatch_payload["selected_count"] >= 1
    assert dispatch_payload["sent_count"] >= 1
    assert any(
        attempt["subscription_id"] == subscription_id
        and attempt["delivery_status"] == "sent"
        and attempt["channel"] == "email"
        for attempt in dispatch_payload["attempts"]
    )

    deliveries = client.get("/alerts/deliveries", headers=WORKSPACE_A)
    assert deliveries.status_code == 200
    assert any(
        attempt["subscription_id"] == subscription_id
        and attempt["delivery_status"] == "sent"
        for attempt in deliveries.json()
    )

    isolated_deliveries = client.get("/alerts/deliveries", headers=WORKSPACE_B)
    assert all(
        attempt["subscription_id"] != subscription_id
        for attempt in isolated_deliveries.json()
    )

    isolated_events = client.get("/alerts/events", headers=WORKSPACE_B)
    assert all(event["subscription_id"] != subscription_id for event in isolated_events.json())

    blocked_trace = client.get(f"/traces/{trace_id}", headers=WORKSPACE_B)
    assert blocked_trace.status_code == 404

    metrics = client.get("/ops/metrics", headers=WORKSPACE_A)
    assert metrics.status_code == 200
    payload = metrics.json()
    assert payload["analysis_runs"] >= 1
    assert payload["saved_reports"] >= 1
    assert payload["alert_subscriptions"] >= 1
    assert payload["alert_events"] >= 1
    assert payload["triggered_alerts"] >= 1
    assert payload["alert_channels"] >= 1
    assert payload["alert_delivery_attempts"] >= 1
    assert payload["sent_alert_deliveries"] >= 1
    assert payload["trace_spans"] >= len(analysis["trace_events"])
    assert payload["average_quality_score"] > 0
    assert payload["estimated_cost_krw"] > 0

    data_governance = client.get("/ops/data-governance", headers=WORKSPACE_A)
    assert data_governance.status_code == 200
    governance_payload = data_governance.json()
    assert governance_payload["workspace_id"] == saved_payload["workspace_id"]
    assert governance_payload["total_records"] > 0
    assert governance_payload["raw_contact_surfaces"] >= 1
    assert governance_payload["status"] == "blocker"
    assert any(
        item["table_name"] == "alert_subscriptions"
        and item["status"] == "blocker"
        for item in governance_payload["inventory"]
    )

    quality = client.get("/ops/quality", headers=WORKSPACE_A)
    assert quality.status_code == 200
    quality_payload = quality.json()
    assert quality_payload["audit_count"] >= 1
    assert quality_payload["average_quality_score"] > 0
    assert quality_payload["total_estimated_cost_krw"] > 0
    assert any(item["trace_id"] == trace_id for item in quality_payload["recent_audits"])

    regression = client.get("/ops/regression", headers=WORKSPACE_A)
    assert regression.status_code == 200
    regression_payload = regression.json()
    assert regression_payload["workspace_id"] == saved_payload["workspace_id"]
    assert regression_payload["recent"]["run_count"] >= 1
    assert regression_payload["recent"]["average_quality_score"] > 0
    assert regression_payload["status"] in {"ok", "warning", "blocker"}
    assert regression_payload["next_actions"]

    trace_runs = client.get("/ops/traces", headers=WORKSPACE_A)
    assert trace_runs.status_code == 200
    assert any(
        item["trace_id"] == trace_id and item["span_count"] == len(analysis["trace_events"])
        for item in trace_runs.json()
    )

    trace_spans = client.get(f"/ops/traces/{trace_id}/spans", headers=WORKSPACE_A)
    assert trace_spans.status_code == 200
    assert [item["sequence"] for item in trace_spans.json()] == list(
        range(1, len(analysis["trace_events"]) + 1)
    )

    blocked_trace_spans = client.get(f"/ops/traces/{trace_id}/spans", headers=WORKSPACE_B)
    assert blocked_trace_spans.status_code == 404

    observability_export = client.post(
        "/ops/observability/exports",
        headers=WORKSPACE_A,
        json={
            "trace_id": trace_id,
            "destination": "opentelemetry",
            "include_payload": True,
        },
    )
    assert observability_export.status_code == 200
    observability_payload = observability_export.json()
    assert observability_payload["trace_id"] == trace_id
    assert observability_payload["workspace_id"] == saved_payload["workspace_id"]
    assert observability_payload["status"] == "queued"
    assert observability_payload["provider_message"]
    assert observability_payload["retry_count"] == 0
    assert observability_payload["dispatched_at"] is None
    assert observability_payload["span_count"] == len(analysis["trace_events"])
    assert observability_payload["quality_score"] > 0
    assert observability_payload["payload"]["schema_version"] == "specpilot.observability.v1"
    assert observability_payload["payload"]["quality"]["score"] > 0
    assert len(observability_payload["payload"]["spans"]) == len(analysis["trace_events"])

    observability_exports = client.get(
        "/ops/observability/exports",
        headers=WORKSPACE_A,
    )
    assert observability_exports.status_code == 200
    assert any(
        item["export_id"] == observability_payload["export_id"]
        for item in observability_exports.json()
    )

    observability_dry_run = client.post(
        "/ops/observability/dispatch",
        headers=WORKSPACE_A,
        json={
            "export_ids": [observability_payload["export_id"]],
            "dry_run": True,
        },
    )
    assert observability_dry_run.status_code == 200
    assert observability_dry_run.json()["selected_count"] == 1
    assert observability_dry_run.json()["dry_run"] is True
    assert observability_dry_run.json()["exports"][0]["status"] == "dry_run"

    observability_dispatch = client.post(
        "/ops/observability/dispatch",
        headers=WORKSPACE_A,
        json={"export_ids": [observability_payload["export_id"]]},
    )
    assert observability_dispatch.status_code == 200
    dispatch_payload = observability_dispatch.json()
    assert dispatch_payload["selected_count"] == 1
    assert dispatch_payload["sent_count"] == 1
    assert dispatch_payload["failed_count"] == 0
    assert dispatch_payload["exports"][0]["status"] == "sent"
    assert dispatch_payload["exports"][0]["retry_count"] == 1
    assert dispatch_payload["exports"][0]["dispatched_at"] is not None
    assert "opentelemetry exporter outbox" in dispatch_payload["exports"][0]["provider_message"]

    observability_exports_after_dispatch = client.get(
        "/ops/observability/exports",
        headers=WORKSPACE_A,
    ).json()
    assert any(
        item["export_id"] == observability_payload["export_id"] and item["status"] == "sent"
        for item in observability_exports_after_dispatch
    )

    isolated_observability_exports = client.get(
        "/ops/observability/exports",
        headers=WORKSPACE_B,
    )
    assert all(
        item["export_id"] != observability_payload["export_id"]
        for item in isolated_observability_exports.json()
    )

    isolated_observability_dispatch = client.post(
        "/ops/observability/dispatch",
        headers=WORKSPACE_B,
        json={"export_ids": [observability_payload["export_id"]]},
    )
    assert isolated_observability_dispatch.status_code == 200
    assert isolated_observability_dispatch.json()["selected_count"] == 0

    blocked_observability_export = client.post(
        "/ops/observability/exports",
        headers=WORKSPACE_B,
        json={"trace_id": trace_id, "destination": "opentelemetry"},
    )
    assert blocked_observability_export.status_code == 404

    metadata_only_export = client.post(
        "/ops/observability/exports",
        headers=WORKSPACE_A,
        json={
            "trace_id": trace_id,
            "destination": "langsmith",
            "include_payload": False,
        },
    )
    assert metadata_only_export.status_code == 200
    metadata_only_dispatch = client.post(
        "/ops/observability/dispatch",
        headers=WORKSPACE_A,
        json={"export_ids": [metadata_only_export.json()["export_id"]]},
    )
    assert metadata_only_dispatch.status_code == 200
    assert metadata_only_dispatch.json()["failed_count"] == 1
    assert metadata_only_dispatch.json()["exports"][0]["status"] == "failed"
    assert "payload" in metadata_only_dispatch.json()["exports"][0]["provider_message"]

    feedback = client.post(
        "/feedback",
        headers=WORKSPACE_A,
        json={
            "trace_id": trace_id,
            "rating": 5,
            "purchase_intent": True,
            "selected_product_id": first_alert["product_id"],
            "reason": "추천 근거와 가격 알림이 충분합니다.",
            "improvement_requests": ["실제 판매 링크 연동"],
            "contact": "buyer@example.com",
        },
    )
    assert feedback.status_code == 200
    feedback_payload = feedback.json()
    assert feedback_payload["rating"] == 5
    assert feedback_payload["contact_masked"] == "bu***@example.com"

    feedback_list = client.get("/feedback", headers=WORKSPACE_A)
    assert any(
        item["feedback_id"] == feedback_payload["feedback_id"]
        for item in feedback_list.json()
    )

    isolated_feedback = client.get("/feedback", headers=WORKSPACE_B)
    assert all(
        item["feedback_id"] != feedback_payload["feedback_id"]
        for item in isolated_feedback.json()
    )

    beta_lead = client.post(
        "/beta/leads",
        headers=WORKSPACE_A,
        json={
            "email": "creator@example.com",
            "persona": "creator",
            "use_case": "영상 편집용 PC와 노트북 추천을 반복해서 비교",
            "company_size": "freelancer",
            "contact_consent": True,
            "source": "pytest",
        },
    )
    assert beta_lead.status_code == 200
    lead_payload = beta_lead.json()
    assert lead_payload["email_masked"] == "cr***@example.com"

    beta_leads = client.get("/beta/leads", headers=WORKSPACE_A)
    assert any(item["lead_id"] == lead_payload["lead_id"] for item in beta_leads.json())

    metrics_after_feedback = client.get("/ops/metrics", headers=WORKSPACE_A).json()
    assert metrics_after_feedback["feedback_count"] >= 1
    assert metrics_after_feedback["beta_leads"] >= 1
    assert metrics_after_feedback["average_satisfaction"] >= 5
    assert metrics_after_feedback["purchase_intent_rate"] > 0
    assert metrics_after_feedback["public_share_views"] >= 2

    readiness = client.get("/beta/readiness", headers=WORKSPACE_A)
    assert readiness.status_code == 200
    readiness_payload = readiness.json()
    assert readiness_payload["workspace_id"].startswith("workspace_")
    assert readiness_payload["launch_readiness_score"] > 0
    assert readiness_payload["readiness_label"]
    assert readiness_payload["analysis_runs"] >= 1
    assert readiness_payload["feedback_count"] >= 1
    assert readiness_payload["beta_leads"] >= 1
    assert readiness_payload["public_share_views"] >= 2
    assert len(readiness_payload["checks"]) >= 5
    assert readiness_payload["next_actions"]

    isolated_readiness = client.get("/beta/readiness", headers=WORKSPACE_B)
    assert isolated_readiness.status_code == 200
    assert isolated_readiness.json()["public_share_views"] == 0

    cohort = client.post(
        "/beta/cohorts",
        headers=WORKSPACE_A,
        json={
            "name": "영상 편집 QHD 데스크톱 cohort",
            "scenario": "영상 편집과 QHD 144Hz 게임용 데스크톱",
            "category": "desktop_pc",
            "target_persona": "creator",
            "target_size": 10,
            "success_metric": "purchase_intent_rate",
            "keywords": ["영상 편집", "QHD", "데스크톱"],
            "notes": "pytest cohort",
        },
    )
    assert cohort.status_code == 200
    cohort_payload = cohort.json()
    assert cohort_payload["lead_count"] >= 1
    assert cohort_payload["feedback_count"] >= 1
    assert cohort_payload["purchase_intent_rate"] > 0
    assert cohort_payload["readiness_score"] > 0

    cohorts = client.get("/beta/cohorts", headers=WORKSPACE_A)
    assert any(item["cohort_id"] == cohort_payload["cohort_id"] for item in cohorts.json())

    isolated_cohorts = client.get("/beta/cohorts", headers=WORKSPACE_B)
    assert all(item["cohort_id"] != cohort_payload["cohort_id"] for item in isolated_cohorts.json())

    backlog = client.get("/beta/backlog", headers=WORKSPACE_A)
    assert backlog.status_code == 200
    backlog_items = backlog.json()
    assert backlog_items
    assert any(item["source_type"] == "readiness" for item in backlog_items)
    learning_backlog = next(item for item in backlog_items if item["source_type"] == "learning")
    assert learning_backlog["source_id"] == top_recommendation["product"]["id"]
    assert "학습 인사이트 개선" in learning_backlog["title"]
    assert learning_backlog["suggested_action"]
    assert all(item["workspace_id"] == readiness_payload["workspace_id"] for item in backlog_items)

    backlog_id = backlog_items[0]["backlog_id"]
    action = client.patch(
        f"/beta/backlog/{backlog_id}",
        headers=WORKSPACE_A,
        json={
            "status": "in_progress",
            "assignee": "pm",
            "note": "pytest에서 운영 액션 상태 검증",
        },
    )
    assert action.status_code == 200
    action_payload = action.json()
    assert action_payload["status"] == "in_progress"
    assert action_payload["assignee"] == "pm"

    updated_backlog = client.get("/beta/backlog", headers=WORKSPACE_A).json()
    tracked_item = next(item for item in updated_backlog if item["backlog_id"] == backlog_id)
    assert tracked_item["status"] == "in_progress"
    assert tracked_item["assignee"] == "pm"
    assert tracked_item["action_note"] == "pytest에서 운영 액션 상태 검증"
    assert tracked_item["sla_due_at"]
    assert tracked_item["is_overdue"] is False

    isolated_action = client.patch(
        f"/beta/backlog/{backlog_id}",
        headers=WORKSPACE_B,
        json={"status": "done", "assignee": "other-workspace"},
    )
    assert isolated_action.status_code == 200
    unchanged_backlog = client.get("/beta/backlog", headers=WORKSPACE_A).json()
    unchanged_item = next(item for item in unchanged_backlog if item["backlog_id"] == backlog_id)
    assert unchanged_item["status"] == "in_progress"
    assert unchanged_item["assignee"] == "pm"

    completed_action = client.patch(
        f"/beta/backlog/{backlog_id}",
        headers=WORKSPACE_A,
        json={
            "status": "done",
            "assignee": "pm",
            "note": "pytest에서 SLA 완료 처리",
            "completion_summary": "pytest 완료 요약",
        },
    )
    assert completed_action.status_code == 200
    completed_payload = completed_action.json()
    assert completed_payload["completed_at"]
    assert completed_payload["completion_summary"] == "pytest 완료 요약"

    backlog_summary = client.get("/beta/backlog/summary", headers=WORKSPACE_A)
    assert backlog_summary.status_code == 200
    summary_payload = backlog_summary.json()
    assert summary_payload["workspace_id"] == readiness_payload["workspace_id"]
    assert summary_payload["total_count"] >= 1
    assert summary_payload["done_count"] >= 1
    assert "pytest 완료 요약" in summary_payload["completion_summaries"]
    assert summary_payload["next_actions"]

    launch_gate = client.get("/beta/launch-gate", headers=WORKSPACE_A)
    assert launch_gate.status_code == 200
    launch_payload = launch_gate.json()
    assert launch_payload["workspace_id"] == readiness_payload["workspace_id"]
    assert launch_payload["decision"] in {"go", "limited_beta", "hold", "blocked"}
    assert launch_payload["status"] in {"ok", "warning", "blocker"}
    assert launch_payload["summary"]
    assert launch_payload["required_actions"]
    assert len(launch_payload["checks"]) >= 7
    assert {check["area"] for check in launch_payload["checks"]} >= {
        "readiness",
        "regression",
        "learning",
        "backlog",
        "conversion",
        "delivery",
        "integration",
        "data_governance",
    }
    assert launch_payload["metric_cards"]["learning_insights"] >= 1
    assert launch_payload["metric_cards"]["purchase_outcomes"] >= 2
    assert "integration_score" in launch_payload["metric_cards"]
    assert "integration_blockers" in launch_payload["metric_cards"]
    assert launch_payload["metric_cards"]["data_governance_status"] in {
        "ok",
        "warning",
        "blocker",
    }
    assert launch_payload["metric_cards"]["raw_contact_surfaces"] >= 1

    isolated_launch_gate = client.get("/beta/launch-gate", headers=WORKSPACE_B)
    assert isolated_launch_gate.status_code == 200
    isolated_launch_payload = isolated_launch_gate.json()
    assert isolated_launch_payload["workspace_id"] != launch_payload["workspace_id"]
    assert isolated_launch_payload["metric_cards"]["purchase_outcomes"] == 0

    cohort_report = client.get(
        f"/beta/cohorts/{cohort_payload['cohort_id']}/report",
        headers=WORKSPACE_A,
    )
    assert cohort_report.status_code == 200
    report_payload = cohort_report.json()
    assert report_payload["cohort"]["cohort_id"] == cohort_payload["cohort_id"]
    assert report_payload["metric_cards"]["lead_count"] >= 1
    assert report_payload["recommendations"]
    assert "베타 cohort 리포트" in report_payload["markdown"]

    markdown_report = client.get(
        f"/beta/cohorts/{cohort_payload['cohort_id']}/report.md",
        headers=WORKSPACE_A,
    )
    assert markdown_report.status_code == 200
    assert "## 핵심 지표" in markdown_report.text

    isolated_report = client.get(
        f"/beta/cohorts/{cohort_payload['cohort_id']}/report",
        headers=WORKSPACE_B,
    )
    assert isolated_report.status_code == 404


def test_alert_preview_endpoint_returns_three_targets() -> None:
    response = client.post(
        "/alerts/preview",
        json={
            "query": "영상 편집용 노트북 200만원 이하로 비교해줘",
            "category": "laptop",
            "budget_krw": 2_000_000,
            "purpose": "Premiere Pro video editing",
            "must_haves": ["32GB RAM 선호", "외장 GPU"],
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_source_collection_and_admin_review_flow() -> None:
    source_slug = uuid4().hex[:8]
    status = client.get("/sources/status")
    assert status.status_code == 200
    assert len(status.json()) >= 4

    collected = client.post(
        "/sources/collect",
        json={
            "query": "영상 편집과 게임용 데스크톱 200만원 QHD 144Hz",
            "category": "desktop_pc",
            "limit": 12,
        },
    )
    assert collected.status_code == 200
    payload = collected.json()
    assert payload["candidates"]
    assert payload["review_queue"]

    ingested = client.post(
        "/sources/ingest-url",
        json={
            "url": f"https://example.com/product/creator-pc-{source_slug}",
            "category": "desktop_pc",
            "kind": "price",
            "expected_model": "Creator RTX 4070 PC",
            "seller": "Example Store",
            "html": """
            <html>
              <head>
                <title>Creator RTX 4070 PC | Example Store</title>
                <meta name="description" content="32GB RAM, 1TB SSD 구성의 영상 편집 PC">
              </head>
              <body>
                <h1>Creator RTX 4070 PC</h1>
                <p>최종 결제 금액 1,899,000원</p>
                <p>무료배송, 카드 할인 50,000원 적용 가능</p>
                <p>재고 있음, 바로 구매 가능</p>
                <p>QHD 144Hz 게임과 영상 편집 추천 구성</p>
              </body>
            </html>
            """,
        },
    )
    assert ingested.status_code == 200
    ingested_payload = ingested.json()
    assert ingested_payload["candidate"]["adapter_id"] == "operator_url_ingest"
    assert ingested_payload["candidate"]["extracted_price_krw"] == 1_899_000
    assert ingested_payload["candidate"]["shipping_fee_krw"] == 0
    assert ingested_payload["candidate"]["coupon_or_card_benefit_krw"] == 50_000
    assert ingested_payload["candidate"]["effective_price_krw"] == 1_849_000
    assert ingested_payload["candidate"]["availability_status"] == "in_stock"
    assert ingested_payload["candidate"]["model_match_status"] == "ok"
    assert any(
        "추정 실구매가 1,849,000원" in item
        for item in ingested_payload["candidate"]["extraction_signals"]
    )
    assert ingested_payload["candidate"]["needs_review"] is True
    assert ingested_payload["review_item"]["status"] == "pending"
    assert "HTML 스냅샷" in ingested_payload["extraction_notes"][0]

    monitor = client.post(
        "/sources/monitors",
        headers=WORKSPACE_A,
        json={
            "url": f"https://example.com/product/monitor-pc-{source_slug}",
            "category": "desktop_pc",
            "kind": "price",
            "expected_model": "Monitor RTX 4070 PC",
            "seller": "Monitor Store",
            "cadence_minutes": 120,
            "html_snapshot": """
            <html>
              <head><title>Monitor RTX 4070 PC</title></head>
              <body>모니터링 기준 가격 1,799,000원</body>
            </html>
            """,
        },
    )
    assert monitor.status_code == 200
    monitor_payload = monitor.json()
    assert monitor_payload["last_status"] == "never_run"
    assert "html_snapshot" not in monitor_payload

    schedule_before = client.get("/sources/schedule", headers=WORKSPACE_A)
    assert schedule_before.status_code == 200
    assert any(
        item["monitor"]["monitor_id"] == monitor_payload["monitor_id"]
        for item in schedule_before.json()["due"]
    )

    due_refresh = client.post(
        "/sources/refresh-due",
        headers=WORKSPACE_A,
        json={"limit": 10},
    )
    assert due_refresh.status_code == 200
    due_payload = due_refresh.json()
    assert due_payload["selected_count"] >= 1
    assert any(
        item["monitor_id"] == monitor_payload["monitor_id"]
        and item["status"] == "succeeded"
        for item in due_payload["runs"]
    )

    schedule_after = client.get("/sources/schedule", headers=WORKSPACE_A)
    assert schedule_after.status_code == 200
    assert not any(
        item["monitor"]["monitor_id"] == monitor_payload["monitor_id"]
        for item in schedule_after.json()["due"]
    )

    refresh = client.post(
        "/sources/refresh",
        headers=WORKSPACE_A,
        json={"monitor_ids": [monitor_payload["monitor_id"]]},
    )
    assert refresh.status_code == 200
    refresh_payload = refresh.json()
    assert refresh_payload["selected_count"] == 1
    assert refresh_payload["succeeded_count"] == 1
    assert refresh_payload["failed_count"] == 0
    assert refresh_payload["candidates"][0]["extracted_price_krw"] == 1_799_000
    assert refresh_payload["review_items"][0]["status"] == "pending"

    monitors = client.get("/sources/monitors", headers=WORKSPACE_A)
    assert monitors.status_code == 200
    assert monitors.json()[0]["last_status"] == "succeeded"
    assert monitors.json()[0]["last_source_id"] == refresh_payload["candidates"][0]["source_id"]

    refresh_runs = client.get("/sources/refresh-runs", headers=WORKSPACE_A)
    assert refresh_runs.status_code == 200
    assert refresh_runs.json()[0]["status"] == "succeeded"

    live_without_policy = client.post(
        "/sources/ingest-url",
        headers=WORKSPACE_A,
        json={
            "url": f"https://unapproved-{source_slug}.example.net/product",
            "category": "desktop_pc",
            "kind": "price",
            "expected_model": "blocked live fetch",
        },
    )
    assert live_without_policy.status_code == 403
    assert "provider" in live_without_policy.json()["detail"]

    regression_after_block = client.get("/ops/regression", headers=WORKSPACE_A)
    assert regression_after_block.status_code == 200
    assert any(
        item["host"] == f"unapproved-{source_slug}.example.net"
        and item["blocked_count"] >= 1
        for item in regression_after_block.json()["provider_reliability"]
    )

    pending_provider = client.post(
        "/sources/providers",
        headers=WORKSPACE_A,
        json={
            "provider_name": "Pending Provider",
            "host_pattern": f"pending-{source_slug}.example.com",
            "kind": "price",
            "live_fetch_allowed": True,
            "robots_status": "pending",
            "terms_status": "approved",
            "credential_status": "operator_reviewed",
            "rate_limit_per_hour": 10,
        },
    )
    assert pending_provider.status_code == 200
    pending_check = client.post(
        "/sources/providers/check",
        headers=WORKSPACE_A,
        json={"url": f"https://pending-{source_slug}.example.com/product"},
    )
    assert pending_check.status_code == 200
    assert pending_check.json()["allowed"] is False

    approved_provider = client.post(
        "/sources/providers",
        headers=WORKSPACE_A,
        json={
            "provider_name": "Approved Provider",
            "host_pattern": f"approved-{source_slug}.example.com",
            "kind": "price",
            "live_fetch_allowed": True,
            "robots_status": "approved",
            "terms_status": "approved",
            "credential_status": "operator_reviewed",
            "rate_limit_per_hour": 1,
        },
    )
    assert approved_provider.status_code == 200
    provider_check = client.post(
        "/sources/providers/check",
        headers=WORKSPACE_A,
        json={"url": f"https://shop.approved-{source_slug}.example.com/product"},
    )
    assert provider_check.status_code == 200
    assert provider_check.json()["allowed"] is True
    assert provider_check.json()["remaining_hourly_quota"] == 0

    providers = client.get("/sources/providers", headers=WORKSPACE_A)
    assert providers.status_code == 200
    assert any(
        item["provider_id"] == approved_provider.json()["provider_id"]
        for item in providers.json()
    )

    isolated_monitors = client.get("/sources/monitors", headers=WORKSPACE_B)
    assert isolated_monitors.status_code == 200
    assert not any(
        item["monitor_id"] == monitor_payload["monitor_id"]
        for item in isolated_monitors.json()
    )
    isolated_providers = client.get("/sources/providers", headers=WORKSPACE_B)
    assert isolated_providers.status_code == 200
    assert not any(
        item["provider_id"] == approved_provider.json()["provider_id"]
        for item in isolated_providers.json()
    )

    blocked_url = client.post(
        "/sources/ingest-url",
        json={
            "url": "http://127.0.0.1/internal",
            "category": "desktop_pc",
            "kind": "price",
            "expected_model": "blocked",
            "html": "<html><title>blocked</title></html>",
        },
    )
    assert blocked_url.status_code == 400

    blocked_userinfo_url = client.post(
        "/sources/ingest-url",
        json={
            "url": "https://user:pass@example.com/product",
            "category": "desktop_pc",
            "kind": "price",
            "expected_model": "blocked",
            "html": "<html><title>blocked</title></html>",
        },
    )
    assert blocked_userinfo_url.status_code == 400

    reviews = client.get("/admin/reviews")
    assert reviews.status_code == 200
    review_items = reviews.json()
    assert review_items
    assert any(
        item["source"]["source_id"] == ingested_payload["candidate"]["source_id"]
        for item in review_items
    )
    assert any(
        item["source"]["source_id"] == refresh_payload["candidates"][0]["source_id"]
        for item in review_items
    )

    decision = client.post(
        f"/admin/reviews/{review_items[0]['review_id']}/decision",
        json={
            "status": "approved",
            "reviewer": "pytest",
            "note": "테스트 승인",
        },
    )
    assert decision.status_code == 200
    assert decision.json()["status"] == "approved"

    dashboard = client.get("/admin/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["adapter_statuses"]


def test_integration_readiness_tracks_external_provider_state_by_workspace() -> None:
    initial = client.get("/ops/integration-readiness", headers=WORKSPACE_A)
    assert initial.status_code == 200
    initial_payload = initial.json()
    assert initial_payload["workspace_id"].startswith("workspace_")
    assert initial_payload["status"] in {"warning", "blocker"}
    assert initial_payload["required_count"] >= 6
    assert initial_payload["blocker_count"] >= 1
    assert any(check["category"] == "price_api" for check in initial_payload["checks"])

    provider = client.post(
        "/ops/integrations",
        headers=WORKSPACE_A,
        json={
            "provider_name": "Pytest Price API",
            "category": "price_api",
            "status": "verified",
            "credential_status": "vault_connected",
            "rate_limit_per_hour": 120,
            "retention_days": 30,
            "endpoint": "https://api.example.test/prices",
            "evidence": "pytest smoke test passed",
            "notes": "credential value is stored outside SpecPilot",
        },
    )
    assert provider.status_code == 200
    assert provider.json()["last_verified_at"]

    providers = client.get("/ops/integrations", headers=WORKSPACE_A)
    assert providers.status_code == 200
    assert any(
        item["integration_id"] == provider.json()["integration_id"]
        for item in providers.json()
    )

    updated = client.get("/ops/integration-readiness", headers=WORKSPACE_A)
    assert updated.status_code == 200
    updated_payload = updated.json()
    price_check = next(
        check for check in updated_payload["checks"] if check["category"] == "price_api"
    )
    assert price_check["status"] == "ok"
    assert updated_payload["verified_count"] >= 1

    launch_gate = client.get("/beta/launch-gate", headers=WORKSPACE_A)
    assert launch_gate.status_code == 200
    assert any(check["area"] == "integration" for check in launch_gate.json()["checks"])

    isolated = client.get("/ops/integrations", headers=WORKSPACE_B)
    assert isolated.status_code == 200
    assert not any(
        item["integration_id"] == provider.json()["integration_id"]
        for item in isolated.json()
    )
