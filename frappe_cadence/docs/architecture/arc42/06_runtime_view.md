# 06 Runtime View

This document summarizes the core behavioral workflows in [`apps/frappe_cadence/frappe_cadence/hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:1).

## Workflow Summaries

| Trigger / Workflow | Primary Document | Description |
| :--- | :--- | :--- |
| **01 Lead Cadence Enrollment** | [**01-lead-cadence-enrollment.md**](../bpmn/01-lead-cadence-enrollment.md) | Evaluates lead fields against Python AST conditions (`assign_condition`) and assigns leads via Round Robin or Load Balancing ([`evaluate_lead_for_cadences`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:215)). |
| **02 Playbook Provisioning** | [**02-playbook-provisioning.md**](../bpmn/02-playbook-provisioning.md) | Synchronizes Cadence creation with Playbook Execution and transitions MCC status from `Provisioning` to `Draft` or `Error` ([`playbook_execution.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/playbook_execution/playbook_execution.py:4)). |
| **03 MCC Step Scheduling** | [**03-mcc-step-scheduling.md**](../bpmn/03-mcc-step-scheduling.md) | Executes multi-channel step schedules in background queues, managing prerequisite checks (templates, bios, Sift AI predictions) via `wait_for_event()` ([`process_schedule`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:161)). |
| **04 Sift AI Template Optimization** | [**04-sift-template-optimization.md**](../bpmn/04-sift-template-optimization.md) | Generates AI prompt payloads, executes POST requests to Sift AI endpoints, and processes asynchronous callbacks (`sift.optimize_callback`, `sift.predict_callback`) ([`sift.py`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:4)). |
| **05 Engagement Tracking** | [**05-communication-engagement-tracking.md**](../bpmn/05-communication-engagement-tracking.md) | Processes communication doc events and external delivery webhooks (`report_event`), updating MCC status and cancelling queued steps on replies or bounces ([`cadence_provider.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py:53)). |
| **06 Cadence Provider Allocation** | [**06-cadence-provider-allocation.md**](../bpmn/06-cadence-provider-allocation.md) | Re-evaluates provider routing for active MCC records whenever provider configurations change ([`populate_mccs_with_new_provider`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py:22)). |
| **07 User Bio Provisioning** | [**07-user-bio-provisioning.md**](../bpmn/07-user-bio-provisioning.md) | Enforces bio permissions and emits `user_bio_created` events to unblock step queues waiting for sender context ([`user_bio.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py:22)). |
