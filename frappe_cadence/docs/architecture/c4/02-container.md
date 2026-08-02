# C2: Container Diagram

## 🎯 Container Architecture
This document defines the runnable services, databases, queues, and external API integrations for the `frappe_cadence` application.

## 📊 Container ERD

```mermaid
erDiagram
    FrappeDeskUI ||--|| FrappeWSGIApp : "HTTPS / JSON"
    FrappeWSGIApp ||--|| MariaDBDatabase : "SQL"
    FrappeWSGIApp ||--o{ BackgroundWorkerPool : "Redis / RQ"
    BackgroundWorkerPool }|--|| MariaDBDatabase : "reads_and_writes"
    BackgroundWorkerPool }|--|| SiftService : "HTTPS / REST"
    BackgroundWorkerPool }|--|| ExternalChannelGateways : "HTTPS / REST / SMTP"
    SiftService ||--o{ FrappeWSGIApp : "Webhooks"
    ExternalChannelGateways ||--o{ FrappeWSGIApp : "Webhooks"

    FrappeDeskUI {
        string type "Web Browser / SPA"
        string framework "Frappe JS"
    }

    FrappeWSGIApp {
        string runtime "Python 3 / Gunicorn"
        string framework "Frappe Framework"
    }

    MariaDBDatabase {
        string engine "MariaDB / InnoDB"
        string storage "Persistent Volume"
    }

    BackgroundWorkerPool {
        string broker "Redis"
        string runner "Frappe RQ Worker"
    }

    SiftService {
        string external_endpoint "Sift AI API"
    }

    ExternalChannelGateways {
        string external_endpoint "Vendor APIs (Twilio, SendGrid, etc.)"
    }
```

## 📝 Container Descriptions
- **FrappeDeskUI**: User-facing web application serving the interactive UI for managing Cadences, Templates, and Analytics.
- **FrappeWSGIApp**: Core backend API handling business logic, whitelisted endpoints, and inbound webhooks.
- **MariaDBDatabase**: Primary transactional datastore for domain aggregates (`Cadence`, `Multi Channel Cadence`, `Communication`, etc.).
- **BackgroundWorkerPool**: Message broker and background workers managing asynchronous job execution (`process_schedule`, assignments).
- **SiftService**: External AI service providing prompt personalization and optimization.
- **ExternalChannelGateways**: External third-party APIs for dispatching emails, SMS, LinkedIn messages, and WhatsApp.
