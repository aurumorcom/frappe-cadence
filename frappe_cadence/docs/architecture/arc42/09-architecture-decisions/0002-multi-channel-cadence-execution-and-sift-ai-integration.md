# ADR 0002: Multi-Channel Cadence Execution and Sift AI Integration

## Status
Accepted

## Date
2026-08-02

## Context
Sales outreach requires orchestrating multiple channels (Email, SMS, LinkedIn, WhatsApp) and generating dynamic personalized content using AI language models based on user bios and prospect context.

## Decision
1. **Multi-Channel Orchestration**: Use a single `MultiChannelCadence` execution record linked to channel-specific `Cadence Multi Channel Schedule` steps.
2. **Asynchronous Event Coordination**: Suspend worker execution using `wait_for_event()` and resume on `emit_event()` signals to avoid keeping thread execution blocked on delay timers or webhook responses.
3. **Sift AI Webhooks**: Dispatch prompt generation payloads to Sift AI over HTTPS with background webhooks (`/responses` endpoint) and resume step execution upon receiving asynchronous webhook callbacks.

## Consequences
- High concurrency and low worker memory utilization.
- Decouples message scheduling from AI generation latencies.
