from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from specpilot_ai.core.config import get_settings
from specpilot_ai.core.models import (
    AdminReviewDashboard,
    AlertSubscription,
    AlertSubscriptionRequest,
    AnalyzeRequest,
    AnalyzeResponse,
    Category,
    OperationsMetrics,
    PriceAlertPlan,
    ProductBrief,
    ReviewDecision,
    ReviewDecisionRequest,
    ReviewQueueItem,
    ReviewStatus,
    SavedReportDetail,
    SavedReportSummary,
    SaveReportRequest,
    SourceAdapterStatus,
    SourceCollectionRequest,
    SourceCollectionResponse,
    TraceEvent,
)
from specpilot_ai.graph.neo4j_client import Neo4jRepository
from specpilot_ai.graph.product_graph import pc_purchase_graph_schema
from specpilot_ai.sources.collector import SourceCollector
from specpilot_ai.storage.sqlite_store import SpecPilotStore
from specpilot_ai.web.admin_page import admin_page_html
from specpilot_ai.web.launch_page import launch_page_html
from specpilot_ai.workflows.purchase_agent import run_analysis

app = FastAPI(
    title="SpecPilot AI API",
    version="0.1.0",
    description="AI PC and laptop purchase decision agent with LangGraph and LangChain.",
)

_TRACE_CACHE: dict[str, AnalyzeResponse] = {}


def _store() -> SpecPilotStore:
    return SpecPilotStore(get_settings())


def _collector() -> SourceCollector:
    return SourceCollector()


@app.get("/", response_class=HTMLResponse)
def launch_page() -> str:
    return launch_page_html()


@app.get("/admin", response_class=HTMLResponse)
def admin_page() -> str:
    return admin_page_html()


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
        "storage_ready": True,
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
    _store().save_analysis(response)
    return response


@app.post("/alerts/preview", response_model=list[PriceAlertPlan])
def price_alert_preview(request: AnalyzeRequest) -> list[PriceAlertPlan]:
    response = run_analysis(request)
    _TRACE_CACHE[response.graph_trace_id] = response
    _store().save_analysis(response)
    return response.report.price_alerts


@app.get("/traces/{trace_id}", response_model=list[TraceEvent])
def trace_events(trace_id: str) -> list[TraceEvent]:
    response = _TRACE_CACHE.get(trace_id)
    if response is None:
        response = _store().get_analysis(trace_id)
    if response is None:
        raise HTTPException(status_code=404, detail="trace_id를 찾을 수 없습니다.")
    return response.trace_events


@app.post("/reports/save", response_model=SavedReportSummary)
def save_report(request: SaveReportRequest) -> SavedReportSummary:
    response = _TRACE_CACHE.get(request.trace_id) or _store().get_analysis(request.trace_id)
    if response is None:
        raise HTTPException(status_code=404, detail="저장할 분석 결과를 찾을 수 없습니다.")
    title = request.title or _default_report_title(response)
    return _store().save_report(
        response,
        title=title,
        owner_label=request.owner_label,
        notes=request.notes,
    )


@app.get("/reports", response_model=list[SavedReportSummary])
def list_reports(limit: int = 20) -> list[SavedReportSummary]:
    return _store().list_reports(limit=limit)


@app.get("/reports/{report_id}", response_model=SavedReportDetail)
def get_report(report_id: str) -> SavedReportDetail:
    report = _store().get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="저장 리포트를 찾을 수 없습니다.")
    return report


@app.post("/alerts/subscribe", response_model=AlertSubscription)
def subscribe_alert(request: AlertSubscriptionRequest) -> AlertSubscription:
    response = _TRACE_CACHE.get(request.trace_id) or _store().get_analysis(request.trace_id)
    if response is None:
        raise HTTPException(status_code=404, detail="알림을 연결할 분석 결과를 찾을 수 없습니다.")
    try:
        return _store().create_alert_subscription(
            response,
            product_id=request.product_id,
            target_price_krw=request.target_price_krw,
            channels=request.channels,
            contact=request.contact,
            owner_label=request.owner_label,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/alerts/subscriptions", response_model=list[AlertSubscription])
def list_alert_subscriptions(limit: int = 50) -> list[AlertSubscription]:
    return _store().list_alert_subscriptions(limit=limit)


@app.get("/ops/metrics", response_model=OperationsMetrics)
def operations_metrics() -> OperationsMetrics:
    return _store().metrics()


@app.get("/sources/status", response_model=list[SourceAdapterStatus])
def source_adapter_statuses() -> list[SourceAdapterStatus]:
    return _collector().statuses()


@app.post("/sources/collect", response_model=SourceCollectionResponse)
def collect_sources(request: SourceCollectionRequest) -> SourceCollectionResponse:
    response = _collector().collect(request)
    review_items = _collector().build_review_items(response.review_queue)
    _store().add_review_items(review_items)
    return response


@app.get("/admin/reviews", response_model=list[ReviewQueueItem])
def list_admin_reviews(
    status: ReviewStatus | None = ReviewStatus.pending,
    limit: int = 50,
) -> list[ReviewQueueItem]:
    return _store().list_review_items(status=status, limit=limit)


@app.post("/admin/reviews/{review_id}/decision", response_model=ReviewDecision)
def decide_admin_review(
    review_id: str,
    request: ReviewDecisionRequest,
) -> ReviewDecision:
    decision = _store().decide_review(
        review_id,
        status=request.status,
        reviewer=request.reviewer,
        note=request.note,
    )
    if decision is None:
        raise HTTPException(status_code=404, detail="검수 항목을 찾을 수 없습니다.")
    return decision


@app.get("/admin/dashboard", response_model=AdminReviewDashboard)
def admin_dashboard() -> AdminReviewDashboard:
    return AdminReviewDashboard(
        adapter_statuses=_collector().statuses(),
        pending_reviews=_store().list_review_items(status=ReviewStatus.pending, limit=25),
        metrics=_store().metrics(),
    )


def _default_report_title(response: AnalyzeResponse) -> str:
    top = response.report.top_recommendations[0] if response.report.top_recommendations else None
    if top is None:
        return f"{response.criteria.category.value} 구매 분석"
    return f"{top.product.model_name} 중심 구매 리포트"
