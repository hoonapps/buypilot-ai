from specpilot_ai.core.models import BenchmarkEvidence, ProductCandidate, ReviewInsight
from specpilot_ai.data.catalog import benchmark_catalog, review_catalog


def review_for(product: ProductCandidate) -> ReviewInsight:
    row = review_catalog()[product.id]
    return ReviewInsight(
        product_id=product.id,
        pros=row.pros,
        cons=row.cons,
        repeated_complaints=row.repeated_complaints,
        risk_signals=row.risk_signals,
        trust_score=row.trust_score,
        evidence_count=row.evidence_count,
        sentiment_summary=row.sentiment_summary,
    )


def benchmarks_for(product: ProductCandidate) -> list[BenchmarkEvidence]:
    return [
        BenchmarkEvidence(
            product_id=product.id,
            workload=row.workload,
            score_label=row.score_label,
            summary=row.summary,
            evidence_url=row.evidence_url,
        )
        for row in benchmark_catalog().get(product.id, [])
    ]


def strongest_reason(product: ProductCandidate, review: ReviewInsight) -> str:
    if product.tags:
        return f"{product.tags[0]} 조건과 맞고, {review.pros[0]}"
    return review.pros[0] if review.pros else "목적 조건과 가격 균형이 좋습니다."


def main_risk(review: ReviewInsight) -> str:
    if review.risk_signals:
        return review.risk_signals[0]
    if review.cons:
        return review.cons[0]
    return "구매 직전 가격과 옵션명을 다시 확인해야 합니다."
