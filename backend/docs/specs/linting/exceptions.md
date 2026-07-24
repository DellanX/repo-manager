# Linting Exceptions Specification

## Purpose

Define when and how linting exceptions are allowed.

## When Exceptions Are Allowed

- Dynamic input shape is unavoidable and cannot be represented safely with explicit models.
- Tooling false-positive is confirmed and cannot be resolved with code changes.
- Temporary migration constraints require staged compliance.

## Required Exception Record

Each exception must include:
- File and symbol location.
- Rule/tool identifier.
- Why compliant implementation is not currently viable.
- Risk impact and mitigation.
- Owner.
- Created date.
- Review date.
- Expiry or reevaluation trigger.
- Tracking issue or ADR link.

## Approval and Review

- Exceptions require reviewer approval in the PR introducing the exception.
- Exceptions must be re-reviewed on schedule or at expiry.
- Expired exceptions are considered policy violations.

## Boilerplate Template

Use this template for records:

- Location:
- Rule:
- Rationale:
- Risk and Mitigation:
- Owner:
- Created:
- Review Date:
- Expiry/Trigger:
- Tracking Reference:
