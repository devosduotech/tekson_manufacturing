# Tekson Manufacturing

**ERPNext V15 Manufacturing Custom Application**

**Version:** 1.0.0  
**Publisher:** OSDuo Tech LLP  
**License:** MIT

Tekson Manufacturing is a custom ERPNext application designed to enhance manufacturing operations for Teksons. It provides advanced material readiness validation, work order automation, and shop floor execution controls.

---

## Features

### Current (v1.0.0)
- ✅ Job Card controller override with auto work order completion
- ✅ Previous operation dependency validation
- ✅ Material availability validation
- ✅ Start Status automation (Awaiting, Ready, In Progress, Completed)
- ✅ Custom fields for Job Card enhanced tracking
- ✅ Automatic Stock Entry creation on work order completion

### Coming in Phase 1 (Planned)
- 🔄 Material Readiness Engine (cumulative transfer checking)
- 🔄 Enhanced Work Order Completion Engine
- 🔄 Material Traceability & Diagnostic Messages
- 🔄 Warehouse Configuration (Raw, Component, WIP, FG)
- 🔄 Common Component handling across multiple WOs

### Future Roadmap
- Operator Work Queue
- Supervisor Dashboard
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

1. **Configure Manufacturing Settings:**
   - Set up warehouse configuration (Raw Material, WIP, FG)
   - Configure default warehouses per operation

2. **Verify Job Card Override:**
   ```python
   # In bench console
   from tekson_manufacturing.manufacturing.custom_job_card import TeksonJobCard
   print("TeksonJobCard loaded successfully")
   ```

3. **Test with Sample Work Order:**
   - Create a Work Order
   - Complete all Job Cards
   - Verify Work Order auto-completes

---

## Architecture

### Separation of Responsibilities

```
Production Planning → Material Readiness → Manufacturing Execution → Monitoring
```

1. **Planning Layer:** Decides source (Internal/Purchase/Subcontract)
2. **Readiness Layer:** Validates material availability
3. **Execution Layer:** Manages Job Cards & operations
4. **Monitoring Layer:** Provides diagnostics & traceability

### Key Components

| Module | Purpose |
|--------|---------|
| `custom_job_card.py` | Extends ERPNext JobCard with auto-completion |
| `work_order.py` | Work order status evaluation & completion |
| `material_engine.py` | Material readiness validation (Phase 1) |
| `traceability.py` | Shortage diagnostics (Phase 1) |

---

## Documentation

- **[DEVELOPMENT_SUMMARY.md](./DEVELOPMENT_SUMMARY.md)** - Complete development history and technical architecture
- **[UAT_REVIEW_ARCHITECTURE.md](./UAT_REVIEW_ARCHITECTURE.md)** - UAT findings and new architecture design
- **[PHASE1_IMPLEMENTATION_PLAN.md](./PHASE1_IMPLEMENTATION_PLAN.md)** - Current development priorities and timeline
- **[CHANGELOG.md](./CHANGELOG.md)** - Version history

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

| Version | Date | Status |
|---------|------|--------|
| 1.0.0 | 2026-07-31 | ✅ Released |
| 1.1.0 | TBD | 🔄 In Development (Phase 1) |

---

## License

MIT License - See [license.txt](./license.txt) for details.
