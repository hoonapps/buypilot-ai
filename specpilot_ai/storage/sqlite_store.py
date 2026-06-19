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
    BetaLead,
    BetaLeadRequest,
    BetaReadinessCheck,
    BetaReadinessDashboard,
    Category,
    CheckStatus,
    FeedbackRecord,
    FeedbackRequest,
    OperationsMetrics,
    ProviderReviewStatus,
    PublicReport,
    QualityDashboard,
    ReportShare,
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
    TraceEvent,
    TraceRunSummary,
    TraceSpanRecord,
)

SUPPORTED_ALERT_CHANNELS = {"email", "webhook", "sms"}


class SpecPilotStore:
    def __init__(self, settings: Settings) -> None:
        self.db_path = Path(settings.storage_path)
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

    def get_public_report(self, share_token: str) -> PublicReport | None:
        now = _now()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT sr.report_id, sr.title, sr.final_pick_id, sr.top_model_name,
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
        return PublicReport(
            report_id=data["report_id"],
            title=data["title"],
            top_model_name=data["top_model_name"],
            final_pick_id=data["final_pick_id"],
            shared_at=data["shared_at"],
            share_views=data["share_views"] + 1,
            response=AnalyzeResponse.model_validate_json(data["response_json"]),
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
            contact=contact,
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
                    subscription.contact,
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
                contact_masked=_mask_contact(subscription.contact),
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
            source_monitors=source_monitors,
            source_refresh_runs=source_refresh_runs,
            source_refresh_failures=source_refresh_failures,
            source_provider_policies=source_provider_policies,
            source_provider_fetches=source_provider_fetches,
            source_provider_blocked_fetches=source_provider_blocked_fetches,
            trace_spans=trace_spans,
            feedback_count=feedback_count,
            beta_leads=beta_leads,
            latest_trace_id=latest["trace_id"] if latest else None,
            average_top_score=round(float(score_row[0] or 0), 2),
            average_quality_score=round(float(quality_row[0] or 0), 2),
            average_satisfaction=round(float(feedback_row["average_satisfaction"] or 0), 2),
            purchase_intent_rate=round(float(feedback_row["purchase_intent_rate"] or 0), 4),
            estimated_cost_krw=round(float(quality_row[1] or 0), 2),
            conversion_ready_rate=round(float(ready_row[0] or 0), 4),
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

                CREATE INDEX IF NOT EXISTS idx_saved_reports_trace
                    ON saved_reports(trace_id);
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
                CREATE INDEX IF NOT EXISTS idx_trace_spans_workspace
                    ON trace_spans(workspace_id, trace_id);
                CREATE INDEX IF NOT EXISTS idx_user_feedback_workspace
                    ON user_feedback(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_user_feedback_trace
                    ON user_feedback(trace_id);
                CREATE INDEX IF NOT EXISTS idx_beta_leads_workspace
                    ON beta_leads(workspace_id);
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
            _ensure_column(conn, "saved_reports", "workspace_id", "TEXT NOT NULL DEFAULT 'demo'")
            _ensure_column(conn, "saved_reports", "share_token", "TEXT")
            _ensure_column(conn, "saved_reports", "shared_at", "TEXT")
            _ensure_column(conn, "saved_reports", "share_views", "INTEGER NOT NULL DEFAULT 0")
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
        contact=data["contact"],
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
        + feedback * 0.18
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
