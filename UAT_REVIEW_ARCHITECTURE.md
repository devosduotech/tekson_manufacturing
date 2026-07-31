# Teksons ERPNext V15 Manufacturing - UAT Review & Architecture

**Version:** 1.0  
**Date:** 31 July 2026  
**Document Type:** Technical Review & Architecture Design  
**Status:** Approved for Development

---

## 1. Objective

This document summarizes the technical discussions held after the first Manufacturing UAT.

The purpose of this review is to:

- Capture observations from the customer's UAT
- Correlate the observations with the exported system data
- Identify the root causes
- Finalize the architecture for the next phase of development
- Provide a technical reference for the development team before implementing further changes

---

## 2. UAT Evidence Reviewed

The following files and information formed the basis of today's discussion.

**Location:** `UAT/` folder in this repository

### 2.1 Customer UAT Screenshots

The customer shared screenshots demonstrating:
- Material validation failures
- Previous Operation validation
- Parent Job Cards becoming available before expected
- Job Card List behaviour
- Shop Floor execution

These screenshots were used to verify that the custom validation was functioning and to identify gaps in the dependency logic.

### 2.2 Work Order Export

**File:** `UAT/work_orders.xlsx` (or similar)

**Major observations:**
- Total Work Orders generated correctly
- Multi-level BOM explosion working correctly
- Routing generated correctly
- Parent and Child Work Orders created correctly
- Production hierarchy maintained

**Issues identified:**
Several Work Orders remained in "In Process" despite all Job Cards being completed:

| Work Order | Status | Issue |
|------------|--------|-------|
| WO/260714/0034 | In Process | All JC completed |
| WO/260714/0051 | In Process | All JC completed |
| WO/260714/0063 | In Process | All JC completed |
| WO/260714/0001 | In Process | All JC completed |
| WO/260714/0025 | In Process | All JC completed |

### 2.3 Job Card Export

**File:** `UAT/job_cards.xlsx` (or similar)

**Validated:**
- Operation sequence
- Dependency Status
- Material Status
- Start Status
- Completion Status
- Custom fields

The export confirmed that the custom fields introduced in the project were functioning as expected.

### 2.4 Stock Entry Export

**File:** `UAT/stock_entries.xlsx` (or similar)

**Analysed:**
- Material Transfer entries
- Manufacture entries
- Consumption entries
- Warehouse movements

**Key Finding:** This export is critical because the validation currently appears to rely on individual Stock Entries rather than evaluating cumulative material availability.

---

## 3. Positive Findings

The UAT confirmed that the following customizations are functioning correctly:

### 3.1 Routing
- Multi-level Routing ✓
- Operation Sequence ✓
- Job Card generation ✓

### 3.2 Previous Operation Validation
The custom dependency validation successfully prevented operators from starting operations whose predecessor Job Cards were incomplete.

### 3.3 Material Validation
Material availability validation correctly prevented production when required materials had not yet reached the designated WIP warehouse.

### 3.4 Multi-Level BOM Creation
The Production Plan correctly generated:
- Parent Work Orders
- Child Work Orders
- Sub Assembly Work Orders
- Shop Floor Execution

### 3.5 Overall Workflow
Operators were able to:
- Receive Job Cards
- Perform operations
- Record production
- Complete manufacturing transactions

**Conclusion:** The execution workflow proved stable enough for the first UAT.

---

## 4. Customer Observations & Issues

### Observation 1: Parent-Child Dependency Gap
**Issue:** CORE Assembly was allowed to start before all child components were completed.

**Example:** Parent WO started while child WOs were still pending.

**Root Cause:** System checks material availability via Stock Entry but doesn't verify if child/sub-assembly WOs are completed.

---

### Observation 2: Work Order Status Not Updating
**Issue:** Several completed Work Orders remained in "In Process".

**Affected Work Orders:**
```
WO/260714/0034
WO/260714/0051
WO/260714/0063
WO/260714/0001
WO/260714/0025
```

**Root Cause:** Work Order completion engine not triggering correctly after all Job Cards complete.

---

### Observation 3: Child Work Orders Not Started
**Issue:** The following Child Work Orders were still "Not Started":

```
WO/260714/0002
WO/260714/0003
WO/260714/0035
WO/260714/0052
WO/260714/0058
WO/260714/0062
```

**Root Cause:** Material readiness not properly evaluated for child components.

---

### Observation 4: Material Classification Gap
**Issue:** Material validation currently checks Stock Entry availability but does not adequately distinguish between:

| Material Type | Current Approach | Required Approach |
|---------------|------------------|-------------------|
| Raw Materials | Stock Entry check | Cumulative transfer check |
| Purchased Components | Stock Entry check | Cumulative transfer check |
| Manufactured Components | Stock Entry check | Available qty in WIP/Stores |
| Sub Assemblies | Stock Entry check | Available qty regardless of source WO |
| Common Components | Stock Entry check | Available stock across all WOs |

**Root Cause:** Validation checks individual Stock Entries instead of cumulative available quantity.

---

## 5. Customer Feedback Summary

**Verbal Feedback Points:**

1. **CORE Assembly Issue:** CORE assembly was allowed to start before completing child components (example case)

2. **WO Status Stuck:** All Job Cards of WO/260714/0034 completed but WO status is "In Process" still. Same with:
   - WO/260714/0051
   - WO/260714/0063
   - WO/260714/0001
   - WO/260714/0025

3. **Child WO Not Checked:** System not checking child components or sub-assembly WO/JC completion or availability

4. **Pending Child WOs:** Following WOs not yet started:
   - WO/260714/0002
   - WO/260714/0003
   - WO/260714/0062
   - WO/260714/0035
   - WO/260714/0052
   - WO/260714/0058

5. **Material Verification:** Need to differentiate material availability between:
   - Raw Material
   - Child Component / Sub Assembly
   
   Should check whether ALL stock entries made (transfer for raw material OR child component/sub-assembly)

6. **Multiple Stock Entries:** May have multiple stock entries to check for parent component WO

7. **Common Components:** Child components/sub-assemblies like Fins/Turbulators are common across multiple Finished Goods

8. **Flexible Workflow:** Every workstation doesn't need to follow same workflow - planning team may change final assembly priority based on material availability and customer needs

9. **Subcontracting:** Some items may be subcontracted outside for manufacturing. Can use Production Plan setup at planning stage if required

---

## 6. Initial Technical Conclusion

**Initial Hypothesis:**
Parent Work Orders should wait until Child Work Orders completed.

**Proposed Solution:**
Introduce Child Work Order Dependency Engine.

**Revised Understanding:**
Further discussion showed this approach would introduce additional business limitations and doesn't reflect real manufacturing practices.

---

## 7. Real Manufacturing Scenarios Identified

### 7.1 Common Components
Components such as:
- Fins
- Turbulators

Are produced in bulk and consumed across multiple Finished Goods.

**Therefore:** Parent WO → Specific Child WO is not always a valid dependency.

---

### 7.2 Dynamic Production Priorities
Planning may change production priorities daily based on:
- Customer commitments
- Material availability
- Capacity
- Dispatch schedules

**Therefore:** Execution should not force production according to original Production Plan sequence.

---

### 7.3 Existing Inventory
Many components may already exist in inventory from previous production batches.

**Therefore:** Execution should use available inventory rather than insisting on production from a newly created Child Work Order.

---

### 7.4 Partial Transfers
Materials are frequently transferred in multiple Stock Entries.

**Example:**
```
Required Quantity = 10
Transfer 1 = 4
Transfer 2 = 3
Transfer 3 = 3
```

**Current validation should evaluate:** Total Available = 10

**Instead of:** Checking a single Stock Entry

---

## 8. Major Architectural Change

### Old Philosophy: Work Order Dependency Engine
```
Parent WO waits for → Child WO completion
                     ↓
            Specific source tracking
                     ↓
            Document-driven execution
```

### New Philosophy: Material Readiness Engine
```
Job Card asks → "Is required quantity available?"
                     ↓
            Source-agnostic validation
                     ↓
            Inventory-driven execution
```

**Key Question:** The Job Card should answer one question:

> "Is the required quantity available for production?"

**It should NOT determine:**
- Which Work Order produced it
- Whether it was manufactured yesterday
- Whether it came from inventory
- Whether it was produced in another batch

Those become **traceability questions**, not **execution questions**.

---

## 9. Material Classification Matrix

| Material Type | Validation Approach |
|---------------|---------------------|
| Purchased Raw Material | Check transferred quantity in WIP |
| Purchased Component | Check transferred quantity in WIP |
| Internal Manufactured Component | Check available quantity in WIP/Stores |
| Common Manufactured Component | Check available stock regardless of originating WO |
| Sub Assembly | Check available quantity |
| Customer Supplied Material | Check allocated quantity |
| Phantom Items | Previous Operation only |

---

## 10. Subcontract Manufacturing

**Approach:** Handle at Planning Layer, not Execution Layer.

ERPNext already provides Production Plan and subcontracting capabilities.

**Planning should determine:**
- Manufactured internally
- Purchased
- Subcontracted
- Consumed from existing inventory

**Execution remains unchanged:** Simply verify material readiness.

---

## 11. Separation of Responsibilities

### Layer 1: Planning Layer

**Responsibilities:**
- Production Planning
- Internal vs Purchase vs Subcontract decisions
- Priority planning
- Capacity planning
- Material reservations

**Master Document:** Production Plan

**For every BOM item, decides:**

| Item | Source |
|------|--------|
| Tank | Internal |
| Core | Internal |
| Fan | Purchase |
| Powder Coating | Subcontract |
| Fins | Existing Inventory |

**No Job Cards exist yet.**

---

### Layer 2: Manufacturing Execution Layer

**Responsibilities:**
- Previous Operation validation
- Material readiness
- Job Card execution
- Manufacturing transactions

**Principle:** Execution remains independent of material source.

---

### Layer 3: Monitoring & Traceability Layer

**Responsibilities:**
Identify why production cannot proceed.

**Diagnostic Examples:**
- Purchase pending
- Internal production pending
- Subcontract receipt pending
- Material transfer pending
- Insufficient stock
- Material reserved by another Work Order
- Child production still running

---

## 12. Proposed Architecture

### 12.1 High-Level Flow

```
Production Planning Layer
         │
         │ Decide HOW to fulfill demand
         │
    ┌────┴────┬────────────┬────────────┐
    │         │            │            │
Internal    Purchase   Subcontract   Existing Stock
    │         │            │            │
    └────┬────┴────────────┴────────────┘
         │
         ▼
  Production Plan Release
         │
         ▼
   Work Order Generation
         │
         ▼
  Material Readiness Evaluation
         │
         ▼
    Job Card Execution Layer
         │
         ▼
  Manufacturing / Transfers / QC
         │
         ▼
  Work Order Completion Engine
         │
         ▼
   Finished Goods Receipt
```

---

### 12.2 Detailed Phase Breakdown

#### Phase 1 – Planning Layer
**Where most business decisions happen**

**Responsibilities:**
- Demand planning
- Production priority
- Internal vs Purchase vs Subcontract
- Material reservation
- Capacity planning

**The planner answers:** "How are we going to fulfill this demand?" (not "Can production start?")

**Production Plan becomes the master planning document.**

---

#### Phase 2 – Material Planning
**After Production Plan approval**

**System performs:**
- Material Requirement Planning
- Calculate: Raw Material, Purchased Components, Manufactured Components, Common Components, Subcontract Components

**Then generate:**
- Purchase Requests
- Purchase Orders
- Subcontract Orders
- Internal Work Orders

---

#### Phase 3 – Warehouse Architecture
**Improved design from current**

**Instead of treating all warehouses equally:**

| Warehouse Type | Purpose |
|----------------|---------|
| Central Stores | Purchased materials (Steel, Copper, Fasteners, Paint) |
| Common Component Stores | Shared inventory (Fins, Turbulators, Standard Brackets) |
| Process WIP Warehouses | One WIP per manufacturing section (Fin Forming WIP, Core Assembly WIP, Tank Assembly WIP, Brazing WIP, PDI WIP) |
| Finished Goods Warehouse | Final receipt |

**Each workstation only checks its own WIP.**

---

#### Phase 4 – Production Plan Release
**When planner releases Production Plan**

**System generates:**
```
Parent WO
    ↓
Child WO
    ↓
Job Cards
```

**Important:** These are only **execution documents**, NOT **dependency documents**.

---

#### Phase 5 – Work Order Engine
**Work Order manages only:**
- BOM
- Routing
- Quantity
- Progress
- Cost
- Completion

**Nothing more.**

---

#### Phase 6 – Material Readiness Engine
**This becomes the heart of the project**

**Instead of many validations, everything goes through:**

```python
evaluate_material_readiness(work_order)
```

**For every BOM item, determine:**
- Material Source
- Warehouse
- Required Qty
- Available Qty
- Reserved Qty
- Ready?

**No concern about:**
- Purchase
- Manufacturing
- Subcontract
- Existing Stock

Those are **planning decisions**.

---

#### Phase 7 – Job Card Readiness Engine
**When operator clicks Start**

**System checks:**
```
Previous Operation Completed?
    ↓ YES
Material Readiness - All materials ready?
    ↓ YES
Allow Start
```

**It should NOT check:**
- Child WO Completed? (because material may already exist)

---

#### Phase 8 – Material Traceability Engine
**Only when material is NOT available**

**Investigate:**
```
Material Missing
    ↓
Why?
    ↓
Possible reasons:
- Purchase Pending
- Transfer Pending
- Manufacturing Running
- Subcontract Receipt Pending
- Reserved elsewhere
- Insufficient Stock
```

**This is diagnostic, not execution.**

---

#### Phase 9 – Work Order Completion Engine
**Every event calls `evaluate_work_order_status()`:**

**Events:**
- Job Card Complete
- Manufacture Entry
- Cancel
- Transfer

**Check:**
- Job Cards
- Production Qty
- Pending Operations
- Outstanding Manufacturing

**Then update:**
```
Not Started → In Process → Completed
```

---

## 13. Warehouse Configuration

### 13.1 Formal Warehouse Classification

| Warehouse Type | Purpose |
|----------------|---------|
| Raw Material Store | Purchased materials |
| Common Component Store | Shared manufactured components |
| Process WIP | Operation-wise production |
| FG Store | Finished Goods |
| Rework | Rework |
| Rejection | Scrap |
| Vendor | Subcontract |

---

### 13.2 Configuration Required

**Instead of hard-coding warehouse names, create configuration:**

**Manufacturing Settings:**
- Raw Material Warehouse
- Common Component Warehouse
- Default WIP
- FG Warehouse
- Reject Warehouse
- Rework Warehouse

**Operation can override Company default WIP.**

---

### 13.3 Planning Configuration

**Production Plan should additionally decide:**

| Item | Source |
|------|--------|
| Purchase | ✓ |
| Internal | ✓ |
| Subcontract | ✓ |
| Existing Inventory | ✓ |

**Future:** Support hybrid scenarios where part of quantity is manufactured internally and balance is subcontracted.

---

## 14. Proposed Custom App Structure

```
tekson_manufacturing/
│
├── planning/
│   ├── production_plan.py
│   ├── source_assignment.py
│   └── reservation_engine.py
│
├── readiness/
│   ├── material_engine.py
│   ├── jobcard_engine.py
│   └── workorder_engine.py
│
├── execution/
│   ├── stock_transfer.py
│   └── manufacturing.py
│
├── monitoring/
│   ├── traceability.py
│   └── dashboards.py
│
├── reports/
│
├── settings/
│
└── api/
```

---

## 15. Development Roadmap

### Phase 1 (Current Priority)
- [ ] Material Readiness Engine
- [ ] Work Order Completion Engine
- [ ] Material Traceability
- [ ] Fix: WO status not updating to "Completed"
- [ ] Fix: Cumulative material transfer checking

### Phase 2
- [ ] Material Reservations
- [ ] Planning Rules
- [ ] Warehouse Configuration
- [ ] Common Component Handling

### Phase 3
- [ ] Subcontract Planning Integration
- [ ] Alternate Supply Sources
- [ ] Inventory Allocation
- [ ] Batch Planning

### Phase 4
- [ ] Operator Work Queue
- [ ] Supervisor Dashboard
- [ ] Planning Dashboard
- [ ] Exception Dashboard

---

## 16. Long-Term Vision

The architecture should deliberately separate responsibilities:

1. **Production Planning** decides:
   - Where materials will come from (internal manufacturing, purchase, subcontracting, or existing inventory)
   - What should be produced

2. **Material Readiness** determines:
   - Whether the required quantities are physically available
   - Whether quantities are allocated to start an operation

3. **Manufacturing Execution** manages:
   - Job Cards
   - Operation sequencing
   - Production activities
   - Without concerning itself with sourcing decisions

4. **Monitoring and Traceability** explain:
   - Why production cannot proceed
   - Provide visibility into shortages
   - Pending transfers
   - Subcontract status
   - Production progress

**Benefits:**
- Aligns with Teksons' operating model
- Scalable foundation for future enhancements:
  - Subcontracting
  - Common component production
  - Multi-plant manufacturing
  - Inventory buffering
  - Dynamic production priorities
  - Advanced planning
- No changes required to shop-floor execution logic
- Establishes `tekson_manufacturing` as a manufacturing execution layer that complements ERPNext's standard planning and inventory capabilities rather than replacing them

---

## 17. Immediate Action Items

### Critical Fixes (Phase 1)

1. **Work Order Completion Engine**
   - Fix auto-status update when all Job Cards complete
   - Ensure `evaluate_work_order_status()` triggers on all relevant events

2. **Material Readiness Engine**
   - Implement cumulative transfer checking (not individual Stock Entry)
   - Distinguish between material types (Raw, Component, Sub-Assembly, Common)
   - Source-agnostic availability checking

3. **Material Traceability**
   - Diagnostic messages for operators
   - Clear indication of WHY production is blocked

### Documentation

4. **Warehouse Configuration**
   - Define warehouse types
   - Create Manufacturing Settings doctype
   - Configure per-operation WIP overrides

5. **Testing**
   - Test with UAT data
   - Verify all affected Work Orders resolve correctly

---

## 18. Technical Notes for Development Team

The observations made during this UAT indicate that the current implementation has successfully validated the fundamental concepts of:
- Multi-level BOM execution
- Routing
- Operation sequencing
- Material movement

**The remaining work is no longer focused on fixing isolated defects**, but on **evolving the manufacturing validation framework** into a more flexible architecture that reflects real production practices.

**The development team should therefore:**

❌ **AVOID:** Introducing additional point-to-point validations between Parent and Child Work Orders

✅ **ADOPT:** Centre all future enhancements around a **reusable Material Readiness Engine** that is:
- Inventory-driven
- Planning-aware
- Independent of material source

**This architecture will support:**
- Internal manufacturing
- Common components
- Existing inventory
- Multiple material transfers
- Dynamic production priorities
- Future subcontracting

With **minimal changes to the execution layer**.

---

## 19. Customer Communication

**Next Steps to Communicate:**

1. Acknowledge all UAT issues documented
2. Explain architectural change (WO Dependency → Material Readiness)
3. Provide timeline for Phase 1 fixes
4. Schedule next UAT after Phase 1 completion
5. Request feedback on proposed warehouse configuration

---

## 20. Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-31 | OSDuo Tech LLP | Initial UAT Review & Architecture |

**Approved By:** ___________________  
**Date:** ___________________

**Next Review Date:** After Phase 1 Completion

---

*This document serves as the baseline design reference for the next development phase of the tekson_manufacturing application.*
