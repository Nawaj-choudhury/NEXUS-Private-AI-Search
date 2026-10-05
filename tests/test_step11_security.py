import tempfile
import unittest
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from backend.app.core.config import Settings, settings
from backend.app.api.research import research
from backend.app.api.routes import health_check, readiness_check
from backend.app.schemas.crawl import CrawlRequestSchema
from backend.app.schemas.research import ResearchRequestSchema
from crawler.url_utils import normalize_url
from database.models import StoredChunk
from database.repository import DocumentRepository
from indexer.pipeline import IndexingPipeline
from indexer.models import Document, DocumentMetadata
from knowledge_graph.builder import GraphBuilder
from knowledge_graph.store import GraphStore
from retrieval.vector_store import VectorStore
from backend.app.services.indexing import private_vault_for_user


class Step11SecurityTests(unittest.TestCase):
    def test_request_limits_reject_oversized_inputs(self):
        with self.assertRaises(ValidationError):
            ResearchRequestSchema(query="q" * 501)
        with self.assertRaises(ValidationError):
            CrawlRequestSchema(url="https://example.com", max_pages=101)

    def test_private_network_and_credential_urls_are_rejected(self):
        with self.assertRaises(ValueError):
            normalize_url("http://127.0.0.1:8000")
        with self.assertRaises(ValueError):
            normalize_url("https://user:password@example.com/private")

    def test_user_vault_rejects_absolute_and_traversal_ids(self):
        original_vault = settings.private_vault_path
        with tempfile.TemporaryDirectory() as directory:
            settings.private_vault_path = Path(directory)
            try:
                for user_id in ("C:\\outside", "..\\..\\outside", "../outside"):
                    with self.subTest(user_id=user_id), self.assertRaises(ValueError):
                        private_vault_for_user(user_id)
                safe_path = private_vault_for_user("user-safe")
                self.assertTrue(safe_path.resolve().is_relative_to((Path(directory).resolve() / "users")))
            finally:
                settings.private_vault_path = original_vault

    def test_user_vault_rejects_symlink_escape(self):
        original_vault = settings.private_vault_path
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            user_directory = root / "users" / "user-link"
            user_directory.mkdir(parents=True)
            outside = root / "outside"
            outside.mkdir()
            try:
                os.symlink(outside, user_directory / "documents", target_is_directory=True)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"Symlink creation unavailable: {type(error).__name__}")
            settings.private_vault_path = root
            try:
                with self.assertRaises(ValueError):
                    private_vault_for_user("user-link")
            finally:
                settings.private_vault_path = original_vault

    def test_production_requires_secure_session_cookie(self):
        with self.assertRaises(ValidationError):
            Settings(environment="production", cors_origins=["https://nexus.example"])
        production = Settings(environment="production", cors_origins=["https://nexus.example"], cookie_secure=True)
        self.assertTrue(production.cookie_secure)

    def test_private_file_pipeline_skips_unsupported_and_oversized_files(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "vault"
            vault.mkdir()
            (vault / "good.txt").write_text("local evidence", encoding="utf-8")
            (vault / "ignored.exe").write_text("not indexed", encoding="utf-8")
            (vault / "large.txt").write_text("x" * 32, encoding="utf-8")
            repository = DocumentRepository(Path(directory) / "index.db")
            result = IndexingPipeline(vault, repository, 100, 10, max_document_size=16).rebuild()
            self.assertEqual(result["files_indexed"], 1)
            self.assertEqual(len(repository.all_chunks()), 1)

    def test_deletion_removes_database_vectors_and_graph_document(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = DocumentRepository(root / "index.db")
            vector_store = VectorStore(root / "vectors.db")
            timestamp = datetime.now(timezone.utc)
            metadata = DocumentMetadata("doc-1", "note.txt", "text/plain", "note.txt", 8, timestamp, timestamp)
            repository.upsert_document(Document("doc-1", "note.txt", "text/plain", "note.txt", "evidence", metadata), "hash", [])
            vector_store.upsert([("chunk-1", "doc-1", "note.txt", "note.txt", "evidence", [1.0, 0.0])])
            graph_store = GraphStore(root / "graph.db")
            graph = GraphBuilder().build([StoredChunk("doc-1", "chunk-1", "note.txt", "note.txt", "machine learning evidence", 0)])
            graph_store.replace_graph(graph)
            repository.remove_missing_documents(set())
            vector_store.remove_missing_documents(set())
            graph_store.remove_document("doc-1")
            self.assertEqual(repository.all_chunks(), [])
            self.assertEqual(vector_store.count(), 0)
            self.assertEqual(graph_store.graph().nodes, ())

    def test_research_errors_do_not_expose_provider_details(self):
        with patch("backend.app.api.research.research_private_documents", side_effect=RuntimeError("C:\\private\\secret.txt")):
            with self.assertRaises(HTTPException) as context:
                research(ResearchRequestSchema(query="safe"))
        self.assertEqual(context.exception.status_code, 503)
        self.assertNotIn("secret.txt", str(context.exception.detail))

    def test_health_and_readiness_are_high_level(self):
        health = health_check()
        readiness = readiness_check()
        self.assertIn(health["status"], {"ok", "degraded"})
        self.assertIn(readiness["status"], {"ready", "not_ready"})
        self.assertNotIn("database_path", str(health))
        self.assertNotIn("cache", str(readiness))


if __name__ == "__main__":
    unittest.main()
