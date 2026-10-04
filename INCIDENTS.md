# INCIDENTS

The defect ledger. Every entry is a real failure, the class it belongs to, the method it produced,
and the control that proves the fix. **This file is the raw material the method corpus is made from.**

A method without an incident behind it is a preference. A method with one is a scar.

---

## I1 · The payload was verified; the artifact was not

**What happened.** A workflow embedding a bash heredoc as an unindented YAML plain scalar was pushed
to four public repos. The heredoc body sat at column 0, outside the mapping, so the file was invalid
YAML. GitHub created a run per repo that reported `failure` with **`total_count: 0` jobs** — a failed
pipeline containing no test failure at all.

The local test had extracted the script from the workflow and executed it. It passed. The **workflow
file** was never parsed.

**Class.** Verifying a component in place of the container. The artifact that ships is the file, not
the payload inside it.

**Method produced.** `validate_workflows.py` check 6 — column-0 content inside a `run:` block, run
*before* the YAML parse so the parse failure is reported as what it is.
**Control:** `C1`, `C9`.

**Note the second-order effect:** a broken pipeline and a failing test are indistinguishable from the
badge. Both are red. That ambiguity is what made the defect survive a passing local test.

---

## I2 · The gate refused every correct file it was shown

**What happened.** The first version of the gate reported `missing top-level 'on:'` on known-good,
GitHub-green workflows. PyYAML parses an unquoted `on:` key as the **boolean `True`** — the YAML 1.1
"Norway problem". The gate was looking for the string `"on"` and the document had `True`.

**Class.** False positive from a well-known serialization quirk. Caught by a control, not by review.

**Method produced.** Key normalisation before the membership test — accept either spelling.
**Control:** `C8`.

---

## I3 · The gate accused working automation, and the accusation was wrong

**What happened.** The gate's first theater rule flagged `star-lab` as theater. **The file was read
before anything was changed** — and step 1 runs real unit and CLI tests, which can fail; step 2 is
named "Doctor (best effort)" and is an advisory smoke check beside a real gate. Legitimate, and
honestly labelled.

The automation was not changed. **The gate was.**

**Class.** A rule that treats a *step* property as a *job* property. Theater is a property of the
whole job: a job is theater when *nothing* in it can fail the build. An advisory step next to a real
gate is not theater — it is a real gate with a smoke check.

**Method produced.** The `failable` counter, evaluated per job, with `continue-on-error` and
fully-neutralised `run` commands excluded and a local `chmod … || true` inside an otherwise real
command *not* counted as theater.
**Control:** `C3`.

**The discipline this one establishes, and it is the most important line in this file:** a gate's
verdict is a *hypothesis about a file*, not a fact about it. Read the file before acting on the gate.

---

## I4 · Five false refusals in one run — the gate could not see actions

**What happened.** Running v1.0 over all 19 workflows on the account produced 5 refusals. All five
were false positives:

| File | Why it was refused | Why it is not theater |
|---|---|---|
| `aegis/commitlint.yml` | single `uses:` step, no `run:` | `amannn/action-semantic-pull-request` fails the build on a bad PR title — a real gate |
| `star-lab/commitlint.yml` | same | same |
| `sovereign-contracts/commitlint.yml` | same | same |
| `interlock/automerge.yml` | single `uses:` step | `peter-evans/enable-pull-request-automerge` is a task, not a check — it makes no claim to gate anything |
| `sovereign-contracts/automerge.yml` | same | same |

**Root cause:** `failable` counted only `run:` steps. Any job built purely from `uses:` steps
therefore scored zero and was refused.

**Class.** Structural blindness to a whole category of evidence. Predicted by reading line 90 before
running the audit, and confirmed by reading all five files before accepting the verdict.

**Method produced.** A `uses:` step counts as failable unless it is `continue-on-error`. v1.1.
**Control:** `C6` (accept) paired with `C7` (refuse when the same shape is neutralised).
**Re-audit result:** 19/19 valid under v1.1; the negative control still refuses synthetic theater.

**Principle this establishes:** *a false positive in a gate is as damaging as a false negative.* A
gate that refuses correct work teaches its users to ignore it, and an ignored gate protects nothing.

---

## I5 · The method lived in a directory that gets emptied

**What happened.** The gate was written to a scratch directory belonging to a different profile, with
a live prune marker in the sibling path. It was unversioned, uncommitted, and unreferenced — one idle
cycle from not existing, with no copy anywhere.

**Class.** An artifact with no declared home. Not a code defect — a storage defect, and the one most
likely to erase everything else in this ledger.

**Method produced.** `tools/` in this repository, with the previous version kept beside the current
one under an explicit filename, and the original's hash recorded in `PLAN.md`.
The rule: **if a method is not in the registry, it does not exist.**

---

## I6 · Every hand-probe was wrong, and all in the same direction

**What happened.** Three coverage reads were taken by hand during the compilation of this repository.
All three were wrong:

| Probe | Hand-read | Actual | Direction |
|---|---|---|---|
| does `agentready` have a workflow? | no | yes | under-detected |
| how many public repos have ≥1 workflow? | 13 | 14 | under-detected |
| how many READMEs omit their check command? | 4 | 6 | under-detected |

The mechanism in the first two: a `--jq 'length'` against a path that 404'd printed the API's error
body into the output column, which read as data. The third was a narrower pattern than the compiler's.

**Class.** Manual probes with unvalidated failure modes. A probe that cannot distinguish *"absent"*
from *"my request failed"* will report absence for both.

**Method produced.** `compile_register.py` — the enumeration is done in code with the failure path
handled explicitly, and the README column is labelled a **heuristic** rather than a proof. When two
implementations of that column disagreed, the disagreement was printed rather than resolved.

**The honest consequence:** this ledger contains **no confirmed instance of theater** in any of the
14 workflow-bearing repos. The 5 refusals were the gate's errors, not the account's. A blank result
from a corrected instrument is worth more than five findings from a broken one.

---

## I7 · The repository could not commit the evidence of the failure it exists to catch

**What happened.** Adding the negative-control fixtures turned up two defects in a row, both found
by trying to *commit a known-bad file*:

1. `tools/tests/fixtures/broken-heredoc.yml` was **refused by the write path** that validates YAML —
   because it is invalid YAML on purpose. The guard is correct and the artifact is correct, and the
   two cannot both win. *A guard that prevents you from storing the evidence of the failure it
   guards against.*
2. Worse, and only visible after the first defect: the CI step checking that fixture used
   `if validate_workflows.py <fixture>; then ... else echo "refused as expected"; fi`. A **missing**
   fixture raises an uncaught `FileNotFoundError`, which exits **1** — the same code as a refusal.
   So the step would have printed *"refused as expected"* and passed, with no fixture present at all.
   A green check that verifies nothing. **The exact category this repository exists to detect.**

**Class.** Two instances of one class: *an operation that failed and an operation that concluded are
indistinguishable from outside.* It is I1 again — a broken pipeline and a failing test are both red —
one level up, inside the instrument.

**Method produced.**
- Fixtures are **generated from code** (`tools/tests/make_fixtures.py`), where the intent is explicit
  and the content is a literal. The guard is not weakened; the artifact gets a different provenance.
- Exit codes are now a documented contract: **0** valid · **1** refused (a judgement) · **2** usage ·
  **3** could not read or parse (an error, not a judgement). Errors exit 3, never 1.
- CI asserts the **exact** exit code (`-ne 1` fails the build) instead of merely non-zero, and
  asserts the fixture exists before running the gate against it.

**Control:** `C10` — invoke the CLI with a path that does not exist and require exit 3.

**The generalisable rule, and it is worth more than the fix:** *a negative control must be able to
distinguish "it said no" from "it never ran".* A control that only checks for failure cannot tell
a working gate from a gate that is absent.

---

## I8 · The compiler claimed "checked this run" while reading a cache

**What happened.** Publishing this repository added a twentieth public repo — which the register then
had to describe, including its own. It reported **14 of 20** repositories as having at least one
workflow. The true number was **15 of 20**: the new repository's own CI was not in the workflow cache,
and the compiler only refreshed that cache when the index file was *missing*.

So the header line — *"Every line below was produced by a named check during this run"* — was **false
for the workflow column**. Not wrong by accident: wrong by a default.

**Class.** A claim about freshness that the code did not enforce. Identical in shape to I1 and I7:
the distinction between *"checked now"* and *"recalled from an earlier check"* was invisible from
outside, and the artifact asserted the stronger of the two.

**Method produced.** Refreshing is now the **default**; `--offline` is the explicit escape hatch, and
it prints a warning and is meant to be labelled in the output. Retained `--refresh` for compatibility.

**Control:** this one has no unit control yet, and that is stated rather than glossed. Closing it
properly means asserting that a repository created between two runs appears in the second. Recorded
here as an **open control** rather than counted as done.

**The rule, and it is the third time this ledger has landed on it:**
*a claim of freshness is a claim, and it needs the same evidence as any other.* "Checked this run"
must be enforced by the code that makes the claim, or it is a sentence someone wrote once.

---

## What the ledger is for

**Every incident here produced a method and a control.** The pattern in **six of the eight** is the
same: **the instrument was wrong, not the thing it measured.** Four of those six were caught by a
control rather than by review, which is the argument for controls in one sentence.

The rule this file exists to enforce:

> **A method ships with its controls as a runnable file, or it does not ship.**

**No counts appear in this file on purpose.** A number typed into prose is a claim no code enforces —
and this file previously stated how many controls existed, which was wrong within the day (recorded as
E1-1 in `HEAL.md`). The live counts are produced by `tools/tests/verify_all.py`, and published in
`STATUS.md`, which is generated rather than written.

Run them yourself:

```bash
python3 tools/tests/test_validator.py   # every control, both directions
python3 tools/tests/probe_hunt.py       # the adversarial hunt for cases we did NOT think of
python3 tools/tests/verify_all.py       # all of it; exit 0 only when clean
```
