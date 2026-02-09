# Rollback Policy

**Project:** Morpheus Intelligence Platform  
**Last Updated:** 2026-01-19  
**Status:** Active

---

## Overview

This document defines the rollback policy and procedures for the Morpheus Intelligence Platform. Every change must have a documented rollback strategy before implementation.

## Rollback Requirements

### Mandatory Rollback Documentation

Before making any change, you must:

1. **Create a rollback point** with one of the following:
   - Git commit reference (if git is available)
   - File-based rollback in `./rollback/<timestamp>/` (if git is not available)

2. **Document the rollback procedure** including:
   - What changed
   - How to undo the change
   - Any dependencies or prerequisites
   - Expected time to rollback

3. **Capture evidence** of the state before changes:
   - Configuration files
   - Code snapshots
   - Database schemas (if applicable)
   - Test results or logs

## Rollback Strategies

### Strategy 1: Git-Based Rollback (Preferred)

**When to Use:**  
When the project is in a git repository

**Process:**

1. **Before Changes:**
   ```bash
   git status
   git add -A
   git commit -m "checkpoint: before [description of change]"
   git rev-parse HEAD > rollback/current-commit.txt
   ```

2. **Rollback Procedure:**
   ```bash
   # Get the commit hash from documentation
   ROLLBACK_COMMIT=$(cat rollback/current-commit.txt)
   
   # Option A: Reset to previous commit (destructive)
   git reset --hard $ROLLBACK_COMMIT
   
   # Option B: Revert with a new commit (preserves history)
   git revert HEAD
   ```

3. **Documentation:**
   - Record commit hash in changelog
   - Link to commit in laststep.md
   - Tag critical commits for easy identification

### Strategy 2: File-Based Rollback (Current)

**When to Use:**  
When git is not available (current project state)

**Process:**

1. **Before Changes:**
   ```bash
   # Create rollback directory with timestamp
   mkdir -p ./rollback/YYYYMMDD-HHMMSS-description/
   ```

2. **Capture State:**
   - `notes.md` - What's changing and why
   - `file-manifest.txt` - List of affected files
   - `evidence.txt` - Before state, logs, test results
   - Copy or snapshot of files being changed

3. **Rollback Procedure:**
   - Read `notes.md` for rollback instructions
   - Restore files from snapshots if available
   - Follow manual rollback steps documented

4. **Documentation:**
   - Each rollback folder is self-contained
   - Reference in changelog and laststep.md

### Strategy 3: Database Rollback (Future)

**When to Use:**  
When database schema or data changes are involved

**Process:**

1. **Before Changes:**
   - Export current schema
   - Create database backup
   - Document migration scripts
   - Test rollback procedure on staging

2. **Rollback Procedure:**
   - Run reverse migration scripts
   - Restore from backup if necessary
   - Verify data integrity

## Rollback Directory Structure

```
rollback/
├── 20260119-043026-doc-reorganization/
│   ├── notes.md                    # What changed, how to rollback
│   ├── file-manifest.txt           # List of affected files
│   ├── evidence.txt                # Before state, logs
│   └── [file-snapshots]            # Copies of original files (if needed)
├── YYYYMMDD-HHMMSS-description/    # Next change
│   └── ...
└── current-commit.txt              # Latest git commit (if git available)
```

## Change Categories and Rollback Requirements

### Low-Risk Changes
**Examples:** Documentation updates, comments, formatting

**Requirements:**
- Minimum: Entry in changelog
- File-based rollback optional (but recommended)

### Medium-Risk Changes
**Examples:** New features, refactoring, dependency updates

**Requirements:**
- Mandatory rollback point
- Documentation in laststep.md
- File manifest and notes
- Testing before deployment

### High-Risk Changes
**Examples:** Database migrations, breaking API changes, security updates

**Requirements:**
- Mandatory rollback point with tested procedure
- Detailed rollback documentation
- Staged deployment with testing at each stage
- Rollback tested on staging environment first
- Approval from technical lead

## Rollback Testing

### Pre-Deployment Testing
1. Create rollback point
2. Apply changes in test environment
3. Test rollback procedure
4. Verify system returns to original state
5. Document any issues encountered

### Post-Deployment Validation
1. Monitor system for issues (15-30 minutes minimum)
2. Verify key functionality works
3. Check logs for errors
4. If issues detected, execute rollback immediately

## Emergency Rollback Procedure

### When to Execute Emergency Rollback
- Critical bug discovered in production
- Security vulnerability introduced
- System instability or crashes
- Data integrity issues

### Emergency Steps

1. **Immediate Actions:**
   - Stop deployments
   - Notify team
   - Access rollback documentation

2. **Execute Rollback:**
   - Follow documented rollback procedure
   - Verify each step
   - Test critical paths after rollback

3. **Post-Rollback:**
   - Document what went wrong
   - Update rollback procedures if needed
   - Plan fix for the issue
   - Schedule remediation

## Rollback Validation

After executing a rollback:

1. **Functional Validation:**
   - Test critical user paths
   - Verify API endpoints respond correctly
   - Check database integrity

2. **Technical Validation:**
   - Review error logs
   - Check performance metrics
   - Verify all services running

3. **Documentation:**
   - Update changelog with rollback event
   - Update laststep.md with current state
   - Document lessons learned in decisions.md

## Best Practices

### Do's
- ✅ Always create rollback point before changes
- ✅ Document rollback procedure before implementing
- ✅ Test rollback procedure when possible
- ✅ Keep rollback documentation up to date
- ✅ Include rollback reference in all change docs
- ✅ Communicate rollback procedures to team
- ✅ Archive old rollback folders (after 90 days)

### Don'ts
- ❌ Never skip rollback documentation
- ❌ Don't assume rollback will work without testing
- ❌ Don't delete rollback folders immediately after deploy
- ❌ Don't make multiple unrelated changes in one commit
- ❌ Don't rollback without understanding the impact
- ❌ Don't forget to update documentation after rollback

## Rollback Retention Policy

### Retention Schedule
- **Recent rollbacks (< 30 days):** Keep all files
- **Medium-term (30-90 days):** Keep documentation, archive snapshots
- **Long-term (> 90 days):** Keep notes.md only, compress rest

### Archive Process
```bash
# After 90 days, compress and archive
cd rollback/
tar -czf archived/YYYYMMDD-description.tar.gz YYYYMMDD-HHMMSS-description/
rm -rf YYYYMMDD-HHMMSS-description/
```

## Rollback Metrics

Track these metrics to improve process:
- Number of rollbacks per month
- Time to execute rollback
- Success rate of rollback procedures
- Issues discovered during rollback
- Root causes requiring rollbacks

## References

- [`./changelog.md`](./changelog.md) - All changes with rollback references
- [`../laststep.md`](../laststep.md) - Latest change and rollback info
- [`./decisions.md`](./decisions.md) - Architectural decisions affecting rollback

---

**Note:** This policy must be followed for all changes. Failure to document rollback procedures may result in delayed incident resolution and system downtime.
