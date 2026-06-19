# ruff: noqa: E501

from html import escape

from specpilot_ai.core.models import PublicReport


def public_report_html(report: PublicReport) -> str:
    purchase = report.response.report
    decision = purchase.purchase_decision
    share_brief = purchase.share_brief
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
    scenario_cards = "\n".join(
        f"""
        <article class="card">
          <span class="rank">{escape(item.label)}</span>
          <h3>{escape(item.model_name)}</h3>
          <strong>{_won(item.effective_price_krw)}</strong>
          <small>총점 {item.total_score}</small>
          <p>{escape(item.why)}</p>
          <p>{escape(item.tradeoff)}</p>
        </article>
        """
        for item in purchase.scenario_options
    )
    stress_cards = "\n".join(
        f"""
        <article class="card">
          <span class="rank">{escape(item.label)}</span>
          <h3>{escape(item.selected_model_name or item.status)}</h3>
          <p>{escape(item.assumption)}</p>
          <p><strong>{escape(item.status)}</strong> · {escape(item.impact)}</p>
          <p>{escape(item.recommendation)}</p>
        </article>
        """
        for item in purchase.stress_tests
    )
    deal_window_cards = "\n".join(
        f"""
        <article class="card">
          <span class="rank">{escape(item.label)}</span>
          <h3>{escape(item.model_name)}</h3>
          <strong>{_won(item.current_price_krw)}</strong>
          <small>목표가 {_won(item.target_price_krw)} · {escape(item.status)}</small>
          <p><strong>{escape(item.urgency)}</strong> · {escape(item.wait_reason)}</p>
          <p>{escape(item.volatility_risk)}</p>
          <p>{escape(item.buy_trigger)}</p>
          <ul>{_list_items(item.monitoring_plan)}</ul>
        </article>
        """
        for item in purchase.deal_windows
    )
    evidence_cards = "\n".join(
        f"""
        <article class="card">
          <span class="rank">{"검수 필요" if item.review_required else "근거 충분"}</span>
          <h3>{escape(item.model_name)}</h3>
          <p>{escape(item.price_evidence)}</p>
          <p>{escape(item.review_evidence)}</p>
          <p><strong>{escape(item.trust_summary)}</strong></p>
          <ul>{_list_items(item.benchmark_evidence) or "<li>벤치마크 근거 추가 확인 필요</li>"}</ul>
          <ul>{_list_items(item.compatibility_evidence) or "<li>호환성 세부 체크 추가 확인 필요</li>"}</ul>
        </article>
        """
        for item in purchase.evidence_packs
    )
    option_audit_cards = "\n".join(
        f"""
        <article class="card">
          <span class="rank">옵션 검수</span>
          <h3>{escape(audit.model_name)}</h3>
          <p>{escape(audit.summary)}</p>
          <div class="table-wrap">
            <table>
              <thead><tr><th>항목</th><th>기대값</th><th>확인 방법</th></tr></thead>
              <tbody>{_option_audit_rows(audit.critical_items)}</tbody>
            </table>
          </div>
          <ul>{_list_items(audit.purchase_blockers or audit.mismatch_risks)}</ul>
        </article>
        """
        for audit in purchase.option_audits
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
    criteria_rows = "\n".join(
        f"""
        <tr>
          <td>{escape(item.model_name)}</td>
          <td>{item.coverage_score}점</td>
          <td>{item.matched_count}</td>
          <td>{item.warning_count}</td>
          <td>{item.blocker_count}</td>
          <td>{escape(item.summary)}</td>
        </tr>
        """
        for item in purchase.criteria_matches
    )
    execution = purchase.execution_plan
    checkout_steps = "\n".join(
        f"<li>{escape(item)}</li>"
        for item in (execution.checkout_steps if execution else [])
    )
    seller_questions = "\n".join(
        f"<li>{escape(item)}</li>"
        for item in (execution.seller_questions if execution else [])
    )
    flags = "\n".join(f"<li>{escape(flag)}</li>" for flag in purchase.verification_flags)
    trust = "\n".join(
        f"<li>{escape(source.source_name)} · {escape(source.trust_grade)} · 신뢰도 {round(source.confidence * 100)}%</li>"
        for source in purchase.source_trust
    )
    decision_steps = "\n".join(
        f"<li>{escape(item)}</li>" for item in (decision.next_steps if decision else [])
    )
    decision_risks = "\n".join(
        f"<li>{escape(item)}</li>" for item in (decision.risk_flags if decision else [])
    )
    checklist = "\n".join(
        f"<li>{escape(item)}</li>"
        for item in (
            purchase.top_recommendations[0].before_buy_checklist
            if purchase.top_recommendations
            else []
        )
    )
    brief_reasons = _list_items(share_brief.key_reasons if share_brief else [])
    brief_watchouts = _list_items(share_brief.watchouts if share_brief else [])
    brief_questions = _list_items(share_brief.reviewer_questions if share_brief else [])
    purchase_link_cards = _purchase_link_cards(report)
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
    <section class="section panel">
      <span class="kicker">Share brief</span>
      <h2>공유용 검토 브리프</h2>
      <p><strong>{escape(share_brief.verdict_label if share_brief else "판정 대기")}</strong> · 확신도 {share_brief.confidence if share_brief else 0}점</p>
      <p>{escape(share_brief.copy_text if share_brief else "공개 리포트를 공유해 결제 전 한 번 더 검토받으세요.")}</p>
      <div class="two">
        <div><h3>핵심 근거</h3><ul>{brief_reasons}</ul></div>
        <div><h3>확인할 점</h3><ul>{brief_watchouts}</ul></div>
      </div>
      <h3>검토 질문</h3>
      <ul>{brief_questions}</ul>
    </section>
    <section class="section">
      <h2>대안 시나리오</h2>
      <div class="grid cards">{scenario_cards}</div>
    </section>
    <section class="section">
      <h2>구매 타이밍 윈도우</h2>
      <div class="grid cards">{deal_window_cards}</div>
    </section>
    <section class="section">
      <h2>구매 링크</h2>
      <div class="grid cards">{purchase_link_cards}</div>
    </section>
    <section class="section">
      <h2>예산/조건 스트레스 테스트</h2>
      <div class="grid cards">{stress_cards}</div>
    </section>
    <section class="section">
      <h2>후보별 근거 팩</h2>
      <div class="grid cards">{evidence_cards}</div>
    </section>
    <section class="section">
      <h2>옵션/사양 검수표</h2>
      <div class="grid cards">{option_audit_cards}</div>
    </section>
    <section class="two section">
      <div class="panel">
        <span class="kicker">Purchase decision</span>
        <h2>{escape(decision.label if decision else "구매 판정")}</h2>
        <p>확신도 {decision.confidence if decision else 0}점 · {escape(decision.reason if decision else "분석 결과 기반 구매 가능성을 계산합니다.")}</p>
        <ul>{decision_steps or "<li>최종 판매 페이지의 가격과 옵션명을 다시 확인하세요.</li>"}</ul>
      </div>
      <div class="panel">
        <span class="kicker">Execution package</span>
        <h2>구매 실행 패키지</h2>
        <p>{escape(execution.urgency if execution else "확인 필요")} · {escape(execution.primary_action if execution else "결제 전 조건과 출처를 확인하세요.")}</p>
        <ul>{checkout_steps or "<li>최종 판매 페이지의 가격과 옵션명을 다시 확인하세요.</li>"}</ul>
      </div>
    </section>
    <section class="two section">
      <div class="panel">
        <h2>판매자 확인 질문</h2>
        <ul>{seller_questions or "<li>최종 결제 금액과 옵션명이 리포트와 같은지 확인해 주세요.</li>"}</ul>
      </div>
      <div class="panel">
        <h2>공유 검토 문구</h2>
        <p>{escape(execution.share_message if execution else "추천 리포트를 공유해 결제 전 한 번 더 검토받으세요.")}</p>
      </div>
    </section>
    <section class="two section">
      <div class="panel">
        <h2>결제 전 체크리스트</h2>
        <ul>{checklist or decision_risks or "<li>출처, 가격, 재고, 옵션명을 다시 확인하세요.</li>"}</ul>
      </div>
    </section>
    <section class="panel section">
      <h2>후보 비교표</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>순위</th><th>모델</th><th>실구매가</th><th>목적</th><th>호환</th><th>주요 리스크</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </section>
    <section class="panel section">
      <h2>조건 충족 매트릭스</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>모델</th><th>충족률</th><th>충족</th><th>확인</th><th>차단</th><th>요약</th></tr></thead>
          <tbody>{criteria_rows}</tbody>
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


def _list_items(items: list[str]) -> str:
    return "\n".join(f"<li>{escape(item)}</li>" for item in items)


def _purchase_link_cards(report: PublicReport) -> str:
    if not report.purchase_links:
        return """
        <article class="card">
          <span class="rank">링크 준비 중</span>
          <h3>구매 링크 검수 전</h3>
          <p>공개 전 운영자가 제휴 여부와 비제휴 대안을 검수한 링크만 노출합니다.</p>
        </article>
        """
    return "\n".join(
        f"""
        <article class="card">
          <span class="rank">{'제휴' if link.is_affiliate else '비제휴'} · {escape(link.status.value)}</span>
          <h3>{escape(link.seller_name)}</h3>
          <p>{escape(link.model_name)}</p>
          <strong>{_won(link.effective_price_krw) if link.effective_price_krw is not None else '가격 확인 필요'}</strong>
          <p>{escape(link.disclosure)}</p>
          <ul>{_list_items(link.policy_warnings) or '<li>추천 순위와 링크 수익은 분리해 운영합니다.</li>'}</ul>
          <a class="cta" href="{escape(link.click_path)}?source=public_report">판매처 확인</a>
        </article>
        """
        for link in report.purchase_links
    )


def _option_audit_rows(items) -> str:
    return "\n".join(
        f"""
        <tr>
          <td>{escape(item.field)}</td>
          <td>{escape(item.expected_value)}</td>
          <td>{escape(item.verification_hint)}</td>
        </tr>
        """
        for item in items
    )
