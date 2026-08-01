# MES Exception Handling Rules

**Document Type:** Business Rules Specification  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Ready for Review  
**Project:** Tekson Manufacturing MES  
**ERPNext Version:** V15

---

## Overview

This document defines exception handling rules for the Tekson MES. These rules govern how the system responds to abnormal conditions during manufacturing execution.

All exception handling logic must implement these rules.

---

## Exception Categories

1. **Material Exceptions** (EX-MAT-001 to EX-MAT-010)
2. **Production Exceptions** (EX-PROD-001 to EX-PROD-010)
3. **Equipment Exceptions** (EX-EQP-001 to EX-EQP-010)
4. **Quality Exceptions** (EX-QUAL-001 to EX-QUAL-010)
5. **Cancellation Exceptions** (EX-CAN-001 to EX-CAN-010)
6. **System Exceptions** (EX-SYS-001 to EX-SYS-010)

---

## Material Exceptions

### EX-MAT-001: Material Shortage

**Scenario:** Required material not available in Department Warehouse when Job Card ready to start.

**Rule:**
- Job Card status = "Awaiting Material"
- Diagnostic message shows:
  - Item code and name
  - Required quantity
  - Available quantity
  - Shortage quantity
  - Responsible department (Stores)
- Production cannot start until material available

**Responsibility:**
- Stores: Transfer material to Department Warehouse
- Production: Wait for material
- MES: Block Job Card start, show diagnostic

**Resolution:**
```
Stores transfers material
        ↓
Department Warehouse updated
        ↓
MES validates Material Readiness
        ↓
Job Card status = "Ready to Start"
```

---

### EX-MAT-002: Partial Material Availability

**Scenario:** Some materials available, others not available.

**Rule:**
- Job Card status = "Awaiting Material"
- Diagnostic shows ALL missing materials
- Production cannot start until ALL materials available
- No partial starts allowed

**Rationale:**
- Prevents WIP buildup
- Ensures complete production capability
- Simplifies material tracking

---

### EX-MAT-003: Material Transfer Failure

**Scenario:** Stock Entry for Material Transfer fails or is cancelled.

**Rule:**
- If Transfer cancelled BEFORE production starts:
  - Job Card remains "Awaiting Material"
  - Stores must create new Transfer
- If Transfer cancelled AFTER production starts:
  - Production continues
  - Quality check required before completion
  - Supervisor approval required

**Responsibility:**
- Stores: Create replacement Transfer
- Supervisor: Approve continuation if production started
- Quality: Inspect if production continued

---

### EX-MAT-004: Wrong Material Transferred

**Scenario:** Stores transfers wrong material to Department Warehouse.

**Rule:**
- Production MUST NOT use wrong material
- Job Card status = "Awaiting Material"
- Stores must:
  - Return wrong material to source
  - Transfer correct material
- Quality inspection required for any accidental usage

**Responsibility:**
- Stores: Correct the transfer
- Production: Verify material before use
- Quality: Inspect if wrong material used

---

### EX-MAT-005: Damaged Material

**Scenario:** Material damaged during transfer or in Department Warehouse.

**Rule:**
- Damaged material MUST NOT be used
- Transfer to Reject Store
- Stores must transfer replacement material
- Quality must assess damage

**Responsibility:**
- Stores: Transfer replacement
- Quality: Assess and approve reject
- Production: Report damage immediately

---

### EX-MAT-006: Inventory Mismatch

**Scenario:** System shows material available, but physical count differs.

**Rule:**
- If physical < system:
  - Use physical quantity
  - Update system via Stock Reconciliation
  - Investigate variance
- If physical > system:
  - Update system via Stock Reconciliation
  - Use system quantity until updated

**Responsibility:**
- Stores: Initiate Stock Reconciliation
- Production: Use conservative quantity
- Quality: Investigate root cause

---

### EX-MAT-007: Expired Material

**Scenario:** Material has exceeded shelf life or expiry date.

**Rule:**
- Expired material MUST NOT be used
- Transfer to Reject Store
- Stores must transfer fresh material
- Quality must approve expiry extension if applicable

**Responsibility:**
- Stores: Remove expired material
- Quality: Approve/reject expiry extension
- Production: Report expired material

---

### EX-MAT-008: Alternate Material

**Scenario:** Specified material not available, alternate material available.

**Rule:**
- Alternate material requires Engineering approval
- Quality must approve substitution
- BOM may require temporary revision
- Traceability must record actual material used

**Responsibility:**
- Engineering: Approve alternate
- Quality: Validate alternate
- Production: Record actual material used

---

### EX-MAT-009: Material Reserved by Another WO

**Scenario:** Material needed but reserved by another Work Order.

**Rule:**
- Check reservation priority
- If higher priority WO:
  - Hold current WO
  - Notify Production Planner
- If equal priority:
  - First-come-first-served
  - Planner may reassign

**Responsibility:**
- Production Planner: Resolve conflict
- Stores: Enforce priority
- MES: Show reservation conflict

---

### EX-MAT-010: Common Component Shortage

**Scenario:** Common component (Fins, Turbulators) not available for multiple WOs.

**Rule:**
- Check global stock across all departments
- Allocate based on WO priority
- Production Planner decides allocation
- MES shows allocation status

**Responsibility:**
- Production Planner: Allocate common components
- Stores: Track allocations
- MES: Show allocation per WO

---

## Production Exceptions

### EX-PROD-001: Partial Job Card Completion

**Scenario:** Job Card completed for less than required quantity.

**Rule:**
- Partial completion ALLOWED
- Record actual completed quantity
- Remaining quantity can be:
  - Completed in same Job Card (rework)
  - Created as new Job Card
  - Written off as scrap (with approval)

**Responsibility:**
- Production: Record actual quantity
- Supervisor: Approve remaining quantity handling
- MES: Track partial completion

---

### EX-PROD-002: Over Production

**Scenario:** Job Card completed for more than required quantity.

**Rule:**
- Over production ALLOWED up to 10% tolerance
- >10% requires Supervisor approval
- Excess quantity:
  - Added to FG Store
  - Traced to Work Order
  - May be used for future orders

**Responsibility:**
- Production: Report over production
- Supervisor: Approve if >10%
- Quality: Inspect over production
- Stores: Receipt excess to FG

---

### EX-PROD-003: Under Production

**Scenario:** Job Card completed for significantly less than required quantity.

**Rule:**
- Under production >10% requires investigation
- Root cause must be documented
- Remaining quantity handling:
  - New Job Card
  - Write off as scrap
  - Accept as-is (with Customer approval)

**Responsibility:**
- Production: Report under production
- Quality: Investigate root cause
- Supervisor: Decide remaining quantity handling

---

### EX-PROD-004: Wrong Operation Performed

**Scenario:** Operator performs wrong operation or skips operation.

**Rule:**
- Job Card status = "Quality Hold"
- Quality must assess impact
- Rework may be required
- Process deviation must be documented

**Responsibility:**
- Quality: Assess impact
- Production: Perform rework if required
- Supervisor: Document deviation

---

### EX-PROD-005: Operation Sequence Violation

**Scenario:** Operator attempts to start operation before previous operation complete.

**Rule:**
- MES blocks operation start
- Diagnostic shows blocking operation
- Supervisor override NOT allowed
- Previous operation must be completed first

**Responsibility:**
- MES: Block start automatically
- Production: Complete previous operation
- Supervisor: Monitor sequence compliance

---

### EX-PROD-006: Incorrect Parameters Used

**Scenario:** Operator uses incorrect machine parameters or settings.

**Rule:**
- Production MUST STOP immediately
- Quality must assess impact
- Rework or scrap decision required
- Parameter deviation documented

**Responsibility:**
- Production: Stop and report
- Quality: Assess product impact
- Supervisor: Document deviation

---

### EX-PROD-007: Unreported Production

**Scenario:** Production completed but not reported in system.

**Rule:**
- Back-reporting ALLOWED with Supervisor approval
- Actual completion time recorded
- Reason for delay documented
- Quality check required

**Responsibility:**
- Production: Report immediately upon discovery
- Supervisor: Approve back-reporting
- Quality: Verify quality

---

### EX-PROD-008: Duplicate Production Reporting

**Scenario:** Same production quantity reported twice.

**Rule:**
- System prevents duplicate reporting
- If duplicate occurs:
  - Reverse duplicate entry
  - Investigate root cause
  - Corrective action required

**Responsibility:**
- Supervisor: Reverse duplicate
- Production: Prevent recurrence
- Quality: Verify actual quantity

---

### EX-PROD-009: Production Without Job Card

**Scenario:** Production performed without Job Card in system.

**Rule:**
- Production MUST NOT start without Job Card
- If occurred:
  - Quality hold required
  - Retroactive Job Card creation
  - Supervisor approval required
  - Root cause investigation

**Responsibility:**
- Quality: Place on hold
- Supervisor: Approve retroactive JC
- Production: Investigate root cause

---

### EX-PROD-010: Unauthorized Substitution

**Scenario:** Operator substitutes material or process without approval.

**Rule:**
- Production placed on Quality Hold
- Engineering must approve substitution
- Quality must inspect product
- Disciplinary action may apply

**Responsibility:**
- Quality: Place on hold
- Engineering: Evaluate substitution
- Supervisor: Investigate and document

---

## Equipment Exceptions

### EX-EQP-001: Machine Breakdown

**Scenario:** Machine/equipment fails during production.

**Rule:**
- Job Card status = "On Hold"
- Production Planner decides:
  - Wait for repair
  - Move to alternate workstation
  - Postpone production
- Downtime recorded

**Responsibility:**
- Maintenance: Repair equipment
- Production Planner: Reschedule
- Production: Record downtime

---

### EX-EQP-002: Workstation Unavailable

**Scenario:** Assigned workstation not available (occupied, maintenance, etc.).

**Rule:**
- Check alternate workstations with same Workstation Type
- If available:
  - Reassign Job Card
  - Update Workstation in system
- If not available:
  - Hold production
  - Notify Production Planner

**Responsibility:**
- Production Planner: Find alternate
- Production: Update system
- Supervisor: Approve reassignment

---

### EX-EQP-003: Alternate Workstation Required

**Scenario:** Primary workstation cannot perform operation, alternate needed.

**Rule:**
- Alternate workstation MUST have same Workstation Type
- Capability check required
- Quality may require first-article inspection
- Update system with actual workstation

**Responsibility:**
- Production: Find alternate
- Quality: First-article inspection if required
- Supervisor: Approve alternate

---

### EX-EQP-004: Tooling Not Available

**Scenario:** Required tooling, fixtures, or dies not available.

**Rule:**
- Production CANNOT start
- Job Card status = "Awaiting Resources"
- Tool Room must provide tooling
- Delay recorded

**Responsibility:**
- Tool Room: Provide tooling
- Production: Report delay
- Supervisor: Expedite if critical

---

### EX-EQP-005: Calibration Expired

**Scenario:** Equipment calibration has expired.

**Rule:**
- Equipment MUST NOT be used
- Quality must approve emergency calibration
- Or equipment must be recalibrated
- Production delayed until calibrated

**Responsibility:**
- Quality: Approve/Reject use
- Maintenance: Recalibrate
- Production: Wait for calibration

---

## Quality Exceptions

### EX-QUAL-001: Quality Rejection During Production

**Scenario:** Quality inspection rejects production during Job Card execution.

**Rule:**
- Job Card status = "Quality Hold"
- Rejected quantity transferred to Reject Store
- Rework may be authorized
- Or scrap with approval

**Responsibility:**
- Quality: Place on hold
- Production: Perform rework or scrap
- Supervisor: Approve disposition

---

### EX-QUAL-002: First Article Inspection Failed

**Scenario:** First article inspection fails.

**Rule:**
- Production MUST STOP
- Machine setup must be corrected
- New first article required
- All previous pieces may be rejected

**Responsibility:**
- Quality: Reject first article
- Production: Correct setup
- Supervisor: Authorize restart

---

### EX-QUAL-003: In-Process Inspection Failed

**Scenario:** In-process quality check fails.

**Rule:**
- Production暂停 (pause)
- Root cause investigation
- Correction required
- Re-inspection required

**Responsibility:**
- Quality: Report failure
- Production: Correct issue
- Quality: Re-inspect

---

### EX-QUAL-004: Final Inspection Failed

**Scenario:** Final inspection fails before Work Order completion.

**Rule:**
- Work Order status = "Quality Hold"
- Rework authorized
- Or downgrade to lower grade
- Or scrap

**Responsibility:**
- Quality: Place on hold
- Production: Rework
- Supervisor: Decide disposition

---

## Cancellation Exceptions

### EX-CAN-001: Job Card Cancellation

**Scenario:** Job Card must be cancelled before completion.

**Rule:**
- Cancellation ALLOWED with Supervisor approval
- If production started:
  - Record actual production
  - Transfer consumed material to WIP
  - Create new Job Card for remaining qty
- If production not started:
  - Cancel Job Card
  - Return material to Stores

**Responsibility:**
- Supervisor: Approve cancellation
- Production: Record actuals
- Stores: Handle material return

---

### EX-CAN-002: Work Order Cancellation

**Scenario:** Work Order must be cancelled before completion.

**Rule:**
- Cancellation ALLOWED with Production Manager approval
- All Job Cards cancelled or completed
- Material returned to Stores
- WIP cleared
- FG receipt reversed if applicable

**Responsibility:**
- Production Manager: Approve cancellation
- Production: Complete/cancel Job Cards
- Stores: Handle material return
- Quality: Final disposition

---

### EX-CAN-003: Production Plan Cancellation

**Scenario:** Production Plan cancelled after Work Orders created.

**Rule:**
- All associated Work Orders cancelled
- Follow EX-CAN-002 for each WO
- Material returned to original source
- Capacity released

**Responsibility:**
- Production Planner: Cancel Plan
- Supervisor: Cancel Work Orders
- Stores: Handle returns

---

## System Exceptions

### EX-SYS-001: Stock Entry Creation Failure

**Scenario:** MES cannot create Stock Entry automatically.

**Rule:**
- Error logged with full details
- Manual Stock Entry creation required
- Supervisor notified
- System admin notified

**Responsibility:**
- Supervisor: Create manual Stock Entry
- IT: Investigate system failure
- Production: Report issue

---

### EX-SYS-002: Material Readiness Check Failure

**Scenario:** Material Readiness Engine fails or times out.

**Rule:**
- Conservative approach: Assume NOT ready
- Job Card status = "Awaiting Validation"
- System admin notified
- Manual validation allowed with approval

**Responsibility:**
- IT: Fix system issue
- Supervisor: Approve manual validation
- Production: Wait for resolution

---

### EX-SYS-003: Dependency Validation Failure

**Scenario:** Dependency Engine fails to validate previous operations.

**Rule:**
- Conservative approach: Block start
- Job Card status = "Awaiting Validation"
- Manual check of previous operations required
- Supervisor approval required

**Responsibility:**
- IT: Fix system issue
- Supervisor: Manual validation
- Production: Wait for resolution

---

### EX-SYS-004: Data Inconsistency

**Scenario:** System detects data inconsistency (e.g., WO qty ≠ sum of JC qty).

**Rule:**
- Warning logged
- Production can continue
- Data correction required
- Root cause investigation

**Responsibility:**
- IT: Investigate inconsistency
- Supervisor: Approve data correction
- Production: Report issue

---

### EX-SYS-005: Performance Degradation

**Scenario:** System performance degrades (slow queries, timeouts).

**Rule:**
- IT notified immediately
- Caching may be enabled
- Background jobs may be paused
- Users notified of delay

**Responsibility:**
- IT: Resolve performance issue
- Production: Report delays
- Supervisor: Prioritize critical work

---

## Exception Handling Principles

### Principle 1: Safety First

Never compromise product quality or safety to meet production targets.

### Principle 2: Document Everything

Every exception must be documented with:
- Exception type
- Timestamp
- People involved
- Resolution
- Root cause (if known)

### Principle 3: Escalation Path

Every exception has a clear escalation path:
```
Operator → Supervisor → Department Head → Production Manager
```

### Principle 4: Conservative Approach

When in doubt, take conservative approach:
- Block production rather than risk quality
- Require approval rather than assume
- Investigate rather than ignore

### Principle 5: Traceability

Every exception must maintain traceability:
- What happened
- When it happened
- Who was involved
- How it was resolved
- What was the impact

---

## Exception Matrix

| Exception | Can Production Continue? | Approval Required | Quality Check Required |
|-----------|-------------------------|-------------------|----------------------|
| EX-MAT-001: Material Shortage | ❌ No | Stores | No |
| EX-MAT-002: Partial Material | ❌ No | Stores | No |
| EX-MAT-003: Transfer Failure | ⚠️ If started | Supervisor | ✅ Yes |
| EX-PROD-001: Partial Completion | ✅ Yes | Supervisor | No |
| EX-PROD-002: Over Production | ✅ Yes | Supervisor (>10%) | ✅ Yes |
| EX-PROD-003: Under Production | ⚠️ Investigate | Supervisor | ✅ Yes |
| EX-EQP-001: Machine Breakdown | ❌ No | Planner | No |
| EX-QUAL-001: Quality Rejection | ❌ No | Supervisor | ✅ Yes |
| EX-CAN-001: Job Card Cancel | ⚠️ Record actuals | Supervisor | ✅ Yes |
| EX-CAN-002: Work Order Cancel | ❌ No | Production Manager | ✅ Yes |

---

## Implementation Notes

### Logging Requirements

Every exception must be logged with:
- Exception code (e.g., EX-MAT-001)
- Timestamp
- Work Order number
- Job Card number
- Department
- People involved
- Resolution
- Root cause (if known)

### Diagnostic Messages

Every exception must show clear diagnostic:
- What happened
- Why it happened
- What to do next
- Who to contact

### Approval Workflow

Every exception requiring approval must:
- Identify approver
- Send notification
- Record approval timestamp
- Track approval status

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-31 | OSDuo Tech LLP | Initial exception handling specification |

**Approved By:** ___________________  
**Date:** ___________________

**Next Review:** After first UAT cycle

---

*This document is maintained in the repository and updated as new exception scenarios are identified.*
