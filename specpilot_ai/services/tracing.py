from specpilot_ai.core.models import AgentStep, CheckStatus, TraceEvent


def trace_event(
    step: AgentStep,
    title: str,
    detail: str,
    *,
    status: CheckStatus = CheckStatus.ok,
    evidence_count: int = 0,
) -> TraceEvent:
    return TraceEvent(
        step=step,
        title=title,
        detail=detail,
        status=status,
        evidence_count=evidence_count,
    )
