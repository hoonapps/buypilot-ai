# ruff: noqa: E501

def admin_page_html() -> str:
    return """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SpecPilot AI Admin</title>
  <style>
    :root {
      --bg: #f6f7f2;
      --ink: #18201d;
      --muted: #66736d;
      --line: #d9dfd8;
      --panel: #fff;
      --teal: #0d756d;
      --gold: #b97922;
      --red: #a9473e;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      min-height: 68px;
      padding: 0 4vw;
      border-bottom: 1px solid var(--line);
      background: rgba(255,255,255,0.82);
      backdrop-filter: blur(16px);
    }
    a { color: inherit; text-decoration: none; font-weight: 800; }
    main { width: min(1240px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0 48px; }
    .kicker { color: var(--teal); font-size: 12px; font-weight: 900; text-transform: uppercase; }
    h1, h2, h3, p { margin-top: 0; }
    h1 { font-size: clamp(30px, 4vw, 48px); line-height: 1.05; margin: 8px 0 12px; }
    p { color: var(--muted); line-height: 1.6; }
    .grid { display: grid; gap: 14px; }
    .top-grid { grid-template-columns: 1.1fr 0.9fr; align-items: start; }
    .cards { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .panel, .card {
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 18px;
    }
    .metric { font-size: 30px; font-weight: 950; margin: 6px 0; }
    .source { display: grid; gap: 6px; border-left: 4px solid var(--teal); }
    .warn { border-left-color: var(--gold); }
    .review-list { display: grid; gap: 12px; }
    .review-item { border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: #fff; }
    .quality-list { display: grid; gap: 10px; }
    .quality-item { border-left: 4px solid var(--teal); }
    .quality-item.warn { border-left-color: var(--gold); }
    .quality-item.danger { border-left-color: var(--red); }
    .actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
    button {
      min-height: 36px;
      border: 0;
      border-radius: 8px;
      padding: 0 12px;
      font: inherit;
      font-weight: 900;
      cursor: pointer;
    }
    .primary { background: var(--teal); color: white; }
    .secondary { border: 1px solid var(--line); background: #fff; }
    .danger { background: var(--red); color: #fff; }
    input {
      width: 100%;
      min-height: 40px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 9px 10px;
      font: inherit;
      margin: 6px 0;
    }
    @media (max-width: 920px) {
      header { align-items: flex-start; flex-direction: column; padding: 14px 16px; gap: 8px; }
      main { width: min(100% - 24px, 1240px); }
      .top-grid, .cards { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <strong>SpecPilot AI Admin</strong>
    <nav><a href="/">제품 화면</a></nav>
  </header>
  <main>
    <section class="grid top-grid">
      <div class="panel">
        <span class="kicker">Operations Console</span>
        <h1>추천 근거를 공개 전에 검수합니다</h1>
        <p>가격, 리뷰, 벤치마크 어댑터 상태와 검수 대기 근거를 확인하고 승인/반려할 수 있습니다.</p>
        <input id="source-query" value="영상 편집과 게임용 데스크톱 200만원 QHD 144Hz" />
        <input id="source-url" value="https://example.com/product/specpilot" />
        <input id="source-model" value="RTX 4070 영상 편집 PC" />
        <input id="source-provider-host" value="example.com" />
        <div class="actions">
          <button class="primary" id="collect">소스 수집</button>
          <button class="secondary" id="ingest-url">URL 인입</button>
          <button class="secondary" id="save-provider">provider 정책 저장</button>
          <button class="secondary" id="save-monitor">모니터 등록</button>
          <button class="secondary" id="refresh-monitors">모니터 refresh</button>
          <button class="secondary" id="refresh-due-monitors">due refresh</button>
          <button class="secondary" id="refresh">새로고침</button>
        </div>
      </div>
      <div class="panel">
        <h2>운영 지표</h2>
        <div class="grid cards" id="metrics"></div>
      </div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>베타 출시 준비도</h2>
      <p>분석, 공유, 알림, 피드백, 리드, 품질 차단 사유를 묶어 공개 확대 가능성을 판단합니다.</p>
      <div class="grid cards" id="beta-readiness-summary"></div>
      <div class="quality-list" id="beta-readiness-checks" style="margin-top:12px"></div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>출시 게이트</h2>
      <p>준비도, 품질 회귀, 학습 인사이트, 백로그 SLA, 전환/발송 상태를 묶어 공개 go/no-go를 판단합니다.</p>
      <div class="grid cards" id="launch-gate-summary"></div>
      <div class="quality-list" id="launch-gate-checks" style="margin-top:12px"></div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>외부 연동 준비도</h2>
      <p>가격 API, 오픈마켓, 공식 스토어, 이메일, 관측성, 스케줄러 등 공개 전 필수 연동의 credential/rate limit/검증 상태를 확인합니다.</p>
      <div class="actions">
        <button class="secondary" id="seed-integrations">핵심 연동 등록</button>
      </div>
      <div class="grid cards" id="integration-readiness-summary" style="margin-top:12px"></div>
      <div class="quality-list" id="integration-readiness-checks" style="margin-top:12px"></div>
      <div class="review-list" id="integration-providers" style="margin-top:12px"></div>
    </section>
    <section class="grid top-grid" style="margin-top:14px">
      <div class="panel">
        <h2>소스 어댑터</h2>
        <div class="grid" id="sources"></div>
      </div>
      <div class="panel">
        <h2>검수 대기</h2>
        <div class="review-list" id="reviews"></div>
      </div>
    </section>
    <section class="grid top-grid" style="margin-top:14px">
      <div class="panel">
        <h2>URL 모니터</h2>
        <p>실제 상품 URL을 반복 수집 대상으로 등록하고 refresh 상태를 추적합니다.</p>
        <div class="grid cards" id="source-schedule"></div>
        <div class="review-list" id="source-monitors"></div>
      </div>
      <div class="panel">
        <h2>수집 refresh 이력</h2>
        <p>성공, 실패, live fetch 여부와 검수 큐 연결 상태를 확인합니다.</p>
        <div class="review-list" id="source-refresh-runs"></div>
      </div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>Source Provider 정책</h2>
      <p>live fetch 허용 host, robots/약관 검토, 시간당 rate limit 상태를 확인합니다.</p>
      <div class="review-list" id="source-providers"></div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>품질/비용 감사</h2>
      <p>분석별 품질 점수, 예상 비용, 공개 전 차단 사유를 확인합니다.</p>
      <div class="quality-list" id="quality"></div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>품질 회귀 모니터</h2>
      <p>최근 분석 품질, 비용 변화, provider 차단율을 비교해 출시 안정성을 확인합니다.</p>
      <div class="quality-list" id="ops-regression"></div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>Trace 저장소</h2>
      <p>분석별 LangGraph 단계 span, 품질 점수, 경고/차단 수를 확인합니다.</p>
      <div class="quality-list" id="traces"></div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>Observability export outbox</h2>
      <p>trace span과 품질 감사 payload를 LangSmith/OpenTelemetry 연동 전 큐 형태로 보존합니다.</p>
      <div class="actions">
        <button class="secondary" id="dispatch-observability">observability dispatch</button>
      </div>
      <div class="quality-list" id="observability-exports"></div>
    </section>
    <section class="grid top-grid" style="margin-top:14px">
      <div class="panel">
        <h2>사용자 피드백</h2>
        <p>추천 만족도, 구매 의향, 선택 후보와 개선 요청을 확인합니다.</p>
        <div class="review-list" id="feedback"></div>
      </div>
      <div class="panel">
        <h2>베타 리드</h2>
        <p>공개 전 베타 신청자와 사용 맥락을 추적합니다.</p>
        <div class="review-list" id="beta-leads"></div>
      </div>
    </section>
    <section class="grid top-grid" style="margin-top:14px">
      <div class="panel">
        <h2>베타 cohort</h2>
        <p>구매 시나리오별 리드, 피드백, 구매 의향을 묶고 cohort 리포트 export를 운영합니다.</p>
        <div class="actions">
          <button class="secondary" id="save-beta-cohort">기본 cohort 생성</button>
        </div>
        <div class="review-list" id="beta-cohorts"></div>
      </div>
      <div class="panel">
        <h2>개선 백로그</h2>
        <p>출시 준비도, 낮은 만족도, 품질 차단 사유에서 자동 생성된 개선 항목의 운영 상태와 SLA 상태입니다.</p>
        <div class="quality-list" id="beta-backlog-summary"></div>
        <div class="review-list" id="beta-backlog"></div>
      </div>
    </section>
    <section class="grid top-grid" style="margin-top:14px">
      <div class="panel">
        <h2>결제 전 검수</h2>
        <p>저장 리포트에서 실제 결제 직전 가격, 옵션, 판매자 답변, 리스크 승인 상태를 검수합니다.</p>
        <div class="review-list" id="checkout-reviews"></div>
      </div>
      <div class="panel">
        <h2>구매 결과</h2>
        <p>저장 리포트가 실제 구매, 이탈, 지연, 반품으로 이어졌는지 추적합니다.</p>
        <div class="review-list" id="purchase-outcomes"></div>
      </div>
      <div class="panel">
        <h2>학습 인사이트</h2>
        <p>구매 결과, 피드백, 결제 검수 신호를 제품별 개선 액션으로 묶습니다.</p>
        <div class="quality-list" id="learning-insight-summary"></div>
        <div class="review-list" id="learning-insights"></div>
      </div>
      <div class="panel">
        <h2>완료 리포트 배치</h2>
        <p>저장된 구매 리포트를 템플릿과 수신자 그룹 기준으로 운영 outbox에 발송합니다.</p>
        <input id="completion-target" value="ops@example.com" />
        <input id="completion-group" value="ops@example.com, buyer@example.com" />
        <div class="actions">
          <button class="secondary" id="save-completion-template">템플릿 저장</button>
          <button class="secondary" id="save-completion-group">수신자 그룹 저장</button>
          <button class="primary" id="dispatch-completion-reports">완료 리포트 발송</button>
        </div>
        <div class="review-list" id="completion-templates"></div>
        <div class="review-list" id="completion-groups"></div>
        <div class="review-list" id="completion-batches"></div>
        <div class="review-list" id="completion-engagement"></div>
        <div class="review-list" id="completion-provider-events"></div>
      </div>
      <div class="panel">
        <h2>알림 발송 채널</h2>
        <p>목표가 도달 큐를 이메일, 웹훅, 문자 outbox로 발송 처리합니다.</p>
        <input id="channel-target" value="ops@example.com" />
        <div class="actions">
          <button class="primary" id="save-email-channel">이메일 채널 저장</button>
          <button class="secondary" id="dispatch-alerts">큐 발송</button>
        </div>
        <div class="review-list" id="channels"></div>
      </div>
      <div class="panel">
        <h2>발송 시도</h2>
        <p>발송 성공, 실패, 재시도 예정 상태를 확인합니다.</p>
        <div class="review-list" id="deliveries"></div>
      </div>
    </section>
  </main>
  <script>
    let latestCompletionTemplates = [];
    let latestCompletionGroups = [];

    async function loadDashboard() {
      const [
        response,
        qualityResponse,
        feedbackResponse,
        betaLeadResponse,
        channelResponse,
        deliveryResponse,
        eventResponse,
        traceResponse,
        monitorResponse,
        refreshRunResponse,
        providerResponse,
        scheduleResponse,
        readinessResponse,
        launchGateResponse,
        integrationReadinessResponse,
        integrationProviderResponse,
        betaCohortResponse,
        betaBacklogResponse,
        betaBacklogSummaryResponse,
        regressionResponse,
        learningInsightResponse,
        observabilityResponse,
        completionBatchResponse,
        completionTemplateResponse,
        completionGroupResponse,
        completionEngagementResponse,
        completionProviderEventResponse,
        checkoutReviewResponse,
        purchaseOutcomeResponse
      ] = await Promise.all([
        fetch('/admin/dashboard'),
        fetch('/ops/quality'),
        fetch('/feedback'),
        fetch('/beta/leads'),
        fetch('/alerts/channels'),
        fetch('/alerts/deliveries'),
        fetch('/alerts/events'),
        fetch('/ops/traces'),
        fetch('/sources/monitors'),
        fetch('/sources/refresh-runs'),
        fetch('/sources/providers'),
        fetch('/sources/schedule'),
        fetch('/beta/readiness'),
        fetch('/beta/launch-gate'),
        fetch('/ops/integration-readiness'),
        fetch('/ops/integrations'),
        fetch('/beta/cohorts'),
        fetch('/beta/backlog'),
        fetch('/beta/backlog/summary'),
        fetch('/ops/regression'),
        fetch('/ops/learning-insights'),
        fetch('/ops/observability/exports'),
        fetch('/reports/completion-batches'),
        fetch('/reports/completion-templates'),
        fetch('/reports/completion-recipient-groups'),
        fetch('/reports/completion-engagement'),
        fetch('/reports/completion-provider-events'),
        fetch('/checkout-reviews'),
        fetch('/purchase-outcomes')
      ]);
      const data = await response.json();
      const quality = await qualityResponse.json();
      const feedback = await feedbackResponse.json();
      const betaLeads = await betaLeadResponse.json();
      const channels = await channelResponse.json();
      const deliveries = await deliveryResponse.json();
      const events = await eventResponse.json();
      const traces = await traceResponse.json();
      const monitors = await monitorResponse.json();
      const refreshRuns = await refreshRunResponse.json();
      const providers = await providerResponse.json();
      const schedule = await scheduleResponse.json();
      const readiness = await readinessResponse.json();
      const launchGate = await launchGateResponse.json();
      const integrationReadiness = await integrationReadinessResponse.json();
      const integrationProviders = await integrationProviderResponse.json();
      const betaCohorts = await betaCohortResponse.json();
      const betaBacklog = await betaBacklogResponse.json();
      const betaBacklogSummary = await betaBacklogSummaryResponse.json();
      const regression = await regressionResponse.json();
      const learningInsights = await learningInsightResponse.json();
      const observabilityExports = await observabilityResponse.json();
      const completionBatches = await completionBatchResponse.json();
      const completionTemplates = await completionTemplateResponse.json();
      const completionGroups = await completionGroupResponse.json();
      const completionEngagement = await completionEngagementResponse.json();
      const completionProviderEvents = await completionProviderEventResponse.json();
      const checkoutReviews = await checkoutReviewResponse.json();
      const purchaseOutcomes = await purchaseOutcomeResponse.json();
      latestCompletionTemplates = completionTemplates;
      latestCompletionGroups = completionGroups;
      renderMetrics(data.metrics);
      renderBetaReadiness(readiness);
      renderLaunchGate(launchGate);
      renderIntegrationReadiness(integrationReadiness);
      renderIntegrationProviders(integrationProviders);
      renderSources(data.adapter_statuses);
      renderReviews(data.pending_reviews);
      renderSourceSchedule(schedule);
      renderSourceMonitors(monitors);
      renderSourceRefreshRuns(refreshRuns);
      renderSourceProviders(providers);
      renderQuality(quality);
      renderOpsRegression(regression);
      renderLearningInsights(learningInsights);
      renderFeedback(feedback);
      renderBetaLeads(betaLeads);
      renderBetaCohorts(betaCohorts);
      renderBetaBacklogSummary(betaBacklogSummary);
      renderBetaBacklog(betaBacklog);
      renderChannels(channels, events);
      renderDeliveries(deliveries);
      renderCompletionTemplates(completionTemplates);
      renderCompletionGroups(completionGroups);
      renderCompletionBatches(completionBatches);
      renderCompletionEngagement(completionEngagement);
      renderCompletionProviderEvents(completionProviderEvents);
      renderCheckoutReviews(checkoutReviews);
      renderPurchaseOutcomes(purchaseOutcomes);
      renderTraces(traces);
      renderObservabilityExports(observabilityExports);
    }

    function renderMetrics(metrics) {
      document.querySelector('#metrics').innerHTML = [
        ['분석', metrics.analysis_runs],
        ['저장', metrics.saved_reports],
        ['공유', metrics.shared_reports],
        ['공개 조회', metrics.public_share_views],
        ['알림', metrics.alert_subscriptions],
        ['발송 큐', metrics.alert_events],
        ['채널', metrics.alert_channels],
        ['발송 시도', metrics.alert_delivery_attempts],
        ['발송 성공', metrics.sent_alert_deliveries],
        ['발송 실패', metrics.failed_alert_deliveries],
        ['완료 batch', metrics.completion_report_batches],
        ['완료 발송', metrics.completion_report_deliveries],
        ['완료 열람', metrics.completion_delivery_opens],
        ['완료 클릭', metrics.completion_delivery_clicks],
        ['완료 반송', metrics.completion_delivery_bounces],
        ['완료 신고', metrics.completion_delivery_complaints],
        ['완료 제외', metrics.completion_delivery_suppressions],
        ['결제 검수', metrics.checkout_reviews],
        ['결제 보류', metrics.checkout_blocked_reviews],
        ['결제 가능', metrics.checkout_ready_reviews],
        ['구매 결과', metrics.purchase_outcomes],
        ['실구매', metrics.completed_purchase_outcomes],
        ['구매 이탈', metrics.abandoned_purchase_outcomes],
        ['구매 지연', metrics.delayed_purchase_outcomes],
        ['반품/취소', metrics.returned_purchase_outcomes],
        ['구매 링크', metrics.purchase_links],
        ['제휴 링크', metrics.affiliate_purchase_links],
        ['링크 클릭', metrics.purchase_link_clicks],
        ['실구매 전환', Math.round(metrics.purchase_conversion_rate * 100) + '%'],
        ['최종가 차이', Math.round(metrics.average_final_price_delta_krw) + '원'],
        ['전환 금액', Math.round(metrics.purchase_outcome_value_krw) + '원'],
        ['URL 모니터', metrics.source_monitors],
        ['소스 refresh', metrics.source_refresh_runs],
        ['refresh 실패', metrics.source_refresh_failures],
        ['provider 정책', metrics.source_provider_policies],
        ['provider fetch', metrics.source_provider_fetches],
        ['fetch 차단', metrics.source_provider_blocked_fetches],
        ['Trace span', metrics.trace_spans],
        ['트리거', metrics.triggered_alerts],
        ['품질', metrics.average_quality_score],
        ['예상비용', Math.round(metrics.estimated_cost_krw) + '원'],
        ['전환 준비율', Math.round(metrics.conversion_ready_rate * 100) + '%'],
        ['피드백', metrics.feedback_count],
        ['베타 리드', metrics.beta_leads],
        ['만족도', metrics.average_satisfaction],
        ['구매 의향', Math.round(metrics.purchase_intent_rate * 100) + '%']
      ].map(([label, value]) => `<div class="card"><span class="kicker">${label}</span><div class="metric">${value}</div></div>`).join('');
    }

    function renderBetaReadiness(readiness) {
      document.querySelector('#beta-readiness-summary').innerHTML = [
        ['준비도', Math.round(readiness.launch_readiness_score) + '점'],
        ['상태', readiness.readiness_label],
        ['공유 조회', readiness.public_share_views],
        ['구매 의향', Math.round(readiness.purchase_intent_rate * 100) + '%']
      ].map(([label, value]) => `<div class="card"><span class="kicker">${label}</span><div class="metric">${value}</div></div>`).join('');
      const actions = readiness.next_actions || [];
      document.querySelector('#beta-readiness-checks').innerHTML = `
        ${(readiness.checks || []).map((check) => {
          const tone = check.status === 'blocker' ? 'danger' : check.status === 'warning' ? 'warn' : '';
          return `
            <article class="review-item quality-item ${tone}">
              <span class="kicker">${check.area} · ${check.status}</span>
              <h3>${check.label} · ${check.metric}</h3>
              <p>${check.recommendation}</p>
            </article>
          `;
        }).join('')}
        <article class="review-item">
          <span class="kicker">Next actions</span>
          <h3>다음 실행 항목</h3>
          <ul>${actions.length ? actions.map((item) => `<li>${item}</li>`).join('') : '<li>현재 기준으로 추가 차단 항목이 없습니다.</li>'}</ul>
        </article>
      `;
    }

    function renderLaunchGate(gate) {
      document.querySelector('#launch-gate-summary').innerHTML = [
        ['판정', gate.decision],
        ['상태', gate.status],
        ['준비도', Math.round(gate.launch_readiness_score) + '점'],
        ['필수 액션', (gate.required_actions || []).length]
      ].map(([label, value]) => `<div class="card"><span class="kicker">${label}</span><div class="metric">${value}</div></div>`).join('');
      const requiredActions = gate.required_actions || [];
      document.querySelector('#launch-gate-checks').innerHTML = `
        <article class="review-item quality-item ${gate.status === 'blocker' ? 'danger' : gate.status === 'warning' ? 'warn' : ''}">
          <span class="kicker">launch-gate · ${gate.status}</span>
          <h3>${gate.readiness_label} · ${gate.decision}</h3>
          <p>${gate.summary}</p>
        </article>
        ${(gate.checks || []).map((check) => {
          const tone = check.status === 'blocker' ? 'danger' : check.status === 'warning' ? 'warn' : '';
          return `
            <article class="review-item quality-item ${tone}">
              <span class="kicker">${check.area} · ${check.status}</span>
              <h3>${check.label}</h3>
              <p>${check.metric}</p>
              <p>${check.recommendation}</p>
            </article>
          `;
        }).join('')}
        <article class="review-item">
          <span class="kicker">Required actions</span>
          <h3>공개 전 필수 액션</h3>
          <ul>${requiredActions.length ? requiredActions.map((item) => `<li>${item}</li>`).join('') : '<li>현재 기준으로 공개 전 필수 액션이 없습니다.</li>'}</ul>
        </article>
      `;
    }

    function renderIntegrationReadiness(readiness) {
      document.querySelector('#integration-readiness-summary').innerHTML = [
        ['준비도', Math.round(readiness.readiness_score) + '점'],
        ['상태', readiness.status],
        ['verified', readiness.verified_count],
        ['blocker', readiness.blocker_count]
      ].map(([label, value]) => `<div class="card"><span class="kicker">${label}</span><div class="metric">${value}</div></div>`).join('');
      const actions = readiness.required_actions || [];
      document.querySelector('#integration-readiness-checks').innerHTML = `
        <article class="review-item quality-item ${readiness.status === 'blocker' ? 'danger' : readiness.status === 'warning' ? 'warn' : ''}">
          <span class="kicker">integration-readiness · ${readiness.status}</span>
          <h3>${Math.round(readiness.readiness_score)}점</h3>
          <p>${readiness.summary}</p>
        </article>
        ${(readiness.checks || []).map((check) => {
          const tone = check.status === 'blocker' ? 'danger' : check.status === 'warning' ? 'warn' : '';
          return `
            <article class="review-item quality-item ${tone}">
              <span class="kicker">${check.category} · ${check.status}</span>
              <h3>${check.label}${check.provider_name ? ' · ' + check.provider_name : ''}</h3>
              <p>${check.metric}</p>
              <p>${check.recommendation}</p>
            </article>
          `;
        }).join('')}
        <article class="review-item">
          <span class="kicker">Required actions</span>
          <h3>외부 연동 필수 액션</h3>
          <ul>${actions.length ? actions.map((item) => `<li>${item}</li>`).join('') : '<li>현재 기준으로 추가 외부 연동 액션이 없습니다.</li>'}</ul>
        </article>
      `;
    }

    function renderIntegrationProviders(items) {
      const root = document.querySelector('#integration-providers');
      if (!items.length) {
        root.innerHTML = '<p>아직 등록된 외부 연동 provider가 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => {
        const tone = item.status === 'blocked' ? 'danger' : item.status === 'mock' || item.status === 'configured' ? 'warn' : '';
        return `
          <article class="review-item quality-item ${tone}">
            <span class="kicker">${item.category} · ${item.status}</span>
            <h3>${item.provider_name}</h3>
            <p>credential ${item.credential_status} / 시간당 ${item.rate_limit_per_hour}회 / 보존 ${item.retention_days}일</p>
            <p>${item.evidence || item.notes || item.endpoint || '운영 증거 없음'}</p>
          </article>
        `;
      }).join('');
    }

    function renderSources(sources) {
      document.querySelector('#sources').innerHTML = sources.map((source) => `
        <div class="card source ${source.confidence < 0.8 ? 'warn' : ''}">
          <strong>${source.name}</strong>
          <span>${source.kind} / 신뢰도 ${Math.round(source.confidence * 100)}% / ${source.freshness_minutes}분</span>
          <p>${source.message}</p>
        </div>
      `).join('');
    }

    function renderSourceSchedule(schedule) {
      document.querySelector('#source-schedule').innerHTML = [
        ['due', schedule.due_count],
        ['upcoming', schedule.upcoming_count],
        ['생성', new Date(schedule.generated_at).toLocaleString()]
      ].map(([label, value]) => `<div class="card"><span class="kicker">${label}</span><div class="metric">${value}</div></div>`).join('');
    }

    function renderSourceMonitors(monitors) {
      const root = document.querySelector('#source-monitors');
      if (!monitors.length) {
        root.innerHTML = '<p>아직 등록된 URL 모니터가 없습니다.</p>';
        return;
      }
      root.innerHTML = monitors.map((item) => `
        <article class="review-item ${item.last_status === 'failed' ? 'danger' : ''}">
          <span class="kicker">${item.kind} · ${item.active ? '활성' : '비활성'} · ${item.cadence_minutes}분</span>
          <h3>${item.expected_model || item.url}</h3>
          <p>${item.url}</p>
          <p>마지막 상태: ${item.last_status} / 실패 ${item.failure_count}회 / 마지막 소스: ${item.last_source_id || '없음'}</p>
        </article>
      `).join('');
    }

    function renderSourceRefreshRuns(items) {
      const root = document.querySelector('#source-refresh-runs');
      if (!items.length) {
        root.innerHTML = '<p>아직 refresh 이력이 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => `
        <article class="review-item ${item.status === 'failed' ? 'danger' : ''}">
          <span class="kicker">${item.status} · ${item.fetched_live ? 'live fetch' : 'snapshot'}</span>
          <h3>${item.monitor_id}</h3>
          <p>${item.message}</p>
          <p>source: ${item.source_id || '없음'} / review: ${item.review_id || '없음'}</p>
        </article>
      `).join('');
    }

    function renderSourceProviders(items) {
      const root = document.querySelector('#source-providers');
      if (!items.length) {
        root.innerHTML = '<p>아직 등록된 provider 정책이 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => {
        const blocked = !item.live_fetch_allowed || item.robots_status !== 'approved' || item.terms_status !== 'approved';
        return `
          <article class="review-item ${blocked ? 'warn' : ''}">
            <span class="kicker">${item.kind} · ${item.host_pattern} · ${item.live_fetch_allowed ? 'live 허용' : 'live 차단'}</span>
            <h3>${item.provider_name}</h3>
            <p>robots ${item.robots_status} / terms ${item.terms_status} / credential ${item.credential_status}</p>
            <p>시간당 ${item.rate_limit_per_hour}회 / ${item.notes || '운영 메모 없음'}</p>
          </article>
        `;
      }).join('');
    }

    function renderReviews(reviews) {
      const root = document.querySelector('#reviews');
      if (!reviews.length) {
        root.innerHTML = '<p>현재 검수 대기 항목이 없습니다.</p>';
        return;
      }
      root.innerHTML = reviews.map((item) => `
        <article class="review-item">
          <span class="kicker">${item.source.kind} · ${item.source.adapter_id}</span>
          <h3>${item.source.title}</h3>
          <p>${item.source.evidence_text}</p>
          <p>사유: ${item.reason}</p>
          <div class="actions">
            <button class="primary" onclick="decide('${item.review_id}', 'approved')">승인</button>
            <button class="danger" onclick="decide('${item.review_id}', 'rejected')">반려</button>
          </div>
        </article>
      `).join('');
    }

    function renderQuality(quality) {
      const root = document.querySelector('#quality');
      if (!quality.recent_audits.length) {
        root.innerHTML = '<p>아직 품질 감사 데이터가 없습니다.</p>';
        return;
      }
      root.innerHTML = quality.recent_audits.map((audit) => {
        const tone = audit.launch_blockers.length ? 'danger' : audit.warning_count ? 'warn' : '';
        const blockers = audit.launch_blockers.length
          ? audit.launch_blockers.map((item) => `<li>${item}</li>`).join('')
          : '<li>공개 차단 사유 없음</li>';
        return `
          <article class="review-item quality-item ${tone}">
            <span class="kicker">${audit.trace_id}</span>
            <h3>품질 ${audit.quality_score}점 · 예상 비용 ${Math.round(audit.estimated_cost_krw)}원</h3>
            <p>소스 호출 ${audit.estimated_source_calls}회 / 토큰 ${audit.estimated_llm_tokens} / 경고 ${audit.warning_count} / 검수 필요 출처 ${audit.review_required_sources}</p>
            <ul>${blockers}</ul>
          </article>
        `;
      }).join('');
    }

    function renderOpsRegression(regression) {
      const root = document.querySelector('#ops-regression');
      const tone = regression.status === 'blocker'
        ? 'danger'
        : regression.status === 'warning' ? 'warn' : '';
      const providerCards = regression.provider_reliability.length
        ? regression.provider_reliability.map((item) => `
          <li>${item.provider_name} · 차단 ${Math.round(item.blocked_rate * 100)}% · ${item.recommendation}</li>
        `).join('')
        : '<li>아직 provider fetch 이력이 없습니다.</li>';
      const risks = regression.risk_flags.length
        ? regression.risk_flags.map((item) => `<li>${item}</li>`).join('')
        : '<li>현재 회귀 신호 없음</li>';
      root.innerHTML = `
        <article class="review-item quality-item ${tone}">
          <span class="kicker">release health · ${regression.status}</span>
          <h3>최근 품질 ${regression.recent.average_quality_score}점 · 변화 ${regression.quality_delta}점</h3>
          <p>${regression.summary}</p>
          <p>최근 비용 ${Math.round(regression.recent.average_cost_krw)}원 / 이전 비용 ${Math.round(regression.previous.average_cost_krw)}원 / 비용 변화율 ${Math.round(regression.cost_delta_rate * 100)}%</p>
          <h4>리스크 플래그</h4>
          <ul>${risks}</ul>
          <h4>provider 차단율</h4>
          <ul>${providerCards}</ul>
        </article>
      `;
    }

    function renderLearningInsights(dashboard) {
      const summaryRoot = document.querySelector('#learning-insight-summary');
      const listRoot = document.querySelector('#learning-insights');
      const tone = dashboard.status === 'blocker'
        ? 'danger'
        : dashboard.status === 'warning' ? 'warn' : '';
      const actions = dashboard.top_actions && dashboard.top_actions.length
        ? dashboard.top_actions.map((item) => `<li>${item}</li>`).join('')
        : '<li>현재 즉시 실행할 학습 액션은 없습니다.</li>';
      summaryRoot.innerHTML = `
        <article class="review-item quality-item ${tone}">
          <span class="kicker">learning · ${dashboard.status}</span>
          <h3>제품 인사이트 ${dashboard.insight_count}개</h3>
          <p>${dashboard.summary}</p>
          <ul>${actions}</ul>
        </article>
      `;
      if (!dashboard.insights.length) {
        listRoot.innerHTML = '<p>아직 제품별 학습 인사이트가 없습니다.</p>';
        return;
      }
      listRoot.innerHTML = dashboard.insights.map((item) => {
        const itemTone = item.status === 'blocker'
          ? 'danger'
          : item.status === 'warning' ? 'warn' : '';
        const tags = item.learning_tags.length ? item.learning_tags.join(' / ') : '태그 없음';
        return `
          <article class="review-item quality-item ${itemTone}">
            <span class="kicker">${item.status} · ${tags}</span>
            <h3>${item.model_name || item.product_id} · 전환 ${Math.round(item.conversion_rate * 100)}%</h3>
            <p>${item.evidence}</p>
            <p>만족도 ${item.average_satisfaction} / 결제 보류 ${item.checkout_blocked_count}/${item.checkout_review_count} / 전환금액 ${Math.round(item.conversion_value_krw).toLocaleString()}원</p>
            <p>${item.recommended_action}</p>
          </article>
        `;
      }).join('');
    }

    function renderTraces(items) {
      const root = document.querySelector('#traces');
      if (!items.length) {
        root.innerHTML = '<p>아직 저장된 trace가 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => {
        const tone = item.blocker_count ? 'danger' : item.warning_count ? 'warn' : '';
        return `
          <article class="review-item quality-item ${tone}">
            <span class="kicker">${item.trace_id} · ${item.category}</span>
            <h3>${item.top_model_name || item.final_pick_id || '분석 결과'} · span ${item.span_count}개</h3>
            <p>${item.purpose}</p>
            <p>품질 ${item.quality_score}점 / 경고 ${item.warning_count} / 차단 ${item.blocker_count}</p>
            <div class="actions">
              <button class="secondary" data-observability-trace="${item.trace_id}">export 큐 적재</button>
            </div>
          </article>
        `;
      }).join('');
      root.querySelectorAll('[data-observability-trace]').forEach((button) => {
        button.addEventListener('click', async () => {
          await fetch('/ops/observability/exports', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              trace_id: button.dataset.observabilityTrace,
              destination: 'opentelemetry',
              include_payload: true
            })
          });
          await loadDashboard();
        });
      });
    }

    function renderObservabilityExports(items) {
      const root = document.querySelector('#observability-exports');
      if (!items.length) {
        root.innerHTML = '<p>아직 observability export outbox 항목이 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => {
        const tone = item.status === 'failed' ? 'danger' : item.status === 'queued' ? 'warn' : '';
        return `
        <article class="review-item quality-item ${tone}">
          <span class="kicker">${item.destination} · ${item.status}</span>
          <h3>${item.trace_id} · span ${item.span_count}개 · 품질 ${item.quality_score}점</h3>
          <p>export id: ${item.export_id} / 생성: ${new Date(item.created_at).toLocaleString()} / 시도 ${item.retry_count || 0}회</p>
          <p>${item.provider_message || 'provider 처리 전'}${item.next_retry_at ? ' / 재시도: ' + new Date(item.next_retry_at).toLocaleString() : ''}</p>
          <p>payload: ${item.payload?.schema_version || 'payload 제외'}</p>
        </article>
      `;
      }).join('');
    }

    function renderFeedback(items) {
      const root = document.querySelector('#feedback');
      if (!items.length) {
        root.innerHTML = '<p>아직 사용자 피드백이 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => `
        <article class="review-item">
          <span class="kicker">${item.trace_id}</span>
          <h3>만족도 ${item.rating}점 · 구매 의향 ${item.purchase_intent ? '있음' : '없음'}</h3>
          <p>${item.reason || '상세 사유 없음'}</p>
          <p>선택 후보: ${item.selected_product_id || '미선택'} / 연락처: ${item.contact_masked || '없음'}</p>
          <p>개선 요청: ${item.improvement_requests.length ? item.improvement_requests.join(', ') : '없음'}</p>
        </article>
      `).join('');
    }

    function renderBetaLeads(items) {
      const root = document.querySelector('#beta-leads');
      if (!items.length) {
        root.innerHTML = '<p>아직 베타 신청자가 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => `
        <article class="review-item">
          <span class="kicker">${item.persona} · ${item.company_size}</span>
          <h3>${item.email_masked}</h3>
          <p>${item.use_case}</p>
          <p>동의: ${item.contact_consent ? '예' : '아니오'} / 유입: ${item.source}</p>
        </article>
      `).join('');
    }

    function renderBetaCohorts(items) {
      const root = document.querySelector('#beta-cohorts');
      if (!items.length) {
        root.innerHTML = '<p>아직 베타 cohort가 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => `
        <article class="review-item">
          <span class="kicker">${item.category} · ${item.target_persona} · ${item.active ? '활성' : '비활성'}</span>
          <h3>${item.name} · 준비도 ${Math.round(item.readiness_score)}점</h3>
          <p>${item.scenario}</p>
          <p>리드 ${item.lead_count}/${item.target_size}명 / 피드백 ${item.feedback_count}건 / 만족도 ${item.average_satisfaction} / 구매 의향 ${Math.round(item.purchase_intent_rate * 100)}%</p>
          <p><a href="/beta/cohorts/${item.cohort_id}/report" target="_blank">JSON 리포트</a> · <a href="/beta/cohorts/${item.cohort_id}/report.md" target="_blank">Markdown export</a></p>
        </article>
      `).join('');
    }

    function renderBetaBacklog(items) {
      const root = document.querySelector('#beta-backlog');
      if (!items.length) {
        root.innerHTML = '<p>현재 자동 개선 백로그가 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => {
        const tone = item.severity === 'blocker' ? 'danger' : item.severity === 'warning' ? 'warn' : '';
        return `
          <article class="review-item quality-item ${tone}">
            <span class="kicker">${item.source_type} · ${item.severity} · ${item.status}</span>
            <h3>${item.title}</h3>
            <p>${item.evidence}</p>
            <p>${item.suggested_action}</p>
            <p>담당: ${item.assignee || '미지정'} / SLA: ${item.sla_due_at || '미정'} ${item.is_overdue ? '· 지연' : ''}</p>
            <p>메모: ${item.action_note || '없음'} / 완료 요약: ${item.completion_summary || '없음'}</p>
            <div class="actions">
              <button class="secondary" data-backlog-action="${item.backlog_id}" data-status="in_progress">진행 중</button>
              <button class="primary" data-backlog-action="${item.backlog_id}" data-status="done">완료</button>
            </div>
          </article>
        `;
      }).join('');
      root.querySelectorAll('[data-backlog-action]').forEach((button) => {
        button.addEventListener('click', async () => {
          await fetch(`/beta/backlog/${button.dataset.backlogAction}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              status: button.dataset.status,
              assignee: 'ops',
              note: button.dataset.status === 'done' ? '관리자 콘솔에서 완료 처리' : '관리자 콘솔에서 진행 시작',
              completion_summary: button.dataset.status === 'done' ? '관리자 콘솔에서 SLA 항목 완료' : ''
            })
          });
          await loadDashboard();
        });
      });
    }

    function renderBetaBacklogSummary(summary) {
      const root = document.querySelector('#beta-backlog-summary');
      root.innerHTML = `
        <article class="review-item quality-item ${summary.overdue_count ? 'danger' : summary.due_soon_count ? 'warn' : ''}">
          <span class="kicker">SLA summary</span>
          <h3>전체 ${summary.total_count}건 · 지연 ${summary.overdue_count}건 · 24시간 내 ${summary.due_soon_count}건</h3>
          <p>open ${summary.open_count} / 진행 ${summary.in_progress_count} / 완료 ${summary.done_count} / blocker ${summary.blocker_count}</p>
          <ul>${summary.next_actions.map((item) => `<li>${item}</li>`).join('')}</ul>
        </article>
      `;
    }

    function renderChannels(items, events) {
      const root = document.querySelector('#channels');
      const queuedCount = events.filter((item) => ['queued', 'failed'].includes(item.delivery_status)).length;
      const channelCards = items.length
        ? items.map((item) => `
          <article class="review-item">
            <span class="kicker">${item.channel} · ${item.enabled ? '활성' : '비활성'}</span>
            <h3>${item.display_name}</h3>
            <p>대상: ${item.target_masked} / 재시도 한도: ${item.retry_limit}</p>
          </article>
        `).join('')
        : '<p>아직 등록된 발송 채널이 없습니다.</p>';
      root.innerHTML = `
        <article class="review-item">
          <span class="kicker">Queue</span>
          <h3>발송 대기 ${queuedCount}건</h3>
          <p>목표가 도달 이벤트 중 queued/failed 상태만 발송 처리됩니다.</p>
        </article>
        ${channelCards}
      `;
    }

    function renderDeliveries(items) {
      const root = document.querySelector('#deliveries');
      if (!items.length) {
        root.innerHTML = '<p>아직 발송 시도 기록이 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => `
        <article class="review-item">
          <span class="kicker">${item.channel} · ${item.delivery_status}</span>
          <h3>${item.contact_masked}</h3>
          <p>${item.provider_message}</p>
          <p>이벤트: ${item.event_id} / 시도: ${item.retry_count}${item.next_retry_at ? ' / 재시도: ' + item.next_retry_at : ''}</p>
        </article>
      `).join('');
    }

    function renderCompletionBatches(items) {
      const root = document.querySelector('#completion-batches');
      if (!items.length) {
        root.innerHTML = '<p>아직 완료 리포트 batch가 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => {
        const tone = item.status === 'failed' ? 'danger' : item.status === 'partial' ? 'warn' : '';
        const deliveries = item.deliveries.length
          ? item.deliveries.map((delivery) => `
            <li>${delivery.report_id} · ${delivery.channel} · ${delivery.status} · ${delivery.target_masked} · 열람 ${delivery.open_count || 0} / 클릭 ${delivery.click_count || 0}<br />pixel ${delivery.tracking_pixel_path || '없음'} / click ${delivery.tracking_click_path || '없음'}</li>
          `).join('')
          : '<li>개별 발송 기록 없음</li>';
        return `
          <article class="review-item quality-item ${tone}">
            <span class="kicker">${item.status} · ${new Date(item.created_at).toLocaleString()}</span>
            <h3>선택 ${item.selected_count}건 · 성공 ${item.sent_count}건 · 실패 ${item.failed_count}건</h3>
            <p>${item.note || '메모 없음'}</p>
            <ul>${deliveries}</ul>
          </article>
        `;
      }).join('');
    }

    function renderCheckoutReviews(items) {
      const root = document.querySelector('#checkout-reviews');
      if (!items.length) {
        root.innerHTML = '<p>아직 결제 전 검수 기록이 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => {
        const tone = item.checkout_blocked ? 'danger' : item.readiness_status === 'warning' ? 'warn' : '';
        const checks = item.items.map((check) => `
          <li>${check.label} · ${check.status} · ${check.evidence}</li>
        `).join('');
        const missing = item.missing_acknowledgements.length
          ? `<p>미승인 리스크: ${item.missing_acknowledgements.join(' / ')}</p>`
          : '<p>미승인 리스크 없음</p>';
        return `
          <article class="review-item quality-item ${tone}">
            <span class="kicker">${item.readiness_status} · ${new Date(item.created_at).toLocaleString()}</span>
            <h3>${item.model_name || item.product_id || '선택 후보'} · ${Math.round(item.readiness_score)}점</h3>
            <p>${item.final_recommendation}</p>
            ${missing}
            <ul>${checks}</ul>
          </article>
        `;
      }).join('');
    }

    function renderPurchaseOutcomes(items) {
      const root = document.querySelector('#purchase-outcomes');
      if (!items.length) {
        root.innerHTML = '<p>아직 구매 결과 기록이 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => {
        const tone = ['abandoned', 'returned'].includes(item.status)
          ? 'danger'
          : item.status === 'delayed' ? 'warn' : '';
        const delta = item.price_delta_krw === null || item.price_delta_krw === undefined
          ? '최종가 미입력'
          : `${item.price_delta_krw > 0 ? '+' : ''}${item.price_delta_krw.toLocaleString()}원`;
        const paid = item.final_paid_price_krw
          ? `${item.final_paid_price_krw.toLocaleString()}원`
          : '금액 없음';
        return `
          <article class="review-item quality-item ${tone}">
            <span class="kicker">${item.status} · ${new Date(item.created_at).toLocaleString()}</span>
            <h3>${item.model_name || item.product_id || '선택 후보'} · ${paid}</h3>
            <p>예상가 대비 ${delta} / 만족도 ${item.satisfaction || '미입력'}</p>
            <p>${item.learning_signal}</p>
            <p>${item.reason || item.notes || '상세 메모 없음'}</p>
          </article>
        `;
      }).join('');
    }

    function renderCompletionTemplates(items) {
      const root = document.querySelector('#completion-templates');
      if (!items.length) {
        root.innerHTML = '<p>아직 완료 리포트 템플릿이 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => `
        <article class="review-item">
          <span class="kicker">${item.channel} · ${item.enabled ? '활성' : '비활성'}</span>
          <h3>${item.name}</h3>
          <p>${item.subject}</p>
        </article>
      `).join('');
    }

    function renderCompletionEngagement(items) {
      const root = document.querySelector('#completion-engagement');
      if (!items.length) {
        root.innerHTML = '<p>아직 완료 리포트 열람/클릭 이벤트가 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => `
        <article class="review-item">
          <span class="kicker">${item.event_type} · ${new Date(item.created_at).toLocaleString()}</span>
          <h3>${item.target_masked} · ${item.report_id}</h3>
          <p>delivery: ${item.delivery_id} / batch: ${item.batch_id}</p>
        </article>
      `).join('');
    }

    function renderCompletionProviderEvents(items) {
      const root = document.querySelector('#completion-provider-events');
      if (!items.length) {
        root.innerHTML = '<p>아직 완료 리포트 provider webhook 이벤트가 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => {
        const tone = item.delivery_status === 'failed' ? 'danger' : item.delivery_status === 'skipped' ? 'warn' : '';
        return `
          <article class="review-item quality-item ${tone}">
            <span class="kicker">${item.provider_name} · ${item.event_type} · ${new Date(item.created_at).toLocaleString()}</span>
            <h3>${item.delivery_status} · ${item.report_id}</h3>
            <p>${item.provider_message || 'provider 메시지 없음'}</p>
            <p>delivery: ${item.delivery_id} / batch: ${item.batch_id}</p>
          </article>
        `;
      }).join('');
    }

    function renderCompletionGroups(items) {
      const root = document.querySelector('#completion-groups');
      if (!items.length) {
        root.innerHTML = '<p>아직 완료 리포트 수신자 그룹이 없습니다.</p>';
        return;
      }
      root.innerHTML = items.map((item) => `
        <article class="review-item">
          <span class="kicker">${item.channel} · ${item.enabled ? '활성' : '비활성'} · ${item.unsubscribe_policy}</span>
          <h3>${item.name} · 수신 ${item.recipient_count}명 · 제외 ${item.unsubscribed_count}명</h3>
          <p>${item.recipients_masked.join(', ') || '수신자 없음'}</p>
        </article>
      `).join('');
    }

    async function decide(reviewId, status) {
      await fetch(`/admin/reviews/${reviewId}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, reviewer: 'admin', note: '관리자 콘솔 처리' })
      });
      await loadDashboard();
    }

    document.querySelector('#collect').addEventListener('click', async () => {
      await fetch('/sources/collect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: document.querySelector('#source-query').value,
          category: 'desktop_pc',
          limit: 16
        })
      });
      await loadDashboard();
    });
    document.querySelector('#ingest-url').addEventListener('click', async () => {
      await fetch('/sources/ingest-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: document.querySelector('#source-url').value,
          category: 'desktop_pc',
          kind: 'price',
          expected_model: document.querySelector('#source-model').value,
          source_name: 'admin_console'
        })
      });
      await loadDashboard();
    });
    document.querySelector('#save-provider').addEventListener('click', async () => {
      await fetch('/sources/providers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_name: '운영 승인 provider',
          host_pattern: document.querySelector('#source-provider-host').value,
          kind: 'price',
          live_fetch_allowed: true,
          robots_status: 'approved',
          terms_status: 'approved',
          credential_status: 'operator_reviewed',
          rate_limit_per_hour: 30,
          notes: '관리자 콘솔에서 등록한 live fetch 정책'
        })
      });
      await loadDashboard();
    });
    document.querySelector('#seed-integrations').addEventListener('click', async () => {
      const providers = [
        ['가격 비교 공식 API', 'price_api', 'configured', 120, 30],
        ['오픈마켓 provider', 'marketplace', 'configured', 80, 30],
        ['공식 스토어 provider', 'official_store', 'configured', 60, 30],
        ['이메일 발송 provider', 'email', 'configured', 500, 90],
        ['Observability exporter', 'observability', 'configured', 1000, 180],
        ['외부 scheduler', 'scheduler', 'configured', 24, 30]
      ];
      await Promise.all(providers.map(([provider_name, category, status, rate_limit_per_hour, retention_days]) => (
        fetch('/ops/integrations', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            provider_name,
            category,
            status,
            credential_status: 'operator_reviewed',
            rate_limit_per_hour,
            retention_days,
            endpoint: 'managed-by-ops',
            evidence: '관리자 콘솔에서 공개 전 smoke test 대상으로 등록',
            notes: '실제 credential 값은 저장하지 않음'
          })
        })
      )));
      await loadDashboard();
    });
    document.querySelector('#save-monitor').addEventListener('click', async () => {
      await fetch('/sources/monitors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: document.querySelector('#source-url').value,
          category: 'desktop_pc',
          kind: 'price',
          expected_model: document.querySelector('#source-model').value,
          source_name: 'admin_console_monitor',
          cadence_minutes: 180
        })
      });
      await loadDashboard();
    });
    document.querySelector('#refresh-monitors').addEventListener('click', async () => {
      await fetch('/sources/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit: 20 })
      });
      await loadDashboard();
    });
    document.querySelector('#refresh-due-monitors').addEventListener('click', async () => {
      await fetch('/sources/refresh-due', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit: 20 })
      });
      await loadDashboard();
    });
    document.querySelector('#save-beta-cohort').addEventListener('click', async () => {
      await fetch('/beta/cohorts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: '영상 편집 QHD 데스크톱 cohort',
          scenario: document.querySelector('#source-query').value,
          category: 'desktop_pc',
          target_persona: 'creator',
          target_size: 10,
          success_metric: 'purchase_intent_rate',
          keywords: ['영상 편집', 'QHD', '데스크톱'],
          notes: '관리자 콘솔에서 생성한 공개 베타 검증 cohort'
        })
      });
      await loadDashboard();
    });
    document.querySelector('#save-email-channel').addEventListener('click', async () => {
      await fetch('/alerts/channels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: 'email',
          display_name: '운영 이메일 outbox',
          target: document.querySelector('#channel-target').value,
          enabled: true,
          retry_limit: 3
        })
      });
      await loadDashboard();
    });
    document.querySelector('#dispatch-alerts').addEventListener('click', async () => {
      await fetch('/alerts/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dry_run: false, limit: 50 })
      });
      await loadDashboard();
    });
    document.querySelector('#save-completion-template').addEventListener('click', async () => {
      await fetch('/reports/completion-templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: '운영 완료 리포트',
          channel: 'email',
          subject: '[SpecPilot] {title}',
          body: '{title}\\n추천 1순위: {top_model_name}\\n공개 리포트: {public_path}\\n결제 전 옵션명과 최종 금액을 확인해 주세요.',
          enabled: true
        })
      });
      await loadDashboard();
    });
    document.querySelector('#save-completion-group').addEventListener('click', async () => {
      const recipients = document.querySelector('#completion-group').value
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);
      await fetch('/reports/completion-recipient-groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: '운영 완료 리포트 수신자',
          channel: 'email',
          recipients,
          unsubscribed_recipients: [],
          unsubscribe_policy: 'exclude_unsubscribed',
          enabled: true,
          description: '관리자 콘솔 기본 수신자 그룹'
        })
      });
      await loadDashboard();
    });
    document.querySelector('#dispatch-completion-reports').addEventListener('click', async () => {
      const template = latestCompletionTemplates[0];
      const group = latestCompletionGroups[0];
      await fetch('/reports/completion-batches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: 'email',
          target: document.querySelector('#completion-target').value,
          template_id: template ? template.template_id : null,
          recipient_group_id: group ? group.group_id : null,
          respect_unsubscribe: true,
          dry_run: false,
          limit: 20,
          note: '관리자 콘솔 완료 리포트 발송'
        })
      });
      await loadDashboard();
    });
    document.querySelector('#refresh').addEventListener('click', loadDashboard);
    document.querySelector('#dispatch-observability').addEventListener('click', async () => {
      await fetch('/ops/observability/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dry_run: false, limit: 50 })
      });
      await loadDashboard();
    });
    loadDashboard();
  </script>
</body>
</html>
"""
