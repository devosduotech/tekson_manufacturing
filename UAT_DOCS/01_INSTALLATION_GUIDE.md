# Tekson MES — Installation Guide

**Version:** v15.0.1
**For:** ERPNext V15
**Date:** August 2026

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| ERPNext | V15 (15.x.x) |
| Frappe | V15 |
| Python | 3.11+ |
| MariaDB | 10.6+ |
| Redis | 6+ |
| Node.js | 16+ |

---

## Step 1: Get the App

```bash
cd ~/frappe-bench
bench get-app https://github.com/devosduotech/tekson_manufacturing --branch main
```

---

## Step 2: Install on Site

```bash
bench --site [your-site-name] install-app tekson_manufacturing
```

---

## Step 3: Run Migrations

```bash
bench --site [your-site-name] migrate
bench --site [your-site-name] clear-cache
```

---

## Step 4: Restart Services

```bash
sudo systemctl restart frappe-bench.target
```

---

## Step 5: Verify Installation

```bash
bench --site [your-site-name] console
```

```python
# Test engine imports
from tekson_manufacturing.mes.dataclasses import MaterialResult
from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
from tekson_manufacturing.mes.mes_coordinator import MESExecutionCoordinator
print("✅ All engines loaded")

# Check custom fields
fields = frappe.get_all('Custom Field', 
    filters={'dt': 'Job Card', 'fieldname': ['in', [
        'custom_can_start_operation',
        'custom_material_available_for_operation',
        'custom_readiness_status',
        'custom_material_status'
    ]]})
print(f"✅ {len(fields)} custom fields found")
```

---

## Step 6: Configure BOMs

For each BOM:
1. Open **Manufacturing → BOM** in ERPNext
2. In **Items** table → set `Operation` field on each row (mandatory)
3. In **Operations** table → set `Workstation Type` on each row

---

## Post-Installation Checklist

- [ ] All custom fields present on Job Card form
- [ ] BOM Items have `Operation` assigned
- [ ] BOM Operations have `Workstation Type` assigned
- [ ] Test Work Order can be created and submitted
- [ ] Job Cards show readiness status fields

---

## Updating the App

```bash
cd ~/frappe-bench/apps/tekson_manufacturing
git pull origin main
cd ~/frappe-bench
bench --site [your-site-name] migrate
bench --site [your-site-name] clear-cache
sudo systemctl restart frappe-bench.target
```

---

## Uninstalling

```bash
bench --site [your-site-name] uninstall-app tekson_manufacturing
```

---

## Support

Contact the implementation team for any installation issues.
