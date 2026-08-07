# 01 Lead Cadence Enrollment Workflow

This workflow documents the automatic evaluation and enrollment of leads into sales cadences, triggered by updates to either [`frappe_crm.doctype.crm_lead.crm_lead`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:169) or [`frappe_cadence.cadence.doctype.cadence.cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:128).

## Workflow Diagram

```mermaid
flowchart TD
    StartTrigger(["Trigger: CRM Lead on_update OR Cadence on_update"]) --> EnqueueJob["Enqueue evaluate_lead_for_cadences() / evaluate_cadence_for_leads()"]
    EnqueueJob --> FetchCadences["Fetch Active Cadences & AST Conditions"]
    FetchCadences --> ASTParse{"assign_condition specified?"}
    ASTParse -- Yes --> ParseAST["Convert AST Condition to SQL Filters"]
    ASTParse -- No --> CheckMatch["Evaluate Lead Field Match"]
    ParseAST --> CheckMatch
    CheckMatch -- Match Found --> DetermineSender["Determine Sender (determine_sender)"]
    CheckMatch -- No Match --> EndNoMatch(["End: No Cadence Match"])
    DetermineSender --> RuleType{"Assignment Rule?"}
    RuleType -- Round Robin --> RoundRobin["Pick Next User & Update last_user"]
    RuleType -- Load Balancing --> LoadBalance["Select User with Least Active MCCs"]
    RoundRobin --> CreateMCC["Instantiate Multi Channel Cadence"]
    LoadBalance --> CreateMCC
    CreateMCC --> CheckMCCExists{"Multi Channel Cadence Already Exists?"}
    CheckMCCExists -- Yes --> EndDuplicate(["End: Idempotent Return - Duplicate Skipped"])
    CheckMCCExists -- No --> SaveMCC["Save Multi Channel Cadence (status = 'Provisioning')"]
    SaveMCC --> EndSuccess(["End: Lead Enrolled in Multi Channel Cadence"])
```

## Step Specifications

1. **Trigger**:
   - `CRM Lead on_update` hook enqueues `evaluate_lead_for_cadences(lead_name)`.
   - `Cadence on_update` hook enqueues `evaluate_cadence_for_leads(cadence_name)`.
2. **Condition AST Parsing**:
   - Parses Python conditions (`doc.status == "New" and doc.annual_revenue > 50000`) into structured JSON SQL filters via [`_ast_to_filters`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:67).
3. **Sender Determination**:
   - Implements `Round Robin` or `Load Balancing` across user pools in [`determine_sender`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence/cadence.py:272).
4. **Enrollment**:
   - Creates a new [`frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence`](apps/frappe_cadence/frappe_cadence/cadence/doctype/multi_channel_cadence/multi_channel_cadence.py:32) record in `Provisioning` state.
