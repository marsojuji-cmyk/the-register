#!/usr/bin/env python3
"""Adversarial hunt: try to make the gate give a WRONG answer.

The controls in test_validator.py prove the gate handles the cases they cover. This hunts
a different set: probes written separately from the controls, so a gap in one is not
automatically a gap in the other.

**What this does NOT claim — Cursor review X18.** Every probe below is a literal string
written by the same lane that wrote the gate, with an expectation that lane chose. So this
is a *second pass by the same mind*, not independence, and it cannot cover cases nobody
imagined. Independence would require either a second reviewer (WEAK-SPOTS WS-4) or a
generator that writes cases nobody chose (WS-3, the fuzzer). An earlier revision of this
docstring said it hunted "the cases we did not think of", which was false and is why the
wording is now this specific.

Every probe states what a correct gate should do; anything where the gate disagrees is a
finding.

Run:  python3 tools/tests/probe_hunt.py
Exit: 0 if the gate behaved correctly on every probe, 1 if any probe found a defect.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validate_workflows import check_text  # noqa: E402

HEAD = 'name: p\non: [push]\njobs:\n'

# (id, what a correct gate should do, description, yaml)
PROBES: list[tuple[str, str, str, str]] = [
    ("P1", "ACCEPT", "top-level `permissions:` at column 0 AFTER a run block",
     HEAD + '  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\npermissions:\n  contents: read\n'),

    ("P2", "ACCEPT", "top-level `env:` at column 0 after a run block",
     HEAD + '  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\nenv:\n  FOO: bar\n'),

    ("P3", "ACCEPT", "a step NAME that contains the substring 'run:'",
     HEAD + '  a:\n    runs-on: ubuntu-latest\n    steps:\n      - name: "cargo run: build"\n        uses: actions/checkout@v4\n      - run: make\n'),

    ("P4", "REFUSE", "a step with an explicitly EMPTY run value (docstring claims non-empty)",
     HEAD + '  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: ""\n'),

    ("P5", "REFUSE", "a job that can NEVER run (`if: false`) - nothing in it can fail",
     HEAD + '  a:\n    if: false\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\n'),

    ("P6", "REFUSE", "every step gated by `if: false` - the job can never fail",
     HEAD + '  a:\n    runs-on: ubuntu-latest\n    steps:\n      - if: false\n        run: make\n'),

    ("P7", "REFUSE", "an empty `jobs:` mapping - nothing to run",
     'name: p\non: [push]\njobs:\n'),

    ("P8", "REFUSE", "`jobs:` present but null",
     'name: p\non: [push]\njobs: null\n'),

    ("P9", "REFUSE", "a step that is a bare string, not a mapping",
     HEAD + '  a:\n    runs-on: ubuntu-latest\n    steps:\n      - just a string\n'),

    ("P10", "ACCEPT", "two jobs, the second defined after a run block in the first",
     HEAD + '  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\n  b:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\n'),

    ("P11", "REFUSE", "a `uses:` step with no `runs-on` on the job",
     HEAD + '  a:\n    steps:\n      - uses: actions/checkout@v4\n'),

    ("P12", "ACCEPT", "a run block using an explicit indentation indicator (`|2`)",
     HEAD + '  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: |2\n          set -e\n          make\n'),

    ("P13", "REFUSE", "the exact heredoc defect, no leading name key",
     'name: p\non: [push]\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: |\n          python3 - <<PY\nprint(1)\nPY\n'),

    ("P14", "ACCEPT", "a neutralised step ALONGSIDE a real gate (the star-lab shape)",
     HEAD + '  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\n      - name: advisory\n        run: lint || true\n        continue-on-error: true\n'),
]


def main() -> int:
    findings = 0
    print(f"{'id':<5}{'verdict':<9}{'expected':<10}description")
    print("-" * 104)
    for pid, expect, desc, text in PROBES:
        errs = check_text(text)
        got = "REFUSE" if errs else "ACCEPT"
        ok = got == expect
        if not ok:
            findings += 1
        verdict = "ok" if ok else "DEFECT"
        print(f"{pid:<5}{verdict:<9}{expect:<10}{desc}")
        if not ok:
            for e in errs[:2]:
                print(f"       └─ {e[:96]}")
    print("-" * 104)
    print(f"{len(PROBES) - findings}/{len(PROBES)} probes behave correctly; "
          f"{findings} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
