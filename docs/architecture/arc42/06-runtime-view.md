# Runtime View

## Overview
This section describes the runtime execution flows, state transitions, and exception paths across [`frappe_cadence`](apps/frappe_cadence/frappe_cadence/hooks.py:1).

---

## Scenario 0A: Listmonk Settings Authorization & Webhook Provisioning
Link to BPMN Workflow: [`01. Listmonk Settings & Webhook Provisioning Workflow`](apps/frappe_cadence/docs/architecture/bpmn/01-listmonk-settings-and-webhook-provisioning.md)

### Trigger & Steps
1. Administrator configures [`Listmonk Settings`](apps/frappe_cadence/frappe_cadence/cadence/doctype/listmonk_settings/listmonk_settings.py:8) with `base_url` and `access_token`.
2. Controller triggers [`ListmonkClient.test_connection()`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/client.py:140) to verify API connectivity.
3. Upon successful authorization, [`setup_webhook()`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/jobs/webhook.py:21) automatically registers or updates the webhook endpoint in Listmonk with HMAC secret security.

---

## Scenario 0B: Listmonk Historical Lead Bootstrapping
Link to BPMN Workflow: [`02. Listmonk Lead Bootstrap Workflow`](apps/frappe_cadence/docs/architecture/bpmn/02-listmonk-lead-bootstrap.md)

### Trigger & Steps
1. Authorized user executes [`ListmonkSettings.bootstrap_listmonk()`](apps/frappe_cadence/frappe_cadence/cadence/doctype/listmonk_settings/listmonk_settings.py:41).
2. The system enqueues [`sync_all_crm_leads()`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/jobs/subscriber.py:59) to query all CRM leads.
3. Asynchronous [`upsert_subscriber()`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/jobs/subscriber.py:15) jobs synchronize subscriber records and store `listmonk_id` back onto each `CRM Lead`.

---

## Scenario 1: Lead Qualification and Cadence Enrollment
Link to BPMN Workflow: [`03. Lead Qualification and Enrollment Workflow`](apps/frappe_cadence/docs/architecture/bpmn/03-lead-qualification-and-enrollment.md)

### Trigger & Steps
1. An incoming or existing [`CRM Lead`](apps/frappe_cadence/frappe_cadence/cadence/doctype/crm_lead/crm_lead.py:6) is saved, triggering `on_update`.
2. `crm_lead.on_update` enqueues [`evaluate_cadences_for_lead()`](apps/frappe_cadence/frappe_cadence/jobs/cadence.py:107) and [`upsert_subscriber()`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/jobs/subscriber.py:15).
3. The background job iterates through enabled [`Cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:10) records, checking pre-compiled `assign_condition_json` filters against the lead's attributes.
4. If conditions match and no duplicate enrollment exists in [`Multi Channel Cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:7), [`determine_sender()`](apps/frappe_cadence/frappe_cadence/jobs/cadence.py:155) selects a sales rep using the configured `Round Robin` or `Load Balancing` rule.
5. A new [`Multi Channel Cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:7) document is inserted with initial status `Draft`.

### Exception Path
- If condition syntax in `assign_condition` is malformed upon cadence creation, `ast.parse()` raises `frappe.ValidationError`, blocking invalid rules before runtime.

---

## Scenario 2: Playbook Enrichment & Attribute Synchronization
Link to BPMN Workflow: [`04. Playbook Enrichment Workflow`](apps/frappe_cadence/docs/architecture/bpmn/04-playbook-enrichment.md) & [`05. Listmonk Sequence Synchronization Workflow`](apps/frappe_cadence/docs/architecture/bpmn/05-listmonk-sequence-sync.md)

### Trigger & Steps
1. [`MultiChannelCadence.on_update()`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:12) detects a new `Draft` record and checks if `reference_playbook` is configured.
2. A [`Playbook Execution`](apps/frappe_cadence/frappe_cadence/cadence/doctype/playbook_execution/playbook_execution.py:7) document is inserted with status `Queued`.
3. As the playbook runs, it gathers company dossier research into [`Context`](apps/frappe_cadence/frappe_cadence/cadence/doctype/context/context.py:6) and marks execution `completed`.
4. The completion hook updates [`Multi Channel Cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:7) to `Provisioning` and triggers [`add_subscriber_to_sequence()`](apps/frappe_cadence/frappe_cadence/jobs/multi_channel_cadence.py:25).
5. [`add_subscriber_to_sequence()`](apps/frappe_cadence/frappe_cadence/jobs/multi_channel_cadence.py:25) fetches sender [`User Bio`](apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py:8) and research context, formats template attributes, attaches the subscriber to the Listmonk campaign sequence, and sets status to `Scheduled`.

### Exception Path
- If Listmonk is temporarily unreachable (HTTP 500/timeout), the `requests` error bubbles up to FastStream, causing automatic retry based on `retries: 3` configuration without marking the lead as failed.

---

## Scenario 3: Webhook Ingestion & Engagement Feedback Loop
Link to BPMN Workflow: [`06. Webhook Feedback & Engagement Workflow`](apps/frappe_cadence/docs/architecture/bpmn/06-webhook-feedback-and-engagement.md)

### Trigger & Steps
1. External Listmonk engine pushes an HTTP POST request to [`/api/method/frappe_cadence.integrations.listmonk.jobs.webhook.webhook`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/jobs/webhook.py:68).
2. Handler computes HMAC-SHA256 of the raw body against `webhook_secret` and compares it with `Listmonk-Signature`.
3. Valid payloads are parsed in [`process_webhook_payload()`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/jobs/webhook.py:98), matching `Multi Channel Cadence` by `listmonk_subscriber_id` and `listmonk_sequence_id`.
4. Transitions status according to event types:
   - `campaign.started` / `sequence.step_executed` $\rightarrow$ `In Progress`
   - `replied` $\rightarrow$ `Replied` (and triggers [`remove_subscriber_from_sequence()`](apps/frappe_cadence/frappe_cadence/jobs/multi_channel_cadence.py:99))
   - `subscriber.bounced` $\rightarrow$ `Failed`
   - `unsubscribed` / `opted_out` $\rightarrow$ `Opted Out` (and removes subscriber from list)
   - `completed` $\rightarrow$ `Finished`

### Exception Path
- If the signature is invalid or secret mismatches, the request is rejected immediately with `frappe.PermissionError` (HTTP 403) and logged to the Error Log.
