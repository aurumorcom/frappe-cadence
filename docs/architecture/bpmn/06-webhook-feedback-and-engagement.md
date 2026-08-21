# Behavioral Workflows (BPMN): Webhook Feedback & Engagement

## 🎯 Primary Workflow: Webhook Ingestion & Engagement Tracking Workflow

```mermaid
flowchart TD
    Start([Receive Inbound Webhook]) --> InboundWebhook[Receive Inbound POST Webhook from Listmonk]
    
    InboundWebhook --> VerifySignature{HMAC-SHA256 Signature Valid?}
    VerifySignature -- No --> RejectWebhook([Reject Webhook with 403 PermissionError - End])
    VerifySignature -- Yes --> ParseEvent{Evaluate Webhook Event Type}
    
    ParseEvent -- campaign.started / step_executed --> SetMCCInProgress[Update MCC Status to 'In Progress']
    ParseEvent -- replied --> SetMCCReplied[Update MCC Status to 'Replied']
    ParseEvent -- subscriber.bounced --> SetMCCBounced[Update MCC Status to 'Failed']
    ParseEvent -- unsubscribed / opted_out --> SetMCCOptedOut[Update MCC Status to 'Opted Out']
    ParseEvent -- completed --> SetMCCFinished[Update MCC Status to 'Finished']
    
    SetMCCReplied --> RemoveFromSequence[Remove Subscriber from Listmonk Sequence List]
    SetMCCOptedOut --> RemoveFromSequence
    SetMCCFinished --> RemoveFromSequence
    
    SetMCCInProgress --> LogInteraction[Record Event Details into History]
    RemoveFromSequence --> LogInteraction
    SetMCCBounced --> LogInteraction
    
    LogInteraction --> End([Outreach Lifecycle Complete - End])
```

## 📝 Workflow Step Descriptions

1. **Receive Webhook**: Listmonk pushes engagement events (open, click, step delivery, bounce, unsubscribe) to [`webhook()`](apps/frappe_cadence/frappe_cadence/integrations/listmonk/jobs/webhook.py:68).
2. **Verify HMAC-SHA256 Signature**: Checks payload against `Listmonk-Signature` using `hmac.compare_digest()`.
3. **Parse Event Payload**: Evaluates event strings and maps them to Multi Channel Cadence status targets.
4. **Transition Status**: Updates [`Multi Channel Cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:7) status in the database.
5. **Sequence Disassociation**: Automatically unenrolls leads upon reply, opt-out, or completion via [`remove_subscriber_from_sequence()`](apps/frappe_cadence/frappe_cadence/jobs/multi_channel_cadence.py:99).
6. **Interaction Audit Logging**: Records engagement timestamps and metadata into [`History`](apps/frappe_cadence/frappe_cadence/cadence/doctype/history/history.py:10).
