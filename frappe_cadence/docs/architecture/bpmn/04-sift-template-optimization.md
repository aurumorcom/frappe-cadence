# 04 Sift AI Template Optimization & Prediction Workflow

This workflow documents multi-channel AI prompt optimization and engagement prediction, triggered by template saves or direct invocation of Sift whitelisted API endpoints [`optimize`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:63) and [`predict`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:202).

## Workflow Diagram

```mermaid
flowchart TD
    StartTrigger(["Trigger: Template on_update OR API call sift.optimize / sift.predict"]) --> LoadSettings["Load Sift Settings Credentials"]
    LoadSettings --> GenSchema["Execute get_annotation_schema() for Target Template"]
    GenSchema --> BuildPayload["Construct Sift Webhook Payload (Template, History, Lead Context)"]
    BuildPayload --> SendRequest["POST Webhook Payload to Sift AI API"]
    SendRequest --> SiftProcessing["Sift AI Engine Processes Request Asynchronously"]
    
    SiftProcessing --> ReceiveCallback(["Trigger: Whitelisted Callback Endpoint optimize_callback / predict_callback"])
    ReceiveCallback --> ValidatePayload{"Is Callback Signature Valid?"}
    ValidatePayload -- No --> LogCallbackError["Log Error & Return 400 Bad Request"]
    LogCallbackError --> EndError(["End: Callback Rejected"])
    
    ValidatePayload -- Yes --> CheckType{"Callback Event Type?"}
    CheckType -- Optimization --> SaveAnnotation["Save Channel Template Annotation Record"]
    CheckType -- Prediction / Output --> UpdateTemplate["Update Output Content on Channel Template"]
    
    SaveAnnotation --> EmitEvent["Emit Event: template_updated / sift_callback_received"]
    UpdateTemplate --> EmitEvent
    EmitEvent --> ResumeMCC["Resume Paused Multi Channel Cadence Steps"]
    ResumeMCC --> EndSuccess(["End: AI Optimization Sync Completed"])
```

## Step Specifications

1. **Trigger & Schema Extraction**:
   - `sift.optimize()` or `sift.predict()` dynamically extracts meta fields and builds strict JSON schemas via [`get_annotation_schema`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:41).
2. **Asynchronous Webhook POST**:
   - Posts template body, lead attributes, and past lead communication history to Sift AI service endpoints.
3. **Webhook Callback Receiver**:
   - [`optimize_callback`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:152) and [`predict_callback`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:279) process inbound webhook payloads.
4. **Annotation & Event Emission**:
   - Writes AI scores and feedback to channel template annotation records (`Email Template Annotation`, `SMS Template Annotation`, etc.) and broadcasts events to unblock paused step queues.
