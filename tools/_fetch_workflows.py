#!/usr/bin/env python3
"""Fetch every GitHub Actions workflow from every public repo, for offline auditing."""
import json
import subprocess
import sys
from pathlib import Path

OWNER = "marsojuji-cmyk"
OUT = Path(__file__).resolve().parent / "workflows"
OUT.mkdir(parents=True, exist_ok=True)


def gh(*args: str) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)
    return r.stdout if r.returncode == 0 else ""


def main() -> int:
    repos = json.loads(gh("repo", "list", OWNER, "--limit", "100",
                          "--json", "name,isPrivate") or "[]")
    publics = [r["name"] for r in repos if not r["isPrivate"]]

    index = []
    for repo in publics:
        raw = gh("api", f"repos/{OWNER}/{repo}/contents/.github/workflows")
        try:
            entries = json.loads(raw)
        except Exception:
            entries = []
        if not isinstance(entries, list):
            entries = []
        for e in entries:
            path = e.get("path", "")
            if not path.endswith((".yml", ".yaml")):
                continue
            body = gh("api", "-H", "Accept: application/vnd.github.raw",
                      f"repos/{OWNER}/{repo}/contents/{path}")
            if not body.strip():
                continue
            d = OUT / repo
            d.mkdir(exist_ok=True)
            fname = Path(path).name
            (d / fname).write_text(body, encoding="utf-8")
            index.append({"repo": repo, "path": path,
                          "local": str((d / fname).relative_to(OUT))})

    (OUT.parent / "workflow-index.json").write_text(
        json.dumps(index, indent=2), encoding="utf-8")
    print(f"repos scanned: {len(publics)}")
    print(f"workflow files fetched: {len(index)}")
    for i in index:
        print(f"  {i['local']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
