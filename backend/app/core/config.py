from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NEXUS API"
    environment: Literal["development", "production"] = "development"
    cors_origins: list[str] = ["http://localhost:5173"]
    private_vault_path: Path = Path("private_vault")
    database_path: Path = Path("database/nexus.db")
    auth_enabled: bool = True
    session_cookie_name: str = "nexus_session"
    session_ttl_seconds: int = Field(default=86400, ge=300, le=30_000_000)
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    auth_rate_limit: int = Field(default=10, ge=1, le=1000)
    max_login_attempts: int = Field(default=5, ge=1, le=100)
    session_secret: str = "development-session-secret-change-me"
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    chunk_size: int = Field(default=800, ge=100, le=10_000)
    chunk_overlap: int = Field(default=120, ge=0, le=2_000)
    max_document_size: int = Field(default=20_000_000, ge=1_024, le=100_000_000)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_store_path: Path = Path("database/vectors.db")
    semantic_top_k: int = Field(default=10, ge=1, le=100)
    bm25_top_k: int = Field(default=10, ge=1, le=100)
    hybrid_top_k: int = Field(default=10, ge=1, le=100)
    rrf_k: int = Field(default=60, ge=1, le=1_000)
    reranker_enabled: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    candidate_top_k: int = Field(default=20, ge=1, le=100)
    final_top_k: int = Field(default=5, ge=1, le=50)
    duplicate_similarity_threshold: float = 0.9
    hf_home: str = ".cache/huggingface"
    hf_hub_cache: str = ".cache/huggingface/hub"
    sentence_transformers_home: str = ".cache/sentence-transformers"
    hf_hub_offline: bool = False
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:1b"
    research_top_k: int = Field(default=5, ge=1, le=20)
    max_context_chars: int = Field(default=6000, ge=500, le=50_000)
    research_temperature: float = 0.1
    local_ai_enabled: bool = True
    crawler_max_pages: int = Field(default=10, ge=1, le=100)
    crawler_max_depth: int = Field(default=1, ge=0, le=5)
    crawler_timeout: float = Field(default=10.0, gt=0, le=60)
    crawler_delay_seconds: float = Field(default=0.5, ge=0, le=60)
    crawler_user_agent: str = "NEXUS-Private-AI-Search/1.0"
    crawler_max_response_size: int = Field(default=2_000_000, ge=1_024, le=20_000_000)
    crawler_allow_localhost: bool = False
    graph_store_path: Path = Path("database/knowledge_graph.db")
    graph_max_depth: int = Field(default=2, ge=0, le=5)
    graph_max_nodes: int = Field(default=30, ge=1, le=200)
    graph_min_edge_weight: float = 1.0
    graph_max_concepts_per_document: int = 15
    graph_min_concept_frequency: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, origins: list[str]) -> list[str]:
        if not origins or any(origin == "*" for origin in origins):
            raise ValueError("cors_origins must contain explicit origins and cannot use '*'")
        return origins

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")) or any(character.isspace() for character in value):
            raise ValueError("ollama_base_url must be an absolute HTTP(S) URL")
        return value.rstrip("/")

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, overlap: int, info) -> int:
        chunk_size = info.data.get("chunk_size", 800)
        if overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return overlap

    @model_validator(mode="after")
    def validate_production_origins(self):
        if self.environment == "production" and any("localhost" in origin or "127.0.0.1" in origin for origin in self.cors_origins):
            raise ValueError("production CORS origins must not use localhost")
        if self.environment == "production" and not self.cookie_secure:
            raise ValueError("cookie_secure must be enabled in production")
        return self


settings = Settings()