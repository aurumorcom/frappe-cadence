# Cross-cutting Concepts

## Security & Authentication
- **Webhook Authenticity**: The inbound webhook handler mandates HMAC-SHA256 signature verification matching `Listmonk-Signature` against the configured `webhook_secret`.
- **Role-Based Access Control (RBAC)**: All DocTypes implement strict Frappe permissions. For example, `User Bio` validates that non-System Managers can only modify their own profile records.
- **SQL & Injection Prevention**: Condition expressions are sanitized using Python AST compilation, and all SQL queries use parameterized arguments or Frappe Query Builder (`frappe.qb`).

## Persistency & Data Access
- **Transactional State Management**: State transitions on `Multi Channel Cadence` utilize Frappe's document lifecycle hooks (`before_insert`, `on_update`, `on_trash`).
- **Research Context Persistence**: Summaries and source references in [`Deep Research`](apps/frappe_listmonk/frappe_listmonk/listmonk/doctype/deep_research/deep_research.json:1) link explicitly to [`Source`](apps/frappe_listmonk/frappe_listmonk/listmonk/doctype/source/source.json:1) records and child table rows.
- **Asset Persistence**: The `History` controller automatically downloads remote screenshot URLs and stores them as managed private/public Frappe `File` records.

## Asynchronous Processing & Orchestration
- **Queue Configuration**: Background jobs are registered in `hooks.py` with fine-grained rate limits.
- **Transient Error Handling**: Operations throwing `requests.exceptions.RequestException` or HTTP 5xx errors are allowed to raise naturally so FastStream / `frappe_controller` can perform deterministic retries.
- **Batching & Chunking**: Lead evaluation splits large prospect datasets into 100-record chunks using `as_child=True` child tasks to avoid monolithic worker starvation.

## Observability & Logging
- **Named Application Loggers**: Standardized logging via `frappe.logger("listmonk")`.
- **Traceable Error Recording**: Unrecoverable failures are stored directly into Frappe's `Error Log` DocType via `frappe.log_error()`.
