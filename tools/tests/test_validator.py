#!/usr/bin/env python3
"""Controls for validate_workflows.py — the gate's own evidence, as a runnable file.

A method whose evidence cannot be re-run by a stranger is a claim, not a method.
This file is the method's evidence.

Run it:
    python3 tests/test_validator.py          # no pytest required
    python3 -m pytest tests/ -v              # also works if pytest is installed

Both directions are covered. A control that only tests refusal cannot tell a
working gate from a gate that refuses everything; a control that only tests
acceptance cannot tell a working gate from `return []`.

Controls:
  C1  the exact broken file that reached production            -> REFUSE
  C2  a known-good, GitHub-green workflow                      -> ACCEPT
  C3  real gate + honestly-labelled best-effort step           -> ACCEPT
  C4  a job where nothing can fail                             -> REFUSE (theater)
  C5  the rewritten claims workflows                           -> ACCEPT
  C6  an all-`uses:` job (real action gate)                    -> ACCEPT  [added v1.1]
  C7  an all-`uses:` job where every step is neutralised       -> REFUSE (theater)
  C8  unquoted `on:` (the YAML 1.1 "Norway problem")           -> ACCEPT
  C9  a run block with column-0 content                        -> REFUSE (parse defect)
  C10 a path that does not exist                               -> ERROR (exit 3, not 1)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validate_workflows import check_text  # noqa: E402

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

# C1 — the file that actually reached four public repos: a bash heredoc body at
# column 0 inside a `run:` block, which makes the whole document unparseable.
BROKEN_HEREDOC = '''\
name: claims
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
'''

# C2 — a normal, GitHub-green workflow: install then test, both failable.
GOOD_CI = '''\
name: ci
on:
  push:
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install
        run: pip install -e ".[dev]"
      - name: Test
        run: python -m pytest -q
'''

# C3 — a real gate plus an advisory step that is named as advisory. This was the
# 2026-10-04 star-lab case: the first verdict called it theater and was wrong.
REAL_GATE_PLUS_ADVISORY = '''\
name: lab-ci
on: [push]
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Unit tests
        run: python3 -m unittest tests.test_tokens tests.test_forge
      - name: CLI tests
        run: bash tests/test_lab_cli.sh
      - name: Doctor (best effort)
        run: python3 lab.py --doctor
        continue-on-error: true
'''

# C4 — theater: every run step neutralised. Nothing here can fail the build.
THEATER_RUN = '''\
name: always-green
on: [push]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Lint
        run: ruff check . || true
      - name: Types
        run: mypy . || true
'''

# C5 — the shape the four claims workflows were rewritten into: a thin caller.
CLAIMS_CALLER = '''\
name: claims
on:
  push:
  pull_request:
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Verify markdown claims
        run: python3 scripts/check_claims.py
'''

# C6 — an all-`uses:` job. A real action gate: a non-conforming PR title fails
# the build. v1.0 refused this. This control is the fix's proof.
ALL_USES_GATE = '''\
name: commitlint
on:
  pull_request_target:
    types: [opened, edited, synchronize]
jobs:
  lint-title:
    runs-on: ubuntu-latest
    steps:
      - uses: amannn/action-semantic-pull-request@v5
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
'''

# C7 — the same shape, but neutralised: now it really is theater.
ALL_USES_NEUTRALISED = '''\
name: pretend
on: [push]
jobs:
  lint-title:
    runs-on: ubuntu-latest
    steps:
      - uses: amannn/action-semantic-pull-request@v5
        continue-on-error: true
'''

# C8 — PyYAML parses an unquoted `on:` as boolean True. v1.0 reported a false
# "missing top-level 'on:'" on every valid file until this was handled.
NORWAY_PROBLEM = '''\
name: minimal
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: make
'''

# C9 — column-0 content inside a run block, without a heredoc: the pure defect.
COLUMN_ZERO_IN_RUN = '''\
name: bad
on: [push]
jobs:
  go:
    runs-on: ubuntu-latest
    steps:
      - name: step
        run: |
          echo start
echo stray
'''


# C11–C16 — promoted from tools/tests/probe_hunt.py on 2026-10-04. Each one is a defect
# the gate actually had: C11/C12 were false positives, C13–C16 false negatives.
PERMISSIONS_AFTER_RUN = '''\
name: p
on: [push]
jobs:
  a:
    runs-on: ubuntu-latest
    steps:
      - run: make
permissions:
  contents: read
'''

ENV_AFTER_RUN = '''\
name: p
on: [push]
jobs:
  a:
    runs-on: ubuntu-latest
    steps:
      - run: make
env:
  FOO: bar
'''

EMPTY_RUN_VALUE = '''\
name: p
on: [push]
jobs:
  a:
    runs-on: ubuntu-latest
    steps:
      - run: ""
'''

JOB_IF_FALSE = '''\
name: p
on: [push]
jobs:
  a:
    if: false
    runs-on: ubuntu-latest
    steps:
      - run: make
'''

STEP_IF_FALSE = '''\
name: p
on: [push]
jobs:
  a:
    runs-on: ubuntu-latest
    steps:
      - if: false
        run: make
'''

JOBS_EMPTY = '''\
name: p
on: [push]
jobs:
'''

JOBS_NULL = '''\
name: p
on: [push]
jobs: null
'''

CONDITIONAL_JOB_IS_NOT_THEATER = '''\
name: p
on: [push]
jobs:
  a:
    if: github.actor == 'dependabot[bot]'
    runs-on: ubuntu-latest
    steps:
      - uses: peter-evans/enable-pull-request-automerge@v3
'''

# C19 — THE KNOWN LIMIT, PINNED. check 6 exempts column-0 lines shaped like mapping keys,
# so a run block whose first unindented line is `foo: bar` leaks it out as a top-level key.
# The document stays valid YAML and the gate ACCEPTS. That is the documented limit in the
# module docstring — and this control pins it so a future change in either direction fails
# loudly here instead of silently altering behaviour.
#
# Expecting ACCEPT is deliberate. A documented limit with no control is a comment; with a
# control it is a tested fact. If someone later closes this hole, C19 fails and they update
# both. If someone later widens it, C19 fails too.
KNOWN_LIMIT_LEAKED_KEY = '''\
name: p
on: [push]
jobs:
  a:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo start
          more
foo: bar
'''


CONTROLS = [
    ("C1 broken heredoc pushed to production", BROKEN_HEREDOC, "refuse"),
    ("C2 normal GitHub-green ci", GOOD_CI, "accept"),
    ("C3 real gate + labelled advisory step", REAL_GATE_PLUS_ADVISORY, "accept"),
    ("C4 every run step neutralised", THEATER_RUN, "refuse"),
    ("C5 claims workflow as thin caller", CLAIMS_CALLER, "accept"),
    ("C6 all-uses job (real action gate)", ALL_USES_GATE, "accept"),
    ("C7 all-uses job, neutralised", ALL_USES_NEUTRALISED, "refuse"),
    ("C8 unquoted on: (Norway problem)", NORWAY_PROBLEM, "accept"),
    ("C9 column-0 content in a run block", COLUMN_ZERO_IN_RUN, "refuse"),
    ("C11 permissions: at column 0 after a run block", PERMISSIONS_AFTER_RUN, "accept"),
    ("C12 env: at column 0 after a run block", ENV_AFTER_RUN, "accept"),
    ("C13 step with an empty run value", EMPTY_RUN_VALUE, "refuse"),
    ("C14 job that is constantly disabled", JOB_IF_FALSE, "refuse"),
    ("C15 job whose every step is disabled", STEP_IF_FALSE, "refuse"),
    ("C16 empty jobs mapping", JOBS_EMPTY, "refuse"),
    ("C17 null jobs mapping", JOBS_NULL, "refuse"),
    ("C18 conditional job is NOT theater", CONDITIONAL_JOB_IS_NOT_THEATER, "accept"),
    ("C19 KNOWN LIMIT: leaked key-shaped line accepted", KNOWN_LIMIT_LEAKED_KEY, "accept"),
]



# --------------------------------------------------------------------------- #
# Assertions (pytest-compatible) and a standalone runner
# --------------------------------------------------------------------------- #

def _expect(name: str, text: str, want: str) -> tuple[bool, str]:
    errs = check_text(text)
    got = "refuse" if errs else "accept"
    ok = got == want
    detail = "; ".join(errs)[:110] if errs else "-"
    return ok, f"{'PASS' if ok else 'FAIL'}  {name:<44} want={want:<6} got={got:<6} {detail}"


def test_c1_broken_heredoc() -> None:
    assert check_text(BROKEN_HEREDOC), "the production defect must be refused"


def test_c2_good_ci() -> None:
    assert not check_text(GOOD_CI)


def test_c3_real_gate_plus_advisory() -> None:
    assert not check_text(REAL_GATE_PLUS_ADVISORY)


def test_c4_theater_run() -> None:
    assert check_text(THEATER_RUN)


def test_c5_claims_caller() -> None:
    assert not check_text(CLAIMS_CALLER)


def test_c6_all_uses_job_is_not_theater() -> None:
    """v1.1 regression control: an action step CAN fail the build."""
    assert not check_text(ALL_USES_GATE)


def test_c7_all_uses_neutralised_is_theater() -> None:
    assert check_text(ALL_USES_NEUTRALISED)


def test_c8_unquoted_on() -> None:
    assert not check_text(NORWAY_PROBLEM)


def test_c9_column_zero_in_run() -> None:
    assert check_text(COLUMN_ZERO_IN_RUN)


# System controls: these invoke the CLI, because the exit code is part of the contract.
def _system_controls() -> list[tuple[str, bool, str]]:
    """Return (name, passed, detail) for controls that test main(), not check_text()."""
    import contextlib
    import io

    from validate_workflows import main

    results: list[tuple[str, bool, str]] = []

    # C10 — a missing file must ERROR (3), not REFUSE (1). A CI step that treats any
    # non-zero exit as "refused as expected" passes when its own fixture is absent.
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        code = main(["validate_workflows.py", "/nonexistent/definitely-not-here.yml"])
    results.append((
        "C10 missing fixture errors (3), does not refuse (1)",
        code == 3,
        f"want=3 got={code}",
    ))

    return results


def main() -> int:
    print(__doc__.strip().splitlines()[0])
    print("=" * 100)
    failed = 0
    total = 0
    for name, text, want in CONTROLS:
        ok, line = _expect(name, text, want)
        print(line)
        total += 1
        if not ok:
            failed += 1
    for name, ok, detail in _system_controls():
        print(f"{'PASS' if ok else 'FAIL'}  {name:<44} {detail}")
        total += 1
        if not ok:
            failed += 1
    print("=" * 100)
    print(f"{total - failed}/{total} controls satisfied")
    if failed:
        print("GATE IS NOT TRUSTWORTHY — do not use it to judge a workflow.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
