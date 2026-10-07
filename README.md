# THE REGISTER

**Compiles this account's public-repo register from named checks, and refuses to publish when any check fails.**

[![controls](https://github.com/marsojuji-cmyk/the-register/actions/workflows/controls.yml/badge.svg)](https://github.com/marsojuji-cmyk/the-register/actions/workflows/controls.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-3776AB.svg)](.github/workflows/controls.yml)

**No named check, no line.** **The idea:** a register written by hand is true on the day it is written and silently false
afterwards. This one is **compiled**. Every line it prints was produced by a named check during
the same run, so it cannot drift — and when it is wrong, it is wrong reproducibly, in a way
someone else can re-run and argue with.

## What it guarantees

- **Every line comes from a check.** `tools/compile_register.py` produces each row of `REGISTER.md` from a named check in the same run. Each column names its method.
- **The gate verifies its own method.** `tools/tests/test_validator.py` runs 19 controls in both directions: known-bad workflows must be refused and known-good ones accepted.
- **Publishing is gated.** `tools/tests/verify_all.py` runs checks Z1–Z7 and exits non-zero if any fails. Z1–Z2 cover controls and the probe hunt. Z3 checks `REGISTER.md` against a fresh live compile, and Z4 does the same for `STATUS.md`. Z5 checks that every heal item is closed. Z6 rejects secrets or absolute home paths. Z7 checks that the published repo description matches its source. CI runs the same gate on every push.

## Quickstart

```bash
git clone https://github.com/marsojuji-cmyk/the-register && cd the-register
python3 -m pip install pyyaml                 # the only dependency, plus an authenticated gh CLI
python3 tools/tests/test_validator.py         # 19/19 controls: the method's own evidence
python3 tools/compile_register.py --refresh   # compiles REGISTER.md from live state
python3 tools/tests/verify_all.py             # the full publish gate
```

No pytest required: the controls run as a plain script and exit non-zero on failure.

## How it fails

| Condition | Behaviour |
|---|---|
| A control does not match its expected verdict | `test_validator.py` exits non-zero, and `verify_all.py` fails Z1 |
| `REGISTER.md` or `STATUS.md` drifts from a fresh compile | Z3 or Z4 fails, and the gate refuses to publish |
| A tracked file contains a secret or an absolute home path | Z6 fails |
| The live repo description differs from the canonical string | Z7 fails |
| `gh` is unauthenticated or a fetch fails | `gh()` returns empty output and the compiler records the item as absent, so a failed fetch under-reports and never over-reports. Z3 then flags the drift against the committed `REGISTER.md` |

## Evidence

- `python3 tools/tests/test_validator.py`, run locally 2026-10-07: **19/19 controls satisfied**.
- `python3 tools/tests/verify_all.py`, run locally 2026-10-07: **12/12 checks passed**, "CLEAN — safe to publish".
- CI `controls` is green on `main`.
- `REGISTER.md` (compiled 2026-10-07): 19 public repos, `SECURITY.md` on 15/19, a workflow on 17/19, 0 workflows refused by the gate.
- `INCIDENTS.md` records nine incidents (I1–I9), each with the control it produced.

## Why this exists

The account has 19 public repositories. `REGISTER.md` records which of them carry a `SECURITY.md`,
which have CI, and which have test suites. Two have been referenced by parties outside the account.

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

## The one rule

> **A method ships with its controls as a runnable file, or it does not ship.**

The gate in `tools/` is not trusted because it works. It is trusted because its controls are
committed, cover both directions, and include cases where the gate itself was wrong.

## Layout

```
REGISTER.md                    compiled — every line checked this run
INCIDENTS.md                   the defect ledger: nine incidents (I1–I9), each with its method fix and control
CANON.md                       the category and the six refusals
CODES.md                       the grammar
tools/validate_workflows.py    the method — refuses a workflow GitHub will reject or that cannot fail
tools/validate_workflows.v1.*.orig.py   earlier versions, kept for provenance
tools/tests/test_validator.py  the method's evidence — 19 controls, both directions
tools/tests/verify_all.py      the publish gate — Z1–Z7, exits non-zero on any failure
tools/compile_register.py      the compiler
tools/workflow-index.json      what was fetched, and from where
tools/workflows/<repo>/        every workflow file, as fetched
```

## What this does not claim

This register measures **presence and parseability**. It does not measure correctness, security,
usefulness, or adoption.

Green CI here means a pipeline **can** fail — not that it is testing anything worth testing.
`tests/` present means a directory exists — not that the tests pass.

**The only claim that grants authority is an external party depending on, citing, or routing
through an artifact.** Two such instances are known. That number is the one worth watching, and it
is deliberately *not* in the table, because it cannot be compiled from an API.

## Status

Active. CI recompiles and re-verifies the register on every push, and the Z7 canonical tracks the repo description.

## License

**MIT** (see `LICENSE`), chosen 2026-10-04 and reversible.

The choice follows from the goal: the point of a standard is that other people use it, and a
repository with no licence is "all rights reserved" by default — which blocks exactly the adoption
the register exists to earn. Permissive licensing removes a reason not to look.

**The discipline this does not waive:** if a method here is adopted elsewhere, name the source in
the adopting artifact. Attribution in the artifact — not in a footnote elsewhere — is what keeps a
borrowed method from becoming a contested one. That applies to this repository's methods the same
way it applies to anything borrowed *into* it. See `INCIDENTS.md` I2 for the case where a gate was
corrected rather than a file, and `CODES.md` sign 5 for the standing rule.
