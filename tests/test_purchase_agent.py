from specpilot_ai.core.models import AgentStep, AnalyzeRequest, Category
from specpilot_ai.graph.product_graph import pc_purchase_graph_schema
from specpilot_ai.workflows.purchase_agent import run_analysis


def test_desktop_pc_analysis_returns_top_three_and_compatibility_notes() -> None:
    response = run_analysis(
        AnalyzeRequest(
            query="영상 편집과 게임용 데스크톱 200만원 안에서 맞춰줘",
            category=Category.desktop_pc,
            budget_krw=2_000_000,
            purpose="Premiere Pro, DaVinci Resolve, QHD gaming",
            must_haves=["QHD 144Hz", "32GB RAM", "업그레이드 여지"],
            channels=["price_compare", "open_market", "official_store"],
        )
    )

    assert response.steps[0] == AgentStep.intent_parser
    assert AgentStep.compatibility_checker in response.steps
    assert response.steps[-1] == AgentStep.report_writer
    assert len(response.report.top_recommendations) == 3
    assert len(response.report.excluded_products) == 2
    assert len(response.report.comparison_table) == 5
    assert response.report.price_alerts
    assert response.report.benchmark_evidence
    assert response.trace_events
    assert response.report.compatibility_notes
    assert response.report.source_trust
    assert response.report.trust_policy is not None
    assert response.report.trust_policy.affiliate_disclosure
    assert response.report.purchase_decision is not None
    assert response.report.purchase_decision.verdict in {
        "buy_now",
        "wait_for_price",
        "review_required",
    }
    assert response.report.purchase_decision.next_steps
    assert len(response.report.scenario_options) == 3
    assert {option.scenario for option in response.report.scenario_options} == {
        "value",
        "performance",
        "safe",
    }
    assert any(source.evidence_count > 0 for source in response.report.source_trust)
    assert response.quality_audit is not None
    assert response.quality_audit.quality_score > 0
    assert response.quality_audit.estimated_cost_krw > 0
    assert response.quality_audit.trace_id == response.graph_trace_id
    assert response.report.final_pick_id == response.report.top_recommendations[0].product.id
    assert response.graph_trace_id.startswith("trace_")


def test_laptop_analysis_is_supported() -> None:
    response = run_analysis(
        AnalyzeRequest(
            query="영상 편집용 노트북 200만원 이하로 비교해줘",
            category=Category.laptop,
            budget_krw=2_000_000,
            purpose="Premiere Pro and DaVinci Resolve video editing",
            must_haves=["32GB RAM 선호", "외장 GPU"],
        )
    )

    assert response.criteria.category == Category.laptop
    assert response.report.top_recommendations[0].product.category == Category.laptop
    assert response.report.top_recommendations[0].compatibility_checks
    assert response.report.top_recommendations[0].benchmark_evidence


def test_pc_purchase_graph_schema_has_component_and_compatibility_relationships() -> None:
    schema = pc_purchase_graph_schema()
    rel_types = {relationship.type for relationship in schema.relationships}
    labels = {node.label for node in schema.nodes}

    assert "Build" in labels
    assert "Component" in labels
    assert "PriceAlert" in labels
    assert "AnalysisTrace" in labels
    assert "USES" in rel_types
    assert "CHECKED_BY" in rel_types
    assert "HAS_BENCHMARK" in rel_types
    assert "WATCHED_BY" in rel_types
