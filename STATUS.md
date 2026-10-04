# STATUS

**GENERATED — do not edit.** Rendered by `tools/tests/verify_all.py` from the results of the
run that checked it. Nothing writes this file by hand; if a number here looks wrong, the fix
is in the code that produces it.

A hand-written status page is true on the day it is written and silently false afterwards.
This one is compared against a fresh rendering on every run, so a change in the results
fails the check until the file is regenerated and committed.

Generated: 2026-10-04 09:21 MDT

## This run

| check | result | detail |
|---|---|---|
| Z1 gate controls (both directions) | PASS | 19/19 controls satisfied |
| Z2 adversarial probe hunt (0 findings) | PASS | 14/14 probes behave correctly; 0 finding(s) |
| Z2b review findings match post-fix expectations | PASS | 30/30 cases already match the post-fix expectation; 0 to fix |
| Z1b fixtures generate | PASS | 2 files |
| Z1b bad fixtures REFUSED with exit 1 | PASS | both refused |
| Z1b missing file ERRORS with exit 3 | PASS | exit 3 |
| Z1c this repository passes its own gate | PASS | 1/1 workflows valid |
| Z3 REGISTER.md matches a fresh compile | PASS | no substantive drift |
| Z5 every E1/E2 row explicitly closed | PASS | all 23 rows closed |
| Z6 no secrets or absolute home paths in tracked files | PASS | clean |
| Z7 repository description matches this source | PASS | in sync |

11/11 checks passed — **11 of the 12 checks this run
performs.** The missing one is the render check itself (`Z4`): it produces this table and therefore
cannot appear inside it. The console prints 12/12; the two numbers
disagreeing here is arithmetic, not drift.

## What this does NOT claim

- That any test **passes**. A `tests/` directory is presence, not correctness.
- That any workflow is **meaningful**. The gate proves a job *can* fail; it does not prove
  the job tests anything worth testing.
- That any code is **correct, secure, or used**.
- That the probe hunt covers cases nobody imagined. It is a second pass by the same lane —
  see the honest note in `tools/tests/probe_hunt.py`.
- Anything about parties outside this account. **The only claim that grants authority is an
  external party depending on, citing, or routing through an artifact.**

## Provenance

The method is identified by content hash in `REGISTER.md`, never by a hand-maintained version
string. Every defect this project has found is in `INCIDENTS.md` with the control it produced;
the disposition of every known gap is in `HEAL.md`; the structural weak spots are in
`WEAK-SPOTS.md`.
