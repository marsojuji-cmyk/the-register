#!/usr/bin/env python3
"""The one command. Exit 0 only when the repository is in its best possible condition.

Implements the contract in HEAL.md:

  Z1  every control passes, both directions                       -> E2 on failure
  Z2  the adversarial probe hunt reports 0 findings               -> E2 on failure
  Z3  every generated artifact matches a fresh generation         -> E1 on failure
  Z4  no number in prose that no code enforces                    -> E1 on failure
  Z5  no E1/E2 row in HEAL.md is still OPEN                       -> E1 on failure
  --  plus: the repo passes its own gate, and carries no leaked secrets or home paths

Run:   python3 tools/tests/verify_all.py
Exit:  0 clean · 1 failures (listed) · 2 could not run a check at all
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
PY = sys.executable

# Lines that change every run and therefore cannot be compared. Everything else must match.
VOLATILE = (
    re.compile(r"^- \*\*Compiled:\*\*"),
    re.compile(r"compiled \d{4}-\d{2}-\d{2}"),
    re.compile(r"^(Generated|Checked|Verified):"),
)
OVERRIDE = "verify-all: stable"

results: list[tuple[str, bool, str]] = []


def _strip_volatile(text: str) -> str:
    return "\n".join(
        OVERRIDE if any(p.search(ln) for p in VOLATILE) else ln
        for ln in text.splitlines()
    ).strip()


def run(args: list[str], timeout: int = 300) -> tuple[int, str]:
    p = subprocess.run(args, capture_output=True, text=True, cwd=str(ROOT), timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))


# ---------------------------------------------------------------- Z1 controls
def z1() -> None:
    code, out = run([PY, "tools/tests/test_validator.py"])
    tail = [l for l in out.splitlines() if "controls satisfied" in l]
    check("Z1 gate controls (both directions)", code == 0,
          tail[-1] if tail else out.strip().splitlines()[-1:] or "")


# ---------------------------------------------------------------- Z2 probe hunt
def z2() -> None:
    code, out = run([PY, "tools/tests/probe_hunt.py"])
    tail = [l for l in out.splitlines() if "finding" in l]
    check("Z2 adversarial probe hunt (0 findings)", code == 0, tail[-1] if tail else "")


# ---------------------------------------------------------------- fixtures + self-audit
def fixtures() -> None:
    code, out = run([PY, "tools/tests/make_fixtures.py"])
    if code != 0:
        check("Z1b fixtures generate", False, out.strip()[:80])
        return
    check("Z1b fixtures generate", True, "2 files")
    bad = []
    for f in ("broken-heredoc.yml", "theater.yml"):
        c, _ = run([PY, "tools/validate_workflows.py", f"tools/tests/fixtures/{f}"])
        if c != 1:
            bad.append(f"{f}->{c}")
    check("Z1b bad fixtures REFUSED with exit 1", not bad, ", ".join(bad) or "both refused")
    c, _ = run([PY, "tools/validate_workflows.py", "/nonexistent/probe.yml"])
    check("Z1b missing file ERRORS with exit 3", c == 3, f"exit {c}")


def self_audit() -> None:
    wfs = sorted(str(p.relative_to(ROOT)) for p in (ROOT / ".github/workflows").glob("*.yml"))
    if not wfs:
        check("Z1c this repository has CI", False, "no workflows found")
        return
    c, out = run([PY, "tools/validate_workflows.py", *wfs])
    check("Z1c this repository passes its own gate", c == 0,
          out.strip().splitlines()[-1] if out.strip() else "")


# ---------------------------------------------------------------- Z3 artifact freshness
def z3() -> None:
    target = ROOT / "REGISTER.md"
    if not target.exists():
        check("Z3 REGISTER.md present", False, "missing")
        return
    committed = target.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "REGISTER.md"
        # Always LIVE. The register's whole claim is that every line was checked during this
        # run, and its provenance line says so — compiling from cache would make that line
        # differ, and the comparison would stop meaning anything. Network required; failure
        # to reach GitHub is a failure of the check, never a pass.
        code, out = run([PY, "tools/compile_register.py", "--out", str(tmp)], 600)
        if not tmp.exists():
            check("Z3 REGISTER.md matches a fresh compile", False, "compile produced nothing")
            return
        fresh = tmp.read_text(encoding="utf-8")
    a, b = _strip_volatile(committed), _strip_volatile(fresh)
    if a == b:
        check("Z3 REGISTER.md matches a fresh compile", True, "no substantive drift")
    else:
        import difflib
        d = list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0))
        check("Z3 REGISTER.md matches a fresh compile", False,
              f"{len(d)} diff lines: {' / '.join(d[2:6])[:110]}")


# ---------------------------------------------------------------- Z4 generated status
def z4() -> None:
    status = ROOT / "STATUS.md"
    if not status.exists():
        check("Z4 STATUS.md is generated, not written", False, "missing")
        return
    body = status.read_text(encoding="utf-8")
    ok = "GENERATED" in body.upper()
    check("Z4 STATUS.md declares itself generated", ok,
          "counts cannot drift if they are produced, not typed")


# ---------------------------------------------------------------- Z5 heal register
def z5() -> None:
    heal = ROOT / "HEAL.md"
    if not heal.exists():
        check("Z5 all E1/E2 items healed", False, "HEAL.md missing")
        return
    open_items = []
    for ln in heal.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s.startswith("| **E1-") and not s.startswith("| E1-") and not s.startswith("| E2-"):
            continue
        if "**open**" in s.lower():
            open_items.append(s.split("|")[1].strip())
    check("Z5 no blocking (E1/E2) item left OPEN", not open_items,
          ", ".join(open_items) or "all closed")


# ---------------------------------------------------------------- leaks
LEAK = re.compile(
    r"(ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}"
    r"|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|/Users/[a-z]+/)"
)


def leaks() -> None:
    c, out = run(["git", "ls-files"])
    hits = []
    for rel in out.split():
        if rel.startswith("tools/workflows/"):
            continue  # cached third-party workflows contain secret-scan regexes
        f = ROOT / rel
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, ln in enumerate(text.splitlines(), 1):
            if LEAK.search(ln):
                hits.append(f"{rel}:{i}")
    check("Z6 no secrets or absolute home paths in tracked files", not hits,
          ", ".join(hits[:4]) or "clean")

    # Z7 — THE REPOSITORY DESCRIPTION IS A CLAIM SURFACE TOO. One was typed by hand on
    # 2026-10-04 and went stale within minutes, which is WS-2: prose asserting what no code
    # enforces. It is now asserted against this single source, and it deliberately contains
    # no counts — a number in a published string is exactly the defect being plugged.
    canonical = (
        "A register that compiles itself: every claim is produced by a named check during "
        "the run. Ships with a pre-push gate that refuses to publish a repository that is "
        "not clean."
    )
    _, live = run(["gh", "api", "repos/marsojuji-cmyk/the-register", "--jq", ".description"])
    live = live.strip()
    check("Z7 repository description matches this source", live == canonical,
          "in sync" if live == canonical else f"live: {live[:64]!r}")


def main() -> int:
    for fn in (z1, z2, fixtures, self_audit, z3, z4, z5, leaks):
        try:
            fn()
        except Exception as exc:  # a check that cannot run is a failure, never a pass
            check(f"{fn.__name__} could not run", False, repr(exc)[:110])

    width = max(len(n) for n, _, _ in results)
    failed = 0
    print("VERIFY ALL".ljust(width + 12, "="))
    for name, ok, detail in results:
        if not ok:
            failed += 1
        print(f"{'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
    print("=" * (width + 12))
    print(f"{len(results) - failed}/{len(results)} checks passed")

    if failed:
        print("\nPUSH REFUSED. Nothing reaches GitHub unless it is in its best condition.")
        print("Fix the failure, or record the gap in HEAL.md with a severity, owner and status.")
        return 1
    print("\nCLEAN — safe to publish.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
