# SpecPilot AI

컴퓨터 견적과 노트북 구매를 위한 AI 의사결정 에이전트입니다.

SpecPilot AI는 최저가 링크만 보여주는 쇼핑 도구가 아닙니다. 사용자의 예산, 사용 목적, 모니터 해상도, 필수 조건, 제외 조건을 구조화한 뒤 후보 5개를 비교하고, 최종 TOP 3와 제외 후보 2개를 리포트로 제공합니다. 각 후보에는 실구매가, 호환성 체크, 리뷰 리스크, 벤치마크 근거, 구매 전 체크리스트, 가격 알림 목표가가 포함됩니다.

## 제품 포지션

초기 집중 영역은 두 가지입니다.

- 데스크톱 PC 견적 추천
- 노트북 구매 비교

지원하는 판단 축:

- CPU/GPU/RAM/SSD/PSU/케이스 조합
- CPU 소켓, 메인보드, 파워 용량, GPU 장착 공간, 쿨러 높이
- 노트북 RAM, 외장 GPU, 무게, 배터리, 발열/팬 소음 리스크
- 배송비, 조립비, 쿠폰, 카드 할인을 반영한 실구매가
- 리뷰 반복 불만과 벤치마크 근거
- 목적 적합도, 가격 경쟁력, 리뷰 신뢰도, 구매 안정성, 호환성 점수

## 현재 구현된 기능

- FastAPI 기반 제품 API
- 루트 경로(`/`)에서 바로 실행 가능한 웹 분석 화면
- 분석 전 조건 진단: 누락 조건, 추가 질문, 추천 필수/제외 조건, 정규화 요청 생성
- LangGraph 기반 11단계 구매 분석 워크플로
- 데스크톱/노트북 후보 카탈로그
- 모델 정규화와 중복 제거
- 상세 호환성 체크
- 실구매가 계산
- 리뷰/벤치마크 근거 연결
- TOP 3 추천과 제외 후보 2개
- 비교표, 가격 알림 목표가, 구매 전 체크리스트
- 공유용 검토 브리프: 핵심 판정, 근거, 리스크, 검토 질문, 복사용 문구
- 후보별 근거 팩: 가격 계산, 리뷰 근거 수, 벤치마크, 호환성, 출처 신뢰 요약
- 옵션/사양 검수표: 판매 페이지 옵션명과 핵심 사양 대조
- 구매 판정: 구매 진행 가능, 가격 대기, 검수 후 구매
- 대안 시나리오: 예산 절감, 성능 우선, 안전 우선 비교
- 조건 충족 매트릭스: 필수 조건과 제외 조건의 충족/확인/차단 상태 비교
- 예산/조건 스트레스 테스트: 예산 10% 절감, 예산 10% 여유, 조건 강화 시 선택 변화 분석
- 구매 타이밍 윈도우: 후보별 적정가 밴드, 목표가, 변동 리스크, 결제 트리거
- 구매 실행 패키지: 결제 전 실행 단계, 판매자 확인 질문, 공유 검토 문구
- 출처 신뢰도, 캐시 만료 기준, 제휴 고지 정책
- Agent trace 조회와 SQLite span 저장
- SQLite 기반 분석 결과 저장
- 저장 리포트 조회와 가격 알림 구독
- 저장 리포트 공개 공유 링크 생성과 공개 리포트 페이지
- 목표가 도달 평가와 발송 큐 이벤트 저장
- 이메일/웹훅/SMS 알림 채널 설정, 발송 큐 dispatch, 발송 시도/재시도 기록
- 추천 만족도 피드백, 구매 의향, 선택 후보 저장
- 베타 신청 리드 저장과 개인정보 마스킹
- 운영 지표 API
- 분석 품질 감사와 예상 비용 대시보드
- 가격/리뷰/벤치마크/공식 스토어 소스 어댑터 계약
- 실제 상품 URL/HTML 스냅샷 인입과 관리자 검수 큐 등록
- URL 모니터 등록, 수집 refresh 실행, refresh 이력 추적
- Due schedule preview와 due 모니터 refresh 실행
- Source provider 정책: live fetch 허용 host, robots/약관 승인, 시간당 rate limit 게이트
- 관리자 검수 콘솔(`/admin`)
- 공개 신뢰 정책 API(`/policy/trust`)
- Neo4j 그래프 스키마 미리보기
- 데모 모드 기본 지원

## 빠른 실행

### 로컬 Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn specpilot_ai.api.main:app --reload
```

브라우저에서 엽니다.

```text
http://127.0.0.1:8000/
```

API 문서:

```text
http://127.0.0.1:8000/docs
```

### Docker Compose

```bash
docker compose up --build
```

앱:

```text
http://127.0.0.1:8000/
```

관리자 콘솔:

```text
http://127.0.0.1:8000/admin
```

컨테이너 헬스체크:

```bash
curl http://127.0.0.1:8000/ready
```

## 대표 API

베타 공개용 API는 `X-SpecPilot-Key` 헤더로 워크스페이스를 구분합니다. 헤더를 생략하면 데모 워크스페이스(`demo`)로 동작합니다.

```bash
export SPECPILOT_KEY=specpilot-demo-key
```

```bash
curl http://127.0.0.1:8000/me \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

### 분석 실행

분석 전 입력 품질을 먼저 확인하려면 `/intake/diagnose`를 호출합니다. 이 응답은 바로 분석해도 되는지, 어떤 질문을 더 해야 하는지, 어떤 필수/제외 조건을 자동 보강할지 알려줍니다.

```bash
curl -X POST http://127.0.0.1:8000/intake/diagnose \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "query": "영상 편집과 QHD 144Hz 게임용 데스크톱 220만원 안에서 맞춰줘",
    "category": "desktop_pc",
    "budget_krw": 2200000,
    "purpose": "Premiere Pro, QHD gaming",
    "must_haves": ["32GB RAM", "QHD 144Hz"],
    "exclusions": ["중고", "리퍼"]
  }'
```

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "query": "영상 편집과 게임용 데스크톱 200만원 안에서 맞춰줘. QHD 144Hz 모니터를 쓰고 업그레이드 여지도 있었으면 좋겠어.",
    "category": "desktop_pc",
    "budget_krw": 2000000,
    "purpose": "Premiere Pro, DaVinci Resolve, QHD gaming",
    "must_haves": ["QHD 144Hz", "32GB RAM", "업그레이드 여지"],
    "exclusions": ["중고", "리퍼", "출처 없는 가격"],
    "channels": ["price_compare", "open_market", "official_store"]
  }'
```

### 가격 알림 미리보기

```bash
curl -X POST http://127.0.0.1:8000/alerts/preview \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "query": "영상 편집용 노트북 200만원 이하로 비교해줘",
    "category": "laptop",
    "budget_krw": 2000000,
    "purpose": "Premiere Pro video editing",
    "must_haves": ["32GB RAM 선호", "외장 GPU"]
  }'
```

### Trace 조회

`/analyze` 응답의 `graph_trace_id`를 사용합니다.

```bash
curl http://127.0.0.1:8000/traces/trace_xxxxxxxxxxxx \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

### 출처 신뢰 정책

가격, 리뷰, 벤치마크 출처의 캐시 기준과 제휴 고지 원칙을 확인합니다.

```bash
curl http://127.0.0.1:8000/policy/trust
```

### 리포트 저장

```bash
curl -X POST http://127.0.0.1:8000/reports/save \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "trace_id": "trace_xxxxxxxxxxxx",
    "title": "영상 편집용 PC 구매 리포트",
    "owner_label": "guest",
    "notes": "200만원 예산 기준"
  }'
```

저장된 리포트 목록:

```bash
curl http://127.0.0.1:8000/reports \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

공유 링크 생성:

```bash
curl -X POST http://127.0.0.1:8000/reports/report_xxxxxxxxxxxx/share \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

공개 JSON 조회:

```bash
curl http://127.0.0.1:8000/public/reports/share_xxxxxxxxxxxxxxxxxxxx
```

공개 리포트 페이지:

```text
http://127.0.0.1:8000/r/share_xxxxxxxxxxxxxxxxxxxx
```

공유 해제:

```bash
curl -X DELETE http://127.0.0.1:8000/reports/report_xxxxxxxxxxxx/share \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

### 가격 알림 구독

```bash
curl -X POST http://127.0.0.1:8000/alerts/subscribe \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "trace_id": "trace_xxxxxxxxxxxx",
    "product_id": "build-001",
    "target_price_krw": 1848000,
    "channels": ["email"],
    "contact": "buyer@example.com",
    "owner_label": "guest"
  }'
```

목표가 도달 평가:

```bash
curl -X POST http://127.0.0.1:8000/alerts/evaluate \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "price_overrides_krw": {
      "build-001": 1847999
    },
    "dry_run": false
  }'
```

알림 발송 이벤트 조회:

```bash
curl http://127.0.0.1:8000/alerts/events \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

알림 발송 채널 설정:

```bash
curl -X POST http://127.0.0.1:8000/alerts/channels \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "channel": "email",
    "display_name": "운영 이메일 outbox",
    "target": "ops@example.com",
    "enabled": true,
    "retry_limit": 3
  }'
```

큐 발송 처리:

```bash
curl -X POST http://127.0.0.1:8000/alerts/dispatch \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "dry_run": false,
    "limit": 50
  }'
```

발송 시도 조회:

```bash
curl http://127.0.0.1:8000/alerts/deliveries \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

### 사용자 피드백과 베타 신청

분석 결과에 대한 만족도, 구매 의향, 선택 후보, 개선 요청을 저장합니다. 연락처는 원문을 저장하지 않고 마스킹된 값만 보관합니다.

```bash
curl -X POST http://127.0.0.1:8000/feedback \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "trace_id": "trace_xxxxxxxxxxxx",
    "rating": 5,
    "purchase_intent": true,
    "selected_product_id": "build-001",
    "reason": "추천 근거와 가격 알림 조건이 충분합니다.",
    "improvement_requests": ["실제 판매 링크 연동"],
    "contact": "buyer@example.com"
  }'
```

```bash
curl http://127.0.0.1:8000/feedback \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

베타 신청 리드는 이메일 원문을 저장하지 않고 마스킹된 이메일만 저장합니다.

```bash
curl -X POST http://127.0.0.1:8000/beta/leads \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "email": "creator@example.com",
    "persona": "creator",
    "use_case": "영상 편집용 PC와 노트북 추천을 반복해서 비교",
    "company_size": "freelancer",
    "contact_consent": true,
    "source": "readme"
  }'
```

```bash
curl http://127.0.0.1:8000/beta/leads \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

운영 지표:

```bash
curl http://127.0.0.1:8000/ops/metrics \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

분석 품질/비용 감사:

```bash
curl http://127.0.0.1:8000/ops/quality \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

저장된 trace 목록:

```bash
curl http://127.0.0.1:8000/ops/traces \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

trace span 조회:

```bash
curl http://127.0.0.1:8000/ops/traces/trace_xxxxxxxxxxxx/spans \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

### 소스 어댑터 상태와 수집

```bash
curl http://127.0.0.1:8000/sources/status
```

```bash
curl -X POST http://127.0.0.1:8000/sources/collect \
  -H "Content-Type: application/json" \
  -d '{
    "query": "영상 편집과 게임용 데스크톱 200만원 QHD 144Hz",
    "category": "desktop_pc",
    "limit": 12
  }'
```

실제 상품 페이지 URL 또는 운영자가 보관한 HTML 스냅샷을 후보 근거로 인입합니다. 내부망/private IP URL은 차단하고, 인입된 근거는 항상 관리자 검수 큐에 들어갑니다.

```bash
curl -X POST http://127.0.0.1:8000/sources/ingest-url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/product/creator-pc",
    "category": "desktop_pc",
    "kind": "price",
    "expected_model": "Creator RTX 4070 PC",
    "seller": "Example Store",
    "html": "<html><title>Creator RTX 4070 PC</title><body>최종 결제 금액 1,899,000원</body></html>"
  }'
```

반복 확인이 필요한 상품 URL은 모니터로 등록하고 refresh 실행 이력을 남깁니다.

```bash
curl -X POST http://127.0.0.1:8000/sources/monitors \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "url": "https://example.com/product/creator-pc",
    "category": "desktop_pc",
    "kind": "price",
    "expected_model": "Creator RTX 4070 PC",
    "seller": "Example Store",
    "cadence_minutes": 180,
    "html_snapshot": "<html><title>Creator RTX 4070 PC</title><body>최종 결제 금액 1,899,000원</body></html>"
  }'
```

```bash
curl -X POST http://127.0.0.1:8000/sources/refresh \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{"limit": 20}'
```

```bash
curl http://127.0.0.1:8000/sources/refresh-runs \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

`cadence_minutes`와 `last_run_at` 기준으로 지금 실행해야 할 모니터만 확인하고 실행합니다. 이 API는 cron, GitHub Actions, Cloud Scheduler 같은 외부 스케줄러에서 호출하기 위한 운영 경계입니다.

```bash
curl http://127.0.0.1:8000/sources/schedule \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

```bash
curl -X POST http://127.0.0.1:8000/sources/refresh-due \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{"limit": 20}'
```

실제 live fetch는 provider 정책이 승인된 host만 허용합니다. 정책이 없거나 robots/약관 검토가 승인되지 않았거나 시간당 rate limit을 넘으면 차단됩니다.

```bash
curl -X POST http://127.0.0.1:8000/sources/providers \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "provider_name": "Example Store",
    "host_pattern": "example.com",
    "kind": "price",
    "live_fetch_allowed": true,
    "robots_status": "approved",
    "terms_status": "approved",
    "credential_status": "operator_reviewed",
    "rate_limit_per_hour": 30,
    "notes": "robots와 약관 검토 완료"
  }'
```

```bash
curl -X POST http://127.0.0.1:8000/sources/providers/check \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{"url": "https://shop.example.com/product/creator-pc"}'
```

관리자 검수 화면:

```text
http://127.0.0.1:8000/admin
```

관리자 검수 API:

```bash
curl http://127.0.0.1:8000/admin/dashboard
```

## 분석 워크플로

LangGraph 노드는 다음 순서로 실행됩니다.

1. Intent Parser - 요청을 예산, 목적, 카테고리, 필수 조건으로 구조화
2. Clarifier - 예산, 해상도, 휴대성, 조립 여부의 모호성 확인
3. Query Planner - 가격, 스펙, 리뷰, 벤치마크 검색 계획 생성
4. Product Collector - 데스크톱 견적 또는 노트북 후보 5개 수집
5. Deduplicator - 모델명과 옵션 차이 정규화
6. Compatibility Checker - 소켓, 파워, 케이스, RAM, 노트북 휴대성 검증
7. Price Tracker - 배송비, 조립비, 쿠폰, 카드 할인 반영
8. Review Analyzer - 장점, 단점, 반복 불만, 리스크 신호 요약
9. Scoring Engine - 목적별 가중치로 종합 점수 산출
10. Verifier - 출처, 가격 시점, 호환성, 벤치마크 근거 확인
11. Report Writer - TOP 3, 제외 후보, 비교표, 가격 알림 생성

## 점수 가중치

| 평가 축 | 가중치 | 설명 |
|---|---:|---|
| 목적 적합도 | 35% | 게임, 영상 편집, 개발, 사무 목적에 맞는 구성 |
| 가격 경쟁력 | 22% | 예산 대비 실구매가, 배송비, 조립비, 쿠폰 반영 |
| 리뷰 신뢰도 | 15% | 반복 불만, 장기 사용 후기, 리스크 신호 |
| 구매 안정성 | 10% | 판매처 유형, 재고, 할인 조건 |
| 호환성 | 10% | 소켓, 파워, 폼팩터, 업그레이드 여지 |
| 개인 선호 | 8% | 필수 조건과 제외 조건 반영 |

## 응답에서 봐야 할 핵심 필드

- `/intake/diagnose.readiness_score`: 분석 준비도 점수
- `/intake/diagnose.clarifying_questions`: 분석 전 되물어볼 핵심 질문
- `/intake/diagnose.normalized_request`: 추천 조건을 보강한 분석 요청
- `report.top_recommendations`: 최종 추천 TOP 3
- `report.excluded_products`: 제외 후보 2개와 이유
- `report.comparison_table`: 추천/제외 후보 5개 비교표
- `report.compatibility_checks`: 후보별 호환성 세부 체크
- `report.benchmark_evidence`: 성능 근거
- `report.price_alerts`: 목표가와 재조회 주기
- `report.purchase_decision`: 구매 판정, 확신도, 위험 플래그, 다음 행동
- `report.scenario_options`: 예산 절감, 성능 우선, 안전 우선 대안 비교
- `report.criteria_matches`: 후보별 필수/제외 조건 충족률, 경고, 차단 사유
- `report.stress_tests`: 예산 축소/확대와 조건 강화 시 유지, 변경, 대기 판단
- `report.deal_windows`: 후보별 현재가, 목표가, 적정가 밴드, 변동 리스크, 결제 트리거
- `report.evidence_packs`: 후보별 가격, 리뷰, 벤치마크, 호환성, 출처 신뢰 근거 묶음
- `report.option_audits`: 후보별 핵심 사양 기대값, 확인 방법, 옵션 불일치 리스크
- `report.share_brief`: 공유받은 사람이 바로 검토할 판정, 핵심 근거, 리스크, 질문, 복사용 문구
- `report.execution_plan`: 결제 전 실행 단계, 판매자 질문, 공유 검토 문구
- `report.source_health`: 출처 상태 요약
- `report.source_trust`: 출처별 신뢰 등급, 신뢰도, 캐시 TTL, 검수 필요 여부
- `report.trust_policy`: 가격 캐시, 제휴 고지, 공정성, 리뷰 표현 정책
- `quality_audit`: 분석 품질 점수, 예상 소스 호출, 예상 토큰/비용, 공개 차단 사유
- `trace_events`: Agent 단계별 실행 로그
- `/ops/traces`: 워크스페이스별 저장 trace 요약, span 수, 품질 점수
- `/ops/traces/{trace_id}/spans`: 단계별 trace span 저장 이력
- `share_token`, `shared_at`, `share_views`: 저장 리포트 공개 공유 상태
- `feedback_count`, `average_satisfaction`, `purchase_intent_rate`: 추천 결과가 실제 구매 판단으로 이어지는지 보는 운영 지표
- `beta_leads`: 베타 신청 리드 수
- `alert_channels`, `alert_delivery_attempts`, `sent_alert_deliveries`, `failed_alert_deliveries`: 알림 발송 채널과 dispatch 운영 지표
- `trace_spans`: 별도 저장된 LangGraph 단계 span 수

## 로컬 저장소

분석 실행, trace span, 저장 리포트, 공유 토큰, 가격 알림 구독, 알림 채널, 발송 큐, 발송 시도, 사용자 피드백, 베타 리드는 기본적으로 SQLite에 저장됩니다.
저장 리포트, 공유 토큰, 알림, 발송 채널, 피드백, 리드는 `X-SpecPilot-Key`에서 계산된 워크스페이스 단위로 분리됩니다. 공개 리포트는 공유 토큰이 발급된 단일 리포트만 조회할 수 있습니다.

기본 경로:

```text
.specpilot/specpilot.sqlite3
```

환경 변수로 변경할 수 있습니다.

```bash
STORAGE_PATH=/data/specpilot.sqlite3
```

## Neo4j 선택 실행

기본값은 `DEMO_MODE=true`라서 Neo4j 없이도 실행됩니다.

Neo4j를 연결하려면:

```bash
docker compose up -d neo4j
```

환경 변수:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=specpilot-password
DEMO_MODE=false
```

그래프 스키마:

```text
http://127.0.0.1:8000/graph/schema
```

## 테스트

```bash
source .venv/bin/activate
pytest -q
```

전체 품질 게이트:

```bash
make verify
```

Docker 이미지 빌드:

```bash
make docker-build
```

현재 테스트는 다음을 검증합니다.

- 데스크톱 PC 분석이 TOP 3와 제외 후보 2개를 반환하는지
- 노트북 분석이 호환성 체크와 벤치마크 근거를 포함하는지
- Neo4j 구매 그래프 스키마가 핵심 노드/관계를 갖는지
- 루트 웹 UI가 표시되는지
- `/intake/diagnose`가 누락 조건, 추가 질문, 정규화 요청을 반환하는지
- `/analyze`, `/alerts/preview`, `/traces/{trace_id}`가 동작하는지
- `/reports/save`, `/reports/{report_id}`, `/alerts/subscribe`, `/ops/metrics`가 동작하는지
- `/reports/{report_id}/share`, `/public/reports/{share_token}`, `/r/{share_token}`이 공개 공유 리포트를 만들고 해제하는지
- `/alerts/evaluate`, `/alerts/events`가 목표가 도달 이벤트를 저장하고 격리하는지
- `/alerts/channels`, `/alerts/dispatch`, `/alerts/deliveries`가 발송 채널 설정, 큐 발송, 발송 시도 기록을 워크스페이스별로 처리하는지
- `/ops/traces`, `/ops/traces/{trace_id}/spans`가 저장 trace와 단계별 span을 워크스페이스별로 반환하는지
- `/feedback`, `/beta/leads`가 만족도와 베타 리드를 저장하고 워크스페이스별로 격리하는지
- `/ops/quality`가 품질 감사와 예상 비용을 워크스페이스별로 반환하는지
- `/sources/status`, `/sources/collect`, `/sources/ingest-url`, `/sources/monitors`, `/sources/schedule`, `/sources/refresh`, `/sources/refresh-due`, `/sources/refresh-runs`, `/sources/providers`, `/sources/providers/check`, `/admin/reviews`, `/admin/dashboard`가 동작하는지
- `/policy/trust`가 캐시, 제휴 고지, 공정성 정책을 반환하는지
- `/health`, `/ready` 운영 엔드포인트가 동작하는지

## CI

GitHub Actions는 `main` push와 PR에서 다음을 실행합니다.

- Python 3.12 설치
- `ruff check .`
- `pytest -q`
- Docker 이미지 빌드

## 운영 원칙

- 가격은 수집 시각과 출처를 함께 보여줍니다.
- 분석 전 조건 진단으로 예산, 목적, 필수 조건, 카테고리별 맥락이 부족한 요청을 먼저 보강합니다.
- 가격 소스는 캐시 TTL과 만료 시 재확인 정책을 함께 보여줍니다.
- 리뷰는 확정 판단이 아니라 리스크 신호로 표현합니다.
- 후보별 근거 팩은 가격 계산식, 리뷰 근거 수, 벤치마크, 호환성 검증을 한 카드로 보여줍니다.
- 옵션/사양 검수표는 판매 페이지 옵션명, 장바구니 구성표, 최종 결제 화면을 같은 기대값으로 대조하게 합니다.
- 공유용 검토 브리프는 공개 리포트를 받은 사람이 긴 리포트 전에 판정, 리스크, 질문을 먼저 확인하게 합니다.
- 출처 없는 스펙이나 가격은 추천 근거로 사용하지 않습니다.
- 외부 URL 인입은 내부망/private IP를 차단하고 실제 추천 반영 전에 검수 큐를 거칩니다.
- URL 모니터 refresh는 성공/실패, live fetch 여부, 연결된 검수 항목을 이력으로 남깁니다.
- due refresh는 `cadence_minutes`와 마지막 실행 시각을 기준으로 지금 실행할 모니터만 처리합니다.
- live fetch는 provider 정책, robots/약관 승인, 시간당 rate limit을 통과해야 실행됩니다.
- 특정 판매처 편향을 줄이기 위해 가격, 호환성, 리뷰, 안정성 점수를 분리합니다.
- 제휴 링크를 붙일 경우 추천 기준과 제휴 고지를 분리해서 노출해야 합니다.
- 신뢰도 0.8 미만 또는 리스크 플래그가 있는 근거는 관리자 검수 큐에 넣습니다.
- 공개 전 품질 점수, 경고 수, 차단 사유, 예상 비용을 운영 콘솔에서 확인합니다.
- 각 분석의 LangGraph 단계는 별도 trace span으로 저장해 운영 콘솔에서 품질 점수와 함께 추적합니다.
- 공개 공유 리포트는 토큰 기반으로 열고, 워크스페이스 소유자만 공유를 생성하거나 해제합니다.
- 구매 판정은 점수만으로 결정하지 않고 가격 목표가, 호환성 차단, 출처 검수 필요 여부를 함께 봅니다.
- 최종 1순위만 강요하지 않고 예산, 성능, 안전 우선 대안을 함께 보여줍니다.
- 사용자가 입력한 필수 조건과 제외 조건은 후보별 충족 매트릭스로 다시 검증합니다.
- 구매 타이밍 윈도우는 현재가, 목표가, 적정가 밴드, 쿠폰/재고 변동 리스크를 묶어 지금 결제할지 기다릴지 판단하게 합니다.
- 구매 실행 패키지는 결제 전 확인, 판매자 문의, 주변 검토 공유까지 한 흐름으로 제공합니다.
- 목표가 도달 알림은 발송 큐와 채널별 dispatch 시도를 남기고 실패 시 재시도 기준을 함께 저장합니다.
- 연락처와 이메일 원문은 저장하지 않고 마스킹된 값만 운영 콘솔에 노출합니다.
- 추천 만족도와 구매 의향은 모델 개선 신호로 쓰되 추천 순위에는 즉시 반영하지 않습니다.

## 다음 제품화 과제

- 가격 비교/오픈마켓/공식 스토어의 공식 provider 계약과 외부 cron/Cloud Scheduler 배포 연결
- 실제 이메일/SMS/웹훅 provider credential 연결과 운영 rate limit 적용
- LangSmith 또는 OpenTelemetry 외부 export 연동
- 실제 구매 시나리오 베타 테스트
