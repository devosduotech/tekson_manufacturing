# Enhancement Backlog - Phase 1 MES

**Document ID:** MES-EB-001  
**Version:** 1.0  
**Date:** August 2, 2026  
**Status:** Active  
**Owner:** Project Manager  

---

## Purpose

This document captures all enhancement requests, ideas, and improvements identified **during** Phase 1 implementation. These items are **intentionally deferred** to maintain the business process freeze and ensure timely UAT completion.

**Classification:**
- **Phase 1.1:** Operational efficiency enhancements (post-UAT, pre-production)
- **Phase 2:** Productivity improvements (future releases)
- **Future:** Strategic enhancements (long-term roadmap)

---

## Backlog Items

### EH-001: Stores Picking List

**Priority:** HIGH  
**Target Phase:** Phase 1.1  
**Status:** Deferred  

**Description:**
Consolidated picking list for Stores department showing all material requirements for the day's released Work Orders.

**Current State:**
- Stores opens individual Work Orders
- Creates Material Transfer manually for each WO
- Time-consuming, prone to oversight

**Future State:**
- Daily dashboard showing all released WOs
- Consolidated view by:
  - Raw Material Stores items
  - BOF Stores items
  - Department-wise grouping
- Single-click Material Transfer generation
- Shortage report (what's not available)

**Benefits:**
- 60-70% reduction in Stores transaction time
- Better visibility of daily material requirements
- Easier shortage identification

**Dependencies:** None  
**Complexity:** Medium  
**Estimated Effort:** 3-5 days  

---

### EH-002: Consolidated Material Issue

**Priority:** HIGH  
**Target Phase:** Phase 1.1  
**Status:** Deferred  

**Description:**
Allow Stores to issue materials for multiple Work Orders in a single Stock Entry transaction.

**Current State:**
- One Stock Entry per Work Order
- Multiple transactions for common materials

**Future State:**
- Single Stock Entry can serve multiple WOs
- System auto-splits quantities per WO in background
- Maintains WO-level traceability
- Reduces transaction count

**Benefits:**
- Fewer Stock Entries to manage
- Faster material issue process
- Reduced data entry

**Dependencies:** EH-001  
**Complexity:** Medium  
**Estimated Effort:** 4-6 days  

---

### EH-003: Department Material Replenishment Dashboard

**Priority:** MEDIUM  
**Target Phase:** Phase 1.1  
**Status:** Deferred  

**Description:**
Real-time dashboard showing Department WIP levels, consumption rates, and replenishment needs.

**Features:**
- Current WIP balance by department
- Consumption trend (last 7 days)
- Replenishment alerts (when WIP < threshold)
- Pending Material Transfers
- Material Request generation (one-click)

**Benefits:**
- Proactive replenishment
- Prevents production stoppages
- Better inventory visibility

**Dependencies:** None  
**Complexity:** Medium  
**Estimated Effort:** 5-7 days  

---

### EH-004: Barcode Material Issue

**Priority:** MEDIUM  
**Target Phase:** Phase 2  
**Status:** Deferred  

**Description:**
Barcode scanning for material issue transactions in Stores.

**Features:**
- Scan item barcode
- Scan warehouse location
- Auto-populate Stock Entry
- Reduce manual data entry errors

**Benefits:**
- Faster material issue
- Reduced errors
- Better traceability

**Dependencies:** Barcode infrastructure  
**Complexity:** High  
**Estimated Effort:** 10-15 days  

---

### EH-005: Handheld Shop Floor Interface

**Priority:** LOW  
**Target Phase:** Phase 2  
**Status:** Deferred  

**Description:**
Mobile/tablet interface for operators to view Job Cards, start/complete operations, and report issues.

**Features:**
- Job Card list (filtered by operator/department)
- Start/Complete buttons
- Quantity entry
- Issue reporting
- Real-time status updates

**Benefits:**
- Shop floor mobility
- Real-time data capture
- Reduced paperwork

**Dependencies:** Hardware procurement  
**Complexity:** High  
**Estimated Effort:** 15-20 days  

---

### EH-006: Planner Production Buckets

**Priority:** LOW  
**Target Phase:** Phase 2  
**Status:** Deferred  

**Description:**
Allow Planner to define production time buckets (daily, weekly, shift-wise) for better scheduling.

**Features:**
- Shift definition (Morning, Afternoon, Night)
- Daily production targets
- Weekly planning view
- Capacity planning per bucket

**Benefits:**
- Better production planning
- Capacity visibility
- Shift-wise tracking

**Dependencies:** None  
**Complexity:** Medium  
**Estimated Effort:** 7-10 days  

---

### EH-007: Dynamic Work Order Consolidation

**Priority:** LOW  
**Target Phase:** Phase 2  
**Status:** Deferred  

**Description:**
Automatically consolidate Work Orders with common sub-assemblies during planning phase.

**Features:**
- Identify common sub-assemblies across WOs
- Suggest consolidated child WO creation
- Optimize material usage
- Reduce setup changes

**Benefits:**
- Reduced material waste
- Better batch planning
- Lower setup costs

**Dependencies:** Advanced planning logic  
**Complexity:** High  
**Estimated Effort:** 15-20 days  

---

### EH-008: Scrap Management Workflow

**Priority:** MEDIUM  
**Target Phase:** Phase 2  
**Status:** Deferred  

**Description:**
Formalized scrap handling workflow with approval, tracking, and inventory adjustment.

**Features:**
- Scrap generation reporting
- Scrap reason codes
- Approval workflow
- Scrap Store inventory tracking
- Scrap value calculation

**Benefits:**
- Better scrap tracking
- Cost visibility
- Process accountability

**Dependencies:** None  
**Complexity:** Medium  
**Estimated Effort:** 8-12 days  

---

### EH-009: Rework Job Card Flow

**Priority:** LOW  
**Target Phase:** Phase 2  
**Status:** Deferred  

**Description:**
Handle quality rework through dedicated Job Card workflow.

**Features:**
- Create rework Job Card from rejected QC
- Track rework operations
- Separate rework cost tracking
- Rwork completion approval

**Benefits:**
- Quality tracking
- Rework cost visibility
- Continuous improvement data

**Dependencies:** Quality module  
**Complexity:** Medium  
**Estimated Effort:** 10-12 days  

---

### EH-010: Management Priority Override

**Priority:** LOW  
**Target Phase:** Phase 2  
**Status:** Deferred  

**Description:**
Allow management to manually block/release Job Cards for priority changes.

**Features:**
- "Blocked by Management" status
- Release authorization
- Priority override with reason
- Audit trail

**Benefits:**
- Flexible production control
- Emergency priority handling
- Clear accountability

**Dependencies:** None  
**Complexity:** Low  
**Estimated Effort:** 3-5 days  

---

### EH-011: WIP Return to Stores Workflow

**Priority:** MEDIUM  
**Target Phase:** Phase 1.1  
**Status:** Deferred  

**Description:**
Formalized workflow for returning excess material from Department WIP to Stores.

**Features:**
- Return request initiation
- Approval workflow
- Stock Entry creation
- Department WIP reduction
- Stores inventory increase

**Benefits:**
- Better inventory accuracy
- Excess material recovery
- Cost reduction

**Dependencies:** None  
**Complexity:** Low  
**Estimated Effort:** 4-6 days  

---

### EH-012: Material Shortage Alerts

**Priority:** HIGH  
**Target Phase:** Phase 1.1  
**Status:** Deferred  

**Description:**
Proactive alerts when Material Readiness identifies shortages.

**Features:**
- Email notifications to Stores
- Dashboard alerts
- Escalation rules
- Shortage resolution tracking

**Benefits:**
- Faster response to shortages
- Prevents production delays
- Better communication

**Dependencies:** None  
**Complexity:** Low  
**Estimated Effort:** 3-5 days  

---

## Summary by Phase

### Phase 1.1 (Post-UAT, Pre-Production)

| ID | Enhancement | Priority | Effort |
|----|-------------|----------|--------|
| EH-001 | Stores Picking List | HIGH | 3-5 days |
| EH-002 | Consolidated Material Issue | HIGH | 4-6 days |
| EH-003 | Department Replenishment Dashboard | MEDIUM | 5-7 days |
| EH-011 | WIP Return to Stores | MEDIUM | 4-6 days |
| EH-012 | Material Shortage Alerts | HIGH | 3-5 days |

**Total Phase 1.1 Effort:** 19-29 days

---

### Phase 2 (Productivity Improvements)

| ID | Enhancement | Priority | Effort |
|----|-------------|----------|--------|
| EH-004 | Barcode Material Issue | MEDIUM | 10-15 days |
| EH-005 | Handheld Shop Floor Interface | LOW | 15-20 days |
| EH-006 | Planner Production Buckets | LOW | 7-10 days |
| EH-007 | Dynamic WO Consolidation | LOW | 15-20 days |
| EH-008 | Scrap Management | MEDIUM | 8-12 days |
| EH-009 | Rework Flow | LOW | 10-12 days |
| EH-010 | Management Priority Override | LOW | 3-5 days |

**Total Phase 2 Effort:** 68-94 days

---

## Prioritization Matrix

```
                    Impact
            Low ───────────── High
        ┌───────────┬───────────┐
        │           │           │
  High  │  EH-006   │  EH-001   │
        │  EH-007   │  EH-002   │
Effort  │           │  EH-012   │
        ├───────────┼───────────┤
        │           │           │
   Low  │  EH-005   │  EH-003   │
        │  EH-009   │  EH-011   │
        │           │  EH-010   │
        │           │  EH-004   │
        │           │  EH-008   │
        └───────────┴───────────┘
```

**Quick Wins (Low Effort, High Impact):**
- EH-003: Department Replenishment Dashboard
- EH-011: WIP Return to Stores
- EH-010: Management Priority Override
- EH-004: Barcode Material Issue (Medium effort)

---

## Approval & Sequencing

| Phase | Enhancements | Approval Required | Target Date |
|-------|--------------|-------------------|-------------|
| Phase 1.1 | EH-001, EH-002, EH-003, EH-011, EH-012 | Project Manager | Post-UAT |
| Phase 2 | All remaining | Customer + PM | Q4 2026 |

---

## Change Control

**Adding New Enhancements:**
1. Log enhancement request
2. Classify (Phase 1.1 / Phase 2 / Future)
3. Assign priority (High/Medium/Low)
4. Estimate effort
5. Add to backlog
6. **DO NOT IMPLEMENT** until freeze lifted

**Removing Enhancements:**
- Only by Project Manager approval
- Must document rationale
- Update this document

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Aug 2, 2026 | AI Assistant | Initial backlog creation |
| | | | |

---

**Status:** ✅ **ACTIVE**  
**Next Review:** After Customer UAT  

**Note:** This backlog grows as new ideas are identified. Implementation only begins after Phase 1 freeze is lifted.
