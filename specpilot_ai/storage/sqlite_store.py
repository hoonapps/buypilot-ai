import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from specpilot_ai.core.config import Settings
from specpilot_ai.core.models import (
    AgentStep,
    AlertDeliveryAttempt,
    AlertDeliveryEvent,
    AlertDispatchResponse,
    AlertEvaluationResponse,
    AlertNotificationChannel,
    AlertNotificationChannelRequest,
    AlertSubscription,
    AnalysisQualityAudit,
    AnalyzeResponse,
    BetaBacklogAction,
    BetaBacklogActionRequest,
    BetaBacklogItem,
    BetaBacklogStatus,
    BetaBacklogSummary,
    BetaCohort,
    BetaCohortReport,
    BetaCohortRequest,
    BetaLead,
    BetaLeadRequest,
    BetaReadinessCheck,
    BetaReadinessDashboard,
    Category,
    CheckoutReview,
    CheckoutReviewItem,
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
    CompletionReportDelivery,
    CompletionReportPreview,
    CompletionReportPreviewRequest,
    CompletionReportTemplate,
    CompletionReportTemplateRequest,
    DataGovernanceDashboard,
    DataInventoryItem,
    FeedbackRecord,
    FeedbackRequest,
    GrowthEventRecord,
    GrowthEventRequest,
    GrowthEventType,
    GrowthFunnelDashboard,
    GrowthFunnelStep,
    IntegrationCategory,
    IntegrationProvider,
    IntegrationProviderRequest,
    IntegrationReadinessCheck,
    IntegrationReadinessDashboard,
    IntegrationStatus,
    LaunchExperiment,
    LaunchExperimentDashboard,
    LaunchExperimentEvent,
    LaunchExperimentEventRequest,
    LaunchExperimentRequest,
    LaunchExperimentVariant,
    LaunchGateCheck,
    LaunchGateDashboard,
    LaunchPulseDashboard,
    LaunchPulseMetric,
    LaunchPulseSignal,
    ObservabilityDispatchResponse,
    ObservabilityExportRecord,
    ObservabilityExportRequest,
    OperationsMetrics,
    OpsLearningDashboard,
    OpsLearningInsight,
    OpsRegressionDashboard,
    OpsRegressionPeriod,
    PricingDashboard,
    PricingPlan,
    ProviderReliabilityMetric,
    ProviderReviewStatus,
    PublicAcquisitionHub,
    PublicAcquisitionSurface,
    PublicObjectionAnswer,
    PublicProofAsset,
    PublicProofEvidence,
    PublicProofHub,
    PublicReport,
    PublicReportConversionCta,
    PurchaseDecisionBoard,
    PurchaseDecisionBoardItem,
    PurchaseLink,
    PurchaseLinkClick,
    PurchaseLinkGovernance,
    PurchaseLinkRequest,
    PurchaseOutcome,
    PurchaseOutcomeRequest,
    PurchaseOutcomeStatus,
    QualityDashboard,
    ReferralLeaderboardItem,
    ReportAdvisorAnswer,
    ReportAdvisorQuestionRequest,
    ReportShare,
    ReportShareAssets,
    ReportShareAssetVariant,
    RetentionHubDashboard,
    RetentionPlay,
    RetentionSignal,
    ReviewDecision,
    ReviewQueueItem,
    ReviewStatus,
    SavedReportDetail,
    SavedReportSummary,
    SourceCandidate,
    SourceMonitor,
    SourceMonitorRequest,
    SourceProviderFetchLog,
    SourceProviderPolicy,
    SourceProviderPolicyRequest,
    SourceRefreshRun,
    SubscriptionIntent,
    SubscriptionIntentRequest,
    TraceEvent,
    TraceRunSummary,
    TraceSpanRecord,
    WaitlistReferral,
    WaitlistReferralDashboard,
    WaitlistReferralRequest,
)

SUPPORTED_ALERT_CHANNELS = {"email", "webhook", "sms"}
DATA_INVENTORY_SPECS = [
    {
        "table_name": "analysis_runs",
        "label": "분석 요청/결과",
        "pii_scope": "none",
        "retention_days": 180,
        "created_column": "created_at",
    },
    {
        "table_name": "saved_reports",
        "label": "저장 리포트와 공유 토큰",
        "pii_scope": "workspace_scoped",
        "retention_days": 180,
        "created_column": "created_at",
    },
    {
        "table_name": "report_advisor_answers",
        "label": "저장 리포트 구매 상담",
        "pii_scope": "masked_contact",
        "retention_days": 180,
        "created_column": "created_at",
    },
    {
        "table_name": "checkout_reviews",
        "label": "결제 전 검수",
        "pii_scope": "workspace_scoped",
        "retention_days": 180,
        "created_column": "created_at",
    },
    {
        "table_name": "purchase_outcomes",
        "label": "실제 구매 결과",
        "pii_scope": "masked_order",
        "retention_days": 365,
        "created_column": "created_at",
    },
    {
        "table_name": "alert_subscriptions",
        "label": "가격 알림 구독",
        "pii_scope": "raw_contact",
        "retention_days": 90,
        "created_column": "created_at",
    },
    {
        "table_name": "alert_delivery_events",
        "label": "목표가 알림 이벤트",
        "pii_scope": "masked_contact",
        "retention_days": 90,
        "created_column": "created_at",
    },
    {
        "table_name": "alert_delivery_attempts",
        "label": "알림 발송 시도",
        "pii_scope": "masked_contact",
        "retention_days": 90,
        "created_column": "created_at",
    },
    {
        "table_name": "completion_report_deliveries",
        "label": "완료 리포트 발송",
        "pii_scope": "masked_contact",
        "retention_days": 90,
        "created_column": "created_at",
    },
    {
        "table_name": "completion_delivery_engagement",
        "label": "완료 리포트 열람/클릭",
        "pii_scope": "masked_contact",
        "retention_days": 90,
        "created_column": "created_at",
    },
    {
        "table_name": "user_feedback",
        "label": "사용자 피드백",
        "pii_scope": "masked_contact",
        "retention_days": 365,
        "created_column": "created_at",
    },
    {
        "table_name": "beta_leads",
        "label": "베타 신청 리드",
        "pii_scope": "masked_contact",
        "retention_days": 365,
        "created_column": "created_at",
    },
    {
        "table_name": "subscription_intents",
        "label": "요금제 관심 등록",
        "pii_scope": "masked_contact",
        "retention_days": 365,
        "created_column": "created_at",
    },
    {
        "table_name": "growth_events",
        "label": "제품 성장 퍼널 이벤트",
        "pii_scope": "workspace_scoped",
        "retention_days": 180,
        "created_column": "created_at",
    },
    {
        "table_name": "launch_experiments",
        "label": "출시 CTA 실험",
        "pii_scope": "workspace_scoped",
        "retention_days": 180,
        "created_column": "created_at",
    },
    {
        "table_name": "launch_experiment_events",
        "label": "출시 CTA 실험 이벤트",
        "pii_scope": "workspace_scoped",
        "retention_days": 180,
        "created_column": "created_at",
    },
    {
        "table_name": "observability_exports",
        "label": "관측성 export payload",
        "pii_scope": "workspace_scoped",
        "retention_days": 30,
        "created_column": "created_at",
    },
]


class SpecPilotStore:
    def __init__(self, settings: Settings) -> None:
        self.db_path = Path(settings.storage_path)
        self.public_site_url = settings.public_site_url.strip().rstrip("/")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def save_analysis(self, response: AnalyzeResponse) -> None:
        self.save_analysis_for_workspace("demo", response)

    def save_analysis_for_workspace(self, workspace_id: str, response: AnalyzeResponse) -> None:
        now = _now()
        payload = response.model_dump_json()
        final_pick = response.report.final_pick_id
        top = (
            response.report.top_recommendations[0]
            if response.report.top_recommendations
            else None
        )
        top_model = top.product.model_name if top else None
        top_score = top.score.total_score if top else 0
        audit = response.quality_audit
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO analysis_runs (
                    trace_id, workspace_id, category, purpose, budget_krw, final_pick_id,
                    top_model_name, top_score, quality_score, estimated_cost_krw,
                    warning_count, blocker_count, quality_audit_json, response_json,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(trace_id) DO UPDATE SET
                    workspace_id=excluded.workspace_id,
                    category=excluded.category,
                    purpose=excluded.purpose,
                    budget_krw=excluded.budget_krw,
                    final_pick_id=excluded.final_pick_id,
                    top_model_name=excluded.top_model_name,
                    top_score=excluded.top_score,
                    quality_score=excluded.quality_score,
                    estimated_cost_krw=excluded.estimated_cost_krw,
                    warning_count=excluded.warning_count,
                    blocker_count=excluded.blocker_count,
                    quality_audit_json=excluded.quality_audit_json,
                    response_json=excluded.response_json,
                    updated_at=excluded.updated_at
                """,
                (
                    response.graph_trace_id,
                    workspace_id,
                    response.criteria.category.value,
                    response.criteria.purpose,
                    response.criteria.budget_krw,
                    final_pick,
                    top_model,
                    top_score,
                    audit.quality_score if audit else 0,
                    audit.estimated_cost_krw if audit else 0,
                    audit.warning_count if audit else 0,
                    audit.blocker_count if audit else 0,
                    audit.model_dump_json() if audit else "{}",
                    payload,
                    now,
                    now,
                ),
            )
            self._replace_trace_spans(
                conn,
                workspace_id,
                response.graph_trace_id,
                response.trace_events,
            )

    def get_analysis(self, trace_id: str) -> AnalyzeResponse | None:
        return self.get_analysis_for_workspace("demo", trace_id)

    def get_analysis_for_workspace(
        self,
        workspace_id: str,
        trace_id: str,
    ) -> AnalyzeResponse | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT response_json
                FROM analysis_runs
                WHERE trace_id = ? AND workspace_id = ?
                """,
                (trace_id, workspace_id),
            ).fetchone()
        if row is None:
            return None
        return AnalyzeResponse.model_validate_json(row["response_json"])

    def save_report(
        self,
        response: AnalyzeResponse,
        *,
        title: str,
        owner_label: str,
        notes: str,
    ) -> SavedReportSummary:
        return self.save_report_for_workspace(
            "demo",
            response,
            title=title,
            owner_label=owner_label,
            notes=notes,
        )

    def save_report_for_workspace(
        self,
        workspace_id: str,
        response: AnalyzeResponse,
        *,
        title: str,
        owner_label: str,
        notes: str,
    ) -> SavedReportSummary:
        self.save_analysis_for_workspace(workspace_id, response)
        now = _now()
        report_id = f"report_{uuid4().hex[:12]}"
        top = (
            response.report.top_recommendations[0]
            if response.report.top_recommendations
            else None
        )
        top_model = top.product.model_name if top else None
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO saved_reports (
                    report_id, trace_id, workspace_id, title, owner_label, notes,
                    final_pick_id, top_model_name, share_token, shared_at, share_views,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, 0, ?, ?)
                """,
                (
                    report_id,
                    response.graph_trace_id,
                    workspace_id,
                    title,
                    owner_label,
                    notes,
                    response.report.final_pick_id,
                    top_model,
                    now,
                    now,
                ),
            )
        return SavedReportSummary(
            report_id=report_id,
            trace_id=response.graph_trace_id,
            workspace_id=workspace_id,
            title=title,
            owner_label=owner_label,
            final_pick_id=response.report.final_pick_id,
            top_model_name=top_model,
            share_token=None,
            shared_at=None,
            share_views=0,
            created_at=now,
            updated_at=now,
        )

    def list_reports(self, limit: int = 20) -> list[SavedReportSummary]:
        return self.list_reports_for_workspace("demo", limit=limit)

    def list_reports_for_workspace(
        self,
        workspace_id: str,
        limit: int = 20,
    ) -> list[SavedReportSummary]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT report_id, trace_id, workspace_id, title, owner_label, final_pick_id,
                       top_model_name, share_token, shared_at, share_views, created_at, updated_at
                FROM saved_reports
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_saved_report_summary_from_row(row) for row in rows]

    def purchase_decision_board_for_workspace(
        self,
        workspace_id: str,
        limit: int = 20,
    ) -> PurchaseDecisionBoard:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT sr.*, ar.response_json,
                       COUNT(DISTINCT cr.review_id) AS checkout_review_count,
                       SUM(
                           CASE
                               WHEN cr.checkout_blocked = 1 THEN 1
                               ELSE 0
                           END
                       ) AS checkout_blocked_count,
                       (
                           SELECT latest_cr.checkout_blocked
                           FROM checkout_reviews latest_cr
                           WHERE latest_cr.report_id = sr.report_id
                             AND latest_cr.workspace_id = sr.workspace_id
                           ORDER BY latest_cr.created_at DESC
                           LIMIT 1
                       ) AS latest_checkout_blocked,
                       COUNT(DISTINCT po.outcome_id) AS purchase_outcome_count,
                       COUNT(DISTINCT pl.link_id) AS purchase_link_count
                FROM saved_reports sr
                JOIN analysis_runs ar
                    ON ar.trace_id = sr.trace_id AND ar.workspace_id = sr.workspace_id
                LEFT JOIN checkout_reviews cr
                    ON cr.report_id = sr.report_id AND cr.workspace_id = sr.workspace_id
                LEFT JOIN purchase_outcomes po
                    ON po.report_id = sr.report_id AND po.workspace_id = sr.workspace_id
                LEFT JOIN purchase_links pl
                    ON pl.report_id = sr.report_id AND pl.workspace_id = sr.workspace_id
                WHERE sr.workspace_id = ?
                GROUP BY sr.report_id
                ORDER BY sr.created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        items = [_decision_board_item_from_row(row) for row in rows]
        ready_items = [item for item in items if item.board_status == CheckStatus.ok]
        price_wait_count = sum(
            1 for item in items if "가격" in item.decision_label or item.price_gap_krw
        )
        checkout_blocked_count = sum(1 for item in items if item.checkout_blocked)
        missing_outcome_count = sum(1 for item in items if not item.has_purchase_outcome)
        status = _decision_board_status(items)
        return PurchaseDecisionBoard(
            workspace_id=workspace_id,
            generated_at=_now(),
            status=status,
            summary=_decision_board_summary(items, status),
            report_count=len(items),
            ready_to_buy_count=len(ready_items),
            price_wait_count=price_wait_count,
            checkout_blocked_count=checkout_blocked_count,
            missing_outcome_count=missing_outcome_count,
            total_ready_value_krw=sum(
                item.effective_price_krw or 0 for item in ready_items
            ),
            next_actions=_decision_board_next_actions(items),
            items=items,
        )

    def upsert_completion_report_template_for_workspace(
        self,
        workspace_id: str,
        request: CompletionReportTemplateRequest,
    ) -> CompletionReportTemplate:
        now = _now()
        channel = request.channel.strip().lower() or "email"
        template_id = f"template_{uuid4().hex[:12]}"
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT template_id, created_at
                FROM completion_report_templates
                WHERE workspace_id = ? AND name = ?
                """,
                (workspace_id, request.name),
            ).fetchone()
            if row is not None:
                template_id = row["template_id"]
                created_at = row["created_at"]
            else:
                created_at = now
            conn.execute(
                """
                INSERT INTO completion_report_templates (
                    template_id, workspace_id, name, channel, subject, body,
                    enabled, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(workspace_id, name) DO UPDATE SET
                    channel = excluded.channel,
                    subject = excluded.subject,
                    body = excluded.body,
                    enabled = excluded.enabled,
                    updated_at = excluded.updated_at
                """,
                (
                    template_id,
                    workspace_id,
                    request.name.strip() or "기본 완료 리포트",
                    channel,
                    request.subject,
                    request.body,
                    int(request.enabled),
                    created_at,
                    now,
                ),
            )
        return CompletionReportTemplate(
            template_id=template_id,
            workspace_id=workspace_id,
            name=request.name.strip() or "기본 완료 리포트",
            channel=channel,
            subject=request.subject,
            body=request.body,
            enabled=request.enabled,
            created_at=created_at,
            updated_at=now,
        )

    def list_completion_report_templates_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[CompletionReportTemplate]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM completion_report_templates
                WHERE workspace_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_completion_template_from_row(row) for row in rows]

    def upsert_completion_recipient_group_for_workspace(
        self,
        workspace_id: str,
        request: CompletionRecipientGroupRequest,
    ) -> CompletionRecipientGroup:
        now = _now()
        group_id = f"group_{uuid4().hex[:12]}"
        channel = request.channel.strip().lower() or "email"
        recipients = _normalized_recipients(request.recipients)
        unsubscribed = _normalized_recipients(request.unsubscribed_recipients)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT group_id, created_at
                FROM completion_recipient_groups
                WHERE workspace_id = ? AND name = ?
                """,
                (workspace_id, request.name),
            ).fetchone()
            if row is not None:
                group_id = row["group_id"]
                created_at = row["created_at"]
            else:
                created_at = now
            conn.execute(
                """
                INSERT INTO completion_recipient_groups (
                    group_id, workspace_id, name, channel, recipients_json,
                    unsubscribed_json, unsubscribe_policy, enabled, description,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(workspace_id, name) DO UPDATE SET
                    channel = excluded.channel,
                    recipients_json = excluded.recipients_json,
                    unsubscribed_json = excluded.unsubscribed_json,
                    unsubscribe_policy = excluded.unsubscribe_policy,
                    enabled = excluded.enabled,
                    description = excluded.description,
                    updated_at = excluded.updated_at
                """,
                (
                    group_id,
                    workspace_id,
                    request.name.strip() or "운영 수신자 그룹",
                    channel,
                    json.dumps(recipients, ensure_ascii=False),
                    json.dumps(unsubscribed, ensure_ascii=False),
                    request.unsubscribe_policy.strip() or "exclude_unsubscribed",
                    int(request.enabled),
                    request.description,
                    created_at,
                    now,
                ),
            )
        return CompletionRecipientGroup(
            group_id=group_id,
            workspace_id=workspace_id,
            name=request.name.strip() or "운영 수신자 그룹",
            channel=channel,
            recipients_masked=[_mask_target(item) for item in recipients],
            recipient_count=len(recipients),
            unsubscribed_count=len(unsubscribed),
            unsubscribe_policy=request.unsubscribe_policy.strip()
            or "exclude_unsubscribed",
            enabled=request.enabled,
            description=request.description,
            created_at=created_at,
            updated_at=now,
        )

    def list_completion_recipient_groups_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[CompletionRecipientGroup]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM completion_recipient_groups
                WHERE workspace_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_completion_recipient_group_from_row(row) for row in rows]

    def preview_completion_report_for_workspace(
        self,
        workspace_id: str,
        request: CompletionReportPreviewRequest,
    ) -> CompletionReportPreview | None:
        reports = self._select_completion_reports(
            workspace_id,
            report_ids=[request.report_id],
            limit=1,
        )
        if not reports:
            return None
        report = reports[0]
        template = self._completion_template(workspace_id, request.template_id)
        group = self._completion_recipient_group(workspace_id, request.recipient_group_id)
        channel = _completion_channel(request.channel, template=template, group=group)
        subject = _render_completion_text(_completion_subject(template), report)
        body = _render_completion_text(_completion_body(template), report)
        targets = _completion_targets(request, group)
        eligible = [
            target
            for target, is_unsubscribed in targets
            if not (is_unsubscribed and request.respect_unsubscribe)
        ]
        excluded = [
            target
            for target, is_unsubscribed in targets
            if is_unsubscribed and request.respect_unsubscribe
        ]
        return CompletionReportPreview(
            workspace_id=workspace_id,
            report_id=report.report_id,
            template_id=template["template_id"] if template else None,
            recipient_group_id=group["group_id"] if group else None,
            channel=channel,
            subject=subject,
            body=body,
            targets_masked=[_mask_target(target) for target in eligible],
            excluded_targets_masked=[_mask_target(target) for target in excluded],
            target_count=len(eligible),
            excluded_count=len(excluded),
            public_path=f"/r/{report.share_token}" if report.share_token else "비공개 리포트",
            preview_generated_at=_now(),
        )

    def create_completion_report_batch_for_workspace(
        self,
        workspace_id: str,
        request: CompletionReportBatchRequest,
    ) -> CompletionReportBatch:
        reports = self._select_completion_reports(
            workspace_id,
            report_ids=request.report_ids,
            limit=request.limit,
        )
        now = _now()
        batch_id = f"batch_{uuid4().hex[:12]}"
        template = self._completion_template(workspace_id, request.template_id)
        group = self._completion_recipient_group(workspace_id, request.recipient_group_id)
        channel = _completion_channel(request.channel, template=template, group=group)
        subject = _completion_subject(template)
        targets = _completion_targets(request, group)
        deliveries: list[CompletionReportDelivery] = []
        for report in reports:
            for target, is_unsubscribed in targets:
                retry_count = self._next_completion_retry_count(
                    workspace_id,
                    report.report_id,
                    channel,
                )
                if is_unsubscribed and request.respect_unsubscribe:
                    status = "skipped"
                    provider_message = "unsubscribe 정책에 따라 완료 리포트 발송을 제외했습니다."
                    next_retry_at = None
                else:
                    status, provider_message, next_retry_at = _completion_dispatch_status(
                        channel=channel,
                        target=target,
                        retry_count=retry_count,
                        dry_run=request.dry_run,
                        now=now,
                    )
                delivery = CompletionReportDelivery(
                    delivery_id=f"delivery_{uuid4().hex[:12]}",
                    batch_id=batch_id,
                    report_id=report.report_id,
                    workspace_id=workspace_id,
                    channel=channel,
                    target_masked=_mask_target(target),
                    template_id=template["template_id"] if template else None,
                    recipient_group_id=group["group_id"] if group else None,
                    subject=_render_completion_text(subject, report),
                    status=status,
                    provider_message=provider_message,
                    retry_count=retry_count,
                    next_retry_at=next_retry_at,
                    sent_at=now if status == "sent" else None,
                    tracking_token=f"trk_{uuid4().hex[:24]}",
                    created_at=now,
                )
                delivery.tracking_pixel_path = f"/t/o/{delivery.tracking_token}.png"
                delivery.tracking_click_path = f"/t/c/{delivery.tracking_token}"
                if delivery.status == "sent":
                    delivery.provider_message = (
                        f"{delivery.provider_message} "
                        f"tracking_pixel={delivery.tracking_pixel_path} "
                        f"tracking_click={delivery.tracking_click_path}"
                    )
                deliveries.append(delivery)
        sent_count = sum(1 for delivery in deliveries if delivery.status == "sent")
        failed_count = sum(1 for delivery in deliveries if delivery.status == "failed")
        batch_status = _completion_batch_status(
            selected_count=len(reports),
            target_count=len(targets),
            sent_count=sent_count,
            failed_count=failed_count,
            dry_run=request.dry_run,
        )
        batch = CompletionReportBatch(
            batch_id=batch_id,
            workspace_id=workspace_id,
            status=batch_status,
            template_id=template["template_id"] if template else None,
            recipient_group_id=group["group_id"] if group else None,
            target_count=len(targets),
            selected_count=len(reports),
            sent_count=sent_count,
            failed_count=failed_count,
            dry_run=request.dry_run,
            note=request.note,
            created_at=now,
            deliveries=deliveries,
        )
        if not request.dry_run and reports:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO completion_report_batches (
                        batch_id, workspace_id, status, selected_count, sent_count,
                        failed_count, dry_run, note, template_id, recipient_group_id,
                        target_count, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        batch.batch_id,
                        batch.workspace_id,
                        batch.status,
                        batch.selected_count,
                        batch.sent_count,
                        batch.failed_count,
                        int(batch.dry_run),
                        batch.note,
                        batch.template_id,
                        batch.recipient_group_id,
                        batch.target_count,
                        batch.created_at,
                    ),
                )
                for delivery in deliveries:
                    conn.execute(
                        """
                        INSERT INTO completion_report_deliveries (
                            delivery_id, batch_id, report_id, workspace_id, channel,
                            target_masked, template_id, recipient_group_id, subject,
                            status, provider_message, retry_count, next_retry_at,
                            sent_at, tracking_token, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            delivery.delivery_id,
                            delivery.batch_id,
                            delivery.report_id,
                            delivery.workspace_id,
                            delivery.channel,
                            delivery.target_masked,
                            delivery.template_id,
                            delivery.recipient_group_id,
                            delivery.subject,
                            delivery.status,
                            delivery.provider_message,
                            delivery.retry_count,
                            delivery.next_retry_at,
                            delivery.sent_at,
                            delivery.tracking_token,
                            delivery.created_at,
                        ),
                    )
        return batch

    def list_completion_report_batches_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[CompletionReportBatch]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM completion_report_batches
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
            batches = [_completion_batch_from_row(row) for row in rows]
            for batch in batches:
                delivery_rows = conn.execute(
                    """
                    SELECT d.*,
                           COUNT(e.event_id) AS engagement_count,
                           SUM(CASE WHEN e.event_type = 'open' THEN 1 ELSE 0 END) AS open_count,
                           SUM(CASE WHEN e.event_type = 'click' THEN 1 ELSE 0 END) AS click_count,
                           MAX(e.created_at) AS last_engaged_at
                    FROM completion_report_deliveries d
                    LEFT JOIN completion_delivery_engagement e
                        ON e.delivery_id = d.delivery_id AND e.workspace_id = d.workspace_id
                    WHERE d.batch_id = ? AND d.workspace_id = ?
                    GROUP BY d.delivery_id
                    ORDER BY d.created_at ASC
                    """,
                    (batch.batch_id, workspace_id),
                ).fetchall()
                batch.deliveries = [
                    _completion_delivery_from_row(row) for row in delivery_rows
                ]
        return batches

    def record_completion_delivery_engagement_for_workspace(
        self,
        workspace_id: str,
        delivery_id: str,
        request: CompletionDeliveryEngagementRequest,
    ) -> CompletionDeliveryEngagement | None:
        now = _now()
        event_type = _completion_engagement_type(request.event_type)
        with self._connect() as conn:
            delivery = conn.execute(
                """
                SELECT *
                FROM completion_report_deliveries
                WHERE workspace_id = ? AND delivery_id = ?
                """,
                (workspace_id, delivery_id),
            ).fetchone()
            if delivery is None:
                return None
            event = CompletionDeliveryEngagement(
                event_id=f"engage_{uuid4().hex[:12]}",
                delivery_id=delivery["delivery_id"],
                batch_id=delivery["batch_id"],
                report_id=delivery["report_id"],
                workspace_id=workspace_id,
                event_type=event_type,
                target_masked=delivery["target_masked"],
                metadata=request.metadata,
                created_at=now,
            )
            conn.execute(
                """
                INSERT INTO completion_delivery_engagement (
                    event_id, delivery_id, batch_id, report_id, workspace_id,
                    event_type, target_masked, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.delivery_id,
                    event.batch_id,
                    event.report_id,
                    event.workspace_id,
                    event.event_type,
                    event.target_masked,
                    json.dumps(event.metadata, ensure_ascii=False),
                    event.created_at,
                ),
            )
        return event

    def record_completion_delivery_engagement_by_tracking_token(
        self,
        tracking_token: str,
        event_type: str,
        metadata: dict | None = None,
    ) -> CompletionDeliveryEngagement | None:
        now = _now()
        normalized_event_type = _completion_engagement_type(event_type)
        with self._connect() as conn:
            delivery = conn.execute(
                """
                SELECT *
                FROM completion_report_deliveries
                WHERE tracking_token = ?
                """,
                (tracking_token,),
            ).fetchone()
            if delivery is None or delivery["status"] != "sent":
                return None
            event = CompletionDeliveryEngagement(
                event_id=f"engage_{uuid4().hex[:12]}",
                delivery_id=delivery["delivery_id"],
                batch_id=delivery["batch_id"],
                report_id=delivery["report_id"],
                workspace_id=delivery["workspace_id"],
                event_type=normalized_event_type,
                target_masked=delivery["target_masked"],
                metadata=metadata or {},
                created_at=now,
            )
            conn.execute(
                """
                INSERT INTO completion_delivery_engagement (
                    event_id, delivery_id, batch_id, report_id, workspace_id,
                    event_type, target_masked, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.delivery_id,
                    event.batch_id,
                    event.report_id,
                    event.workspace_id,
                    event.event_type,
                    event.target_masked,
                    json.dumps(event.metadata, ensure_ascii=False),
                    event.created_at,
                ),
            )
        return event

    def list_completion_delivery_engagement_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[CompletionDeliveryEngagement]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM completion_delivery_engagement
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_completion_engagement_from_row(row) for row in rows]

    def record_completion_delivery_provider_event(
        self,
        request: CompletionDeliveryProviderWebhookRequest,
    ) -> CompletionDeliveryProviderEvent | None:
        now = _now()
        event_type = _completion_provider_event_type(request.event_type)
        delivery_status = _completion_provider_delivery_status(event_type)
        with self._connect() as conn:
            delivery = conn.execute(
                """
                SELECT *
                FROM completion_report_deliveries
                WHERE (? != '' AND tracking_token = ?)
                   OR (? IS NOT NULL AND delivery_id = ?)
                """,
                (
                    request.tracking_token,
                    request.tracking_token,
                    request.delivery_id,
                    request.delivery_id,
                ),
            ).fetchone()
            if delivery is None:
                return None
            event = CompletionDeliveryProviderEvent(
                provider_event_id=f"provider_evt_{uuid4().hex[:12]}",
                delivery_id=delivery["delivery_id"],
                batch_id=delivery["batch_id"],
                report_id=delivery["report_id"],
                workspace_id=delivery["workspace_id"],
                provider_name=request.provider_name.strip() or "email_provider",
                event_type=event_type,
                delivery_status=delivery_status,
                provider_message=request.provider_message,
                metadata=request.metadata,
                created_at=now,
            )
            conn.execute(
                """
                INSERT INTO completion_delivery_provider_events (
                    provider_event_id, delivery_id, batch_id, report_id, workspace_id,
                    provider_name, event_type, delivery_status, provider_message,
                    metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.provider_event_id,
                    event.delivery_id,
                    event.batch_id,
                    event.report_id,
                    event.workspace_id,
                    event.provider_name,
                    event.event_type,
                    event.delivery_status,
                    event.provider_message,
                    json.dumps(event.metadata, ensure_ascii=False),
                    event.created_at,
                ),
            )
            conn.execute(
                """
                UPDATE completion_report_deliveries
                SET status = ?, provider_message = ?
                WHERE delivery_id = ? AND workspace_id = ?
                """,
                (
                    delivery_status,
                    _completion_provider_message(event, delivery["provider_message"]),
                    event.delivery_id,
                    event.workspace_id,
                ),
            )
        return event

    def list_completion_delivery_provider_events_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[CompletionDeliveryProviderEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM completion_delivery_provider_events
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_completion_provider_event_from_row(row) for row in rows]

    def get_report(self, report_id: str) -> SavedReportDetail | None:
        return self.get_report_for_workspace("demo", report_id)

    def get_report_for_workspace(
        self,
        workspace_id: str,
        report_id: str,
    ) -> SavedReportDetail | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT sr.*, ar.response_json
                FROM saved_reports sr
                JOIN analysis_runs ar ON ar.trace_id = sr.trace_id
                WHERE sr.report_id = ? AND sr.workspace_id = ?
                """,
                (report_id, workspace_id),
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        response = AnalyzeResponse.model_validate_json(data.pop("response_json"))
        return SavedReportDetail(
            report_id=data["report_id"],
            trace_id=data["trace_id"],
            workspace_id=data["workspace_id"],
            title=data["title"],
            owner_label=data["owner_label"],
            notes=data["notes"],
            final_pick_id=data["final_pick_id"],
            top_model_name=data["top_model_name"],
            share_token=data["share_token"],
            shared_at=data["shared_at"],
            share_views=data["share_views"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            response=response,
        )

    def create_report_advisor_answer_for_workspace(
        self,
        workspace_id: str,
        report_id: str,
        request: ReportAdvisorQuestionRequest,
    ) -> ReportAdvisorAnswer | None:
        report = self.get_report_for_workspace(workspace_id, report_id)
        if report is None:
            return None
        answer = _build_report_advisor_answer(report, request)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO report_advisor_answers (
                    answer_id, report_id, trace_id, workspace_id, question, context,
                    selected_product_id, selected_model_name, buyer_stage, answer,
                    status, confidence, grounded_evidence_json, cited_product_ids_json,
                    next_actions_json, contact_masked, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    answer.answer_id,
                    answer.report_id,
                    answer.trace_id,
                    answer.workspace_id,
                    answer.question,
                    answer.context,
                    answer.selected_product_id,
                    answer.selected_model_name,
                    answer.buyer_stage,
                    answer.answer,
                    answer.status.value,
                    answer.confidence,
                    json.dumps(answer.grounded_evidence, ensure_ascii=False),
                    json.dumps(answer.cited_product_ids, ensure_ascii=False),
                    json.dumps(answer.next_actions, ensure_ascii=False),
                    answer.contact_masked,
                    answer.created_at,
                ),
            )
        return answer

    def list_report_advisor_answers_for_workspace(
        self,
        workspace_id: str,
        report_id: str | None = None,
        limit: int = 50,
    ) -> list[ReportAdvisorAnswer]:
        if report_id:
            where = "workspace_id = ? AND report_id = ?"
            params: tuple[object, ...] = (workspace_id, report_id, limit)
        else:
            where = "workspace_id = ?"
            params = (workspace_id, limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                FROM report_advisor_answers
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [_report_advisor_answer_from_row(row) for row in rows]

    def create_checkout_review_for_workspace(
        self,
        workspace_id: str,
        report_id: str,
        request: CheckoutReviewRequest,
    ) -> CheckoutReview | None:
        report = self.get_report_for_workspace(workspace_id, report_id)
        if report is None:
            return None
        review = _build_checkout_review(report, request)
        if review is None:
            return None
        now = review.created_at
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO checkout_reviews (
                    review_id, report_id, trace_id, workspace_id, product_id, model_name,
                    confirmed_price_krw, readiness_status, readiness_score,
                    checkout_blocked, missing_acknowledgements_json, seller_questions_json,
                    seller_answers_json, items_json, final_recommendation, notes, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review.review_id,
                    review.report_id,
                    review.trace_id,
                    review.workspace_id,
                    review.product_id,
                    review.model_name,
                    review.confirmed_price_krw,
                    review.readiness_status.value,
                    review.readiness_score,
                    int(review.checkout_blocked),
                    json.dumps(review.missing_acknowledgements, ensure_ascii=False),
                    json.dumps(review.seller_questions, ensure_ascii=False),
                    json.dumps(review.seller_answers, ensure_ascii=False),
                    json.dumps(
                        [item.model_dump(mode="json") for item in review.items],
                        ensure_ascii=False,
                    ),
                    review.final_recommendation,
                    review.notes,
                    now,
                ),
            )
        return review

    def list_checkout_reviews_for_workspace(
        self,
        workspace_id: str,
        report_id: str | None = None,
        limit: int = 50,
    ) -> list[CheckoutReview]:
        if report_id:
            where = "workspace_id = ? AND report_id = ?"
            params: tuple[object, ...] = (workspace_id, report_id, limit)
        else:
            where = "workspace_id = ?"
            params = (workspace_id, limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                FROM checkout_reviews
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [_checkout_review_from_row(row) for row in rows]

    def create_purchase_outcome_for_workspace(
        self,
        workspace_id: str,
        report_id: str,
        request: PurchaseOutcomeRequest,
    ) -> PurchaseOutcome | None:
        report = self.get_report_for_workspace(workspace_id, report_id)
        if report is None:
            return None
        outcome = _build_purchase_outcome(report, request)
        if outcome is None:
            return None
        with self._connect() as conn:
            if outcome.checkout_review_id:
                checkout = conn.execute(
                    """
                    SELECT review_id
                    FROM checkout_reviews
                    WHERE review_id = ? AND report_id = ? AND workspace_id = ?
                    """,
                    (outcome.checkout_review_id, report_id, workspace_id),
                ).fetchone()
                if checkout is None:
                    return None
            conn.execute(
                """
                INSERT INTO purchase_outcomes (
                    outcome_id, report_id, trace_id, workspace_id, product_id,
                    model_name, checkout_review_id, status, final_paid_price_krw,
                    expected_price_krw, price_delta_krw, source_channel, reason,
                    satisfaction, order_reference_masked, conversion_value_krw,
                    learning_signal, notes, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    outcome.outcome_id,
                    outcome.report_id,
                    outcome.trace_id,
                    outcome.workspace_id,
                    outcome.product_id,
                    outcome.model_name,
                    outcome.checkout_review_id,
                    outcome.status.value,
                    outcome.final_paid_price_krw,
                    outcome.expected_price_krw,
                    outcome.price_delta_krw,
                    outcome.source_channel,
                    outcome.reason,
                    outcome.satisfaction,
                    outcome.order_reference_masked,
                    outcome.conversion_value_krw,
                    outcome.learning_signal,
                    outcome.notes,
                    outcome.created_at,
                ),
            )
        return outcome

    def list_purchase_outcomes_for_workspace(
        self,
        workspace_id: str,
        report_id: str | None = None,
        limit: int = 50,
    ) -> list[PurchaseOutcome]:
        if report_id:
            where = "workspace_id = ? AND report_id = ?"
            params: tuple[object, ...] = (workspace_id, report_id, limit)
        else:
            where = "workspace_id = ?"
            params = (workspace_id, limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                FROM purchase_outcomes
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [_purchase_outcome_from_row(row) for row in rows]

    def create_purchase_link_for_workspace(
        self,
        workspace_id: str,
        report_id: str,
        request: PurchaseLinkRequest,
    ) -> PurchaseLink | None:
        report = self.get_report_for_workspace(workspace_id, report_id)
        if report is None:
            return None
        link = _build_purchase_link(report, request)
        if link is None:
            return None
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO purchase_links (
                    link_id, report_id, trace_id, workspace_id, product_id, model_name,
                    seller_name, url, is_affiliate, affiliate_network, price_krw,
                    shipping_fee_krw, coupon_krw, effective_price_krw, rank, active,
                    notes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    link.link_id,
                    link.report_id,
                    link.trace_id,
                    link.workspace_id,
                    link.product_id,
                    link.model_name,
                    link.seller_name,
                    link.url,
                    int(link.is_affiliate),
                    link.affiliate_network,
                    link.price_krw,
                    link.shipping_fee_krw,
                    link.coupon_krw,
                    link.effective_price_krw,
                    link.rank,
                    int(link.active),
                    link.notes,
                    link.created_at,
                    link.updated_at,
                ),
            )
        return self._purchase_link_with_policy(link)

    def list_purchase_links_for_workspace(
        self,
        workspace_id: str,
        report_id: str,
        *,
        active_only: bool = False,
        limit: int = 100,
    ) -> list[PurchaseLink]:
        where = "pl.workspace_id = ? AND pl.report_id = ?"
        params: list[object] = [workspace_id, report_id]
        if active_only:
            where = f"{where} AND pl.active = 1"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT pl.*,
                       COALESCE(COUNT(plc.click_id), 0) AS click_count
                FROM purchase_links pl
                LEFT JOIN purchase_link_clicks plc
                  ON plc.link_id = pl.link_id
                WHERE {where}
                GROUP BY pl.link_id
                ORDER BY pl.rank ASC, pl.created_at ASC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        links = [_purchase_link_from_row(row) for row in rows]
        return self._purchase_links_with_policy(links)

    def purchase_link_governance_for_workspace(
        self,
        workspace_id: str,
        report_id: str,
    ) -> PurchaseLinkGovernance | None:
        report = self.get_report_for_workspace(workspace_id, report_id)
        if report is None:
            return None
        links = self.list_purchase_links_for_workspace(
            workspace_id,
            report_id,
            active_only=False,
            limit=200,
        )
        return _purchase_link_governance(workspace_id, report_id, links)

    def record_purchase_link_click(
        self,
        link_id: str,
        *,
        source: str = "public_report",
        referrer_host: str = "",
        user_agent_family: str = "",
    ) -> tuple[PurchaseLinkClick, str] | None:
        now = _now()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM purchase_links
                WHERE link_id = ? AND active = 1
                """,
                (link_id,),
            ).fetchone()
            if row is None:
                return None
            link = _purchase_link_from_row(row)
            click = PurchaseLinkClick(
                click_id=f"plink_click_{uuid4().hex[:12]}",
                link_id=link.link_id,
                report_id=link.report_id,
                workspace_id=link.workspace_id,
                product_id=link.product_id,
                source=source,
                referrer_host=referrer_host[:160],
                user_agent_family=user_agent_family[:80],
                created_at=now,
            )
            conn.execute(
                """
                INSERT INTO purchase_link_clicks (
                    click_id, link_id, report_id, workspace_id, product_id,
                    source, referrer_host, user_agent_family, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    click.click_id,
                    click.link_id,
                    click.report_id,
                    click.workspace_id,
                    click.product_id,
                    click.source,
                    click.referrer_host,
                    click.user_agent_family,
                    click.created_at,
                ),
            )
        return click, link.url

    def _purchase_link_with_policy(self, link: PurchaseLink) -> PurchaseLink:
        links = self.list_purchase_links_for_workspace(
            link.workspace_id,
            link.report_id,
            active_only=False,
            limit=200,
        )
        by_id = {item.link_id: item for item in links}
        return by_id.get(link.link_id, link)

    def _purchase_links_with_policy(self, links: list[PurchaseLink]) -> list[PurchaseLink]:
        affiliate_products = {
            link.product_id for link in links if link.active and link.is_affiliate
        }
        non_affiliate_products = {
            link.product_id for link in links if link.active and not link.is_affiliate
        }
        has_any_non_affiliate = bool(non_affiliate_products)
        enriched = []
        for link in links:
            warnings = list(link.policy_warnings)
            status = link.status
            if link.is_affiliate and link.product_id not in non_affiliate_products:
                warnings.append("제휴 링크에는 같은 후보의 비제휴 대안을 함께 노출해야 합니다.")
                status = CheckStatus.warning
            if link.is_affiliate and not has_any_non_affiliate:
                warnings.append("리포트 전체에 비제휴 구매 대안이 없어 공개 전 보강이 필요합니다.")
                status = CheckStatus.blocker
            if (
                link.product_id in affiliate_products
                and link.product_id not in non_affiliate_products
            ):
                status = CheckStatus.blocker if link.is_affiliate else status
            enriched.append(
                link.model_copy(
                    update={
                        "status": status,
                        "policy_warnings": _dedupe_strings(warnings),
                    }
                )
            )
        return enriched

    def share_report_for_workspace(
        self,
        workspace_id: str,
        report_id: str,
    ) -> ReportShare | None:
        now = _now()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT report_id, share_token, shared_at, share_views
                FROM saved_reports
                WHERE report_id = ? AND workspace_id = ?
                """,
                (report_id, workspace_id),
            ).fetchone()
            if row is None:
                return None
            token = row["share_token"] or f"share_{uuid4().hex[:20]}"
            shared_at = row["shared_at"] or now
            conn.execute(
                """
                UPDATE saved_reports
                SET share_token = ?, shared_at = ?, updated_at = ?
                WHERE report_id = ? AND workspace_id = ?
                """,
                (token, shared_at, now, report_id, workspace_id),
            )
        return ReportShare(
            report_id=report_id,
            share_token=token,
            public_path=f"/r/{token}",
            is_public=True,
            shared_at=shared_at,
            share_views=row["share_views"],
        )

    def revoke_report_share_for_workspace(
        self,
        workspace_id: str,
        report_id: str,
    ) -> ReportShare | None:
        now = _now()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT report_id, share_views
                FROM saved_reports
                WHERE report_id = ? AND workspace_id = ?
                """,
                (report_id, workspace_id),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                """
                UPDATE saved_reports
                SET share_token = NULL, shared_at = NULL, updated_at = ?
                WHERE report_id = ? AND workspace_id = ?
                """,
                (now, report_id, workspace_id),
            )
        return ReportShare(
            report_id=report_id,
            share_token=None,
            public_path=None,
            is_public=False,
            shared_at=None,
            share_views=row["share_views"],
        )

    def share_assets_for_workspace(
        self,
        workspace_id: str,
        report_id: str,
    ) -> ReportShareAssets | None:
        report = self.get_report_for_workspace(workspace_id, report_id)
        if report is None:
            return None
        return _build_report_share_assets(report)

    def get_public_report(self, share_token: str) -> PublicReport | None:
        now = _now()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT sr.report_id, sr.workspace_id, sr.title, sr.final_pick_id, sr.top_model_name,
                       sr.shared_at, sr.share_views, ar.response_json
                FROM saved_reports sr
                JOIN analysis_runs ar
                    ON ar.trace_id = sr.trace_id AND ar.workspace_id = sr.workspace_id
                WHERE sr.share_token = ? AND sr.shared_at IS NOT NULL
                """,
                (share_token,),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                """
                UPDATE saved_reports
                SET share_views = share_views + 1, updated_at = ?
                WHERE share_token = ?
                """,
                (now, share_token),
            )
        data = dict(row)
        purchase_links = self.list_purchase_links_for_workspace(
            data["workspace_id"],
            data["report_id"],
            active_only=True,
            limit=50,
        )
        return PublicReport(
            report_id=data["report_id"],
            title=data["title"],
            top_model_name=data["top_model_name"],
            final_pick_id=data["final_pick_id"],
            shared_at=data["shared_at"],
            share_views=data["share_views"] + 1,
            response=AnalyzeResponse.model_validate_json(data["response_json"]),
            purchase_links=purchase_links,
            conversion_cta=_public_report_conversion_cta(
                share_token=share_token,
                title=data["title"],
                top_model_name=data["top_model_name"],
            ),
        )

    def create_alert_subscription(
        self,
        response: AnalyzeResponse,
        *,
        product_id: str,
        target_price_krw: int,
        channels: list[str],
        contact: str,
        owner_label: str,
    ) -> AlertSubscription:
        return self.create_alert_subscription_for_workspace(
            "demo",
            response,
            product_id=product_id,
            target_price_krw=target_price_krw,
            channels=channels,
            contact=contact,
            owner_label=owner_label,
        )

    def create_alert_subscription_for_workspace(
        self,
        workspace_id: str,
        response: AnalyzeResponse,
        *,
        product_id: str,
        target_price_krw: int,
        channels: list[str],
        contact: str,
        owner_label: str,
    ) -> AlertSubscription:
        self.save_analysis_for_workspace(workspace_id, response)
        prices = {
            item.product_id: item.current_price_krw
            for item in response.report.price_alerts
        }
        current_price = prices.get(product_id)
        if current_price is None:
            for row in response.report.comparison_table:
                if row.product_id == product_id:
                    current_price = row.effective_price_krw
                    break
        if current_price is None:
            raise ValueError(f"Unknown product_id for alert: {product_id}")

        now = _now()
        subscription = AlertSubscription(
            subscription_id=f"alert_{uuid4().hex[:12]}",
            trace_id=response.graph_trace_id,
            product_id=product_id,
            workspace_id=workspace_id,
            target_price_krw=target_price_krw,
            current_price_krw=current_price,
            channels=channels,
            contact_masked=_mask_contact(contact),
            owner_label=owner_label,
            status="active",
            created_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO alert_subscriptions (
                    subscription_id, trace_id, product_id, workspace_id, target_price_krw,
                    current_price_krw, channels_json, contact, owner_label,
                    status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    subscription.subscription_id,
                    subscription.trace_id,
                    subscription.product_id,
                    subscription.workspace_id,
                    subscription.target_price_krw,
                    subscription.current_price_krw,
                    json.dumps(subscription.channels, ensure_ascii=False),
                    contact,
                    subscription.owner_label,
                    subscription.status,
                    subscription.created_at,
                ),
            )
        return subscription

    def list_alert_subscriptions(self, limit: int = 50) -> list[AlertSubscription]:
        return self.list_alert_subscriptions_for_workspace("demo", limit=limit)

    def list_alert_subscriptions_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[AlertSubscription]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM alert_subscriptions
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_alert_from_row(row) for row in rows]

    def evaluate_alerts_for_workspace(
        self,
        workspace_id: str,
        *,
        price_overrides_krw: dict[str, int],
        dry_run: bool,
        limit: int,
    ) -> AlertEvaluationResponse:
        subscriptions = self.list_alert_subscriptions_for_workspace(workspace_id, limit=limit)
        now = _now()
        events: list[AlertDeliveryEvent] = []
        for subscription in subscriptions:
            if subscription.status != "active":
                continue
            current_price = price_overrides_krw.get(
                subscription.product_id,
                subscription.current_price_krw,
            )
            if current_price > subscription.target_price_krw:
                continue
            event = AlertDeliveryEvent(
                event_id=f"event_{uuid4().hex[:12]}",
                subscription_id=subscription.subscription_id,
                trace_id=subscription.trace_id,
                product_id=subscription.product_id,
                workspace_id=workspace_id,
                target_price_krw=subscription.target_price_krw,
                current_price_krw=current_price,
                delta_krw=subscription.target_price_krw - current_price,
                channels=subscription.channels,
                contact_masked=subscription.contact_masked,
                delivery_status="dry_run" if dry_run else "queued",
                message=(
                    f"{subscription.product_id} 현재가 {current_price:,}원이 "
                    f"목표가 {subscription.target_price_krw:,}원 이하입니다."
                ),
                created_at=now,
            )
            events.append(event)
        if events and not dry_run:
            self.add_alert_events(events)
        return AlertEvaluationResponse(
            workspace_id=workspace_id,
            evaluated_count=len(subscriptions),
            triggered_count=len(events),
            dry_run=dry_run,
            events=events,
        )

    def add_alert_events(self, events: list[AlertDeliveryEvent]) -> list[AlertDeliveryEvent]:
        with self._connect() as conn:
            for event in events:
                conn.execute(
                    """
                    INSERT INTO alert_delivery_events (
                        event_id, subscription_id, trace_id, product_id, workspace_id,
                        target_price_krw, current_price_krw, delta_krw, channels_json,
                        contact_masked, delivery_status, message, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id,
                        event.subscription_id,
                        event.trace_id,
                        event.product_id,
                        event.workspace_id,
                        event.target_price_krw,
                        event.current_price_krw,
                        event.delta_krw,
                        json.dumps(event.channels, ensure_ascii=False),
                        event.contact_masked,
                        event.delivery_status,
                        event.message,
                        event.created_at,
                    ),
                )
        return events

    def list_alert_events_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[AlertDeliveryEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM alert_delivery_events
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_alert_event_from_row(row) for row in rows]

    def upsert_alert_channel_for_workspace(
        self,
        workspace_id: str,
        request: AlertNotificationChannelRequest,
    ) -> AlertNotificationChannel:
        channel = request.channel.strip().lower()
        if channel not in SUPPORTED_ALERT_CHANNELS:
            raise ValueError(
                f"지원하지 않는 알림 채널입니다: {request.channel}. "
                f"가능한 채널: {', '.join(sorted(SUPPORTED_ALERT_CHANNELS))}"
            )
        now = _now()
        display_name = request.display_name.strip() or _default_channel_name(channel)
        target = request.target.strip() or _default_channel_target(channel)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT channel_id, created_at
                FROM alert_notification_channels
                WHERE workspace_id = ? AND channel = ?
                """,
                (workspace_id, channel),
            ).fetchone()
            channel_id = row["channel_id"] if row else f"channel_{uuid4().hex[:12]}"
            created_at = row["created_at"] if row else now
            conn.execute(
                """
                INSERT INTO alert_notification_channels (
                    channel_id, workspace_id, channel, display_name, target,
                    enabled, retry_limit, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(workspace_id, channel) DO UPDATE SET
                    display_name=excluded.display_name,
                    target=excluded.target,
                    enabled=excluded.enabled,
                    retry_limit=excluded.retry_limit,
                    updated_at=excluded.updated_at
                """,
                (
                    channel_id,
                    workspace_id,
                    channel,
                    display_name,
                    target,
                    1 if request.enabled else 0,
                    request.retry_limit,
                    created_at,
                    now,
                ),
            )
        return AlertNotificationChannel(
            channel_id=channel_id,
            workspace_id=workspace_id,
            channel=channel,
            display_name=display_name,
            target_masked=_mask_target(target),
            enabled=request.enabled,
            retry_limit=request.retry_limit,
            created_at=created_at,
            updated_at=now,
        )

    def list_alert_channels_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[AlertNotificationChannel]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM alert_notification_channels
                WHERE workspace_id = ?
                ORDER BY channel ASC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_alert_channel_from_row(row) for row in rows]

    def dispatch_alert_events_for_workspace(
        self,
        workspace_id: str,
        *,
        event_ids: list[str],
        dry_run: bool,
        limit: int,
    ) -> AlertDispatchResponse:
        events = self._queued_alert_events(workspace_id, event_ids=event_ids, limit=limit)
        channels = self._alert_channel_config_map(workspace_id)
        attempts: list[AlertDeliveryAttempt] = []
        now = _now()
        with self._connect() as conn:
            for event in events:
                event_attempts: list[AlertDeliveryAttempt] = []
                for channel in event.channels:
                    channel_key = channel.strip().lower()
                    attempt_number = self._next_attempt_number(
                        conn,
                        event.event_id,
                        channel_key,
                    )
                    status, provider_message, next_retry_at = _dispatch_status(
                        channel_key,
                        channels.get(channel_key),
                        attempt_number,
                        dry_run,
                        now,
                    )
                    attempt = AlertDeliveryAttempt(
                        attempt_id=f"attempt_{uuid4().hex[:12]}",
                        event_id=event.event_id,
                        subscription_id=event.subscription_id,
                        workspace_id=workspace_id,
                        channel=channel_key,
                        contact_masked=event.contact_masked,
                        delivery_status=status,
                        provider_message=provider_message,
                        retry_count=attempt_number,
                        next_retry_at=next_retry_at,
                        created_at=now,
                    )
                    event_attempts.append(attempt)
                    attempts.append(attempt)
                    if not dry_run:
                        self._insert_alert_attempt(conn, attempt)
                if not dry_run and event_attempts:
                    conn.execute(
                        """
                        UPDATE alert_delivery_events
                        SET delivery_status = ?
                        WHERE event_id = ? AND workspace_id = ?
                        """,
                        (
                            "sent"
                            if any(
                                attempt.delivery_status == "sent"
                                for attempt in event_attempts
                            )
                            else "failed",
                            event.event_id,
                            workspace_id,
                        ),
                    )
        return AlertDispatchResponse(
            workspace_id=workspace_id,
            selected_count=len(events),
            sent_count=sum(1 for attempt in attempts if attempt.delivery_status == "sent"),
            failed_count=sum(1 for attempt in attempts if attempt.delivery_status == "failed"),
            dry_run=dry_run,
            attempts=attempts,
        )

    def list_alert_delivery_attempts_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[AlertDeliveryAttempt]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM alert_delivery_attempts
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_alert_attempt_from_row(row) for row in rows]

    def list_trace_runs_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[TraceRunSummary]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    ar.trace_id,
                    ar.workspace_id,
                    ar.category,
                    ar.purpose,
                    ar.final_pick_id,
                    ar.top_model_name,
                    ar.quality_score,
                    ar.warning_count,
                    ar.blocker_count,
                    ar.created_at,
                    COUNT(ts.span_id) AS span_count
                FROM analysis_runs ar
                LEFT JOIN trace_spans ts
                    ON ts.trace_id = ar.trace_id AND ts.workspace_id = ar.workspace_id
                WHERE ar.workspace_id = ?
                GROUP BY ar.trace_id
                ORDER BY ar.created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_trace_summary_from_row(row) for row in rows]

    def list_trace_spans_for_workspace(
        self,
        workspace_id: str,
        trace_id: str,
    ) -> list[TraceSpanRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM trace_spans
                WHERE workspace_id = ? AND trace_id = ?
                ORDER BY sequence ASC
                """,
                (workspace_id, trace_id),
            ).fetchall()
        return [_trace_span_from_row(row) for row in rows]

    def quality_dashboard_for_workspace(
        self,
        workspace_id: str | None,
        limit: int = 20,
    ) -> QualityDashboard:
        with self._connect() as conn:
            where = " WHERE workspace_id = ?" if workspace_id else ""
            params: tuple[str, ...] = (workspace_id,) if workspace_id else ()
            summary = conn.execute(
                f"""
                SELECT
                    COUNT(*) AS audit_count,
                    AVG(quality_score) AS average_quality_score,
                    SUM(estimated_cost_krw) AS total_estimated_cost_krw,
                    SUM(warning_count) AS warning_count,
                    SUM(blocker_count) AS blocker_count
                FROM analysis_runs{where}
                """,
                params,
            ).fetchone()
            rows = conn.execute(
                f"""
                SELECT quality_audit_json
                FROM analysis_runs{where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (*params, limit),
            ).fetchall()
        audits = [
            AnalysisQualityAudit.model_validate_json(row["quality_audit_json"])
            for row in rows
            if row["quality_audit_json"] and row["quality_audit_json"] != "{}"
        ]
        return QualityDashboard(
            workspace_id=workspace_id,
            audit_count=int(summary["audit_count"] or 0),
            average_quality_score=round(float(summary["average_quality_score"] or 0), 2),
            total_estimated_cost_krw=round(float(summary["total_estimated_cost_krw"] or 0), 2),
            warning_count=int(summary["warning_count"] or 0),
            blocker_count=int(summary["blocker_count"] or 0),
            recent_audits=audits,
        )

    def ops_regression_for_workspace(
        self,
        workspace_id: str,
        window_size: int = 5,
    ) -> OpsRegressionDashboard:
        window = max(1, min(window_size, 50))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT trace_id, quality_score, estimated_cost_krw,
                       warning_count, blocker_count, created_at
                FROM analysis_runs
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, window * 2),
            ).fetchall()
            provider_rows = conn.execute(
                """
                SELECT
                    l.provider_id,
                    COALESCE(p.provider_name, l.host) AS provider_name,
                    l.host,
                    COUNT(*) AS fetch_count,
                    SUM(CASE WHEN l.status = 'allowed' THEN 1 ELSE 0 END) AS allowed_count,
                    SUM(CASE WHEN l.status = 'blocked' THEN 1 ELSE 0 END) AS blocked_count
                FROM source_provider_fetch_log l
                LEFT JOIN source_provider_policies p
                  ON p.provider_id = l.provider_id
                 AND p.workspace_id = l.workspace_id
                WHERE l.workspace_id = ?
                GROUP BY l.provider_id, l.host, provider_name
                ORDER BY blocked_count DESC, fetch_count DESC
                LIMIT 100
                """,
                (workspace_id,),
            ).fetchall()
        recent = _ops_regression_period("recent", rows[:window])
        previous = _ops_regression_period("previous", rows[window : window * 2])
        quality_delta = round(recent.average_quality_score - previous.average_quality_score, 2)
        cost_delta = round(recent.average_cost_krw - previous.average_cost_krw, 2)
        cost_delta_rate = (
            round(cost_delta / previous.average_cost_krw, 4)
            if previous.average_cost_krw
            else 0
        )
        provider_reliability = [
            _provider_reliability_metric(row) for row in provider_rows
        ]
        status, risk_flags, next_actions = _ops_regression_status(
            recent=recent,
            previous=previous,
            quality_delta=quality_delta,
            cost_delta_rate=cost_delta_rate,
            provider_reliability=provider_reliability,
        )
        summary = _ops_regression_summary(
            status=status,
            recent=recent,
            previous=previous,
            quality_delta=quality_delta,
            cost_delta_rate=cost_delta_rate,
        )
        return OpsRegressionDashboard(
            workspace_id=workspace_id,
            status=status,
            summary=summary,
            window_size=window,
            recent=recent,
            previous=previous,
            quality_delta=quality_delta,
            cost_delta_krw=cost_delta,
            cost_delta_rate=cost_delta_rate,
            provider_reliability=provider_reliability,
            risk_flags=risk_flags,
            next_actions=next_actions,
        )

    def learning_insights_for_workspace(
        self,
        workspace_id: str,
        limit: int = 20,
    ) -> OpsLearningDashboard:
        capped_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    product_id,
                    MAX(model_name) AS model_name,
                    COUNT(*) AS outcome_count,
                    SUM(CASE WHEN status = 'purchased' THEN 1 ELSE 0 END)
                        AS purchase_count,
                    SUM(CASE WHEN status = 'abandoned' THEN 1 ELSE 0 END)
                        AS abandoned_count,
                    SUM(CASE WHEN status = 'delayed' THEN 1 ELSE 0 END)
                        AS delayed_count,
                    SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END)
                        AS returned_count,
                    AVG(satisfaction) AS average_satisfaction,
                    AVG(price_delta_krw) AS average_price_delta_krw,
                    SUM(conversion_value_krw) AS conversion_value_krw,
                    MAX(created_at) AS latest_at
                FROM purchase_outcomes
                WHERE workspace_id = ? AND product_id IS NOT NULL
                GROUP BY product_id
                ORDER BY latest_at DESC
                LIMIT ?
                """,
                (workspace_id, capped_limit),
            ).fetchall()
            checkout_rows = conn.execute(
                """
                SELECT
                    product_id,
                    COUNT(*) AS checkout_review_count,
                    SUM(CASE WHEN checkout_blocked = 1 THEN 1 ELSE 0 END)
                        AS checkout_blocked_count
                FROM checkout_reviews
                WHERE workspace_id = ? AND product_id IS NOT NULL
                GROUP BY product_id
                """,
                (workspace_id,),
            ).fetchall()
            feedback_rows = conn.execute(
                """
                SELECT
                    selected_product_id AS product_id,
                    COUNT(*) AS feedback_count,
                    AVG(rating) AS feedback_satisfaction
                FROM user_feedback
                WHERE workspace_id = ? AND selected_product_id IS NOT NULL
                GROUP BY selected_product_id
                """,
                (workspace_id,),
            ).fetchall()
        checkout_by_product = {row["product_id"]: row for row in checkout_rows}
        feedback_by_product = {row["product_id"]: row for row in feedback_rows}
        insights = [
            _learning_insight_from_rows(
                outcome=row,
                checkout=checkout_by_product.get(row["product_id"]),
                feedback=feedback_by_product.get(row["product_id"]),
            )
            for row in rows
        ]
        status = _learning_dashboard_status(insights)
        top_actions = _learning_top_actions(insights)
        if not insights:
            return OpsLearningDashboard(
                workspace_id=workspace_id,
                generated_at=_now(),
                status=CheckStatus.warning,
                summary=(
                    "아직 구매 결과 표본이 없습니다. 완료 리포트 발송 후 "
                    "실제 구매, 이탈, 지연, 반품 결과를 최소 5건 이상 수집하세요."
                ),
                insight_count=0,
                top_actions=[
                    "구매 완료 사용자에게 purchase outcome 기록을 요청하세요.",
                    "이탈 사용자는 가격, 신뢰, 옵션 불확실성 사유를 분리해 기록하세요.",
                ],
            )
        return OpsLearningDashboard(
            workspace_id=workspace_id,
            generated_at=_now(),
            status=status,
            summary=_learning_dashboard_summary(status, insights),
            insight_count=len(insights),
            top_actions=top_actions,
            insights=insights,
        )

    def create_observability_export_for_workspace(
        self,
        workspace_id: str,
        request: ObservabilityExportRequest,
    ) -> ObservabilityExportRecord | None:
        analysis = self.get_analysis_for_workspace(workspace_id, request.trace_id)
        if analysis is None:
            return None
        spans = self.list_trace_spans_for_workspace(workspace_id, request.trace_id)
        quality = analysis.quality_audit
        now = _now()
        export_id = f"obs_{uuid4().hex[:12]}"
        payload = (
            _observability_payload(
                workspace_id=workspace_id,
                destination=request.destination,
                analysis=analysis,
                spans=spans,
            )
            if request.include_payload
            else {}
        )
        record = ObservabilityExportRecord(
            export_id=export_id,
            workspace_id=workspace_id,
            trace_id=request.trace_id,
            destination=request.destination,
            status="queued",
            span_count=len(spans),
            quality_score=quality.quality_score if quality else 0,
            payload=payload,
            provider_message="export outbox에 적재되었습니다.",
            retry_count=0,
            dispatched_at=None,
            next_retry_at=None,
            created_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO observability_exports (
                    export_id, workspace_id, trace_id, destination, status,
                    span_count, quality_score, payload_json, provider_message,
                    retry_count, dispatched_at, next_retry_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.export_id,
                    record.workspace_id,
                    record.trace_id,
                    record.destination,
                    record.status,
                    record.span_count,
                    record.quality_score,
                    json.dumps(record.payload, ensure_ascii=False),
                    record.provider_message,
                    record.retry_count,
                    record.dispatched_at,
                    record.next_retry_at,
                    record.created_at,
                ),
            )
        return record

    def list_observability_exports_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[ObservabilityExportRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM observability_exports
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_observability_export_from_row(row) for row in rows]

    def dispatch_observability_exports_for_workspace(
        self,
        workspace_id: str,
        *,
        export_ids: list[str],
        dry_run: bool,
        limit: int,
    ) -> ObservabilityDispatchResponse:
        exports = self._queued_observability_exports(
            workspace_id,
            export_ids=export_ids,
            limit=limit,
        )
        now = _now()
        dispatched: list[ObservabilityExportRecord] = []
        with self._connect() as conn:
            for export in exports:
                retry_count = export.retry_count + 1
                status, provider_message, next_retry_at = _observability_dispatch_status(
                    export,
                    retry_count=retry_count,
                    dry_run=dry_run,
                    now=now,
                )
                updated = export.model_copy(
                    update={
                        "status": status,
                        "provider_message": provider_message,
                        "retry_count": retry_count,
                        "dispatched_at": now if status == "sent" else None,
                        "next_retry_at": next_retry_at,
                    }
                )
                dispatched.append(updated)
                if not dry_run:
                    conn.execute(
                        """
                        UPDATE observability_exports
                        SET status = ?,
                            provider_message = ?,
                            retry_count = ?,
                            dispatched_at = ?,
                            next_retry_at = ?
                        WHERE workspace_id = ? AND export_id = ?
                        """,
                        (
                            updated.status,
                            updated.provider_message,
                            updated.retry_count,
                            updated.dispatched_at,
                            updated.next_retry_at,
                            workspace_id,
                            updated.export_id,
                        ),
                    )
        return ObservabilityDispatchResponse(
            workspace_id=workspace_id,
            selected_count=len(exports),
            sent_count=sum(1 for item in dispatched if item.status == "sent"),
            failed_count=sum(1 for item in dispatched if item.status == "failed"),
            dry_run=dry_run,
            exports=dispatched,
        )

    def create_feedback_for_workspace(
        self,
        workspace_id: str,
        request: FeedbackRequest,
    ) -> FeedbackRecord:
        now = _now()
        record = FeedbackRecord(
            feedback_id=f"feedback_{uuid4().hex[:12]}",
            trace_id=request.trace_id,
            workspace_id=workspace_id,
            rating=request.rating,
            purchase_intent=request.purchase_intent,
            selected_product_id=request.selected_product_id,
            reason=request.reason,
            improvement_requests=request.improvement_requests,
            contact_masked=_mask_contact(request.contact) if request.contact else "",
            created_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_feedback (
                    feedback_id, trace_id, workspace_id, rating, purchase_intent,
                    selected_product_id, reason, improvement_requests_json,
                    contact_masked, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.feedback_id,
                    record.trace_id,
                    record.workspace_id,
                    record.rating,
                    1 if record.purchase_intent else 0,
                    record.selected_product_id,
                    record.reason,
                    json.dumps(record.improvement_requests, ensure_ascii=False),
                    record.contact_masked,
                    record.created_at,
                ),
            )
        return record

    def list_feedback_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[FeedbackRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM user_feedback
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_feedback_from_row(row) for row in rows]

    def create_growth_event_for_workspace(
        self,
        workspace_id: str,
        request: GrowthEventRequest,
    ) -> GrowthEventRecord:
        now = _now()
        event = GrowthEventRecord(
            event_id=f"growth_{uuid4().hex[:12]}",
            workspace_id=workspace_id,
            event_type=request.event_type,
            trace_id=request.trace_id,
            report_id=request.report_id,
            product_id=request.product_id,
            source=request.source[:80],
            surface=request.surface[:80],
            label=request.label[:160],
            metadata=request.metadata,
            created_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO growth_events (
                    event_id, workspace_id, event_type, trace_id, report_id,
                    product_id, source, surface, label, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.workspace_id,
                    event.event_type.value,
                    event.trace_id,
                    event.report_id,
                    event.product_id,
                    event.source,
                    event.surface,
                    event.label,
                    json.dumps(event.metadata, ensure_ascii=False),
                    event.created_at,
                ),
            )
        return event

    def list_growth_events_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[GrowthEventRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM growth_events
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_growth_event_from_row(row) for row in rows]

    def growth_funnel_for_workspace(
        self,
        workspace_id: str,
        limit: int = 20,
    ) -> GrowthFunnelDashboard:
        metrics = self.metrics_for_workspace(workspace_id)
        recent_events = self.list_growth_events_for_workspace(workspace_id, limit=limit)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT event_type,
                       COUNT(*) AS event_count,
                       COUNT(DISTINCT COALESCE(trace_id, event_id)) AS unique_traces
                FROM growth_events
                WHERE workspace_id = ?
                GROUP BY event_type
                """,
                (workspace_id,),
            ).fetchall()
            surface_rows = conn.execute(
                """
                SELECT surface, COUNT(*) AS event_count
                FROM growth_events
                WHERE workspace_id = ?
                GROUP BY surface
                ORDER BY event_count DESC, surface ASC
                LIMIT 5
                """,
                (workspace_id,),
            ).fetchall()
        counts = {str(row["event_type"]): int(row["event_count"]) for row in rows}
        unique_counts = {str(row["event_type"]): int(row["unique_traces"]) for row in rows}
        baseline = max(metrics.analysis_runs, 1)
        steps = [
            _growth_funnel_step(
                GrowthEventType.analysis_view,
                "분석 결과 조회",
                counts,
                unique_counts,
                baseline,
                warning_threshold=0.35,
                ok_threshold=0.65,
                recommendation="분석 완료 후 결과 카드가 첫 화면에서 보이도록 유지하세요.",
            ),
            _growth_funnel_step(
                GrowthEventType.recommendation_click,
                "추천 카드 클릭",
                counts,
                unique_counts,
                baseline,
                warning_threshold=0.2,
                ok_threshold=0.45,
                recommendation="추천 카드의 가격/리스크/CTA 문구를 A/B로 비교하세요.",
            ),
            _growth_funnel_step(
                GrowthEventType.alternative_click,
                "대안 시나리오 전환",
                counts,
                unique_counts,
                baseline,
                warning_threshold=0.08,
                ok_threshold=0.2,
                recommendation="예산 확대/축소와 조건 강화 카드의 문구를 더 명확히 하세요.",
            ),
            _growth_funnel_step(
                GrowthEventType.share_cta,
                "공유 리포트 CTA",
                counts,
                unique_counts,
                baseline,
                warning_threshold=0.08,
                ok_threshold=0.18,
                recommendation="공개 리포트 공유 버튼을 구매 판단 카드 근처에 배치하세요.",
            ),
            _growth_funnel_step(
                GrowthEventType.alert_cta,
                "가격 알림 CTA",
                counts,
                unique_counts,
                baseline,
                warning_threshold=0.08,
                ok_threshold=0.18,
                recommendation="가격 대기 판정 사용자에게 목표가 알림을 즉시 제안하세요.",
            ),
            _growth_funnel_step(
                GrowthEventType.subscription_cta,
                "요금제 관심 CTA",
                counts,
                unique_counts,
                baseline,
                warning_threshold=0.03,
                ok_threshold=0.08,
                recommendation="구독 CTA는 리포트 저장/알림 생성 뒤에 다시 노출하세요.",
            ),
        ]
        activation_rate = _event_rate(counts, GrowthEventType.recommendation_click, baseline)
        share_rate = _event_rate(counts, GrowthEventType.share_cta, baseline)
        alert_rate = _event_rate(counts, GrowthEventType.alert_cta, baseline)
        paid_intent_rate = _event_rate(counts, GrowthEventType.subscription_cta, baseline)
        status = _growth_funnel_status(steps, metrics.analysis_runs)
        next_actions = [step.recommendation for step in steps if step.status != CheckStatus.ok]
        return GrowthFunnelDashboard(
            workspace_id=workspace_id,
            generated_at=_now(),
            total_events=metrics.growth_events,
            unique_traces=metrics.growth_unique_traces,
            activation_rate=activation_rate,
            share_rate=share_rate,
            alert_rate=alert_rate,
            paid_intent_rate=paid_intent_rate,
            status=status,
            summary=_growth_funnel_summary(status, metrics.growth_events, activation_rate),
            steps=steps,
            top_surfaces=[
                f"{row['surface']} {int(row['event_count'])}건" for row in surface_rows
            ],
            next_actions=next_actions[:5],
            recent_events=recent_events,
        )

    def create_launch_experiment_for_workspace(
        self,
        workspace_id: str,
        request: LaunchExperimentRequest,
    ) -> LaunchExperiment:
        now = _now()
        variants = _launch_experiment_variant_payloads(request)
        experiment_id = f"lexp_{uuid4().hex[:12]}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO launch_experiments (
                    experiment_id, workspace_id, name, channel, audience,
                    hypothesis, primary_metric, target_surface, category,
                    status, variants_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment_id,
                    workspace_id,
                    request.name[:120],
                    request.channel[:80],
                    request.audience[:120],
                    request.hypothesis[:240],
                    request.primary_metric.value,
                    request.target_surface[:120],
                    request.category.value if request.category else None,
                    CheckStatus.warning.value,
                    json.dumps(variants, ensure_ascii=False),
                    now,
                    now,
                ),
            )
            row = conn.execute(
                """
                SELECT *
                FROM launch_experiments
                WHERE workspace_id = ? AND experiment_id = ?
                """,
                (workspace_id, experiment_id),
            ).fetchone()
            stats = _launch_experiment_variant_stats(conn, workspace_id, experiment_id)
        return _launch_experiment_from_row(row, stats)

    def list_launch_experiments_for_workspace(
        self,
        workspace_id: str,
        limit: int = 20,
    ) -> list[LaunchExperiment]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM launch_experiments
                WHERE workspace_id = ?
                ORDER BY updated_at DESC, created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
            return [
                _launch_experiment_from_row(
                    row,
                    _launch_experiment_variant_stats(
                        conn,
                        workspace_id,
                        str(row["experiment_id"]),
                    ),
                )
                for row in rows
            ]

    def record_launch_experiment_event_for_workspace(
        self,
        workspace_id: str,
        experiment_id: str,
        request: LaunchExperimentEventRequest,
    ) -> LaunchExperimentEvent | None:
        now = _now()
        event_type = _launch_experiment_event_type(request.event_type)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM launch_experiments
                WHERE workspace_id = ? AND experiment_id = ?
                """,
                (workspace_id, experiment_id),
            ).fetchone()
            if row is None:
                return None
            variant_ids = {
                str(item["variant_id"])
                for item in json.loads(str(row["variants_json"] or "[]"))
            }
            if request.variant_id not in variant_ids:
                return None
            event = LaunchExperimentEvent(
                event_id=f"lexpevt_{uuid4().hex[:12]}",
                experiment_id=experiment_id,
                workspace_id=workspace_id,
                variant_id=request.variant_id,
                event_type=event_type,
                trace_id=request.trace_id,
                source=request.source[:80],
                surface=request.surface[:120],
                label=request.label[:160],
                metadata=request.metadata,
                created_at=now,
            )
            conn.execute(
                """
                INSERT INTO launch_experiment_events (
                    event_id, workspace_id, experiment_id, variant_id,
                    event_type, trace_id, source, surface, label,
                    metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.workspace_id,
                    event.experiment_id,
                    event.variant_id,
                    event.event_type,
                    event.trace_id,
                    event.source,
                    event.surface,
                    event.label,
                    json.dumps(event.metadata, ensure_ascii=False),
                    event.created_at,
                ),
            )
            conn.execute(
                """
                UPDATE launch_experiments
                SET updated_at = ?
                WHERE workspace_id = ? AND experiment_id = ?
                """,
                (now, workspace_id, experiment_id),
            )
            if event_type == "conversion":
                metadata = {
                    **event.metadata,
                    "launch_experiment_id": experiment_id,
                    "launch_variant_id": request.variant_id,
                    "launch_event_id": event.event_id,
                }
                conn.execute(
                    """
                    INSERT INTO growth_events (
                        event_id, workspace_id, event_type, trace_id, report_id,
                        product_id, source, surface, label, metadata_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"growth_{uuid4().hex[:12]}",
                        workspace_id,
                        str(row["primary_metric"]),
                        event.trace_id,
                        None,
                        None,
                        event.source,
                        event.surface,
                        event.label or row["name"],
                        json.dumps(metadata, ensure_ascii=False),
                        now,
                    ),
                )
        return event

    def list_launch_experiment_events_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[LaunchExperimentEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM launch_experiment_events
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_launch_experiment_event_from_row(row) for row in rows]

    def launch_experiment_dashboard_for_workspace(
        self,
        workspace_id: str,
        limit: int = 20,
    ) -> LaunchExperimentDashboard:
        experiments = self.list_launch_experiments_for_workspace(
            workspace_id,
            limit=limit,
        )
        recent_events = self.list_launch_experiment_events_for_workspace(
            workspace_id,
            limit=limit,
        )
        total_impressions = sum(
            variant.impressions for experiment in experiments for variant in experiment.variants
        )
        total_conversions = sum(
            variant.conversions for experiment in experiments for variant in experiment.variants
        )
        conversion_rate = (
            round(total_conversions / total_impressions, 4)
            if total_impressions
            else 0
        )
        variants = [
            variant for experiment in experiments for variant in experiment.variants
        ]
        best_variant = _best_launch_variant(variants)
        status = _launch_experiment_dashboard_status(
            len(experiments),
            total_impressions,
            conversion_rate,
        )
        return LaunchExperimentDashboard(
            workspace_id=workspace_id,
            generated_at=_now(),
            status=status,
            experiment_count=len(experiments),
            active_experiment_count=sum(
                1 for experiment in experiments if experiment.status != CheckStatus.ok
            ),
            total_impressions=total_impressions,
            total_conversions=total_conversions,
            conversion_rate=conversion_rate,
            best_variant_label=best_variant.label if best_variant else "",
            summary=_launch_experiment_summary(
                len(experiments),
                total_impressions,
                total_conversions,
                conversion_rate,
            ),
            experiments=experiments,
            recommended_experiments=_recommended_launch_experiments(experiments),
            next_actions=_launch_experiment_next_actions(
                experiments,
                total_impressions,
                conversion_rate,
            ),
            recent_events=recent_events,
        )

    def launch_pulse_for_workspace(
        self,
        workspace_id: str,
        limit: int = 12,
    ) -> LaunchPulseDashboard:
        metrics = self.metrics_for_workspace(workspace_id)
        growth = self.growth_funnel_for_workspace(workspace_id, limit=limit)
        referrals = self.waitlist_referral_dashboard_for_workspace(workspace_id, limit=limit)
        pricing = self.pricing_dashboard_for_workspace(workspace_id)
        readiness = self.beta_readiness_for_workspace(workspace_id)
        feedback = self.list_feedback_for_workspace(workspace_id, limit=limit)

        activation_score = _pulse_score_from_rate(
            growth.activation_rate,
            warning=0.3,
            ok=0.65,
        )
        love_score = min(
            100.0,
            metrics.average_satisfaction * 16
            + metrics.purchase_intent_rate * 35
            + min(metrics.feedback_count, 10) * 2,
        )
        sharing_score = min(
            100.0,
            metrics.share_cta_clicks * 12
            + referrals.total_referrals * 10
            + referrals.referred_signup_count * 18
            + referrals.share_rate_hint * 35,
        )
        monetization_score = min(
            100.0,
            pricing.premium_intent_count * 16
            + pricing.team_intent_count * 24
            + min(pricing.estimated_mrr_krw / 10_000, 35),
        )
        reliability_score = min(
            100.0,
            readiness.launch_readiness_score * 0.65
            + metrics.average_quality_score * 0.25
            + metrics.conversion_ready_rate * 10,
        )
        pulse_score = round(
            activation_score * 0.22
            + love_score * 0.24
            + sharing_score * 0.2
            + monetization_score * 0.16
            + reliability_score * 0.18,
            1,
        )
        status = _pulse_status(pulse_score, readiness, growth)
        signals = [
            _pulse_signal(
                area="activation",
                label="첫 체험 반응",
                score=activation_score,
                evidence=(
                    f"성장 이벤트 {growth.total_events}건, 추천 클릭률 "
                    f"{round(growth.activation_rate * 100)}%"
                ),
                recommendation="공개 데모 preset과 추천 카드 CTA를 첫 화면에서 계속 실험하세요.",
            ),
            _pulse_signal(
                area="love",
                label="추천 만족도",
                score=love_score,
                evidence=(
                    f"피드백 {metrics.feedback_count}건, 평균 만족도 "
                    f"{metrics.average_satisfaction}점, 구매 의향 "
                    f"{round(metrics.purchase_intent_rate * 100)}%"
                ),
                recommendation=(
                    "낮은 평점 사유를 개선 백로그로 묶고 "
                    "같은 후보군의 근거를 보강하세요."
                ),
            ),
            _pulse_signal(
                area="sharing",
                label="공유 확산",
                score=sharing_score,
                evidence=(
                    f"공유 CTA {metrics.share_cta_clicks}건, 추천 대기열 "
                    f"{referrals.total_referrals}명, 추천 유입 {referrals.referred_signup_count}명"
                ),
                recommendation=(
                    "공개 리포트 공유 문구와 추천 코드 CTA를 "
                    "같은 화면에 붙여 확산 루프를 짧게 만드세요."
                ),
            ),
            _pulse_signal(
                area="monetization",
                label="유료 수요",
                score=monetization_score,
                evidence=(
                    f"요금제 관심 {pricing.intent_count}건, 유료 의향 "
                    f"{pricing.premium_intent_count + pricing.team_intent_count}건, "
                    f"예상 MRR {pricing.estimated_mrr_krw:,}원"
                ),
                recommendation=(
                    "Team/Premium 의향이 생긴 persona를 "
                    "별도 cohort로 만들어 가격 검증을 이어가세요."
                ),
            ),
            _pulse_signal(
                area="reliability",
                label="출시 안정성",
                score=reliability_score,
                evidence=(
                    f"readiness {readiness.launch_readiness_score}점, 품질 "
                    f"{metrics.average_quality_score}점, 구매 준비율 "
                    f"{round(metrics.conversion_ready_rate * 100)}%"
                ),
            recommendation=(
                "readiness 경고와 품질 차단 사유는 "
                "공개 확대 전에 launch gate에서 먼저 닫으세요."
            ),
            ),
        ]
        metrics_cards = [
            _pulse_metric(
                "pulse_score",
                "Pulse",
                pulse_score,
                "점",
                status,
                "공개 반응, 확산, 유료 수요, 안정성을 합성한 출시 반응 점수",
            ),
            _pulse_metric(
                "purchase_intent_rate",
                "구매 의향",
                round(metrics.purchase_intent_rate * 100),
                "%",
                _pulse_rate_status(metrics.purchase_intent_rate, 0.25, 0.5),
                "피드백 중 실제 구매 의향 비율",
            ),
            _pulse_metric(
                "share_rate",
                "공유 CTA",
                round(growth.share_rate * 100),
                "%",
                _pulse_rate_status(growth.share_rate, 0.15, 0.35),
                "분석 실행 대비 공유 CTA 반응",
            ),
            _pulse_metric(
                "estimated_mrr",
                "예상 MRR",
                pricing.estimated_mrr_krw,
                "원",
                _pulse_count_status(pricing.premium_intent_count + pricing.team_intent_count, 1, 3),
                "요금제 관심 등록에서 계산한 월 반복 매출 신호",
            ),
            _pulse_metric(
                "referrals",
                "추천 대기열",
                referrals.total_referrals,
                "명",
                _pulse_count_status(referrals.total_referrals, 1, 5),
                "초대 링크 기반 공개 전 대기 수요",
            ),
        ]
        return LaunchPulseDashboard(
            workspace_id=workspace_id,
            generated_at=_now(),
            pulse_score=pulse_score,
            status=status,
            headline=_pulse_headline(status, pulse_score),
            summary=_pulse_summary(pulse_score, metrics, referrals, pricing),
            metrics=metrics_cards,
            signals=signals,
            hot_surfaces=growth.top_surfaces,
            top_actions=_pulse_top_actions(signals, growth, referrals, pricing, readiness),
            recent_feedback=feedback,
            recent_growth_events=growth.recent_events,
        )

    def public_acquisition_hub_for_workspace(
        self,
        workspace_id: str,
        limit: int = 12,
    ) -> PublicAcquisitionHub:
        metrics = self.metrics_for_workspace(workspace_id)
        growth = self.growth_funnel_for_workspace(workspace_id, limit=limit)
        referrals = self.waitlist_referral_dashboard_for_workspace(workspace_id, limit=limit)
        pricing = self.pricing_dashboard_for_workspace(workspace_id)
        readiness = self.beta_readiness_for_workspace(workspace_id)
        surfaces = _public_acquisition_surfaces(
            metrics=metrics,
            growth=growth,
            referrals=referrals,
            pricing=pricing,
            readiness=readiness,
        )
        launch_score = round(
            sum(surface.readiness_score for surface in surfaces) / max(len(surfaces), 1),
            1,
        )
        status = _score_status(launch_score, warning=55, ok=75)
        return PublicAcquisitionHub(
            workspace_id=workspace_id,
            generated_at=_now(),
            status=status,
            launch_score=launch_score,
            headline=_public_acquisition_headline(status, launch_score),
            summary=_public_acquisition_summary(metrics, growth, referrals, pricing),
            primary_cta="공개 데모로 분석 시작",
            primary_cta_path="/#demo-gallery",
            surfaces=surfaces,
            seo_paths=[
                "/",
                "/market/desktop-pc",
                "/market/laptop",
                "/r/{share_token}",
            ],
            channel_actions=_public_acquisition_channel_actions(surfaces),
            next_actions=_public_acquisition_next_actions(surfaces, growth, referrals),
            recent_growth_events=growth.recent_events,
        )

    def retention_hub_for_workspace(
        self,
        workspace_id: str,
        limit: int = 12,
    ) -> RetentionHubDashboard:
        metrics = self.metrics_for_workspace(workspace_id)
        board = self.purchase_decision_board_for_workspace(workspace_id, limit=limit)
        growth = self.growth_funnel_for_workspace(workspace_id, limit=limit)
        advisors = self.list_report_advisor_answers_for_workspace(
            workspace_id,
            limit=limit,
        )
        outcomes = self.list_purchase_outcomes_for_workspace(workspace_id, limit=limit)
        alerts = self.list_alert_subscriptions_for_workspace(workspace_id, limit=limit)
        signals = _retention_signals(metrics, board)
        retention_score = round(
            sum(signal.score for signal in signals) / max(len(signals), 1),
            1,
        )
        status = _score_status(retention_score, warning=55, ok=75)
        return RetentionHubDashboard(
            workspace_id=workspace_id,
            generated_at=_now(),
            status=status,
            retention_score=retention_score,
            headline=_retention_headline(status, retention_score),
            summary=_retention_summary(metrics, board, alerts),
            metric_cards=_retention_metric_cards(metrics, board, len(alerts)),
            signals=signals,
            plays=_retention_plays(metrics, board, advisors, outcomes, alerts),
            next_actions=_retention_next_actions(signals, board),
            recent_events=growth.recent_events,
            recent_advisor_answers=advisors[:5],
            recent_purchase_outcomes=outcomes[:5],
        )

    def public_proof_hub_for_workspace(
        self,
        workspace_id: str,
        limit: int = 8,
    ) -> PublicProofHub:
        metrics = self.metrics_for_workspace(workspace_id)
        acquisition = self.public_acquisition_hub_for_workspace(
            workspace_id,
            limit=limit,
        )
        experiments = self.launch_experiment_dashboard_for_workspace(
            workspace_id,
            limit=limit,
        )
        feedback = self.list_feedback_for_workspace(workspace_id, limit=limit)
        proof_assets = _public_proof_assets(metrics, acquisition, experiments)
        proof_score = _public_proof_score(metrics, proof_assets, experiments)
        status = _score_status(proof_score, warning=55, ok=78)
        return PublicProofHub(
            workspace_id=workspace_id,
            generated_at=_now(),
            status=status,
            proof_score=proof_score,
            headline=_public_proof_headline(status, proof_score),
            summary=_public_proof_summary(metrics, proof_assets),
            hero_proof_strip=_public_proof_strip(metrics, experiments),
            metric_cards=_public_proof_metric_cards(metrics, experiments),
            trust_badges=_public_proof_badges(metrics),
            evidence_kit=_public_evidence_kit(metrics, proof_assets),
            proof_assets=proof_assets,
            objection_answers=_public_objection_answers(metrics),
            cta_cards=_public_proof_cta_cards(acquisition, experiments),
            public_paths=[
                "/",
                "/market/desktop-pc",
                "/market/laptop",
                "/policy/trust-center",
                "/public/onboarding/playbooks",
                "/r/{share_token}",
            ],
            recent_feedback=feedback[:5],
            next_actions=_public_proof_next_actions(status, proof_assets, experiments),
        )

    def create_beta_lead_for_workspace(
        self,
        workspace_id: str,
        request: BetaLeadRequest,
    ) -> BetaLead:
        now = _now()
        lead = BetaLead(
            lead_id=f"lead_{uuid4().hex[:12]}",
            workspace_id=workspace_id,
            email_masked=_mask_contact(request.email),
            persona=request.persona,
            use_case=request.use_case,
            company_size=request.company_size,
            contact_consent=request.contact_consent,
            source=request.source,
            created_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO beta_leads (
                    lead_id, workspace_id, email_masked, persona, use_case,
                    company_size, contact_consent, source, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead.lead_id,
                    lead.workspace_id,
                    lead.email_masked,
                    lead.persona,
                    lead.use_case,
                    lead.company_size,
                    1 if lead.contact_consent else 0,
                    lead.source,
                    lead.created_at,
                ),
            )
        return lead

    def list_beta_leads_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[BetaLead]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM beta_leads
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_beta_lead_from_row(row) for row in rows]

    def create_waitlist_referral_for_workspace(
        self,
        workspace_id: str,
        request: WaitlistReferralRequest,
    ) -> WaitlistReferral:
        now = _now()
        referral_code = _referral_code(request.persona)
        referral = WaitlistReferral(
            referral_id=f"wref_{uuid4().hex[:12]}",
            workspace_id=workspace_id,
            email_masked=_mask_contact(request.email),
            persona=request.persona,
            use_case=request.use_case,
            referral_code=referral_code,
            referred_by_code=request.referred_by_code.strip().upper(),
            referral_url=self._referral_url(referral_code),
            referred_signup_count=0,
            priority_score=_waitlist_priority_score(0, request.contact_consent),
            contact_consent=request.contact_consent,
            source=request.source,
            created_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO waitlist_referrals (
                    referral_id, workspace_id, email_masked, persona, use_case,
                    referral_code, referred_by_code, referral_url,
                    contact_consent, source, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    referral.referral_id,
                    referral.workspace_id,
                    referral.email_masked,
                    referral.persona,
                    referral.use_case,
                    referral.referral_code,
                    referral.referred_by_code,
                    referral.referral_url,
                    1 if referral.contact_consent else 0,
                    referral.source,
                    referral.created_at,
                ),
            )
        return referral

    def _referral_url(self, referral_code: str) -> str:
        path = f"/join?ref={referral_code}"
        if not self.public_site_url:
            return path
        return f"{self.public_site_url}{path}"

    def list_waitlist_referrals_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[WaitlistReferral]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT wr.*,
                    (
                        SELECT COUNT(*)
                        FROM waitlist_referrals child
                        WHERE child.workspace_id = wr.workspace_id
                          AND child.referred_by_code = wr.referral_code
                    ) AS referred_signup_count
                FROM waitlist_referrals wr
                WHERE wr.workspace_id = ?
                ORDER BY wr.created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_waitlist_referral_from_row(row) for row in rows]

    def waitlist_referral_dashboard_for_workspace(
        self,
        workspace_id: str,
        limit: int = 20,
    ) -> WaitlistReferralDashboard:
        latest = self.list_waitlist_referrals_for_workspace(workspace_id, limit=limit)
        with self._connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM waitlist_referrals WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchone()[0]
            referred = conn.execute(
                """
                SELECT COUNT(*)
                FROM waitlist_referrals
                WHERE workspace_id = ? AND referred_by_code != ''
                """,
                (workspace_id,),
            ).fetchone()[0]
            rows = conn.execute(
                """
                SELECT wr.*,
                    (
                        SELECT COUNT(*)
                        FROM waitlist_referrals child
                        WHERE child.workspace_id = wr.workspace_id
                          AND child.referred_by_code = wr.referral_code
                    ) AS referred_signup_count
                FROM waitlist_referrals wr
                WHERE wr.workspace_id = ?
                ORDER BY referred_signup_count DESC, wr.created_at ASC
                LIMIT 5
                """,
                (workspace_id,),
            ).fetchall()
        top_referrers = [
            ReferralLeaderboardItem(
                referral_code=row["referral_code"],
                email_masked=row["email_masked"],
                persona=row["persona"],
                referred_signup_count=int(row["referred_signup_count"] or 0),
                priority_score=_waitlist_priority_score(
                    int(row["referred_signup_count"] or 0),
                    bool(row["contact_consent"]),
                ),
                referral_url=row["referral_url"],
            )
            for row in rows
        ]
        share_rate_hint = round(referred / total, 3) if total else 0
        return WaitlistReferralDashboard(
            workspace_id=workspace_id,
            generated_at=_now(),
            total_referrals=int(total or 0),
            referred_signup_count=int(referred or 0),
            share_rate_hint=share_rate_hint,
            summary=_waitlist_referral_summary(int(total or 0), int(referred or 0)),
            top_referrers=top_referrers,
            latest_referrals=latest,
            next_actions=_waitlist_referral_next_actions(int(total or 0), share_rate_hint),
        )

    def create_subscription_intent_for_workspace(
        self,
        workspace_id: str,
        request: SubscriptionIntentRequest,
    ) -> SubscriptionIntent | None:
        plan = pricing_plan_by_id(request.plan_id)
        if plan is None:
            return None
        now = _now()
        billing_cycle = _billing_cycle(request.billing_cycle)
        estimated_mrr = _estimated_subscription_mrr(plan, billing_cycle, request.team_size)
        readiness_status, recommendation = _subscription_intent_readiness(
            plan,
            request,
            estimated_mrr,
        )
        intent = SubscriptionIntent(
            intent_id=f"subintent_{uuid4().hex[:12]}",
            workspace_id=workspace_id,
            email_masked=_mask_contact(request.email),
            plan_id=plan.plan_id,
            plan_name=plan.name,
            billing_cycle=billing_cycle,
            monthly_price_krw=plan.monthly_price_krw,
            estimated_mrr_krw=estimated_mrr,
            persona=request.persona,
            use_case=request.use_case,
            team_size=request.team_size,
            max_budget_krw=request.max_budget_krw,
            feature_priorities=request.feature_priorities,
            purchase_timing=request.purchase_timing,
            contact_consent=request.contact_consent,
            source=request.source,
            readiness_status=readiness_status,
            recommendation=recommendation,
            created_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO subscription_intents (
                    intent_id, workspace_id, email_masked, plan_id, plan_name,
                    billing_cycle, monthly_price_krw, estimated_mrr_krw, persona,
                    use_case, team_size, max_budget_krw, feature_priorities_json,
                    purchase_timing, contact_consent, source, readiness_status,
                    recommendation, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    intent.intent_id,
                    intent.workspace_id,
                    intent.email_masked,
                    intent.plan_id,
                    intent.plan_name,
                    intent.billing_cycle,
                    intent.monthly_price_krw,
                    intent.estimated_mrr_krw,
                    intent.persona,
                    intent.use_case,
                    intent.team_size,
                    intent.max_budget_krw,
                    json.dumps(intent.feature_priorities, ensure_ascii=False),
                    intent.purchase_timing,
                    1 if intent.contact_consent else 0,
                    intent.source,
                    intent.readiness_status.value,
                    intent.recommendation,
                    intent.created_at,
                ),
            )
        return intent

    def list_subscription_intents_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[SubscriptionIntent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM subscription_intents
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_subscription_intent_from_row(row) for row in rows]

    def pricing_dashboard_for_workspace(self, workspace_id: str) -> PricingDashboard:
        intents = self.list_subscription_intents_for_workspace(workspace_id, limit=200)
        intent_count = len(intents)
        premium_count = sum(1 for item in intents if item.plan_id == "premium")
        team_count = sum(1 for item in intents if item.plan_id == "team")
        estimated_mrr = sum(item.estimated_mrr_krw for item in intents)
        budgets = [item.max_budget_krw for item in intents if item.max_budget_krw is not None]
        plan_counts: dict[str, int] = {}
        for item in intents:
            plan_counts[item.plan_id] = plan_counts.get(item.plan_id, 0) + 1
        top_plan_id = max(plan_counts, key=plan_counts.get) if plan_counts else None
        top_plan = pricing_plan_by_id(top_plan_id) if top_plan_id else None
        status, next_actions = _pricing_dashboard_status(intent_count, estimated_mrr, intents)
        summary = (
            f"구독 의향 {intent_count}건, 예상 MRR {estimated_mrr:,}원, "
            f"연환산 {estimated_mrr * 12:,}원입니다."
        )
        return PricingDashboard(
            workspace_id=workspace_id,
            generated_at=_now(),
            intent_count=intent_count,
            premium_intent_count=premium_count,
            team_intent_count=team_count,
            estimated_mrr_krw=estimated_mrr,
            annualized_revenue_krw=estimated_mrr * 12,
            average_budget_krw=round(sum(budgets) / len(budgets), 2) if budgets else 0,
            top_plan_id=top_plan.plan_id if top_plan else None,
            top_plan_name=top_plan.name if top_plan else None,
            readiness_status=status,
            summary=summary,
            next_actions=next_actions,
            plans=pricing_plans(),
            recent_intents=intents[:20],
        )

    def create_beta_cohort_for_workspace(
        self,
        workspace_id: str,
        request: BetaCohortRequest,
    ) -> BetaCohort:
        now = _now()
        keywords = _cohort_keywords(request)
        cohort_id = f"cohort_{uuid4().hex[:12]}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO beta_cohorts (
                    cohort_id, workspace_id, name, scenario, category, target_persona,
                    target_size, success_metric, keywords_json, notes, active,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cohort_id,
                    workspace_id,
                    request.name,
                    request.scenario,
                    request.category.value,
                    request.target_persona,
                    request.target_size,
                    request.success_metric,
                    json.dumps(keywords, ensure_ascii=False),
                    request.notes,
                    1 if request.active else 0,
                    now,
                    now,
                ),
            )
        cohort = BetaCohort(
            cohort_id=cohort_id,
            workspace_id=workspace_id,
            name=request.name,
            scenario=request.scenario,
            category=request.category,
            target_persona=request.target_persona,
            target_size=request.target_size,
            success_metric=request.success_metric,
            keywords=keywords,
            notes=request.notes,
            active=request.active,
            created_at=now,
            updated_at=now,
        )
        return self._hydrate_beta_cohort(cohort)

    def list_beta_cohorts_for_workspace(
        self,
        workspace_id: str,
        *,
        active: bool | None = None,
        limit: int = 50,
    ) -> list[BetaCohort]:
        where = "WHERE workspace_id = ?"
        params: list[object] = [workspace_id]
        if active is not None:
            where += " AND active = ?"
            params.append(1 if active else 0)
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                FROM beta_cohorts
                {where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._hydrate_beta_cohort(_beta_cohort_from_row(row)) for row in rows]

    def get_beta_cohort_for_workspace(
        self,
        workspace_id: str,
        cohort_id: str,
    ) -> BetaCohort | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM beta_cohorts
                WHERE workspace_id = ? AND cohort_id = ?
                """,
                (workspace_id, cohort_id),
            ).fetchone()
        if row is None:
            return None
        return self._hydrate_beta_cohort(_beta_cohort_from_row(row))

    def beta_backlog_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[BetaBacklogItem]:
        items: list[BetaBacklogItem] = []
        readiness = self.beta_readiness_for_workspace(workspace_id)
        now = _now()
        for check in readiness.checks:
            if check.status == CheckStatus.ok:
                continue
            items.append(
                BetaBacklogItem(
                    backlog_id=f"backlog_readiness_{check.area}",
                    workspace_id=workspace_id,
                    source_type="readiness",
                    source_id=check.area,
                    severity=check.status,
                    title=f"{check.label} 보강",
                    evidence=check.metric,
                    suggested_action=check.recommendation,
                    created_at=now,
                )
            )
        learning = self.learning_insights_for_workspace(workspace_id, limit=limit)
        for insight in learning.insights:
            model_name = insight.model_name or insight.product_id
            tags = ", ".join(insight.learning_tags) if insight.learning_tags else "태그 없음"
            items.append(
                BetaBacklogItem(
                    backlog_id=f"backlog_learning_{insight.product_id}",
                    workspace_id=workspace_id,
                    source_type="learning",
                    source_id=insight.product_id,
                    severity=insight.status,
                    title=f"학습 인사이트 개선: {model_name}",
                    evidence=f"{insight.evidence} / 태그: {tags}",
                    suggested_action=insight.recommended_action,
                    created_at=learning.generated_at,
                )
            )
        with self._connect() as conn:
            feedback_rows = conn.execute(
                """
                SELECT feedback_id, rating, purchase_intent, reason,
                       improvement_requests_json, created_at
                FROM user_feedback
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
            audit_rows = conn.execute(
                """
                SELECT trace_id, quality_audit_json, created_at
                FROM analysis_runs
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        for row in feedback_rows:
            requests = json.loads(row["improvement_requests_json"])
            if int(row["rating"]) >= 4 and not requests:
                continue
            severity = CheckStatus.blocker if int(row["rating"]) <= 2 else CheckStatus.warning
            action = (
                requests[0]
                if requests
                else "낮은 만족도 사유를 확인해 추천 설명과 근거를 보강하세요."
            )
            items.append(
                BetaBacklogItem(
                    backlog_id=f"backlog_feedback_{row['feedback_id']}",
                    workspace_id=workspace_id,
                    source_type="feedback",
                    source_id=row["feedback_id"],
                    severity=severity,
                    title=f"사용자 피드백 개선: 만족도 {row['rating']}점",
                    evidence=row["reason"] or "상세 사유 없음",
                    suggested_action=action,
                    created_at=row["created_at"],
                )
            )
        for row in audit_rows:
            if not row["quality_audit_json"] or row["quality_audit_json"] == "{}":
                continue
            audit = AnalysisQualityAudit.model_validate_json(row["quality_audit_json"])
            for index, blocker in enumerate(audit.launch_blockers):
                items.append(
                    BetaBacklogItem(
                        backlog_id=f"backlog_quality_{audit.trace_id}_{index}",
                        workspace_id=workspace_id,
                        source_type="quality",
                        source_id=audit.trace_id,
                        severity=CheckStatus.blocker,
                        title="공개 차단 사유 해소",
                        evidence=blocker,
                        suggested_action=(
                            "해당 분석의 입력 조건, 출처, 옵션 검수표를 "
                            "보강한 뒤 재분석하세요."
                        ),
                        created_at=row["created_at"],
                    )
                )
        return self._apply_beta_backlog_actions(workspace_id, items[:limit])

    def update_beta_backlog_action_for_workspace(
        self,
        workspace_id: str,
        backlog_id: str,
        request: BetaBacklogActionRequest,
    ) -> BetaBacklogAction | None:
        known_items = {
            item.backlog_id: item
            for item in self.beta_backlog_for_workspace(workspace_id, limit=200)
        }
        known_item = known_items.get(backlog_id)
        if known_item is None:
            return None
        now = _now()
        existing = self._beta_backlog_action_for_workspace(workspace_id, backlog_id)
        sla_due_at = request.sla_due_at or (
            existing.sla_due_at if existing and existing.sla_due_at else known_item.sla_due_at
        )
        completed_at = (
            now
            if request.status == BetaBacklogStatus.done
            else None
        )
        completion_summary = request.completion_summary
        if request.status == BetaBacklogStatus.done and not completion_summary:
            completion_summary = _beta_completion_summary(known_item, request)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO beta_backlog_actions (
                    backlog_id, workspace_id, status, assignee, note,
                    sla_due_at, completed_at, completion_summary, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(workspace_id, backlog_id) DO UPDATE SET
                    status = excluded.status,
                    assignee = excluded.assignee,
                    note = excluded.note,
                    sla_due_at = excluded.sla_due_at,
                    completed_at = excluded.completed_at,
                    completion_summary = excluded.completion_summary,
                    updated_at = excluded.updated_at
                """,
                (
                    backlog_id,
                    workspace_id,
                    request.status.value,
                    request.assignee,
                    request.note,
                    sla_due_at,
                    completed_at,
                    completion_summary,
                    now,
                ),
            )
        return BetaBacklogAction(
            backlog_id=backlog_id,
            workspace_id=workspace_id,
            status=request.status,
            assignee=request.assignee,
            note=request.note,
            sla_due_at=sla_due_at,
            completed_at=completed_at,
            completion_summary=completion_summary,
            updated_at=now,
        )

    def beta_backlog_action_summary_for_workspace(
        self,
        workspace_id: str,
        limit: int = 200,
    ) -> BetaBacklogSummary:
        items = self.beta_backlog_for_workspace(workspace_id, limit=limit)
        done_items = [item for item in items if item.status == BetaBacklogStatus.done]
        overdue_items = [item for item in items if item.is_overdue]
        due_soon_items = [
            item
            for item in items
            if _is_due_soon(item.sla_due_at)
            and item.status not in {BetaBacklogStatus.done, BetaBacklogStatus.dismissed}
        ]
        next_actions: list[str] = []
        if overdue_items:
            next_actions.append(f"SLA 초과 백로그 {len(overdue_items)}건을 먼저 처리하세요.")
        if due_soon_items:
            next_actions.append(f"24시간 내 SLA 도래 항목 {len(due_soon_items)}건을 확인하세요.")
        unassigned = [
            item
            for item in items
            if not item.assignee
            and item.status in {BetaBacklogStatus.open, BetaBacklogStatus.in_progress}
        ]
        if unassigned:
            next_actions.append(f"담당자 미지정 백로그 {len(unassigned)}건을 배정하세요.")
        if not next_actions:
            next_actions.append("현재 운영 SLA 기준으로 즉시 처리할 백로그는 없습니다.")
        return BetaBacklogSummary(
            workspace_id=workspace_id,
            total_count=len(items),
            open_count=sum(1 for item in items if item.status == BetaBacklogStatus.open),
            in_progress_count=sum(
                1 for item in items if item.status == BetaBacklogStatus.in_progress
            ),
            done_count=len(done_items),
            dismissed_count=sum(
                1 for item in items if item.status == BetaBacklogStatus.dismissed
            ),
            overdue_count=len(overdue_items),
            due_soon_count=len(due_soon_items),
            blocker_count=sum(1 for item in items if item.severity == CheckStatus.blocker),
            completion_summaries=[
                item.completion_summary
                for item in done_items
                if item.completion_summary
            ][:10],
            next_actions=_dedupe_strings(next_actions),
        )

    def beta_cohort_report_for_workspace(
        self,
        workspace_id: str,
        cohort_id: str,
    ) -> BetaCohortReport | None:
        cohort = self.get_beta_cohort_for_workspace(workspace_id, cohort_id)
        if cohort is None:
            return None
        backlog = [
            item
            for item in self.beta_backlog_for_workspace(workspace_id, limit=100)
            if item.status not in {BetaBacklogStatus.done, BetaBacklogStatus.dismissed}
        ][:10]
        generated_at = _now()
        purchase_rate = round(cohort.purchase_intent_rate * 100)
        summary = (
            f"{cohort.name}은 리드 {cohort.lead_count}/{cohort.target_size}명, "
            f"피드백 {cohort.feedback_count}건, 구매 의향 {purchase_rate}%를 기록했습니다."
        )
        recommendations = _cohort_report_recommendations(cohort, backlog)
        markdown = _render_beta_cohort_markdown(
            cohort=cohort,
            generated_at=generated_at,
            summary=summary,
            recommendations=recommendations,
            backlog=backlog,
        )
        return BetaCohortReport(
            cohort=cohort,
            generated_at=generated_at,
            summary=summary,
            metric_cards={
                "lead_count": cohort.lead_count,
                "target_size": cohort.target_size,
                "feedback_count": cohort.feedback_count,
                "average_satisfaction": cohort.average_satisfaction,
                "purchase_intent_rate": cohort.purchase_intent_rate,
                "readiness_score": cohort.readiness_score,
            },
            recommendations=recommendations,
            backlog=backlog,
            markdown=markdown,
        )

    def _apply_beta_backlog_actions(
        self,
        workspace_id: str,
        items: list[BetaBacklogItem],
    ) -> list[BetaBacklogItem]:
        if not items:
            return items
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM beta_backlog_actions
                WHERE workspace_id = ?
                """,
                (workspace_id,),
            ).fetchall()
        actions = {row["backlog_id"]: _beta_backlog_action_from_row(row) for row in rows}
        merged: list[BetaBacklogItem] = []
        for item in items:
            action = actions.get(item.backlog_id)
            default_due_at = _default_sla_due_at(item)
            if action is None:
                merged.append(
                    item.model_copy(
                        update={
                            "sla_due_at": default_due_at,
                            "is_overdue": _is_overdue(default_due_at, item.status),
                        }
                    )
                )
                continue
            sla_due_at = action.sla_due_at or default_due_at
            merged.append(
                item.model_copy(
                    update={
                        "status": action.status,
                        "assignee": action.assignee,
                        "action_note": action.note,
                        "action_updated_at": action.updated_at,
                        "sla_due_at": sla_due_at,
                        "is_overdue": _is_overdue(sla_due_at, action.status),
                        "completed_at": action.completed_at,
                        "completion_summary": action.completion_summary,
                    }
                )
            )
        return merged

    def _beta_backlog_action_for_workspace(
        self,
        workspace_id: str,
        backlog_id: str,
    ) -> BetaBacklogAction | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM beta_backlog_actions
                WHERE workspace_id = ? AND backlog_id = ?
                """,
                (workspace_id, backlog_id),
            ).fetchone()
        if row is None:
            return None
        return _beta_backlog_action_from_row(row)

    def _hydrate_beta_cohort(self, cohort: BetaCohort) -> BetaCohort:
        keywords = cohort.keywords or [cohort.name, cohort.scenario, cohort.target_persona]
        with self._connect() as conn:
            lead_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM beta_leads
                WHERE workspace_id = ?
                  AND (persona = ? OR use_case LIKE ? OR use_case LIKE ?)
                """,
                (
                    cohort.workspace_id,
                    cohort.target_persona,
                    _like_pattern(cohort.scenario),
                    _like_pattern(keywords[0]),
                ),
            ).fetchone()[0]
            feedback_row = conn.execute(
                """
                SELECT
                    COUNT(*) AS feedback_count,
                    AVG(f.rating) AS average_satisfaction,
                    AVG(CASE WHEN f.purchase_intent = 1 THEN 1.0 ELSE 0.0 END)
                        AS purchase_intent_rate
                FROM user_feedback f
                JOIN analysis_runs ar
                  ON ar.trace_id = f.trace_id
                 AND ar.workspace_id = f.workspace_id
                WHERE f.workspace_id = ?
                  AND (
                    ar.category = ?
                    OR ar.purpose LIKE ?
                    OR f.reason LIKE ?
                    OR f.improvement_requests_json LIKE ?
                  )
                """,
                (
                    cohort.workspace_id,
                    cohort.category.value,
                    _like_pattern(cohort.scenario),
                    _like_pattern(keywords[0]),
                    _like_pattern(keywords[0]),
                ),
            ).fetchone()
        lead_score = min(100.0, (int(lead_count or 0) / cohort.target_size) * 100)
        feedback_count = int(feedback_row["feedback_count"] or 0)
        satisfaction = round(float(feedback_row["average_satisfaction"] or 0), 2)
        intent_rate = round(float(feedback_row["purchase_intent_rate"] or 0), 4)
        feedback_score = min(100.0, feedback_count * 20 + satisfaction * 10 + intent_rate * 30)
        return cohort.model_copy(
            update={
                "lead_count": int(lead_count or 0),
                "feedback_count": feedback_count,
                "average_satisfaction": satisfaction,
                "purchase_intent_rate": intent_rate,
                "readiness_score": round(lead_score * 0.45 + feedback_score * 0.55, 2),
            }
        )

    def add_review_items(self, items: list[ReviewQueueItem]) -> list[ReviewQueueItem]:
        with self._connect() as conn:
            for item in items:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO source_review_queue (
                        review_id, source_id, source_json, status, reason,
                        created_at, resolved_at, reviewer, note
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.review_id,
                        item.source.source_id,
                        item.source.model_dump_json(),
                        item.status.value,
                        item.reason,
                        item.created_at,
                        item.resolved_at,
                        item.reviewer,
                        "",
                    ),
                )
        return items

    def list_review_items(
        self,
        *,
        status: ReviewStatus | None = ReviewStatus.pending,
        limit: int = 50,
    ) -> list[ReviewQueueItem]:
        query = """
            SELECT *
            FROM source_review_queue
        """
        params: list[str | int] = []
        if status is not None:
            query += " WHERE status = ?"
            params.append(status.value)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_review_item_from_row(row) for row in rows]

    def decide_review(
        self,
        review_id: str,
        *,
        status: ReviewStatus,
        reviewer: str,
        note: str,
    ) -> ReviewDecision | None:
        now = _now()
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT review_id FROM source_review_queue WHERE review_id = ?",
                (review_id,),
            ).fetchone()
            if existing is None:
                return None
            conn.execute(
                """
                UPDATE source_review_queue
                SET status = ?, reviewer = ?, note = ?, resolved_at = ?
                WHERE review_id = ?
                """,
                (status.value, reviewer, note, now, review_id),
            )
        return ReviewDecision(
            review_id=review_id,
            status=status,
            reviewer=reviewer,
            note=note,
            resolved_at=now,
        )

    def create_source_monitor_for_workspace(
        self,
        workspace_id: str,
        request: SourceMonitorRequest,
    ) -> SourceMonitor:
        now = _now()
        monitor = SourceMonitor(
            monitor_id=f"monitor_{uuid4().hex[:12]}",
            workspace_id=workspace_id,
            url=request.url,
            category=request.category,
            kind=request.kind,
            expected_model=request.expected_model,
            source_name=request.source_name,
            seller=request.seller,
            cadence_minutes=request.cadence_minutes,
            active=request.active,
            created_at=now,
            updated_at=now,
            html_snapshot=request.html_snapshot,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO source_monitors (
                    monitor_id, workspace_id, url, category, kind, expected_model,
                    source_name, seller, cadence_minutes, active, html_snapshot,
                    last_run_at, last_status, last_source_id, failure_count,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    monitor.monitor_id,
                    monitor.workspace_id,
                    monitor.url,
                    monitor.category.value,
                    monitor.kind.value,
                    monitor.expected_model,
                    monitor.source_name,
                    monitor.seller,
                    monitor.cadence_minutes,
                    1 if monitor.active else 0,
                    monitor.html_snapshot,
                    monitor.last_run_at,
                    monitor.last_status,
                    monitor.last_source_id,
                    monitor.failure_count,
                    monitor.created_at,
                    monitor.updated_at,
                ),
            )
        return monitor

    def list_source_monitors_for_workspace(
        self,
        workspace_id: str,
        *,
        active: bool | None = None,
        monitor_ids: list[str] | None = None,
        limit: int = 50,
    ) -> list[SourceMonitor]:
        query = """
            SELECT *
            FROM source_monitors
            WHERE workspace_id = ?
        """
        params: list[str | int] = [workspace_id]
        if active is not None:
            query += " AND active = ?"
            params.append(1 if active else 0)
        if monitor_ids:
            placeholders = ",".join("?" for _ in monitor_ids)
            query += f" AND monitor_id IN ({placeholders})"
            params.extend(monitor_ids)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_source_monitor_from_row(row) for row in rows]

    def record_source_refresh_run(self, run: SourceRefreshRun) -> SourceRefreshRun:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO source_refresh_runs (
                    run_id, monitor_id, workspace_id, status, source_id,
                    review_id, fetched_live, message, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.monitor_id,
                    run.workspace_id,
                    run.status,
                    run.source_id,
                    run.review_id,
                    1 if run.fetched_live else 0,
                    run.message,
                    run.created_at,
                ),
            )
            conn.execute(
                """
                UPDATE source_monitors
                SET last_run_at = ?,
                    last_status = ?,
                    last_source_id = ?,
                    failure_count = CASE
                        WHEN ? = 'failed' THEN failure_count + 1
                        ELSE 0
                    END,
                    updated_at = ?
                WHERE monitor_id = ? AND workspace_id = ?
                """,
                (
                    run.created_at,
                    run.status,
                    run.source_id,
                    run.status,
                    run.created_at,
                    run.monitor_id,
                    run.workspace_id,
                ),
            )
        return run

    def list_source_refresh_runs_for_workspace(
        self,
        workspace_id: str,
        *,
        limit: int = 50,
    ) -> list[SourceRefreshRun]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM source_refresh_runs
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_source_refresh_run_from_row(row) for row in rows]

    def create_integration_provider_for_workspace(
        self,
        workspace_id: str,
        request: IntegrationProviderRequest,
    ) -> IntegrationProvider:
        now = _now()
        last_verified_at = now if request.status == IntegrationStatus.verified else None
        provider = IntegrationProvider(
            integration_id=f"integration_{uuid4().hex[:12]}",
            workspace_id=workspace_id,
            provider_name=request.provider_name.strip(),
            category=request.category,
            status=request.status,
            credential_status=request.credential_status.strip() or "not_connected",
            rate_limit_per_hour=request.rate_limit_per_hour,
            retention_days=request.retention_days,
            endpoint=request.endpoint.strip(),
            evidence=request.evidence.strip(),
            notes=request.notes.strip(),
            created_at=now,
            updated_at=now,
            last_verified_at=last_verified_at,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO integration_providers (
                    integration_id, workspace_id, provider_name, category, status,
                    credential_status, rate_limit_per_hour, retention_days,
                    endpoint, evidence, notes, created_at, updated_at, last_verified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    provider.integration_id,
                    provider.workspace_id,
                    provider.provider_name,
                    provider.category.value,
                    provider.status.value,
                    provider.credential_status,
                    provider.rate_limit_per_hour,
                    provider.retention_days,
                    provider.endpoint,
                    provider.evidence,
                    provider.notes,
                    provider.created_at,
                    provider.updated_at,
                    provider.last_verified_at,
                ),
            )
        return provider

    def list_integration_providers_for_workspace(
        self,
        workspace_id: str,
        *,
        limit: int = 100,
    ) -> list[IntegrationProvider]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM integration_providers
                WHERE workspace_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_integration_provider_from_row(row) for row in rows]

    def integration_readiness_for_workspace(
        self,
        workspace_id: str,
    ) -> IntegrationReadinessDashboard:
        providers = self.list_integration_providers_for_workspace(workspace_id, limit=500)
        by_category: dict[IntegrationCategory, IntegrationProvider] = {}
        for provider in providers:
            current = by_category.get(provider.category)
            current_weight = (
                _integration_status_weight(current.status) if current is not None else -1
            )
            if _integration_status_weight(provider.status) > current_weight:
                by_category[provider.category] = provider

        checks = [
            _integration_readiness_check(category, by_category.get(category), critical)
            for category, critical in REQUIRED_INTEGRATION_CATEGORIES
        ]
        blocker_count = sum(1 for check in checks if check.status == CheckStatus.blocker)
        warning_count = sum(1 for check in checks if check.status == CheckStatus.warning)
        verified_count = sum(
            1
            for provider in by_category.values()
            if provider.status == IntegrationStatus.verified
        )
        configured_count = sum(
            1
            for provider in by_category.values()
            if provider.status in {IntegrationStatus.configured, IntegrationStatus.verified}
        )
        mock_count = sum(
            1
            for provider in by_category.values()
            if provider.status == IntegrationStatus.mock
        )
        score = _integration_readiness_score(checks)
        if blocker_count:
            status = CheckStatus.blocker
        elif warning_count:
            status = CheckStatus.warning
        else:
            status = CheckStatus.ok
        required_actions = [
            check.recommendation for check in checks if check.status != CheckStatus.ok
        ][:5]
        return IntegrationReadinessDashboard(
            workspace_id=workspace_id,
            generated_at=_now(),
            readiness_score=score,
            status=status,
            verified_count=verified_count,
            configured_count=configured_count,
            blocker_count=blocker_count,
            mock_count=mock_count,
            required_count=len(REQUIRED_INTEGRATION_CATEGORIES),
            summary=_integration_readiness_summary(status, score, blocker_count, warning_count),
            required_actions=required_actions,
            providers=providers,
            checks=checks,
        )

    def create_source_provider_policy_for_workspace(
        self,
        workspace_id: str,
        request: SourceProviderPolicyRequest,
    ) -> SourceProviderPolicy:
        now = _now()
        policy = SourceProviderPolicy(
            provider_id=f"provider_{uuid4().hex[:12]}",
            workspace_id=workspace_id,
            provider_name=request.provider_name,
            host_pattern=request.host_pattern.strip().lower(),
            kind=request.kind,
            live_fetch_allowed=request.live_fetch_allowed,
            robots_status=request.robots_status,
            terms_status=request.terms_status,
            credential_status=request.credential_status.strip() or "not_connected",
            rate_limit_per_hour=request.rate_limit_per_hour,
            notes=request.notes,
            created_at=now,
            updated_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO source_provider_policies (
                    provider_id, workspace_id, provider_name, host_pattern, kind,
                    live_fetch_allowed, robots_status, terms_status, credential_status,
                    rate_limit_per_hour, notes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    policy.provider_id,
                    policy.workspace_id,
                    policy.provider_name,
                    policy.host_pattern,
                    policy.kind.value,
                    1 if policy.live_fetch_allowed else 0,
                    policy.robots_status.value,
                    policy.terms_status.value,
                    policy.credential_status,
                    policy.rate_limit_per_hour,
                    policy.notes,
                    policy.created_at,
                    policy.updated_at,
                ),
            )
        return policy

    def list_source_provider_policies_for_workspace(
        self,
        workspace_id: str,
        *,
        limit: int = 100,
    ) -> list[SourceProviderPolicy]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM source_provider_policies
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (workspace_id, limit),
            ).fetchall()
        return [_source_provider_policy_from_row(row) for row in rows]

    def record_source_provider_fetch(self, log: SourceProviderFetchLog) -> SourceProviderFetchLog:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO source_provider_fetch_log (
                    fetch_id, provider_id, workspace_id, url, host, status,
                    message, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log.fetch_id,
                    log.provider_id,
                    log.workspace_id,
                    log.url,
                    log.host,
                    log.status,
                    log.message,
                    log.created_at,
                ),
            )
        return log

    def count_recent_provider_fetches(
        self,
        workspace_id: str,
        provider_id: str,
        *,
        since_minutes: int = 60,
        status: str = "allowed",
    ) -> int:
        since = (datetime.now(UTC) - timedelta(minutes=since_minutes)).isoformat()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*)
                FROM source_provider_fetch_log
                WHERE workspace_id = ?
                  AND provider_id = ?
                  AND status = ?
                  AND created_at >= ?
                """,
                (workspace_id, provider_id, status, since),
            ).fetchone()
        return int(row[0])

    def metrics(self) -> OperationsMetrics:
        return self.metrics_for_workspace(None)

    def metrics_for_workspace(self, workspace_id: str | None) -> OperationsMetrics:
        with self._connect() as conn:
            where = " WHERE workspace_id = ?" if workspace_id else ""
            params = (workspace_id,) if workspace_id else ()
            analysis_runs = conn.execute(
                f"SELECT COUNT(*) FROM analysis_runs{where}",
                params,
            ).fetchone()[0]
            saved_reports = conn.execute(
                f"SELECT COUNT(*) FROM saved_reports{where}",
                params,
            ).fetchone()[0]
            shared_reports = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM saved_reports{where}
                {' AND ' if where else ' WHERE '}shared_at IS NOT NULL
                """,
                params,
            ).fetchone()[0]
            public_share_views = conn.execute(
                f"SELECT SUM(share_views) FROM saved_reports{where}",
                params,
            ).fetchone()[0]
            alert_subscriptions = conn.execute(
                f"SELECT COUNT(*) FROM alert_subscriptions{where}",
                params,
            ).fetchone()[0]
            feedback_count = conn.execute(
                f"SELECT COUNT(*) FROM user_feedback{where}",
                params,
            ).fetchone()[0]
            beta_leads = conn.execute(
                f"SELECT COUNT(*) FROM beta_leads{where}",
                params,
            ).fetchone()[0]
            subscription_intents = conn.execute(
                f"SELECT COUNT(*) FROM subscription_intents{where}",
                params,
            ).fetchone()[0]
            premium_subscription_intents = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM subscription_intents{where}
                {' AND ' if where else ' WHERE '}plan_id IN ('premium', 'team')
                """,
                params,
            ).fetchone()[0]
            estimated_mrr_row = conn.execute(
                f"SELECT SUM(estimated_mrr_krw) FROM subscription_intents{where}",
                params,
            ).fetchone()
            alert_events = conn.execute(
                f"SELECT COUNT(*) FROM alert_delivery_events{where}",
                params,
            ).fetchone()[0]
            alert_channels = conn.execute(
                f"SELECT COUNT(*) FROM alert_notification_channels{where}",
                params,
            ).fetchone()[0]
            alert_delivery_attempts = conn.execute(
                f"SELECT COUNT(*) FROM alert_delivery_attempts{where}",
                params,
            ).fetchone()[0]
            trace_spans = conn.execute(
                f"SELECT COUNT(*) FROM trace_spans{where}",
                params,
            ).fetchone()[0]
            source_monitors = conn.execute(
                f"SELECT COUNT(*) FROM source_monitors{where}",
                params,
            ).fetchone()[0]
            source_refresh_runs = conn.execute(
                f"SELECT COUNT(*) FROM source_refresh_runs{where}",
                params,
            ).fetchone()[0]
            source_refresh_failures = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM source_refresh_runs{where}
                {' AND ' if where else ' WHERE '}status = 'failed'
                """,
                params,
            ).fetchone()[0]
            source_provider_policies = conn.execute(
                f"SELECT COUNT(*) FROM source_provider_policies{where}",
                params,
            ).fetchone()[0]
            source_provider_fetches = conn.execute(
                f"SELECT COUNT(*) FROM source_provider_fetch_log{where}",
                params,
            ).fetchone()[0]
            source_provider_blocked_fetches = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM source_provider_fetch_log{where}
                {' AND ' if where else ' WHERE '}status = 'blocked'
                """,
                params,
            ).fetchone()[0]
            sent_alert_deliveries = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM alert_delivery_attempts{where}
                {' AND ' if where else ' WHERE '}delivery_status = 'sent'
                """,
                params,
            ).fetchone()[0]
            failed_alert_deliveries = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM alert_delivery_attempts{where}
                {' AND ' if where else ' WHERE '}delivery_status = 'failed'
                """,
                params,
            ).fetchone()[0]
            completion_report_batches = conn.execute(
                f"SELECT COUNT(*) FROM completion_report_batches{where}",
                params,
            ).fetchone()[0]
            completion_report_deliveries = conn.execute(
                f"SELECT COUNT(*) FROM completion_report_deliveries{where}",
                params,
            ).fetchone()[0]
            completion_delivery_opens = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM completion_delivery_engagement{where}
                {' AND ' if where else ' WHERE '}event_type = 'open'
                """,
                params,
            ).fetchone()[0]
            completion_delivery_clicks = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM completion_delivery_engagement{where}
                {' AND ' if where else ' WHERE '}event_type = 'click'
                """,
                params,
            ).fetchone()[0]
            completion_delivery_bounces = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM completion_delivery_provider_events{where}
                {' AND ' if where else ' WHERE '}event_type = 'bounced'
                """,
                params,
            ).fetchone()[0]
            completion_delivery_complaints = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM completion_delivery_provider_events{where}
                {' AND ' if where else ' WHERE '}event_type = 'complained'
                """,
                params,
            ).fetchone()[0]
            completion_delivery_suppressions = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM completion_delivery_provider_events{where}
                {' AND ' if where else ' WHERE '}event_type = 'suppressed'
                """,
                params,
            ).fetchone()[0]
            checkout_reviews = conn.execute(
                f"SELECT COUNT(*) FROM checkout_reviews{where}",
                params,
            ).fetchone()[0]
            checkout_blocked_reviews = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM checkout_reviews{where}
                {' AND ' if where else ' WHERE '}checkout_blocked = 1
                """,
                params,
            ).fetchone()[0]
            checkout_ready_reviews = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM checkout_reviews{where}
                {' AND ' if where else ' WHERE '}readiness_status = 'ok'
                """,
                params,
            ).fetchone()[0]
            report_advisor_answers = conn.execute(
                f"SELECT COUNT(*) FROM report_advisor_answers{where}",
                params,
            ).fetchone()[0]
            report_advisor_warning_answers = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM report_advisor_answers{where}
                {' AND ' if where else ' WHERE '}status IN ('warning', 'blocker')
                """,
                params,
            ).fetchone()[0]
            purchase_outcomes = conn.execute(
                f"SELECT COUNT(*) FROM purchase_outcomes{where}",
                params,
            ).fetchone()[0]
            completed_purchase_outcomes = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM purchase_outcomes{where}
                {' AND ' if where else ' WHERE '}status = 'purchased'
                """,
                params,
            ).fetchone()[0]
            abandoned_purchase_outcomes = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM purchase_outcomes{where}
                {' AND ' if where else ' WHERE '}status = 'abandoned'
                """,
                params,
            ).fetchone()[0]
            delayed_purchase_outcomes = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM purchase_outcomes{where}
                {' AND ' if where else ' WHERE '}status = 'delayed'
                """,
                params,
            ).fetchone()[0]
            returned_purchase_outcomes = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM purchase_outcomes{where}
                {' AND ' if where else ' WHERE '}status = 'returned'
                """,
                params,
            ).fetchone()[0]
            purchase_links = conn.execute(
                f"SELECT COUNT(*) FROM purchase_links{where}",
                params,
            ).fetchone()[0]
            affiliate_purchase_links = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM purchase_links{where}
                {' AND ' if where else ' WHERE '}is_affiliate = 1
                """,
                params,
            ).fetchone()[0]
            purchase_link_clicks = conn.execute(
                f"SELECT COUNT(*) FROM purchase_link_clicks{where}",
                params,
            ).fetchone()[0]
            growth_events = conn.execute(
                f"SELECT COUNT(*) FROM growth_events{where}",
                params,
            ).fetchone()[0]
            growth_unique_traces = conn.execute(
                f"""
                SELECT COUNT(DISTINCT COALESCE(trace_id, event_id))
                FROM growth_events{where}
                """,
                params,
            ).fetchone()[0]
            recommendation_card_clicks = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM growth_events{where}
                {' AND ' if where else ' WHERE '}event_type = 'recommendation_click'
                """,
                params,
            ).fetchone()[0]
            alternative_scenario_clicks = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM growth_events{where}
                {' AND ' if where else ' WHERE '}event_type = 'alternative_click'
                """,
                params,
            ).fetchone()[0]
            share_cta_clicks = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM growth_events{where}
                {' AND ' if where else ' WHERE '}event_type = 'share_cta'
                """,
                params,
            ).fetchone()[0]
            alert_cta_clicks = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM growth_events{where}
                {' AND ' if where else ' WHERE '}event_type = 'alert_cta'
                """,
                params,
            ).fetchone()[0]
            subscription_cta_clicks = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM growth_events{where}
                {' AND ' if where else ' WHERE '}event_type = 'subscription_cta'
                """,
                params,
            ).fetchone()[0]
            outcome_value_row = conn.execute(
                f"""
                SELECT
                    AVG(price_delta_krw) AS average_delta,
                    SUM(conversion_value_krw) AS conversion_value
                FROM purchase_outcomes{where}
                """,
                params,
            ).fetchone()
            triggered_alerts = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM alert_delivery_events{where}
                {' AND ' if where else ' WHERE '}delivery_status IN ('queued', 'sent', 'failed')
                """,
                params,
            ).fetchone()[0]
            latest = conn.execute(
                f"SELECT trace_id FROM analysis_runs{where} ORDER BY created_at DESC LIMIT 1",
                params,
            ).fetchone()
            score_where = (
                " WHERE top_score > 0 AND workspace_id = ?"
                if workspace_id
                else " WHERE top_score > 0"
            )
            score_row = conn.execute(
                f"SELECT AVG(top_score) FROM analysis_runs{score_where}",
                params,
            ).fetchone()
            quality_row = conn.execute(
                f"SELECT AVG(quality_score), SUM(estimated_cost_krw) FROM analysis_runs{where}",
                params,
            ).fetchone()
            feedback_row = conn.execute(
                f"""
                SELECT
                    AVG(rating) AS average_satisfaction,
                    AVG(CASE WHEN purchase_intent = 1 THEN 1.0 ELSE 0.0 END)
                        AS purchase_intent_rate
                FROM user_feedback{where}
                """,
                params,
            ).fetchone()
            ready_row = conn.execute(
                f"""
                SELECT AVG(CASE WHEN final_pick_id IS NOT NULL THEN 1.0 ELSE 0.0 END)
                FROM analysis_runs{where}
                """,
                params,
            ).fetchone()
        return OperationsMetrics(
            workspace_id=workspace_id,
            analysis_runs=analysis_runs,
            saved_reports=saved_reports,
            shared_reports=shared_reports,
            public_share_views=int(public_share_views or 0),
            alert_subscriptions=alert_subscriptions,
            alert_events=alert_events,
            triggered_alerts=triggered_alerts,
            alert_channels=alert_channels,
            alert_delivery_attempts=alert_delivery_attempts,
            sent_alert_deliveries=sent_alert_deliveries,
            failed_alert_deliveries=failed_alert_deliveries,
            completion_report_batches=completion_report_batches,
            completion_report_deliveries=completion_report_deliveries,
            completion_delivery_opens=completion_delivery_opens,
            completion_delivery_clicks=completion_delivery_clicks,
            completion_delivery_bounces=completion_delivery_bounces,
            completion_delivery_complaints=completion_delivery_complaints,
            completion_delivery_suppressions=completion_delivery_suppressions,
            checkout_reviews=checkout_reviews,
            checkout_blocked_reviews=checkout_blocked_reviews,
            checkout_ready_reviews=checkout_ready_reviews,
            report_advisor_answers=report_advisor_answers,
            report_advisor_warning_answers=report_advisor_warning_answers,
            purchase_outcomes=purchase_outcomes,
            completed_purchase_outcomes=completed_purchase_outcomes,
            abandoned_purchase_outcomes=abandoned_purchase_outcomes,
            delayed_purchase_outcomes=delayed_purchase_outcomes,
            returned_purchase_outcomes=returned_purchase_outcomes,
            purchase_links=purchase_links,
            affiliate_purchase_links=affiliate_purchase_links,
            purchase_link_clicks=purchase_link_clicks,
            growth_events=growth_events,
            growth_unique_traces=growth_unique_traces,
            recommendation_card_clicks=recommendation_card_clicks,
            alternative_scenario_clicks=alternative_scenario_clicks,
            share_cta_clicks=share_cta_clicks,
            alert_cta_clicks=alert_cta_clicks,
            subscription_cta_clicks=subscription_cta_clicks,
            purchase_conversion_rate=round(
                (
                    completed_purchase_outcomes
                    / purchase_outcomes
                    if purchase_outcomes
                    else 0
                ),
                4,
            ),
            average_final_price_delta_krw=round(
                float(outcome_value_row["average_delta"] or 0),
                2,
            ),
            purchase_outcome_value_krw=int(outcome_value_row["conversion_value"] or 0),
            source_monitors=source_monitors,
            source_refresh_runs=source_refresh_runs,
            source_refresh_failures=source_refresh_failures,
            source_provider_policies=source_provider_policies,
            source_provider_fetches=source_provider_fetches,
            source_provider_blocked_fetches=source_provider_blocked_fetches,
            trace_spans=trace_spans,
            feedback_count=feedback_count,
            beta_leads=beta_leads,
            subscription_intents=subscription_intents,
            premium_subscription_intents=premium_subscription_intents,
            estimated_mrr_krw=int(estimated_mrr_row[0] or 0),
            latest_trace_id=latest["trace_id"] if latest else None,
            average_top_score=round(float(score_row[0] or 0), 2),
            average_quality_score=round(float(quality_row[0] or 0), 2),
            average_satisfaction=round(float(feedback_row["average_satisfaction"] or 0), 2),
            purchase_intent_rate=round(float(feedback_row["purchase_intent_rate"] or 0), 4),
            estimated_cost_krw=round(float(quality_row[1] or 0), 2),
            conversion_ready_rate=round(float(ready_row[0] or 0), 4),
        )

    def data_governance_for_workspace(self, workspace_id: str) -> DataGovernanceDashboard:
        inventory: list[DataInventoryItem] = []
        with self._connect() as conn:
            for spec in DATA_INVENTORY_SPECS:
                item = _data_inventory_item(conn, workspace_id, spec)
                inventory.append(item)
        total_records = sum(item.record_count for item in inventory)
        raw_contact_surfaces = sum(
            1
            for item in inventory
            if item.record_count and item.pii_scope == "raw_contact"
        )
        masked_contact_surfaces = sum(
            1
            for item in inventory
            if item.record_count and item.pii_scope == "masked_contact"
        )
        retention_actions = [
            item.recommendation
            for item in inventory
            if item.status != CheckStatus.ok
        ]
        status = CheckStatus.ok
        if any(item.status == CheckStatus.blocker for item in inventory):
            status = CheckStatus.blocker
        elif any(item.status == CheckStatus.warning for item in inventory):
            status = CheckStatus.warning
        return DataGovernanceDashboard(
            workspace_id=workspace_id,
            generated_at=_now(),
            status=status,
            summary=_data_governance_summary(status, total_records, raw_contact_surfaces),
            total_records=total_records,
            raw_contact_surfaces=raw_contact_surfaces,
            masked_contact_surfaces=masked_contact_surfaces,
            retention_actions=retention_actions[:8],
            deletion_controls=[
                "DELETE /reports/{report_id}/share 로 공개 리포트 공유를 해제합니다.",
                "완료 리포트 수신자 그룹은 unsubscribe 제외 정책으로 운영합니다.",
                "베타/요금제 연락은 contact_consent가 있는 요청만 저장합니다.",
                (
                    "보존 기간 초과 항목은 운영자가 workspace 단위 export 후 "
                    "삭제 작업 대상으로 분리합니다."
                ),
            ],
            inventory=inventory,
        )

    def beta_readiness_for_workspace(self, workspace_id: str) -> BetaReadinessDashboard:
        metrics = self.metrics_for_workspace(workspace_id)
        quality = self.quality_dashboard_for_workspace(workspace_id, limit=10)
        checks = [
            _readiness_check(
                area="activation",
                label="분석 실행",
                value=metrics.analysis_runs,
                warning_threshold=3,
                ok_threshold=10,
                metric=f"{metrics.analysis_runs}건",
                recommendation=(
                    "대표 데스크톱/노트북 요청을 최소 10건 이상 실행해 "
                    "결과 안정성을 확인하세요."
                ),
            ),
            _readiness_check(
                area="sharing",
                label="공유 리포트 확산",
                value=metrics.shared_reports,
                warning_threshold=1,
                ok_threshold=3,
                metric=f"{metrics.shared_reports}개 공유 / 조회 {metrics.public_share_views}회",
                recommendation="베타 사용자에게 공유 링크를 보내 실제 검토 흐름을 확인하세요.",
            ),
            _readiness_check(
                area="retention",
                label="가격 알림 연결",
                value=metrics.alert_subscriptions,
                warning_threshold=1,
                ok_threshold=3,
                metric=f"{metrics.alert_subscriptions}개 알림",
                recommendation="가격 대기 판정 사용자가 목표가 알림까지 연결되는지 확인하세요.",
            ),
            _readiness_check(
                area="feedback",
                label="피드백 신호",
                value=metrics.feedback_count,
                warning_threshold=3,
                ok_threshold=10,
                metric=(
                    f"{metrics.feedback_count}건 / 만족도 {metrics.average_satisfaction}점 / "
                    f"구매 의향 {round(metrics.purchase_intent_rate * 100)}%"
                ),
                recommendation="공개 전 실제 구매 예정자 피드백을 10건 이상 확보하세요.",
            ),
            _quality_readiness_check(quality),
            _readiness_check(
                area="lead",
                label="베타 리드",
                value=metrics.beta_leads,
                warning_threshold=3,
                ok_threshold=10,
                metric=f"{metrics.beta_leads}명",
                recommendation=(
                    "사용 목적별 베타 신청자를 모아 데스크톱/노트북 "
                    "시나리오를 분리 검증하세요."
                ),
            ),
        ]
        score = _launch_readiness_score(metrics, quality)
        return BetaReadinessDashboard(
            workspace_id=workspace_id,
            launch_readiness_score=score,
            readiness_label=_readiness_label(score),
            analysis_runs=metrics.analysis_runs,
            saved_reports=metrics.saved_reports,
            shared_reports=metrics.shared_reports,
            public_share_views=metrics.public_share_views,
            alert_subscriptions=metrics.alert_subscriptions,
            feedback_count=metrics.feedback_count,
            beta_leads=metrics.beta_leads,
            average_quality_score=metrics.average_quality_score,
            blocker_count=quality.blocker_count,
            average_satisfaction=metrics.average_satisfaction,
            purchase_intent_rate=metrics.purchase_intent_rate,
            conversion_ready_rate=metrics.conversion_ready_rate,
            checks=checks,
            next_actions=[
                check.recommendation
                for check in checks
                if check.status != CheckStatus.ok
            ][:4],
        )

    def launch_gate_for_workspace(self, workspace_id: str) -> LaunchGateDashboard:
        metrics = self.metrics_for_workspace(workspace_id)
        readiness = self.beta_readiness_for_workspace(workspace_id)
        regression = self.ops_regression_for_workspace(workspace_id, window_size=5)
        learning = self.learning_insights_for_workspace(workspace_id, limit=20)
        backlog = self.beta_backlog_action_summary_for_workspace(workspace_id, limit=200)
        integrations = self.integration_readiness_for_workspace(workspace_id)
        data_governance = self.data_governance_for_workspace(workspace_id)
        growth = self.growth_funnel_for_workspace(workspace_id, limit=10)
        checks = [
            _launch_gate_check(
                area="readiness",
                label="베타 출시 준비도",
                status=_launch_readiness_gate_status(readiness.launch_readiness_score),
                metric=f"{readiness.launch_readiness_score}점 · {readiness.readiness_label}",
                recommendation=readiness.next_actions[0]
                if readiness.next_actions
                else "준비도 기준을 유지하세요.",
            ),
            _launch_gate_check(
                area="regression",
                label="품질 회귀",
                status=regression.status,
                metric=(
                    f"최근 품질 {regression.recent.average_quality_score}점 / "
                    f"비용 변화 {round(regression.cost_delta_rate * 100)}%"
                ),
                recommendation=regression.next_actions[0]
                if regression.next_actions
                else "품질 회귀 신호를 계속 모니터링하세요.",
            ),
            _launch_gate_check(
                area="learning",
                label="제품별 학습 인사이트",
                status=learning.status,
                metric=f"{learning.insight_count}개 인사이트 · {learning.summary}",
                recommendation=learning.top_actions[0]
                if learning.top_actions
                else "구매 결과 표본을 계속 수집하세요.",
            ),
            _launch_gate_check(
                area="backlog",
                label="운영 백로그 SLA",
                status=_launch_backlog_gate_status(backlog),
                metric=(
                    f"전체 {backlog.total_count}건 / 지연 {backlog.overdue_count}건 / "
                    f"blocker {backlog.blocker_count}건"
                ),
                recommendation=backlog.next_actions[0]
                if backlog.next_actions
                else "백로그 SLA 상태를 유지하세요.",
            ),
            _launch_gate_check(
                area="conversion",
                label="구매 전환 신호",
                status=_launch_conversion_gate_status(metrics),
                metric=(
                    f"구매 결과 {metrics.purchase_outcomes}건 / "
                    f"전환 {round(metrics.purchase_conversion_rate * 100)}% / "
                    f"구매 의향 {round(metrics.purchase_intent_rate * 100)}%"
                ),
                recommendation=(
                    "피드백, 구매 의향, 실제 구매 결과를 더 모아 "
                    "공개 확대 판단의 표본을 보강하세요."
                ),
            ),
            _launch_gate_check(
                area="growth",
                label="제품 성장 퍼널",
                status=growth.status,
                metric=(
                    f"이벤트 {growth.total_events}건 / "
                    f"추천 클릭 {round(growth.activation_rate * 100)}% / "
                    f"공유 CTA {round(growth.share_rate * 100)}%"
                ),
                recommendation=(
                    growth.next_actions[0]
                    if growth.next_actions
                    else "추천 카드와 CTA 전환 추세를 유지하세요."
                ),
            ),
            _launch_gate_check(
                area="delivery",
                label="리포트 발송/알림 운영",
                status=_launch_delivery_gate_status(metrics),
                metric=(
                    f"완료 발송 {metrics.completion_report_deliveries}건 / "
                    f"알림 발송 성공 {metrics.sent_alert_deliveries}건 / "
                    f"채널 {metrics.alert_channels}개"
                ),
                recommendation=(
                    "완료 리포트 발송, 목표가 알림 채널, provider webhook 상태를 "
                    "실제 운영 흐름으로 검증하세요."
                ),
            ),
            _launch_gate_check(
                area="integration",
                label="외부 연동 준비도",
                status=integrations.status,
                metric=(
                    f"{integrations.readiness_score}점 / "
                    f"verified {integrations.verified_count}개 / "
                    f"blocker {integrations.blocker_count}개"
                ),
                recommendation=integrations.required_actions[0]
                if integrations.required_actions
                else "핵심 외부 연동의 credential, rate limit, 보존 정책을 유지하세요.",
            ),
            _launch_gate_check(
                area="data_governance",
                label="프라이버시/데이터 보존",
                status=data_governance.status,
                metric=(
                    f"데이터 {data_governance.total_records}건 / "
                    f"원문 연락처 표면 {data_governance.raw_contact_surfaces}개"
                ),
                recommendation=data_governance.retention_actions[0]
                if data_governance.retention_actions
                else "마스킹과 보존 정책 기준을 유지하세요.",
            ),
        ]
        status, decision = _launch_gate_status_and_decision(
            checks,
            readiness.launch_readiness_score,
        )
        required_actions = _launch_gate_required_actions(
            checks,
            readiness,
            regression,
            learning,
            backlog,
        )
        return LaunchGateDashboard(
            workspace_id=workspace_id,
            generated_at=_now(),
            decision=decision,
            status=status,
            launch_readiness_score=readiness.launch_readiness_score,
            readiness_label=readiness.readiness_label,
            summary=_launch_gate_summary(decision, checks, readiness.launch_readiness_score),
            required_actions=required_actions,
            checks=checks,
            metric_cards={
                "analysis_runs": metrics.analysis_runs,
                "shared_reports": metrics.shared_reports,
                "purchase_outcomes": metrics.purchase_outcomes,
                "purchase_conversion_rate": metrics.purchase_conversion_rate,
                "average_quality_score": metrics.average_quality_score,
                "open_backlog": backlog.open_count,
                "overdue_backlog": backlog.overdue_count,
                "learning_insights": learning.insight_count,
                "integration_score": integrations.readiness_score,
                "integration_blockers": integrations.blocker_count,
                "data_governance_status": data_governance.status.value,
                "raw_contact_surfaces": data_governance.raw_contact_surfaces,
                "growth_events": growth.total_events,
                "recommendation_click_rate": growth.activation_rate,
                "share_cta_rate": growth.share_rate,
                "subscription_cta_rate": growth.paid_intent_rate,
            },
        )

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    trace_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    category TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    budget_krw INTEGER,
                    final_pick_id TEXT,
                    top_model_name TEXT,
                    top_score REAL NOT NULL DEFAULT 0,
                    quality_score REAL NOT NULL DEFAULT 0,
                    estimated_cost_krw REAL NOT NULL DEFAULT 0,
                    warning_count INTEGER NOT NULL DEFAULT 0,
                    blocker_count INTEGER NOT NULL DEFAULT 0,
                    quality_audit_json TEXT NOT NULL DEFAULT '{}',
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS saved_reports (
                    report_id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    title TEXT NOT NULL,
                    owner_label TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT '',
                    final_pick_id TEXT,
                    top_model_name TEXT,
                    share_token TEXT UNIQUE,
                    shared_at TEXT,
                    share_views INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(trace_id) REFERENCES analysis_runs(trace_id)
                );

                CREATE TABLE IF NOT EXISTS report_advisor_answers (
                    answer_id TEXT PRIMARY KEY,
                    report_id TEXT NOT NULL,
                    trace_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    question TEXT NOT NULL,
                    context TEXT NOT NULL DEFAULT '',
                    selected_product_id TEXT,
                    selected_model_name TEXT,
                    buyer_stage TEXT NOT NULL DEFAULT 'pre_checkout',
                    answer TEXT NOT NULL,
                    status TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0,
                    grounded_evidence_json TEXT NOT NULL DEFAULT '[]',
                    cited_product_ids_json TEXT NOT NULL DEFAULT '[]',
                    next_actions_json TEXT NOT NULL DEFAULT '[]',
                    contact_masked TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(report_id) REFERENCES saved_reports(report_id),
                    FOREIGN KEY(trace_id) REFERENCES analysis_runs(trace_id)
                );

                CREATE TABLE IF NOT EXISTS checkout_reviews (
                    review_id TEXT PRIMARY KEY,
                    report_id TEXT NOT NULL,
                    trace_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    product_id TEXT,
                    model_name TEXT,
                    confirmed_price_krw INTEGER,
                    readiness_status TEXT NOT NULL,
                    readiness_score REAL NOT NULL DEFAULT 0,
                    checkout_blocked INTEGER NOT NULL DEFAULT 0,
                    missing_acknowledgements_json TEXT NOT NULL DEFAULT '[]',
                    seller_questions_json TEXT NOT NULL DEFAULT '[]',
                    seller_answers_json TEXT NOT NULL DEFAULT '{}',
                    items_json TEXT NOT NULL DEFAULT '[]',
                    final_recommendation TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(report_id) REFERENCES saved_reports(report_id),
                    FOREIGN KEY(trace_id) REFERENCES analysis_runs(trace_id)
                );

                CREATE TABLE IF NOT EXISTS purchase_outcomes (
                    outcome_id TEXT PRIMARY KEY,
                    report_id TEXT NOT NULL,
                    trace_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    product_id TEXT,
                    model_name TEXT,
                    checkout_review_id TEXT,
                    status TEXT NOT NULL,
                    final_paid_price_krw INTEGER,
                    expected_price_krw INTEGER,
                    price_delta_krw INTEGER,
                    source_channel TEXT NOT NULL DEFAULT 'manual',
                    reason TEXT NOT NULL DEFAULT '',
                    satisfaction INTEGER,
                    order_reference_masked TEXT NOT NULL DEFAULT '',
                    conversion_value_krw INTEGER NOT NULL DEFAULT 0,
                    learning_signal TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(report_id) REFERENCES saved_reports(report_id),
                    FOREIGN KEY(trace_id) REFERENCES analysis_runs(trace_id),
                    FOREIGN KEY(checkout_review_id) REFERENCES checkout_reviews(review_id)
                );

                CREATE TABLE IF NOT EXISTS purchase_links (
                    link_id TEXT PRIMARY KEY,
                    report_id TEXT NOT NULL,
                    trace_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    product_id TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    seller_name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    is_affiliate INTEGER NOT NULL DEFAULT 0,
                    affiliate_network TEXT NOT NULL DEFAULT '',
                    price_krw INTEGER,
                    shipping_fee_krw INTEGER NOT NULL DEFAULT 0,
                    coupon_krw INTEGER NOT NULL DEFAULT 0,
                    effective_price_krw INTEGER,
                    rank INTEGER NOT NULL DEFAULT 1,
                    active INTEGER NOT NULL DEFAULT 1,
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(report_id) REFERENCES saved_reports(report_id),
                    FOREIGN KEY(trace_id) REFERENCES analysis_runs(trace_id)
                );

                CREATE TABLE IF NOT EXISTS purchase_link_clicks (
                    click_id TEXT PRIMARY KEY,
                    link_id TEXT NOT NULL,
                    report_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    product_id TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'public_report',
                    referrer_host TEXT NOT NULL DEFAULT '',
                    user_agent_family TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(link_id) REFERENCES purchase_links(link_id)
                );

                CREATE TABLE IF NOT EXISTS alert_subscriptions (
                    subscription_id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    target_price_krw INTEGER NOT NULL,
                    current_price_krw INTEGER NOT NULL,
                    channels_json TEXT NOT NULL,
                    contact TEXT NOT NULL,
                    owner_label TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(trace_id) REFERENCES analysis_runs(trace_id)
                );

                CREATE TABLE IF NOT EXISTS source_review_queue (
                    review_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    source_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    reviewer TEXT,
                    note TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS source_monitors (
                    monitor_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    url TEXT NOT NULL,
                    category TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    expected_model TEXT NOT NULL DEFAULT '',
                    source_name TEXT NOT NULL DEFAULT 'source_monitor',
                    seller TEXT,
                    cadence_minutes INTEGER NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    html_snapshot TEXT NOT NULL DEFAULT '',
                    last_run_at TEXT,
                    last_status TEXT NOT NULL DEFAULT 'never_run',
                    last_source_id TEXT,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS source_refresh_runs (
                    run_id TEXT PRIMARY KEY,
                    monitor_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    status TEXT NOT NULL,
                    source_id TEXT,
                    review_id TEXT,
                    fetched_live INTEGER NOT NULL DEFAULT 0,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS source_provider_policies (
                    provider_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    provider_name TEXT NOT NULL,
                    host_pattern TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    live_fetch_allowed INTEGER NOT NULL DEFAULT 0,
                    robots_status TEXT NOT NULL DEFAULT 'pending',
                    terms_status TEXT NOT NULL DEFAULT 'pending',
                    credential_status TEXT NOT NULL DEFAULT 'not_connected',
                    rate_limit_per_hour INTEGER NOT NULL DEFAULT 30,
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS source_provider_fetch_log (
                    fetch_id TEXT PRIMARY KEY,
                    provider_id TEXT,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    url TEXT NOT NULL,
                    host TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS integration_providers (
                    integration_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    provider_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'mock',
                    credential_status TEXT NOT NULL DEFAULT 'not_connected',
                    rate_limit_per_hour INTEGER NOT NULL DEFAULT 0,
                    retention_days INTEGER NOT NULL DEFAULT 0,
                    endpoint TEXT NOT NULL DEFAULT '',
                    evidence TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_verified_at TEXT
                );

                CREATE TABLE IF NOT EXISTS alert_delivery_events (
                    event_id TEXT PRIMARY KEY,
                    subscription_id TEXT NOT NULL,
                    trace_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    target_price_krw INTEGER NOT NULL,
                    current_price_krw INTEGER NOT NULL,
                    delta_krw INTEGER NOT NULL,
                    channels_json TEXT NOT NULL,
                    contact_masked TEXT NOT NULL,
                    delivery_status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(subscription_id) REFERENCES alert_subscriptions(subscription_id)
                );

                CREATE TABLE IF NOT EXISTS alert_notification_channels (
                    channel_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    channel TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    target TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    retry_limit INTEGER NOT NULL DEFAULT 3,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(workspace_id, channel)
                );

                CREATE TABLE IF NOT EXISTS alert_delivery_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    subscription_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    channel TEXT NOT NULL,
                    contact_masked TEXT NOT NULL,
                    delivery_status TEXT NOT NULL,
                    provider_message TEXT NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    next_retry_at TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(event_id) REFERENCES alert_delivery_events(event_id)
                );

                CREATE TABLE IF NOT EXISTS completion_report_templates (
                    template_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    name TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    subject TEXT NOT NULL DEFAULT '',
                    body TEXT NOT NULL DEFAULT '',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(workspace_id, name)
                );

                CREATE TABLE IF NOT EXISTS completion_recipient_groups (
                    group_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    name TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    recipients_json TEXT NOT NULL DEFAULT '[]',
                    unsubscribed_json TEXT NOT NULL DEFAULT '[]',
                    unsubscribe_policy TEXT NOT NULL DEFAULT 'exclude_unsubscribed',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(workspace_id, name)
                );

                CREATE TABLE IF NOT EXISTS completion_report_batches (
                    batch_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    status TEXT NOT NULL,
                    template_id TEXT,
                    recipient_group_id TEXT,
                    target_count INTEGER NOT NULL DEFAULT 0,
                    selected_count INTEGER NOT NULL DEFAULT 0,
                    sent_count INTEGER NOT NULL DEFAULT 0,
                    failed_count INTEGER NOT NULL DEFAULT 0,
                    dry_run INTEGER NOT NULL DEFAULT 0,
                    note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS completion_report_deliveries (
                    delivery_id TEXT PRIMARY KEY,
                    batch_id TEXT NOT NULL,
                    report_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    channel TEXT NOT NULL,
                    target_masked TEXT NOT NULL DEFAULT '',
                    template_id TEXT,
                    recipient_group_id TEXT,
                    subject TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    provider_message TEXT NOT NULL DEFAULT '',
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    next_retry_at TEXT,
                    sent_at TEXT,
                    tracking_token TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(batch_id) REFERENCES completion_report_batches(batch_id),
                    FOREIGN KEY(report_id) REFERENCES saved_reports(report_id)
                );

                CREATE TABLE IF NOT EXISTS completion_delivery_engagement (
                    event_id TEXT PRIMARY KEY,
                    delivery_id TEXT NOT NULL,
                    batch_id TEXT NOT NULL,
                    report_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    event_type TEXT NOT NULL,
                    target_masked TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(delivery_id) REFERENCES completion_report_deliveries(delivery_id)
                );

                CREATE TABLE IF NOT EXISTS completion_delivery_provider_events (
                    provider_event_id TEXT PRIMARY KEY,
                    delivery_id TEXT NOT NULL,
                    batch_id TEXT NOT NULL,
                    report_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    provider_name TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    delivery_status TEXT NOT NULL,
                    provider_message TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(delivery_id) REFERENCES completion_report_deliveries(delivery_id)
                );

                CREATE TABLE IF NOT EXISTS trace_spans (
                    span_id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    sequence INTEGER NOT NULL,
                    step TEXT NOT NULL,
                    title TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    status TEXT NOT NULL,
                    evidence_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    UNIQUE(workspace_id, trace_id, sequence),
                    FOREIGN KEY(trace_id) REFERENCES analysis_runs(trace_id)
                );

                CREATE TABLE IF NOT EXISTS observability_exports (
                    export_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    trace_id TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    status TEXT NOT NULL,
                    span_count INTEGER NOT NULL DEFAULT 0,
                    quality_score REAL NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    provider_message TEXT NOT NULL DEFAULT '',
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    dispatched_at TEXT,
                    next_retry_at TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(trace_id) REFERENCES analysis_runs(trace_id)
                );

                CREATE TABLE IF NOT EXISTS user_feedback (
                    feedback_id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    rating INTEGER NOT NULL,
                    purchase_intent INTEGER NOT NULL,
                    selected_product_id TEXT,
                    reason TEXT NOT NULL DEFAULT '',
                    improvement_requests_json TEXT NOT NULL DEFAULT '[]',
                    contact_masked TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(trace_id) REFERENCES analysis_runs(trace_id)
                );

                CREATE TABLE IF NOT EXISTS beta_leads (
                    lead_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    email_masked TEXT NOT NULL,
                    persona TEXT NOT NULL,
                    use_case TEXT NOT NULL,
                    company_size TEXT NOT NULL,
                    contact_consent INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS waitlist_referrals (
                    referral_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    email_masked TEXT NOT NULL,
                    persona TEXT NOT NULL,
                    use_case TEXT NOT NULL DEFAULT '',
                    referral_code TEXT NOT NULL,
                    referred_by_code TEXT NOT NULL DEFAULT '',
                    referral_url TEXT NOT NULL,
                    contact_consent INTEGER NOT NULL DEFAULT 1,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS subscription_intents (
                    intent_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    email_masked TEXT NOT NULL,
                    plan_id TEXT NOT NULL,
                    plan_name TEXT NOT NULL,
                    billing_cycle TEXT NOT NULL,
                    monthly_price_krw INTEGER NOT NULL DEFAULT 0,
                    estimated_mrr_krw INTEGER NOT NULL DEFAULT 0,
                    persona TEXT NOT NULL,
                    use_case TEXT NOT NULL DEFAULT '',
                    team_size INTEGER NOT NULL DEFAULT 1,
                    max_budget_krw INTEGER,
                    feature_priorities_json TEXT NOT NULL DEFAULT '[]',
                    purchase_timing TEXT NOT NULL,
                    contact_consent INTEGER NOT NULL DEFAULT 1,
                    source TEXT NOT NULL,
                    readiness_status TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS growth_events (
                    event_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    event_type TEXT NOT NULL,
                    trace_id TEXT,
                    report_id TEXT,
                    product_id TEXT,
                    source TEXT NOT NULL DEFAULT 'web',
                    surface TEXT NOT NULL DEFAULT 'home',
                    label TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS launch_experiments (
                    experiment_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    name TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    audience TEXT NOT NULL,
                    hypothesis TEXT NOT NULL,
                    primary_metric TEXT NOT NULL,
                    target_surface TEXT NOT NULL,
                    category TEXT,
                    status TEXT NOT NULL,
                    variants_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS launch_experiment_events (
                    event_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    experiment_id TEXT NOT NULL,
                    variant_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    trace_id TEXT,
                    source TEXT NOT NULL DEFAULT 'web',
                    surface TEXT NOT NULL DEFAULT 'launch-experiment',
                    label TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(experiment_id) REFERENCES launch_experiments(experiment_id)
                );

                CREATE TABLE IF NOT EXISTS beta_cohorts (
                    cohort_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    name TEXT NOT NULL,
                    scenario TEXT NOT NULL,
                    category TEXT NOT NULL,
                    target_persona TEXT NOT NULL,
                    target_size INTEGER NOT NULL,
                    success_metric TEXT NOT NULL,
                    keywords_json TEXT NOT NULL DEFAULT '[]',
                    notes TEXT NOT NULL DEFAULT '',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS beta_backlog_actions (
                    backlog_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'demo',
                    status TEXT NOT NULL,
                    assignee TEXT NOT NULL DEFAULT '',
                    note TEXT NOT NULL DEFAULT '',
                    sla_due_at TEXT,
                    completed_at TEXT,
                    completion_summary TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(workspace_id, backlog_id)
                );

                CREATE INDEX IF NOT EXISTS idx_saved_reports_trace
                    ON saved_reports(trace_id);
                CREATE INDEX IF NOT EXISTS idx_report_advisor_workspace
                    ON report_advisor_answers(workspace_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_report_advisor_report
                    ON report_advisor_answers(report_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_checkout_reviews_workspace
                    ON checkout_reviews(workspace_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_checkout_reviews_report
                    ON checkout_reviews(report_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_purchase_outcomes_workspace
                    ON purchase_outcomes(workspace_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_purchase_outcomes_report
                    ON purchase_outcomes(report_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_purchase_outcomes_status
                    ON purchase_outcomes(workspace_id, status, created_at);
                CREATE INDEX IF NOT EXISTS idx_purchase_links_workspace
                    ON purchase_links(workspace_id, report_id, product_id);
                CREATE INDEX IF NOT EXISTS idx_purchase_link_clicks_link
                    ON purchase_link_clicks(link_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_purchase_link_clicks_workspace
                    ON purchase_link_clicks(workspace_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_alerts_trace
                    ON alert_subscriptions(trace_id);
                CREATE INDEX IF NOT EXISTS idx_source_review_status
                    ON source_review_queue(status);
                CREATE INDEX IF NOT EXISTS idx_source_monitors_workspace
                    ON source_monitors(workspace_id, active);
                CREATE INDEX IF NOT EXISTS idx_source_refresh_workspace
                    ON source_refresh_runs(workspace_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_source_provider_workspace
                    ON source_provider_policies(workspace_id, host_pattern);
                CREATE INDEX IF NOT EXISTS idx_source_provider_fetch_workspace
                    ON source_provider_fetch_log(workspace_id, provider_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_integration_providers_workspace
                    ON integration_providers(workspace_id, category, status);
                CREATE INDEX IF NOT EXISTS idx_alert_events_workspace
                    ON alert_delivery_events(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_alert_events_subscription
                    ON alert_delivery_events(subscription_id);
                CREATE INDEX IF NOT EXISTS idx_alert_channels_workspace
                    ON alert_notification_channels(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_alert_attempts_workspace
                    ON alert_delivery_attempts(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_alert_attempts_event
                    ON alert_delivery_attempts(event_id);
                CREATE INDEX IF NOT EXISTS idx_completion_templates_workspace
                    ON completion_report_templates(workspace_id, updated_at);
                CREATE INDEX IF NOT EXISTS idx_completion_groups_workspace
                    ON completion_recipient_groups(workspace_id, updated_at);
                CREATE INDEX IF NOT EXISTS idx_completion_batches_workspace
                    ON completion_report_batches(workspace_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_completion_deliveries_workspace
                    ON completion_report_deliveries(workspace_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_completion_deliveries_report
                    ON completion_report_deliveries(report_id);
                CREATE INDEX IF NOT EXISTS idx_completion_engagement_workspace
                    ON completion_delivery_engagement(workspace_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_completion_engagement_delivery
                    ON completion_delivery_engagement(delivery_id, event_type);
                CREATE INDEX IF NOT EXISTS idx_completion_provider_events_workspace
                    ON completion_delivery_provider_events(workspace_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_completion_provider_events_delivery
                    ON completion_delivery_provider_events(delivery_id, event_type);
                CREATE INDEX IF NOT EXISTS idx_trace_spans_workspace
                    ON trace_spans(workspace_id, trace_id);
                CREATE INDEX IF NOT EXISTS idx_observability_exports_workspace
                    ON observability_exports(workspace_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_observability_exports_status
                    ON observability_exports(workspace_id, status);
                CREATE INDEX IF NOT EXISTS idx_user_feedback_workspace
                    ON user_feedback(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_user_feedback_trace
                    ON user_feedback(trace_id);
                CREATE INDEX IF NOT EXISTS idx_beta_leads_workspace
                    ON beta_leads(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_waitlist_referrals_workspace
                    ON waitlist_referrals(workspace_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_waitlist_referrals_code
                    ON waitlist_referrals(workspace_id, referral_code);
                CREATE INDEX IF NOT EXISTS idx_waitlist_referrals_parent
                    ON waitlist_referrals(workspace_id, referred_by_code);
                CREATE INDEX IF NOT EXISTS idx_subscription_intents_workspace
                    ON subscription_intents(workspace_id, plan_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_launch_experiments_workspace
                    ON launch_experiments(workspace_id, updated_at);
                CREATE INDEX IF NOT EXISTS idx_launch_experiment_events_workspace
                    ON launch_experiment_events(workspace_id, experiment_id, variant_id);
                CREATE INDEX IF NOT EXISTS idx_beta_cohorts_workspace
                    ON beta_cohorts(workspace_id, active);
                CREATE INDEX IF NOT EXISTS idx_beta_backlog_actions_workspace
                    ON beta_backlog_actions(workspace_id, status);
                """
            )
            _ensure_column(conn, "analysis_runs", "workspace_id", "TEXT NOT NULL DEFAULT 'demo'")
            _ensure_column(conn, "analysis_runs", "quality_score", "REAL NOT NULL DEFAULT 0")
            _ensure_column(conn, "analysis_runs", "estimated_cost_krw", "REAL NOT NULL DEFAULT 0")
            _ensure_column(conn, "analysis_runs", "warning_count", "INTEGER NOT NULL DEFAULT 0")
            _ensure_column(conn, "analysis_runs", "blocker_count", "INTEGER NOT NULL DEFAULT 0")
            _ensure_column(
                conn,
                "analysis_runs",
                "quality_audit_json",
                "TEXT NOT NULL DEFAULT '{}'",
            )
            _ensure_column(
                conn,
                "observability_exports",
                "provider_message",
                "TEXT NOT NULL DEFAULT ''",
            )
            _ensure_column(
                conn,
                "observability_exports",
                "retry_count",
                "INTEGER NOT NULL DEFAULT 0",
            )
            _ensure_column(conn, "observability_exports", "dispatched_at", "TEXT")
            _ensure_column(conn, "observability_exports", "next_retry_at", "TEXT")
            _ensure_column(conn, "saved_reports", "workspace_id", "TEXT NOT NULL DEFAULT 'demo'")
            _ensure_column(conn, "saved_reports", "share_token", "TEXT")
            _ensure_column(conn, "saved_reports", "shared_at", "TEXT")
            _ensure_column(conn, "saved_reports", "share_views", "INTEGER NOT NULL DEFAULT 0")
            _ensure_column(conn, "completion_report_batches", "template_id", "TEXT")
            _ensure_column(conn, "completion_report_batches", "recipient_group_id", "TEXT")
            _ensure_column(
                conn,
                "completion_report_batches",
                "target_count",
                "INTEGER NOT NULL DEFAULT 0",
            )
            _ensure_column(conn, "completion_report_deliveries", "template_id", "TEXT")
            _ensure_column(conn, "completion_report_deliveries", "recipient_group_id", "TEXT")
            _ensure_column(
                conn,
                "completion_report_deliveries",
                "subject",
                "TEXT NOT NULL DEFAULT ''",
            )
            _ensure_column(
                conn,
                "completion_report_deliveries",
                "tracking_token",
                "TEXT NOT NULL DEFAULT ''",
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_completion_delivery_tracking_token
                    ON completion_report_deliveries(tracking_token);
                """
            )
            _ensure_column(
                conn,
                "alert_subscriptions",
                "workspace_id",
                "TEXT NOT NULL DEFAULT 'demo'",
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_saved_reports_workspace
                ON saved_reports(workspace_id)
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_reports_share_token
                ON saved_reports(share_token)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_alerts_workspace
                ON alert_subscriptions(workspace_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_alert_attempts_status
                ON alert_delivery_attempts(workspace_id, delivery_status)
                """
            )
            _ensure_column(conn, "beta_backlog_actions", "sla_due_at", "TEXT")
            _ensure_column(conn, "beta_backlog_actions", "completed_at", "TEXT")
            _ensure_column(
                conn,
                "beta_backlog_actions",
                "completion_summary",
                "TEXT NOT NULL DEFAULT ''",
            )

    def _select_completion_reports(
        self,
        workspace_id: str,
        *,
        report_ids: list[str],
        limit: int,
    ) -> list[SavedReportSummary]:
        with self._connect() as conn:
            if report_ids:
                unique_ids = list(dict.fromkeys(report_ids))
                placeholders = ", ".join("?" for _ in unique_ids)
                rows = conn.execute(
                    f"""
                    SELECT report_id, trace_id, workspace_id, title, owner_label,
                           final_pick_id, top_model_name, share_token, shared_at,
                           share_views, created_at, updated_at
                    FROM saved_reports
                    WHERE workspace_id = ?
                      AND report_id IN ({placeholders})
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (workspace_id, *unique_ids, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT report_id, trace_id, workspace_id, title, owner_label,
                           final_pick_id, top_model_name, share_token, shared_at,
                           share_views, created_at, updated_at
                    FROM saved_reports
                    WHERE workspace_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (workspace_id, limit),
                ).fetchall()
        return [_saved_report_summary_from_row(row) for row in rows]

    def _next_completion_retry_count(
        self,
        workspace_id: str,
        report_id: str,
        channel: str,
    ) -> int:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS retry_count
                FROM completion_report_deliveries
                WHERE workspace_id = ?
                  AND report_id = ?
                  AND channel = ?
                  AND status = 'failed'
                """,
                (workspace_id, report_id, channel),
            ).fetchone()
        return int(row["retry_count"] or 0) + 1

    def _completion_template(
        self,
        workspace_id: str,
        template_id: str | None,
    ) -> sqlite3.Row | None:
        if not template_id:
            return None
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT *
                FROM completion_report_templates
                WHERE workspace_id = ? AND template_id = ? AND enabled = 1
                """,
                (workspace_id, template_id),
            ).fetchone()

    def _completion_recipient_group(
        self,
        workspace_id: str,
        group_id: str | None,
    ) -> sqlite3.Row | None:
        if not group_id:
            return None
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT *
                FROM completion_recipient_groups
                WHERE workspace_id = ? AND group_id = ? AND enabled = 1
                """,
                (workspace_id, group_id),
            ).fetchone()

    def _queued_alert_events(
        self,
        workspace_id: str,
        *,
        event_ids: list[str],
        limit: int,
    ) -> list[AlertDeliveryEvent]:
        with self._connect() as conn:
            if event_ids:
                placeholders = ", ".join("?" for _ in event_ids)
                rows = conn.execute(
                    f"""
                    SELECT *
                    FROM alert_delivery_events
                    WHERE workspace_id = ?
                      AND event_id IN ({placeholders})
                      AND delivery_status IN ('queued', 'failed')
                    ORDER BY created_at ASC
                    LIMIT ?
                    """,
                    (workspace_id, *event_ids, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM alert_delivery_events
                    WHERE workspace_id = ?
                      AND delivery_status IN ('queued', 'failed')
                    ORDER BY created_at ASC
                    LIMIT ?
                    """,
                    (workspace_id, limit),
                ).fetchall()
        return [_alert_event_from_row(row) for row in rows]

    def _queued_observability_exports(
        self,
        workspace_id: str,
        *,
        export_ids: list[str],
        limit: int,
    ) -> list[ObservabilityExportRecord]:
        with self._connect() as conn:
            if export_ids:
                placeholders = ", ".join("?" for _ in export_ids)
                rows = conn.execute(
                    f"""
                    SELECT *
                    FROM observability_exports
                    WHERE workspace_id = ?
                      AND export_id IN ({placeholders})
                      AND status IN ('queued', 'failed')
                    ORDER BY created_at ASC
                    LIMIT ?
                    """,
                    (workspace_id, *export_ids, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM observability_exports
                    WHERE workspace_id = ?
                      AND status IN ('queued', 'failed')
                    ORDER BY created_at ASC
                    LIMIT ?
                    """,
                    (workspace_id, limit),
                ).fetchall()
        return [_observability_export_from_row(row) for row in rows]

    def _alert_channel_config_map(
        self,
        workspace_id: str,
    ) -> dict[str, sqlite3.Row]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM alert_notification_channels
                WHERE workspace_id = ?
                """,
                (workspace_id,),
            ).fetchall()
        return {row["channel"]: row for row in rows}

    def _next_attempt_number(
        self,
        conn: sqlite3.Connection,
        event_id: str,
        channel: str,
    ) -> int:
        row = conn.execute(
            """
            SELECT COUNT(*)
            FROM alert_delivery_attempts
            WHERE event_id = ? AND channel = ?
            """,
            (event_id, channel),
        ).fetchone()
        return int(row[0]) + 1

    def _insert_alert_attempt(
        self,
        conn: sqlite3.Connection,
        attempt: AlertDeliveryAttempt,
    ) -> None:
        conn.execute(
            """
            INSERT INTO alert_delivery_attempts (
                attempt_id, event_id, subscription_id, workspace_id, channel,
                contact_masked, delivery_status, provider_message, retry_count,
                next_retry_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt.attempt_id,
                attempt.event_id,
                attempt.subscription_id,
                attempt.workspace_id,
                attempt.channel,
                attempt.contact_masked,
                attempt.delivery_status,
                attempt.provider_message,
                attempt.retry_count,
                attempt.next_retry_at,
                attempt.created_at,
            ),
        )

    def _replace_trace_spans(
        self,
        conn: sqlite3.Connection,
        workspace_id: str,
        trace_id: str,
        events: list[TraceEvent],
    ) -> None:
        conn.execute(
            "DELETE FROM trace_spans WHERE workspace_id = ? AND trace_id = ?",
            (workspace_id, trace_id),
        )
        now = _now()
        for sequence, event in enumerate(events, start=1):
            conn.execute(
                """
                INSERT INTO trace_spans (
                    span_id, trace_id, workspace_id, sequence, step, title,
                    detail, status, evidence_count, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"span_{uuid4().hex[:12]}",
                    trace_id,
                    workspace_id,
                    sequence,
                    event.step.value,
                    event.title,
                    event.detail,
                    event.status.value,
                    event.evidence_count,
                    now,
                ),
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def _alert_from_row(row: sqlite3.Row) -> AlertSubscription:
    data = dict(row)
    return AlertSubscription(
        subscription_id=data["subscription_id"],
        trace_id=data["trace_id"],
        product_id=data["product_id"],
        workspace_id=data["workspace_id"],
        target_price_krw=data["target_price_krw"],
        current_price_krw=data["current_price_krw"],
        channels=json.loads(data["channels_json"]),
        contact_masked=_mask_contact(data["contact"]),
        owner_label=data["owner_label"],
        status=data["status"],
        created_at=data["created_at"],
    )


def _alert_event_from_row(row: sqlite3.Row) -> AlertDeliveryEvent:
    data = dict(row)
    return AlertDeliveryEvent(
        event_id=data["event_id"],
        subscription_id=data["subscription_id"],
        trace_id=data["trace_id"],
        product_id=data["product_id"],
        workspace_id=data["workspace_id"],
        target_price_krw=data["target_price_krw"],
        current_price_krw=data["current_price_krw"],
        delta_krw=data["delta_krw"],
        channels=json.loads(data["channels_json"]),
        contact_masked=data["contact_masked"],
        delivery_status=data["delivery_status"],
        message=data["message"],
        created_at=data["created_at"],
    )


def _alert_channel_from_row(row: sqlite3.Row) -> AlertNotificationChannel:
    data = dict(row)
    return AlertNotificationChannel(
        channel_id=data["channel_id"],
        workspace_id=data["workspace_id"],
        channel=data["channel"],
        display_name=data["display_name"],
        target_masked=_mask_target(data["target"]),
        enabled=bool(data["enabled"]),
        retry_limit=data["retry_limit"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _alert_attempt_from_row(row: sqlite3.Row) -> AlertDeliveryAttempt:
    data = dict(row)
    return AlertDeliveryAttempt(
        attempt_id=data["attempt_id"],
        event_id=data["event_id"],
        subscription_id=data["subscription_id"],
        workspace_id=data["workspace_id"],
        channel=data["channel"],
        contact_masked=data["contact_masked"],
        delivery_status=data["delivery_status"],
        provider_message=data["provider_message"],
        retry_count=data["retry_count"],
        next_retry_at=data["next_retry_at"],
        created_at=data["created_at"],
    )


def _trace_summary_from_row(row: sqlite3.Row) -> TraceRunSummary:
    data = dict(row)
    return TraceRunSummary(
        trace_id=data["trace_id"],
        workspace_id=data["workspace_id"],
        category=Category(data["category"]),
        purpose=data["purpose"],
        final_pick_id=data["final_pick_id"],
        top_model_name=data["top_model_name"],
        quality_score=data["quality_score"],
        warning_count=data["warning_count"],
        blocker_count=data["blocker_count"],
        span_count=data["span_count"],
        created_at=data["created_at"],
    )


def _trace_span_from_row(row: sqlite3.Row) -> TraceSpanRecord:
    data = dict(row)
    return TraceSpanRecord(
        span_id=data["span_id"],
        trace_id=data["trace_id"],
        workspace_id=data["workspace_id"],
        sequence=data["sequence"],
        step=AgentStep(data["step"]),
        title=data["title"],
        detail=data["detail"],
        status=CheckStatus(data["status"]),
        evidence_count=data["evidence_count"],
        created_at=data["created_at"],
    )


def _observability_export_from_row(row: sqlite3.Row) -> ObservabilityExportRecord:
    data = dict(row)
    return ObservabilityExportRecord(
        export_id=data["export_id"],
        workspace_id=data["workspace_id"],
        trace_id=data["trace_id"],
        destination=data["destination"],
        status=data["status"],
        span_count=data["span_count"],
        quality_score=data["quality_score"],
        payload=json.loads(data["payload_json"]),
        provider_message=data["provider_message"],
        retry_count=data["retry_count"],
        dispatched_at=data["dispatched_at"],
        next_retry_at=data["next_retry_at"],
        created_at=data["created_at"],
    )


def _saved_report_summary_from_row(row: sqlite3.Row) -> SavedReportSummary:
    data = dict(row)
    return SavedReportSummary(
        report_id=data["report_id"],
        trace_id=data["trace_id"],
        title=data["title"],
        workspace_id=data["workspace_id"],
        owner_label=data["owner_label"],
        final_pick_id=data["final_pick_id"],
        top_model_name=data["top_model_name"],
        share_token=data["share_token"],
        shared_at=data["shared_at"],
        share_views=data["share_views"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _decision_board_item_from_row(row: sqlite3.Row) -> PurchaseDecisionBoardItem:
    data = dict(row)
    response = AnalyzeResponse.model_validate_json(data["response_json"])
    report = response.report
    final_pick_id = report.final_pick_id
    top = _decision_board_top_recommendation(response)
    decision = report.purchase_decision
    deal = _decision_board_deal_window(response)
    checkout_blocked = bool(data["latest_checkout_blocked"] or 0)
    has_purchase_outcome = (data["purchase_outcome_count"] or 0) > 0
    has_purchase_links = (data["purchase_link_count"] or 0) > 0
    decision_label = decision.label if decision else "검수 후 구매"
    effective_price = top.price.effective_price_krw if top else None
    target_price = deal.target_price_krw if deal else None
    price_gap = (
        max(0, effective_price - target_price)
        if effective_price is not None and target_price is not None
        else None
    )
    status = _decision_board_item_status(
        decision_label=decision_label,
        checkout_blocked=checkout_blocked,
        price_gap_krw=price_gap,
    )
    next_steps = _decision_board_item_next_steps(
        decision_steps=decision.next_steps if decision else [],
        has_purchase_links=has_purchase_links,
        has_purchase_outcome=has_purchase_outcome,
        is_shared=data["share_token"] is not None,
        checkout_blocked=checkout_blocked,
        price_gap_krw=price_gap,
    )
    risk_flags = list(decision.risk_flags if decision else [])
    risk_flags.extend(report.verification_flags[:2])
    return PurchaseDecisionBoardItem(
        report_id=data["report_id"],
        trace_id=data["trace_id"],
        title=data["title"],
        owner_label=data["owner_label"],
        category=response.criteria.category,
        purpose=response.criteria.purpose,
        top_model_name=top.product.model_name if top else data["top_model_name"],
        final_pick_id=final_pick_id,
        decision_label=decision_label,
        board_status=status,
        recommended_action=_decision_board_recommended_action(
            decision_label=decision_label,
            execution_action=report.execution_plan.primary_action
            if report.execution_plan
            else "",
            checkout_blocked=checkout_blocked,
            has_purchase_outcome=has_purchase_outcome,
            has_purchase_links=has_purchase_links,
            price_gap_krw=price_gap,
        ),
        effective_price_krw=effective_price,
        target_price_krw=target_price,
        price_gap_krw=price_gap,
        confidence=decision.confidence if decision else 0,
        checkout_blocked=checkout_blocked,
        has_purchase_outcome=has_purchase_outcome,
        has_purchase_links=has_purchase_links,
        is_shared=data["share_token"] is not None,
        next_steps=next_steps,
        risk_flags=risk_flags[:5],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _decision_board_top_recommendation(response: AnalyzeResponse):
    final_pick_id = response.report.final_pick_id
    if final_pick_id:
        for recommendation in response.report.top_recommendations:
            if recommendation.product.id == final_pick_id:
                return recommendation
    return response.report.top_recommendations[0] if response.report.top_recommendations else None


def _decision_board_deal_window(response: AnalyzeResponse):
    final_pick_id = response.report.final_pick_id
    if final_pick_id:
        for deal in response.report.deal_windows:
            if deal.product_id == final_pick_id:
                return deal
    return response.report.deal_windows[0] if response.report.deal_windows else None


def _decision_board_item_status(
    *,
    decision_label: str,
    checkout_blocked: bool,
    price_gap_krw: int | None,
) -> CheckStatus:
    if checkout_blocked or "차단" in decision_label:
        return CheckStatus.blocker
    if "대기" in decision_label or "검수" in decision_label or (price_gap_krw or 0) > 0:
        return CheckStatus.warning
    return CheckStatus.ok


def _decision_board_item_next_steps(
    *,
    decision_steps: list[str],
    has_purchase_links: bool,
    has_purchase_outcome: bool,
    is_shared: bool,
    checkout_blocked: bool,
    price_gap_krw: int | None,
) -> list[str]:
    steps = list(decision_steps[:3])
    if checkout_blocked:
        steps.insert(0, "결제 전 검수의 차단 항목을 먼저 해소하세요.")
    if (price_gap_krw or 0) > 0:
        steps.append("목표가 알림을 유지하고 가격 재조회 후 결제하세요.")
    if not has_purchase_links:
        steps.append("공개 전 제휴 링크와 비제휴 구매 대안을 함께 등록하세요.")
    if not is_shared:
        steps.append("검토자에게 보낼 공개 공유 리포트를 생성하세요.")
    if not has_purchase_outcome:
        steps.append("구매, 지연, 이탈 중 하나로 결과를 닫아 학습 신호를 남기세요.")
    return _unique_non_empty(steps)[:6]


def _decision_board_recommended_action(
    *,
    decision_label: str,
    execution_action: str,
    checkout_blocked: bool,
    has_purchase_outcome: bool,
    has_purchase_links: bool,
    price_gap_krw: int | None,
) -> str:
    if checkout_blocked:
        return "결제 보류: 판매자 답변과 리스크 승인 누락을 먼저 처리하세요."
    if has_purchase_outcome:
        return "구매 결과 기록 완료: 학습 인사이트에서 유사 조건 랭킹 반영 여부를 확인하세요."
    if (price_gap_krw or 0) > 0 or "대기" in decision_label:
        return "가격 대기: 목표가 알림과 재조회 기준을 유지하세요."
    if not has_purchase_links:
        return "구매 링크 보강: 비제휴 대안까지 등록한 뒤 공유하세요."
    return execution_action or "결제 직전 가격, 옵션명, 반품 조건을 재확인하세요."


def _decision_board_status(items: list[PurchaseDecisionBoardItem]) -> CheckStatus:
    if any(item.board_status == CheckStatus.blocker for item in items):
        return CheckStatus.blocker
    if not items or any(item.board_status == CheckStatus.warning for item in items):
        return CheckStatus.warning
    return CheckStatus.ok


def _decision_board_summary(
    items: list[PurchaseDecisionBoardItem],
    status: CheckStatus,
) -> str:
    if not items:
        return "아직 비교할 저장 리포트가 없습니다. 분석을 실행하고 리포트를 저장하세요."
    ready = sum(1 for item in items if item.board_status == CheckStatus.ok)
    blocked = sum(1 for item in items if item.board_status == CheckStatus.blocker)
    waiting = sum(1 for item in items if item.board_status == CheckStatus.warning)
    if status == CheckStatus.blocker:
        return f"저장 리포트 {len(items)}건 중 {blocked}건은 결제 전 차단 항목 해소가 필요합니다."
    if status == CheckStatus.warning:
        return (
            f"저장 리포트 {len(items)}건 중 {waiting}건은 "
            "가격 대기 또는 검수 후 구매 상태입니다."
        )
    return f"저장 리포트 {len(items)}건 중 {ready}건은 결제 전 최종 확인 단계로 이동할 수 있습니다."


def _decision_board_next_actions(items: list[PurchaseDecisionBoardItem]) -> list[str]:
    if not items:
        return ["대표 구매 시나리오를 분석하고 리포트를 저장하세요."]
    actions: list[str] = []
    if any(item.checkout_blocked for item in items):
        actions.append("결제 전 검수 차단 리포트의 판매자 답변과 리스크 승인을 완료하세요.")
    if any((item.price_gap_krw or 0) > 0 for item in items):
        actions.append("가격 대기 리포트는 목표가 알림과 URL 모니터 refresh를 연결하세요.")
    if any(not item.has_purchase_links for item in items):
        actions.append("공개 공유 전 제휴 링크와 비제휴 구매 대안을 함께 등록하세요.")
    if any(not item.has_purchase_outcome for item in items):
        actions.append("구매, 지연, 이탈, 반품 결과를 기록해 추천 학습 루프를 닫으세요.")
    if not actions:
        actions.append("준비 완료 리포트를 공유하고 구매 결과 추적을 유지하세요.")
    return actions[:5]


def _unique_non_empty(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        normalized = item.strip()
        if normalized and normalized not in seen:
            unique.append(normalized)
            seen.add(normalized)
    return unique


def _report_advisor_answer_from_row(row: sqlite3.Row) -> ReportAdvisorAnswer:
    data = dict(row)
    return ReportAdvisorAnswer(
        answer_id=data["answer_id"],
        report_id=data["report_id"],
        trace_id=data["trace_id"],
        workspace_id=data["workspace_id"],
        question=data["question"],
        context=data["context"],
        selected_product_id=data["selected_product_id"],
        selected_model_name=data["selected_model_name"],
        buyer_stage=data["buyer_stage"],
        answer=data["answer"],
        status=CheckStatus(data["status"]),
        confidence=data["confidence"],
        grounded_evidence=json.loads(data["grounded_evidence_json"]),
        cited_product_ids=json.loads(data["cited_product_ids_json"]),
        next_actions=json.loads(data["next_actions_json"]),
        contact_masked=data["contact_masked"],
        created_at=data["created_at"],
    )


def _checkout_review_from_row(row: sqlite3.Row) -> CheckoutReview:
    data = dict(row)
    return CheckoutReview(
        review_id=data["review_id"],
        report_id=data["report_id"],
        trace_id=data["trace_id"],
        workspace_id=data["workspace_id"],
        product_id=data["product_id"],
        model_name=data["model_name"],
        confirmed_price_krw=data["confirmed_price_krw"],
        readiness_status=CheckStatus(data["readiness_status"]),
        readiness_score=data["readiness_score"],
        checkout_blocked=bool(data["checkout_blocked"]),
        missing_acknowledgements=json.loads(data["missing_acknowledgements_json"]),
        seller_questions=json.loads(data["seller_questions_json"]),
        seller_answers=json.loads(data["seller_answers_json"]),
        items=[
            CheckoutReviewItem.model_validate(item)
            for item in json.loads(data["items_json"])
        ],
        final_recommendation=data["final_recommendation"],
        notes=data["notes"],
        created_at=data["created_at"],
    )


def _purchase_outcome_from_row(row: sqlite3.Row) -> PurchaseOutcome:
    data = dict(row)
    return PurchaseOutcome(
        outcome_id=data["outcome_id"],
        report_id=data["report_id"],
        trace_id=data["trace_id"],
        workspace_id=data["workspace_id"],
        product_id=data["product_id"],
        model_name=data["model_name"],
        checkout_review_id=data["checkout_review_id"],
        status=PurchaseOutcomeStatus(data["status"]),
        final_paid_price_krw=data["final_paid_price_krw"],
        expected_price_krw=data["expected_price_krw"],
        price_delta_krw=data["price_delta_krw"],
        source_channel=data["source_channel"],
        reason=data["reason"],
        satisfaction=data["satisfaction"],
        order_reference_masked=data["order_reference_masked"],
        conversion_value_krw=data["conversion_value_krw"],
        learning_signal=data["learning_signal"],
        notes=data["notes"],
        created_at=data["created_at"],
    )


def _purchase_link_from_row(row: sqlite3.Row) -> PurchaseLink:
    data = dict(row)
    is_affiliate = bool(data["is_affiliate"])
    disclosure = (
        "제휴 링크입니다. 추천 순위는 목적 적합도, 실구매가, 호환성, 리뷰 신뢰도로 계산했습니다."
        if is_affiliate
        else "비제휴 구매 대안입니다."
    )
    return PurchaseLink(
        link_id=data["link_id"],
        report_id=data["report_id"],
        trace_id=data["trace_id"],
        workspace_id=data["workspace_id"],
        product_id=data["product_id"],
        model_name=data["model_name"],
        seller_name=data["seller_name"],
        url=data["url"],
        is_affiliate=is_affiliate,
        affiliate_network=data["affiliate_network"],
        price_krw=data["price_krw"],
        shipping_fee_krw=data["shipping_fee_krw"],
        coupon_krw=data["coupon_krw"],
        effective_price_krw=data["effective_price_krw"],
        rank=data["rank"],
        active=bool(data["active"]),
        disclosure=disclosure,
        policy_warnings=[],
        click_path=f"/buy/{data['link_id']}",
        click_count=data["click_count"] if "click_count" in data else 0,
        notes=data["notes"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _build_purchase_link(
    report: SavedReportDetail,
    request: PurchaseLinkRequest,
) -> PurchaseLink | None:
    purchase = report.response.report
    product_id = request.product_id or purchase.final_pick_id
    recommendation = next(
        (
            item
            for item in purchase.top_recommendations
            if item.product.id == product_id
        ),
        None,
    )
    if recommendation is None:
        return None
    price = request.price_krw
    effective_price = (
        price + request.shipping_fee_krw - request.coupon_krw
        if price is not None
        else None
    )
    now = _now()
    link_id = f"plink_{uuid4().hex[:12]}"
    disclosure = (
        "제휴 링크입니다. 추천 순위는 목적 적합도, 실구매가, 호환성, 리뷰 신뢰도로 계산했습니다."
        if request.is_affiliate
        else "비제휴 구매 대안입니다."
    )
    return PurchaseLink(
        link_id=link_id,
        report_id=report.report_id,
        trace_id=report.trace_id,
        workspace_id=report.workspace_id,
        product_id=recommendation.product.id,
        model_name=recommendation.product.model_name,
        seller_name=request.seller_name.strip(),
        url=request.url.strip(),
        is_affiliate=request.is_affiliate,
        affiliate_network=request.affiliate_network.strip(),
        price_krw=price,
        shipping_fee_krw=request.shipping_fee_krw,
        coupon_krw=request.coupon_krw,
        effective_price_krw=effective_price,
        rank=request.rank,
        active=request.active,
        disclosure=disclosure,
        policy_warnings=[],
        click_path=f"/buy/{link_id}",
        notes=request.notes.strip(),
        created_at=now,
        updated_at=now,
    )


def _purchase_link_governance(
    workspace_id: str,
    report_id: str,
    links: list[PurchaseLink],
) -> PurchaseLinkGovernance:
    active_links = [link for link in links if link.active]
    affiliate_count = sum(1 for link in active_links if link.is_affiliate)
    non_affiliate_count = sum(1 for link in active_links if not link.is_affiliate)
    click_count = sum(link.click_count for link in links)
    required_actions: list[str] = []
    status = CheckStatus.ok
    if affiliate_count and non_affiliate_count == 0:
        status = CheckStatus.blocker
        required_actions.append("제휴 링크 공개 전 비제휴 구매 대안을 최소 1개 이상 추가하세요.")
    elif any(link.status != CheckStatus.ok for link in links):
        status = CheckStatus.warning
        required_actions.append("후보별 제휴 링크와 비제휴 링크의 균형을 맞추세요.")
    if not active_links:
        status = CheckStatus.warning
        required_actions.append("공개 리포트에서 사용자가 확인할 구매 링크를 등록하세요.")
    summary = (
        f"활성 구매 링크 {len(active_links)}개, 제휴 {affiliate_count}개, "
        f"비제휴 {non_affiliate_count}개, 클릭 {click_count}회입니다."
    )
    return PurchaseLinkGovernance(
        workspace_id=workspace_id,
        report_id=report_id,
        status=status,
        affiliate_link_count=affiliate_count,
        non_affiliate_link_count=non_affiliate_count,
        active_link_count=len(active_links),
        click_count=click_count,
        summary=summary,
        required_actions=_dedupe_strings(required_actions),
        links=links,
    )


def _build_purchase_outcome(
    report: SavedReportDetail,
    request: PurchaseOutcomeRequest,
) -> PurchaseOutcome | None:
    purchase = report.response.report
    product_id = request.product_id or purchase.final_pick_id
    recommendation = next(
        (
            item
            for item in purchase.top_recommendations
            if item.product.id == product_id
        ),
        None,
    )
    if recommendation is None:
        return None
    expected_price = recommendation.price.effective_price_krw
    final_price = request.final_paid_price_krw
    price_delta = (
        final_price - expected_price
        if final_price is not None and expected_price is not None
        else None
    )
    conversion_value = (
        final_price
        if request.status == PurchaseOutcomeStatus.purchased and final_price is not None
        else 0
    )
    return PurchaseOutcome(
        outcome_id=f"outcome_{uuid4().hex[:12]}",
        report_id=report.report_id,
        trace_id=report.trace_id,
        workspace_id=report.workspace_id,
        product_id=recommendation.product.id,
        model_name=recommendation.product.model_name,
        checkout_review_id=request.checkout_review_id,
        status=request.status,
        final_paid_price_krw=final_price,
        expected_price_krw=expected_price,
        price_delta_krw=price_delta,
        source_channel=request.source_channel.strip() or "manual",
        reason=request.reason,
        satisfaction=request.satisfaction,
        order_reference_masked=_mask_order_reference(request.order_reference),
        conversion_value_krw=conversion_value,
        learning_signal=_purchase_learning_signal(request, price_delta),
        notes=request.notes,
        created_at=_now(),
    )


def _purchase_learning_signal(
    request: PurchaseOutcomeRequest,
    price_delta: int | None,
) -> str:
    if request.status == PurchaseOutcomeStatus.purchased:
        if price_delta is not None and price_delta > 50_000:
            return (
                "구매는 완료됐지만 최종가가 리포트 예상가보다 높아 "
                "가격 신선도 개선이 필요합니다."
            )
        if request.satisfaction is not None and request.satisfaction <= 3:
            return "구매는 완료됐지만 만족도가 낮아 추천 근거와 사후 기대값 설명을 점검해야 합니다."
        return "추천이 실제 구매로 전환됐습니다. 유사 조건 추천 랭킹의 긍정 신호입니다."
    if request.status == PurchaseOutcomeStatus.abandoned:
        return (
            request.reason.strip()
            or "사용자가 구매를 포기했습니다. 가격, 신뢰, 옵션 불확실성 원인을 확인해야 합니다."
        )
    if request.status == PurchaseOutcomeStatus.delayed:
        return (
            request.reason.strip()
            or "사용자가 구매를 연기했습니다. 가격 알림과 재검토 리마인더 연결이 필요합니다."
        )
    return (
        request.reason.strip()
        or "구매 후 반품/취소가 발생했습니다. 호환성, 배송, 기대 성능 차이를 회귀 분석해야 합니다."
    )


def _build_report_advisor_answer(
    report: SavedReportDetail,
    request: ReportAdvisorQuestionRequest,
) -> ReportAdvisorAnswer:
    purchase = report.response.report
    question = request.question.strip()
    context = request.context.strip()
    selected = _advisor_selected_recommendation(report, request.selected_product_id)
    final_pick = _advisor_selected_recommendation(report, purchase.final_pick_id)
    top = selected or final_pick or (
        purchase.top_recommendations[0] if purchase.top_recommendations else None
    )
    if top is None:
        return ReportAdvisorAnswer(
            answer_id=f"advisor_{uuid4().hex[:12]}",
            report_id=report.report_id,
            trace_id=report.trace_id,
            workspace_id=report.workspace_id,
            question=question,
            context=context,
            selected_product_id=request.selected_product_id,
            buyer_stage=request.buyer_stage,
            answer="저장 리포트에 추천 후보가 없어 추가 상담 답변을 만들 수 없습니다.",
            status=CheckStatus.blocker,
            confidence=0,
            grounded_evidence=[],
            cited_product_ids=[],
            next_actions=["분석을 다시 실행해 추천 후보가 포함된 리포트를 저장하세요."],
            contact_masked=_mask_contact(request.contact) if request.contact else "",
            created_at=_now(),
        )

    topic = _advisor_question_topic(question)
    evidence = _advisor_evidence_for_topic(purchase, top.product.id, topic)
    next_actions = _advisor_next_actions_for_topic(purchase, top.product.id, topic)
    status = _advisor_status_for_topic(purchase, top.product.id, topic)
    answer = _advisor_answer_text(purchase, top, topic, question)
    cited_ids = _dedupe_nonempty(
        [
            top.product.id,
            *[
                item.product.id
                for item in purchase.top_recommendations[:3]
                if topic == "compare"
            ],
        ]
    )
    confidence = 88.0
    if status == CheckStatus.warning:
        confidence = 78.0
    if status == CheckStatus.blocker:
        confidence = 62.0

    return ReportAdvisorAnswer(
        answer_id=f"advisor_{uuid4().hex[:12]}",
        report_id=report.report_id,
        trace_id=report.trace_id,
        workspace_id=report.workspace_id,
        question=question,
        context=context,
        selected_product_id=top.product.id,
        selected_model_name=top.product.model_name,
        buyer_stage=request.buyer_stage.strip() or "pre_checkout",
        answer=answer,
        status=status,
        confidence=confidence,
        grounded_evidence=evidence,
        cited_product_ids=cited_ids,
        next_actions=next_actions,
        contact_masked=_mask_contact(request.contact) if request.contact else "",
        created_at=_now(),
    )


def _advisor_selected_recommendation(
    report: SavedReportDetail,
    product_id: str | None,
):
    if not product_id:
        return None
    return next(
        (
            item
            for item in report.response.report.top_recommendations
            if item.product.id == product_id
        ),
        None,
    )


def _advisor_question_topic(question: str) -> str:
    normalized = question.lower()
    if any(word in normalized for word in ["가격", "할인", "기다", "언제", "목표가", "타이밍"]):
        return "price"
    if any(
        word in normalized
        for word in ["호환", "파워", "케이스", "램", "ram", "업그레이드", "소켓"]
    ):
        return "compatibility"
    if any(word in normalized for word in ["리스크", "후기", "리뷰", "발열", "소음", "as", "불만"]):
        return "risk"
    if any(word in normalized for word in ["비교", "대안", "1순위", "2순위", "차이", "더 나"]):
        return "compare"
    if any(word in normalized for word in ["결제", "구매", "주문", "판매자", "옵션", "체크"]):
        return "checkout"
    return "summary"


def _advisor_evidence_for_topic(purchase, product_id: str, topic: str) -> list[str]:
    recommendation = next(
        (item for item in purchase.top_recommendations if item.product.id == product_id),
        None,
    )
    deal = next((item for item in purchase.deal_windows if item.product_id == product_id), None)
    evidence_pack = next(
        (item for item in purchase.evidence_packs if item.product_id == product_id),
        None,
    )
    option_audit = next(
        (item for item in purchase.option_audits if item.product_id == product_id),
        None,
    )
    evidence: list[str] = []
    if recommendation:
        evidence.append(
            f"{recommendation.product.model_name}: 총점 {recommendation.score.total_score}점, "
            f"실구매가 {recommendation.price.effective_price_krw:,}원"
        )
    if topic == "price" and deal:
        evidence.append(
            f"현재가 {deal.current_price_krw:,}원, 목표가 {deal.target_price_krw:,}원, "
            f"적정가 밴드 {deal.fair_price_band_krw}"
        )
        evidence.append(f"가격 판단: {deal.wait_reason}")
    if topic == "compatibility":
        checks = [
            item
            for item in purchase.compatibility_checks
            if item.product_id == product_id
        ][:4]
        evidence.extend(f"{item.component}: {item.message}" for item in checks)
    if topic == "risk":
        if evidence_pack:
            evidence.append(evidence_pack.review_evidence)
            evidence.append(evidence_pack.trust_summary)
        if purchase.purchase_decision and purchase.purchase_decision.risk_flags:
            evidence.extend(purchase.purchase_decision.risk_flags[:3])
    if topic == "compare":
        evidence.extend(
            f"TOP {item.rank}: {item.product.model_name} / {item.price.effective_price_krw:,}원 / "
            f"{item.score.total_score}점"
            for item in purchase.top_recommendations[:3]
        )
    if topic == "checkout" and option_audit:
        evidence.extend(
            f"{item.field}: {item.expected_value} / {item.verification_hint}"
            for item in option_audit.critical_items[:3]
        )
        evidence.extend(option_audit.mismatch_risks[:3])
    if topic == "summary" and purchase.purchase_decision:
        evidence.append(
            f"{purchase.purchase_decision.label}: {purchase.purchase_decision.reason}"
        )
    return _dedupe_nonempty(evidence)[:8]


def _advisor_next_actions_for_topic(purchase, product_id: str, topic: str) -> list[str]:
    deal = next((item for item in purchase.deal_windows if item.product_id == product_id), None)
    option_audit = next(
        (item for item in purchase.option_audits if item.product_id == product_id),
        None,
    )
    if topic == "price":
        actions = [deal.buy_trigger] if deal else []
        if deal and deal.current_price_krw > deal.target_price_krw:
            actions.append("목표가 알림을 걸고 같은 성능대 대안 후보를 다시 비교하세요.")
        return _dedupe_nonempty(actions) or [
            "결제 직전 판매 페이지 가격과 배송비를 다시 확인하세요."
        ]
    if topic == "compatibility":
        return [
            "보유 모니터 해상도와 주사율을 기준으로 GPU가 과하거나 부족하지 않은지 확인하세요.",
            "케이스, 파워, 메인보드, RAM 규격을 최종 판매 옵션명과 대조하세요.",
        ]
    if topic == "risk":
        return [
            "반복 불만과 AS/반품 조건을 판매 페이지에서 다시 확인하세요.",
            "리스크가 마음에 걸리면 안전 우선 대안 시나리오를 우선 검토하세요.",
        ]
    if topic == "compare":
        return [
            "1순위와 2순위의 가격 차이를 성능/안정성 점수 차이와 함께 비교하세요.",
            "예산을 10% 줄였을 때도 선택이 유지되는지 스트레스 테스트 결과를 확인하세요.",
        ]
    if topic == "checkout":
        questions = purchase.execution_plan.seller_questions if purchase.execution_plan else []
        actions = list(questions[:3])
        if option_audit:
            actions.extend(item.verification_hint for item in option_audit.critical_items[:3])
        return _dedupe_nonempty(actions) or [
            "주문 옵션명, 최종 결제 금액, 반품 조건을 캡처해 보관하세요."
        ]
    if purchase.purchase_decision:
        return purchase.purchase_decision.next_steps[:4]
    return ["추천 리포트의 TOP 3와 제외 후보를 다시 확인하세요."]


def _advisor_status_for_topic(purchase, product_id: str, topic: str) -> CheckStatus:
    deal = next((item for item in purchase.deal_windows if item.product_id == product_id), None)
    option_audit = next(
        (item for item in purchase.option_audits if item.product_id == product_id),
        None,
    )
    if topic == "price" and deal:
        return deal.status
    if topic == "checkout" and option_audit and option_audit.purchase_blockers:
        return CheckStatus.blocker
    if topic == "risk" and purchase.purchase_decision and purchase.purchase_decision.risk_flags:
        return CheckStatus.warning
    if topic == "compatibility":
        checks = [
            item.status
            for item in purchase.compatibility_checks
            if item.product_id == product_id
        ]
        if CheckStatus.blocker in checks:
            return CheckStatus.blocker
        if CheckStatus.warning in checks:
            return CheckStatus.warning
    return CheckStatus.ok


def _advisor_answer_text(purchase, recommendation, topic: str, question: str) -> str:
    model_name = recommendation.product.model_name
    price = recommendation.price.effective_price_krw
    decision_label = (
        purchase.purchase_decision.label
        if purchase.purchase_decision
        else "추가 확인 필요"
    )
    if topic == "price":
        deal = next(
            (
                item
                for item in purchase.deal_windows
                if item.product_id == recommendation.product.id
            ),
            None,
        )
        if deal and deal.current_price_krw > deal.target_price_krw:
            return (
                f"{model_name}은 현재 {deal.current_price_krw:,}원으로 목표가 "
                f"{deal.target_price_krw:,}원보다 높습니다. 지금 당장 필요한 상황이 아니라면 "
                f"가격 알림을 걸고 {deal.buy_trigger} 조건을 기다리는 쪽이 유리합니다."
            )
        return (
            f"{model_name}은 현재 리포트 기준 실구매가 {price:,}원입니다. "
            "목표가와 큰 차이가 없거나 구매 트리거를 충족하면 결제 전 검수 후 진행할 수 있습니다."
        )
    if topic == "compatibility":
        return (
            f"{model_name}은 리포트의 호환성 검수 기준으로 목적 적합도와 구성 균형을 통과했습니다. "
            "다만 최종 판매 옵션명에서 RAM, SSD, 파워, 케이스/노트북 세부 옵션이 "
            "리포트와 같은지 확인해야 합니다."
        )
    if topic == "risk":
        return (
            f"{model_name}의 핵심 리스크는 리뷰 반복 불만, 출처 신뢰도, 옵션 불일치 가능성입니다. "
            "확정 표현이 아니라 리포트 근거에 묶인 위험 신호로 보고, "
            "판매자 확인과 반품 조건 확인 후 결정하세요."
        )
    if topic == "compare":
        runner_up = (
            purchase.top_recommendations[1]
            if len(purchase.top_recommendations) > 1
            else None
        )
        if runner_up:
            return (
                f"1순위 {model_name}은 {price:,}원, "
                f"2순위 {runner_up.product.model_name}은 "
                f"{runner_up.price.effective_price_krw:,}원입니다. "
                "점수 차이가 작고 가격 차이가 크면 대안 시나리오를, "
                "점수 차이가 크면 1순위를 유지하는 판단이 맞습니다."
            )
        return (
            f"{model_name}이 현재 리포트의 최상위 후보입니다. "
            "대안 후보가 부족하면 조건을 바꿔 재분석하세요."
        )
    if topic == "checkout":
        return (
            f"{model_name}을 결제하려면 주문 옵션명, 최종 결제 금액, 배송비/쿠폰, 판매자 답변을 "
            "리포트와 대조해야 합니다. 리스크 승인 누락이 있으면 결제 보류로 두는 것이 맞습니다."
        )
    return (
        f"질문 '{question}'에 대한 리포트 기반 답변입니다. 현재 판정은 '{decision_label}'이고, "
        f"기준 후보는 {model_name}입니다. 리포트에 없는 스펙이나 가격은 단정하지 않고 "
        "결제 직전 재확인이 필요합니다."
    )


def _build_checkout_review(
    report: SavedReportDetail,
    request: CheckoutReviewRequest,
) -> CheckoutReview | None:
    purchase = report.response.report
    product_id = request.product_id or purchase.final_pick_id
    recommendation = next(
        (
            item
            for item in purchase.top_recommendations
            if item.product.id == product_id
        ),
        None,
    )
    if recommendation is None:
        return None
    product_id = recommendation.product.id
    model_name = recommendation.product.model_name
    current_price = recommendation.price.effective_price_krw

    option_audit = next(
        (item for item in purchase.option_audits if item.product_id == product_id),
        None,
    )
    deal_window = next(
        (item for item in purchase.deal_windows if item.product_id == product_id),
        None,
    )
    risk_candidates = [
        *(purchase.purchase_decision.risk_flags if purchase.purchase_decision else []),
        *(option_audit.purchase_blockers if option_audit else []),
        *(option_audit.mismatch_risks if option_audit else []),
    ]
    if deal_window and deal_window.status != CheckStatus.ok:
        risk_candidates.append(deal_window.wait_reason)
    required_acknowledgements = _dedupe_nonempty(risk_candidates)
    acknowledged = set(_dedupe_nonempty(request.acknowledged_risks))
    missing_acknowledgements = [
        item for item in required_acknowledgements if item not in acknowledged
    ]

    seller_questions = (
        purchase.execution_plan.seller_questions
        if purchase.execution_plan
        else []
    )
    answered_questions = {
        question
        for question, answer in request.seller_answers.items()
        if question.strip() and answer.strip()
    }
    missing_seller_questions = [
        question for question in seller_questions if question not in answered_questions
    ]

    items = [
        _checkout_price_item(
            request.confirmed_price_krw,
            current_price,
            report.response.criteria.budget_krw,
        ),
        _checkout_option_item(option_audit),
        _checkout_seller_item(seller_questions, missing_seller_questions),
        _checkout_source_item(purchase.source_trust),
        _checkout_ack_item(missing_acknowledgements),
    ]
    blocker_count = sum(item.status == CheckStatus.blocker for item in items)
    warning_count = sum(item.status == CheckStatus.warning for item in items)
    readiness_score = max(
        0,
        100 - blocker_count * 32 - warning_count * 12 - len(missing_acknowledgements) * 8,
    )
    if blocker_count:
        readiness_status = CheckStatus.blocker
        final_recommendation = (
            "결제를 보류하세요. 누락된 리스크 승인 또는 필수 검수 항목이 있습니다."
        )
    elif warning_count:
        readiness_status = CheckStatus.warning
        final_recommendation = (
            "결제 전 판매자 답변과 가격을 한 번 더 확인하면 진행 가능합니다."
        )
    else:
        readiness_status = CheckStatus.ok
        final_recommendation = (
            "결제 진행 가능 상태입니다. 최종 주문 화면의 금액과 옵션명을 보존하세요."
        )

    return CheckoutReview(
        review_id=f"checkout_{uuid4().hex[:12]}",
        report_id=report.report_id,
        trace_id=report.trace_id,
        workspace_id=report.workspace_id,
        product_id=product_id,
        model_name=model_name,
        confirmed_price_krw=request.confirmed_price_krw,
        readiness_status=readiness_status,
        readiness_score=round(float(readiness_score), 1),
        checkout_blocked=readiness_status == CheckStatus.blocker,
        missing_acknowledgements=missing_acknowledgements,
        seller_questions=seller_questions,
        seller_answers={
            question: answer
            for question, answer in request.seller_answers.items()
            if question.strip() and answer.strip()
        },
        items=items,
        final_recommendation=final_recommendation,
        notes=request.notes,
        created_at=_now(),
    )


def _checkout_price_item(
    confirmed_price: int | None,
    current_price: int,
    budget: int | None,
) -> CheckoutReviewItem:
    if confirmed_price is None:
        return CheckoutReviewItem(
            item_id="price_confirmation",
            label="최종 결제 금액 확인",
            status=CheckStatus.warning,
            evidence="최종 주문 화면의 배송비, 조립비, 카드 할인 반영 금액이 입력되지 않았습니다.",
        )
    tolerance = max(50_000, int(current_price * 0.03)) if current_price else 50_000
    if budget is not None and confirmed_price > budget:
        return CheckoutReviewItem(
            item_id="price_confirmation",
            label="최종 결제 금액 확인",
            status=CheckStatus.blocker,
            evidence=f"확인 금액 {confirmed_price:,}원이 예산 {budget:,}원을 초과합니다.",
        )
    if current_price and confirmed_price > current_price + tolerance:
        return CheckoutReviewItem(
            item_id="price_confirmation",
            label="최종 결제 금액 확인",
            status=CheckStatus.warning,
            evidence=(
                f"확인 금액 {confirmed_price:,}원이 리포트 실구매가 "
                f"{current_price:,}원보다 높습니다."
            ),
        )
    return CheckoutReviewItem(
        item_id="price_confirmation",
        label="최종 결제 금액 확인",
        status=CheckStatus.ok,
        evidence=f"확인 금액 {confirmed_price:,}원이 리포트 가격 범위와 맞습니다.",
    )


def _checkout_option_item(audit) -> CheckoutReviewItem:
    if audit is None:
        return CheckoutReviewItem(
            item_id="option_audit",
            label="옵션/사양 검수",
            status=CheckStatus.warning,
            evidence="선택 후보의 옵션 검수표를 찾지 못했습니다.",
        )
    if audit.purchase_blockers:
        return CheckoutReviewItem(
            item_id="option_audit",
            label="옵션/사양 검수",
            status=CheckStatus.blocker,
            evidence=" / ".join(audit.purchase_blockers),
        )
    warning_items = [
        item for item in audit.critical_items if item.status != CheckStatus.ok
    ]
    if warning_items or audit.mismatch_risks:
        return CheckoutReviewItem(
            item_id="option_audit",
            label="옵션/사양 검수",
            status=CheckStatus.warning,
            evidence=(
                " / ".join(audit.mismatch_risks[:2])
                or f"{len(warning_items)}개 사양 확인이 필요합니다."
            ),
        )
    return CheckoutReviewItem(
        item_id="option_audit",
        label="옵션/사양 검수",
        status=CheckStatus.ok,
        evidence=audit.summary,
    )


def _checkout_seller_item(
    seller_questions: list[str],
    missing_questions: list[str],
) -> CheckoutReviewItem:
    if not seller_questions:
        return CheckoutReviewItem(
            item_id="seller_questions",
            label="판매자 확인 질문",
            status=CheckStatus.ok,
            evidence="추가 판매자 질문이 필요하지 않습니다.",
            required=False,
        )
    if missing_questions:
        return CheckoutReviewItem(
            item_id="seller_questions",
            label="판매자 확인 질문",
            status=CheckStatus.warning,
            evidence=f"{len(missing_questions)}개 질문의 답변이 아직 없습니다.",
        )
    return CheckoutReviewItem(
        item_id="seller_questions",
        label="판매자 확인 질문",
        status=CheckStatus.ok,
        evidence="필수 판매자 확인 질문에 대한 답변이 기록되었습니다.",
    )


def _checkout_source_item(source_trust: list) -> CheckoutReviewItem:
    review_required = [
        source for source in source_trust if source.requires_human_review
    ]
    if review_required:
        names = ", ".join(source.source_name for source in review_required[:3])
        return CheckoutReviewItem(
            item_id="source_trust",
            label="출처 신뢰도",
            status=CheckStatus.warning,
            evidence=f"검수 필요 출처가 있습니다: {names}",
        )
    return CheckoutReviewItem(
        item_id="source_trust",
        label="출처 신뢰도",
        status=CheckStatus.ok,
        evidence="가격, 리뷰, 벤치마크 출처가 정책 기준을 통과했습니다.",
    )


def _checkout_ack_item(missing_acknowledgements: list[str]) -> CheckoutReviewItem:
    if missing_acknowledgements:
        return CheckoutReviewItem(
            item_id="risk_acknowledgement",
            label="리스크 승인",
            status=CheckStatus.blocker,
            evidence=f"{len(missing_acknowledgements)}개 리스크를 아직 승인하지 않았습니다.",
        )
    return CheckoutReviewItem(
        item_id="risk_acknowledgement",
        label="리스크 승인",
        status=CheckStatus.ok,
        evidence="구매 전 리스크 승인 항목이 모두 처리되었습니다.",
    )


def _dedupe_nonempty(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _completion_template_from_row(row: sqlite3.Row) -> CompletionReportTemplate:
    data = dict(row)
    return CompletionReportTemplate(
        template_id=data["template_id"],
        workspace_id=data["workspace_id"],
        name=data["name"],
        channel=data["channel"],
        subject=data["subject"],
        body=data["body"],
        enabled=bool(data["enabled"]),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _completion_recipient_group_from_row(row: sqlite3.Row) -> CompletionRecipientGroup:
    data = dict(row)
    recipients = json.loads(data["recipients_json"])
    unsubscribed = json.loads(data["unsubscribed_json"])
    return CompletionRecipientGroup(
        group_id=data["group_id"],
        workspace_id=data["workspace_id"],
        name=data["name"],
        channel=data["channel"],
        recipients_masked=[_mask_target(item) for item in recipients],
        recipient_count=len(recipients),
        unsubscribed_count=len(unsubscribed),
        unsubscribe_policy=data["unsubscribe_policy"],
        enabled=bool(data["enabled"]),
        description=data["description"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _completion_batch_from_row(row: sqlite3.Row) -> CompletionReportBatch:
    data = dict(row)
    return CompletionReportBatch(
        batch_id=data["batch_id"],
        workspace_id=data["workspace_id"],
        status=data["status"],
        template_id=data["template_id"],
        recipient_group_id=data["recipient_group_id"],
        target_count=data["target_count"],
        selected_count=data["selected_count"],
        sent_count=data["sent_count"],
        failed_count=data["failed_count"],
        dry_run=bool(data["dry_run"]),
        note=data["note"],
        created_at=data["created_at"],
        deliveries=[],
    )


def _completion_delivery_from_row(row: sqlite3.Row) -> CompletionReportDelivery:
    data = dict(row)
    tracking_token = data.get("tracking_token") or ""
    return CompletionReportDelivery(
        delivery_id=data["delivery_id"],
        batch_id=data["batch_id"],
        report_id=data["report_id"],
        workspace_id=data["workspace_id"],
        channel=data["channel"],
        target_masked=data["target_masked"],
        template_id=data["template_id"],
        recipient_group_id=data["recipient_group_id"],
        subject=data["subject"],
        status=data["status"],
        provider_message=data["provider_message"],
        retry_count=data["retry_count"],
        next_retry_at=data["next_retry_at"],
        sent_at=data["sent_at"],
        engagement_count=int(data.get("engagement_count") or 0),
        open_count=int(data.get("open_count") or 0),
        click_count=int(data.get("click_count") or 0),
        last_engaged_at=data.get("last_engaged_at"),
        tracking_token=tracking_token,
        tracking_pixel_path=(
            f"/t/o/{tracking_token}.png" if tracking_token else ""
        ),
        tracking_click_path=f"/t/c/{tracking_token}" if tracking_token else "",
        created_at=data["created_at"],
    )


def _completion_engagement_from_row(row: sqlite3.Row) -> CompletionDeliveryEngagement:
    data = dict(row)
    return CompletionDeliveryEngagement(
        event_id=data["event_id"],
        delivery_id=data["delivery_id"],
        batch_id=data["batch_id"],
        report_id=data["report_id"],
        workspace_id=data["workspace_id"],
        event_type=data["event_type"],
        target_masked=data["target_masked"],
        metadata=json.loads(data["metadata_json"]),
        created_at=data["created_at"],
    )


def _completion_provider_event_from_row(
    row: sqlite3.Row,
) -> CompletionDeliveryProviderEvent:
    data = dict(row)
    return CompletionDeliveryProviderEvent(
        provider_event_id=data["provider_event_id"],
        delivery_id=data["delivery_id"],
        batch_id=data["batch_id"],
        report_id=data["report_id"],
        workspace_id=data["workspace_id"],
        provider_name=data["provider_name"],
        event_type=data["event_type"],
        delivery_status=data["delivery_status"],
        provider_message=data["provider_message"],
        metadata=json.loads(data["metadata_json"]),
        created_at=data["created_at"],
    )


def _feedback_from_row(row: sqlite3.Row) -> FeedbackRecord:
    data = dict(row)
    return FeedbackRecord(
        feedback_id=data["feedback_id"],
        trace_id=data["trace_id"],
        workspace_id=data["workspace_id"],
        rating=data["rating"],
        purchase_intent=bool(data["purchase_intent"]),
        selected_product_id=data["selected_product_id"],
        reason=data["reason"],
        improvement_requests=json.loads(data["improvement_requests_json"]),
        contact_masked=data["contact_masked"],
        created_at=data["created_at"],
    )


def _growth_event_from_row(row: sqlite3.Row) -> GrowthEventRecord:
    data = dict(row)
    return GrowthEventRecord(
        event_id=data["event_id"],
        workspace_id=data["workspace_id"],
        event_type=GrowthEventType(data["event_type"]),
        trace_id=data["trace_id"],
        report_id=data["report_id"],
        product_id=data["product_id"],
        source=data["source"],
        surface=data["surface"],
        label=data["label"],
        metadata=json.loads(data["metadata_json"]),
        created_at=data["created_at"],
    )


def _launch_experiment_event_from_row(row: sqlite3.Row) -> LaunchExperimentEvent:
    data = dict(row)
    return LaunchExperimentEvent(
        event_id=data["event_id"],
        experiment_id=data["experiment_id"],
        workspace_id=data["workspace_id"],
        variant_id=data["variant_id"],
        event_type=data["event_type"],
        trace_id=data["trace_id"],
        source=data["source"],
        surface=data["surface"],
        label=data["label"],
        metadata=json.loads(data["metadata_json"]),
        created_at=data["created_at"],
    )


def _launch_experiment_variant_payloads(
    request: LaunchExperimentRequest,
) -> list[dict[str, str | int]]:
    if not request.variants:
        return [
            {
                "variant_id": f"var_{uuid4().hex[:10]}",
                "label": "A",
                "headline": "조건에 맞는 컴퓨터를 구매 실패 없이 고르세요",
                "body": "예산, 용도, 가격 타이밍, 결제 전 검수를 한 번에 확인합니다.",
                "cta_label": "내 조건으로 분석",
                "cta_path": "/",
                "allocation_percent": 50,
            },
            {
                "variant_id": f"var_{uuid4().hex[:10]}",
                "label": "B",
                "headline": "컴퓨터 견적 고민을 3분 안에 줄이세요",
                "body": (
                    "데스크톱과 노트북 후보를 비교하고 "
                    "바로 살지 기다릴지 판단합니다."
                ),
                "cta_label": "3분 진단 시작",
                "cta_path": "/#start-concierge",
                "allocation_percent": 50,
            },
        ]
    return [
        {
            "variant_id": f"var_{uuid4().hex[:10]}",
            "label": variant.label[:40],
            "headline": variant.headline[:160],
            "body": variant.body[:320],
            "cta_label": variant.cta_label[:80],
            "cta_path": variant.cta_path[:200],
            "allocation_percent": variant.allocation_percent,
        }
        for variant in request.variants
    ]


def _launch_experiment_variant_stats(
    conn: sqlite3.Connection,
    workspace_id: str,
    experiment_id: str,
) -> dict[str, dict[str, int]]:
    rows = conn.execute(
        """
        SELECT variant_id, event_type, COUNT(*) AS event_count
        FROM launch_experiment_events
        WHERE workspace_id = ? AND experiment_id = ?
        GROUP BY variant_id, event_type
        """,
        (workspace_id, experiment_id),
    ).fetchall()
    stats: dict[str, dict[str, int]] = {}
    for row in rows:
        variant_id = str(row["variant_id"])
        event_type = str(row["event_type"])
        stats.setdefault(variant_id, {"impressions": 0, "conversions": 0})
        if event_type == "conversion":
            stats[variant_id]["conversions"] = int(row["event_count"] or 0)
        else:
            stats[variant_id]["impressions"] += int(row["event_count"] or 0)
    return stats


def _launch_variant_from_payload(
    payload: dict,
    stats: dict[str, dict[str, int]],
) -> LaunchExperimentVariant:
    variant_id = str(payload["variant_id"])
    variant_stats = stats.get(variant_id, {"impressions": 0, "conversions": 0})
    impressions = int(variant_stats.get("impressions", 0))
    conversions = int(variant_stats.get("conversions", 0))
    conversion_rate = round(conversions / impressions, 4) if impressions else 0
    status = _launch_variant_status(impressions, conversion_rate)
    return LaunchExperimentVariant(
        variant_id=variant_id,
        label=str(payload["label"]),
        headline=str(payload["headline"]),
        body=str(payload["body"]),
        cta_label=str(payload["cta_label"]),
        cta_path=str(payload["cta_path"]),
        allocation_percent=int(payload["allocation_percent"]),
        impressions=impressions,
        conversions=conversions,
        conversion_rate=conversion_rate,
        status=status,
        evidence=f"노출 {impressions}회 / 전환 {conversions}건",
        recommendation=_launch_variant_recommendation(status, impressions, conversion_rate),
    )


def _launch_experiment_from_row(
    row: sqlite3.Row,
    stats: dict[str, dict[str, int]],
) -> LaunchExperiment:
    data = dict(row)
    variants_payload = json.loads(data["variants_json"])
    variants = [
        _launch_variant_from_payload(payload, stats) for payload in variants_payload
    ]
    best_variant = _best_launch_variant(variants)
    status = _launch_experiment_status(variants)
    winning_variant_id = (
        best_variant.variant_id if best_variant and status == CheckStatus.ok else None
    )
    return LaunchExperiment(
        experiment_id=data["experiment_id"],
        workspace_id=data["workspace_id"],
        name=data["name"],
        channel=data["channel"],
        audience=data["audience"],
        hypothesis=data["hypothesis"],
        primary_metric=GrowthEventType(data["primary_metric"]),
        target_surface=data["target_surface"],
        category=Category(data["category"]) if data["category"] else None,
        status=status,
        winning_variant_id=winning_variant_id,
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        variants=variants,
    )


def _beta_lead_from_row(row: sqlite3.Row) -> BetaLead:
    data = dict(row)
    return BetaLead(
        lead_id=data["lead_id"],
        workspace_id=data["workspace_id"],
        email_masked=data["email_masked"],
        persona=data["persona"],
        use_case=data["use_case"],
        company_size=data["company_size"],
        contact_consent=bool(data["contact_consent"]),
        source=data["source"],
        created_at=data["created_at"],
    )


def _waitlist_referral_from_row(row: sqlite3.Row) -> WaitlistReferral:
    data = dict(row)
    referred_signup_count = int(data.get("referred_signup_count") or 0)
    return WaitlistReferral(
        referral_id=data["referral_id"],
        workspace_id=data["workspace_id"],
        email_masked=data["email_masked"],
        persona=data["persona"],
        use_case=data["use_case"],
        referral_code=data["referral_code"],
        referred_by_code=data["referred_by_code"],
        referral_url=data["referral_url"],
        referred_signup_count=referred_signup_count,
        priority_score=_waitlist_priority_score(
            referred_signup_count,
            bool(data["contact_consent"]),
        ),
        contact_consent=bool(data["contact_consent"]),
        source=data["source"],
        created_at=data["created_at"],
    )


def _subscription_intent_from_row(row: sqlite3.Row) -> SubscriptionIntent:
    data = dict(row)
    return SubscriptionIntent(
        intent_id=data["intent_id"],
        workspace_id=data["workspace_id"],
        email_masked=data["email_masked"],
        plan_id=data["plan_id"],
        plan_name=data["plan_name"],
        billing_cycle=data["billing_cycle"],
        monthly_price_krw=data["monthly_price_krw"],
        estimated_mrr_krw=data["estimated_mrr_krw"],
        persona=data["persona"],
        use_case=data["use_case"],
        team_size=data["team_size"],
        max_budget_krw=data["max_budget_krw"],
        feature_priorities=json.loads(data["feature_priorities_json"]),
        purchase_timing=data["purchase_timing"],
        contact_consent=bool(data["contact_consent"]),
        source=data["source"],
        readiness_status=CheckStatus(data["readiness_status"]),
        recommendation=data["recommendation"],
        created_at=data["created_at"],
    )


def pricing_plans() -> list[PricingPlan]:
    return [
        PricingPlan(
            plan_id="free",
            name="Free 리포트",
            audience="가끔 PC나 노트북을 비교하는 개인",
            monthly_price_krw=0,
            annual_price_krw=0,
            features=[
                "기본 추천 리포트",
                "공유 리포트",
                "구매 전 체크리스트",
            ],
            recommended_for=["첫 구매자", "가벼운 비교"],
            cta_label="무료로 시작",
        ),
        PricingPlan(
            plan_id="premium",
            name="Premium 구매 코치",
            audience="가격 알림과 상세 근거가 필요한 개인 구매자",
            monthly_price_krw=9900,
            annual_price_krw=99000,
            features=[
                "상세 근거 팩",
                "가격 알림",
                "저장 견적 비교",
                "결제 전 검수 기록",
            ],
            recommended_for=["게이밍 PC", "영상 편집 PC", "고가 노트북"],
            cta_label="프리미엄 관심 등록",
        ),
        PricingPlan(
            plan_id="team",
            name="Team 구매 보조",
            audience="사무용 PC와 노트북을 반복 구매하는 팀",
            monthly_price_krw=49000,
            annual_price_krw=490000,
            features=[
                "팀 공유 리포트",
                "구매 결과 학습 인사이트",
                "완료 리포트 발송",
                "운영 대시보드",
            ],
            recommended_for=["스타트업", "사무 장비 구매", "B2B 구매 담당자"],
            cta_label="팀 도입 문의",
        ),
    ]


def pricing_plan_by_id(plan_id: str | None) -> PricingPlan | None:
    normalized = (plan_id or "").strip().lower()
    return next((plan for plan in pricing_plans() if plan.plan_id == normalized), None)


def _billing_cycle(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"annual", "yearly", "year"}:
        return "annual"
    return "monthly"


def _estimated_subscription_mrr(
    plan: PricingPlan,
    billing_cycle: str,
    team_size: int,
) -> int:
    if plan.plan_id == "free":
        return 0
    if billing_cycle == "annual":
        return int(round(plan.annual_price_krw / 12))
    multiplier = max(1, team_size if plan.plan_id == "team" else 1)
    return plan.monthly_price_krw * multiplier


def _subscription_intent_readiness(
    plan: PricingPlan,
    request: SubscriptionIntentRequest,
    estimated_mrr: int,
) -> tuple[CheckStatus, str]:
    if plan.plan_id == "free":
        return CheckStatus.warning, "무료 사용자는 프리미엄 전환 조건을 후속 질문으로 확인하세요."
    if request.max_budget_krw is not None and request.max_budget_krw < estimated_mrr:
        return CheckStatus.warning, "희망 예산이 요금제보다 낮아 가격/기능 패키지를 재검토하세요."
    if request.purchase_timing in {"now", "within_7_days", "within_30_days"}:
        return CheckStatus.ok, "즉시 전환 가능성이 있어 온보딩과 결제 연결 우선순위가 높습니다."
    return CheckStatus.warning, "구매 시점이 멀어 리마인더와 사용 사례 검증이 필요합니다."


def _pricing_dashboard_status(
    intent_count: int,
    estimated_mrr: int,
    intents: list[SubscriptionIntent],
) -> tuple[CheckStatus, list[str]]:
    actions: list[str] = []
    if intent_count < 5:
        actions.append("대표 persona별 구독 의향을 최소 5건 이상 수집하세요.")
    if estimated_mrr < 100_000:
        actions.append("프리미엄/팀 요금제 메시지를 개선해 예상 MRR 10만원 이상을 검증하세요.")
    if not any(item.plan_id == "team" for item in intents):
        actions.append("B2B 구매 보조 수요를 확인할 team plan 리드를 확보하세요.")
    if not actions:
        return CheckStatus.ok, ["결제 연동 전환 실험을 준비하세요."]
    if intent_count == 0:
        return CheckStatus.blocker, actions
    return CheckStatus.warning, actions


def _beta_cohort_from_row(row: sqlite3.Row) -> BetaCohort:
    data = dict(row)
    return BetaCohort(
        cohort_id=data["cohort_id"],
        workspace_id=data["workspace_id"],
        name=data["name"],
        scenario=data["scenario"],
        category=Category(data["category"]),
        target_persona=data["target_persona"],
        target_size=data["target_size"],
        success_metric=data["success_metric"],
        keywords=json.loads(data["keywords_json"]),
        notes=data["notes"],
        active=bool(data["active"]),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _beta_backlog_action_from_row(row: sqlite3.Row) -> BetaBacklogAction:
    data = dict(row)
    return BetaBacklogAction(
        backlog_id=data["backlog_id"],
        workspace_id=data["workspace_id"],
        status=BetaBacklogStatus(data["status"]),
        assignee=data["assignee"],
        note=data["note"],
        sla_due_at=data["sla_due_at"],
        completed_at=data["completed_at"],
        completion_summary=data["completion_summary"],
        updated_at=data["updated_at"],
    )


def _review_item_from_row(row: sqlite3.Row) -> ReviewQueueItem:
    data = dict(row)
    return ReviewQueueItem(
        review_id=data["review_id"],
        source=SourceCandidate.model_validate_json(data["source_json"]),
        status=ReviewStatus(data["status"]),
        reason=data["reason"],
        created_at=data["created_at"],
        resolved_at=data["resolved_at"],
        reviewer=data["reviewer"],
    )


def _source_monitor_from_row(row: sqlite3.Row) -> SourceMonitor:
    data = dict(row)
    return SourceMonitor(
        monitor_id=data["monitor_id"],
        workspace_id=data["workspace_id"],
        url=data["url"],
        category=Category(data["category"]),
        kind=data["kind"],
        expected_model=data["expected_model"],
        source_name=data["source_name"],
        seller=data["seller"],
        cadence_minutes=data["cadence_minutes"],
        active=bool(data["active"]),
        last_run_at=data["last_run_at"],
        last_status=data["last_status"],
        last_source_id=data["last_source_id"],
        failure_count=data["failure_count"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        html_snapshot=data["html_snapshot"],
    )


def _source_refresh_run_from_row(row: sqlite3.Row) -> SourceRefreshRun:
    data = dict(row)
    return SourceRefreshRun(
        run_id=data["run_id"],
        monitor_id=data["monitor_id"],
        workspace_id=data["workspace_id"],
        status=data["status"],
        source_id=data["source_id"],
        review_id=data["review_id"],
        fetched_live=bool(data["fetched_live"]),
        message=data["message"],
        created_at=data["created_at"],
    )


def _source_provider_policy_from_row(row: sqlite3.Row) -> SourceProviderPolicy:
    data = dict(row)
    return SourceProviderPolicy(
        provider_id=data["provider_id"],
        workspace_id=data["workspace_id"],
        provider_name=data["provider_name"],
        host_pattern=data["host_pattern"],
        kind=data["kind"],
        live_fetch_allowed=bool(data["live_fetch_allowed"]),
        robots_status=ProviderReviewStatus(data["robots_status"]),
        terms_status=ProviderReviewStatus(data["terms_status"]),
        credential_status=data["credential_status"],
        rate_limit_per_hour=data["rate_limit_per_hour"],
        notes=data["notes"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


REQUIRED_INTEGRATION_CATEGORIES: list[tuple[IntegrationCategory, bool]] = [
    (IntegrationCategory.price_api, True),
    (IntegrationCategory.marketplace, True),
    (IntegrationCategory.official_store, True),
    (IntegrationCategory.review_feed, False),
    (IntegrationCategory.benchmark, False),
    (IntegrationCategory.email, True),
    (IntegrationCategory.webhook, False),
    (IntegrationCategory.observability, True),
    (IntegrationCategory.affiliate, False),
    (IntegrationCategory.scheduler, True),
]

INTEGRATION_CATEGORY_LABELS = {
    IntegrationCategory.price_api: "가격 비교 공식 API",
    IntegrationCategory.marketplace: "오픈마켓 provider",
    IntegrationCategory.official_store: "공식 스토어 provider",
    IntegrationCategory.review_feed: "리뷰 수집 feed",
    IntegrationCategory.benchmark: "벤치마크 수집",
    IntegrationCategory.email: "이메일 발송 provider",
    IntegrationCategory.sms: "SMS 발송 provider",
    IntegrationCategory.webhook: "외부 webhook",
    IntegrationCategory.observability: "LangSmith/OpenTelemetry export",
    IntegrationCategory.affiliate: "제휴 링크/비제휴 대안",
    IntegrationCategory.scheduler: "외부 scheduler",
}


def _integration_provider_from_row(row: sqlite3.Row) -> IntegrationProvider:
    data = dict(row)
    return IntegrationProvider(
        integration_id=data["integration_id"],
        workspace_id=data["workspace_id"],
        provider_name=data["provider_name"],
        category=IntegrationCategory(data["category"]),
        status=IntegrationStatus(data["status"]),
        credential_status=data["credential_status"],
        rate_limit_per_hour=data["rate_limit_per_hour"],
        retention_days=data["retention_days"],
        endpoint=data["endpoint"],
        evidence=data["evidence"],
        notes=data["notes"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        last_verified_at=data["last_verified_at"],
    )


def _integration_status_weight(status: IntegrationStatus) -> int:
    return {
        IntegrationStatus.blocked: 0,
        IntegrationStatus.mock: 1,
        IntegrationStatus.configured: 2,
        IntegrationStatus.verified: 3,
    }[status]


def _integration_readiness_check(
    category: IntegrationCategory,
    provider: IntegrationProvider | None,
    critical: bool,
) -> IntegrationReadinessCheck:
    label = INTEGRATION_CATEGORY_LABELS[category]
    if provider is None:
        return IntegrationReadinessCheck(
            category=category,
            label=label,
            status=CheckStatus.blocker if critical else CheckStatus.warning,
            metric="등록된 provider 없음",
            recommendation=(
                f"{label} 연동 provider, credential 상태, rate limit, "
                "보존 정책을 등록하세요."
            ),
        )
    if provider.status == IntegrationStatus.blocked:
        return IntegrationReadinessCheck(
            category=category,
            label=label,
            status=CheckStatus.blocker,
            provider_name=provider.provider_name,
            metric=f"{provider.status.value} · credential {provider.credential_status}",
            recommendation=f"{label} 차단 사유를 해소하고 검증 증거를 남기세요.",
        )
    if provider.status == IntegrationStatus.mock:
        return IntegrationReadinessCheck(
            category=category,
            label=label,
            status=CheckStatus.blocker if critical else CheckStatus.warning,
            provider_name=provider.provider_name,
            metric=f"mock · credential {provider.credential_status}",
            recommendation=f"{label} mock을 실제 provider configured 이상으로 전환하세요.",
        )
    if provider.status == IntegrationStatus.configured:
        status = CheckStatus.warning if critical else CheckStatus.ok
        return IntegrationReadinessCheck(
            category=category,
            label=label,
            status=status,
            provider_name=provider.provider_name,
            metric=(
                f"configured · 시간당 {provider.rate_limit_per_hour}회 · "
                f"보존 {provider.retention_days}일"
            ),
            recommendation=f"{label} smoke test와 운영 증거를 남겨 verified 상태로 올리세요.",
        )
    return IntegrationReadinessCheck(
        category=category,
        label=label,
        status=CheckStatus.ok,
        provider_name=provider.provider_name,
        metric=(
            f"verified · 시간당 {provider.rate_limit_per_hour}회 · "
            f"보존 {provider.retention_days}일"
        ),
        recommendation=f"{label} 연동 검증 상태를 유지하세요.",
    )


def _integration_readiness_score(checks: list[IntegrationReadinessCheck]) -> float:
    if not checks:
        return 0
    points = {
        CheckStatus.ok: 100.0,
        CheckStatus.warning: 55.0,
        CheckStatus.blocker: 0.0,
    }
    return round(sum(points[check.status] for check in checks) / len(checks), 2)


def _integration_readiness_summary(
    status: CheckStatus,
    score: float,
    blocker_count: int,
    warning_count: int,
) -> str:
    if status == CheckStatus.ok:
        return f"외부 연동 준비도 {score}점입니다. 핵심 연동이 verified 기준을 충족했습니다."
    if status == CheckStatus.blocker:
        return (
            f"외부 연동 준비도 {score}점입니다. blocker {blocker_count}건을 "
            "처리하기 전에는 공개 출시를 막아야 합니다."
        )
    return f"외부 연동 준비도 {score}점입니다. warning {warning_count}건을 검증하세요."


def _data_inventory_item(
    conn: sqlite3.Connection,
    workspace_id: str,
    spec: dict[str, object],
) -> DataInventoryItem:
    table = str(spec["table_name"])
    created_column = str(spec["created_column"])
    row = conn.execute(
        f"""
        SELECT COUNT(*) AS record_count,
               MIN({created_column}) AS earliest_created_at,
               MAX({created_column}) AS latest_created_at
        FROM {table}
        WHERE workspace_id = ?
        """,
        (workspace_id,),
    ).fetchone()
    record_count = int(row["record_count"] or 0)
    retention_days = int(spec["retention_days"])
    pii_scope = str(spec["pii_scope"])
    status = CheckStatus.ok
    recommendation = "보존/마스킹 기준을 충족합니다."
    earliest = row["earliest_created_at"]
    if record_count and pii_scope == "raw_contact":
        status = CheckStatus.blocker
        recommendation = (
            f"{spec['label']} 테이블은 원문 연락처 컬럼을 포함합니다. "
            "응답 표면 마스킹을 유지하고 저장 컬럼을 contact_hash/contact_masked로 분리하세요."
        )
    elif record_count and _retention_expired(earliest, retention_days):
        status = CheckStatus.warning
        recommendation = (
            f"{spec['label']} 보존 기준 {retention_days}일을 넘은 항목이 있습니다. "
            "워크스페이스 export 후 삭제 작업 대상으로 분리하세요."
        )
    return DataInventoryItem(
        table_name=table,
        label=str(spec["label"]),
        record_count=record_count,
        pii_scope=pii_scope,
        retention_days=retention_days,
        earliest_created_at=earliest,
        latest_created_at=row["latest_created_at"],
        status=status,
        recommendation=recommendation,
    )


def _retention_expired(created_at: str | None, retention_days: int) -> bool:
    parsed = _parse_iso_datetime(created_at)
    if parsed is None:
        return False
    return parsed < datetime.now(UTC) - timedelta(days=retention_days)


def _data_governance_summary(
    status: CheckStatus,
    total_records: int,
    raw_contact_surfaces: int,
) -> str:
    if status == CheckStatus.blocker:
        return (
            f"워크스페이스 데이터 {total_records}건 중 원문 연락처 표면 "
            f"{raw_contact_surfaces}개가 있어 공개 출시 전 저장 구조 보강이 필요합니다."
        )
    if status == CheckStatus.warning:
        return (
            f"워크스페이스 데이터 {total_records}건 기준 보존 기간 초과 항목이 있어 "
            "삭제 작업 대상을 분리해야 합니다."
        )
    return f"워크스페이스 데이터 {total_records}건이 현재 마스킹/보존 기준을 충족합니다."


def _ensure_column(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _cohort_keywords(request: BetaCohortRequest) -> list[str]:
    seeds = [request.name, request.scenario, request.target_persona, *request.keywords]
    normalized: list[str] = []
    for seed in seeds:
        value = seed.strip()
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def _like_pattern(value: str) -> str:
    return f"%{value}%"


def _observability_payload(
    *,
    workspace_id: str,
    destination: str,
    analysis: AnalyzeResponse,
    spans: list[TraceSpanRecord],
) -> dict:
    quality = analysis.quality_audit
    top = (
        analysis.report.top_recommendations[0]
        if analysis.report.top_recommendations
        else None
    )
    return {
        "schema_version": "specpilot.observability.v1",
        "destination": destination,
        "workspace_id": workspace_id,
        "trace_id": analysis.graph_trace_id,
        "category": analysis.criteria.category.value,
        "purpose": analysis.criteria.purpose,
        "budget_krw": analysis.criteria.budget_krw,
        "final_pick_id": analysis.report.final_pick_id,
        "top_model_name": top.product.model_name if top else None,
        "quality": {
            "score": quality.quality_score if quality else 0,
            "warning_count": quality.warning_count if quality else 0,
            "blocker_count": quality.blocker_count if quality else 0,
            "estimated_cost_krw": quality.estimated_cost_krw if quality else 0,
            "launch_blockers": quality.launch_blockers if quality else [],
        },
        "spans": [
            {
                "span_id": span.span_id,
                "sequence": span.sequence,
                "step": span.step.value,
                "title": span.title,
                "status": span.status.value,
                "evidence_count": span.evidence_count,
                "created_at": span.created_at,
            }
            for span in spans
        ],
    }


def _default_sla_due_at(item: BetaBacklogItem) -> str:
    created_at = _parse_iso_datetime(item.created_at) or datetime.now(UTC)
    if item.severity == CheckStatus.blocker:
        due_at = created_at + timedelta(hours=48)
    elif item.severity == CheckStatus.warning:
        due_at = created_at + timedelta(days=5)
    else:
        due_at = created_at + timedelta(days=7)
    return due_at.isoformat()


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _is_overdue(
    due_at: str | None,
    status: BetaBacklogStatus,
) -> bool:
    if status in {BetaBacklogStatus.done, BetaBacklogStatus.dismissed}:
        return False
    parsed = _parse_iso_datetime(due_at)
    return bool(parsed and parsed < datetime.now(UTC))


def _is_due_soon(due_at: str | None) -> bool:
    parsed = _parse_iso_datetime(due_at)
    if parsed is None:
        return False
    now = datetime.now(UTC)
    return now <= parsed <= now + timedelta(hours=24)


def _beta_completion_summary(
    item: BetaBacklogItem,
    request: BetaBacklogActionRequest,
) -> str:
    note = request.note.strip()
    if note:
        return f"{item.title} 완료: {note}"
    return f"{item.title} 완료 처리. 근거: {item.evidence}"


def _ops_regression_period(label: str, rows: list[sqlite3.Row]) -> OpsRegressionPeriod:
    if not rows:
        return OpsRegressionPeriod(label=label)
    run_count = len(rows)
    quality = sum(float(row["quality_score"] or 0) for row in rows) / run_count
    cost = sum(float(row["estimated_cost_krw"] or 0) for row in rows) / run_count
    warnings = sum(int(row["warning_count"] or 0) for row in rows)
    blockers = sum(int(row["blocker_count"] or 0) for row in rows)
    created_values = [row["created_at"] for row in rows if row["created_at"]]
    return OpsRegressionPeriod(
        label=label,
        run_count=run_count,
        average_quality_score=round(quality, 2),
        average_cost_krw=round(cost, 2),
        warning_count=warnings,
        blocker_count=blockers,
        started_at=min(created_values) if created_values else None,
        ended_at=max(created_values) if created_values else None,
    )


def _learning_insight_from_rows(
    *,
    outcome: sqlite3.Row,
    checkout: sqlite3.Row | None,
    feedback: sqlite3.Row | None,
) -> OpsLearningInsight:
    outcome_count = int(outcome["outcome_count"] or 0)
    purchase_count = int(outcome["purchase_count"] or 0)
    abandoned_count = int(outcome["abandoned_count"] or 0)
    delayed_count = int(outcome["delayed_count"] or 0)
    returned_count = int(outcome["returned_count"] or 0)
    checkout_review_count = int(checkout["checkout_review_count"] or 0) if checkout else 0
    checkout_blocked_count = int(checkout["checkout_blocked_count"] or 0) if checkout else 0
    feedback_count = int(feedback["feedback_count"] or 0) if feedback else 0
    conversion_rate = purchase_count / outcome_count if outcome_count else 0
    return_rate = returned_count / outcome_count if outcome_count else 0
    average_satisfaction = _learning_average_satisfaction(outcome, feedback)
    average_delta = round(float(outcome["average_price_delta_krw"] or 0), 2)
    status, tags, action = _learning_status_and_action(
        conversion_rate=conversion_rate,
        return_rate=return_rate,
        abandoned_count=abandoned_count,
        delayed_count=delayed_count,
        checkout_review_count=checkout_review_count,
        checkout_blocked_count=checkout_blocked_count,
        average_satisfaction=average_satisfaction,
        average_delta=average_delta,
    )
    evidence = (
        f"결과 {outcome_count}건, 구매 {purchase_count}건, 이탈 {abandoned_count}건, "
        f"지연 {delayed_count}건, 반품 {returned_count}건, 최종가 차이 {average_delta:,.0f}원"
    )
    return OpsLearningInsight(
        product_id=outcome["product_id"],
        model_name=outcome["model_name"],
        outcome_count=outcome_count,
        purchase_count=purchase_count,
        abandoned_count=abandoned_count,
        delayed_count=delayed_count,
        returned_count=returned_count,
        checkout_review_count=checkout_review_count,
        checkout_blocked_count=checkout_blocked_count,
        feedback_count=feedback_count,
        average_satisfaction=average_satisfaction,
        conversion_rate=round(conversion_rate, 4),
        return_rate=round(return_rate, 4),
        average_price_delta_krw=average_delta,
        conversion_value_krw=int(outcome["conversion_value_krw"] or 0),
        status=status,
        evidence=evidence,
        recommended_action=action,
        learning_tags=tags,
    )


def _learning_average_satisfaction(
    outcome: sqlite3.Row,
    feedback: sqlite3.Row | None,
) -> float:
    values = [
        float(value)
        for value in (
            outcome["average_satisfaction"],
            feedback["feedback_satisfaction"] if feedback else None,
        )
        if value is not None
    ]
    if not values:
        return 0
    return round(sum(values) / len(values), 2)


def _learning_status_and_action(
    *,
    conversion_rate: float,
    return_rate: float,
    abandoned_count: int,
    delayed_count: int,
    checkout_review_count: int,
    checkout_blocked_count: int,
    average_satisfaction: float,
    average_delta: float,
) -> tuple[CheckStatus, list[str], str]:
    tags: list[str] = []
    if average_delta > 50_000:
        tags.append("가격 신선도")
    if checkout_review_count and checkout_blocked_count / checkout_review_count >= 0.35:
        tags.append("결제 검수 차단")
    if return_rate >= 0.2:
        tags.append("반품 리스크")
    if abandoned_count:
        tags.append("구매 이탈")
    if delayed_count:
        tags.append("가격 대기")
    if average_satisfaction and average_satisfaction < 4:
        tags.append("만족도 낮음")
    if return_rate >= 0.2 or (average_satisfaction and average_satisfaction < 3):
        return (
            CheckStatus.blocker,
            tags,
            "추천 노출을 줄이고 반품/낮은 만족도 사유를 가격, 호환성, 기대 성능으로 분해하세요.",
        )
    if conversion_rate < 0.5 or tags:
        return (
            CheckStatus.warning,
            tags,
            "가격 신선도, 옵션 검수, 이탈 사유를 보강한 뒤 유사 조건 랭킹을 재검토하세요.",
        )
    return (
        CheckStatus.ok,
        tags or ["긍정 전환"],
        "실제 구매 전환 신호가 양호합니다. 유사 예산/목적 추천에서 긍정 근거로 유지하세요.",
    )


def _learning_dashboard_status(insights: list[OpsLearningInsight]) -> CheckStatus:
    if any(item.status == CheckStatus.blocker for item in insights):
        return CheckStatus.blocker
    if any(item.status == CheckStatus.warning for item in insights):
        return CheckStatus.warning
    return CheckStatus.ok


def _learning_top_actions(insights: list[OpsLearningInsight]) -> list[str]:
    actions = [
        f"{item.model_name or item.product_id}: {item.recommended_action}"
        for item in insights
        if item.status != CheckStatus.ok
    ]
    if not actions:
        actions = [
            f"{item.model_name or item.product_id}: {item.recommended_action}"
            for item in insights[:3]
        ]
    return _dedupe_strings(actions)[:5]


def _learning_dashboard_summary(
    status: CheckStatus,
    insights: list[OpsLearningInsight],
) -> str:
    outcome_count = sum(item.outcome_count for item in insights)
    purchase_count = sum(item.purchase_count for item in insights)
    conversion_rate = purchase_count / outcome_count if outcome_count else 0
    if status == CheckStatus.blocker:
        return (
            f"구매 결과 {outcome_count}건 중 반품/만족도 차단 신호가 있습니다. "
            f"전체 실구매 전환율은 {round(conversion_rate * 100)}%입니다."
        )
    if status == CheckStatus.warning:
        return (
            f"구매 결과 {outcome_count}건 기준 보강할 제품이 있습니다. "
            f"전체 실구매 전환율은 {round(conversion_rate * 100)}%입니다."
        )
    return (
        f"구매 결과 {outcome_count}건의 학습 신호가 안정적입니다. "
        f"전체 실구매 전환율은 {round(conversion_rate * 100)}%입니다."
    )


def _provider_reliability_metric(row: sqlite3.Row) -> ProviderReliabilityMetric:
    fetch_count = int(row["fetch_count"] or 0)
    allowed_count = int(row["allowed_count"] or 0)
    blocked_count = int(row["blocked_count"] or 0)
    blocked_rate = round(blocked_count / fetch_count, 4) if fetch_count else 0
    if blocked_rate >= 0.5 and blocked_count >= 2:
        status = CheckStatus.blocker
        recommendation = "provider 정책, robots/약관 승인, rate limit을 즉시 재검토하세요."
    elif blocked_rate >= 0.25:
        status = CheckStatus.warning
        recommendation = "차단 사유를 확인하고 host 정책 또는 수집 cadence를 조정하세요."
    else:
        status = CheckStatus.ok
        recommendation = "현재 provider fetch 품질은 안정적입니다."
    return ProviderReliabilityMetric(
        provider_id=row["provider_id"],
        provider_name=row["provider_name"],
        host=row["host"],
        fetch_count=fetch_count,
        allowed_count=allowed_count,
        blocked_count=blocked_count,
        blocked_rate=blocked_rate,
        status=status,
        recommendation=recommendation,
    )


def _ops_regression_status(
    *,
    recent: OpsRegressionPeriod,
    previous: OpsRegressionPeriod,
    quality_delta: float,
    cost_delta_rate: float,
    provider_reliability: list[ProviderReliabilityMetric],
) -> tuple[CheckStatus, list[str], list[str]]:
    risk_flags: list[str] = []
    next_actions: list[str] = []
    if recent.run_count == 0:
        risk_flags.append("최근 분석 실행 데이터가 없습니다.")
        next_actions.append("대표 구매 시나리오 분석을 먼저 실행해 기준선을 만드세요.")
        return CheckStatus.warning, risk_flags, next_actions
    if previous.run_count == 0:
        risk_flags.append("이전 비교 구간이 없어 회귀 여부를 제한적으로만 판단합니다.")
        next_actions.append("동일 시나리오를 반복 실행해 품질 기준선을 확보하세요.")
    if recent.average_quality_score < 75:
        risk_flags.append(f"최근 평균 품질이 {recent.average_quality_score}점으로 낮습니다.")
        next_actions.append("공개 차단 사유, 출처 신뢰, 옵션 검수표를 우선 보강하세요.")
    if previous.run_count and quality_delta <= -8:
        risk_flags.append(f"품질 점수가 이전 구간 대비 {abs(quality_delta)}점 하락했습니다.")
        next_actions.append("최근 trace span과 품질 감사 노트를 비교해 하락 원인을 분리하세요.")
    if recent.blocker_count > previous.blocker_count and recent.blocker_count > 0:
        risk_flags.append(f"최근 blocker가 {recent.blocker_count}건으로 증가했습니다.")
        next_actions.append("blocker가 있는 공개 리포트 생성을 중단하고 백로그로 전환하세요.")
    if cost_delta_rate >= 0.3:
        risk_flags.append(
            f"분석당 비용이 이전 구간 대비 {round(cost_delta_rate * 100)}% 증가했습니다."
        )
        next_actions.append("source 호출 수와 LLM token 사용량 증가 원인을 확인하세요.")
    blocked_providers = [
        item
        for item in provider_reliability
        if item.status in {CheckStatus.warning, CheckStatus.blocker}
    ]
    if blocked_providers:
        names = ", ".join(item.provider_name for item in blocked_providers[:3])
        risk_flags.append(f"provider fetch 차단율 주의: {names}")
        next_actions.append("provider별 robots/약관 승인과 cadence를 재점검하세요.")
    if not next_actions:
        next_actions.append("현재 회귀 신호가 없으므로 베타 cohort 확대를 유지하세요.")
    status = CheckStatus.ok
    if any(item.status == CheckStatus.blocker for item in provider_reliability):
        status = CheckStatus.blocker
    if recent.average_quality_score < 70 or recent.blocker_count >= 3:
        status = CheckStatus.blocker
    elif risk_flags and status != CheckStatus.blocker:
        status = CheckStatus.warning
    return status, risk_flags, _dedupe_strings(next_actions)


def _ops_regression_summary(
    *,
    status: CheckStatus,
    recent: OpsRegressionPeriod,
    previous: OpsRegressionPeriod,
    quality_delta: float,
    cost_delta_rate: float,
) -> str:
    if recent.run_count == 0:
        return "회귀 모니터링을 위한 분석 실행 데이터가 아직 없습니다."
    direction = "상승" if quality_delta >= 0 else "하락"
    if previous.run_count == 0:
        return (
            f"최근 {recent.run_count}건 평균 품질은 "
            f"{recent.average_quality_score}점이며 비교 기준선이 더 필요합니다."
        )
    return (
        f"최근 {recent.run_count}건 평균 품질은 {recent.average_quality_score}점으로 "
        f"이전 구간 대비 {abs(quality_delta)}점 {direction}했고, "
        f"분석당 비용 변화율은 {round(cost_delta_rate * 100)}%입니다. "
        f"현재 상태는 {status.value}입니다."
    )


def _dedupe_strings(items: list[str]) -> list[str]:
    deduped: list[str] = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped


def _cohort_report_recommendations(
    cohort: BetaCohort,
    backlog: list[BetaBacklogItem],
) -> list[str]:
    recommendations: list[str] = []
    if cohort.lead_count < cohort.target_size:
        remaining = cohort.target_size - cohort.lead_count
        recommendations.append(f"목표 cohort까지 베타 리드 {remaining}명을 추가 모집하세요.")
    if cohort.feedback_count < 5:
        recommendations.append(
            "피드백 표본이 작으므로 실제 구매 직전 사용자 인터뷰를 우선 확보하세요."
        )
    if cohort.purchase_intent_rate < 0.4:
        recommendations.append(
            "구매 의향이 낮아 가격 근거, 호환성 설명, 대안 시나리오를 보강하세요."
        )
    if backlog:
        blockers = sum(1 for item in backlog if item.severity == CheckStatus.blocker)
        if blockers:
            recommendations.append(f"출시 전 blocker 백로그 {blockers}건을 먼저 닫으세요.")
        else:
            recommendations.append("warning 백로그를 처리해 공개 리포트 신뢰도를 높이세요.")
    if not recommendations:
        recommendations.append("현재 cohort는 공개 베타 확대 기준을 충족합니다.")
    return recommendations


def _render_beta_cohort_markdown(
    *,
    cohort: BetaCohort,
    generated_at: str,
    summary: str,
    recommendations: list[str],
    backlog: list[BetaBacklogItem],
) -> str:
    lines = [
        f"# {cohort.name} 베타 cohort 리포트",
        "",
        f"- 생성 시각: {generated_at}",
        f"- 워크스페이스: {cohort.workspace_id}",
        f"- 시나리오: {cohort.scenario}",
        f"- 카테고리: {cohort.category.value}",
        f"- 대상 persona: {cohort.target_persona}",
        "",
        "## 요약",
        "",
        summary,
        "",
        "## 핵심 지표",
        "",
        f"- 리드: {cohort.lead_count}/{cohort.target_size}명",
        f"- 피드백: {cohort.feedback_count}건",
        f"- 평균 만족도: {cohort.average_satisfaction}",
        f"- 구매 의향: {round(cohort.purchase_intent_rate * 100)}%",
        f"- cohort 준비도: {round(cohort.readiness_score)}점",
        "",
        "## 다음 액션",
        "",
    ]
    lines.extend(f"- {item}" for item in recommendations)
    lines.extend(["", "## 열린 개선 백로그", ""])
    if not backlog:
        lines.append("- 현재 열린 백로그가 없습니다.")
    else:
        for item in backlog:
            owner = f" / 담당: {item.assignee}" if item.assignee else ""
            lines.append(
                f"- [{item.status.value}] {item.title} "
                f"({item.source_type}, {item.severity.value}{owner})"
            )
            lines.append(f"  - 근거: {item.evidence}")
            lines.append(f"  - 조치: {item.suggested_action}")
            if item.action_note:
                lines.append(f"  - 운영 메모: {item.action_note}")
    return "\n".join(lines) + "\n"


def _readiness_check(
    *,
    area: str,
    label: str,
    value: int | float,
    warning_threshold: int | float,
    ok_threshold: int | float,
    metric: str,
    recommendation: str,
) -> BetaReadinessCheck:
    if value >= ok_threshold:
        status = CheckStatus.ok
        recommendation = f"{label} 기준은 공개 베타 기준을 충족했습니다."
    elif value >= warning_threshold:
        status = CheckStatus.warning
    else:
        status = CheckStatus.blocker
    return BetaReadinessCheck(
        area=area,
        label=label,
        status=status,
        metric=metric,
        recommendation=recommendation,
    )


def _quality_readiness_check(quality: QualityDashboard) -> BetaReadinessCheck:
    if quality.audit_count == 0:
        return BetaReadinessCheck(
            area="quality",
            label="품질 감사",
            status=CheckStatus.blocker,
            metric="품질 감사 0건",
            recommendation="대표 분석을 실행해 품질 점수와 공개 차단 사유를 먼저 저장하세요.",
        )
    if quality.blocker_count > 0:
        return BetaReadinessCheck(
            area="quality",
            label="품질 감사",
            status=CheckStatus.blocker,
            metric=f"평균 {quality.average_quality_score}점 / 차단 {quality.blocker_count}건",
            recommendation=(
                "공개 차단 사유가 있는 분석은 검수하거나 입력 조건을 "
                "보강한 뒤 다시 실행하세요."
            ),
        )
    if quality.average_quality_score < 80:
        return BetaReadinessCheck(
            area="quality",
            label="품질 감사",
            status=CheckStatus.warning,
            metric=f"평균 {quality.average_quality_score}점 / 경고 {quality.warning_count}건",
            recommendation=(
                "출처, 옵션 검수, 구매 판정 경고를 줄여 평균 품질 "
                "80점 이상으로 올리세요."
            ),
        )
    return BetaReadinessCheck(
        area="quality",
        label="품질 감사",
        status=CheckStatus.ok,
        metric=f"평균 {quality.average_quality_score}점 / 차단 0건",
        recommendation="품질 감사 기준은 공개 베타 기준을 충족했습니다.",
    )


def _launch_gate_check(
    *,
    area: str,
    label: str,
    status: CheckStatus,
    metric: str,
    recommendation: str,
) -> LaunchGateCheck:
    return LaunchGateCheck(
        area=area,
        label=label,
        status=status,
        metric=metric,
        recommendation=recommendation,
    )


def _launch_readiness_gate_status(score: float) -> CheckStatus:
    if score < 45:
        return CheckStatus.blocker
    if score < 70:
        return CheckStatus.warning
    return CheckStatus.ok


def _launch_backlog_gate_status(backlog: BetaBacklogSummary) -> CheckStatus:
    if backlog.overdue_count:
        return CheckStatus.blocker
    if backlog.blocker_count or backlog.due_soon_count:
        return CheckStatus.warning
    return CheckStatus.ok


def _launch_conversion_gate_status(metrics: OperationsMetrics) -> CheckStatus:
    if metrics.purchase_outcomes == 0 and metrics.feedback_count == 0:
        return CheckStatus.blocker
    if metrics.purchase_outcomes < 3 or metrics.purchase_conversion_rate < 0.25:
        return CheckStatus.warning
    return CheckStatus.ok


def _launch_delivery_gate_status(metrics: OperationsMetrics) -> CheckStatus:
    if metrics.alert_channels == 0:
        return CheckStatus.warning
    if metrics.completion_report_deliveries == 0 and metrics.sent_alert_deliveries == 0:
        return CheckStatus.warning
    if (
        metrics.failed_alert_deliveries > metrics.sent_alert_deliveries
        and metrics.sent_alert_deliveries
    ):
        return CheckStatus.warning
    return CheckStatus.ok


def _launch_gate_status_and_decision(
    checks: list[LaunchGateCheck],
    score: float,
) -> tuple[CheckStatus, str]:
    if any(check.status == CheckStatus.blocker for check in checks):
        return CheckStatus.blocker, "blocked"
    if score >= 85 and all(check.status == CheckStatus.ok for check in checks):
        return CheckStatus.ok, "go"
    if score >= 70:
        return CheckStatus.warning, "limited_beta"
    return CheckStatus.warning, "hold"


def _launch_gate_required_actions(
    checks: list[LaunchGateCheck],
    readiness: BetaReadinessDashboard,
    regression: OpsRegressionDashboard,
    learning: OpsLearningDashboard,
    backlog: BetaBacklogSummary,
) -> list[str]:
    actions = [
        check.recommendation
        for check in checks
        if check.status != CheckStatus.ok
    ]
    actions.extend(readiness.next_actions[:2])
    actions.extend(regression.next_actions[:2])
    actions.extend(learning.top_actions[:2])
    actions.extend(backlog.next_actions[:2])
    if not actions:
        actions.append("공개 배포 후 24시간 동안 품질 회귀와 구매 결과를 집중 모니터링하세요.")
    return _dedupe_strings(actions)[:8]


def _launch_gate_summary(
    decision: str,
    checks: list[LaunchGateCheck],
    score: float,
) -> str:
    blocker_count = sum(1 for check in checks if check.status == CheckStatus.blocker)
    warning_count = sum(1 for check in checks if check.status == CheckStatus.warning)
    if decision == "go":
        return f"출시 준비도 {score}점입니다. 핵심 게이트가 통과되어 공개 확대가 가능합니다."
    if decision == "limited_beta":
        return (
            f"출시 준비도 {score}점입니다. blocker는 없지만 warning {warning_count}건을 "
            "모니터링하며 제한 베타로 확대하세요."
        )
    if decision == "blocked":
        return (
            f"출시 준비도 {score}점입니다. blocker {blocker_count}건이 있어 공개 확대를 "
            "중단하고 필수 액션을 먼저 처리해야 합니다."
        )
    return (
        f"출시 준비도 {score}점입니다. warning {warning_count}건을 보강한 뒤 "
        "다시 출시 게이트를 확인하세요."
    )


def _launch_readiness_score(metrics: OperationsMetrics, quality: QualityDashboard) -> float:
    activation = min(100.0, metrics.analysis_runs * 10 + metrics.saved_reports * 12)
    sharing = min(100.0, metrics.shared_reports * 22 + metrics.public_share_views * 4)
    retention = min(100.0, metrics.alert_subscriptions * 25)
    feedback = min(
        100.0,
        metrics.feedback_count * 8
        + metrics.average_satisfaction * 8
        + metrics.purchase_intent_rate * 25,
    )
    outcome_signal = min(
        100.0,
        metrics.purchase_outcomes * 10
        + metrics.completed_purchase_outcomes * 18
        + metrics.purchase_conversion_rate * 30,
    )
    lead = min(100.0, metrics.beta_leads * 10)
    quality_score = max(
        0.0,
        metrics.average_quality_score
        - quality.blocker_count * 18
        - quality.warning_count * 1.5,
    )
    score = (
        activation * 0.18
        + sharing * 0.16
        + retention * 0.12
        + feedback * 0.12
        + outcome_signal * 0.06
        + lead * 0.12
        + quality_score * 0.24
    )
    return round(min(100.0, max(0.0, score)), 2)


def _readiness_label(score: float) -> str:
    if score >= 85:
        return "공개 확대 가능"
    if score >= 70:
        return "제한 베타 가능"
    if score >= 45:
        return "파일럿 보강 필요"
    return "출시 전 검증 부족"


def _referral_code(persona: str) -> str:
    prefix = "".join(ch for ch in persona.upper() if ch.isalnum())[:4] or "SPAI"
    return f"{prefix}-{uuid4().hex[:6].upper()}"


def _waitlist_priority_score(referred_signup_count: int, contact_consent: bool) -> int:
    consent_bonus = 10 if contact_consent else 0
    return min(100, 40 + referred_signup_count * 15 + consent_bonus)


def _waitlist_referral_summary(total: int, referred: int) -> str:
    if total == 0:
        return "아직 추천 대기열 가입이 없어 공개 전 공유 루프를 검증해야 합니다."
    if referred == 0:
        return f"추천 대기열 {total}명이 등록됐지만 초대 전환은 아직 없습니다."
    return f"추천 대기열 {total}명 중 {referred}명이 기존 추천 코드로 유입됐습니다."


def _waitlist_referral_next_actions(total: int, share_rate_hint: float) -> list[str]:
    actions: list[str] = []
    if total < 10:
        actions.append("공개 리포트와 온보딩 카드에 추천 대기열 CTA를 노출하세요.")
    if share_rate_hint < 0.2:
        actions.append("추천 코드 공유 문구와 혜택 메시지를 A/B 테스트하세요.")
    actions.append("상위 추천자에게 우선 초대와 팀 구매 인터뷰를 제안하세요.")
    return actions[:3]


def _default_channel_name(channel: str) -> str:
    labels = {
        "email": "이메일 알림",
        "webhook": "웹훅 알림",
        "sms": "문자 알림",
    }
    return labels.get(channel, channel)


def _default_channel_target(channel: str) -> str:
    if channel == "webhook":
        return "https://example.com/specpilot-alert-webhook"
    if channel == "sms":
        return "sms-outbox://specpilot"
    return "email-outbox://specpilot"


def _dispatch_status(
    channel: str,
    config: sqlite3.Row | None,
    retry_count: int,
    dry_run: bool,
    now: str,
) -> tuple[str, str, str | None]:
    if dry_run:
        return "dry_run", f"{channel} 채널 발송 리허설을 완료했습니다.", None
    if config is None:
        return (
            "failed",
            f"{channel} 채널 설정이 없어 발송하지 못했습니다.",
            _retry_at(now, 30),
        )
    if not bool(config["enabled"]):
        return (
            "failed",
            f"{channel} 채널이 비활성화되어 발송하지 못했습니다.",
            _retry_at(now, 60),
        )
    retry_limit = int(config["retry_limit"])
    if retry_count > retry_limit + 1:
        return "failed", f"{channel} 채널 재시도 한도를 초과했습니다.", None
    target = str(config["target"])
    if channel == "webhook" and not target.startswith(("http://", "https://")):
        return "failed", "웹훅 대상 URL이 올바르지 않습니다.", _retry_at(now, 30)
    return (
        "sent",
        f"{channel} 채널 outbox가 알림을 접수했습니다: {_mask_target(target)}",
        None,
    )


def _normalized_recipients(recipients: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for recipient in recipients:
        value = recipient.strip()
        key = value.lower()
        if value and key not in seen:
            normalized.append(value)
            seen.add(key)
    return normalized


def _completion_channel(
    requested_channel: str,
    *,
    template: sqlite3.Row | None,
    group: sqlite3.Row | None,
) -> str:
    if group is not None:
        return str(group["channel"]).strip().lower() or "email"
    if template is not None:
        return str(template["channel"]).strip().lower() or "email"
    return requested_channel.strip().lower() or "email"


def _completion_subject(template: sqlite3.Row | None) -> str:
    if template is None:
        return "SpecPilot AI 구매 리포트"
    return str(template["subject"]).strip() or "SpecPilot AI 구매 리포트"


def _completion_body(template: sqlite3.Row | None) -> str:
    if template is None:
        return (
            "{title}\n"
            "추천 1순위: {top_model_name}\n"
            "공개 리포트: {public_path}\n"
            "결제 전 옵션명, 배송비, 카드 혜택을 다시 확인해 주세요."
        )
    return str(template["body"]).strip() or "완료 리포트를 확인해 주세요: {public_path}"


def _completion_targets(
    request: CompletionReportBatchRequest | CompletionReportPreviewRequest,
    group: sqlite3.Row | None,
) -> list[tuple[str, bool]]:
    if group is None:
        return [(request.target.strip(), False)]
    recipients = _normalized_recipients(json.loads(group["recipients_json"]))
    unsubscribed = {
        item.lower()
        for item in _normalized_recipients(json.loads(group["unsubscribed_json"]))
    }
    return [(recipient, recipient.lower() in unsubscribed) for recipient in recipients]


def _render_completion_text(template: str, report: SavedReportSummary) -> str:
    public_path = f"/r/{report.share_token}" if report.share_token else "비공개 리포트"
    values = {
        "title": report.title,
        "top_model_name": report.top_model_name or "추천 후보 확인 필요",
        "final_pick_id": report.final_pick_id or "미정",
        "report_id": report.report_id,
        "trace_id": report.trace_id,
        "public_path": public_path,
    }
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{" + key + "}", value)
    return rendered


def _completion_engagement_type(event_type: str) -> str:
    normalized = event_type.strip().lower()
    if normalized in {"open", "opened"}:
        return "open"
    if normalized in {"click", "clicked"}:
        return "click"
    if normalized in {"share", "shared"}:
        return "share"
    if normalized in {"reply", "replied"}:
        return "reply"
    return "custom"


def _completion_provider_event_type(event_type: str) -> str:
    normalized = event_type.strip().lower()
    if normalized in {"delivered", "delivery", "sent", "accepted"}:
        return "delivered"
    if normalized in {"bounce", "bounced", "hard_bounce", "soft_bounce"}:
        return "bounced"
    if normalized in {"complaint", "complained", "spam", "spam_report"}:
        return "complained"
    if normalized in {"suppress", "suppressed", "unsubscribe", "unsubscribed"}:
        return "suppressed"
    if normalized in {"defer", "deferred", "retry", "delayed"}:
        return "deferred"
    if normalized in {"drop", "dropped", "rejected"}:
        return "dropped"
    return "custom"


def _completion_provider_delivery_status(event_type: str) -> str:
    if event_type == "delivered":
        return "sent"
    if event_type in {"bounced", "complained", "dropped"}:
        return "failed"
    if event_type == "suppressed":
        return "skipped"
    if event_type == "deferred":
        return "retry_scheduled"
    return "sent"


def _completion_provider_message(
    event: CompletionDeliveryProviderEvent,
    previous_message: str,
) -> str:
    message = (
        f"provider_webhook={event.provider_name}:{event.event_type} "
        f"status={event.delivery_status}"
    )
    if event.provider_message:
        message = f"{message} message={event.provider_message}"
    if previous_message:
        return f"{previous_message} | {message}"
    return message


def _completion_dispatch_status(
    *,
    channel: str,
    target: str,
    retry_count: int,
    dry_run: bool,
    now: str,
) -> tuple[str, str, str | None]:
    normalized_target = target.strip()
    if dry_run:
        return "dry_run", f"{channel} 완료 리포트 발송 리허설을 완료했습니다.", None
    if channel not in SUPPORTED_ALERT_CHANNELS:
        return (
            "failed",
            f"{channel} 완료 리포트 채널은 아직 지원하지 않습니다.",
            _retry_at(now, 60),
        )
    if not normalized_target:
        return "failed", "완료 리포트를 받을 대상이 비어 있습니다.", _retry_at(now, 30)
    if retry_count > 4:
        return "failed", f"{channel} 완료 리포트 재시도 한도를 초과했습니다.", None
    if channel == "webhook" and not normalized_target.startswith(("http://", "https://")):
        return "failed", "완료 리포트 웹훅 URL이 올바르지 않습니다.", _retry_at(now, 30)
    return (
        "sent",
        f"{channel} 완료 리포트 outbox가 {_mask_target(normalized_target)} 대상으로 접수했습니다.",
        None,
    )


def _completion_batch_status(
    *,
    selected_count: int,
    target_count: int,
    sent_count: int,
    failed_count: int,
    dry_run: bool,
) -> str:
    if dry_run:
        return "dry_run"
    if selected_count == 0:
        return "empty"
    if target_count == 0:
        return "failed"
    if failed_count and not sent_count:
        return "failed"
    if failed_count:
        return "partial"
    if sent_count == 0:
        return "skipped"
    return "sent"


def _observability_dispatch_status(
    export: ObservabilityExportRecord,
    *,
    retry_count: int,
    dry_run: bool,
    now: str,
) -> tuple[str, str, str | None]:
    destination = export.destination.strip().lower()
    if dry_run:
        return (
            "dry_run",
            f"{destination} observability exporter 리허설을 완료했습니다.",
            None,
        )
    if retry_count > 4:
        return "failed", f"{destination} exporter 재시도 한도를 초과했습니다.", None
    if not export.payload:
        return (
            "failed",
            "전송할 observability payload가 없어 export하지 못했습니다.",
            None,
        )
    if destination not in {"opentelemetry", "langsmith"}:
        return (
            "failed",
            f"{destination} exporter가 아직 설정되지 않았습니다.",
            _retry_at(now, 60),
        )
    return (
        "sent",
        (
            f"{destination} exporter outbox가 trace {export.trace_id} "
            f"span {export.span_count}개를 접수했습니다."
        ),
        None,
    )


def _growth_funnel_step(
    key: GrowthEventType,
    label: str,
    counts: dict[str, int],
    unique_counts: dict[str, int],
    baseline: int,
    *,
    warning_threshold: float,
    ok_threshold: float,
    recommendation: str,
) -> GrowthFunnelStep:
    event_count = counts.get(key.value, 0)
    conversion_rate = _event_rate(counts, key, baseline)
    status = CheckStatus.blocker
    if conversion_rate >= ok_threshold:
        status = CheckStatus.ok
    elif conversion_rate >= warning_threshold:
        status = CheckStatus.warning
    return GrowthFunnelStep(
        key=key,
        label=label,
        event_count=event_count,
        unique_traces=unique_counts.get(key.value, 0),
        conversion_rate=conversion_rate,
        status=status,
        recommendation=recommendation,
    )


def _launch_experiment_event_type(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"conversion", "converted", "click", "signup", "intent"}:
        return "conversion"
    return "impression"


def _launch_variant_status(impressions: int, conversion_rate: float) -> CheckStatus:
    if impressions < 5:
        return CheckStatus.blocker
    if conversion_rate >= 0.08:
        return CheckStatus.ok
    if conversion_rate >= 0.03:
        return CheckStatus.warning
    return CheckStatus.blocker


def _launch_variant_recommendation(
    status: CheckStatus,
    impressions: int,
    conversion_rate: float,
) -> str:
    if impressions < 5:
        return "표본이 부족합니다. 같은 채널에서 노출을 먼저 확보하세요."
    if status == CheckStatus.ok:
        return "승자 후보입니다. 같은 angle을 다음 채널에도 확장하세요."
    if conversion_rate > 0:
        return "카피의 proof point와 CTA를 더 구체적으로 바꿔 재검증하세요."
    return "전환이 없습니다. 문제 고통, 가격대, CTA 위치를 새 variant로 바꾸세요."


def _best_launch_variant(
    variants: list[LaunchExperimentVariant],
) -> LaunchExperimentVariant | None:
    eligible = [variant for variant in variants if variant.impressions > 0]
    if not eligible:
        return None
    return max(
        eligible,
        key=lambda item: (item.conversion_rate, item.conversions, item.impressions),
    )


def _launch_experiment_status(
    variants: list[LaunchExperimentVariant],
) -> CheckStatus:
    impressions = sum(variant.impressions for variant in variants)
    if impressions < 10:
        return CheckStatus.warning if impressions else CheckStatus.blocker
    if any(variant.status == CheckStatus.ok for variant in variants):
        return CheckStatus.ok
    if any(variant.conversions for variant in variants):
        return CheckStatus.warning
    return CheckStatus.blocker


def _launch_experiment_dashboard_status(
    experiment_count: int,
    total_impressions: int,
    conversion_rate: float,
) -> CheckStatus:
    if experiment_count == 0:
        return CheckStatus.blocker
    if total_impressions >= 40 and conversion_rate >= 0.06:
        return CheckStatus.ok
    if total_impressions >= 10 or conversion_rate > 0:
        return CheckStatus.warning
    return CheckStatus.blocker


def _launch_experiment_summary(
    experiment_count: int,
    total_impressions: int,
    total_conversions: int,
    conversion_rate: float,
) -> str:
    if not experiment_count:
        return "아직 출시 CTA 실험이 없습니다. launch-kit 문구를 실제 실험으로 전환하세요."
    return (
        f"출시 실험 {experiment_count}개에서 노출 {total_impressions}회, "
        f"전환 {total_conversions}건, 전환율 {round(conversion_rate * 100, 1)}%를 "
        "집계했습니다."
    )


def _recommended_launch_experiments(
    experiments: list[LaunchExperiment],
) -> list[LaunchExperiment]:
    return sorted(
        experiments,
        key=lambda item: (
            item.status == CheckStatus.ok,
            -sum(variant.impressions for variant in item.variants),
            item.updated_at,
        ),
    )[:3]


def _launch_experiment_next_actions(
    experiments: list[LaunchExperiment],
    total_impressions: int,
    conversion_rate: float,
) -> list[str]:
    if not experiments:
        return [
            "커뮤니티, 검색, 추천 대기열용 CTA 실험을 최소 2개 variant로 생성하세요.",
            "primary metric은 subscription_cta 또는 share_cta 중 하나로 고정하세요.",
        ]
    actions: list[str] = []
    if total_impressions < 40:
        actions.append("각 variant가 최소 20회 이상 노출되도록 채널별 배포량을 맞추세요.")
    if conversion_rate < 0.03:
        actions.append("문제 고통, 예산대, 결제 전 검수 proof를 CTA 문구에 직접 넣으세요.")
    for experiment in experiments:
        if experiment.status != CheckStatus.ok:
            actions.append(f"{experiment.name}: 표본 또는 전환이 부족한 variant를 재작성하세요.")
        if len(actions) >= 5:
            break
    if not actions:
        actions.append("승자 variant를 공개 유입 허브의 주 CTA와 SEO 페이지에 반영하세요.")
    return actions[:5]


def _score_status(score: float, *, warning: float, ok: float) -> CheckStatus:
    if score >= ok:
        return CheckStatus.ok
    if score >= warning:
        return CheckStatus.warning
    return CheckStatus.blocker


def _acquisition_surface(
    *,
    key: str,
    label: str,
    path: str,
    channel: str,
    score: float,
    primary_cta: str,
    proof: str,
    metric: str,
    next_action: str,
) -> PublicAcquisitionSurface:
    normalized_score = round(max(0, min(score, 100)), 1)
    return PublicAcquisitionSurface(
        key=key,
        label=label,
        path=path,
        channel=channel,
        status=_score_status(normalized_score, warning=55, ok=75),
        readiness_score=normalized_score,
        primary_cta=primary_cta,
        proof=proof,
        metric=metric,
        next_action=next_action,
    )


def _public_acquisition_surfaces(
    *,
    metrics: OperationsMetrics,
    growth: GrowthFunnelDashboard,
    referrals: WaitlistReferralDashboard,
    pricing: PricingDashboard,
    readiness: BetaReadinessDashboard,
) -> list[PublicAcquisitionSurface]:
    market_score = min(100.0, 62 + metrics.analysis_runs * 2 + metrics.growth_events * 1.5)
    return [
        _acquisition_surface(
            key="demo_gallery",
            label="공개 데모 갤러리",
            path="/#demo-gallery",
            channel="first_session",
            score=min(
                100.0,
                48 + metrics.analysis_runs * 5 + metrics.recommendation_card_clicks * 8,
            ),
            primary_cta="데모 적용 후 분석 실행",
            proof=(
                f"분석 {metrics.analysis_runs}건, "
                f"추천 클릭 {metrics.recommendation_card_clicks}건"
            ),
            metric=f"추천 클릭률 {round(growth.activation_rate * 100)}%",
            next_action="첫 화면 데모 preset과 분석 버튼을 계속 붙여 빈 폼 이탈을 줄이세요.",
        ),
        _acquisition_surface(
            key="market_desktop",
            label="데스크톱 PC SEO 리포트",
            path="/market/desktop-pc",
            channel="search",
            score=market_score,
            primary_cta="데스크톱 조건 분석",
            proof="월간 데스크톱 후보, 가격 구간, 리스크 체크리스트 공개",
            metric=f"성장 이벤트 {metrics.growth_events}건",
            next_action="커뮤니티 글과 검색 유입을 데스크톱 공개 리포트로 모으세요.",
        ),
        _acquisition_surface(
            key="market_laptop",
            label="노트북 SEO 리포트",
            path="/market/laptop",
            channel="search",
            score=market_score,
            primary_cta="노트북 조건 분석",
            proof="월간 노트북 후보, 휴대성/발열/외장 GPU 리스크 공개",
            metric=f"공개 조회 {metrics.public_share_views}회",
            next_action="노트북 구매 키워드 유입은 공개 리포트 CTA와 연결하세요.",
        ),
        _acquisition_surface(
            key="public_report",
            label="공개 공유 리포트",
            path="/r/{share_token}",
            channel="share",
            score=min(
                100.0,
                metrics.shared_reports * 18
                + metrics.public_share_views * 5
                + metrics.share_cta_clicks * 8
                + growth.share_rate * 40,
            ),
            primary_cta="리포트 공유",
            proof=f"공유 리포트 {metrics.shared_reports}개, 조회 {metrics.public_share_views}회",
            metric=f"공유 CTA {round(growth.share_rate * 100)}%",
            next_action=(
                "분석 직후 공유 자산을 복사하게 해 "
                "가족/커뮤니티 검토 루프를 짧게 만드세요."
            ),
        ),
        _acquisition_surface(
            key="referral_waitlist",
            label="추천 대기열",
            path="/#referrals",
            channel="referral",
            score=min(
                100.0,
                referrals.total_referrals * 14
                + referrals.referred_signup_count * 22
                + referrals.share_rate_hint * 35,
            ),
            primary_cta="초대 링크 만들기",
            proof=(
                f"대기열 {referrals.total_referrals}명, "
                f"추천 유입 {referrals.referred_signup_count}명"
            ),
            metric=f"추천 유입률 {round(referrals.share_rate_hint * 100)}%",
            next_action="공유 리포트 하단에 추천 코드 CTA를 붙여 좋은 반응을 초대로 전환하세요.",
        ),
        _acquisition_surface(
            key="trust_center",
            label="공개 Trust Center",
            path="/#trust-center",
            channel="trust",
            score=min(
                100.0,
                readiness.launch_readiness_score * 0.8
                + metrics.average_quality_score * 0.2,
            ),
            primary_cta="신뢰 기준 확인",
            proof=(
                f"readiness {readiness.launch_readiness_score}점, "
                f"품질 {metrics.average_quality_score}점"
            ),
            metric=readiness.readiness_label,
            next_action="제휴 고지, 출처 검수, 개인정보 기준을 공유 리포트와 함께 노출하세요.",
        ),
        _acquisition_surface(
            key="pricing_interest",
            label="Premium/Team 전환",
            path="/#pricing",
            channel="monetization",
            score=min(
                100.0,
                pricing.intent_count * 18
                + (pricing.premium_intent_count + pricing.team_intent_count) * 14
                + min(pricing.estimated_mrr_krw / 12_000, 30),
            ),
            primary_cta="요금제 관심 등록",
            proof=f"요금제 관심 {pricing.intent_count}건, 예상 MRR {pricing.estimated_mrr_krw:,}원",
            metric=pricing.top_plan_name or "요금제 수요 검증 전",
            next_action="반복 구매/팀 구매 persona에는 Team 구매 보조 CTA를 우선 노출하세요.",
        ),
    ]


def _public_acquisition_headline(status: CheckStatus, launch_score: float) -> str:
    if status == CheckStatus.ok:
        return f"공개 유입 허브 {launch_score}점, 유입 확대를 시작할 수 있습니다."
    if status == CheckStatus.warning:
        return f"공개 유입 허브 {launch_score}점, 일부 표면 보강 후 확대하세요."
    return f"공개 유입 허브 {launch_score}점, 첫 유입 표면부터 확보해야 합니다."


def _public_acquisition_summary(
    metrics: OperationsMetrics,
    growth: GrowthFunnelDashboard,
    referrals: WaitlistReferralDashboard,
    pricing: PricingDashboard,
) -> str:
    return (
        f"분석 {metrics.analysis_runs}건, 공유 조회 {metrics.public_share_views}회, "
        f"공유 CTA {round(growth.share_rate * 100)}%, 추천 대기열 "
        f"{referrals.total_referrals}명, 요금제 관심 {pricing.intent_count}건을 "
        "공개 표면별로 묶었습니다."
    )


def _public_acquisition_channel_actions(
    surfaces: list[PublicAcquisitionSurface],
) -> list[str]:
    by_channel: dict[str, PublicAcquisitionSurface] = {}
    for surface in sorted(surfaces, key=lambda item: item.readiness_score):
        by_channel.setdefault(surface.channel, surface)
    return [
        f"{surface.channel}: {surface.label} - {surface.next_action}"
        for surface in by_channel.values()
    ][:6]


def _public_acquisition_next_actions(
    surfaces: list[PublicAcquisitionSurface],
    growth: GrowthFunnelDashboard,
    referrals: WaitlistReferralDashboard,
) -> list[str]:
    actions = [
        surface.next_action
        for surface in sorted(surfaces, key=lambda item: item.readiness_score)
        if surface.status != CheckStatus.ok
    ][:4]
    actions.extend(growth.next_actions[:1])
    actions.extend(referrals.next_actions[:1])
    deduped: list[str] = []
    for action in actions:
        if action and action not in deduped:
            deduped.append(action)
    if not deduped:
        deduped.append("모든 공개 표면이 안정적입니다. 검색/커뮤니티 트래픽을 더 배정하세요.")
    return deduped[:6]


def _retention_signal(
    *,
    key: str,
    label: str,
    score: float,
    metric: str,
    insight: str,
    next_action: str,
) -> RetentionSignal:
    normalized_score = round(max(0, min(score, 100)), 1)
    return RetentionSignal(
        key=key,
        label=label,
        status=_score_status(normalized_score, warning=55, ok=75),
        score=normalized_score,
        metric=metric,
        insight=insight,
        next_action=next_action,
    )


def _public_proof_asset(
    *,
    key: str,
    label: str,
    score: float,
    metric: str,
    proof: str,
    public_path: str,
    cta_label: str,
    next_action: str,
) -> PublicProofAsset:
    return PublicProofAsset(
        key=key,
        label=label,
        status=_score_status(score, warning=45, ok=75),
        metric=metric,
        proof=proof,
        public_path=public_path,
        cta_label=cta_label,
        next_action=next_action,
    )


def _public_proof_assets(
    metrics: OperationsMetrics,
    acquisition: PublicAcquisitionHub,
    experiments: LaunchExperimentDashboard,
) -> list[PublicProofAsset]:
    feedback_score = min(
        100.0,
        metrics.feedback_count * 10
        + metrics.average_satisfaction * 12
        + metrics.purchase_intent_rate * 35,
    )
    market_score = min(
        100.0,
        metrics.analysis_runs * 2
        + metrics.saved_reports * 5
        + metrics.public_share_views * 3,
    )
    experiment_score = min(
        100.0,
        experiments.total_impressions * 1.2
        + experiments.total_conversions * 15
        + experiments.conversion_rate * 120,
    )
    return [
        _public_proof_asset(
            key="trust_center",
            label="공개 신뢰 기준",
            score=85,
            metric="Trust Center 공개",
            proof="추천 공정성, 출처 검수, 개인정보 최소화, 사람 검수 기준을 공개합니다.",
            public_path="/policy/trust-center",
            cta_label="신뢰 기준 보기",
            next_action="Trust Center 링크를 랜딩 상단과 공개 리포트 하단에 고정하세요.",
        ),
        _public_proof_asset(
            key="market_reports",
            label="공개 시장 리포트",
            score=market_score,
            metric=(
                f"분석 {metrics.analysis_runs}건 / "
                f"저장 리포트 {metrics.saved_reports}건"
            ),
            proof="데스크톱 PC와 노트북 추천 픽, 가격 구간, 리스크 신호를 공개 리포트화합니다.",
            public_path="/market/desktop-pc",
            cta_label="시장 리포트 보기",
            next_action="공개 카테고리 리포트에 현재 승자 CTA를 연결하세요.",
        ),
        _public_proof_asset(
            key="share_review",
            label="공유 검토 흐름",
            score=min(100.0, metrics.shared_reports * 18 + metrics.public_share_views * 8),
            metric=(
                f"공유 리포트 {metrics.shared_reports}개 / "
                f"공개 조회 {metrics.public_share_views}회"
            ),
            proof="공개 토큰 리포트로 가족, 동료, 커뮤니티가 같은 근거를 검토할 수 있습니다.",
            public_path="/r/{share_token}",
            cta_label="공유 리포트 열기",
            next_action="공유 리포트에 검토 질문과 가격 알림 CTA를 같이 배치하세요.",
        ),
        _public_proof_asset(
            key="buyer_feedback",
            label="구매자 피드백",
            score=feedback_score,
            metric=(
                f"피드백 {metrics.feedback_count}건 / "
                f"만족도 {metrics.average_satisfaction}점 / "
                f"구매 의향 {round(metrics.purchase_intent_rate * 100)}%"
            ),
            proof=(
                "추천 만족도, 구매 의향, 개선 요청을 원문 연락처 없이 "
                "마스킹해 학습 신호로 씁니다."
            ),
            public_path="/#conversion",
            cta_label="피드백 남기기",
            next_action="만족도 4점 이상 피드백을 공개 proof 문구로 재가공하세요.",
        ),
        _public_proof_asset(
            key="cta_experiment",
            label="CTA 실험 검증",
            score=experiment_score,
            metric=(
                f"노출 {experiments.total_impressions}회 / "
                f"전환 {experiments.total_conversions}건 / "
                f"전환율 {round(experiments.conversion_rate * 100, 1)}%"
            ),
            proof="launch-kit 카피를 실제 variant 노출과 전환으로 검증해 승자 후보를 고릅니다.",
            public_path="/#launch-experiments",
            cta_label="실험 결과 보기",
            next_action="승자 CTA를 공개 유입 허브의 primary CTA와 SEO 페이지에 반영하세요.",
        ),
        _public_proof_asset(
            key="public_surfaces",
            label="공개 유입 표면",
            score=acquisition.launch_score,
            metric=f"유입 허브 {round(acquisition.launch_score)}점",
            proof=(
                "데모, SEO 리포트, 공유 리포트, 추천 대기열, "
                "Trust Center 표면을 함께 관리합니다."
            ),
            public_path="/#acquisition-hub",
            cta_label="유입 허브 보기",
            next_action="점수가 낮은 공개 표면부터 채널 액션을 완료하세요.",
        ),
    ]


def _public_proof_score(
    metrics: OperationsMetrics,
    proof_assets: list[PublicProofAsset],
    experiments: LaunchExperimentDashboard,
) -> float:
    asset_score = sum(_status_score(asset.status) for asset in proof_assets) / max(
        len(proof_assets),
        1,
    )
    signal_bonus = min(
        12.0,
        metrics.public_share_views * 0.8
        + metrics.feedback_count
        + experiments.total_conversions * 1.5,
    )
    return round(min(100.0, asset_score + signal_bonus), 1)


def _status_score(status: CheckStatus) -> float:
    if status == CheckStatus.ok:
        return 82.0
    if status == CheckStatus.warning:
        return 58.0
    return 28.0


def _public_proof_headline(status: CheckStatus, score: float) -> str:
    if status == CheckStatus.ok:
        return f"공개 검증 허브 {score}점, 바로 신뢰 proof로 밀 수 있습니다."
    if status == CheckStatus.warning:
        return f"공개 검증 허브 {score}점, proof는 있으나 표본을 더 쌓아야 합니다."
    return f"공개 검증 허브 {score}점, 신뢰 proof를 먼저 만들어야 합니다."


def _public_proof_summary(
    metrics: OperationsMetrics,
    proof_assets: list[PublicProofAsset],
) -> str:
    ok_assets = sum(1 for asset in proof_assets if asset.status == CheckStatus.ok)
    return (
        f"신뢰/시장/공유/피드백/실험/유입 증거 {len(proof_assets)}개 중 "
        f"{ok_assets}개가 공개 proof로 사용 가능합니다. 공개 조회 "
        f"{metrics.public_share_views}회, 피드백 {metrics.feedback_count}건을 함께 반영했습니다."
    )


def _public_proof_strip(
    metrics: OperationsMetrics,
    experiments: LaunchExperimentDashboard,
) -> list[str]:
    strip = [
        "제휴 여부와 추천 순위를 분리합니다",
        "가격 출처, 수집 시각, 캐시 TTL을 공개합니다",
        "공개 리포트는 토큰으로 격리됩니다",
        "연락처 원문 없이 피드백을 학습 신호로 씁니다",
    ]
    if metrics.public_share_views:
        strip.insert(0, f"공개 공유 리포트 {metrics.public_share_views}회 조회")
    if metrics.feedback_count:
        strip.insert(
            0,
            f"구매자 피드백 {metrics.feedback_count}건, 만족도 {metrics.average_satisfaction}점",
        )
    if experiments.total_conversions:
        strip.insert(0, f"CTA 실험 전환 {experiments.total_conversions}건 검증")
    return list(dict.fromkeys(strip))[:6]


def _public_evidence_kit(
    metrics: OperationsMetrics,
    proof_assets: list[PublicProofAsset],
) -> list[PublicProofEvidence]:
    asset_status = {asset.key: asset.status for asset in proof_assets}
    return [
        PublicProofEvidence(
            title="추천 공정성 공개",
            status=CheckStatus.ok,
            audience="첫 방문자",
            proof=(
                "제휴 링크 여부와 추천 점수는 분리하고, 목적 적합도/가격/호환성/"
                "리뷰 신뢰도/구매 안정성 기준을 공개합니다."
            ),
            source_path="/policy/trust-center",
            reuse_hint="랜딩 hero 하단 proof strip과 공개 리포트 하단 신뢰 문구로 재사용",
        ),
        PublicProofEvidence(
            title="시장 리포트형 시작점",
            status=asset_status.get("market_reports", CheckStatus.blocker),
            audience="검색 유입 사용자",
            proof=(
                "데스크톱 PC와 노트북 카테고리별 예산 구간, 추천 픽, 리스크 신호, "
                "구매 전 체크리스트를 공개 페이지로 제공합니다."
            ),
            source_path="/market/desktop-pc",
            reuse_hint="SEO 페이지와 커뮤니티 답변의 첫 CTA로 연결",
        ),
        PublicProofEvidence(
            title="공유 검토 루프",
            status=asset_status.get("share_review", CheckStatus.blocker),
            audience="가족/동료 검토 사용자",
            proof=(
                "저장 리포트를 읽기 전용 공개 토큰으로 바꿔 같은 근거와 구매 전 "
                "질문을 함께 검토하게 합니다."
            ),
            source_path="/r/{share_token}",
            reuse_hint="분석 완료 화면의 공유 CTA와 커뮤니티 검토 flow에 배치",
        ),
        PublicProofEvidence(
            title="실구매 실패 방어선",
            status=CheckStatus.ok
            if metrics.checkout_reviews or metrics.source_monitors
            else CheckStatus.warning,
            audience="구매 직전 사용자",
            proof=(
                "상품 URL 수집, 가격/배송/재고/모델명 검수, 결제 전 옵션 확인, "
                "목표가 알림으로 실제 구매 실패를 줄입니다."
            ),
            source_path="/#source-check",
            reuse_hint="가격 대기/결제 전 검수 섹션의 신뢰 근거로 노출",
        ),
    ]


def _public_proof_metric_cards(
    metrics: OperationsMetrics,
    experiments: LaunchExperimentDashboard,
) -> dict[str, int | float | str]:
    return {
        "analysis_runs": metrics.analysis_runs,
        "shared_reports": metrics.shared_reports,
        "public_share_views": metrics.public_share_views,
        "feedback_count": metrics.feedback_count,
        "average_satisfaction": metrics.average_satisfaction,
        "purchase_intent_rate": f"{round(metrics.purchase_intent_rate * 100)}%",
        "launch_experiment_conversions": experiments.total_conversions,
        "launch_experiment_rate": f"{round(experiments.conversion_rate * 100, 1)}%",
    }


def _public_proof_badges(metrics: OperationsMetrics) -> list[str]:
    badges = [
        "제휴 여부와 추천 순위 분리",
        "출처 신뢰도와 캐시 TTL 공개",
        "공개 리포트 토큰 격리",
        "연락처 원문 대신 마스킹 저장",
    ]
    if metrics.purchase_outcomes:
        badges.append("실제 구매 결과 학습 루프")
    if metrics.checkout_ready_reviews or metrics.checkout_blocked_reviews:
        badges.append("결제 전 옵션/금액 검수")
    return badges


def _public_objection_answers(
    metrics: OperationsMetrics,
) -> list[PublicObjectionAnswer]:
    return [
        PublicObjectionAnswer(
            question="최저가 광고 링크만 밀어주는 서비스인가요?",
            answer=(
                "아닙니다. 추천 순위는 목적 적합도, 가격, 호환성, 리뷰 신뢰도, "
                "구매 안정성으로 계산하고 제휴 링크 여부는 분리합니다."
            ),
            evidence=[
                "제휴/비제휴 구매 링크 governance",
                "추천 공정성 Trust Center",
            ],
        ),
        PublicObjectionAnswer(
            question="가격 정보가 오래되면 어떻게 하나요?",
            answer=(
                "가격 캐시 TTL, 수집 시각, 출처 링크, 목표가 알림, URL 모니터를 "
                "함께 제공해 재확인 흐름을 유지합니다."
            ),
            evidence=[
                f"가격 알림 {metrics.alert_subscriptions}개",
                f"소스 모니터 {metrics.source_monitors}개",
            ],
        ),
        PublicObjectionAnswer(
            question="실제 구매 실패를 줄이는 근거가 있나요?",
            answer=(
                "결제 전 검수, 구매 결과 추적, 학습 인사이트, 공개 공유 검토를 "
                "닫힌 루프로 묶어 다음 추천 품질에 반영합니다."
            ),
            evidence=[
                f"결제 검수 {metrics.checkout_reviews}건",
                f"구매 결과 {metrics.purchase_outcomes}건",
            ],
        ),
    ]


def _public_proof_cta_cards(
    acquisition: PublicAcquisitionHub,
    experiments: LaunchExperimentDashboard,
) -> list[str]:
    cards = [
        acquisition.primary_cta,
        "내 예산과 용도에 맞춰 바로 분석하기",
        "Trust Center에서 추천 기준 확인하기",
    ]
    if experiments.best_variant_label:
        cards.insert(0, f"검증된 CTA 적용: {experiments.best_variant_label}")
    return list(dict.fromkeys(cards))[:5]


def _public_proof_next_actions(
    status: CheckStatus,
    proof_assets: list[PublicProofAsset],
    experiments: LaunchExperimentDashboard,
) -> list[str]:
    actions = [
        asset.next_action for asset in proof_assets if asset.status != CheckStatus.ok
    ][:4]
    if experiments.best_variant_label:
        actions.insert(
            0,
            f"{experiments.best_variant_label} CTA를 랜딩 hero와 공개 리포트 CTA로 승격하세요.",
        )
    if status == CheckStatus.blocker:
        actions.append("피드백, 공유 조회, CTA 실험 표본을 먼저 만들어 공개 proof를 보강하세요.")
    if not actions:
        actions.append("공개 검증 허브 지표를 랜딩 상단 proof strip으로 노출하세요.")
    return list(dict.fromkeys(actions))[:6]


def _retention_signals(
    metrics: OperationsMetrics,
    board: PurchaseDecisionBoard,
) -> list[RetentionSignal]:
    saved = max(metrics.saved_reports, 1)
    report_count = max(board.report_count, 1)
    delivery_engagements = metrics.completion_delivery_opens + metrics.completion_delivery_clicks
    return [
        _retention_signal(
            key="saved_to_alert",
            label="저장 리포트 -> 가격 알림",
            score=min(100.0, (metrics.alert_subscriptions / saved) * 100),
            metric=f"{metrics.alert_subscriptions}개 알림 / 저장 {metrics.saved_reports}건",
            insight="가격 대기 사용자를 목표가 알림으로 붙잡는 축입니다.",
            next_action="가격 대기 판정 리포트에는 목표가 알림 CTA를 상단에 고정하세요.",
        ),
        _retention_signal(
            key="share_revisit",
            label="공유 리포트 재방문",
            score=min(100.0, metrics.public_share_views * 8 + metrics.share_cta_clicks * 12),
            metric=(
                f"공개 조회 {metrics.public_share_views}회 / "
                f"공유 CTA {metrics.share_cta_clicks}건"
            ),
            insight="가족, 동료, 커뮤니티 검토가 재방문으로 이어지는지 보는 축입니다.",
            next_action="공유 리포트 하단에 가격 알림과 결제 전 검수 CTA를 함께 배치하세요.",
        ),
        _retention_signal(
            key="decision_followup",
            label="구매 보드 후속 처리",
            score=min(
                100.0,
                ((report_count - board.missing_outcome_count) / report_count) * 100,
            ),
            metric=(
                f"리포트 {board.report_count}건 / "
                f"구매 결과 미기록 {board.missing_outcome_count}건"
            ),
            insight="저장 리포트가 실제 구매 결과까지 닫혔는지 보는 축입니다.",
            next_action=(
                "구매 가능/가격 대기 리포트에는 "
                "24시간 후 구매 결과 회수 액션을 예약하세요."
            ),
        ),
        _retention_signal(
            key="advisor_loop",
            label="저장 리포트 상담 루프",
            score=min(
                100.0,
                metrics.report_advisor_answers * 22
                + max(0, metrics.report_advisor_warning_answers) * 8,
            ),
            metric=(
                f"상담 {metrics.report_advisor_answers}건 / "
                f"주의 답변 {metrics.report_advisor_warning_answers}건"
            ),
            insight="정적 리포트가 결제 전 대화형 상담으로 이어지는지 보는 축입니다.",
            next_action="경고 답변이 있는 리포트는 결제 전 검수 또는 판매자 질문으로 연결하세요.",
        ),
        _retention_signal(
            key="purchase_learning",
            label="구매 결과 학습",
            score=min(
                100.0,
                metrics.purchase_outcomes * 16
                + metrics.completed_purchase_outcomes * 18
                - metrics.returned_purchase_outcomes * 12,
            ),
            metric=(
                f"구매 결과 {metrics.purchase_outcomes}건 / "
                f"전환율 {round(metrics.purchase_conversion_rate * 100)}%"
            ),
            insight="실제 구매/이탈/반품이 다음 추천 품질로 돌아오는 축입니다.",
            next_action=(
                "구매 결과가 없는 저장 리포트부터 회수하고 "
                "반품 신호는 학습 인사이트로 보내세요."
            ),
        ),
        _retention_signal(
            key="delivery_engagement",
            label="완료 리포트/알림 engagement",
            score=min(
                100.0,
                metrics.sent_alert_deliveries * 12
                + delivery_engagements * 14
                - metrics.failed_alert_deliveries * 8,
            ),
            metric=(
                f"알림 발송 {metrics.sent_alert_deliveries}건 / "
                f"열람+클릭 {delivery_engagements}건"
            ),
            insight="제품이 사용자를 다시 불러오는 메시지를 실제로 전달하는 축입니다.",
            next_action=(
                "발송 실패가 있으면 채널 설정을 먼저 고치고, "
                "성공 채널에는 완료 리포트를 붙이세요."
            ),
        ),
    ]


def _retention_metric_cards(
    metrics: OperationsMetrics,
    board: PurchaseDecisionBoard,
    active_alerts: int,
) -> dict[str, int | float | str]:
    return {
        "saved_reports": metrics.saved_reports,
        "active_alerts": active_alerts,
        "public_share_views": metrics.public_share_views,
        "missing_outcomes": board.missing_outcome_count,
        "purchase_conversion_rate": f"{round(metrics.purchase_conversion_rate * 100)}%",
        "sent_alert_deliveries": metrics.sent_alert_deliveries,
        "completion_engagements": (
            metrics.completion_delivery_opens + metrics.completion_delivery_clicks
        ),
        "ready_value_krw": board.total_ready_value_krw,
    }


def _retention_headline(status: CheckStatus, score: float) -> str:
    if status == CheckStatus.ok:
        return f"리텐션 허브 {score}점, 재방문 루프가 작동하고 있습니다."
    if status == CheckStatus.warning:
        return f"리텐션 허브 {score}점, 알림과 구매 결과 회수를 보강하세요."
    return f"리텐션 허브 {score}점, 첫 재참여 루프를 먼저 만들어야 합니다."


def _retention_summary(
    metrics: OperationsMetrics,
    board: PurchaseDecisionBoard,
    alerts: list[AlertSubscription],
) -> str:
    return (
        f"저장 리포트 {metrics.saved_reports}건, 활성 알림 {len(alerts)}개, "
        f"공유 조회 {metrics.public_share_views}회, 구매 결과 "
        f"{metrics.purchase_outcomes}건, 미기록 후속 처리 "
        f"{board.missing_outcome_count}건을 재참여 흐름으로 묶었습니다."
    )


def _retention_plays(
    metrics: OperationsMetrics,
    board: PurchaseDecisionBoard,
    advisors: list[ReportAdvisorAnswer],
    outcomes: list[PurchaseOutcome],
    alerts: list[AlertSubscription],
) -> list[RetentionPlay]:
    plays = [
        RetentionPlay(
            play_id="price_wait_alert",
            label="가격 대기 리포트 목표가 알림 전환",
            audience="가격 대기 판정 또는 목표가 차이가 있는 저장 리포트 사용자",
            trigger="price_wait_count > 0 또는 alert_subscriptions 부족",
            channel="email/webhook",
            cta_label="목표가 알림 켜기",
            cta_target="#price-alert",
            expected_impact="즉시 구매하지 않는 사용자를 목표가 도달 시점에 다시 부릅니다.",
            evidence=[
                f"가격 대기 {board.price_wait_count}건",
                f"활성 알림 {len(alerts)}개",
            ],
        ),
        RetentionPlay(
            play_id="outcome_capture",
            label="구매 결과 회수",
            audience="저장 리포트는 있지만 구매 결과가 없는 사용자",
            trigger="missing_outcome_count > 0",
            channel="in_app/completion_report",
            cta_label="구매 결과 남기기",
            cta_target="#purchase-outcome",
            expected_impact="추천이 실제 구매로 이어졌는지 닫힌 루프로 학습합니다.",
            evidence=[
                f"구매 결과 미기록 {board.missing_outcome_count}건",
                f"구매 결과 {metrics.purchase_outcomes}건",
            ],
        ),
        RetentionPlay(
            play_id="advisor_rescue",
            label="결제 전 상담 구조",
            audience="경고 상담 답변 또는 검수 차단이 있는 사용자",
            trigger="report_advisor_warning_answers 또는 checkout_blocked_count",
            channel="in_app",
            cta_label="구매 상담 이어가기",
            cta_target="#advisor",
            expected_impact="구매 직전 불확실성을 상담과 검수로 흡수합니다.",
            evidence=[
                f"주의 상담 {metrics.report_advisor_warning_answers}건",
                f"검수 차단 {board.checkout_blocked_count}건",
            ],
        ),
        RetentionPlay(
            play_id="share_reengagement",
            label="공유 리포트 재방문 CTA",
            audience="공유 리포트를 열람한 가족/동료/커뮤니티 검토자",
            trigger="public_share_views 또는 share_cta_clicks",
            channel="public_report",
            cta_label="내 조건으로 다시 분석",
            cta_target="/r/{share_token}",
            expected_impact="공유받은 사람을 새 분석과 추천 대기열로 전환합니다.",
            evidence=[
                f"공개 조회 {metrics.public_share_views}회",
                f"공유 CTA {metrics.share_cta_clicks}건",
            ],
        ),
        RetentionPlay(
            play_id="completion_report_followup",
            label="완료 리포트 후속 발송",
            audience="구매 완료 또는 지연 결과가 기록된 사용자",
            trigger="purchase_outcomes 또는 completion_report_deliveries",
            channel="email/webhook/sms",
            cta_label="완료 리포트 보내기",
            cta_target="#completion-reports",
            expected_impact="구매 후 만족도와 반품 신호를 회수해 다음 추천 품질을 높입니다.",
            evidence=[
                f"완료 리포트 발송 {metrics.completion_report_deliveries}건",
                f"최근 구매 결과 {len(outcomes)}건",
            ],
        ),
    ]
    if advisors:
        plays[2].evidence.append(f"최근 상담: {advisors[0].question[:36]}")
    if outcomes:
        plays[4].evidence.append(f"최근 결과: {outcomes[0].status.value}")
    return plays


def _retention_next_actions(
    signals: list[RetentionSignal],
    board: PurchaseDecisionBoard,
) -> list[str]:
    actions = [
        signal.next_action
        for signal in sorted(signals, key=lambda item: item.score)
        if signal.status != CheckStatus.ok
    ][:4]
    actions.extend(board.next_actions[:2])
    deduped: list[str] = []
    for action in actions:
        if action and action not in deduped:
            deduped.append(action)
    if not deduped:
        deduped.append("리텐션 루프가 안정적입니다. 완료 리포트와 추천 대기열 CTA를 확대하세요.")
    return deduped[:6]


def _public_report_conversion_cta(
    *,
    share_token: str,
    title: str,
    top_model_name: str | None,
) -> PublicReportConversionCta:
    report_ref = share_token.replace("share_", "")[:10].upper()
    model_label = top_model_name or "공유된 추천 후보"
    return PublicReportConversionCta(
        headline="이 리포트를 내 조건으로 다시 검증하세요",
        body=(
            f"{model_label} 리포트를 공유받았다면 예산, 용도, 필수 조건을 바꿔 "
            "내 상황에 맞는 TOP 3와 구매 전 체크리스트를 다시 받을 수 있습니다."
        ),
        primary_label="내 조건으로 분석 시작",
        primary_path=f"/?source=public-report&report={share_token}#analysis",
        secondary_label="공개 베타 대기열 등록",
        secondary_path=f"/join?source=public-report&report={share_token}",
        report_ref=report_ref,
        proof_points=[
            "공유 리포트의 가격, 호환성, 리뷰 리스크 구조를 그대로 재사용",
            "가입 후 본인 추천 코드를 발급해 초대 링크로 다시 확산",
            "결제 전 옵션명, 배송비, 카드 혜택 확인 체크리스트 제공",
        ],
        next_actions=[
            f"{title}를 내 예산과 구매 시점으로 다시 분석",
            "대기열에 등록하고 새 추천 코드로 주변 구매자를 초대",
            "구매 직전 판매 페이지 옵션명과 최종 결제 금액 재확인",
        ],
    )


def _build_report_share_assets(report: SavedReportDetail) -> ReportShareAssets:
    purchase = report.response.report
    criteria = report.response.criteria
    top = purchase.top_recommendations[0] if purchase.top_recommendations else None
    decision = purchase.purchase_decision
    brief = purchase.share_brief
    top_model = report.top_model_name or (top.product.model_name if top else "추천 후보")
    price = top.price.effective_price_krw if top else None
    public_path = f"/r/{report.share_token}" if report.share_token else None
    public_label = public_path or "공개 공유 링크 생성 후 자동 입력"
    verdict = decision.label if decision else "구매 검토 필요"
    confidence = round(decision.confidence) if decision else 0
    reasons = brief.key_reasons if brief else []
    watchouts = brief.watchouts if brief else []
    reviewer_questions = brief.reviewer_questions if brief else []
    primary_reason = reasons[0] if reasons else (top.fit_summary if top else purchase.summary)
    primary_watchout = (
        watchouts[0]
        if watchouts
        else "결제 전 옵션명, 배송비, 카드 혜택을 다시 확인하세요."
    )
    category_label = "노트북" if criteria.category == Category.laptop else "데스크톱 PC"
    budget_label = f"{criteria.budget_krw:,}원" if criteria.budget_krw else "예산 미정"
    price_label = f"{price:,}원" if price is not None else "가격 확인 필요"
    headline = f"{category_label} 구매 후보는 {top_model}입니다"
    subheadline = (
        f"{verdict} · 확신도 {confidence}점 · 실구매가 {price_label}. "
        f"{primary_reason}"
    )
    og_title = f"{top_model} 구매 검토 리포트"
    og_description = _clamp_text(
        f"{verdict}: {primary_reason} 결제 전 확인: {primary_watchout}",
        155,
    )
    visual_card_text = [
        "SpecPilot AI 구매 검토",
        f"추천: {top_model}",
        f"판정: {verdict}",
        f"실구매가: {price_label}",
    ]
    hashtags = _dedupe_strings(
        [
            "#SpecPilotAI",
            "#컴퓨터구매",
            "#노트북구매" if criteria.category == Category.laptop else "#PC견적",
            "#구매검토",
            "#가격비교",
        ]
    )
    variants = [
        _share_asset_variant(
            channel="kakao",
            label="카카오톡 공유",
            headline=headline,
            body=(
                f"{top_model}으로 {category_label} 구매 검토 리포트를 만들었어요. "
                f"{verdict}, 실구매가 {price_label} 기준이고 "
                "결제 전 체크포인트도 같이 정리했습니다."
            ),
            cta="공개 리포트 보기",
            public_label=public_label,
        ),
        _share_asset_variant(
            channel="community",
            label="커뮤니티 검토 요청",
            headline=f"{category_label} 구매 전 검토 부탁드립니다",
            body=(
                f"예산 {budget_label}, 용도는 {criteria.purpose}입니다. "
                f"SpecPilot AI가 {top_model}을 1순위로 추천했고 판정은 {verdict}입니다. "
                f"핵심 근거는 {primary_reason}이고, 우려 지점은 {primary_watchout}입니다."
            ),
            cta="다른 분들 의견도 받고 싶습니다",
            public_label=public_label,
        ),
        _share_asset_variant(
            channel="blog",
            label="블로그/노션 요약",
            headline=og_title,
            body=(
                f"{criteria.purpose} 용도로 {category_label} 후보를 비교했습니다. "
                f"최종 후보는 {top_model}, 실구매가는 {price_label}, 구매 판정은 {verdict}입니다. "
                "리포트에는 TOP 3 비교, 대안 시나리오, 구매 타이밍, "
                "결제 전 체크리스트가 포함됩니다."
            ),
            cta="상세 비교 리포트",
            public_label=public_label,
        ),
    ]
    next_actions = [
        "공개 리포트 URL을 카카오톡 또는 커뮤니티 검토 요청 문구와 함께 공유하세요.",
        "댓글에서 반복되는 우려를 구매 상담 Q&A 또는 결제 전 검수에 반영하세요.",
        "공유 후 성장 퍼널의 share_cta와 recommendation_click 전환을 확인하세요.",
    ]
    if not report.share_token:
        next_actions.insert(0, "먼저 /reports/{report_id}/share 로 공개 링크를 생성하세요.")
    return ReportShareAssets(
        workspace_id=report.workspace_id,
        report_id=report.report_id,
        share_token=report.share_token,
        public_path=public_path,
        generated_at=_now(),
        headline=headline,
        subheadline=_clamp_text(subheadline, 220),
        og_title=_clamp_text(og_title, 70),
        og_description=og_description,
        visual_card_text=visual_card_text,
        hashtags=hashtags,
        reviewer_questions=reviewer_questions[:5],
        variants=variants,
        next_actions=next_actions,
    )


def _share_asset_variant(
    *,
    channel: str,
    label: str,
    headline: str,
    body: str,
    cta: str,
    public_label: str,
) -> ReportShareAssetVariant:
    body = _clamp_text(body, 420)
    copy_text = f"{headline}\n\n{body}\n\n{cta}: {public_label}"
    return ReportShareAssetVariant(
        channel=channel,
        label=label,
        headline=_clamp_text(headline, 80),
        body=body,
        cta=cta,
        copy_text=copy_text,
    )


def _clamp_text(value: str, limit: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 1)].rstrip() + "…"


def _event_rate(
    counts: dict[str, int],
    key: GrowthEventType,
    baseline: int,
) -> float:
    return round(counts.get(key.value, 0) / max(baseline, 1), 4)


def _growth_funnel_status(
    steps: list[GrowthFunnelStep],
    analysis_runs: int,
) -> CheckStatus:
    if analysis_runs == 0:
        return CheckStatus.blocker
    if any(step.status == CheckStatus.blocker for step in steps[:2]):
        return CheckStatus.blocker
    if any(step.status == CheckStatus.warning for step in steps):
        return CheckStatus.warning
    return CheckStatus.ok


def _growth_funnel_summary(
    status: CheckStatus,
    total_events: int,
    activation_rate: float,
) -> str:
    if status == CheckStatus.ok:
        return (
            f"성장 이벤트 {total_events}건과 추천 클릭률 "
            f"{round(activation_rate * 100)}%가 공개 확대 기준을 충족합니다."
        )
    if status == CheckStatus.warning:
        return (
            f"성장 이벤트 {total_events}건이 수집됐지만 추천 클릭률 "
            f"{round(activation_rate * 100)}%를 더 끌어올려야 합니다."
        )
    return (
        "분석 실행 또는 추천 카드 클릭 표본이 부족해 공개 반응을 판단하기 어렵습니다."
    )


def _pulse_score_from_rate(value: float, *, warning: float, ok: float) -> float:
    if value <= 0:
        return 0
    if value >= ok:
        return 100
    if value <= warning:
        return round((value / warning) * 55, 1)
    return round(55 + ((value - warning) / (ok - warning)) * 45, 1)


def _pulse_rate_status(value: float, warning: float, ok: float) -> CheckStatus:
    if value >= ok:
        return CheckStatus.ok
    if value >= warning:
        return CheckStatus.warning
    return CheckStatus.blocker


def _pulse_count_status(value: int, warning: int, ok: int) -> CheckStatus:
    if value >= ok:
        return CheckStatus.ok
    if value >= warning:
        return CheckStatus.warning
    return CheckStatus.blocker


def _pulse_status(
    pulse_score: float,
    readiness: BetaReadinessDashboard,
    growth: GrowthFunnelDashboard,
) -> CheckStatus:
    if (
        pulse_score < 35
        or readiness.launch_readiness_score < 35
        or growth.status == CheckStatus.blocker
    ):
        return CheckStatus.blocker
    if pulse_score < 70 or readiness.launch_readiness_score < 70:
        return CheckStatus.warning
    return CheckStatus.ok


def _pulse_signal(
    *,
    area: str,
    label: str,
    score: float,
    evidence: str,
    recommendation: str,
) -> LaunchPulseSignal:
    if score >= 70:
        status = CheckStatus.ok
    elif score >= 35:
        status = CheckStatus.warning
    else:
        status = CheckStatus.blocker
    return LaunchPulseSignal(
        area=area,
        label=label,
        status=status,
        score=round(score, 1),
        evidence=evidence,
        recommendation=recommendation,
    )


def _pulse_metric(
    key: str,
    label: str,
    value: int | float | str,
    unit: str,
    status: CheckStatus,
    detail: str,
) -> LaunchPulseMetric:
    return LaunchPulseMetric(
        key=key,
        label=label,
        value=value,
        unit=unit,
        status=status,
        detail=detail,
    )


def _pulse_headline(status: CheckStatus, pulse_score: float) -> str:
    if status == CheckStatus.ok:
        return f"공개 반응 Pulse {pulse_score}점, 확대 실험을 진행할 수 있습니다."
    if status == CheckStatus.warning:
        return f"공개 반응 Pulse {pulse_score}점, 강한 신호는 있지만 보강이 필요합니다."
    return f"공개 반응 Pulse {pulse_score}점, 표본과 핵심 전환을 먼저 확보해야 합니다."


def _pulse_summary(
    pulse_score: float,
    metrics: OperationsMetrics,
    referrals: WaitlistReferralDashboard,
    pricing: PricingDashboard,
) -> str:
    return (
        f"분석 {metrics.analysis_runs}건, 피드백 {metrics.feedback_count}건, "
        f"추천 대기열 {referrals.total_referrals}명, 요금제 관심 {pricing.intent_count}건을 "
        f"종합한 출시 반응 점수는 {pulse_score}점입니다."
    )


def _pulse_top_actions(
    signals: list[LaunchPulseSignal],
    growth: GrowthFunnelDashboard,
    referrals: WaitlistReferralDashboard,
    pricing: PricingDashboard,
    readiness: BetaReadinessDashboard,
) -> list[str]:
    actions = [
        signal.recommendation
        for signal in sorted(signals, key=lambda item: item.score)
        if signal.status != CheckStatus.ok
    ][:3]
    actions.extend(growth.next_actions[:1])
    actions.extend(referrals.next_actions[:1])
    actions.extend(pricing.next_actions[:1])
    actions.extend(readiness.next_actions[:1])
    deduped: list[str] = []
    for action in actions:
        if action and action not in deduped:
            deduped.append(action)
    if not deduped:
        deduped.append(
            "Pulse 신호가 안정적입니다. 상위 유입 채널에 공개 베타 트래픽을 더 배정하세요."
        )
    return deduped[:6]


def _retry_at(now: str, minutes: int) -> str:
    base = datetime.fromisoformat(now)
    return (base + timedelta(minutes=minutes)).isoformat()


def _mask_target(target: str) -> str:
    if target.startswith(("http://", "https://")):
        scheme, rest = target.split("://", 1)
        host = rest.split("/", 1)[0]
        return f"{scheme}://{host}/***"
    return _mask_contact(target)


def _mask_contact(contact: str) -> str:
    if "@" in contact:
        name, domain = contact.split("@", 1)
        visible = name[:2] if len(name) > 2 else name[:1]
        return f"{visible}***@{domain}"
    if len(contact) <= 4:
        return "***"
    return f"{contact[:3]}***{contact[-2:]}"


def _mask_order_reference(reference: str) -> str:
    normalized = reference.strip()
    if not normalized:
        return ""
    if len(normalized) <= 6:
        return "***"
    return f"{normalized[:3]}***{normalized[-3:]}"
