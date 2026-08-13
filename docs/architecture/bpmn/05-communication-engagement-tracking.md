# 05 Communication Engagement Tracking Workflow

This workflow documents external engagement tracking (opens, clicks, replies, bounces) and communication lifecycle management, triggered by [`frappe_cadence.cadence.doctype.communication.communication`](apps/frappe_cadence/frappe_cadence/cadence/doctype/communication/communication.py:1) doc events and webhook invocations.

## Workflow Diagram

```mermaid
flowchart TD
    StartCommTrigger(["Trigger: Communication after_insert / on_update OR Engagement Webhook"]) --> DetectSource{"Source of Event?"}
    DetectSource -- Communication Event --> ProcessComm["Execute Communication Hook"]
    DetectSource -- Engagement Webhook --> MatchComm["Find Communication by External Message ID"]
    
    ProcessComm --> MatchMCC["Locate Target Multi Channel Cadence"]
    MatchComm --> MatchMCC
    
    MatchMCC --> EvaluateEventType{"Evaluate Event Type / Delivery Status"}
    EvaluateEventType -- sent / opened / clicked --> LogEngagement["Log Activity in History & History Group"]
    EvaluateEventType -- replied --> MarkReplied["Update Communication (status = 'Replied', delivery_status = 'Sent') & MCC (status = 'Completed')"]
    EvaluateEventType -- bounced --> MarkBounced["Update Communication (delivery_status = 'Failed') & MCC (status = 'Error')"]
    EvaluateEventType -- unsubscribed --> MarkUnsub["Update Multi Channel Cadence (status = 'Unsubscribed')"]
    
    LogEngagement --> UpdateHistory["Append Metrics to History Log"]
    MarkReplied --> CancelPendingSteps["Cancel Remaining Queued process_schedule Jobs"]
    MarkBounced --> CancelPendingSteps
    MarkUnsub --> CancelPendingSteps
    
    CancelPendingSteps --> UpdateHistory
    UpdateHistory --> EndTrackingSuccess(["End: Engagement Tracked & Cadence Updated"])
```

## Step Specifications

1. **Trigger & Delivery Webhook**:
   - Outbound and inbound events invoke webhook callbacks with contextual metadata (lead email/phone, message ID).
2. **Engagement Evaluation**:
   - Categorizes events into informational engagement (`opened`, `clicked`) versus cadence terminal events (`replied`, `bounced`, `unsubscribed`).
3. **MCC State & Queue Cancellation**:
   - Terminal events transition [`frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:12) to `Completed`, `Error`, or `Unsubscribed` and emit events to terminate pending scheduled steps.
4. **History Logging**:
   - Writes timeline interactions into [`frappe_cadence.cadence.doctype.history.history`](apps/frappe_cadence/frappe_cadence/cadence/doctype/history/history.py:1) for reporting and analytics.
