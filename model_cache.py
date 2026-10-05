from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

PROJECT_ROOT = Path(__file__).resolve().parent

ModelKind = Literal["embedding", "reranker"]
ModelState = Literal["READY_LOCAL", "NOT_CACHED", "DOWNLOAD_REQUIRED", "LOAD_FAILED"]


@dataclass(frozen=True)
class ModelCacheStatus:
    model_name: str
    kind: ModelKind
    state: ModelState
    cache_dir: Path
    detail: str = ""


def _resolve_path(value: str | None, default: Path) -> Path:
    candidate = Path(value).expanduser() if value else default
    return candidate if candidate.is_absolute() else (PROJECT_ROOT / candidate).resolve()


def configure_model_cache(project_root: Path = PROJECT_ROOT) -> dict[str, Path]:
    hf_home = _resolve_path(os.getenv("HF_HOME"), project_root / ".cache" / "huggingface")
    hub_cache = _resolve_path(os.getenv("HF_HUB_CACHE"), hf_home / "hub")
    sentence_transformers_home = _resolve_path(
        os.getenv("SENTENCE_TRANSFORMERS_HOME"),
        project_root / ".cache" / "sentence-transformers",
    )

    os.environ.setdefault("HF_HOME", str(hf_home))
    os.environ.setdefault("HF_HUB_CACHE", str(hub_cache))
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(sentence_transformers_home))
    os.environ.setdefault("HF_HUB_OFFLINE", "false")

    return {
        "hf_home": hf_home,
        "hf_hub_cache": hub_cache,
        "sentence_transformers_home": sentence_transformers_home,
    }


def _cache_directory_for_kind(kind: ModelKind) -> Path:
    cache_dirs = configure_model_cache()
    return cache_dirs["sentence_transformers_home" if kind == "embedding" else "hf_hub_cache"]


def _model_cache_root_for_kind(kind: ModelKind) -> Path:
    return _cache_directory_for_kind(kind)


def _safe_model_slug(model_name: str) -> str:
    return model_name.replace("/", "--").replace("\\", "--")


def _local_model_path(model_name: str, kind: ModelKind) -> Path:
    cache_root = _cache_directory_for_kind(kind)
    slug = _safe_model_slug(model_name)
    return cache_root / f"models--{slug}"


def _has_local_model_files(model_path: Path) -> bool:
    if not model_path.exists():
        return False
    if (model_path / "config.json").exists():
        return True
    if (model_path / "config_sentence_transformers.json").exists():
        return True
    if (model_path / "snapshots").exists() and any((snapshot / "config.json").exists() for snapshot in model_path.glob("snapshots/*")):
        return True
    return False


def is_model_cached(model_name: str, kind: ModelKind) -> bool:
    return _has_local_model_files(_local_model_path(model_name, kind))


def get_model_status(model_name: str, kind: ModelKind) -> ModelCacheStatus:
    cache_dir = _model_cache_root_for_kind(kind)
    model_dir = _local_model_path(model_name, kind)
    if not model_dir.exists():
        return ModelCacheStatus(model_name, kind, "NOT_CACHED", cache_dir, "Model files are not present in the local cache; run python -m scripts.prepare_models.")
    if not _has_local_model_files(model_dir):
        return ModelCacheStatus(model_name, kind, "DOWNLOAD_REQUIRED", cache_dir, "Cache directory exists but required files are incomplete; rerun python -m scripts.prepare_models.")

    try:
        if kind == "embedding":
            model = _load_embedding_model(model_name, local_only=True, cache_dir=_cache_directory_for_kind(kind))
            _ = model.encode(["warmup"], normalize_embeddings=True, show_progress_bar=False)
        else:
            model = _load_reranker_model(model_name, local_only=True, cache_dir=_cache_directory_for_kind(kind))
            _ = model.predict([("warmup", "warmup")], show_progress_bar=False, apply_softmax=False)
        return ModelCacheStatus(model_name, kind, "READY_LOCAL", cache_dir, "Model loaded from local cache.")
    except Exception as exc:
        return ModelCacheStatus(model_name, kind, "LOAD_FAILED", cache_dir, str(exc))


def _load_embedding_model(model_name: str, *, local_only: bool, cache_dir: Path | None = None):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        model_name,
        cache_folder=str(cache_dir or _cache_directory_for_kind("embedding")),
        local_files_only=local_only,
    )


def _load_reranker_model(model_name: str, *, local_only: bool, cache_dir: Path | None = None):
    from sentence_transformers import CrossEncoder

    return CrossEncoder(
        model_name,
        cache_folder=str(cache_dir or _cache_directory_for_kind("reranker")),
        local_files_only=local_only,
    )


def prepare_model(model_name: str, kind: ModelKind) -> ModelCacheStatus:
    cache_dir = _cache_directory_for_kind(kind)
    offline = os.getenv("HF_HUB_OFFLINE", "").strip().lower() == "true"
    if offline:
        raise RuntimeError("HF_HUB_OFFLINE=true is active; model preparation requires a network-enabled run to populate the local cache.")
    try:
        if kind == "embedding":
            model = _load_embedding_model(model_name, local_only=False, cache_dir=cache_dir)
            _ = model.encode(["warmup"], normalize_embeddings=True, show_progress_bar=False)
        else:
            model = _load_reranker_model(model_name, local_only=False, cache_dir=cache_dir)
            _ = model.predict([("warmup", "warmup")], show_progress_bar=False, apply_softmax=False)
        return get_model_status(model_name, kind)
    except Exception as exc:
        raise RuntimeError(
            f"Model preparation failed for {kind} model '{model_name}' in cache '{cache_dir}'. "
            "Run this command with network access: python -m scripts.prepare_models"
        ) from exc


def prepare_model_if_needed(model_name: str, kind: ModelKind) -> ModelCacheStatus:
    status = get_model_status(model_name, kind)
    if status.state == "READY_LOCAL":
        return status
    return prepare_model(model_name, kind)


def load_embedding_model_from_cache(model_name: str, *, allow_download: bool = False):
    cache_dir = _cache_directory_for_kind("embedding")
    try:
        return _load_embedding_model(model_name, local_only=not allow_download, cache_dir=cache_dir)
    except Exception as exc:
        status = get_model_status(model_name, "embedding")
        if status.state in {"NOT_CACHED", "DOWNLOAD_REQUIRED"}:
            raise RuntimeError(
                f"Embedding model '{model_name}' is not cached locally. Run 'python -m scripts.prepare_models' before runtime tests or application execution."
            ) from exc
        raise RuntimeError(f"Embedding model '{model_name}' could not be loaded locally: {status.detail}") from exc


def load_reranker_model_from_cache(model_name: str, *, allow_download: bool = False):
    cache_dir = _cache_directory_for_kind("reranker")
    try:
        return _load_reranker_model(model_name, local_only=not allow_download, cache_dir=cache_dir)
    except Exception as exc:
        status = get_model_status(model_name, "reranker")
        if status.state in {"NOT_CACHED", "DOWNLOAD_REQUIRED"}:
            raise RuntimeError(
                f"Reranker model '{model_name}' is not cached locally. Run 'python -m scripts.prepare_models' before runtime tests or application execution."
            ) from exc
        raise RuntimeError(f"Reranker model '{model_name}' could not be loaded locally: {status.detail}") from exc
