# Tekson Manufacturing

**ERPNext V15 Manufacturing Custom Application**

**Publisher:** OSDuo Tech LLP  
**License:** MIT  
**Current Status:** Architecture Frozen - Business Logic Implementation In Progress

Tekson Manufacturing is a custom ERPNext application designed to enhance manufacturing operations for Teksons. It provides advanced material readiness validation, work order automation, and shop floor execution controls.

---

## Features

### Current Implementation
- ✅ Service-Oriented MES Architecture
- ✅ Execution Engine (framework implemented)
- ✅ Material Readiness Engine (framework implemented)
- ✅ Dependency Engine (framework implemented)
- ✅ Diagnostics Engine (framework implemented)
- ✅ Service Layer (reusable business logic)
- ✅ API Layer (client-side integration)
- ✅ Job Card controller override with auto work order completion
- ✅ Configuration framework (Manufacturing Settings)

### Implementation Status
- ✅ Architecture (100% complete)
- 🔄 Core MES Engines (framework implemented, business logic in progress)
- 🔄 Configuration Layer (framework ready)
- 🔄 Testing & UAT (pending)

**Note:** Version numbering will be updated only after successful UAT completion and bug fixes.

### Future Roadmap (Phase 2+)
- Operator Work Queue
- Supervisor Dashboard
- Production Bucket concept
- Date-wise Work Order consolidation
- Planner Workbench
- Capacity planning
- Subcontract Planning Integration
- Production Analytics & OEE
- Multi-plant Manufacturing Support

---

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/devosduotech/tekson_manufacturing --branch develop
bench install-app tekson_manufacturing
```

### Post-Installation

1. **Verify Installation:**
   ```python
   # In bench console
   from tekson_manufacturing.execution.execution_engine import ExecutionEngine
   from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
   print("MES Engines loaded successfully")
   ```

2. **Configure Manufacturing Settings:**
   - Enable/disable MES features
   - Configure warehouse mappings
   - Set default warehouses

3. **Test APIs:**
   ```python
   # Check if Job Card can start
   from tekson_manufacturing.api.job_card import check_can_start
   result = check_can_start("Job Card Name")
   
   # Check material readiness
   from tekson_manufacturing.api.work_order import check_material_readiness
   result = check_material_readiness("Work Order Name")
   ```

4. **Test with Sample Work Order:**
   - Create a Work Order
   - Complete all Job Cards
   - Verify Work Order auto-completes
   - Check diagnostic messages

---

## Architecture

### Separation of Responsibilities

```
Production Planning (ERPNext Standard)
        ↓
Manufacturing Execution (tekson_manufacturing MES)
        ↓
Monitoring & Traceability
```

1. **Planning Layer:** ERPNext Production Plan (standard)
2. **Execution Layer:** MES Engine (Phase 1)
3. **Monitoring Layer:** Diagnostics & Traceability

### MES Architecture (Phase 1)

```
tekson_manufacturing/
│
├── manufacturing/          # ERPNext Overrides (Thin Layer)
├── execution/              # MES Engine (Central Orchestrator)
├── readiness/              # Material Readiness Engine
├── validation/             # Dependency Validation Engine
├── diagnostics/            # Operator Messages Engine
├── services/               # Reusable Business Logic
├── api/                    # Whitelisted APIs
└── settings/               # Configuration Framework
```

### Key Components

| Module | Purpose | Implementation Status |
|--------|---------|----------------------|
| `execution/execution_engine.py` | Central MES orchestrator | Framework Implemented |
| `readiness/material_readiness.py` | Material readiness validation | Framework Implemented |
| `validation/dependency_engine.py` | Previous operation validation | Framework Implemented |
| `diagnostics/messages.py` | Clear operator messages | Framework Implemented |
| `services/job_card_service.py` | Job Card business logic | Framework Implemented |
| `services/work_order_service.py` | Work Order business logic | Framework Implemented |
| `api/job_card.py` | Job Card APIs | Framework Implemented |
| `api/work_order.py` | Work Order APIs | Framework Implemented |
| `settings/manufacturing_settings.py` | Configuration framework | Framework Ready |

**Note:** Framework implementation provides structure and interfaces. Business logic implementation is in progress.

### Architecture Documentation

- **[MES_ARCHITECTURE_IMPLEMENTATION.md](./MES_ARCHITECTURE_IMPLEMENTATION.md)** - MES architecture & implementation guide
- **[MES_BUSINESS_RULES.md](./MES_BUSINESS_RULES.md)** - Business rules specification (70+ rules)
- **[WAREHOUSE_ARCHITECTURE_DECISION.md](./WAREHOUSE_ARCHITECTURE_DECISION.md)** - Department-centric warehouse model ⭐ NEW
- **[IMPLEMENTATION_TRACEABILITY.md](./IMPLEMENTATION_TRACEABILITY.md)** - Rule-to-code mapping
- **[MES_TEST_SCENARIOS.md](./MES_TEST_SCENARIOS.md)** - Test scenarios and UAT checklist

---

## Documentation

### Architecture & Design
- **[MES_ARCHITECTURE_IMPLEMENTATION.md](./MES_ARCHITECTURE_IMPLEMENTATION.md)** - **MES architecture & implementation guide** ⭐
- **[MES_BUSINESS_RULES.md](./MES_BUSINESS_RULES.md)** - **Business rules specification** ⭐ NEW
- **[ARCHITECTURE_UPDATES.md](./ARCHITECTURE_UPDATES.md)** - Latest architecture decisions (MPS/MES separation)
- **[UAT_REVIEW_ARCHITECTURE.md](./UAT_REVIEW_ARCHITECTURE.md)** - UAT findings and initial architecture

### Planning & Timeline
- **[PROJECT_TIMELINE.md](./PROJECT_TIMELINE.md)** - Master timeline & roadmap
- **[TIMELINE_SUMMARY_FOR_CUSTOMER.md](./TIMELINE_SUMMARY_FOR_CUSTOMER.md)** - Executive summary for customers
- **[PHASE1_IMPLEMENTATION_PLAN.md](./PHASE1_IMPLEMENTATION_PLAN.md)** - Technical implementation details

### History & Reference
- **[DEVELOPMENT_SUMMARY.md](./DEVELOPMENT_SUMMARY.md)** - Complete development history
- **[SESSION_SUMMARY_20260731.md](./SESSION_SUMMARY_20260731.md)** - Session records
- **[CHANGELOG.md](./CHANGELOG.md)** - Version history
- **[DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)** - Navigation guide

---

## Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/tekson_manufacturing
pre-commit install
```

Pre-commit is configured to use:
- ruff
- eslint
- prettier
- pyupgrade

### Development Workflow

1. Create feature branch from `develop`
2. Implement changes with tests
3. Submit pull request to `develop`
4. Code review and merge
5. Release to `main` with version tag

---

## Support

**Email:** developer@osduotech.com  
**Publisher:** OSDuo Tech LLP

For issues, feature requests, or questions, please create an issue on GitHub.

---

## UAT Feedback

If you encounter issues during UAT testing:

1. Document the issue with screenshots
2. Note the Work Order / Job Card numbers
3. Describe expected vs actual behaviour
4. Share via GitHub Issues or email

**Current UAT Issues (Phase 1):**
- Work Order status not updating to "Completed"
- Parent WO starting before child components complete
- Material validation not checking cumulative transfers
- Need to differentiate material types (Raw vs Component)

---

## Current Status

**Architecture:** ✅ Frozen  
**Framework:** ✅ Implemented  
**Business Logic:** 🔄 In Progress  
**Next Milestone:** Material Readiness Engine completion → Testing → UAT

**Version Policy:** Version numbering will be updated only after successful UAT completion and all bug fixes.

---

## License

MIT License - See [license.txt](./license.txt) for details.
