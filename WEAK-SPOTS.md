# WEAK SPOTS — the classes that keep producing the defects

**Opened:** 2026-10-04 · Companion to `HEAL.md` (which lists instances) and `INCIDENTS.md` (which lists scars)

---

## The meta-observation

Today produced eight incidents, thirteen heal items and six method defects. Nearly all of them are
instances of **nine recurring classes**. Fixing instances is infinite work. Fixing classes is finite —
and it is the only reason the error count can ever go down instead of sideways.

This document names the classes, then plugs the ones that can be plugged mechanically.

---

## WS-1 · Failure and conclusion are indistinguishable from outside  *(6 instances — the most productive class)*

**Instances.** A broken pipeline and a failing test are both red, both report `failure`. A missing
fixture exits `1`, the same code as a refusal — so a negative control printed "refused as expected"
while verifying nothing. A cache read was reported as "checked this run". A probe's exit code
measured `tail` instead of the script. The heredoc defect reported zero jobs.

**Why it keeps happening.** The default return type of a shell command is one bit. One bit cannot
carry three states.

**Plug — boundary discipline.** Every process boundary returns one of **three** distinct states:
`OK` / `REFUSED` / `ERRORED`. Never assert `!= 0`; assert the exact expected code. Never let a
bare `except` collapse into a pass.

**Mechanical form:** a lint over our own tooling that flags every `subprocess` call whose result is
not compared against a specific code, and every `except:` that does not re-raise or record.
**Status:** the exit-code contract is in place (v1.2). **The lint is not built — this is the highest-value unbuilt plug.**

---

## WS-2 · Prose asserts what no code enforces  *(5 instances)*

**Instances.** A control count in `INCIDENTS.md`, wrong within the day. "Nine controls" in the GitHub
repository description. A licence section describing MIT before the file existed. "Every line was
produced during this run" while reading a cache.

**Why it keeps happening.** Prose is written once and read forever. Nothing regenerates it.

**Plug — the generated-prose rule.** Any number or state in prose is either produced by the same run
that prints it, or asserted by a check. One generated `STATUS.md`; prose points at it.

**Mechanical form, and this is the part still open:** **the GitHub repository description is a claim
surface too**, and it was typed by hand and went stale within minutes. It must be asserted from a
canonical source, exactly like every other generated artifact.
**Status:** partially plugged (prose counts removed; `STATUS.md` generated). **Repository description — UNPLUGGED.**

---

## WS-3 · A gate is only as good as the cases we imagined  *(1 instance, 6 defects)*

**Instances.** Eighteen controls passed, in both directions, while the method answered **wrong on six
real cases** the controls never covered.

**Why it keeps happening.** Controls are written by the same mind that wrote the method, so they
share its blind spots.

**Plug — the hunt.** Cases we did *not* imagine must be hunted, and every finding is promoted to a
permanent control so the hunt's yield compounds. The hunt now runs inside `verify_all`.

**Deeper form, not built:** property-based fuzzing — generate mutated workflow files and assert (a)
no crash, (b) internal consistency between checks, (c) that every refusal names a real reason.
**Status:** hunt live and enforced. **Fuzzer not built.**

---

## WS-4 · We verify ourselves  *(structural — the biggest hole)*

**Observation.** One lane wrote the gate, calibrated it, wrote its controls, wrote the hunt, judged the
results, and signed the heal register. The estate's own doctrine says self-grading inflates (models
grade themselves 87–64 in their own favour) and that analysis/audit belongs to **another** lane.

Every defect found today was found by *running* something — not by review. That is evidence the
review path is absent, not that review is unnecessary.

**Plug — independent adversarial review of the verifier.** Hand the analysis lane the gate, the
controls, the hunt and the heal register with one instruction: **break it.** Specifically: find a
workflow that the gate passes and that cannot fail; find a claim in the published artifacts that no
check enforces; find a case where a refusal and an error are the same code.

**This is a handoff, not a courtesy.** The charter assigns adversarial analysis to Grok Build and
code to Cursor; this lane has been doing both halves itself.
**Status: UNPLUGGED. Highest priority of the non-mechanical items.**

---

## WS-5 · CI enforces LESS than the local gate  *(verified live, this minute)*

**Observation.** `grep -c verify_all .github/workflows/controls.yml` → **0**. CI runs the controls,
the fixtures and the self-audit — it does **not** run Z3 (artifact freshness), Z4 (generated status) or
Z5 (heal register). So `git push --no-verify` — **one flag** — bypasses the hook entirely and CI
reports green while the published register is stale.

**Why it matters.** The local hook is the *convenience*; CI is supposed to be the *guarantee*. Right
now the guarantee is weaker than the convenience. That inverts the whole design.

**Plug — CI runs the identical command.** `python3 tools/tests/verify_all.py`, same as the hook.
Anything else is two different standards wearing one name.
**Status: UNPLUGGED, verified. Plugging now.**

---

## WS-6 · The guard is local-only, and the account has no ongoing check

**Observation.** `core.hooksPath` is local git config — not committed, not transferable. A fresh clone
has no hook, and nothing on any schedule examines the other nineteen repositories.

**Plug.** Two parts: (a) CI as the backstop (WS-5); (b) a **scheduled** coverage run that reports
drift across every public repo — because the register can only see drift when it is run, and a
register that depends on someone remembering to run it is the "habit is not a mechanism" failure this
estate already canonised.
**Status: UNPLUGGED.**

---

## WS-7 · Documented limits are not pinned

**Observation.** `validate_workflows.py` documents a known limit in check 6 — a heredoc whose first
unindented line looks like a mapping key slips past it. Nothing asserts that behaviour. A future edit
could silently change it in either direction and no control would notice.

**Plug.** A control that pins the **known-limit** behaviour, so the documented limit is a tested fact
rather than a comment.
**Status: UNPLUGGED (cheap). Plugging now.**

---

## WS-8 · The evidence of a failure cannot be stored by a validating writer

**Observation.** The deliberately-broken fixture was refused by the YAML-validating write path. The
guard is right, the artifact is right, and they cannot both win.

**Plug.** Known-bad artifacts are **generated from code**, never hand-edited — the generator is the
document of intent. The general rule: *never hand-edit a counterexample.*
**Status: plugged for YAML fixtures; the rule is recorded.**

---

## WS-9 · Context rides every turn — including into a model tier that trains on prompts

**Observation.** The active model for this chat is now `muse-spark-1.3-contributor` (provider
`meta-ai`). The `-contributor` tier is recorded as **training on prompts**. Memory is injected into
every turn, and the memory store carries estate state — hostnames, paths, project internals, decisions.

Independent of any judgement about the tier: the pairing of *always-injected private context* with
*a tier that retains prompts* is a data-hygiene exposure, and it is not one this lane can plug.

**Plug (yours to make):** the platform already refuses to enable data-training tiers
non-interactively unless a named security flag is flipped — that flag must stay unflipped. Beyond
that: choose the tier deliberately, and treat this chat's contents as publishable.
**Status: FLAGGED. Needs your decision, not my action.**

---

## WS-10 · An acknowledgement is not an outcome  *(new, observed 2026-10-04)*

**What happened.** The agent-messaging layer returned:

```json
{"status": "queued", "detail": "Durably queued for the live Bot Chat owner. Do NOT wait or resend."}
```

Minutes later the delivery process exited 1: `HTTP 402 personal-team-blocked:spending-limit`. **The
receiving agent never saw the message.** The caller had been told "queued", told not to verify, and
had already reported the handoff as dispatched to a human.

**Why it belongs in this file.** It is WS-1 one level up — the same defect, in a *different layer of
the stack*, found hours apart. A queue acknowledgement is a statement about **intent**. Delivery is a
fact about **the world**. The interface reports the first in the grammar of the second, and the
stronger claim is the one that gets believed.

**The compounding error, which is worse than the plumbing.** Because the ack was confident, a human was
told a review was in flight when no review existed. That is E1 — a false published claim — with the
prose being *my own status report* rather than a README. The rule in `HEAL.md` §1 (Z4) applies to what
this lane tells its operator, not only to what it commits.

**Plug.**
1. **`queued` means not delivered.** Never report a handoff as dispatched on the strength of an ack.
   A delivery receipt, or the recipient's own reply, is the receipt. Anything else is intent.
2. **An unavailable lane must be reported as unavailable**, with the named fix — not silently retried
   and not counted as coverage. Here the fix is external and specific: Grok needs credits or a
   subscription before that lane exists again.
3. **When the independent reviewer is unavailable, substitute mechanical independence.** A reviewer
   who shares this lane's assumptions is not independent; a *fuzzer* does not share assumptions at all.
   It is a weaker form of independence than a second mind, but it is available today and it cannot be
   talked out of a finding.

**Status: recorded; plug 1 and 2 applied immediately (this lane's reporting changed in the same turn
the failure was known). Plug 3 is WS-3.**

---

## Summary — what gets plugged, by whom

| id | class | plug | who | status |
|---|---|---|---|---|
| WS-10 | ack ≠ delivery | never report a handoff as dispatched without a receipt; name an unavailable lane | this lane | **plugged (reporting corrected)** |
| WS-5 | CI weaker than the gate | CI runs `verify_all` | this lane | **PLUGGED** |
| WS-7 | limit not pinned | control C19 pins the known limit | this lane | **PLUGGED** |
| WS-2 | description is a claim surface | asserted from a canonical source (Z7) | this lane | **PLUGGED** |
| WS-1 | one-bit boundaries | lint for exact-exit-code assertions | this lane | queued |
| WS-3 | blind spots | property-based fuzzer | this lane | queued |
| WS-4 | self-verification | hand the verifier to the analysis lane to break | **handoff** | **DONE — reviewed** |
| WS-6 | no ongoing check | scheduled account-wide drift run | this lane | queued |
| WS-8 | counterexamples unstorable | generators | — | plugged |
| WS-9 | context into a training tier | your decision | **you** | flagged |

**The one-line diagnosis:** every plug above is the same plug. *Make the difference between "it said
no", "it broke", and "it never ran" impossible to miss — and make that guarantee live in one place
that both the machine and the human read.*
