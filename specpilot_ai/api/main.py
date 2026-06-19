from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from specpilot_ai.core.config import get_settings
from specpilot_ai.core.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    Category,
    PriceAlertPlan,
    ProductBrief,
    TraceEvent,
)
from specpilot_ai.graph.neo4j_client import Neo4jRepository
from specpilot_ai.graph.product_graph import pc_purchase_graph_schema
from specpilot_ai.web.launch_page import launch_page_html
from specpilot_ai.workflows.purchase_agent import run_analysis

app = FastAPI(
    title="SpecPilot AI API",
    version="0.1.0",
    description="AI PC and laptop purchase decision agent with LangGraph and LangChain.",
)

_TRACE_CACHE: dict[str, AnalyzeResponse] = {}


@app.get("/", response_class=HTMLResponse)
def launch_page() -> str:
    return launch_page_html()


@app.get("/health")
def health() -> dict[str, str | bool]:
    settings = get_settings()
    repo = Neo4jRepository(settings)
    try:
        neo4j_ready = repo.ping()
    finally:
        repo.close()
    return {
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "neo4j_ready": neo4j_ready,
    }


@app.get("/product/brief", response_model=ProductBrief)
def product_brief() -> ProductBrief:
    return ProductBrief(
        name="SpecPilot AI",
        one_liner=(
            "A PC and laptop buying assistant that compares specs, compatibility, "
            "prices, reviews and upgrade paths."
        ),
        target_users=[
            "컴퓨터 견적을 처음 맞추는 개인 소비자",
            "작업용 장비를 예산 안에서 고르는 프리랜서와 크리에이터",
            "게임/영상편집/개발용 PC 또는 노트북을 고르는 사용자",
            "사무용 PC와 노트북 구매안을 만드는 소규모 사업자",
        ],
        core_workflows=[
            "Intent Parser",
            "Product Collector",
            "Compatibility Checker",
            "Review Analyzer",
            "Price Tracker",
            "Scoring Engine",
            "Verifier",
            "Report Writer",
        ],
        mvp_categories=[Category.desktop_pc, Category.laptop],
        stack=["FastAPI", "LangGraph", "LangChain LCEL", "Neo4j", "LangSmith-ready traces"],
    )


@app.get("/demo/scenarios")
def demo_scenarios() -> dict[str, list[dict[str, object]]]:
    return {
        "scenarios": [
            {
                "name": "영상 편집 + QHD 게이밍 데스크톱",
                "request": {
                    "query": (
                        "영상 편집과 게임용 데스크톱 200만원 안에서 맞춰줘. "
                        "QHD 144Hz 모니터를 쓰고 업그레이드 여지도 있었으면 좋겠어."
                    ),
                    "category": Category.desktop_pc,
                    "budget_krw": 2_000_000,
                    "purpose": "Premiere Pro, DaVinci Resolve, QHD gaming",
                    "must_haves": ["QHD 144Hz", "32GB RAM", "업그레이드 여지"],
                    "exclusions": ["중고", "리퍼", "출처 없는 가격"],
                },
            },
            {
                "name": "크리에이터 노트북",
                "request": {
                    "query": "영상 편집용 노트북 200만원 이하로 비교해줘",
                    "category": Category.laptop,
                    "budget_krw": 2_000_000,
                    "purpose": "Premiere Pro and DaVinci Resolve video editing",
                    "must_haves": ["32GB RAM 선호", "외장 GPU", "휴대성"],
                    "exclusions": ["RAM 8GB", "리퍼"],
                },
            },
        ]
    }


@app.get("/categories")
def categories() -> dict[str, list[str]]:
    return {"mvp_categories": [category.value for category in Category]}


@app.get("/graph/schema")
def graph_schema() -> dict[str, object]:
    settings = get_settings()
    schema = pc_purchase_graph_schema()
    repo = Neo4jRepository(settings)
    try:
        preview = repo.graph_schema_preview(schema)
    finally:
        repo.close()
    return {"schema": schema.model_dump(), "preview": preview}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    response = run_analysis(request)
    _TRACE_CACHE[response.graph_trace_id] = response
    return response


@app.post("/alerts/preview", response_model=list[PriceAlertPlan])
def price_alert_preview(request: AnalyzeRequest) -> list[PriceAlertPlan]:
    response = run_analysis(request)
    _TRACE_CACHE[response.graph_trace_id] = response
    return response.report.price_alerts


@app.get("/traces/{trace_id}", response_model=list[TraceEvent])
def trace_events(trace_id: str) -> list[TraceEvent]:
    response = _TRACE_CACHE.get(trace_id)
    if response is None:
        return []
    return response.trace_events
