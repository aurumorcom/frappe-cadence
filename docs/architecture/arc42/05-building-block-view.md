# Building Block View

## Whitebox Overall System
This section outlines the system's structural containers and internal components.

Link to C2 Container Model: [`C2 Container Diagram`](apps/frappe_listmonk/docs/architecture/c4/02-container.md)

### Contained Building Blocks

| Building Block | Responsibility | Technical Foundation |
| :--- | :--- | :--- |
| **Gunicorn Web Server** | Receives HTTP requests, serves Frappe Desk, and handles webhook callbacks | Python 3.14 / Frappe WSGI |
| **FastStream Background Worker** | Consumes asynchronous queues, executes cadence qualification, and synchronizes external systems | Python / FastStream / Frappe Controller |
| **MariaDB Database** | Persists DocTypes, relational constraints, research data, and logs | MariaDB 10.11 / InnoDB |
| **Redis Queue Broker** | Manages message queues, job state distribution, and rate-limiting counters | Redis 7 |
| **Listmonk Integration Client** | Translates internal domain models into Listmonk API requests | Python `requests` & Pydantic schemas |

### Important Interfaces

- `ListmonkClient.create_subscriber(req)`: Provisions contacts in Listmonk with custom contact metadata.
- `ListmonkClient.update_subscriber(subscriber_id, req)`: Synchronizes contact attributes, research context, and user bio tags.
- `ListmonkClient.create_list(req)` / `update_list(list_id, req)`: Provisions and synchronizes campaign lists.
- `webhook()`: Whitelisted public endpoint processing incoming HMAC-verified Listmonk notifications.

## Level 2
Link to C3 Component Model: [`C3 Component Diagram`](apps/frappe_listmonk/docs/architecture/c4/03-component.md)

### Component Specifications
1. **Cadence Controller (`DocType::Cadence`)**: Manages cadence lifecycle, AST expression parsing, and sequence provisioning.
2. **MultiChannelCadence Controller (`DocType::MultiChannelCadence`)**: Orchestrates individual prospect outreach instances from `Draft` through `Scheduled` to terminal states.
3. **Listmonk Settings (`DocType::ListmonkSettings`)**: Single DocType configuring base URLs, API tokens, webhook secrets, and bootstrap commands.
4. **Deep Research & Source Controllers (`DocType::DeepResearch`, `DocType::Source`, `DocType::DeepResearchSource`)**: Manages AI research summaries, web source references, and linked entity metadata via [`DeepResearch`](apps/frappe_listmonk/frappe_listmonk/listmonk/doctype/deep_research/deep_research.py:5) and [`Source`](apps/frappe_listmonk/frappe_listmonk/listmonk/doctype/source/source.py:5).

## Level 3
Deep decomposition of sub-components:
- **Condition Compiler**: Transforms Python AST nodes into structured filters.
- **Sender Allocator**: Queries active Multi Channel Cadence counts per user for load balancing or increments circular indexes for round-robin routing.
- **Webhook Verifier**: Calculates HMAC-SHA256 digests on raw request payloads to prevent unauthorized state manipulation.
