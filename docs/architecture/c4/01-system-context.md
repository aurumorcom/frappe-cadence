# C1: System Context Diagram

## 🎯 System Boundaries
This document defines the high-level system context, primary domain entities, external systems, and user actors interacting with [`frappe_cadence`](apps/frappe_cadence/frappe_cadence/hooks.py:1).

## 📊 Context ERD

```mermaid
erDiagram
    SalesRepresentative ||--o{ Cadence : "manages"
    SalesRepresentative ||--o{ MultiChannelCadence : "executes"
    CRMLead ||--o{ MultiChannelCadence : "enrolled_into"
    Cadence ||--o{ MultiChannelCadence : "instantiates"
    Cadence ||--|| Playbook : "references"
    MultiChannelCadence ||--o| PlaybookExecution : "triggers_enrichment"
    MultiChannelCadence }|--|| ListmonkSubscriberAPI : "synchronizes_lead"
    Cadence }|--|| ListmonkSequenceAPI : "provisions_campaign_list"
    ListmonkWebhookReceiver ||--o{ MultiChannelCadence : "updates_engagement_status"

    SalesRepresentative {
        string user_id PK
        string email
        string full_name
        string role_profile
    }

    CRMLead {
        string lead_id PK
        string first_name
        string email
        string company_name
        string status
        int listmonk_id
    }

    Cadence {
        string cadence_code PK
        string cadence_name
        int enabled
        string assign_condition
        string rule
        int listmonk_id
        string reference_playbook
    }

    MultiChannelCadence {
        string name PK
        string cadence_name FK
        string recipient FK
        string sender FK
        string status
        int listmonk_subscriber_id
        int listmonk_sequence_id
        string playbook_execution FK
    }

    Playbook {
        string name PK
        string playbook_name
        string document_type
        int is_active
    }

    PlaybookExecution {
        string name PK
        string playbook FK
        string multi_channel_cadence FK
        string status
    }

    ListmonkSubscriberAPI {
        string endpoint "/api/subscribers"
        string protocol "HTTPS_JSON"
    }

    ListmonkSequenceAPI {
        string endpoint "/api/lists"
        string protocol "HTTPS_JSON"
    }

    ListmonkWebhookReceiver {
        string endpoint "/api/method/webhook"
        string signature_header "Listmonk-Signature"
    }
```

## 📝 Entity Descriptions

- **SalesRepresentative**: Sales user or manager who configures automated cadences, provides personal bio profiles, and oversees outreach execution.
- **CRMLead**: Prospective client record in Frappe CRM containing demographic, organization, and contact channel details.
- **Cadence**: Template defining outreach campaign strategies, AST-evaluated qualification criteria, sender distribution rules, and attached playbooks.
- **MultiChannelCadence**: Concrete instance of an enrolled lead navigating an active outreach sequence with associated sender profile and progression status.
- **Playbook**: Automated enrichment workflow definition orchestrating contextual research and data gathering tasks.
- **PlaybookExecution**: Runtime tracking document for an executing enrichment run for a specific MultiChannelCadence.
- **ListmonkSubscriberAPI**: External REST endpoint for creating and updating subscriber attributes and list memberships.
- **ListmonkSequenceAPI**: External REST endpoint for provisioning and status management of campaign mailing lists.
- **ListmonkWebhookReceiver**: Inbound webhook handler validating HMAC-SHA256 signatures and recording delivery and engagement updates.
