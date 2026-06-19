# SpecPilot AI

SpecPilot AI is an AI purchase decision agent for desktop PC builds and laptops.

It helps a user say, "I need a 2 million KRW PC for video editing and gaming," then turns that request into a few realistic build or laptop options with compatibility checks, price evidence, review risk signals, and a final recommendation report.

## Product focus

This is not a generic shopping bot. The first product wedge is **computer and laptop purchasing**:

- Desktop PC build recommendations
- Laptop recommendations
- CPU/GPU/RAM/SSD/PSU compatibility checks
- Price comparison source aggregation
- Review and benchmark summary
- Upgrade path and buyer-fit explanation

Price comparison services, open markets, official stores, benchmark pages, and community reviews are treated as data sources. The product should not be branded around one source.

## MVP user stories

- As a first-time PC buyer, I want 3 build options within my budget so I do not overpay or buy incompatible parts.
- As a video editor, I want to know whether CPU, GPU, RAM, and SSD choices match Premiere Pro and DaVinci Resolve.
- As a gamer, I want a build matched to my monitor resolution and refresh rate.
- As a laptop buyer, I want to compare performance, weight, heat, fan noise, upgrade limits, and real purchase price.

## Agent workflow

The LangGraph workflow is explicit and inspectable:

1. Intent Parser - structure budget, purpose, category, must-haves, exclusions.
2. Clarifier - flag missing budget, display target, or compatibility requirements.
3. Query Planner - create search plans for specs, prices, reviews, and benchmarks.
4. Product Collector - collect desktop build or laptop candidates.
5. Deduplicator - normalize model names and remove duplicate variants.
6. Compatibility Checker - validate CPU socket, motherboard, PSU wattage, RAM and form factor.
7. Price Tracker - compute effective price with shipping/coupon/build fees.
8. Review Analyzer - summarize pros, cons, repeated complaints and risk signals.
9. Scoring Engine - score purpose fit, price, review trust, stability, preference and compatibility.
10. Verifier - check source links, price timestamp, and compatibility notes.
11. Report Writer - produce TOP 3, excluded options, timing and checklist.

## Stack

- FastAPI for the API layer
- LangGraph for stateful agent execution
- LangChain LCEL for prompt and deterministic report writing steps
- Neo4j for build, component, offer, seller, benchmark, review and compatibility graph
- PostgreSQL later for user history, saved comparisons and alerts
- Redis/Celery or Temporal later for scheduled price rechecks

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn specpilot_ai.api.main:app --reload
```

Open:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/product/brief`
- `http://127.0.0.1:8000/categories`
- `http://127.0.0.1:8000/graph/schema`

## Demo request

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "영상 편집과 게임용 데스크톱 200만원 안에서 맞춰줘",
    "category": "desktop_pc",
    "budget_krw": 2000000,
    "purpose": "Premiere Pro, DaVinci Resolve, QHD gaming",
    "must_haves": ["QHD 144Hz", "32GB RAM", "업그레이드 여지"],
    "channels": ["price_compare", "open_market", "official_store"]
  }'
```

## Optional Neo4j

```bash
docker compose up -d neo4j
```

Environment:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=specpilot-password
```

`DEMO_MODE=true` is the default, so no external API key or Neo4j instance is required for the current demo workflow.

## Scoring weights

- Purpose fit: 35%
- Price competitiveness: 22%
- Review trust: 15%
- Purchase stability: 10%
- Compatibility: 10%
- Personal preference: 8%

## Data model direction

Neo4j graph:

```cypher
(:Build)-[:USES]->(:Component)
(:Build)-[:SOLD_AS]->(:Offer)-[:OFFERED_BY]->(:Seller)
(:Build)-[:CHECKED_BY]->(:CompatibilitySignal)
(:Component)-[:HAS_BENCHMARK]->(:Benchmark)
(:Laptop)-[:HAS_REVIEW]->(:Review)
```

Relational tables later:

- users
- analysis_runs
- saved_builds
- offers
- price_alerts
- graph_traces

## Product roadmap

- Week 1: desktop/laptop requirements, component taxonomy and scoring rules
- Week 2: LangGraph state model, intent parser, clarifier
- Week 3: price/spec source adapters and model normalization
- Week 4: compatibility checker for CPU socket, board, RAM, PSU and case
- Week 5: review/benchmark analyzer and risk signal extraction
- Week 6: recommendation report API and comparison UI
- Week 7: saved builds, price alerts and trace dashboard
- Week 8: beta testing with real PC purchase scenarios

## Important policy

SpecPilot AI should explain uncertainty. It should say "review risk signal" or "price needs recheck," not make absolute claims about fake reviews, exact future prices, or guaranteed performance.
