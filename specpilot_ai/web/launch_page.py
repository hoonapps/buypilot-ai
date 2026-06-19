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
      const report = data.report;
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
      const alerts = report.price_alerts.map((alert) => `
        <li>${alert.product_id}: 목표가 ${won(alert.target_price_krw)} / ${alert.recheck_interval_days}일마다 재확인</li>
      `).join('');
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
        </div>
        <div class="grid cards">${topCards}</div>
        <section class="sections">
          <div class="card comparison-card">
            <h3>비교표</h3>
            <table>
              <thead><tr><th>순위</th><th>모델</th><th>실구매가</th><th>목적</th><th>호환</th><th>주요 리스크</th></tr></thead>
              <tbody>${rows}</tbody>
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
          <div class="card">
            <h3>Agent Trace</h3>
            <div class="trace">${traces}</div>
          </div>
        </section>
      `;
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
