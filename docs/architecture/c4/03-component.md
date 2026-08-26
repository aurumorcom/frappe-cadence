# C3: Component Diagram

## 🎯 Component Architecture
This document details the internal DocType models, controller components, integration handlers, and relationship cardinalities within [`frappe_listmonk`](apps/frappe_listmonk/frappe_listmonk/hooks.py:1).

## 📊 Component ERD

```mermaid
erDiagram
    Cadence ||--o{ MultiChannelCadence : "generates"
    Cadence ||--o{ UserBio : "overrides_bio"
    CRMLead ||--o{ MultiChannelCadence : "enrolled_as_recipient"
    MultiChannelCadence ||--o| DeepResearch : "context_attached"
    DeepResearch ||--o{ DeepResearchSource : "sources"
    DeepResearchSource }|--|| Source : "references"
    MultiChannelCadence ||--o| PlaybookExecution : "triggers"
    HistoryGroup ||--o{ HistoryGroupHistory : "contains_items"
    HistoryGroupHistory }|--|| History : "references_record"
    ListmonkSettings ||--|| ListmonkClient : "configures"
    MultiChannelCadence }|--|| ListmonkClient : "dispatches_to"
    Cadence }|--|| ListmonkClient : "provisions_via"

    Cadence {
        string name PK
        string cadence_name
        int enabled
        string naming_series
        string cadence_code
        int listmonk_id
        string assign_condition
        string assign_condition_json
        string rule
        string reference_playbook
        string last_user FK
    }

    MultiChannelCadence {
        string name PK
        string cadence_name FK
        string status
        string last_status
        string cadence_for
        string recipient FK
        string sender FK
        int listmonk_subscriber_id
        int listmonk_sequence_id
        string playbook_execution FK
        date start_date
        date end_date
    }

    CRMLead {
        string name PK
        string first_name
        string email
        string email_id
        string company_name
        string status
        int listmonk_id
        string enrichment_status FK
        string location
    }

    UserBio {
        string name PK
        int enabled
        int is_default
        string reference_user FK
        string reference_cadence FK
        string content
    }

    DeepResearch {
        string name PK
        string reference_doctype
        string reference_doc
        string rule FK
        string summary
    }

    DeepResearchSource {
        string name PK
        string parent FK
        string source FK
        string reference_doctype
        string reference_name
        string url
    }

    Source {
        string name PK
        string reference_doctype
        string reference_name
        string url
    }

    History {
        string name PK
        string url
        string markdown
        string screenshot
        string html
        string reference_doctype
        string reference_doc
    }

    HistoryGroup {
        string name PK
        string url
        string reference_doctype
        string reference_doc
    }

    HistoryGroupHistory {
        string name PK
        string parent FK
        string history FK
    }

    PlaybookExecution {
        string name PK
        string playbook FK
        string multi_channel_cadence FK
        string status
    }

    ListmonkSettings {
        string name PK
        string base_url
        string access_token
        string webhook_secret
        string status
        int enabled
    }

    ListmonkClient {
        string base_url
        string token
        int timeout
    }
```

## 📝 Component Descriptions

- **Cadence**: Core configuration DocType containing condition definitions, assignment strategy (Round Robin vs Load Balancing), and sequence metadata.
- **MultiChannelCadence**: State-machine managing document tracking each prospect's lifecycle from `Draft` through `Enriching`, `Provisioning`, `Scheduled`, `In Progress`, and terminal states (`Replied`, `Finished`, `Opted Out`, `Failed`).
- **CRMLead**: Lead record representing the prospect, carrying demographic data, enrichment flags, and Listmonk subscriber ID pointers.
- **UserBio**: Personalization profile providing sender identity bios customized per sales rep and specific outreach cadence.
- **DeepResearch**: Structured dossier and AI research summary collected during playbook enrichment, attached with source references.
- **DeepResearchSource**: Child table linking research source records and reference URLs to a DeepResearch document.
- **Source**: Standalone reference DocType storing web source URLs and linked entity metadata.
- **History**: Granular log of crawled web pages, markdown content, and screenshot attachments associated with CRM documents.
- **HistoryGroup**: Aggregate container bundling multiple history items for a target URL.
- **HistoryGroupHistory**: Child table joining history items into a HistoryGroup.
- **PlaybookExecution**: Background runner orchestrating multi-step research and intelligence gathering before outreach dispatch.
- **ListmonkSettings**: Single DocType configuring API authentication tokens, base URLs, and automated webhook subscriptions for Listmonk.
- **ListmonkClient**: Dedicated HTTP communication wrapper exposing typed methods for managing subscribers, sequences, campaigns, and webhooks.
