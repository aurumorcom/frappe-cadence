# Architecture Documentation: Frappe Cadence (`frappe_cadence`)

Welcome to the architectural documentation for the **`frappe_cadence`** application ([`apps/frappe_cadence/frappe_cadence/hooks.py`](apps/frappe_cadence/frappe_cadence/hooks.py:1)).

## Navigation Index

### 1. C4 Modeling (`c4/`)
- [**C1 System Context Model**](c4/01-context.md): High-level system context and external system boundaries.
- [**C2 Container Model**](c4/02-container.md): Execution containers, WSGI app, database, Redis workers, Sift AI, and channel providers.
- [**C3 Component Model**](c4/03-component.md): Complete entity relationship diagram and component specifications.

### 2. Behavioral Workflows (`bpmn/`)
- [**01 Lead Cadence Enrollment Workflow**](bpmn/01-lead-cadence-enrollment.md): Automatic lead condition parsing, evaluation, and assignment.
- [**02 Playbook Execution Provisioning Workflow**](bpmn/02-playbook-provisioning.md): Playbook creation, async execution, and MCC status sync.
- [**03 Multi Channel Cadence Step Scheduling Workflow**](bpmn/03-mcc-step-scheduling.md): Multi-step execution across email, SMS, LinkedIn, and WhatsApp channels.
- [**04 Sift AI Template Optimization & Prediction Workflow**](bpmn/04-sift-template-optimization.md): Multi-channel AI optimization, prediction, and annotation callbacks.
- [**05 Communication Engagement Tracking Workflow**](bpmn/05-communication-engagement-tracking.md): External webhook reporting, communication updates, and cadence status transitions.
- [**06 Cadence Provider Allocation Workflow**](bpmn/06-cadence-provider-allocation.md): Provider setup, channel router resolution, and active MCC re-allocation.
- [**07 User Bio Provisioning Workflow**](bpmn/07-user-bio-provisioning.md): Sender bio management, privacy controls, and event-driven step wake-up.

### 3. arc42 System Documentation (`arc42/`)
- [**01 Introduction and Goals**](arc42/01_introduction_and_goals.md)
- [**02 Architecture Constraints**](arc42/02_architecture_constraints.md)
- [**03 Context and Scope**](arc42/03_context_and_scope.md)
- [**04 Solution Strategy**](arc42/04_solution_strategy.md)
- [**05 Building Block View**](arc42/05_building_block_view.md)
- [**06 Runtime View**](arc42/06_runtime_view.md)
- [**07 Deployment View**](arc42/07_deployment_view.md)
- [**08 Cross-Cutting Concepts**](arc42/08_cross_cutting_concepts.md)
- [**09 Architecture Decisions (ADRs)**](arc42/09_architecture_decisions/0001-record-architecture-decisions.md)
  - [0001 Baseline Architectural Decisions](arc42/09_architecture_decisions/0001-record-architecture-decisions.md)
  - [0002 Multi-Channel Cadence Execution and Sift AI Integration](arc42/09_architecture_decisions/0002-multi-channel-cadence-execution-and-sift-ai-integration.md)
- [**10 Quality Requirements**](arc42/10_quality_requirements.md)
- [**11 Risks and Technical Debt**](arc42/11_risks_and_technical_debt.md)
- [**12 Glossary**](arc42/12_glossary.md)
