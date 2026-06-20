import ipaddress
from datetime import UTC, datetime, timedelta
from urllib.parse import unquote, urlparse
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse

from specpilot_ai.api.auth import workspace_context
from specpilot_ai.core.config import get_settings
from specpilot_ai.core.models import (
    AdminReviewDashboard,
    AlertDeliveryAttempt,
    AlertDeliveryEvent,
    AlertDispatchRequest,
    AlertDispatchResponse,
    AlertEvaluationRequest,
    AlertEvaluationResponse,
    AlertNotificationChannel,
    AlertNotificationChannelRequest,
    AlertSubscription,
    AlertSubscriptionRequest,
    AnalyzeRequest,
    AnalyzeResponse,
    BetaBacklogAction,
    BetaBacklogActionRequest,
    BetaBacklogItem,
    BetaBacklogSummary,
    BetaCohort,
    BetaCohortReport,
    BetaCohortRequest,
    BetaLead,
    BetaLeadRequest,
    BetaReadinessDashboard,
    Category,
    CategoryMarketReport,
    CheckoutReview,
    CheckoutReviewRequest,
    CheckStatus,
    CompletionDeliveryEngagement,
    CompletionDeliveryEngagementRequest,
    CompletionDeliveryProviderEvent,
    CompletionDeliveryProviderWebhookRequest,
    CompletionRecipientGroup,
    CompletionRecipientGroupRequest,
    CompletionReportBatch,
    CompletionReportBatchRequest,
    CompletionReportPreview,
    CompletionReportPreviewRequest,
    CompletionReportTemplate,
    CompletionReportTemplateRequest,
    DataGovernanceDashboard,
    DemoScenarioGallery,
    FeedbackRecord,
    FeedbackRequest,
    GrowthEventRecord,
    GrowthEventRequest,
    GrowthFunnelDashboard,
    IntakeDiagnosisRequest,
    IntakeDiagnosisResponse,
    IntegrationProvider,
    IntegrationProviderRequest,
    IntegrationReadinessDashboard,
    LaunchCampaignKit,
    LaunchDistributionPlan,
    LaunchExperiment,
    LaunchExperimentDashboard,
    LaunchExperimentEvent,
    LaunchExperimentEventRequest,
    LaunchExperimentRequest,
    LaunchGateDashboard,
    LaunchPulseDashboard,
    ObservabilityDispatchRequest,
    ObservabilityDispatchResponse,
    ObservabilityExportRecord,
    ObservabilityExportRequest,
    OperationsMetrics,
    OpsLearningDashboard,
    OpsRegressionDashboard,
    PriceAlertPlan,
    PricingDashboard,
    PricingPlan,
    PrivacyPolicySummary,
    ProductBrief,
    PublicAcquisitionHub,
    PublicCategoryMarketReport,
    PublicConversionBoard,
    PublicLaunchRoom,
    PublicLaunchRoomCard,
    PublicLaunchRoomMarketLink,
    PublicProofHub,
    PublicReferralLeaderboard,
    PublicReport,
    PurchaseDecisionBoard,
    PurchaseLink,
    PurchaseLinkGovernance,
    PurchaseLinkRequest,
    PurchaseOnboardingPlaybook,
    PurchaseOutcome,
    PurchaseOutcomeRequest,
    PurchaseStartConcierge,
    QualityDashboard,
    ReferralRewardProgress,
    ReferralShareKit,
    ReportAdvisorAnswer,
    ReportAdvisorQuestionRequest,
    ReportShare,
    ReportShareAssets,
    RetentionHubDashboard,
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
    SourceMonitor,
    SourceMonitorRequest,
    SourceProviderCheckRequest,
    SourceProviderFetchLog,
    SourceProviderGate,
    SourceProviderPolicy,
    SourceProviderPolicyRequest,
    SourceRefreshRequest,
    SourceRefreshResponse,
    SourceRefreshRun,
    SourceScheduleItem,
    SourceSchedulePreview,
    SourceUrlIngestRequest,
    SourceUrlIngestResponse,
    SubscriptionIntent,
    SubscriptionIntentRequest,
    TraceEvent,
    TraceRunSummary,
    TraceSpanRecord,
    TrustCenterDashboard,
    TrustPolicySummary,
    WaitlistReferral,
    WaitlistReferralDashboard,
    WaitlistReferralRequest,
    WorkspaceContext,
)
from specpilot_ai.graph.neo4j_client import Neo4jRepository
from specpilot_ai.graph.product_graph import pc_purchase_graph_schema
from specpilot_ai.services.demo_gallery import build_demo_scenario_gallery
from specpilot_ai.services.intake import diagnose_intake
from specpilot_ai.services.launch_campaign import (
    build_launch_campaign_kit,
    build_launch_distribution_plan,
)
from specpilot_ai.services.market import build_category_market_report
from specpilot_ai.services.onboarding import purchase_onboarding_playbooks
from specpilot_ai.services.start_concierge import build_start_concierge
from specpilot_ai.services.trust import build_privacy_policy, build_trust_center, build_trust_policy
from specpilot_ai.sources.collector import SourceCollector
from specpilot_ai.sources.url_ingestion import ingest_source_url
from specpilot_ai.storage.sqlite_store import SpecPilotStore, pricing_plans
from specpilot_ai.web.admin_page import admin_page_html
from specpilot_ai.web.launch_page import launch_page_html
from specpilot_ai.web.public_report_page import public_report_html
from specpilot_ai.workflows.purchase_agent import run_analysis

app = FastAPI(
    title="SpecPilot AI API",
    version="0.1.0",
    description="AI PC and laptop purchase decision agent with LangGraph and LangChain.",
)

WORKSPACE_DEPENDENCY = Depends(workspace_context)
_TRACE_CACHE: dict[tuple[str, str], AnalyzeResponse] = {}
_TRACKING_PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


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
def health() -> dict[str, object]:
    settings = get_settings()
    repo = Neo4jRepository(settings)
    try:
        neo4j_ready = repo.ping()
    finally:
        repo.close()
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "app_version": settings.app_version,
        "demo_mode": settings.demo_mode,
        "neo4j_ready": neo4j_ready,
        "storage_ready": True,
        "storage_path": settings.storage_path,
        "source_adapters": len(_collector().statuses()),
    }


@app.get("/ready")
def ready() -> dict[str, object]:
    settings = get_settings()
    store = _store()
    metrics = store.metrics()
    adapter_statuses = _collector().statuses()
    return {
        "ready": True,
        "app_env": settings.app_env,
        "storage_ready": True,
        "source_adapters_ready": all(adapter.enabled for adapter in adapter_statuses),
        "analysis_runs": metrics.analysis_runs,
        "pending_reviews": len(_store().list_review_items(limit=100)),
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


@app.get("/policy/trust", response_model=TrustPolicySummary)
def trust_policy() -> TrustPolicySummary:
    return build_trust_policy()


@app.get("/policy/privacy", response_model=PrivacyPolicySummary)
def privacy_policy() -> PrivacyPolicySummary:
    return build_privacy_policy()


@app.get("/policy/trust-center", response_model=TrustCenterDashboard)
def trust_center() -> TrustCenterDashboard:
    return build_trust_center()


@app.get("/demo/scenarios", response_model=DemoScenarioGallery)
def demo_scenarios() -> DemoScenarioGallery:
    return build_demo_scenario_gallery()


@app.get("/categories")
def categories() -> dict[str, list[str]]:
    return {"mvp_categories": [category.value for category in Category]}


@app.post("/intake/diagnose", response_model=IntakeDiagnosisResponse)
def intake_diagnosis(request: IntakeDiagnosisRequest) -> IntakeDiagnosisResponse:
    return diagnose_intake(request)


@app.post("/public/start-concierge", response_model=PurchaseStartConcierge)
def public_start_concierge(
    request: IntakeDiagnosisRequest,
) -> PurchaseStartConcierge:
    return build_start_concierge(request)


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
def analyze(
    request: AnalyzeRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> AnalyzeResponse:
    response = run_analysis(request)
    _TRACE_CACHE[(workspace.workspace_id, response.graph_trace_id)] = response
    _store().save_analysis_for_workspace(workspace.workspace_id, response)
    return response


@app.post("/alerts/preview", response_model=list[PriceAlertPlan])
def price_alert_preview(
    request: AnalyzeRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[PriceAlertPlan]:
    response = run_analysis(request)
    _TRACE_CACHE[(workspace.workspace_id, response.graph_trace_id)] = response
    _store().save_analysis_for_workspace(workspace.workspace_id, response)
    return response.report.price_alerts


@app.get("/traces/{trace_id}", response_model=list[TraceEvent])
def trace_events(
    trace_id: str,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[TraceEvent]:
    response = _TRACE_CACHE.get((workspace.workspace_id, trace_id))
    if response is None:
        response = _store().get_analysis_for_workspace(workspace.workspace_id, trace_id)
    if response is None:
        raise HTTPException(status_code=404, detail="trace_id를 찾을 수 없습니다.")
    return response.trace_events


@app.post("/reports/save", response_model=SavedReportSummary)
def save_report(
    request: SaveReportRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> SavedReportSummary:
    response = _TRACE_CACHE.get(
        (workspace.workspace_id, request.trace_id)
    ) or _store().get_analysis_for_workspace(
        workspace.workspace_id,
        request.trace_id,
    )
    if response is None:
        raise HTTPException(status_code=404, detail="저장할 분석 결과를 찾을 수 없습니다.")
    title = request.title or _default_report_title(response)
    owner_label = request.owner_label if request.owner_label != "guest" else workspace.owner_label
    return _store().save_report_for_workspace(
        workspace.workspace_id,
        response,
        title=title,
        owner_label=owner_label,
        notes=request.notes,
    )


@app.get("/reports", response_model=list[SavedReportSummary])
def list_reports(
    limit: int = 20,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[SavedReportSummary]:
    return _store().list_reports_for_workspace(workspace.workspace_id, limit=limit)


@app.get("/reports/decision-board", response_model=PurchaseDecisionBoard)
def report_decision_board(
    limit: int = 20,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> PurchaseDecisionBoard:
    return _store().purchase_decision_board_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.post("/reports/completion-templates", response_model=CompletionReportTemplate)
def upsert_completion_template(
    request: CompletionReportTemplateRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> CompletionReportTemplate:
    return _store().upsert_completion_report_template_for_workspace(
        workspace.workspace_id,
        request,
    )


@app.get("/reports/completion-templates", response_model=list[CompletionReportTemplate])
def list_completion_templates(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[CompletionReportTemplate]:
    return _store().list_completion_report_templates_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.post("/reports/completion-recipient-groups", response_model=CompletionRecipientGroup)
def upsert_completion_recipient_group(
    request: CompletionRecipientGroupRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> CompletionRecipientGroup:
    return _store().upsert_completion_recipient_group_for_workspace(
        workspace.workspace_id,
        request,
    )


@app.get(
    "/reports/completion-recipient-groups",
    response_model=list[CompletionRecipientGroup],
)
def list_completion_recipient_groups(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[CompletionRecipientGroup]:
    return _store().list_completion_recipient_groups_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.post("/reports/completion-preview", response_model=CompletionReportPreview)
def preview_completion_report(
    request: CompletionReportPreviewRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> CompletionReportPreview:
    preview = _store().preview_completion_report_for_workspace(
        workspace.workspace_id,
        request,
    )
    if preview is None:
        raise HTTPException(status_code=404, detail="미리보기할 저장 리포트를 찾을 수 없습니다.")
    return preview


@app.post("/reports/completion-batches", response_model=CompletionReportBatch)
def create_completion_report_batch(
    request: CompletionReportBatchRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> CompletionReportBatch:
    return _store().create_completion_report_batch_for_workspace(
        workspace.workspace_id,
        request,
    )


@app.get("/reports/completion-batches", response_model=list[CompletionReportBatch])
def list_completion_report_batches(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[CompletionReportBatch]:
    return _store().list_completion_report_batches_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.post(
    "/reports/completion-deliveries/{delivery_id}/engagement",
    response_model=CompletionDeliveryEngagement,
)
def record_completion_delivery_engagement(
    delivery_id: str,
    request: CompletionDeliveryEngagementRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> CompletionDeliveryEngagement:
    engagement = _store().record_completion_delivery_engagement_for_workspace(
        workspace.workspace_id,
        delivery_id,
        request,
    )
    if engagement is None:
        raise HTTPException(
            status_code=404,
            detail="engagement를 기록할 delivery를 찾을 수 없습니다.",
        )
    return engagement


@app.get(
    "/reports/completion-engagement",
    response_model=list[CompletionDeliveryEngagement],
)
def list_completion_delivery_engagement(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[CompletionDeliveryEngagement]:
    return _store().list_completion_delivery_engagement_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.post(
    "/reports/completion-deliveries/provider-webhooks",
    response_model=CompletionDeliveryProviderEvent,
)
def record_completion_delivery_provider_webhook(
    request: CompletionDeliveryProviderWebhookRequest,
    x_specpilot_webhook_secret: str | None = Header(default=None),
) -> CompletionDeliveryProviderEvent:
    if x_specpilot_webhook_secret != get_settings().completion_webhook_secret:
        raise HTTPException(
            status_code=401,
            detail="completion webhook secret이 올바르지 않습니다.",
        )
    event = _store().record_completion_delivery_provider_event(request)
    if event is None:
        raise HTTPException(
            status_code=404,
            detail="webhook을 연결할 completion delivery가 없습니다.",
        )
    return event


@app.get(
    "/reports/completion-provider-events",
    response_model=list[CompletionDeliveryProviderEvent],
)
def list_completion_delivery_provider_events(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[CompletionDeliveryProviderEvent]:
    return _store().list_completion_delivery_provider_events_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.get("/t/o/{tracking_token}.png")
def completion_tracking_pixel(tracking_token: str, request: Request) -> Response:
    _store().record_completion_delivery_engagement_by_tracking_token(
        tracking_token,
        "open",
        _tracking_metadata(request, "pixel"),
    )
    return Response(
        content=_TRACKING_PIXEL_PNG,
        media_type="image/png",
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
        },
    )


@app.get("/t/c/{tracking_token}")
def completion_tracking_click(
    tracking_token: str,
    request: Request,
    to: str = "/",
) -> RedirectResponse:
    destination = _safe_tracking_redirect_path(to)
    _store().record_completion_delivery_engagement_by_tracking_token(
        tracking_token,
        "click",
        _tracking_metadata(request, "redirect", destination=destination),
    )
    return RedirectResponse(destination, status_code=302)


@app.get("/reports/{report_id}", response_model=SavedReportDetail)
def get_report(
    report_id: str,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> SavedReportDetail:
    report = _store().get_report_for_workspace(workspace.workspace_id, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="저장 리포트를 찾을 수 없습니다.")
    return report


@app.post(
    "/reports/{report_id}/advisor-questions",
    response_model=ReportAdvisorAnswer,
)
def create_report_advisor_answer(
    report_id: str,
    request: ReportAdvisorQuestionRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> ReportAdvisorAnswer:
    answer = _store().create_report_advisor_answer_for_workspace(
        workspace.workspace_id,
        report_id,
        request,
    )
    if answer is None:
        raise HTTPException(
            status_code=404,
            detail="상담 답변을 만들 저장 리포트를 찾을 수 없습니다.",
        )
    return answer


@app.get(
    "/reports/{report_id}/advisor-questions",
    response_model=list[ReportAdvisorAnswer],
)
def list_report_advisor_answers(
    report_id: str,
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[ReportAdvisorAnswer]:
    report = _store().get_report_for_workspace(workspace.workspace_id, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="상담 답변을 조회할 저장 리포트를 찾을 수 없습니다.",
        )
    return _store().list_report_advisor_answers_for_workspace(
        workspace.workspace_id,
        report_id=report_id,
        limit=limit,
    )


@app.get("/advisor-questions", response_model=list[ReportAdvisorAnswer])
def list_workspace_report_advisor_answers(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[ReportAdvisorAnswer]:
    return _store().list_report_advisor_answers_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.post("/reports/{report_id}/checkout-review", response_model=CheckoutReview)
def create_checkout_review(
    report_id: str,
    request: CheckoutReviewRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> CheckoutReview:
    review = _store().create_checkout_review_for_workspace(
        workspace.workspace_id,
        report_id,
        request,
    )
    if review is None:
        raise HTTPException(
            status_code=404,
            detail="checkout review를 만들 리포트를 찾을 수 없습니다.",
        )
    return review


@app.get("/reports/{report_id}/checkout-reviews", response_model=list[CheckoutReview])
def list_report_checkout_reviews(
    report_id: str,
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[CheckoutReview]:
    report = _store().get_report_for_workspace(workspace.workspace_id, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="checkout review를 조회할 리포트를 찾을 수 없습니다.",
        )
    return _store().list_checkout_reviews_for_workspace(
        workspace.workspace_id,
        report_id=report_id,
        limit=limit,
    )


@app.get("/checkout-reviews", response_model=list[CheckoutReview])
def list_checkout_reviews(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[CheckoutReview]:
    return _store().list_checkout_reviews_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.post("/reports/{report_id}/purchase-outcomes", response_model=PurchaseOutcome)
def create_purchase_outcome(
    report_id: str,
    request: PurchaseOutcomeRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> PurchaseOutcome:
    outcome = _store().create_purchase_outcome_for_workspace(
        workspace.workspace_id,
        report_id,
        request,
    )
    if outcome is None:
        raise HTTPException(
            status_code=404,
            detail="purchase outcome을 만들 리포트 또는 후보를 찾을 수 없습니다.",
        )
    return outcome


@app.get("/reports/{report_id}/purchase-outcomes", response_model=list[PurchaseOutcome])
def list_report_purchase_outcomes(
    report_id: str,
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[PurchaseOutcome]:
    report = _store().get_report_for_workspace(workspace.workspace_id, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="purchase outcome을 조회할 리포트를 찾을 수 없습니다.",
        )
    return _store().list_purchase_outcomes_for_workspace(
        workspace.workspace_id,
        report_id=report_id,
        limit=limit,
    )


@app.get("/purchase-outcomes", response_model=list[PurchaseOutcome])
def list_purchase_outcomes(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[PurchaseOutcome]:
    return _store().list_purchase_outcomes_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.post("/reports/{report_id}/purchase-links", response_model=PurchaseLink)
def create_purchase_link(
    report_id: str,
    request: PurchaseLinkRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> PurchaseLink:
    _validate_public_purchase_url(request.url)
    link = _store().create_purchase_link_for_workspace(
        workspace.workspace_id,
        report_id,
        request,
    )
    if link is None:
        raise HTTPException(
            status_code=404,
            detail="purchase link를 만들 리포트 또는 후보를 찾을 수 없습니다.",
        )
    return link


@app.get("/reports/{report_id}/purchase-links", response_model=list[PurchaseLink])
def list_report_purchase_links(
    report_id: str,
    active_only: bool = False,
    limit: int = 100,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[PurchaseLink]:
    report = _store().get_report_for_workspace(workspace.workspace_id, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="purchase link를 조회할 리포트를 찾을 수 없습니다.",
        )
    return _store().list_purchase_links_for_workspace(
        workspace.workspace_id,
        report_id,
        active_only=active_only,
        limit=limit,
    )


@app.get(
    "/reports/{report_id}/purchase-link-governance",
    response_model=PurchaseLinkGovernance,
)
def report_purchase_link_governance(
    report_id: str,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> PurchaseLinkGovernance:
    governance = _store().purchase_link_governance_for_workspace(
        workspace.workspace_id,
        report_id,
    )
    if governance is None:
        raise HTTPException(
            status_code=404,
            detail="purchase link governance를 조회할 리포트를 찾을 수 없습니다.",
        )
    return governance


@app.post("/reports/{report_id}/share", response_model=ReportShare)
def share_report(
    report_id: str,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> ReportShare:
    share = _store().share_report_for_workspace(workspace.workspace_id, report_id)
    if share is None:
        raise HTTPException(status_code=404, detail="공유할 리포트를 찾을 수 없습니다.")
    return share


@app.get("/reports/{report_id}/share-assets", response_model=ReportShareAssets)
def report_share_assets(
    report_id: str,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> ReportShareAssets:
    assets = _store().share_assets_for_workspace(workspace.workspace_id, report_id)
    if assets is None:
        raise HTTPException(
            status_code=404,
            detail="공유 자산을 만들 저장 리포트를 찾을 수 없습니다.",
        )
    return assets


@app.delete("/reports/{report_id}/share", response_model=ReportShare)
def revoke_report_share(
    report_id: str,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> ReportShare:
    share = _store().revoke_report_share_for_workspace(workspace.workspace_id, report_id)
    if share is None:
        raise HTTPException(status_code=404, detail="공유를 해제할 리포트를 찾을 수 없습니다.")
    return share


@app.get("/public/reports/{share_token}", response_model=PublicReport)
def get_public_report(share_token: str) -> PublicReport:
    report = _store().get_public_report(share_token)
    if report is None:
        raise HTTPException(status_code=404, detail="공개 리포트를 찾을 수 없습니다.")
    return report


@app.get("/r/{share_token}", response_class=HTMLResponse)
def public_report_page(share_token: str) -> str:
    report = _store().get_public_report(share_token)
    if report is None:
        raise HTTPException(status_code=404, detail="공개 리포트를 찾을 수 없습니다.")
    return public_report_html(report)


@app.get("/buy/{link_id}")
def purchase_link_redirect(link_id: str, request: Request) -> RedirectResponse:
    click = _store().record_purchase_link_click(
        link_id,
        source=request.query_params.get("source", "public_report"),
        referrer_host=_referrer_host(request.headers.get("referer")),
        user_agent_family=_user_agent_family(request.headers.get("user-agent")),
    )
    if click is None:
        raise HTTPException(status_code=404, detail="구매 링크를 찾을 수 없습니다.")
    _, destination = click
    return RedirectResponse(destination, status_code=302)


@app.post("/alerts/subscribe", response_model=AlertSubscription)
def subscribe_alert(
    request: AlertSubscriptionRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> AlertSubscription:
    response = _TRACE_CACHE.get(
        (workspace.workspace_id, request.trace_id)
    ) or _store().get_analysis_for_workspace(
        workspace.workspace_id,
        request.trace_id,
    )
    if response is None:
        raise HTTPException(status_code=404, detail="알림을 연결할 분석 결과를 찾을 수 없습니다.")
    owner_label = request.owner_label if request.owner_label != "guest" else workspace.owner_label
    try:
        return _store().create_alert_subscription_for_workspace(
            workspace.workspace_id,
            response,
            product_id=request.product_id,
            target_price_krw=request.target_price_krw,
            channels=request.channels,
            contact=request.contact,
            owner_label=owner_label,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/alerts/subscriptions", response_model=list[AlertSubscription])
def list_alert_subscriptions(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[AlertSubscription]:
    return _store().list_alert_subscriptions_for_workspace(workspace.workspace_id, limit=limit)


@app.post("/alerts/evaluate", response_model=AlertEvaluationResponse)
def evaluate_alerts(
    request: AlertEvaluationRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> AlertEvaluationResponse:
    return _store().evaluate_alerts_for_workspace(
        workspace.workspace_id,
        price_overrides_krw=request.price_overrides_krw,
        dry_run=request.dry_run,
        limit=request.limit,
    )


@app.get("/alerts/events", response_model=list[AlertDeliveryEvent])
def list_alert_events(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[AlertDeliveryEvent]:
    return _store().list_alert_events_for_workspace(workspace.workspace_id, limit=limit)


@app.post("/alerts/channels", response_model=AlertNotificationChannel)
def upsert_alert_channel(
    request: AlertNotificationChannelRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> AlertNotificationChannel:
    try:
        return _store().upsert_alert_channel_for_workspace(workspace.workspace_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/alerts/channels", response_model=list[AlertNotificationChannel])
def list_alert_channels(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[AlertNotificationChannel]:
    return _store().list_alert_channels_for_workspace(workspace.workspace_id, limit=limit)


@app.post("/alerts/dispatch", response_model=AlertDispatchResponse)
def dispatch_alerts(
    request: AlertDispatchRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> AlertDispatchResponse:
    return _store().dispatch_alert_events_for_workspace(
        workspace.workspace_id,
        event_ids=request.event_ids,
        dry_run=request.dry_run,
        limit=request.limit,
    )


@app.get("/alerts/deliveries", response_model=list[AlertDeliveryAttempt])
def list_alert_deliveries(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[AlertDeliveryAttempt]:
    return _store().list_alert_delivery_attempts_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.get("/ops/metrics", response_model=OperationsMetrics)
def operations_metrics(
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> OperationsMetrics:
    return _store().metrics_for_workspace(workspace.workspace_id)


@app.get("/ops/data-governance", response_model=DataGovernanceDashboard)
def data_governance(
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> DataGovernanceDashboard:
    return _store().data_governance_for_workspace(workspace.workspace_id)


@app.get("/ops/quality", response_model=QualityDashboard)
def quality_dashboard(
    limit: int = 20,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> QualityDashboard:
    return _store().quality_dashboard_for_workspace(workspace.workspace_id, limit=limit)


@app.get("/ops/regression", response_model=OpsRegressionDashboard)
def ops_regression_dashboard(
    window_size: int = 5,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> OpsRegressionDashboard:
    return _store().ops_regression_for_workspace(
        workspace.workspace_id,
        window_size=window_size,
    )


@app.get("/ops/learning-insights", response_model=OpsLearningDashboard)
def ops_learning_insights(
    limit: int = 20,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> OpsLearningDashboard:
    return _store().learning_insights_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.get("/ops/traces", response_model=list[TraceRunSummary])
def list_trace_runs(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[TraceRunSummary]:
    return _store().list_trace_runs_for_workspace(workspace.workspace_id, limit=limit)


@app.get("/ops/traces/{trace_id}/spans", response_model=list[TraceSpanRecord])
def list_trace_spans(
    trace_id: str,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[TraceSpanRecord]:
    spans = _store().list_trace_spans_for_workspace(workspace.workspace_id, trace_id)
    if not spans:
        raise HTTPException(status_code=404, detail="trace span을 찾을 수 없습니다.")
    return spans


@app.post("/ops/observability/exports", response_model=ObservabilityExportRecord)
def create_observability_export(
    request: ObservabilityExportRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> ObservabilityExportRecord:
    export = _store().create_observability_export_for_workspace(
        workspace.workspace_id,
        request,
    )
    if export is None:
        raise HTTPException(status_code=404, detail="export할 trace를 찾을 수 없습니다.")
    return export


@app.get("/ops/observability/exports", response_model=list[ObservabilityExportRecord])
def list_observability_exports(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[ObservabilityExportRecord]:
    return _store().list_observability_exports_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.post("/ops/observability/dispatch", response_model=ObservabilityDispatchResponse)
def dispatch_observability_exports(
    request: ObservabilityDispatchRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> ObservabilityDispatchResponse:
    return _store().dispatch_observability_exports_for_workspace(
        workspace.workspace_id,
        export_ids=request.export_ids,
        dry_run=request.dry_run,
        limit=request.limit,
    )


@app.get("/me", response_model=WorkspaceContext)
def me(workspace: WorkspaceContext = WORKSPACE_DEPENDENCY) -> WorkspaceContext:
    return workspace


@app.get("/pricing/plans", response_model=list[PricingPlan])
def list_pricing_plans() -> list[PricingPlan]:
    return pricing_plans()


@app.get(
    "/public/onboarding/playbooks",
    response_model=list[PurchaseOnboardingPlaybook],
)
def public_onboarding_playbooks(
    category: Category | None = None,
) -> list[PurchaseOnboardingPlaybook]:
    return purchase_onboarding_playbooks(category=category)


@app.get("/public/proof-hub", response_model=PublicProofHub)
def public_proof_hub(
    limit: int = 8,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> PublicProofHub:
    return _store().public_proof_hub_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.get("/public/launch-room", response_model=PublicLaunchRoom)
def public_launch_room(
    limit: int = 8,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> PublicLaunchRoom:
    store = _store()
    demos = build_demo_scenario_gallery()
    launch_kit = build_launch_campaign_kit()
    proof = store.public_proof_hub_for_workspace(workspace.workspace_id, limit=limit)
    acquisition = store.public_acquisition_hub_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )
    pulse = store.launch_pulse_for_workspace(workspace.workspace_id, limit=limit)
    referrals = store.waitlist_referral_dashboard_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )
    pricing = store.pricing_dashboard_for_workspace(workspace.workspace_id)
    desktop_report = build_category_market_report(
        workspace_id="public-launch-room",
        metrics=store.metrics_for_workspace(workspace.workspace_id),
        category_filter=Category.desktop_pc,
    )
    laptop_report = build_category_market_report(
        workspace_id="public-launch-room",
        metrics=store.metrics_for_workspace(workspace.workspace_id),
        category_filter=Category.laptop,
    )
    launch_score = round(
        (proof.proof_score + acquisition.launch_score + pulse.pulse_score) / 3,
        1,
    )
    status = _score_status_for_public_room(launch_score)
    lead_demo = demos.scenarios[0]
    headline = "컴퓨터와 노트북 구매 실패를 줄이는 공개 AI 구매 리포트"
    hero_message = (
        "예산과 용도를 넣으면 TOP 3 추천, 제외 후보, 가격 타이밍, "
        "공유 검토, 결제 전 체크까지 한 번에 이어집니다."
    )
    return PublicLaunchRoom(
        workspace_id=workspace.workspace_id,
        generated_at=datetime.now(UTC).isoformat(),
        status=status,
        launch_score=launch_score,
        headline=headline,
        hero_message=hero_message,
        share_title="SpecPilot AI 공개 런칭룸",
        share_text=(
            "최저가 링크가 아니라 가격, 호환성, 리뷰 리스크, 구매 타이밍, "
            "결제 전 검수를 함께 보는 PC/노트북 구매 AI입니다."
        ),
        primary_cta=lead_demo.demo_cta,
        primary_cta_path="/#analysis",
        proof_strip=proof.hero_proof_strip,
        demo_cards=[
            PublicLaunchRoomCard(
                key=scenario.scenario_id,
                title=scenario.title,
                status=CheckStatus.ok,
                metric=scenario.expected_outcome,
                body=scenario.one_liner,
                cta_label=scenario.demo_cta,
                cta_path="/#analysis",
            )
            for scenario in demos.scenarios
        ],
        launch_cards=[
            PublicLaunchRoomCard(
                key="proof_hub",
                title="공개 검증 허브",
                status=proof.status,
                metric=f"{round(proof.proof_score)}점",
                body=proof.summary,
                cta_label="검증 허브 보기",
                cta_path="/#proof-hub",
            ),
            PublicLaunchRoomCard(
                key="acquisition_hub",
                title="공개 유입 허브",
                status=acquisition.status,
                metric=f"{round(acquisition.launch_score)}점",
                body=acquisition.summary,
                cta_label=acquisition.primary_cta,
                cta_path=acquisition.primary_cta_path,
            ),
            PublicLaunchRoomCard(
                key="launch_pulse",
                title="런치 반응 Pulse",
                status=pulse.status,
                metric=f"{round(pulse.pulse_score)}점",
                body=pulse.summary,
                cta_label="반응 Pulse 보기",
                cta_path="/#launch-pulse",
            ),
            PublicLaunchRoomCard(
                key="referral_waitlist",
                title="추천 대기열",
                status=_count_status(referrals.total_referrals, warning=1, ok=5),
                metric=(
                    f"{referrals.total_referrals}명 대기 / "
                    f"추천 {referrals.referred_signup_count}명"
                ),
                body=referrals.summary,
                cta_label="초대 링크 만들기",
                cta_path="/#referrals",
            ),
            PublicLaunchRoomCard(
                key="pricing_interest",
                title="수익화 관심",
                status=pricing.readiness_status,
                metric=f"예상 MRR {pricing.estimated_mrr_krw:,}원",
                body=pricing.summary,
                cta_label="요금제 관심 등록",
                cta_path="/#pricing-ops",
            ),
        ],
        market_links=[
            _launch_room_market_link(Category.desktop_pc, desktop_report),
            _launch_room_market_link(Category.laptop, laptop_report),
        ],
        secondary_ctas=[
            launch_kit.primary_cta,
            "공개 리포트로 구매 검토 받기",
            "추천 대기열 초대 링크 만들기",
            "Trust Center에서 추천 기준 확인하기",
        ],
        channel_posts=[
            variant.body
            for playbook in launch_kit.channel_playbooks
            for variant in playbook.copy_variants[:1]
        ][:3],
        next_actions=list(
            dict.fromkeys(
                [
                    *proof.next_actions[:2],
                    *acquisition.next_actions[:2],
                    *pulse.top_actions[:2],
                ],
            ),
        )[:6],
    )


@app.get("/market/category-reports", response_model=CategoryMarketReport)
def category_market_report(
    category: Category | None = None,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> CategoryMarketReport:
    return build_category_market_report(
        workspace_id=workspace.workspace_id,
        metrics=_store().metrics_for_workspace(workspace.workspace_id),
        category_filter=category,
    )


@app.get(
    "/public/market/category-reports/{category}",
    response_model=PublicCategoryMarketReport,
)
def public_category_market_report(category: Category) -> PublicCategoryMarketReport:
    report = build_category_market_report(
        workspace_id="public-market",
        metrics=_store().metrics_for_workspace("demo"),
        category_filter=category,
    )
    slug = "desktop-pc" if category == Category.desktop_pc else "laptop"
    category_label = "데스크톱 PC" if category == Category.desktop_pc else "노트북"
    title = f"{report.report_month} {category_label} 구매 리포트"
    description = (
        f"SpecPilot AI가 {category_label} 후보를 가격대, 추천 역할, "
        "리스크, 구매 타이밍 기준으로 정리한 공개 월간 리포트입니다."
    )
    return PublicCategoryMarketReport(
        category=category,
        slug=slug,
        canonical_path=f"/market/{slug}",
        title=title,
        description=description,
        share_text=f"{title} - 추천 픽과 가격/리스크 체크포인트를 확인하세요.",
        seo_keywords=[
            category_label,
            "컴퓨터 구매",
            "노트북 구매",
            "구매 리포트",
            "가격 비교",
            "SpecPilot AI",
        ],
        cta_cards=[
            "내 예산과 용도에 맞춰 바로 분석하기",
            "가격 알림으로 목표가 도달 시점 잡기",
            "공개 리포트로 가족/동료와 검토하기",
        ],
        report=report,
    )


@app.post("/billing/subscription-intents", response_model=SubscriptionIntent)
def create_subscription_intent(
    request: SubscriptionIntentRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> SubscriptionIntent:
    intent = _store().create_subscription_intent_for_workspace(
        workspace.workspace_id,
        request,
    )
    if intent is None:
        raise HTTPException(status_code=404, detail="요금제를 찾을 수 없습니다.")
    return intent


@app.get("/billing/subscription-intents", response_model=list[SubscriptionIntent])
def list_subscription_intents(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[SubscriptionIntent]:
    return _store().list_subscription_intents_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.get("/ops/pricing-dashboard", response_model=PricingDashboard)
def pricing_dashboard(
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> PricingDashboard:
    return _store().pricing_dashboard_for_workspace(workspace.workspace_id)


@app.post("/feedback", response_model=FeedbackRecord)
def create_feedback(
    request: FeedbackRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> FeedbackRecord:
    response = _TRACE_CACHE.get(
        (workspace.workspace_id, request.trace_id)
    ) or _store().get_analysis_for_workspace(
        workspace.workspace_id,
        request.trace_id,
    )
    if response is None:
        raise HTTPException(status_code=404, detail="피드백을 연결할 분석 결과를 찾을 수 없습니다.")
    return _store().create_feedback_for_workspace(workspace.workspace_id, request)


@app.get("/feedback", response_model=list[FeedbackRecord])
def list_feedback(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[FeedbackRecord]:
    return _store().list_feedback_for_workspace(workspace.workspace_id, limit=limit)


@app.post("/growth/events", response_model=GrowthEventRecord)
def create_growth_event(
    request: GrowthEventRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> GrowthEventRecord:
    return _store().create_growth_event_for_workspace(workspace.workspace_id, request)


@app.get("/growth/events", response_model=list[GrowthEventRecord])
def list_growth_events(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[GrowthEventRecord]:
    return _store().list_growth_events_for_workspace(workspace.workspace_id, limit=limit)


@app.get("/growth/funnel", response_model=GrowthFunnelDashboard)
def growth_funnel(
    limit: int = 20,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> GrowthFunnelDashboard:
    return _store().growth_funnel_for_workspace(workspace.workspace_id, limit=limit)


@app.post("/beta/leads", response_model=BetaLead)
def create_beta_lead(
    request: BetaLeadRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> BetaLead:
    return _store().create_beta_lead_for_workspace(workspace.workspace_id, request)


@app.get("/beta/leads", response_model=list[BetaLead])
def list_beta_leads(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[BetaLead]:
    return _store().list_beta_leads_for_workspace(workspace.workspace_id, limit=limit)


@app.post("/growth/waitlist-referrals", response_model=WaitlistReferral)
def create_waitlist_referral(
    request: WaitlistReferralRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> WaitlistReferral:
    return _store().create_waitlist_referral_for_workspace(
        workspace.workspace_id,
        request,
    )


@app.get("/growth/waitlist-referrals", response_model=list[WaitlistReferral])
def list_waitlist_referrals(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[WaitlistReferral]:
    return _store().list_waitlist_referrals_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.get("/growth/referral-dashboard", response_model=WaitlistReferralDashboard)
def waitlist_referral_dashboard(
    limit: int = 20,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> WaitlistReferralDashboard:
    return _store().waitlist_referral_dashboard_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.get("/growth/referral-leaderboard", response_model=PublicReferralLeaderboard)
def referral_leaderboard(
    referral_code: str = "",
    limit: int = 10,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> PublicReferralLeaderboard:
    return _store().public_referral_leaderboard_for_workspace(
        workspace.workspace_id,
        referral_code=referral_code,
        limit=limit,
    )


@app.get("/growth/referral-share-kit/{referral_code}", response_model=ReferralShareKit)
def referral_share_kit(
    referral_code: str,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> ReferralShareKit:
    kit = _store().referral_share_kit_for_workspace(
        workspace.workspace_id,
        referral_code,
    )
    if kit is None:
        raise HTTPException(status_code=404, detail="Referral code not found")
    return kit


@app.get(
    "/growth/referral-rewards/{referral_code}",
    response_model=ReferralRewardProgress,
)
def referral_rewards(
    referral_code: str,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> ReferralRewardProgress:
    progress = _store().referral_reward_progress_for_workspace(
        workspace.workspace_id,
        referral_code,
    )
    if progress is None:
        raise HTTPException(status_code=404, detail="Referral code not found")
    return progress


@app.get("/growth/launch-kit", response_model=LaunchCampaignKit)
def growth_launch_kit(
    category: Category | None = None,
    audience: str = "creator",
) -> LaunchCampaignKit:
    return build_launch_campaign_kit(category=category, audience=audience)


@app.get("/growth/launch-distribution-plan", response_model=LaunchDistributionPlan)
def growth_launch_distribution_plan(
    category: Category | None = None,
    audience: str = "creator",
    limit: int = 12,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> LaunchDistributionPlan:
    store = _store()
    kit = build_launch_campaign_kit(category=category, audience=audience)
    board = store.public_conversion_board_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )
    pulse = store.launch_pulse_for_workspace(workspace.workspace_id, limit=limit)
    experiments = store.launch_experiment_dashboard_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )
    referrals = store.waitlist_referral_dashboard_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )
    return build_launch_distribution_plan(
        workspace_id=workspace.workspace_id,
        kit=kit,
        board=board,
        pulse=pulse,
        experiments=experiments,
        referrals=referrals,
    )


@app.post("/growth/launch-experiments", response_model=LaunchExperiment)
def create_launch_experiment(
    request: LaunchExperimentRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> LaunchExperiment:
    return _store().create_launch_experiment_for_workspace(
        workspace.workspace_id,
        request,
    )


@app.get("/growth/launch-experiments", response_model=list[LaunchExperiment])
def list_launch_experiments(
    limit: int = 20,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[LaunchExperiment]:
    return _store().list_launch_experiments_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.post(
    "/growth/launch-experiments/{experiment_id}/events",
    response_model=LaunchExperimentEvent,
)
def record_launch_experiment_event(
    experiment_id: str,
    request: LaunchExperimentEventRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> LaunchExperimentEvent:
    event = _store().record_launch_experiment_event_for_workspace(
        workspace.workspace_id,
        experiment_id,
        request,
    )
    if event is None:
        raise HTTPException(status_code=404, detail="launch experiment not found")
    return event


@app.get("/growth/launch-experiment-dashboard", response_model=LaunchExperimentDashboard)
def launch_experiment_dashboard(
    limit: int = 20,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> LaunchExperimentDashboard:
    return _store().launch_experiment_dashboard_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.get("/growth/launch-pulse", response_model=LaunchPulseDashboard)
def growth_launch_pulse(
    limit: int = 12,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> LaunchPulseDashboard:
    return _store().launch_pulse_for_workspace(workspace.workspace_id, limit=limit)


@app.get("/growth/acquisition-hub", response_model=PublicAcquisitionHub)
def growth_acquisition_hub(
    limit: int = 12,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> PublicAcquisitionHub:
    return _store().public_acquisition_hub_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.get("/growth/public-conversion-board", response_model=PublicConversionBoard)
def growth_public_conversion_board(
    limit: int = 12,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> PublicConversionBoard:
    return _store().public_conversion_board_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.get("/growth/retention-hub", response_model=RetentionHubDashboard)
def growth_retention_hub(
    limit: int = 12,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> RetentionHubDashboard:
    return _store().retention_hub_for_workspace(workspace.workspace_id, limit=limit)


@app.get("/beta/readiness", response_model=BetaReadinessDashboard)
def beta_readiness(
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> BetaReadinessDashboard:
    return _store().beta_readiness_for_workspace(workspace.workspace_id)


@app.get("/beta/launch-gate", response_model=LaunchGateDashboard)
def beta_launch_gate(
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> LaunchGateDashboard:
    return _store().launch_gate_for_workspace(workspace.workspace_id)


@app.post("/beta/cohorts", response_model=BetaCohort)
def create_beta_cohort(
    request: BetaCohortRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> BetaCohort:
    return _store().create_beta_cohort_for_workspace(workspace.workspace_id, request)


@app.get("/beta/cohorts", response_model=list[BetaCohort])
def list_beta_cohorts(
    active: bool | None = None,
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[BetaCohort]:
    return _store().list_beta_cohorts_for_workspace(
        workspace.workspace_id,
        active=active,
        limit=limit,
    )


@app.get("/beta/cohorts/{cohort_id}/report", response_model=BetaCohortReport)
def beta_cohort_report(
    cohort_id: str,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> BetaCohortReport:
    report = _store().beta_cohort_report_for_workspace(workspace.workspace_id, cohort_id)
    if report is None:
        raise HTTPException(status_code=404, detail="베타 cohort를 찾을 수 없습니다.")
    return report


@app.get("/beta/cohorts/{cohort_id}/report.md", response_class=PlainTextResponse)
def beta_cohort_markdown_report(
    cohort_id: str,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> str:
    report = _store().beta_cohort_report_for_workspace(workspace.workspace_id, cohort_id)
    if report is None:
        raise HTTPException(status_code=404, detail="베타 cohort를 찾을 수 없습니다.")
    return report.markdown


@app.get("/beta/backlog", response_model=list[BetaBacklogItem])
def beta_backlog(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[BetaBacklogItem]:
    return _store().beta_backlog_for_workspace(workspace.workspace_id, limit=limit)


@app.get("/beta/backlog/summary", response_model=BetaBacklogSummary)
def beta_backlog_summary(
    limit: int = 200,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> BetaBacklogSummary:
    return _store().beta_backlog_action_summary_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.patch("/beta/backlog/{backlog_id}", response_model=BetaBacklogAction)
def update_beta_backlog_action(
    backlog_id: str,
    request: BetaBacklogActionRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> BetaBacklogAction:
    action = _store().update_beta_backlog_action_for_workspace(
        workspace.workspace_id,
        backlog_id,
        request,
    )
    if action is None:
        raise HTTPException(status_code=404, detail="개선 백로그 항목을 찾을 수 없습니다.")
    return action


@app.get("/sources/status", response_model=list[SourceAdapterStatus])
def source_adapter_statuses() -> list[SourceAdapterStatus]:
    return _collector().statuses()


@app.post("/sources/providers", response_model=SourceProviderPolicy)
def create_source_provider_policy(
    request: SourceProviderPolicyRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> SourceProviderPolicy:
    return _store().create_source_provider_policy_for_workspace(workspace.workspace_id, request)


@app.get("/sources/providers", response_model=list[SourceProviderPolicy])
def list_source_provider_policies(
    limit: int = 100,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[SourceProviderPolicy]:
    return _store().list_source_provider_policies_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.post("/sources/providers/check", response_model=SourceProviderGate)
def check_source_provider_policy(
    request: SourceProviderCheckRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> SourceProviderGate:
    return _source_provider_gate(request.url, workspace.workspace_id)


@app.post("/ops/integrations", response_model=IntegrationProvider)
def create_integration_provider(
    request: IntegrationProviderRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> IntegrationProvider:
    return _store().create_integration_provider_for_workspace(workspace.workspace_id, request)


@app.get("/ops/integrations", response_model=list[IntegrationProvider])
def list_integration_providers(
    limit: int = 100,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[IntegrationProvider]:
    return _store().list_integration_providers_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


@app.get("/ops/integration-readiness", response_model=IntegrationReadinessDashboard)
def integration_readiness(
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> IntegrationReadinessDashboard:
    return _store().integration_readiness_for_workspace(workspace.workspace_id)


@app.post("/sources/collect", response_model=SourceCollectionResponse)
def collect_sources(request: SourceCollectionRequest) -> SourceCollectionResponse:
    response = _collector().collect(request)
    review_items = _collector().build_review_items(response.review_queue)
    _store().add_review_items(review_items)
    return response


@app.post("/sources/ingest-url", response_model=SourceUrlIngestResponse)
def ingest_url_source(
    request: SourceUrlIngestRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> SourceUrlIngestResponse:
    if not request.html.strip():
        gate = _source_provider_gate(request.url, workspace.workspace_id, record=True)
        if not gate.allowed:
            raise HTTPException(status_code=403, detail=gate.message)
    try:
        response = ingest_source_url(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if response.review_item is not None:
        _store().add_review_items([response.review_item])
    return response


@app.post("/sources/monitors", response_model=SourceMonitor)
def create_source_monitor(
    request: SourceMonitorRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> SourceMonitor:
    try:
        ingest_source_url(
            SourceUrlIngestRequest(
                url=request.url,
                category=request.category,
                kind=request.kind,
                expected_model=request.expected_model,
                source_name=request.source_name,
                seller=request.seller,
                html=request.html_snapshot or "<html><title>SpecPilot URL 검증</title></html>",
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _store().create_source_monitor_for_workspace(workspace.workspace_id, request)


@app.get("/sources/monitors", response_model=list[SourceMonitor])
def list_source_monitors(
    active: bool | None = None,
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[SourceMonitor]:
    return _store().list_source_monitors_for_workspace(
        workspace.workspace_id,
        active=active,
        limit=limit,
    )


@app.post("/sources/refresh", response_model=SourceRefreshResponse)
def refresh_source_monitors(
    request: SourceRefreshRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> SourceRefreshResponse:
    monitors = _store().list_source_monitors_for_workspace(
        workspace.workspace_id,
        active=None if request.include_inactive else True,
        monitor_ids=request.monitor_ids or None,
        limit=request.limit,
    )
    return _refresh_monitors(
        monitors,
        workspace_id=workspace.workspace_id,
        html_overrides=request.html_overrides,
    )


@app.get("/sources/schedule", response_model=SourceSchedulePreview)
def source_refresh_schedule(
    limit: int = 100,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> SourceSchedulePreview:
    monitors = _store().list_source_monitors_for_workspace(
        workspace.workspace_id,
        active=True,
        limit=limit,
    )
    return _source_schedule_preview(workspace.workspace_id, monitors)


@app.post("/sources/refresh-due", response_model=SourceRefreshResponse)
def refresh_due_source_monitors(
    request: SourceRefreshRequest,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> SourceRefreshResponse:
    monitors = _store().list_source_monitors_for_workspace(
        workspace.workspace_id,
        active=None if request.include_inactive else True,
        monitor_ids=request.monitor_ids or None,
        limit=request.limit,
    )
    due_monitors = [
        item.monitor
        for item in _source_schedule_items(monitors, datetime.now(UTC))
        if item.due
    ]
    return _refresh_monitors(
        due_monitors,
        workspace_id=workspace.workspace_id,
        html_overrides=request.html_overrides,
    )


@app.get("/sources/refresh-runs", response_model=list[SourceRefreshRun])
def list_source_refresh_runs(
    limit: int = 50,
    workspace: WorkspaceContext = WORKSPACE_DEPENDENCY,
) -> list[SourceRefreshRun]:
    return _store().list_source_refresh_runs_for_workspace(
        workspace.workspace_id,
        limit=limit,
    )


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


def _source_provider_gate(
    url: str,
    workspace_id: str,
    *,
    record: bool = False,
) -> SourceProviderGate:
    host = _host_from_url(url)
    provider = _matching_source_provider(host, workspace_id)
    status = "blocked"
    if provider is None:
        gate = SourceProviderGate(
            allowed=False,
            host=host,
            provider=None,
            remaining_hourly_quota=0,
            message="승인된 source provider 정책이 없어 live fetch를 차단했습니다.",
        )
    elif not provider.live_fetch_allowed:
        gate = SourceProviderGate(
            allowed=False,
            host=host,
            provider=provider,
            remaining_hourly_quota=0,
            message="source provider live fetch 허용이 꺼져 있습니다.",
        )
    elif provider.robots_status.value != "approved" or provider.terms_status.value != "approved":
        gate = SourceProviderGate(
            allowed=False,
            host=host,
            provider=provider,
            remaining_hourly_quota=0,
            message="robots 또는 이용약관 검토가 승인되지 않아 live fetch를 차단했습니다.",
        )
    else:
        used = _store().count_recent_provider_fetches(
            workspace_id,
            provider.provider_id,
            since_minutes=60,
            status="allowed",
        )
        remaining = max(0, provider.rate_limit_per_hour - used)
        if remaining <= 0:
            gate = SourceProviderGate(
                allowed=False,
                host=host,
                provider=provider,
                remaining_hourly_quota=0,
                message="source provider 시간당 rate limit을 초과했습니다.",
            )
        else:
            status = "allowed"
            gate = SourceProviderGate(
                allowed=True,
                host=host,
                provider=provider,
                remaining_hourly_quota=remaining - 1,
                message="source provider 정책과 rate limit을 통과했습니다.",
            )
    if record:
        _store().record_source_provider_fetch(
            SourceProviderFetchLog(
                fetch_id=f"fetch_{uuid4().hex[:12]}",
                provider_id=provider.provider_id if provider else None,
                workspace_id=workspace_id,
                url=url,
                host=host,
                status=status,
                message=gate.message,
                created_at=datetime.now(UTC).isoformat(),
            )
        )
    return gate


def _host_from_url(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        raise HTTPException(status_code=400, detail="URL host를 확인할 수 없습니다.")
    return host


def _matching_source_provider(
    host: str,
    workspace_id: str,
) -> SourceProviderPolicy | None:
    policies = _store().list_source_provider_policies_for_workspace(workspace_id, limit=500)
    matches = [
        policy
        for policy in policies
        if host == policy.host_pattern or host.endswith(f".{policy.host_pattern}")
    ]
    if not matches:
        return None
    return sorted(matches, key=lambda item: len(item.host_pattern), reverse=True)[0]


def _refresh_monitors(
    monitors: list[SourceMonitor],
    *,
    workspace_id: str,
    html_overrides: dict[str, str],
) -> SourceRefreshResponse:
    runs: list[SourceRefreshRun] = []
    candidates = []
    review_items: list[ReviewQueueItem] = []
    for monitor in monitors:
        html = html_overrides.get(monitor.monitor_id, monitor.html_snapshot)
        if not html.strip():
            gate = _source_provider_gate(monitor.url, workspace_id, record=True)
            if not gate.allowed:
                run = _source_refresh_run(
                    monitor=monitor,
                    status="failed",
                    message=gate.message,
                )
                runs.append(_store().record_source_refresh_run(run))
                continue
        try:
            response = ingest_source_url(
                SourceUrlIngestRequest(
                    url=monitor.url,
                    category=monitor.category,
                    kind=monitor.kind,
                    expected_model=monitor.expected_model,
                    source_name=monitor.source_name,
                    seller=monitor.seller,
                    html=html,
                )
            )
        except ValueError as exc:
            run = _source_refresh_run(
                monitor=monitor,
                status="failed",
                message=str(exc),
            )
        else:
            if response.review_item is not None:
                _store().add_review_items([response.review_item])
                review_items.append(response.review_item)
            candidates.append(response.candidate)
            run = _source_refresh_run(
                monitor=monitor,
                status="succeeded",
                source_id=response.candidate.source_id,
                review_id=response.review_item.review_id if response.review_item else None,
                fetched_live=response.fetched_live,
                message=" / ".join(response.extraction_notes),
            )
        runs.append(_store().record_source_refresh_run(run))
    return SourceRefreshResponse(
        selected_count=len(monitors),
        succeeded_count=sum(1 for run in runs if run.status == "succeeded"),
        failed_count=sum(1 for run in runs if run.status == "failed"),
        candidates=candidates,
        review_items=review_items,
        runs=runs,
    )


def _source_schedule_preview(
    workspace_id: str,
    monitors: list[SourceMonitor],
) -> SourceSchedulePreview:
    now = datetime.now(UTC)
    items = _source_schedule_items(monitors, now)
    due = [item for item in items if item.due]
    upcoming = [item for item in items if not item.due]
    return SourceSchedulePreview(
        workspace_id=workspace_id,
        due_count=len(due),
        upcoming_count=len(upcoming),
        generated_at=now.isoformat(),
        due=due,
        upcoming=upcoming,
    )


def _source_schedule_items(
    monitors: list[SourceMonitor],
    now: datetime,
) -> list[SourceScheduleItem]:
    return [_source_schedule_item(monitor, now) for monitor in monitors]


def _source_schedule_item(
    monitor: SourceMonitor,
    now: datetime,
) -> SourceScheduleItem:
    next_due = _next_due_at(monitor)
    due = next_due is None or next_due <= now
    overdue_minutes = 0
    if due and next_due is not None:
        overdue_minutes = max(0, int((now - next_due).total_seconds() // 60))
    return SourceScheduleItem(
        monitor=monitor,
        due=due,
        next_due_at=next_due.isoformat() if next_due else None,
        overdue_minutes=overdue_minutes,
    )


def _next_due_at(monitor: SourceMonitor) -> datetime | None:
    if monitor.last_run_at is None:
        return None
    last_run_at = datetime.fromisoformat(monitor.last_run_at)
    if last_run_at.tzinfo is None:
        last_run_at = last_run_at.replace(tzinfo=UTC)
    return last_run_at + timedelta(minutes=monitor.cadence_minutes)


def _source_refresh_run(
    *,
    monitor: SourceMonitor,
    status: str,
    message: str,
    source_id: str | None = None,
    review_id: str | None = None,
    fetched_live: bool = False,
) -> SourceRefreshRun:
    return SourceRefreshRun(
        run_id=f"refresh_{uuid4().hex[:12]}",
        monitor_id=monitor.monitor_id,
        workspace_id=monitor.workspace_id,
        status=status,
        source_id=source_id,
        review_id=review_id,
        fetched_live=fetched_live,
        message=message,
        created_at=datetime.now(UTC).isoformat(),
    )


def _default_report_title(response: AnalyzeResponse) -> str:
    top = response.report.top_recommendations[0] if response.report.top_recommendations else None
    if top is None:
        return f"{response.criteria.category.value} 구매 분석"
    return f"{top.product.model_name} 중심 구매 리포트"


def _tracking_metadata(
    request: Request,
    surface: str,
    destination: str | None = None,
) -> dict[str, str]:
    metadata = {
        "surface": surface,
        "user_agent": _limited_header(request.headers.get("user-agent")),
    }
    if destination is not None:
        metadata["destination"] = destination
    return metadata


def _limited_header(value: str | None, limit: int = 180) -> str:
    if not value:
        return ""
    return value[:limit]


def _score_status_for_public_room(score: float) -> CheckStatus:
    if score >= 75:
        return CheckStatus.ok
    if score >= 55:
        return CheckStatus.warning
    return CheckStatus.blocker


def _count_status(value: int, *, warning: int, ok: int) -> CheckStatus:
    if value >= ok:
        return CheckStatus.ok
    if value >= warning:
        return CheckStatus.warning
    return CheckStatus.blocker


def _launch_room_market_link(
    category: Category,
    report: CategoryMarketReport,
) -> PublicLaunchRoomMarketLink:
    slug = "desktop-pc" if category == Category.desktop_pc else "laptop"
    category_label = "데스크톱 PC" if category == Category.desktop_pc else "노트북"
    lead_pick = report.picks[0].model_name if report.picks else "추천 후보 준비 중"
    return PublicLaunchRoomMarketLink(
        category=category,
        title=f"{report.report_month} {category_label} 공개 구매 리포트",
        path=f"/market/{slug}",
        share_text=(
            f"{category_label} 구매 전 가격 구간, 추천 픽, 리스크 신호를 먼저 확인하세요."
        ),
        lead_pick=lead_pick,
        risk_count=len(report.risk_signals),
    )


def _validate_public_purchase_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="구매 링크는 http 또는 https URL이어야 합니다.")
    host = (parsed.hostname or "").lower()
    if not host:
        raise HTTPException(status_code=400, detail="구매 링크 host를 확인할 수 없습니다.")
    if host in {"localhost", "metadata.google.internal"} or host.endswith(".local"):
        raise HTTPException(status_code=400, detail="내부 네트워크 구매 링크는 저장할 수 없습니다.")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        raise HTTPException(
            status_code=400,
            detail="private 또는 loopback 구매 링크는 저장할 수 없습니다.",
        )


def _referrer_host(referrer: str | None) -> str:
    if not referrer:
        return ""
    return (urlparse(referrer).hostname or "")[:160]


def _user_agent_family(user_agent: str | None) -> str:
    value = (user_agent or "").lower()
    if "iphone" in value or "android" in value or "mobile" in value:
        return "mobile"
    if "bot" in value or "crawler" in value or "spider" in value:
        return "bot"
    if value:
        return "desktop"
    return ""


def _safe_tracking_redirect_path(target: str | None) -> str:
    if not target:
        return "/"
    normalized = unquote(target).strip()
    if normalized.startswith("/") and not normalized.startswith("//"):
        return normalized
    return "/"
