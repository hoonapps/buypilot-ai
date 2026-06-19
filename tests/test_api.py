from uuid import uuid4

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
    assert "완료 리포트 발송" in response.text
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

    metrics_after_share = client.get("/ops/metrics", headers=WORKSPACE_A).json()
    assert metrics_after_share["shared_reports"] >= 1
    assert metrics_after_share["public_share_views"] >= 2

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

    isolated_completion_batch = client.post(
        "/reports/completion-batches",
        headers=WORKSPACE_B,
        json={"report_ids": [saved_payload["report_id"]], "target": "ops@example.com"},
    )
    assert isolated_completion_batch.status_code == 200
    assert isolated_completion_batch.json()["selected_count"] == 0

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
