# Development Personas

**Project:** Morpheus Intelligence Platform  
**Last Updated:** 2026-01-19  
**Status:** Active

---

## Overview

This document defines the development personas used in the Code Mode Standard Operating Procedure (SOP). Each persona represents a specific role with distinct responsibilities, mindset, and focus areas. By explicitly adopting these personas during development, we ensure comprehensive coverage of all aspects of software delivery.

## The Four Personas

```
┌─────────────┐
│     PM      │  Defines WHAT and WHY
└──────┬──────┘
       │
       v
┌─────────────┐
│  HEAD DEV   │  Designs HOW (architecture)
└──────┬──────┘
       │
       v
┌─────────────┐
│ JUNIOR DEV  │  Implements (code)
└──────┬──────┘
       │
       v
┌─────────────┐
│     QA      │  Verifies (quality)
└─────────────┘
```

---

## [PM] - Product Manager

### Core Responsibility
**Define the problem, requirements, and success criteria before any technical work begins.**

### Mindset
- User-focused: What value are we creating?
- Business-focused: Why does this matter?
- Priority-focused: What's most important?
- Risk-aware: What could go wrong?

### Key Activities

#### 1. Problem Definition
```markdown
**Problem Statement:**
[Clear description of the problem]

**Impact:**
- Who is affected?
- How badly?
- Why now?

**Scope:**
- In scope: [What we'll address]
- Out of scope: [What we won't]
```

#### 2. Requirements Gathering
- Functional requirements: What must it do?
- Non-functional requirements: How well must it perform?
- Constraints: What limitations exist?
- Dependencies: What must happen first?

#### 3. Success Criteria
```markdown
**Acceptance Criteria:**
1. ✅ [Specific, measurable criterion]
2. ✅ [Specific, measurable criterion]
3. ✅ [Specific, measurable criterion]

**Definition of Done:**
- Feature works as specified
- Tests pass
- Documentation updated
- Code reviewed
```

#### 4. Prioritization
- 🔴 **Critical:** Blocking other work, must do now
- 🟡 **Medium:** Important but not urgent
- 🟢 **Low:** Nice to have

### Questions PM Asks
- What problem are we solving?
- For whom?
- Why is this the right priority?
- How will we measure success?
- What happens if we don't do this?
- What are the risks?
- What's the minimum viable solution?

### PM Deliverables
1. Clear problem statement
2. Prioritized requirements
3. Acceptance criteria
4. Risk assessment
5. Task breakdown in [`pm-board.md`](./pm-board.md)

### Example PM Output
```markdown
## [PM] Frontend Rendering Fix

**Problem:**
Users see blank pages when navigating to any route except home.
This blocks all user testing and demo preparation.

**Impact:**
- 100% of users affected on all pages
- Cannot demo to stakeholders
- Cannot test Phase 0.5 completion

**Root Cause Hypothesis:**
React Router v7 migration may have breaking changes in routing config.

**Acceptance Criteria:**
1. ✅ All pages load without blank screen
2. ✅ Navigation between pages works
3. ✅ No console errors on page load
4. ✅ Components render expected content

**Priority:** 🔴 Critical - Blocking Phase 0.5 completion

**Risk Assessment:**
- High: Fixes may introduce new bugs
- Medium: May require refactoring routing logic
- Low: Breaking changes to backend

**Tasks:**
1. Investigate routing configuration
2. Fix identified issues
3. Test all routes
4. Verify no regressions
```

---

## [HEAD DEV] - Technical Lead

### Core Responsibility
**Design the technical approach, evaluate tradeoffs, and ensure architectural consistency.**

### Mindset
- Architecture-focused: How does this fit the system?
- Tradeoff-aware: What are we optimizing for?
- Future-thinking: What are long-term implications?
- Pragmatic: Good enough > perfect

### Key Activities

#### 1. Solution Design
- Propose technical approach
- Identify architectural patterns to use
- Define component boundaries
- Plan data flow

#### 2. Tradeoff Analysis
```markdown
**Approach A:**
✅ Pros: [Benefits]
❌ Cons: [Drawbacks]
📊 Score: X/10

**Approach B:**
✅ Pros: [Benefits]
❌ Cons: [Drawbacks]
📊 Score: Y/10

**Recommendation:** Approach A because [rationale]
```

#### 3. Technical Planning
- Break down into implementable chunks
- Identify dependencies
- Estimate complexity
- Plan rollback strategy

#### 4. Risk Mitigation
- Identify technical risks
- Propose mitigations
- Define fallback plans
- Set quality gates

### Questions HEAD DEV Asks
- How does this fit our architecture?
- What patterns should we use?
- What are the tradeoffs?
- What could break?
- How do we roll back if needed?
- What's the simplest approach?
- What are we NOT doing?
- Is this maintainable?

### HEAD DEV Deliverables
1. Technical approach
2. Architecture diagram (if needed)
3. Tradeoff analysis
4. Implementation plan
5. Rollback strategy
6. ADR in [`decisions.md`](./decisions.md) (for significant decisions)

### Example HEAD DEV Output
```markdown
## [HEAD DEV] Frontend Rendering Fix

**Technical Analysis:**

**Root Cause:**
React Router v7 changed from `BrowserRouter` to `RouterProvider` with
data router pattern. Our current routing setup is incompatible.

**Approach Options:**

**Option A: Update to RouterProvider pattern**
✅ Pros: Modern pattern, better data loading, type-safe
❌ Cons: Requires refactoring all routes, 2-3 hours work
📊 Complexity: Medium

**Option B: Downgrade to React Router v6**
✅ Pros: Quick fix, known pattern, 30 min work
❌ Cons: Technical debt, miss v7 features, future migration needed
📊 Complexity: Low

**Option C: Fix current BrowserRouter usage**
✅ Pros: Minimal changes
❌ Cons: May not be supported in v7, unclear if it will work
📊 Complexity: Low-Medium, uncertain

**Recommendation:** Option A

**Rationale:**
- One-time cost now vs. recurring debt
- v7 pattern is better for our use case
- Aligns with best practices
- Clean migration path

**Implementation Plan:**
1. Update routing configuration to RouterProvider
2. Convert routes to route objects
3. Update navigation calls
4. Test all routes
5. Verify no regressions

**Rollback Plan:**
Git commit before changes, can revert in < 1 minute

**Risks:**
- May uncover additional routing issues → Mitigate with incremental testing
- Breaking changes in route components → Mitigate with careful review
```

---

## [JUNIOR DEV] - Implementation Engineer

### Core Responsibility
**Implement the solution incrementally, clearly, and safely with no surprises.**

### Mindset
- Implementation-focused: Make it work
- Clarity-focused: Code is for humans
- Safety-focused: Small, reviewable changes
- Test-focused: Prove it works

### Key Activities

#### 1. Incremental Implementation
- Small, logical commits
- One change at a time
- No hidden refactoring
- Clear commit messages

#### 2. Code Quality
```python
# GOOD: Clear, simple, well-documented
def get_table_metadata(dataset_id: str, table_id: str) -> TableMetadata:
    """
    Fetch metadata for a specific table.
    
    Args:
        dataset_id: Dataset identifier
        table_id: Table identifier
        
    Returns:
        TableMetadata with table information
        
    Raises:
        ValueError: If IDs are invalid
    """
    if not dataset_id or not table_id:
        raise ValueError("Dataset and table IDs required")
    
    return self._fetch_metadata(dataset_id, table_id)
```

```python
# BAD: Clever, complex, undocumented
def gtm(d,t):
    return self._fm(d,t) if d and t else None
```

#### 3. Progressive Testing
- Test as you go
- Verify each change works
- Check for regressions
- Document test steps

#### 4. Status Updates
- Update [`pm-board.md`](./pm-board.md) as you progress
- Commit frequently
- Document blockers immediately

### Questions JUNIOR DEV Asks
- What am I implementing exactly?
- Is this the simplest approach?
- What could break?
- How do I test this?
- Does this match the design?
- Is this readable?
- What commit message explains this?
- Should I ask for help?

### JUNIOR DEV Deliverables
1. Working code
2. Clear commit history
3. Inline documentation
4. Basic test validation
5. Updated task status in [`pm-board.md`](./pm-board.md)

### Example JUNIOR DEV Output
```markdown
## [JUNIOR DEV] Frontend Rendering Fix - Implementation

**Step 1: Create route configuration**
✅ Created routes.tsx with RouterProvider pattern
```typescript
// routes.tsx
export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <PlatformOverview /> },
      { path: "customer360", element: <Customer360 /> },
      { path: "knowledge-graph", element: <KnowledgeGraphExplorer /> },
      { path: "data-nexus", element: <DataNexus /> },
      { path: "action-executor", element: <ActionExecutor /> },
    ],
  },
]);
```
Commit: "feat: Add RouterProvider route configuration"

**Step 2: Update main entry point**
✅ Updated index.tsx to use RouterProvider
```typescript
// index.tsx
import { RouterProvider } from 'react-router-dom';
import { router } from './routes';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <RouterProvider router={router} />
);
```
Commit: "feat: Switch to RouterProvider in index.tsx"

**Step 3: Update navigation**
✅ Updated App.tsx navigation to use Link components
- Verified no direct history manipulation
- All navigation uses Link from react-router-dom
Commit: "fix: Update navigation to use Link components"

**Step 4: Test each route**
✅ Tested locally:
- / → Loads correctly
- /customer360 → Loads correctly
- /knowledge-graph → Loads correctly
- /data-nexus → Loads correctly
- /action-executor → Loads correctly

No console errors, all navigation works.
```

---

## [QA] - Quality Assurance

### Core Responsibility
**Verify the solution works, find edge cases, and confirm acceptance criteria are met.**

### Mindset
- Skeptical: Assume it might be broken
- Thorough: Check all paths
- User-focused: How will users experience this?
- Edge-case-focused: What hasn't been tested?

### Key Activities

#### 1. Test Planning
- Review acceptance criteria
- Identify test scenarios
- Plan edge cases
- Determine test data needed

#### 2. Test Execution
```markdown
**Test Scenarios:**

1. ✅ Happy Path
   - Input: [Normal input]
   - Expected: [Success]
   - Actual: [Success] ✓

2. ⚠️ Edge Case: Empty Input
   - Input: [Empty string]
   - Expected: [Error message]
   - Actual: [Crashes] ✗ BUG FOUND

3. ✅ Edge Case: Special Characters
   - Input: [SQL injection attempt]
   - Expected: [Sanitized/rejected]
   - Actual: [Sanitized] ✓
```

#### 3. Regression Testing
- Test related functionality
- Verify nothing else broke
- Check error handling
- Validate logging

#### 4. Acceptance Verification
- Map tests to acceptance criteria
- Confirm all criteria met
- Document any gaps
- Sign off or escalate

### Questions QA Asks
- Does it meet acceptance criteria?
- What edge cases exist?
- What could go wrong?
- How does it fail?
- Are errors handled gracefully?
- What about performance?
- What did we miss?
- Is it actually usable?

### QA Deliverables
1. Test results
2. Bug reports (if any)
3. Edge cases identified
4. Acceptance criteria verification
5. Recommendation (approve/reject)

### Example QA Output
```markdown
## [QA] Frontend Rendering Fix - Verification

**Acceptance Criteria Verification:**

1. ✅ All pages load without blank screen
   - Tested: All 5 routes load correctly
   - Evidence: Screenshots in rollback folder

2. ✅ Navigation between pages works
   - Tested: All navigation links functional
   - Tested: Browser back/forward buttons work
   - Tested: Direct URL access works

3. ✅ No console errors on page load
   - Verified: Clean console on all pages
   - Checked: No warning or error messages

4. ✅ Components render expected content
   - Platform Overview: Shows dashboard ✓
   - Customer 360: Shows customer view ✓
   - Knowledge Graph: Shows graph placeholder ✓
   - Data Nexus: Shows data explorer ✓
   - Action Executor: Shows action interface ✓

**Edge Cases Tested:**

1. ✅ Refresh on nested route
   - Result: Page maintains state, no blank screen

2. ✅ Invalid route (404 handling)
   - Result: ⚠️ No 404 page configured
   - Recommendation: Add 404 route (low priority)

3. ✅ Fast navigation (click spam)
   - Result: Navigation stable, no crashes

4. ✅ Deep linking
   - Result: All routes accessible via direct URL

**Regression Testing:**

1. ✅ Backend API calls still work
2. ✅ State management intact
3. ✅ Component props passing correctly
4. ✅ Styling not broken

**Bugs Found:**
- Minor: No 404 page (low priority, not blocking)

**Performance:**
- Initial load: < 1s ✓
- Navigation: < 100ms ✓

**Recommendation:** ✅ APPROVED
All acceptance criteria met. Minor issue (404) can be addressed in Phase 1.

**Risk Assessment:**
- Low risk: Changes isolated to routing
- Well-tested: All main flows verified
- Rollback available: Clean git commit

**Sign-off:** Phase 0.5 frontend rendering COMPLETE
```

---

## Using Personas Effectively

### In Practice

#### Individual Development
Even when working alone, explicitly adopt each persona in sequence:
1. **[PM]** What am I solving?
2. **[HEAD DEV]** How should I solve it?
3. **[JUNIOR DEV]** Implement it clearly
4. **[QA]** Did I really solve it?

#### Team Development
- Different people can take different personas
- Everyone reviews output from each persona's perspective
- Personas help identify gaps in thinking

### Persona Anti-Patterns

❌ **Skip PM:** Jump straight to coding
- Result: Solve wrong problem

❌ **Skip HEAD DEV:** No design phase
- Result: Technical debt, inconsistent architecture

❌ **Skip JUNIOR DEV mindset:** Clever over clear
- Result: Unmaintainable code

❌ **Skip QA:** Assume it works
- Result: Bugs in production

---

## Persona Cheat Sheet

| Persona | Focus | Question | Output |
|---------|-------|----------|--------|
| **PM** | Problem | "What & Why?" | Requirements, priorities |
| **HEAD DEV** | Design | "How?" | Architecture, tradeoffs |
| **JUNIOR DEV** | Code | "Implement" | Working, clear code |
| **QA** | Quality | "Does it work?" | Test results, bugs |

---

## Evolution & Feedback

### When to Adapt Personas

- **Small bugs:** Lightweight version (faster)
- **Large features:** Full depth (thorough)
- **Hotfixes:** May skip/combine personas with documented exception

### Continuous Improvement

- Retrospect on persona effectiveness
- Adjust based on team feedback
- Document improvements in [`decisions.md`](./decisions.md)

---

**Maintenance:** Review persona definitions quarterly. Update based on team experience and project evolution.
