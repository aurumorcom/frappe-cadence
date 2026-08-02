# ADR 0003: Multi-Channel Cadence Lifecycle Fixes

## Status
Accepted

## Date
2026-08-02

## Context
During an architectural audit of the `frappe_cadence` module against the BPMN specifications, several critical lifecycle breaks were identified. Specifically, background worker threads hanging indefinitely when external Sift AI callbacks failed, invalid state transitions when handling external provider engagement webhooks, and `PlaybookExecution` sync mismatch when initializing a `Multi Channel Cadence` in the `Provisioning` state. These issues led to silent job failures and memory leaks in the Redis worker pool.

## Decision
We implemented a strict, unified event-driven state machine for `Multi Channel Cadence` execution:
1. **Provisioning State Lock**: The `Multi Channel Cadence` is explicitly created in the `"Provisioning"` state and exclusively transitions to `"Draft"` when `playbook_execution.py:on_update` receives a `"success"` event, or `"Error"` on failure.
2. **Terminal State Propagation**: The `report_event` webhook receiver maps external provider engagement events to strict allowed statuses (`"Completed"`, `"Error"`, `"Unsubscribed"`) and emits corresponding `emit_event()` signals to gracefully terminate any suspended orchestration threads waiting on `process_schedule`.
3. **Graceful Callback Degradation**: All Sift AI callback handlers (`email_template.py`, etc.) now capture `.failed` payload types, immediately update the `Communication` record to `"Failed"`, and emit a `"callback"` event to unblock the worker thread rather than hanging indefinitely.
4. **Contextual Bio Injection**: The `get_user_bio` function was corrected to query based on `mcc.sender` (the assigned sales rep) and `mcc.cadence_name` (the internal Cadence ID) to ensure the AI receives the correct personalized context.

## Consequences
### Positive
- Redis worker threads no longer hang indefinitely on AI failures or terminal cadence states.
- The lifecycle from `Provisioning` to `Draft` accurately mirrors the BPMN flow, preventing race conditions.
- Strict mapping of external webhook events ensures database state integrity.

### Negative & Risks
- Tighter coupling to the `frappe_controller` event system; any refactor to `emit_event` or `wait_for_event` will break the state machine.
- Mitigation strategy: All lifecycle transitions are heavily covered by integration tests mimicking the exact file paths.
