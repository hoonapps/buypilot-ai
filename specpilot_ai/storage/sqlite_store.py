import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from specpilot_ai.core.config import Settings
from specpilot_ai.core.models import (
    AlertDeliveryEvent,
    AlertEvaluationResponse,
    AlertSubscription,
    AnalysisQualityAudit,
    AnalyzeResponse,
    BetaLead,
    BetaLeadRequest,
    FeedbackRecord,
    FeedbackRequest,
    OperationsMetrics,
    PublicReport,
    QualityDashboard,
    ReportShare,
    ReviewDecision,
    ReviewQueueItem,
    ReviewStatus,
    SavedReportDetail,
    SavedReportSummary,
    SourceCandidate,
)


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
            triggered_alerts = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM alert_delivery_events{where}
                {' AND ' if where else ' WHERE '}delivery_status IN ('queued', 'sent')
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
            alert_subscriptions=alert_subscriptions,
            alert_events=alert_events,
            triggered_alerts=triggered_alerts,
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
                CREATE INDEX IF NOT EXISTS idx_alert_events_workspace
                    ON alert_delivery_events(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_alert_events_subscription
                    ON alert_delivery_events(subscription_id);
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


def _mask_contact(contact: str) -> str:
    if "@" in contact:
        name, domain = contact.split("@", 1)
        visible = name[:2] if len(name) > 2 else name[:1]
        return f"{visible}***@{domain}"
    if len(contact) <= 4:
        return "***"
    return f"{contact[:3]}***{contact[-2:]}"
