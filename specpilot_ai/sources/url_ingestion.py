import ipaddress
import re
from datetime import UTC, datetime
from hashlib import sha1
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from specpilot_ai.core.models import (
    ReviewQueueItem,
    ReviewStatus,
    SourceCandidate,
    SourceKind,
    SourceUrlIngestRequest,
    SourceUrlIngestResponse,
)

MAX_HTML_BYTES = 220_000
PRICE_PATTERN = re.compile(r"(?<!\d)(\d{1,3}(?:,\d{3})+|\d{5,8})\s*원")
BLOCKED_HOSTS = {"localhost", "metadata.google.internal"}


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
    price = _extract_price(" ".join([title, evidence_text]))
    risk_flags = _risk_flags(request, price, fetched_live, snapshot)
    confidence = _confidence(price, snapshot, fetched_live)
    source_id = _source_id(request.url, request.kind, model_name, evidence_text)
    candidate = SourceCandidate(
        source_id=source_id,
        adapter_id="operator_url_ingest",
        kind=request.kind,
        title=title[:160],
        url=request.url,
        normalized_model=_normalize_model(model_name),
        extracted_price_krw=price,
        seller=request.seller or _seller_from_url(request.url),
        evidence_text=evidence_text[:500],
        confidence=confidence,
        collected_at=_now(),
        needs_review=True,
        risk_flags=risk_flags,
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
    matches = [int(match.group(1).replace(",", "")) for match in PRICE_PATTERN.finditer(text)]
    reasonable = [price for price in matches if 50_000 <= price <= 20_000_000]
    return min(reasonable) if reasonable else None


def _risk_flags(
    request: SourceUrlIngestRequest,
    price: int | None,
    fetched_live: bool,
    snapshot: _HtmlSnapshotParser,
) -> list[str]:
    risks = ["실제 URL 근거 운영자 검수 필요", "이용약관/robots 확인 필요"]
    if price is None and request.kind == SourceKind.price:
        risks.append("가격 추출 실패")
    if fetched_live:
        risks.append("라이브 HTML 수집")
    if not snapshot.title:
        risks.append("페이지 제목 추출 실패")
    return risks


def _confidence(
    price: int | None,
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
    if fetched_live:
        confidence -= 0.04
    return max(0.4, min(0.78, round(confidence, 2)))


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
