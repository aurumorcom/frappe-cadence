# Solution Strategy

The core architectural solution strategy revolves around an event-driven, asynchronous orchestration engine built on top of the synchronous Frappe framework.

- **Asynchronous Execution (`frappe_controller`)**: Long-running sequences are broken down into discrete steps. Workers sleep using `wait_for_event()` and are awakened via `emit_event()` when pre-requisites (like previous steps or AI callbacks) complete.
- **AI Personalization Layer**: Templates designated as `Prompt` delegate content generation to the Sift AI API, incorporating the sender's bio and the prospect's interaction history to maximize relevance.
- **Idempotent Step Execution**: If a background worker is killed or a server restarts, the `process_schedule` function evaluates current persistent state (e.g., checking if a `Communication` record already exists) before re-executing logic, preventing duplicate outbound messages.
