from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".cache", ".venv", "node_modules", "dist", "__pycache__", ".git"}
PATTERNS = {
    "hardcoded credential": re.compile(r"(?i)\b(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]"),
    "wildcard CORS": re.compile(r"allow_origins\s*=\s*\[\s*['\"]\*['\"]"),
    "unsafe HTML injection": re.compile(r"dangerouslySetInnerHTML|innerHTML\s*="),
    "subprocess execution": re.compile(r"\bsubprocess\.(run|Popen|call|check_call)|\bos\.(system|popen)\b"),
    "hardcoded cloud AI endpoint": re.compile(r"(?i)https?://[^\s'\"]*(openai|anthropic|groq)\.[^\s'\"]+"),
}


def source_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not SKIP_PARTS.intersection(path.parts) and path.suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".env", ".md"}
    ]


def main() -> int:
    findings: list[tuple[str, Path, int]] = []
    for path in source_files():
        if path == Path(__file__):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    if name == "hardcoded cloud AI endpoint" and "README" in path.name:
                        continue
                    findings.append((name, path.relative_to(ROOT), line_number))
    print("NEXUS static security check")
    if findings:
        for name, path, line_number in findings:
            print(f"FINDING: {name} at {path}:{line_number}")
        print(f"RESULT: {len(findings)} finding(s) require review")
        return 1
    print("RESULT: PASS - no configured dangerous patterns found")
    print("Scope: source files only; this is a static sanity check, not a professional security audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
