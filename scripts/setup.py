from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    print("NEXUS setup check")
    print(f"python={sys.executable}")
    print(f"python_version={sys.version.split()[0]}")
    if sys.version_info < (3, 11):
        print("ERROR: Python 3.11 or newer is required")
        return 1
    missing = [module for module in ("fastapi", "pydantic", "sentence_transformers", "pypdf") if importlib.util.find_spec(module) is None]
    if missing:
        print(f"missing_python_packages={','.join(missing)}")
        print("Install with: python -m pip install -r requirements.txt")
        return 1
    print(f"node_available={bool(__import__('shutil').which('node'))}")
    print(f"npm_available={bool(__import__('shutil').which('npm'))}")
    for directory in (ROOT / "database", ROOT / "private_vault" / "documents", ROOT / ".cache"):
        directory.mkdir(parents=True, exist_ok=True)
        print(f"directory_ready={directory.relative_to(ROOT)}")
    from model_cache import get_model_status

    models = (("sentence-transformers/all-MiniLM-L6-v2", "embedding"), ("cross-encoder/ms-marco-MiniLM-L-6-v2", "reranker"))
    for name, kind in models:
        status = get_model_status(name, kind)
        print(f"{kind}_model={status.state}")
    print("Setup check complete. Model downloads are explicit: python -m scripts.prepare_models")
    print("Next: python -m scripts.demo_setup, then start the backend and frontend.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
