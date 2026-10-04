# HEAL — strategy, register, and the definition of "zero errors"

**Opened:** 2026-10-04 · **Rule under enforcement:** *nothing reaches GitHub unless it is in its best
possible condition, with 0 errors.*

---

## 0. The premise had to be challenged first

**"0 errors" was undefined, and as stated it can never be satisfied** — there is always an open
control, always an unfixed gap, always a hygiene item. A rule that cannot be met is bypassed on day
three and then cited as if it were still in force. That is how every "we'll be careful" policy dies,
and it is the same failure this repository was built to document.

So the rule is kept, and made satisfiable, by defining it precisely:

> **Zero errors means: nothing false on the public surface, nothing known-wrong in the method, and
> nothing open that is not written down with an owner.**
>
> *Unknown* errors block. *Dispositioned* gaps are published. "We don't know" blocks;
> "we know, it's listed, here's the owner" does not.

That distinction is the whole strategy. It is checkable, and it can actually reach zero — **and it
did, on the day it was written.** See §7.

---

## 1. The contract — a push is allowed iff `verify_all.py` exits 0

| id | condition | severity on failure | live result |
|---|---|---|---|
| **Z1** | every control passes, both directions, including the cases where the gate was previously wrong | E2 | **18/18 pass** |
| **Z2** | the adversarial probe hunt reports **0** findings | E2 | **14/14, 0 findings** |
| **Z3** | every generated artifact matches a fresh **live** compile | E1 | **no substantive drift** |
| **Z4** | no number in prose that no code enforces — counts generated, or asserted | E1 | **STATUS.md is generated** |
| **Z5** | no blocking (E1/E2) item left open in this file | E1 | **all closed** |
| **Z6** | this repository passes its own gate; no secrets or absolute home paths in tracked files | E2/E1 | **clean** |
| **Z7** | the published repository description matches its canonical source | E1 | **asserted** |

**Z4 is the deepest fix and the generalisation of everything found today.** The recurring defect is
prose asserting something no code checks: a cache read reported as "checked this run"; a control count
written once and never updated; a licence claim absent from the repo it describes. If a sentence
contains a number, either the number is produced by the same run that prints it, or a test asserts it.

---

## 2. The mechanism — physical, not a promise

| link | what it does | armed state |
|---|---|---|
| `tools/tests/verify_all.py` | one command; exit 0 only when Z1–Z6 hold | **live — 10/10 checks** |
| `.githooks/pre-push` | refuses the push when verify_all is non-zero | **installed, executable, positive control recorded (§7)** |
| `.github/workflows/controls.yml` | runs the same checks in CI, so a bypassed hook is caught in ~60s | live |
| `STATUS.md` | generated, so its counts cannot drift | live |
| `HEAL.md` | this file; machine-read by Z5 | live |

---

## 3. Severity taxonomy

| sev | name | meaning | blocks a push? |
|---|---|---|---|
| **E1** | PUBLISHED-FALSE | the public surface asserts something untrue, or a number no code enforces | **yes** |
| **E2** | METHOD-WRONG | a check gives a wrong answer on a real case (false positive **or** negative) | **yes** |
| **E3** | MECHANISM-MISSING | a guard that should exist and does not | no — listed, dated, owned |
| **E4** | HYGIENE | drift, dead code, naming, metadata | no — listed |

A false positive is rated **equal** to a false negative. A gate that refuses correct work teaches its
users to ignore it, and an ignored gate protects nothing.

---

## 4. E1 — published-false *(blocking)*

| id | the error | heal | status |
|---|---|---|---|
| **E1-1** | published `INCIDENTS.md` stated a control count that no code enforced, and was wrong within the day | all counts removed from prose; `INCIDENTS.md` now points at the generated `STATUS.md` and at the commands | **closed** |
| **E1-2** | published `REGISTER.md` marked the README column ❌ for repos where the column is not applicable | tri-state `cmd_cell` wired into the table, the totals and the HTML view; profile/docs repos read `—` | **closed** |
| **E1-3** | the published method was v1.2 with six known defects while the README presented it as sound | v1.3 applied; 18/18 controls, 14/14 probes, account re-audit 20/20 clean; published atomically with the fix | **closed** |

---

## 5. E2 — method-wrong *(blocking)*

All six found by `tools/tests/probe_hunt.py`, now permanent controls C11–C18.

| id | the error | control | heal | status |
|---|---|---|---|---|
| **E2-1** | false positive: `permissions:` at column 0 after a run block accused of being run content | C11 | column-0 lines shaped like mapping keys end the block | **closed** |
| **E2-2** | false positive: same for `env:` | C12 | same | **closed** |
| **E2-3** | false negative: a job with `if: false` can never run — accepted silently | C14 | `_constant_false()` on the job `if:` | **closed** |
| **E2-4** | false negative: every step disabled by `if: false` still counted as failable | C15 | constantly-false steps excluded | **closed** |
| **E2-5** | false negative: an empty `jobs:` mapping is a workflow that can never fail | C16 | empty jobs refused | **closed** |
| **E2-6** | false negative: `jobs: null` masked by `or {}` | C17 | null jobs refused | **closed** |

---

## 5b. E2 — method-wrong, from the Cursor-lane adversarial review *(blocking)*

22 of 26 probes found a defect. All are reproduced in `tools/tests/review_probe.py` with a
post-fix expectation, and that file is enforced by check **Z2b** — so a regression fails the push.

| id | finding | heal | status |
|---|---|---|---|
| **E2-7** | X1: neutralisation tested one literal suffix (`\|\| true`), so `exit 0`, `\|\|true`, `\|\| true;`, `\|\| exit 0`, `:` were all scored failable | pattern over the **last line** (the last command decides exit status) | **closed** |
| **E2-8** | X2: falsy `if:` handled `False` and `"false"` only; GitHub's falsy literals also include `0`, `-0`, `""` | full falsy set | **closed** |
| **E2-9** | X3: `needs` never read — unknown job names and needs cycles both accepted; GitHub rejects both | existence check + cycle detection | **closed** |
| **E2-10** | X4: `on:` null and `on: {}` accepted — a workflow that can never fire can never fail | non-empty trigger required | **closed** |
| **E2-11** | X5: the YAML-1.1 forgiveness clause matched **any** truthy key, so a file with no `on:` was accepted if it also had `true: x` | `on:` presence read from the raw text | **closed** |
| **E2-12** | X6: `runs-on:` tested for key presence only; null and `""` accepted | emptiness check | **closed** |
| **E2-13** | X7: a step with **both** `uses:` and `run:` accepted | refused | **closed** |
| **E2-14** | X12: parse errors exited 1 while the documented contract said 3 covered "read or parsed" | contract now states what the code does; deep nesting caught so one category yields one code | **closed** |
| **E2-15** | X13: **false positive** — job-level `uses:` (reusable workflow) refused for missing `runs-on`/`steps`, which it does not have by design | reusable-workflow calls exempted; v1.1's fix covered step level only | **closed** |
| **E2-16** | X14: **false positive** — `bool(continue-on-error)` is true for any non-empty string, so a matrix expression scored the step neutralised and refused the job | only an unambiguous `true` neutralises | **closed** |
| **E2-17** | X15: **false positive** — `continue-on-error: "false"` refused although the expression is falsy and the step can fail | same fix as E2-16 | **closed** |
| **E2-18** | X11: Z5 detected an open heal item by matching the literal `**open**` in a row starting `\| **E1-`; dropping the bold or the space hid an open blocking item | **inverted to fail closed** — a blocking row that does not say `closed` counts as open, and an unparseable table is a failure, not an empty pass | **closed** |
| **E2-19** | X19: Z6 split `git ls-files` on whitespace, so a tracked path containing a SPACE split into two unreadable paths that the bare `except` skipped — a spaced file was never leak-scanned | `-z`, NUL-separated; unreadable paths are now a failure, not a skip | **closed** |
| **E2-20** | X10: **`STATUS.md` was not generated by anything.** It was hand-written, claimed to be generated in four documents, and this file recorded an E1 as closed on the strength of that false statement. Its "control", Z4, was `"GENERATED" in body.upper()` — one line any file containing that word passes | Z4 now **renders** the status from the run and compares it; the file is generated for real | **closed** |

### Recorded, not fixed

| id | finding | disposition |
|---|---|---|
| **E3-8** | X8 (INFERRED): unknown top-level keys may be rejected outright by GitHub, which would mean the leaked `foo: bar` in C19 is not silent absorption but an outright refusal — upgrading C19's stated consequence | **open** — settle empirically by pushing a throwaway workflow and reading GitHub's parse error. The reviewer offered to run it. |
| **E3-9** | X9 (INFERRED): expression syntax inside `if:` is never validated (`if: ${{ a = b }}` accepted) | **open** — limited value, high false-positive risk |
| **E3-10** | X17 (LOW): C19 was a `want=accept` control, so fixing the known limit made the suite print "GATE IS NOT TRUSTWORTHY" — it called a corrected gate untrustworthy and a broken one fine | **closed** — the known-limit control is now a **PIN**: it reports `PIN ok` / `PIN chg` and never fails, so green keeps meaning "the gate behaves as intended" |
| **E3-11** | X16 (LOW): the reviewer calls `if: 'false'` a false positive. **Disputed and not changed.** YAML single-quoting is YAML syntax, so the value is the string `false`, which GitHub evaluates as the expression `false` — falsy, so the job can never run. `if: "'false'"` (quotes inside the value) is the truthy case, and this gate does not refuse it | **open** — same empirical push would settle it |

The review's "did not file" list is respected: WS-3 (fuzzer), WS-6, WS-9 and the
"does not prove the job tests anything worth testing" limit were already disclosed in
`WEAK-SPOTS.md` and are not re-counted as new findings.

---

## 6. E3 — mechanism-missing, and E4 — hygiene

| id | the gap | heal | status |
|---|---|---|---|
| E3-1 | no pre-push hook; nothing physically blocked a bad push | `.githooks/pre-push` + `core.hooksPath`; positive control recorded | **closed** |
| E3-2 | no control for the freshness claim (I8) | **Z3 forces a live compile and compares against the committed register** — a repo added between runs fails the check until regenerated. End-to-end rather than a unit test | **closed** |
| E3-3 | no consolidated verification command | `tools/tests/verify_all.py` | **closed** |
| E3-4 | **`ep-aec-conformance` had no licence** — the flagship, externally cited, "all rights reserved" | MIT added; read-back confirms `MIT` | **closed** |
| E3-5 | three code repos did not document their check command | real command appended to each README, taken from that repo's own CI; read-back confirms all three | **closed** |
| E3-6 | no signed commits or build-provenance attestations | planned; not started | **open** |
| E3-7 | **the register does not check licences** — the gap that hid E3-4 | proposed column; not built | **open** |
| E4-1 | `cmd_cell` / `has_checks` computed but unused | wired into table, totals and HTML | **closed** |
| E4-2 | `tools/_fetch_workflows.py` superseded by `compile_register.py` | retained as first-fetch provenance; not deleted | **open** |
| E4-3 | check 4 claimed a non-empty `run:` and did not enforce it | enforced in v1.3 | **closed** |
| E4-4 | `agentready` had no `SECURITY.md` | added; read-back confirms | **closed** |
| E4-5 | `self-verifying-artifacts` skill carries lint warnings | not started | **open** |
| E4-6 | **this session's own probe printed `exit=0` after a pipe — it measured `tail`, not the script** | recounted; recorded here as a live example of the class | **closed** |

The four `open` rows are all E3/E4 — they do not block, and Z5 confirms no **E1/E2** row says `open`.

---

## 7. Positive control — the guard has been observed firing, three times, independently

A guard that has never fired is indistinguishable from a guard that is not there.

| # | run | observation |
|---|---|---|
| 1 | first `verify_all`, before the heals | **8/10 — exit 1 — "PUSH REFUSED"**, naming Z3 (stale register) and Z5 (E1-1, E1-2, E1-3 open) — both of which were in fact unfixed |
| 2 | the heal commit `eaccbf9`, run as a background job | tamper → **"PUSH REFUSED", push exit 1**; restore → **10/10 CLEAN**, push allowed, `8d0b804..eaccbf9` |
| 3 | re-run in-session after v1.3 | tamper → **9/10 → PUSH REFUSED**, push exit 1; restore → local == remote == `eaccbf9`, `0 0` ahead/behind, tree clean |

All three refused a **real** defect before allowing a push, and each refusal named something that was
genuinely wrong. A gate that has only ever passed has not been tested.

**On the counts printed in those logs.** Runs 1 and 2 show `18 controls` and `10 checks` because they
ran before control C19 and check Z7 existed. They are correct **for their timestamp**, not stale — and
a reader who finds a lower number in an old log has found history, not drift. Current counts are
produced by `STATUS.md` and the runner, and are deliberately not stated here.

That note exists because a number in a log looks exactly like a number in prose, and the rule in §1
(Z4) applies to log transcripts as much as to READMEs.

---

## 8. Anti-patterns this doctrine exists to kill

Each one was observed **today**, in this repository, by accident:

1. **A check that cannot fail.** A jobs-less workflow; a constantly-disabled job; a job of neutralised steps.
2. **A claim of verification no code enforces.** "Checked this run" while reading a cache. A control count in prose.
3. **A gate whose errors are indistinguishable from its judgements.** A missing fixture exiting `1`, the same code as a refusal — so a negative control passed while verifying nothing.
4. **A probe that cannot detect its own failure.** The exit code after a pipe.
5. **The evidence of a failure that cannot be stored.** A deliberately-broken fixture refused by a validating write path.
6. **A method with no home.** A gate one prune cycle from deletion.

The common root, six times out of six: **an operation that failed and an operation that concluded look
identical from outside, unless something is built to make them distinguishable.**

---

## 9. Falsifier for this strategy

If `verify_all.py` stops refusing real defects — i.e. a defect reaches GitHub with the hook installed
and CI green — the doctrine is decoration. The check at that point is not a new rule; it is to delete
the claim and say what actually holds.
