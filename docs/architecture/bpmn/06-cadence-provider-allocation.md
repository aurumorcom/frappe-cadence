# 06 Cadence Provider Allocation Workflow

This workflow documents provider registration, channel router resolution, and active MCC provider re-allocation, triggered by updates to [`frappe_cadence.cadence.doctype.cadence_provider.cadence_provider`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py:10).

## Workflow Diagram

```mermaid
flowchart TD
    StartProviderUpdate(["Trigger: Cadence Provider on_update"]) --> EnqueuePopulate["Enqueue populate_mccs_with_new_provider()"]
    EnqueuePopulate --> FetchActiveMCCs["Fetch Active Multi Channel Cadence Records (Provisioning / Scheduled / In Progress)"]
    FetchActiveMCCs --> LoopMCCs["Iterate Over Active Multi Channel Cadence Instances"]
    
    LoopMCCs --> ResolveRouter["Execute resolve_providers_for_mcc()"]
    ResolveRouter --> QueryProviders["Query Enabled Cadence Providers & Channels"]
    QueryProviders --> SortPriority["Sort Providers by Priority Weight"]
    SortPriority --> BuildMapping["Map Optimal Provider per Channel (Email, SMS, LinkedIn, WhatsApp)"]
    
    BuildMapping --> DiffProviders{"Provider Mapping Changed?"}
    DiffProviders -- No --> NextMCC["Skip to Next MCC Record"]
    DiffProviders -- Yes --> UpdateMCCProviders["Update MCC Cadence Provider Child Table Snapshot"]
    
    UpdateMCCProviders --> SaveMCC["Save Multi Channel Cadence Document"]
    SaveMCC --> NextMCC
    NextMCC --> MoreMCCs{"More Active MCC Records?"}
    MoreMCCs -- Yes --> LoopMCCs
    MoreMCCs -- No --> EndSuccess(["End: Provider Allocation & Snapshot Completed"])
```

## Step Specifications

1. **Trigger & Background Dispatch**:
   - `Cadence Provider on_update` enqueues [`populate_mccs_with_new_provider`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py:22) in background worker queues.
2. **Channel Router Resolution**:
   - [`resolve_providers_for_mcc`](apps/frappe_cadence/frappe_cadence/cadence/doctype/cadence_provider/cadence_provider.py:104) ranks available providers by priority and matching channel flags.
3. **MCC Snapshot Re-population**:
   - Re-snapshots child table [`frappe_cadence.cadence.doctype.mcc_cadence_provider.mcc_cadence_provider`](apps/frappe_cadence/frappe_cadence/cadence/doctype/mcc_cadence_provider/mcc_cadence_provider.py:1) for active cadence instances without interrupting scheduled steps.
