# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities through **GitHub's private vulnerability reporting**
(the *Security* tab → *Report a vulnerability*) rather than in a public issue.

Include, where you can: what you ran, what you expected, what happened, and the version or commit
you were on. A reproduction is worth more than a description.

## Scope

This repository contains **analysis tooling and documentation**. It does not process untrusted
input at rest, hold credentials, or run as a service.

The one place it touches input is the workflow parser: `tools/validate_workflows.py` reads YAML
files and reports on their structure. It uses `yaml.safe_load`, which does not construct arbitrary
Python objects. If you find a way to make it execute something, that is a vulnerability and I want
to know.

## What this project claims, and what it does not

Stated plainly, because a security policy that overclaims is worse than none:

- It claims the gate **parses** a workflow and can tell whether a job **contains a step that could
  fail the build**. Both are checked by committed controls. See `tools/tests/test_validator.py`.
- It does **not** claim any workflow is meaningful, any test passes, or any artifact is correct,
  secure, or used. `REGISTER.md` carries the same disclaimer at the point of use.

## Supported versions

`main`. This is a working method, versioned by file name where a correction changed behaviour
(`tools/validate_workflows.v1.0.orig.py` is kept beside the current version for provenance).
