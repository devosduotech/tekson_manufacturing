# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
