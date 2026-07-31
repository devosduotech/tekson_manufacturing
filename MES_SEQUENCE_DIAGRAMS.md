# MES Sequence Diagrams

**Document Type:** Technical Specification  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Frozen for Implementation  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document contains sequence diagrams for major MES processes. Use these diagrams for debugging, understanding flow, and onboarding new developers.

---

## Diagram 1: Material Readiness Evaluation

```
┌─────────┐      ┌──────────────┐      ┌───────────────────┐      ┌──────────┐      ┌──────────┐
│ Planner │      │ Work Order   │      │ MaterialReadiness │      │  Stock   │      │  Stock   │
│         │      │              │      │     Engine        │      │  Entry   │      │  Ledger  │
└────┬────┘      └──────┬───────┘      └─────────┬─────────┘      └────┬─────┘      └────┬─────┘
     │                  │                        │                     │                 │
     │  Submit WO       │                        │                     │                 │
     │─────────────────>│                        │                     │                 │
     │                  │                        │                     │                 │
     │                  │  on_submit event       │                     │                 │
     │                  │───────────────────────>│                     │                 │
     │                  │                        │                     │                 │
     │                  │                        │  get_department_warehouse()
     │                  │                        │─────────────────────│                 │
     │                  │                        │                     │                 │
     │                  │                        │<────────────────────│                 │
     │                  │                        │  warehouse          │                 │
     │                  │                        │                     │                 │
     │                  │                        │  get_required_materials()
     │                  │                        │─────────────────────│                 │
     │                  │                        │                     │                 │
     │                  │                        │<────────────────────│                 │
     │                  │                        │  materials[]        │                 │
     │                  │                        │                     │                 │
     │                  │                        │  For each material: │                 │
     │                  │                        │  get_cumulative_transferred_qty()
     │                  │                        │─────────────────────────────────────>│
     │                  │                        │                     │                 │
     │                  │                        │<─────────────────────────────────────│
     │                  │                        │  cumulative_qty     │                 │
     │                  │                        │                     │                 │
     │                  │                        │  get_actual_stock() │                 │
     │                  │                        │─────────────────────────────────────>│
     │                  │                        │                     │                 │
     │                  │                        │<─────────────────────────────────────│
     │                  │                        │  actual_qty         │                 │
     │                  │                        │                     │                 │
     │                  │                        │  determine_transfer_status()
     │                  │                        │                     │                 │
     │                  │                        │                     │                 │
     │                  │  Update custom fields  │                     │                 │
     │                  │<───────────────────────│                     │                 │
     │                  │                        │                     │                 │
     │                  │  Refresh Job Cards     │                     │                 │
     │                  │───────────────────────>│                     │                 │
     │                  │                        │                     │                 │
```

---

## Diagram 2: Job Card Start Validation

```
┌──────────┐      ┌───────────┐      ┌───────────────┐      ┌──────────────┐      ┌──────────────┐
│ Operator │      │ Job Card  │      │ Execution     │      │ Dependency   │      │  Material    │
│          │      │           │      │ Engine        │      │ Engine       │      │  Engine      │
└────┬─────┘      └─────┬─────┘      └───────┬───────┘      └──────┬───────┘      └──────┬───────┘
     │                  │                    │                     │                     │
     │  Click Start     │                    │                     │                     │
     │─────────────────>│                    │                     │                     │
     │                  │                    │                     │                     │
     │                  │  before_save       │                     │                     │
     │                  │───────────────────>│                     │                     │
     │                  │                    │                     │                     │
     │                  │                    │  can_job_card_start()
     │                  │                    │─────────────────────│                     │
     │                  │                    │                     │                     │
     │                  │                    │                     │  validate_previous_operation()
     │                  │                    │                     │────────────────────>│
     │                  │                    │                     │                     │
     │                  │                    │                     │<────────────────────│
     │                  │                    │                     │  dep_result         │
     │                  │                    │                     │                     │
     │                  │                    │                     │  can_job_card_start()
     │                  │                    │──────────────────────────────────────────>│
     │                  │                    │                     │                     │
     │                  │                    │<──────────────────────────────────────────│
     │                  │                    │  material_result   │                     │
     │                  │                    │                     │                     │
     │                  │                    │  Check results     │                     │
     │                  │                    │                     │                     │
     │                  │                    │                     │                     │
     │                  │  Throw Error       │                     │                     │
     │                  │<───────────────────│                     │                     │
     │                  │  (if validation fails)
     │                  │                     │                     │                     │
     │  Error Message   │                     │                     │                     │
     │<─────────────────│                     │                     │                     │
     │                  │                     │                     │                     │
     │                  │  Update status     │                     │                     │
     │                  │  (if validation passes)
     │                  │<───────────────────│                     │                     │
     │                  │                     │                     │                     │
     │  Success         │                     │                     │                     │
     │<─────────────────│                     │                     │                     │
     │                  │                     │                     │                     │
```

---

## Diagram 3: Stock Entry to Material Refresh

```
┌─────────┐      ┌───────────┐      ┌──────────────┐      ┌───────────────────┐      ┌──────────┐
│ Stores  │      │ Stock     │      │ Stock        │      │ MaterialReadiness │      │  Job     │
│         │      │ Entry     │      │ Service      │      │ Engine            │      │  Card    │
└────┬────┘      └─────┬─────┘      └──────┬───────┘      └─────────┬─────────┘      └────┬─────┘
     │                 │                   │                        │                     │
     │  Create SE      │                   │                        │                     │
     │────────────────>│                   │                        │                     │
     │                 │                   │                        │                     │
     │  Submit SE      │                   │                        │                     │
     │────────────────>│                   │                        │                     │
     │                 │                   │                        │                     │
     │                 │  on_submit        │                        │                     │
     │                 │──────────────────>│                        │                     │
     │                 │                   │                        │                     │
     │                 │                   │  Check purpose         │                     │
     │                 │                   │  (MTF for Manufacture) │                     │
     │                 │                   │                        │                     │
     │                 │                   │  evaluate_material_readiness()
     │                 │                   │───────────────────────>│                     │
     │                 │                   │                        │                     │
     │                 │                   │                        │  get_cumulative_transferred_qty()
     │                 │                   │                        │  (MR-011)           │
     │                 │                   │                        │                     │
     │                 │                   │                        │                     │
     │                 │                   │<───────────────────────│                     │
     │                 │                   │  result               │                     │
     │                 │                   │                        │                     │
     │                 │                   │                        │                     │
     │                 │  Update WO        │                        │                     │
     │                 │<──────────────────│                        │                     │
     │                 │  custom_material_readiness
     │                 │  custom_transfer_completeness
     │                 │                   │                        │                     │
     │                 │  Refresh Job Cards│                        │                     │
     │                 │────────────────────────────────────────────────────────────────>│
     │                 │                   │                        │  update_material_status()
     │                 │                   │                        │                     │
     │                 │                   │                        │                     │
     │                 │  Notify if Ready  │                        │                     │
     │                 │<──────────────────│                        │                     │
     │                 │                   │                        │                     │
     │  Notification   │                   │                        │                     │
     │<────────────────│                   │                        │                     │
     │                 │                   │                        │                     │
```

---

## Diagram 4: Job Card Completion to Auto-Complete WO

```
┌──────────┐      ┌───────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────┐
│ Operator │      │ Job Card  │      │ Job Card     │      │ Execution    │      │  Stock   │
│          │      │           │      │ Service      │      │ Engine       │      │  Entry   │
└────┬─────┘      └─────┬─────┘      └──────┬───────┘      └──────┬───────┘      └────┬─────┘
     │                  │                   │                     │                   │
     │  Complete JC     │                   │                     │                   │
     │─────────────────>│                   │                     │                   │
     │                  │                   │                     │                   │
     │  Submit JC       │                   │                     │                   │
     │─────────────────>│                   │                     │                   │
     │                  │                   │                     │                   │
     │                  │  on_submit        │                     │                   │
     │                  │──────────────────>│                     │                   │
     │                  │                   │                     │                   │
     │                  │                   │  Validate completion
     │                  │                   │  (JC-002)           │                   │
     │                  │                   │                     │                   │
     │                  │                   │  Get next JC        │                   │
     │                  │                   │─────────────────────│                   │
     │                  │                   │                     │                   │
     │                  │                   │<────────────────────│                   │
     │                  │                   │  next_jc            │                   │
     │                  │                   │                     │                   │
     │                  │                   │  Refresh next JC    │                   │
     │                  │─────────────────────────────────────────│                   │
     │                  │                   │  update_start_status()
     │                  │                   │                     │                   │
     │                  │                   │  Refresh WO progress
     │                  │─────────────────────────────────────────│                   │
     │                  │                   │                     │                   │
     │                  │                   │  Check auto-complete (WO-001)
     │                  │                   │─────────────────────│                   │
     │                  │                   │                     │                   │
     │                  │                   │                     │  All JC complete? │
     │                  │                   │                     │                   │
     │                  │                   │                     │  Yes              │
     │                  │                   │                     │                   │
     │                  │                   │                     │  Create Manufacture SE
     │                  │                   │────────────────────────────────────────>│
     │                  │                   │                     │                   │
     │                  │                   │<────────────────────────────────────────│
     │                  │                   │  se.name            │                   │
     │                  │                   │                     │                   │
     │                  │                   │  Submit SE          │                   │
     │                  │                   │────────────────────────────────────────>│
     │                  │                   │                     │                   │
     │                  │                   │  Update WO status
     │                  │<──────────────────│                     │                   │
     │                  │  Completed        │                     │                   │
     │                  │                   │                     │                   │
     │  Success         │                   │                     │                   │
     │<─────────────────│                   │                     │                   │
     │                  │                   │                     │                   │
```

---

## Diagram 5: Exception Handling

```
┌──────────┐      ┌───────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────┐
│ System   │      │ Exception │      │ Exception    │      │ Notification │      │  User    │
│          │      │ Handler   │      │ Logger       │      │ Service      │      │          │
└────┬─────┘      └─────┬─────┘      └──────┬───────┘      └──────┬───────┘      └────┬─────┘
     │                  │                   │                     │                   │
     │  Exception       │                   │                     │                   │
     │  Occurs          │                   │                     │                   │
     │─────────────────>│                   │                     │                   │
     │                  │                   │                     │                   │
     │                  │  Map to code       │                     │                   │
     │                  │  (EX-XXX)          │                     │                   │
     │                  │                   │                     │                   │
     │                  │  Create log entry  │                     │                   │
     │                  │──────────────────>│                     │                   │
     │                  │                   │                     │                   │
     │                  │                   │  Insert to DB       │                   │
     │                  │                   │  (MES Exception Log)│                   │
     │                  │                   │                     │                   │
     │                  │                   │                     │                   │
     │                  │  Determine severity│                     │                   │
     │                  │───────────────────│                     │                   │
     │                  │                   │                     │                   │
     │                  │  Notify stakeholders
     │                  │────────────────────────────────────────>│                   │
     │                  │                   │                     │                   │
     │                  │                   │                     │  Send email       │
     │                  │                   │                     │  Send notification│
     │                  │                   │                     │                   │
     │                  │  Update document status
     │                  │───────────────────────────────────────────────────────────>│
     │                  │                   │                     │  custom_exception_code
     │                  │                   │                     │  custom_exception_message
     │                  │                   │                     │                   │
     │                  │  Block operation  │                     │                   │
     │                  │<──────────────────│                     │                   │
     │                  │                   │                     │                   │
     │  Error Message   │                   │                     │                   │
     │<─────────────────│                   │                     │                   │
     │                  │                   │                     │                   │
     │  Notification    │                   │                     │                   │
     │<──────────────────────────────────────────────────────────────────────────────│
     │                  │                   │                     │                   │
```

---

## Diagram 6: Department Transfer Integration

```
┌─────────┐      ┌───────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────┐
│ Planner │      │ Work Order│      │ Material     │      │  Stock       │      │  Job     │
│         │      │           │      │ Engine       │      │  Service     │      │  Card    │
└────┬────┘      └─────┬─────┘      └──────┬───────┘      └──────┬───────┘      └────┬─────┘
     │                 │                   │                     │                   │
     │  Generate WO    │                   │                     │                   │
     │────────────────>│                   │                     │                   │
     │                 │                   │                     │                   │
     │  Submit WO      │                   │                     │                   │
     │────────────────>│                   │                     │                   │
     │                 │                   │                     │                   │
     │                 │  Evaluate readiness
     │                 │──────────────────>│                     │                   │
     │                 │                   │                     │                   │
     │                 │                   │  Get suggestions    │                   │
     │                 │                   │─────────────────────│                   │
     │                 │                   │                     │                   │
     │                 │                   │<────────────────────│                   │
     │                 │                   │  suggestions[]      │                   │
     │                 │                   │                     │                   │
     │                 │  Not Ready        │                     │                   │
     │                 │<──────────────────│                     │                   │
     │                 │                   │                     │                   │
     │  Notifications  │                   │                     │                   │
     │<────────────────│                   │                     │                   │
     │                 │                   │                     │                   │
     │  Create Transfer│                   │                     │                   │
     │──────────────────────────────────────────────────────────>│                   │
     │                 │                   │                     │                   │
     │                 │  Submit SE        │                     │                   │
     │                 │────────────────────────────────────────>│                   │
     │                 │                   │                     │                   │
     │                 │                   │  Refresh readiness  │                   │
     │                 │────────────────────────────────────────>│                   │
     │                 │                   │                     │                   │
     │                 │                   │<────────────────────│                   │
     │                 │                   │  Now Ready          │                   │
     │                 │                   │                     │                   │
     │                 │  Refresh JC       │                     │                   │
     │                 │───────────────────────────────────────────────────────────>│
     │                 │                   │                     │  Update status   │
     │                 │                   │                     │  Ready to Start  │
     │                 │                   │                     │                   │
     │                 │                   │                     │                   │
     │  Ready to Start │                   │                     │                   │
     │<────────────────────────────────────────────────────────────────────────────│
     │                 │                   │                     │                   │
```

---

## Diagram Notation

| Symbol       | Meaning                          |
|--------------|----------------------------------|
| `───> `       | Synchronous call                 |
| `───>│`       | Asynchronous call                |
| `<───│`       | Return value                     |
| `┌───┐`       | Object/Component                 |
| `│   │`       | Lifeline                         |
| `Note`        | Additional information           |

---

## Revision History

| Version | Date       | Author      | Changes                          |
|---------|------------|-------------|----------------------------------|
| 1.0     | 2026-07-31 | Development | Initial creation                 |

---

## Related Documents

- MES_EVENT_FLOW.md - Event triggers
- MES_SERVICE_INTERFACES.md - Method signatures
- MES_ARCHITECTURE_IMPLEMENTATION.md - Architecture overview
