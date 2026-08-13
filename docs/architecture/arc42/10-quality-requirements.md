# Quality Requirements

## Quality Requirements Overview
Quality requirements for [`frappe_cadence`](apps/frappe_cadence/frappe_cadence/hooks.py:1) focus on operational reliability, idempotency of prospect enrollment, transactional integrity, and resilience to third-party API disruptions.

## Quality Scenarios

### Scenario Q1: Idempotent Cadence Enrollment
- **Source**: Concurrent document updates on [`CRM Lead`](apps/frappe_cadence/frappe_cadence/cadence/doctype/crm_lead/crm_lead.py:6) and [`Cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:10).
- **Stimulus**: Multiple background jobs trigger `add_lead_batch_to_cadence()` simultaneously for the same lead.
- **Environment**: High concurrency under production queue load.
- **Response**: The unique index and existence check in [`add_lead_batch_to_cadence()`](apps/frappe_cadence/frappe_cadence/jobs/cadence.py:125) prevents duplicate [`Multi Channel Cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:7) insertion.
- **Measurement**: Exactly 1 `Multi Channel Cadence` document created per lead/cadence pair.

### Scenario Q2: Third-Party Outreach Engine Outage
- **Source**: Listmonk API service downtime or network partition.
- **Stimulus**: [`add_contact_to_sequence()`](apps/frappe_cadence/frappe_cadence/jobs/multi_channel_cadence.py:25) receives HTTP 503 from Listmonk.
- **Environment**: Normal operation during maintenance window.
- **Response**: Job fails without corrupting database state; FastStream retry mechanism retains job payload in queue and retries with backoff.
- **Measurement**: Zero failed leads marked permanently broken during transient outages.

### Scenario Q3: Webhook Forgery Prevention
- **Source**: Malicious external actor sending forged status update webhooks.
- **Stimulus**: HTTP POST sent to `/api/method/.../webhook` without valid HMAC header.
- **Environment**: Public ingress endpoint.
- **Response**: Handler rejects payload before state modification, returning HTTP 403 / `frappe.PermissionError`.
- **Measurement**: 100% of forged payloads blocked; zero unauthorized status transitions.
