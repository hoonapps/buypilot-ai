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
        <div class="actions">
          <button class="primary" id="collect">소스 수집</button>
          <button class="secondary" id="ingest-url">URL 인입</button>
          <button class="secondary" id="save-monitor">모니터 등록</button>
          <button class="secondary" id="refresh-monitors">모니터 refresh</button>
          <button class="secondary" id="refresh">새로고침</button>
        </div>
      </div>
      <div class="panel">
        <h2>운영 지표</h2>
        <div class="grid cards" id="metrics"></div>
      </div>
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
        <div class="review-list" id="source-monitors"></div>
      </div>
      <div class="panel">
        <h2>수집 refresh 이력</h2>
        <p>성공, 실패, live fetch 여부와 검수 큐 연결 상태를 확인합니다.</p>
        <div class="review-list" id="source-refresh-runs"></div>
      </div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>품질/비용 감사</h2>
      <p>분석별 품질 점수, 예상 비용, 공개 전 차단 사유를 확인합니다.</p>
      <div class="quality-list" id="quality"></div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>Trace 저장소</h2>
      <p>분석별 LangGraph 단계 span, 품질 점수, 경고/차단 수를 확인합니다.</p>
      <div class="quality-list" id="traces"></div>
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
        refreshRunResponse
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
        fetch('/sources/refresh-runs')
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
      renderMetrics(data.metrics);
      renderSources(data.adapter_statuses);
      renderReviews(data.pending_reviews);
      renderSourceMonitors(monitors);
      renderSourceRefreshRuns(refreshRuns);
      renderQuality(quality);
      renderFeedback(feedback);
      renderBetaLeads(betaLeads);
      renderChannels(channels, events);
      renderDeliveries(deliveries);
      renderTraces(traces);
    }

    function renderMetrics(metrics) {
      document.querySelector('#metrics').innerHTML = [
        ['분석', metrics.analysis_runs],
        ['저장', metrics.saved_reports],
        ['알림', metrics.alert_subscriptions],
        ['발송 큐', metrics.alert_events],
        ['채널', metrics.alert_channels],
        ['발송 시도', metrics.alert_delivery_attempts],
        ['발송 성공', metrics.sent_alert_deliveries],
        ['발송 실패', metrics.failed_alert_deliveries],
        ['URL 모니터', metrics.source_monitors],
        ['소스 refresh', metrics.source_refresh_runs],
        ['refresh 실패', metrics.source_refresh_failures],
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

    function renderSources(sources) {
      document.querySelector('#sources').innerHTML = sources.map((source) => `
        <div class="card source ${source.confidence < 0.8 ? 'warn' : ''}">
          <strong>${source.name}</strong>
          <span>${source.kind} / 신뢰도 ${Math.round(source.confidence * 100)}% / ${source.freshness_minutes}분</span>
          <p>${source.message}</p>
        </div>
      `).join('');
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
    document.querySelector('#refresh').addEventListener('click', loadDashboard);
    loadDashboard();
  </script>
</body>
</html>
"""
