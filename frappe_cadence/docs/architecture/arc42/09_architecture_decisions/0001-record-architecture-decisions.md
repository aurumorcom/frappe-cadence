# 0001 Baseline Architectural Decisions

## Context

`frappe_cadence` provides automated multi-channel sales engagement capabilities for Frappe CRM ([`apps/frappe_cadence/frappe_cadence/hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:1)).

## Decisions

1. **Framework Integration Strategy**:
   - Utilize standard Frappe `doc_events` in [`hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:139) to listen for CRM Lead, Cadence, Communication, Playbook Execution, and Template updates.
2. **Background Job Queueing**:
   - Manage all cadence step executions, lead evaluations, and provider re-allocations asynchronously via Redis worker queues configured with rate limits in `controller_events`.
3. **C4 & BPMN Architectural Documentation Standard**:
   - Maintain structural documentation strictly using Mermaid `erDiagram` in `c4/` and behavioral workflows using Mermaid `flowchart` per trigger under `bpmn/`.

## Consequences

- **Positive**:
  - Prevents UI blocking during high-volume sales outreach.
  - Ensures full testability and architectural clarity across multi-channel outreach workflows.
- **Negative**:
  - Requires Redis background worker availability for cadence execution and webhook processing.
