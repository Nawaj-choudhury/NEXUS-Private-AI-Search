from __future__ import annotations

from model_cache import configure_model_cache, get_model_status, prepare_model

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def main() -> int:
    configure_model_cache()
    print("Preparing local AI models...")
    for model_name, kind in [(EMBEDDING_MODEL, "embedding"), (RERANKER_MODEL, "reranker")]:
        try:
            status = prepare_model(model_name, kind)
        except Exception as exc:
            print(f"{kind.upper()} MODEL PREPARATION FAILED: {model_name}")
            print(exc)
            return 1
        print(f"{kind.upper()} model: {model_name}")
        print(f"  state={status.state}")
        print(f"  cache={status.cache_dir}")
        print(f"  detail={status.detail or 'ok'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
