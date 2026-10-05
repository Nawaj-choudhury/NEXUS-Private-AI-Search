import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app
from backend.app.services.indexing import private_vault_for_user, rebuild_private_index
from database.connection import connect
from database.repository import DocumentRepository
from knowledge_graph.models import Edge, Graph, Node
from knowledge_graph.store import GraphStore


class AuthIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="nexus_auth_"))
        self.original_db = settings.database_path
        self.original_vault = settings.private_vault_path
        self.original_vector = settings.vector_store_path
        self.original_graph = settings.graph_store_path
        settings.database_path = self.temp_dir / "nexus.db"
        settings.private_vault_path = self.temp_dir / "private_vault"
        settings.vector_store_path = self.temp_dir / "vectors.db"
        settings.graph_store_path = self.temp_dir / "graph.db"
        self.client = TestClient(app)
        self.repo = DocumentRepository(settings.database_path)

    def tearDown(self) -> None:
        settings.database_path = self.original_db
        settings.private_vault_path = self.original_vault
        settings.vector_store_path = self.original_vector
        settings.graph_store_path = self.original_graph
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_register_login_and_me(self) -> None:
        response = self.client.post("/api/auth/register", json={"email": "user@example.com", "password": "StrongPass123!"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user"]["email"], "user@example.com")

        login = self.client.post("/api/auth/login", json={"email": "user@example.com", "password": "StrongPass123!"})
        self.assertEqual(login.status_code, 200)
        self.assertTrue(login.json()["authenticated"])

        me = self.client.get("/api/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["email"], "user@example.com")

    def test_duplicate_email_rejected(self) -> None:
        self.client.post("/api/auth/register", json={"email": "dupe@example.com", "password": "StrongPass123!"})
        response = self.client.post("/api/auth/register", json={"email": "dupe@example.com", "password": "StrongPass123!"})
        self.assertEqual(response.status_code, 409)

    def test_user_ids_do_not_collide_for_shared_email_local_part(self) -> None:
        first = self.client.post("/api/auth/register", json={"email": "same@example.com", "password": "StrongPass123!"})
        second = self.client.post("/api/auth/register", json={"email": "same@another.example", "password": "StrongPass123!"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertNotEqual(first.json()["user"]["user_id"], second.json()["user"]["user_id"])

    def test_non_web_search_and_research_require_authentication(self) -> None:
        for mode in ("semantic", "hybrid"):
            response = self.client.get("/api/search", params={"q": "private evidence", "mode": mode})
            self.assertEqual(response.status_code, 401)
        research = self.client.post("/api/research", json={"query": "private evidence", "mode": "hybrid"})
        self.assertEqual(research.status_code, 401)

    def test_graph_node_and_source_lookups_are_user_scoped(self) -> None:
        alpha = self.client.post("/api/auth/register", json={"email": "graph-alpha@example.com", "password": "StrongPass123!"}).json()["user"]["user_id"]
        beta = self.client.post("/api/auth/register", json={"email": "graph-beta@example.com", "password": "StrongPass123!"}).json()["user"]["user_id"]
        graph = Graph(
            (
                Node("doc:alpha", "document", "alpha-private.txt", "private", "doc-alpha", user_id=alpha),
                Node("doc:beta", "document", "beta-private.txt", "private", "doc-beta", user_id=beta),
                Node("concept:alpha", "concept", "machine learning", source_type="private", user_id=alpha),
                Node("concept:beta", "concept", "cybersecurity", source_type="private", user_id=beta),
            ),
            (
                Edge("doc:alpha", "concept:alpha", "MENTIONS", 1.0, 1, "test"),
                Edge("doc:beta", "concept:beta", "MENTIONS", 1.0, 1, "test"),
            ),
        )
        GraphStore(settings.graph_store_path).replace_graph(graph)
        self.client.post("/api/auth/login", json={"email": "graph-alpha@example.com", "password": "StrongPass123!"})
        foreign_graph = self.client.get("/api/graph/concept/doc%3Abeta")
        foreign_sources = self.client.get("/api/graph/sources/concept%3Abeta")
        self.assertEqual(foreign_graph.status_code, 200)
        self.assertEqual(foreign_graph.json()["nodes"], [])
        self.assertIsNone(foreign_graph.json()["center_id"])
        self.assertEqual(foreign_sources.json(), [])

    def test_private_search_is_isolated_between_users(self) -> None:
        alpha_registration = self.client.post("/api/auth/register", json={"email": "alpha@example.com", "password": "StrongPass123!"})
        beta_registration = self.client.post("/api/auth/register", json={"email": "beta@example.com", "password": "StrongPass123!"})
        alpha_user_id = alpha_registration.json()["user"]["user_id"]
        beta_user_id = beta_registration.json()["user"]["user_id"]

        alpha_cookie = self.client.cookies
        alpha_response = self.client.post("/api/auth/login", json={"email": "alpha@example.com", "password": "StrongPass123!"})
        self.assertEqual(alpha_response.status_code, 200)
        alpha_cookie = self.client.cookies

        self.repo.upsert_document(
            document_type="private",
            user_id=alpha_user_id,
            filename="alpha-private.txt",
            source_path="alpha-private.txt",
            content="alpha secret",
            document_id="doc-alpha",
            chunks=[("chunk-a-1", "doc-alpha", "alpha-private.txt", "alpha secret", 0)],
        )

        beta_login = self.client.post("/api/auth/logout", json={})
        self.assertEqual(beta_login.status_code, 200)

        beta_response = self.client.post("/api/auth/login", json={"email": "beta@example.com", "password": "StrongPass123!"})
        self.assertEqual(beta_response.status_code, 200)

        self.repo.upsert_document(
            document_type="private",
            user_id=beta_user_id,
            filename="beta-private.txt",
            source_path="beta-private.txt",
            content="beta secret",
            document_id="doc-beta",
            chunks=[("chunk-b-1", "doc-beta", "beta-private.txt", "beta secret", 0)],
        )

        alpha_after = self.client.post("/api/auth/login", json={"email": "alpha@example.com", "password": "StrongPass123!"})
        self.assertEqual(alpha_after.status_code, 200)
        private_results = self.client.get("/api/search", params={"q": "secret", "mode": "private"})
        self.assertEqual(private_results.status_code, 200)
        self.assertIn("alpha-private.txt", private_results.text)
        self.assertNotIn("beta-private.txt", private_results.text)

    def test_user_vault_rebuilds_preserve_document_and_vector_ownership(self) -> None:
        alpha = self.client.post("/api/auth/register", json={"email": "index-alpha@example.com", "password": "StrongPass123!"}).json()["user"]["user_id"]
        beta = self.client.post("/api/auth/register", json={"email": "index-beta@example.com", "password": "StrongPass123!"}).json()["user"]["user_id"]
        for user_id, filename, content in (
            (alpha, "alpha-private.txt", "alpha secret machine learning document"),
            (beta, "beta-private.txt", "beta secret cybersecurity document"),
        ):
            vault = private_vault_for_user(user_id)
            vault.mkdir(parents=True, exist_ok=True)
            (vault / filename).write_text(content, encoding="utf-8")
            result = rebuild_private_index(user_id)
            self.assertEqual(result["files_indexed"], 1)

        for user_id, expected_filename, hidden_filename in (
            (alpha, "alpha-private.txt", "beta-private.txt"),
            (beta, "beta-private.txt", "alpha-private.txt"),
        ):
            chunks = self.repo.all_chunks(user_id=user_id, source_type="private")
            self.assertEqual([chunk.filename for chunk in chunks], [expected_filename])
            self.assertTrue(all(chunk.user_id == user_id for chunk in chunks))
            self.assertNotIn(hidden_filename, str(chunks))

        with connect(settings.vector_store_path) as connection:
            owners = {row["user_id"] for row in connection.execute("SELECT DISTINCT user_id FROM embeddings").fetchall()}
        self.assertEqual(owners, {alpha, beta})


if __name__ == "__main__":
    unittest.main()
