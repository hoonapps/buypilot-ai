from datetime import UTC, datetime
from uuid import uuid4

from specpilot_ai.core.models import (
    ReviewQueueItem,
    ReviewStatus,
    SourceAdapterStatus,
    SourceCandidate,
    SourceCollectionRequest,
    SourceCollectionResponse,
)
from specpilot_ai.sources.adapters import SourceAdapter, default_adapters


class SourceCollector:
    def __init__(self, adapters: list[SourceAdapter] | None = None) -> None:
        self.adapters = adapters or default_adapters()

    def statuses(self) -> list[SourceAdapterStatus]:
        return [adapter.health() for adapter in self.adapters]

    def collect(self, request: SourceCollectionRequest) -> SourceCollectionResponse:
        selected = self._selected_adapters(request.adapters)
        candidates: list[SourceCandidate] = []
        per_adapter_limit = max(1, request.limit // max(1, len(selected)))
        for adapter in selected:
            candidates.extend(adapter.collect(request.query, request.category, per_adapter_limit))
        candidates = candidates[: request.limit]
        review_queue = [candidate for candidate in candidates if candidate.needs_review]
        return SourceCollectionResponse(
            query=request.query,
            category=request.category,
            adapter_statuses=[adapter.health() for adapter in selected],
            candidates=candidates,
            review_queue=review_queue,
        )

    def build_review_items(
        self,
        candidates: list[SourceCandidate],
    ) -> list[ReviewQueueItem]:
        return [
            ReviewQueueItem(
                review_id=f"review_{uuid4().hex[:12]}",
                source=candidate,
                status=ReviewStatus.pending,
                reason=_review_reason(candidate),
                created_at=_now(),
            )
            for candidate in candidates
            if candidate.needs_review
        ]

    def _selected_adapters(self, adapter_ids: list[str]) -> list[SourceAdapter]:
        if not adapter_ids:
            return self.adapters
        selected = [adapter for adapter in self.adapters if adapter.adapter_id in set(adapter_ids)]
        return selected or self.adapters


def _review_reason(candidate: SourceCandidate) -> str:
    reasons = []
    if candidate.confidence < 0.8:
        reasons.append(f"신뢰도 {candidate.confidence:.2f}")
    reasons.extend(candidate.risk_flags)
    return " / ".join(reasons) if reasons else "운영자 검수 필요"


def _now() -> str:
    return datetime.now(UTC).isoformat()
