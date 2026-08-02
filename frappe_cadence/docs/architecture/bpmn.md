# Behavioral Workflows (BPMN)

## 🎯 Primary Workflow: End-to-End Multi-Channel Execution Workflow

```mermaid
flowchart TD
    StartTrigger(["Trigger: CRM Lead on_update OR Cadence on_update"]) --> EvalLead[evaluate_lead_for_cadences / evaluate_cadence_for_leads]
    EvalLead --> MatchCheck{Matches Assign Rules?}
    MatchCheck -- Yes --> Sender[Determine Sender via Round Robin / Load Balancing]
    Sender --> CreateMCC[Create Multi Channel Cadence status = 'Provisioning']
    CheckMCCExists -- No --> CreateMCC

    CreateMCC --> PlaybookEngine[Playbook Engine Runs PlaybookExecution]
    PlaybookEngine --> WaitProvisioning[Wait: Multi Channel Cadence status = 'Provisioning']
    WaitProvisioning --> PlaybookExecDone[PlaybookExecution Status Changes]
    PlaybookExecDone --> PlaybookHook[playbook_execution.py:on_update]
    PlaybookHook -- success --> SetDraft[Update Multi Channel Cadence status = 'Draft']
    PlaybookHook -- error / canceled --> SetError[Update Multi Channel Cadence status = 'Error']

    SetDraft --> UserSched[User Schedules Cadence]
    UserSched --> EnqueueSteps[Enqueue process_schedule Jobs]

    EnqueueSteps --> ProcStep[process_schedule Worker]
    ProcStep --> CheckMCCStatus{Multi Channel Cadence Status Active?}
    CheckMCCStatus -- Terminal --> ExitStep([Exit Step])
    CheckMCCStatus -- Draft / Provisioning --> WaitSched[wait_for_event mcc_scheduled / mcc_in_progress]
    CheckMCCStatus -- Active --> CheckPrev{Previous Step Done?}
    CheckPrev -- No --> WaitStep[wait_for_event cadence_step_completed]
    CheckPrev -- Yes --> CheckTmpl{Template Type}
    
    CheckTmpl -- Enabled --> StaticComm[Create Communication delivery_status = 'Scheduled']
    StaticComm --> EmitDone[emit_event cadence_step_completed]
    
    CheckTmpl -- Prompt --> BioCheck{Sender Bio Exists?}
    BioCheck -- No --> WaitBio[wait_for_event user_bio_created]
    BioCheck -- Yes --> SiftReq[POST to Sift API with template.sift_id & mcc.sender bio]
    SiftReq --> WaitCb[wait_for_event callback]

    SiftCb([Sift Webhook Callback]) --> CbStatus{Sift Event Type}
    CbStatus -- completed --> UpdateComm[Update Communication content & delivery_status = 'Scheduled']
    CbStatus -- failed --> FailComm[Set Communication delivery_status = 'Failed']
    UpdateComm --> EmitCb[emit_event callback]
    FailComm --> EmitCb
    EmitCb -. Wakes Up .-> WaitCb
    
    ProviderCb([Cadence Provider Webhook Callback]) --> ProvStatus{Event Type}
    ProvStatus -- message_replied --> UpdateMCCReplied[Update Multi Channel Cadence status = 'Completed']
    UpdateMCCReplied --> UpdateCommReplied[Update Communication status = 'Replied', delivery_status = 'Sent']
    UpdateCommReplied --> EmitMCCCompleted[emit_event mcc_completed & cadence_step_completed]
    
    ProvStatus -- bounce --> UpdateMCCError[Update Multi Channel Cadence status = 'Error']
    UpdateMCCError --> UpdateCommBounce[Set Communication delivery_status = 'Failed']
    UpdateCommBounce --> EmitMCCError[emit_event mcc_error]
    
    ProvStatus -- unsubscribed --> UpdateMCCUnsub[Update Multi Channel Cadence status = 'Unsubscribed']
    UpdateMCCUnsub --> EmitMCCUnsub[emit_event mcc_unsubscribed]
    
    EmitMCCCompleted -. Terminates .-> WaitStep
    EmitMCCError -. Terminates .-> WaitStep
    EmitMCCUnsub -. Terminates .-> WaitStep
```

## 📝 Workflow Step Descriptions
1. **Enrollment**: Automatically triggered by `CRM Lead` or `Cadence` updates. Evaluates assignment conditions and assigns a sender using Load Balancing or Round Robin before instantiating the `Multi Channel Cadence` in the `Provisioning` state.
2. **Provisioning**: The `Multi Channel Cadence` waits for its linked `PlaybookExecution` to complete. Upon successful execution, the status transitions to `Draft`.
3. **Orchestration & Scheduling**: Once scheduled by the user, the status transitions to `Scheduled` or `In Progress`, enqueuing asynchronous `process_schedule` worker jobs.
4. **Step Processing**: The worker handles sequence ordering by waiting for the previous step to complete. It evaluates the template:
    - For `Enabled` templates, it directly creates a `Communication`.
    - For `Prompt` templates, it fetches the sender's `User Bio`, queries the `Sift API` for AI content optimization based on `template.sift_id`, and waits for a callback.
5. **Webhook Callback**: The Sift callback updates the draft `Communication` with the AI-generated content and resumes the suspended worker.
6. **Engagement Tracking**: The `Cadence Provider` webhook processes engagement events (`message_replied`, `bounce`, `unsubscribed`) and automatically updates the `Multi Channel Cadence` status, propagating terminal events to clean up any sleeping orchestration threads.
