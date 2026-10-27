"""
Operation-driven target warehouse resolution for material transfers.

Business rule: a transfer for a BOM Item line targets the warehouse of the
operation consuming that material (BOM Item.operation). The Work Order
header warehouse is derived from the BOM's FIRST operation and must NEVER be
used for items that carry an operation — BOMs span multiple plant floors.

Resolution chain for an operation (mirrors Job Card creation in
job_card_utils.allocate_workstation + set_wip_warehouse):

    BOM Operation (operation match, case/whitespace tolerant)
        -> workstation_type (or direct workstation link)
        -> Workstation -> plant_floor
        -> "WIP-{plant_floor} - TPL" (must exist)

The Job Card's stored wip_warehouse (or, failing that, its workstation) is
the fallback when configuration cannot be resolved. When both are present and
disagree, configuration wins — it is what the user maintains; the caller
should surface the mismatch as a warning so the Job Card can be re-saved.

Every failed link appends a plain-English reason to the optional `reasons`
list so callers can tell the user *what* to fix instead of only that the
material was skipped.
"""

import re

import frappe


def normalize_operation(operation) -> str:
    """Case- and whitespace-insensitive key for operation names.

    BOM Item / BOM Operation / Job Card all store the operation as a Link,
    but the link values can differ in case or spacing (duplicate Operation
    masters, trailing spaces) while still meaning the same routing step.
    """
    return " ".join((operation or "").split()).casefold()


def _add_reason(reasons, text):
    """Record a diagnostic reason (no-op when the caller does not collect)."""
    if reasons is not None and text and text not in reasons:
        reasons.append(text)


def wip_warehouse_name(plant_floor) -> str:
    """Canonical WIP warehouse name for a plant floor."""
    return f"WIP-{(plant_floor or '').strip()} - TPL"


def find_wip_warehouse(plant_floor, reasons=None) -> str:
    """
    plant_floor -> WIP warehouse. The convention name `WIP-{floor} - TPL`
    wins; when it does not exist, a *unique* naming variant of the same
    floor's WIP is accepted (e.g. `WIP - RP - TPL`) and logged, so a
    mis-spelled warehouse does not silently drop material. '' when nothing
    plausible exists.
    """
    floor = (plant_floor or "").strip()
    if not floor:
        return ""

    exact = wip_warehouse_name(floor)
    if frappe.db.exists("Warehouse", exact):
        return exact

    pattern = re.compile(rf"^WIP[^0-9A-Za-z]*{re.escape(floor)}([^0-9A-Za-z]|$)", re.I)
    variants = []
    for row in frappe.get_all(
        "Warehouse", {"name": ["like", f"%{floor}%"]}, ["name"]
    ):
        name = (row.get("name") or "").strip()
        if name and name != exact and pattern.match(name):
            variants.append(name)

    if len(variants) == 1:
        frappe.logger().warning(
            f"Warehouse '{exact}' does not exist — using '{variants[0]}' for plant floor {floor}"
        )
        return variants[0]

    if variants:
        _add_reason(
            reasons,
            f"warehouse {exact} does not exist and several WIP warehouses match plant floor "
            f"{floor}: {', '.join(sorted(variants))}",
        )
    else:
        _add_reason(reasons, f"warehouse {exact} does not exist for plant floor {floor}")
    return ""


def warehouse_for_workstation(workstation, reasons=None) -> str:
    """Workstation -> plant_floor -> WIP warehouse ('' when unresolvable)."""
    workstation = (workstation or "").strip()
    if not workstation:
        return ""
    plant_floor = frappe.db.get_value("Workstation", workstation, "plant_floor")
    if not plant_floor:
        _add_reason(reasons, f"Workstation {workstation} has no plant floor")
        return ""
    return find_wip_warehouse(plant_floor, reasons)


def _warehouse_for_workstation_type(ws_type, reasons=None) -> str:
    """workstation_type -> first workstation -> plant_floor -> WIP warehouse."""
    ws_type = (ws_type or "").strip()
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
        _add_reason(reasons, f"no Workstation of type '{ws_type}'")
        return ""
    return warehouse_for_workstation(workstation, reasons)


def _bom_operation_rows(bom_no, cache):
    """BOM Operation rows of one BOM, fetched once per batch (cache)."""
    rows_key = ("ops", bom_no)
    if rows_key not in cache:
        cache[rows_key] = frappe.get_all(
            "BOM Operation",
            {"parent": bom_no},
            ["operation", "workstation_type", "workstation"],
            order_by="idx asc",
        )
    return cache[rows_key]


def resolve_operation_warehouse(bom_no, operation, fallback_bom_no=None,
                                cache=None, reasons=None) -> str:
    """
    Configuration-derived WIP warehouse for `operation` — '' when it cannot
    be resolved. Operation matching ignores case and surrounding whitespace.

    `cache` is an optional dict reused across a batch of lookups (BOM
    Operation rows are fetched once per BOM, results memoised per operation).
    `reasons` is an optional list that receives one entry per failed link.
    """
    operation_display = " ".join((operation or "").split())
    operation_key = normalize_operation(operation)
    if not operation_key:
        return ""

    if cache is None:
        cache = {}

    cache_key = ("wh", bom_no, fallback_bom_no, operation_key)
    if cache_key in cache:
        warehouse, cached_reasons = cache[cache_key]
        for reason in cached_reasons:
            _add_reason(reasons, reason)
        return warehouse

    candidates = [bom_no]
    if fallback_bom_no and fallback_bom_no != bom_no:
        candidates.append(fallback_bom_no)

    local_reasons = []
    warehouse = ""
    for candidate in candidates:
        if not candidate:
            continue
        rows = _bom_operation_rows(candidate, cache)
        if not rows:
            _add_reason(local_reasons, f"BOM '{candidate}' has no routing (BOM Operation) rows")
            continue
        matched = [r for r in rows if normalize_operation(r.get("operation")) == operation_key]
        if not matched:
            routing = ", ".join(
                " ".join((r.get("operation") or "").split()) for r in rows
                if (r.get("operation") or "").strip()
            )
            routing_list = routing or "none"
            _add_reason(
                local_reasons,
                f"BOM '{candidate}' routing has no operation '{operation_display}' "
                f"(routing: {routing_list})",
            )
            continue
        for row in matched:
            ws_type = row.get("workstation_type") or row.get("workstation")
            if not ws_type:
                _add_reason(
                    local_reasons,
                    f"routing row '{operation_display}' of BOM '{candidate}' has no workstation "
                    f"/ workstation type",
                )
                continue
            warehouse = _warehouse_for_workstation_type(ws_type, local_reasons)
            if warehouse:
                break
        if warehouse:
            break

    cache[cache_key] = (warehouse, tuple(local_reasons))
    for reason in local_reasons:
        _add_reason(reasons, reason)
    return warehouse


def resolve_target_warehouse(bom_no, operation, source_bom=None, jc_warehouse=None,
                             jc_workstation=None, fallback_warehouse="", cache=None,
                             reasons=None) -> str:
    """
    Target (WIP) warehouse for one BOM Item line.

    - Operation configured: configuration-derived warehouse, else the Job
      Card's wip_warehouse, else the Job Card's workstation's plant floor.
      The Work Order header warehouse is NEVER used.
    - No operation: fallback_warehouse (Work Order WIP).

    Returns '' when an operation is configured but neither configuration nor
    a Job Card resolves it — callers must skip such lines instead of
    silently falling back to the first-operation warehouse.
    """
    if not normalize_operation(operation):
        return fallback_warehouse or ""

    primary = source_bom or bom_no
    secondary = bom_no if (source_bom and bom_no and source_bom != bom_no) else None
    warehouse = resolve_operation_warehouse(primary, operation,
                                            fallback_bom_no=secondary, cache=cache,
                                            reasons=reasons)
    if warehouse:
        return warehouse
    if jc_warehouse:
        return jc_warehouse
    if jc_workstation:
        warehouse = warehouse_for_workstation(jc_workstation, reasons)
        if warehouse:
            return warehouse
    _add_reason(
        reasons,
        f"no Job Card WIP warehouse (or workstation plant floor) for operation "
        f"'{' '.join((operation or '').split())}'",
    )
    return ""
