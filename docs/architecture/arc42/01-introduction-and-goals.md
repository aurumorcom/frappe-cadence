# Introduction and Goals

## Requirements Overview
[`frappe_listmonk`](apps/frappe_listmonk/frappe_listmonk/hooks.py:1) is an enterprise cold outreach and sales engagement automation engine built on top of the Frappe Framework. It automates multi-step prospect communication workflows, coordinates AI/playbook-driven research and enrichment, distributes outbound communications across sales teams using configurable routing rules, synchronizes with the external Listmonk mailing engine, and tracks live engagement metrics in Frappe CRM.

### Core Functional Capabilities
- **Automated Lead Qualification**: Real-time evaluation of `CRM Lead` records against Cadence assignment conditions parsed via Abstract Syntax Trees (AST).
- **Intelligent Sales Rep Routing**: Multi-tenant workload distribution supporting `Round Robin` and `Load Balancing` algorithms across sales representatives.
- **Automated Playbook Enrichment**: Decoupled asynchronous enrichment via `Playbook Execution` to generate research dossiers prior to outreach delivery.
- **Bi-directional Listmonk Synchronization**: Native REST integration for subscriber provisioning, sequence list subscriptions, and transactional message dispatch.
- **Real-Time Webhook Processing**: Secure HMAC-SHA256 authenticated webhook receiver updating engagement states (`In Progress`, `Replied`, `Finished`, `Opted Out`, `Failed`).

## Quality Goals

| Priority | Quality Goal | Target Metric / Scenario |
| :--- | :--- | :--- |
| 1 | Idempotency & Safety | Zero duplicate enrollments of a `CRM Lead` into the same Cadence. |
| 2 | High Asynchronous Throughput | Background batch processing via `frappe_controller` handling >5,000 leads evaluated per minute. |
| 3 | Resilience & Fault Tolerance | External Listmonk HTTP timeouts auto-retried with exponential backoff without losing sequence state. |
| 4 | Auditability & History | Structured research summaries and source references in [`Deep Research`](apps/frappe_listmonk/frappe_listmonk/listmonk/doctype/deep_research/deep_research.json:1) and interaction logging in `History`. |

## Stakeholders

| Department | Expectations |
| :--- | :--- |
| Product | Deliver intuitive outreach automation, configurable cadence conditions, and clear lifecycle progression views. |
| Marketing | High-deliverability campaign synchronization with Listmonk, rich template personalization, and accurate engagement metrics. |
| Business | Scalable lead conversion, automated sales rep load-balancing, and reduced manual qualification overhead. |
| Customer Success | Seamless prospect journey progression, automated bio personalization, and instant reply alerting. |
| Customer Support | Reliable diagnostic logging in Frappe Error Log and transparent document revision histories. |
| IT & Infrastructure | Robust HMAC webhook verification, rate-limited FastStream queue workers, and zero web thread blocking. |
| Design & Technology | Strict C4/BPMN/arc42 architectural compliance, safe AST query compilation, and modular integration schemas. |
