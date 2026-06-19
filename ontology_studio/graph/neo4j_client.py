from collections.abc import Iterable

from neo4j import GraphDatabase

from ontology_studio.core.config import Settings
from ontology_studio.core.models import OntologySpec


class Neo4jRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._driver = None
        if not settings.demo_mode:
            self._driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password),
            )

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def ping(self) -> bool:
        if self.settings.demo_mode:
            return True
        if not self._driver:
            return False
        self._driver.verify_connectivity()
        return True

    def ontology_preview(self, ontology: OntologySpec) -> list[str]:
        lines = [f"Domain: {ontology.domain}"]
        lines.extend(f"(:{node.label} {{{node.key_property}}})" for node in ontology.nodes)
        lines.extend(
            f"(:{rel.source})-[:{rel.type}]->(:{rel.target})"
            for rel in ontology.relationships
        )
        return lines

    def create_constraints(self, ontology: OntologySpec) -> list[str]:
        statements = [
            f"CREATE CONSTRAINT {node.label.lower()}_{node.key_property}_unique IF NOT EXISTS "
            f"FOR (n:{node.label}) REQUIRE n.{node.key_property} IS UNIQUE"
            for node in ontology.nodes
        ]
        if self.settings.demo_mode:
            return statements
        self._execute_write(statements)
        return statements

    def _execute_write(self, statements: Iterable[str]) -> None:
        if not self._driver:
            raise RuntimeError("Neo4j driver is not configured")
        with self._driver.session(database=self.settings.neo4j_database) as session:
            for statement in statements:
                session.run(statement)
