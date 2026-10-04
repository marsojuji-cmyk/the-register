#!/usr/bin/env python3
"""Pre-push gate for GitHub Actions workflow files.

Refuses to let a workflow be pushed that GitHub will reject or that cannot fail.

Built after a real incident: a workflow embedding a bash heredoc as an unindented
YAML plain scalar was pushed to four public repos. GitHub could not parse it, so
each run reported `failure` with ZERO jobs — which looks like a failing test and
is actually a broken file.

Checks:
  1. valid YAML (strict)
  2. top-level `on:` and `jobs:` present
  3. each job has `runs-on` and `steps`
  4. every step is `uses:` or `run:` with non-empty value
  5. THEATER: rejects a job in which no step can fail the build
  6. no line at column 0 inside a run block (the exact defect above)

Exit 0 = safe to push. Exit 1 = refused, with reasons.

--------------------------------------------------------------------------------
v1.1 — 2026-10-04 — FALSE POSITIVE FIX  (incident 2026-10-04)
--------------------------------------------------------------------------------
v1.0 counted only `run:` steps as failable. Any job built purely from `uses:`
steps therefore had failable == 0 and was refused as THEATER. Running v1.0 over
all 19 workflows on this account produced 5 refusals; reading the files showed
all 5 were false positives:

    aegis/commitlint.yml                uses: amannn/action-semantic-pull-request@v5
    star-lab/commitlint.yml             (same)
    sovereign-contracts/commitlint.yml  (same)
    interlock/automerge.yml             uses: peter-evans/enable-pull-request-automerge@v3
    sovereign-contracts/automerge.yml   (same)

The three commitlint jobs are genuine gates — a non-conforming PR title fails the
build. The two automerge jobs are tasks, not checks, and do not pretend otherwise.
An action step can fail the build. The gate was wrong, not the workflows.

Fix: a `uses:` step counts as failable unless it is `continue-on-error`.
Control: tests/test_validator.py :: C6 all_uses_job_is_not_theater.

Principle this incident establishes: a false positive in a gate is as damaging as
a false negative. A gate that refuses correct work teaches its users to ignore it,
and an ignored gate protects nothing.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

THEATER_RUN_CONSTRUCTS = ("|| true", "continue-on-error", "if: always()")


def check_text(raw: str) -> list[str]:
    """Validate one workflow's YAML text. Returns refusals (empty list = OK)."""
    errs: list[str] = []

    # check 6 first: it is a parse failure disguised as a content failure
    in_run = False
    for lineno, line in enumerate(raw.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if in_run:
            if indent == 0 and not line.lstrip().startswith(("-", "jobs:", "on:", "name:")):
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
    jobs = doc.get("jobs") or {}
    if not isinstance(jobs, dict):
        errs.append("'jobs' is not a mapping")
        return errs

    for jname, job in jobs.items():
        if not isinstance(job, dict):
            errs.append(f"job {jname}: not a mapping")
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
            neutralised = bool(step.get("continue-on-error"))
            run = step.get("run")
            if isinstance(run, str) and run.strip():
                # a step is UNFAILABLE only if the whole command is neutralised, or the
                # step is marked continue-on-error. A local `chmod ... || true` inside an
                # otherwise real command is not theater.
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
    targets = [Path(a) for a in argv[1:]]
    if not targets:
        print("usage: validate_workflows.py <file.yml> [...]", file=sys.stderr)
        return 2
    bad = 0
    for t in targets:
        errs = check_file(t)
        if errs:
            bad += 1
            print(f"REFUSED  {t}")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"OK       {t}")
    print(f"\n{len(targets) - bad}/{len(targets)} workflows valid")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
