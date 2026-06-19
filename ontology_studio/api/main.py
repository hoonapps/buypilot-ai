from fastapi import FastAPI

from ontology_studio.core.config import get_settings
from ontology_studio.core.models import ProductBrief, QueryRequest, QueryResponse
from ontology_studio.graph.neo4j_client import Neo4jRepository
from ontology_studio.graph.ontology import default_ontology
from ontology_studio.workflows.retrieval import run_query

app = FastAPI(
    title="Ontology Studio API",
    version="0.1.0",
    description="Ontology-driven GraphRAG API with LangChain, LangGraph and Neo4j.",
)


@app.get("/health")
def health() -> dict[str, str | bool]:
    settings = get_settings()
    repo = Neo4jRepository(settings)
    try:
        neo4j_ready = repo.ping()
    finally:
        repo.close()
    return {
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "neo4j_ready": neo4j_ready,
    }


@app.get("/product/brief", response_model=ProductBrief)
def product_brief() -> ProductBrief:
    return ProductBrief(
        name="Ontology Studio",
        one_liner=(
            "Upload domain knowledge, design an ontology, "
            "and ship graph-grounded AI answers."
        ),
        target_users=[
            "AI service builders",
            "Compliance and legal operations teams",
            "Financial research and product teams",
            "Enterprise knowledge management teams",
        ],
        core_workflows=[
            "Ontology design",
            "Document and CSV ingestion",
            "Neo4j graph construction",
            "Vector, full-text and Text2Cypher retrieval",
            "LangGraph stateful answer workflow",
        ],
        stack=["FastAPI", "LangChain", "LangGraph", "Neo4j", "langchain-neo4j"],
    )


@app.get("/ontology/{domain}")
def ontology(domain: str) -> dict[str, object]:
    settings = get_settings()
    spec = default_ontology(domain)
    repo = Neo4jRepository(settings)
    try:
        preview = repo.ontology_preview(spec)
    finally:
        repo.close()
    return {"ontology": spec.model_dump(), "preview": preview}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    return run_query(request)
