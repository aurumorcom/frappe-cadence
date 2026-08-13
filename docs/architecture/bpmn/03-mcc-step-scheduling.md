# 03 Multi Channel Cadence Step Scheduling Workflow

This workflow documents multi-step cadence execution across email, SMS, LinkedIn, and WhatsApp channels, triggered by [`frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:1) updates.

## Workflow Diagram

```mermaid
flowchart TD
    StartMCCUpdate(["Trigger: Multi Channel Cadence on_update / after_insert"]) --> SyncLeadTable["Update Hidden Cadences Table on CRM Lead"]
    SyncLeadTable --> EnqueueSteps["Enqueue process_schedule() for Each Step Schedule"]
    
    EnqueueSteps --> StartProcessSchedule(["Execute process_schedule() Job"])
    StartProcessSchedule --> CheckMCCStatus{"Is Multi Channel Cadence status Active?"}
    CheckMCCStatus -- Terminal: Completed/Error/Unsubscribed --> EndTerminal(["End: Terminal Cadence State - Exit"])
    CheckMCCStatus -- Inactive: Draft/Provisioning --> WaitMCCEvent["wait_for_event('mcc_scheduled' / 'mcc_in_progress')"]
    CheckMCCStatus -- Yes --> CheckPrevStep{"Previous Step Schedule Specified?"}
    
    WaitMCCEvent --> CheckMCCStatus
    CheckPrevStep -- Yes --> CheckPrevComm{"Previous Step Communication Sent?"}
    CheckPrevComm -- No --> WaitPrevEvent["wait_for_event('doc:Communication:after_insert')"]
    WaitPrevEvent --> CheckPrevComm
    CheckPrevComm -- Yes --> CheckCurrentComm{"Communication Already Sent for Step?"}
    CheckPrevStep -- No --> CheckCurrentComm
    
    CheckCurrentComm -- Yes --> EndIdempotent(["End: Idempotent Return - Already Dispatched"])
    CheckCurrentComm -- No --> FetchTemplate["Load Channel Template & Check status"]
    FetchTemplate --> IsTemplateEnabled{"Is Template Enabled?"}
    IsTemplateEnabled -- No --> WaitTemplateEvent["wait_for_event('doc:Email Template:on_update')"]
    WaitTemplateEvent --> FetchTemplate
    
    IsTemplateEnabled -- Yes --> FetchUserBio["Execute get_user_bio(mcc.sender, mcc.cadence_name)"]
    FetchUserBio --> HasUserBio{"Is User Bio Available?"}
    HasUserBio -- No --> WaitBioEvent["wait_for_event('doc:User Bio:on_update')"]
    WaitBioEvent --> FetchUserBio
    
    HasUserBio -- Yes --> HasPromptTemplate{"Step uses Prompt Template & Sift AI?"}
    HasPromptTemplate -- Yes --> CheckSiftCache{"Personalization in Redis Cache?"}
    CheckSiftCache -- No --> PostSiftWebhook["POST Webhook to Sift AI API with template.sift_id model"]
    PostSiftWebhook --> WaitSiftCallback["wait_for_event('sift_callback_received')"]
    WaitSiftCallback --> CheckSiftCache
    CheckSiftCache -- Yes --> RenderMessage["Render Message with Sift AI Output"]
    HasPromptTemplate -- No --> RenderStandard["Render Template with Jinja & Bio Context"]
    
    RenderMessage --> CreateComm["Insert Communication Record"]
    RenderStandard --> CreateComm
    CreateComm --> DispatchMessage["Dispatch Message"]
    DispatchMessage --> EmitStepComplete["Emit step_communication_dispatched & Update MCC Progress"]
    EmitStepComplete --> EndStepSuccess(["End: Step Dispatched Successfully"])
```

## Step Specifications

1. **Sequential Step Dependency**:
   - `process_schedule` uses `wait_for_event()` to pause processing if a preceding step has not completed or if MCC status is `Draft` or `Paused`.
2. **Template & Sift AI Personalization**:
   - Evaluates template enablement, retrieves sender bio context via [`get_user_bio`](apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py:25), and optionally posts prompt payloads to external Sift AI services.
3. **Communication Creation**:
   - Generates a [`frappe_cadence.cadence.doctype.communication.communication`](apps/frappe_cadence/frappe_cadence/cadence/doctype/communication/communication.py:1) document tracking channel, step, and output payload.
