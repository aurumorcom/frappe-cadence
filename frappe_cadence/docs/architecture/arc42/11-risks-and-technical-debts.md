# Risks and Technical Debts

- **Event Key Coupling**: The asynchronous orchestration heavily relies on string-based event keys (`mcc_scheduled`, `callback`, `cadence_step_completed`). A typo or mismatch between the `emit_event` and `wait_for_event` functions results in silent deadlocks.
  - *Mitigation*: Comprehensive integration testing mimicking exact lifecycle states.
- **Provider Vendor Lock-in**: Currently, the system uses a custom hashing mechanism to route to `CadenceProvider`. If a vendor changes their webhook payload structure, the unified `report_event` function may fail to map statuses properly.
  - *Mitigation*: The `report_event` method expects normalized arguments (`event_type`, `context`), forcing the provider-specific integration code (not covered here) to map raw vendor payloads cleanly before invoking `report_event`.
- **Database Connection Limits**: If thousands of cadences awaken simultaneously, the resulting DB writes could exhaust MariaDB connections.
  - *Mitigation*: `process_schedule` uses Frappe's `medium` queue to limit concurrency and throttle throughput natively.
