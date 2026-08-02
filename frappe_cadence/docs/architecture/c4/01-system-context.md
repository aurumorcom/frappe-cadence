# C1: System Context Diagram

## 🎯 System Boundaries
This document defines the C1 System Context and external boundaries for the `frappe_cadence` application.

## 📊 Context ERD

```mermaid
erDiagram
    User ||--o{ Cadence : "configures_and_manages"
    User ||--o{ UserBio : "maintains_personal_bio"
    CRMLead ||--o{ MultiChannelCadence : "enrolled_in_outreach_sequence"
    Cadence ||--o{ MultiChannelCadence : "instantiates_lead_sequences"
    MultiChannelCadence ||--o{ CadenceProvider : "routes_channel_delivery"
    MultiChannelCadence ||--o{ SiftAPI : "requests_prompt_personalization"
    CadenceProvider ||--o{ ChannelDeliveryProviders : "dispatches_email_sms_linkedin_whatsapp"
    ChannelDeliveryProviders ||--o{ CRMLead : "delivers_messages_and_tracks_engagement"
    ChannelDeliveryProviders ||--o{ Communication : "reports_delivery_and_reply_webhooks"

    User {
        string name PK
        string full_name
        string email
    }

    Cadence {
        string cadence_code PK
        string cadence_name
        string rule
    }

    UserBio {
        string name PK
        string reference_user FK
        string reference_cadence FK
        string content
    }

    CRMLead {
        string name PK
        string first_name
        string last_name
        string email_id
    }

    MultiChannelCadence {
        string name PK
        string cadence_name FK
        string recipient FK
        string sender FK
        string status
    }

    CadenceProvider {
        string name PK
        string provider_name
        int priority
    }

    Communication {
        string name PK
        string communication_medium
        string reference_doctype
        string reference_name FK
        string delivery_status
    }

    SiftAPI {
        string endpoint_url
    }

    ChannelDeliveryProviders {
        string provider_name
    }
```

## 📝 Entity Descriptions
- **User**: Sales representative, account executive, or system administrator operating the CRM desk.
- **Cadence**: Master multi-step sales cadence template defining triggers, steps, rules, and user pools.
- **UserBio**: Personal sender bio and background context used by Sift API during template optimization.
- **CRMLead**: Target prospect record containing lead attributes, assignment tags, and cadence references.
- **MultiChannelCadence**: Active execution instance tracking a specific lead's progression through cadence schedule steps.
- **CadenceProvider**: Integrated multi-channel provider configuration with router weights.
- **Communication**: System communication record logging dispatched outreach messages and engagement status.
- **SiftAPI**: External Sift optimization and prediction API service.
- **ChannelDeliveryProviders**: Third-party outreach channels (e.g. SendGrid, Twilio, LinkedIn, WhatsApp).
