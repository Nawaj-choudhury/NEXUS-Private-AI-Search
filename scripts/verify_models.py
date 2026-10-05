from __future__ import annotations

from model_cache import configure_model_cache, get_model_status

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def check_embedding() -> None:
    status = get_model_status(EMBEDDING_MODEL, "embedding")
    print(f"Embedding model status: {status.state} | cache={status.cache_dir}")
    if status.state != "READY_LOCAL":
        raise RuntimeError(f"Embedding model is not available locally: {status.detail}")
    from sentence_transformers import SentenceTransformer

    cache_dir = status.cache_dir
    model = SentenceTransformer(EMBEDDING_MODEL, cache_folder=str(cache_dir), local_files_only=True)
    vector = model.encode(["nexus local verification"], normalize_embeddings=True, show_progress_bar=False)
    if vector.shape[0] != 1:
        raise RuntimeError(f"Unexpected embedding output shape: {vector.shape}")
    print(f"Embedding dims: {vector.shape[1]}")


def check_reranker() -> None:
    status = get_model_status(RERANKER_MODEL, "reranker")
    print(f"Reranker model status: {status.state} | cache={status.cache_dir}")
    if status.state != "READY_LOCAL":
        raise RuntimeError(f"Reranker model is not available locally: {status.detail}")
    from sentence_transformers import CrossEncoder

    cache_dir = status.cache_dir
    model = CrossEncoder(RERANKER_MODEL, cache_folder=str(cache_dir), local_files_only=True)
    scores = model.predict([("nexus search", "private ai search engine")], show_progress_bar=False, apply_softmax=False)
    if not hasattr(scores, "__len__") or len(scores) != 1:
        raise RuntimeError(f"Unexpected reranker output: {scores}")
    print(f"Reranker output length: {len(scores)}")


def main() -> int:
    configure_model_cache()
    print("Verifying local model cache...")
    check_embedding()
    check_reranker()
    print("LOCAL MODEL VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
