#!/usr/bin/env python3
"""Pre-push gate for GitHub Actions workflow files.

Refuses to let a workflow be pushed that GitHub will reject or that cannot fail.

Built after a real incident: a workflow embedding a bash heredoc as an unindented
YAML plain scalar was pushed to four public repos. GitHub could not parse it, so
each run reported `failure` with ZERO jobs — which looks like a failing test and
is actually a broken file.

Checks:
  1. valid YAML (strict)
  2. top-level `on:` and `jobs:` present, with `jobs` non-null and non-empty
  3. each job has `runs-on` and `steps`
  4. every step is `uses:` or a non-empty `run:`
  5. THEATER: rejects a job in which no step can fail the build — a fully neutralised
     `run`, `continue-on-error: true`, a constantly-false `if:`, or a job that is
     itself constantly disabled
  6. no line at column 0 inside a run block (the exact defect above)

Exit codes are a contract, because CI asserts on them:
    0  all targets valid
    1  at least one target REFUSED  (a judgement about content)
    2  usage error
    3  at least one target could not be read or parsed (an ERROR, not a judgement)

--------------------------------------------------------------------------------
VERSION HISTORY — every entry found by RUNNING it, not by reading it
--------------------------------------------------------------------------------
v1.1 — 2026-10-04 — FALSE POSITIVE. v1.0 counted only `run:` steps as failable, so every
all-`uses:` job was refused as theater. 5 refusals, all false positives: three
commitlint jobs (amannn/action-semantic-pull-request — genuine gates) and two
automerge jobs (tasks, not checks). An action step can fail the build. The gate was
wrong, not the workflows. Fix: a `uses:` step counts as failable unless neutralised.

v1.2 — 2026-10-04 — 1 and 3 were indistinguishable. An uncaught FileNotFoundError
exits 1, so a CI step asserting "non-zero means refused" would pass with its own
fixture missing. Errors now exit 3.

v1.3 — 2026-10-04 — four fixes, all found by tools/tests/probe_hunt.py (8/14 probes
behaved correctly before; the six defects are now permanent controls C11–C18):
  (a) FALSE POSITIVE: the column-0 rule used a hardcoded exempt list, so any OTHER
      top-level key following a run block was accused — `permissions:`, `env:`, …
      Now a column-0 line shaped like a mapping key ends the block instead.
  (b) FALSE NEGATIVE: `doc.get("jobs") or {}` masked `jobs: null` and an empty
      `jobs:` mapping. Both produce a workflow that can never fail. Both refused.
  (c) FALSE NEGATIVE: a job with `if: false` can never run, so nothing in it can
      fail. Accepted silently. Now refused as theater.
  (d) FALSE NEGATIVE: a step with `if: false` counted as failable. Now excluded.
  Plus: a step whose `run:` is present but empty is now reported (check 4 said
  "non-empty" and did not enforce it).

Principle these incidents establish: a false positive in a gate is as damaging as
a false negative. A gate that refuses correct work teaches its users to ignore it,
and an ignored gate protects nothing.

KNOWN LIMIT, stated rather than implied: check 6 exempts column-0 lines that look
like mapping keys, so a heredoc whose first unindented line is literally `foo: bar`
slips past check 6. It is usually still caught by check 1, because the remaining
unindented lines make the document unparseable. A heuristic with a floor, not a proof.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

__version__ = "1.3"

# A column-0 line matching this is a top-level mapping key, not run-block content.
_TOP_LEVEL_KEY = re.compile(r"^[A-Za-z_][\w.\-]*:")


def _constant_false(value) -> bool:
    """True only if an `if:` expression can never evaluate true.

    Deliberately narrow. `if: github.actor == 'dependabot[bot]'` is a real gate for the
    runs it applies to and must not be flagged. A literal false — YAML boolean, or the
    string "false" — can never run, which makes everything inside it unfailable.
    """
    if value is False:
        return True
    if isinstance(value, str) and value.strip().strip("'\"").lower() == "false":
        return True
    return False


def check_text(raw: str) -> list[str]:
    """Validate one workflow's YAML text. Returns refusals (empty list = OK)."""
    errs: list[str] = []

    # check 6 first: it is a parse failure disguised as a content failure
    in_run = False
    for lineno, line in enumerate(raw.splitlines(), 1):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        if in_run and indent == 0:
            if _TOP_LEVEL_KEY.match(stripped):
                in_run = False  # the block ended; this is a new top-level key  (v1.3)
            else:
                errs.append(
                    f"line {lineno}: column-0 content inside a run block "
                    f"(this is what makes the file unparseable): {line[:60]!r}"
                )
                in_run = False
        if "run:" in line and indent > 0:
            in_run = True

    try:
        doc = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        errs.append(f"INVALID YAML: {exc}")
        return errs

    if not isinstance(doc, dict):
        errs.append("top level is not a mapping")
        return errs
    # YAML 1.1 parses an unquoted `on:` key as the BOOLEAN True (PyYAML behavior).
    # Accept either spelling rather than reporting a false "missing top-level 'on:'".
    keys = {k if isinstance(k, str) else str(k) for k in doc}
    if "on" not in keys and True not in doc:
        errs.append("missing top-level 'on:'")

    if "jobs" not in keys:
        errs.append("missing top-level 'jobs:'")
        return errs
    jobs = doc.get("jobs")
    if not isinstance(jobs, dict):
        # v1.3: `or {}` used to mask `jobs: null`.
        errs.append("'jobs' is not a mapping (or is null)")
        return errs
    if not jobs:
        # v1.3: an empty jobs mapping is a workflow that can never fail. Pure theater.
        errs.append("'jobs' is empty — a workflow with no jobs can never fail")
        return errs

    for jname, job in jobs.items():
        if not isinstance(job, dict):
            errs.append(f"job {jname}: not a mapping")
            continue
        # v1.3: a constantly-disabled job is the canonical way to switch a check off
        # while leaving it green. It can never run, so nothing in it can fail.
        if _constant_false(job.get("if")):
            errs.append(
                f"job {jname}: THEATER — job `if:` is constantly false, so it can never "
                f"run and nothing in it can fail the build"
            )
            continue
        if "runs-on" not in job:
            errs.append(f"job {jname}: missing 'runs-on'")
        steps = job.get("steps")
        if not isinstance(steps, list) or not steps:
            errs.append(f"job {jname}: missing/empty 'steps'")
            continue
        failable = 0
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                errs.append(f"job {jname} step {i}: not a mapping")
                continue
            if "uses" not in step and "run" not in step:
                errs.append(f"job {jname} step {i}: neither 'uses' nor 'run'")
            run = step.get("run")
            if "run" in step and not (isinstance(run, str) and run.strip()):
                # v1.3: check 4 claimed "non-empty value" and did not enforce it.
                errs.append(f"job {jname} step {i}: 'run' is present but empty")
            # A step is UNFAILABLE if it is neutralised three ways: the whole command is
            # neutralised, the step is continue-on-error, or it can never run at all.
            # A local `chmod ... || true` inside an otherwise real command is not theater.
            neutralised = (
                bool(step.get("continue-on-error"))
                or _constant_false(step.get("if"))  # v1.3
            )
            if isinstance(run, str) and run.strip():
                if not run.strip().endswith("|| true") and not neutralised:
                    failable += 1
            elif step.get("uses") and not neutralised:
                # v1.1: an action step can fail the build. Counting only `run:` steps made
                # every all-`uses:` job look like theater — 5 false positives, 2026-10-04.
                failable += 1
        # THEATER is a property of the WORKFLOW, not of one step: it is theater when
        # nothing in the job can fail the build. An advisory step alongside a real gate
        # is legitimate and, if it is labelled as such, honest.
        if failable == 0:
            errs.append(
                f"job {jname}: THEATER — no step in this job can fail the build "
                f"(every run step is neutralised and/or continue-on-error)"
            )
    return errs


def check_file(path: Path) -> list[str]:
    """Validate one workflow file. Returns refusals (empty list = OK)."""
    return check_text(path.read_text(encoding="utf-8"))


def main(argv: list[str]) -> int:
    """Exit codes are a contract, because CI asserts on them.

        0  all targets valid
        1  at least one target REFUSED   (a judgement about the content)
        2  usage error
        3  at least one target could not be read or parsed (an ERROR, not a judgement)

    v1.2 — 1 and 3 were previously indistinguishable. An uncaught FileNotFoundError
    exits 1, so a CI step asserting "non-zero means refused" would pass when its own
    fixture was missing. The same defect one level up from v1.0's: a refusal and a crash
    looked identical from outside.
    """
    targets = [Path(a) for a in argv[1:]]
    if not targets:
        print("usage: validate_workflows.py <file.yml> [...]", file=sys.stderr)
        return 2
    bad = 0
    errored = 0
    for t in targets:
        try:
            errs = check_file(t)
        except Exception as exc:
            errored += 1
            print(f"ERROR    {t}")
            print(f"    - could not read or parse: {exc}")
            continue
        if errs:
            bad += 1
            print(f"REFUSED  {t}")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"OK       {t}")
    ok = len(targets) - bad - errored
    tail = f" ({bad} refused, {errored} errored)" if errored else ""
    print(f"\n{ok}/{len(targets)} workflows valid{tail}")
    if errored:
        return 3
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
