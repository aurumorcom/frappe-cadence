# 07 User Bio Provisioning Workflow

This workflow documents sender bio creation, privacy validation, and event-driven step queue wake-up, triggered by updates to [`frappe_cadence.cadence.doctype.user_bio.user_bio`](apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py:5).

## Workflow Diagram

```mermaid
flowchart TD
    StartBioTrigger(["Trigger: User Bio save / on_update"]) --> ValidatePermissions{"Validate Permission & Owner?"}
    ValidatePermissions -- Unauthorized --> RejectSave["Raise PermissionError"]
    RejectSave --> EndRejected(["End: User Bio Save Rejected"])
    
    ValidatePermissions -- Authorized --> SaveBio["Save User Bio Content for User & Cadence"]
    SaveBio --> EmitBioEvent["Execute emit_event('user_bio_created', reference_user)"]
    EmitBioEvent --> BroadcastEvent["Broadcast user_bio_created Event"]
    
    BroadcastEvent --> QueryWaitingSteps["Query Paused process_schedule Jobs Waiting on Bio"]
    QueryWaitingSteps --> HasWaitingJobs{"Any Steps Waiting on Sender Bio?"}
    HasWaitingJobs -- No --> EndNoWaiters(["End: User Bio Saved, No Waiting Step Queues"])
    HasWaitingJobs -- Yes --> ResumeSteps["Unblock wait_for_event() in process_schedule Jobs"]
    
    ResumeSteps --> ReFetchBio["Execute get_user_bio() for Sender Context"]
    ReFetchBio --> ContinueStep["Proceed with Message Personalization & Dispatch"]
    ContinueStep --> EndSuccess(["End: User Bio Provisioned & Step Execution Resumed"])
```

## Step Specifications

1. **Trigger & Permission Check**:
   - `User Bio` validates that non-admin users can only create/modify bios where `reference_user` matches `frappe.session.user` ([`has_permission`](apps/frappe_cadence/frappe_cadence/cadence/doctype/user_bio/user_bio.py:11)).
2. **Event Emission**:
   - `on_update` triggers `emit_event("user_bio_created", ...)` to notify reactive event listeners.
3. **Step Queue Resolution**:
   - Background tasks paused in [`process_schedule`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:161) resume execution, rendering personalized AI prompts with the newly provisioned bio.
