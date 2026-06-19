from enum import StrEnum

from pydantic import BaseModel, Field, computed_field


class Category(StrEnum):
    desktop_pc = "desktop_pc"
    laptop = "laptop"


class AgentStep(StrEnum):
    intent_parser = "intent_parser"
    clarifier = "clarifier"
    query_planner = "query_planner"
    product_collector = "product_collector"
    deduplicator = "deduplicator"
    compatibility_checker = "compatibility_checker"
    price_tracker = "price_tracker"
    review_analyzer = "review_analyzer"
    scoring_engine = "scoring_engine"
    verifier = "verifier"
    report_writer = "report_writer"


class CheckStatus(StrEnum):
    ok = "ok"
    warning = "warning"
    blocker = "blocker"


class SourceKind(StrEnum):
    price = "price"
    review = "review"
    benchmark = "benchmark"
    official = "official"


class ReviewStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class BetaBacklogStatus(StrEnum):
    open = "open"
    in_progress = "in_progress"
    done = "done"
    dismissed = "dismissed"


class ProviderReviewStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class TrustGrade(StrEnum):
    high = "high"
    medium = "medium"
    review_required = "review_required"


class WorkspaceContext(BaseModel):
    workspace_id: str
    owner_label: str
    role: str = "owner"


class PurchaseCriteria(BaseModel):
    category: Category
    budget_krw: int | None = Field(default=None, ge=0)
    purpose: str
    must_haves: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    purchase_timing: str = "within_30_days"
    channels: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    query: str = Field(min_length=2)
    category: Category = Category.desktop_pc
    budget_krw: int | None = Field(default=None, ge=0)
    purpose: str = "pc setup purchase"
    must_haves: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    purchase_timing: str = "within_30_days"
    channels: list[str] = Field(default_factory=lambda: ["price_compare", "open_market"])


class IntakeDiagnosisRequest(BaseModel):
    query: str = ""
    category: Category = Category.desktop_pc
    budget_krw: int | None = Field(default=None, ge=0)
    purpose: str = ""
    must_haves: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    purchase_timing: str = "within_30_days"
    channels: list[str] = Field(default_factory=list)


class IntakeSlotDiagnosis(BaseModel):
    slot: str
    label: str
    status: CheckStatus
    message: str
    recommendation: str


class IntakeDiagnosisResponse(BaseModel):
    readiness_score: float = Field(ge=0, le=100)
    readiness_label: str
    next_action: str
    missing_slots: list[str] = Field(default_factory=list)
    clarifying_questions: list[str] = Field(default_factory=list)
    suggested_must_haves: list[str] = Field(default_factory=list)
    suggested_exclusions: list[str] = Field(default_factory=list)
    slot_diagnostics: list[IntakeSlotDiagnosis] = Field(default_factory=list)
    normalized_request: AnalyzeRequest
    warnings: list[str] = Field(default_factory=list)


class ProductCandidate(BaseModel):
    id: str
    brand: str
    model_name: str
    normalized_model: str
    category: Category
    form_factor: str
    specs: dict[str, str | int | float]
    source_url: str
    option_summary: str = ""
    tags: list[str] = Field(default_factory=list)
    source_type: str = "demo_catalog"
    availability: str = "in_stock"


class PriceSnapshot(BaseModel):
    product_id: str
    seller: str
    price_krw: int
    shipping_fee_krw: int = 0
    coupon_krw: int = 0
    assembly_fee_krw: int = 0
    os_fee_krw: int = 0
    card_discount_krw: int = 0
    captured_at: str
    url: str
    stock_status: str = "in_stock"
    source_type: str = "price_compare"

    @computed_field
    @property
    def effective_price_krw(self) -> int:
        return (
            self.price_krw
            + self.shipping_fee_krw
            + self.assembly_fee_krw
            + self.os_fee_krw
            - self.coupon_krw
            - self.card_discount_krw
        )


class ReviewInsight(BaseModel):
    product_id: str
    pros: list[str]
    cons: list[str]
    repeated_complaints: list[str]
    risk_signals: list[str]
    trust_score: float = Field(ge=0, le=1)
    evidence_count: int = Field(default=0, ge=0)
    sentiment_summary: str = ""


class CompatibilityCheck(BaseModel):
    product_id: str
    component: str
    status: CheckStatus
    message: str
    evidence: str


class BenchmarkEvidence(BaseModel):
    product_id: str
    workload: str
    score_label: str
    summary: str
    evidence_url: str


class ComparisonRow(BaseModel):
    product_id: str
    rank: int | None = None
    model_name: str
    effective_price_krw: int
    purpose_fit: float
    compatibility: float
    review_trust: float
    strongest_reason: str
    main_risk: str


class PriceAlertPlan(BaseModel):
    product_id: str
    current_price_krw: int
    target_price_krw: int
    recheck_interval_days: int
    channels: list[str]
    trigger_reason: str


class TraceEvent(BaseModel):
    step: AgentStep
    title: str
    detail: str
    status: CheckStatus = CheckStatus.ok
    evidence_count: int = 0


class TraceSpanRecord(BaseModel):
    span_id: str
    trace_id: str
    workspace_id: str = "demo"
    sequence: int
    step: AgentStep
    title: str
    detail: str
    status: CheckStatus
    evidence_count: int = 0
    created_at: str


class TraceRunSummary(BaseModel):
    trace_id: str
    workspace_id: str = "demo"
    category: Category
    purpose: str
    final_pick_id: str | None = None
    top_model_name: str | None = None
    quality_score: float = 0
    warning_count: int = 0
    blocker_count: int = 0
    span_count: int = 0
    created_at: str


class ScoreCard(BaseModel):
    product_id: str
    purpose_fit: float = Field(ge=0, le=100)
    price_competitiveness: float = Field(ge=0, le=100)
    review_trust: float = Field(ge=0, le=100)
    purchase_stability: float = Field(ge=0, le=100)
    personal_preference: float = Field(ge=0, le=100)
    compatibility: float = Field(ge=0, le=100)
    total_score: float = Field(ge=0, le=100)
    rationale: str


class Recommendation(BaseModel):
    rank: int
    product: ProductCandidate
    price: PriceSnapshot
    review: ReviewInsight
    score: ScoreCard
    fit_summary: str
    before_buy_checklist: list[str]
    benchmark_evidence: list[BenchmarkEvidence] = Field(default_factory=list)
    compatibility_checks: list[CompatibilityCheck] = Field(default_factory=list)


class ExcludedProduct(BaseModel):
    product: ProductCandidate
    reason: str


class SourceTrustAssessment(BaseModel):
    source_type: str
    source_name: str
    kind: SourceKind
    trust_grade: TrustGrade
    confidence: float = Field(ge=0, le=1)
    freshness_minutes: int
    cache_ttl_minutes: int
    evidence_count: int = Field(ge=0)
    requires_human_review: bool = False
    policy_notes: list[str] = Field(default_factory=list)


class TrustPolicySummary(BaseModel):
    cache_policy: str
    stale_price_action: str
    affiliate_disclosure: str
    fairness_rules: list[str]
    review_rules: list[str]
    source_assessments: list[SourceTrustAssessment] = Field(default_factory=list)


class PurchaseDecision(BaseModel):
    verdict: str
    label: str
    confidence: float = Field(ge=0, le=100)
    reason: str
    risk_flags: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class ScenarioOption(BaseModel):
    scenario: str
    label: str
    product_id: str
    model_name: str
    effective_price_krw: int
    total_score: float = Field(ge=0, le=100)
    why: str
    tradeoff: str


class CriterionMatchItem(BaseModel):
    check_type: str
    criterion: str
    status: CheckStatus
    evidence: str


class ProductCriteriaMatch(BaseModel):
    product_id: str
    model_name: str
    coverage_score: float = Field(ge=0, le=100)
    matched_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    blocker_count: int = Field(ge=0)
    summary: str
    items: list[CriterionMatchItem] = Field(default_factory=list)


class PurchaseStressTest(BaseModel):
    scenario: str
    label: str
    assumption: str
    status: CheckStatus
    budget_krw: int | None = None
    selected_product_id: str | None = None
    selected_model_name: str | None = None
    price_gap_krw: int = 0
    impact: str
    recommendation: str


class ProductDealWindow(BaseModel):
    product_id: str
    model_name: str
    status: CheckStatus
    label: str
    current_price_krw: int
    target_price_krw: int
    fair_price_band_krw: str
    urgency: str
    volatility_risk: str
    wait_reason: str
    buy_trigger: str
    monitoring_plan: list[str] = Field(default_factory=list)


class ProductEvidencePack(BaseModel):
    product_id: str
    model_name: str
    price_evidence: str
    review_evidence: str
    benchmark_evidence: list[str] = Field(default_factory=list)
    compatibility_evidence: list[str] = Field(default_factory=list)
    trust_summary: str
    citation_urls: list[str] = Field(default_factory=list)
    review_required: bool = False


class OptionAuditItem(BaseModel):
    field: str
    expected_value: str
    status: CheckStatus
    verification_hint: str


class ProductOptionAudit(BaseModel):
    product_id: str
    model_name: str
    summary: str
    critical_items: list[OptionAuditItem] = Field(default_factory=list)
    mismatch_risks: list[str] = Field(default_factory=list)
    purchase_blockers: list[str] = Field(default_factory=list)


class ShareReviewBrief(BaseModel):
    headline: str
    verdict_label: str
    final_pick_id: str | None = None
    final_pick_model: str | None = None
    effective_price_krw: int | None = None
    confidence: float = Field(ge=0, le=100)
    key_reasons: list[str] = Field(default_factory=list)
    watchouts: list[str] = Field(default_factory=list)
    reviewer_questions: list[str] = Field(default_factory=list)
    copy_text: str


class PurchaseExecutionPlan(BaseModel):
    product_id: str | None = None
    model_name: str | None = None
    headline: str
    primary_action: str
    urgency: str
    price_recheck_required: bool = True
    checkout_steps: list[str] = Field(default_factory=list)
    seller_questions: list[str] = Field(default_factory=list)
    share_message: str


class PurchaseReport(BaseModel):
    summary: str
    top_recommendations: list[Recommendation]
    excluded_products: list[ExcludedProduct]
    purchase_timing: str
    compatibility_notes: list[str]
    citations: list[str]
    verification_flags: list[str]
    comparison_table: list[ComparisonRow] = Field(default_factory=list)
    benchmark_evidence: list[BenchmarkEvidence] = Field(default_factory=list)
    compatibility_checks: list[CompatibilityCheck] = Field(default_factory=list)
    price_alerts: list[PriceAlertPlan] = Field(default_factory=list)
    source_health: list[str] = Field(default_factory=list)
    decision_matrix: list[str] = Field(default_factory=list)
    source_trust: list[SourceTrustAssessment] = Field(default_factory=list)
    trust_policy: TrustPolicySummary | None = None
    purchase_decision: PurchaseDecision | None = None
    scenario_options: list[ScenarioOption] = Field(default_factory=list)
    criteria_matches: list[ProductCriteriaMatch] = Field(default_factory=list)
    stress_tests: list[PurchaseStressTest] = Field(default_factory=list)
    deal_windows: list[ProductDealWindow] = Field(default_factory=list)
    evidence_packs: list[ProductEvidencePack] = Field(default_factory=list)
    option_audits: list[ProductOptionAudit] = Field(default_factory=list)
    share_brief: ShareReviewBrief | None = None
    execution_plan: PurchaseExecutionPlan | None = None
    final_pick_id: str | None = None


class AnalyzeResponse(BaseModel):
    criteria: PurchaseCriteria
    steps: list[AgentStep]
    report: PurchaseReport
    graph_trace_id: str
    trace_events: list[TraceEvent] = Field(default_factory=list)
    quality_audit: "AnalysisQualityAudit | None" = None


class AnalysisQualityAudit(BaseModel):
    trace_id: str
    quality_score: float = Field(ge=0, le=100)
    estimated_source_calls: int = Field(ge=0)
    estimated_llm_tokens: int = Field(ge=0)
    estimated_cost_krw: float = Field(ge=0)
    warning_count: int = Field(ge=0)
    blocker_count: int = Field(ge=0)
    citation_count: int = Field(ge=0)
    review_required_sources: int = Field(ge=0)
    launch_blockers: list[str] = Field(default_factory=list)
    operator_notes: list[str] = Field(default_factory=list)


class QualityDashboard(BaseModel):
    workspace_id: str | None = None
    audit_count: int
    average_quality_score: float = 0
    total_estimated_cost_krw: float = 0
    warning_count: int = 0
    blocker_count: int = 0
    recent_audits: list[AnalysisQualityAudit] = Field(default_factory=list)


class OpsRegressionPeriod(BaseModel):
    label: str
    run_count: int = 0
    average_quality_score: float = 0
    average_cost_krw: float = 0
    warning_count: int = 0
    blocker_count: int = 0
    started_at: str | None = None
    ended_at: str | None = None


class ProviderReliabilityMetric(BaseModel):
    provider_id: str | None = None
    provider_name: str
    host: str
    fetch_count: int = 0
    allowed_count: int = 0
    blocked_count: int = 0
    blocked_rate: float = 0
    status: CheckStatus = CheckStatus.ok
    recommendation: str = ""


class OpsRegressionDashboard(BaseModel):
    workspace_id: str
    status: CheckStatus
    summary: str
    window_size: int
    recent: OpsRegressionPeriod
    previous: OpsRegressionPeriod
    quality_delta: float = 0
    cost_delta_krw: float = 0
    cost_delta_rate: float = 0
    provider_reliability: list[ProviderReliabilityMetric] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    trace_id: str
    rating: int = Field(ge=1, le=5)
    purchase_intent: bool = False
    selected_product_id: str | None = None
    reason: str = ""
    improvement_requests: list[str] = Field(default_factory=list)
    contact: str = ""


class FeedbackRecord(BaseModel):
    feedback_id: str
    trace_id: str
    workspace_id: str = "demo"
    rating: int
    purchase_intent: bool
    selected_product_id: str | None = None
    reason: str
    improvement_requests: list[str]
    contact_masked: str = ""
    created_at: str


class BetaLeadRequest(BaseModel):
    email: str = Field(min_length=3)
    persona: str = "individual_buyer"
    use_case: str
    company_size: str = "personal"
    contact_consent: bool = True
    source: str = "web"


class BetaLead(BaseModel):
    lead_id: str
    workspace_id: str = "demo"
    email_masked: str
    persona: str
    use_case: str
    company_size: str
    contact_consent: bool
    source: str
    created_at: str


class BetaCohortRequest(BaseModel):
    name: str = Field(min_length=2)
    scenario: str = Field(min_length=2)
    category: Category = Category.desktop_pc
    target_persona: str = "individual_buyer"
    target_size: int = Field(default=10, ge=1, le=10000)
    success_metric: str = "purchase_intent_rate"
    keywords: list[str] = Field(default_factory=list)
    notes: str = ""
    active: bool = True


class BetaCohort(BaseModel):
    cohort_id: str
    workspace_id: str = "demo"
    name: str
    scenario: str
    category: Category
    target_persona: str
    target_size: int
    success_metric: str
    keywords: list[str] = Field(default_factory=list)
    notes: str = ""
    active: bool = True
    lead_count: int = 0
    feedback_count: int = 0
    average_satisfaction: float = 0
    purchase_intent_rate: float = 0
    readiness_score: float = Field(default=0, ge=0, le=100)
    created_at: str
    updated_at: str


class BetaBacklogItem(BaseModel):
    backlog_id: str
    workspace_id: str = "demo"
    source_type: str
    source_id: str
    severity: CheckStatus
    title: str
    evidence: str
    suggested_action: str
    status: BetaBacklogStatus = BetaBacklogStatus.open
    assignee: str = ""
    action_note: str = ""
    action_updated_at: str | None = None
    created_at: str


class BetaBacklogActionRequest(BaseModel):
    status: BetaBacklogStatus = BetaBacklogStatus.in_progress
    assignee: str = ""
    note: str = ""


class BetaBacklogAction(BaseModel):
    backlog_id: str
    workspace_id: str = "demo"
    status: BetaBacklogStatus
    assignee: str = ""
    note: str = ""
    updated_at: str


class BetaCohortReport(BaseModel):
    cohort: BetaCohort
    generated_at: str
    summary: str
    metric_cards: dict[str, int | float | str] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    backlog: list[BetaBacklogItem] = Field(default_factory=list)
    markdown: str


class SaveReportRequest(BaseModel):
    trace_id: str
    title: str | None = None
    owner_label: str = "guest"
    notes: str = ""


class SavedReportSummary(BaseModel):
    report_id: str
    trace_id: str
    title: str
    workspace_id: str = "demo"
    owner_label: str
    final_pick_id: str | None = None
    top_model_name: str | None = None
    share_token: str | None = None
    shared_at: str | None = None
    share_views: int = 0
    created_at: str
    updated_at: str


class SavedReportDetail(SavedReportSummary):
    response: AnalyzeResponse
    notes: str = ""


class ReportShare(BaseModel):
    report_id: str
    share_token: str | None = None
    public_path: str | None = None
    is_public: bool = False
    shared_at: str | None = None
    share_views: int = 0


class PublicReport(BaseModel):
    report_id: str
    title: str
    top_model_name: str | None = None
    final_pick_id: str | None = None
    shared_at: str
    share_views: int = 0
    response: AnalyzeResponse


class AlertSubscriptionRequest(BaseModel):
    trace_id: str
    product_id: str
    target_price_krw: int = Field(gt=0)
    channels: list[str] = Field(default_factory=lambda: ["email"])
    contact: str = "guest@example.com"
    owner_label: str = "guest"


class AlertSubscription(BaseModel):
    subscription_id: str
    trace_id: str
    product_id: str
    workspace_id: str = "demo"
    target_price_krw: int
    current_price_krw: int
    channels: list[str]
    contact: str
    owner_label: str
    status: str
    created_at: str


class AlertEvaluationRequest(BaseModel):
    price_overrides_krw: dict[str, int] = Field(default_factory=dict)
    dry_run: bool = False
    limit: int = Field(default=50, ge=1, le=200)


class AlertDeliveryEvent(BaseModel):
    event_id: str
    subscription_id: str
    trace_id: str
    product_id: str
    workspace_id: str = "demo"
    target_price_krw: int
    current_price_krw: int
    delta_krw: int
    channels: list[str]
    contact_masked: str
    delivery_status: str
    message: str
    created_at: str


class AlertEvaluationResponse(BaseModel):
    workspace_id: str
    evaluated_count: int
    triggered_count: int
    dry_run: bool
    events: list[AlertDeliveryEvent] = Field(default_factory=list)


class AlertNotificationChannelRequest(BaseModel):
    channel: str = "email"
    display_name: str = ""
    target: str = ""
    enabled: bool = True
    retry_limit: int = Field(default=3, ge=0, le=10)


class AlertNotificationChannel(BaseModel):
    channel_id: str
    workspace_id: str = "demo"
    channel: str
    display_name: str
    target_masked: str
    enabled: bool
    retry_limit: int
    created_at: str
    updated_at: str


class AlertDispatchRequest(BaseModel):
    event_ids: list[str] = Field(default_factory=list)
    dry_run: bool = False
    limit: int = Field(default=50, ge=1, le=200)


class AlertDeliveryAttempt(BaseModel):
    attempt_id: str
    event_id: str
    subscription_id: str
    workspace_id: str = "demo"
    channel: str
    contact_masked: str
    delivery_status: str
    provider_message: str
    retry_count: int = 0
    next_retry_at: str | None = None
    created_at: str


class AlertDispatchResponse(BaseModel):
    workspace_id: str
    selected_count: int
    sent_count: int
    failed_count: int
    dry_run: bool
    attempts: list[AlertDeliveryAttempt] = Field(default_factory=list)


class OperationsMetrics(BaseModel):
    workspace_id: str | None = None
    analysis_runs: int
    saved_reports: int
    shared_reports: int = 0
    public_share_views: int = 0
    alert_subscriptions: int
    alert_events: int = 0
    triggered_alerts: int = 0
    alert_channels: int = 0
    alert_delivery_attempts: int = 0
    sent_alert_deliveries: int = 0
    failed_alert_deliveries: int = 0
    source_monitors: int = 0
    source_refresh_runs: int = 0
    source_refresh_failures: int = 0
    source_provider_policies: int = 0
    source_provider_fetches: int = 0
    source_provider_blocked_fetches: int = 0
    trace_spans: int = 0
    feedback_count: int = 0
    beta_leads: int = 0
    latest_trace_id: str | None = None
    average_top_score: float = 0
    average_quality_score: float = 0
    average_satisfaction: float = 0
    purchase_intent_rate: float = 0
    estimated_cost_krw: float = 0
    conversion_ready_rate: float = 0


class BetaReadinessCheck(BaseModel):
    area: str
    label: str
    status: CheckStatus
    metric: str
    recommendation: str


class BetaReadinessDashboard(BaseModel):
    workspace_id: str
    launch_readiness_score: float = Field(ge=0, le=100)
    readiness_label: str
    analysis_runs: int
    saved_reports: int
    shared_reports: int
    public_share_views: int
    alert_subscriptions: int
    feedback_count: int
    beta_leads: int
    average_quality_score: float = 0
    blocker_count: int = 0
    average_satisfaction: float = 0
    purchase_intent_rate: float = 0
    conversion_ready_rate: float = 0
    checks: list[BetaReadinessCheck] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class SourceAdapterStatus(BaseModel):
    adapter_id: str
    name: str
    kind: SourceKind
    enabled: bool
    freshness_minutes: int
    confidence: float = Field(ge=0, le=1)
    last_checked_at: str
    message: str


class SourceCandidate(BaseModel):
    source_id: str
    adapter_id: str
    kind: SourceKind
    title: str
    url: str
    normalized_model: str
    extracted_price_krw: int | None = None
    seller: str | None = None
    evidence_text: str
    confidence: float = Field(ge=0, le=1)
    collected_at: str
    needs_review: bool = False
    risk_flags: list[str] = Field(default_factory=list)


class SourceCollectionRequest(BaseModel):
    query: str = Field(min_length=2)
    category: Category = Category.desktop_pc
    adapters: list[str] = Field(default_factory=list)
    limit: int = Field(default=12, ge=1, le=50)


class SourceCollectionResponse(BaseModel):
    query: str
    category: Category
    adapter_statuses: list[SourceAdapterStatus]
    candidates: list[SourceCandidate]
    review_queue: list[SourceCandidate]


class SourceUrlIngestRequest(BaseModel):
    url: str = Field(min_length=8)
    category: Category = Category.desktop_pc
    kind: SourceKind = SourceKind.price
    expected_model: str = ""
    source_name: str = "operator_url"
    seller: str | None = None
    html: str = ""


class ReviewQueueItem(BaseModel):
    review_id: str
    source: SourceCandidate
    status: ReviewStatus = ReviewStatus.pending
    reason: str
    created_at: str
    resolved_at: str | None = None
    reviewer: str | None = None


class SourceUrlIngestResponse(BaseModel):
    candidate: SourceCandidate
    review_item: ReviewQueueItem | None = None
    fetched_live: bool = False
    extraction_notes: list[str] = Field(default_factory=list)


class SourceMonitorRequest(BaseModel):
    url: str = Field(min_length=8)
    category: Category = Category.desktop_pc
    kind: SourceKind = SourceKind.price
    expected_model: str = ""
    source_name: str = "source_monitor"
    seller: str | None = None
    cadence_minutes: int = Field(default=180, ge=15, le=10080)
    active: bool = True
    html_snapshot: str = ""


class SourceMonitor(BaseModel):
    monitor_id: str
    workspace_id: str
    url: str
    category: Category
    kind: SourceKind
    expected_model: str
    source_name: str
    seller: str | None = None
    cadence_minutes: int
    active: bool
    last_run_at: str | None = None
    last_status: str = "never_run"
    last_source_id: str | None = None
    failure_count: int = 0
    created_at: str
    updated_at: str
    html_snapshot: str = Field(default="", exclude=True)


class SourceRefreshRequest(BaseModel):
    monitor_ids: list[str] = Field(default_factory=list)
    limit: int = Field(default=20, ge=1, le=100)
    include_inactive: bool = False
    html_overrides: dict[str, str] = Field(default_factory=dict)


class SourceRefreshRun(BaseModel):
    run_id: str
    monitor_id: str
    workspace_id: str
    status: str
    source_id: str | None = None
    review_id: str | None = None
    fetched_live: bool = False
    message: str
    created_at: str


class SourceRefreshResponse(BaseModel):
    selected_count: int
    succeeded_count: int
    failed_count: int
    candidates: list[SourceCandidate] = Field(default_factory=list)
    review_items: list[ReviewQueueItem] = Field(default_factory=list)
    runs: list[SourceRefreshRun] = Field(default_factory=list)


class SourceScheduleItem(BaseModel):
    monitor: SourceMonitor
    due: bool
    next_due_at: str | None = None
    overdue_minutes: int = 0


class SourceSchedulePreview(BaseModel):
    workspace_id: str
    due_count: int
    upcoming_count: int
    generated_at: str
    due: list[SourceScheduleItem] = Field(default_factory=list)
    upcoming: list[SourceScheduleItem] = Field(default_factory=list)


class SourceProviderPolicyRequest(BaseModel):
    provider_name: str = Field(min_length=2)
    host_pattern: str = Field(min_length=3)
    kind: SourceKind = SourceKind.price
    live_fetch_allowed: bool = False
    robots_status: ProviderReviewStatus = ProviderReviewStatus.pending
    terms_status: ProviderReviewStatus = ProviderReviewStatus.pending
    credential_status: str = "not_connected"
    rate_limit_per_hour: int = Field(default=30, ge=1, le=5000)
    notes: str = ""


class SourceProviderPolicy(BaseModel):
    provider_id: str
    workspace_id: str
    provider_name: str
    host_pattern: str
    kind: SourceKind
    live_fetch_allowed: bool
    robots_status: ProviderReviewStatus
    terms_status: ProviderReviewStatus
    credential_status: str
    rate_limit_per_hour: int
    notes: str = ""
    created_at: str
    updated_at: str


class SourceProviderFetchLog(BaseModel):
    fetch_id: str
    provider_id: str | None = None
    workspace_id: str
    url: str
    host: str
    status: str
    message: str
    created_at: str


class SourceProviderGate(BaseModel):
    allowed: bool
    host: str
    provider: SourceProviderPolicy | None = None
    remaining_hourly_quota: int = 0
    message: str


class SourceProviderCheckRequest(BaseModel):
    url: str = Field(min_length=8)


class ReviewDecisionRequest(BaseModel):
    status: ReviewStatus
    reviewer: str = "operator"
    note: str = ""


class ReviewDecision(BaseModel):
    review_id: str
    status: ReviewStatus
    reviewer: str
    note: str
    resolved_at: str


class AdminReviewDashboard(BaseModel):
    adapter_statuses: list[SourceAdapterStatus]
    pending_reviews: list[ReviewQueueItem]
    metrics: OperationsMetrics


class ProductBrief(BaseModel):
    name: str
    one_liner: str
    target_users: list[str]
    core_workflows: list[str]
    mvp_categories: list[Category]
    stack: list[str]
