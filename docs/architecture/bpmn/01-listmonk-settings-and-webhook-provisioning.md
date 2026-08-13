# Behavioral Workflows (BPMN): Listmonk Settings & Webhook Provisioning

## 🎯 Primary Workflow: Settings Authorization & Webhook Provisioning Workflow

```mermaid
flowchart TD
    StartSettings([Save Listmonk Settings]) --> StripBaseUrl[Validate & Strip Base URL Trailing Slashes]
    StripBaseUrl --> CheckEnabled{Is Enabled Checked?}
    
    CheckEnabled -- No --> SetDisabled[Set status = 'Disabled']
    CheckEnabled -- Yes --> CheckCreds{Base URL & Access Token Present?}
    
    CheckCreds -- No --> SetUnauthorized[Set status = 'Unauthorized']
    CheckCreds -- Yes --> TestConn[Execute ListmonkClient.test_connection]
    
    TestConn --> ConnResult{Connection Successful / HTTP 200?}
    ConnResult -- No / Exception --> SetUnauthorized
    ConnResult -- Yes --> SetAuthorized[Set status = 'Authorized']
    
    SetAuthorized --> EnqueueWebhook[Enqueue setup_webhook Task]
    EnqueueWebhook --> FetchWebhooks[ListmonkClient.get_webhooks]
    FetchWebhooks --> WebhookExists{Webhook for Site URL Exists?}
    
    WebhookExists -- Yes --> UpdateWebhook[Update Webhook: Events & HMAC Secret]
    WebhookExists -- No --> CreateWebhook[Create Webhook: Events & HMAC Secret]
    
    UpdateWebhook --> ProvisionComplete([Settings & Webhook Provisioned - End])
    CreateWebhook --> ProvisionComplete
    SetDisabled --> End([End Workflow])
    SetUnauthorized --> End
```

## 📝 Workflow Step Descriptions

1. **Save Listmonk Settings**: Triggered via Desk UI when [`Listmonk Settings`](apps/frappe_cadence/frappe_cadence/cadence/doctype/listmonk_settings/listmonk_settings.py:8) is inserted or updated.
2. **URL Validation**: [`ListmonkSettings.validate()`](apps/frappe_cadence/frappe_cadence/cadence/doctype/listmonk_settings/listmonk_settings.py:9) strips trailing slashes from the API base URL.
3. **Enabled Check**: If `enabled = 0`, sets `status = 'Disabled'`.
4. **Credential Verification**: Ensures both `base_url` and `access_token` exist in settings or `site_config.json`.
5. **Connection Test**: Executes [`ListmonkClient.test_connection()`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/client.py:140) against `/api/sequences`.
6. **Authorization State**: If valid, updates `status = 'Authorized'`.
7. **Automated Webhook Setup**: Enqueues [`setup_webhook()`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/jobs/webhook.py:21) which provisions or updates the site's webhook subscription in Listmonk with HMAC secret authentication.
