# Tekson Manufacturing MES - Documentation Index

**Document Type:** Navigation Guide  
**Version:** 2.0  
**Date:** 2026-08-02  
**Status:** ✅ **READY FOR TESTING**  
**Project:** Tekson Manufacturing MES  
**Phase:** Testing (UAT Preparation)

---

## Quick Start

**New to the project?** Start here:

1. **📊 PROJECT_STATUS_REPORT_Aug2_2026.md** (10 min) - Current project status
2. **BUSINESS_PROCESS_FREEZE_v1.0.md** (15 min) - Frozen business process
3. **01_PROJECT_OVERVIEW.md** (5 min) - Understand what we're building
4. **MES_ARCHITECTURE_IMPLEMENTATION.md** (15 min) - Understand the architecture
5. **MES_BUSINESS_RULES.md** (30 min) - 24 frozen business rules
6. **UAT/UAT_TEST_PLAN_FULL_CYCLE.md** (20 min) - UAT test scenarios
7. Start testing! 🚀

---

## 🔥 Latest Documents (Aug 2, 2026)

| Document | Purpose | Priority |
|----------|---------|----------|
| [PROJECT_STATUS_REPORT_Aug2_2026.md](PROJECT_STATUS_REPORT_Aug2_2026.md) | Current status report | 🔴 HIGH |
| [BUSINESS_PROCESS_FREEZE_v1.0.md](BUSINESS_PROCESS_FREEZE_v1.0.md) | Business process freeze | 🔴 HIGH |
| [ENHANCEMENT_BACKLOG_v1.0.md](ENHANCEMENT_BACKLOG_v1.0.md) | Deferred enhancements | 🔴 HIGH |
| [UAT/GAP_ANALYSIS_SERVER_SCRIPTS.md](../UAT/GAP_ANALYSIS_SERVER_SCRIPTS.md) | Server script comparison | 🟡 MEDIUM |
| [UAT/JOB_CARD_CUSTOM_FIELDS_IMPLEMENTATION.md](../UAT/JOB_CARD_CUSTOM_FIELDS_IMPLEMENTATION.md) | Custom fields guide | 🟡 MEDIUM |
| [UAT/SERVER_SCRIPT_RETIREMENT_MATRIX.md](../UAT/SERVER_SCRIPT_RETIREMENT_MATRIX.md) | Script retirement plan | 🟡 MEDIUM |
| [UAT/CUSTOM_FIELDS_CATEGORIZATION.md](../UAT/CUSTOM_FIELDS_CATEGORIZATION.md) | Field categorization | 🟡 MEDIUM |

---

## 1. Project Overview

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| [01_PROJECT_OVERVIEW.md](01_PROJECT_OVERVIEW.md) | Project introduction, scope, objectives | All | Frozen |
| [MES_PHASE_1_SCOPE.md](MES_PHASE_1_SCOPE.md) | Phase 1 detailed scope | All | Frozen |
| [MES_PROJECT_CONSTRAINTS.md](MES_PROJECT_CONSTRAINTS.md) | Project constraints and assumptions | All | Frozen |
| [PHASE1_STATUS_REPORT.md](PHASE1_STATUS_REPORT.md) | Current project status (living) | All | Living |

---

## 2. Business Requirements

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| [BUSINESS_RULES_SPECIFICATION.md](BUSINESS_RULES_SPECIFICATION.md) | 85 business rules (all sprints) | Business, Dev | Frozen |
| [MES_EXCEPTION_HANDLING.md](MES_EXCEPTION_HANDLING.md) | 46 exception scenarios | Dev, QA | Frozen |
| [MES_SECURITY_MATRIX.md](MES_SECURITY_MATRIX.md) | 10 roles, 75 permissions | Security, Dev | Frozen |
| [MES_WAREHOUSE_STRUCTURE.md](MES_WAREHOUSE_STRUCTURE.md) | Department warehouse model | All | Frozen |

---

## 3. Architecture & Design

### 3.1 Architecture

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| [MES_ARCHITECTURE_OVERVIEW.md](MES_ARCHITECTURE_OVERVIEW.md) | 5-layer architecture | Dev | Frozen |
| [MES_SERVICE_INTERFACES.md](MES_SERVICE_INTERFACES.md) | Service definitions | Dev | Frozen |
| [MES_DATA_MODEL.md](MES_DATA_MODEL.md) | Data model and relationships | Dev | Frozen |
| [MES_INTEGRATION_POINTS.md](MES_INTEGRATION_POINTS.md) | External system integration | Dev | Frozen |

### 3.2 Event Flow

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| [EVENT_REGISTRY.md](EVENT_REGISTRY.md) | ERP event handlers (22 events) | Dev | Frozen |
| [MES_STATE_MACHINE.md](MES_STATE_MACHINE.md) | Job Card, Work Order states | Dev | Frozen |

### 3.3 Repository Pattern

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| [REPOSITORY_COVERAGE_MATRIX.md](REPOSITORY_COVERAGE_MATRIX.md) | Repository-ERP mapping | Dev | Frozen |

---

## 4. Development Standards

### 4.1 Coding Standards

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| [PYTHON_CODING_STANDARDS.md](PYTHON_CODING_STANDARDS.md) | Python coding conventions | Dev | Frozen |
| [CODE_REVIEW_STANDARDS.md](CODE_REVIEW_STANDARDS.md) | Code review checklist | Dev | Frozen |
| [MES_LOGGING_STANDARD.md](MES_LOGGING_STANDARD.md) | Logging standards | Dev | Frozen |

### 4.2 Sprint Execution

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| [SPRINT_DEFINITION_OF_DONE.md](SPRINT_DEFINITION_OF_DONE.md) | Sprint completion criteria | Dev, QA | Frozen |
| [MES_IMPLEMENTATION_MATRIX.md](MES_IMPLEMENTATION_MATRIX.md) | Sprint tracking (living) | Dev, PM | Living |
| [CHANGELOG.md](CHANGELOG.md) | Version history (living) | All | Living |

### 4.3 Technical Debt & Limitations

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) | Technical debt tracking (living) | Dev | Living |
| [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) | System limitations (living) | Dev, QA | Living |

---

## 5. Testing

### 5.1 Test Planning

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| [MES_TEST_SCENARIOS.md](MES_TEST_SCENARIOS.md) | Test scenarios by sprint | QA | Frozen |
| [UAT_ACCEPTANCE_MATRIX.md](UAT_ACCEPTANCE_MATRIX.md) | UAT test cases (living) | Business, QA | Living |
| [MES_INTEGRATION_MATRIX.md](MES_INTEGRATION_MATRIX.md) | Integration tests (living) | Dev, QA | Living |

### 5.2 Release & Deployment

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) | Deployment checklist | Dev, Ops | Frozen |
| [MES_DEPLOYMENT_PROCEDURE.md](MES_DEPLOYMENT_PROCEDURE.md) | Deployment procedure | Ops | Frozen |
| [MES_ROLLBACK_PROCEDURE.md](MES_ROLLBACK_PROCEDURE.md) | Rollback procedure | Ops | Frozen |

---

## 6. Governance

### 6.1 Decision Making

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| [DECISION_LOG.md](DECISION_LOG.md) | Design decisions (11 decisions) | All | Controlled |
| [DOCUMENTATION_GOVERNANCE.md](DOCUMENTATION_GOVERNANCE.md) | Document lifecycle policy | All | Frozen |
| [VERSION_ROADMAP.md](VERSION_ROADMAP.md) | Version planning (Phase 1-3) | All | Frozen |

### 6.2 Risk & Change Management

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| [RISK_REGISTER.md](RISK_REGISTER.md) | 8 project risks (living) | PM, All | Living |
| [MES_CHANGE_MANAGEMENT.md](MES_CHANGE_MANAGEMENT.md) | Change request process | PM, All | Frozen |

---

## 7. Implementation Status

### Sprints Complete

| Sprint | Business Rules | Status | Version |
|--------|----------------|--------|---------|
| **Sprint 1** | MR-010, MR-011 | ✅ Complete | 1.0.1 |
| **Sprint 2** | DV-001, DV-002 | ✅ Complete | 1.0.2 |
| **Sprint 3** | JC-001 to JC-005, WO-001, WO-002 | ✅ Complete | 1.0.3 |

### Sprints Planned

| Sprint | Business Rules | Status | Version |
|--------|----------------|--------|---------|
| **Sprint 4** | DM-001 to DM-004 | 📋 Planned | 1.0.5 |
| **Sprint 5** | WH-001 to WH-005 | 📋 Planned | 1.0.6 |
| **Sprint 6** | 46 Exception Scenarios | 📋 Planned | 1.0.7 |
| **Sprint 7** | Security Framework | 📋 Planned | 1.0.8 |
| **Sprints 8-9** | MES User Interface | 📋 Planned | 1.0.9 |
| **Sprint 10** | Production Readiness | 📋 Planned | 1.0.10 |

### Overall Progress

| Metric | Status |
|--------|--------|
| Business Rules Implemented | 11 / 85 (13%) |
| Sprints Complete | 3 / 10 (30%) |
| Weighted Effort Complete | 35% |
| Documentation Complete | 100% |

---

## 8. Key Contracts (Frozen Interfaces)

### 8.1 Repository Interfaces

**DO NOT CHANGE without governance approval**

| Repository | File | Methods |
|------------|------|---------|
| JobCardRepository | `repositories/job_card_repository.py` | 8 methods |
| WorkOrderRepository | `repositories/work_order_repository.py` | 9 methods |
| StockRepository | `repositories/stock_repository.py` | 8 methods |
| WarehouseRepository | `repositories/warehouse_repository.py` | 8 methods |

### 8.2 Service Interfaces

**DO NOT CHANGE without governance approval**

| Service | File | Methods |
|---------|------|---------|
| JobCardService | `services/job_card_service.py` | 6 methods |
| WorkOrderService | `services/work_order_service.py` | 5 methods |
| StockService | `services/stock_service.py` | 5 methods |

### 8.3 Event Handlers

**DO NOT CHANGE without governance approval**

| Event Type | Count | File |
|------------|-------|------|
| Work Order Events | 7 | `hooks.py` |
| Job Card Events | 6 | `hooks.py` |
| Stock Entry Events | 5 | `hooks.py` |

---

## 9. File Structure

```
tekson_manufacturing/
├── docs/                              # All documentation (40 files)
│   ├── 00_PROJECT_INDEX.md           # This file
│   ├── 01_PROJECT_OVERVIEW.md        # Start here
│   ├── BUSINESS_RULES_SPECIFICATION.md
│   ├── MES_ARCHITECTURE_OVERVIEW.md
│   ├── PYTHON_CODING_STANDARDS.md
│   ├── SPRINT_DEFINITION_OF_DONE.md
│   ├── EVENT_REGISTRY.md
│   ├── REPOSITORY_COVERAGE_MATRIX.md
│   ├── UAT_ACCEPTANCE_MATRIX.md
│   └── ... (30 more documents)
│
├── tekson_manufacturing/              # Source code
│   ├── repositories/                  # Repository layer
│   │   ├── job_card_repository.py
│   │   ├── work_order_repository.py
│   │   ├── stock_repository.py
│   │   └── warehouse_repository.py
│   ├── services/                      # Service layer
│   │   ├── job_card_service.py
│   │   ├── work_order_service.py
│   │   └── stock_service.py
│   ├── readiness/                     # Sprint 1: Material Readiness
│   │   └── material_readiness.py
│   ├── validation/                    # Sprint 2: Dependency Engine
│   │   └── dependency_engine.py
│   ├── execution/                     # Sprint 3: Execution Engine
│   │   └── execution_engine.py
│   ├── tests/                         # Unit tests
│   │   ├── test_material_readiness.py
│   │   ├── test_dependency_engine.py
│   │   └── test_execution_engine.py
│   ├── utils/                         # Utilities
│   │   └── exceptions.py
│   └── hooks.py                       # ERP event handlers
│
└── ... (config files)
```

---

## 10. Quick Reference

### Business Rules by Category

| Category | Rules | Sprint |
|----------|-------|--------|
| Material Readiness | MR-010, MR-011 | 1 |
| Dependency Validation | DV-001, DV-002 | 2 |
| Job Card Execution | JC-001 to JC-005 | 3 |
| Work Order Completion | WO-001, WO-002 | 3 |
| Diagnostics & Messages | DM-001 to DM-004 | 4 |
| Department Transfer | WH-001 to WH-005 | 5 |
| Exception Handling | 46 scenarios | 6 |
| Security Framework | Security rules | 7 |
| User Interface | UI/UX rules | 8-9 |
| Production Readiness | Production criteria | 10 |

### Key Commands

```bash
# Run tests
bench run-tests --app tekson_manufacturing

# Run linting
bench lint

# Build assets
bench build --app tekson_manufacturing

# Open frappe console
bench --site [site-name] console

# Check test coverage
bench run-tests --app tekson_manufacturing --coverage
```

### Key URLs

| Resource | URL |
|----------|-----|
| GitHub Repository | https://github.com/devosduotech/tekson_manufacturing |
| Branch | `develop` |
| ERPNext V15 Docs | https://frappeframework.com/docs/v15 |

---

## 11. Contact & Support

| Role | Responsibility |
|------|----------------|
| Technical Lead | Architecture, code review, technical decisions |
| Developers | Implementation, unit testing, documentation |
| QA | Integration testing, UAT coordination |
| Project Manager | Sprint planning, stakeholder communication |
| Business Users | UAT execution, business rule validation |

---

## 12. Document Status Legend

| Status | Meaning | Change Process |
|--------|---------|----------------|
| **Frozen** | Cannot change without governance approval | Change Request + Technical Lead approval |
| **Controlled** | Managed changes with version tracking | Version increment + changelog update |
| **Living** | Updated regularly (after each sprint) | Sprint completion update |
| **Active** | Current working document | Standard edit process |

---

## 13. Onboarding Checklist

### Day 1

- [ ] Read **01_PROJECT_OVERVIEW.md**
- [ ] Read **MES_ARCHITECTURE_OVERVIEW.md**
- [ ] Read **BUSINESS_RULES_SPECIFICATION.md** (relevant sections)
- [ ] Set up development environment
- [ ] Run existing tests

### Day 2

- [ ] Read **PYTHON_CODING_STANDARDS.md**
- [ ] Read **SPRINT_DEFINITION_OF_DONE.md**
- [ ] Read **EVENT_REGISTRY.md**
- [ ] Read **REPOSITORY_COVERAGE_MATRIX.md**
- [ ] Review existing code (Sprints 1-3)

### Day 3

- [ ] Start Sprint 4 implementation
- [ ] Follow Definition of Done for all tasks
- [ ] Update living documents after completion

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-01 | Development | Initial documentation index creation |

---

## Related Documents

All documents listed above are in the `docs/` directory.

**Start Here:** [01_PROJECT_OVERVIEW.md](01_PROJECT_OVERVIEW.md)
