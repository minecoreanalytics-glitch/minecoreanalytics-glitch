# Morpheus Intelligence Platform - Documentation

**Version:** 1.0  
**Last Updated:** 2026-01-19  
**Status:** Active Development

---

## Overview

This directory contains all project documentation for the Morpheus Intelligence Platform - a universal data intelligence platform that transforms how organizations discover, understand, and leverage their data assets.

## Documentation Index

### Core Documentation

- **[PRD.md](./PRD.md)** - Product Requirements Document  
  Complete product vision, requirements, features, and success metrics

- **[architecture.md](./architecture.md)** - System Architecture  
  Core platform architecture, components, and design patterns

- **[dev-plan.md](./dev-plan.md)** - Development Plan & Roadmap  
  MVP roadmap, current status, and implementation timeline

### Supporting Documentation

- **[requirements.md](./requirements.md)** - Technical Requirements
  Detailed technical specifications and dependencies

- **[decisions.md](./decisions.md)** - Architectural Decision Records
  Key technical decisions and their rationale

- **[changelog.md](./changelog.md)** - Change Log
  Track of all significant changes to the project

- **[rollback-policy.md](./rollback-policy.md)** - Rollback Policy
  Procedures for rolling back changes safely

- **[platform-catalog-plan.md](./platform-catalog-plan.md)** - Platform Catalog Implementation
  Phase 0 catalog API implementation plan

### Governance Documentation

- **[pm-board.md](./pm-board.md)** - Project Management Board
  Kanban-style task tracking with status and priorities

- **[quality-gates.md](./quality-gates.md)** - Quality Gates & Standards
  Quality requirements and gates for each development stage

- **[research-policy.md](./research-policy.md)** - Research Policy
  Guidelines for technical research and decision-making

- **[personas.md](./personas.md)** - Development Personas
  PM, HEAD DEV, JUNIOR DEV, and QA persona definitions

## Quick Links

### For New Team Members
1. Start with [`PRD.md`](./PRD.md) to understand the product vision
2. Review [`architecture.md`](./architecture.md) for system design
3. Check [`dev-plan.md`](./dev-plan.md) for current development status

### For Developers
1. Review [`architecture.md`](./architecture.md) for technical architecture
2. Check [`decisions.md`](./decisions.md) for key technical decisions
3. Consult [`requirements.md`](./requirements.md) for technical specifications
4. Follow [`rollback-policy.md`](./rollback-policy.md) before making changes

### For Product/Business
1. Review [`PRD.md`](./PRD.md) for product requirements
2. Check [`dev-plan.md`](./dev-plan.md) for timeline and status
3. Monitor [`changelog.md`](./changelog.md) for recent updates

## Project Structure

```
morpheus-intelligence-platform/
├── doc/                    # All project documentation (this folder)
├── backend/               # Python FastAPI backend
│   ├── core/             # Core platform components
│   ├── modules/          # Feature modules
│   └── scripts/          # Utility scripts
├── components/           # React UI components
├── pages/               # Application pages
├── services/            # Frontend services
└── laststep.md          # Last change tracking file
```

## Documentation Standards

### File Naming
- Use lowercase with hyphens: `platform-catalog-plan.md`
- Required files use lowercase: `changelog.md`, `decisions.md`

### Markdown Standards
- Use ATX-style headers (`#` syntax)
- Include table of contents for documents > 100 lines
- Use code blocks with language specification
- Link to other docs using relative paths

### Change Management
- All significant changes must be documented in [`changelog.md`](./changelog.md)
- Architectural decisions must be recorded in [`decisions.md`](./decisions.md)
- Always update [`../laststep.md`](../laststep.md) after changes

## Contact & Support

For questions or issues with documentation:
- Check existing docs in this folder
- Review [`decisions.md`](./decisions.md) for context on technical choices
- Consult [`dev-plan.md`](./dev-plan.md) for current priorities

---

**Note:** This documentation follows the Code Mode SOP standards for repeatable engineering process, ensuring requirements-first development, safe incremental delivery, and complete rollback traceability.
