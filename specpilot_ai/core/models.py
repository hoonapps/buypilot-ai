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


class IntegrationCategory(StrEnum):
    price_api = "price_api"
    marketplace = "marketplace"
    official_store = "official_store"
    review_feed = "review_feed"
    benchmark = "benchmark"
    email = "email"
    sms = "sms"
    webhook = "webhook"
    observability = "observability"
    affiliate = "affiliate"
    scheduler = "scheduler"


class IntegrationStatus(StrEnum):
    mock = "mock"
    configured = "configured"
    verified = "verified"
    blocked = "blocked"


class PurchaseOutcomeStatus(StrEnum):
    purchased = "purchased"
    abandoned = "abandoned"
    delayed = "delayed"
    returned = "returned"


class GrowthEventType(StrEnum):
    analysis_view = "analysis_view"
    recommendation_click = "recommendation_click"
    alternative_click = "alternative_click"
    share_cta = "share_cta"
    alert_cta = "alert_cta"
    purchase_link_cta = "purchase_link_cta"
    subscription_cta = "subscription_cta"
    feedback_cta = "feedback_cta"


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


class DemoScenario(BaseModel):
    scenario_id: str
    title: str
    category: Category
    persona: str
    one_liner: str
    request: AnalyzeRequest
    expected_outcome: str
    proof_points: list[str] = Field(default_factory=list)
    demo_cta: str
    share_angle: str
    tags: list[str] = Field(default_factory=list)


class DemoScenarioGallery(BaseModel):
    gallery_version: str = "specpilot.demo_gallery.v1"
    headline: str
    subheadline: str
    primary_metric: str
    scenarios: list[DemoScenario] = Field(default_factory=list)


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


class PrivacyDataCategory(BaseModel):
    category: str
    label: str
    stored_fields: list[str] = Field(default_factory=list)
    masking: str
    retention: str
    user_control: str


class PrivacyPolicySummary(BaseModel):
    policy_version: str = "specpilot.privacy.v1"
    headline: str
    data_minimization: str
    public_report_policy: str
    contact_policy: str
    retention_policy: str
    user_controls: list[str] = Field(default_factory=list)
    prohibited_data: list[str] = Field(default_factory=list)
    data_categories: list[PrivacyDataCategory] = Field(default_factory=list)


class TrustCenterGate(BaseModel):
    area: str
    label: str
    status: CheckStatus
    public_message: str
    evidence: list[str] = Field(default_factory=list)
    buyer_impact: str
    next_action: str


class TrustCenterDashboard(BaseModel):
    policy_version: str = "specpilot.trust_center.v1"
    generated_at: str
    headline: str
    public_summary: str
    overall_status: CheckStatus
    trust_policy: TrustPolicySummary
    privacy_policy: PrivacyPolicySummary
    public_commitments: list[str] = Field(default_factory=list)
    buyer_rights: list[str] = Field(default_factory=list)
    operational_gates: list[TrustCenterGate] = Field(default_factory=list)
    risk_disclosures: list[str] = Field(default_factory=list)
    escalation_paths: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


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


class OpsLearningInsight(BaseModel):
    product_id: str
    model_name: str | None = None
    outcome_count: int = 0
    purchase_count: int = 0
    abandoned_count: int = 0
    delayed_count: int = 0
    returned_count: int = 0
    checkout_review_count: int = 0
    checkout_blocked_count: int = 0
    feedback_count: int = 0
    average_satisfaction: float = 0
    conversion_rate: float = 0
    return_rate: float = 0
    average_price_delta_krw: float = 0
    conversion_value_krw: int = 0
    status: CheckStatus = CheckStatus.ok
    evidence: str = ""
    recommended_action: str = ""
    learning_tags: list[str] = Field(default_factory=list)


class OpsLearningDashboard(BaseModel):
    workspace_id: str
    generated_at: str
    status: CheckStatus
    summary: str
    insight_count: int = 0
    top_actions: list[str] = Field(default_factory=list)
    insights: list[OpsLearningInsight] = Field(default_factory=list)


class ObservabilityExportRequest(BaseModel):
    trace_id: str
    destination: str = "opentelemetry"
    include_payload: bool = True


class ObservabilityExportRecord(BaseModel):
    export_id: str
    workspace_id: str = "demo"
    trace_id: str
    destination: str
    status: str = "queued"
    span_count: int = 0
    quality_score: float = 0
    payload: dict = Field(default_factory=dict)
    provider_message: str = ""
    retry_count: int = 0
    dispatched_at: str | None = None
    next_retry_at: str | None = None
    created_at: str


class ObservabilityDispatchRequest(BaseModel):
    export_ids: list[str] = Field(default_factory=list)
    dry_run: bool = False
    limit: int = Field(default=50, ge=1, le=200)


class ObservabilityDispatchResponse(BaseModel):
    workspace_id: str
    selected_count: int
    sent_count: int
    failed_count: int
    dry_run: bool
    exports: list[ObservabilityExportRecord] = Field(default_factory=list)


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


class WaitlistReferralRequest(BaseModel):
    email: str = Field(min_length=3)
    persona: str = "individual_buyer"
    use_case: str = ""
    referred_by_code: str = ""
    source: str = "web"
    contact_consent: bool = True


class WaitlistReferral(BaseModel):
    referral_id: str
    workspace_id: str = "demo"
    email_masked: str
    persona: str
    use_case: str = ""
    referral_code: str
    referred_by_code: str = ""
    referral_url: str
    referred_signup_count: int = 0
    priority_score: int = 0
    contact_consent: bool
    source: str
    created_at: str


class ReferralLeaderboardItem(BaseModel):
    referral_code: str
    email_masked: str
    persona: str
    referred_signup_count: int = 0
    priority_score: int = 0
    referral_url: str


class WaitlistReferralDashboard(BaseModel):
    workspace_id: str
    generated_at: str
    total_referrals: int = 0
    referred_signup_count: int = 0
    share_rate_hint: float = 0
    summary: str
    top_referrers: list[ReferralLeaderboardItem] = Field(default_factory=list)
    latest_referrals: list[WaitlistReferral] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class PublicReferralLeaderboardEntry(BaseModel):
    rank: int
    referral_code: str
    email_masked: str
    persona: str
    referred_signup_count: int = 0
    priority_score: int = 0
    reward_label: str
    status: str = "ranked"


class PublicReferralLeaderboard(BaseModel):
    leaderboard_version: str = "specpilot.public_referral_leaderboard.v1"
    workspace_id: str
    generated_at: str
    headline: str
    summary: str
    total_referrals: int = 0
    referred_signup_count: int = 0
    current_rank: int | None = None
    current_entry: PublicReferralLeaderboardEntry | None = None
    entries: list[PublicReferralLeaderboardEntry] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class ReferralShareKitVariant(BaseModel):
    channel: str
    label: str
    headline: str
    body: str
    cta: str
    copy_text: str


class ReferralShareKit(BaseModel):
    kit_version: str = "specpilot.referral_share_kit.v1"
    workspace_id: str
    referral_code: str
    referral_url: str
    generated_at: str
    headline: str
    subheadline: str
    hashtags: list[str] = Field(default_factory=list)
    variants: list[ReferralShareKitVariant] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class ReferralRewardTier(BaseModel):
    tier_id: str
    label: str
    required_referrals: int = Field(ge=0)
    benefit: str
    status: str


class ReferralRewardProgress(BaseModel):
    reward_version: str = "specpilot.referral_rewards.v1"
    workspace_id: str
    referral_code: str
    referral_url: str
    generated_at: str
    referred_signup_count: int = 0
    headline: str
    summary: str
    progress_percent: int = Field(ge=0, le=100)
    current_tier: ReferralRewardTier | None = None
    next_tier: ReferralRewardTier | None = None
    tiers: list[ReferralRewardTier] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class PublicReferralLaunchKit(BaseModel):
    kit_version: str = "specpilot.public_referral_launch_kit.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    headline: str
    summary: str
    dashboard: WaitlistReferralDashboard
    leaderboard: PublicReferralLeaderboard
    reward_tiers: list[ReferralRewardTier] = Field(default_factory=list)
    share_examples: list[ReferralShareKitVariant] = Field(default_factory=list)
    cta_cards: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class PricingPlan(BaseModel):
    plan_id: str
    name: str
    audience: str
    monthly_price_krw: int = Field(ge=0)
    annual_price_krw: int = Field(ge=0)
    features: list[str] = Field(default_factory=list)
    recommended_for: list[str] = Field(default_factory=list)
    cta_label: str = "관심 등록"


class SubscriptionIntentRequest(BaseModel):
    email: str = Field(min_length=3)
    plan_id: str = "premium"
    billing_cycle: str = "monthly"
    persona: str = "individual_buyer"
    use_case: str = ""
    team_size: int = Field(default=1, ge=1, le=10000)
    max_budget_krw: int | None = Field(default=None, ge=0)
    feature_priorities: list[str] = Field(default_factory=list)
    purchase_timing: str = "within_30_days"
    contact_consent: bool = True
    source: str = "web"


class SubscriptionIntent(BaseModel):
    intent_id: str
    workspace_id: str = "demo"
    email_masked: str
    plan_id: str
    plan_name: str
    billing_cycle: str
    monthly_price_krw: int
    estimated_mrr_krw: int
    persona: str
    use_case: str = ""
    team_size: int = 1
    max_budget_krw: int | None = None
    feature_priorities: list[str] = Field(default_factory=list)
    purchase_timing: str
    contact_consent: bool
    source: str
    readiness_status: CheckStatus
    recommendation: str
    created_at: str


class PricingDashboard(BaseModel):
    workspace_id: str
    generated_at: str
    intent_count: int = 0
    premium_intent_count: int = 0
    team_intent_count: int = 0
    estimated_mrr_krw: int = 0
    annualized_revenue_krw: int = 0
    average_budget_krw: float = 0
    top_plan_id: str | None = None
    top_plan_name: str | None = None
    readiness_status: CheckStatus
    summary: str
    next_actions: list[str] = Field(default_factory=list)
    plans: list[PricingPlan] = Field(default_factory=list)
    recent_intents: list[SubscriptionIntent] = Field(default_factory=list)


class TeamPurchaseConsultKit(BaseModel):
    kit_version: str = "specpilot.team_purchase_consult_kit.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    headline: str
    summary: str
    target_plan: PricingPlan
    team_intent_count: int = 0
    estimated_team_mrr_krw: int = 0
    recommended_team_size: int = 1
    decision_maker_brief: str
    consultation_agenda: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    roi_points: list[str] = Field(default_factory=list)
    rollout_steps: list[str] = Field(default_factory=list)
    email_copy: str
    cta_cards: list[str] = Field(default_factory=list)
    recent_team_intents: list[SubscriptionIntent] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class MarketReportPick(BaseModel):
    category: Category
    product_id: str
    model_name: str
    role_label: str
    effective_price_krw: int
    target_price_krw: int
    price_band: str
    stock_status: str
    source_type: str
    benchmark_summary: str
    risk_status: CheckStatus
    fit_tags: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    watchouts: list[str] = Field(default_factory=list)


class MarketPriceSegment(BaseModel):
    category: Category
    label: str
    min_price_krw: int
    max_price_krw: int
    recommended_budget_krw: int
    summary: str
    representative_product_ids: list[str] = Field(default_factory=list)


class MarketRiskSignal(BaseModel):
    title: str
    status: CheckStatus
    affected_product_ids: list[str] = Field(default_factory=list)
    evidence: str
    action: str


class MarketTrendCard(BaseModel):
    title: str
    category: Category | None = None
    signal: str
    evidence: str
    recommendation: str


class CategoryMarketReport(BaseModel):
    workspace_id: str
    generated_at: str
    report_month: str
    category_filter: Category | None = None
    headline: str
    summary: str
    total_candidates: int = 0
    picks: list[MarketReportPick] = Field(default_factory=list)
    price_segments: list[MarketPriceSegment] = Field(default_factory=list)
    risk_signals: list[MarketRiskSignal] = Field(default_factory=list)
    trend_cards: list[MarketTrendCard] = Field(default_factory=list)
    workspace_signals: dict[str, int | float | str] = Field(default_factory=dict)
    publishing_checklist: list[str] = Field(default_factory=list)


class PublicCategoryMarketReport(BaseModel):
    category: Category
    slug: str
    canonical_path: str
    title: str
    description: str
    share_text: str
    seo_keywords: list[str] = Field(default_factory=list)
    cta_cards: list[str] = Field(default_factory=list)
    report: CategoryMarketReport


class PublicProofAsset(BaseModel):
    key: str
    label: str
    status: CheckStatus
    metric: str
    proof: str
    public_path: str
    cta_label: str
    next_action: str


class PublicObjectionAnswer(BaseModel):
    question: str
    answer: str
    evidence: list[str] = Field(default_factory=list)


class PublicObjectionCard(BaseModel):
    key: str
    question: str
    status: CheckStatus
    short_answer: str
    proof_points: list[str] = Field(default_factory=list)
    evidence_paths: list[str] = Field(default_factory=list)
    cta_label: str
    cta_path: str


class PublicObjectionComparison(BaseModel):
    criterion: str
    price_comparison_sites: str
    specpilot_ai: str
    why_it_matters: str


class PublicLaunchObjectionKit(BaseModel):
    kit_version: str = "specpilot.public_launch_objection_kit.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    objection_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    primary_cta: str
    primary_cta_path: str
    objections: list[PublicObjectionCard] = Field(default_factory=list)
    comparisons: list[PublicObjectionComparison] = Field(default_factory=list)
    trust_badges: list[str] = Field(default_factory=list)
    channel_replies: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class PublicLaunchShareVariant(BaseModel):
    channel: str
    label: str
    audience: str
    share_url: str
    headline: str
    body: str
    cta_label: str
    copy_text: str
    tracking_event: str
    proof_points: list[str] = Field(default_factory=list)
    disclosure: str


class PublicLaunchSharePack(BaseModel):
    pack_version: str = "specpilot.public_launch_share_pack.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    share_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    primary_url: str
    primary_copy: str
    variants: list[PublicLaunchShareVariant] = Field(default_factory=list)
    proof_strip: list[str] = Field(default_factory=list)
    trust_disclosures: list[str] = Field(default_factory=list)
    measurement_events: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class PublicLaunchActionRoute(BaseModel):
    key: str
    persona: str
    trigger: str
    recommended_action: str
    cta_label: str
    cta_path: str
    priority_score: float = Field(ge=0, le=100)
    status: CheckStatus
    why_now: str
    proof_points: list[str] = Field(default_factory=list)
    fallback_action: str
    tracking_event: str


class PublicLaunchActionRouter(BaseModel):
    router_version: str = "specpilot.public_launch_action_router.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    routing_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    default_route_key: str
    routes: list[PublicLaunchActionRoute] = Field(default_factory=list)
    quick_filters: list[str] = Field(default_factory=list)
    measurement_events: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class PublicProofEvidence(BaseModel):
    title: str
    status: CheckStatus
    audience: str
    proof: str
    source_path: str
    reuse_hint: str


class PublicProofHub(BaseModel):
    proof_version: str = "specpilot.public_proof_hub.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    proof_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    hero_proof_strip: list[str] = Field(default_factory=list)
    metric_cards: dict[str, int | float | str] = Field(default_factory=dict)
    trust_badges: list[str] = Field(default_factory=list)
    evidence_kit: list[PublicProofEvidence] = Field(default_factory=list)
    proof_assets: list[PublicProofAsset] = Field(default_factory=list)
    objection_answers: list[PublicObjectionAnswer] = Field(default_factory=list)
    cta_cards: list[str] = Field(default_factory=list)
    public_paths: list[str] = Field(default_factory=list)
    recent_feedback: list[FeedbackRecord] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class PublicSocialProofItem(BaseModel):
    proof_id: str
    kind: str
    title: str
    body: str
    metric: str
    persona: str = ""
    source_label: str
    rating: int | None = None
    status: CheckStatus = CheckStatus.ok
    created_at: str | None = None


class PublicSocialProofWall(BaseModel):
    wall_version: str = "specpilot.public_social_proof_wall.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    proof_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    metric_cards: dict[str, int | float | str] = Field(default_factory=dict)
    proof_strip: list[str] = Field(default_factory=list)
    items: list[PublicSocialProofItem] = Field(default_factory=list)
    trust_notes: list[str] = Field(default_factory=list)
    cta_cards: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class PublicLaunchRoomCard(BaseModel):
    key: str
    title: str
    status: CheckStatus
    metric: str
    body: str
    cta_label: str
    cta_path: str


class PublicLaunchRoomMarketLink(BaseModel):
    category: Category
    title: str
    path: str
    share_text: str
    lead_pick: str
    risk_count: int = 0


class PublicLaunchRoom(BaseModel):
    room_version: str = "specpilot.public_launch_room.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    launch_score: float = Field(ge=0, le=100)
    headline: str
    hero_message: str
    share_title: str
    share_text: str
    primary_cta: str
    primary_cta_path: str
    proof_strip: list[str] = Field(default_factory=list)
    demo_cards: list[PublicLaunchRoomCard] = Field(default_factory=list)
    launch_cards: list[PublicLaunchRoomCard] = Field(default_factory=list)
    market_links: list[PublicLaunchRoomMarketLink] = Field(default_factory=list)
    secondary_ctas: list[str] = Field(default_factory=list)
    channel_posts: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class PublicLaunchSmokeCheck(BaseModel):
    key: str
    label: str
    status: CheckStatus
    public_path: str
    expected_signal: str
    metric: str
    recommendation: str


class PublicLaunchSmokeDashboard(BaseModel):
    smoke_version: str = "specpilot.public_launch_smoke.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    smoke_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    ok_count: int = 0
    warning_count: int = 0
    blocker_count: int = 0
    publish_ready_paths: list[str] = Field(default_factory=list)
    checks: list[PublicLaunchSmokeCheck] = Field(default_factory=list)
    measurement_events: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class PurchaseOnboardingStep(BaseModel):
    title: str
    description: str
    required_inputs: list[str] = Field(default_factory=list)
    output: str


class PurchaseOnboardingPlaybook(BaseModel):
    playbook_id: str
    category: Category
    persona: str
    title: str
    description: str
    hero_query: str
    purpose: str
    budget_hint_krw: int
    must_haves: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    readiness_slots: list[str] = Field(default_factory=list)
    steps: list[PurchaseOnboardingStep] = Field(default_factory=list)
    trust_gates: list[str] = Field(default_factory=list)
    recommended_plan_id: str = "free"
    cta_label: str = "내 조건으로 분석 시작"
    cta_anchor: str = "#analysis"


class BuyerChecklistItem(BaseModel):
    item_id: str
    label: str
    status: CheckStatus
    why_it_matters: str
    user_input_hint: str
    failure_if_missing: str


class BuyerChecklistSection(BaseModel):
    section_id: str
    title: str
    summary: str
    items: list[BuyerChecklistItem] = Field(default_factory=list)


class PublicBuyerChecklist(BaseModel):
    checklist_version: str = "specpilot.public_buyer_checklist.v1"
    generated_at: str
    category: Category
    persona: str
    budget_krw: int
    headline: str
    summary: str
    readiness_score: float = Field(ge=0, le=100)
    budget_fit: str
    primary_cta_label: str = "내 조건으로 분석 시작"
    primary_cta_anchor: str = "#analysis"
    analysis_prefill: str
    sections: list[BuyerChecklistSection] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    evidence_to_capture: list[str] = Field(default_factory=list)
    share_copy: str
    next_actions: list[str] = Field(default_factory=list)


class BuyerPersonaQuizOption(BaseModel):
    option_id: str
    label: str
    description: str


class BuyerPersonaQuizQuestion(BaseModel):
    question_id: str
    title: str
    helper: str
    options: list[BuyerPersonaQuizOption] = Field(default_factory=list)


class PublicBuyerPersonaQuiz(BaseModel):
    quiz_version: str = "specpilot.public_buyer_persona_quiz.v1"
    generated_at: str
    headline: str
    summary: str
    questions: list[BuyerPersonaQuizQuestion] = Field(default_factory=list)
    result_endpoint: str = "/public/buyer-persona-quiz/result"
    next_actions: list[str] = Field(default_factory=list)


class BuyerPersonaQuizAnswer(BaseModel):
    question_id: str
    option_id: str


class BuyerPersonaQuizRequest(BaseModel):
    answers: list[BuyerPersonaQuizAnswer] = Field(default_factory=list)
    source: str = "web"


class BuyerPersonaQuizResult(BaseModel):
    result_version: str = "specpilot.buyer_persona_quiz_result.v1"
    generated_at: str
    persona_id: str
    persona_label: str
    category: Category
    recommended_plan_id: str
    recommended_budget_krw: int
    confidence_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    analysis_prefill: str
    checklist_path: str
    primary_cta_label: str
    primary_cta_path: str
    proof_points: list[str] = Field(default_factory=list)
    share_copy: str
    next_actions: list[str] = Field(default_factory=list)


class MistakeCostRiskOption(BaseModel):
    risk_id: str
    label: str
    default_weight: float = Field(ge=0, le=1)
    description: str


class PublicMistakeCostCalculator(BaseModel):
    calculator_version: str = "specpilot.public_mistake_cost_calculator.v1"
    generated_at: str
    headline: str
    summary: str
    default_category: Category
    default_budget_krw: int
    default_quantity: int = 1
    risk_options: list[MistakeCostRiskOption] = Field(default_factory=list)
    result_endpoint: str = "/public/mistake-cost-calculator/result"
    next_actions: list[str] = Field(default_factory=list)


class MistakeCostCalculatorRequest(BaseModel):
    category: Category = Category.desktop_pc
    budget_krw: int = Field(default=2_200_000, ge=300_000, le=30_000_000)
    quantity: int = Field(default=1, ge=1, le=200)
    urgency: str = "normal"
    selected_risks: list[str] = Field(default_factory=list)
    source: str = "web"


class MistakeCostLineItem(BaseModel):
    item_id: str
    label: str
    estimated_cost_krw: int
    prevention: str


class MistakeCostCalculatorResult(BaseModel):
    result_version: str = "specpilot.mistake_cost_calculator_result.v1"
    generated_at: str
    category: Category
    budget_krw: int
    quantity: int
    urgency: str
    estimated_mistake_cost_krw: int
    protected_value_krw: int
    risk_score: float = Field(ge=0, le=100)
    risk_level: str
    headline: str
    summary: str
    line_items: list[MistakeCostLineItem] = Field(default_factory=list)
    analysis_prefill: str
    primary_cta_label: str = "이 리스크로 분석 시작"
    primary_cta_path: str = "#analysis"
    share_copy: str
    next_actions: list[str] = Field(default_factory=list)


class BuyerChallengeStep(BaseModel):
    step_id: str
    title: str
    action: str
    proof: str


class BuyerChallengeShareVariant(BaseModel):
    channel: str
    label: str
    headline: str
    body: str
    cta: str
    copy_text: str


class PublicBuyerChallengeKit(BaseModel):
    kit_version: str = "specpilot.public_buyer_challenge_kit.v1"
    generated_at: str
    category: Category
    budget_krw: int
    persona: str
    headline: str
    summary: str
    challenge_title: str
    challenge_steps: list[BuyerChallengeStep] = Field(default_factory=list)
    analysis_prefill: str
    checklist_path: str
    mistake_cost_path: str
    persona_quiz_path: str = "/public/buyer-persona-quiz"
    hashtags: list[str] = Field(default_factory=list)
    proof_points: list[str] = Field(default_factory=list)
    share_variants: list[BuyerChallengeShareVariant] = Field(default_factory=list)
    primary_cta_label: str = "챌린지 조건으로 분석 시작"
    primary_cta_path: str = "#analysis"
    next_actions: list[str] = Field(default_factory=list)


class PublicSpecRiskScanner(BaseModel):
    scanner_version: str = "specpilot.public_spec_risk_scanner.v1"
    generated_at: str
    headline: str
    summary: str
    default_category: Category = Category.desktop_pc
    default_budget_krw: int = 2_200_000
    result_endpoint: str = "/public/spec-risk-scanner/result"
    example_request: dict[str, str | int] = Field(default_factory=dict)
    required_evidence: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class SpecRiskScannerRequest(BaseModel):
    category: Category = Category.desktop_pc
    product_title: str = "데스크톱 PC 견적"
    option_text: str = ""
    cart_total_krw: int | None = Field(default=None, ge=0, le=30_000_000)
    budget_krw: int = Field(default=2_200_000, ge=300_000, le=30_000_000)
    expected_cpu: str = ""
    expected_gpu: str = ""
    expected_ram_gb: int | None = Field(default=None, ge=0, le=1024)
    expected_storage_gb: int | None = Field(default=None, ge=0, le=16384)
    expected_os: str = ""
    evidence_text: str = ""
    source: str = "web"


class SpecRiskCheck(BaseModel):
    check_id: str
    label: str
    status: CheckStatus
    expected: str
    observed: str
    recommendation: str


class SpecRiskScannerResult(BaseModel):
    result_version: str = "specpilot.spec_risk_scanner_result.v1"
    generated_at: str
    category: Category
    product_title: str
    budget_krw: int
    cart_total_krw: int | None = None
    verdict: str
    readiness_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    checks: list[SpecRiskCheck] = Field(default_factory=list)
    blocker_count: int = 0
    warning_count: int = 0
    missing_evidence: list[str] = Field(default_factory=list)
    analysis_prefill: str
    share_copy: str
    primary_cta_label: str = "검수 결과로 분석 시작"
    primary_cta_path: str = "#analysis"
    next_actions: list[str] = Field(default_factory=list)


class CandidateCompareItem(BaseModel):
    product_id: str
    model_name: str
    category: Category
    role_label: str
    effective_price_krw: int
    price_gap_krw: int
    score: float = Field(ge=0, le=100)
    status: CheckStatus
    option_summary: str
    fit_summary: str
    reasons: list[str] = Field(default_factory=list)
    watchouts: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    cta_label: str = "이 후보로 분석"


class CandidateCompareAxis(BaseModel):
    axis_id: str
    label: str
    winner_product_id: str | None = None
    summary: str


class CandidateCompareScenario(BaseModel):
    scenario: str
    label: str
    product_id: str
    model_name: str
    why: str
    tradeoff: str


class PublicCandidateCompare(BaseModel):
    compare_version: str = "specpilot.public_candidate_compare.v1"
    generated_at: str
    category: Category
    budget_krw: int
    purpose: str
    headline: str
    summary: str
    winner_product_id: str | None = None
    winner_reason: str
    items: list[CandidateCompareItem] = Field(default_factory=list)
    axes: list[CandidateCompareAxis] = Field(default_factory=list)
    scenarios: list[CandidateCompareScenario] = Field(default_factory=list)
    analysis_prefill: str
    share_copy: str
    primary_cta_label: str = "이 비교표로 분석 시작"
    primary_cta_path: str = "#analysis"
    next_actions: list[str] = Field(default_factory=list)


class PublicDealTimingWindow(BaseModel):
    timing_version: str = "specpilot.public_deal_timing_window.v1"
    generated_at: str
    category: Category
    budget_krw: int
    purpose: str
    headline: str
    summary: str
    lead_product_id: str | None = None
    lead_label: str
    buy_now_count: int = 0
    wait_count: int = 0
    hold_count: int = 0
    target_savings_krw: int = 0
    windows: list[ProductDealWindow] = Field(default_factory=list)
    analysis_prefill: str
    share_copy: str
    primary_cta_label: str = "타이밍 조건으로 분석 시작"
    primary_cta_path: str = "#analysis"
    next_actions: list[str] = Field(default_factory=list)


class StartConciergeMilestone(BaseModel):
    step: str
    title: str
    status: CheckStatus
    detail: str
    next_action: str


class StartConciergeAction(BaseModel):
    label: str
    target: str
    action_type: str
    reason: str


class PurchaseStartConcierge(BaseModel):
    concierge_version: str = "specpilot.start_concierge.v1"
    category: Category
    readiness_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    primary_action: StartConciergeAction
    matched_playbook: PurchaseOnboardingPlaybook
    diagnosis: IntakeDiagnosisResponse
    milestones: list[StartConciergeMilestone] = Field(default_factory=list)
    quick_actions: list[StartConciergeAction] = Field(default_factory=list)
    proof_points: list[str] = Field(default_factory=list)
    conversion_prompt: str


class GrowthEventRequest(BaseModel):
    event_type: GrowthEventType
    trace_id: str | None = None
    report_id: str | None = None
    product_id: str | None = None
    source: str = "web"
    surface: str = "home"
    label: str = ""
    metadata: dict[str, int | float | str | bool] = Field(default_factory=dict)


class GrowthEventRecord(BaseModel):
    event_id: str
    workspace_id: str = "demo"
    event_type: GrowthEventType
    trace_id: str | None = None
    report_id: str | None = None
    product_id: str | None = None
    source: str
    surface: str
    label: str
    metadata: dict[str, int | float | str | bool] = Field(default_factory=dict)
    created_at: str


class GrowthFunnelStep(BaseModel):
    key: GrowthEventType
    label: str
    event_count: int = 0
    unique_traces: int = 0
    conversion_rate: float = 0
    status: CheckStatus = CheckStatus.warning
    recommendation: str


class GrowthFunnelDashboard(BaseModel):
    workspace_id: str
    generated_at: str
    total_events: int = 0
    unique_traces: int = 0
    activation_rate: float = 0
    share_rate: float = 0
    alert_rate: float = 0
    paid_intent_rate: float = 0
    status: CheckStatus = CheckStatus.warning
    summary: str
    steps: list[GrowthFunnelStep] = Field(default_factory=list)
    top_surfaces: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    recent_events: list[GrowthEventRecord] = Field(default_factory=list)


class LaunchCopyVariant(BaseModel):
    variant_id: str
    channel: str
    headline: str
    body: str
    cta_label: str
    cta_path: str
    tracking_event: GrowthEventType = GrowthEventType.share_cta


class LaunchChannelPlaybook(BaseModel):
    channel: str
    audience: str
    angle: str
    post_timing: str
    copy_variants: list[LaunchCopyVariant] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    success_metric: str


class LaunchCampaignKit(BaseModel):
    kit_version: str = "specpilot.launch_kit.v1"
    generated_at: str
    category: Category | None = None
    audience: str
    offer: str
    positioning: str
    hero_message: str
    primary_cta: str
    primary_cta_path: str
    proof_points: list[str] = Field(default_factory=list)
    target_segments: list[str] = Field(default_factory=list)
    channel_playbooks: list[LaunchChannelPlaybook] = Field(default_factory=list)
    cta_experiments: list[str] = Field(default_factory=list)
    launch_checklist: list[str] = Field(default_factory=list)
    risk_disclosures: list[str] = Field(default_factory=list)
    measurement_plan: list[str] = Field(default_factory=list)


class LaunchDistributionSlot(BaseModel):
    slot_id: str
    phase: str
    channel: str
    timing: str
    audience: str
    priority: int = Field(ge=1, le=10)
    status: CheckStatus
    headline: str
    body: str
    cta_label: str
    cta_path: str
    copy_text: str
    tracking_event: GrowthEventType = GrowthEventType.share_cta
    success_metric: str
    proof_to_attach: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)


class LaunchDistributionPlan(BaseModel):
    plan_version: str = "specpilot.launch_distribution_plan.v1"
    workspace_id: str
    generated_at: str
    category: Category | None = None
    audience: str
    launch_window: str
    status: CheckStatus
    distribution_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    primary_cta: str
    priority_channels: list[str] = Field(default_factory=list)
    experiment_to_promote: str = ""
    slots: list[LaunchDistributionSlot] = Field(default_factory=list)
    measurement_events: list[str] = Field(default_factory=list)
    risk_controls: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class LaunchExperimentVariantRequest(BaseModel):
    label: str = Field(min_length=1)
    headline: str = Field(min_length=2)
    body: str = Field(min_length=2)
    cta_label: str = Field(min_length=1)
    cta_path: str = "/"
    allocation_percent: int = Field(default=50, ge=1, le=100)


class LaunchExperimentRequest(BaseModel):
    name: str = Field(min_length=2)
    channel: str = "community"
    audience: str = "individual_buyer"
    hypothesis: str = Field(min_length=2)
    primary_metric: GrowthEventType = GrowthEventType.subscription_cta
    target_surface: str = "launch-page"
    category: Category | None = None
    variants: list[LaunchExperimentVariantRequest] = Field(default_factory=list)


class LaunchExperimentEventRequest(BaseModel):
    variant_id: str = Field(min_length=2)
    event_type: str = "impression"
    trace_id: str | None = None
    source: str = "web"
    surface: str = "launch-experiment"
    label: str = ""
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class LaunchExperimentEvent(BaseModel):
    event_id: str
    experiment_id: str
    workspace_id: str
    variant_id: str
    event_type: str
    trace_id: str | None = None
    source: str
    surface: str
    label: str = ""
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)
    created_at: str


class LaunchExperimentVariant(BaseModel):
    variant_id: str
    label: str
    headline: str
    body: str
    cta_label: str
    cta_path: str
    allocation_percent: int = Field(ge=1, le=100)
    impressions: int = 0
    conversions: int = 0
    conversion_rate: float = 0
    status: CheckStatus = CheckStatus.warning
    evidence: str = ""
    recommendation: str = ""


class LaunchExperiment(BaseModel):
    experiment_id: str
    workspace_id: str = "demo"
    name: str
    channel: str
    audience: str
    hypothesis: str
    primary_metric: GrowthEventType
    target_surface: str
    category: Category | None = None
    status: CheckStatus = CheckStatus.warning
    winning_variant_id: str | None = None
    created_at: str
    updated_at: str
    variants: list[LaunchExperimentVariant] = Field(default_factory=list)


class LaunchExperimentDashboard(BaseModel):
    dashboard_version: str = "specpilot.launch_experiment_hub.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    experiment_count: int = 0
    active_experiment_count: int = 0
    total_impressions: int = 0
    total_conversions: int = 0
    conversion_rate: float = 0
    best_variant_label: str = ""
    summary: str
    experiments: list[LaunchExperiment] = Field(default_factory=list)
    recommended_experiments: list[LaunchExperiment] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    recent_events: list[LaunchExperimentEvent] = Field(default_factory=list)


class LaunchPulseMetric(BaseModel):
    key: str
    label: str
    value: int | float | str
    unit: str = ""
    status: CheckStatus = CheckStatus.warning
    detail: str


class LaunchPulseSignal(BaseModel):
    area: str
    label: str
    status: CheckStatus
    score: float = Field(ge=0, le=100)
    evidence: str
    recommendation: str


class LaunchPulseDashboard(BaseModel):
    pulse_version: str = "specpilot.launch_pulse.v1"
    workspace_id: str
    generated_at: str
    pulse_score: float = Field(ge=0, le=100)
    status: CheckStatus
    headline: str
    summary: str
    metrics: list[LaunchPulseMetric] = Field(default_factory=list)
    signals: list[LaunchPulseSignal] = Field(default_factory=list)
    hot_surfaces: list[str] = Field(default_factory=list)
    top_actions: list[str] = Field(default_factory=list)
    recent_feedback: list[FeedbackRecord] = Field(default_factory=list)
    recent_growth_events: list[GrowthEventRecord] = Field(default_factory=list)


class LaunchWarRoomSignal(BaseModel):
    key: str
    label: str
    status: CheckStatus
    metric: str
    evidence: str
    owner: str
    next_action: str


class LaunchWarRoomPlay(BaseModel):
    play_id: str
    label: str
    status: CheckStatus
    trigger: str
    action: str
    expected_impact: str
    owner: str


class LaunchWarRoomDashboard(BaseModel):
    war_room_version: str = "specpilot.launch_war_room.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    command_score: float = Field(ge=0, le=100)
    decision: str
    headline: str
    summary: str
    metric_cards: dict[str, int | float | str] = Field(default_factory=dict)
    signals: list[LaunchWarRoomSignal] = Field(default_factory=list)
    plays: list[LaunchWarRoomPlay] = Field(default_factory=list)
    escalation_paths: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class LaunchWeekRecapWin(BaseModel):
    key: str
    label: str
    metric: str
    evidence: str
    repeat_action: str


class LaunchWeekRecapRisk(BaseModel):
    key: str
    label: str
    status: CheckStatus
    evidence: str
    mitigation: str
    owner: str


class LaunchWeekRecapDashboard(BaseModel):
    recap_version: str = "specpilot.launch_week_recap.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    recap_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    metric_cards: dict[str, int | float | str] = Field(default_factory=dict)
    wins: list[LaunchWeekRecapWin] = Field(default_factory=list)
    risks: list[LaunchWeekRecapRisk] = Field(default_factory=list)
    channel_moves: list[str] = Field(default_factory=list)
    founder_update: str
    next_actions: list[str] = Field(default_factory=list)


class LaunchCommunityReplyTemplate(BaseModel):
    key: str
    label: str
    trigger: str
    tone: str
    copy_text: str
    cta_label: str
    cta_path: str
    tracking_event: str


class LaunchCommunityRisk(BaseModel):
    key: str
    label: str
    status: CheckStatus
    evidence: str
    response_rule: str


class LaunchCommunityKit(BaseModel):
    kit_version: str = "specpilot.launch_community_kit.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    response_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    metric_cards: dict[str, int | float | str] = Field(default_factory=dict)
    pinned_update: str
    reply_templates: list[LaunchCommunityReplyTemplate] = Field(default_factory=list)
    risks: list[LaunchCommunityRisk] = Field(default_factory=list)
    tracking_events: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class LaunchMediaAsset(BaseModel):
    key: str
    label: str
    kind: str
    path: str
    usage: str
    alt_text: str
    tracking_event: str


class LaunchMediaPitch(BaseModel):
    channel: str
    audience: str
    headline: str
    body: str
    cta_label: str
    cta_path: str
    copy_text: str


class LaunchMediaKit(BaseModel):
    kit_version: str = "specpilot.launch_media_kit.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    media_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    metric_cards: dict[str, int | float | str] = Field(default_factory=dict)
    hero_statement: str
    proof_points: list[str] = Field(default_factory=list)
    assets: list[LaunchMediaAsset] = Field(default_factory=list)
    pitches: list[LaunchMediaPitch] = Field(default_factory=list)
    usage_guidelines: list[str] = Field(default_factory=list)
    tracking_events: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class PublicAcquisitionSurface(BaseModel):
    key: str
    label: str
    path: str
    channel: str
    status: CheckStatus
    readiness_score: float = Field(ge=0, le=100)
    primary_cta: str
    proof: str
    metric: str
    next_action: str


class PublicAcquisitionHub(BaseModel):
    hub_version: str = "specpilot.public_acquisition_hub.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    launch_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    primary_cta: str
    primary_cta_path: str
    surfaces: list[PublicAcquisitionSurface] = Field(default_factory=list)
    seo_paths: list[str] = Field(default_factory=list)
    channel_actions: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    recent_growth_events: list[GrowthEventRecord] = Field(default_factory=list)


class PublicConversionStage(BaseModel):
    key: str
    label: str
    status: CheckStatus
    metric: str
    insight: str
    next_action: str


class PublicConversionBoard(BaseModel):
    board_version: str = "specpilot.public_conversion_board.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    conversion_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    metric_cards: dict[str, int | float | str] = Field(default_factory=dict)
    stages: list[PublicConversionStage] = Field(default_factory=list)
    priority_surfaces: list[PublicAcquisitionSurface] = Field(default_factory=list)
    channel_actions: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    recent_growth_events: list[GrowthEventRecord] = Field(default_factory=list)


class RetentionSignal(BaseModel):
    key: str
    label: str
    status: CheckStatus
    score: float = Field(ge=0, le=100)
    metric: str
    insight: str
    next_action: str


class RetentionPlay(BaseModel):
    play_id: str
    label: str
    audience: str
    trigger: str
    channel: str
    cta_label: str
    cta_target: str
    expected_impact: str
    evidence: list[str] = Field(default_factory=list)


class RetentionHubDashboard(BaseModel):
    hub_version: str = "specpilot.retention_hub.v1"
    workspace_id: str
    generated_at: str
    status: CheckStatus
    retention_score: float = Field(ge=0, le=100)
    headline: str
    summary: str
    metric_cards: dict[str, int | float | str] = Field(default_factory=dict)
    signals: list[RetentionSignal] = Field(default_factory=list)
    plays: list[RetentionPlay] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    recent_events: list[GrowthEventRecord] = Field(default_factory=list)
    recent_advisor_answers: list["ReportAdvisorAnswer"] = Field(default_factory=list)
    recent_purchase_outcomes: list["PurchaseOutcome"] = Field(default_factory=list)


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
    sla_due_at: str | None = None
    is_overdue: bool = False
    completed_at: str | None = None
    completion_summary: str = ""
    created_at: str


class BetaBacklogActionRequest(BaseModel):
    status: BetaBacklogStatus = BetaBacklogStatus.in_progress
    assignee: str = ""
    note: str = ""
    sla_due_at: str | None = None
    completion_summary: str = ""


class BetaBacklogAction(BaseModel):
    backlog_id: str
    workspace_id: str = "demo"
    status: BetaBacklogStatus
    assignee: str = ""
    note: str = ""
    sla_due_at: str | None = None
    completed_at: str | None = None
    completion_summary: str = ""
    updated_at: str


class BetaBacklogSummary(BaseModel):
    workspace_id: str = "demo"
    total_count: int = 0
    open_count: int = 0
    in_progress_count: int = 0
    done_count: int = 0
    dismissed_count: int = 0
    overdue_count: int = 0
    due_soon_count: int = 0
    blocker_count: int = 0
    completion_summaries: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


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


class PurchaseDecisionBoardItem(BaseModel):
    report_id: str
    trace_id: str
    title: str
    owner_label: str
    category: Category
    purpose: str
    top_model_name: str | None = None
    final_pick_id: str | None = None
    decision_label: str
    board_status: CheckStatus
    recommended_action: str
    effective_price_krw: int | None = None
    target_price_krw: int | None = None
    price_gap_krw: int | None = None
    confidence: float = Field(ge=0, le=100)
    checkout_blocked: bool = False
    has_purchase_outcome: bool = False
    has_purchase_links: bool = False
    is_shared: bool = False
    next_steps: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class PurchaseDecisionBoard(BaseModel):
    workspace_id: str
    generated_at: str
    status: CheckStatus
    summary: str
    report_count: int = 0
    ready_to_buy_count: int = 0
    price_wait_count: int = 0
    checkout_blocked_count: int = 0
    missing_outcome_count: int = 0
    total_ready_value_krw: int = 0
    next_actions: list[str] = Field(default_factory=list)
    items: list[PurchaseDecisionBoardItem] = Field(default_factory=list)


class ReportAdvisorQuestionRequest(BaseModel):
    question: str = Field(min_length=2)
    context: str = ""
    selected_product_id: str | None = None
    buyer_stage: str = "pre_checkout"
    contact: str = ""


class ReportAdvisorAnswer(BaseModel):
    answer_id: str
    report_id: str
    trace_id: str
    workspace_id: str = "demo"
    question: str
    context: str = ""
    selected_product_id: str | None = None
    selected_model_name: str | None = None
    buyer_stage: str
    answer: str
    status: CheckStatus
    confidence: float = Field(ge=0, le=100)
    grounded_evidence: list[str] = Field(default_factory=list)
    cited_product_ids: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    contact_masked: str = ""
    created_at: str


class CheckoutReviewRequest(BaseModel):
    product_id: str | None = None
    confirmed_price_krw: int | None = Field(default=None, ge=0)
    acknowledged_risks: list[str] = Field(default_factory=list)
    seller_answers: dict[str, str] = Field(default_factory=dict)
    notes: str = ""


class CheckoutReviewItem(BaseModel):
    item_id: str
    label: str
    status: CheckStatus
    evidence: str
    required: bool = True


class CheckoutReview(BaseModel):
    review_id: str
    report_id: str
    trace_id: str
    workspace_id: str = "demo"
    product_id: str | None = None
    model_name: str | None = None
    confirmed_price_krw: int | None = None
    readiness_status: CheckStatus
    readiness_score: float = Field(ge=0, le=100)
    checkout_blocked: bool = False
    missing_acknowledgements: list[str] = Field(default_factory=list)
    seller_questions: list[str] = Field(default_factory=list)
    seller_answers: dict[str, str] = Field(default_factory=dict)
    items: list[CheckoutReviewItem] = Field(default_factory=list)
    final_recommendation: str
    notes: str = ""
    created_at: str


class PurchaseOutcomeRequest(BaseModel):
    product_id: str | None = None
    checkout_review_id: str | None = None
    status: PurchaseOutcomeStatus = PurchaseOutcomeStatus.purchased
    final_paid_price_krw: int | None = Field(default=None, ge=0)
    source_channel: str = "manual"
    reason: str = ""
    satisfaction: int | None = Field(default=None, ge=1, le=5)
    order_reference: str = ""
    notes: str = ""


class PurchaseOutcome(BaseModel):
    outcome_id: str
    report_id: str
    trace_id: str
    workspace_id: str = "demo"
    product_id: str | None = None
    model_name: str | None = None
    checkout_review_id: str | None = None
    status: PurchaseOutcomeStatus
    final_paid_price_krw: int | None = None
    expected_price_krw: int | None = None
    price_delta_krw: int | None = None
    source_channel: str = "manual"
    reason: str = ""
    satisfaction: int | None = None
    order_reference_masked: str = ""
    conversion_value_krw: int = 0
    learning_signal: str
    notes: str = ""
    created_at: str


class PurchaseLinkRequest(BaseModel):
    product_id: str | None = None
    seller_name: str = Field(min_length=1)
    url: str = Field(min_length=8)
    is_affiliate: bool = False
    affiliate_network: str = ""
    price_krw: int | None = Field(default=None, ge=0)
    shipping_fee_krw: int = Field(default=0, ge=0)
    coupon_krw: int = Field(default=0, ge=0)
    rank: int = Field(default=1, ge=1, le=20)
    active: bool = True
    notes: str = ""


class PurchaseLink(BaseModel):
    link_id: str
    report_id: str
    trace_id: str
    workspace_id: str = "demo"
    product_id: str
    model_name: str
    seller_name: str
    url: str
    is_affiliate: bool = False
    affiliate_network: str = ""
    price_krw: int | None = None
    shipping_fee_krw: int = 0
    coupon_krw: int = 0
    effective_price_krw: int | None = None
    rank: int = 1
    active: bool = True
    status: CheckStatus = CheckStatus.ok
    disclosure: str
    policy_warnings: list[str] = Field(default_factory=list)
    click_path: str
    click_count: int = 0
    notes: str = ""
    created_at: str
    updated_at: str


class PurchaseLinkClick(BaseModel):
    click_id: str
    link_id: str
    report_id: str
    workspace_id: str = "demo"
    product_id: str
    source: str = "public_report"
    referrer_host: str = ""
    user_agent_family: str = ""
    created_at: str


class PurchaseLinkGovernance(BaseModel):
    workspace_id: str
    report_id: str
    status: CheckStatus
    affiliate_link_count: int = 0
    non_affiliate_link_count: int = 0
    active_link_count: int = 0
    click_count: int = 0
    summary: str
    required_actions: list[str] = Field(default_factory=list)
    links: list[PurchaseLink] = Field(default_factory=list)


class CompletionReportBatchRequest(BaseModel):
    report_ids: list[str] = Field(default_factory=list)
    channel: str = "email"
    target: str = "ops@example.com"
    template_id: str | None = None
    recipient_group_id: str | None = None
    respect_unsubscribe: bool = True
    dry_run: bool = False
    limit: int = Field(default=20, ge=1, le=100)
    note: str = ""


class CompletionReportPreviewRequest(BaseModel):
    report_id: str
    channel: str = "email"
    target: str = "ops@example.com"
    template_id: str | None = None
    recipient_group_id: str | None = None
    respect_unsubscribe: bool = True


class CompletionReportPreview(BaseModel):
    workspace_id: str = "demo"
    report_id: str
    template_id: str | None = None
    recipient_group_id: str | None = None
    channel: str
    subject: str
    body: str
    targets_masked: list[str] = Field(default_factory=list)
    excluded_targets_masked: list[str] = Field(default_factory=list)
    target_count: int = 0
    excluded_count: int = 0
    public_path: str = "비공개 리포트"
    preview_generated_at: str


class CompletionReportTemplateRequest(BaseModel):
    name: str
    channel: str = "email"
    subject: str = "SpecPilot AI 구매 리포트"
    body: str = (
        "{title}\n"
        "추천 1순위: {top_model_name}\n"
        "공개 리포트: {public_path}\n"
        "결제 전 옵션명, 배송비, 카드 혜택을 다시 확인해 주세요."
    )
    enabled: bool = True


class CompletionReportTemplate(BaseModel):
    template_id: str
    workspace_id: str = "demo"
    name: str
    channel: str
    subject: str
    body: str
    enabled: bool = True
    created_at: str
    updated_at: str


class CompletionRecipientGroupRequest(BaseModel):
    name: str
    channel: str = "email"
    recipients: list[str] = Field(default_factory=list)
    unsubscribed_recipients: list[str] = Field(default_factory=list)
    unsubscribe_policy: str = "exclude_unsubscribed"
    enabled: bool = True
    description: str = ""


class CompletionRecipientGroup(BaseModel):
    group_id: str
    workspace_id: str = "demo"
    name: str
    channel: str
    recipients_masked: list[str] = Field(default_factory=list)
    recipient_count: int = 0
    unsubscribed_count: int = 0
    unsubscribe_policy: str = "exclude_unsubscribed"
    enabled: bool = True
    description: str = ""
    created_at: str
    updated_at: str


class CompletionReportDelivery(BaseModel):
    delivery_id: str
    batch_id: str
    report_id: str
    workspace_id: str = "demo"
    channel: str
    target_masked: str
    template_id: str | None = None
    recipient_group_id: str | None = None
    subject: str = ""
    status: str
    provider_message: str = ""
    retry_count: int = 0
    next_retry_at: str | None = None
    sent_at: str | None = None
    engagement_count: int = 0
    open_count: int = 0
    click_count: int = 0
    last_engaged_at: str | None = None
    tracking_token: str = ""
    tracking_pixel_path: str = ""
    tracking_click_path: str = ""
    created_at: str


class CompletionDeliveryEngagementRequest(BaseModel):
    event_type: str = "open"
    metadata: dict = Field(default_factory=dict)


class CompletionDeliveryEngagement(BaseModel):
    event_id: str
    delivery_id: str
    batch_id: str
    report_id: str
    workspace_id: str = "demo"
    event_type: str
    target_masked: str = ""
    metadata: dict = Field(default_factory=dict)
    created_at: str


class CompletionDeliveryProviderWebhookRequest(BaseModel):
    tracking_token: str = ""
    delivery_id: str | None = None
    provider_name: str = "email_provider"
    event_type: str = "delivered"
    provider_message: str = ""
    metadata: dict = Field(default_factory=dict)


class CompletionDeliveryProviderEvent(BaseModel):
    provider_event_id: str
    delivery_id: str
    batch_id: str
    report_id: str
    workspace_id: str = "demo"
    provider_name: str
    event_type: str
    delivery_status: str
    provider_message: str = ""
    metadata: dict = Field(default_factory=dict)
    created_at: str


class CompletionReportBatch(BaseModel):
    batch_id: str
    workspace_id: str = "demo"
    status: str
    template_id: str | None = None
    recipient_group_id: str | None = None
    target_count: int = 0
    selected_count: int
    sent_count: int = 0
    failed_count: int = 0
    dry_run: bool = False
    note: str = ""
    created_at: str
    deliveries: list[CompletionReportDelivery] = Field(default_factory=list)


class ReportShare(BaseModel):
    report_id: str
    share_token: str | None = None
    public_path: str | None = None
    is_public: bool = False
    shared_at: str | None = None
    share_views: int = 0


class ReportShareAssetVariant(BaseModel):
    channel: str
    label: str
    headline: str
    body: str
    cta: str
    copy_text: str


class ReportShareAssets(BaseModel):
    asset_version: str = "specpilot.share_assets.v1"
    workspace_id: str = "demo"
    report_id: str
    share_token: str | None = None
    public_path: str | None = None
    generated_at: str
    headline: str
    subheadline: str
    og_title: str
    og_description: str
    visual_card_text: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    reviewer_questions: list[str] = Field(default_factory=list)
    variants: list[ReportShareAssetVariant] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class PublicReportConversionCta(BaseModel):
    cta_version: str = "specpilot.public_report_conversion.v1"
    headline: str
    body: str
    primary_label: str
    primary_path: str
    secondary_label: str
    secondary_path: str
    source: str = "public-report"
    surface: str = "public_report"
    report_ref: str
    proof_points: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class PublicReport(BaseModel):
    report_id: str
    title: str
    top_model_name: str | None = None
    final_pick_id: str | None = None
    shared_at: str
    share_views: int = 0
    response: AnalyzeResponse
    purchase_links: list[PurchaseLink] = Field(default_factory=list)
    conversion_cta: PublicReportConversionCta


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
    contact_masked: str
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
    completion_report_batches: int = 0
    completion_report_deliveries: int = 0
    completion_delivery_opens: int = 0
    completion_delivery_clicks: int = 0
    completion_delivery_bounces: int = 0
    completion_delivery_complaints: int = 0
    completion_delivery_suppressions: int = 0
    checkout_reviews: int = 0
    checkout_blocked_reviews: int = 0
    checkout_ready_reviews: int = 0
    report_advisor_answers: int = 0
    report_advisor_warning_answers: int = 0
    purchase_outcomes: int = 0
    completed_purchase_outcomes: int = 0
    abandoned_purchase_outcomes: int = 0
    delayed_purchase_outcomes: int = 0
    returned_purchase_outcomes: int = 0
    purchase_links: int = 0
    affiliate_purchase_links: int = 0
    purchase_link_clicks: int = 0
    growth_events: int = 0
    growth_unique_traces: int = 0
    recommendation_card_clicks: int = 0
    alternative_scenario_clicks: int = 0
    share_cta_clicks: int = 0
    alert_cta_clicks: int = 0
    subscription_cta_clicks: int = 0
    purchase_conversion_rate: float = 0
    average_final_price_delta_krw: float = 0
    purchase_outcome_value_krw: int = 0
    source_monitors: int = 0
    source_refresh_runs: int = 0
    source_refresh_failures: int = 0
    source_provider_policies: int = 0
    source_provider_fetches: int = 0
    source_provider_blocked_fetches: int = 0
    trace_spans: int = 0
    feedback_count: int = 0
    beta_leads: int = 0
    subscription_intents: int = 0
    premium_subscription_intents: int = 0
    estimated_mrr_krw: int = 0
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


class LaunchGateCheck(BaseModel):
    area: str
    label: str
    status: CheckStatus
    metric: str
    recommendation: str


class LaunchGateDashboard(BaseModel):
    workspace_id: str
    generated_at: str
    decision: str
    status: CheckStatus
    launch_readiness_score: float = Field(ge=0, le=100)
    readiness_label: str
    summary: str
    required_actions: list[str] = Field(default_factory=list)
    checks: list[LaunchGateCheck] = Field(default_factory=list)
    metric_cards: dict[str, int | float | str] = Field(default_factory=dict)


class DataInventoryItem(BaseModel):
    table_name: str
    label: str
    record_count: int = 0
    pii_scope: str
    retention_days: int
    earliest_created_at: str | None = None
    latest_created_at: str | None = None
    status: CheckStatus = CheckStatus.ok
    recommendation: str


class DataGovernanceDashboard(BaseModel):
    workspace_id: str
    generated_at: str
    status: CheckStatus
    summary: str
    total_records: int = 0
    raw_contact_surfaces: int = 0
    masked_contact_surfaces: int = 0
    retention_actions: list[str] = Field(default_factory=list)
    deletion_controls: list[str] = Field(default_factory=list)
    inventory: list[DataInventoryItem] = Field(default_factory=list)


class IntegrationProviderRequest(BaseModel):
    provider_name: str = Field(min_length=2)
    category: IntegrationCategory
    status: IntegrationStatus = IntegrationStatus.configured
    credential_status: str = "not_connected"
    rate_limit_per_hour: int = Field(default=60, ge=0, le=100000)
    retention_days: int = Field(default=30, ge=0, le=3650)
    endpoint: str = ""
    evidence: str = ""
    notes: str = ""


class IntegrationProvider(BaseModel):
    integration_id: str
    workspace_id: str
    provider_name: str
    category: IntegrationCategory
    status: IntegrationStatus
    credential_status: str
    rate_limit_per_hour: int
    retention_days: int
    endpoint: str = ""
    evidence: str = ""
    notes: str = ""
    created_at: str
    updated_at: str
    last_verified_at: str | None = None


class IntegrationReadinessCheck(BaseModel):
    category: IntegrationCategory
    label: str
    status: CheckStatus
    provider_name: str | None = None
    metric: str
    recommendation: str


class IntegrationReadinessDashboard(BaseModel):
    workspace_id: str
    generated_at: str
    readiness_score: float = Field(ge=0, le=100)
    status: CheckStatus
    verified_count: int = 0
    configured_count: int = 0
    blocker_count: int = 0
    mock_count: int = 0
    required_count: int = 0
    summary: str
    required_actions: list[str] = Field(default_factory=list)
    providers: list[IntegrationProvider] = Field(default_factory=list)
    checks: list[IntegrationReadinessCheck] = Field(default_factory=list)


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
    shipping_fee_krw: int | None = None
    coupon_or_card_benefit_krw: int | None = None
    effective_price_krw: int | None = None
    availability_status: str = "unknown"
    model_match_status: CheckStatus = CheckStatus.warning
    seller: str | None = None
    evidence_text: str
    confidence: float = Field(ge=0, le=1)
    collected_at: str
    needs_review: bool = False
    risk_flags: list[str] = Field(default_factory=list)
    extraction_signals: list[str] = Field(default_factory=list)


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
