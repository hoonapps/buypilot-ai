# ruff: noqa: E501

from html import escape

from specpilot_ai.core.models import PublicReport


def public_report_html(report: PublicReport) -> str:
    purchase = report.response.report
    top_cards = "\n".join(
        f"""
        <article class="card">
          <span class="rank">TOP {rec.rank}</span>
          <h3>{escape(rec.product.model_name)}</h3>
          <p>{escape(rec.fit_summary)}</p>
          <strong>{_won(rec.price.effective_price_krw)}</strong>
          <small>총점 {rec.score.total_score} · 호환성 {rec.score.compatibility}</small>
        </article>
        """
        for rec in purchase.top_recommendations
    )
    rows = "\n".join(
        f"""
        <tr>
          <td>{'TOP ' + str(row.rank) if row.rank else '제외'}</td>
          <td>{escape(row.model_name)}</td>
          <td>{_won(row.effective_price_krw)}</td>
          <td>{row.purpose_fit}점</td>
          <td>{row.compatibility}점</td>
          <td>{escape(row.main_risk)}</td>
        </tr>
        """
        for row in purchase.comparison_table
    )
    flags = "\n".join(f"<li>{escape(flag)}</li>" for flag in purchase.verification_flags)
    trust = "\n".join(
        f"<li>{escape(source.source_name)} · {escape(source.trust_grade)} · 신뢰도 {round(source.confidence * 100)}%</li>"
        for source in purchase.source_trust
    )
    return f"""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(report.title)} · SpecPilot AI</title>
  <style>
    :root {{
      --bg: #f6f7f2;
      --ink: #18201d;
      --muted: #66736d;
      --line: #d9dfd8;
      --panel: #fff;
      --teal: #0d756d;
      --gold: #b97922;
      --shadow: 0 22px 60px rgba(24, 32, 29, 0.1);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: linear-gradient(180deg, #fbfcf8 0%, var(--bg) 100%);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      min-height: 68px;
      padding: 0 4vw;
      border-bottom: 1px solid var(--line);
      background: rgba(255,255,255,0.86);
      backdrop-filter: blur(16px);
    }}
    a {{ color: inherit; text-decoration: none; font-weight: 900; }}
    main {{ width: min(1180px, calc(100% - 28px)); margin: 0 auto; padding: 30px 0 56px; }}
    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(280px, 0.45fr);
      gap: 18px;
      align-items: stretch;
    }}
    .panel, .card {{
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
    }}
    .panel {{ padding: clamp(20px, 3vw, 34px); }}
    .kicker {{ color: var(--teal); font-size: 12px; font-weight: 950; text-transform: uppercase; }}
    h1, h2, h3, p {{ margin-top: 0; }}
    h1 {{ max-width: 820px; margin: 10px 0 14px; font-size: clamp(32px, 5vw, 56px); line-height: 1.04; letter-spacing: 0; }}
    h2 {{ font-size: clamp(22px, 3vw, 34px); letter-spacing: 0; }}
    p {{ color: var(--muted); line-height: 1.65; }}
    .metric {{ display: grid; gap: 6px; }}
    .metric strong {{ font-size: 30px; }}
    .grid {{ display: grid; gap: 14px; margin-top: 16px; }}
    .cards {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .card {{ padding: 16px; box-shadow: none; }}
    .rank {{ color: var(--teal); font-size: 12px; font-weight: 950; }}
    .card strong {{ display: block; margin: 10px 0 5px; font-size: 24px; }}
    .card small {{ color: var(--muted); font-weight: 800; }}
    .section {{ margin-top: 18px; }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; min-width: 820px; border-collapse: collapse; font-size: 14px; }}
    th, td {{ padding: 11px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: 12px; }}
    ul {{ margin: 0; padding-left: 18px; color: var(--muted); line-height: 1.7; }}
    .two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .cta {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      margin-top: 18px;
      padding: 0 15px;
      border-radius: 8px;
      background: var(--teal);
      color: white;
    }}
    @media (max-width: 900px) {{
      header {{ align-items: flex-start; flex-direction: column; gap: 8px; padding: 14px 16px; }}
      .hero, .cards, .two {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <strong>SpecPilot AI</strong>
    <a href="/">새 구매 분석하기</a>
  </header>
  <main>
    <section class="hero">
      <div class="panel">
        <span class="kicker">Public purchase report</span>
        <h1>{escape(report.title)}</h1>
        <p>{escape(purchase.summary)}</p>
        <p>{escape(purchase.purchase_timing)}</p>
        <a class="cta" href="/">내 조건으로 다시 분석하기</a>
      </div>
      <aside class="panel metric">
        <span class="kicker">최종 후보</span>
        <strong>{escape(report.top_model_name or purchase.final_pick_id or "추천 후보")}</strong>
        <p>공유 조회 {report.share_views}회 · 공개 시각 {escape(report.shared_at[:10])}</p>
      </aside>
    </section>
    <section class="grid cards">{top_cards}</section>
    <section class="panel section">
      <h2>후보 비교표</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>순위</th><th>모델</th><th>실구매가</th><th>목적</th><th>호환</th><th>주요 리스크</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </section>
    <section class="two section">
      <div class="panel">
        <h2>검증 플래그</h2>
        <ul>{flags}</ul>
      </div>
      <div class="panel">
        <h2>출처 신뢰도</h2>
        <ul>{trust}</ul>
      </div>
    </section>
  </main>
</body>
</html>
"""


def _won(value: int) -> str:
    return f"{value:,}원"
