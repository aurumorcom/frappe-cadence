# Context and Scope

## Business Context
The system bridges the gap between raw CRM leads and proactive, multi-channel sales engagement. By orchestrating templates, user bios, and AI-driven personalization, it reduces the manual overhead required for sales representatives to execute complex, timed outreach campaigns.

[C1 System Context Diagram](../c4/01-system-context.md)

## Technical Context
The `frappe_cadence` application communicates via:
- **Internal Database**: MariaDB / InnoDB for persistent DocType storage.
- **Background Tasks**: Redis job queues executing Frappe methods asynchronously.
- **External Webhooks**: Exposes endpoints (`frappe_cadence.cadence.*_template.callback`) for asynchronous Sift AI response delivery.
- **External APIs**: Calls out to `sift.optimize` and `sift.predict` over HTTPS REST, and dispatches actual messages via `CadenceProvider` configured routing.
