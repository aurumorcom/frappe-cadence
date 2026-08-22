# Cross-cutting Concepts

## Security & Authentication
- **Webhook Authenticity**: The inbound webhook handler in [`webhook()`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/jobs/webhook.py:68) mandates HMAC-SHA256 signature verification matching `Listmonk-Signature` against the configured `webhook_secret`.
- **Role-Based Access Control (RBAC)**: All DocTypes implement strict Frappe permissions. For example, [`User Bio`](apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py:8) validates that non-System Managers can only modify their own profile records.
- **SQL & Injection Prevention**: Condition expressions are sanitized using Python AST compilation, and all SQL queries use parameterized arguments or Frappe Query Builder (`frappe.qb`).

## Persistency & Data Access
- **Transactional State Management**: State transitions on [`Multi Channel Cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:7) utilize Frappe's document lifecycle hooks (`before_insert`, `on_update`, `on_trash`).
- **Audit Trails**: Changes to research notes in [`Deep Research`](apps/frappe_cadence/frappe_cadence/cadence/doctype/deep_research/deep_research.py:6) automatically snapshot historical records into [`Deep Research History`](apps/frappe_cadence/frappe_cadence/cadence/doctype/deep_research_history/deep_research_history.json:37) with user attribution and timestamping.
- **Asset Persistence**: The [`History`](apps/frappe_cadence/frappe_cadence/cadence/doctype/history/history.py:10) controller automatically downloads remote screenshot URLs and stores them as managed private/public Frappe `File` records.

## Asynchronous Processing & Orchestration
- **Queue Configuration**: Background jobs are registered in [`hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:20) with fine-grained rate limits (e.g., 120/min for contact upserts, 60/min for sequence updates).
- **Transient Error Handling**: Operations throwing `requests.exceptions.RequestException` or HTTP 5xx errors are allowed to raise naturally so FastStream / `frappe_controller` can perform deterministic retries.
- **Batching & Chunking**: Lead evaluation splits large prospect datasets into 100-record chunks using `as_child=True` child tasks to avoid monolithic worker starvation.

## Observability & Logging
- **Named Application Loggers**: Standardized logging via `frappe.logger("cadence")` and `frappe.logger("listmonk")`.
- **Traceable Error Recording**: Unrecoverable failures are stored directly into Frappe's `Error Log` DocType via `frappe.log_error()`.
