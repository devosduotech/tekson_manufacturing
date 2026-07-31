# Tekson Manufacturing Custom App - Development Summary

**Version:** 1.0.0  
**Document Version:** 0.1  
**Last Updated:** 2026-07-31  
**Purpose:** Internal Development Documentation

---

## 1. Objective

The primary objective of creating the **tekson_manufacturing** custom application is to isolate all Teksons-specific manufacturing enhancements from the ERPNext core, ensuring:

- ERPNext upgrades remain straightforward
- Customer-specific business logic is maintained separately
- Future enhancements can be developed without modifying ERPNext source files
- Customizations are easier to maintain and version control

The long-term objective is to move all Teksons-specific functionality into this application.

---

## 2. Current Application Structure

```
tekson_manufacturing/
│
├── hooks.py
├── manufacturing/
│   ├── custom_job_card.py
│   ├── work_order.py
│   └── job_card_old.py
│
├── public/
│   └── js/
│       └── job_card_list.js
│
├── templates/
├── config/
├── patches/
└── modules.txt
```

---

## 3. ERPNext Overrides Implemented

### 3.1 Job Card Controller Override

Implemented in `hooks.py`:

```python
override_doctype_class = {
    "Job Card": "tekson_manufacturing.manufacturing.custom_job_card.TeksonJobCard"
}
```

**Purpose:**
- Extend Job Card functionality
- Keep ERPNext core untouched
- Allow future controller-level enhancements

**File:** `tekson_manufacturing/manufacturing/custom_job_card.py`

```python
class TeksonJobCard(JobCard):
    def on_submit(self):
        super().on_submit()
        if not self.work_order:
            return
        work_order = self.work_order
        frappe.db.after_commit.add(
            lambda: complete_work_order(work_order)
        )
```

---

## 4. Job Card Status Automation

The majority of manufacturing logic currently resides inside Server Scripts.

### 4.1 Dependency Status

Automatically determines:
- Awaiting
- Awaiting Previous Operation
- Ready

Based on routing sequence.

### 4.2 Material Availability

Checks:
- Required Material transferred
- Material available

And updates:
- `custom_material_available_for_operation`
- `custom_material_status_details`

### 4.3 Start Status

Automatically calculates `custom_start_status`

**Possible values:**
```
- Awaiting
- Awaiting Previous Operation
- Awaiting Material
- Material Available
- Ready to Start
- In Progress
- Completed
```

### 4.4 Can Start Operation

Automatically updates `custom_can_start_operation`

This becomes the master flag deciding whether production may start.

---

## 5. Job Card UI Enhancements

Additional custom fields introduced:
- Start Status
- Dependency Status
- Material Available
- Material Status Details
- Can Start Operation

These fields are now visible on Job Card.

---

## 6. Server Script Corrections

### 6.1 Removed Unsupported Imports

Server Scripts cannot contain `import frappe` - removed successfully.

### 6.2 Removed Unsupported Python Features

SafeExec rejects `.format()` and several advanced Python attributes. Converted all occurrences into simple string concatenation.

**Example:**

Old:
```python
"Status {}".format(status)
```

New:
```python
"Status " + status
```

### 6.3 Validation Fix

Custom field `custom_start_status` was updated with additional Select options:
```
- Awaiting Material
- Awaiting Previous Operation
- Material Available
```

Preventing:
```
ValidationError: Start Status cannot be Awaiting Material
```

---

## 7. Database Refresh

Successfully refreshed all Job Cards after corrections.

**Verified:** 203 Job Cards updated correctly

Verified through:
```python
frappe.db.count("Job Card")
```

and direct SQL queries.

---

## 8. Client Script Migration

Initially, Job Card List customization existed as a Client Script.

**Goal:** Display only:
- Operation
- Production Item
- Qty
- Sequence
- Start Status

Instead of ERPNext defaults.

**The Client Script was removed because:**
- Difficult to maintain
- Interfered with ERPNext rendering
- Not suitable for long-term support

---

## 9. Moving UI Logic to Custom App

Created `public/js/job_card_list.js`

Configured `app_include_js` inside `hooks.py`:

```python
app_include_js = [
    "/assets/tekson_manufacturing/js/job_card_list.js"
]
```

**Verified:** "Tekson JS Loaded" appeared in browser console.

Confirmed assets build and loading pipeline is working correctly.

---

## 10. Investigation of ERPNext List View

A detailed investigation was performed.

**Discovery:**

ERPNext Job Card List View is not controlled only by `frappe.listview_settings`.

Instead, it is dynamically rebuilt by:

```
ListView
    ↓
BaseList
    ↓
ReportView
```

Which recreates columns after loading.

**Therefore:** Removing columns through standard ListView APIs is unreliable.

---

## 11. Experiments Performed

### Attempt 1
Override `frappe.listview_settings` - Partially successful

### Attempt 2
Modify `cur_list.columns` - Columns returned after refresh

### Attempt 3
Rebuild headers via `setup_columns()`, `render_header()`, `refresh()` - ERPNext rebuilt original columns

### Attempt 4
DOM manipulation via `$(".list-row...")` - Worked only until refresh

### Attempt 5
Router events via `frappe.router.on("change")` - Worked only after opening a Job Card and returning (not reliable on initial page load)

---

## 12. Current Status of List View

Current customization has been **disabled**.

**Reason:** The behaviour is inconsistent because ERPNext internally rebuilds the Job Card List View after page load. This is not suitable for production UAT.

The JS file remains in the codebase with `ENABLE_TEKSON_JOB_CARD_VIEW = false` flag for future reference.

---

## 13. Decision Taken

**For UAT:** Continue using standard ERPNext Job Card List.

**Reason:** UAT should focus on:
- Manufacturing workflow
- Dependency logic
- Material availability
- Job Card execution

UI enhancements should not delay implementation.

---

## 14. Future Enhancement Plan

Instead of modifying ERPNext List View, develop a **dedicated Shop Floor interface** inside the custom application.

### Proposed Page: "Operator Work Queue"

**Features:**
- Operation-wise grouping
- Color-coded statuses
- Production Item
- Qty
- Sequence
- Start Status
- Workstation filtering
- Supervisor dashboard
- Touch-friendly interface
- Auto refresh
- Start/Complete buttons
- Purpose-built for operators

This avoids dependency on ERPNext List View internals.

---

## 15. Current Project Status

### 15.1 Completed

- [x] Custom application created
- [x] Controller override configured
- [x] Job Card controller inherited
- [x] Server Script corrections completed
- [x] Start Status automation completed
- [x] Dependency logic completed
- [x] Material availability automation completed
- [x] Job Card custom fields integrated
- [x] Job Card refresh completed
- [x] Client Script removed
- [x] Custom JS loading from application verified
- [x] ERPNext List View behaviour analysed
- [x] Version control setup (v1.0.0)
- [x] GitHub repository created and pushed

### 15.2 Deferred

- [ ] Custom Job Card List View
- [ ] Color-coded List View
- [ ] Column resizing
- [ ] Hidden standard columns
- [ ] Operation grouping
- [ ] Shop Floor dashboard

---

## 16. Next Recommended Development Phases

### Phase 2: Controller Migration
- Move Server Scripts into Python controllers wherever appropriate
- Reduce dependence on Server Scripts

### Phase 3: Shop Floor Interface
- Develop dedicated Shop Floor Work Queue
- Operator-friendly UI

### Phase 4: Resource Management
- Machine Allocation
- Workstation Assignment
- Operator Login

### Phase 5: Analytics & Monitoring
- Production Dashboard
- OEE (Overall Equipment Effectiveness)
- Supervisor Monitoring
- Production KPIs

---

## 17. Technical Architecture

### 17.1 File Structure

| File | Purpose |
|------|---------|
| `hooks.py` | App configuration, overrides, JS includes |
| `manufacturing/custom_job_card.py` | TeksonJobCard class overriding ERPNext JobCard |
| `manufacturing/work_order.py` | `complete_work_order()` function for auto stock entry |
| `manufacturing/job_card_old.py` | Legacy code (commented out, for reference) |
| `public/js/job_card_list.js` | Custom ListView script (disabled) |

### 17.2 Key Functions

#### `complete_work_order(work_order)`
**Location:** `manufacturing/work_order.py`

**Purpose:** Automatically creates and submits Manufacturing Stock Entry when all operations are completed.

**Logic Flow:**
1. Load Work Order
2. Check if already completed
3. Verify no duplicate stock entry exists
4. Confirm ALL operations are "Completed"
5. Create Stock Entry via `make_stock_entry()`
6. Submit Stock Entry
7. Update Work Order status to "Completed"

**Returns:** Stock Entry name or status message

---

## 18. Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-07-31 | Initial production release |
| | | - Job Card override implemented |
| | | - Work order auto-completion |
| | | - Server Script corrections |
| | | - Start Status automation |

---

## 19. GitHub Repository

**URL:** https://github.com/devosduotech/tekson_manufacturing

**Branches:**
- `main` - Production releases
- `develop` - Active development

**Tags:**
- `v1.0.0` - Initial release

---

## 20. Key Outcome

This session established the **foundation architecture** of the `tekson_manufacturing` custom application. Business-critical manufacturing logic (dependency checking, material validation, and start-status automation) is functioning correctly and isolated from ERPNext core behavior.

UI customization of the standard Job Card List View was investigated extensively but intentionally deferred due to limitations in ERPNext's internal ListView rendering. The agreed direction is to implement a dedicated operator-facing Shop Floor interface in the custom application after successful UAT, rather than continuing to modify the standard List View.

---

## 21. Contact Information

**Publisher:** OSDuo Tech LLP  
**Email:** developer@osduotech.com

---

*This document is maintained in the project repository for future reference and onboarding.*
