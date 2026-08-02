# Glossary

| Term | Definition |
| :--- | :--- |
| AST | Abstract Syntax Tree. Used to parse Python conditions (`doc.status == "New"`) into SQL filters for lead assignments. |
| Cadence | The master template defining the sequence of outreach steps, assignment rules, and user pools. |
| Idempotency | The property of a function (`process_schedule`) that allows it to be executed multiple times without changing the result beyond the initial application. |
| MultiChannelCadence | The specific instance of a cadence running for a single prospect (`CRM Lead`). |
| Playbook Execution | The synchronous or asynchronous setup processes executed via the `frappe_playbook` app before a cadence becomes fully active (`Draft` status). |
| Sift API | The external AI orchestration layer providing context-aware messaging prompts. |
