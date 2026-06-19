from enum import StrEnum

from pydantic import BaseModel, Field


class RetrievalMode(StrEnum):
    vector = "vector"
    full_text = "full_text"
    text2cypher = "text2cypher"
    enhanced_graphrag = "enhanced_graphrag"


class OntologyNode(BaseModel):
    label: str
    description: str
    key_property: str
    examples: list[str] = Field(default_factory=list)


class OntologyRelationship(BaseModel):
    type: str
    source: str
    target: str
    description: str


class OntologySpec(BaseModel):
    domain: str
    nodes: list[OntologyNode]
    relationships: list[OntologyRelationship]
    constraints: list[str] = Field(default_factory=list)


class QueryRequest(BaseModel):
    question: str = Field(min_length=2)
    domain: str = "general"
    preferred_mode: RetrievalMode | None = None


class QueryResponse(BaseModel):
    question: str
    domain: str
    mode: RetrievalMode
    answer: str
    evidence: list[str]
    next_actions: list[str]


class ProductBrief(BaseModel):
    name: str
    one_liner: str
    target_users: list[str]
    core_workflows: list[str]
    stack: list[str]
