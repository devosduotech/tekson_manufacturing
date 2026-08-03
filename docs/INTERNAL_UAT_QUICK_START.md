# Internal UAT Deployment - Quick Start

**Status:** ✅ **READY TO DEPLOY**  
**Version:** 1.0  
**Date:** 2026-08-03  

---

## 🚀 Quick Deployment (5 Minutes)

### Option 1: Automated Script (Recommended)

```bash
# Navigate to app directory
cd /home/karthic/Desktop/new_applications/tekson_manufacturing

# Run deployment script
./deploy_to_vm.sh

# Follow prompts
# → Enter 'y' to continue
# → Script handles everything automatically
```

### Option 2: Manual Deployment

```bash
# 1. Navigate to bench
cd ~/frappe-bench  # or your bench path

# 2. Pull latest code
cd apps/tekson_manufacturing
git pull origin develop

# 3. Install app (if needed)
bench --site teksons.dev install-app tekson_manufacturing

# 4. Clear cache
bench --site teksons.dev clear-cache

# 5. Restart
bench restart
```

---

## ✅ Verification (2 Minutes)

After deployment, verify:

```bash
# Open console
bench --site teksons.dev console
```

```python
# Test 1: Check imports
from tekson_manufacturing.mes.dataclasses import MaterialResult
from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
from tekson_manufacturing.mes.mes_coordinator import MESExecutionCoordinator
print("✅ All imports successful")

# Test 2: Check custom fields
fields = frappe.get_all('Custom Field', 
    filters={'dt': 'Job Card', 'fieldname': ['in', [
        'custom_material_status',
        'custom_readiness_status',
        'custom_can_start_operation'
    ]]})
print(f"✅ Found {len(fields)} custom fields")

# Test 3: Create test result
result = MaterialResult(
    is_ready=True,
    status="Material Available",
    message="Test successful",
    available_qty=100.0,
    required_qty=50.0
)
print(f"✅ Dataclass works: {result.status}")
```

---

## 🧪 First Test (10 Minutes)

### Create Your First Work Order

1. **Open Browser:** `http://localhost:8000`
2. **Login** to ERPNext
3. **Navigate:** Manufacturing → Work Order → Add Work Order
4. **Create WO:**
   - Production Item: R215
   - Qty: 10
   - BOM: Select default
   - Submit
5. **Verify Job Cards:**
   - Check custom fields
   - Should show "Waiting for Material"

### Create Material Transfer

1. **Stock Entry:** Material Transfer for Manufacture
2. **Work Order:** Select your WO
3. **Submit**
4. **Verify:** Job Cards refresh to "Ready to Start"

### Complete Operation

1. **Open Job Card 1**
2. **Click Start**
3. **Enter time**
4. **Complete**
5. **Verify:** Job Card 2 becomes ready

---

## 📋 Test Scenarios

Execute these in order:

| # | Test Case | Time | Status |
|---|-----------|------|--------|
| 1 | WO Submit (no stock) | 5 min | ⬜ |
| 2 | Readiness evaluation | 2 min | ⬜ |
| 3 | Material Transfer | 5 min | ⬜ |
| 4 | Start Operation 1 | 2 min | ⬜ |
| 5 | Complete Operation 1 | 3 min | ⬜ |
| 6 | Operation 2 becomes ready | 1 min | ⬜ |
| 7 | Complete all operations | 10 min | ⬜ |
| 8 | FG Stock Entry | 5 min | ⬜ |
| 9 | Partial production | 10 min | ⬜ |
| 10 | Dependency blocking | 5 min | ⬜ |
| 11 | Performance test | 10 min | ⬜ |
| 12 | Cancel & Amend | 10 min | ⬜ |

**Total Time:** ~75 minutes (1.5 hours with breaks)

---

## 🐛 Issue Tracking

Found an issue? Document it:

**Template:**
```
Issue ID: UAT-001
Severity: High/Medium/Low
Test Case: TC-MFG-XXX

Steps:
1. ...
2. ...

Expected: ...
Actual: ...

Screenshot: [Attach]
```

Save in: `docs/UAT_ISSUES.md`

---

## 📊 Success Criteria

### Pass Criteria:
- ✅ All core tests pass (TC-MFG-001 to 008)
- ✅ ≥ 80% test pass rate
- ✅ Zero critical bugs
- ✅ ≤ 2 high priority bugs
- ✅ Performance targets met

### Performance Targets:
| Operation | Target | Acceptable |
|-----------|--------|------------|
| WO Submit (40 JCs) | < 2s | < 5s |
| Material Transfer | < 3s | < 10s |
| Job Card Complete | < 1s | < 2s |
| Start Button | < 100ms | < 200ms |

---

## 📞 Support

**Technical Issues:**
- Check error logs: `bench --site teksons.dev view-error-log`
- Console debugging: `bench --site teksons.dev console`
- Review docs: `INTERNAL_UAT_TESTING_GUIDE.md`

**Contact:**
- Technical Lead: [Name]
- MES Developer: [Name]
- Project Manager: [Name]

---

## 🎯 Next Steps

### After Internal UAT:

1. **Fix Issues:** Address all critical/high bugs
2. **Document Results:** Complete UAT summary
3. **Prepare for Customer UAT:**
   - Refine test scenarios
   - Prepare training materials
   - Schedule customer sessions
4. **Go/No-Go Decision:** Week 3, Day 5

---

## 📁 Documentation Reference

| Document | Purpose |
|----------|---------|
| `deploy_to_vm.sh` | Automated deployment |
| `INTERNAL_UAT_TESTING_GUIDE.md` | Detailed test instructions |
| `UAT_DEPLOYMENT_GUIDE.md` | Full UAT deployment guide |
| `MANUFACTURING_WORKFLOW_AUDIT.md` | 15 manufacturing test scenarios |
| `PRODUCTION_READINESS_AUDIT.md` | Production readiness checklist |

---

## ✅ Pre-Deployment Checklist

Before deploying:

- [ ] Backup site data
- [ ] Note current commit hash
- [ ] Have rollback plan ready
- [ ] Test data prepared (Items, BOMs)
- [ ] Browser ready (Chrome/Firefox)
- [ ] Issue tracking template ready
- [ ] Screen recording software (optional)
- [ ] Notebook for observations

---

## 🎊 Ready to Deploy!

**Everything is prepared. Time to test!**

```bash
# Execute deployment
./deploy_to_vm.sh
```

**Good luck with UAT!** 🚀

---

**Deployment Completed By:** _______________  
**Date:** _______________  
**Time Started:** _______________  
**Time Completed:** _______________  
**Issues Found:** _______________  
**Overall Status:** ⬜ Success / ⬜ Partial / ⬜ Failed
