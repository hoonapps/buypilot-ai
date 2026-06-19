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
    created_at: str
    updated_at: str


class SavedReportDetail(SavedReportSummary):
    response: AnalyzeResponse
    notes: str = ""


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


class OperationsMetrics(BaseModel):
    workspace_id: str | None = None
    analysis_runs: int
    saved_reports: int
    alert_subscriptions: int
    alert_events: int = 0
    triggered_alerts: int = 0
    feedback_count: int = 0
    beta_leads: int = 0
    latest_trace_id: str | None = None
    average_top_score: float = 0
    average_quality_score: float = 0
    average_satisfaction: float = 0
    purchase_intent_rate: float = 0
    estimated_cost_krw: float = 0
    conversion_ready_rate: float = 0


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


class ReviewQueueItem(BaseModel):
    review_id: str
    source: SourceCandidate
    status: ReviewStatus = ReviewStatus.pending
    reason: str
    created_at: str
    resolved_at: str | None = None
    reviewer: str | None = None


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
