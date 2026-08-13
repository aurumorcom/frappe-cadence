# ADR 0001: Record Architecture Decisions

## Status
Accepted

## Date
2026-07-15

## Context
[`frappe_cadence`](apps/frappe_cadence/frappe_cadence/hooks.py:1) requires a standardized, structured mechanism to document significant architectural decisions, external integrations, AST evaluation mechanisms, and asynchronous orchestration patterns to prevent knowledge drift and ensure architectural consistency across the engineering team.

## Decision
We adopt the Architecture Decision Record (ADR) pattern as integrated within arc42 Chapter 09. All architectural decisions MUST be recorded as numbered Markdown documents located in `arc42/09-architecture-decisions/` using the zero-padded sequential naming format (e.g., `0001-record-architecture-decisions.md`, `0002-ast-condition-evaluation.md`). Every ADR must define `Status`, `Date`, `Context`, `Decision`, and `Consequences`.

## Consequences
### Positive
- Transparent, version-controlled history of all technical choices and trade-offs.
- Immediate clarity for new developers onboarding onto the project.
- Prevents regressive architecture changes that violate core design principles.

### Negative & Risks
- Requires continuous maintenance and discipline to author ADRs before implementing non-trivial architecture modifications.
