import ipaddress
import re
from datetime import UTC, datetime
from hashlib import sha1
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from specpilot_ai.core.models import (
    CheckStatus,
    ReviewQueueItem,
    ReviewStatus,
    SourceCandidate,
    SourceKind,
    SourceUrlIngestRequest,
    SourceUrlIngestResponse,
)

MAX_HTML_BYTES = 220_000
PRICE_PATTERN = re.compile(r"(?<!\d)(\d{1,3}(?:,\d{3})+|\d{5,8})\s*원")
FREE_SHIPPING_PATTERN = re.compile(r"(무료\s*배송|배송비\s*무료|무배)")
SHIPPING_PATTERN = re.compile(
    r"(?:배송비|배송료|택배비)\s*[:：]?\s*(\d{1,3}(?:,\d{3})+|\d{3,6})\s*원"
)
DISCOUNT_PATTERN = re.compile(
    r"(?:쿠폰|카드\s*할인|즉시\s*할인|청구\s*할인|할인)\s*[:：]?\s*(\d{1,3}(?:,\d{3})+|\d{3,7})\s*원"
)
BLOCKED_HOSTS = {"localhost", "metadata.google.internal"}
SOLD_OUT_KEYWORDS = ("품절", "일시품절", "판매 종료", "판매종료", "재고 없음", "재고없음")
LOW_STOCK_KEYWORDS = ("재고 부족", "재고부족", "마감 임박", "한정 수량", "품절 임박")
IN_STOCK_KEYWORDS = ("구매 가능", "판매중", "재고 있음", "재고있음", "바로 구매", "장바구니")


class _HtmlSnapshotParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.meta_description = ""
        self.text_chunks: list[str] = []
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            values = {key.lower(): value or "" for key, value in attrs}
            if values.get("name", "").lower() == "description" and values.get("content"):
                self.meta_description = _clean_text(values["content"])

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = _clean_text(data)
        if not text:
            return
        if self._in_title:
            self.title = _clean_text(f"{self.title} {text}")
        elif self._skip_depth == 0 and len(text) >= 2:
            self.text_chunks.append(text)


def ingest_source_url(request: SourceUrlIngestRequest) -> SourceUrlIngestResponse:
    _validate_public_url(request.url)
    fetched_live = False
    notes: list[str] = []
    html = request.html.strip()
    if not html:
        html = _fetch_html(request.url)
        fetched_live = True
        notes.append("외부 URL에서 HTML 스냅샷을 가져왔습니다.")
    else:
        notes.append("요청에 포함된 HTML 스냅샷으로 추출했습니다.")

    snapshot = _parse_html(html)
    title = snapshot.title or request.expected_model or request.url
    model_name = request.expected_model.strip() or _model_from_title(title)
    evidence_text = _evidence_text(snapshot)
    extraction_text = " ".join([title, evidence_text])
    price = _extract_price(extraction_text)
    shipping_fee = _extract_shipping_fee(extraction_text)
    discount = _extract_discount(extraction_text)
    effective_price = _effective_price(price, shipping_fee, discount)
    availability = _availability_status(extraction_text)
    model_match_status = _model_match_status(request.expected_model, extraction_text)
    extraction_signals = _extraction_signals(
        price=price,
        shipping_fee=shipping_fee,
        discount=discount,
        effective_price=effective_price,
        availability=availability,
        model_match_status=model_match_status,
        fetched_live=fetched_live,
    )
    risk_flags = _risk_flags(
        request,
        price,
        shipping_fee,
        availability,
        model_match_status,
        fetched_live,
        snapshot,
    )
    confidence = _confidence(
        price,
        shipping_fee,
        availability,
        model_match_status,
        snapshot,
        fetched_live,
    )
    source_id = _source_id(request.url, request.kind, model_name, evidence_text)
    candidate = SourceCandidate(
        source_id=source_id,
        adapter_id="operator_url_ingest",
        kind=request.kind,
        title=title[:160],
        url=request.url,
        normalized_model=_normalize_model(model_name),
        extracted_price_krw=price,
        shipping_fee_krw=shipping_fee,
        coupon_or_card_benefit_krw=discount,
        effective_price_krw=effective_price,
        availability_status=availability,
        model_match_status=model_match_status,
        seller=request.seller or _seller_from_url(request.url),
        evidence_text=evidence_text[:500],
        confidence=confidence,
        collected_at=_now(),
        needs_review=True,
        risk_flags=risk_flags,
        extraction_signals=extraction_signals,
    )
    review_item = ReviewQueueItem(
        review_id=f"review_{source_id.removeprefix('source_')}",
        source=candidate,
        status=ReviewStatus.pending,
        reason=" / ".join(["실제 URL 인입", *risk_flags]),
        created_at=_now(),
    )
    return SourceUrlIngestResponse(
        candidate=candidate,
        review_item=review_item,
        fetched_live=fetched_live,
        extraction_notes=notes,
    )


def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("http 또는 https URL만 인입할 수 있습니다.")
    if parsed.username or parsed.password:
        raise ValueError("사용자 정보가 포함된 URL은 인입할 수 없습니다.")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("URL host를 확인할 수 없습니다.")
    if host in BLOCKED_HOSTS or host.endswith(".local"):
        raise ValueError("내부 네트워크 URL은 인입할 수 없습니다.")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        raise ValueError("private 또는 loopback IP URL은 인입할 수 없습니다.")


def _fetch_html(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "SpecPilotAI/0.1 source-verifier",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urlopen(req, timeout=8) as response:
            content_type = response.headers.get("content-type", "")
            if "html" not in content_type and "text/plain" not in content_type:
                raise ValueError(f"HTML 응답이 아닙니다: {content_type}")
            return response.read(MAX_HTML_BYTES).decode("utf-8", errors="replace")
    except URLError as exc:
        raise ValueError(f"외부 URL을 가져오지 못했습니다: {exc}") from exc


def _parse_html(html: str) -> _HtmlSnapshotParser:
    parser = _HtmlSnapshotParser()
    parser.feed(html[:MAX_HTML_BYTES])
    return parser


def _evidence_text(snapshot: _HtmlSnapshotParser) -> str:
    chunks = [snapshot.meta_description, *snapshot.text_chunks[:20]]
    text = _clean_text(" ".join(chunk for chunk in chunks if chunk))
    return text or "상품 페이지에서 추출 가능한 본문 텍스트가 부족합니다."


def _extract_price(text: str) -> int | None:
    matches = [
        int(match.group(1).replace(",", ""))
        for match in PRICE_PATTERN.finditer(text)
        if not _is_adjustment_price_context(text, match.start())
    ]
    reasonable = [price for price in matches if 50_000 <= price <= 20_000_000]
    return min(reasonable) if reasonable else None


def _is_adjustment_price_context(text: str, start: int) -> bool:
    context = text[max(0, start - 18) : start]
    return any(keyword in context for keyword in ("배송비", "배송료", "택배비", "할인", "쿠폰"))


def _extract_shipping_fee(text: str) -> int | None:
    if FREE_SHIPPING_PATTERN.search(text):
        return 0
    fees = [int(match.group(1).replace(",", "")) for match in SHIPPING_PATTERN.finditer(text)]
    reasonable = [fee for fee in fees if 0 <= fee <= 300_000]
    return min(reasonable) if reasonable else None


def _extract_discount(text: str) -> int | None:
    discounts = [
        int(match.group(1).replace(",", "")) for match in DISCOUNT_PATTERN.finditer(text)
    ]
    reasonable = [discount for discount in discounts if 0 < discount <= 5_000_000]
    return max(reasonable) if reasonable else None


def _effective_price(
    price: int | None,
    shipping_fee: int | None,
    discount: int | None,
) -> int | None:
    if price is None:
        return None
    return max(0, price + (shipping_fee or 0) - (discount or 0))


def _availability_status(text: str) -> str:
    if any(keyword in text for keyword in SOLD_OUT_KEYWORDS):
        return "sold_out"
    if any(keyword in text for keyword in LOW_STOCK_KEYWORDS):
        return "low_stock"
    if any(keyword in text for keyword in IN_STOCK_KEYWORDS):
        return "in_stock"
    return "unknown"


def _model_match_status(expected_model: str, text: str) -> CheckStatus:
    expected = _model_tokens(expected_model)
    if not expected:
        return CheckStatus.warning
    observed = _model_tokens(text)
    overlap = len(expected & observed)
    ratio = overlap / len(expected)
    if ratio >= 0.72:
        return CheckStatus.ok
    if ratio >= 0.38:
        return CheckStatus.warning
    return CheckStatus.blocker


def _model_tokens(value: str) -> set[str]:
    normalized = re.sub(r"[^0-9a-zA-Z가-힣]+", " ", value.lower())
    tokens = {
        token
        for token in normalized.split()
        if len(token) >= 2 and token not in {"pc", "rtx", "intel", "amd", "store", "product"}
    }
    return tokens


def _extraction_signals(
    *,
    price: int | None,
    shipping_fee: int | None,
    discount: int | None,
    effective_price: int | None,
    availability: str,
    model_match_status: CheckStatus,
    fetched_live: bool,
) -> list[str]:
    signals: list[str] = []
    if price is not None:
        signals.append(f"표시 가격 {price:,}원")
    if shipping_fee is not None:
        signals.append("무료배송" if shipping_fee == 0 else f"배송비 {shipping_fee:,}원")
    if discount is not None:
        signals.append(f"할인/쿠폰 {discount:,}원")
    if effective_price is not None:
        signals.append(f"추정 실구매가 {effective_price:,}원")
    signals.append(f"재고 상태 {availability}")
    signals.append(f"모델명 일치도 {model_match_status.value}")
    if fetched_live:
        signals.append("라이브 수집")
    return signals


def _risk_flags(
    request: SourceUrlIngestRequest,
    price: int | None,
    shipping_fee: int | None,
    availability: str,
    model_match_status: CheckStatus,
    fetched_live: bool,
    snapshot: _HtmlSnapshotParser,
) -> list[str]:
    risks = ["실제 URL 근거 운영자 검수 필요", "이용약관/robots 확인 필요"]
    if price is None and request.kind == SourceKind.price:
        risks.append("가격 추출 실패")
    if shipping_fee is None and request.kind == SourceKind.price:
        risks.append("배송비 확인 필요")
    if availability == "sold_out":
        risks.append("품절 또는 판매 종료")
    elif availability == "low_stock":
        risks.append("재고 부족 신호")
    elif availability == "unknown":
        risks.append("재고 상태 미확인")
    if model_match_status == CheckStatus.blocker:
        risks.append("기대 모델명과 페이지 내용 불일치")
    elif model_match_status == CheckStatus.warning:
        risks.append("모델명 부분 일치 또는 검수 필요")
    if fetched_live:
        risks.append("라이브 HTML 수집")
    if not snapshot.title:
        risks.append("페이지 제목 추출 실패")
    return risks


def _confidence(
    price: int | None,
    shipping_fee: int | None,
    availability: str,
    model_match_status: CheckStatus,
    snapshot: _HtmlSnapshotParser,
    fetched_live: bool,
) -> float:
    confidence = 0.58
    if snapshot.title:
        confidence += 0.08
    if snapshot.meta_description:
        confidence += 0.04
    if price is not None:
        confidence += 0.12
    if shipping_fee is not None:
        confidence += 0.04
    if availability in {"in_stock", "low_stock"}:
        confidence += 0.04
    if model_match_status == CheckStatus.ok:
        confidence += 0.08
    elif model_match_status == CheckStatus.blocker:
        confidence -= 0.1
    if fetched_live:
        confidence -= 0.04
    return max(0.35, min(0.9, round(confidence, 2)))


def _model_from_title(title: str) -> str:
    return _clean_text(title.split("|")[0].split("-")[0])[:80] or "external product"


def _normalize_model(model_name: str) -> str:
    normalized = re.sub(r"[^0-9a-zA-Z가-힣]+", "-", model_name.strip().lower())
    return normalized.strip("-") or "external-product"


def _seller_from_url(url: str) -> str:
    return urlparse(url).hostname or "external"


def _source_id(url: str, kind: SourceKind, model_name: str, evidence_text: str) -> str:
    seed = f"{url}:{kind.value}:{model_name}:{evidence_text[:120]}"
    return f"source_{sha1(seed.encode()).hexdigest()[:12]}"


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _now() -> str:
    return datetime.now(UTC).isoformat()
