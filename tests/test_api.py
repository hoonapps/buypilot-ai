from fastapi.testclient import TestClient

from specpilot_ai.api.main import app

client = TestClient(app)
WORKSPACE_A = {"X-SpecPilot-Key": "pytest-workspace-a"}
WORKSPACE_B = {"X-SpecPilot-Key": "pytest-workspace-b"}


def test_launch_page_exposes_product_ui() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "SpecPilot AI" in response.text
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
    assert "발송 큐" in response.text
    assert "알림 발송 채널" in response.text
    assert "발송 시도" in response.text
    assert "Trace 저장소" in response.text
    assert "품질/비용 감사" in response.text
    assert "사용자 피드백" in response.text
    assert "베타 리드" in response.text


def test_trust_policy_endpoint_exposes_cache_and_fairness_rules() -> None:
    response = client.get("/policy/trust")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_policy"]
    assert payload["affiliate_disclosure"]
    assert payload["fairness_rules"]
    assert payload["review_rules"]
    assert payload["source_assessments"]


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

    share = client.post(
        f"/reports/{saved_payload['report_id']}/share",
        headers=WORKSPACE_A,
    )
    assert share.status_code == 200
    share_payload = share.json()
    assert share_payload["is_public"] is True
    assert share_payload["share_token"].startswith("share_")
    assert share_payload["public_path"].startswith("/r/share_")

    blocked_share = client.post(
        f"/reports/{saved_payload['report_id']}/share",
        headers=WORKSPACE_B,
    )
    assert blocked_share.status_code == 404

    public_report = client.get(f"/public/reports/{share_payload['share_token']}")
    assert public_report.status_code == 200
    assert public_report.json()["response"]["graph_trace_id"] == trace_id
    assert public_report.json()["share_views"] == 1

    public_page = client.get(f"/r/{share_payload['share_token']}")
    assert public_page.status_code == 200
    assert "테스트 구매 리포트" in public_page.text
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

    report_after_share = client.get(
        f"/reports/{saved_payload['report_id']}",
        headers=WORKSPACE_A,
    )
    assert report_after_share.json()["share_token"] == share_payload["share_token"]
    assert report_after_share.json()["share_views"] >= 2

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

    quality = client.get("/ops/quality", headers=WORKSPACE_A)
    assert quality.status_code == 200
    quality_payload = quality.json()
    assert quality_payload["audit_count"] >= 1
    assert quality_payload["average_quality_score"] > 0
    assert quality_payload["total_estimated_cost_krw"] > 0
    assert any(item["trace_id"] == trace_id for item in quality_payload["recent_audits"])

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

    reviews = client.get("/admin/reviews")
    assert reviews.status_code == 200
    review_items = reviews.json()
    assert review_items

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
