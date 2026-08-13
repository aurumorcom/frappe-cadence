# Architecture Constraints

## Technical Constraints

- **Frappe Framework Ecosystem**: The application MUST operate within a standard Frappe Bench workspace on Python `>=3.14` and Frappe v16+.
- **Required Ecosystem Apps**: Declared in [`hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:8) as `["frappe_controller", "frappe_playbook", "crm"]`.
- **Database Engine**: Relational storage constrained to MariaDB (InnoDB engine) adhering to Frappe DocType ORM schemas.
- **Asynchronous Task Architecture**: Background execution MUST route through [`frappe.enqueue()`](apps/frappe_cadence/frappe_cadence/jobs/cadence.py:115) integrated with `frappe_controller` and FastStream workers rather than standalone blocking threads.
- **AST Condition Parser**: Condition evaluation MUST use Python's built-in `ast.parse()` mode in [`Cadence._ast_to_filters()`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:43). Using raw Python `eval()` or `exec()` is strictly forbidden.
- **External Mailing Integration**: Campaign scheduling and sequence execution are delegated to Listmonk via REST APIs and Webhooks.

## Organizational and Operational Constraints

- **Code Formatting and Linting**: Enforced via `ruff` with tab-based indentation, double quotes, and line-length 110 configured in [`pyproject.toml`](apps/frappe_cadence/pyproject.toml:24).
- **Authentication and Secrets Management**: Secrets (such as `listmonk_access_token` and `listmonk_webhook_secret`) MUST be stored in `site_config.json` or encrypted inside [`Listmonk Settings`](apps/frappe_cadence/frappe_cadence/cadence/doctype/listmonk_settings/listmonk_settings.py:8).
- **Multi-Tenancy**: All background jobs and database operations MUST preserve Frappe site multi-tenant boundaries.
