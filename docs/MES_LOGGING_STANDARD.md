# MES Logging Standard

**Document Type:** Technical Specification  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Frozen for Implementation  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document defines the logging standard for the MES system. All modules MUST follow this standard for consistent, searchable, and actionable logs.

---

## Log Levels

| Level   | Code | Usage                                              | Example                                      |
|---------|------|----------------------------------------------------|----------------------------------------------|
| DEBUG   | 10   | Detailed technical information for debugging       | SQL query executed, variable values            |
| INFO    | 20   | Normal operational messages                        | Job Card started, Material transferred         |
| WARNING | 30   | Potential issues that don't block operations       | Partial transfer, Near-threshold values        |
| ERROR   | 40   | Errors that block operations                       | Validation failure, Permission denied          |
| CRITICAL| 50   | System-level failures requiring immediate action   | Database connection lost, Configuration missing|

---

## Log Format

### Standard Log Message Format

```
[MES] [{MODULE}] [{LEVEL}] [{BUSINESS_RULE}] {MESSAGE} | Context: {context}
```

**Components:**

| Component       | Description                          | Example              |
|-----------------|--------------------------------------|----------------------|
| `MES`           | System identifier                    | MES                  |
| `MODULE`        | Module name                          | MATERIAL, EXECUTION  |
| `LEVEL`         | Log level                            | INFO, ERROR          |
| `BUSINESS_RULE` | Business rule code (if applicable)   | MR-010, DV-001       |
| `MESSAGE`       | Human-readable message               | Material transferred |
| `CONTEXT`       | JSON with relevant document refs     | {"wo": "WO-001"}     |

---

## Log Categories

### 1. Execution Logs

**Module Code:** `EXECUTION`  
**Purpose:** Job Card and Work Order execution

```python
# Job Card Start
frappe.log_error(
    message=f"[MES] [EXECUTION] [INFO] [JC-001] Job Card {jc.name} started | Context: {context}",
    title=f"MES Job Card Start - {jc.name}"
)

# Job Card Completion
frappe.log_error(
    message=f"[MES] [EXECUTION] [INFO] [JC-002] Job Card {jc.name} completed {qty} units | Context: {context}",
    title=f"MES Job Card Complete - {jc.name}"
)

# Work Order Completion
frappe.log_error(
    message=f"[MES] [EXECUTION] [INFO] [WO-001] Work Order {wo.name} auto-completed | Context: {context}",
    title=f"MES Work Order Complete - {wo.name}"
)
```

### 2. Material Logs

**Module Code:** `MATERIAL`  
**Purpose:** Material readiness and transfers

```python
# Material Evaluation
frappe.log_error(
    message=f"[MES] [MATERIAL] [INFO] [MR-010] Material readiness evaluated for {wo.name}: {status} | Context: {context}",
    title=f"MES Material Readiness - {wo.name}"
)

# Material Transfer
frappe.log_error(
    message=f"[MES] [MATERIAL] [INFO] [MR-011] Cumulative transfer for {item}: {qty} kg | Context: {context}",
    title=f"MES Material Transfer - {item}"
)

# Material Shortage
frappe.log_error(
    message=f"[MES] [MATERIAL] [WARNING] [MR-010] Material shortage for {item}: {shortage} kg | Context: {context}",
    title=f"MES Material Shortage - {item}"
)
```

### 3. Dependency Logs

**Module Code:** `DEPENDENCY`  
**Purpose:** Operation dependency validation

```python
# Dependency Validation
frappe.log_error(
    message=f"[MES] [DEPENDENCY] [INFO] [DV-001] Previous operation validated for {jc.name}: {result} | Context: {context}",
    title=f"MES Dependency Check - {jc.name}"
)

# Sequence Validation
frappe.log_error(
    message=f"[MES] [DEPENDENCY] [INFO] [DV-002] Sequence validated for {wo.name}: {status} | Context: {context}",
    title=f"MES Sequence Check - {wo.name}"
)
```

### 4. Security Logs

**Module Code:** `SECURITY`  
**Purpose:** Permission and access control

```python
# Permission Check
frappe.log_error(
    message=f"[MES] [SECURITY] [INFO] [SEC-001] Permission checked for {user}: {action} on {doc} | Context: {context}",
    title=f"MES Permission Check - {user}"
)

# Permission Denied
frappe.log_error(
    message=f"[MES] [SECURITY] [ERROR] [SEC-001] Permission denied for {user}: {action} on {doc} | Context: {context}",
    title=f"MES Permission Denied - {user}"
)

# Department Scope Violation
frappe.log_error(
    message=f"[MES] [SECURITY] [WARNING] [SEC-002] Department scope violation: {user} tried to access {dept} | Context: {context}",
    title=f"MES Scope Violation - {user}"
)
```

### 5. Exception Logs

**Module Code:** `EXCEPTION`  
**Purpose:** Exception handling

```python
# Exception Raised
frappe.log_error(
    message=f"[MES] [EXCEPTION] [ERROR] [{exception_code}] {message} | Context: {context}",
    title=f"MES Exception - {exception_code}"
)

# Exception Resolved
frappe.log_error(
    message=f"[MES] [EXCEPTION] [INFO] [{exception_code}] Exception resolved by {user} | Context: {context}",
    title=f"MES Exception Resolved - {exception_code}"
)
```

### 6. Performance Logs

**Module Code:** `PERFORMANCE`  
**Purpose:** Performance monitoring

```python
# Execution Time
frappe.log_error(
    message=f"[MES] [PERFORMANCE] [DEBUG] Execution time for {function}: {time_ms}ms | Context: {context}",
    title=f"MES Performance - {function}"
)

# Query Performance
frappe.log_error(
    message=f"[MES] [PERFORMANCE] [DEBUG] Query time for {query_type}: {time_ms}ms | Context: {context}",
    title=f"MES Query Performance - {query_type}"
)
```

### 7. Diagnostic Logs

**Module Code:** `DIAGNOSTIC`  
**Purpose:** System diagnostics

```python
# Status Refresh
frappe.log_error(
    message=f"[MES] [DIAGNOSTIC] [INFO] Status refreshed for {doc_type} {doc_name} | Context: {context}",
    title=f"MES Status Refresh - {doc_name}"
)

# Configuration Change
frappe.log_error(
    message=f"[MES] [DIAGNOSTIC] [WARNING] Configuration changed: {setting} = {value} | Context: {context}",
    title=f"MES Configuration Change - {setting}"
)
```

---

## Logging Functions

### Standard Logging Function

```python
import frappe
import json
from datetime import datetime

def log_mes_event(module, level, business_rule, message, context=None):
    """
    Standard MES logging function
    
    Args:
        module: Module code (EXECUTION, MATERIAL, etc.)
        level: Log level (INFO, WARNING, ERROR, etc.)
        business_rule: Business rule code (MR-010, etc.)
        message: Human-readable message
        context: dict with relevant document references
    """
    if context is None:
        context = {}
    
    # Add standard context
    context['timestamp'] = datetime.now().isoformat()
    context['user'] = frappe.session.user
    
    # Format message
    formatted_message = f"[MES] [{module}] [{level}] [{business_rule}] {message} | Context: {json.dumps(context)}"
    
    # Get log level from settings
    mes_settings = frappe.get_doc("MES Settings", "MES Settings")
    configured_level = getattr(frappe.log, mes_settings.log_level.lower(), frappe.log.INFO)
    
    # Log if level is sufficient
    level_value = getattr(frappe.log, level.lower(), frappe.log.INFO)
    
    if level_value >= configured_level:
        frappe.log_error(
            message=formatted_message,
            title=f"MES {module} - {business_rule}"
        )
```

### Usage Examples

```python
# Example 1: Material readiness evaluation
context = {
    'work_order': work_order,
    'is_ready': result['is_ready'],
    'items_checked': len(result['transferred_items'])
}

log_mes_event(
    module='MATERIAL',
    level='INFO',
    business_rule='MR-010',
    message=f"Material readiness evaluated: {'Ready' if result['is_ready'] else 'Not Ready'}",
    context=context
)

# Example 2: Validation failure
context = {
    'job_card': job_card,
    'validation_type': 'dependency',
    'reason': result['reason']
}

log_mes_event(
    module='EXECUTION',
    level='ERROR',
    business_rule='DV-001',
    message=f"Job Card start blocked: {result['reason']}",
    context=context
)

# Example 3: Performance monitoring
import time
start_time = time.time()

# ... operation ...

execution_time = (time.time() - start_time) * 1000  # ms

context = {
    'function': 'evaluate_material_readiness',
    'work_order': work_order,
    'execution_time_ms': execution_time
}

log_mes_event(
    module='PERFORMANCE',
    level='DEBUG',
    business_rule='',
    message=f"Execution time: {execution_time:.2f}ms",
    context=context
)
```

---

## Context Standards

### Required Context Fields by Event

| Event Type              | Required Context Fields                        | Optional Fields              |
|-------------------------|------------------------------------------------|------------------------------|
| Job Card Start          | job_card, work_order, user                     | operation, department        |
| Job Card Complete       | job_card, work_order, quantity, user           | operation, time_taken        |
| Material Evaluation     | work_order, is_ready, items_count              | missing_items, department    |
| Material Transfer       | work_order, item_code, quantity, warehouse     | stock_entry, user            |
| Dependency Validation   | job_card, work_order, is_valid                 | previous_op, sequence_id     |
| Permission Check        | user, action, doc_type, doc_name               | role, department             |
| Exception               | exception_code, category, severity             | resolution, resolved_by      |

---

## Log Retention

| Log Level   | Retention Period | Archive Method          |
|-------------|------------------|-------------------------|
| DEBUG       | 7 days           | Auto-delete             |
| INFO        | 30 days          | Auto-delete             |
| WARNING     | 90 days          | Archive to file         |
| ERROR       | 1 year           | Archive to file         |
| CRITICAL    | 5 years          | Permanent archive       |

**Configuration:**

```python
# MES Settings
mes_settings.retention_days = 90  # Default for INFO and WARNING

# Scheduled job for cleanup
def cleanup_old_logs():
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() - timedelta(days=mes_settings.retention_days)
    
    # Delete old DEBUG and INFO logs
    frappe.db.sql("""
        DELETE FROM `tabError Log`
        WHERE creation < %s
        AND (error LIKE '%[DEBUG]%' OR error LIKE '%[INFO]%')
    """, (cutoff_date,))
```

---

## Log Search Patterns

### Searching by Module

```sql
SELECT * FROM `tabError Log`
WHERE error LIKE '%[MATERIAL]%'
ORDER BY creation DESC
LIMIT 100
```

### Searching by Business Rule

```sql
SELECT * FROM `tabError Log`
WHERE error LIKE '%[MR-010]%'
ORDER BY creation DESC
LIMIT 100
```

### Searching by Document

```sql
SELECT * FROM `tabError Log`
WHERE error LIKE '%WO-2026-001%'
ORDER BY creation DESC
```

### Searching by Time Range

```sql
SELECT * FROM `tabError Log`
WHERE creation BETWEEN '2026-07-01' AND '2026-07-31'
AND error LIKE '%[ERROR]%'
ORDER BY creation DESC
```

---

## Performance Considerations

### Do's

```python
# ✅ Log asynchronously for non-critical operations
frappe.enqueue(
    'tekson_manufacturing.utils.log_event',
    module='MATERIAL',
    level='INFO',
    business_rule='MR-010',
    message='Material evaluated',
    context=context
)

# ✅ Use appropriate log level
if result['is_ready']:
    log_mes_event('MATERIAL', 'INFO', 'MR-010', 'Material ready')
else:
    log_mes_event('MATERIAL', 'WARNING', 'MR-010', 'Material not ready')

# ✅ Include only necessary context
context = {'work_order': wo, 'is_ready': result['is_ready']}
```

### Don'ts

```python
# ❌ Don't log sensitive data
context = {'password': password, 'api_key': api_key}  # NEVER

# ❌ Don't log in tight loops
for item in items:  # Will create thousands of logs
    log_mes_event(...)

# ❌ Don't log without context
log_mes_event('MATERIAL', 'INFO', 'MR-010', 'Evaluated')  # Too vague

# ❌ Don't use ERROR level for normal operations
log_mes_event('MATERIAL', 'ERROR', 'MR-010', 'Material checked')  # Wrong level
```

---

## Testing Logs

```python
import unittest
from unittest.mock import patch

class TestLogging(unittest.TestCase):
    
    @patch('frappe.log_error')
    def test_material_readiness_logging(self, mock_log):
        """Test that material readiness is logged correctly"""
        from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
        
        engine = MaterialReadinessEngine(work_order="WO-2026-001")
        result = engine.evaluate_material_readiness()
        
        # Verify log was called
        self.assertTrue(mock_log.called)
        
        # Verify log format
        call_args = mock_log.call_args
        self.assertIn('[MES]', call_args[1]['message'])
        self.assertIn('[MATERIAL]', call_args[1]['message'])
        self.assertIn('[MR-010]', call_args[1]['message'])
```

---

## Revision History

| Version | Date       | Author      | Changes                          |
|---------|------------|-------------|----------------------------------|
| 1.0     | 2026-07-31 | Development | Initial creation                 |

---

## Related Documents

- MES_CONFIGURATION_MATRIX.md - Log level configuration
- MES_EVENT_FLOW.md - Event triggers for logging
- CODE_REVIEW_STANDARDS.md - Logging requirements
