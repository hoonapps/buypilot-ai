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
- LangGraph 기반 11단계 구매 분석 워크플로
- 데스크톱/노트북 후보 카탈로그
- 모델 정규화와 중복 제거
- 상세 호환성 체크
- 실구매가 계산
- 리뷰/벤치마크 근거 연결
- TOP 3 추천과 제외 후보 2개
- 비교표, 가격 알림 목표가, 구매 전 체크리스트
- 출처 신뢰도, 캐시 만료 기준, 제휴 고지 정책
- Agent trace 조회
- SQLite 기반 분석 결과 저장
- 저장 리포트 조회와 가격 알림 구독
- 목표가 도달 평가와 발송 큐 이벤트 저장
- 운영 지표 API
- 가격/리뷰/벤치마크/공식 스토어 소스 어댑터 계약
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

운영 지표:

```bash
curl http://127.0.0.1:8000/ops/metrics \
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

- `report.top_recommendations`: 최종 추천 TOP 3
- `report.excluded_products`: 제외 후보 2개와 이유
- `report.comparison_table`: 추천/제외 후보 5개 비교표
- `report.compatibility_checks`: 후보별 호환성 세부 체크
- `report.benchmark_evidence`: 성능 근거
- `report.price_alerts`: 목표가와 재조회 주기
- `report.source_health`: 출처 상태 요약
- `report.source_trust`: 출처별 신뢰 등급, 신뢰도, 캐시 TTL, 검수 필요 여부
- `report.trust_policy`: 가격 캐시, 제휴 고지, 공정성, 리뷰 표현 정책
- `trace_events`: Agent 단계별 실행 로그

## 로컬 저장소

분석 실행, 저장 리포트, 가격 알림 구독은 기본적으로 SQLite에 저장됩니다.
저장 리포트와 알림은 `X-SpecPilot-Key`에서 계산된 워크스페이스 단위로 분리됩니다.

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
- `/analyze`, `/alerts/preview`, `/traces/{trace_id}`가 동작하는지
- `/reports/save`, `/reports/{report_id}`, `/alerts/subscribe`, `/ops/metrics`가 동작하는지
- `/alerts/evaluate`, `/alerts/events`가 목표가 도달 이벤트를 저장하고 격리하는지
- `/sources/status`, `/sources/collect`, `/admin/reviews`, `/admin/dashboard`가 동작하는지
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
- 가격 소스는 캐시 TTL과 만료 시 재확인 정책을 함께 보여줍니다.
- 리뷰는 확정 판단이 아니라 리스크 신호로 표현합니다.
- 출처 없는 스펙이나 가격은 추천 근거로 사용하지 않습니다.
- 특정 판매처 편향을 줄이기 위해 가격, 호환성, 리뷰, 안정성 점수를 분리합니다.
- 제휴 링크를 붙일 경우 추천 기준과 제휴 고지를 분리해서 노출해야 합니다.
- 신뢰도 0.8 미만 또는 리스크 플래그가 있는 근거는 관리자 검수 큐에 넣습니다.

## 다음 제품화 과제

- 실제 가격 비교/오픈마켓/공식 스토어 어댑터의 네트워크 커넥터 연결
- 실제 가격 알림 발송 채널 어댑터 연동
- LangSmith 또는 OpenTelemetry trace 저장
- 관리자용 분석 비용 대시보드
- 실제 구매 시나리오 베타 테스트
