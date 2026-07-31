# 11 Risks and Technical Debt

This document identifies architectural risks, technical debt, and mitigation strategies for [`apps/frappe_cadence/frappe_cadence/hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:1).

## Technical Debt & Identified Risks

| Risk / Technical Debt Item | Potential Impact | Current Mitigation / Recommendation |
| :--- | :--- | :--- |
| **Sift AI Callback Webhook Verification** | Unauthenticated guest callback endpoints could accept spoofed AI predictions if token validation fails. | Ensure request signatures are strictly verified in [`optimize_callback`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:152) and [`predict_callback`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:279) using `Sift Settings.webhook_secret`. |
| **Python AST Expression Flexibility** | Complex user-entered `assign_condition` strings could fail AST parsing or lead to SQL syntax errors. | Validate conditions during `before_save` via [`_ast_to_filters`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:67) and raise descriptive `ValidationError` messages. |
| **Redis Cache Eviction for AI Prompts** | Expired Redis cache keys during `process_schedule` re-trigger external Sift AI HTTP calls. | Standardize cache fallback timeouts and implement exponential backoff retries on Sift API connections. |
| **Multi-Channel Provider Failover** | If a primary channel provider goes offline, MCC execution stalls until provider configuration updates. | Dynamic provider re-allocation via [`populate_mccs_with_new_provider`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py:22) allows active cadence recovery. |
