# Audit Policy

**Project:** Morpheus Intelligence Platform  
**Last Updated:** 2026-01-22  
**Status:** Draft

## Purpose
Define the minimum audit requirements for all changes to the Morpheus Intelligence Platform, ensuring traceability, accountability, and evidence retention.

## Principles
- Every meaningful change must have a recorded task, change log entry, and rollback reference.
- Evidence (logs, screenshots, or diffs) must be captured for verification.
- Access to audit records must remain read-only for non-owners.

## Requirements
1. **Task Traceability**: Each change links to a task in [`pm-board.md`](./pm-board.md).
2. **Change Log**: Each change is summarized in [`changelog.md`](./changelog.md) with date and rollback reference.
3. **Rollback**: A rollback bundle or git commit reference must exist per [`rollback-policy.md`](./rollback-policy.md).
4. **Evidence**: Verification outputs (command logs, screenshots) must be retained or referenced.
5. **Decisions**: Tradeoffs are captured in [`decisions.md`](./decisions.md) when alternatives are considered.

## Enforcement
- Changes failing audit requirements must not be marked Done.
- QA signs off only when verification evidence is present.

## References
- [`rollback-policy.md`](./rollback-policy.md)
- [`quality-gates.md`](./quality-gates.md)
- [`decisions.md`](./decisions.md)
