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
    assert "목표가 도달 테스트" in response.text
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
    assert payload["report"]["top_recommendations"][0]["price"]["effective_price_krw"] > 0
    assert payload["quality_audit"]["quality_score"] > 0
    assert payload["quality_audit"]["estimated_cost_krw"] > 0
    assert payload["trace_events"]

    trace_response = client.get(f"/traces/{payload['graph_trace_id']}")
    assert trace_response.status_code == 200
    assert trace_response.json()


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
    assert "후보 비교표" in public_page.text

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
    assert any(
        event["subscription_id"] == subscription_id
        and event["delivery_status"] == "queued"
        for event in evaluated_payload["events"]
    )

    events = client.get("/alerts/events", headers=WORKSPACE_A)
    assert events.status_code == 200
    assert any(event["subscription_id"] == subscription_id for event in events.json())

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
    assert payload["average_quality_score"] > 0
    assert payload["estimated_cost_krw"] > 0

    quality = client.get("/ops/quality", headers=WORKSPACE_A)
    assert quality.status_code == 200
    quality_payload = quality.json()
    assert quality_payload["audit_count"] >= 1
    assert quality_payload["average_quality_score"] > 0
    assert quality_payload["total_estimated_cost_krw"] > 0
    assert any(item["trace_id"] == trace_id for item in quality_payload["recent_audits"])

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
