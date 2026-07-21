# Security Baseline Specification

## Status

This is a mandatory baseline. New features must satisfy these controls before merge.

## Required Controls

1. Workspace isolation
- All file paths must resolve under configured workspace root.
- Traversal attempts (for example `../`) must be rejected with a controlled error.

2. Command execution restrictions
- `exec` capability must enforce a policy.
- Policy must be one of: explicit allowlist or sandboxed execution environment.
- Free-form arbitrary shell execution in production mode is forbidden.

3. Input validation limits
- Maximum sizes must be defined for command input and file writes.
- Requests that exceed limits must fail with deterministic 4xx errors.

4. Error hygiene
- Errors must not leak secrets, local usernames, or full filesystem details.
- Standard error format must be documented and reused across APIs.

5. Event auditability
- Sensitive fields must be redacted in event payloads.
- Event records must include operation name, status, and timestamp.

6. Auth readiness gate
- Current auth state must be declared as "not implemented" in user-facing docs.
- Production deployment requires an explicit auth decision record.

7. Credential handling
- Credentials must be encrypted at rest and referenced by ID, not returned in plaintext.
- Secret material must be redacted from logs, events, and error payloads.

8. Webhook outbound safety
- Webhook targets must enforce SSRF protections (allowlist and network boundary policy).
- Webhook payloads must be signed and signature algorithm documented.

## Test Requirements

- Traversal rejection tests for read and write paths.
- Injection-pattern rejection tests for command execution policy.
- Input-size boundary tests.
- Redaction checks for logs/events.
- Unauthorized access tests once auth is introduced.
