#!/usr/bin/env python3
"""Pre-push gate for GitHub Actions workflow files.

Refuses to let a workflow be pushed that GitHub will reject or that cannot fail.

Exit codes are a contract, because CI asserts on them:

    0  all targets valid
    1  at least one target REFUSED   (the gate reached a VERDICT: this file is unacceptable)
    2  usage error
    3  at least one target could not be READ, or the check itself failed
       (the gate could not reach a verdict)

`1` means "I judged this bad". `3` means "I never got to judge". Collapsing them is the
defect that produced most of this project's incident log. An unparseable file is a VERDICT
(1), not a failure to judge: GitHub will reject it, which is exactly what this gate exists
to catch.

--------------------------------------------------------------------------------
FINDING HISTORY — every entry found by RUNNING it, or by a review that ran it
--------------------------------------------------------------------------------
v1.1  FALSE POSITIVE. Only `run:` steps counted as failable, so every all-`uses:` job was
      refused as theater (5 false refusals: three commitlint action gates, two automerge
      tasks). An action step can fail the build.

v1.2  1 and 3 were indistinguishable. An uncaught FileNotFoundError exits 1, so a CI step
      asserting "non-zero means refused" passed with its own fixture missing.

v1.3  Four fixes from tools/tests/probe_hunt.py: two false positives (a hardcoded column-0
      exempt list), two false negatives (`jobs: null` and empty `jobs:` masked by `or {}`;
      a constantly-false `if:`). Plus check 4 claimed a non-empty `run:` without enforcing it.

v1.4  Eighteen fixes from the Cursor-lane adversarial review. Every one is reproduced in
      tools/tests/review_probe.py with a post-fix expectation, and pinned by a control.
        X1    the neutralisation test was one literal suffix ("|| true"), so every other
              spelling of "always exits 0" was scored failable: `exit 0`, `||true`,
              `|| true;`, `|| exit 0`, `:`. Now a pattern over the LAST line, because the
              last command decides a script's exit status.
        X2    `_constant_false` handled False and "false" only. GitHub's falsy literals also
              include 0, -0 and "". Now the full set.
        X3    `needs` was never read. A `needs:` naming a non-existent job, and a needs
              cycle, are both rejected by GitHub.
        X4    `on:` present but null, and `on: {}`, were accepted — a workflow that can
              never fire can never fail, the same verdict already given to empty `jobs:`.
        X5    the YAML-1.1 forgiveness clause `True not in doc` matched ANY truthy key, so a
              file with no `on:` at all was accepted if it also had `true: x`. Presence is
              now read from the raw text.
        X6    `runs-on:` was tested for key presence only; null and "" were accepted.
        X7    a step with BOTH `uses:` and `run:` was accepted.
        X12   parse errors exited 1 while the docstring claimed 3 covered "read or parsed".
              The contract now says what the code does: unparseable is a verdict (1);
              3 is reserved for a file that could not be read at all. Deep nesting
              (RecursionError) is caught and treated as unparseable, so one category no
              longer splits across two codes.
        X13   FALSE POSITIVE: a job-level `uses:` (reusable workflow) was refused for
              missing `runs-on`/`steps`, which such a job does not have by design. v1.1
              fixed this at step level and never considered job level.
        X14   FALSE POSITIVE: `bool(continue-on-error)` is true for every non-empty string,
              so `continue-on-error: ${{ matrix.experimental }}` scored the step neutralised
              and refused the job.
        X15   FALSE POSITIVE: `continue-on-error: "false"` was refused; the expression
              `false` is falsy, so the step can fail.

v1.5  Three closures from GitHub's own verdicts — asked directly, in a private probe repo
      (commit cd4e15a, three files, three runs), read from the run objects rather than from a
      summary of them:
        X8  an UNKNOWN TOP-LEVEL KEY is not silently absorbed: **GitHub refuses the file**.
            Run 37210112238 came back `failure` with 0 jobs and its run NAME fell back to the
            file path — GitHub never read the `name:` key, so it died before parsing. The
            leaked `foo: bar` was therefore never a "documented limit accepted on purpose";
            it was a file GitHub rejects on every push, forever. Now refused by name.
        X9  a malformed expression refuses the file too (run 37210112994 — same signature:
            0 jobs, path-as-name). `${{ a = b }}` with a single `=` is now caught. Other
            malformed expressions still pass; this is a partial close, stated as such.
        X16 CLOSED, and it was never a false positive. Run 37210115515 RAN the file: its step
            log shows `if: 'false'` SKIPPED and `if: "'false'"` EXECUTED. Refusing the first
            and accepting the second is correct. The earlier "disputed, not changed" note in
            HEAL.md was wrong on two counts: the code at 4fd3d33 DID strip quotes
            (`value.strip().strip("'\"").lower() == "false"`), so it refused all four
            spellings; the X2 rewrite fixed it as a side effect.
      Also verified and recorded: `gh workflow list --all` reports BOTH unparseable files as
      state `active`. So **`active` does not mean `runnable`** — any tool that counts
      workflows by presence, including this project's own register, will count a file GitHub
      refuses as a gate. That is a defect in the register, not in the gate.

DELIBERATE TRADE-OFF, stated rather than implied: `continue-on-error` given as an
EXPRESSION is treated as NOT neutralising. That can hide a genuinely neutralised step (a
false negative) in exchange for never refusing a correct matrix-gated workflow (a false
positive). Both cost the same here; the direction is chosen on purpose, and it is pinned.

KNOWN LIMITS, each pinned by a control:
  * Expression syntax is checked only for the single-`=` operator. Every other malformed
    expression still passes, and GitHub refuses the whole file for those too (X9, partly open).
  * `continue-on-error` given as an expression is treated as not neutralising — the
    deliberate false negative above. Pinned so a change in either direction is noticed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

__version__ = "1.5"

# A column-0 line matching this is a top-level mapping key, not run-block content.
_TOP_LEVEL_KEY = re.compile(r"^[A-Za-z_][\w.\-]*:")

# X1 -- spellings of "this command cannot exit non-zero".
_WHOLE_NEUTRAL = re.compile(r"^(?:true|:|/bin/true|/usr/bin/true|exit\s+0)$")
_NEUTRAL_TAIL = re.compile(r"\|\|\s*(?:true|:|/bin/true|/usr/bin/true|exit\s+0)$")

# X2 -- GitHub evaluates the `if:` value as an expression; these evaluate falsy.
_FALSY_STRINGS = {"false", "0", "-0", ""}

# X8 -- the only top-level keys a workflow may carry. Anything else and GitHub refuses the
# whole file (verified, run 37210112238: 0 jobs, run name fell back to the file path).
KNOWN_TOP_LEVEL = {
    "name", "run-name", "on", "permissions", "env", "defaults", "concurrency", "jobs",
}

# X9 -- a single '=' is an assignment; GitHub's expression language wants '=='. Matched only
# outside quoted strings so `format('{0}={1}', a, b)` is not a false positive.
_ASSIGN = re.compile(r"(?<![=!<>])=(?!=)")


def _constant_false(value) -> bool:
    """True only if an `if:` expression can never evaluate true.

    Deliberately not quote-stripping: `if: 'false'` in YAML is the string `false`, which
    GitHub evaluates as the expression `false` — falsy, so the job can never run.
    `if: "'false'"` (quotes INSIDE the value) is a non-empty string literal and evaluates
    truthy; stripping quotes would wrongly refuse it.
    """
    if value is True or value is None:
        return False
    if value is False:
        return True
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, str):
        return value.strip() in _FALSY_STRINGS
    return False


def _bad_expression(value) -> str | None:
    """X9 -- return a reason if an `if:` expression is malformed, else None.

    Only the single-`=` operator is detected. That is one malformed expression out of many,
    and it is the one with a verified verdict: run 37210112994 shows GitHub refusing the
    entire file for it. Quoted strings are removed first, because `=` inside a literal is
    legal and refusing it would be a false positive.
    """
    if not isinstance(value, str):
        return None
    bare = re.sub(r"'[^']*'|\"[^\"]*\"", "", value)
    if _ASSIGN.search(bare):
        return "contains a single '=' — GitHub's expression language requires '=='"
    return None


def _run_is_neutralised(run: str) -> bool:
    """X1 -- True when the script's exit status cannot be non-zero."""
    text = run.strip()
    if not text:
        return True
    last = text.splitlines()[-1].strip().rstrip(";").strip()
    return bool(_WHOLE_NEUTRAL.match(last)) or bool(_NEUTRAL_TAIL.search(last))


def _neutralises_errors(value) -> bool:
    """X14/X15 -- True only when continue-on-error is unambiguously ON."""
    if value is True:
        return True
    if isinstance(value, str) and value.strip().lower() == "true":
        return True
    return False


def _non_empty(value) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _needs_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    """X3 -- return one cycle path if the `needs` edges contain one, else None."""
    GREY, BLACK = 1, 2
    colour: dict[str, int] = {n: 0 for n in graph}

    def visit(node: str, path: list[str]) -> list[str] | None:
        colour[node] = GREY
        for nxt in graph.get(node, ()):
            if nxt not in graph:
                continue
            if colour[nxt] == GREY:
                return path + [node, nxt]
            if colour[nxt] == 0:
                found = visit(nxt, path + [node])
                if found:
                    return found
        colour[node] = BLACK
        return None

    for n in list(graph):
        if colour[n] == 0:
            found = visit(n, [])
            if found:
                return found
    return None


def _top_level_keys(raw: str) -> list[str]:
    """X5 -- keys read from the TEXT, not inferred from a parsed boolean."""
    out = []
    for line in raw.splitlines():
        if not line or line[0].isspace():
            continue
        if _TOP_LEVEL_KEY.match(line):
            out.append(line.split(":", 1)[0].strip().strip("'\""))
    return out


def check_text(raw: str) -> list[str]:
    """Validate one workflow's YAML text. Returns refusals (empty list = OK)."""
    errs: list[str] = []

    # --- check 6: column-0 content inside a run block (the original production defect)
    in_run = False
    for lineno, line in enumerate(raw.splitlines(), 1):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        if in_run and indent == 0:
            if _TOP_LEVEL_KEY.match(stripped):
                in_run = False
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
    except RecursionError:
        # X12 -- deeply nested is unparseable too; one category, one verdict.
        errs.append("INVALID YAML: document nesting exceeds the parser limit")
        return errs

    if not isinstance(doc, dict):
        errs.append("top level is not a mapping")
        return errs

    # --- X5: `on:` presence from the raw text
    if "on" not in _top_level_keys(raw):
        errs.append("missing top-level 'on:'")
    else:
        on_val = doc["on"] if "on" in doc else doc.get(True)
        if not _non_empty(on_val):
            # X4: a trigger that can never fire means nothing in the workflow can fail.
            errs.append("'on:' has no triggers — a workflow that can never fire can never fail")

    # --- X8: unknown top-level keys. Verified against GitHub, not inferred: it refuses the
    # entire file (0 jobs, run name falls back to the path). This also closes the check-6
    # heuristic's hole — a heredoc whose first unindented line is `foo: bar` leaks out as a
    # top-level key, and that file is refused by GitHub rather than silently absorbed.
    unknown = [k for k in _top_level_keys(raw) if k not in KNOWN_TOP_LEVEL]
    if unknown:
        errs.append(
            f"unknown top-level key(s) {unknown} — GitHub refuses the ENTIRE file, "
            f"not just the key (verified: a refused run reports 0 jobs and its name falls "
            f"back to the file path)"
        )

    if "jobs" not in {k if isinstance(k, str) else str(k) for k in doc}:
        errs.append("missing top-level 'jobs:'")
        return errs
    jobs = doc.get("jobs")
    if not isinstance(jobs, dict):
        errs.append("'jobs' is not a mapping (or is null)")
        return errs
    if not jobs:
        errs.append("'jobs' is empty — a workflow with no jobs can never fail")
        return errs

    # --- X3: `needs` must name real jobs and must not cycle
    job_names = {str(k) for k in jobs}
    graph: dict[str, list[str]] = {}
    for jname, job in jobs.items():
        if not isinstance(job, dict):
            continue
        needs = job.get("needs")
        if isinstance(needs, str):
            names = [needs]
        elif isinstance(needs, list):
            names = [n for n in needs if isinstance(n, str)]
        else:
            names = []
        graph[str(jname)] = names
        unknown = [n for n in names if n not in job_names]
        if unknown:
            errs.append(
                f"job {jname}: 'needs' names job(s) that do not exist {unknown} "
                f"— GitHub rejects this"
            )
    cycle = _needs_cycle(graph)
    if cycle:
        errs.append(f"'needs' contains a cycle: {' -> '.join(cycle)} — GitHub rejects this")

    for jname, job in jobs.items():
        if not isinstance(job, dict):
            errs.append(f"job {jname}: not a mapping")
            continue

        # --- X13: a reusable-workflow call takes neither runs-on nor steps
        if "uses" in job:
            if "runs-on" in job or "steps" in job:
                errs.append(
                    f"job {jname}: a reusable-workflow call ('uses:') takes neither "
                    f"'runs-on' nor 'steps'"
                )
            continue

        bad = _bad_expression(job.get("if"))
        if bad:
            errs.append(f"job {jname}: `if:` {bad}")
        if _constant_false(job.get("if")):
            errs.append(
                f"job {jname}: THEATER — job `if:` is constantly false, so it can never "
                f"run and nothing in it can fail the build"
            )
            continue
        if "runs-on" not in job:
            errs.append(f"job {jname}: missing 'runs-on'")
        elif not _non_empty(job.get("runs-on")):
            # X6
            errs.append(f"job {jname}: 'runs-on' is present but empty")

        steps = job.get("steps")
        if not isinstance(steps, list) or not steps:
            errs.append(f"job {jname}: missing/empty 'steps'")
            continue
        failable = 0
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                errs.append(f"job {jname} step {i}: not a mapping")
                continue
            has_uses, has_run = "uses" in step, "run" in step
            if not has_uses and not has_run:
                errs.append(f"job {jname} step {i}: neither 'uses' nor 'run'")
            if has_uses and has_run:
                # X7
                errs.append(f"job {jname} step {i}: has both 'uses' and 'run'")
            run = step.get("run")
            if has_run and not (isinstance(run, str) and run.strip()):
                errs.append(f"job {jname} step {i}: 'run' is present but empty")
            bad = _bad_expression(step.get("if"))
            if bad:
                errs.append(f"job {jname} step {i}: `if:` {bad}")
            neutralised = (
                _neutralises_errors(step.get("continue-on-error"))  # X14, X15
                or _constant_false(step.get("if"))                  # X2
            )
            if isinstance(run, str) and run.strip():
                if not _run_is_neutralised(run) and not neutralised:  # X1
                    failable += 1
            elif has_uses and not neutralised:
                failable += 1
        # THEATER is a property of the JOB, not of one step: it is theater when nothing in
        # the job can fail the build. An advisory step beside a real gate is legitimate.
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
    errored = 0
    for t in targets:
        try:
            errs = check_file(t)
        except Exception as exc:
            errored += 1
            print(f"ERROR    {t}")
            print(f"    - could not read: {exc}")
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
