# Solution Strategy

## Summary and Rationale for Major Architectural Decisions

[`frappe_cadence`](apps/frappe_cadence/frappe_cadence/hooks.py:1) leverages a modern event-driven, decoupled architectural pattern designed for high reliability, minimal cognitive overhead, and scalable sales automation.

### 1. AST-Based Safe Dynamic Filtering
- **Decision**: Avoid Python's dynamic `eval()` or string queries for lead qualification.
- **Rationale**: Python's `ast.parse()` module decomposes condition strings (e.g., `doc.status == 'Open' and doc.country == 'US'`) into safe Abstract Syntax Trees. These are compiled into standard Frappe JSON query filter lists during [`Cadence.before_save()`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:31) to prevent code injection while enabling high-performance SQL indexing.

### 2. Decoupled Asynchronous Processing with Frappe Controller
- **Decision**: Execute heavy operations (Listmonk synchronization, lead batching, playbook enrichment) as asynchronous background jobs registered in [`hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:20) under `controller_events`.
- **Rationale**: Keeps web request latencies low, shields desk UI users from external service delays, and provides built-in rate-limiting and retry capabilities.

### 3. Separation of Sequence Orchestration vs Sequence Execution
- **Decision**: Use Frappe for lead management, enrichment, and business logic, while delegating low-level email dispatch, delays, interval handling, and SMTP infrastructure to Listmonk.
- **Rationale**: Eliminates the need to maintain complex email queue schedulers, deliverability engines, and link-tracking infrastructure within Frappe.

### 4. Dynamic Sender Persona & Context Hierarchy
- **Decision**: Resolve sender biographies and research context hierarchically per cadence or fallback to default profiles via [`User Bio`](apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py:8) and [`Context`](apps/frappe_cadence/frappe_cadence/cadence/doctype/context/context.py:6).
- **Rationale**: Allows sales representatives to tailor their tone, credentials, and message content per campaign while maintaining global defaults.
