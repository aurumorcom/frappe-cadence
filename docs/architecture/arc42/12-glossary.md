# Glossary

## Dictionary of Terms

| Term | Definition |
| :--- | :--- |
| **AST (Abstract Syntax Tree)** | A tree representation of Python source code parsed via `ast.parse()`, used in Cadence to safely compile dynamic condition strings without `eval()`. |
| **Cadence** | A defined sequence and rule set for multi-step automated sales outreach campaigns. |
| **CRM Lead** | A prospect entity in Frappe CRM containing demographic, communication, and enrichment details. |
| **Context** | A document storing AI-researched dossiers, background intelligence, and point-in-time company data attached to a lead. |
| **Context History** | Child table recording versioned snapshots of Context records over time. |
| **FastStream Worker** | Background asynchronous worker managed by `frappe_controller` executing decoupled tasks. |
| **History** | Persistent audit log containing web crawling archives, extracted markdown, and screenshot images. |
| **History Group** | An aggregate grouping container organizing multiple History records under a target URL. |
| **Listmonk** | An external high-performance mailing engine handling subscriber lists, sequence schedules, email templates, and delivery analytics. |
| **Listmonk Sequence** | A mailing list inside Listmonk configured to execute an automated multi-step outbound campaign. |
| **Multi Channel Cadence (MCC)** | An active tracking instance representing a single lead enrolled into a specific Cadence and assigned to a sales representative. |
| **Playbook** | An automated workflow configuration orchestrating multi-step prospect research, data scraping, and intelligence compilation. |
| **Playbook Execution** | Runtime execution instance tracking the status and output of an active research Playbook. |
| **Round Robin** | An assignment rule rotating leads sequentially across a list of sales representatives. |
| **Load Balancing** | An assignment rule dynamically assigning new leads to the sales representative with the lowest count of active outreach instances. |
| **User Bio** | A personalized sender biography configured per sales representative and optionally customized per cadence. |
