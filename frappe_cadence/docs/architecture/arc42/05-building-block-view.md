# Building Block View

## Whitebox Overall System
[C2 Container Diagram](../c4/02-container.md)

### Contained Building Blocks
- **Frappe WSGI App**: The Python runtime handling requests and business logic.
- **MariaDB Database**: Relational storage for application state.
- **Background Worker Pool**: Redis-backed executors for the asynchronous orchestration.

### Important Interfaces
- **Sift API HTTP Interface**: REST endpoints for prompt optimization and webhook ingestion.
- **Provider Gateway Interface**: Abstraction layer allowing multiple email/SMS/LinkedIn vendors.

## Level 2
[C3 Component Diagram](../c4/03-component.md)

## Level 3
The internal logic of `MultiChannelCadence.process_schedule()` forms the most complex Level 3 block, handling:
1. **State Evaluation**: Determining if the cadence is active, paused, or terminal.
2. **Dependency Checking**: Ensuring previous sequence steps are completed.
3. **Idempotency Locks**: Checking `Communication` records to prevent double-dispatch.
4. **Content Resolution**: Evaluating if the template requires static insertion or dynamic AI prompting.
5. **Event Suspension**: Yielding the thread (`wait_for_event`) until asynchronous preconditions are met.
