# Pre-UAT Critical Fixes

**Document ID:** MES-PUF-001  
**Version:** 1.0  
**Date:** August 2, 2026  
**Status:** 🔴 **ACTION REQUIRED**  
**Priority:** CRITICAL - Must fix before Customer UAT  

---

## PUF-001: Work Order Daily Planning Requirement

### Issue Description

**Current Behavior:**
- Production Plan with "Consolidate Sub-assemblies" checked creates WOs across all days as single batch
- Example: 12 units on Aug 2 + 12 units on Aug 3 = 70 WOs (all together, no daily separation)
- Planner loses daily production visibility

**Expected Behavior:**
- WOs should ALWAYS be created per planned start date
- Example: 
  - Aug 2: 12 units → 87 WOs (1 FG + 13 sub-assemblies × 12 units, some consolidated)
  - Aug 3: 12 units → 87 WOs (separate batch)
  - Total: 174 WOs (clearly separated by day)

### Business Impact

| Aspect | Current (Consolidated) | Required (Daily) |
|--------|----------------------|------------------|
| **Daily Planning** | ❌ Not visible | ✅ Clear daily batches |
| **Material Readiness** | ❌ Mixed dates | ✅ Date-specific |
| **Production Scheduling** | ❌ Hard to prioritize | ✅ Easy daily prioritization |
| **WIP Tracking** | ❌ Mixed inventory | ✅ Date-wise tracking |
| **Planner Workflow** | ❌ Manual separation needed | ✅ Automatic separation |

### Root Cause

ERPNext Production Plan's "Consolidate Sub-assemblies" feature:
- Groups WOs by item across all dates
- Ignores planned start date when consolidating
- Designed for batch production, not daily scheduling

### Solution Options

#### Option A: Disable Consolidation (Recommended - Quick Fix)
**Implementation:**
- Always keep "Consolidate Sub-assemblies" UNCHECKED
- Planner creates separate Production Plans per day if needed
- Or accept 174 WOs as current behavior (87/day)

**Pros:**
- ✅ No code changes required
- ✅ Immediate solution
- ✅ Maintains daily visibility

**Cons:**
- ❌ More WOs to manage (but correctly organized)
- ❌ Planner needs to understand the behavior

**Effort:** 0 days (documentation/training only)

---

#### Option B: Custom Production Plan Logic (Long-term)
**Implementation:**
- Override Production Plan's WO creation logic
- Force daily separation even with consolidation checked
- Create WOs grouped by planned_start_date

**Pros:**
- ✅ Best user experience
- ✅ Flexible planning
- ✅ Maintains consolidation benefits

**Cons:**
- ❌ Requires custom development
- ❌ 3-5 days effort
- ❌ Testing required

**Effort:** 3-5 days

---

#### Option C: Production Plan Per Day (Operational Workaround)
**Implementation:**
- Planner creates one Production Plan per day
- Aug 2: PP with 12 units, date=Aug 2
- Aug 3: PP with 12 units, date=Aug 3
- Each PP creates 87 WOs

**Pros:**
- ✅ No code changes
- ✅ Clear separation
- ✅ Easy to track

**Cons:**
- ❌ More Production Plans to manage
- ❌ Manual process

**Effort:** 0 days (process change only)

---

### Recommended Approach

**Immediate (Before UAT):**
1. ✅ **Option A** - Document that "Consolidate Sub-assemblies" should remain UNCHECKED
2. ✅ Train planners to create separate Production Plans per day if needed
3. ✅ Accept 174 WOs as correct behavior (87 WOs/day × 2 days)

**Post-UAT (Phase 1.1 or Phase 2):**
- Evaluate if Option B (custom logic) is needed based on user feedback
- May not be needed if planners adapt to Option A or C

---

### Implementation Checklist

#### Before UAT (Immediate)
- [ ] Document this behavior in user training materials
- [ ] Add to "Known Limitations" or "Best Practices" guide
- [ ] Train planners on correct usage:
  - Keep "Consolidate Sub-assemblies" UNCHECKED
  - Or create separate PP per day
- [ ] Update UAT test scenarios to reflect correct behavior
- [ ] Verify 87 WOs/day is acceptable to planners

#### During UAT
- [ ] Get planner feedback on daily WO visibility
- [ ] Assess if current behavior meets operational needs
- [ ] Document any pain points

#### Post-UAT Decision
- [ ] If planners are satisfied → No action needed
- [ ] If daily separation is critical → Implement Option B in Phase 2

---

### Impact on Other Features

| Feature | Impact | Mitigation |
|---------|--------|------------|
| **Material Readiness** | None - evaluates per WO | ✅ No impact |
| **Job Card Execution** | None - WOs are separate | ✅ No impact |
| **WIP Tracking** | Minimal - WIP is per department | ✅ No impact |
| **Reporting** | Can filter by planned_start_date | ✅ Use date filters |
| **Stores Picking** | May need daily view | ✅ Phase 1.1 enhancement |

---

### Test Scenarios

#### Test 1: Verify Daily WO Creation
```
Given: Production Plan with 2 dates (Aug 2: 12 units, Aug 3: 12 units)
When: "Consolidate Sub-assemblies" is UNCHECKED
Then: 
  - 87 WOs created for Aug 2
  - 87 WOs created for Aug 3
  - Total: 174 WOs
  - Each WO has correct planned_start_date
```

#### Test 2: Verify Planner Workflow
```
Given: Planner needs to schedule production for Aug 2
When: Planner filters WOs by planned_start_date = Aug 2
Then:
  - Shows only 87 WOs for Aug 2
  - Can prioritize these 87 WOs
  - Material readiness evaluated for Aug 2 WOs
```

#### Test 3: Verify Material Transfer
```
Given: 87 WOs for Aug 2
When: Stores creates Material Transfer
Then:
  - Transfer is for Aug 2 WOs only
  - WIP warehouse receives materials for Aug 2 production
  - Aug 3 WOs not included
```

---

### Documentation Updates Required

1. **User Training Guide:**
   - Add section: "Production Plan Best Practices"
   - Explain: "Keep 'Consolidate Sub-assemblies' UNCHECKED for daily planning"
   - Show: Example of daily WO separation

2. **Known Limitations:**
   - Document: "Consolidate Sub-assemblies feature not recommended for daily production planning"
   - Workaround: "Create separate Production Plans per day or keep consolidation unchecked"

3. **UAT Test Plan:**
   - Update scenarios to reflect 87 WOs/day expectation
   - Add test: "Verify daily WO separation"

---

### Acceptance Criteria

**Pre-UAT:**
- [ ] Planners understand the behavior
- [ ] Documentation updated
- [ ] UAT test scenarios updated
- [ ] 87 WOs/day accepted as correct behavior

**Post-UAT (if needed):**
- [ ] Option B implemented (if planners request)
- [ ] Tested with multi-day Production Plans
- [ ] User acceptance confirmed

---

### Owner & Timeline

| Role | Name | Responsibility | Due Date |
|------|------|----------------|----------|
| **Business Owner** | Planning Manager | Accept/reject behavior | Aug 4 |
| **Functional** | Functional Consultant | Document & train | Aug 4 |
| **Technical** | Tech Lead | Implement Option B if needed | Sep 1 (if approved) |
| **Project Manager** | PM | Track decision | Aug 4 |

---

### Decision Log

| Date | Decision | Rationale | Approved By |
|------|----------|-----------|-------------|
| Aug 2, 2026 | Issue identified | Planner needs daily visibility | - |
| [Pending] | Decision pending | Awaiting planner feedback | Planning Manager |

---

### Related Documents

- [Enhancement Backlog](ENHANCEMENT_BACKLOG_v1.0.md) - Deferred Topics Register
- [Operational Decisions](OPERATIONAL_DECISIONS.md) - OD-007 (Planner Controls)
- [UAT Test Plan](../UAT/UAT_TEST_PLAN_FULL_CYCLE.md) - Scenario 10
- [Business Process Freeze](BUSINESS_PROCESS_FREEZE_v1.0.md) - WO-007

---

**Status:** 🔴 **PENDING DECISION**  
**Next Review:** Aug 4, 2026 (Planner feedback)  
**Distribution:** Planning Manager, Functional Consultant, Project Manager

---

**END OF DOCUMENT**
