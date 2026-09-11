# Phase 1 Code Audit — BOM Bulk Creator

**Date:** 2026-09-11
**Reviewer:** Code Audit
**Version:** v15.1.20
**Status:** Good foundation, several structural issues to fix before Phase 2

---

## Overall Assessment

| Area | Status | Assessment |
|------|--------|------------|
| DocType structure | Good | Appropriate foundation |
| Multi-level hierarchy model | Good / needs cleanup | Works, but relationship model is more complicated than necessary |
| BOM generation | Good | Bottom-up approach is correct |
| Draft BOM creation | Good | Correctly avoids submitting BOMs |
| ERPNext core isolation | Good | No core modification |
| Duplicate enqueue protection | Needs improvement | Race condition remains |
| Validation | Needs improvement | Current validation is incomplete |
| Tree server APIs | Partial | Useful foundation, but several methods need correction |
| Tree UI | **Not implemented** | Correctly treated as Phase 2 |
| Warehouse handling | **Not yet implemented** | Must be addressed before actual BOM creation can be reliable |
| Test coverage | **Weak** | Test class is effectively empty |
| Error handling | Needs improvement | Partial BOM creation is possible |
| Documentation/comments | Needs cleanup | Some comments describe behavior no longer present |

**Rating:** 7/10 as a foundation. Not a rewrite — targeted corrections worth making.

---

## Phase Boundary Definition

### Phase 1 — Completed Foundation

- BOM Bulk Creator DocType
- Final FG information
- Items table
- Hierarchy data model
- Cost calculation
- Multi-level BOM discovery
- Bottom-up BOM generation
- Draft BOM creation
- No child bom_no linkage
- Status tracking
- Error logging
- Server-side APIs for future Tree

### Phase 1 Hardening — MUST DO Before Phase 2

1. Remove is_root references from JS
2. Add Target FG Warehouse to parent + child doctypes
3. Validate warehouse before enqueue
4. Add cycle validation (prevent A→B→A)
5. Fix delete_node to operate on row.name not item_code
6. Fix enqueue race condition (atomic status transition)
7. Add qty > 0 validation in edit_qty
8. Add check_permission('write') to mutation methods
9. Correct stale docstrings in create_boms
10. Add basic integration tests (12 scenarios)

### Phase 2 — Tree UI

- Render root
- Render hierarchy
- Expand/collapse
- Select node
- Add RM
- Add sub-assembly
- Convert RM → sub-assembly
- Edit quantity
- Delete node
- Show warehouse
- Sync Tree ↔ Items table

---

## Critical Findings

### 1. is_root is wrong

JS references `is_root` field but BOM Bulk Creator Item does not have this field. Remove `set_root_item()` and `is_root` check from child handler.

### 2. Parent-child relationship is the biggest architectural weakness

Currently uses: `fg_item`, `parent_row_no`, `fg_reference_id`, `idx` together.

Flow: `parent_row_no` → `row.idx` → `row.name` → `fg_reference_id`

This is fragile because `idx` is an ordering value, not a permanent identity.

**Better model:** Make `fg_reference_id = canonical parent node ID` and treat `parent_row_no` as compatibility/legacy field.

### 3. set_reference_id() depends on idx

```python
parent_reference = {row.idx: row.name for row in self.items}
```

This creates dependency on `idx`. Phase 1 can remain temporarily, but Tree UI should use `row.name` directly.

### 4. set_is_expandable() is conceptually weak

Current logic checks if item code appears as FG item elsewhere. Should instead check if the specific node has children:

```python
row.is_expandable = any(
    child.fg_reference_id == row.name
    for child in self.items
)
```

### 5. delete_node() needs correction

Currently switches from `row.name` to `item_code` for recursive deletion. Creates ambiguity when same item code appears in multiple branches. Should operate on `row.name` throughout.

### 6. Missing Target FG Warehouse

BOM_FIELDS does not include Target FG Warehouse. The header has `default_warehouse` but labeled "Default Source Warehouse". Need:
- `target_fg_warehouse` on parent doctype
- `target_fg_warehouse` on child doctype (per BOM node)

### 7. Validation is insufficient

Current validation only catches root self-reference. Missing:
- Root: FG item exists, Qty > 0, Company exists, Target FG Warehouse exists
- BOM node: Item exists, Qty > 0, Target FG Warehouse exists
- Tree relationship: Parent exists, No orphan node, No cycle, No self-reference
- BOM generation: No invalid BOM-producing node, No duplicate active creation job

### 8. BOM creation has partial-failure problem

If BOM A and B created but C fails, A and B remain in database. Need better error reporting showing what was created vs what failed.

### 9. Enqueue race condition

Current check-then-set is susceptible to race:
```
Request A → sees Draft
Request B → sees Draft
Request A → sets In Progress
Request B → sets In Progress
```

Need atomic/locked status transition.

### 10. edit_qty() lacks quantity validation

No check for `qty > 0`. Can save `qty = 0` or `qty = -5`.

### 11. Missing permissions on mutation methods

`add_item()`, `add_sub_assembly()`, `delete_node()`, `edit_qty()` should have `self.check_permission("write")`.

### 12. Stale docstrings

`create_boms()` docstring says "Child BOMs are created first, then parent BOMs reference them via bom_no" but code explicitly sets `"bom_no": ""`.

---

## What NOT to Change

- Do not modify ERPNext BOM
- Do not modify ERPNext BOM Creator
- Do not submit generated BOMs
- Do not automatically populate bom_no with Draft BOMs
- Do not introduce a separate custom BOM DocType
- Do not create a separate Frappe Page for the Tree
- Do not duplicate the complete ERPNext BOM Creator code
- Do not make item code the tree node ID
- Do not implement drag/drop/re-parenting yet

---

## Priority Order

```
                CURRENT PHASE 1
                      │
         ┌────────────┴────────────┐
         │                         │
   BOM Generation              Tree Support
         │                         │
         ▼                         ▼
  Warehouse handling        Node identity
  Validation                Delete logic
  Race protection            Cycle validation
         │                         │
         └────────────┬────────────┘
                      ▼
              PHASE 1 HARDENING
                      │
                      ▼
                 PHASE 2
                 BOM TREE UI
```

**Three mandatory fixes before Tree UI:**

1. Replace `idx`-driven parent relationship with stable node identity
2. Make Target FG Warehouse part of the BOM-node model and validate before BOM generation
3. Make Tree operations operate on exact row names, particularly `delete_node()`
