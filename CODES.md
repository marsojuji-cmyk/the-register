# CODES

The grammar. Seven signs, legible at a glance, stable for years.

**These are not invented.** Every one of them was already in use across the repositories' own
descriptions before this file existed — *claim-tiered, witness, pre-registered, conformance,
provenance, adversarial, accountable, fail-closed*. They were never declared, which is why nineteen
repos read as nineteen projects instead of one house. Declaring them is the cheapest identity
available, and the only work involved is being consistent from here.

---

## The seven signs

**1 · claim-tiered**
Every statement carries its tier, in the sentence, without being asked. A claim without a tier is
a claim with no method.
*In practice:* "green CI (Tier 2)" — never bare "green".

**2 · witness**
A verified claim names the thing that witnessed it — a person, an artifact, a hash, a run, an
external party. No witness, no verification.
*In practice:* "verified — run 37201697856", "verified — sha256 `3168a2b5…`".

**3 · pre-registered**
Say what would count as success or failure **before** the result exists. Written down, dated,
unmodified afterwards. A criterion chosen after the fact is a story.
*In practice:* the falsifier section of any plan, written before the work starts.

**4 · conformance**
Independent verification against a published baseline, by someone who did not write the thing.
*In practice:* the conformance suite, the controls file, the register's `gate` column.

**5 · provenance**
Where it came from, before the argument starts. Cite the upstream; publish the diff between you and
the original. This is the discipline that keeps a borrowed method from becoming a contested one.
*In practice:* `INCIDENTS.md`, which names the previous version's hash and keeps it beside the new one.

**6 · adversarial**
Every method is tested by the case that should break it, not only by the case that should pass.
Both directions, or the controls are theatre.
*In practice:* `C4` and `C7` — the controls that must be *refused*.

**7 · fail-closed**
On ambiguity, refuse. An unreadable input is a failed input.
*In practice:* the gate exits non-zero and says why; it never passes something it could not parse.

---

## The composite

```
<artifact>   claim-tiered · witnessed · pre-registered · conformant · adversarial · fail-closed
```

Seven signs at a glance. A stranger who reads one artifact should be able to identify the next one
as belonging to the same house without being told.

---

## The one phrase to lead with

> **"What tier is that claim?"**

It is the whole grammar in five words, it is usable by someone who has never heard of this
repository, and it is the door into everything else. If a single phrase is going to travel, make it
that one.

---

## Falsifier

**Six months, measured one way:** do the READMEs, register entries, commit messages and incident
records visibly carry these signs without anyone reminding themselves to add them? If they still need
remembering, the codes are decoration — collapse them to sign 1 alone, or delete the file.
