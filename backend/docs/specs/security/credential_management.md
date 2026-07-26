# Credential Management Specification

## Purpose

Enable secure non-interactive authentication to providers such as GitHub, GitLab, and Azure DevOps for clone, fetch, pull, and push operations.

## Scope

- Credential storage, retrieval, rotation, and revocation.
- Provider-specific credential adapters.
- Secret references used by git operations and webhook signing.

## Credential Types

- Personal access tokens.
- OAuth access and refresh tokens.
- SSH private keys and passphrase references.
- App installation tokens or short-lived service tokens.

## Mandatory Security Controls

1. Encryption at rest for all stored secrets.
2. In-memory secret minimization and zeroization where feasible.
3. No plaintext credentials in logs, events, or error messages.
4. Strict access controls by principal and repository scope.
5. Secret reference model for API responses.
6. Rotation and revocation support.

## API and MCP Requirements

Required capability surface:

- Create credential
- Update credential
- Revoke credential
- List credential metadata without secret values
- Bind credential to repository or integration context

MCP must expose equivalent credential lifecycle tools with least-privilege defaults.

### Implemented Surface (Current)

- `GET /api/v1/credentials` -> list credential metadata only (no secret values).
- `POST /api/v1/credentials` -> create credential metadata + secure secret storage.
- `PUT /api/v1/credentials/{credential_id}` -> update metadata and optional secret rotation.
- `DELETE /api/v1/credentials/{credential_id}` -> revoke credential and remove secret.
- `POST /api/v1/clone` accepts optional `credential_id` for HTTPS private-host clone auth.
- MCP tools:
  - `credentials.list`
  - `credentials.create`
  - `credentials.update`
  - `credentials.revoke`
  - `git.clone` with optional `credential_id`

### Secret Backend Configuration

Credential metadata is persisted in SQLite, while secret values are stored through a pluggable secure backend.

- `REPO_MANAGER_SECRET_BACKEND=keyring` (default)
  - Uses OS keyring/credential manager.
  - If unavailable, operations fail with: `No secure keyring backend is available`.
- `REPO_MANAGER_SECRET_BACKEND=vault`
  - Uses HashiCorp Vault KV v2 API.
  - Required env vars:
    - `REPO_MANAGER_VAULT_ADDR` (for example `https://vault.example.com`)
    - `REPO_MANAGER_VAULT_TOKEN`
  - Optional env vars:
    - `REPO_MANAGER_VAULT_MOUNT` (default: `secret`)
    - `REPO_MANAGER_VAULT_PATH_PREFIX` (default: `repo-manager/credentials`)
    - `REPO_MANAGER_VAULT_NAMESPACE` (for Vault Enterprise namespaces)

## Provider Requirements

- GitHub: token validation and scope checks.
- GitLab: token validation and project scope checks.
- Azure DevOps: PAT validation and organization scope checks.

## Operational Requirements

- Audit trail for credential create, use, rotate, and revoke.
- Expiration monitoring and proactive renewal alerts.
- Provider outage handling with retry and clear user-visible errors.

## Validation Requirements

- Secret redaction tests for all logs and API errors.
- Access control tests across principals and repositories.
- Rotation and revocation workflow tests.
- Provider adapter contract tests.
