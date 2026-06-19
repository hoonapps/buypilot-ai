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
        <div class="actions">
          <button class="primary" id="collect">소스 수집</button>
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
    <section class="panel" style="margin-top:14px">
      <h2>품질/비용 감사</h2>
      <p>분석별 품질 점수, 예상 비용, 공개 전 차단 사유를 확인합니다.</p>
      <div class="quality-list" id="quality"></div>
    </section>
  </main>
  <script>
    async function loadDashboard() {
      const [response, qualityResponse] = await Promise.all([
        fetch('/admin/dashboard'),
        fetch('/ops/quality')
      ]);
      const data = await response.json();
      const quality = await qualityResponse.json();
      renderMetrics(data.metrics);
      renderSources(data.adapter_statuses);
      renderReviews(data.pending_reviews);
      renderQuality(quality);
    }

    function renderMetrics(metrics) {
      document.querySelector('#metrics').innerHTML = [
        ['분석', metrics.analysis_runs],
        ['저장', metrics.saved_reports],
        ['알림', metrics.alert_subscriptions],
        ['발송 큐', metrics.alert_events],
        ['트리거', metrics.triggered_alerts],
        ['품질', metrics.average_quality_score],
        ['예상비용', Math.round(metrics.estimated_cost_krw) + '원'],
        ['전환 준비율', Math.round(metrics.conversion_ready_rate * 100) + '%']
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
    document.querySelector('#refresh').addEventListener('click', loadDashboard);
    loadDashboard();
  </script>
</body>
</html>
"""
