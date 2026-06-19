# ruff: noqa: E501

def launch_page_html() -> str:
    return """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SpecPilot AI</title>
  <style>
    :root {
      --bg: #f5f6f1;
      --ink: #18201d;
      --muted: #66736d;
      --panel: #ffffff;
      --line: #d9dfd8;
      --teal: #0d756d;
      --teal-dark: #084f49;
      --gold: #b97922;
      --red: #a9473e;
      --blue: #2e5d8f;
      --shadow: 0 24px 70px rgba(24, 32, 29, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: linear-gradient(180deg, #fbfcf8 0%, var(--bg) 100%);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      align-items: center;
      justify-content: space-between;
      min-height: 72px;
      padding: 0 4vw;
      border-bottom: 1px solid rgba(217, 223, 216, 0.85);
      background: rgba(245, 246, 241, 0.88);
      backdrop-filter: blur(18px);
    }
    .brand { display: flex; align-items: center; gap: 12px; font-weight: 900; }
    .mark {
      display: grid;
      place-items: center;
      width: 38px;
      height: 38px;
      border-radius: 8px;
      background: var(--ink);
      color: white;
    }
    nav { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
    nav a {
      color: var(--muted);
      text-decoration: none;
      padding: 8px 10px;
      border-radius: 8px;
      font-weight: 700;
      font-size: 14px;
    }
    nav a:hover { background: rgba(13, 117, 109, 0.08); color: var(--teal-dark); }
    main { width: min(1220px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0 56px; }
    .workspace {
      display: grid;
      grid-template-columns: minmax(320px, 0.82fr) minmax(0, 1.18fr);
      gap: 18px;
      align-items: start;
    }
    .panel {
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255,255,255,0.92);
      box-shadow: var(--shadow);
    }
    .input-panel { padding: clamp(20px, 3vw, 32px); position: sticky; top: 96px; }
    .kicker {
      display: inline-flex;
      color: var(--teal-dark);
      font-size: 12px;
      font-weight: 900;
      text-transform: uppercase;
    }
    h1, h2, h3, p { margin-top: 0; }
    h1 { font-size: clamp(34px, 5vw, 56px); line-height: 1.02; margin: 10px 0 14px; letter-spacing: 0; }
    h2 { font-size: clamp(24px, 3vw, 36px); margin-bottom: 10px; letter-spacing: 0; }
    h3 { font-size: 17px; margin-bottom: 8px; letter-spacing: 0; }
    p { color: var(--muted); line-height: 1.65; }
    label { display: grid; gap: 7px; margin: 14px 0; font-weight: 800; color: #26312d; }
    input, textarea, select {
      width: 100%;
      min-height: 42px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      padding: 10px 12px;
    }
    textarea { min-height: 104px; resize: vertical; }
    .two { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
    button {
      border: 0;
      border-radius: 8px;
      min-height: 44px;
      padding: 0 15px;
      font: inherit;
      font-weight: 900;
      cursor: pointer;
    }
    .primary { background: var(--teal); color: white; }
    .secondary { border: 1px solid var(--line); background: white; color: var(--ink); }
    .mini-action { min-height: 36px; padding: 0 11px; font-size: 13px; }
    .result-panel { padding: clamp(18px, 3vw, 28px); }
    .status {
      display: grid;
      gap: 8px;
      margin-bottom: 18px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f8faf5;
    }
    .grid { display: grid; gap: 12px; }
    .cards { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .card {
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: white;
      padding: 16px;
    }
    .rank { color: var(--teal-dark); font-size: 12px; font-weight: 900; }
    .price { font-size: 24px; font-weight: 950; margin: 8px 0; }
    .score {
      display: inline-flex;
      padding: 5px 8px;
      border-radius: 999px;
      background: rgba(13, 117, 109, 0.09);
      color: var(--teal-dark);
      font-size: 12px;
      font-weight: 900;
    }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }
    th, td { padding: 11px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
    th { color: var(--muted); font-size: 12px; }
    .sections { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }
    .comparison-card { grid-column: 1 / -1; overflow-x: auto; }
    .comparison-card table { min-width: 860px; }
    .list { display: grid; gap: 8px; padding-left: 0; list-style: none; margin: 0; }
    .list li { padding: 10px; border: 1px solid var(--line); border-radius: 8px; background: #fff; color: var(--muted); line-height: 1.55; }
    .trace { display: grid; gap: 8px; margin-top: 12px; }
    .trace div { border-left: 4px solid var(--teal); padding: 8px 10px; background: #fff; border-radius: 8px; }
    .warn { border-left-color: var(--gold) !important; }
    .hidden { display: none; }
    @media (max-width: 960px) {
      header { position: static; align-items: flex-start; flex-direction: column; padding: 16px; }
      main { width: min(100% - 24px, 1220px); }
      .workspace, .sections, .cards, .two { grid-template-columns: 1fr; }
      .input-panel { position: static; }
    }
  </style>
</head>
<body>
  <header>
    <div class="brand"><div class="mark">S</div><div>SpecPilot AI</div></div>
    <nav>
      <a href="/docs">API Docs</a>
      <a href="/product/brief">Product Brief</a>
      <a href="/graph/schema">Graph Schema</a>
    </nav>
  </header>
  <main>
    <div class="workspace">
      <section class="panel input-panel">
        <span class="kicker">Computer purchase agent</span>
        <h1>컴퓨터와 노트북 구매 판단을 끝까지 대신합니다</h1>
        <p>예산, 목적, 해상도, 필수 조건을 넣으면 후보 5개를 비교하고 TOP 3, 제외 후보, 호환성, 가격 알림, 구매 전 체크리스트를 생성합니다.</p>
        <form id="analysis-form">
          <label>구매 요청
            <textarea id="query">영상 편집과 게임용 데스크톱 200만원 안에서 맞춰줘. QHD 144Hz 모니터를 쓰고 업그레이드 여지도 있었으면 좋겠어.</textarea>
          </label>
          <div class="two">
            <label>카테고리
              <select id="category">
                <option value="desktop_pc">데스크톱 PC</option>
                <option value="laptop">노트북</option>
              </select>
            </label>
            <label>예산
              <input id="budget" type="number" value="2000000" />
            </label>
          </div>
          <label>사용 목적
            <input id="purpose" value="Premiere Pro, DaVinci Resolve, QHD gaming" />
          </label>
          <label>필수 조건
            <input id="mustHaves" value="QHD 144Hz, 32GB RAM, 업그레이드 여지" />
          </label>
          <label>제외 조건
            <input id="exclusions" value="중고, 리퍼, 출처 없는 가격" />
          </label>
          <div class="actions">
            <button class="primary" type="submit">분석 실행</button>
            <button class="secondary" type="button" id="laptop-demo">노트북 데모</button>
          </div>
        </form>
      </section>
      <section class="panel result-panel" id="results">
        <div class="status">
          <span class="kicker">Ready</span>
          <h2>분석을 실행하면 결과가 여기에 표시됩니다</h2>
          <p>현재 데모 모드는 외부 가격 사이트를 실시간 크롤링하지 않고, 검증용 카탈로그와 규칙 기반 분석 엔진으로 동작합니다.</p>
        </div>
      </section>
    </div>
  </main>
  <script>
    const form = document.querySelector('#analysis-form');
    const results = document.querySelector('#results');
    const laptopDemo = document.querySelector('#laptop-demo');
    let latestAnalysis = null;
    let latestSavedReport = null;

    function splitInput(value) {
      return value.split(',').map((item) => item.trim()).filter(Boolean);
    }

    function won(value) {
      return new Intl.NumberFormat('ko-KR').format(value) + '원';
    }

    function payload() {
      return {
        query: document.querySelector('#query').value,
        category: document.querySelector('#category').value,
        budget_krw: Number(document.querySelector('#budget').value),
        purpose: document.querySelector('#purpose').value,
        must_haves: splitInput(document.querySelector('#mustHaves').value),
        exclusions: splitInput(document.querySelector('#exclusions').value),
        channels: ['price_compare', 'open_market', 'official_store']
      };
    }

    function render(data) {
      latestAnalysis = data;
      latestSavedReport = null;
      const report = data.report;
      const decision = report.purchase_decision || {};
      const decisionSteps = (decision.next_steps || []).map((item) => `<li>${item}</li>`).join('');
      const decisionRisks = (decision.risk_flags || []).map((item) => `<li>${item}</li>`).join('');
      const firstChecklist = (report.top_recommendations[0]?.before_buy_checklist || []).map((item) => `<li>${item}</li>`).join('');
      const scenarioCards = (report.scenario_options || []).map((item) => `
        <article class="card">
          <span class="rank">${item.label}</span>
          <h3>${item.model_name}</h3>
          <div class="price">${won(item.effective_price_krw)}</div>
          <span class="score">총점 ${item.total_score}</span>
          <p>${item.why}</p>
          <p>${item.tradeoff}</p>
        </article>
      `).join('');
      const topCards = report.top_recommendations.map((rec) => `
        <article class="card">
          <div class="rank">TOP ${rec.rank}</div>
          <h3>${rec.product.model_name}</h3>
          <p>${rec.product.option_summary}</p>
          <div class="price">${won(rec.price.effective_price_krw)}</div>
          <span class="score">총점 ${rec.score.total_score}</span>
          <p>${rec.fit_summary}</p>
        </article>
      `).join('');
      const rows = report.comparison_table.map((row) => `
        <tr>
          <td>${row.rank ? 'TOP ' + row.rank : '제외'}</td>
          <td>${row.model_name}</td>
          <td>${won(row.effective_price_krw)}</td>
          <td>${row.purpose_fit}</td>
          <td>${row.compatibility}</td>
          <td>${row.main_risk}</td>
        </tr>
      `).join('');
      const criteriaRows = (report.criteria_matches || []).map((item) => `
        <tr>
          <td>${item.model_name}</td>
          <td>${item.coverage_score}</td>
          <td>${item.matched_count}</td>
          <td>${item.warning_count}</td>
          <td>${item.blocker_count}</td>
          <td>${item.summary}</td>
        </tr>
      `).join('');
      const stressCards = (report.stress_tests || []).map((item) => `
        <article class="card">
          <div class="rank">${item.label}</div>
          <h3>${item.selected_model_name || item.status}</h3>
          <p>${item.assumption}</p>
          <p><strong>${item.status}</strong> · ${item.impact}</p>
          <p>${item.recommendation}</p>
        </article>
      `).join('');
      const evidenceCards = (report.evidence_packs || []).map((item) => {
        const benchmarks = (item.benchmark_evidence || []).map((line) => `<li>${line}</li>`).join('');
        const compatibility = (item.compatibility_evidence || []).map((line) => `<li>${line}</li>`).join('');
        return `
          <article class="card">
            <div class="rank">${item.review_required ? '검수 필요' : '근거 충분'}</div>
            <h3>${item.model_name}</h3>
            <p>${item.price_evidence}</p>
            <p>${item.review_evidence}</p>
            <p><strong>${item.trust_summary}</strong></p>
            <ul class="list">${benchmarks || '<li>벤치마크 근거 추가 확인 필요</li>'}</ul>
            <ul class="list">${compatibility || '<li>호환성 세부 체크 추가 확인 필요</li>'}</ul>
          </article>
        `;
      }).join('');
      const optionAuditCards = (report.option_audits || []).map((audit) => {
        const items = (audit.critical_items || []).map((item) => `
          <tr><td>${item.field}</td><td>${item.expected_value}</td><td>${item.verification_hint}</td></tr>
        `).join('');
        const risks = (audit.mismatch_risks || []).map((risk) => `<li>${risk}</li>`).join('');
        const blockers = (audit.purchase_blockers || []).map((risk) => `<li>${risk}</li>`).join('');
        return `
          <article class="card comparison-card">
            <div class="rank">옵션 검수</div>
            <h3>${audit.model_name}</h3>
            <p>${audit.summary}</p>
            <table>
              <thead><tr><th>항목</th><th>기대값</th><th>확인 방법</th></tr></thead>
              <tbody>${items}</tbody>
            </table>
            <ul class="list">${blockers || risks}</ul>
          </article>
        `;
      }).join('');
      const alerts = report.price_alerts.map((alert) => `
        <li>${alert.product_id}: 목표가 ${won(alert.target_price_krw)} / ${alert.recheck_interval_days}일마다 재확인</li>
      `).join('');
      const trustRows = (report.source_trust || []).map((source) => `
        <tr>
          <td>${source.source_name}</td>
          <td>${source.trust_grade}</td>
          <td>${Math.round(source.confidence * 100)}%</td>
          <td>${source.cache_ttl_minutes}분</td>
          <td>${source.requires_human_review ? '검수 필요' : '자동 사용'}</td>
        </tr>
      `).join('');
      const policy = report.trust_policy || {};
      const policyRules = [
        policy.cache_policy,
        policy.stale_price_action,
        policy.affiliate_disclosure
      ].filter(Boolean).map((item) => `<li>${item}</li>`).join('');
      const execution = report.execution_plan || {};
      const checkoutSteps = (execution.checkout_steps || []).map((item) => `<li>${item}</li>`).join('');
      const sellerQuestions = (execution.seller_questions || []).map((item) => `<li>${item}</li>`).join('');
      const traces = data.trace_events.map((event) => `
        <div class="${event.status === 'warning' ? 'warn' : ''}">
          <strong>${event.title}</strong><br />
          <span>${event.detail}</span>
        </div>
      `).join('');
      results.innerHTML = `
        <div class="status">
          <span class="kicker">Trace ${data.graph_trace_id}</span>
          <h2>${report.summary}</h2>
          <p>${report.purchase_timing}</p>
          <div class="actions">
            <button class="primary mini-action" type="button" id="save-report">리포트 저장</button>
            <button class="secondary mini-action" type="button" id="share-report">공유 링크 생성</button>
            <button class="secondary mini-action" type="button" id="subscribe-alert">1순위 가격 알림</button>
            <button class="secondary mini-action" type="button" id="test-alert">목표가 도달 테스트</button>
            <button class="secondary mini-action" type="button" id="submit-feedback">피드백 보내기</button>
            <button class="secondary mini-action" type="button" id="join-beta">베타 신청</button>
            <button class="secondary mini-action" type="button" id="view-metrics">운영 지표</button>
          </div>
        </div>
        <div class="grid cards">${topCards}</div>
        <section class="section">
          <h3>대안 시나리오</h3>
          <div class="grid cards">${scenarioCards}</div>
        </section>
        <section class="section">
          <h3>예산/조건 스트레스 테스트</h3>
          <div class="grid cards">${stressCards}</div>
        </section>
        <section class="section">
          <h3>후보별 근거 팩</h3>
          <div class="grid cards">${evidenceCards}</div>
        </section>
        <section class="section">
          <h3>옵션/사양 검수표</h3>
          <div class="grid cards">${optionAuditCards}</div>
        </section>
        <section class="sections">
          <div class="card">
            <h3>구매 판정</h3>
            <p><strong>${decision.label || '판정 대기'}</strong> · 확신도 ${decision.confidence || 0}점</p>
            <p>${decision.reason || '분석 결과를 기반으로 구매 가능성을 계산합니다.'}</p>
            <ul class="list">${decisionSteps}</ul>
          </div>
          <div class="card">
            <h3>구매 실행 패키지</h3>
            <p><strong>${execution.urgency || '확인 필요'}</strong> · ${execution.primary_action || '결제 전 조건과 출처를 확인하세요.'}</p>
            <ul class="list">${checkoutSteps || '<li>최종 판매 페이지의 가격과 옵션명을 다시 확인하세요.</li>'}</ul>
          </div>
          <div class="card">
            <h3>판매자 확인 질문</h3>
            <ul class="list">${sellerQuestions || '<li>최종 결제 금액과 옵션명이 리포트와 같은지 확인해 주세요.</li>'}</ul>
          </div>
          <div class="card">
            <h3>공유 검토 문구</h3>
            <p>${execution.share_message || '추천 리포트를 공유해 결제 전 한 번 더 검토받으세요.'}</p>
          </div>
          <div class="card">
            <h3>결제 전 체크리스트</h3>
            <ul class="list">${firstChecklist || decisionRisks || '<li>최종 판매 페이지의 가격과 옵션명을 다시 확인하세요.</li>'}</ul>
          </div>
          <div class="card comparison-card">
            <h3>비교표</h3>
            <table>
              <thead><tr><th>순위</th><th>모델</th><th>실구매가</th><th>목적</th><th>호환</th><th>주요 리스크</th></tr></thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
          <div class="card comparison-card">
            <h3>조건 충족 매트릭스</h3>
            <table>
              <thead><tr><th>모델</th><th>충족률</th><th>충족</th><th>확인</th><th>차단</th><th>요약</th></tr></thead>
              <tbody>${criteriaRows}</tbody>
            </table>
          </div>
          <div class="card">
            <h3>가격 알림</h3>
            <ul class="list">${alerts}</ul>
          </div>
          <div class="card">
            <h3>검증 플래그</h3>
            <ul class="list">${report.verification_flags.map((item) => `<li>${item}</li>`).join('')}</ul>
          </div>
          <div class="card comparison-card">
            <h3>출처 신뢰도</h3>
            <table>
              <thead><tr><th>출처</th><th>등급</th><th>신뢰도</th><th>캐시</th><th>처리</th></tr></thead>
              <tbody>${trustRows}</tbody>
            </table>
          </div>
          <div class="card">
            <h3>캐시/제휴 정책</h3>
            <ul class="list">${policyRules}</ul>
          </div>
          <div class="card">
            <h3>Agent Trace</h3>
            <div class="trace">${traces}</div>
          </div>
        </section>
      `;
      bindResultActions();
    }

    function selectedProductId() {
      const top = latestAnalysis?.report?.top_recommendations?.[0]?.product?.product_id;
      const alertProduct = latestAnalysis?.report?.price_alerts?.[0]?.product_id;
      return top || alertProduct || null;
    }

    async function saveCurrentReport() {
      if (latestSavedReport?.trace_id === latestAnalysis.graph_trace_id) {
        return latestSavedReport;
      }
      const response = await fetch('/reports/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trace_id: latestAnalysis.graph_trace_id,
          owner_label: 'demo-user',
          notes: '웹 UI에서 저장한 구매 리포트'
        })
      });
      latestSavedReport = await response.json();
      return latestSavedReport;
    }

    function bindResultActions() {
      document.querySelector('#save-report')?.addEventListener('click', async () => {
        const saved = await saveCurrentReport();
        alert(`저장 완료: ${saved.report_id}`);
      });

      document.querySelector('#share-report')?.addEventListener('click', async () => {
        const saved = await saveCurrentReport();
        const response = await fetch(`/reports/${saved.report_id}/share`, {
          method: 'POST'
        });
        const share = await response.json();
        const url = `${window.location.origin}${share.public_path}`;
        if (navigator.clipboard) {
          await navigator.clipboard.writeText(url);
        }
        alert(`공유 링크 생성 완료: ${url}`);
      });

      document.querySelector('#subscribe-alert')?.addEventListener('click', async () => {
        const first = latestAnalysis.report.price_alerts[0];
        const response = await fetch('/alerts/subscribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            trace_id: latestAnalysis.graph_trace_id,
            product_id: first.product_id,
            target_price_krw: first.target_price_krw,
            channels: ['email'],
            contact: 'demo@example.com',
            owner_label: 'demo-user'
          })
        });
        const subscribed = await response.json();
        alert(`알림 구독 완료: ${subscribed.subscription_id}`);
      });

      document.querySelector('#test-alert')?.addEventListener('click', async () => {
        const first = latestAnalysis.report.price_alerts[0];
        const response = await fetch('/alerts/evaluate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            price_overrides_krw: {
              [first.product_id]: first.target_price_krw - 1
            },
            dry_run: false
          })
        });
        const evaluated = await response.json();
        const events = await fetch('/alerts/events').then((item) => item.json());
        const latest = events[0];
        alert(`평가 ${evaluated.evaluated_count}건 / 발송 큐 ${evaluated.triggered_count}건${latest ? ' / 최근 이벤트 ' + latest.event_id : ''}`);
      });

      document.querySelector('#submit-feedback')?.addEventListener('click', async () => {
        const response = await fetch('/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            trace_id: latestAnalysis.graph_trace_id,
            rating: 5,
            purchase_intent: true,
            selected_product_id: selectedProductId(),
            reason: '웹 UI 추천 결과와 가격 알림 조건이 구매 판단에 충분합니다.',
            improvement_requests: ['실제 판매 링크 연동', '재고 변동 알림'],
            contact: 'buyer@example.com'
          })
        });
        const feedback = await response.json();
        alert(`피드백 저장 완료: ${feedback.feedback_id}`);
      });

      document.querySelector('#join-beta')?.addEventListener('click', async () => {
        const response = await fetch('/beta/leads', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: 'beta@example.com',
            persona: document.querySelector('#category').value === 'laptop' ? 'mobile_creator' : 'pc_buyer',
            use_case: document.querySelector('#query').value,
            company_size: 'personal',
            contact_consent: true,
            source: 'launch_page'
          })
        });
        const lead = await response.json();
        alert(`베타 신청 완료: ${lead.lead_id}`);
      });

      document.querySelector('#view-metrics')?.addEventListener('click', async () => {
        const response = await fetch('/ops/metrics');
        const metrics = await response.json();
        alert(`분석 ${metrics.analysis_runs}건 / 저장 ${metrics.saved_reports}건 / 알림 ${metrics.alert_subscriptions}건 / 발송 이벤트 ${metrics.alert_events}건 / 피드백 ${metrics.feedback_count}건 / 베타 ${metrics.beta_leads}건`);
      });
    }

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      results.innerHTML = '<div class="status"><span class="kicker">Running</span><h2>분석 중입니다</h2><p>후보 수집, 호환성, 가격, 리뷰, 벤치마크 근거를 순서대로 계산합니다.</p></div>';
      const response = await fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload())
      });
      render(await response.json());
    });

    laptopDemo.addEventListener('click', () => {
      document.querySelector('#category').value = 'laptop';
      document.querySelector('#query').value = '영상 편집용 노트북 200만원 이하로 비교해줘. 휴대성도 중요하고 외장 GPU가 있으면 좋겠어.';
      document.querySelector('#purpose').value = 'Premiere Pro and DaVinci Resolve video editing';
      document.querySelector('#mustHaves').value = '32GB RAM 선호, 외장 GPU, 휴대성';
      document.querySelector('#exclusions').value = '리퍼, RAM 8GB, 출처 없는 가격';
    });
  </script>
</body>
</html>
"""
