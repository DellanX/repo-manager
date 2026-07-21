# Webhooks API Specification

Source modules (planned): new API and runtime modules for webhook subscriptions and dispatch.

## Purpose

Provide webhook management APIs so users can subscribe monitoring events to external systems.

## Managed Webhook Model

Webhook record fields:

- `webhook_id`
- `name`
- `target_url`
- `event_types`
- `secret_ref`
- `enabled`
- `retry_policy`
- `created_at`
- `updated_at`

`secret_ref` points to credential storage and never stores plaintext secrets in webhook records.

## Required API Endpoints

1. `POST /webhooks`
- Create webhook configuration.

2. `GET /webhooks`
- List webhook configurations.

3. `GET /webhooks/{webhook_id}`
- Get webhook details.

4. `PATCH /webhooks/{webhook_id}`
- Update webhook configuration.

5. `DELETE /webhooks/{webhook_id}`
- Delete webhook configuration.

6. `POST /webhooks/{webhook_id}/test`
- Send signed test event to target.

## Delivery Contract

- Payload includes event metadata, correlation ID, timestamp, and event body.
- Requests are signed with HMAC using referenced secret.
- Retries use bounded exponential backoff.
- Dead-letter state must be persisted after retry exhaustion.

## MCP Requirements

MCP must expose webhook tools:

- `integration.create_webhook`
- `integration.list_webhooks`
- `integration.update_webhook`
- `integration.delete_webhook`
- `integration.test_webhook`

## Config Surface

A configuration interface is required for webhook lifecycle management and status inspection.

- UI page is preferred, but API-first management is mandatory.
- Per-webhook enable and disable controls are required.
- Runtime health and last delivery status must be queryable.

## Validation Requirements

- Signature generation and verification tests.
- Retry and dead-letter tests.
- Endpoint idempotency tests for create and update operations.
- SSRF guard tests for target URL restrictions.
