# Ontology Studio

Ontology Studio is a product MVP scaffold for building ontology-driven GraphRAG systems with LangChain, LangGraph, and Neo4j.

The product idea is simple: teams upload documents or structured data, the system proposes an ontology, stores entities and relationships in Neo4j, and routes questions through the best retrieval strategy.

## Why this product

Plain vector RAG is useful, but it often misses relationships such as ownership, hierarchy, legal dependency, investment exposure, publisher influence, or document lineage. GraphRAG adds a knowledge graph so the answer can use both semantic similarity and explicit relationships.

## Product modules

- **Ontology designer**: defines node labels, relationship types, properties, and constraints.
- **Ingestion pipeline**: turns documents, CSV rows, and domain text into graph-ready records.
- **Graph memory**: stores the ontology and extracted knowledge in Neo4j.
- **Retrieval router**: chooses vector search, full-text search, Text2Cypher, or enhanced GraphRAG.
- **LangGraph workflow**: keeps ingestion, search, validation, and answer generation as explicit state transitions.
- **API layer**: exposes product endpoints for frontend or B2B integration.

## Stack

- Python 3.12
- FastAPI
- LangChain
- LangGraph
- langchain-neo4j
- Neo4j AuraDB or local Neo4j
- uv for environment management

## Quick start

```bash
uv sync
cp .env.example .env
uv run uvicorn ontology_studio.api.main:app --reload
```

If `uv` is not installed:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn ontology_studio.api.main:app --reload
```

Open:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/product/brief`
- `http://127.0.0.1:8000/query`

The default configuration runs in demo mode, so it does not require an LLM key or Neo4j connection to inspect the workflow shape.

## Optional Neo4j

```bash
docker compose up -d neo4j
```

Then set:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=ontology-studio-password
```

## Example request

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"ETF 상품 추천에서 어떤 검색 전략을 써야 해?","domain":"finance"}'
```

## Product direction

The best first vertical is **Compliance Copilot**: legal documents, internal policies, owners, approval evidence, and audit events naturally form a graph. A second vertical is **ETF Advisor**, because products, issuers, sectors, assets, risk factors, and investor profiles are strongly relational.
