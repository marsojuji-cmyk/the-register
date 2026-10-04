#!/usr/bin/env python3
"""Encode the Cursor-lane review findings as measurable cases, with POST-FIX expectations.

Purpose: measure the current gate against every finding before changing anything, and
re-measure after. A finding that cannot be measured is a claim, not a defect report.

Each case is (review_id, severity, description, yaml, expected_after_fix).
Run:  python3 tools/tests/review_probe.py
Exit: 0 when every case matches its post-fix expectation.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validate_workflows import check_text  # noqa: E402

HEAD = "name: p\non: [push]\njobs:\n"
JOB = "  a:\n    runs-on: ubuntu-latest\n    steps:\n"


CASES: list[tuple[str, str, str, str, str]] = [
    # ---- X1: neutralisation detection is a suffix test for ONE spelling
    ("X1a", "HIGH FN", "run: exit 0 (whole command cannot fail)",
     HEAD + JOB + "      - run: exit 0\n", "refuse"),
    ("X1b", "HIGH FN", "run: echo hi ||true  (no space before true)",
     HEAD + JOB + "      - run: echo hi ||true\n", "refuse"),
    ("X1c", "HIGH FN", "run: echo hi || true;  (trailing semicolon)",
     HEAD + JOB + "      - run: echo hi || true;\n", "refuse"),
    ("X1d", "HIGH FN", "run: echo hi || exit 0",
     HEAD + JOB + "      - run: echo hi || exit 0\n", "refuse"),
    ("X1e", "HIGH FN", "run: ':',  the bash no-op",
     HEAD + JOB + "      - run: ':'\n", "refuse"),

    # ---- X2: falsy literals beyond False and "false"
    ("X2a", "HIGH FN", "job if: 0",
     "name: p\non: [push]\njobs:\n  a:\n    if: 0\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\n", "refuse"),
    ("X2b", "HIGH FN", "step if: 0",
     HEAD + JOB + "      - if: 0\n        run: make\n", "refuse"),
    ("X2c", "HIGH FN", "job if: \"\" (empty string literal)",
     "name: p\non: [push]\njobs:\n  a:\n    if: \"\"\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\n", "refuse"),

    # ---- X3: needs is never read
    ("X3a", "MED-HIGH FN", "needs: [zzz] where job zzz does not exist",
     "name: p\non: [push]\njobs:\n  a:\n    needs: [zzz]\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\n", "refuse"),

    # ---- X4: a trigger that can never fire
    ("X4a", "MED FN", "top-level `on:` present but null",
     "name: p\non:\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\n", "refuse"),
    ("X4b", "MED FN", "top-level `on: {}` empty mapping",
     "name: p\non: {}\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\n", "refuse"),

    # ---- X5: the YAML-1.1 forgiveness clause matches ANY truthy key
    ("X5a", "MED FN", "no `on:` at all (control: must refuse)",
     "name: p\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\n", "refuse"),
    ("X5b", "MED FN", "no `on:` but a top-level `true: x` forgives it",
     "name: p\ntrue: x\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\n", "refuse"),

    # ---- X6: runs-on only tested for key presence
    ("X6a", "MED-LOW FN", "runs-on: null",
     "name: p\non: [push]\njobs:\n  a:\n    runs-on:\n    steps:\n      - run: make\n", "refuse"),
    ("X6b", "MED-LOW FN", "runs-on: \"\"",
     "name: p\non: [push]\njobs:\n  a:\n    runs-on: \"\"\n    steps:\n      - run: make\n", "refuse"),

    # ---- X7: a step is either uses or run, never both
    ("X7", "LOW-MED FN", "a step with BOTH uses: and run:",
     HEAD + "  a:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n        run: make\n", "refuse"),

    # ---- X13/X14/X15: FALSE POSITIVES on valid, documented workflows
    ("X13", "HIGH FP", "job-level `uses:` (reusable workflow) - no runs-on/steps by design",
     "name: p\non: [push]\njobs:\n  call:\n    uses: ./.github/workflows/reusable.yml\n", "accept"),
    ("X14", "HIGH FP", "continue-on-error as an expression (matrix-gated)",
     HEAD + "  a:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Test\n        run: make test\n        continue-on-error: ${{ matrix.experimental }}\n", "accept"),
    ("X15", "MED FP", "continue-on-error: \"false\" - evaluates falsy, so the step CAN fail",
     HEAD + "  a:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Test\n        run: make test\n        continue-on-error: \"false\"\n", "accept"),

    # ---- regression guards: things that must NOT change
    ("R1", "guard", "a normal real gate still accepted",
     HEAD + "  a:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: python3 -m pytest -q\n", "accept"),
    ("R2", "guard", "the star-lab shape: real gate + labelled best-effort step",
     HEAD + "  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: python3 -m unittest tests\n      - name: Doctor (best effort)\n        run: python3 lab.py --doctor\n        continue-on-error: true\n", "accept"),
    ("R3", "guard", "all-uses job (a real action gate) still accepted",
     "name: p\non: [pull_request]\njobs:\n  lint-title:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: amannn/action-semantic-pull-request@v5\n", "accept"),
    ("R4", "guard", "conditional job (not constant false) still accepted",
     "name: p\non: [push]\njobs:\n  a:\n    if: github.actor == 'dependabot[bot]'\n    runs-on: ubuntu-latest\n    steps:\n      - uses: peter-evans/enable-pull-request-automerge@v3\n", "accept"),
]


def main() -> int:
    print(f"{'id':<6}{'sev':<12}{'now':<8}{'want':<8}description")
    print("-" * 108)
    already_ok = 0
    for cid, sev, desc, text, want in CASES:
        errs = check_text(text)
        now = "refuse" if errs else "accept"
        ok = now == want
        already_ok += ok
        flag = "ok" if ok else "DEFECT"
        print(f"{cid:<6}{sev:<12}{now:<8}{want:<8}{desc}   [{flag}]")
        if not ok and errs:
            print(f"       └─ {errs[0][:96]}")
    print("-" * 108)
    print(f"{already_ok}/{len(CASES)} cases already match the post-fix expectation; "
          f"{len(CASES) - already_ok} to fix")
    return 0 if already_ok == len(CASES) else 1


if __name__ == "__main__":
    sys.exit(main())
