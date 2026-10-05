import tempfile
import unittest
from pathlib import Path

from database.repository import DocumentRepository
from indexer.pipeline import IndexingPipeline
from model_cache import get_model_status
from retrieval.fusion import reciprocal_rank_fusion
from retrieval.embeddings import get_embedding_model
from retrieval.hybrid_search import HybridSearch
from retrieval.semantic_search import SemanticSearch
from retrieval.vector_store import VectorStore
from search_engine.engine import SearchEngine
from search_engine.models import Document


class StubEmbeddingModel:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] if "machine" in text else [0.0, 1.0] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0] if "learning" in text else [0.0, 1.0]


class Step5Tests(unittest.TestCase):
    def test_local_embedding_generation(self) -> None:
        status = get_model_status("sentence-transformers/all-MiniLM-L6-v2", "embedding")
        if status.state != "READY_LOCAL":
            self.skipTest("embedding model cache is not prepared; run python -m scripts.prepare_models")
        embedding = get_embedding_model("sentence-transformers/all-MiniLM-L6-v2").embed_query("local search")
        self.assertEqual(len(embedding), 384)
        self.assertTrue(all(isinstance(value, float) for value in embedding))

    def test_vector_storage_persists_and_searches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = VectorStore(Path(directory) / "vectors.db")
            store.upsert([("chunk", "doc", "note.txt", "note.txt", "machine learning", [1.0, 0.0])])
            restarted = VectorStore(Path(directory) / "vectors.db")
            results = restarted.search([1.0, 0.0], 5)
            self.assertEqual(restarted.count(), 1)
            self.assertEqual(results[0].chunk_id, "chunk")
            self.assertAlmostEqual(results[0].score, 1.0)
            self.assertEqual(restarted.search([0.0, 1.0], 5)[0].score, 0.0)

    def test_semantic_retrieval_and_rrf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = VectorStore(Path(directory) / "vectors.db")
            store.upsert([("chunk", "doc", "note.txt", "note.txt", "machine learning", [1.0, 0.0])])
            results = SemanticSearch(store, StubEmbeddingModel()).search("how systems learn")
            self.assertEqual(results[0].chunk_id, "chunk")
            self.assertEqual(results[0].document_id, "doc")
        fused = reciprocal_rank_fusion([[('a', None), ('b', None)], [('b', None), ('a', None)]], 60)
        self.assertEqual({item[0] for item in fused}, {"a", "b"})
        self.assertEqual(fused[0][1], fused[1][1])

    def test_hybrid_modes_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = VectorStore(Path(directory) / "vectors.db")
            store.upsert([("chunk", "doc", "note.txt", "note.txt", "machine learning", [1.0, 0.0])])
            engine = HybridSearch(
                SearchEngine([Document("chunk", "note.txt", "machine learning", "note.txt", "doc", "chunk")]),
                SemanticSearch(store, StubEmbeddingModel()),
            )
            self.assertEqual(engine.search("machine", "keyword")[0].metadata.retrieval_method, "keyword")
            self.assertEqual(engine.search("learning", "semantic")[0].metadata.retrieval_method, "semantic")
            hybrid = engine.search("learning")[0]
            self.assertEqual(hybrid.metadata.retrieval_method, "hybrid")
            self.assertIsNotNone(hybrid.metadata.fusion_score)

    def test_embedding_lifecycle_and_private_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = root / "documents"
            vault.mkdir()
            note = vault / "private.txt"
            note.write_text("machine learning notes", encoding="utf-8")
            vectors = VectorStore(root / "vectors.db")
            pipeline = IndexingPipeline(vault, DocumentRepository(root / "index.db"), 100, 10, vectors, StubEmbeddingModel())
            self.assertEqual(pipeline.rebuild()["files_indexed"], 1)
            self.assertEqual(vectors.count(), 1)
            stored_chunk = DocumentRepository(root / "index.db").all_chunks()[0]
            self.assertEqual(stored_chunk.source_path, "private.txt")
            self.assertNotIn(str(root), stored_chunk.source_path)
            self.assertEqual(pipeline.rebuild()["files_indexed"], 0)
            note.write_text("cybersecurity notes", encoding="utf-8")
            self.assertEqual(pipeline.rebuild()["files_indexed"], 1)
            note.unlink()
            self.assertEqual(pipeline.rebuild()["files_removed"], 1)
            self.assertEqual(vectors.count(), 0)


if __name__ == "__main__":
    unittest.main()