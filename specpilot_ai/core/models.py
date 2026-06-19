from enum import StrEnum

from pydantic import BaseModel, Field


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
    final_pick_id: str | None = None


class AnalyzeResponse(BaseModel):
    criteria: PurchaseCriteria
    steps: list[AgentStep]
    report: PurchaseReport
    graph_trace_id: str
    trace_events: list[TraceEvent] = Field(default_factory=list)


class ProductBrief(BaseModel):
    name: str
    one_liner: str
    target_users: list[str]
    core_workflows: list[str]
    mvp_categories: list[Category]
    stack: list[str]
