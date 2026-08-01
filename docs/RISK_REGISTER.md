# MES Risk Register

**Document Type:** Risk Management  
**Version:** 1.0  
**Date:** 2026-08-01  
**Status:** Active  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document identifies, tracks, and manages project risks throughout the MES implementation lifecycle.

**Risk Scoring:**
- **Probability:** Low (1), Medium (2), High (3)
- **Impact:** Low (1), Medium (2), High (3)
- **Risk Score:** Probability × Impact (1-9)
- **Priority:** Score ≥6 = High, 3-5 = Medium, 1-2 = Low

---

## Active Risks

### R-001: Customer Changes Manufacturing Process During UAT

**Category:** Business  
**Probability:** Medium (2)  
**Impact:** High (3)  
**Risk Score:** 6 (High Priority)  
**Status:** ⏳ Active  
**Owner:** Project Manager  
**Identified:** 2026-08-01

**Description:**
Customer may request changes to manufacturing workflow, business rules, or warehouse structure during UAT phase, requiring significant rework.

**Triggers:**
- Customer feedback during UAT
- Process optimization requests
- Regulatory compliance changes

**Mitigation Strategy:**
- Formal Change Request process established
- Document all changes with impact assessment
- Freeze business rules before UAT (already done)
- Communicate change impact on timeline and cost

**Contingency Plan:**
- Prioritize changes (critical vs. nice-to-have)
- Defer non-critical changes to Phase 2
- Allocate 10% buffer for critical changes

**Current Status:**
- Business rules frozen (Version 1.0)
- Change management process documented
- Customer educated on change impact

---

### R-002: ERPNext v15 Patch Changes APIs

**Category:** Technical  
**Probability:** Low (1)  
**Impact:** High (3)  
**Risk Score:** 3 (Medium Priority)  
**Status:** ⏳ Active  
**Owner:** Technical Lead  
**Identified:** 2026-08-01

**Description:**
ERPNext v15 patches may change core APIs (Work Order, Job Card, Stock Entry) breaking MES integration.

**Triggers:**
- ERPNext version update
- API deprecation notices
- Breaking changes in patch notes

**Mitigation Strategy:**
- Lock tested ERPNext version (commit hash)
- Monitor ERPNext release notes
- Isolate ERPNext dependencies in Repository layer
- Comprehensive integration tests

**Contingency Plan:**
- Maintain ERPNext version compatibility matrix
- Quick patch development if API changes
- Fallback to previous stable version

**Current Status:**
- Repository layer isolates ERPNext dependencies
- Version locked to tested commit
- Integration tests in place

---

### R-003: Large Work Orders Impact Performance

**Category:** Performance  
**Probability:** Medium (2)  
**Impact:** Medium (2)  
**Risk Score:** 4 (Medium Priority)  
**Status:** ⏳ Active  
**Owner:** Developer A  
**Identified:** 2026-08-01

**Description:**
Work Orders with 50+ Job Cards or large BOMs may cause performance degradation in material readiness evaluation and dependency validation.

**Triggers:**
- Work Order with >50 operations
- BOM with >100 items
- Response time >3 seconds

**Mitigation Strategy:**
- Performance testing with large datasets (Sprint 10)
- Query optimization (TD-003)
- Caching implementation (TD-001)
- Performance budget defined (<2-3 seconds)

**Contingency Plan:**
- Pagination for large Job Card lists
- Async material evaluation
- Background processing for complex validations

**Current Status:**
- Performance targets defined
- Technical debt registered
- Testing planned for Sprint 10

---

### R-004: Incorrect BOM/Master Data Configuration

**Category:** Data  
**Probability:** High (3)  
**Impact:** High (3)  
**Risk Score:** 9 (High Priority)  
**Status:** ⏳ Active  
**Owner:** Functional Consultant  
**Identified:** 2026-08-01

**Description:**
Incorrect BOM structure, routing, or warehouse configuration may cause MES to fail or produce incorrect results.

**Triggers:**
- Missing operations in routing
- Incorrect warehouse assignments
- Missing Plant Floor configuration
- Incomplete BOM items

**Mitigation Strategy:**
- ERP Configuration Review before implementation (in progress)
- Data validation scripts
- Master data checklist
- Functional consultant review

**Contingency Plan:**
- Data correction scripts
- Manual data cleanup
- Temporary workarounds for critical issues

**Current Status:**
- ERP Configuration Review pending
- Validation scripts planned
- Master data checklist created

---

### R-005: Key Developer Unavailability

**Category:** Resource  
**Probability:** Medium (2)  
**Impact:** High (3)  
**Risk Score:** 6 (High Priority)  
**Status:** ⏳ Active  
**Owner:** Project Manager  
**Identified:** 2026-08-01

**Description:**
Key developer (Developer A, B, or C) becomes unavailable during critical sprint, delaying implementation.

**Triggers:**
- Illness
- Resignation
- Reassignment to other projects

**Mitigation Strategy:**
- Cross-training (backup assigned for each module)
- Comprehensive documentation
- Code review by multiple developers
- Knowledge sharing sessions

**Contingency Plan:**
- Activate backup developer
- Reprioritize sprint backlog
- Extend sprint duration if necessary

**Current Status:**
- Backup assignments documented
- Code reviews mandatory
- Documentation comprehensive

---

### R-006: Integration Issues Between Sprints

**Category:** Technical  
**Probability:** Medium (2)  
**Impact:** Medium (2)  
**Risk Score:** 4 (Medium Priority)  
**Status:** ⏳ Active  
**Owner:** Technical Lead  
**Identified:** 2026-08-01

**Description:**
Sprints 1-3 implemented separately may have integration issues when combined with Sprints 4-7.

**Triggers:**
- API incompatibilities
- Data model conflicts
- Service interface changes

**Mitigation Strategy:**
- Integration matrix tracking
- Continuous integration testing
- Stable service interfaces (frozen)
- Regular integration reviews

**Contingency Plan:**
- Dedicated integration sprint
- Refactoring if necessary
- Interface adapters

**Current Status:**
- Integration matrix created
- Service interfaces frozen
- Integration tests planned

---

### R-007: User Resistance to New Workflow

**Category:** Organizational  
**Probability:** High (3)  
**Impact:** Medium (2)  
**Risk Score:** 6 (High Priority)  
**Status:** ⏳ Active  
**Owner:** Business Owner  
**Identified:** 2026-08-01

**Description:**
Shop floor operators and supervisors may resist new MES workflow, preferring old manual processes.

**Triggers:**
- Negative feedback during UAT
- Low adoption rates
- Workarounds developed

**Mitigation Strategy:**
- Early user involvement in design
- Comprehensive training program
- Super-user identification
- Clear benefits communication

**Contingency Plan:**
- Phased rollout (one department at a time)
- Additional training sessions
- Feedback incorporation
- Incentives for adoption

**Current Status:**
- User-friendly design prioritized
- Training plan in development
- Super-users identified

---

### R-008: Scope Creep During Implementation

**Category:** Project Management  
**Probability:** Medium (2)  
**Impact:** High (3)  
**Risk Score:** 6 (High Priority)  
**Status:** ⏳ Active  
**Owner:** Project Manager  
**Identified:** 2026-08-01

**Description:**
Additional features or enhancements requested during implementation, expanding scope beyond Phase 1.

**Triggers:**
- "While you're at it" requests
- Competitive feature requests
- Process improvement ideas

**Mitigation Strategy:**
- Frozen business rules (85 rules documented)
- Formal change request process
- Version roadmap (Phase 2, 3 documented)
- Regular scope reviews

**Contingency Plan:**
- Defer to Phase 2 or 1.1+
- Prioritize against existing backlog
- Impact assessment for all requests

**Current Status:**
- Scope frozen (Version 1.0 baseline)
- Change process established
- Version roadmap published

---

## Risk Summary

### By Category

| Category | Count | High Priority | Medium Priority | Low Priority |
|----------|-------|---------------|-----------------|--------------|
| Business | 1 | 1 | 0 | 0 |
| Technical | 2 | 0 | 2 | 0 |
| Performance | 1 | 0 | 1 | 0 |
| Data | 1 | 1 | 0 | 0 |
| Resource | 1 | 1 | 0 | 0 |
| Organizational | 1 | 1 | 0 | 0 |
| Project Management | 1 | 1 | 0 | 0 |
| **Total** | **8** | **5** | **3** | **0** |

### By Priority

| Priority | Count | Percentage |
|----------|-------|------------|
| High (Score 6-9) | 5 | 63% |
| Medium (Score 3-5) | 3 | 37% |
| Low (Score 1-2) | 0 | 0% |

### Top 5 Risks

| ID | Risk | Score | Priority | Owner |
|----|------|-------|----------|-------|
| R-004 | Incorrect BOM/Master Data | 9 | High | Functional Consultant |
| R-001 | Customer Process Changes | 6 | High | Project Manager |
| R-005 | Key Developer Unavailable | 6 | High | Project Manager |
| R-007 | User Resistance | 6 | High | Business Owner |
| R-008 | Scope Creep | 6 | High | Project Manager |

---

## Risk Review Schedule

| Review Type | Frequency | Participants |
|-------------|-----------|--------------|
| Team Review | Every Sprint | All developers |
| Management Review | Monthly | PM, TL, Business Owner |
| Stakeholder Review | Quarterly | All stakeholders |
| Pre-UAT Review | Before UAT | All |
| Post-UAT Review | After UAT | All |

---

## Risk Closure Criteria

A risk is closed when:

1. ✅ Mitigation strategy implemented
2. ✅ Risk no longer applicable
3. ✅ Impact reduced to acceptable level
4. ✅ Stakeholders agree to close

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-01 | Development | Initial risk register creation |

---

## Related Documents

- PHASE1_STATUS_REPORT.md - Project status
- TECHNICAL_DEBT.md - Technical debt items
- KNOWN_LIMITATIONS.md - Known limitations
- DOCUMENTATION_GOVERNANCE.md - Governance policy
