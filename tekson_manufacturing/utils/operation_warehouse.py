"""
Operation-driven target warehouse resolution for material transfers.

Business rule: a transfer for a BOM Item line targets the warehouse of the
operation consuming that material (BOM Item.operation). The Work Order
header warehouse is derived from the BOM's FIRST operation and must NEVER be
used for items that carry an operation — BOMs span multiple plant floors.

Resolution chain for an operation (mirrors Job Card creation in
job_card_utils.allocate_workstation + set_wip_warehouse):

    BOM Operation (operation match, whitespace tolerant)
        -> workstation_type (or direct workstation link)
        -> Workstation -> plant_floor
        -> "WIP-{plant_floor} - TPL" (must exist)

The Job Card's stored wip_warehouse is the fallback when configuration
cannot be resolved. When both are present and disagree, configuration wins —
it is what the user maintains; the caller should surface the mismatch as a
warning so the Job Card can be re-saved.
"""

import frappe


def _warehouse_for_workstation_type(ws_type: str) -> str:
    """workstation_type -> first workstation -> plant_floor -> WIP warehouse."""
    if not ws_type:
        return ""
    workstation = frappe.db.get_value(
        "Workstation",
        {"workstation_type": ws_type},
        "name",
        order_by="name asc",
    )
    if not workstation and frappe.db.exists("Workstation", ws_type):
        # BOM Operation carries a direct workstation link instead of a type
        workstation = ws_type
    if not workstation:
        return ""
    plant_floor = frappe.db.get_value("Workstation", workstation, "plant_floor")
    if not plant_floor:
        return ""
    warehouse = f"WIP-{plant_floor} - TPL"
    return warehouse if frappe.db.exists("Warehouse", warehouse) else ""


def resolve_operation_warehouse(bom_no, operation, fallback_bom_no=None, cache=None) -> str:
    """
    Configuration-derived WIP warehouse for `operation` — '' when it cannot
    be resolved. Operation matching ignores leading/trailing whitespace.

    `cache` is an optional dict reused across a batch of lookups (BOM
    Operation rows are fetched once per BOM, results memoised per operation).
    """
    operation = (operation or "").strip()
    if not operation:
        return ""

    if cache is None:
        cache = {}

    cache_key = ("wh", bom_no, fallback_bom_no, operation)
    if cache_key in cache:
        return cache[cache_key]

    warehouse = ""
    candidates = [bom_no]
    if fallback_bom_no and fallback_bom_no != bom_no:
        candidates.append(fallback_bom_no)

    for candidate in candidates:
        if not candidate:
            continue
        rows_key = ("ops", candidate)
        if rows_key not in cache:
            cache[rows_key] = frappe.get_all(
                "BOM Operation",
                {"parent": candidate},
                ["operation", "workstation_type", "workstation"],
                order_by="idx asc",
            )
        for row in cache[rows_key]:
            if (row.get("operation") or "").strip() != operation:
                continue
            warehouse = _warehouse_for_workstation_type(
                row.get("workstation_type") or row.get("workstation")
            )
            if warehouse:
                break
        if warehouse:
            break

    cache[cache_key] = warehouse
    return warehouse


def resolve_target_warehouse(bom_no, operation, source_bom=None,
                             jc_warehouse=None, fallback_warehouse="") -> str:
    """
    Target (WIP) warehouse for one BOM Item line.

    - Operation configured: configuration-derived warehouse, else the Job
      Card's wip_warehouse. The Work Order header warehouse is NEVER used.
    - No operation: fallback_warehouse (Work Order WIP).

    Returns '' when an operation is configured but neither configuration nor
    a Job Card resolves it — callers must skip such lines instead of
    silently falling back to the first-operation warehouse.
    """
    if not (operation or "").strip():
        return fallback_warehouse or ""

    primary = source_bom or bom_no
    secondary = bom_no if (source_bom and bom_no and source_bom != bom_no) else None
    warehouse = resolve_operation_warehouse(primary, operation, fallback_bom_no=secondary)
    if warehouse:
        return warehouse
    if jc_warehouse:
        return jc_warehouse
    return ""
