# 02 Playbook Execution Provisioning Workflow

This workflow documents the automatic playbook creation and asynchronous execution status updates that transition cadence records from `Provisioning` to `Draft` or `Error`, triggered by [`frappe_cadence.cadence.doctype.cadence.cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:41) insertion and [`frappe_cadence.cadence.doctype.playbook_execution.playbook_execution`](apps/frappe_cadence/frappe_cadence/cadence/doctype/playbook_execution/playbook_execution.py:4) updates.

## Workflow Diagram

```mermaid
flowchart TD
    StartCadenceInsert(["Trigger: Cadence after_insert"]) --> EnsurePlaybook["Execute ensure_playbook()"]
    EnsurePlaybook --> HasPlaybook{"Reference Playbook Linked?"}
    HasPlaybook -- No --> CreatePlaybook["Create Playbook & Link Reference"]
    HasPlaybook -- Yes --> LinkPlaybook["Attach Existing Playbook Reference"]
    CreatePlaybook --> AsyncExecution["Initiate Background Playbook Execution"]
    LinkPlaybook --> AsyncExecution
    
    AsyncExecution --> StartPlaybookUpdate(["Trigger: Playbook Execution on_update"])
    StartPlaybookUpdate --> CheckStatusChanged{"status Value Changed?"}
    CheckStatusChanged -- No --> EndNoOp(["End: No Action Required"])
    CheckStatusChanged -- Yes --> QueryMCC["Query Multi Channel Cadence (status = 'Provisioning')"]
    QueryMCC --> EvaluateStatus{"Playbook Execution status?"}
    
    EvaluateStatus -- success --> SetDraft["Update Multi Channel Cadence (status = 'Draft')"]
    EvaluateStatus -- error --> SetError["Update Multi Channel Cadence (status = 'Error')"]
    EvaluateStatus -- other --> EndPending(["End: Pending Playbook Execution"])
    
    SetDraft --> TriggerMCCUpdate["Trigger Multi Channel Cadence on_update & Step Execution"]
    SetError --> EndErrorState(["End: Multi Channel Cadence Marked as Error"])
    TriggerMCCUpdate --> EndSuccess(["End: Cadence Provisioning Completed"])
```

## Step Specifications

1. **Cadence Creation & Playbook Association**:
   - `Cadence after_insert` hook invokes `ensure_playbook()` to establish the associated Playbook instance.
2. **Asynchronous Execution Event**:
   - `Playbook Execution on_update` hook in [`playbook_execution.py`](apps/frappe_cadence/frappe_cadence/cadence/doctype/playbook_execution/playbook_execution.py:4) listens for state transitions.
3. **Provisioning Transition**:
   - When status reaches `success`, linked [`frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:32) documents move from `Provisioning` to `Draft`, unlocking background schedule processing.
