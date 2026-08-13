# Context and Scope

## Business Context
The business context of [`frappe_cadence`](apps/frappe_cadence/frappe_cadence/hooks.py:1) encompasses sales representatives, prospective leads, sales managers, automated research playbooks, and outbound delivery engines.

Link to C1 System Context Model: [`C1 System Context Diagram`](apps/frappe_cadence/docs/architecture/c4/01-system-context.md)

### External Interfaces and Actors
- **Sales Reps & Managers**: Configure outreach cadences, view enrolled leads, and manage personal sender bios.
- **CRM Leads**: Domain aggregate representing target prospects that are automatically enrolled when meeting qualification criteria.
- **Listmonk Outbound Engine**: External delivery microservice responsible for sending sequenced emails, managing delays, tracking bounces, opens, and unsubscribes.
- **Playbook Enrichment Service**: Automated background research process aggregating context and intelligence for target prospects.

## Technical Context

| Interface Channel | Protocol | Format | Security / Authentication | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Desk Web Interface** | HTTPS (Port 443) | HTML / JSON / REST | Frappe Session Cookie / Token | User management of cadences and bio profiles |
| **Listmonk REST API** | HTTPS / HTTP (Port 9000) | JSON | Bearer / API Token | List creation, subscriber upsert, sequence enrollment |
| **Inbound Webhook** | HTTPS / HTTP (Port 8000) | JSON | HMAC-SHA256 (`Listmonk-Signature`) | Ingestion of live campaign engagement events |
| **Task Queue** | Redis Protocol (Port 6379) | Binary / Pickle | Redis Auth | Decoupled background task dispatch |
| **Relational Storage** | MySQL Protocol (Port 3306) | SQL | Database User / Password | Transactional persistence of DocTypes |
