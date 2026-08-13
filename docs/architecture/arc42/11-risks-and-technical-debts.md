# Risks and Technical Debts

## Identified Risks and Single Points of Failure

| Risk ID | Description | Impact | Probability | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **RISK-01** | External Listmonk dependency unavailability halts new outreach scheduling. | High | Medium | FastStream queue retry policies (`retries: 3`) and alert triggers on queue depth spikes. |
| **RISK-02** | Webhook secret desynchronization causes all incoming webhooks to fail signature validation. | High | Low | Automated webhook setup script in [`setup_webhook()`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/jobs/webhook.py:21) re-synchronizing secrets upon credentials update. |
| **RISK-03** | Large batch evaluation (>50,000 leads) blocking queue workers. | Medium | Medium | Lead chunking (100 records per job) via `as_child=True` in [`evaluate_leads_for_cadence()`](apps/frappe_cadence/frappe_cadence/jobs/cadence.py:67). |

## Technical Debts

1. **Schema Coupling**: The app expects certain custom fields on `CRM Lead` (e.g. `listmonk_id`, `enrichment_status`) that must be synced via fixtures in [`custom_field.json`](apps/frappe_cadence/frappe_cadence/fixtures/custom_field.json:1).
2. **Listmonk Contact Deletion Synchronization**: When a lead is deleted in Frappe, [`delete_contact()`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/jobs/contact.py:53) removes the subscriber in Listmonk; network failures during delete hooks need reconciliation scripts.
3. **Synchronous Webhook Ingestion**: Webhook handler directly processes status changes during the HTTP request lifecycle; under extreme burst volume, incoming webhooks should be buffered directly to Redis before DB write.
