# Runtime View

## Multi-Channel Execution Workflow
[BPMN Workflows](../bpmn.md)

This runtime view details the exact sequence of events when a lead enters a multi-channel cadence:

1. **Trigger**: An update to a CRM Lead or Cadence evaluates assignment conditions.
2. **Provisioning**: A `Multi Channel Cadence` is created in `Provisioning` state. A background `PlaybookExecution` runs.
3. **Draft Transition**: Upon playbook success, the system moves the MCC to `Draft`. The user schedules it.
4. **Step Orchestration**: The `process_schedule` worker begins execution.
5. **AI Evaluation (Optional)**: If the step uses a `Prompt` template, the worker sends a request to the Sift API containing the user's bio and suspends itself.
6. **Callback Resumption**: The webhook endpoint receives the AI payload, updates the `Communication` record, and emits an event to resume the worker.
7. **Delivery & Engagement Tracking**: Channel services dispatch the message. As engagement occurs (replies, bounces, unsubscribes), engagement webhooks update the MCC state to terminal (`Completed`, `Error`, `Unsubscribed`), emitting events that cancel further step processing.
