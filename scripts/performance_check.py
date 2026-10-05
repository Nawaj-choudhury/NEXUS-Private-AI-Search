from __future__ import annotations

from statistics import mean
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from database.models import StoredChunk
from knowledge_graph.builder import GraphBuilder
from reranker.local_reranker import LocalReranker
from retrieval.hybrid_search import HybridSearch
from retrieval.semantic_search import SemanticSearch
from retrieval.vector_store import VectorStore
from search_engine.engine import SearchEngine
from search_engine.models import Document


class BenchmarkEmbedding:
    def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


class BenchmarkReranker:
    def predict(self, pairs, **kwargs):
        return [1.0 if query.lower() in content.lower() else 0.5 for query, content in pairs]


def timed(operation, repeats: int = 5) -> float:
    samples = []
    for _ in range(repeats):
        started = perf_counter()
        operation()
        samples.append((perf_counter() - started) * 1000)
    return mean(samples)


def main() -> int:
    documents = [
        Document(f"chunk-{index}", f"note-{index}.txt", "machine learning search evidence", f"note-{index}.txt", "private", f"chunk-{index}")
        for index in range(50)
    ]
    engine = SearchEngine(documents)
    with TemporaryDirectory() as directory:
        vector_store = VectorStore(Path(directory) / "vectors.db")
        vector_store.upsert([
            (document.chunk_id, document.document_id or document.id, document.title, document.source, document.content, [1.0, 0.0])
            for document in documents
        ])
        semantic = SemanticSearch(vector_store, BenchmarkEmbedding(), top_k=10)
        reranker = LocalReranker(model=BenchmarkReranker(), enabled=True)
        hybrid = HybridSearch(engine, semantic, reranker=reranker, top_k=10, candidate_top_k=10, final_top_k=5)
        chunks = [StoredChunk(document_id=f"doc-{index}", chunk_id=f"chunk-{index}", filename=f"note-{index}.txt", source_path=f"note-{index}.txt", content="machine learning search evidence", position=0) for index in range(50)]
        builder = GraphBuilder()

        print("NEXUS local performance check")
        print(f"keyword_search_ms={timed(lambda: engine.search('machine learning')):.3f}")
        print(f"semantic_search_ms={timed(lambda: semantic.search('machine learning')):.3f}")
        print(f"hybrid_search_ms={timed(lambda: hybrid.search('machine learning')):.3f}")
        print(f"hybrid_reranked_search_ms={timed(lambda: hybrid.search('machine learning', rerank=True)):.3f}")
        graph = builder.build(chunks)
        print(f"graph_rebuild_ms={timed(lambda: builder.build(chunks)):.3f} nodes={len(graph.nodes)} edges={len(graph.edges)}")
        print(f"graph_query_ms={timed(lambda: [node for node in graph.nodes if node.node_type == 'concept'][:10]):.3f}")
        print("Privacy: benchmark uses synthetic in-memory content only.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
