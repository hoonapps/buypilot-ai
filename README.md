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
- 공유 자산 생성: 공개 리포트 URL 기준 카카오톡, 커뮤니티, 블로그/노션용 복사 문구와 OG 카드 메타 생성
- 후보별 근거 팩: 가격 계산, 리뷰 근거 수, 벤치마크, 호환성, 출처 신뢰 요약
- 옵션/사양 검수표: 판매 페이지 옵션명과 핵심 사양 대조
- 구매 판정: 구매 진행 가능, 가격 대기, 검수 후 구매
- 대안 시나리오: 예산 절감, 성능 우선, 안전 우선 비교
- 조건 충족 매트릭스: 필수 조건과 제외 조건의 충족/확인/차단 상태 비교
- 예산/조건 스트레스 테스트: 예산 10% 절감, 예산 10% 여유, 조건 강화 시 선택 변화 분석
- 구매 타이밍 윈도우: 후보별 적정가 밴드, 목표가, 변동 리스크, 결제 트리거
- 구매 실행 패키지: 결제 전 실행 단계, 판매자 확인 질문, 공유 검토 문구
- 결제 전 검수: 저장 리포트 기준 최종 결제 금액, 옵션/사양, 판매자 답변, 리스크 승인 상태를 기록하고 결제 가능/보류 판정
- 구매 링크 거버넌스: 저장 리포트 후보별 제휴/비제휴 구매 링크, 제휴 고지, 정책 경고, 클릭 리다이렉트 추적
- 구매 결과 추적: 저장 리포트가 실제 구매, 이탈, 지연, 반품/취소로 이어졌는지 기록하고 최종 결제 금액 차이와 학습 신호 집계
- 구매 의사결정 보드: 저장 리포트 여러 건의 결제 가능, 가격 대기, 검수 차단, 링크/결과 미기록 상태와 다음 액션을 한 화면에서 집계
- 학습 인사이트: 구매 결과, 결제 전 검수 차단, 사용자 피드백을 제품별 전환/반품/가격 신호로 묶어 개선 액션 추천
- 월간 카테고리 리포트: 데스크톱 PC/노트북 후보를 가격대, 추천 역할, 리스크, 워크스페이스 구매 신호로 묶어 공개 콘텐츠와 수익화 검증에 사용
- 공개 카테고리 리포트: 월간 데스크톱 PC/노트북 리포트를 SEO 제목, 공유 문구, CTA와 함께 API 키 없이 공개 발행
- 구매 온보딩 플레이북: 데스크톱/노트북/팀 구매 상황별 시작 질문, 필수 입력 슬롯, 검수 게이트, 분석 CTA를 공개 API로 제공
- 공개 구매 실패 방지 체크리스트: 카테고리, 예산, 구매자 상황별 필수 확인 항목, 위험 신호, 결제 전 증거 캡처, 분석 prefill을 공개 lead magnet으로 제공
- 첫 구매 진단 콘시어지: 입력 조건을 즉시 진단해 맞춤 온보딩 플레이북, 누락 질문, 분석/공유/검수 다음 행동으로 연결
- 성장 퍼널: 분석 결과 조회, 추천 카드 클릭, 대안 시나리오 클릭, 공유/알림/구독 CTA를 이벤트로 저장하고 출시 게이트에 반응 지표로 반영
- 공개 유입 허브: 데모, SEO 카테고리 리포트, 공유 리포트, 추천 대기열, Trust Center, 요금제 관심을 표면별 준비도와 채널 액션으로 집계
- 공개 전환 보드: 유입 허브, 성장 퍼널, 런치 Pulse, 추천 대기열, 요금제 관심, readiness를 한 snapshot으로 묶어 출시 직후 채널 배정과 병목 액션을 결정
- 리텐션 허브: 저장 리포트, 가격 알림, 공유 조회, 구매 상담, 구매 결과, 완료 리포트 반응을 재참여 점수와 플레이로 집계
- 추천 대기열: 가입자별 추천 코드와 공유 URL, 카카오톡/커뮤니티/이메일 공유 키트, 추천 보상 사다리, 공개 리더보드를 발급하고 추천 유입, 우선순위 점수로 공개 전 확산 루프를 검증
- 런치 반응 Pulse: 성장 이벤트, 만족도, 구매 의향, 추천 대기열, 요금제 관심, readiness를 합성해 공개 반응 온도와 다음 액션을 반환
- 출시 실험 허브: 공개 CTA 카피 variant를 만들고 노출/전환 이벤트, 승자 후보, 다음 실험 액션을 워크스페이스별로 집계
- 출시 캠페인 키트: 커뮤니티/검색/추천 채널별 공개 베타 카피, CTA 실험, 출시 체크리스트, 위험 고지, 측정 계획 생성
- 출시 배포 플래너: 런치 키트, 공개 전환 보드, Pulse, CTA 실험, 추천 대기열을 합쳐 D-day부터 D+7까지 채널별 배포 슬롯과 복사 문구 생성
- 공개 데모 갤러리: 데스크톱/크리에이터 노트북/팀 구매 시나리오를 한 번에 폼 적용 가능한 출시용 preset으로 제공
- 출처 신뢰도, 캐시 만료 기준, 제휴 고지 정책
- Agent trace 조회와 SQLite span 저장
- Observability export outbox: trace span과 품질 감사 payload를 OpenTelemetry/LangSmith 연동 전 큐로 저장하고 dispatch/retry 상태 추적
- 외부 연동 준비도: 가격 API, 오픈마켓, 공식 스토어, 이메일, 관측성, 제휴, scheduler provider의 mock/configured/verified/blocker 상태를 운영 게이트로 집계
- 프라이버시/데이터 거버넌스: 공개 개인정보 정책, 워크스페이스별 데이터 인벤토리, 보존 기간, 원문 연락처 표면을 출시 게이트에 반영
- 공개 Trust Center: 추천 공정성, 출처 검수, 개인정보 최소화, 사람 검수 기준과 구매자 권리/위험 고지를 한 응답으로 공개
- 공개 검증 허브: Trust Center, 시장 리포트, 공유 조회, 피드백, CTA 실험, 공개 유입 표면을 proof 카드와 출시 proof strip으로 집계
- 공개 소셜 proof wall: 마스킹 피드백, 실구매 결과, 추천 유입 리더보드를 랜딩에 바로 노출할 공개 반응 카드로 선별
- 공개 런칭룸: 데모 갤러리, 시장 리포트, proof strip, 유입/반응/추천/수익화 CTA를 외부 공유용 출시 페이지 패키지로 집계
- Next.js 공개 런칭 페이지: 웹사이트 `/launch`에서 런칭룸과 소셜 proof wall API를 읽어 제품 스크린샷 배경, 데모 CTA, 실제 반응 proof, 시장 리포트, 공유 문구를 외부 공유용 첫 화면으로 렌더링하고 추천 대기열과 요금제 관심을 즉시 저장
- Next.js 추천 초대 페이지: 제품 API가 발급하는 `/join?ref={referral_code}` 공유 URL을 초대 코드가 미리 채워진 대기열/요금제 관심 폼으로 연결하고, 가입 후 절대 초대 링크 복사/공유 액션을 성장 이벤트로 기록
- SQLite 기반 분석 결과 저장
- 저장 리포트 조회와 가격 알림 구독
- 저장 리포트 공개 공유 링크 생성과 공개 리포트 페이지
- 리포트 기반 구매 상담 Q&A: 저장 리포트에 가격, 호환성, 리스크, 비교, 결제 전 질문을 던지고 근거/다음 행동과 함께 답변 저장
- 완료 리포트 배치 발송: 저장 리포트를 이메일/웹훅/SMS outbox로 묶어 발송하고 미리보기, 성공/실패/재시도, 공개 추적 픽셀/클릭 리다이렉트, provider webhook, 반송/신고/수신 제외, 열람/클릭 상태 추적
- 목표가 도달 평가와 발송 큐 이벤트 저장
- 이메일/웹훅/SMS 알림 채널 설정, 발송 큐 dispatch, 발송 시도/재시도 기록
- 추천 만족도 피드백, 구매 의향, 선택 후보 저장
- 베타 신청 리드 저장과 개인정보 마스킹
- 요금제/구독 의향 수집: Free/Premium/Team 요금제, 관심 등록, 예상 MRR, 연환산 매출, 전환 준비 액션 추적
- 팀 구매 상담 키트: Team 관심 리드를 상담 브리프, 안건, ROI 포인트, 롤아웃 단계, 복사용 제안 메일로 전환
- 베타 출시 준비도 대시보드: 분석, 공유, 알림, 피드백, 리드, 품질 차단 사유를 launch readiness 점수로 집계
- 출시 게이트: readiness, 품질 회귀, 학습 인사이트, 백로그 SLA, 전환/발송/외부 연동 운영 상태로 공개 go/no-go 판정
- 베타 cohort 운영: 구매 시나리오별 리드, 피드백, 만족도, 구매 의향 집계
- 자동 개선 백로그: readiness 경고, 낮은 만족도, 품질 차단 사유, 제품별 학습 인사이트를 운영 항목으로 변환
- cohort 리포트 export: JSON/Markdown으로 베타 운영 리포트 출력
- 개선 백로그 운영 상태 관리: 담당자, 진행 상태, 운영 메모를 워크스페이스별로 저장
- 개선 백로그 SLA: severity별 기본 마감, 지연/마감임박 집계, 완료 요약 자동 저장
- 운영 지표 API
- 분석 품질 감사와 예상 비용 대시보드
- 품질 회귀 모니터: 최근/이전 분석 품질, 비용 변화, provider 차단율 비교
- 가격/리뷰/벤치마크/공식 스토어 소스 어댑터 계약
- 실제 상품 URL/HTML 스냅샷 인입과 관리자 검수 큐 등록
- URL 모니터 등록, 수집 refresh 실행, refresh 이력 추적
- Due schedule preview와 due 모니터 refresh 실행
- Source provider 정책: live fetch 허용 host, robots/약관 승인, 시간당 rate limit 게이트
- 관리자 검수 콘솔(`/admin`)
- 공개 신뢰 정책 API(`/policy/trust`)
- 공개 프라이버시 정책 API(`/policy/privacy`)
- 공개 Trust Center API(`/policy/trust-center`)
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

공개 웹사이트와 연결할 때는 추천 대기열 공유 URL이 바로 외부에 보낼 수 있는 절대 URL이 되도록 설정합니다.

```bash
PUBLIC_SITE_URL=https://specpilot-ai-site.vercel.app
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

### 구매 온보딩 플레이북

처음 온 사용자는 공개 플레이북으로 자기 상황에 맞는 시작 질문, 예산 힌트, 필수 입력 슬롯, 결제 전 검수 게이트를 먼저 확인할 수 있습니다.

```bash
curl "http://127.0.0.1:8000/public/onboarding/playbooks?category=laptop"
```

공개 구매 실패 방지 체크리스트는 카테고리, 예산, 구매자 상황을 받아 분석 전 필수 확인 항목, 결제 전 증거, 위험 신호, 분석 요청 prefill을 반환합니다.

```bash
curl "http://127.0.0.1:8000/public/buyer-checklist?category=desktop_pc&budget_krw=2200000&persona=creator_gamer"
```

첫 구매 진단 콘시어지는 현재 입력값을 진단하고 가장 가까운 플레이북, 누락 질문, 분석 실행, 공유/가격 대기, 결제 전 검수 다음 행동을 한 응답으로 반환합니다.

```bash
curl -X POST http://127.0.0.1:8000/public/start-concierge \
  -H "Content-Type: application/json" \
  -d '{
    "query": "출장이 많은 영상 편집자용 노트북을 골라줘. 2kg 이하, 32GB RAM, GPU 가속",
    "category": "laptop",
    "budget_krw": 2200000,
    "purpose": "출장 편집, Premiere Pro",
    "must_haves": ["2kg 이하", "32GB RAM", "외장 GPU"],
    "exclusions": ["중고", "리퍼", "발열 반복 불만"]
  }'
```

### 공개 데모 갤러리

첫 방문자가 빈 입력 폼에서 막히지 않도록 데스크톱, 휴대형 크리에이터 노트북, 팀 구매 시나리오를 바로 적용 가능한 분석 요청과 기대 결과, 공유 포인트로 제공합니다.

```bash
curl http://127.0.0.1:8000/demo/scenarios
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

### 프라이버시 정책과 데이터 거버넌스

공개 개인정보/보존 정책:

```bash
curl http://127.0.0.1:8000/policy/privacy
```

공개 Trust Center:

```bash
curl http://127.0.0.1:8000/policy/trust-center
```

공개 검증 허브:

```bash
curl http://127.0.0.1:8000/public/proof-hub \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

공개 소셜 proof wall:

```bash
curl http://127.0.0.1:8000/public/social-proof-wall \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

공개 런칭룸:

```bash
curl http://127.0.0.1:8000/public/launch-room \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

워크스페이스별 데이터 인벤토리와 보존/마스킹 상태:

```bash
curl http://127.0.0.1:8000/ops/data-governance \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
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

공개 리포트 JSON과 HTML에는 `conversion_cta`가 포함됩니다. 공유받은 사람은 같은 리포트에서 바로 “내 조건으로 분석 시작” 또는 “공개 베타 대기열 등록”으로 이동하고, 가입 후 본인 추천 코드를 발급받아 다시 초대 링크로 확산할 수 있습니다.

공유 자산 생성:

```bash
curl http://127.0.0.1:8000/reports/report_xxxxxxxxxxxx/share-assets \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

공유 해제:

```bash
curl -X DELETE http://127.0.0.1:8000/reports/report_xxxxxxxxxxxx/share \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

저장 리포트 기반 구매 상담:

```bash
curl -X POST http://127.0.0.1:8000/reports/report_xxxxxxxxxxxx/advisor-questions \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "question": "지금 결제해도 돼, 아니면 목표가까지 기다리는 게 좋아?",
    "context": "이번 주 안에는 구매 가능하지만 가격이 중요합니다.",
    "selected_product_id": "desktop_creator_4070",
    "buyer_stage": "pre_checkout",
    "contact": "buyer@example.com"
  }'
```

상담 이력 조회:

```bash
curl http://127.0.0.1:8000/reports/report_xxxxxxxxxxxx/advisor-questions \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

워크스페이스 전체 상담 이력:

```bash
curl http://127.0.0.1:8000/advisor-questions \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

결제 전 검수 생성:

```bash
curl -X POST http://127.0.0.1:8000/reports/report_xxxxxxxxxxxx/checkout-review \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "product_id": "desktop_creator_4070",
    "confirmed_price_krw": 1980000,
    "acknowledged_risks": [
      "가격 변동 가능성이 있어 결제 직전 재확인이 필요합니다."
    ],
    "seller_answers": {
      "주문 옵션명이 리포트의 CPU/GPU/RAM/SSD와 같은가요?": "동일 옵션 확인 완료"
    },
    "notes": "최종 주문 화면 캡처 보관 완료"
  }'
```

결제 전 검수 이력 조회:

```bash
curl http://127.0.0.1:8000/reports/report_xxxxxxxxxxxx/checkout-reviews \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

워크스페이스 전체 결제 검수 이력:

```bash
curl http://127.0.0.1:8000/checkout-reviews \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

구매 링크 등록:

```bash
curl -X POST http://127.0.0.1:8000/reports/report_xxxxxxxxxxxx/purchase-links \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "product_id": "desktop_creator_4070",
    "seller_name": "공식 스토어",
    "url": "https://shop.example.com/specpilot-desktop",
    "is_affiliate": false,
    "price_krw": 1990000,
    "shipping_fee_krw": 3000,
    "coupon_krw": 5000,
    "rank": 1,
    "notes": "비제휴 대안 링크"
  }'
```

구매 링크 거버넌스:

```bash
curl http://127.0.0.1:8000/reports/report_xxxxxxxxxxxx/purchase-link-governance \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

공개 리포트의 구매 링크는 `/buy/plink_xxxxxxxxxxxx` 내부 redirect를 거쳐 클릭 이벤트를 저장한 뒤 실제 판매처로 이동합니다. 제휴 링크가 있으면 같은 후보의 비제휴 대안을 함께 등록해야 하며, 제휴 링크만 단독 노출되면 governance가 blocker로 표시됩니다.

구매 결과 기록:

```bash
curl -X POST http://127.0.0.1:8000/reports/report_xxxxxxxxxxxx/purchase-outcomes \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "product_id": "desktop_creator_4070",
    "checkout_review_id": "checkout_xxxxxxxxxxxx",
    "status": "purchased",
    "final_paid_price_krw": 1990000,
    "source_channel": "checkout_review",
    "reason": "최종 주문 완료",
    "satisfaction": 5,
    "order_reference": "ORDER-2026-000123",
    "notes": "주문 화면 캡처 보관"
  }'
```

구매 결과 이력 조회:

```bash
curl http://127.0.0.1:8000/reports/report_xxxxxxxxxxxx/purchase-outcomes \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

워크스페이스 전체 구매 결과:

```bash
curl http://127.0.0.1:8000/purchase-outcomes \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

제품별 학습 인사이트:

```bash
curl http://127.0.0.1:8000/ops/learning-insights \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

완료 리포트 배치 발송:

```bash
curl -X POST http://127.0.0.1:8000/reports/completion-batches \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "report_ids": ["report_xxxxxxxxxxxx"],
    "channel": "email",
    "target": "ops@example.com",
    "note": "구매 완료 후보 운영 발송"
  }'
```

완료 리포트 batch 조회:

```bash
curl http://127.0.0.1:8000/reports/completion-batches \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

완료 리포트 템플릿 저장:

```bash
curl -X POST http://127.0.0.1:8000/reports/completion-templates \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "name": "운영 완료 리포트",
    "channel": "email",
    "subject": "[SpecPilot] {title}",
    "body": "{title}\n추천 1순위: {top_model_name}\n공개 리포트: {public_path}",
    "enabled": true
  }'
```

완료 리포트 수신자 그룹 저장:

```bash
curl -X POST http://127.0.0.1:8000/reports/completion-recipient-groups \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "name": "운영 수신자",
    "channel": "email",
    "recipients": ["ops@example.com", "buyer@example.com"],
    "unsubscribed_recipients": ["buyer@example.com"],
    "unsubscribe_policy": "exclude_unsubscribed"
}'
```

완료 리포트 미리보기:

```bash
curl -X POST http://127.0.0.1:8000/reports/completion-preview \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "report_id": "report_xxxxxxxxxxxx",
    "template_id": "template_xxxxxxxxxxxx",
    "recipient_group_id": "group_xxxxxxxxxxxx",
    "respect_unsubscribe": true
  }'
```

템플릿과 수신자 그룹을 사용하는 batch 발송:

```bash
curl -X POST http://127.0.0.1:8000/reports/completion-batches \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "report_ids": ["report_xxxxxxxxxxxx"],
    "template_id": "template_xxxxxxxxxxxx",
    "recipient_group_id": "group_xxxxxxxxxxxx",
    "respect_unsubscribe": true,
    "note": "운영 수신자 그룹 발송"
}'
```

완료 리포트 열람/클릭 이벤트 기록:

```bash
curl -X POST http://127.0.0.1:8000/reports/completion-deliveries/delivery_xxxxxxxxxxxx/engagement \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "event_type": "open",
    "metadata": {
      "source": "email_pixel"
    }
  }'
```

완료 리포트 열람/클릭 이벤트 조회:

```bash
curl http://127.0.0.1:8000/reports/completion-engagement \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

완료 리포트 발송 응답의 `tracking_pixel_path`와 `tracking_click_path`는 실제 이메일 provider에 삽입할 수 있습니다. 픽셀은 인증 없이 1x1 PNG를 반환하며 open 이벤트를 기록하고, 클릭 path는 안전한 상대 경로만 redirect 대상으로 허용합니다.

```bash
curl -I http://127.0.0.1:8000/t/o/trk_xxxxxxxxxxxxxxxxxxxxxxxx.png
```

```bash
curl -I 'http://127.0.0.1:8000/t/c/trk_xxxxxxxxxxxxxxxxxxxxxxxx?to=/r/share_xxxxxxxxxxxxxxxxxxxx'
```

완료 리포트 provider webhook 수집:

`COMPLETION_WEBHOOK_SECRET` 환경 변수로 운영 secret을 바꿀 수 있습니다.

```bash
curl -X POST http://127.0.0.1:8000/reports/completion-deliveries/provider-webhooks \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Webhook-Secret: specpilot-webhook-secret" \
  -d '{
    "tracking_token": "trk_xxxxxxxxxxxxxxxxxxxxxxxx",
    "provider_name": "email-provider",
    "event_type": "hard_bounce",
    "provider_message": "mailbox unavailable",
    "metadata": {
      "smtp_code": "550"
    }
  }'
```

완료 리포트 provider 이벤트 조회:

```bash
curl http://127.0.0.1:8000/reports/completion-provider-events \
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

요금제와 구독 의향을 확인합니다. 구독 의향은 이메일 원문을 저장하지 않고 마스킹된 값, 희망 요금제, 결제 주기, 팀 규모, 최대 예산, 기능 우선순위, 예상 MRR만 남깁니다.

```bash
curl http://127.0.0.1:8000/pricing/plans \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

```bash
curl -X POST http://127.0.0.1:8000/billing/subscription-intents \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "email": "buyer@example.com",
    "plan_id": "premium",
    "billing_cycle": "monthly",
    "persona": "individual_buyer",
    "use_case": "게이밍 PC 가격 알림과 결제 전 검수",
    "team_size": 1,
    "max_budget_krw": 20000,
    "feature_priorities": ["가격 알림", "저장 견적 비교", "결제 전 검수"],
    "purchase_timing": "within_30_days",
    "source": "readme"
  }'
```

```bash
curl http://127.0.0.1:8000/ops/pricing-dashboard \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

Team 구매 상담 키트를 확인합니다.

```bash
curl http://127.0.0.1:8000/ops/team-purchase-consult-kit \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

베타 공개 확대 가능성을 확인합니다.

```bash
curl http://127.0.0.1:8000/beta/readiness \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

공개 go/no-go 출시 게이트를 확인합니다.

```bash
curl http://127.0.0.1:8000/beta/launch-gate \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

시나리오별 베타 cohort를 만들고 개선 백로그를 확인합니다.

```bash
curl -X POST http://127.0.0.1:8000/beta/cohorts \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "name": "영상 편집 QHD 데스크톱 cohort",
    "scenario": "영상 편집과 QHD 144Hz 게임용 데스크톱",
    "category": "desktop_pc",
    "target_persona": "creator",
    "target_size": 10,
    "success_metric": "purchase_intent_rate",
    "keywords": ["영상 편집", "QHD", "데스크톱"],
    "notes": "공개 베타 검증 cohort"
  }'
```

```bash
curl http://127.0.0.1:8000/beta/cohorts \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

```bash
curl http://127.0.0.1:8000/beta/backlog \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

개선 백로그를 운영 상태로 전환하고 SLA/완료 요약을 관리합니다.

```bash
curl -X PATCH http://127.0.0.1:8000/beta/backlog/backlog_readiness_lead \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "status": "in_progress",
    "assignee": "ops",
    "note": "크리에이터 베타 리드 모집 캠페인 진행",
    "sla_due_at": "2026-06-21T09:00:00+00:00"
  }'
```

```bash
curl -X PATCH http://127.0.0.1:8000/beta/backlog/backlog_readiness_lead \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "status": "done",
    "assignee": "ops",
    "note": "베타 리드 10명 모집 완료",
    "completion_summary": "크리에이터 cohort 리드 모집 완료"
  }'
```

```bash
curl http://127.0.0.1:8000/beta/backlog/summary \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

cohort 리포트를 export합니다.

```bash
curl http://127.0.0.1:8000/beta/cohorts/{cohort_id}/report \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

```bash
curl http://127.0.0.1:8000/beta/cohorts/{cohort_id}/report.md \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

운영 지표:

```bash
curl http://127.0.0.1:8000/ops/metrics \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

성장 퍼널 이벤트 저장과 대시보드:

```bash
curl -X POST http://127.0.0.1:8000/growth/events \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "event_type": "recommendation_click",
    "trace_id": "trace_xxx",
    "product_id": "desktop-001",
    "surface": "recommendation-card",
    "label": "TOP 1 추천 카드"
  }'
```

```bash
curl http://127.0.0.1:8000/growth/funnel \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

공개 유입 허브:

```bash
curl http://127.0.0.1:8000/growth/acquisition-hub \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

공개 전환 보드:

```bash
curl http://127.0.0.1:8000/growth/public-conversion-board \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

리텐션 허브:

```bash
curl http://127.0.0.1:8000/growth/retention-hub \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

추천 대기열과 리더보드:

`PUBLIC_SITE_URL`이 설정되어 있으면 `referral_url`은 `https://.../join?ref=...` 형태의 절대 초대 링크로 반환됩니다. 설정하지 않으면 로컬 개발용 상대 경로 `/join?ref=...`를 유지합니다.

```bash
curl -X POST http://127.0.0.1:8000/growth/waitlist-referrals \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "email": "creator@example.com",
    "persona": "creator",
    "use_case": "영상 편집용 PC 구매 비교를 친구에게 공유하고 싶습니다.",
    "referred_by_code": "",
    "source": "readme"
  }'
```

```bash
curl http://127.0.0.1:8000/growth/referral-dashboard \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

공개 추천 리더보드:

```bash
curl 'http://127.0.0.1:8000/growth/referral-leaderboard?referral_code=CREA-ABC123' \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

추천 초대 공유 키트:

```bash
curl http://127.0.0.1:8000/growth/referral-share-kit/CREA-ABC123 \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

추천 보상 사다리:

```bash
curl http://127.0.0.1:8000/growth/referral-rewards/CREA-ABC123 \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

런치 반응 Pulse:

```bash
curl http://127.0.0.1:8000/growth/launch-pulse \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

출시 실험 허브:

```bash
curl -X POST http://127.0.0.1:8000/growth/launch-experiments \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "name": "커뮤니티 첫 분석 CTA",
    "channel": "community",
    "audience": "desktop_pc_buyer",
    "hypothesis": "구매 실패 방지 메시지가 빠른 진단 메시지보다 전환이 높다.",
    "primary_metric": "subscription_cta",
    "target_surface": "community-post",
    "category": "desktop_pc",
    "variants": [
      {
        "label": "구매 실패 방지",
        "headline": "200만원 PC 견적, 결제 전에 실패 가능성을 줄이세요",
        "body": "가격 타이밍, 호환성, 결제 전 검수까지 한 번에 확인합니다.",
        "cta_label": "구매 전 검수하기",
        "cta_path": "/#start-concierge",
        "allocation_percent": 50
      },
      {
        "label": "3분 빠른 진단",
        "headline": "컴퓨터 견적 고민을 3분 안에 줄이세요",
        "body": "용도와 예산을 넣으면 후보와 가격 대기 여부를 보여줍니다.",
        "cta_label": "3분 진단 시작",
        "cta_path": "/",
        "allocation_percent": 50
      }
    ]
  }'
```

```bash
curl http://127.0.0.1:8000/growth/launch-experiment-dashboard \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

출시 캠페인 키트:

```bash
curl 'http://127.0.0.1:8000/growth/launch-kit?category=desktop_pc&audience=creator'
```

출시 배포 플랜:

```bash
curl 'http://127.0.0.1:8000/growth/launch-distribution-plan?category=desktop_pc&audience=creator' \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

분석 품질/비용 감사:

```bash
curl http://127.0.0.1:8000/ops/quality \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

출시 후 품질 회귀와 provider 차단율을 확인합니다.

```bash
curl "http://127.0.0.1:8000/ops/regression?window_size=5" \
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

observability export outbox 적재:

```bash
curl -X POST http://127.0.0.1:8000/ops/observability/exports \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "trace_id": "trace_xxxxxxxxxxxx",
    "destination": "opentelemetry",
    "include_payload": true
  }'
```

observability export outbox 조회:

```bash
curl http://127.0.0.1:8000/ops/observability/exports \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY"
```

observability export dispatch:

```bash
curl -X POST http://127.0.0.1:8000/ops/observability/dispatch \
  -H "Content-Type: application/json" \
  -H "X-SpecPilot-Key: $SPECPILOT_KEY" \
  -d '{
    "dry_run": false,
    "limit": 50
  }'
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

실제 상품 페이지 URL 또는 운영자가 보관한 HTML 스냅샷을 후보 근거로 인입합니다. 내부망/private IP URL과 사용자 정보가 포함된 URL은 차단하고, 인입된 근거는 항상 관리자 검수 큐에 들어갑니다. 인입 결과에는 표시 가격, 배송비, 쿠폰/카드 할인, 추정 실구매가, 재고 상태, 기대 모델명 일치도, 추출 신호가 포함됩니다.

```bash
curl -X POST http://127.0.0.1:8000/sources/ingest-url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/product/creator-pc",
    "category": "desktop_pc",
    "kind": "price",
    "expected_model": "Creator RTX 4070 PC",
    "seller": "Example Store",
    "html": "<html><title>Creator RTX 4070 PC</title><body>최종 결제 금액 1,899,000원 무료배송 카드 할인 50,000원 재고 있음</body></html>"
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
- `/public/start-concierge`: 입력 진단, 맞춤 온보딩 플레이북, 시작 마일스톤, 빠른 CTA를 묶은 첫 구매 경로
- `/demo/scenarios`: 첫 방문자가 10초 안에 분석 폼을 채우는 공개 데모 갤러리, preset 요청, 기대 결과, 공유 포인트
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
- `/ops/observability/exports`: trace span과 품질 감사 payload를 외부 observability 연동 전 outbox로 저장한 이력
- `/ops/observability/dispatch`: queued/failed observability export를 OpenTelemetry/LangSmith exporter outbox로 dispatch하고 성공/실패/재시도 상태를 저장
- `/ops/integrations`: 외부 연동 provider의 category, credential 상태, rate limit, 보존 기간, 운영 증거를 워크스페이스별로 저장
- `/ops/integration-readiness`: 가격 API, 오픈마켓, 공식 스토어, 이메일, observability, scheduler 등 공개 전 필수 연동의 mock/configured/verified/blocker 상태와 필수 액션을 집계
- `/policy/privacy`: 저장 데이터 범위, 마스킹, 보존 기간, 사용자 제어, 금지 데이터를 공개 정책으로 반환
- `/policy/trust-center`: 추천 공정성, 출처 검수, 개인정보 최소화, 사람 검수 게이트, 구매자 권리, 위험 고지, 다음 액션을 공개 신뢰 대시보드로 반환
- `/public/proof-hub`: Trust Center, 공개 시장 리포트, 공유 조회, 피드백, 출시 CTA 실험, 공개 유입 표면을 공개 proof 카드, hero proof strip, evidence kit, 반박 답변으로 집계
- `/public/social-proof-wall`: 만족도 높은 마스킹 피드백, 구매 결과, 추천 유입 리더보드를 랜딩용 공개 proof 카드, 신뢰 고지, CTA로 선별
- `/public/launch-room`: 데모 갤러리, 공개 시장 리포트, proof strip, 유입 허브, 런치 Pulse, 추천 대기열, 요금제 관심을 외부 공유용 런칭룸 카드로 집계
- `/ops/team-purchase-consult-kit`: Team 요금제 관심 리드를 상담 브리프, 확인 입력, ROI 포인트, 롤아웃 단계, 제안 메일 초안으로 집계
- `/ops/data-governance`: 워크스페이스별 테이블 인벤토리, 원문 연락처 표면, 마스킹 표면, 보존 초과 액션을 집계
- `share_token`, `shared_at`, `share_views`: 저장 리포트 공개 공유 상태
- `/reports/{report_id}/share-assets`: 공개 리포트 URL, 구매 판정, 최종 후보, 검토 질문을 조합해 카카오톡/커뮤니티/블로그 공유 문구와 OG 메타를 생성
- `/reports/{report_id}/purchase-links`, `/reports/{report_id}/purchase-link-governance`, `/buy/{link_id}`: 후보별 제휴/비제휴 구매 링크, 제휴 고지, 비제휴 대안 정책 경고, 공개 클릭 redirect와 클릭 지표
- `/public/market/category-reports/{category}`: 데스크톱 PC/노트북 월간 카테고리 리포트를 SEO 제목, canonical path, 공유 문구, CTA 카드와 함께 공개 조회
- `/public/onboarding/playbooks`: 데스크톱 PC, 휴대형 노트북, 팀 구매자용 시작 질문, 예산 힌트, 필수 입력 슬롯, 신뢰 검수 게이트, 분석 CTA를 공개 조회
- `/public/buyer-checklist`: 카테고리/예산/구매자 상황별 구매 실패 방지 체크리스트, 결제 전 증거, 위험 신호, 분석 prefill을 공개 조회
- `/reports/completion-templates`, `/reports/completion-recipient-groups`, `/reports/completion-preview`, `/reports/completion-batches`, `/reports/completion-engagement`, `/reports/completion-provider-events`, `/reports/completion-deliveries/provider-webhooks`, `/t/o/{tracking_token}.png`, `/t/c/{tracking_token}`: 완료 리포트 템플릿, 수신자 그룹, unsubscribe 제외, 발송 전 렌더링 미리보기, batch와 개별 delivery 성공/실패/재시도/열람/클릭/반송/신고/수신 제외 상태, provider 삽입용 공개 추적 픽셀/클릭 리다이렉트
- `purchase_outcomes`, `completed_purchase_outcomes`, `purchase_conversion_rate`, `average_final_price_delta_krw`, `purchase_outcome_value_krw`: 실제 구매 결과와 최종 결제 금액 차이를 보는 운영 지표
- `/ops/learning-insights`: 실제 구매 결과, 결제 전 검수 차단, 만족도 피드백을 제품별 전환율, 반품률, 가격 차이, 개선 액션으로 집계
- `/growth/events`, `/growth/funnel`: 추천 카드, 대안 시나리오, 공유 리포트, 가격 알림, 요금제 CTA 반응을 저장하고 단계별 전환율과 다음 액션을 집계
- `/growth/acquisition-hub`: 공개 데모, SEO 카테고리 리포트, 공유 리포트, 추천 대기열, Trust Center, 요금제 관심 표면의 준비도와 채널별 액션을 집계
- `/growth/public-conversion-board`: 공개 유입 허브, 성장 퍼널, 런치 Pulse, 추천 대기열, 요금제 관심, readiness를 전환 점수, 단계별 병목, 우선 표면, 채널 액션으로 합성
- `/growth/retention-hub`: 저장 리포트, 가격 알림, 공개 조회, 구매 상담, 구매 결과, 완료 리포트 engagement를 재참여 신호, 플레이, 다음 액션으로 집계
- `/growth/waitlist-referrals`, `/growth/referral-dashboard`, `/growth/referral-leaderboard`, `/growth/referral-share-kit/{referral_code}`, `/growth/referral-rewards/{referral_code}`: 추천 대기열 가입, 추천 코드/공유 URL, `PUBLIC_SITE_URL` 기반 절대 초대 링크, 공개 추천 순위, 카카오톡/커뮤니티/이메일 공유 문구, 추천 보상 사다리, 추천 유입 수, 우선순위 점수를 워크스페이스별로 집계
- `/growth/launch-pulse`: 성장 이벤트, 피드백, 추천 대기열, 요금제 관심, readiness를 합성해 공개 반응 Pulse 점수와 다음 액션을 반환
- `/growth/launch-experiments`, `/growth/launch-experiments/{experiment_id}/events`, `/growth/launch-experiment-dashboard`: 공개 CTA variant, 노출/전환 이벤트, 승자 후보, 다음 실험 액션을 관리
- `/growth/launch-kit`: 공개 베타 채널별 카피, CTA 실험, 출시 체크리스트, 위험 고지, 측정 계획을 반환
- `/growth/launch-distribution-plan`: 런치 키트, 공개 전환 보드, 런치 Pulse, CTA 실험, 추천 대기열을 합성해 첫 주 채널 배포 슬롯, 복사 문구, 측정 이벤트, 위험 통제를 반환
- `/beta/launch-gate`: readiness, 품질 회귀, 학습 인사이트, 백로그 SLA, 전환/성장/발송/외부 연동/데이터 거버넌스 운영 상태를 공개 go/no-go 판정과 필수 액션으로 집계
- `feedback_count`, `average_satisfaction`, `purchase_intent_rate`: 추천 결과가 실제 구매 판단으로 이어지는지 보는 운영 지표
- `beta_leads`: 베타 신청 리드 수
- `alert_channels`, `alert_delivery_attempts`, `sent_alert_deliveries`, `failed_alert_deliveries`: 알림 발송 채널과 dispatch 운영 지표
- `growth_events`, `recommendation_card_clicks`, `alternative_scenario_clicks`, `share_cta_clicks`, `alert_cta_clicks`, `subscription_cta_clicks`: 공개 후 제품 반응과 CTA 전환을 보는 성장 퍼널 지표
- `trace_spans`: 별도 저장된 LangGraph 단계 span 수

## 로컬 저장소

분석 실행, trace span, observability export outbox, 외부 연동 준비도, 데이터 거버넌스 인벤토리, 저장 리포트, 공유 토큰, 완료 리포트 템플릿/수신자 그룹/batch/delivery/engagement/provider event, 가격 알림 구독, 알림 채널, 발송 큐, 발송 시도, 성장 퍼널 이벤트, 사용자 피드백, 베타 리드, 출시 게이트 판단 근거는 기본적으로 SQLite에 저장된 운영 신호에서 계산됩니다.
저장 리포트, 공유 토큰, 외부 연동 provider, 완료 리포트 템플릿/수신자 그룹/batch/engagement/provider event, 알림, 발송 채널, 피드백, 리드는 `X-SpecPilot-Key`에서 계산된 워크스페이스 단위로 분리됩니다. 공개 리포트는 공유 토큰이 발급된 단일 리포트만 조회할 수 있습니다.

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
- `/reports/{report_id}/share`, `/reports/{report_id}/share-assets`, `/public/reports/{share_token}`, `/r/{share_token}`이 공개 공유 리포트, 전환 CTA, 채널별 공유 문구를 만들고 해제하는지
- `/reports/{report_id}/advisor-questions`, `/advisor-questions`가 저장 리포트 기반 구매 상담 답변, 근거, 다음 행동, 워크스페이스 격리를 처리하는지
- `/reports/{report_id}/checkout-review`, `/reports/{report_id}/checkout-reviews`, `/checkout-reviews`가 결제 전 검수와 워크스페이스 격리를 처리하는지
- `/reports/{report_id}/purchase-links`, `/reports/{report_id}/purchase-link-governance`, `/buy/{link_id}`가 제휴/비제휴 구매 링크, 정책 경고, 공개 클릭 redirect, 클릭 지표를 처리하는지
- `/reports/{report_id}/purchase-outcomes`, `/purchase-outcomes`가 실제 구매, 이탈, 지연, 반품/취소 결과와 최종가 차이를 저장하고 워크스페이스별로 격리하는지
- `/ops/learning-insights`가 구매 결과, 결제 검수, 피드백을 제품별 전환/리스크/개선 액션으로 묶고 워크스페이스별로 격리하는지
- `/reports/completion-preview`, `/reports/completion-batches`, `/reports/completion-engagement`, `/reports/completion-provider-events`, `/reports/completion-deliveries/provider-webhooks`, `/t/o/{tracking_token}.png`, `/t/c/{tracking_token}`가 완료 리포트 미리보기, batch, delivery, 공개 추적 픽셀/클릭 리다이렉트, provider webhook, 열람/클릭/반송/신고/수신 제외 상태를 저장하고 워크스페이스별로 격리하는지
- `/alerts/evaluate`, `/alerts/events`가 목표가 도달 이벤트를 저장하고 격리하는지
- `/alerts/channels`, `/alerts/dispatch`, `/alerts/deliveries`가 발송 채널 설정, 큐 발송, 발송 시도 기록을 워크스페이스별로 처리하는지
- `/ops/traces`, `/ops/traces/{trace_id}/spans`가 저장 trace와 단계별 span을 워크스페이스별로 반환하는지
- `/ops/observability/exports`, `/ops/observability/dispatch`가 trace span과 품질 감사 payload를 outbox로 저장하고 dispatch/retry 상태를 워크스페이스별로 격리하는지
- `/feedback`, `/beta/leads`, `/beta/readiness`, `/beta/launch-gate`, `/beta/cohorts`, `/beta/backlog`가 만족도, 베타 리드, 출시 준비도, 공개 go/no-go, cohort, 개선 백로그를 워크스페이스별로 격리하는지
- `/growth/public-conversion-board`가 공개 유입, 활성화, 공유, 추천, 유료 수요, 안정성 단계를 워크스페이스별로 집계하고 격리하는지
- `/beta/backlog/{backlog_id}`, `/beta/backlog/summary`, `/beta/cohorts/{cohort_id}/report`, `/beta/cohorts/{cohort_id}/report.md`가 백로그 SLA/완료 요약과 cohort export를 워크스페이스별로 처리하는지
- `/ops/quality`가 품질 감사와 예상 비용을 워크스페이스별로 반환하는지
- `/ops/regression`이 최근/이전 품질 구간, 비용 변화, provider 차단율을 워크스페이스별로 집계하는지
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
- 제휴 링크를 붙일 경우 추천 기준과 제휴 고지를 분리해서 노출하고, 같은 후보의 비제휴 구매 대안을 함께 제공합니다.
- 공개 구매 링크는 내부 `/buy/{link_id}` redirect로 클릭을 기록하되, 추천 순위 계산에는 클릭 수나 제휴 여부를 직접 반영하지 않습니다.
- 신뢰도 0.8 미만 또는 리스크 플래그가 있는 근거는 관리자 검수 큐에 넣습니다.
- 공개 전 품질 점수, 경고 수, 차단 사유, 예상 비용을 운영 콘솔에서 확인합니다.
- 품질 회귀 모니터는 최근 분석 구간과 이전 구간을 비교해 품질 하락, 비용 급등, provider 차단율을 함께 봅니다.
- 각 분석의 LangGraph 단계는 별도 trace span으로 저장해 운영 콘솔에서 품질 점수와 함께 추적합니다.
- Observability export outbox는 trace span, 품질 점수, 공개 차단 사유, 최종 추천 요약을 payload로 보존하고 dispatch/retry 상태를 남겨 외부 APM 연결 전에도 회귀 원인을 재현할 수 있게 합니다.
- 공개 공유 리포트는 토큰 기반으로 열고, 워크스페이스 소유자만 공유를 생성하거나 해제합니다.
- 구매 판정은 점수만으로 결정하지 않고 가격 목표가, 호환성 차단, 출처 검수 필요 여부를 함께 봅니다.
- 최종 1순위만 강요하지 않고 예산, 성능, 안전 우선 대안을 함께 보여줍니다.
- 사용자가 입력한 필수 조건과 제외 조건은 후보별 충족 매트릭스로 다시 검증합니다.
- 구매 타이밍 윈도우는 현재가, 목표가, 적정가 밴드, 쿠폰/재고 변동 리스크를 묶어 지금 결제할지 기다릴지 판단하게 합니다.
- 구매 실행 패키지는 결제 전 확인, 판매자 문의, 주변 검토 공유까지 한 흐름으로 제공합니다.
- 구매 결과는 주문번호 원문을 저장하지 않고 마스킹하며, 실제 구매/이탈/지연/반품 신호와 최종가 차이를 모델 개선과 운영 판단에 사용합니다.
- 학습 인사이트는 구매 결과, 결제 전 검수 차단, 피드백 만족도를 합쳐 제품별 전환율, 반품률, 가격 신선도, 다음 개선 액션으로 운영 콘솔에 노출합니다.
- 완료 리포트 배치는 저장된 구매 리포트를 운영 채널 outbox로 묶어 전달하고, 템플릿, 수신자 그룹, unsubscribe 제외, 발송 전 렌더링 미리보기, provider 삽입용 공개 추적 픽셀/클릭 리다이렉트, provider webhook 기반 반송/신고/수신 제외, batch별 성공/실패/재시도/열람/클릭 상태를 남깁니다.
- 목표가 도달 알림은 발송 큐와 채널별 dispatch 시도를 남기고 실패 시 재시도 기준을 함께 저장합니다.
- 연락처와 이메일 원문은 응답/운영 콘솔에 노출하지 않고 마스킹된 값만 표시합니다. `/ops/data-governance`는 원문 연락처 컬럼이 남은 저장 표면을 blocker로 표시해 저장 구조 보강 대상을 드러냅니다.
- 추천 만족도와 구매 의향은 모델 개선 신호로 쓰되 추천 순위에는 즉시 반영하지 않습니다.
- 베타 출시 준비도는 분석 실행, 공유 리포트 조회, 알림 연결, 피드백, 리드, 품질 차단 사유를 함께 보며 단일 지표만으로 공개 확대를 결정하지 않습니다.
- 베타 cohort는 시나리오와 persona 기준으로 리드와 피드백을 묶고, 자동 개선 백로그는 readiness/피드백/품질 차단/학습 인사이트 신호에서 생성합니다.
- cohort 리포트는 JSON/Markdown으로 export하고, 개선 백로그의 운영 상태, SLA, 담당자 메모, 완료 요약은 워크스페이스별로 격리합니다.

## 다음 제품화 과제

- `/ops/integration-readiness`에 등록한 가격 비교/오픈마켓/공식 스토어 provider 계약을 실제 credential vault와 연결
- 외부 cron/Cloud Scheduler 배포 후 scheduler 연동을 `verified` 상태로 승격
- 실제 이메일/SMS/웹훅 provider credential 연결, 운영 rate limit smoke test, bounce/suppression 동기화
- 실제 LangSmith/OpenTelemetry credential을 사용하는 managed exporter 배치 작업을 `verified` 상태로 승격
- provider별 webhook 서명 검증 어댑터와 suppression list 양방향 동기화
