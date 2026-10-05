import json
from pathlib import Path

from database.connection import connect

from .models import Edge, Graph, Node


class GraphStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._initialize()

    def _initialize(self) -> None:
        with connect(self.database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS graph_nodes (
                    node_id TEXT PRIMARY KEY,
                    node_type TEXT NOT NULL,
                    label TEXT NOT NULL,
                    source_type TEXT,
                    document_id TEXT,
                    url TEXT,
                    domain TEXT,
                    occurrence_count INTEGER NOT NULL DEFAULT 0,
                    chunk_ids TEXT NOT NULL DEFAULT '[]',
                    user_id TEXT
                );
                CREATE TABLE IF NOT EXISTS graph_edges (
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    weight REAL NOT NULL,
                    evidence_count INTEGER NOT NULL,
                    method TEXT NOT NULL,
                    PRIMARY KEY (source_id, target_id, relation)
                );
                """
            )
            existing = {row["name"] for row in connection.execute("PRAGMA table_info(graph_nodes)").fetchall()}
            if "user_id" not in existing:
                connection.execute("ALTER TABLE graph_nodes ADD COLUMN user_id TEXT")

    def replace_graph(self, graph: Graph) -> None:
        with connect(self.database_path) as connection:
            connection.execute("DELETE FROM graph_edges")
            connection.execute("DELETE FROM graph_nodes")
            self._insert(connection, graph)

    def upsert_document(self, document_id: str, graph: Graph) -> None:
        self.remove_document(document_id)
        with connect(self.database_path) as connection:
            self._insert(connection, graph)
            self._remove_orphans(connection)

    def remove_document(self, document_id: str) -> None:
        with connect(self.database_path) as connection:
            source_rows = connection.execute("SELECT node_id FROM graph_nodes WHERE document_id = ?", (document_id,)).fetchall()
            source_ids = [row["node_id"] for row in source_rows]
            concept_ids: set[str] = set()
            for source_id in source_ids:
                concept_rows = connection.execute(
                    "SELECT target_id FROM graph_edges WHERE source_id = ? AND relation = 'MENTIONS'",
                    (source_id,),
                ).fetchall()
                concept_ids.update(row["target_id"] for row in concept_rows)
                connection.execute("DELETE FROM graph_edges WHERE source_id = ? OR target_id = ?", (source_id, source_id))
            connection.execute("DELETE FROM graph_nodes WHERE document_id = ?", (document_id,))
            for concept_id in concept_ids:
                supported = connection.execute(
                    "SELECT 1 FROM graph_edges WHERE relation = 'MENTIONS' AND target_id = ? LIMIT 1",
                    (concept_id,),
                ).fetchone()
                if supported is None:
                    connection.execute("DELETE FROM graph_edges WHERE source_id = ? OR target_id = ?", (concept_id, concept_id))
                    connection.execute("DELETE FROM graph_nodes WHERE node_id = ? AND node_type = 'concept'", (concept_id,))
            self._remove_orphans(connection)

    @staticmethod
    def _insert(connection, graph: Graph) -> None:
        connection.executemany(
            "INSERT OR REPLACE INTO graph_nodes (node_id, node_type, label, source_type, document_id, url, domain, occurrence_count, chunk_ids, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(node.node_id, node.node_type, node.label, node.source_type, node.document_id, node.url, node.domain, node.occurrence_count, json.dumps(node.chunk_ids), node.user_id) for node in graph.nodes],
        )
        connection.executemany(
            "INSERT INTO graph_edges (source_id, target_id, relation, weight, evidence_count, method) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(source_id, target_id, relation) DO UPDATE SET weight=excluded.weight, evidence_count=excluded.evidence_count, method=excluded.method",
            [(edge.source_id, edge.target_id, edge.relation, edge.weight, edge.evidence_count, edge.method) for edge in graph.edges],
        )

    @staticmethod
    def _remove_orphans(connection) -> None:
        connection.execute("DELETE FROM graph_nodes WHERE node_type = 'concept' AND node_id NOT IN (SELECT source_id FROM graph_edges WHERE relation = 'MENTIONS' UNION SELECT target_id FROM graph_edges WHERE relation = 'MENTIONS')")

    def graph(self, user_id: str | None = None) -> Graph:
        with connect(self.database_path) as connection:
            if user_id is None:
                nodes = connection.execute("SELECT * FROM graph_nodes ORDER BY node_id").fetchall()
            else:
                nodes = connection.execute("SELECT * FROM graph_nodes WHERE (source_type = 'public_web' OR user_id = ?) ORDER BY node_id", (user_id,)).fetchall()
            edges = connection.execute("SELECT * FROM graph_edges ORDER BY source_id, target_id, relation").fetchall()
        filtered_edges = []
        if user_id is not None:
            node_ids = {row["node_id"] for row in nodes}
            filtered_edges = [
                Edge(row["source_id"], row["target_id"], row["relation"], row["weight"], row["evidence_count"], row["method"])
                for row in edges
                if row["source_id"] in node_ids and row["target_id"] in node_ids
            ]
        else:
            filtered_edges = [Edge(row["source_id"], row["target_id"], row["relation"], row["weight"], row["evidence_count"], row["method"]) for row in edges]
        return Graph(
            tuple(Node(row["node_id"], row["node_type"], row["label"], row["source_type"], row["document_id"], row["url"], row["domain"], row["occurrence_count"], tuple(json.loads(row["chunk_ids"])), row["user_id"]) for row in nodes),
            tuple(filtered_edges),
        )

    def find_concepts(self, query: str, limit: int = 10, user_id: str | None = None) -> list[Node]:
        terms = [term.casefold() for term in query.split() if term]
        phrase = " ".join(terms)
        graph = self.graph(user_id=user_id)
        matches = [node for node in graph.nodes if node.node_type == "concept" and any(term in node.label.casefold() for term in terms)]
        return sorted(matches, key=lambda node: (0 if node.label.casefold() == phrase else 1, -node.occurrence_count, node.label))[:limit]