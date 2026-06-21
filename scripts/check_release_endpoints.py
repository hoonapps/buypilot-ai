from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from specpilot_ai.api.main import app


@dataclass(frozen=True)
class SmokeCheck:
    name: str
    method: str
    path: str
    required_keys: tuple[str, ...]


CHECKS = (
    SmokeCheck(
        name="ready",
        method="GET",
        path="/ready",
        required_keys=("ready", "storage_ready", "source_adapters_ready"),
    ),
    SmokeCheck(
        name="launch-smoke",
        method="GET",
        path="/public/launch-smoke?limit=8",
        required_keys=(
            "status",
            "smoke_score",
            "checks",
            "publish_ready_paths",
            "measurement_events",
        ),
    ),
    SmokeCheck(
        name="public-launch-preflight",
        method="GET",
        path="/ops/public-launch-preflight?limit=8",
        required_keys=(
            "status",
            "go_decision",
            "preflight_score",
            "checks",
            "launch_brief",
            "tracking_events",
        ),
    ),
    SmokeCheck(
        name="launch-gate",
        method="GET",
        path="/beta/launch-gate",
        required_keys=("decision", "launch_readiness_score", "checks", "required_actions"),
    ),
    SmokeCheck(
        name="public-price-watch-kit",
        method="GET",
        path="/public/price-watch-kit?category=desktop_pc&budget_krw=2200000&purpose=qhd_creator",
        required_keys=(
            "watch_version",
            "headline",
            "watched_count",
            "primary_watch_label",
            "candidates",
            "alert_script",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-listing-decoder-kit",
        method="POST",
        path="/public/listing-decoder-kit",
        required_keys=(
            "kit_version",
            "confidence_score",
            "decoded_specs",
            "scanner_prefill",
            "seller_questions",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-spec-term-decoder-kit",
        method="POST",
        path="/public/spec-term-decoder-kit",
        required_keys=(
            "kit_version",
            "decoder_status",
            "clarity_score",
            "explanations",
            "seller_questions",
            "scanner_prefill",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-purchase-question-triage-kit",
        method="POST",
        path="/public/purchase-question-triage-kit",
        required_keys=(
            "kit_version",
            "question_type",
            "triage_status",
            "urgency_score",
            "routed_kits",
            "buyer_reply",
            "community_post",
            "scanner_prefill",
        ),
    ),
    SmokeCheck(
        name="public-review-risk-kit",
        method="POST",
        path="/public/review-risk-kit",
        required_keys=(
            "kit_version",
            "review_status",
            "review_risk_score",
            "repeated_complaints",
            "review_signals",
            "seller_questions",
            "analysis_prefill",
        ),
    ),
    SmokeCheck(
        name="public-product-page-evidence-kit",
        method="POST",
        path="/public/product-page-evidence-kit",
        required_keys=(
            "kit_version",
            "priority",
            "evidence_score",
            "effective_price_krw",
            "availability_status",
            "model_match_status",
            "source_signals",
            "scanner_prefill",
            "price_prefill",
            "seller_evidence_prefill",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-setup-compatibility-kit",
        method="POST",
        path="/public/setup-compatibility-kit",
        required_keys=(
            "kit_version",
            "compatibility_score",
            "verdict",
            "checks",
            "scanner_prefill",
            "analysis_prefill",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-shopping-cart-intake-kit",
        method="POST",
        path="/public/shopping-cart-intake-kit",
        required_keys=(
            "kit_version",
            "cart_total_krw",
            "readiness_score",
            "verdict",
            "lines",
            "scanner_prefill",
            "approval_prefill",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-purchase-approval-brief-kit",
        method="POST",
        path="/public/purchase-approval-brief-kit",
        required_keys=(
            "kit_version",
            "priority",
            "decision_rule",
            "approval_question",
            "buyer_brief",
            "vote_options",
            "copy_variants",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-requirements-consensus-kit",
        method="POST",
        path="/public/requirements-consensus-kit",
        required_keys=(
            "kit_version",
            "consensus_status",
            "consensus_score",
            "agreed_must_haves",
            "agreed_exclusions",
            "conflicts",
            "stakeholders",
            "decision_rules",
            "recommended_request",
            "copy_variants",
            "analysis_prefill",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-build-blueprint-kit",
        method="POST",
        path="/public/build-blueprint-kit",
        required_keys=(
            "kit_version",
            "blueprint_status",
            "blueprint_score",
            "target_profile",
            "components",
            "search_queries",
            "compatibility_rules",
            "avoid_conditions",
            "cart_text_template",
            "setup_prefill",
            "analysis_prefill",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-seller-evidence-kit",
        method="POST",
        path="/public/seller-evidence-kit",
        required_keys=(
            "kit_version",
            "priority",
            "answer_status",
            "seller_message",
            "questions",
            "answer_rubric",
            "approval_prefill",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-seller-negotiation-kit",
        method="POST",
        path="/public/seller-negotiation-kit",
        required_keys=(
            "kit_version",
            "priority",
            "negotiation_score",
            "expected_saving_krw",
            "fair_offer_krw",
            "max_acceptable_price_krw",
            "levers",
            "message_variants",
            "guardrails",
            "seller_questions",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-custom-candidate-decision-kit",
        method="POST",
        path="/public/custom-candidate-decision-kit",
        required_keys=(
            "kit_version",
            "decision",
            "winner_candidate_id",
            "confidence_score",
            "items",
            "axes",
            "scenarios",
            "decision_rules",
            "seller_questions",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-checkout-lock-kit",
        method="POST",
        path="/public/checkout-lock-kit",
        required_keys=(
            "kit_version",
            "lock_status",
            "lock_score",
            "price_delta_krw",
            "checks",
            "locked_fields",
            "seller_questions",
            "capture_checklist",
            "execution_prefill",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-decision-defense-kit",
        method="POST",
        path="/public/decision-defense-kit",
        required_keys=(
            "kit_version",
            "defense_status",
            "defense_score",
            "reviewer_brief",
            "objections",
            "comparisons",
            "proof_checklist",
            "reviewer_questions",
            "copy_variants",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-purchase-aftercare-kit",
        method="POST",
        path="/public/purchase-aftercare-kit",
        required_keys=(
            "kit_version",
            "priority",
            "return_deadline",
            "warranty_deadline",
            "deadlines",
            "outcome_prefill",
            "messages",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-outcome-share-card-kit",
        method="POST",
        path="/public/outcome-share-card-kit",
        required_keys=(
            "kit_version",
            "proof_status",
            "proof_score",
            "outcome_status",
            "price_delta_krw",
            "proof_metrics",
            "proof_points",
            "share_variants",
            "learning_signals",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-first-boot-setup-kit",
        method="POST",
        path="/public/first-boot-setup-kit",
        required_keys=(
            "kit_version",
            "priority",
            "setup_score",
            "first_boot_checklist",
            "driver_checklist",
            "benchmark_plan",
            "messages",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-benchmark-validation-kit",
        method="POST",
        path="/public/benchmark-validation-kit",
        required_keys=(
            "kit_version",
            "performance_status",
            "performance_score",
            "bottleneck_summary",
            "checks",
            "evidence_checklist",
            "issue_triage",
            "seller_message",
            "messages",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-defect-claim-kit",
        method="POST",
        path="/public/defect-claim-kit",
        required_keys=(
            "kit_version",
            "claim_status",
            "claim_score",
            "urgency_label",
            "timeline",
            "evidence_checklist",
            "evidence_gaps",
            "claim_steps",
            "seller_message",
            "manufacturer_message",
            "messages",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-upgrade-readiness-kit",
        method="POST",
        path="/public/upgrade-readiness-kit",
        required_keys=(
            "kit_version",
            "priority",
            "readiness_score",
            "horizon_months",
            "readiness_items",
            "upgrade_paths",
            "seller_questions",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-ownership-cost-kit",
        method="POST",
        path="/public/ownership-cost-kit",
        required_keys=(
            "kit_version",
            "priority",
            "ownership_score",
            "expected_resale_value_krw",
            "net_cost_krw",
            "monthly_cost_krw",
            "cost_lines",
            "scenarios",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-warranty-return-kit",
        method="POST",
        path="/public/warranty-return-kit",
        required_keys=(
            "kit_version",
            "priority",
            "protection_score",
            "estimated_return_cost_krw",
            "policy_checks",
            "cost_lines",
            "seller_questions",
            "evidence_checklist",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-price-breakdown-kit",
        method="POST",
        path="/public/price-breakdown-kit",
        required_keys=(
            "kit_version",
            "priority",
            "price_score",
            "subtotal_krw",
            "effective_price_krw",
            "budget_delta_krw",
            "report_price_delta_krw",
            "price_lines",
            "risk_flags",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-deal-sanity-kit",
        method="POST",
        path="/public/deal-sanity-kit",
        required_keys=(
            "kit_version",
            "deal_status",
            "sanity_score",
            "effective_price_krw",
            "savings_krw",
            "sanity_flags",
            "seller_questions",
            "evidence_checklist",
            "checkout_stop_rules",
            "price_prefill",
            "analysis_prefill",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-price-trust-kit",
        method="POST",
        path="/public/price-trust-kit",
        required_keys=(
            "kit_version",
            "trust_status",
            "trust_score",
            "selected_effective_price_krw",
            "report_price_delta_krw",
            "candidates",
            "checks",
            "evidence_checklist",
            "disclosure_notes",
            "buyer_warning",
            "messages",
            "analysis_prefill",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-budget-stress-kit",
        method="POST",
        path="/public/budget-stress-kit",
        required_keys=(
            "kit_version",
            "baseline_status",
            "gap_krw",
            "recommended_scenario_id",
            "scenarios",
            "decision_rules",
            "analysis_prefill",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-purchase-execution-kit",
        method="POST",
        path="/public/purchase-execution-kit",
        required_keys=(
            "kit_version",
            "priority",
            "execution_score",
            "primary_action",
            "decision_checkpoint",
            "checkout_steps",
            "evidence_gates",
            "seller_questions",
            "stop_conditions",
            "share_messages",
            "share_copy",
        ),
    ),
    SmokeCheck(
        name="public-reviewer-quick-card-kit",
        method="POST",
        path="/public/reviewer-quick-card-kit",
        required_keys=(
            "kit_version",
            "review_status",
            "review_score",
            "buyer_summary",
            "reviewer_instruction",
            "vote_options",
            "risk_checks",
            "reviewer_questions",
            "required_evidence",
            "reply_templates",
            "analysis_prefill",
            "share_copy",
        ),
    ),
)


def _request(
    client: TestClient,
    method: str,
    path: str,
    headers: dict[str, str],
    *,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = client.request(method, path, headers=headers, json=json_body)
    if response.status_code != 200:
        raise AssertionError(f"{method} {path} returned HTTP {response.status_code}: {response.text}")
    return response.json()


def _seed_release_workspace(client: TestClient, headers: dict[str, str]) -> None:
    analyses: list[dict[str, Any]] = []
    scenarios = [
        (
            "desktop_pc",
            2_200_000,
            "QHD 게임과 영상 편집용 데스크톱을 220만원 안에서 추천해줘",
            "QHD gaming, Premiere Pro",
            ["RTX 4070급", "32GB RAM", "업그레이드 여지"],
        ),
        (
            "laptop",
            1_700_000,
            "개발과 출장 발표용 노트북을 170만원 안에서 골라줘",
            "development, travel presentation",
            ["가벼운 무게", "긴 배터리", "32GB RAM"],
        ),
    ]
    for index in range(10):
        category, budget, query, purpose, must_haves = scenarios[index % len(scenarios)]
        analyses.append(
            _request(
                client,
                "POST",
                "/analyze",
                headers,
                json_body={
                    "query": f"{query} 출시 스모크 #{index + 1}",
                    "category": category,
                    "budget_krw": budget,
                    "purpose": purpose,
                    "must_haves": must_haves,
                    "purchase_timing": "within_14_days",
                },
            )
        )

    saved_reports: list[dict[str, Any]] = []
    for index, analysis in enumerate(analyses):
        saved = _request(
            client,
            "POST",
            "/reports/save",
            headers,
            json_body={
                "trace_id": analysis["graph_trace_id"],
                "title": f"출시 스모크 구매 리포트 {index + 1}",
                "owner_label": "release-smoke",
            },
        )
        saved_reports.append(saved)
        product_id = analysis["report"]["top_recommendations"][0]["product"]["id"]
        _request(
            client,
            "POST",
            "/feedback",
            headers,
            json_body={
                "trace_id": analysis["graph_trace_id"],
                "rating": 5 if index % 3 else 4,
                "purchase_intent": True,
                "selected_product_id": product_id,
                "reason": "가격 근거와 제외 후보가 명확해 구매 판단에 도움이 됨",
                "contact": f"buyer{index}@release-smoke.example.com",
            },
        )
        _request(
            client,
            "POST",
            "/beta/leads",
            headers,
            json_body={
                "email": f"lead{index}@release-smoke.example.com",
                "persona": "team_buyer" if index % 2 else "individual_buyer",
                "use_case": "컴퓨터와 노트북 구매 기준을 빠르게 비교",
                "company_size": "2-10" if index % 2 else "personal",
                "source": "release_smoke",
            },
        )

    for saved in saved_reports[:3]:
        share = _request(client, "POST", f"/reports/{saved['report_id']}/share", headers)
        client.get(f"/public/reports/{share['share_token']}", headers=headers)

    for index, analysis in enumerate(analyses[:3]):
        alert = analysis["report"]["price_alerts"][0]
        _request(
            client,
            "POST",
            "/alerts/subscribe",
            headers,
            json_body={
                "trace_id": analysis["graph_trace_id"],
                "product_id": alert["product_id"],
                "target_price_krw": alert["target_price_krw"],
                "channels": ["email"],
                "contact": f"alert{index}@release-smoke.example.com",
                "owner_label": "release-smoke",
            },
        )
    _request(
        client,
        "POST",
        "/alerts/channels",
        headers,
        json_body={
            "channel": "email",
            "display_name": "Release smoke email",
            "target": "ops@release-smoke.example.com",
        },
    )
    _request(client, "POST", "/alerts/evaluate", headers, json_body={"dry_run": False})
    _request(client, "POST", "/alerts/dispatch", headers, json_body={"dry_run": False})

    event_types = [
        "analysis_view",
        "recommendation_click",
        "recommendation_click",
        "alternative_click",
        "share_cta",
        "alert_cta",
        "subscription_cta",
    ]
    for index, analysis in enumerate(analyses):
        product_id = analysis["report"]["top_recommendations"][0]["product"]["id"]
        report_id = saved_reports[index]["report_id"]
        for event_type in event_types:
            _request(
                client,
                "POST",
                "/growth/events",
                headers,
                json_body={
                    "event_type": event_type,
                    "trace_id": analysis["graph_trace_id"],
                    "report_id": report_id,
                    "product_id": product_id,
                    "source": "release_smoke",
                    "surface": "launch-page",
                    "label": f"{event_type} release smoke",
                    "metadata": {"scenario_index": index},
                },
            )

    first_referral = _request(
        client,
        "POST",
        "/growth/waitlist-referrals",
        headers,
        json_body={
            "email": "referral0@release-smoke.example.com",
            "persona": "team_buyer",
            "use_case": "팀 PC 구매 기준 공유",
            "source": "release_smoke",
        },
    )
    for index in range(1, 6):
        _request(
            client,
            "POST",
            "/growth/waitlist-referrals",
            headers,
            json_body={
                "email": f"referral{index}@release-smoke.example.com",
                "persona": "individual_buyer",
                "use_case": "주변 구매 예정자에게 추천 링크 공유",
                "referred_by_code": first_referral["referral_code"],
                "source": "release_smoke",
            },
        )

    for index, plan_id in enumerate(["premium", "team", "team", "premium", "team"]):
        _request(
            client,
            "POST",
            "/billing/subscription-intents",
            headers,
            json_body={
                "email": f"intent{index}@release-smoke.example.com",
                "plan_id": plan_id,
                "persona": "team_buyer" if plan_id == "team" else "individual_buyer",
                "team_size": 4 if plan_id == "team" else 1,
                "use_case": "반복 구매 리포트와 가격 알림 운영",
                "feature_priorities": ["가격 알림", "공유 리포트", "구매 결과 학습"],
                "source": "release_smoke",
            },
        )

    for saved, analysis in zip(saved_reports[:3], analyses[:3], strict=True):
        recommendation = analysis["report"]["top_recommendations"][0]
        product = recommendation["product"]
        _request(
            client,
            "POST",
            f"/reports/{saved['report_id']}/purchase-outcomes",
            headers,
            json_body={
                "product_id": product["id"],
                "status": "purchased",
                "final_paid_price_krw": recommendation["price"]["effective_price_krw"],
                "source_channel": "release_smoke",
                "reason": "추천 리포트 기준으로 결제 완료",
                "satisfaction": 5,
            },
        )

    experiment = _request(
        client,
        "POST",
        "/growth/launch-experiments",
        headers,
        json_body={
            "name": "출시 스모크 CTA",
            "channel": "community",
            "audience": "desktop_pc_buyer",
            "hypothesis": "구매 실패 방지 메시지가 분석 시작 전환을 높인다.",
            "primary_metric": "subscription_cta",
            "target_surface": "launch-page",
            "category": "desktop_pc",
            "variants": [
                {
                    "label": "구매 실패 방지",
                    "headline": "컴퓨터 견적, 결제 전에 실패 가능성을 줄이세요",
                    "body": "가격 타이밍, 호환성, 결제 전 검수까지 한 번에 확인합니다.",
                    "cta_label": "내 견적 검증",
                    "cta_path": "/#start-concierge",
                    "allocation_percent": 50,
                },
                {
                    "label": "빠른 추천",
                    "headline": "예산과 용도만 넣으면 후보를 좁혀드립니다",
                    "body": "데스크톱과 노트북 구매 후보를 근거와 함께 비교합니다.",
                    "cta_label": "바로 분석",
                    "cta_path": "/#demo-gallery",
                    "allocation_percent": 50,
                },
            ],
        },
    )
    variant_id = experiment["variants"][0]["variant_id"]
    for index in range(12):
        event_type = "conversion" if index < 3 else "impression"
        _request(
            client,
            "POST",
            f"/growth/launch-experiments/{experiment['experiment_id']}/events",
            headers,
            json_body={
                "variant_id": variant_id,
                "event_type": event_type,
                "source": "release_smoke",
                "surface": "launch-page",
            },
        )

    for category in [
        "price_api",
        "marketplace",
        "official_store",
        "review_feed",
        "benchmark",
        "email",
        "webhook",
        "observability",
        "affiliate",
        "scheduler",
    ]:
        _request(
            client,
            "POST",
            "/ops/integrations",
            headers,
            json_body={
                "provider_name": f"release-smoke-{category}",
                "category": category,
                "status": "verified",
                "credential_status": "connected",
                "rate_limit_per_hour": 120,
                "retention_days": 30,
                "endpoint": f"https://example.com/{category}",
                "evidence": "release smoke dry-run verified",
            },
        )


def _get_nested(payload: dict[str, Any], key: str) -> Any:
    current: Any = payload
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(key)
        current = current[part]
    return current


def _assert_no_blockers(name: str, payload: dict[str, Any]) -> None:
    status = payload.get("status")
    decision = payload.get("decision") or payload.get("go_decision")
    if status == "blocker" or decision == "blocked":
        blockers = [
            item.get("key") or item.get("area") or item.get("label")
            for item in payload.get("checks", [])
            if item.get("status") == "blocker"
        ]
        raise AssertionError(f"{name} still has release blockers: {blockers}")


def _assert_public_launch_payload(name: str, payload: dict[str, Any]) -> None:
    if name == "ready":
        if payload["ready"] is not True:
            raise AssertionError("/ready did not report ready=true")
        return

    if name == "launch-smoke":
        if not payload["publish_ready_paths"]:
            raise AssertionError("launch smoke did not expose publish_ready_paths")
        if not payload["checks"]:
            raise AssertionError("launch smoke did not expose checks")
        if "launch_smoke_view" not in payload["measurement_events"]:
            raise AssertionError("launch smoke measurement_events missing launch_smoke_view")
        _assert_no_blockers(name, payload)
        return

    if name == "public-launch-preflight":
        if payload["go_decision"] not in {"go", "limited_beta", "hold", "blocked"}:
            raise AssertionError(f"unexpected go_decision={payload['go_decision']}")
        if not payload["launch_brief"]:
            raise AssertionError("preflight launch_brief is empty")
        if not payload["checks"]:
            raise AssertionError("preflight checks are empty")
        _assert_no_blockers(name, payload)
        return

    if name == "launch-gate":
        if payload["decision"] not in {"go", "limited_beta", "hold", "blocked"}:
            raise AssertionError(f"unexpected launch gate decision={payload['decision']}")
        if not payload["checks"]:
            raise AssertionError("launch gate checks are empty")
        _assert_no_blockers(name, payload)


def run_smoke() -> list[dict[str, Any]]:
    client = TestClient(app)
    headers = {"X-SpecPilot-Key": f"release-smoke-{uuid4().hex}"}
    _seed_release_workspace(client, headers)
    results: list[dict[str, Any]] = []

    for check in CHECKS:
        json_body = None
        if check.name == "public-listing-decoder-kit":
            json_body = {
                "category": "laptop",
                "product_title": (
                    "CreatorBook Pro 16 Ryzen 7 8845HS RTX 4060 "
                    "RAM 32GB SSD 1TB Windows 11"
                ),
                "budget_krw": 2_200_000,
                "cart_total_krw": 2_090_000,
                "purpose": "portable_creator",
                "source": "release_smoke",
            }
        if check.name == "public-spec-term-decoder-kit":
            json_body = {
                "category": "laptop",
                "product_title": "CreatorBook Pro 16 RTX 4060 RAM 32GB SSD 1TB FreeDOS",
                "listing_text": (
                    "RTX 4060 TGP 75W / RAM 온보드 16GB+슬롯 16GB / "
                    "SSD 1TB / FreeDOS / USB-C PD충전 / 국내 AS"
                ),
                "terms": ["FreeDOS", "TGP", "온보드", "PD충전"],
                "buyer_level": "beginner",
                "primary_purpose": "portable_creator",
                "budget_krw": 2_200_000,
                "source": "release_smoke",
            }
        if check.name == "public-purchase-question-triage-kit":
            json_body = {
                "category": "desktop_pc",
                "buyer_question": "이 RTX 4070 SUPER 특가 오늘 결제해도 될까요?",
                "product_title": "Creator RTX 4070 SUPER Build",
                "listing_text": (
                    "Ryzen 7 7800X3D RTX 4070 SUPER RAM 32GB SSD 1TB Windows 11 "
                    "카드 할인 오늘 마감 / 반품 7일 / 국내 AS"
                ),
                "budget_krw": 2_200_000,
                "cart_total_krw": 2_185_000,
                "purchase_stage": "checkout",
                "audience": "beginner",
                "source": "release_smoke",
            }
        if check.name == "public-review-risk-kit":
            json_body = {
                "category": "laptop",
                "product_title": "CreatorBook Pro 16 RTX 4060",
                "review_snippets": [
                    "성능은 만족하지만 게임할 때 발열과 팬 소음이 꽤 있습니다.",
                    "영상 편집 중 온도가 높고 팬이 자주 돕니다. AS 응대는 보통입니다.",
                    "배송은 빨랐지만 화면 빛샘과 초기불량 교환 후기가 보여 걱정됩니다.",
                ],
                "rating": 4.1,
                "review_count": 86,
                "budget_krw": 2_200_000,
                "usage_context": "portable_creator",
                "source": "release_smoke",
            }
        if check.name == "public-product-page-evidence-kit":
            json_body = {
                "category": "desktop_pc",
                "url": "https://shop.example.com/product/creator-4070-super",
                "product_title": "Creator RTX 4070 SUPER Build",
                "expected_model": "Creator RTX 4070 SUPER Build",
                "expected_cpu": "Ryzen 7 7800X3D",
                "expected_gpu": "RTX 4070 SUPER",
                "expected_ram_gb": 32,
                "expected_storage_gb": 1000,
                "expected_os": "Windows 11",
                "budget_krw": 2_200_000,
                "seller_name": "PC Mall",
                "page_text": (
                    "Creator RTX 4070 SUPER Build Ryzen 7 7800X3D RTX 4070 SUPER "
                    "RAM 32GB SSD 1TB Windows 11 판매중 재고 있음 최종 결제 금액 "
                    "2,165,000원 무료배송 카드 할인 40,000원 국내 제조사 AS 반품 7일"
                ),
                "source": "release_smoke",
            }
        if check.name == "public-setup-compatibility-kit":
            json_body = {
                "category": "desktop_pc",
                "cpu": "Ryzen 7 7800X3D",
                "gpu": "RTX 4070 SUPER",
                "ram_gb": 32,
                "storage_gb": 1000,
                "monitor_resolution": "QHD",
                "psu_watt": 750,
                "form_factor": "ATX tower",
                "budget_krw": 2_200_000,
                "purpose": "qhd_creator",
                "source": "release_smoke",
            }
        if check.name == "public-shopping-cart-intake-kit":
            json_body = {
                "category": "desktop_pc",
                "budget_krw": 2_200_000,
                "purpose": "qhd_creator",
                "items": [
                    {"title": "Ryzen 7 7800X3D", "price_krw": 430000},
                    {"title": "RTX 4070 SUPER 12GB", "price_krw": 910000},
                    {"title": "DDR5 RAM 32GB", "price_krw": 145000},
                    {"title": "NVMe SSD 1TB", "price_krw": 110000},
                    {"title": "B650 메인보드", "price_krw": 210000},
                    {"title": "750W 파워", "price_krw": 120000},
                    {"title": "ATX 케이스", "price_krw": 95000},
                    {"title": "Windows 11 Home", "price_krw": 160000},
                ],
                "source": "release_smoke",
            }
        if check.name == "public-purchase-approval-brief-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "verdict": "verify",
                "budget_krw": 2_200_000,
                "cart_total_krw": 2_185_000,
                "blocker_count": 0,
                "warning_count": 2,
                "key_reasons": ["QHD 편집 목적에 GPU/RAM은 맞음"],
                "missing_evidence": ["배송 예정일", "AS 조건"],
                "audience": "family",
                "decision_deadline": "오늘 결제 전",
                "source": "release_smoke",
            }
        if check.name == "public-requirements-consensus-kit":
            json_body = {
                "category": "desktop_pc",
                "purchase_context": "QHD 게임과 영상 편집용 첫 데스크톱",
                "shared_budget_krw": 2_200_000,
                "target_timing": "within_14_days",
                "stakeholders": [
                    {
                        "name": "구매자",
                        "role": "owner",
                        "priority": "high",
                        "max_budget_krw": 2_200_000,
                        "use_cases": ["QHD 게임", "영상 편집"],
                        "must_haves": ["RTX 4070급 GPU", "RAM 32GB"],
                        "nice_to_haves": ["Windows 11"],
                        "deal_breakers": ["해외 리퍼"],
                        "timeline": "within_7_days",
                        "risk_tolerance": "medium",
                    },
                    {
                        "name": "가족",
                        "role": "approver",
                        "priority": "medium",
                        "max_budget_krw": 2_100_000,
                        "use_cases": ["장기 사용"],
                        "must_haves": ["국내 AS", "반품 7일"],
                        "deal_breakers": ["반품 불가"],
                        "timeline": "within_14_days",
                        "risk_tolerance": "low",
                    },
                    {
                        "name": "커뮤니티",
                        "role": "reviewer",
                        "priority": "low",
                        "max_budget_krw": 2_300_000,
                        "use_cases": ["부품 업그레이드"],
                        "must_haves": ["업그레이드 가능"],
                        "nice_to_haves": ["SSD 1TB"],
                        "deal_breakers": ["FreeDOS"],
                        "timeline": "wait_for_discount",
                        "risk_tolerance": "medium",
                    },
                ],
                "source": "release_smoke",
            }
        if check.name == "public-build-blueprint-kit":
            json_body = {
                "category": "desktop_pc",
                "budget_krw": 2_200_000,
                "purpose": "QHD 게임과 영상 편집",
                "priority_mode": "balanced",
                "must_haves": ["RTX 4070급 GPU", "RAM 32GB", "국내 AS"],
                "exclusions": ["해외 리퍼", "반품 불가"],
                "monitor_resolution": "QHD",
                "purchase_timing": "within_14_days",
                "source": "release_smoke",
            }
        if check.name == "public-seller-evidence-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "seller_name": "release-smoke-seller",
                "verdict": "verify",
                "budget_krw": 2_200_000,
                "cart_total_krw": 2_185_000,
                "risk_terms": ["FreeDOS"],
                "missing_evidence": ["배송 예정일", "반품 조건", "AS 조건"],
                "must_confirm": ["실제 출고 사양"],
                "source": "release_smoke",
            }
        if check.name == "public-seller-negotiation-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "seller_name": "PC Mall",
                "current_price_krw": 2_165_000,
                "target_price_krw": 2_100_000,
                "budget_krw": 2_200_000,
                "competing_price_krw": 2_120_000,
                "shipping_fee_krw": 10_000,
                "assembly_fee_krw": 30_000,
                "os_fee_krw": 0,
                "desired_ship_days": 2,
                "stock_count": 8,
                "urgency": "within_7_days",
                "risk_terms": ["카드 할인"],
                "must_keep_conditions": ["실제 출고 사양", "국내 AS", "반품 7일"],
                "source": "release_smoke",
            }
        if check.name == "public-custom-candidate-decision-kit":
            json_body = {
                "category": "desktop_pc",
                "budget_krw": 2_200_000,
                "purpose": "qhd_creator",
                "must_haves": ["RTX 4070급 GPU", "RAM 32GB", "국내 AS"],
                "candidates": [
                    {
                        "candidate_id": "release_a",
                        "title": "Creator RTX 4070 SUPER Build",
                        "seller_name": "PC Mall",
                        "url": "https://shop.example.com/a",
                        "listed_price_krw": 2_165_000,
                        "discount_krw": 40_000,
                        "cpu": "Ryzen 7 7800X3D",
                        "gpu": "RTX 4070 SUPER",
                        "ram_gb": 32,
                        "storage_gb": 1000,
                        "os_name": "Windows 11",
                        "warranty_months": 24,
                        "return_window_days": 14,
                        "stock_status": "in_stock",
                        "risk_terms": [],
                        "evidence_text": "국내 제조사 AS, 반품 14일, 재고 있음",
                    },
                    {
                        "candidate_id": "release_b",
                        "title": "Budget RTX 4060 Build",
                        "seller_name": "Budget PC",
                        "url": "https://shop.example.com/b",
                        "listed_price_krw": 1_720_000,
                        "shipping_fee_krw": 10_000,
                        "cpu": "Ryzen 5 7500F",
                        "gpu": "RTX 4060",
                        "ram_gb": 16,
                        "storage_gb": 512,
                        "os_name": "FreeDOS",
                        "warranty_months": 12,
                        "return_window_days": 7,
                        "stock_status": "in_stock",
                        "risk_terms": ["FreeDOS"],
                    },
                    {
                        "candidate_id": "release_c",
                        "title": "해외 리퍼 RTX 4080 PC",
                        "seller_name": "Open Market",
                        "url": "https://market.example.net/c",
                        "listed_price_krw": 2_050_000,
                        "shipping_fee_krw": 80_000,
                        "cpu": "Core i7",
                        "gpu": "RTX 4080",
                        "ram_gb": 32,
                        "storage_gb": 1000,
                        "os_name": "Windows 11",
                        "warranty_months": 0,
                        "return_window_days": 0,
                        "stock_status": "low_stock",
                        "risk_terms": ["해외", "리퍼", "반품 불가"],
                    },
                ],
                "source": "release_smoke",
            }
        if check.name == "public-checkout-lock-kit":
            json_body = {
                "category": "desktop_pc",
                "budget_krw": 2_200_000,
                "locked_candidate": {
                    "candidate_id": "release_a",
                    "title": "Creator RTX 4070 SUPER Build",
                    "seller_name": "PC Mall",
                    "locked_price_krw": 2_165_000,
                    "cpu": "Ryzen 7 7800X3D",
                    "gpu": "RTX 4070 SUPER",
                    "ram_gb": 32,
                    "storage_gb": 1000,
                    "os_name": "Windows 11",
                    "warranty_months": 24,
                    "return_window_days": 14,
                },
                "checkout_title": "Creator RTX 4070 SUPER Build",
                "checkout_seller_name": "PC Mall",
                "checkout_option_text": (
                    "Ryzen 7 7800X3D / RTX 4070 SUPER / RAM 32GB / "
                    "SSD 1TB / Windows 11"
                ),
                "checkout_total_krw": 2_150_000,
                "checkout_quantity": 1,
                "payment_method": "카드 결제",
                "evidence_text": "재고 있음, 오늘 출고, AS 24개월, 반품 14일, 무료배송",
                "source": "release_smoke",
            }
        if check.name == "public-decision-defense-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "seller_name": "PC Mall",
                "decision": "verify",
                "budget_krw": 2_200_000,
                "final_price_krw": 2_150_000,
                "confidence_score": 86,
                "purpose": "QHD 게임과 영상 편집",
                "audience": "community",
                "key_reasons": [
                    "RTX 4070 SUPER와 RAM 32GB가 목적에 맞음",
                    "예산 안에서 Windows 11과 국내 AS가 포함됨",
                    "해외 리퍼 후보보다 반품/보증 조건이 안전함",
                ],
                "watchouts": ["배송 예정일 캡처 필요", "쿠폰 적용 후 최종가 재확인"],
                "evidence_ready": ["최종 결제 금액", "옵션명", "AS 24개월", "반품 14일"],
                "alternatives": [
                    {
                        "title": "Budget RTX 4060 Build",
                        "price_krw": 1_730_000,
                        "reason_not_selected": "GPU와 RAM이 목적 대비 부족하고 FreeDOS 추가 비용이 있음",
                    }
                ],
                "objection_focus": ["price", "cheaper_alternative", "risk"],
                "source": "release_smoke",
            }
        if check.name == "public-purchase-aftercare-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "seller_name": "release-smoke-seller",
                "purchase_date": "2026-06-01",
                "delivered_date": "2026-06-03",
                "final_paid_price_krw": 2_185_000,
                "expected_price_krw": 2_200_000,
                "return_window_days": 7,
                "warranty_months": 12,
                "issues": [],
                "source": "release_smoke",
            }
        if check.name == "public-outcome-share-card-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "outcome_status": "purchased",
                "planned_price_krw": 2_200_000,
                "final_paid_price_krw": 2_165_000,
                "budget_krw": 2_200_000,
                "satisfaction_score": 9,
                "time_to_decide_hours": 18,
                "issues": [],
                "saved_reasons": ["최종 결제 금액 캡처", "AS 조건 확인"],
                "regrets": [],
                "next_recommendation": "반품 조건과 최종 결제 금액을 먼저 캡처",
                "share_audience": "community",
                "source": "release_smoke",
            }
        if check.name == "public-first-boot-setup-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "os_name": "Windows 11",
                "primary_purpose": "QHD 영상 편집",
                "monitor_resolution": "2560x1440 144Hz",
                "connection_type": "DisplayPort",
                "peripherals": ["모니터", "키보드", "마우스"],
                "missing_drivers": ["graphics"],
                "observed_issues": [],
                "warranty_registered": False,
                "bios_updated": True,
                "source": "release_smoke",
            }
        if check.name == "public-benchmark-validation-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "primary_purpose": "QHD 영상 편집",
                "cpu_name": "Ryzen 7 7800X3D",
                "gpu_name": "RTX 4070 SUPER",
                "ram_gb": 32,
                "expected_cpu_score": 18_000,
                "observed_cpu_score": 17_400,
                "expected_gpu_score": 28_000,
                "observed_gpu_score": 27_200,
                "expected_ssd_read_mbps": 7_000,
                "observed_ssd_read_mbps": 6_850,
                "max_cpu_temp_c": 82,
                "max_gpu_temp_c": 78,
                "fan_noise_note": "부하 시 정상 팬 소음",
                "throttling_observed": False,
                "crashes": [],
                "driver_versions_checked": True,
                "evidence_links": ["release-smoke://benchmark"],
                "source": "release_smoke",
            }
        if check.name == "public-defect-claim-kit":
            json_body = {
                "category": "laptop",
                "product_title": "CreatorBook 16",
                "seller_name": "Laptop Store",
                "manufacturer_name": "Maker",
                "purchase_date": "2026-06-01",
                "delivered_date": "2026-06-19",
                "return_deadline": "2026-06-26",
                "warranty_deadline": "2027-06-01",
                "final_paid_price_krw": 1_780_000,
                "order_reference_masked": "ORD***123",
                "preferred_resolution": "exchange",
                "issue_summary": "벤치마크 중 꺼짐과 화면 깜빡임",
                "observed_issues": ["렌더링 중 꺼짐", "화면 깜빡임", "고주파"],
                "failed_checks": ["GPU 점수 59%", "CPU 106도"],
                "benchmark_status": "blocker",
                "evidence_items": ["결제 영수증", "시리얼 사진", "꺼짐 재현 영상", "온도 그래프"],
                "seller_responses": ["판매자 1차 문의 접수"],
                "policy_text": "초기 불량 교환 가능",
                "source": "release_smoke",
            }
        if check.name == "public-upgrade-readiness-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "cpu_platform": "AM5",
                "gpu_name": "RTX 4070 SUPER",
                "ram_gb": 32,
                "ram_slots_total": 4,
                "ram_slots_used": 2,
                "storage_slots_total": 3,
                "storage_slots_used": 1,
                "psu_watt": 750,
                "case_form_factor": "ATX mid tower",
                "target_years": 4,
                "planned_upgrades": ["RAM 64GB", "SSD 2TB", "GPU 교체"],
                "constraints": ["QHD 144Hz 유지"],
                "budget_krw": 2_200_000,
                "source": "release_smoke",
            }
        if check.name == "public-ownership-cost-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "purchase_price_krw": 2_185_000,
                "expected_years": 3,
                "resale_rate_percent": 35,
                "yearly_maintenance_krw": 60_000,
                "planned_upgrade_cost_krw": 180_000,
                "warranty_months": 24,
                "downtime_days": 1,
                "daily_value_krw": 120_000,
                "brand_resale_signal": "medium",
                "condition_risks": [],
                "source": "release_smoke",
            }
        if check.name == "public-warranty-return-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "seller_name": "PC Mall",
                "purchase_price_krw": 2_185_000,
                "return_window_days": 14,
                "exchange_window_days": 14,
                "dead_on_arrival_days": 7,
                "warranty_months": 24,
                "opened_box_return_allowed": True,
                "warranty_provider": "manufacturer",
                "warranty_transferable": True,
                "return_shipping_fee_krw": 10_000,
                "restocking_fee_percent": 0,
                "policy_text": "국내 제조사 AS, 초기 불량 교환 가능",
                "risk_terms": [],
                "source": "release_smoke",
            }
        if check.name == "public-price-breakdown-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "seller_name": "PC Mall",
                "listed_price_krw": 2_185_000,
                "quantity": 1,
                "shipping_fee_krw": 10_000,
                "assembly_fee_krw": 30_000,
                "os_fee_krw": 0,
                "coupon_discount_krw": 40_000,
                "card_discount_krw": 20_000,
                "point_rebate_krw": 0,
                "budget_krw": 2_200_000,
                "expected_report_price_krw": 2_185_000,
                "discount_expires_hours": 72,
                "stock_count": 8,
                "risk_terms": ["카드 할인"],
                "source": "release_smoke",
            }
        if check.name == "public-deal-sanity-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "seller_name": "PC Mall",
                "listed_price_krw": 2_165_000,
                "reference_price_krw": 2_350_000,
                "lowest_seen_price_krw": 2_100_000,
                "budget_krw": 2_200_000,
                "shipping_fee_krw": 0,
                "coupon_discount_krw": 40_000,
                "card_discount_krw": 20_000,
                "point_rebate_krw": 0,
                "warranty_months": 24,
                "return_window_days": 14,
                "stock_count": 8,
                "discount_expires_hours": 48,
                "seller_rating_percent": 97.5,
                "review_count": 180,
                "risk_terms": ["카드 할인"],
                "evidence_text": "국내 AS 24개월, 반품 14일, 새상품",
                "source": "release_smoke",
            }
        if check.name == "public-price-trust-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "report_price_krw": 2_165_000,
                "budget_krw": 2_200_000,
                "selected_seller_name": "PC Mall",
                "candidates": [
                    {
                        "source_name": "가격비교",
                        "seller_name": "PC Mall",
                        "product_title": "Creator RTX 4070 SUPER Build",
                        "listed_price_krw": 2_165_000,
                        "shipping_fee_krw": 10_000,
                        "coupon_discount_krw": 40_000,
                        "card_discount_krw": 20_000,
                        "captured_minutes_ago": 18,
                        "stock_count": 8,
                        "affiliate_link": True,
                        "non_affiliate_available": True,
                        "screenshot_captured": True,
                        "checkout_price_verified": True,
                        "url_verified": True,
                        "condition_notes": ["국내 AS 24개월", "반품 14일"],
                    },
                    {
                        "source_name": "공식몰",
                        "seller_name": "Official Store",
                        "product_title": "Creator RTX 4070 SUPER Build",
                        "listed_price_krw": 2_190_000,
                        "shipping_fee_krw": 0,
                        "captured_minutes_ago": 22,
                        "stock_count": 12,
                        "affiliate_link": False,
                        "non_affiliate_available": True,
                        "screenshot_captured": True,
                        "checkout_price_verified": True,
                        "url_verified": True,
                        "condition_notes": ["공식몰", "국내 AS"],
                    },
                ],
                "source": "release_smoke",
            }
        if check.name == "public-budget-stress-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "current_budget_krw": 2_000_000,
                "target_price_krw": 2_165_000,
                "reference_good_price_krw": 2_100_000,
                "required_specs": ["RTX 4070 SUPER", "32GB RAM", "국내 AS"],
                "flexible_specs": ["케이스 RGB", "SSD 2TB", "조립 옵션"],
                "blocked_conditions": ["해외 리퍼", "반품 불가"],
                "use_case": "QHD 영상 편집과 게임",
                "urgency": "이번 주 안에 구매",
                "can_wait_days": 21,
                "risk_tolerance": "보통",
                "source": "release_smoke",
            }
        if check.name == "public-purchase-execution-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "seller_name": "PC Mall",
                "verdict": "verify",
                "final_price_krw": 2_165_000,
                "budget_krw": 2_200_000,
                "blocker_count": 0,
                "warning_count": 2,
                "missing_evidence": ["AS 조건", "배송 예정일"],
                "seller_questions": ["실제 출고 사양이 장바구니 옵션과 같은가요?"],
                "evidence_ready": ["최종 결제 금액", "옵션명"],
                "decision_deadline": "오늘 22시 전",
                "payment_method": "카드 결제",
                "share_audience": "family",
                "source": "release_smoke",
            }
        if check.name == "public-reviewer-quick-card-kit":
            json_body = {
                "category": "desktop_pc",
                "product_title": "Creator RTX 4070 SUPER Build",
                "buyer_decision": "verify",
                "final_price_krw": 2_165_000,
                "budget_krw": 2_200_000,
                "confidence_percent": 76,
                "blocker_count": 0,
                "warning_count": 2,
                "key_reasons": ["QHD 편집 목적에 GPU/RAM이 맞음", "예산 안", "국내 AS"],
                "watchouts": ["배송 예정일", "카드 할인 조건"],
                "missing_evidence": ["AS 조건", "배송 예정일"],
                "reviewer_role": "family",
                "review_deadline": "오늘 22시 전",
                "share_channel": "kakao",
                "source": "release_smoke",
            }
        response = client.request(check.method, check.path, headers=headers, json=json_body)
        if response.status_code != 200:
            raise AssertionError(f"{check.name} returned HTTP {response.status_code}")
        payload = response.json()
        for key in check.required_keys:
            _get_nested(payload, key)
        _assert_public_launch_payload(check.name, payload)
        results.append(
            {
                "name": check.name,
                "path": check.path,
                "status": payload.get("status") or payload.get("decision") or "ok",
                "decision": payload.get("decision") or payload.get("go_decision"),
                "score": payload.get("smoke_score")
                or payload.get("preflight_score")
                or payload.get("launch_readiness_score"),
            }
        )

    return results


def main() -> int:
    try:
        print(json.dumps({"release_smoke": run_smoke()}, ensure_ascii=False, indent=2))
    except Exception as error:
        print(f"release smoke failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
