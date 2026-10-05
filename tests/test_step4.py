import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter

from backend.app.api.search import search
from backend.app.api.indexing import rebuild_index
from backend.app.core.config import settings
from database.repository import DocumentRepository
from indexer.chunker import chunk_document
from indexer.cleaner import clean_text
from indexer.loaders import load_document
from indexer.metadata import metadata_for_file
from indexer.pipeline import IndexingPipeline
from search_engine.engine import SearchEngine
from search_engine.models import Document
from search_engine.scorer import BM25Scorer
from search_engine.tokenizer import tokenize


class Step4Tests(unittest.TestCase):
    def test_txt_and_markdown_loading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            txt = root / "note.txt"
            markdown = root / "note.md"
            txt.write_text("plain text", encoding="utf-8")
            markdown.write_text("# Markdown", encoding="utf-8")
            self.assertEqual(load_document(txt), "plain text")
            self.assertEqual(load_document(markdown), "# Markdown")

    def test_pdf_loading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blank.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=200)
            with path.open("wb") as stream:
                writer.write(stream)
            self.assertIsInstance(load_document(path), str)

    def test_cleaning_and_chunking(self) -> None:
        cleaned = clean_text("alpha  \n\n\n beta\x00")
        self.assertEqual(cleaned, "alpha\n\nbeta")
        chunks = chunk_document("doc", "note.txt", "abcdefghij", chunk_size=6, chunk_overlap=2)
        self.assertEqual([chunk.position for chunk in chunks], [0, 1])
        self.assertEqual(chunks[0].document_id, "doc")

    def test_metadata_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "note.md"
            path.write_text("content", encoding="utf-8")
            metadata = metadata_for_file(path, root)
            self.assertEqual(metadata.filename, "note.md")
            self.assertEqual(metadata.file_type, "md")
            self.assertEqual(metadata.source_path, "note.md")
            self.assertGreater(metadata.file_size, 0)

    def test_bm25_scoring_and_ranking(self) -> None:
        documents = [
            Document("one", "One", "machine learning machine", "one.txt"),
            Document("two", "Two", "machine", "two.txt"),
        ]
        engine = SearchEngine(documents, k1=1.5, b=0.75)
        results = engine.search("machine learning")
        self.assertEqual(results[0].document.id, "one")
        self.assertGreater(results[0].score, 0)
        self.assertIsInstance(BM25Scorer(), BM25Scorer)
        self.assertEqual(tokenize("Machine-learning"), ["machine", "learning"])

    def test_pipeline_duplicate_change_and_delete_handling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = root / "documents"
            vault.mkdir()
            note = vault / "note.txt"
            note.write_text("machine learning", encoding="utf-8")
            repository = DocumentRepository(root / "index.db")
            pipeline = IndexingPipeline(vault, repository, chunk_size=100, chunk_overlap=10)

            first = pipeline.rebuild()
            second = pipeline.rebuild()
            self.assertEqual(first["files_indexed"], 1)
            self.assertEqual(second["files_indexed"], 0)
            self.assertEqual(len(repository.all_chunks()), 1)

            note.write_text("cybersecurity defense", encoding="utf-8")
            changed = pipeline.rebuild()
            self.assertEqual(changed["files_indexed"], 1)
            self.assertEqual(repository.all_chunks()[0].content, "cybersecurity defense")

            note.unlink()
            removed = pipeline.rebuild()
            self.assertEqual(removed["files_removed"], 1)
            self.assertEqual(repository.all_chunks(), [])

    def test_api_search_uses_persistent_private_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = root / "documents"
            vault.mkdir()
            (vault / "private.txt").write_text("local machine learning notes", encoding="utf-8")
            repository = DocumentRepository(root / "index.db")
            IndexingPipeline(vault, repository, 100, 10).rebuild()
            original_vault, original_database, original_vectors = settings.private_vault_path, settings.database_path, settings.vector_store_path
            settings.private_vault_path, settings.database_path, settings.vector_store_path = vault, root / "index.db", root / "vectors.db"
            try:
                response = search("machine learning", mode="keyword")
            finally:
                settings.private_vault_path, settings.database_path, settings.vector_store_path = original_vault, original_database, original_vectors
            self.assertEqual(response.total_results, 1)
            self.assertEqual(response.results[0].source, "private.txt")
            self.assertTrue(response.results[0].document_id)
            self.assertTrue(response.results[0].chunk_id)

    def test_index_rebuild_api_reports_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = root / "documents"
            vault.mkdir()
            (vault / "private.txt").write_text("local indexing test", encoding="utf-8")
            original_vault, original_database, original_vectors = settings.private_vault_path, settings.database_path, settings.vector_store_path
            settings.private_vault_path, settings.database_path, settings.vector_store_path = vault, root / "index.db", root / "vectors.db"
            try:
                response = rebuild_index()
            finally:
                settings.private_vault_path, settings.database_path, settings.vector_store_path = original_vault, original_database, original_vectors
            self.assertEqual(response.files_discovered, 1)
            self.assertEqual(response.files_indexed, 1)
            self.assertEqual(response.files_failed, 0)
            self.assertEqual(response.chunks_created, 1)


if __name__ == "__main__":
    unittest.main()