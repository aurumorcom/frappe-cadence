# 01 Introduction and Goals

`frappe_cadence` is an open-source cold outreach and sales engagement automation application for the Frappe Framework ([`apps/frappe_cadence/frappe_cadence/hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:1)).

## Requirements Overview

The application automates multi-channel sales engagement sequences (Email, SMS, LinkedIn, WhatsApp), integrates with Sift AI for automated template optimization and prediction, manages sender load-balancing and round-robin assignment, and handles real-time engagement tracking.

### Key Functional Requirements
- **Automated Lead Enrollment & Evaluation**: Dynamic Python AST condition parsing (`assign_condition`) evaluating incoming leads against target cadences ([`apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:52)).
- **Sender Allocation & Load Balancing**: Automatic sender determination supporting `Round Robin` and `Load Balancing` across sales team members ([`determine_sender`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:272)).
- **Multi-Channel Step Scheduling**: Flexible step schedule definition supporting Email, SMS, LinkedIn, and WhatsApp channels with customizable delay offsets ([`process_schedule`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:161)).
- **Sift AI Personalization**: Asynchronous Sift AI engine integration for template optimization, prompt predictions, and structured multi-modal content generation ([`apps/frappe_cadence/frappe_cadence/integrations/sift.py`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:4)).
- **Sender Bio Contextualization**: Granular user bio management with privacy validation and event-driven step queue wake-up ([`apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py:5)).
- **Dynamic Provider Routing**: Multi-channel provider router assigning and snapshotting delivery providers per active cadence instance ([`apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py:104)).

## Quality Goals

| Quality Goal | Motivation / Scenario | Target Metric |
| :--- | :--- | :--- |
| **Reliability** | Ensure cadence execution steps withstand transient external API downtime or delayed provider webhooks. | Event-driven event listeners (`wait_for_event`) and background job retries managed by `controller_events` ([`apps/frappe_cadence/frappe_cadence/hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:182)). |
| **Data Privacy & Security** | Protect sender bios and AI annotations from unauthorized cross-user access. | Strict permission evaluation in [`UserBio.has_permission`](apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py:11) enforcing owner and administrator restrictions. |
| **Scalability & Performance** | Handle high lead volumes without blocking the web application server. | Background worker pool queue offloading with rate-limiting (50/min for `process_schedule`) and Redis caching for AI predictions. |

## Stakeholders

| Role | Expectation |
| :--- | :--- |
| **Sales Representatives** | Automated multi-channel outreach execution with AI-personalized messaging. |
| **Sales Managers & Operations** | Balanced workload distribution across representatives and unified engagement tracking. |
| **System Engineers** | Fault-tolerant queue management, non-blocking AI callbacks, and predictable provider routing. |
