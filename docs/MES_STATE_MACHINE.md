# MES State Machine Definition

**Document Type:** Technical Specification  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Frozen for Implementation  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document defines all valid state transitions in the MES system. State changes must follow these transitions. Invalid transitions must be rejected with appropriate error messages.

---

## Job Card State Machine

### States

| State Code | Display Name           | Description                              |
|------------|------------------------|------------------------------------------|
| `DRAFT`    | Draft                  | Job Card created but not submitted       |
| `READY`    | Ready to Start         | All dependencies met, can start          |
| `WIP`      | Work In Progress       | Operation in progress                    |
| `COMPLETED`| Completed              | Operation completed                      |
| `BLOCKED`  | Blocked                | Blocked due to exception                 |
| `CANCELLED`| Cancelled              | Cancelled                                |

### State Transitions

```
┌─────────┐
│  DRAFT  │
└────┬────┘
     │
     │ submit()
     ▼
┌─────────────────┐
│  READY          │◄───────────────┐
└────┬────────────┘                │
     │                             │
     │ start()                     │ refresh()
     ▼                             │
┌─────────────────┐                │
│  WIP            │────────────────┘
└────┬────────────┘
     │
     │ complete()
     ▼
┌─────────────────┐
│  COMPLETED      │
└────┬────────────┘
     │
     │ (No backward transitions allowed)
     │
     ▼
┌─────────────────┐
│  CANCELLED      │ (Only via Work Order cancellation)
└─────────────────┘
```

### Transition Rules

| From      | To        | Allowed | Method        | Validation                          |
|-----------|-----------|---------|---------------|-------------------------------------|
| DRAFT     | READY     | ✅      | submit()      | Standard ERPNext validation         |
| DRAFT     | WIP       | ❌      | -             | Must submit first                   |
| DRAFT     | COMPLETED | ❌      | -             | Must submit and start first         |
| READY     | WIP       | ✅      | start()       | DV-001, MR-010, SEC-001            |
| READY     | COMPLETED | ❌      | -             | Must start first                    |
| READY     | READY     | ✅      | refresh()     | Status refresh                      |
| WIP       | WIP       | ✅      | refresh()     | Status refresh                      |
| WIP       | COMPLETED | ✅      | complete()    | JC-002, quantity validation         |
| WIP       | READY     | ❌      | -             | Cannot go backward                  |
| COMPLETED | WIP       | ❌      | -             | Cannot go backward                  |
| COMPLETED | READY     | ❌      | -             | Cannot go backward                  |
| ANY       | CANCELLED | ⚠️     | cancel()      | Only via Work Order cancellation    |

### State Change Triggers

| Trigger                          | From    | To        | Handler                              |
|----------------------------------|---------|-----------|--------------------------------------|
| Job Card submitted               | DRAFT   | READY     | `on_submit` hook                     |
| Operator clicks Start            | READY   | WIP       | `before_save` validation             |
| Operator clicks Complete         | WIP     | COMPLETED | `on_submit` validation               |
| Previous JC completed            | READY   | READY     | `refresh_status()`                   |
| Material transferred             | READY   | READY     | `refresh_material_status()`          |
| Exception raised                 | READY   | BLOCKED   | `handle_exception()`                 |
| Exception resolved               | BLOCKED | READY     | `resolve_exception()`                |

---

## Work Order State Machine

### States

| State Code   | Display Name     | Description                          |
|--------------|------------------|--------------------------------------|
| `DRAFT`      | Draft            | Work Order created but not submitted |
| `SUBMITTED`  | Submitted        | Work Order submitted                 |
| `IN PROCESS` | In Process       | Production in progress               |
| `COMPLETED`  | Completed        | All operations completed             |
| `CANCELLED`  | Cancelled        | Cancelled                            |
| `STOPPED`    | Stopped          | Temporarily stopped                  |

### State Transitions

```
┌─────────┐
│  DRAFT  │
└────┬────┘
     │
     │ submit()
     ▼
┌─────────────────┐
│  SUBMITTED      │
└────┬────────────┘
     │
     │ First JC starts
     ▼
┌─────────────────┐
│  IN PROCESS     │
└────┬────────────┘
     │
     │ All JC completed
     ▼
┌─────────────────┐
│  COMPLETED      │
└────┬────────────┘
     │
     │ (No backward transitions allowed)
```

### Transition Rules

| From      | To         | Allowed | Method           | Validation                       |
|-----------|------------|---------|------------------|----------------------------------|
| DRAFT     | SUBMITTED  | ✅      | submit()         | BOM validation                   |
| DRAFT     | IN PROCESS | ❌      | -                | Must submit first                |
| SUBMITTED | IN PROCESS | ✅      | Auto (JC start)  | First Job Card starts            |
| SUBMITTED | COMPLETED  | ❌      | -                | Must be in process first         |
| IN PROCESS| IN PROCESS | ✅      | refresh()        | Progress update                  |
| IN PROCESS| COMPLETED  | ✅      | auto_complete()  | WO-001, all JC completed         |
| IN PROCESS| SUBMITTED  | ❌      | -                | Cannot go backward               |
| COMPLETED | IN PROCESS | ❌      | -                | Cannot go backward               |
| ANY       | CANCELLED  | ✅      | cancel()         | Standard ERPNext cancellation    |
| ANY       | STOPPED    | ⚠️     | stop_production()| Manager approval                 |
| STOPPED   | IN PROCESS | ✅      | resume_production()| Manager approval               |

---

## Material Readiness State Machine

### States

| State Code      | Display Name      | Description                        |
|-----------------|-------------------|------------------------------------|
| `NOT_CHECKED`   | Not Checked       | Material readiness not evaluated   |
| `NOT_READY`     | Not Ready         | Materials not available            |
| `PARTIAL`       | Partially Ready   | Some materials available           |
| `READY`         | Ready             | All materials available            |

### State Transitions

```
┌─────────────┐
│  NOT_CHECKED│
└──────┬──────┘
       │
       │ evaluate()
       ▼
┌─────────────┐      ┌─────────────┐
│  NOT_READY  │◄────►│   PARTIAL   │
└──────┬──────┘      └──────┬──────┘
       │                    │
       │                    │
       └─────────┬──────────┘
                 │
                 │ All materials transferred
                 ▼
           ┌─────────────┐
           │    READY    │
           └─────────────┘
```

### Transition Rules

| From       | To        | Allowed | Trigger                        | Validation        |
|------------|-----------|---------|--------------------------------|-------------------|
| NOT_CHECKED| NOT_READY | ✅      | evaluate_material_readiness()  | MR-010            |
| NOT_CHECKED| PARTIAL   | ✅      | evaluate_material_readiness()  | MR-010            |
| NOT_CHECKED| READY     | ✅      | evaluate_material_readiness()  | MR-010            |
| NOT_READY  | PARTIAL   | ✅      | Material transfer              | MR-011            |
| NOT_READY  | READY     | ✅      | Material transfer              | MR-010, MR-011    |
| PARTIAL    | NOT_READY | ❌      | -                              | Cannot go backward|
| PARTIAL    | READY     | ✅      | Material transfer              | MR-010, MR-011    |
| READY      | PARTIAL   | ⚠️     | Material consumption/return    | Exception         |
| READY      | NOT_READY | ⚠️     | Material consumption/return    | Exception         |

---

## Dependency Validation State Machine

### States

| State Code      | Display Name      | Description                        |
|-----------------|-------------------|------------------------------------|
| `NOT_CHECKED`   | Not Checked       | Dependency not validated           |
| `PENDING`       | Pending           | Previous operation not complete    |
| `VALID`         | Valid             | All dependencies met               |
| `INVALID`       | Invalid           | Dependency validation failed       |

### State Transitions

```
┌─────────────┐
│  NOT_CHECKED│
└──────┬──────┘
       │
       │ validate()
       ▼
┌─────────────┐
│   PENDING   │
└──────┬──────┘
       │
       │ Previous operation completes
       ▼
┌─────────────┐
│    VALID    │
└─────────────┘
```

### Transition Rules

| From       | To        | Allowed | Trigger                    | Validation        |
|------------|-----------|---------|----------------------------|-------------------|
| NOT_CHECKED| PENDING   | ✅      | validate_dependencies()    | DV-001            |
| NOT_CHECKED| VALID     | ✅      | validate_dependencies()    | DV-001 (first op) |
| PENDING    | VALID     | ✅      | Previous JC completes      | DV-001            |
| PENDING    | INVALID   | ❌      | -                          | N/A               |
| VALID      | PENDING   | ❌      | -                          | Cannot go backward|

---

## Exception State Machine

### States

| State Code      | Display Name      | Description                        |
|-----------------|-------------------|------------------------------------|
| `OPEN`          | Open              | Exception raised                   |
| `IN_PROGRESS`   | In Progress       | Being resolved                     |
| `RESOLVED`      | Resolved          | Resolution applied                 |
| `CLOSED`        | Closed            | Exception closed                   |

### State Transitions

```
┌─────────┐
│   OPEN  │
└────┬────┘
     │
     │ acknowledge()
     ▼
┌─────────────┐
│ IN_PROGRESS │
└──────┬──────┘
       │
       │ resolve()
       ▼
┌─────────────┐
│  RESOLVED   │
└──────┬──────┘
       │
       │ verify()
       ▼
┌─────────┐
│  CLOSED │
└─────────┘
```

### Transition Rules

| From        | To          | Allowed | Trigger              | Validation            |
|-------------|-------------|---------|----------------------|-----------------------|
| OPEN        | IN_PROGRESS | ✅      | acknowledge()        | Assign resolver       |
| OPEN        | RESOLVED    | ⚠️     | quick_resolve()      | Auto-resolution       |
| IN_PROGRESS | RESOLVED    | ✅      | resolve()            | Apply resolution      |
| IN_PROGRESS | OPEN        | ✅      | reassign()           | Change resolver       |
| RESOLVED    | CLOSED      | ✅      | verify_and_close()   | Verification          |
| RESOLVED    | OPEN        | ✅      | reopen()             | Resolution failed     |
| CLOSED      | OPEN        | ❌      | -                    | Must create new       |

---

## Stock Entry State Machine (MES Context)

### States

| State Code   | Display Name     | Description                          |
|--------------|------------------|--------------------------------------|
| `DRAFT`      | Draft            | Stock Entry created                  |
| `SUBMITTED`  | Submitted        | Stock Entry submitted                |
| `CANCELLED`  | Cancelled        | Cancelled                            |

### MES-Specific Validation

| Purpose                       | From    | To        | Validation                      |
|-------------------------------|---------|-----------|---------------------------------|
| Material Transfer for Mfg     | DRAFT   | SUBMITTED | MR-010, warehouse validation    |
| Manufacture                   | DRAFT   | SUBMITTED | WO-001, all JC completed        |
| Material Return               | DRAFT   | SUBMITTED | Department validation           |

---

## State Change Logging

All state changes MUST be logged per MES_LOGGING_STANDARD.md:

```python
# Example: Job Card start
log_mes_event(
    module='EXECUTION',
    level='INFO',
    business_rule='JC-001',
    message=f"Job Card {jc.name} state changed: READY → WIP",
    context={
        'job_card': jc.name,
        'from_state': 'READY',
        'to_state': 'WIP',
        'user': frappe.session.user
    }
)
```

---

## State Validation Helper

```python
def validate_state_transition(doc, from_state, to_state):
    """
    Validate state transition is allowed
    
    Args:
        doc: Document (Job Card, Work Order, etc.)
        from_state: Current state
        to_state: Target state
    
    Raises:
        MESValidationError: If transition not allowed
    """
    # Define allowed transitions
    allowed_transitions = {
        'Job Card': {
            ('DRAFT', 'READY'): True,
            ('READY', 'WIP'): True,
            ('WIP', 'COMPLETED'): True,
            # ... etc
        },
        'Work Order': {
            # ... etc
        }
    }
    
    doctype = doc.doctype
    transition = (from_state, to_state)
    
    if doctype not in allowed_transitions:
        return True  # No validation for this DocType
    
    if not allowed_transitions[doctype].get(transition):
        from tekson_manufacturing.utils.exceptions import MESValidationError
        raise MESValidationError(
            f"Invalid state transition: {from_state} → {to_state} for {doctype}"
        )
```

---

## Revision History

| Version | Date       | Author      | Changes                          |
|---------|------------|-------------|----------------------------------|
| 1.0     | 2026-07-31 | Development | Initial creation                 |

---

## Related Documents

- MES_DATA_DICTIONARY.md - Status field definitions
- MES_EVENT_FLOW.md - State change triggers
- MES_BUSINESS_RULES.md - Business rules enforcing states
