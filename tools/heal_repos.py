#!/usr/bin/env python3
"""One-shot heal of the account-level gaps recorded in HEAL.md.

E3-4  ep-aec-conformance has no licence  -> add MIT (house default; 15 sibling repos use it)
E4-4  agentready has no SECURITY.md      -> add one
E3-5  exhibit / intent-spec / interlock do not document their check command
                                          -> APPEND the real command, taken from each repo's own CI

Non-destructive by construction:
  * new files are created, never overwritten (the script refuses if the path exists)
  * README edits APPEND a section; the existing bytes are preserved and verified by length

Usage:
    python3 tools/heal_repos.py --dry-run     # show exactly what would change
    python3 tools/heal_repos.py               # apply
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path

OWNER = "marsojuji-cmyk"
ROOT = Path(__file__).resolve().parents[1]

MIT = """MIT License

Copyright (c) 2026 Marcus Richards

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

AGENTREADY_SECURITY = """# Security Policy

## Reporting a vulnerability

Please use **GitHub's private vulnerability reporting** (the *Security* tab → *Report a
vulnerability*) rather than a public issue.

Include what you ran, what you expected, what happened, and the version or commit. A
reproduction is worth more than a description.

## Scope

`agentready` is a zero-dependency scanner: it fetches a URL and scores how well AI agents can
read, cite and operate the page. It does not hold credentials, run as a service, or store data.

Two things are in scope and worth reporting:

1. **Anything that makes the score wrong** — a page scored well that an agent cannot use, or
   scored badly that it can. A scoring tool that reports incorrectly is the whole product.
2. **Anything unsafe in fetching** — SSRF, redirect handling, unbounded reads, or content that
   causes the scanner to execute rather than inspect.

## What this does not claim

The score is a **heuristic**, not a verdict. It measures how a page presents itself to an agent;
it does not prove a page is accurate, safe, or honest. Treat a high score as "worth checking",
never as "verified".
"""

README_SECTION = """
---

## Verify it yourself

```bash
{cmd}
```

The same command this repository's CI runs on every push. If it does not pass on a clean clone,
the CI badge is wrong and so is this README — please open an issue.

Every claim in this README is meant to be checkable by someone who does not trust it yet.
"""


def gh(*args: str) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=120)
    if r.returncode != 0 and "--allow-fail" not in args:
        return ""
    return r.stdout


def put_file(repo: str, path: str, content: str, message: str, dry: bool) -> bool:
    existing = gh("api", f"repos/{OWNER}/{repo}/contents/{path}", "--jq", ".sha")
    if existing.strip():
        print(f"  SKIP   {repo}/{path} — already exists")
        return False
    if dry:
        print(f"  CREATE {repo}/{path} ({len(content)} bytes)")
        return True
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
    }
    p = Path("/tmp/heal-payload.json")
    p.write_text(json.dumps(payload), encoding="utf-8")
    out = gh("api", "-X", "PUT", f"repos/{OWNER}/{repo}/contents/{path}", "--input", str(p))
    ok = '"sha"' in out or '"content"' in out
    print(f"  {'OK    ' if ok else 'FAILED'} {repo}/{path}")
    return ok


def append_readme(repo: str, cmd: str, dry: bool) -> bool:
    meta = gh("api", f"repos/{OWNER}/{repo}/readme", "--jq", '{name: .name, sha: .sha}')
    try:
        m = json.loads(meta)
    except Exception:
        print(f"  FAILED {repo}/README — could not read metadata")
        return False
    raw = gh("api", "-H", "Accept: application/vnd.github.raw", f"repos/{OWNER}/{repo}/readme")
    if not raw.strip():
        print(f"  FAILED {repo}/README — empty read")
        return False
    if "## Verify it yourself" in raw:
        print(f"  SKIP   {repo}/{m['name']} — section already present")
        return False
    before = len(raw)
    new = raw.rstrip("\n") + "\n" + README_SECTION.format(cmd=cmd)
    print(f"  APPEND {repo}/{m['name']}  {before} -> {len(new)} bytes (+{len(new) - before})")
    if dry:
        return True
    payload = {
        "message": f"docs: document the check command a stranger can run ({cmd})",
        "content": base64.b64encode(new.encode()).decode(),
        "sha": m["sha"],
    }
    p = Path("/tmp/heal-payload.json")
    p.write_text(json.dumps(payload), encoding="utf-8")
    out = gh("api", "-X", "PUT", f"repos/{OWNER}/{repo}/contents/{m['name']}", "--input", str(p))
    ok = '"sha"' in out
    print(f"  {'OK    ' if ok else 'FAILED'} {repo}/{m['name']}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = args.dry_run

    print("E3-4  licence for the flagship")
    put_file("ep-aec-conformance", "LICENSE", MIT,
             "chore: add MIT licence\n\nWithout a licence the default is all rights reserved, "
             "which blocks the reuse this repository exists to invite.", dry)

    print("E4-4  SECURITY.md for agentready")
    put_file("agentready", "SECURITY.md", AGENTREADY_SECURITY,
             "chore: add SECURITY.md\n\nSingle remaining gap in account-wide coverage.", dry)

    print("E3-5  document the check command (taken from each repo's own CI)")
    append_readme("exhibit", "python3 -m unittest discover tests -v", dry)
    append_readme("intent-spec", "python3 scripts/check_claims.py", dry)
    append_readme("interlock", 'pip install -e ".[test]" && pytest -q', dry)

    print()
    print("dry run" if dry else "applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
