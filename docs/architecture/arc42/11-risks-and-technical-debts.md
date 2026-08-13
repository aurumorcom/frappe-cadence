# Risks and Technical Debts

- **Event Key Coupling**: The asynchronous orchestration heavily relies on string-based event keys (`mcc_scheduled`, `callback`, `cadence_step_completed`). A typo or mismatch between the `emit_event` and `wait_for_event` functions results in silent deadlocks.
  - *Mitigation*: Comprehensive integration testing mimicking exact lifecycle states.
- **Database Connection Limits**: If thousands of cadences awaken simultaneously, the resulting DB writes could exhaust MariaDB connections.
  - *Mitigation*: `process_schedule` uses Frappe's `medium` queue to limit concurrency and throttle throughput natively.
