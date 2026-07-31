# 08 Cross-Cutting Concepts

This document details cross-cutting operational principles implemented across [`apps/frappe_cadence/frappe_cadence/hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:1).

## 1. Authentication & Whitelisted Methods

- **Method Whitelisting & Type Annotations**:
  - Whitelisted API endpoints (`optimize`, `predict`, `get_user_bio`, `get_history`) require type-annotated parameters (`require_type_annotated_api_methods = True` in [`hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:287)).
- **Guest Access Controls**:
  - Public callback endpoints (e.g. `optimize_callback`, `predict_callback`, `frappe_cadence.cadence.email_template.callback`) declare `@frappe.whitelist(allow_guest=True)`. Callback handlers must validate request signatures or contextual identifiers before mutating database state.

## 2. Asynchronous Event-Driven Synchronization

- **Event Queue Suspend & Resume (`wait_for_event`)**:
  - Background step execution in [`process_schedule`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:161) suspends execution when prerequisite resources (templates, bios, preceding communication dispatches) are incomplete.
- **Reactive Event Emission (`emit_event`)**:
  - Document events (such as `user_bio_created`, `email_template_enabled`, or `sift_callback_received`) publish events that immediately wake up blocked background step tasks.

## 3. Rate Limiting & Background Job Governance

- **Controller Event Rate Limits**:
  - Outbound scheduling tasks are rate-limited via `controller_events` in [`hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:182):
    - `process_schedule`: max 50 executions/min, 3 retries, 300s timeout.
    - `evaluate_cadence_for_leads`: 1 retry, 600s timeout.
    - `populate_mccs_with_new_provider`: 1 retry, 600s timeout.

## 4. Privacy & Contextual Access Control

- **User Bio Privacy Hierarchy**:
  - [`UserBio.has_permission`](apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py:11) enforces that standard users can only read/edit bios where `reference_user` equals `frappe.session.user`.
  - Cadence step resolution retrieves bios with fallback mechanisms ([`get_user_bio`](apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py:25)): checks for cadence-specific bio overrides first, falling back to global user default bios.
