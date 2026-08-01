# MES Security Matrix

**Document Type:** Security & Access Control Specification  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Ready for Review  
**Project:** Tekson Manufacturing MES  
**ERPNext Version:** V15

---

## Overview

This document defines role-based access control for the Tekson MES. Every user action must be validated against this security matrix.

All security implementations must enforce these permissions.

---

## User Roles

| Role Code | Role Name | Department |
|-----------|-----------|------------|
| PROD-PLNR | Production Planner | Planning |
| STORES-MGR | Stores Manager | Stores |
| STORES-OPR | Stores Operator | Stores |
| DEPT-SUPV | Department Supervisor | Production |
| SHOP-OPR | Shop Floor Operator | Production |
| QUAL-INSR | Quality Inspector | Quality |
| QUAL-MGR | Quality Manager | Quality |
| MFG-MGR | Manufacturing Manager | Manufacturing |
| SYS-ADMIN | System Administrator | IT |

---

## Permission Matrix

### Job Card Operations

| Permission | PROD-PLNR | STORES-MGR | STORES-OPR | DEPT-SUPV | SHOP-OPR | QUAL-INSR | QUAL-MGR | MFG-MGR | SYS-ADMIN |
|------------|-----------|------------|------------|-----------|----------|-----------|----------|---------|-----------|
| View All Job Cards | ✅ | ❌ | ❌ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ |
| View Department Job Cards | ✅ | ❌ | ❌ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| Start Job Card | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Complete Job Card | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Cancel Job Card | ⚠️ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Edit Job Card | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ⚠️ | ✅ |
| Override Validation | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Back-report Production | ❌ | ❌ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ✅ | ❌ |
| Approve Over Production | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Print Job Card | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |

**Legend:**
- ✅ = Full permission
- ⚠️ = Restricted permission (own department/data only)
- ❌ = No permission

---

### Work Order Operations

| Permission | PROD-PLNR | STORES-MGR | STORES-OPR | DEPT-SUPV | SHOP-OPR | QUAL-INSR | QUAL-MGR | MFG-MGR | SYS-ADMIN |
|------------|-----------|------------|------------|-----------|----------|-----------|----------|---------|-----------|
| Create Work Order | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ |
| Submit Work Order | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Cancel Work Order | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| View All Work Orders | ✅ | ⚠️ | ⚠️ | ⚠️ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| View Department WOs | ✅ | ❌ | ❌ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ |
| Complete Work Order | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Edit Work Order | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Print Work Order | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ |

---

### Material Transfer Operations

| Permission | PROD-PLNR | STORES-MGR | STORES-OPR | DEPT-SUPV | SHOP-OPR | QUAL-INSR | QUAL-MGR | MFG-MGR | SYS-ADMIN |
|------------|-----------|------------|------------|-----------|----------|-----------|----------|---------|-----------|
| Create Material Transfer | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ |
| Submit Material Transfer | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Cancel Material Transfer | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| View All Transfers | ✅ | ✅ | ✅ | ⚠️ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| View Department Transfers | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Transfer to Department | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Return Material to Stores | ❌ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ | ✅ | ❌ |

---

### Stock Entry Operations

| Permission | PROD-PLNR | STORES-MGR | STORES-OPR | DEPT-SUPV | SHOP-OPR | QUAL-INSR | QUAL-MGR | MFG-MGR | SYS-ADMIN |
|------------|-----------|------------|------------|-----------|----------|-----------|----------|---------|-----------|
| Create Manufacture Entry | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Submit Manufacture Entry | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Cancel Manufacture Entry | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| View All Stock Entries | ✅ | ✅ | ✅ | ⚠️ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| View Department Entries | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |

---

### Quality Operations

| Permission | PROD-PLNR | STORES-MGR | STORES-OPR | DEPT-SUPV | SHOP-OPR | QUAL-INSR | QUAL-MGR | MFG-MGR | SYS-ADMIN |
|------------|-----------|------------|------------|-----------|----------|-----------|----------|---------|-----------|
| Create Quality Inspection | ❌ | ❌ | ❌ | ⚠️ | ❌ | ✅ | ✅ | ⚠️ | ❌ |
| Submit Quality Inspection | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| Reject Production | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| Approve Rework | ❌ | ❌ | ❌ | ⚠️ | ❌ | ✅ | ✅ | ✅ | ❌ |
| Place on Quality Hold | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| Release from Hold | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Approve Concession | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |

---

### Master Data Operations

| Permission | PROD-PLNR | STORES-MGR | STORES-OPR | DEPT-SUPV | SHOP-OPR | QUAL-INSR | QUAL-MGR | MFG-MGR | SYS-ADMIN |
|------------|-----------|------------|------------|-----------|----------|-----------|----------|---------|-----------|
| Create BOM | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ |
| Edit BOM | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ |
| Create Routing | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ |
| Edit Routing | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ |
| Create Operation | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Create Workstation | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Edit Workstation | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Create Warehouse | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Edit Warehouse | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

---

### Exception Handling Operations

| Permission | PROD-PLNR | STORES-MGR | STORES-OPR | DEPT-SUPV | SHOP-OPR | QUAL-INSR | QUAL-MGR | MFG-MGR | SYS-ADMIN |
|------------|-----------|------------|------------|-----------|----------|-----------|----------|---------|-----------|
| Report Material Shortage | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Report Machine Breakdown | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Approve Alternate Workstation | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Approve Alternate Material | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ✅ | ✅ | ❌ |
| Approve Back-reporting | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Approve Over Production | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Approve Under Production | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Approve Job Card Cancel | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Approve Work Order Cancel | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Override System Validation | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

---

### Reporting & Analytics

| Permission | PROD-PLNR | STORES-MGR | STORES-OPR | DEPT-SUPV | SHOP-OPR | QUAL-INSR | QUAL-MGR | MFG-MGR | SYS-ADMIN |
|------------|-----------|------------|------------|-----------|----------|-----------|----------|---------|-----------|
| View Production Reports | ✅ | ❌ | ❌ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ |
| View Department Reports | ❌ | ❌ | ❌ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| View WIP Reports | ✅ | ⚠️ | ⚠️ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| View Quality Reports | ✅ | ❌ | ❌ | ⚠️ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Export Data | ✅ | ⚠️ | ❌ | ⚠️ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| View Dashboard | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Configure Dashboard | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

---

### System Administration

| Permission | PROD-PLNR | STORES-MGR | STORES-OPR | DEPT-SUPV | SHOP-OPR | QUAL-INSR | QUAL-MGR | MFG-MGR | SYS-ADMIN |
|------------|-----------|------------|------------|-----------|----------|-----------|----------|---------|-----------|
| Create User | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Edit User | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Delete User | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Assign Role | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| View Audit Log | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ✅ |
| Configure MES Settings | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| View System Logs | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Backup Data | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Restore Data | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Role Definitions

### Production Planner (PROD-PLNR)

**Responsibilities:**
- Create and review Production Plans
- Create and submit Work Orders
- Review routings and BOMs
- Monitor production progress
- Resolve material conflicts

**Access Scope:**
- All Work Orders and Job Cards
- Production reports and analytics
- Master data (BOM, Routing, Operations)

---

### Stores Manager (STORES-MGR)

**Responsibilities:**
- Manage material transfers
- Approve Stock Entries
- Monitor inventory levels
- Manage warehouse operations

**Access Scope:**
- Material Transfer creation and approval
- Stock Entry viewing (all)
- Warehouse management

---

### Stores Operator (STORES-OPR)

**Responsibilities:**
- Create Material Transfers
- Pick and issue materials
- Receive materials from suppliers
- Maintain warehouse organization

**Access Scope:**
- Material Transfer creation (limited)
- Stock viewing
- Basic warehouse operations

---

### Department Supervisor (DEPT-SUPV)

**Responsibilities:**
- Supervise department operations
- Approve Job Card starts/completions
- Handle exceptions in department
- Monitor department performance

**Access Scope:**
- Department Job Cards and Work Orders
- Exception approvals (department only)
- Department reports

---

### Shop Floor Operator (SHOP-OPR)

**Responsibilities:**
- Execute Job Cards
- Report production
- Report issues
- Maintain quality

**Access Scope:**
- Assigned Job Cards only
- Production reporting
- Basic viewing (own work)

---

### Quality Inspector (QUAL-INSR)

**Responsibilities:**
- Perform quality inspections
- Reject/approve production
- Place items on quality hold
- Document quality issues

**Access Scope:**
- Quality inspections
- Quality-related viewing
- Hold/release actions

---

### Quality Manager (QUAL-MGR)

**Responsibilities:**
- Manage quality operations
- Approve concessions
- Review quality reports
- Handle quality exceptions

**Access Scope:**
- All quality operations
- Quality reports and analytics
- Exception approvals

---

### Manufacturing Manager (MFG-MGR)

**Responsibilities:**
- Oversee all manufacturing operations
- Approve major exceptions
- Review all reports
- Configure MES settings

**Access Scope:**
- All manufacturing data
- All approvals
- System configuration

---

### System Administrator (SYS-ADMIN)

**Responsibilities:**
- Manage users and roles
- Maintain system health
- Handle technical issues
- Backup and restore

**Access Scope:**
- Full system access
- User management
- Technical configuration

---

## Department Restrictions

### Department-Based Access Control

Users can only access data for their assigned department unless explicitly granted cross-department access.

**Department Assignments:**
- W Department
- RA Department
- RP Department
- CNC Department
- Ralu Weld Department
- Ralu In Department
- Assembly Department
- Testing Department
- Painting Department

**Examples:**
- SHOP-OPR in CNC can only see CNC Job Cards
- DEPT-SUPV in W can only approve W Department exceptions
- QUAL-INSR may have cross-department access for quality functions

---

## Approval Hierarchies

### Level 1: Supervisor Approval

**Can Approve:**
- Job Card cancellation
- Back-reporting (within 24 hours)
- Over production (<10%)
- Under production (<10%)
- Department transfer

**Approvers:**
- DEPT-SUPV
- MFG-MGR

---

### Level 2: Manager Approval

**Can Approve:**
- Work Order cancellation
- Over production (>10%)
- Under production (>10%)
- Alternate material
- Concession
- Override validation

**Approvers:**
- MFG-MGR
- QUAL-MGR (for quality-related)

---

### Level 3: Engineering Approval

**Can Approve:**
- Alternate material (engineering impact)
- Process deviation
- BOM change

**Approvers:**
- Engineering Manager (not in MES roles - external approval)

---

## Implementation Rules

### Rule SEC-001: Permission Check

**Every user action MUST check permissions before execution.**

```python
def start_job_card(job_card, user):
    if not user.has_permission("start_job_card", job_card):
        frappe.throw("Insufficient permissions")
```

---

### Rule SEC-002: Department Scope

**Users with department-restricted permissions can only access their department's data.**

```python
def get_job_cards(user):
    if user.restricted_to_department:
        return get_job_cards_for_department(user.department)
    else:
        return get_all_job_cards()
```

---

### Rule SEC-003: Approval Trail

**Every approval MUST be logged with:**
- Approver name
- Timestamp
- Action approved
- Comments (if any)

---

### Rule SEC-004: Override Logging

**Every override of system validation MUST be logged with:**
- User who overrode
- Reason for override
- Timestamp
- Impact assessment

---

### Rule SEC-005: Segregation of Duties

**Critical functions require segregation:**
- Person who creates Material Transfer ≠ Person who approves it
- Person who reports production ≠ Person who approves it
- Person who creates User ≠ Person who uses it

---

## Audit Requirements

### Audit Log

Every action must be logged with:
- User
- Timestamp
- Action performed
- Document affected
- IP address
- Success/Failure

### Audit Reports

Available to:
- MFG-MGR (manufacturing actions)
- QUAL-MGR (quality actions)
- SYS-ADMIN (all actions)

### Audit Retention

- Operational logs: 1 year
- Security logs: 3 years
- Approval logs: 5 years

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-31 | OSDuo Tech LLP | Initial security matrix specification |

**Approved By:** ___________________  
**Date:** ___________________

**Next Review:** After first UAT cycle

---

*This document is maintained in the repository and updated as roles and permissions evolve.*
