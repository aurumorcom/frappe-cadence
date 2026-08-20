# C2: Container Diagram

## 🎯 Container Architecture
This document defines the runnable runtime containers, data stores, background brokers, workers, and external service containers for [`frappe_cadence`](apps/frappe_cadence/frappe_cadence/hooks.py:1).

## 📊 Container ERD

```mermaid
erDiagram
    BrowserFrontend ||--|| Nginx : "HTTPS / Port 443"
    Nginx ||--|| Gunicorn : "WSGI Proxy / Port 8000"
    Gunicorn ||--|| MariaDB : "SQL / Port 3306"
    Gunicorn ||--o{ RedisBroker : "Enqueue Jobs / Port 6379"
    FastStreamWorker }|--|| RedisBroker : "Consumes Tasks"
    FastStreamWorker ||--|| MariaDB : "SQL / State Transitions"
    FastStreamWorker }|--|| ListmonkSubscriberAPI : "REST / Port 9000"
    FastStreamWorker }|--|| ListmonkSequenceAPI : "REST / Port 9000"
    ListmonkEngine ||--|| Gunicorn : "Webhook POST / Port 8000"

    BrowserFrontend {
        string technology "Frappe Desk SPA / Vue 3"
        string client "Chrome / Firefox / Edge"
    }

    Nginx {
        string type "Reverse Proxy & TLS Termination"
        int port 443
    }

    Gunicorn {
        string runtime "Python 3.14 / Frappe WSGI"
        int port 8000
    }

    MariaDB {
        string engine "MariaDB 10.11 / InnoDB"
        int port 3306
    }

    RedisBroker {
        string type "Redis 7 / Message Broker"
        int port 6379
    }

    FastStreamWorker {
        string runner "Frappe Controller / FastStream"
        string concurrency "Multi-Threaded Worker"
    }

    ListmonkEngine {
        string runtime "Go Service / Listmonk 3+"
        int port 9000
    }

    ListmonkSubscriberAPI {
        string external_endpoint "api.listmonk.app/api/subscribers"
    }

    ListmonkSequenceAPI {
        string external_endpoint "api.listmonk.app/api/lists"
    }
```

## 📝 Container Descriptions

- **BrowserFrontend**: User interface for sales managers and reps to author cadences, monitor enrollments, and view outreach analytics.
- **Nginx**: Edge proxy server managing TLS termination, asset caching, and routing requests to the WSGI backend.
- **Gunicorn**: Primary Frappe web server handling HTTP API routes, desk UI views, document transactions, and webhook ingestion.
- **MariaDB**: Relational transactional database storing DocType records, relational schemas, user bios, contexts, and engagement histories.
- **RedisBroker**: In-memory message broker coordinating background task queues and `frappe_controller` execution streams.
- **FastStreamWorker**: Asynchronous background worker executing decoupled tasks including lead qualification, cadence batching, and Listmonk synchronization.
- **ListmonkEngine**: Standalone external cold outreach and email newsletter engine executing multi-step sequences, intervals, and sending pipelines.
- **ListmonkSubscriberAPI**: REST interface of Listmonk handling subscriber creation, attribute synchronization, and metadata updates.
- **ListmonkSequenceAPI**: REST interface of Listmonk managing list creation, status toggles, and subscriber list attachments.
