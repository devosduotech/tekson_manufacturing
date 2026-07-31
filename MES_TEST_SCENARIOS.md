# MES Test Scenarios

**Document Type:** Testing Specification  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Ready for Implementation

---

## Overview

This document defines test scenarios for validating the Manufacturing Execution System (MES) implementation against business rules (MES_BUSINESS_RULES.md).

---

## Test Categories

1. **Job Card Execution Tests** (TC-JC-001 to TC-JC-010)
2. **Material Readiness Tests** (TC-MR-001 to TC-MR-010)
3. **Work Order Completion Tests** (TC-WO-001 to TC-WO-010)
4. **Dependency Validation Tests** (TC-DV-001 to TC-DV-010)
5. **Diagnostics Tests** (TC-DM-001 to TC-DM-010)
6. **Integration Tests** (TC-INT-001 to TC-INT-010)

---

## Job Card Execution Tests

### TC-JC-001: Job Card Cannot Start Without Previous Operation

**Rule:** JC-001

**Scenario:**
- Create Work Order with 3 operations
- Submit Job Card for Operation 2 (skip Operation 1)

**Expected Result:**
- ❌ Job Card start blocked
- ✅ Error: "Previous operation 'Operation 1' is not completed"
- ✅ Diagnostic shows previous Job Card details

**Test Data:**
- Work Order: WO-TEST-001
- Operations: Cutting → Welding → Painting
- Job Cards: JC-001 (Cutting), JC-002 (Welding), JC-003 (Painting)

---

### TC-JC-002: First Operation Can Start Without Dependency

**Rule:** JC-001 (Exception)

**Scenario:**
- Create Work Order with 3 operations
- Submit Job Card for Operation 1

**Expected Result:**
- ✅ Job Card start allowed
- ✅ No previous operation check

---

### TC-JC-003: Job Card Cannot Complete Without Required Quantity

**Rule:** JC-002

**Scenario:**
- Job Card for_quantity = 10
- total_completed_qty = 5
- Attempt to complete Job Card

**Expected Result:**
- ❌ Completion blocked
- ✅ Error: "Completed quantity (5) is less than required (10)"

---

### TC-JC-004: Job Card Can Complete When Quantity Achieved

**Rule:** JC-002

**Scenario:**
- Job Card for_quantity = 10
- total_completed_qty = 10
- Complete Job Card

**Expected Result:**
- ✅ Completion allowed
- ✅ Job Card status = "Completed"

---

## Material Readiness Tests

### TC-MR-001: Cumulative Transfer Validation

**Rule:** MR-001

**Scenario:**
- Work Order requires 100 kg Copper Tube
- Transfer 1: 40 kg (SE-001)
- Transfer 2: 35 kg (SE-002)
- Transfer 3: 25 kg (SE-003)
- Check material readiness

**Expected Result:**
- ✅ Total available = 100 kg
- ✅ Material readiness = Ready
- ✅ All transfers counted cumulatively

**Test Data:**
- Work Order: WO-TEST-002
- Item: Copper Tube
- Required: 100 kg

---

### TC-MR-002: Material Shortage Detected

**Rule:** MR-001, MR-007

**Scenario:**
- Work Order requires 100 kg
- Only 60 kg transferred
- Check material readiness

**Expected Result:**
- ❌ Material readiness = Not Ready
- ✅ Shortage detected: 40 kg
- ✅ Diagnostic message with details
- ✅ Action recommended

---

### TC-MR-003: Common Component Global Stock Check

**Rule:** MR-004

**Scenario:**
- FG1 requires 50 Fins
- FG2 requires 30 Fins
- Existing stock: 100 Fins (from previous production)
- Check readiness for both

**Expected Result:**
- ✅ FG1: Ready (100 available)
- ✅ FG2: Ready (50 remaining after FG1)
- ✅ No specific Work Order check

---

### TC-MR-004: Manufactured Component Availability

**Rule:** MR-002, MR-009

**Scenario:**
- Parent WO requires Core Assembly
- Child WO producing Core Assembly: 60% complete
- Check parent WO readiness

**Expected Result:**
- ❌ Not ready (insufficient stock)
- ✅ Diagnostic: "Child WO in process (60% complete)"

---

### TC-MR-005: Multiple Material Types in Single WO

**Rule:** MR-009

**Scenario:**
- Work Order requires:
  - Steel Plate (Raw Material): 200 kg
  - Copper Tube (Purchased): 100 kg
  - Core Assembly (Manufactured): 10 nos
  - Fins (Common): 200 nos
- Check readiness for each

**Expected Result:**
- ✅ Each material checked with appropriate strategy
- ✅ Raw Material: Check transfers
- ✅ Purchased: Check transfers
- ✅ Manufactured: Check stock
- ✅ Common: Check global stock

---

## Work Order Completion Tests

### TC-WO-001: Auto-Completion When All Job Cards Done

**Rule:** WO-001

**Scenario:**
- Work Order with 3 Job Cards
- Complete all 3 Job Cards
- Submit last Job Card

**Expected Result:**
- ✅ Work Order auto-completes
- ✅ Stock Entry created
- ✅ Status = "Completed"

---

### TC-WO-002: Duplicate Stock Entry Prevention

**Rule:** WO-002

**Scenario:**
- Work Order already has Manufacture Stock Entry
- Complete last Job Card again (re-submit)

**Expected Result:**
- ✅ No duplicate Stock Entry
- ✅ Status updated correctly
- ✅ Message: "Stock Entry already exists"

---

### TC-WO-003: Work Order Status Updates Correctly

**Rule:** WO-003

**Scenario:**
- Work Order with 5 Job Cards
- Complete 2 Job Cards
- Check status

**Expected Result:**
- ✅ Status = "In Process"
- ✅ Produced qty updated

---

## Dependency Validation Tests

### TC-DV-001: Previous Operation Blocking

**Rule:** DV-001

**Scenario:**
- Operation sequence: 1 → 2 → 3
- Operation 1: Not completed
- Attempt to start Operation 2

**Expected Result:**
- ❌ Start blocked
- ✅ Error: "Previous operation not completed"

---

### TC-DV-002: Sequence Integrity Check

**Rule:** DV-002

**Scenario:**
- Create Job Cards with sequence: 1, 2, 4 (skip 3)

**Expected Result:**
- ❌ Validation error
- ✅ Error: "Sequence gap detected"

---

### TC-DV-003: Dependency Refresh on Completion

**Rule:** DV-004

**Scenario:**
- Complete Job Card (sequence 1)
- Check Job Card (sequence 2) status

**Expected Result:**
- ✅ Job Card 2 custom_start_status updated
- ✅ Now shows "Ready to Start"

---

## Diagnostics Tests

### TC-DM-001: Clear Material Shortage Message

**Rule:** DM-001

**Scenario:**
- Material shortage: 40 kg Copper Tube
- Generate diagnostic

**Expected Result:**
- ✅ Title: "Material Not Available: Copper Tube"
- ✅ Details: Required, Available, Shortage
- ✅ Reason: Specific cause
- ✅ Action: Actionable step

---

### TC-DM-002: Diagnostic Categories

**Rule:** DM-002

**Scenario:**
- Test different error types

**Expected Result:**
- ✅ Material shortage: category = "material_shortage"
- ✅ Dependency blocking: category = "dependency_blocking"
- ✅ Success: category = "validation_passed"

---

### TC-DM-003: Severity Levels

**Rule:** DM-003

**Scenario:**
- Test different severities

**Expected Result:**
- ✅ Blocking error: severity = "high"
- ✅ Warning: severity = "medium"
- ✅ Info: severity = "none"

---

## Integration Tests

### TC-INT-001: End-to-End Job Card Flow

**Scenario:**
1. Create Work Order
2. Generate Job Cards
3. Submit Job Card 1
4. Complete Job Card 1
5. Submit Job Card 2
6. Complete Job Card 2
7. Submit Job Card 3
8. Complete Job Card 3

**Expected Result:**
- ✅ All validations pass
- ✅ Work Order auto-completes
- ✅ Stock Entry created
- ✅ Status = "Completed"

---

### TC-INT-002: Material Readiness Integration

**Scenario:**
1. Create Work Order with multiple materials
2. Transfer materials incrementally
3. Check readiness after each transfer
4. Start Job Card when ready

**Expected Result:**
- ✅ Readiness updates after each transfer
- ✅ Cumulative calculation works
- ✅ Job Card start allowed when ready

---

### TC-INT-003: Error Handling

**Scenario:**
- Trigger various error conditions
- Check error messages

**Expected Result:**
- ✅ Clear, actionable messages
- ✅ No generic errors
- ✅ Proper severity levels

---

## UAT Test Checklist

### Pre-UAT Preparation
- [ ] Test data created
- [ ] Test environment ready
- [ ] Users trained
- [ ] Feedback forms prepared

### UAT Execution
- [ ] TC-JC-001: Previous operation blocking
- [ ] TC-JC-002: First operation start
- [ ] TC-MR-001: Cumulative transfers
- [ ] TC-MR-002: Material shortage detection
- [ ] TC-WO-001: Auto-completion
- [ ] TC-INT-001: End-to-end flow

### UAT Sign-off
- [ ] All critical tests passed
- [ ] User feedback collected
- [ ] Issues documented
- [ ] Go/No-Go decision made

---

## Test Data Requirements

### Work Orders
- WO-TEST-001: 3 operations (simple)
- WO-TEST-002: Multiple materials
- WO-TEST-003: Parent-Child relationship
- WO-TEST-004: Common components

### Items
- RM-001: Raw Material (Steel Plate)
- RM-002: Raw Material (Copper Tube)
- PC-001: Purchased Component
- MC-001: Manufactured Component (Core Assembly)
- CC-001: Common Component (Fins)
- CC-002: Common Component (Turbulators)

### Warehouses
- RM-STORE: Raw Material Store
- CC-STORE: Common Component Store
- WIP-001: Process WIP (Operation 1)
- WIP-002: Process WIP (Operation 2)
- FG-STORE: Finished Goods Store

---

## Notes

- Tests should be executed in order (unit → integration → UAT)
- All tests must pass before customer UAT
- Document any deviations from expected results
- Update test scenarios as new requirements emerge

---

*This document is maintained alongside implementation. Update after each test cycle.*
