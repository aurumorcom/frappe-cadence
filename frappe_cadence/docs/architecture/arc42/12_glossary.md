# 12 Glossary

Alphabetical glossary of domain and technical terms used in [`apps/frappe_cadence/frappe_cadence/hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:1).

## Terms & Definitions

| Term | Definition | Context / Reference |
| :--- | :--- | :--- |
| **AST (Abstract Syntax Tree)** | Structural representation of Python code used in `assign_condition` to convert lead matching rules into safe SQL queries. | [`apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:67) |
| **Cadence** | Master outreach sequence template defining steps, delay offsets, channels, and sender assignment rules. | [`apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:33) |
| **Cadence Provider** | Multi-channel provider configuration (Email, SMS, LinkedIn, WhatsApp) specifying capabilities and priority. | [`apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py:10) |
| **Multi Channel Cadence (MCC)** | An active execution instance tracking a specific prospect lead's progress through a cadence. | [`apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:32) |
| **Playbook Execution** | Asynchronous playbook execution lifecycle record linking Cadence creation with CRM workflows. | [`apps/frappe_cadence/frappe_cadence/cadence/doctype/playbook_execution/playbook_execution.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/playbook_execution/playbook_execution.py:4) |
| **Sift AI** | External AI engine integrated for cold outreach prompt optimization and engagement prediction. | [`apps/frappe_cadence/frappe_cadence/integrations/sift.py`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:4) |
| **User Bio** | Personal sender context and background information attached to users to personalize AI prompts. | [`apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py:5) |
