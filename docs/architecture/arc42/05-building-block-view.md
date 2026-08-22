# Building Block View

## Whitebox Overall System
This section outlines the system's structural containers and internal components.

Link to C2 Container Model: [`C2 Container Diagram`](apps/frappe_cadence/docs/architecture/c4/02-container.md)

### Contained Building Blocks

| Building Block | Responsibility | Technical Foundation |
| :--- | :--- | :--- |
| **Gunicorn Web Server** | Receives HTTP requests, serves Frappe Desk, and handles webhook callbacks | Python 3.14 / Frappe WSGI |
| **FastStream Background Worker** | Consumes asynchronous queues, executes cadence qualification, and synchronizes external systems | Python / FastStream / Frappe Controller |
| **MariaDB Database** | Persists DocTypes, relational constraints, revision histories, and logs | MariaDB 10.11 / InnoDB |
| **Redis Queue Broker** | Manages message queues, job state distribution, and rate-limiting counters | Redis 7 |
| **Listmonk Integration Client** | Translates internal domain models into Listmonk API requests | Python `requests` & Pydantic schemas |

### Important Interfaces

- `ListmonkClient.create_subscriber(req)`: Provisions contacts in Listmonk with custom contact metadata.
- `ListmonkClient.update_subscriber(subscriber_id, req)`: Synchronizes contact attributes, research context, and user bio tags.
- `ListmonkClient.create_list(req)` / `update_list(list_id, req)`: Provisions and synchronizes campaign lists.
- `webhook()`: Whitelisted public endpoint processing incoming HMAC-verified Listmonk notifications.

## Level 2
Link to C3 Component Model: [`C3 Component Diagram`](apps/frappe_cadence/docs/architecture/c4/03-component.md)

### Component Specifications
1. **Cadence Controller (`DocType::Cadence`)**: Manages cadence lifecycle, AST expression parsing, and sequence provisioning via [`Cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:10).
2. **MultiChannelCadence Controller (`DocType::MultiChannelCadence`)**: Orchestrates individual prospect outreach instances from `Draft` through `Scheduled` to terminal states via [`MultiChannelCadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:7).
3. **Listmonk Settings (`DocType::ListmonkSettings`)**: Single DocType configuring base URLs, API tokens, webhook secrets, and bootstrap commands via [`ListmonkSettings`](apps/frappe_cadence/frappe_cadence/cadence/doctype/listmonk_settings/listmonk_settings.py:8).
4. **Deep Research & History Controllers (`DocType::DeepResearch`, `DocType::History`)**: Manages AI research notes, screenshots, web archives, and revision logs via [`DeepResearch`](apps/frappe_cadence/frappe_cadence/cadence/doctype/deep_research/deep_research.py:6) and [`History`](apps/frappe_cadence/frappe_cadence/cadence/doctype/history/history.py:10).

## Level 3
Deep decomposition of sub-components:
- **Condition Compiler**: Located in [`Cadence._ast_to_filters()`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:43). Transforms Python AST nodes into structured filters (e.g., `["doc.first_name", "=", "Jane"]`).
- **Sender Allocator**: Located in [`determine_sender()`](apps/frappe_cadence/frappe_cadence/jobs/cadence.py:155). Queries active Multi Channel Cadence counts per user for load balancing or increments circular indexes for round-robin routing.
- **Webhook Verifier**: Located in [`webhook()`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/jobs/webhook.py:68). Calculates HMAC-SHA256 digests on raw request payloads to prevent unauthorized state manipulation.
