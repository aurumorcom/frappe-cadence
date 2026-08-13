# Deployment View

## Infrastructure Level 1

```mermaid
graph TD
    subgraph HostServer["Host Server / Cloud Cluster (Docker / Kubernetes)"]
        subgraph IngressLayer["Edge & Reverse Proxy"]
            NginxNode["Nginx Ingress (Port 80/443)"]
        end

        subgraph ApplicationLayer["Frappe Bench Cluster"]
            GunicornNode["Gunicorn WSGI Workers (Port 8000)"]
            FastStreamNode["FastStream Background Workers"]
            ScheduleWorkerNode["Frappe Scheduler"]
        end

        subgraph DataLayer["Persistence & Caching"]
            MariaDBNode[("MariaDB Primary (Port 3306)")]
            RedisQueueNode[("Redis Message Broker (Port 6379)")]
            RedisCacheNode[("Redis Cache (Port 6379)")]
        end

        subgraph ExternalMicroservices["Outreach Infrastructure"]
            ListmonkNode["Listmonk Outreach Engine (Port 9000)"]
            PostgreSQLNode[("PostgreSQL for Listmonk (Port 5432)")]
        end
    end

    ClientDevice["Client Browser / Webhook Sender"] -->|HTTPS| NginxNode
    NginxNode -->|Reverse Proxy| GunicornNode
    GunicornNode -->|TCP / SQL| MariaDBNode
    GunicornNode -->|TCP / Redis| RedisQueueNode
    FastStreamNode -->|Consume / Defer| RedisQueueNode
    FastStreamNode -->|State Persistence| MariaDBNode
    ScheduleWorkerNode -->|Cron Enqueue| RedisQueueNode
    FastStreamNode -->|REST API HTTP/S| ListmonkNode
    ListmonkNode -->|Webhook HTTP/S| NginxNode
    ListmonkNode -->|SQL| PostgreSQLNode
```

### Motivation
A containerized multi-tier deployment ensures strict physical separation between the synchronous user request thread pool (Gunicorn), long-running asynchronous worker queues (FastStream), persistent transactional data (MariaDB), and the standalone cold email engine (Listmonk).

### Quality and/or Performance Features
- **Zero UI Blocking**: Time-consuming external API calls and qualification scans are isolated on FastStream worker nodes.
- **Independent Elasticity**: Background workers can scale horizontally based on queue depth metrics in Redis.
- **Fail-Safe Webhook Gateway**: Inbound webhooks pass through Nginx SSL termination before reaching Gunicorn.

### Mapping of Building Blocks to Infrastructure

| Building Block | Target Node / Container | Ports | Protocols |
| :--- | :--- | :--- | :--- |
| **Desk UI / Web API** | `Gunicorn WSGI Container` | 8000 | HTTP / WSGI |
| **Queue Workers** | `FastStream Worker Container` | - | Redis TCP |
| **Scheduler** | `Frappe Scheduler Container` | - | Redis TCP |
| **DocType Database** | `MariaDB Container` | 3306 | MySQL Protocol |
| **Message Broker** | `Redis Queue Container` | 6379 | RESP Protocol |
| **Email Sequence Engine** | `Listmonk Service Container` | 9000 | HTTP / REST |

## Infrastructure Level 2
- **Environment Configuration**: Listmonk credentials and secrets configured via `sites/<site>/site_config.json` or encrypted inside [`Listmonk Settings`](apps/frappe_cadence/frappe_cadence/cadence/doctype/listmonk_settings/listmonk_settings.py:8).
- **Network Isolation**: All backend containers communicate within an internal Docker bridge network, exposing only ports 80/443 publicly via Nginx.
