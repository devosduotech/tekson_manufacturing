# UAT Acceptance Matrix

**Document Type:** Testing  
**Version:** 1.0  
**Date:** 2026-08-01  
**Status:** Controlled (Living Document)  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document defines User Acceptance Testing (UAT) test cases for all business rules. Each business rule must have corresponding UAT test cases with customer sign-off.

**Purpose:** Ensure all business rules are validated by business users before production release.

---

## UAT Process

### Phase 1: Preparation (Before UAT)

1. **Test Environment Setup**
   - UAT environment configured
   - Test data loaded
   - Users trained

2. **Test Case Review**
   - Business users review test cases
   - Test cases approved by business stakeholders

3. **UAT Schedule**
   - UAT dates scheduled
   - Users assigned to test cases
   - Sign-off deadlines set

### Phase 2: Execution (During UAT)

1. **Test Execution**
   - Users execute test cases
   - Results documented
   - Issues logged

2. **Issue Resolution**
   - Critical issues fixed
   - Re-testing performed
   - Sign-off updated

### Phase 3: Sign-Off (After UAT)

1. **UAT Completion**
   - All test cases executed
   - All critical issues resolved
   - Business sign-off obtained

2. **Production Readiness**
   - UAT report approved
   - Production deployment scheduled
   - Version 1.0 released

---

## UAT Test Cases by Business Rule

### Sprint 1: Material Readiness (MR-010, MR-011)

| Test ID | Business Rule | Test Case | Expected Result | Tester | Date | Status | Sign-Off |
|---------|---------------|-----------|-----------------|--------|------|--------|----------|
| **TC-MR-010-01** | MR-010 | Stores transfers materials to Department Warehouse (Welding) | Stock Entry created from Stores to WIP-W, status validated | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-MR-010-02** | MR-010 | Stores transfers materials to Department Warehouse (RA) | Stock Entry created from Stores to WIP-RA, status validated | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-MR-010-03** | MR-010 | Stores transfers materials to Department Warehouse (RP) | Stock Entry created from Stores to WIP-RP, status validated | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-MR-010-04** | MR-010 | Stores transfers materials to Department Warehouse (CNC) | Stock Entry created from Stores to WIP-CNC, status validated | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-MR-010-05** | MR-010 | Invalid warehouse (not department) rejected | Error: "Warehouse must be a department warehouse" | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-MR-011-01** | MR-011 | Cumulative availability check - All materials available | `is_ready = True`, no missing items | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-MR-011-02** | MR-011 | Cumulative availability check - Some materials missing | `is_ready = False`, missing items listed | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-MR-011-03** | MR-011 | Cumulative availability check - All materials missing | `is_ready = False`, all items in missing list | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-MR-011-04** | MR-011 | Cumulative availability includes parent WO completed qty | Parent completion increases available qty | | | ⬜ Pass ⬜ Fail | _______ |

---

### Sprint 2: Dependency Validation (DV-001, DV-002)

| Test ID | Business Rule | Test Case | Expected Result | Tester | Date | Status | Sign-Off |
|---------|---------------|-----------|-----------------|--------|------|--------|----------|
| **TC-DV-001-01** | DV-001 | Job Card creation - Previous operation completed | Job Card created successfully | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-DV-001-02** | DV-001 | Job Card creation - Previous operation in progress | Error: "Previous operation must be completed first" | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-DV-001-03** | DV-001 | Job Card creation - Previous operation not started | Error: "Previous operation must be completed first" | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-DV-001-04** | DV-001 | First operation Job Card creation (no previous) | Job Card created successfully | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-DV-002-01** | DV-002 | Material availability check - All materials available | Dependency validated, Job Card can proceed | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-DV-002-02** | DV-002 | Material availability check - Materials missing | Error: "Materials not available for operation" | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-DV-002-03** | DV-002 | Material availability check - Partial availability | Error with shortage details | | | ⬜ Pass ⬜ Fail | _______ |

---

### Sprint 3: Execution Engine (JC-001 to JC-005, WO-001, WO-002)

| Test ID | Business Rule | Test Case | Expected Result | Tester | Date | Status | Sign-Off |
|---------|---------------|-----------|-----------------|--------|------|--------|----------|
| **TC-JC-001-01** | JC-001 | Start Job Card - Sequential operation (Op 10 complete, starting Op 20) | Job Card status = "Work In Progress" | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-JC-001-02** | JC-001 | Start Job Card - Skip operation (Op 10 not complete, trying Op 30) | Error: "Operations must be completed sequentially" | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-JC-002-01** | JC-002 | Complete Job Card - Valid status transition | Status = "Completed", completion time recorded | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-JC-002-02** | JC-002 | Complete Job Card - Invalid status transition | Error: "Cannot complete Job Card in current status" | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-JC-003-01** | JC-003 | Complete Job Card - Triggers next operation | Next Job Card status = "Open" | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-JC-003-02** | JC-003 | Complete Job Card - Last operation | No next operation, Work Order completion check triggered | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-JC-004-01** | JC-004 | Complete Job Card - Department transfer created | Stock Entry created from current dept to next dept | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-JC-004-02** | JC-004 | Complete Job Card - Last operation transfer | Stock Entry created from current dept to finished goods | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-JC-005-01** | JC-005 | Complete Job Card - Reversal | Previous operation status restored, material transfer reversed | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-WO-001-01** | WO-001 | Parent WO completion - All child WOs complete | Parent WO status = "Completed" | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-WO-001-02** | WO-001 | Parent WO completion - Some child WOs incomplete | Parent WO status remains "Work In Progress" | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-WO-002-01** | WO-002 | Child WO completion - Updates parent WO progress | Parent WO % complete updated | | | ⬜ Pass ⬜ Fail | _______ |
| **TC-WO-002-02** | WO-002 | Child WO completion - Last child | Parent WO completion check triggered | | | ⬜ Pass ⬜ Fail | _______ |

---

### Sprint 4: Diagnostics & Messages (DM-001 to DM-004) - Planned

| Test ID | Business Rule | Test Case | Expected Result | Tester | Date | Status | Sign-Off |
|---------|---------------|-----------|-----------------|--------|------|--------|----------|
| **TC-DM-001-01** | DM-001 | Diagnostic message - Material shortage | User-friendly message with shortage details | | | ⬜ Not Tested | _______ |
| **TC-DM-002-01** | DM-002 | Diagnostic message - Dependency violation | User-friendly message with dependency details | | | ⬜ Not Tested | _______ |
| **TC-DM-003-01** | DM-003 | UI message formatting - Error | Red error banner with clear message | | | ⬜ Not Tested | _______ |
| **TC-DM-004-01** | DM-004 | Message log - All operations logged | Message Log entry created for all operations | | | ⬜ Not Tested | _______ |

---

### Sprint 5: Department Transfer Integration (WH-001 to WH-005) - Planned

| Test ID | Business Rule | Test Case | Expected Result | Tester | Date | Status | Sign-Off |
|---------|---------------|-----------|-----------------|--------|------|--------|----------|
| **TC-WH-001-01** | WH-001 | Department transfer - W to RA | Stock Entry W → RA created | | | ⬜ Not Tested | _______ |
| **TC-WH-002-01** | WH-002 | Department transfer - RA to RP | Stock Entry RA → RP created | | | ⬜ Not Tested | _______ |
| **TC-WH-003-01** | WH-003 | Department transfer - RP to CNC | Stock Entry RP → CNC created | | | ⬜ Not Tested | _______ |
| **TC-WH-004-01** | WH-004 | Department transfer - Ralu Weld | Stock Entry to Ralu Weld created | | | ⬜ Not Tested | _______ |
| **TC-WH-005-01** | WH-005 | Department transfer - Ralu In | Stock Entry to Ralu In created | | | ⬜ Not Tested | _______ |

---

## UAT Sign-Off Summary

### Sprint 1-3 (Implemented)

| Business Rule | Test Cases | Pass | Fail | Not Tested | Sign-Off Status |
|---------------|------------|------|------|------------|-----------------|
| MR-010 | 5 | | | 5 | ⬜ Pending |
| MR-011 | 4 | | | 4 | ⬜ Pending |
| DV-001 | 4 | | | 4 | ⬜ Pending |
| DV-002 | 3 | | | 3 | ⬜ Pending |
| JC-001 | 2 | | | 2 | ⬜ Pending |
| JC-002 | 2 | | | 2 | ⬜ Pending |
| JC-003 | 2 | | | 2 | ⬜ Pending |
| JC-004 | 2 | | | 2 | ⬜ Pending |
| JC-005 | 1 | | | 1 | ⬜ Pending |
| WO-001 | 2 | | | 2 | ⬜ Pending |
| WO-002 | 2 | | | 2 | ⬜ Pending |
| **Total** | **29** | **0** | **0** | **29** | **⬜ Pending** |

### Sprint 4-10 (Planned)

| Sprint | Business Rules | Test Cases | Pass | Fail | Not Tested | Sign-Off Status |
|--------|----------------|------------|------|------|------------|-----------------|
| Sprint 4 | DM-001 to DM-004 | 4 | | | 4 | ⬜ Not Started |
| Sprint 5 | WH-001 to WH-005 | 5 | | | 5 | ⬜ Not Started |
| Sprint 6 | 46 Exception Scenarios | 46 | | | 46 | ⬜ Not Started |
| Sprint 7 | Security Rules | TBD | | | TBD | ⬜ Not Started |
| Sprints 8-9 | UI/UX | TBD | | | TBD | ⬜ Not Started |
| Sprint 10 | Production Readiness | TBD | | | TBD | ⬜ Not Started |

---

## UAT Issue Log

| Issue ID | Test Case | Description | Severity | Status | Resolved By | Date |
|----------|-----------|-------------|----------|--------|-------------|------|
| ISSUE-001 | | | ⬜ Critical ⬜ High ⬜ Medium ⬜ Low | ⬜ Open ⬜ In Progress ⬜ Resolved ⬜ Closed | | |
| ISSUE-002 | | | ⬜ Critical ⬜ High ⬜ Medium ⬜ Low | ⬜ Open ⬜ In Progress ⬜ Resolved ⬜ Closed | | |

---

## UAT Approval

### Business User Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Production Manager | | | |
| Stores Manager | | | |
| Quality Manager | | | |
| Operations Head | | | |

### IT Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Technical Lead | | | |
| Project Manager | | | |

### Final UAT Approval

**UAT Status:** ⬜ Passed ⬜ Failed ⬜ Conditional

**Conditions (if any):**
```
_______________________________________________
_______________________________________________
```

**Production Release Approved:** ⬜ Yes ⬜ No

**Name:** _______________________  
**Signature:** _______________________  
**Date:** _______________________

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-01 | Development | Initial UAT acceptance matrix creation |
| | | | |

---

## Related Documents

- MES_IMPLEMENTATION_MATRIX.md - Sprint tracking
- RELEASE_CHECKLIST.md - Deployment checklist
- MES_TEST_STRATEGY.md - Testing approach
- KNOWN_LIMITATIONS.md - System limitations
