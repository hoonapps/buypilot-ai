from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph

from ontology_studio.core.models import QueryRequest, QueryResponse, RetrievalMode
from ontology_studio.graph.ontology import default_ontology


class GraphRagState(TypedDict, total=False):
    request: QueryRequest
    mode: RetrievalMode
    evidence: list[str]
    answer: str
    next_actions: list[str]


def choose_mode(state: GraphRagState) -> GraphRagState:
    request = state["request"]
    if request.preferred_mode:
        state["mode"] = request.preferred_mode
        return state

    question = request.question.lower()
    relation_keywords = ["관계", "연결", "담당", "경로", "누가", "어떤 부서", "왜"]
    exact_keywords = ["티커", "조항", "이름", "코드", "언론사", "기자"]

    if any(keyword in question for keyword in relation_keywords):
        state["mode"] = RetrievalMode.text2cypher
    elif any(keyword in question for keyword in exact_keywords):
        state["mode"] = RetrievalMode.full_text
    elif request.domain in {"compliance", "finance"}:
        state["mode"] = RetrievalMode.enhanced_graphrag
    else:
        state["mode"] = RetrievalMode.vector
    return state


def retrieve_context(state: GraphRagState) -> GraphRagState:
    request = state["request"]
    ontology = default_ontology(request.domain)
    mode = state["mode"]

    evidence_by_mode = {
        RetrievalMode.vector: [
            "Semantic chunks: 질문 의미와 가까운 문서 청크 3개",
            "Embedding store: bge-m3 또는 OpenAI embedding으로 구성 가능",
        ],
        RetrievalMode.full_text: [
            "Full-text index: 고유명사, 조항명, 티커, 담당자명 exact-ish 검색",
            "Analyzer note: 한국어는 CJK/nori 분석기 검토 필요",
        ],
        RetrievalMode.text2cypher: [
            "Generated Cypher: MATCH 경로 탐색으로 관계 조건 질의",
            (
                f"Ontology schema: {len(ontology.nodes)} nodes, "
                f"{len(ontology.relationships)} relationships"
            ),
        ],
        RetrievalMode.enhanced_graphrag: [
            "Vector candidates: 의미상 관련 문서 후보 검색",
            "Graph expansion: 후보 문서와 연결된 엔티티, 담당 부서, 근거 규칙 확장",
            "Answer grounding: 문서 근거와 그래프 관계를 함께 주입",
        ],
    }
    state["evidence"] = evidence_by_mode[mode]
    return state


def generate_answer(state: GraphRagState) -> GraphRagState:
    request = state["request"]
    mode = state["mode"]
    mode_label = {
        RetrievalMode.vector: "벡터 검색",
        RetrievalMode.full_text: "전문 검색",
        RetrievalMode.text2cypher: "Text2Cypher",
        RetrievalMode.enhanced_graphrag: "Enhanced GraphRAG",
    }[mode]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are the deterministic demo answer writer for Ontology Studio.",
            ),
            (
                "human",
                "Question: {question}\nMode: {mode_label}\nEvidence:\n{evidence}",
            ),
        ]
    )
    demo_writer = RunnableLambda(
        lambda prompt_value: (
            f"'{request.question}' 질문은 {mode_label} 경로가 적합합니다. "
            "Ontology Studio는 먼저 질문 유형을 분류하고, 필요한 근거를 검색한 뒤 "
            "LLM 답변에 그래프 관계와 문서 근거를 함께 넣습니다."
        )
    )
    chain = prompt | demo_writer
    state["answer"] = chain.invoke(
        {
            "question": request.question,
            "mode_label": mode_label,
            "evidence": "\n".join(f"- {item}" for item in state["evidence"]),
        }
    )
    state["next_actions"] = [
        "도메인 온톨로지의 노드와 관계를 검토한다.",
        "Neo4j 제약조건과 인덱스를 만든다.",
        "실제 문서/CSV를 넣어 검색 결과 품질을 평가한다.",
    ]
    return state


def build_graph():
    workflow = StateGraph(GraphRagState)
    workflow.add_node("choose_mode", choose_mode)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("generate_answer", generate_answer)
    workflow.set_entry_point("choose_mode")
    workflow.add_edge("choose_mode", "retrieve_context")
    workflow.add_edge("retrieve_context", "generate_answer")
    workflow.add_edge("generate_answer", END)
    return workflow.compile()


def run_query(request: QueryRequest) -> QueryResponse:
    graph = build_graph()
    state = graph.invoke({"request": request})
    return QueryResponse(
        question=request.question,
        domain=request.domain,
        mode=state["mode"],
        answer=state["answer"],
        evidence=state["evidence"],
        next_actions=state["next_actions"],
    )
