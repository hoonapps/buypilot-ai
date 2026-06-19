from abc import ABC, abstractmethod
from datetime import UTC, datetime
from hashlib import sha1

from specpilot_ai.core.models import (
    Category,
    SourceAdapterStatus,
    SourceCandidate,
    SourceKind,
)
from specpilot_ai.data.catalog import (
    desktop_candidates,
    laptop_candidates,
    price_catalog,
    review_catalog,
)


class SourceAdapter(ABC):
    adapter_id: str
    name: str
    kind: SourceKind
    freshness_minutes: int

    @abstractmethod
    def health(self) -> SourceAdapterStatus:
        raise NotImplementedError

    @abstractmethod
    def collect(self, query: str, category: Category, limit: int) -> list[SourceCandidate]:
        raise NotImplementedError


class DemoPriceCompareAdapter(SourceAdapter):
    adapter_id = "price_compare_demo"
    name = "가격비교 데모 어댑터"
    kind = SourceKind.price
    freshness_minutes = 15

    def health(self) -> SourceAdapterStatus:
        return _status(
            self,
            confidence=0.9,
            message="가격, 배송비, 쿠폰, 카드 할인 필드를 정상 수집할 수 있습니다.",
        )

    def collect(self, query: str, category: Category, limit: int) -> list[SourceCandidate]:
        products = _products_for(category)
        prices = price_catalog()
        rows: list[SourceCandidate] = []
        for product in products:
            price = prices[product.id]
            if price["source_type"] not in {"price_compare", "open_market", "pc_builder"}:
                continue
            effective_price = (
                int(price["price_krw"])
                + int(price["shipping_fee_krw"])
                + int(price["assembly_fee_krw"])
                + int(price["os_fee_krw"])
                - int(price["coupon_krw"])
                - int(price["card_discount_krw"])
            )
            risk_flags = []
            if str(price["stock_status"]) == "limited":
                risk_flags.append("재고 한정")
            if "출처" in query and not product.source_url:
                risk_flags.append("출처 누락")
            rows.append(
                _candidate(
                    adapter=self,
                    kind=SourceKind.price,
                    title=f"{product.model_name} 실구매가",
                    url=product.source_url,
                    normalized_model=product.normalized_model,
                    evidence_text=(
                        f"{price['seller']} 기준 실구매가 {effective_price:,}원, "
                        f"재고 상태 {price['stock_status']}"
                    ),
                    extracted_price_krw=effective_price,
                    seller=str(price["seller"]),
                    confidence=0.88 if not risk_flags else 0.72,
                    risk_flags=risk_flags,
                )
            )
        return rows[:limit]


class DemoOfficialStoreAdapter(SourceAdapter):
    adapter_id = "official_store_demo"
    name = "공식 스토어 데모 어댑터"
    kind = SourceKind.official
    freshness_minutes = 60

    def health(self) -> SourceAdapterStatus:
        return _status(
            self,
            confidence=0.86,
            message="공식 스토어 가격과 옵션명을 확인할 수 있습니다.",
        )

    def collect(self, query: str, category: Category, limit: int) -> list[SourceCandidate]:
        products = [
            product
            for product in _products_for(category)
            if product.source_type == "official_store"
        ]
        rows = [
            _candidate(
                adapter=self,
                kind=SourceKind.official,
                title=f"{product.model_name} 공식 옵션",
                url=product.source_url,
                normalized_model=product.normalized_model,
                evidence_text=f"공식 스토어 옵션: {product.option_summary}",
                confidence=0.9,
            )
            for product in products
        ]
        return rows[:limit]


class DemoReviewAdapter(SourceAdapter):
    adapter_id = "review_signal_demo"
    name = "리뷰 리스크 데모 어댑터"
    kind = SourceKind.review
    freshness_minutes = 240

    def health(self) -> SourceAdapterStatus:
        return _status(
            self,
            confidence=0.82,
            message="반복 불만과 리뷰 리스크 신호를 추출할 수 있습니다.",
        )

    def collect(self, query: str, category: Category, limit: int) -> list[SourceCandidate]:
        rows: list[SourceCandidate] = []
        reviews = review_catalog()
        for product in _products_for(category):
            review = reviews[product.id]
            risk_flags = list(review.risk_signals[:2])
            rows.append(
                _candidate(
                    adapter=self,
                    kind=SourceKind.review,
                    title=f"{product.model_name} 리뷰 요약",
                    url=product.source_url,
                    normalized_model=product.normalized_model,
                    evidence_text=review.sentiment_summary,
                    confidence=review.trust_score,
                    risk_flags=risk_flags,
                )
            )
        return rows[:limit]


class DemoBenchmarkAdapter(SourceAdapter):
    adapter_id = "benchmark_demo"
    name = "벤치마크 데모 어댑터"
    kind = SourceKind.benchmark
    freshness_minutes = 1440

    def health(self) -> SourceAdapterStatus:
        return _status(
            self,
            confidence=0.78,
            message="목적별 벤치마크 근거를 연결할 수 있습니다.",
        )

    def collect(self, query: str, category: Category, limit: int) -> list[SourceCandidate]:
        products = _products_for(category)
        rows = [
            _candidate(
                adapter=self,
                kind=SourceKind.benchmark,
                title=f"{product.model_name} 목적별 성능 근거",
                url=product.source_url,
                normalized_model=product.normalized_model,
                evidence_text=f"{query} 목적에 대해 {product.option_summary} 구성을 비교합니다.",
                confidence=0.76,
                risk_flags=(
                    ["벤치마크 출처 수동 검수 필요"]
                    if product.category == Category.laptop
                    else []
                ),
            )
            for product in products
        ]
        return rows[:limit]


def default_adapters() -> list[SourceAdapter]:
    return [
        DemoPriceCompareAdapter(),
        DemoOfficialStoreAdapter(),
        DemoReviewAdapter(),
        DemoBenchmarkAdapter(),
    ]


def _products_for(category: Category):
    return desktop_candidates() if category == Category.desktop_pc else laptop_candidates()


def _status(adapter: SourceAdapter, *, confidence: float, message: str) -> SourceAdapterStatus:
    return SourceAdapterStatus(
        adapter_id=adapter.adapter_id,
        name=adapter.name,
        kind=adapter.kind,
        enabled=True,
        freshness_minutes=adapter.freshness_minutes,
        confidence=confidence,
        last_checked_at=_now(),
        message=message,
    )


def _candidate(
    *,
    adapter: SourceAdapter,
    kind: SourceKind,
    title: str,
    url: str,
    normalized_model: str,
    evidence_text: str,
    confidence: float,
    extracted_price_krw: int | None = None,
    seller: str | None = None,
    risk_flags: list[str] | None = None,
) -> SourceCandidate:
    risks = risk_flags or []
    seed = f"{adapter.adapter_id}:{normalized_model}:{title}"
    return SourceCandidate(
        source_id=f"source_{sha1(seed.encode()).hexdigest()[:12]}",
        adapter_id=adapter.adapter_id,
        kind=kind,
        title=title,
        url=url,
        normalized_model=normalized_model,
        extracted_price_krw=extracted_price_krw,
        seller=seller,
        evidence_text=evidence_text,
        confidence=confidence,
        collected_at=_now(),
        needs_review=confidence < 0.8 or bool(risks),
        risk_flags=risks,
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()
