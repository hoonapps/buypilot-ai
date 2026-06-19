from fastapi.testclient import TestClient

from specpilot_ai.api.main import app

client = TestClient(app)


def test_launch_page_exposes_product_ui() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "SpecPilot AI" in response.text
    assert "분석 실행" in response.text


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
    assert payload["report"]["top_recommendations"][0]["price"]["effective_price_krw"] > 0
    assert payload["trace_events"]

    trace_response = client.get(f"/traces/{payload['graph_trace_id']}")
    assert trace_response.status_code == 200
    assert trace_response.json()


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
