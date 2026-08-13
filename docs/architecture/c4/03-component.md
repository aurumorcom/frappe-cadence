# C3: Component Diagram

## 🎯 Component Architecture
This document defines the C3 Component model for the `frappe_cadence` application, breaking down the internal modules and controllers.

## 📊 Component ERD

```mermaid
erDiagram
    Cadence ||--o{ CadenceMultiChannelSchedule : "contains_step_schedules"
    Cadence ||--o{ MultiChannelCadence : "instantiates_lead_execution"
    MultiChannelCadence ||--o{ Communication : "dispatches_step_communications"
    UserBio }|..|| User : "belongs_to_sender"
    UserBio }|..|| Cadence : "scoped_to_cadence"
    EmailTemplate ||--o{ EmailTemplateAnnotation : "has_ai_annotations"
    SMSTemplate ||--o{ SMSTemplateAnnotation : "has_ai_annotations"
    LinkedInTemplate ||--o{ LinkedInTemplateAnnotation : "has_ai_annotations"
    WhatsAppTemplate ||--o{ WhatsAppTemplateAnnotation : "has_ai_annotations"
    HistoryGroup ||--o{ HistoryGroupHistory : "groups_history_logs"
    History }|..|| CRMLead : "tracks_prospect_history"
    SiftAPI ||--|| SiftSettings : "loads_api_credentials"

    Cadence {
        string cadence_code PK
        string cadence_name
        string rule
        string assign_condition
    }

    CadenceMultiChannelSchedule {
        string name PK
        string parent FK
        string channel
        int step_number
        int delay_days
    }

    MultiChannelCadence {
        string name PK
        string cadence_name FK
        string recipient
        string status
    }

    Communication {
        string name PK
        string delivery_status
        string status
    }

    UserBio {
        string name PK
        string reference_user FK
        string content
    }

    EmailTemplate {
        string name PK
        string subject
        string response
        string sift_id
    }

    SMSTemplate {
        string name PK
        string message
        string sift_id
    }

    LinkedInTemplate {
        string name PK
        string message
        string sift_id
    }

    WhatsAppTemplate {
        string name PK
        string message
        string sift_id
    }

    HistoryGroup {
        string name PK
    }

    HistoryGroupHistory {
        string name PK
        string parent FK
    }

    History {
        string name PK
        string reference_doctype
        string reference_name
    }

    SiftSettings {
        string name PK
        string sift_base_url
    }

    SiftAPI {
        string endpoint_url
    }

    User {
        string name PK
    }

    CRMLead {
        string name PK
    }
```

## 📝 Component Descriptions
- **Cadence**: Master orchestration DocType tracking schedules, assignment rules, and linked playbook executions.
- **CadenceMultiChannelSchedule**: Child table specifying individual channel steps (Email, SMS, etc.) and delay intervals.
- **MultiChannelCadence**: Active execution tracking for a specific `CRMLead`, managing state from `Provisioning` to `Completed` or `Error`.
- **UserBio**: Sender's personal bio injected into Sift API prompts for personalized messaging.
- **Communication**: Standard Frappe DocType used to track outgoing messages and delivery statuses.
- **EmailTemplate**, **SMSTemplate**, etc.: Channel-specific templates holding the base prompt or static message, and the `sift_id` AI model reference.
- **History**, **HistoryGroup**: Entities for tracking the chronological sequence of events and engagement.
- **SiftSettings**: Single DocType securely storing Sift API keys and base URLs.
