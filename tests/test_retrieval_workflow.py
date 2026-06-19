from ontology_studio.core.models import QueryRequest, RetrievalMode
from ontology_studio.workflows.retrieval import run_query


def test_query_uses_preferred_mode() -> None:
    response = run_query(
        QueryRequest(
            question="KODEX 200 티커를 찾아줘",
            domain="finance",
            preferred_mode=RetrievalMode.full_text,
        )
    )

    assert response.mode == RetrievalMode.full_text
    assert response.evidence
    assert "전문 검색" in response.answer


def test_compliance_defaults_to_enhanced_graphrag() -> None:
    response = run_query(QueryRequest(question="규정 위반 근거를 알려줘", domain="compliance"))

    assert response.mode in {RetrievalMode.enhanced_graphrag, RetrievalMode.text2cypher}
    assert response.next_actions
