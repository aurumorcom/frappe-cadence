# 05 Communication Engagement Tracking Workflow

This workflow documents external engagement tracking (opens, clicks, replies, bounces) and communication lifecycle management, triggered by [`frappe_cadence.cadence.doctype.communication.communication`](apps/frappe_cadence/frappe_cadence/cadence/doctype/communication/communication.py:2) doc events and provider webhook invocations of [`report_event`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py:53).

## Workflow Diagram

```mermaid
flowchart TD
    StartCommTrigger(["Trigger: Communication after_insert / on_update OR Provider Webhook"]) --> DetectSource{"Source of Event?"}
    DetectSource -- Communication Event --> ProcessComm["Execute Communication Hook"]
    DetectSource -- Provider Webhook --> InvokeReportEvent["Execute report_event() with Context"]
    
    ProcessComm --> MatchMCC["Locate Target Multi Channel Cadence"]
    InvokeReportEvent --> MatchComm["Find Communication by External Message ID"]
    MatchComm --> MatchMCC
    
    MatchMCC --> EvaluateEventType{"Evaluate Event Type / Delivery Status"}
    EvaluateEventType -- sent / opened / clicked --> LogEngagement["Log Activity in History & History Group"]
    EvaluateEventType -- replied --> MarkReplied["Update Communication (status = 'Replied') & MCC (status = 'Completed')"]
    EvaluateEventType -- bounced --> MarkBounced["Update Communication (status = 'Bounced') & MCC (status = 'Error')"]
    EvaluateEventType -- unsubscribed --> MarkUnsub["Update Multi Channel Cadence (status = 'Paused')"]
    
    LogEngagement --> UpdateHistory["Append Metrics to History Log"]
    MarkReplied --> CancelPendingSteps["Cancel Remaining Queued process_schedule Jobs"]
    MarkBounced --> CancelPendingSteps
    MarkUnsub --> CancelPendingSteps
    
    CancelPendingSteps --> UpdateHistory
    UpdateHistory --> EndTrackingSuccess(["End: Engagement Tracked & Cadence Updated"])
```

## Step Specifications

1. **Trigger & Delivery Webhook**:
   - Outbound and inbound events invoke [`report_event`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py:53) with contextual metadata (lead email/phone, message ID, provider tag).
2. **Engagement Evaluation**:
   - Categorizes events into informational engagement (`opened`, `clicked`) versus cadence terminal events (`replied`, `bounced`, `unsubscribed`).
3. **MCC State & Queue Cancellation**:
   - Terminal events transition [`frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:32) to `Completed`, `Error`, or `Paused` and cancel pending scheduled steps.
4. **History Logging**:
   - Writes timeline interactions into [`frappe_cadence.cadence.doctype.history.history`](apps/frappe_cadence/frappe_cadence/cadence/doctype/history/history.py:10) for reporting and analytics.
