# Deployment View

## Infrastructure Level 1
The deployment topology consists of a standard Frappe bench deployment, typically containerized via Docker or managed on a VPS.

```text
[ Nginx Reverse Proxy ] -> [ Gunicorn WSGI ] -> (Python App)
                            |-> [ Redis Queue ] -> [ RQ Workers ]
                            |-> [ MariaDB ]
```

### Motivation
Standardizing on the Frappe framework's default deployment model ensures compatibility with the `frappe_bench` CLI, easy upgrades, and predictable scaling using horizontal worker nodes.

### Quality and/or Performance Features
- **Availability**: Web and worker nodes can be scaled independently.
- **Isolation**: Heavy cadence processing (`process_schedule`) runs on background workers, preventing web UI latency spikes.

### Mapping of Building Blocks to Infrastructure
- **Frappe WSGI App**: Runs on the web container/server.
- **Background Worker Pool**: Runs on dedicated worker containers/servers connecting to Redis.
- **MariaDB Database**: Runs on a dedicated database host or managed service (e.g., RDS).

## Infrastructure Level 2
- **Redis Queue Configuration**: Cadence processing uses Frappe's `medium` and `low` queues, isolating high-priority user-facing web events from long-running sales sequences.
