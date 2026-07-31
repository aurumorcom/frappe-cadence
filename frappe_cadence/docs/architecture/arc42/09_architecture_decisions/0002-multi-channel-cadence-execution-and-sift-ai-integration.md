# 0002 Multi-Channel Cadence Execution and Sift AI Integration

## Context

Multi-channel outreach requires coordinating email, SMS, LinkedIn, and WhatsApp channels while leveraging external Sift AI services for personalized content optimization without creating thread blocking or race conditions ([`apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:161)).

## Decisions

1. **Provider Router & Snapshotting**:
   - Dynamic channel provider assignment using priority ranking in [`resolve_providers_for_mcc`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py:104), snapshotting provider choices onto individual `Multi Channel Cadence` records.
2. **Asynchronous Sift AI Webhook Pattern**:
   - Sift AI optimization and prediction calls (`sift.optimize`, `sift.predict`) are sent via POST webhooks, and results are returned asynchronously via whitelisted callback endpoints ([`sift.py`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:4)).
3. **Reactive Step Queue Suspension (`wait_for_event`)**:
   - Step scheduling jobs (`process_schedule`) pause via `wait_for_event()` when waiting for prerequisites (template enablement, Sift callbacks, user bio creation) and automatically resume when corresponding events are emitted.

## Consequences

- **Positive**:
  - Resilient to Sift AI latency or transient vendor downtime.
  - Multi-channel delivery configurations can evolve without breaking active outreach instances.
- **Negative**:
  - Requires maintaining event-driven state transitions and callback signature verifications.
