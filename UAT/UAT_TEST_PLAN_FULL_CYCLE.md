# UAT Test Plan - Full Manufacturing Cycle Validation

**Date:** August 2, 2026  
**Version:** 1.0  
**Environment:** Clean UAT (masters only, no transactional data)  
**Production Plan:** PP/2608/31/0002 (71 Work Orders)  

---

## Objective

Validate complete MES Phase 1 implementation through end-to-end manufacturing cycle:
1. Production Plan → Work Order creation
2. Job Card auto-creation with correct warehouse assignment
3. Material transfer from Stores to WIP
4. Job Card execution (Start → Complete)
5. Inter-department transfers
6. Final Stock Entry to Finished Goods

---

## Prerequisites

### Master Data (Already Configured)
- ✅ 1660 Items with default warehouses
- ✅ 132 Workstations with plant_floor (100%)
- ✅ 21 Warehouses (clean structure)
- ✅ 81 BOMs with operations

### Scripts Installed
- ✅ `job_card_utils.allocate_workstation` (NEW)
- ✅ `job_card_utils.set_wip_warehouse`
- ✅ `work_order_service.auto_create_manufacture_entry` (NEW)
- ✅ `execution_engine` (Job Card + Stock Entry hooks)
- ✅ `material_readiness` engine
- ✅ `dependency_engine`

### Test Data
- **Production Plan:** PP/2608/31/0002
- **Work Orders:** 71 WOs (WO/260802/0002 to WO/260802/0071)
- **Job Cards:** 97 auto-created
- **Stock Entries:** 54 in Draft mode

---

## Test Scenarios

### Scenario 1: Workstation Auto-Assignment (NEW)

**Test ID:** JC-006  
**Purpose:** Verify Job Cards auto-assign workstation from BOM

**Steps:**
1. Create new Work Order for item with BOM
2. Check Job Cards created
3. Verify workstation field is populated

**Expected Result:**
- Job Card has `workstation` field set automatically
- `custom_plant_floor` matches workstation's plant floor
- `wip_warehouse` = `WIP-{plant_floor} - TPL`

**Test Work Order:** Create new WO for any finished good

**Pass Criteria:**
- [ ] Workstation assigned automatically
- [ ] Plant floor copied correctly
- [ ] WIP warehouse matches plant floor

---

### Scenario 2: Job Card WIP Warehouse Assignment

**Test ID:** WH-002  
**Purpose:** Verify Job Cards get correct WIP warehouse

**Steps:**
1. Open existing Job Card (e.g., JC-260802-0001-001)
2. Check `wip_warehouse` field
3. Verify against workstation's plant_floor

**Expected Result:**
```
Workstation: RP-26_Hydraulic Press (plant_floor: RP)
Job Card wip_warehouse: WIP-RP - TPL
```

**Test Job Cards:**
- JC-260802-0001-001 (CNC)
- JC-260802-0002-001 (RA)
- JC-260802-0003-001 (Ralu In)
- JC-260802-0004-001 (Ralu Weld)
- JC-260802-0005-001 (RP)
- JC-260802-0006-001 (W)

**Pass Criteria:**
- [ ] All 6 plant floors represented
- [ ] Warehouse naming follows `WIP-{PlantFloor} - TPL`
- [ ] No generic `WIP Warehouse - TPL`

---

### Scenario 3: Material Transfer Creation

**Test ID:** MR-010  
**Purpose:** Verify material transfers from Stores to WIP

**Steps:**
1. Open Work Order (e.g., WO/260802/0002)
2. Check BOM items
3. Create "Material Transfer for Manufacture"
4. Verify source/destination warehouses

**Expected Result:**
```
From: Raw Material Stores - TPL
To: WIP-{PlantFloor} - TPL (matching first operation)
```

**Test Work Orders:**
- WO/260802/0002 (CNC) → To: WIP-CNC - TPL
- WO/260802/0003 (RA) → To: WIP-RA - TPL
- WO/260802/0004 (Ralu In) → To: WIP-Ralu In - TPL

**Pass Criteria:**
- [ ] Stock Entry created successfully
- [ ] Source warehouse = Raw Material Stores
- [ ] Target warehouse = Correct WIP warehouse
- [ ] All BOM items included

---

### Scenario 4: Material Availability Validation

**Test ID:** MR-011  
**Purpose:** Verify system checks material availability

**Steps:**
1. Try to start Job Card WITHOUT material transfer
2. System should block (if strict validation enabled)
3. Transfer materials
4. Try to start Job Card again

**Expected Result:**
- Before transfer: Error message showing missing items
- After transfer: Job Card can start

**API Test:**
```python
from tekson_manufacturing.readiness.material_readiness import can_job_card_start

result = can_job_card_start("JC-260802-0001-001")
# Should return: {'can_start': True/False, 'reason': ...}
```

**Pass Criteria:**
- [ ] Validation triggers before Job Card start
- [ ] Clear error message with missing items
- [ ] Allows start after transfer

---

### Scenario 5: Operation Sequence Validation

**Test ID:** DV-001  
**Purpose:** Verify operations follow correct sequence

**Steps:**
1. Create Work Order with multiple operations
2. Try to start Job Card 2 (operation 2)
3. System should block (operation 1 not complete)
4. Complete Job Card 1
5. Try Job Card 2 again

**Expected Result:**
- Cannot start JC-002 until JC-001 is "Completed"
- Error: "Previous operation 'Cutting' is not completed"

**Test Work Order:** WO with 2+ operations (e.g., WO/260802/0001)

**Pass Criteria:**
- [ ] First operation can start immediately
- [ ] Second operation blocked until first complete
- [ ] Clear error message with previous JC name

---

### Scenario 6: Job Card Start/Complete Flow

**Test ID:** JC-001, JC-002  
**Purpose:** Verify complete Job Card lifecycle

**Steps:**
1. Start Job Card (Status → Work In Progress)
2. Enter completed quantity
3. Complete Job Card (Status → Completed)
4. Submit Job Card

**Expected Result:**
- Status changes: Open → Work In Progress → Completed
- `total_completed_qty` updated
- Next Job Card status refreshed (JC-004)

**Test Job Card:** Any first-operation JC

**Pass Criteria:**
- [ ] Can start when materials available
- [ ] Can complete when qty achieved
- [ ] Submits successfully
- [ ] Triggers next JC refresh

---

### Scenario 7: Auto-Manufacture on WO Complete

**Test ID:** WO-003 (NEW)  
**Purpose:** Verify auto-creation of Manufacture Stock Entry

**Steps:**
1. Complete all Job Cards for Work Order
2. Submit final Job Card
3. Check Work Order status (should auto-change to "Completed")
4. Verify Manufacture Stock Entry created

**Expected Result:**
- Stock Entry created automatically
- Purpose: "Manufacture"
- From: WIP warehouse
- To: Finished Goods warehouse

**Alternative Test:**
1. Manually set WO status to "Completed"
2. Save
3. Verify Stock Entry created (before_save hook)

**Pass Criteria:**
- [ ] Stock Entry created automatically
- [ ] No duplicate entries
- [ ] Correct warehouses (WIP → FG)
- [ ] Entry submitted successfully

---

### Scenario 8: Multi-Department Flow

**Test ID:** WH-003  
**Purpose:** Verify inter-department material flow

**Steps:**
1. Find Work Order with multiple plant floors
   - Example: W → RP → FG
2. Check Job Cards for each department
3. Verify WIP warehouses change correctly

**Expected Result:**
```
Operation 1 (W): WIP-W - TPL
Operation 2 (RP): WIP-RP - TPL
Final SE: WIP-RP - TPL → Finish Goods Stores - TPL
```

**Test Work Orders:** 11 multi-department WOs from PP/2608/31/0002

**Pass Criteria:**
- [ ] Each JC has correct WIP warehouse
- [ ] Inter-department transfer possible
- [ ] Final SE from last department to FG

---

### Scenario 9: Stock Entry Submission

**Test ID:** SE-001  
**Purpose:** Verify Stock Entry submission workflow

**Steps:**
1. Open Draft Stock Entry (e.g., SE-260802-078)
2. Verify items and warehouses
3. Check stock availability
4. Submit Stock Entry

**Expected Result:**
- If stock available: Submits successfully
- If stock insufficient: Error message

**Test Stock Entries:**
- SE-260802-078 to SE-260802-148 (54 entries in Draft)

**Pass Criteria:**
- [ ] Can submit when stock available
- [ ] Clear error if stock insufficient
- [ ] Updates bin quantities
- [ ] Triggers WO status refresh

---

### Scenario 10: Production Plan to WO Flow

**Test ID:** PP-001  
**Purpose:** Verify Production Plan creates correct WOs

**Steps:**
1. Open Production Plan PP/2608/31/0002
2. Check Work Orders list
3. Verify warehouse assignments

**Expected Result:**
- 71 Work Orders created
- Each WO has correct WIP warehouse
- Job Cards auto-created with correct warehouses

**Pass Criteria:**
- [ ] All 71 WOs created
- [ ] WIP warehouses assigned correctly
- [ ] 97 Job Cards created
- [ ] No errors in creation

---

## Test Execution Checklist

### Preparation
- [ ] Backup UAT database
- [ ] Clear all transactional data (keep masters)
- [ ] Verify master data (items, workstations, warehouses)
- [ ] Install latest code (with gap fixes)
- [ ] Restart bench (to load new hooks)

### Test Execution

| Test # | Scenario | Status | Notes | Tester | Date |
|--------|----------|--------|-------|--------|------|
| 1 | Workstation Auto-Assignment | ⬜ Not Started | | | |
| 2 | Job Card WIP Assignment | ⬜ Not Started | | | |
| 3 | Material Transfer Creation | ⬜ Not Started | | | |
| 4 | Material Availability Check | ⬜ Not Started | | | |
| 5 | Operation Sequence | ⬜ Not Started | | | |
| 6 | Job Card Start/Complete | ⬜ Not Started | | | |
| 7 | Auto-Manufacture on WO Complete | ⬜ Not Started | | | |
| 8 | Multi-Department Flow | ⬜ Not Started | | | |
| 9 | Stock Entry Submission | ⬜ Not Started | | | |
| 10 | Production Plan Flow | ⬜ Not Started | | | |

### Defect Log

| ID | Scenario | Issue | Severity | Status | Assigned To |
|----|----------|-------|----------|--------|-------------|
| | | | | | |

---

## Success Criteria

**Phase 1 MES is production-ready if:**

1. ✅ All 10 test scenarios pass
2. ✅ 100% Job Cards have correct WIP warehouse
3. ✅ Material transfers work for all 6 plant floors
4. ✅ Operation sequence validation prevents out-of-order production
5. ✅ Auto-manufacture creates Stock Entries correctly
6. ✅ Multi-department flow validated
7. ✅ No critical defects open

---

## Test Data Cleanup

### After UAT Completion

**Keep:**
- ✅ Master data (Items, Workstations, Warehouses, BOMs)
- ✅ Test results and defect logs

**Delete:**
- ❌ Test Work Orders
- ❌ Test Job Cards
- ❌ Test Stock Entries
- ❌ Test Production Plans

**Script:**
```bash
# Run cleanup script (to be created)
bench execute tekson_manufacturing.scripts.cleanup_uat_transactions
```

---

## Roles and Responsibilities

| Role | Name | Responsibilities |
|------|------|------------------|
| Test Lead | | Plan tests, track progress, report status |
| Storekeeper | | Test material transfers, verify warehouses |
| Operator | | Test Job Card start/complete |
| Supervisor | | Test multi-department flow, approvals |
| IT Admin | | Setup environment, install code, troubleshoot |

---

## Timeline

| Phase | Duration | Activities |
|-------|----------|------------|
| Preparation | 1 day | Backup, cleanup, code install |
| Test Execution | 2-3 days | Run all 10 scenarios |
| Defect Fix | 1-2 days | Fix issues, retest |
| Sign-off | 1 day | Final review, approval |

**Total:** 5-7 days

---

## Appendix A: Key APIs for Testing

### Check Material Readiness
```python
from tekson_manufacturing.readiness.material_readiness import evaluate_material_readiness

result = evaluate_material_readiness("WO/260802/0002")
print(result['is_ready'])
print(result['missing_items'])
```

### Check Dependency
```python
from tekson_manufacturing.validation.dependency_engine import can_job_card_start

result = can_job_card_start("JC-260802-0001-001")
print(result['can_start'])
print(result['reason'])
```

### Check Execution Status
```python
from tekson_manufacturing.execution.execution_engine import ExecutionEngine

engine = ExecutionEngine()
result = engine.can_job_card_start("JC-260802-0001-001")
print(result)
```

---

## Appendix B: Expected Warehouse Structure

```
All Warehouses - TPL
├── Raw Material Stores - TPL
├── BOF Stores - TPL
├── Work In Progress - TPL (Group)
│   ├── WIP-CNC - TPL
│   ├── WIP-RA - TPL
│   ├── WIP-Ralu In - TPL
│   ├── WIP-Ralu Weld - TPL
│   ├── WIP-RP - TPL
│   └── WIP-W - TPL
├── Finished Goods - TPL
│   └── Finish Goods Stores - TPL
└── Receipt and Despatch Stores - TPL
```

---

## Appendix C: Sample Test Work Orders

| WO Number | Item | Plant Floor | WIP Warehouse | Job Cards |
|-----------|------|-------------|---------------|-----------|
| WO/260802/0002 | [Item Name] | CNC | WIP-CNC - TPL | 1 |
| WO/260802/0003 | [Item Name] | RA | WIP-RA - TPL | 1 |
| WO/260802/0004 | [Item Name] | Ralu In | WIP-Ralu In - TPL | 1 |
| WO/260802/0005 | [Item Name] | Ralu Weld | WIP-Ralu Weld - TPL | 1 |
| WO/260802/0006 | [Item Name] | RP | WIP-RP - TPL | 1 |
| WO/260802/0007 | [Item Name] | W | WIP-W - TPL | 1 |

---

**Document Prepared By:** AI Assistant  
**Date:** August 2, 2026  
**Next Review:** After UAT execution  
**Approval Pending:** Test Lead, Project Manager
