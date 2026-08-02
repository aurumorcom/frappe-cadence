# Cross-cutting Concepts

## Asynchronous Event Handling
Long-running business processes, particularly those involving external AI APIs and multi-day cadence delays, use an asynchronous, event-driven pattern (`frappe_controller`):
- `wait_for_event(event_key, condition)`: Suspends the execution thread.
- `emit_event(event_key, payload)`: Resumes the thread when the payload satisfies the condition.
This allows high scalability without keeping Python processes blocked on network I/O or sleep timers.

## Idempotency & Fault Tolerance
Background jobs interacting with external services or creating DB records are designed to be idempotent. In `process_schedule()`, the function checks for existing `Communication` records before creating new ones. If a worker dies mid-execution and the job is retried, the system safely resumes without duplicating outbound messages.

## Security & API Key Management
Sensitive API keys (like the Sift API Key) are stored securely using Frappe's `get_password()` mechanism inside the `Sift Settings` Single DocType, preventing accidental exposure in logs or the front-end UI.
