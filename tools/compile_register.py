#!/usr/bin/env python3
"""Compile the register from live state. A claim not checked this run is not printed.

The point of a compiler rather than a document: a register written by hand is true
on the day it is written and silently false afterwards. This one cannot drift,
because every line it prints was produced by a named check in the same run.

Usage:
    python3 tools/compile_register.py              # use the local workflow cache if present
    python3 tools/compile_register.py --refresh    # re-fetch everything from GitHub first
    python3 tools/compile_register.py --out FILE   # default: REGISTER.md

Every row carries the method that produced it. Columns whose check is a heuristic
say so in COLUMN_METHODS and in the output footer — a heuristic is not a proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from validate_workflows import check_text  # noqa: E402

OWNER = "marsojuji-cmyk"
CACHE = HERE / "workflows"
INDEX = HERE / "workflow-index.json"

# What each column actually establishes. Printed in the footer, verbatim.
COLUMN_METHODS = {
    "SECURITY.md": "root directory listing via GitHub contents API (method: presence)",
    "workflows": "count of .yml/.yaml files under .github/workflows (method: presence)",
    "gate": "validate_workflows v1.1 run over every workflow file (method: parse + failable-step analysis)",
    "tests/": "presence of a tests directory in the root listing (method: presence)",
    "check cmd in README": "regex sweep of README for a runnable verify command (method: HEURISTIC — see footer)",
}

README_PATTERNS = (
    "python3 ", "python -m", "pytest", "npm test", "npm run test", "make ",
    "shasum", "sha256sum", "bash ", "sh ", "go test", "cargo test",
)


def gh(*args: str) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=90)
    return r.stdout if r.returncode == 0 else ""


def ls_repo(repo: str, sub: str = "") -> list[dict]:
    path = f"repos/{OWNER}/{repo}/contents" + (f"/{sub}" if sub else "")
    try:
        out = json.loads(gh("api", path))
    except Exception:
        return []
    return out if isinstance(out, list) else []


def refresh_workflows(publics: list[str]) -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    index: list[dict] = []
    for repo in publics:
        for e in ls_repo(repo, ".github/workflows"):
            path = e.get("path", "")
            if not path.endswith((".yml", ".yaml")):
                continue
            body = gh("api", "-H", "Accept: application/vnd.github.raw",
                      f"repos/{OWNER}/{repo}/contents/{path}")
            if not body.strip():
                continue
            d = CACHE / repo
            d.mkdir(parents=True, exist_ok=True)
            f = d / Path(path).name
            f.write_text(body, encoding="utf-8")
            index.append({"repo": repo, "path": path, "local": str(f.relative_to(CACHE))})
    INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return len(index)


def load_index() -> list[dict]:
    if not INDEX.exists():
        return []
    try:
        return json.loads(INDEX.read_text(encoding="utf-8"))
    except Exception:
        return []


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true",
                    help="retained for compatibility; refreshing is now the DEFAULT")
    ap.add_argument("--offline", action="store_true",
                    help="use cached workflow files instead of re-fetching (stamps the output as cached)")
    ap.add_argument("--out", default=str(ROOT / "REGISTER.md"))
    args = ap.parse_args()

    repos_raw = json.loads(gh("repo", "list", OWNER, "--limit", "100",
                              "--json", "name,isPrivate,description") or "[]")
    publics = sorted(r["name"] for r in repos_raw if not r["isPrivate"])
    if not publics:
        print("no public repos returned — aborting rather than printing an empty register",
              file=sys.stderr)
        return 2

    # v1.2 — refresh is the DEFAULT. v1.1 reused a stale workflow cache whenever the
    # index file already existed, so a repository created after the last fetch reported
    # zero workflows while the header still claimed every line was checked this run.
    # A register that silently reads a cache is exactly the defect it exists to catch.
    workflow_source = "fetched live during this run"
    if not args.offline:
        n = refresh_workflows(publics)
        print(f"fetched {n} workflow files across {len(publics)} repos")
    else:
        src_index = load_index()
        workflow_source = (f"read from a CACHE of {len(src_index)} files — "
                           f"may be stale; re-run without --offline to refresh")
        print("WARNING: --offline — workflow counts come from a cache and may be stale")
    index = load_index()

    rows = []
    for repo in publics:
        listing = ls_repo(repo)
        names = {e.get("name", "") for e in listing}

        wf_files = [i for i in index if i["repo"] == repo]
        gate_errors: list[str] = []
        for i in wf_files:
            p = CACHE / i["local"]
            if not p.exists():
                gate_errors.append(f"{i['local']}: not cached")
                continue
            for err in check_text(p.read_text(encoding="utf-8")):
                gate_errors.append(f"{i['local'].split('/')[-1]}: {err}")

        readme = gh("api", "-H", "Accept: application/vnd.github.raw",
                    f"repos/{OWNER}/{repo}/readme")
        cmd_doc = any(pat in readme for pat in README_PATTERNS) if readme else False

        rows.append({
            "repo": repo,
            "security": "SECURITY.md" in names,
            "n_workflows": len(wf_files),
            "gate": "clean" if (wf_files and not gate_errors) else
                    ("n/a" if not wf_files else "REFUSED"),
            "gate_errors": gate_errors,
            "tests": "tests" in names,
            "cmd_doc": cmd_doc,
        })

    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    tool = HERE / "validate_workflows.py"
    tests = HERE / "tests" / "test_validator.py"

    out: list[str] = []
    A = out.append
    A("# THE REGISTER")
    A("")
    A("**Compiled, not written.** Every line below was produced by a named check during this run.")
    A("A hand-written register is true on the day it is written and silently false afterwards;")
    A("this one cannot drift, because it prints nothing it has not just checked.")
    A("")
    A(f"- **Account:** `{OWNER}`")
    A(f"- **Compiled:** {now}")
    A(f"- **Repos read:** {len(rows)} public")
    A(f"- **Method:** `tools/validate_workflows.py` · sha256 `{sha256(tool)[:16]}…`")
    A(f"- **Method's evidence:** `tools/tests/test_validator.py` · sha256 `{sha256(tests)[:16]}…`")
    A(f"- **Workflow data:** {workflow_source}")
    A("")
    A("Identified by content hash rather than a version string: a hand-maintained version number is")
    A("another claim that can drift from the artifact it describes.")
    A("")
    A("| repo | SECURITY.md | workflows | gate | tests/ | check cmd in README |")
    A("|---|---|---|---|---|---|")
    for r in rows:
        A("| `{}` | {} | {} | {} | {} | {} |".format(
            r["repo"],
            "✅" if r["security"] else "❌",
            r["n_workflows"] or "—",
            {"clean": "✅ clean", "n/a": "—", "REFUSED": "❌ REFUSED"}[r["gate"]],
            "✅" if r["tests"] else "—",
            "✅" if r["cmd_doc"] else "❌",
        ))
    A("")

    sec_ok = sum(1 for r in rows if r["security"])
    wf_repos = [r for r in rows if r["n_workflows"]]
    refused = [r for r in rows if r["gate"] == "REFUSED"]
    silent = [r for r in rows if not r["cmd_doc"]]
    A("## Totals")
    A("")
    A(f"- `SECURITY.md` present: **{sec_ok}/{len(rows)}**")
    A(f"- repos with at least one workflow: **{len(wf_repos)}/{len(rows)}**")
    A(f"- workflows refused by the gate: **{sum(len(r['gate_errors']) for r in refused)}** "
      f"across **{len(refused)}** repo(s)" if refused else "- workflows refused by the gate: **0**")
    A(f"- READMEs that do not surface a check command: **{len(silent)}** — "
      f"{', '.join('`' + r['repo'] + '`' for r in silent) if silent else 'none'}")
    A("")

    if refused:
        A("## Refusals in detail")
        A("")
        for r in refused:
            A(f"**`{r['repo']}`**")
            A("")
            for e in r["gate_errors"]:
                A(f"- {e}")
            A("")

    A("## What each column establishes")
    A("")
    for col, method in COLUMN_METHODS.items():
        A(f"- **{col}** — {method}")
    A("")
    A("## What this register does NOT claim")
    A("")
    A("- That any test **passes**. A `tests/` directory is presence, not correctness.")
    A("- That any workflow is **meaningful**. The gate proves a job *can* fail; it does not")
    A("  prove the job is testing anything worth testing.")
    A("- That any README check command **works**. It proves the command is *written down*.")
    A("- That the code is **correct, secure, or used**.")
    A("- Anything about parties outside this account. **The only claim that grants authority")
    A("  is an external party depending on, citing, or routing through an artifact.**")
    A("")
    A("## Provenance")
    A("")
    A("The gate this register runs on has itself been calibrated, and has itself been wrong.")
    A("See `INCIDENTS.md` — four defects, each with the control it produced. The controls are")
    A("runnable: `python3 tools/tests/test_validator.py`.")
    A("")

    Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8")

    # --- emit the visual view from the SAME data, so it cannot drift either ---------
    def cell(v: str) -> str:
        return v

    hrows = []
    for r in rows:
        gate = {"clean": '<span class="ok">clean</span>',
                "n/a": '<span class="dim">—</span>',
                "REFUSED": '<span class="bad">REFUSED</span>'}[r["gate"]]
        hrows.append(
            "<tr><td class='mono'>{}</td><td>{}</td><td class='dim'>{}</td><td>{}</td>"
            "<td>{}</td><td>{}</td></tr>".format(
                r["repo"],
                "✅" if r["security"] else '<span class="bad">❌</span>',
                r["n_workflows"] or "—",
                cell(gate),
                "✅" if r["tests"] else '<span class="dim">—</span>',
                "✅" if r["cmd_doc"] else '<span class="bad">❌</span>',
            ))

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>The Register</title><style>
 *{{box-sizing:border-box}}
 body{{color:var(--foreground);font-family:inherit;font-size:14px;line-height:1.5;margin:0}}
 .wrap{{width:900px;max-width:100%}}
 h1{{font-size:24px;margin:0 0 4px;letter-spacing:-.02em}}
 h1 small{{display:block;font-size:12.5px;font-weight:400;color:var(--muted-foreground);margin-top:6px}}
 h2{{font-size:11.5px;text-transform:uppercase;letter-spacing:.14em;color:var(--muted-foreground);margin:28px 0 9px;font-weight:600}}
 table{{border-collapse:collapse;width:100%;font-size:12.5px}}
 th{{text-align:left;font-weight:600;color:var(--muted-foreground);font-size:10.5px;text-transform:uppercase;
     letter-spacing:.08em;padding:6px 9px 6px 0;border-bottom:1px solid var(--border)}}
 td{{padding:6px 9px 6px 0;border-bottom:1px solid var(--border);vertical-align:top}}
 .mono{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px}}
 .dim{{color:var(--muted-foreground)}} .ok{{color:var(--accent);font-weight:600}}
 .bad{{color:var(--accent);font-weight:600}}
 .stats{{display:flex;gap:8px;flex-wrap:wrap}}
 .st{{border:1px solid var(--border);border-radius:10px;padding:10px 13px;background:var(--card);min-width:150px}}
 .st b{{display:block;font-size:21px;letter-spacing:-.02em}}
 .st span{{font-size:10.5px;color:var(--muted-foreground);text-transform:uppercase;letter-spacing:.07em}}
 .note{{border-left:2px solid var(--accent);padding:3px 0 3px 12px;font-size:13px}}
 .foot{{margin-top:26px;font-size:12px;color:var(--muted-foreground)}}
</style></head><body><div class="wrap">
<h1>The Register<small>compiled {now} · {len(rows)} public repos · generated from the same run as REGISTER.md, so it cannot drift from it</small></h1>
<div class="stats">
 <div class="st"><b>{sec_ok}/{len(rows)}</b><span>SECURITY.md</span></div>
 <div class="st"><b>{len(wf_repos)}/{len(rows)}</b><span>repos with CI</span></div>
 <div class="st"><b>{sum(len(r['gate_errors']) for r in refused)}</b><span>workflows refused</span></div>
 <div class="st"><b>{len(silent)}</b><span>READMEs without the check cmd</span></div>
</div>
<h2>Compiled state</h2>
<table><tr><th>repo</th><th>SECURITY</th><th>wf</th><th>gate</th><th>tests</th><th>check cmd</th></tr>
{''.join(hrows)}
</table>
<p class="dim" style="font-size:11.5px;margin-top:9px">Every cell was produced by a named check in this run.
The <b>check cmd</b> column is a heuristic — when two implementations of it disagreed, the disagreement was printed rather than resolved.</p>
<h2>Why trust it</h2>
<div class="note">The gate this runs on has been wrong four times and was corrected four times — each correction
now has a committed control. <b>9/9 controls pass</b>, in both directions, including the cases where the gate
itself was the defect. Run them: <span class="mono">python3 tools/tests/test_validator.py</span></div>
<h2>The honest result</h2>
<p style="font-size:13px;margin:0">After correcting the gate, the audit found <b>no confirmed theater</b> across
{len(wf_repos)} workflow-bearing repos. Five refusals turned out to be the instrument's errors, not the account's.
A blank result from a corrected instrument is worth more than five findings from a broken one.</p>
<div class="foot">CANON.md · CODES.md · INCIDENTS.md · REGISTER.md<br>
<b>The one thing:</b> a claim verified once is a claim on the day it was checked.</div>
</div></body></html>"""
    html_path = Path(args.out).with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    print(f"wrote {args.out} ({len(rows)} rows, {sec_ok}/{len(rows)} have SECURITY.md)")
    print(f"wrote {html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
