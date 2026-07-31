# 04 Solution Strategy

This document outlines the core architectural and technical strategies driving [`apps/frappe_cadence/frappe_cadence/hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:1).

## Key Architectural Decisions

1. **AST Condition Engine & Automatic Enrollment**:
   - Cadence assignment rules (`assign_condition`) are written as Python expressions and compiled down into structured SQL filters via [`_ast_to_filters`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:67). This eliminates manual lead assignment and enables safe SQL execution.
2. **Provider-Agnostic Channel Routing & Snapshotting**:
   - `MultiChannelCadence` (MCC) records do not hardcode vendor APIs. Instead, [`resolve_providers_for_mcc`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py:104) dynamically selects providers for each active channel based on priority weights, storing a snapshot in the `MCC Cadence Provider` child table.
3. **Event-Driven Step Synchronization & Event Waiting**:
   - The [`process_schedule`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:161) background job uses `wait_for_event()` to suspend execution whenever an prerequisite asset is unavailable (e.g. template disabled, previous step communication unsent, Sift AI prediction pending, or user bio missing). When the asset becomes available, an event (`email_template_enabled`, `user_bio_created`, etc.) wakes up the step queue.
4. **Decoupled AI Personalization via Sift Webhooks**:
   - Sift AI integration ([`apps/frappe_cadence/frappe_cadence/integrations/sift.py`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:4)) uses an asynchronous request-callback pattern. Prompt optimization requests are POSTed to Sift, and responses are delivered back via whitelisted callback endpoints (`optimize_callback`, `predict_callback`), storing results in template annotation DocTypes without locking background workers.
5. **Round Robin & Load Balanced Sender Pools**:
   - Cadences distribute leads across assigned users using stateful round-robin tracking or dynamic load-balancing queries ([`determine_sender`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:272)), guaranteeing equitable distribution across sales teams.
