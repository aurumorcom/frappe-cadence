# Architecture Constraints

- **Frappe Framework Dependency**: The system must operate entirely within the Frappe WSGI ecosystem, utilizing `frappe_controller` for event handling and `frappe` standard DocType structures for persistence.
- **Asynchronous Processing**: Orchestration must not block the main web thread. It strictly uses Frappe's Redis-backed background worker queues and an asynchronous event mechanism (`emit_event`, `wait_for_event`).
- **External AI Integration Constraints**: The application depends on an external Sift AI API for prompt optimization. It must handle network timeouts, rate limiting, and webhook callback failures defensively to prevent hanging processes.
- **Data Privacy & GDPR**: Communication history and user bios sent to external APIs must conform to organizational privacy policies, ensuring sensitive lead data is handled securely.
- **Idempotency**: Scheduled job processors (`process_schedule`) must be fully idempotent, safely resuming from the correct execution point if interrupted by server restarts or deployment cycles.
