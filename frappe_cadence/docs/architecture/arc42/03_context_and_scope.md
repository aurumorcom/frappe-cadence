# 03 Context and Scope

This document defines the system context and organizational boundaries for [`apps/frappe_cadence/frappe_cadence/hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:1).

## System Context Diagram

For complete system boundaries and entity definitions, see the [C1 System Context Model](../c4/01-context.md).

```mermaid
erDiagram
    frappe__core__doctype__user__user ||--o{ frappe_cadence__cadence__doctype__cadence__cadence : "configures_and_manages"
    frappe__core__doctype__user__user ||--o{ frappe_cadence__cadence__doctype__user_bio__user_bio : "maintains_personal_bio"
    frappe_crm__doctype__crm_lead__crm_lead ||--o{ frappe_cadence__cadence__doctype__multi_channel_cadence__multi_channel_cadence : "enrolled_in_outreach_sequence"
    frappe_cadence__cadence__doctype__cadence__cadence ||--o{ frappe_cadence__cadence__doctype__multi_channel_cadence__multi_channel_cadence : "instantiates_lead_sequences"
    frappe_cadence__cadence__doctype__multi_channel_cadence__multi_channel_cadence ||--o{ frappe_cadence__cadence__doctype__cadence_provider__cadence_provider : "routes_channel_delivery"
    frappe_cadence__cadence__doctype__multi_channel_cadence__multi_channel_cadence ||--o{ ExternalSystem__Sift_AI_API : "requests_prompt_personalization"
    frappe_cadence__cadence__doctype__cadence_provider__cadence_provider ||--o{ ExternalSystem__Channel_Delivery_Providers : "dispatches_email_sms_linkedin_whatsapp"
    ExternalSystem__Channel_Delivery_Providers ||--o{ frappe_crm__doctype__crm_lead__crm_lead : "delivers_messages_and_tracks_engagement"
    ExternalSystem__Channel_Delivery_Providers ||--o{ frappe_cadence__cadence__doctype__communication__communication : "reports_delivery_and_reply_webhooks"
```

## Boundary & Scope Definitions

- **Internal Boundaries**:
  - `frappe_cadence` manages Cadences, Multi Channel Cadences, Templates, Provider Channels, User Bios, and Communication history.
  - Interacts with `crm` app to read lead details and update lead cadence references.
  - Interacts with `frappe_playbook` to manage sales playbook execution lifecycles.
- **External Interfaces**:
  - **Sift AI API**: Transmits prompt optimization payloads and receives webhook callbacks with AI scores and suggestions ([`apps/frappe_cadence/frappe_cadence/integrations/sift.py`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:4)).
  - **Channel Delivery Gateways**: External provider services (SMTP/SendGrid, Twilio, LinkedIn, WhatsApp) handling actual message dispatch and engagement webhook reporting ([`apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py:53)).
