# MES Performance Budget

**Document Type:** Technical Specification  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Frozen for Implementation  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document defines performance targets for all MES operations. All implementations must meet these targets under normal load conditions.

---

## Performance Targets

### Job Card Operations

| Operation              | Target    | Maximum   | Measurement Point            |
|------------------------|-----------|-----------|------------------------------|
| Open Job Card          | < 1 sec   | 2 sec     | UI render complete           |
| Start Job Card         | < 2 sec   | 3 sec     | Validation + status update   |
| Complete Job Card      | < 2 sec   | 3 sec     | Validation + refresh         |
| Refresh Job Card Status| < 1 sec   | 2 sec     | Status fields updated        |
| Get Job Card Details   | < 0.5 sec | 1 sec     | API response time            |

### Work Order Operations

| Operation              | Target    | Maximum   | Measurement Point            |
|------------------------|-----------|-----------|------------------------------|
| Open Work Order        | < 1 sec   | 2 sec     | UI render complete           |
| Evaluate Material Readiness | < 3 sec | 5 sec  | Full evaluation complete     |
| Refresh Material Status| < 2 sec   | 3 sec     | Status fields updated        |
| Complete Work Order    | < 3 sec   | 5 sec     | Auto-completion + SE creation|
| Get Work Order Details | < 0.5 sec | 1 sec     | API response time            |

### Material Operations

| Operation              | Target    | Maximum   | Measurement Point            |
|------------------------|-----------|-----------|------------------------------|
| Get Stock Balance      | < 0.5 sec | 1 sec     | Query response time          |
| Get Cumulative Transfers | < 1 sec | 2 sec     | Query response time          |
| Create Material Transfer | < 2 sec | 3 sec     | SE creation + submit         |
| Get Transfer Suggestions | < 2 sec | 3 sec     | Full suggestion list         |

### Dependency Operations

| Operation              | Target    | Maximum   | Measurement Point            |
|------------------------|-----------|-----------|------------------------------|
| Validate Previous Operation | < 1 sec | 2 sec  | Validation complete          |
| Validate Sequence      | < 1 sec   | 2 sec     | Validation complete          |
| Get Sequence Details   | < 0.5 sec | 1 sec     | Query response time          |

### Exception Operations

| Operation              | Target    | Maximum   | Measurement Point            |
|------------------------|-----------|-----------|------------------------------|
| Create Exception Log   | < 0.5 sec | 1 sec     | Log entry created            |
| Send Notification      | < 1 sec   | 2 sec     | Notification sent (async)    |
| Resolve Exception      | < 1 sec   | 2 sec     | Status updated               |

---

## Load Conditions

### Normal Load

| Metric                  | Value     |
|-------------------------|-----------|
| Concurrent Users        | 50        |
| Job Cards per Work Order| 10        |
| Work Orders Active      | 100       |
| Stock Entries per Day   | 500       |
| Database Size           | 10 GB     |

### Peak Load

| Metric                  | Value     |
|-------------------------|-----------|
| Concurrent Users        | 200       |
| Job Cards per Work Order| 20        |
| Work Orders Active      | 500       |
| Stock Entries per Day   | 2000      |
| Database Size           | 50 GB     |

**Performance targets apply under Normal Load conditions.**

Under Peak Load, targets may increase by up to 50%.

---

## Performance Monitoring

### Logging Performance

```python
import time

def evaluate_material_readiness(self, work_order):
    start_time = time.time()
    
    # ... operation ...
    
    execution_time = (time.time() - start_time) * 1000  # ms
    
    # Log if exceeds threshold
    if execution_time > 3000:  # 3 seconds
        log_mes_event(
            module='PERFORMANCE',
            level='WARNING',
            business_rule='',
            message=f"Slow operation: {execution_time:.2f}ms (target: 3000ms)",
            context={
                'operation': 'evaluate_material_readiness',
                'work_order': work_order,
                'execution_time_ms': execution_time
            }
        )
```

### Performance Log Format

```
[MES] [PERFORMANCE] [WARNING] [] Slow operation: 3500.25ms (target: 3000ms) | Context: {"operation": "evaluate_material_readiness", "work_order": "WO-2026-001", "execution_time_ms": 3500.25}
```

---

## Performance Testing

### Unit Test Performance

```python
import unittest
import time

class TestPerformance(unittest.TestCase):
    
    def test_material_readiness_performance(self):
        """Test material readiness meets performance target"""
        from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
        
        start_time = time.time()
        
        engine = MaterialReadinessEngine(work_order="WO-2026-001")
        result = engine.evaluate_material_readiness()
        
        execution_time = (time.time() - start_time) * 1000
        
        # Target: < 3000ms
        self.assertLess(execution_time, 3000, 
            f"Material readiness took {execution_time:.2f}ms (target: 3000ms)")
    
    def test_job_card_start_performance(self):
        """Test Job Card start meets performance target"""
        from tekson_manufacturing.services.job_card_service import JobCardService
        
        start_time = time.time()
        
        service = JobCardService()
        result = service.can_start("JC-2026-001")
        
        execution_time = (time.time() - start_time) * 1000
        
        # Target: < 2000ms
        self.assertLess(execution_time, 2000,
            f"Job Card start took {execution_time:.2f}ms (target: 2000ms)")
```

### Load Testing

```python
# Load test script (to be implemented)
# Simulate 50 concurrent users performing operations
# Measure response times
# Verify all operations meet targets
```

---

## Optimization Guidelines

### Database Queries

**Do:**

```python
# ✅ Use indexed fields in filters
job_cards = frappe.get_all(
    "Job Card",
    filters={"work_order": work_order, "docstatus": 1},  # Indexed
    fields=["name", "sequence_id", "status"]
)

# ✅ Use specific fields
job_cards = frappe.get_all(
    "Job Card",
    filters={"work_order": work_order},
    fields=["name", "operation"]  # Only needed fields
)

# ✅ Use SQL for complex queries
result = frappe.db.sql("""
    SELECT SUM(qty)
    FROM `tabStock Entry Detail`
    WHERE item_code = %s
    AND work_order = %s
""", (item_code, work_order))
```

**Don't:**

```python
# ❌ N+1 queries
job_cards = frappe.get_all("Job Card", filters={"work_order": wo})
for jc in job_cards:
    jc_doc = frappe.get_doc("Job Card", jc.name)  # Separate query

# ❌ Select *
job_cards = frappe.get_all("Job Card", filters={"work_order": wo})

# ❌ Unindexed field filters
job_cards = frappe.get_all(
    "Job Card",
    filters={"custom_department": "CNC"}  # Not indexed
)
```

### Caching

```python
# Cache frequently accessed data
@frappe.cache()
def get_department_warehouse(plant_floor):
    return frappe.db.get_value(
        "Warehouse",
        {"custom_plant_floor": plant_floor},
        "name"
    )

# Cache invalidation
def invalidate_department_cache(plant_floor):
    frappe.cache().delete_key(f"department_warehouse:{plant_floor}")
```

### Async Operations

```python
# Use background jobs for non-critical operations
frappe.enqueue(
    'tekson_manufacturing.services.job_card_service.refresh_status',
    job_card=job_card,
    queue='default',
    timeout=300
)

# Use for notifications
frappe.enqueue(
    'tekson_manufacturing.utils.notify_stakeholders',
    event='material_ready',
    work_order=work_order,
    queue='short'
)
```

---

## Performance Budget by Sprint

| Sprint | Focus Area              | Performance Target               |
|--------|-------------------------|----------------------------------|
| 1      | Material Readiness      | MR-010/MR-011 < 3 sec            |
| 2      | Dependency Engine       | DV-001/DV-002 < 2 sec            |
| 3      | Execution Engine        | JC start/complete < 2 sec        |
| 4      | Diagnostics             | Message generation < 1 sec       |
| 5      | Department Transfer     | Transfer suggestion < 2 sec      |
| 6      | Exception Handling      | Exception logging < 0.5 sec      |
| 7      | Security                | Permission check < 0.5 sec       |
| 8-9    | UI                      | Page load < 1 sec                |
| 10     | Integration             | End-to-end < 5 sec               |

---

## Performance Regression

Any code change that increases operation time by more than 20% MUST be:

1. Documented with justification
2. Approved by Technical Lead
3. Added to performance test suite
4. Monitored in production

---

## Revision History

| Version | Date       | Author      | Changes                          |
|---------|------------|-------------|----------------------------------|
| 1.0     | 2026-07-31 | Development | Initial creation                 |

---

## Related Documents

- MES_LOGGING_STANDARD.md - Performance logging format
- CODE_REVIEW_STANDARDS.md - Performance review checklist
- MES_TEST_SCENARIOS.md - Performance test scenarios
