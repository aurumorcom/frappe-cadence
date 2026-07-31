# C2 Container Architecture Model

This document defines the C2 Container diagram for [`apps/frappe_cadence/frappe_cadence/hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:1) and its infrastructural dependencies.

## Container Diagram

```mermaid
erDiagram
    "Frappe Desk UI" ||--o{ "Frappe WSGI App" : "sends_http_requests_and_api_calls"
    "Frappe WSGI App" ||--o{ "MariaDB Database" : "reads_and_writes_doctypes"
    "Frappe WSGI App" ||--o{ "Background Worker Pool" : "enqueues_background_jobs"
    "Background Worker Pool" ||--o{ "MariaDB Database" : "executes_schedule_and_updates_states"
    "Background Worker Pool" ||--o{ "Sift Service" : "sends_prompt_and_optimization_requests"
    "Background Worker Pool" ||--o{ "External Channel Gateways" : "dispatches_multi_channel_messages"
    "Sift Service" ||--o{ "Frappe WSGI App" : "delivers_ai_callback_webhooks"
    "External Channel Gateways" ||--o{ "Frappe WSGI App" : "delivers_engagement_event_webhooks"
```

## Container Specifications

| Container | Technology / Protocol | Purpose / Responsibility |
| :--- | :--- | :--- |
| `Frappe Desk UI` | Web Browser, HTML5, Frappe JS | Client interface for managing Cadences, Multi-Channel Schedules, Templates, User Bios, and Providers. |
| `Frappe WSGI App` | Python 3, Frappe Framework | Handles HTTP controllers, whitelisted API endpoints, and webhook callback receivers ([`apps/frappe_cadence/frappe_cadence/cadence/email_template.py`](apps/frappe_cadence/frappe_cadence/cadence/email_template.py:5), [`apps/frappe_cadence/frappe_cadence/integrations/sift.py`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:151)). |
| `MariaDB Database` | MariaDB / InnoDB Engine | Relational database storing all Cadence DocTypes (`Cadence`, `Multi Channel Cadence`, `User Bio`, `Cadence Provider`, `History`, `Communication`, etc.). |
| `Background Worker Pool` | Redis Queue, `frappe_controller` Job Manager | Executes background evaluation and step dispatch jobs like `process_schedule`, `evaluate_cadence_for_leads`, and `populate_mccs_with_new_provider` ([`apps/frappe_cadence/frappe_cadence/hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:182)). |
| `Sift Service` | HTTPS REST / Webhooks | External Sift engine performing automated template optimization and prompt predictions (`sift.optimize`, `sift.predict`). |
| `External Channel Gateways` | REST / SMTP / Vendor APIs | Third-party messaging gateways handling outbound delivery and inbound delivery/reply webhook notifications. |
