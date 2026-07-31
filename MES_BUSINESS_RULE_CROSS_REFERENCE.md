# MES Business Rule Cross Reference

**Document Type:** Traceability Document  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Frozen for Implementation  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document provides complete traceability from business rules to implementation to test cases.

Format: `Business Rule → Implementation → Event Flow → Test Case`

---

## Material Readiness Rules (MR)

### MR-010: Stores transfers materials to Department Warehouse

| Aspect              | Reference                                          |
|---------------------|----------------------------------------------------|
| **Business Rule**   | MES_BUSINESS_RULES.md#mr-010                       |
| **Implementation**  | `MaterialReadinessEngine.evaluate_material_readiness()` |
|                     | `MaterialReadinessEngine.get_department_warehouse()` |
|                     | `StockService.create_material_transfer()`          |
| **Repository**      | `WarehouseRepository.get_department_warehouse()`   |
|                     | `StockRepository.get_cumulative_transfers()`       |
| **Event Flow**      | MES_EVENT_FLOW.md#event-flow-1-work-order-creation |
|                     | MES_EVENT_FLOW.md#event-flow-2-stock-entry-submit  |
| **Sequence Diagram**| MES_SEQUENCE_DIAGRAMS.md#diagram-1-material-readiness |
|                     | MES_SEQUENCE_DIAGRAMS.md#diagram-6-department-transfer |
| **API**             | `evaluate_material_readiness(work_order)`          |
|                     | `can_job_card_start(job_card)`                     |
|                     | `get_transfer_suggestions(work_order)`             |
|                     | `create_material_transfer_stock_entry(work_order)` |
| **Test Case**       | `test_mr_010_evaluate_readiness_no_transfers`      |
|                     | `test_mr_010_department_warehouse_mapping`         |
|                     | `test_mr_010_job_card_start_permission_no_transfers` |
|                     | `test_mr_010_transfer_suggestions_structure`       |
| **Custom Fields**   | `Work Order.custom_material_readiness`             |
|                     | `Work Order.custom_transfer_completeness`          |
|                     | `Job Card.custom_material_status`                  |
| **Configuration**   | `MES Settings.allow_partial_transfer`              |
|                     | `MES Settings.material_check_mode`                 |
| **Logging**         | `[MES] [MATERIAL] [INFO] [MR-010]`                 |

---

### MR-011: Cumulative availability check

| Aspect              | Reference                                          |
|---------------------|----------------------------------------------------|
| **Business Rule**   | MES_BUSINESS_RULES.md#mr-011                       |
| **Implementation**  | `MaterialReadinessEngine.get_cumulative_transferred_qty()` |
|                     | `MaterialReadinessEngine.get_transfer_entries()`   |
|                     | `StockService.get_cumulative_transfers()`          |
| **Repository**      | `StockRepository.get_cumulative_transfers()`       |
|                     | `StockRepository.get_transfer_entries()`           |
| **Event Flow**      | MES_EVENT_FLOW.md#event-flow-2-stock-entry-submit  |
| **Sequence Diagram**| MES_SEQUENCE_DIAGRAMS.md#diagram-1-material-readiness |
| **API**             | `evaluate_material_readiness(work_order)`          |
|                     | `get_cumulative_transfers(item_code, work_order, warehouse)` |
| **Test Case**       | `test_mr_011_cumulative_transfer_single_entry`     |
|                     | `test_mr_011_cumulative_transfer_multiple_entries` |
|                     | `test_mr_011_transfer_entries_details`             |
|                     | `test_mr_011_partial_transfer_readiness`           |
|                     | `test_mr_011_cumulative_availability_working_set`  |
| **Custom Fields**   | `Stock Entry.custom_transfer_stage`                |
|                     | `Stock Entry.custom_cumulative_qty`                |
| **Configuration**   | `MES Settings.allow_partial_transfer`              |
| **Logging**         | `[MES] [MATERIAL] [INFO] [MR-011]`                 |

---

## Dependency Validation Rules (DV)

### DV-001: Previous operation validation

| Aspect              | Reference                                          |
|---------------------|----------------------------------------------------|
| **Business Rule**   | MES_BUSINESS_RULES.md#dv-001                       |
| **Implementation**  | `DependencyEngine.validate_previous_operation()`   |
|                     | `JobCardService.can_start()`                       |
| **Repository**      | `JobCardRepository.get_previous_operation()`       |
| **Event Flow**      | MES_EVENT_FLOW.md#event-flow-3-job-card-start      |
| **Sequence Diagram**| MES_SEQUENCE_DIAGRAMS.md#diagram-2-job-card-start  |
| **API**             | `can_job_card_start(job_card)`                     |
| **Test Case**       | _To be created in Sprint 2_                        |
| **Custom Fields**   | `Job Card.custom_dependency_status`                |
|                     | `Job Card.custom_dependency_message`               |
|                     | `Job Card.custom_previous_operation`               |
| **Configuration**   | `MES Settings.check_previous_op`                   |
|                     | `MES Settings.strict_sequence`                     |
| **Logging**         | `[MES] [DEPENDENCY] [INFO] [DV-001]`               |

---

### DV-002: Sequence validation

| Aspect              | Reference                                          |
|---------------------|----------------------------------------------------|
| **Business Rule**   | MES_BUSINESS_RULES.md#dv-002                       |
| **Implementation**  | `DependencyEngine.validate_sequence()`             |
| **Repository**      | `JobCardRepository.get_sequence_details()`         |
| **Event Flow**      | MES_EVENT_FLOW.md#event-flow-3-job-card-start      |
| **Sequence Diagram**| MES_SEQUENCE_DIAGRAMS.md#diagram-2-job-card-start  |
| **API**             | `can_job_card_start(job_card)`                     |
| **Test Case**       | _To be created in Sprint 2_                        |
| **Custom Fields**   | `Job Card.custom_dependency_status`                |
| **Configuration**   | `MES Settings.check_sequence`                      |
|                     | `MES Settings.allow_parallel_ops`                  |
| **Logging**         | `[MES] [DEPENDENCY] [INFO] [DV-002]`               |

---

## Job Card Execution Rules (JC)

### JC-001: Job Card Start Permission

| Aspect              | Reference                                          |
|---------------------|----------------------------------------------------|
| **Business Rule**   | MES_BUSINESS_RULES.md#jc-001                       |
| **Implementation**  | `ExecutionEngine.can_job_card_start()`             |
|                     | `JobCardService.can_start()`                       |
| **Event Flow**      | MES_EVENT_FLOW.md#event-flow-3-job-card-start      |
| **Sequence Diagram**| MES_SEQUENCE_DIAGRAMS.md#diagram-2-job-card-start  |
| **Test Case**       | _To be created in Sprint 3_                        |
| **State Machine**   | MES_STATE_MACHINE.md#job-card-state-machine        |
| **Logging**         | `[MES] [EXECUTION] [INFO] [JC-001]`                |

---

### JC-002: Job Card Completion Permission

| Aspect              | Reference                                          |
|---------------------|----------------------------------------------------|
| **Business Rule**   | MES_BUSINESS_RULES.md#jc-002                       |
| **Implementation**  | `ExecutionEngine.can_job_card_complete()`          |
|                     | `JobCardService.can_complete()`                    |
| **Event Flow**      | MES_EVENT_FLOW.md#event-flow-4-job-card-completion |
| **Sequence Diagram**| MES_SEQUENCE_DIAGRAMS.md#diagram-4-job-card-complete |
| **Test Case**       | _To be created in Sprint 3_                        |
| **State Machine**   | MES_STATE_MACHINE.md#job-card-state-machine        |
| **Logging**         | `[MES] [EXECUTION] [INFO] [JC-002]`                |

---

### JC-004: Job Card Auto-Refresh

| Aspect              | Reference                                          |
|---------------------|----------------------------------------------------|
| **Business Rule**   | MES_BUSINESS_RULES.md#jc-004                       |
| **Implementation**  | `JobCardService.refresh_status()`                  |
| **Event Flow**      | MES_EVENT_FLOW.md#event-flow-4-job-card-completion |
| **Test Case**       | _To be created in Sprint 3_                        |
| **Configuration**   | `MES Settings.auto_refresh_deps`                   |
|                     | `MES Settings.refresh_mode`                        |
| **Logging**         | `[MES] [DIAGNOSTIC] [INFO]`                        |

---

## Work Order Completion Rules (WO)

### WO-001: Auto-Completion Trigger

| Aspect              | Reference                                          |
|---------------------|----------------------------------------------------|
| **Business Rule**   | MES_BUSINESS_RULES.md#wo-001                       |
| **Implementation**  | `ExecutionEngine.complete_work_order()`            |
|                     | `WorkOrderService.complete()`                      |
| **Repository**      | `WorkOrderRepository.get_production_progress()`    |
| **Event Flow**      | MES_EVENT_FLOW.md#event-flow-5-wo-auto-complete    |
| **Sequence Diagram**| MES_SEQUENCE_DIAGRAMS.md#diagram-4-job-card-complete |
| **Test Case**       | _To be created in Sprint 3_                        |
| **State Machine**   | MES_STATE_MACHINE.md#work-order-state-machine      |
| **Logging**         | `[MES] [EXECUTION] [INFO] [WO-001]`                |

---

### WO-002: Duplicate Stock Entry Prevention

| Aspect              | Reference                                          |
|---------------------|----------------------------------------------------|
| **Business Rule**   | MES_BUSINESS_RULES.md#wo-002                       |
| **Implementation**  | `ExecutionEngine.complete_work_order()`            |
| **Repository**      | `StockRepository.count_entries_by_work_order()`    |
| **Event Flow**      | MES_EVENT_FLOW.md#event-flow-5-wo-auto-complete    |
| **Test Case**       | _To be created in Sprint 3_                        |
| **Configuration**   | `MES Settings.prevent_duplicate_se`                |
| **Logging**         | `[MES] [EXECUTION] [WARNING] [WO-002]`             |

---

## Warehouse Rules (WH)

### WH-002: Department Warehouse Mapping

| Aspect              | Reference                                          |
|---------------------|----------------------------------------------------|
| **Business Rule**   | MES_BUSINESS_RULES.md#wh-002                       |
| **Implementation**  | `MaterialReadinessEngine.get_department_warehouse()` |
|                     | `WarehouseRepository.get_department_warehouse()`   |
| **Event Flow**      | MES_EVENT_FLOW.md#event-flow-1-work-order-creation |
| **Sequence Diagram**| MES_SEQUENCE_DIAGRAMS.md#diagram-1-material-readiness |
| **Test Case**       | `test_mr_010_department_warehouse_mapping`         |
| **Custom Fields**   | `Warehouse.custom_plant_floor`                     |
|                     | `Warehouse.custom_department`                      |
| **Configuration**   | `MES Settings.default_wip_group`                   |
|                     | `MES Settings.warehouse_naming`                    |
| **Logging**         | `[MES] [MATERIAL] [INFO] [WH-002]`                 |

---

## Security Rules (SEC)

### SEC-001: Permission Checking

| Aspect              | Reference                                          |
|---------------------|----------------------------------------------------|
| **Business Rule**   | MES_BUSINESS_RULES.md#sec-001                      |
| **Implementation**  | `Permissions.check_start_permission()`             |
| **Utility**         | `utils.validate_user_permission()`                 |
| **Event Flow**      | MES_EVENT_FLOW.md#event-flow-3-job-card-start      |
| **Test Case**       | _To be created in Sprint 7_                        |
| **Configuration**   | `MES Settings.enable_permissions`                  |
| **Logging**         | `[MES] [SECURITY] [INFO] [SEC-001]`                |

---

### SEC-002: Department Scope

| Aspect              | Reference                                          |
|---------------------|----------------------------------------------------|
| **Business Rule**   | MES_BUSINESS_RULES.md#sec-002                      |
| **Implementation**  | `Permissions.check_department_scope()`             |
| **Repository**      | `WarehouseRepository.validate_warehouse_access()`  |
| **Event Flow**      | MES_EVENT_FLOW.md#exception-handling               |
| **Test Case**       | _To be created in Sprint 7_                        |
| **Configuration**   | `MES Settings.department_scope`                    |
| **Logging**         | `[MES] [SECURITY] [WARNING] [SEC-002]`             |

---

## Exception Handling Rules (EX-*)

### All 46 Exception Scenarios

| Exception Category | Count | Implementation                          | Logging                    |
|--------------------|-------|-----------------------------------------|----------------------------|
| EX-MAT (Material)  | 8     | `MaterialReadinessEngine`               | `[MES] [EXCEPTION] [ERROR]`|
| EX-PROD (Production)| 10   | `ExecutionEngine`                       | `[MES] [EXCEPTION] [ERROR]`|
| EX-EQ (Equipment)  | 8     | _To be implemented_                     | `[MES] [EXCEPTION] [ERROR]`|
| EX-Q (Quality)     | 8     | _To be implemented_                     | `[MES] [EXCEPTION] [ERROR]`|
| EX-CANCEL (Cancellation)| 6 | _To be implemented_                 | `[MES] [EXCEPTION] [ERROR]`|
| EX-SYS (System)    | 6     | `utils.exceptions`                      | `[MES] [EXCEPTION] [CRITICAL]`|

---

## Traceability Matrix Summary

| Business Rule | Implementation | Test Case | Status      |
|---------------|----------------|-----------|-------------|
| MR-010        | ✅ Complete     | ✅ Complete | Sprint 1   |
| MR-011        | ✅ Complete     | ✅ Complete | Sprint 1   |
| DV-001        | ⏳ Sprint 2     | ⏳ Sprint 2 | Planned    |
| DV-002        | ⏳ Sprint 2     | ⏳ Sprint 2 | Planned    |
| JC-001        | ⏳ Sprint 3     | ⏳ Sprint 3 | Planned    |
| JC-002        | ⏳ Sprint 3     | ⏳ Sprint 3 | Planned    |
| WO-001        | ⏳ Sprint 3     | ⏳ Sprint 3 | Planned    |
| WO-002        | ⏳ Sprint 3     | ⏳ Sprint 3 | Planned    |
| WH-002        | ✅ Complete     | ✅ Complete | Sprint 1   |
| SEC-001       | ⏳ Sprint 7     | ⏳ Sprint 7 | Planned    |
| SEC-002       | ⏳ Sprint 7     | ⏳ Sprint 7 | Planned    |
| EX-* (46)     | ⏳ Sprint 6     | ⏳ Sprint 6 | Planned    |

---

## Revision History

| Version | Date       | Author      | Changes                          |
|---------|------------|-------------|----------------------------------|
| 1.0     | 2026-07-31 | Development | Initial creation                 |

---

## Related Documents

- MES_IMPLEMENTATION_MATRIX.md - Sprint planning
- MES_TEST_SCENARIOS.md - Test case definitions
- MES_EVENT_FLOW.md - Event triggers
