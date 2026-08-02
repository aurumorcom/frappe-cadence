# ADR 0001: Record Architecture Decisions

## Status
Accepted

## Date
2026-08-02

## Context
We need a structured way to record architectural decisions so that technical context and trade-offs are transparent and documented for all contributors to `frappe_cadence`.

## Decision
We will use Architecture Decision Records (ADRs) structured in `docs/architecture/arc42/09-architecture-decisions/` using sequentially numbered files (`0001-...md`, `0002-...md`, etc.).

## Consequences
- Every significant architectural decision is documented alongside codebase changes.
- Future refactoring decisions will be evaluated against past ADRs.
