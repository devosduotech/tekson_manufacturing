# Tekson Manufacturing

**ERPNext V15 Manufacturing Custom Application**

**Version:** 1.1.0 (In Development)  
**Publisher:** OSDuo Tech LLP  
**License:** MIT

Tekson Manufacturing is a custom ERPNext application designed to enhance manufacturing operations for Teksons. It provides advanced material readiness validation, work order automation, and shop floor execution controls.

---

## Features

### Current (v1.1.0 - Phase 1 MES Architecture)
- ✅ Service-Oriented MES Architecture
- ✅ Execution Engine (central orchestrator)
- ✅ Material Readiness Engine (source-agnostic validation)
- ✅ Dependency Engine (previous operation validation)
- ✅ Diagnostics Engine (clear operator messages)
- ✅ Service Layer (reusable business logic)
- ✅ API Layer (client-side integration)
- ✅ Job Card controller override with auto work order completion
- ✅ Configuration framework (Manufacturing Settings)

### Phase 1 Implementation Status
- ✅ Architecture restructuring (complete)
- ✅ Execution Engine (complete)
- ✅ Material Readiness Engine (complete)
- ✅ Dependency Engine (complete)
- ✅ Diagnostics Engine (complete)
- ✅ Service Layer (complete)
- ✅ API Layer (complete)
- 🔄 Manufacturing Settings (framework ready)
- 🔄 Warehouse Configuration (pending)
- 🔄 Testing & UAT (pending)

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

| Module | Purpose | Status |
|--------|---------|--------|
| `execution/execution_engine.py` | Central MES orchestrator | ✅ Complete |
| `readiness/material_readiness.py` | Material readiness validation | ✅ Complete |
| `validation/dependency_engine.py` | Previous operation validation | ✅ Complete |
| `diagnostics/messages.py` | Clear operator messages | ✅ Complete |
| `services/job_card_service.py` | Job Card business logic | ✅ Complete |
| `services/work_order_service.py` | Work Order business logic | ✅ Complete |
| `api/job_card.py` | Job Card APIs | ✅ Complete |
| `api/work_order.py` | Work Order APIs | ✅ Complete |
| `settings/manufacturing_settings.py` | Configuration framework | ✅ Framework |

### Architecture Documentation

See [PHASE1_MES_ARCHITECTURE.md](./PHASE1_MES_ARCHITECTURE.md) for detailed architecture guide.

---

## Documentation

### Architecture & Design
- **[PHASE1_MES_ARCHITECTURE.md](./PHASE1_MES_ARCHITECTURE.md)** - **Phase 1 MES architecture guide** ⭐ NEW
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

## Version History

| Version | Date | Status | Description |
|---------|------|--------|-------------|
| 1.1.0 | 2026-07-31 | 🔄 In Development | Phase 1 MES Architecture (Service-Oriented) |
| 1.0.0 | 2026-07-31 | ✅ Released | Initial release (Job Card override, WO completion) |

---

## License

MIT License - See [license.txt](./license.txt) for details.
