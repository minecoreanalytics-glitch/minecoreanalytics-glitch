# Rollback Notes: Security Hardening (2026-02-02)

**Change Description:**

* Externalizing CORS configuration and Google Credentials.
* Replacing `print` with structured JSON logging.
* Updating Dockerfile to run as non-root user.

**Files Affected:**

* `backend/main.py`
* `backend/Dockerfile`

**Rollback Procedure:**

1. Restore files from this directory:
   ```bash
   cp rollback/20260202-security-hardening/main.py backend/main.py
   cp rollback/20260202-security-hardening/Dockerfile backend/Dockerfile
   ```
2. Verify application starts with `temp_creds.json` present (as the old logic relied on it).
