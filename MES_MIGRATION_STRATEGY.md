# MES Migration Strategy

**Document Type:** Implementation Guide  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Frozen for Implementation  
**Project:** Tekson Manufacturing MES  
**Target ERPNext Version:** V15

---

## Overview

This document defines the migration strategy for deploying MES to ERPNext V15. Includes custom fields, DocTypes, roles, patches, and deployment order.

---

## Migration Phases

```
Phase 1: Foundation
├── Custom Fields
├── Custom DocTypes
└── Roles & Permissions

Phase 2: Configuration
├── MES Settings
├── Property Setters
└── Workspaces

Phase 3: Data Migration
├── Master Data Validation
├── Test Data Setup
└── Fixtures

Phase 4: Deployment
├── Patches
├── Hooks Registration
└── System Validation

Phase 5: Go-Live
├── User Training
├── Production Deployment
└── Monitoring
```

---

## Phase 1: Foundation

### Custom Fields

Create via `fixtures` in `hooks.py`:

```python
fixtures = [
    # Job Card Fields
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_start_status",
        "dt": "Job Card",
        "fieldname": "custom_start_status",
        "label": "MES Start Status",
        "fieldtype": "Select",
        "options": "\nNot Ready\nReady to Start\nIn Progress\nCompleted\nAwaiting Previous Operation\nAwaiting Materials\nBlocked",
        "insert_after": "status",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_can_start",
        "dt": "Job Card",
        "fieldname": "custom_can_start",
        "label": "Can Start",
        "fieldtype": "Check",
        "insert_after": "custom_start_status",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_material_status",
        "dt": "Job Card",
        "fieldname": "custom_material_status",
        "label": "Material Status",
        "fieldtype": "Select",
        "options": "\nNot Checked\nReady\nNot Ready\nPartially Ready",
        "insert_after": "custom_can_start",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_material_status_details",
        "dt": "Job Card",
        "fieldname": "custom_material_status_details",
        "label": "Material Status Details",
        "fieldtype": "Small Text",
        "insert_after": "custom_material_status",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_dependency_status",
        "dt": "Job Card",
        "fieldname": "custom_dependency_status",
        "label": "Dependency Status",
        "fieldtype": "Select",
        "options": "\nNot Checked\nValid\nInvalid\nPending",
        "insert_after": "custom_material_status_details",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_dependency_message",
        "dt": "Job Card",
        "fieldname": "custom_dependency_message",
        "label": "Dependency Message",
        "fieldtype": "Small Text",
        "insert_after": "custom_dependency_status",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_previous_operation",
        "dt": "Job Card",
        "fieldname": "custom_previous_operation",
        "label": "Previous Operation",
        "fieldtype": "Link",
        "options": "Job Card",
        "insert_after": "custom_dependency_message",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_next_operation",
        "dt": "Job Card",
        "fieldname": "custom_next_operation",
        "label": "Next Operation",
        "fieldtype": "Link",
        "options": "Job Card",
        "insert_after": "custom_previous_operation",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_department",
        "dt": "Job Card",
        "fieldname": "custom_department",
        "label": "Department",
        "fieldtype": "Link",
        "options": "Department",
        "insert_after": "custom_next_operation",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_plant_floor",
        "dt": "Job Card",
        "fieldname": "custom_plant_floor",
        "label": "Plant Floor",
        "fieldtype": "Link",
        "options": "Plant Floor",
        "insert_after": "custom_department",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_exception_code",
        "dt": "Job Card",
        "fieldname": "custom_exception_code",
        "label": "Exception Code",
        "fieldtype": "Data",
        "insert_after": "custom_plant_floor",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_exception_message",
        "dt": "Job Card",
        "fieldname": "custom_exception_message",
        "label": "Exception Message",
        "fieldtype": "Small Text",
        "insert_after": "custom_exception_code",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_last_refreshed",
        "dt": "Job Card",
        "fieldname": "custom_last_refreshed",
        "label": "Last Refreshed",
        "fieldtype": "Datetime",
        "insert_after": "custom_exception_message",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Job Card-custom_refreshed_by",
        "dt": "Job Card",
        "fieldname": "custom_refreshed_by",
        "label": "Refreshed By",
        "fieldtype": "Data",
        "insert_after": "custom_last_refreshed",
        "read_only": 1
    },
    
    # Work Order Fields
    {
        "doctype": "Custom Field",
        "name": "Work Order-custom_department",
        "dt": "Work Order",
        "fieldname": "custom_department",
        "label": "Department",
        "fieldtype": "Link",
        "options": "Department",
        "insert_after": "status"
    },
    {
        "doctype": "Custom Field",
        "name": "Work Order-custom_plant_floor",
        "dt": "Work Order",
        "fieldname": "custom_plant_floor",
        "label": "Plant Floor",
        "fieldtype": "Link",
        "options": "Plant Floor",
        "insert_after": "custom_department"
    },
    {
        "doctype": "Custom Field",
        "name": "Work Order-custom_material_readiness",
        "dt": "Work Order",
        "fieldname": "custom_material_readiness",
        "label": "Material Readiness",
        "fieldtype": "Select",
        "options": "\nNot Checked\nReady\nNot Ready\nPartially Ready",
        "insert_after": "custom_plant_floor",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Work Order-custom_transfer_completeness",
        "dt": "Work Order",
        "fieldname": "custom_transfer_completeness",
        "label": "Transfer Completeness",
        "fieldtype": "Percent",
        "insert_after": "custom_material_readiness",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Work Order-custom_dependency_status",
        "dt": "Work Order",
        "fieldname": "custom_dependency_status",
        "label": "Dependency Status",
        "fieldtype": "Select",
        "options": "\nNot Checked\nValid\nInvalid\nPending",
        "insert_after": "custom_transfer_completeness",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Work Order-custom_exception_count",
        "dt": "Work Order",
        "fieldname": "custom_exception_count",
        "label": "Exception Count",
        "fieldtype": "Int",
        "insert_after": "custom_dependency_status",
        "read_only": 1
    },
    {
        "doctype": "Custom Field",
        "name": "Work Order-custom_last_validated",
        "dt": "Work Order",
        "fieldname": "custom_last_validated",
        "label": "Last Validated",
        "fieldtype": "Datetime",
        "insert_after": "custom_exception_count",
        "read_only": 1
    },
    
    # Warehouse Fields
    {
        "doctype": "Custom Field",
        "name": "Warehouse-custom_plant_floor",
        "dt": "Warehouse",
        "fieldname": "custom_plant_floor",
        "label": "Plant Floor",
        "fieldtype": "Link",
        "options": "Plant Floor",
        "insert_after": "warehouse_group"
    },
    {
        "doctype": "Custom Field",
        "name": "Warehouse-custom_department",
        "dt": "Warehouse",
        "fieldname": "custom_department",
        "label": "Department",
        "fieldtype": "Link",
        "options": "Department",
        "insert_after": "custom_plant_floor"
    },
    {
        "doctype": "Custom Field",
        "name": "Warehouse-custom_warehouse_type",
        "dt": "Warehouse",
        "fieldname": "custom_warehouse_type",
        "label": "Warehouse Type",
        "fieldtype": "Select",
        "options": "\nWIP\nRaw Material\nBOF\nFinished Goods\nScrap\nRejected",
        "insert_after": "custom_department"
    },
    
    # Stock Entry Fields
    {
        "doctype": "Custom Field",
        "name": "Stock Entry-custom_department",
        "dt": "Stock Entry",
        "fieldname": "custom_department",
        "label": "Department",
        "fieldtype": "Link",
        "options": "Department",
        "insert_after": "purpose"
    },
    {
        "doctype": "Custom Field",
        "name": "Stock Entry-custom_plant_floor",
        "dt": "Stock Entry",
        "fieldname": "custom_plant_floor",
        "label": "Plant Floor",
        "fieldtype": "Link",
        "options": "Plant Floor",
        "insert_after": "custom_department"
    },
    {
        "doctype": "Custom Field",
        "name": "Stock Entry-custom_transfer_stage",
        "dt": "Stock Entry",
        "fieldname": "custom_transfer_stage",
        "label": "Transfer Stage",
        "fieldtype": "Select",
        "options": "\nPartial\nComplete\nFirst Transfer\nFinal Transfer",
        "insert_after": "custom_plant_floor"
    },
    {
        "doctype": "Custom Field",
        "name": "Stock Entry-custom_cumulative_qty",
        "dt": "Stock Entry",
        "fieldname": "custom_cumulative_qty",
        "label": "Cumulative Quantity",
        "fieldtype": "Float",
        "insert_after": "custom_transfer_stage",
        "read_only": 1
    }
]
```

---

### Custom DocTypes

#### 1. MES Settings

```json
{
    "doctype": "DocType",
    "name": "MES Settings",
    "module": "Tekson Manufacturing",
    "custom": 0,
    "is_single": 1,
    "fields": [
        {
            "fieldname": "enable_mes",
            "label": "Enable MES",
            "fieldtype": "Check",
            "default": "1"
        },
        {
            "fieldname": "allow_partial_transfer",
            "label": "Allow Partial Transfer",
            "fieldtype": "Check",
            "default": "1"
        },
        {
            "fieldname": "material_check_mode",
            "label": "Material Check Mode",
            "fieldtype": "Select",
            "options": "Department Warehouse\nBOM",
            "default": "Department Warehouse"
        },
        {
            "fieldname": "auto_complete_wo",
            "label": "Auto Complete Work Order",
            "fieldtype": "Check",
            "default": "1"
        },
        {
            "fieldname": "enable_strict_validation",
            "label": "Enable Strict Validation",
            "fieldtype": "Check",
            "default": "0"
        },
        {
            "fieldname": "log_level",
            "label": "Log Level",
            "fieldtype": "Select",
            "options": "DEBUG\nINFO\nWARNING\nERROR",
            "default": "INFO"
        }
    ]
}
```

#### 2. MES Exception Log

```json
{
    "doctype": "DocType",
    "name": "MES Exception Log",
    "module": "Tekson Manufacturing",
    "custom": 0,
    "is_single": 0,
    "fields": [
        {
            "fieldname": "exception_code",
            "label": "Exception Code",
            "fieldtype": "Data",
            "in_list_view": 1
        },
        {
            "fieldname": "exception_category",
            "label": "Exception Category",
            "fieldtype": "Select",
            "options": "Material\nProduction\nEquipment\nQuality\nCancellation\nSystem",
            "in_list_view": 1
        },
        {
            "fieldname": "severity",
            "label": "Severity",
            "fieldtype": "Select",
            "options": "Low\nMedium\nHigh\nCritical",
            "in_list_view": 1
        },
        {
            "fieldname": "reference_doctype",
            "label": "Reference DocType",
            "fieldtype": "Link",
            "options": "DocType"
        },
        {
            "fieldname": "reference_docname",
            "label": "Reference DocName",
            "fieldtype": "Data"
        },
        {
            "fieldname": "message",
            "label": "Message",
            "fieldtype": "Small Text"
        },
        {
            "fieldname": "status",
            "label": "Status",
            "fieldtype": "Select",
            "options": "Open\nIn Progress\nResolved\nClosed",
            "default": "Open"
        }
    ]
}
```

---

### Roles

Create via `fixtures`:

```python
fixtures.extend([
    {"doctype": "Role", "role_name": "MES Operator"},
    {"doctype": "Role", "role_name": "MES Supervisor"},
    {"doctype": "Role", "role_name": "MES Planner"},
    {"doctype": "Role", "role_name": "Stores Keeper"},
    {"doctype": "Role", "role_name": "Department Manager"},
    {"doctype": "Role", "role_name": "MES Viewer"}
])
```

---

## Phase 2: Configuration

### Property Setters

```python
# Hide standard fields that are replaced by MES
property_setters = [
    {
        "doctype": "Property Setter",
        "doctype_or_field": "DocType",
        "doc_type": "Job Card",
        "property": "hide",
        "value": "0",  # Don't hide, but MES controls status
        "property_type": "Check"
    }
]
```

---

## Phase 3: Data Migration

### Master Data Validation

```python
# Patch: Validate Plant Floor configuration
def validate_plant_floor_configuration():
    """Ensure all departments have Plant Floor configured"""
    departments = frappe.get_all("Department", fields=["name"])
    
    for dept in departments:
        if not frappe.db.exists("Plant Floor", {"department": dept.name}):
            frappe.log_error(
                f"Plant Floor not configured for Department: {dept.name}",
                "MES Migration"
            )
```

---

## Phase 4: Deployment Patches

### Patch Order (patches.txt)

```
tekson_manufacturing.patches.v1.create_custom_fields
tekson_manufacturing.patches.v1.create_mes_settings
tekson_manufacturing.patches.v1.create_roles
tekson_manufacturing.patches.v1.setup_warehouse_mapping
tekson_manufacturing.patches.v1.configure_hooks
tekson_manufacturing.patches.v1.validate_master_data
tekson_manufacturing.patches.v1.create_test_data
```

---

## Phase 5: Go-Live

### Deployment Checklist

- [ ] All custom fields created
- [ ] All custom DocTypes created
- [ ] Roles and permissions configured
- [ ] MES Settings configured
- [ ] Warehouse mapping validated
- [ ] Test data loaded
- [ ] User training completed
- [ ] Production deployment successful
- [ ] Monitoring enabled

---

## Revision History

| Version | Date       | Author      | Changes                          |
|---------|------------|-------------|----------------------------------|
| 1.0     | 2026-07-31 | Development | Initial creation                 |

---

## Related Documents

- MES_DATA_DICTIONARY.md - Field definitions
- MES_CONFIGURATION_MATRIX.md - Configuration settings
- CODE_REVIEW_STANDARDS.md - Patch standards
