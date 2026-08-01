# MES Data Dictionary

**Document Type:** Technical Specification  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Frozen for Implementation  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document defines all custom fields, DocTypes, and data structures used in the MES implementation. All developers MUST reference this document before creating new fields or modifying existing ones.

---

## Custom Fields by DocType

### Job Card

| Field Name                     | Type       | Length | Purpose                                      | Used By                        | Required | Default        |
|--------------------------------|------------|--------|----------------------------------------------|--------------------------------|----------|----------------|
| `custom_start_status`          | Select     | 50     | MES-controlled start status                  | Material Engine, Dependency Engine | Yes      | Not Ready      |
| `custom_can_start`             | Check      | -      | Flag indicating if JC can start              | Execution Engine               | No       | 0              |
| `custom_material_status`       | Select     | 20     | Material readiness status                    | Material Engine                | No       | Not Checked    |
| `custom_material_status_details` | Small Text | 500    | Detailed material readiness message          | UI, Diagnostics                | No       | -              |
| `custom_dependency_status`     | Select     | 20     | Dependency validation status                 | Dependency Engine              | No       | Not Checked    |
| `custom_dependency_message`    | Small Text | 500    | Detailed dependency validation message       | UI, Diagnostics                | No       | -              |
| `custom_previous_operation`    | Link       | -      | Previous Job Card reference                  | Dependency Engine              | No       | -              |
| `custom_next_operation`        | Link       | -      | Next Job Card reference                      | Execution Engine               | No       | -              |
| `custom_department`            | Link       | -      | Department executing this JC                 | Security, UI                   | No       | -              |
| `custom_plant_floor`           | Link       | -      | Plant floor location                         | Material Engine                | No       | -              |
| `custom_exception_code`        | Data       | 50     | Exception code if blocked                    | Exception Handler              | No       | -              |
| `custom_exception_message`     | Small Text | 500    | User-friendly exception message              | UI                             | No       | -              |
| `custom_last_refreshed`        | Datetime   | -      | Last time status was refreshed               | Service Layer                  | No       | -              |
| `custom_refreshed_by`          | Data       | 100    | User who last refreshed                      | Audit                          | No       | -              |

**Options for Select Fields:**

- `custom_start_status`: Not Ready, Ready to Start, In Progress, Completed, Awaiting Previous Operation, Awaiting Materials, Blocked
- `custom_material_status`: Not Checked, Ready, Not Ready, Partially Ready
- `custom_dependency_status`: Not Checked, Valid, Invalid, Pending

---

### Work Order

| Field Name                     | Type       | Length | Purpose                                      | Used By                        | Required | Default        |
|--------------------------------|------------|--------|----------------------------------------------|--------------------------------|----------|----------------|
| `custom_department`            | Link       | -      | Department responsible for execution         | Material Engine, Security      | No       | -              |
| `custom_plant_floor`           | Link       | -      | Plant floor location                         | Material Engine                | No       | -              |
| `custom_material_readiness`    | Select     | 20     | Overall material readiness status            | UI, Material Engine            | No       | Not Checked    |
| `custom_transfer_completeness` | Percent    | -      | Percentage of materials transferred          | UI, Material Engine            | No       | 0              |
| `custom_dependency_status`     | Select     | 20     | Overall dependency status                    | Dependency Engine              | No       | Not Checked    |
| `custom_exception_count`       | Int        | -      | Count of active exceptions                   | Exception Handler              | No       | 0              |
| `custom_last_validated`        | Datetime   | -      | Last validation timestamp                    | Service Layer                  | No       | -              |

**Options for Select Fields:**

- `custom_material_readiness`: Not Checked, Ready, Not Ready, Partially Ready
- `custom_dependency_status`: Not Checked, Valid, Invalid, Pending

---

### Warehouse

| Field Name                     | Type       | Length | Purpose                                      | Used By                        | Required | Default        |
|--------------------------------|------------|--------|----------------------------------------------|--------------------------------|----------|----------------|
| `custom_plant_floor`           | Link       | -      | Plant floor this warehouse serves            | Material Engine                | No       | -              |
| `custom_department`            | Link       | -      | Department owning this warehouse             | Security                       | No       | -              |
| `custom_warehouse_type`        | Select     | 50     | Type: WIP, Raw Material, Finished Goods      | Material Engine                | No       | -              |

**Options for Select Fields:**

- `custom_arehouse_type`: WIP, Raw Material, BOF, Finished Goods, Scrap, Rejected

---

### Stock Entry

| Field Name                     | Type       | Length | Purpose                                      | Used By                        | Required | Default        |
|--------------------------------|------------|--------|----------------------------------------------|--------------------------------|----------|----------------|
| `custom_department`            | Link       | -      | Department receiving/sending                 | Material Engine                | No       | -              |
| `custom_plant_floor`           | Link       | -      | Plant floor location                         | Material Engine                | No       | -              |
| `custom_transfer_stage`        | Select     | 50     | Stage of transfer: Partial, Complete         | Material Engine                | No       | -              |
| `custom_cumulative_qty`        | Float      | -      | Cumulative quantity transferred              | Material Engine                | No       | -              |

**Options for Select Fields:**

- `custom_transfer_stage`: Partial, Complete, First Transfer, Final Transfer

---

### Operation

| Field Name                     | Type       | Length | Purpose                                      | Used By                        | Required | Default        |
|--------------------------------|------------|--------|----------------------------------------------|--------------------------------|----------|----------------|
| `custom_sequence_required`     | Check      | -      | Whether sequence must be enforced            | Dependency Engine              | No       | 1              |
| `custom_department`            | Link       | -      | Default department for this operation        | Execution Engine               | No       | -              |
| `custom_workstation_type`      | Link       | -      | Workstation type capability                  | Execution Engine               | No       | -              |

---

### Workstation

| Field Name                     | Type       | Length | Purpose                                      | Used By                        | Required | Default        |
|--------------------------------|------------|--------|----------------------------------------------|--------------------------------|----------|----------------|
| `custom_plant_floor`           | Link       | -      | Plant floor location                         | Execution Engine               | No       | -              |
| `custom_department`            | Link       | -      | Department owning workstation                | Security                       | No       | -              |
| `custom_workstation_type`      | Link       | -      | Workstation type for capability grouping     | Execution Engine               | No       | -              |
| `custom_status`                | Select     | 20     | Operational status                           | Execution Engine               | No       | Available      |

**Options for Select Fields:**

- `custom_status`: Available, Busy, Down, Under Maintenance, Blocked

---

## Custom DocTypes

### MES Settings

**Purpose:** Central configuration for MES behavior

| Field Name                     | Type       | Length | Purpose                                      | Default        |
|--------------------------------|------------|--------|----------------------------------------------|----------------|
| `allow_partial_transfer`       | Check      | -      | Allow partial material transfers             | 1              |
| `auto_complete_work_order`     | Check      | -      | Auto-complete WO when all JC done            | 1              |
| `refresh_mode`                 | Select     | 20     | Refresh mode: Immediate, Scheduled, Manual   | Immediate      |
| `material_check_mode`          | Select     | 50     | Material check: Department Warehouse, BOM    | Department Warehouse |
| `allow_override_role`          | Link       | -      | Role allowed to override validations         | Manufacturing Manager |
| `enable_strict_validation`     | Check      | -      | Enable strict validation mode                | 0              |
| `log_level`                    | Select     | 20     | Logging level: INFO, WARNING, ERROR          | INFO           |

---

### MES Exception Log

**Purpose:** Centralized exception tracking

| Field Name                     | Type       | Length | Purpose                                      | Required |
|--------------------------------|------------|--------|----------------------------------------------|----------|
| `exception_code`               | Data       | 50     | Exception code (e.g., EX-MAT-001)            | Yes      |
| `exception_category`           | Select     | 50     | Category: Material, Production, Equipment    | Yes      |
| `severity`                     | Select     | 20     | Severity: Low, Medium, High, Critical        | Yes      |
| `reference_doctype`            | Link       | -      | DocType where exception occurred             | Yes      |
| `reference_docname`            | Data       | 100    | Document name                                | Yes      |
| `department`                   | Link       | -      | Department affected                          | No       |
| `message`                      | Small Text | 500    | Exception message                            | Yes      |
| `resolution`                   | Small Text | 500    | Resolution steps                             | No       |
| `status`                       | Select     | 20     | Status: Open, In Progress, Resolved, Closed  | Yes      |
| `raised_by`                    | Link       | -      | User who raised exception                    | No       |
| `resolved_by`                  | Link       | -      | User who resolved                            | No       |
| `resolution_time`              | Float      | -      | Time taken to resolve (hours)                | No       |

---

### MES Transfer Suggestion

**Purpose:** Temporary table for material transfer suggestions

| Field Name                     | Type       | Length | Purpose                                      | Required |
|--------------------------------|------------|--------|----------------------------------------------|----------|
| `work_order`                   | Link       | -      | Work Order reference                         | Yes      |
| `item_code`                    | Link       | -      | Item to transfer                             | Yes      |
| `required_qty`                 | Float      | -      | Required quantity                            | Yes      |
| `transferred_qty`              | Float      | -      | Already transferred                          | Yes      |
| `remaining_qty`                | Float      | -      | Remaining to transfer                        | Yes      |
| `source_warehouse`             | Link       | -      | Source warehouse                             | Yes      |
| `target_warehouse`             | Link       | -      | Target warehouse                             | Yes      |
| `available_in_source`          | Float      | -      | Available in source warehouse                | Yes      |
| `can_transfer`                 | Check      | -      | Whether transfer is possible                 | Yes      |
| `suggested_by`                 | Data       | 100    | Engine/user who suggested                    | No       |
| `suggested_on`                 | Datetime   | -      | Suggestion timestamp                         | No       |

---

## Field Naming Conventions

1. **Custom fields:** Always prefix with `custom_`
2. **System fields:** No prefix (use ERPNext standard fields)
3. **Link fields:** Use DocType name (e.g., `custom_department` not `custom_dept`)
4. **Boolean fields:** Use `is_`, `can_`, `allow_`, `enable_` prefixes
5. **Quantity fields:** Use `_qty` suffix
6. **Date/Time fields:** Use `_on` or `_at` suffix
7. **Reference fields:** Use `_reference` or specific DocType name

---

## Data Types Reference

| ERPNext Type | Python Type    | SQL Type      | Description                    |
|--------------|----------------|---------------|--------------------------------|
| Data         | str            | VARCHAR       | Short text (up to 140 chars)   |
| Small Text   | str            | TEXT          | Medium text (up to 500 chars)  |
| Text         | str            | TEXT          | Large text                     |
| Long Text    | str            | LONGTEXT      | Very large text                |
| Int          | int            | INT           | Integer                        |
| Float        | float          | DECIMAL       | Decimal number                 |
| Currency     | float          | DECIMAL       | Currency value                 |
| Percent      | float          | DECIMAL       | Percentage (0-100)             |
| Check        | bool           | TINYINT       | Boolean (0 or 1)               |
| Select       | str            | VARCHAR       | Dropdown selection             |
| Link         | str            | VARCHAR       | Reference to DocType           |
| Dynamic Link | str            | VARCHAR       | Dynamic reference              |
| Date         | datetime.date  | DATE          | Date only                      |
| Datetime     | datetime       | DATETIME      | Date and time                  |
| Time         | datetime.time  | TIME          | Time only                      |

---

## Field Creation Process

Before creating a new custom field:

1. ✅ Check this Data Dictionary for existing fields
2. ✅ Verify field doesn't exist in standard ERPNext
3. ✅ Define field purpose and usage
4. ✅ Identify all modules that will use the field
5. ✅ Document in this Data Dictionary
6. ✅ Create field via Custom Field or DocType
7. ✅ Update module docstrings with field references

---

## Field Deprecation

When deprecating a field:

1. Mark field as deprecated in this dictionary
2. Add deprecation warning in code
3. Maintain field for 1 sprint (migration period)
4. Remove field after confirming no usage
5. Update this dictionary with removal date

---

## Revision History

| Version | Date       | Author      | Changes                          |
|---------|------------|-------------|----------------------------------|
| 1.0     | 2026-07-31 | Development | Initial creation                 |

---

## Related Documents

- CODE_REVIEW_STANDARDS.md - Field naming conventions
- MES_BUSINESS_RULES.md - Business rules requiring fields
- MES_ARCHITECTURE_IMPLEMENTATION.md - Architecture context
