# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [In Development] - MES Architecture & Framework

### Added - MES Architecture & Framework Implementation

#### Core MES Engines
- **Execution Engine** - Central orchestrator for manufacturing execution
  - `can_job_card_start()` - Validates if Job Card can start
  - `can_job_card_complete()` - Validates if Job Card can complete
  - `complete_work_order()` - Auto-completes Work Orders
  
- **Material Readiness Engine** - Source-agnostic material validation
  - `evaluate_material_readiness()` - Core validation method
  - `classify_material_type()` - Raw/Component/Common/Subcontract classification
  - `check_material_availability()` - Stock checking with cumulative transfers
  - `get_cumulative_transferred_qty()` - Multiple transfer aggregation

- **Dependency Engine** - Operation dependency validation
  - `validate_previous_operation()` - Previous operation completion check
  - `get_previous_job_card()` - Fetch previous Job Card
  - `validate_operation_sequence()` - Sequence validation

- **Diagnostics Engine** - Clear, actionable operator messages
  - `build_material_shortage_message()` - Detailed shortage diagnostics
  - `build_previous_operation_message()` - Dependency blocking messages
  - `format_for_ui()` - UI-friendly formatting

#### Service Layer
- **JobCardService** - Reusable Job Card business logic
- **WorkOrderService** - Reusable Work Order business logic
- **MaterialService** - Material operations
- **StockService** - Stock operations

#### API Layer
- **Job Card APIs** - `get_job_card_details()`, `check_can_start()`, `check_can_complete()`
- **Work Order APIs** - `get_work_order_details()`, `complete_work_order()`, `check_material_readiness()`
- **Material APIs** - `get_material_status()`, `check_item_readiness()`

#### Configuration Framework
- **Manufacturing Settings** - Enable/disable MES features
  - Auto Complete Work Order
  - Enable Material Readiness
  - Enable Previous Operation Validation
  - Enable Diagnostics
  - Strict Material Validation

#### Architecture
- Service-oriented architecture implementation
- Clear separation of concerns (7 modular components)
- Thin ERPNext override layer
- Backward compatibility maintained

### Changed
- Restructured application into modular business capabilities
- Refactored Job Card override to use Execution Engine
- Refactored Work Order completion to use Execution Engine
- Moved business logic from overrides to Service Layer
- Added event handlers in hooks.py

### Technical Details
- New folder structure: `execution/`, `readiness/`, `validation/`, `diagnostics/`, `services/`, `api/`, `settings/`
- ~2,600 lines of framework code implemented
- 21 new files created
- 3 files modified
- Full backward compatibility maintained
- Architecture frozen - business logic implementation in progress

### Implementation Notes
- Framework provides structure, interfaces, and orchestration
- Business logic implementation ongoing (Material Readiness priority)
- Testing pending completion of core engines
- Version will be assigned after successful UAT and bug fixes

---

## [1.0.0] - 2026-07-31

### Added
- Custom Job Card class (`TeksonJobCard`) that auto-completes work orders on submission
- Work order completion logic with automatic stock entry creation
- Custom Job Card ListView with enhanced status indicators (disabled by default)
- Override for standard ERPNext Job Card doctype class
- Prevention of duplicate manufacture stock entries
- Automatic work order status updates to "Completed"

### Changed
- Initial production release

### Technical Details
- `custom_job_card.py`: Extends ERPNext JobCard with custom on_submit behavior
- `work_order.py`: Contains `complete_work_order()` function for automated stock entry
- `job_card_list.js`: Custom list view configuration (currently disabled via `ENABLE_TEKSON_JOB_CARD_VIEW`)
