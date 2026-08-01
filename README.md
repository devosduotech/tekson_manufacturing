# Tekson Manufacturing MES

**Phase 1 - Manufacturing Execution System for ERPNext V15**

---

## Overview

Complete Manufacturing Execution System (MES) implementation for Teksons, designed for ERPNext Version 15.

**Status:** Feature Complete - Ready for Integration Testing & Internal UAT

---

## Features

### Core Manufacturing (Sprints 1-3) ✅
- Material Readiness Engine (MR-010, MR-011)
- Dependency Validation Engine (DV-001, DV-002)
- Execution Engine (JC-001 to JC-005, WO-001, WO-002)
- Repository Pattern (4 repositories)
- Service Layer (3 services)

### Diagnostics & Validation (Sprints 4-6) ✅
- Diagnostic Messages Framework (DM-001 to DM-004)
- Department Transfer Integration (WH-001 to WH-005)
- Exception Handling (46 scenarios)

### Security & UI (Sprints 7-9) ✅
- Security Framework (SEC-001 to SEC-005)
- Department-scoped permissions
- MES Dashboard & Reports
- UI Components

### System Validation (Sprint 10) 🔄
- Integration Testing
- Performance Testing
- Internal UAT
- Production Readiness

---

## Architecture

5-Layer Service-Oriented Architecture:

```
API Layer → Services → Engines → Repositories → ERPNext ORM
```

**Key Design Decisions:**
- Repository Pattern for data access
- Department-centric warehouse model
- Cumulative material readiness
- Sequential job card execution
- Parent/child WO synchronization

---

## Installation

### Prerequisites

- ERPNext V15
- Python 3.11+
- MariaDB 10.6+

### Install App

```bash
# Get the app
bench get-app https://github.com/devosduotech/tekson_manufacturing --branch develop

# Install on site
bench --site [site-name] install-app tekson_manufacturing
```

### Import Master Data (Optional)

```bash
# Export from VPS
bench --site [vps-site] execute tekson_manufacturing.scripts.export_master_data.export_master_data

# Import to local VM
bench --site [local-site] execute tekson_manufacturing.scripts.import_master_data.import_master_data --args '"/path/to/export"'
```

---

## Usage

### Run Integration Validation

```bash
bench --site [site-name] execute tekson_manufacturing.tests.sprint_10_validation.run_validation
```

### Verify Master Data

```bash
bench --site [site-name] execute tekson_manufacturing.tests.verify_master_data.verify_master_data
```

---

## Documentation

All documentation is in the `docs/` folder:

| Document | Description |
|----------|-------------|
| `00_PROJECT_INDEX.md` | Documentation index (start here) |
| `MES_BUSINESS_RULES.md` | 85 business rules specification |
| `MES_ARCHITECTURE_OVERVIEW.md` | 5-layer architecture |
| `SPRINT_10_PLAN.md` | Validation & production readiness plan |
| `CHANGELOG.md` | Version history |

---

## Progress

| Metric | Status |
|--------|--------|
| Business Rules Implemented | 74/85 (87%) |
| Sprints Complete | 9/10 (90%) |
| Weighted Effort | 83% |
| Unit Tests | 91 tests |
| Code Lines | ~5,550 |
| APIs | 22 endpoints |

---

## Testing

### Unit Tests

```bash
bench run-tests --app tekson_manufacturing
```

### Integration Tests

```bash
# Sprint 10 validation
bench --site [site-name] execute tekson_manufacturing.tests.sprint_10_validation.run_validation
```

---

## Project Structure

```
tekson_manufacturing/
├── docs/                          # Documentation (40+ files)
├── tekson_manufacturing/
│   ├── repositories/              # Repository layer (4 repos)
│   ├── services/                  # Service layer (4 services)
│   ├── readiness/                 # Material readiness engine
│   ├── validation/                # Dependency engine
│   ├── execution/                 # Execution engine
│   ├── diagnostics/               # Messages & exceptions
│   ├── tests/                     # Unit & integration tests
│   ├── scripts/                   # Export/Import scripts
│   ├── www/mes/                   # MES UI pages
│   └── hooks.py                   # ERP event handlers
└── ...
```

---

## License

Proprietary - Teksons

---

## Contact

**Technical Lead:** OSDuo Tech LLP  
**Project:** Tekson Manufacturing MES  
**ERPNext Version:** V15

---

## Version

**Current:** 1.0.9 (Sprints 1-9 Complete)  
**Next:** 1.0.10 (System Validation & Production Readiness)

---

*Last Updated: 2026-08-01*
