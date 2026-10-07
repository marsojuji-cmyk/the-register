# THE REGISTER

**Compiled, not written.** Every line below was produced by a named check during this run.
A hand-written register is true on the day it is written and silently false afterwards;
this one cannot drift, because it prints nothing it has not just checked.

- **Account:** `marsojuji-cmyk`
- **Compiled:** 2026-10-07 16:12 MDT
- **Repos read:** 19 public
- **Method:** `tools/validate_workflows.py` · sha256 `9ec811231609512e…`
- **Method's evidence:** `tools/tests/test_validator.py` · sha256 `7ffab996e59f5f34…`
- **Workflow data:** fetched live during this run

Identified by content hash rather than a version string: a hand-maintained version number is
another claim that can drift from the artifact it describes.

| repo | SECURITY.md | workflows | gate | tests/ | check cmd in README |
|---|---|---|---|---|---|
| `adversarial-seat` | ✅ | 1 | ✅ clean | — | ✅ |
| `agentready` | ✅ | 1 | ✅ clean | — | ✅ |
| `atomic-admission` | ❌ | 1 | ✅ clean | — | ✅ |
| `beacon` | ✅ | 1 | ✅ clean | — | ✅ |
| `ep-aec-conformance` | ✅ | 1 | ✅ clean | ✅ | ✅ |
| `exhibit` | ✅ | 1 | ✅ clean | ✅ | ✅ |
| `governor` | ❌ | 1 | ✅ clean | ✅ | ✅ |
| `hermes-refuse` | ✅ | 1 | ✅ clean | — | ✅ |
| `honestyield.dev` | ❌ | 1 | ✅ clean | — | ✅ |
| `intent-spec` | ✅ | 1 | ✅ clean | — | ✅ |
| `interlock` | ✅ | 1 | ✅ clean | ✅ | ✅ |
| `interlock-forensics` | ✅ | 1 | ✅ clean | — | ✅ |
| `marsojuji-cmyk` | ✅ | — | — | — | — |
| `permit` | ✅ | 1 | ✅ clean | ✅ | ✅ |
| `quote-rescue` | ✅ | — | — | — | — |
| `reclamation-evidence-ledger` | ❌ | 3 | ✅ clean | ✅ | ✅ |
| `sovereign-contracts` | ✅ | 2 | ✅ clean | — | ✅ |
| `star-lab` | ✅ | 2 | ✅ clean | ✅ | ✅ |
| `the-register` | ✅ | 1 | ✅ clean | — | ✅ |

## Totals

- `SECURITY.md` present: **15/19**
- repos with at least one workflow: **17/19**
- workflows refused by the gate: **0**
- READMEs that do not surface a check command: **0** — none

## What each column establishes

- **SECURITY.md** — root directory listing via GitHub contents API (method: presence)
- **workflows** — count of .yml/.yaml files under .github/workflows (method: presence)
- **gate** — validate_workflows v1.1 run over every workflow file (method: parse + failable-step analysis)
- **tests/** — presence of a tests directory in the root listing (method: presence)
- **check cmd in README** — regex sweep of README for a runnable verify command (method: HEURISTIC — see footer)

## What this register does NOT claim

- That any test **passes**. A `tests/` directory is presence, not correctness.
- That any workflow is **meaningful**. The gate proves a job *can* fail; it does not
  prove the job is testing anything worth testing.
- That any README check command **works**. It proves the command is *written down*.
- That the code is **correct, secure, or used**.
- Anything about parties outside this account. **The only claim that grants authority
  is an external party depending on, citing, or routing through an artifact.**

## Provenance

The gate this register runs on has itself been calibrated, and has itself been wrong.
See `INCIDENTS.md` — four defects, each with the control it produced. The controls are
runnable: `python3 tools/tests/test_validator.py`.

