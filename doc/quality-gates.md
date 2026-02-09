# Quality Gates

**Project:** Morpheus Intelligence Platform\
**Last Updated:** 2026-02-02\
**Status:** Active

***

## Overview

This document defines quality gates and standards that must be met before code can progress through development stages. Quality gates ensure consistency, reliability, and maintainability of the Morpheus platform.

## Quality Gate Stages

### 1. Development (Local)

**Gate:** Code Review Ready\
**Required Before:** Creating Pull Request

#### Checklist

* \[ ] Code follows project style guidelines
* \[ ] All new functions/classes have docstrings
* \[ ] No console.log or debugging code in commits
* \[ ] No hardcoded credentials or secrets
* \[ ] TypeScript types defined (frontend)
* \[ ] Type hints added (Python backend)
* \[ ] Code is self-documenting with clear variable names

#### Tools

* ESLint for JavaScript/TypeScript
* Black/Ruff for Python formatting
* TypeScript compiler for type checking
* Manual code review

***

### 2. Testing (Pre-Merge)

**Gate:** All Tests Pass\
**Required Before:** Merging to main branch

#### Checklist

* \[ ] Unit tests written for new functionality
* \[ ] Integration tests pass
* \[ ] No failing tests in test suite
* \[ ] Test coverage > 70% for new code (target)
* \[ ] Edge cases covered
* \[ ] Error handling tested

#### Tools

* pytest for backend tests
* Jest/Vitest for frontend tests
* Coverage reporting tools

#### Current Status

⚠️ **MVP Phase:** Full test coverage not yet implemented. Critical paths should have tests.

***

### 3. Code Review

**Gate:** Approved by Reviewer\
**Required Before:** Merge approval

#### Checklist

* \[ ] Code reviewed by at least one other developer
* \[ ] All review comments addressed
* \[ ] Architecture decisions documented in [`decisions.md`](./decisions.md)
* \[ ] Breaking changes clearly documented
* \[ ] Migration path provided for breaking changes

#### Review Focus Areas

1. **Security:** No vulnerabilities introduced
2. **Performance:** No obvious performance issues
3. **Maintainability:** Code is readable and maintainable
4. **Architecture:** Follows established patterns
5. **Documentation:** Changes documented appropriately

***

### 4. Integration (Pre-Deploy)

**Gate:** Integration Tests Pass\
**Required Before:** Deploying to staging

#### Checklist

* \[ ] End-to-end tests pass
* \[ ] API contracts not broken
* \[ ] Frontend and backend integrate correctly
* \[ ] Database migrations successful (if any)
* \[ ] Configuration valid
* \[ ] Dependencies updated and compatible

#### Tools

* Integration test suite
* API contract testing
* Browser testing (Playwright/Cypress recommended)

***

### 5. Staging Validation

**Gate:** Staging Sign-Off\
**Required Before:** Production deployment

#### Checklist

* \[ ] Application runs in staging environment
* \[ ] Key user flows tested manually
* \[ ] Performance acceptable (load times < 3s)
* \[ ] No critical errors in logs
* \[ ] Security scan passed
* \[ ] Stakeholder approval obtained

#### Validation Scenarios

1. User can connect to BigQuery
2. Metadata catalog populates correctly
3. Graph visualization renders
4. AI chat responds appropriately
5. Error states display correctly

***

### 6. Production Readiness

**Gate:** Production Deployment Approved\
**Required Before:** Deploying to production

#### Checklist

* \[ ] Rollback plan documented
* \[ ] Monitoring and alerting configured
* \[ ] Documentation updated
* \[ ] Release notes prepared
* \[ ] Stakeholder communication sent
* \[ ] Support team briefed (if applicable)

#### Deployment Requirements

* Deployment runbook followed
* Database backup completed
* Rollback tested in staging
* Traffic routing plan confirmed
* Incident response plan ready

#### Current Readiness Assessment (2026-02-02)

**Status:** ✅ READY (Conditional)

**Assessment Summary:**

* ✅ **Security**: Secrets externalized (ADR-007), CORS configured via env vars, container runs as non-root.
* ✅ **Observability**: Structured JSON logging implemented.
* ✅ **CI/CD**: GitHub Actions pipeline (`deploy.yml`) created for linting/testing.
* ⚠️ **Build**: Local build verification still flagged with TAR\_ENTRY\_ERROR (npm), but CI pipeline is established to enforce quality.
* ⚠️ **Deployment**: Cloud Run deployment (`P1-DEP1`) is the final step using the new secure container image.

**Next Actions:**

1. Commit changes to git to trigger the new CI pipeline.
2. Deploy the secured container to Cloud Run.
3. Verify production logs in Cloud Logging.

***

## Quality Standards

### Code Quality

#### Python Backend

```python
# Good Example
def fetch_table_metadata(
    dataset_id: str,
    table_id: str,
    include_columns: bool = True
) -> TableMetadata:
    """
    Fetch metadata for a specific table.
    
    Args:
        dataset_id: The dataset identifier
        table_id: The table identifier
        include_columns: Whether to include column metadata
        
    Returns:
        TableMetadata object with table information
        
    Raises:
        ValueError: If dataset_id or table_id is invalid
        ConnectionError: If database connection fails
    """
    if not dataset_id or not table_id:
        raise ValueError("Dataset and table IDs are required")
    
    # Implementation...
    return metadata
```

#### TypeScript Frontend

```typescript
// Good Example
interface TableMetadata {
  datasetId: string;
  tableId: string;
  columns?: ColumnMetadata[];
  createdAt: Date;
  updatedAt: Date;
}

async function fetchTableMetadata(
  datasetId: string,
  tableId: string,
  includeColumns: boolean = true
): Promise<TableMetadata> {
  if (!datasetId || !tableId) {
    throw new Error('Dataset and table IDs are required');
  }
  
  // Implementation...
  return metadata;
}
```

### Documentation Quality

#### Required Documentation

1. **Code Comments:** Complex logic explained
2. **API Documentation:** All endpoints documented
3. **README Files:** Each major component has README
4. **Architecture Docs:** Design decisions recorded in [`decisions.md`](./decisions.md)
5. **Change Logs:** All changes tracked in [`changelog.md`](./changelog.md)

#### Documentation Standards

* Use Markdown for all documentation
* Keep docs in [`./doc/`](.) folder
* Update docs with code changes
* Include code examples where helpful
* Link to related documentation

***

## Performance Standards

### Response Time Targets

| Operation | Target | Maximum |
|-----------|--------|---------|
| API endpoint response | < 500ms | 2s |
| Page load | < 2s | 3s |
| Graph query | < 2s | 5s |
| Data fetch | < 1s | 3s |

### Resource Limits

| Resource | Development | Production |
|----------|-------------|------------|
| Memory per process | < 512MB | < 1GB |
| API rate limit | 100 req/min | 1000 req/min |
| Query timeout | 30s | 60s |
| File upload size | 10MB | 50MB |

***

## Security Standards

### Authentication & Authorization

* ✅ API keys stored in environment variables
* ✅ No credentials in code or git
* ⏳ OAuth 2.0 for user authentication (planned)
* ⏳ Role-based access control (planned)

### Data Security

* ✅ HTTPS for all communications
* ✅ Input validation on all endpoints
* ⏳ Data encryption at rest (planned)
* ⏳ Audit logging (planned)

### Dependency Security

* Regular security updates
* Snyk/Dependabot monitoring
* No known critical vulnerabilities
* License compliance checked

***

## Exception Process

### When to Request Exception

Quality gate exceptions may be requested for:

* Critical production hotfixes
* Time-sensitive demos
* Technical debt that will be addressed later

### Exception Request Process

1. Document in [`decisions.md`](./decisions.md):
   * What gate is being bypassed
   * Why exception is needed
   * Risk assessment
   * Remediation plan
2. Get approval from:
   * Tech lead
   * Product owner (if user-facing)
3. Create follow-up task in [`pm-board.md`](./pm-board.md)

### Example Exception

```markdown
## ADR-XXX: Skip unit tests for demo hotfix

**Date:** 2026-01-19
**Status:** Approved with remediation

**Context:** Critical demo in 2 hours, blank page bug blocking.

**Decision:** Deploy fix without full test coverage.

**Consequences:**
- Risk: Potential regression in other areas
- Mitigation: Manual testing of key flows
- Remediation: Write tests within 24 hours (task P0.5-T1)

**Approved By:** Tech Lead
```

***

## Metrics & Monitoring

### Quality Metrics (Target)

| Metric | Target | Current |
|--------|--------|---------|
| Test coverage | > 70% | ⏳ TBD |
| Build success rate | > 95% | ⏳ TBD |
| Code review time | < 24h | ⏳ TBD |
| Bug escape rate | < 5% | ⏳ TBD |
| Mean time to recovery | < 1h | ⏳ TBD |

### Monitoring (Planned)

* Application performance monitoring (APM)
* Error tracking and alerting
* User analytics
* Infrastructure monitoring
* Log aggregation

***

## Continuous Improvement

### Retrospective Schedule

* After each major phase completion
* Monthly for ongoing work
* Ad-hoc for critical incidents

### Process Improvements

* Review and update quality gates quarterly
* Adjust standards based on team feedback
* Document lessons learned in [`decisions.md`](./decisions.md)
* Share learnings across team

***

## MVP Phase Adaptations

**Current Phase:** Phase 0.5 - Stabilization

### Relaxed Requirements (Temporary)

* Full test coverage not required (target 70%+)
* Automated deployment not required
* Performance optimization deferred
* Security review simplified for MVP

### Maintained Requirements

* ✅ Code review for all changes
* ✅ No credentials in code
* ✅ Documentation updated
* ✅ Rollback plan documented
* ✅ Manual testing of critical paths

### Post-MVP Requirements

* Implement full test coverage
* Set up CI/CD pipeline
* Conduct security audit
* Implement monitoring and alerting
* Establish SLAs

***

**Maintenance:** Review and update this document quarterly or when processes change significantly. Keep standards realistic and achievable.
