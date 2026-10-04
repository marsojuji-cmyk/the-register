#!/usr/bin/env python3
"""Generate the deliberately-invalid fixtures.

Why this file exists at all: `tools/tests/fixtures/broken-heredoc.yml` cannot be
committed through a write path that validates YAML — it is invalid on purpose, so
every YAML-validating writer refuses it by design.

That is a real defect class and it is recorded as I7 in INCIDENTS.md:

    A guard that prevents you from storing the evidence of the failure it guards
    against.

The fix is not to weaken the guard. It is to generate the artifact from code, where
the intent (this file exists to be rejected) is explicit and the content is a literal
string rather than a file some editor helpfully corrected.

Usage:
    python3 tools/tests/make_fixtures.py      # writes fixtures, prints what it wrote
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"

# The exact shape of the defect that reached four public repos: a heredoc body at
# column 0 inside a `run:` block, making the whole document unparseable.
BROKEN_HEREDOC = """name: claims
on: [push]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verify markdown claims
        run: |
          python3 - <<'PY'
import re, pathlib
for p in pathlib.Path(".").rglob("*.md"):
    print(p)
PY
"""

FILES = {"broken-heredoc.yml": BROKEN_HEREDOC}


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name, body in FILES.items():
        p = FIXTURES / name
        p.write_text(body, encoding="utf-8")
        print(f"wrote {p}  ({len(body)} bytes, intentionally invalid YAML)")
    print()
    print("These files are evidence. Do not 'fix' them — a valid one proves nothing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
