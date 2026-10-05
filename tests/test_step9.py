import tempfile
import unittest
from pathlib import Path

from database.models import StoredChunk
from knowledge_graph.builder import GraphBuilder
from knowledge_graph.extractor import concept_id, extract_concepts, normalize_concept
from knowledge_graph.models import Graph, Node
from knowledge_graph.query import GraphQuery
from knowledge_graph.store import GraphStore


def chunk(document_id: str, chunk_id: str, content: str, source_type: str = "private", url: str | None = None) -> StoredChunk:
    return StoredChunk(document_id, chunk_id, "Notes", "private/path.txt", content, 0, source_type, url, "example.com" if url else None)


class Step9Tests(unittest.TestCase):
    def test_graph_api_and_search_routes_are_registered(self):
        from backend.app.main import app

        paths = set(app.openapi()["paths"])
        self.assertIn("/api/graph/rebuild", paths)
        self.assertIn("/api/graph/concept/{concept_id}", paths)
        self.assertIn("/api/graph/related/{concept_id}", paths)
        self.assertIn("/api/graph/sources/{concept_id}", paths)
        self.assertIn("/api/graph/search", paths)
        self.assertIn("/api/search", paths)

    def test_concept_normalization_and_technical_phrase_preservation(self):
        self.assertEqual(normalize_concept("Machine Learning!"), "machine-learning")
        self.assertEqual(concept_id("Machine Learning"), "concept:machine-learning")
        labels = {concept.label for concept in extract_concepts("Machine learning improves machine learning systems with vector search.")}
        self.assertIn("machine learning", labels)
        self.assertIn("vector search", labels)
        self.assertNotIn("with", labels)

    def test_builder_creates_evidence_backed_nodes_and_edges(self):
        graph = GraphBuilder(max_concepts_per_document=20).build([
            chunk("doc-1", "doc-1:c0", "Machine learning uses vector search and vector search supports retrieval."),
            chunk("doc-2", "doc-2:c0", "Machine learning supports feature engineering.", "public_web", "https://example.com/article"),
        ])
        node_ids = {node.node_id for node in graph.nodes}
        self.assertIn("concept:machine-learning", node_ids)
        self.assertIn("document:doc-1", node_ids)
        self.assertIn("web:doc-2", node_ids)
        self.assertTrue(any(edge.relation == "RELATED_TO" and edge.method == "same-chunk-cooccurrence" for edge in graph.edges))
        self.assertEqual(len({(edge.source_id, edge.target_id, edge.relation) for edge in graph.edges}), len(graph.edges))

    def test_store_persists_bounded_queries_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            store = GraphStore(Path(directory) / "graph.db")
            graph = GraphBuilder().build([chunk("doc-1", "c1", "Machine learning and vector search.", "public_web", "https://example.com/article")])
            store.replace_graph(graph)
            saved = store.graph()
            web_nodes = [node for node in saved.nodes if node.node_type == "web_source"]
            self.assertEqual(web_nodes[0].url, "https://example.com/article")
            self.assertNotIn("private/path.txt", str(saved))
            result = GraphQuery(store).around("concept:machine-learning", max_nodes=2, max_depth=1)
            self.assertLessEqual(len(result.graph.nodes), 2)

    def test_document_update_and_delete_remove_orphans(self):
        with tempfile.TemporaryDirectory() as directory:
            store = GraphStore(Path(directory) / "graph.db")
            builder = GraphBuilder()
            first = builder.build([chunk("doc-1", "c1", "Machine learning systems.")])
            store.replace_graph(first)
            updated = builder.build([chunk("doc-1", "c1", "Vector search systems.")])
            store.replace_graph(updated)
            self.assertNotIn("concept:machine-learning", {node.node_id for node in store.graph().nodes})
            store.remove_document("doc-1")
            self.assertEqual(store.graph().nodes, ())
            self.assertEqual(store.graph().edges, ())


if __name__ == "__main__":
    unittest.main()
