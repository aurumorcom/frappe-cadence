# 10 Quality Requirements

This document defines concrete quality scenarios and testable metrics for [`apps/frappe_cadence/frappe_cadence/hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:1).

## Quality Tree & Scenarios

| Quality Category | Scenario Description | Architectural Mechanism & Target Metric |
| :--- | :--- | :--- |
| **Reliability** | An external Sift AI request times out or external channel provider webhooks fail during high lead throughput. | Background step queues pause gracefully using `wait_for_event()` and retry automatically based on `controller_events` settings (max 3 retries, 300s timeout) ([`hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:182)). |
| **Data Integrity & Idempotency** | Multiple lead updates or duplicate cadence trigger calls occur simultaneously for the same prospect. | Unique constraints on cadence enrollment and duplicate check in [`add_lead_to_cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:255) ensure leads are never double-enrolled. |
| **Security & Privacy** | A non-admin user attempts to access or modify another user's sender bio or AI template annotation. | Custom `has_permission` checks in [`UserBio`](apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py:11) enforce strict session ownership validation. |
| **Performance** | Evaluating large lead databases against complex Python AST assignment conditions. | `_ast_to_filters()` compiles AST conditions into database-native SQL filters for index-accelerated queries ([`cadence.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:67)). |
