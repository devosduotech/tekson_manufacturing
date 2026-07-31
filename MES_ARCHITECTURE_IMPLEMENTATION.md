# Manufacturing Execution System (MES) – Architecture & Implementation Guide

**Date:** 2026-07-31  
**Architecture:** Service-Oriented MES  
**Status:** Architecture Frozen - Framework Implemented

---

## Overview

This document describes the architecture and implementation approach for the Tekson Manufacturing Execution System (MES). The architecture is complete and framework implementation is done. Business logic implementation is in progress.

**Implementation Approach:**
- Architecture: ✅ Frozen
- Framework: ✅ Implemented (structure, interfaces, orchestration)
- Business Logic: 🔄 In Progress (Material Readiness priority)
- Testing: ⏳ Pending
- UAT: ⏳ Pending

**Version Policy:** A formal version number will be assigned only after successful UAT completion and all bug fixes.

---

## New Folder Structure

```
tekson_manufacturing/
│
├── manufacturing/              # ERPNext Overrides (Thin Layer)
│   ├── custom_job_card.py     # Job Card override
│   └── work_order.py          # Work Order helper (backward compat)
│
├── execution/                  # MES Engine
│   ├── execution_engine.py    # Central orchestrator
│   ├── job_card_execution.py  # Job Card execution logic
│   └── work_order_completion.py # WO completion logic
│
├── readiness/                  # Material Readiness
│   ├── material_readiness.py  # Core readiness engine
│   ├── warehouse_validation.py # Warehouse checks
│   └── material_transfer.py   # Transfer validation
│
├── validation/                 # Dependency Validation
│   ├── dependency_engine.py   # Previous operation validation
│   └── operation_validation.py # Operation checks
│
├── diagnostics/                # Operator Messages
│   ├── messages.py            # Message builder
│   └── status_builder.py      # Status construction
│
├── services/                   # Reusable Business Logic
│   ├── job_card_service.py    # Job Card service
│   ├── work_order_service.py  # Work Order service
│   ├── material_service.py    # Material service
│   └── stock_service.py       # Stock service
│
├── api/                        # Whitelisted Methods
│   ├── job_card.py            # Job Card APIs
│   ├── work_order.py          # Work Order APIs
│   └── material.py            # Material APIs
│
├── settings/                   # Configuration
│   ├── manufacturing_settings.py # Settings doctype
│   └── warehouse_config.py    # Warehouse configuration
│
└── utils/                      # Utilities
    └── helpers.py             # Helper functions
```

---

## Architecture Layers

### Layer 1: ERPNext Overrides (manufacturing/)

**Purpose:** Thin adapter layer connecting ERPNext to MES

**Responsibilities:**
- Override Job Card on_submit
- Override Work Order methods (if needed)
- Call Execution Engine
- No business logic

**Example:**
```python
class TeksonJobCard(JobCard):
    def on_submit(self):
        super().on_submit()
        
        # Call Execution Engine
        engine = ExecutionEngine()
        engine.complete_work_order(self.work_order)
```

---

### Layer 2: Execution Engine (execution/)

**Purpose:** Central orchestrator for MES operations

**Responsibilities:**
- Can Job Card start?
- Can Job Card complete?
- Can Work Order complete?
- Coordinate validations
- Generate diagnostics

**Key Class:**
```python
class ExecutionEngine:
    def can_job_card_start(self, job_card)
    def can_job_card_complete(self, job_card)
    def complete_work_order(self, work_order)
```

---

### Layer 3: Material Readiness (readiness/)

**Purpose:** Determine if materials are available

**Responsibilities:**
- Check material availability
- Classify material types
- Calculate cumulative transfers
- Generate shortage details

**Key Class:**
```python
class MaterialReadinessEngine:
    def evaluate_material_readiness(self, work_order)
    def classify_material_type(self, item_code, work_order)
    def check_material_availability(self, item_code, qty, warehouse)
```

---

### Layer 4: Validation (validation/)

**Purpose:** Validate dependencies and operations

**Responsibilities:**
- Previous operation completion
- Operation sequence validation
- Multi-dependency checks (future)

**Key Class:**
```python
class DependencyEngine:
    def validate_previous_operation(self, job_card)
    def validate_operation_sequence(self, work_order)
```

---

### Layer 5: Diagnostics (diagnostics/)

**Purpose:** Build clear, actionable messages

**Responsibilities:**
- Material shortage messages
- Dependency blocking messages
- Success messages
- UI formatting

**Key Class:**
```python
class DiagnosticMessages:
    def build_material_shortage_message(self, shortage_details)
    def build_previous_operation_message(self, details)
    def format_for_ui(self, diagnostics_list)
```

---

### Layer 6: Services (services/)

**Purpose:** Reusable business logic

**Responsibilities:**
- Job Card operations
- Work Order operations
- Material operations
- Stock operations

**Key Classes:**
```python
class JobCardService:
    def get_job_card_details(self, job_card)
    def can_start(self, job_card)
    def refresh_status(self, job_card)

class WorkOrderService:
    def get_work_order_details(self, work_order)
    def complete(self, work_order)
```

---

### Layer 7: API (api/)

**Purpose:** Whitelisted methods for client-side calls

**Responsibilities:**
- Job Card APIs
- Work Order APIs
- Material APIs

**Example:**
```python
@frappe.whitelist()
def get_job_card_details(job_card):
    service = JobCardService()
    return service.get_job_card_details(job_card)
```

---

## Data Flow

### Job Card Start Flow

```
User clicks "Start" on Job Card
        │
        ↓
API: check_can_start(job_card)
        │
        ↓
Execution Engine
        │
        ├─→ Dependency Engine (Previous Operation?)
        ├─→ Material Readiness (Materials available?)
        └─→ Diagnostics (Build messages)
        │
        ↓
Return: can_start, reason, diagnostics
```

### Job Card Submit Flow

```
Job Card.on_submit()
        │
        ↓
Execution Engine
        │
        ├─→ Update dependent Job Cards
        └─→ Complete Work Order (if all JCs done)
        │
        ↓
Work Order Completion
        │
        ├─→ Check all JCs completed
        ├─→ Create Stock Entry
        └─→ Update WO status
```

### Material Readiness Flow

```
evaluate_material_readiness(work_order)
        │
        ↓
Get Required Materials (from BOM)
        │
        ↓
For each material:
    ├─→ Classify type (Raw/Component/Common)
    ├─→ Check availability
    ├─→ Get reason if shortage
    └─→ Build shortage details
        │
        ↓
Return: is_ready, missing_items, shortage_details
```

---

## Key Design Principles

### 1. Service-Oriented Architecture

All business logic lives in **Services**, not in overrides.

**Good:**
```python
# Override calls service
class TeksonJobCard(JobCard):
    def on_submit(self):
        service = JobCardService()
        service.handle_submit(self)
```

**Bad:**
```python
# Business logic in override (avoid)
class TeksonJobCard(JobCard):
    def on_submit(self):
        # 50 lines of business logic
```

---

### 2. Single Responsibility

Each class has one clear responsibility.

- `MaterialReadinessEngine` → Material checks only
- `DependencyEngine` → Dependency validation only
- `DiagnosticMessages` → Message building only
- `ExecutionEngine` → Orchestration only

---

### 3. No Duplicated Logic

All reusable logic is in **Services**.

- Controllers call services
- APIs call services
- UI calls services
- **No duplication**

---

### 4. Clear Diagnostics

Never return generic errors.

**Bad:**
```
"Material not available"
```

**Good:**
```
"Copper Tube shortage:
 Required: 20 kg
 Available: 15 kg
 Shortage: 5 kg
 Reason: Pending transfer from PO-2026-001
 Action: Check with warehouse"
```

---

### 5. Configuration Over Hard-Coding

Use **Manufacturing Settings** for flexibility.

```python
# Check setting
if settings.enable_material_readiness:
    # Validate material
else:
    # Skip validation
```

---

## Manufacturing Settings

Planned configuration options:

```
Manufacturing Settings
├── Auto Complete Work Order (Checkbox)
├── Enable Material Readiness (Checkbox)
├── Enable Previous Operation Validation (Checkbox)
├── Enable Diagnostics (Checkbox)
├── Strict Material Validation (Checkbox)
├── Raw Material Warehouse (Link)
├── Common Component Warehouse (Link)
├── Default WIP Warehouse (Link)
└── Finished Goods Warehouse (Link)
```

---

## Implementation Status

### Framework Implementation ✅ COMPLETE

The following framework components are implemented and ready:

- ✅ Folder structure created
- ✅ All module directories with __init__.py
- ✅ ExecutionEngine class with orchestration methods
- ✅ MaterialReadinessEngine class with evaluation framework
- ✅ DependencyEngine class with validation framework
- ✅ DiagnosticMessages class with message builders
- ✅ JobCardService and WorkOrderService classes
- ✅ API layer with whitelisted methods
- ✅ Event handlers in hooks.py
- ✅ Refactored overrides to use new architecture

### Business Logic Implementation 🔄 IN PROGRESS

Priority focus areas:

1. **Material Readiness Engine** (HIGH PRIORITY)
   - 🔄 Material classification logic
   - 🔄 Cumulative transfer calculation
   - 🔄 Availability checking by material type
   - 🔄 Shortage reason determination
   - 🔄 Integration with warehouse configuration

2. **Dependency Engine**
   - ✅ Previous operation validation (implemented)
   - 🔄 Enhanced multi-dependency support (future)

3. **Diagnostics**
   - 🔄 Complete shortage message details
   - 🔄 UI integration
   - 🔄 User-friendly formatting

4. **Services**
   - 🔄 Complete business logic implementation
   - 🔄 Repository pattern for ERP access

5. **Settings**
   - 🔄 Manufacturing Settings doctype
   - 🔄 Configuration UI
   - 🔄 Integration with engines

### Next Steps

1. Complete Material Readiness Engine business logic
2. Create Manufacturing Settings doctype
3. Write unit tests
4. Internal testing with UAT data
5. Customer UAT
6. Bug fixes
7. **Version assignment after successful UAT**

---

## Migration from Old Architecture

### Current State
```
manufacturing/
├── custom_job_card.py  (has business logic)
└── work_order.py       (has business logic)
```

### Target State
```
manufacturing/
├── custom_job_card.py  (thin adapter)
└── work_order.py       (backward compat wrapper)

execution/
├── execution_engine.py (business logic)

services/
├── job_card_service.py (reusable logic)
└── work_order_service.py (reusable logic)
```

### Migration Steps

1. **Keep existing functionality working**
2. **Create new architecture in parallel**
3. **Test new architecture thoroughly**
4. **Switch overrides to use new architecture**
5. **Remove old business logic from overrides**

---

## Benefits of New Architecture

### 1. Scalability
- Easy to add new features
- Clear separation of concerns
- No spaghetti code

### 2. Testability
- Each component can be tested independently
- Mock services for testing
- Clear interfaces

### 3. Maintainability
- Easy to find code
- Clear responsibilities
- No duplicated logic

### 4. Flexibility
- Configuration over hard-coding
- Easy to enable/disable features
- Backward compatible

### 5. Upgrade Safety
- ERPNext upgrades won't break custom logic
- Clear boundaries between standard and custom
- Minimal override surface area

---

## Next Steps

1. **Complete Material Readiness Engine** - Core MES functionality
2. **Test with UAT data** - Verify all issues resolved
3. **Add Manufacturing Settings** - Configuration flexibility
4. **Create Client Scripts** - Use new APIs
5. **User Training** - Explain new diagnostics
6. **Second UAT** - Validate with customer

---

*This architecture document is maintained in the repository and updated as the implementation progresses.*
