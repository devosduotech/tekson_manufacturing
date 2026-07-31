# MES Event Flow

**Document Type:** Technical Specification  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Frozen for Implementation  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document defines all event flows in the MES system. Each flow shows the sequence of operations, triggers, and side effects. Use this document to implement hooks, service calls, and event handlers.

---

## Event Flow 1: Work Order Creation to Material Readiness

```
┌─────────────────┐
│   Planner       │
│   Creates WO    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Work Order     │
│  Submitted      │
└────────┬────────┘
         │
         │ Event: on_submit
         │ Hook: mes_work_order_submit
         ▼
┌─────────────────┐
│  Material       │
│  Readiness      │
│  Engine         │
└────────┬────────┘
         │
         │ evaluate_material_readiness(WO)
         ▼
┌─────────────────┐
│  Get Department │
│  Warehouse      │
└────────┬────────┘
         │
         │ get_department_warehouse(WO)
         ▼
┌─────────────────┐
│  Check BOM      │
│  Requirements   │
└────────┬────────┘
         │
         │ get_required_materials(WO)
         ▼
┌─────────────────┐
│  Check          │
│  Transfers      │
│  (MR-011)       │
└────────┬────────┘
         │
         │ get_cumulative_transferred_qty()
         ▼
┌─────────────────┐
│  Update WO      │
│  custom_material_readiness
└────────┬────────┘
         │
         │ Event: wo_material_status_changed
         ▼
┌─────────────────┐
│  Refresh JC     │
│  Status         │
└────────┬────────┘
         │
         │ For each JC in WO:
         │ update_material_status()
         ▼
┌─────────────────┐
│  Notify Stores  │
│  (if not ready) │
└─────────────────┘
```

**Implementation:**

```python
# hooks.py
"Work Order": {
    "on_submit": "tekson_manufacturing.services.work_order_service.on_work_order_submit"
}

# work_order_service.py
def on_work_order_submit(doc, method):
    from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
    
    engine = MaterialReadinessEngine(work_order=doc.name)
    result = engine.evaluate_material_readiness()
    
    # Update WO custom fields
    doc.custom_material_readiness = "Ready" if result['is_ready'] else "Not Ready"
    doc.custom_transfer_completeness = result['transfer_summary']['overall_transfer_percent']
    doc.save(ignore_permissions=True)
    
    # Refresh all Job Cards
    refresh_job_card_status(doc.name)
    
    # Log
    frappe.log_error(
        message=f"Material readiness evaluated: {result['is_ready']}",
        title=f"MES Material Readiness - {doc.name}"
    )
```

---

## Event Flow 2: Stock Entry Submit to Material Refresh

```
┌─────────────────┐
│   Stores        │
│   Creates SE    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stock Entry    │
│  Submitted      │
│  (MTF Purpose)  │
└────────┬────────┘
         │
         │ Event: on_submit
         │ Hook: mes_stock_entry_submit
         ▼
┌─────────────────┐
│  Validate       │
│  Work Order     │
└────────┬────────┘
         │
         │ Check se.work_order exists
         ▼
┌─────────────────┐
│  Refresh        │
│  Material       │
│  Readiness      │
└────────┬────────┘
         │
         │ MaterialReadinessEngine.evaluate_material_readiness()
         ▼
┌─────────────────┐
│  Update WO      │
│  Status         │
└────────┬────────┘
         │
         │ Update custom_material_readiness
         │ Update custom_transfer_completeness
         ▼
┌─────────────────┐
│  Refresh JC     │
│  Dependencies   │
└────────┬────────┘
         │
         │ For each JC:
         │ update_material_status()
         │ update_start_status()
         ▼
┌─────────────────┐
│  Notify         │
│  Production     │
│  (if ready now) │
└─────────────────┘
```

**Implementation:**

```python
# hooks.py
"Stock Entry": {
    "on_submit": "tekson_manufacturing.services.stock_service.on_stock_entry_submit",
    "on_cancel": "tekson_manufacturing.services.stock_service.on_stock_entry_cancel"
}

# stock_service.py
def on_stock_entry_submit(doc, method):
    if doc.purpose != "Material Transfer for Manufacture":
        return
    
    if not doc.work_order:
        return
    
    # Refresh material readiness
    from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
    
    engine = MaterialReadinessEngine(work_order=doc.work_order)
    result = engine.evaluate_material_readiness()
    
    # Update WO
    wo = frappe.get_doc("Work Order", doc.work_order)
    wo.custom_material_readiness = "Ready" if result['is_ready'] else "Not Ready"
    wo.custom_transfer_completeness = result['transfer_summary']['overall_transfer_percent']
    wo.save(ignore_permissions=True)
    
    # Refresh Job Cards
    refresh_job_cards_for_work_order(doc.work_order)
    
    # Notify if now ready
    if result['is_ready']:
        notify_production_material_ready(doc.work_order)
```

---

## Event Flow 3: Job Card Start Validation

```
┌─────────────────┐
│   Operator      │
│   Clicks Start  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Job Card       │
│  validate_start │
└────────┬────────┘
         │
         │ Event: before_save (status = Work In Progress)
         ▼
┌─────────────────┐
│  Check          │
│  Dependencies   │
│  (DV-001)       │
└────────┬────────┘
         │
         │ DependencyEngine.validate_previous_operation()
         ▼
┌─────────────────┐
│  Check          │
│  Materials      │
│  (MR-010)       │
└────────┬────────┘
         │
         │ MaterialReadinessEngine.can_job_card_start()
         ▼
┌─────────────────┐
│  Validate       │
│  Permissions    │
│  (SEC-001)      │
└────────┬────────┘
         │
         │ Permissions.check_start_permission()
         ▼
┌─────────────────┐
│  All Valid?     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
   Yes       No
    │         │
    │         ▼
    │  ┌──────────────┐
    │  │ Throw Error  │
    │  │ with Message │
    │  └──────────────┘
    │
    ▼
┌─────────────────┐
│  Allow Start    │
│  Update Status  │
└────────┬────────┘
         │
         │ custom_start_status = "In Progress"
         │ custom_can_start = 1
         ▼
┌─────────────────┐
│  Log Event      │
└─────────────────┘
```

**Implementation:**

```python
# hooks.py
"Job Card": {
    "validate": "tekson_manufacturing.services.job_card_service.validate_job_card",
    "before_save": "tekson_manufacturing.services.job_card_service.before_job_card_save"
}

# job_card_service.py
def before_job_card_save(doc, method):
    if doc.status == "Work In Progress" and doc.custom_start_status != "In Progress":
        # Validate dependencies
        from tekson_manufacturing.validation.dependency_engine import DependencyEngine
        
        dep_engine = DependencyEngine(job_card=doc.name)
        dep_result = dep_engine.validate_previous_operation()
        
        if not dep_result['is_valid']:
            frappe.throw(dep_result['message'])
        
        # Validate materials
        from tekson_manufacturing.readiness.material_readiness import can_job_card_start
        
        material_result = can_job_card_start(doc.name)
        
        if not material_result['can_start']:
            frappe.throw(material_result['reason'])
        
        # Update status
        doc.custom_start_status = "In Progress"
        doc.custom_can_start = 1
```

---

## Event Flow 4: Job Card Completion to Next Operation

```
┌─────────────────┐
│   Operator      │
│   Completes JC  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Job Card       │
│  Submitted      │
└────────┬────────┘
         │
         │ Event: on_submit
         │ Hook: mes_job_card_complete
         ▼
┌─────────────────┐
│  Validate       │
│  Completion     │
│  (JC-002)       │
└────────┬────────┘
         │
         │ Check total_completed_qty >= for_quantity
         ▼
┌─────────────────┐
│  Find Next JC   │
└────────┬────────┘
         │
         │ Get JC with sequence_id + 1
         ▼
┌─────────────────┐
│  Refresh Next   │
│  JC Status      │
│  (JC-004)       │
└────────┬────────┘
         │
         │ update_start_status()
         │ update_dependency_status()
         ▼
┌─────────────────┐
│  Refresh WO     │
│  Progress       │
└────────┬────────┘
         │
         │ Update produced_qty
         │ Check if all JC complete
         ▼
┌─────────────────┐
│  Auto-Complete  │
│  WO? (WO-001)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
   Yes       No
    │         │
    │         ▼
    │  ┌──────────────┐
    │  │ Complete WO  │
    │  │ (WO-001)     │
    │  └──────────────┘
    │
    ▼
┌─────────────────┐
│  Log Event      │
└─────────────────┘
```

**Implementation:**

```python
# hooks.py
"Job Card": {
    "on_submit": "tekson_manufacturing.services.job_card_service.on_job_card_submit"
}

# job_card_service.py
def on_job_card_submit(doc, method):
    # Validate completion
    if doc.total_completed_qty < doc.for_quantity:
        frappe.throw(_("Cannot complete Job Card. Produced quantity {0} < Required quantity {1}").format(
            doc.total_completed_qty, doc.for_quantity
        ))
    
    # Find and refresh next Job Card
    next_jc = get_next_job_card(doc.work_order, doc.sequence_id)
    
    if next_jc:
        refresh_job_card(next_jc.name)
        notify_operator(next_jc)
    
    # Refresh Work Order progress
    refresh_work_order_progress(doc.work_order)
    
    # Check auto-completion
    check_work_order_auto_completion(doc.work_order)
```

---

## Event Flow 5: Work Order Auto-Completion

```
┌─────────────────┐
│  All JC         │
│  Completed      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Check WO-001   │
│  Conditions     │
└────────┬────────┘
         │
         │ All JC status = Completed
         │ produced_qty >= planned_qty
         │ custom_auto_complete = 1
         ▼
┌─────────────────┐
│  Create         │
│  Manufacture SE │
└────────┬────────┘
         │
         │ Stock Entry purpose = Manufacture
         │ Add FG item
         │ Add scrap items (if any)
         ▼
┌─────────────────┐
│  Submit SE      │
└────────┬────────┘
         │
         │ se.submit()
         ▼
┌─────────────────┐
│  Update WO      │
│  Status         │
└────────┬────────┘
         │
         │ wo.status = "Completed"
         │ wo.produced_qty = completed_qty
         ▼
┌─────────────────┐
│  Log Completion │
└─────────────────┘
```

**Implementation:**

```python
# execution_engine.py
def complete_work_order(self, work_order):
    wo = frappe.get_doc("Work Order", work_order)
    
    # Check conditions
    job_cards = frappe.get_all(
        "Job Card",
        filters={"work_order": wo.name},
        fields=["name", "status", "for_quantity"]
    )
    
    all_completed = all(jc.status == "Completed" for jc in job_cards)
    total_produced = sum(jc.for_quantity for jc in job_cards if jc.status == "Completed")
    
    if not all_completed or total_produced < wo.qty:
        return False
    
    # Create Manufacture Stock Entry
    se = frappe.new_doc("Stock Entry")
    se.purpose = "Manufacture"
    se.work_order = wo.name
    se.from_warehouse = self.get_department_warehouse(wo)
    se.to_warehouse = self.get_finished_goods_warehouse(wo)
    
    se.append("items", {
        "item_code": wo.production_item,
        "qty": total_produced,
        "s_warehouse": se.from_warehouse,
        "t_warehouse": se.to_warehouse,
        "uom": frappe.db.get_value("Item", wo.production_item, "stock_uom")
    })
    
    se.insert(ignore_permissions=True)
    se.submit()
    
    # Update WO
    wo.status = "Completed"
    wo.produced_qty = total_produced
    wo.save(ignore_permissions=True)
    
    return True
```

---

## Event Flow 6: Exception Handling

```
┌─────────────────┐
│  Exception      │
│  Occurs         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Catch          │
│  Exception      │
└────────┬────────┘
         │
         │ Determine exception category
         │ Map to EX-XXX code
         ▼
┌─────────────────┐
│  Create         │
│  MES Exception  │
│  Log            │
└────────┬────────┘
         │
         │ MES Exception Log.insert()
         │ severity, category, message
         ▼
┌─────────────────┐
│  Determine      │
│  Notification   │
│  Recipients     │
└────────┬────────┘
         │
         │ Based on severity:
         │ Critical → Manager + Supervisor
         │ High → Supervisor
         │ Medium → Operator
         │ Low → Log only
         ▼
┌─────────────────┐
│  Send           │
│  Notification   │
└────────┬────────┘
         │
         │ Email / System Notification
         ▼
┌─────────────────┐
│  Update JC/WO   │
│  Status         │
└────────┬────────┘
         │
         │ custom_exception_code = EX-XXX
         │ custom_exception_message = ...
         ▼
┌─────────────────┐
│  Block          │
│  Operations     │
└─────────────────┘
```

**Implementation:**

```python
# diagnostics/messages.py
def handle_exception(exception, context):
    from tekson_manufacturing.diagnostics.exception_handler import create_exception_log
    
    # Map to exception code
    exception_code = map_exception_to_code(exception, context)
    
    # Create log
    create_exception_log(
        exception_code=exception_code,
        category=get_exception_category(exception_code),
        severity=get_severity(exception_code),
        reference_doctype=context.get('doctype'),
        reference_docname=context.get('docname'),
        message=str(exception)
    )
    
    # Notify
    notify_stakeholders(exception_code, context)
    
    # Update document status
    if context.get('docname'):
        doc = frappe.get_doc(context['doctype'], context['docname'])
        doc.custom_exception_code = exception_code
        doc.custom_exception_message = get_user_message(exception_code)
        doc.save(ignore_permissions=True)
```

---

## Event Hooks Summary

| DocType     | Event         | Handler                                           |
|-------------|---------------|---------------------------------------------------|
| Work Order  | on_submit     | `services.work_order_service.on_work_order_submit` |
| Work Order  | on_cancel     | `services.work_order_service.on_work_order_cancel` |
| Stock Entry | on_submit     | `services.stock_service.on_stock_entry_submit`     |
| Stock Entry | on_cancel     | `services.stock_service.on_stock_entry_cancel`     |
| Job Card    | validate      | `services.job_card_service.validate_job_card`      |
| Job Card    | before_save   | `services.job_card_service.before_job_card_save`   |
| Job Card    | on_submit     | `services.job_card_service.on_job_card_submit`     |
| Job Card    | on_cancel     | `services.job_card_service.on_job_card_cancel`     |

---

## Scheduled Events

| Frequency | Handler                                          | Purpose                          |
|-----------|--------------------------------------------------|----------------------------------|
| Daily     | `services.scheduler.daily_material_refresh`      | Refresh all WO material status   |
| Hourly    | `services.scheduler.hourly_dependency_check`     | Check pending dependencies       |
| Hourly    | `services.scheduler.exception_cleanup`           | Archive resolved exceptions      |

---

## Notification Events

| Trigger                          | Recipients              | Template                        |
|----------------------------------|-------------------------|---------------------------------|
| Material Ready                   | Production Supervisor   | `material_ready_notification`   |
| Dependency Resolved              | Next Operator           | `dependency_resolved`           |
| Exception Raised (High/Critical) | Supervisor + Manager    | `exception_alert`               |
| Work Order Completed             | Planner + Supervisor    | `work_order_completed`          |

---

## Revision History

| Version | Date       | Author      | Changes                          |
|---------|------------|-------------|----------------------------------|
| 1.0     | 2026-07-31 | Development | Initial creation                 |

---

## Related Documents

- MES_SERVICE_INTERFACES.md - Service method signatures
- MES_LOGGING_STANDARD.md - Logging format and categories
- MES_BUSINESS_RULES.md - Business rules triggering events
