# Architectural Decision Records (ADR)

**Project:** Morpheus Intelligence Platform  
**Last Updated:** 2026-01-19  
**Status:** Active

---

## Overview

This document records all significant architectural and technical decisions made during the development of the Morpheus Intelligence Platform. Each decision includes context, rationale, consequences, and status.

## Decision Log

### ADR-001: Documentation Structure Standardization
**Date:** 2026-01-19  
**Status:** Accepted  
**Context:**  
- Project had documentation scattered across root directory and `./docs/` folder
- No standardized location for tracking changes
- Code Mode SOP requires `./doc/` folder structure with specific required files

**Decision:**  
- Establish `./doc/` as the single source of truth for all project documentation
- Migrate existing documentation from root and `./docs/` to `./doc/`
- Create required documentation stubs per Code Mode SOP
- Implement `laststep.md` for change tracking

**Rationale:**  
- Ensures consistent documentation structure
- Improves discoverability of documentation
- Enables proper change tracking and rollback capability
- Aligns with repeatable engineering process standards

**Consequences:**  
- Positive: Centralized documentation location
- Positive: Improved change tracking with laststep.md
- Positive: Better rollback capability
- Negative: Need to update any hardcoded documentation paths
- Negative: Team needs to learn new documentation structure

**Alternatives Considered:**  
- Keep existing `./docs/` folder (rejected: non-standard naming)
- Distribute docs in component folders (rejected: harder to discover)

**Rollback:** See [`../rollback/20260119-043026-doc-reorganization/notes.md`](../rollback/20260119-043026-doc-reorganization/notes.md)

---

### ADR-002: Python FastAPI Backend Framework
**Date:** ~2026-01 (existing decision, documented here)  
**Status:** Accepted  
**Context:**  
- Need high-performance backend for data intelligence platform
- Must support async operations for BigQuery and other data sources
- Require strong type safety and automatic API documentation

**Decision:**  
Use Python FastAPI as the backend framework

**Rationale:**  
- FastAPI provides high performance with async support
- Automatic OpenAPI documentation generation
- Pydantic for robust data validation
- Large ecosystem of Python data libraries
- Type hints for better code quality

**Consequences:**  
- Positive: Modern async/await patterns
- Positive: Strong typing with Pydantic
- Positive: Excellent performance
- Positive: Auto-generated API docs
- Negative: Python 3.11+ required
- Negative: Learning curve for async patterns

---

### ADR-003: React 19 with Vite for Frontend
**Date:** ~2026-01 (existing decision, documented here)  
**Status:** Accepted  
**Context:**  
- Need modern, performant frontend framework
- Require fast development iteration cycles
- Must support complex data visualizations

**Decision:**  
Use React 19 with Vite build tool and TypeScript

**Rationale:**  
- React provides component-based architecture
- React 19 includes latest performance improvements
- Vite offers fast development experience
- TypeScript adds type safety
- Large ecosystem of visualization libraries

**Consequences:**  
- Positive: Fast development with HMR
- Positive: Strong type safety with TypeScript
- Positive: Rich component ecosystem
- Positive: Excellent performance
- Negative: Bundle size management needed
- Negative: Complexity of modern React patterns

---

### ADR-004: BigQuery as Primary Data Source (MVP)
**Date:** ~2026-01 (existing decision, documented here)  
**Status:** Accepted  
**Context:**  
- Need to focus MVP on single, well-supported data source
- Many enterprise customers use BigQuery
- Good API support and documentation available

**Decision:**  
Focus MVP on Google BigQuery connectivity, with architecture supporting future multi-source expansion

**Rationale:**  
- Reduces MVP scope to manageable size
- BigQuery has excellent Python SDK
- Large enterprise user base
- Strong metadata and schema discovery capabilities
- Architecture allows future expansion to other sources

**Consequences:**  
- Positive: Faster MVP delivery
- Positive: Can leverage BigQuery-specific optimizations
- Positive: Well-documented API
- Negative: Limited to single data source initially
- Negative: BigQuery-specific patterns may need refactoring

**Migration Path:**  
Phase 2 will introduce connector abstraction layer for Snowflake, PostgreSQL, and other sources (see [`architecture.md`](./architecture.md))

---

### ADR-005: Platform Catalog Architecture
**Date:** ~2026-01 (existing decision, documented here)  
**Status:** In Progress  
**Context:**  
- Need centralized metadata catalog
- Must support multiple future data sources
- Require fast metadata queries for UI

**Decision:**  
Implement three-layer architecture:
1. **Connector Layer:** Data source adapters
2. **Metadata Catalog:** Technical metadata storage
3. **Semantic Layer:** Business context mapping

**Rationale:**  
- Separates technical metadata from business semantics
- Enables universal data source support
- Provides flexibility for future enhancements
- Clear separation of concerns

**Consequences:**  
- Positive: Extensible to any data source
- Positive: Clear architectural boundaries
- Positive: Can add semantic meaning without changing connectors
- Negative: More complex than monolithic approach
- Negative: Additional abstraction layers

**See Also:** [`architecture.md`](./architecture.md), [`platform-catalog-plan.md`](./platform-catalog-plan.md)

---

### ADR-006: No Git Repository (Current State)
**Date:** 2026-01-19  
**Status:** Documented  
**Context:**  
- Project is not currently in a git repository
- Code Mode SOP requires rollback capability
- Need version control and change tracking

**Decision:**  
Document current non-git state and implement file-based rollback strategy per SOP

**Rationale:**  
- File-based rollback provides basic safety net
- Can migrate to git repository later
- Meets SOP requirements for rollback capability

**Consequences:**  
- Positive: Rollback capability established
- Negative: Manual rollback process
- Negative: No distributed version control
- Negative: No branch/merge workflows

**Recommendation:**  
Initialize git repository as next priority after documentation reorganization

---

## Decision Template

When adding new decisions, use this template:

```markdown
### ADR-XXX: [Decision Title]
**Date:** YYYY-MM-DD  
**Status:** [Proposed | Accepted | Deprecated | Superseded]  
**Context:**  
[Describe the situation and problem]

**Decision:**  
[State the decision clearly]

**Rationale:**  
[Explain why this decision was made]

**Consequences:**  
- Positive: [Benefits]
- Negative: [Tradeoffs]

**Alternatives Considered:**  
- [Alternative 1] (rejected: reason)
- [Alternative 2] (rejected: reason)

**Rollback:** [Link to rollback documentation if applicable]
```

---

## Status Legend

- **Proposed:** Decision is under consideration
- **Accepted:** Decision is approved and being implemented
- **Deprecated:** Decision is no longer valid but kept for historical context
- **Superseded:** Decision has been replaced by a newer decision

---

**Note:** This document should be updated whenever significant architectural or technical decisions are made. For implementation details, see related documentation in [`./doc/`](./doc/).
### ADR-007: Security Hardening (Config & CORS)

**Date:** 2026-02-02
**Status:** Accepted
**Context:**

* The current backend implementation has hardcoded CORS origins and credentials logic.
* Service account keys are being read from local files (`temp_creds.json`), which is a security risk.
* Logging is currently done via `print()` statements, which is insufficient for production observability.

**Decision:**

* **Externalize Configuration:** Move all environment-specific config (CORS origins, Project ID) to environment variables.
* **Adopt Application Default Credentials (ADC):** Remove dependency on `temp_creds.json` for GCP auth in production, falling back to ADC.
* **Structured Logging:** Replace `print()` with a structured logging configuration (JSON format for Cloud Logging).
* **Run as Non-Root:** Update Dockerfile to run the application as a non-root user.

**Rationale:**

* **Security:** Hardcoded secrets and loose CORS policies are critical vulnerabilities.
* **Observability:** JSON logs are machine-parsable and essential for cloud monitoring.
* **Best Practices:** ADC is the standard way to handle GCP auth securely.

**Consequences:**

* Positive: Improved security posture.
* Positive: Production-ready logging.
* Negative: Local development requires setting environment variables (e.g., `ALLOWED_ORIGINS`).

**Rollback:** File-based rollback will be created in `rollback/` directory before application.
