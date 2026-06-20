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
