# THE REGISTER

**No named check, no line.** A self-verifying record of what is actually true about this account's public artifacts.

**The idea:** a register written by hand is true on the day it is written and silently false
afterwards. This one is **compiled**. Every line it prints was produced by a named check during
the same run, so it cannot drift — and when it is wrong, it is wrong reproducibly, in a way
someone else can re-run and argue with.

---

## Reproduce it

```bash
git clone <this repo> && cd <this repo>
python3 tools/tests/test_validator.py     # 9/9 controls — the method's own evidence
python3 tools/compile_register.py --refresh   # compiles REGISTER.md from live state
```

No dependencies beyond `pyyaml` and an authenticated `gh` CLI. No pytest required — the controls
run as a plain script and exit non-zero on failure.

Read `REGISTER.md` for the compiled output. Read `INCIDENTS.md` for why it can be trusted.

---

## Why this exists

The account has nineteen public repositories. Eighteen of them carry a `SECURITY.md`, most of them
have CI, some have real test suites, and two have been referenced by parties outside it.

None of that was in one place, and none of it was checkable by a stranger. Worse, it was
**checked once, by hand, in a session** — which meant the claims were true on the day and unverified
every day after.

Three hand-probes taken during the compilation of this repo were each wrong:

| Probe | Hand-read | Actual | Direction |
|---|---|---|---|
| does `agentready` have a workflow? | no | **yes** — `scan-on-issue.yml` | under-detected |
| how many repos have a workflow? | 13 | **14** | under-detected |
| how many READMEs omit their check command? | 4 | **6** | under-detected |

Every error ran the same way: manual reads missed things that were there. That is the argument for
a compiled register over a careful reader — not that the compiler is smarter, but that it is
**reproducible**, and a reproducible claim can be disputed.

---

## The one rule

> **A method ships with its controls as a runnable file, or it does not ship.**

The gate in `tools/` is not trusted because it works. It is trusted because its nine controls are
committed, cover both directions, and include cases where the gate itself was wrong.

---

## Layout

```
REGISTER.md                    compiled — every line checked this run
INCIDENTS.md                   the defect ledger: six failures, six methods, six controls
CANON.md                       the category and the six refusals
CODES.md                       the grammar
tools/validate_workflows.py    the method (v1.1) — refuses a workflow GitHub will reject or that cannot fail
tools/validate_workflows.v1.0.orig.py   the previous version, kept for provenance
tools/tests/test_validator.py  the method's evidence — 9 controls, both directions
tools/compile_register.py      the compiler
tools/workflow-index.json      what was fetched, and from where
tools/workflows/<repo>/        every workflow file, as fetched
```

---

## What this does not claim

This register measures **presence and parseability**. It does not measure correctness, security,
usefulness, or adoption.

Green CI here means a pipeline **can** fail — not that it is testing anything worth testing.
`tests/` present means a directory exists — not that the tests pass.

**The only claim that grants authority is an external party depending on, citing, or routing
through an artifact.** Two such instances are known. That number is the one worth watching, and it
is deliberately *not* in the table, because it cannot be compiled from an API.

---

## Licence

**MIT** (see `LICENSE`), chosen 2026-10-04 and reversible.

The choice follows from the goal: the point of a standard is that other people use it, and a
repository with no licence is "all rights reserved" by default — which blocks exactly the adoption
the register exists to earn. Permissive licensing removes a reason not to look.

**The discipline this does not waive:** if a method here is adopted elsewhere, name the source in
the adopting artifact. Attribution in the artifact — not in a footnote elsewhere — is what keeps a
borrowed method from becoming a contested one. That applies to this repository's methods the same
way it applies to anything borrowed *into* it. See `INCIDENTS.md` I2 for the case where a gate was
corrected rather than a file, and `CODES.md` sign 5 for the standing rule.
