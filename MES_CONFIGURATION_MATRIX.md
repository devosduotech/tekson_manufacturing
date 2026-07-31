# MES Configuration Matrix

**Document Type:** Technical Specification  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Frozen for Implementation  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document defines all configurable settings in the MES system. **Do not hard-code** these values. All configuration must be stored in MES Settings DocType and accessed through the Service Layer.

---

## MES Settings DocType

**DocType:** `MES Settings`  
**Access:** `frappe.get_doc("MES Settings", "MES Settings")` (Single DocType)

---

## General Settings

| Field Name              | Type    | Default              | Description                                      | Used By                        |
|-------------------------|---------|----------------------|--------------------------------------------------|--------------------------------|
| `enable_mes`            | Check   | 1                    | Enable/disable MES functionality                 | All modules                    |
| `version`               | Data    | 1.0                  | MES version number                               | System                         |
| `last_updated`          | Datetime| -                    | Last settings update timestamp                   | Audit                          |

---

## Material Management Settings

| Field Name              | Type     | Default              | Description                                      | Business Rule     |
|-------------------------|----------|----------------------|--------------------------------------------------|-------------------|
| `allow_partial_transfer`| Check    | 1                    | Allow partial material transfers                 | MR-011            |
| `material_check_mode`   | Select   | Department Warehouse | Material check: Department Warehouse, BOM        | MR-010            |
| `auto_refresh_on_se`    | Check    | 1                    | Auto-refresh material status on Stock Entry      | Event Flow        |
| `transfer_notification` | Check    | 1                    | Notify production when materials ready           | Event Flow        |

**Options for `material_check_mode`:**
- `Department Warehouse` (default) - Check stock in department warehouse
- `BOM` - Check based on BOM requirements

---

## Execution Settings

| Field Name              | Type     | Default              | Description                                      | Business Rule     |
|-------------------------|----------|----------------------|--------------------------------------------------|-------------------|
| `allow_job_card_start`  | Check    | 1                    | Allow Job Card start                             | JC-001            |
| `strict_sequence`       | Check    | 1                    | Enforce strict operation sequence                | DV-001            |
| `allow_parallel_ops`    | Check    | 0                    | Allow parallel operations                        | DV-002            |
| `auto_complete_wo`      | Check    | 1                    | Auto-complete Work Order                         | WO-001            |
| `prevent_duplicate_se`  | Check    | 1                    | Prevent duplicate Stock Entries                  | WO-002            |

---

## Validation Settings

| Field Name              | Type     | Default              | Description                                      | Business Rule     |
|-------------------------|----------|----------------------|--------------------------------------------------|-------------------|
| `enable_strict_validation` | Check | 0                    | Enable strict validation mode                    | JC-003            |
| `validation_level`      | Select   | Warning              | Validation level: Warning, Error                 | JC-003            |
| `allow_override`        | Check    | 1                    | Allow validation override                        | JC-003            |
| `allow_override_role`   | Link     | Manufacturing Manager| Role allowed to override validations             | SEC-004           |

**Options for `validation_level`:**
- `Warning` - Show warnings but allow override
- `Error` - Block operations on validation failure

---

## Dependency Settings

| Field Name              | Type     | Default              | Description                                      | Business Rule     |
|-------------------------|----------|----------------------|--------------------------------------------------|-------------------|
| `check_previous_op`     | Check    | 1                    | Check previous operation completion              | DV-001            |
| `check_sequence`        | Check    | 1                    | Check operation sequence                         | DV-002            |
| `auto_refresh_deps`     | Check    | 1                    | Auto-refresh dependencies on JC completion       | JC-004            |
| `refresh_mode`          | Select   | Immediate            | Refresh mode: Immediate, Scheduled, Manual       | JC-004            |

**Options for `refresh_mode`:**
- `Immediate` - Refresh immediately on event
- `Scheduled` - Refresh on scheduled interval
- `Manual` - Manual refresh only

---

## Diagnostics Settings

| Field Name              | Type     | Default              | Description                                      | Business Rule     |
|-------------------------|----------|----------------------|--------------------------------------------------|-------------------|
| `enable_diagnostics`    | Check    | 1                    | Enable diagnostic messages                       | DM-001            |
| `show_detailed_errors`  | Check    | 0                    | Show detailed error messages                     | DM-003            |
| `log_level`             | Select   | INFO                 | Logging level: DEBUG, INFO, WARNING, ERROR       | LOG-001           |
| `retention_days`        | Int      | 90                   | Days to retain logs                              | LOG-002           |

**Options for `log_level`:**
- `DEBUG` - All logs
- `INFO` (default) - Informational logs
- `WARNING` - Warnings and errors
- `ERROR` - Errors only

---

## Notification Settings

| Field Name              | Type     | Default              | Description                                      | Used By           |
|-------------------------|----------|----------------------|--------------------------------------------------|-------------------|
| `enable_notifications`  | Check    | 1                    | Enable system notifications                      | Event Flow        |
| `email_notifications`   | Check    | 1                    | Enable email notifications                       | Event Flow        |
| `notify_material_ready` | Check    | 1                    | Notify when materials ready                      | MR-010            |
| `notify_dependency_resolved` | Check | 1                 | Notify when dependency resolved                  | DV-001            |
| `notify_exception`      | Select   | High and Above       | Exception notification: All, High and Above, Critical Only | EX-* |

**Options for `notify_exception`:**
- `All` - All exceptions
- `High and Above` - High, Critical only
- `Critical Only` - Critical exceptions only

---

## Security Settings

| Field Name              | Type     | Default              | Description                                      | Business Rule     |
|-------------------------|----------|----------------------|--------------------------------------------------|-------------------|
| `enable_permissions`    | Check    | 1                    | Enable permission checking                       | SEC-001           |
| `department_scope`      | Check    | 1                    | Enable department-level data scope               | SEC-002           |
| `log_all_actions`       | Check    | 1                    | Log all user actions                             | SEC-005           |
| `session_timeout`       | Int      | 3600                 | Session timeout in seconds                       | SEC-003           |

---

## Warehouse Settings

| Field Name              | Type     | Default              | Description                                      | Business Rule     |
|-------------------------|----------|----------------------|--------------------------------------------------|-------------------|
| `default_wip_group`     | Data     | Work In Progress Stores | Default WIP warehouse group                    | WH-001            |
| `auto_create_warehouses`| Check    | 0                    | Auto-create department warehouses                | WH-002            |
| `warehouse_naming`      | Select   | WIP-{Department}     | Warehouse naming convention                      | WH-002            |

**Options for `warehouse_naming`:**
- `WIP-{Department}` (default) - e.g., WIP-CNC
- `{Department}-WIP` - e.g., CNC-WIP
- `Custom` - Use custom naming

---

## Scheduled Jobs Settings

| Field Name              | Type     | Default              | Description                                      | Frequency         |
|-------------------------|----------|----------------------|--------------------------------------------------|-------------------|
| `daily_material_refresh`| Check    | 1                    | Run daily material refresh                       | Daily 00:00       |
| `hourly_dependency_check` | Check  | 1                    | Run hourly dependency check                      | Hourly            |
| `exception_cleanup`     | Check    | 1                    | Clean up old exceptions                          | Daily 01:00       |
| `performance_monitoring`| Check    | 0                    | Enable performance monitoring                    | Every 5 minutes   |

---

## Accessing Configuration

### Correct Usage

```python
# Get MES Settings
mes_settings = frappe.get_doc("MES Settings", "MES Settings")

# Access configuration
allow_partial = mes_settings.allow_partial_transfer
strict_mode = mes_settings.enable_strict_validation
log_level = mes_settings.log_level

# Use in logic
if mes_settings.auto_complete_wo:
    self.complete_work_order(work_order)
```

### Incorrect Usage (DO NOT DO THIS)

```python
# ❌ Hard-coded values
if quantity >= 100:  # Don't hard-code thresholds
    frappe.throw("Quantity too low")

# ❌ Direct database queries for settings
allow_partial = frappe.db.get_single_value("MES Settings", "allow_partial_transfer")

# ❌ Magic strings
if mode == "Department Warehouse":  # Don't hard-code option values
    ...
```

---

## Configuration Constants

Define these in `tekson_manufacturing/constants.py`:

```python
# Material Check Modes
MATERIAL_CHECK_DEPARTMENT = "Department Warehouse"
MATERIAL_CHECK_BOM = "BOM"

# Validation Levels
VALIDATION_WARNING = "Warning"
VALIDATION_ERROR = "Error"

# Refresh Modes
REFRESH_IMMEDIATE = "Immediate"
REFRESH_SCHEDULED = "Scheduled"
REFRESH_MANUAL = "Manual"

# Log Levels
LOG_DEBUG = "DEBUG"
LOG_INFO = "INFO"
LOG_WARNING = "WARNING"
LOG_ERROR = "ERROR"

# Notification Levels
NOTIFY_ALL = "All"
NOTIFY_HIGH_AND_ABOVE = "High and Above"
NOTIFY_CRITICAL_ONLY = "Critical Only"

# Warehouse Naming
WAREHOUSE_NAMING_WIP_PREFIX = "WIP-{Department}"
WAREHOUSE_NAMING_DEPT_PREFIX = "{Department}-WIP"
WAREHOUSE_NAMING_CUSTOM = "Custom"
```

---

## Environment Variables

Some settings can be overridden via environment variables (for deployment flexibility):

| Environment Variable         | Setting              | Priority |
|------------------------------|----------------------|----------|
| `MES_ENABLE_MES`             | enable_mes           | High     |
| `MES_LOG_LEVEL`              | log_level            | High     |
| `MES_STRICT_MODE`            | enable_strict_validation | High  |
| `MES_AUTO_COMPLETE_WO`       | auto_complete_wo     | High     |
| `MES_SESSION_TIMEOUT`        | session_timeout      | High     |

**Usage:**

```python
import os
from frappe import get_conf

conf = get_conf()

# Environment variable takes priority
log_level = os.environ.get('MES_LOG_LEVEL') or mes_settings.log_level
```

---

## Default Configuration File

For development/testing, provide a default configuration:

```json
{
    "mes_settings": {
        "enable_mes": 1,
        "allow_partial_transfer": 1,
        "material_check_mode": "Department Warehouse",
        "auto_refresh_on_se": 1,
        "strict_sequence": 1,
        "auto_complete_wo": 1,
        "enable_strict_validation": 0,
        "validation_level": "Warning",
        "allow_override": 1,
        "allow_override_role": "Manufacturing Manager",
        "log_level": "INFO",
        "enable_notifications": 1,
        "enable_permissions": 1,
        "department_scope": 1
    }
}
```

---

## Configuration Change Process

1. **Request Change:** Submit change request with justification
2. **Review:** Technical Lead reviews impact
3. **Update:** Add field to MES Settings DocType
4. **Document:** Update this Configuration Matrix
5. **Test:** Verify in development environment
6. **Deploy:** Migrate to production
7. **Communicate:** Notify users of configuration change

---

## Revision History

| Version | Date       | Author      | Changes                          |
|---------|------------|-------------|----------------------------------|
| 1.0     | 2026-07-31 | Development | Initial creation                 |

---

## Related Documents

- MES_DATA_DICTIONARY.md - Field definitions
- MES_LOGGING_STANDARD.md - Logging configuration
- MES_BUSINESS_RULES.md - Business rule references
