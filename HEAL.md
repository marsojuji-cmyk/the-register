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
| — | this repository passes its own gate; no leaked secrets or home paths | E2/E1 | **clean** |

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

## 7. Positive control — the guard has been observed firing

A guard that has never fired is indistinguishable from a guard that is not there.

| step | observation |
|---|---|
| first `verify_all` run, before the heals | **8/10 — exit 1 — "PUSH REFUSED"**, listing Z3 (stale register) and Z5 (E1-1, E1-2, E1-3 open) |
| after the heals | **10/10 — exit 0 — "CLEAN — safe to publish"** |

So the gate was observed refusing a real defect **before** it was observed allowing a push, and the
refusal named the two items that were in fact unfixed. That ordering is the proof; a gate that has
only ever passed has not been tested.

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
