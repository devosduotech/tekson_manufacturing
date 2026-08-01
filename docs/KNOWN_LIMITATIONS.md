# Known Limitations

**Document Type:** Limitations Register  
**Version:** 1.0  
**Date:** 2026-08-01  
**Status:** Active  
**Project:** Tekson Manufacturing MES  
**Target Audience:** Customers, UAT Participants, Support Team  

---

## Overview

This document lists known limitations in the Phase 1 MES implementation. These are features or capabilities that are not yet complete but are planned for future sprints.

**Purpose:** Manage customer expectations during phased delivery.

---

## Current Limitations

### LIM-001: Department Dashboard Not Available

**Priority:** Medium  
**Category:** UI  
**Status:** ⏳ Planned (Sprint 9)  
**Impact:** Supervisors cannot view department-level status overview

**Description:**
The supervisor dashboard showing department status, exception alerts, and approval queue is not yet implemented.

**Current Workaround:**
- Use standard ERPNext Work Order list
- Manually check Job Card status by department filter

**Expected Resolution:**
- Sprint 9: MES UI - Supervisor Dashboard
- Expected completion: Week 7-8

**Customer Impact:**
- Moderate - Additional manual effort required
- No impact on core manufacturing execution

---

### LIM-002: Exception Handling Not Automated

**Priority:** High  
**Category:** Business Logic  
**Status:** ⏳ Planned (Sprint 6)  
**Impact:** Exceptions logged but not automatically handled or notified

**Description:**
While exceptions are logged, the automated exception handling workflow (notifications, resolution tracking, escalation) is not yet implemented.

**Current Workaround:**
- Monitor Error Log manually
- Handle exceptions through standard ERPNext processes

**Expected Resolution:**
- Sprint 6: Exception Handling Integration
- Expected completion: Week 5-6

**Customer Impact:**
- High - Requires manual monitoring
- Risk of delayed exception resolution

---

### LIM-003: Security Roles Not Configured

**Priority:** High  
**Category:** Security  
**Status:** ⏳ Planned (Sprint 7)  
**Impact:** All users have default permissions, no department-level restrictions

**Description:**
The 10-user role security matrix is defined but not yet configured. Department-level data scope is not enforced.

**Current Workaround:**
- Use ERPNext standard role-based permissions
- Manual supervision of user actions

**Expected Resolution:**
- Sprint 7: Security & Permissions
- Expected completion: Week 6-7

**Customer Impact:**
- High - Security and compliance risk
- Not suitable for production until resolved

---

### LIM-004: UI Not Implemented

**Priority:** Medium  
**Category:** UI  
**Status:** ⏳ Planned (Sprints 8-9)  
**Impact:** Users must use standard ERPNext Job Card interface

**Description:**
The custom MES UI with department-filtered lists, color-coded status, and action buttons is not yet implemented.

**Current Workaround:**
- Use standard ERPNext Job Card list and form
- Manual filtering by department

**Expected Resolution:**
- Sprints 8-9: MES UI
- Expected completion: Week 7-8

**Customer Impact:**
- Moderate - Reduced usability
- No impact on functionality

---

### LIM-005: Performance Not Validated at Scale

**Priority:** High  
**Category:** Performance  
**Status:** ⏳ Planned (Sprint 10)  
**Impact:** Performance targets not validated with production data volumes

**Description:**
Performance targets are defined (< 2-3 seconds) but not yet validated with production-scale data (1000+ Work Orders, 10000+ Job Cards).

**Current Workaround:**
- Monitor performance during UAT
- Optimize queries as needed

**Expected Resolution:**
- Sprint 10: Performance Testing
- Expected completion: Week 9

**Customer Impact:**
- High - Potential performance issues in production
- May require optimization after go-live

---

### LIM-006: Integration Not End-to-End Tested

**Priority:** High  
**Category:** Testing  
**Status:** ⏳ Planned (Sprint 10)  
**Impact:** Integration between all engines not fully validated

**Description:**
While individual engines (Material, Dependency, Execution) are tested, end-to-end integration across all components is not yet tested.

**Current Workaround:**
- Manual integration testing during UAT
- Monitor for integration issues

**Expected Resolution:**
- Sprint 10: Integration Testing
- Expected completion: Week 9

**Customer Impact:**
- High - Integration bugs may appear in UAT
- May delay go-live

---

### LIM-007: Department Transfer Workflow Partial

**Priority:** Medium  
**Category:** Business Logic  
**Status:** ⏳ Planned (Sprint 5)  
**Impact:** Department transfer workflow not fully automated

**Description:**
Material transfer from Stores to Department Warehouse is implemented, but the complete department transfer workflow (including completion detection and automatic suggestions) is not yet complete.

**Current Workaround:**
- Manual creation of Stock Entries
- Manual tracking of department transfers

**Expected Resolution:**
- Sprint 5: Department Transfer Integration
- Expected completion: Week 4-5

**Customer Impact:**
- Moderate - Additional manual steps
- No impact on core functionality

---

### LIM-008: Diagnostics Not User-Friendly

**Priority:** Low  
**Category:** UI  
**Status:** ⏳ Planned (Sprint 4)  
**Impact:** Error messages are technical, not user-friendly

**Description:**
Diagnostic messages are currently technical and developer-focused. User-friendly, context-aware messages are not yet implemented.

**Current Workaround:**
- Technical staff interpret error messages
- Create user-friendly explanations manually

**Expected Resolution:**
- Sprint 4: Diagnostics & Messages
- Expected completion: Week 3-4

**Customer Impact:**
- Low - Usability issue
- No impact on functionality

---

## Limitations Summary

| Category | Count | High Priority | Medium Priority | Low Priority |
|----------|-------|---------------|-----------------|--------------|
| UI | 2 | 0 | 2 | 1 |
| Business Logic | 2 | 1 | 1 | 0 |
| Security | 1 | 1 | 0 | 0 |
| Performance | 1 | 1 | 0 | 0 |
| Testing | 1 | 1 | 0 | 0 |
| **Total** | **7** | **4** | **3** | **1** |

---

## Resolution Timeline

```
Week 3-4:  LIM-008 (Diagnostics) ✅ Sprint 4
Week 4-5:  LIM-007 (Dept Transfer) ✅ Sprint 5
Week 5-6:  LIM-002 (Exceptions) ✅ Sprint 6
Week 6-7:  LIM-003 (Security) ✅ Sprint 7
Week 7-8:  LIM-001 (Dashboard) ✅ Sprint 9
           LIM-004 (UI) ✅ Sprint 9
Week 9:    LIM-005 (Performance) ✅ Sprint 10
           LIM-006 (Integration) ✅ Sprint 10
```

---

## Production Readiness Assessment

| Limitation | Blocks Production? | UAT Impact |
|------------|-------------------|------------|
| LIM-001: Dashboard | No | Low |
| LIM-002: Exceptions | **Yes** | High |
| LIM-003: Security | **Yes** | High |
| LIM-004: UI | No | Medium |
| LIM-005: Performance | **Yes** | High |
| LIM-006: Integration | **Yes** | High |
| LIM-007: Dept Transfer | No | Medium |
| LIM-008: Diagnostics | No | Low |

**Production Ready:** After Sprint 10 (all high-priority limitations resolved)

**UAT Ready:** After Sprint 7 (security implemented, core flow complete)

---

## Customer Communication

### For Management

> "The MES Phase 1 core manufacturing execution engine is complete and functional. Current limitations are primarily in UI, security configuration, and performance validation, which are scheduled for resolution in Sprints 4-10. The system is suitable for UAT after Sprint 7, with production readiness expected after Sprint 10."

### For UAT Participants

> "During UAT, you will use the core MES functionality with standard ERPNext interface. Some features like supervisor dashboard and automated exception handling will be demonstrated but not fully functional. Please focus UAT feedback on core manufacturing flow accuracy."

### For Support Team

> "Known limitations are documented and scheduled for resolution. Do not log these as bugs. Escalate only if limitations block critical business processes."

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-01 | Development | Initial creation |

---

## Related Documents

- PHASE1_STATUS_REPORT.md - Overall project status
- MES_IMPLEMENTATION_MATRIX.md - Sprint planning
- TECHNICAL_DEBT.md - Technical debt items
