# Linting Baseline Specification

## Purpose

Provide a reusable boilerplate for linting policy across the repository.

## Required Policy Sections

Every linting policy spec must define:

1. Scope
- Target paths/modules.
- In-scope file types.

2. Rule Categories
- Safety and correctness rules.
- Type discipline rules.
- Style and consistency rules.
- Suppression and ignore rules.

3. Severity and Gate Behavior
- Which violations are blockers.
- Which violations are advisory.
- CI and PR gate expectations.

4. Exception Workflow
- Approval process.
- Required documentation.
- Review cadence and expiry.

5. Change Management
- How rule additions/removals are announced.
- Compatibility notes for rule tightening.

## Baseline Principles

- Prefer explicit typing over generic catch-all types for external input and domain contracts.
- Minimize broad suppressions; require narrow, localized suppressions.
- Keep lint rules deterministic and automatable.
- Use linting to prevent regressions, not only to enforce formatting.

## Review Gate

- PRs that weaken linting gates must include a spec update and rationale.
- PRs adding broad ignores without exception records must be rejected.
