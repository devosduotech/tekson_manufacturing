import frappe
from frappe import _


def populate_job_card_fields(doc, method=None):
    """
    Auto-populate all Job Card custom fields from UAT
    
    Business Rules:
    - JC-007: Item visibility
    - JC-008: Quantity visibility
    - WO-001: Auto-complete when all Job Cards complete
    
    Trigger: Job Card Before Insert
    
    Fields Populated:
    - custom_operation_item_code: From Work Order production_item
    - custom_actual_production_qty: Quantity to produce
    - custom_plant_floor: From Workstation
    
    Side Effects:
    - Updates Work Order status to "Started" if materials are available
    """
    # JC-007: Set Item Code
    if doc.work_order and not doc.get('custom_operation_item_code'):
        production_item = frappe.db.get_value(
            "Work Order",
            doc.work_order,
            "production_item"
        )
        
        if production_item:
            doc.custom_operation_item_code = production_item
    
    # JC-008: Set Production Quantity
    if doc.work_order and not doc.get('custom_actual_production_qty'):
        wo = frappe.get_doc("Work Order", doc.work_order)
        
        if doc.for_quantity:
            doc.custom_actual_production_qty = doc.for_quantity
        elif wo.bom_no and hasattr(doc, 'production_item') and doc.production_item:
            # Multi-level BOM: parent BOM item qty × WO qty
            parent_item = frappe.db.get_value("BOM Item",
                {"parent": wo.bom_no, "item_code": doc.production_item}, "qty")
            if parent_item:
                doc.custom_actual_production_qty = parent_item * wo.qty
            else:
                doc.custom_actual_production_qty = wo.qty
        else:
            doc.custom_actual_production_qty = wo.qty
        
        # WO-001: Update WO status to "Started" if materials are available
        update_work_order_status_if_ready(doc.work_order)


# Workstation statuses that must never receive a new Job Card, regardless of load.
# "Setup" means the machine is still being set up / commissioned and is not yet
# in production. "Problem" means a fault has been reported on it, and
# "Maintenance" means it is under maintenance.
# "Off", "Idle" and "Production" are deliberately NOT blocked: ERPNext core sets
# a workstation to "Production" when a Job Card on it starts and back to "Off"
# when that Job Card completes, so treating "Off" as unavailable would exclude
# every free machine.
BLOCKED_WORKSTATION_STATUSES = ("Maintenance", "Problem", "Setup")

# Job Card states where the machine is occupied right now. These count against
# Workstation.production_capacity (the number of concurrent Job Cards allowed).
ACTIVE_JOB_CARD_STATUSES = ("Work In Progress", "On Hold")

# Terminal Job Card states. Anything else is planned work: it sits in the
# station's queue but does not occupy the machine yet.
CLOSED_JOB_CARD_STATUSES = ("Completed", "Cancelled")


def workstation_workload(workstation_names):
    """
    Workload metrics for the given workstations, in one aggregate query.

    Metrics per workstation:
      active_load - Job Cards occupying the machine now
                    (status in ACTIVE_JOB_CARD_STATUSES, docstatus < 2).
                    This is the number compared with production_capacity.
      open_load   - Job Cards still in the queue (anything not Completed or
                    Cancelled, docstatus < 2). Includes active_load. Used to
                    spread queued work evenly; never a hard availability filter:
                    a large batch of future Job Cards must not make a machine
                    look unavailable today.
      last_used   - latest actual production activity on the machine: the Job
                    Card's actual end date, or "now" while a Job Card is still
                    running (no actual end date yet). Queued Job Cards that never
                    started do not count as use; cancelled Job Cards
                    (docstatus = 2) are ignored. A machine that has never run
                    work keeps an empty value and sorts first.

    Also usable by a future capacity planner, which can combine these metrics
    with its own time-slot eligibility before calling pick_workstation().
    """
    names = list(workstation_names or [])
    metrics = {
        name: {"active_load": 0, "open_load": 0, "last_used": ""}
        for name in names
    }
    if not names:
        return metrics

    for row in frappe.db.sql(
        """
        SELECT workstation,
               MAX(
                   CASE
                       WHEN actual_start_date IS NOT NULL AND actual_end_date IS NULL
                       THEN NOW()
                       ELSE COALESCE(actual_end_date, actual_start_date)
                   END
               ) AS last_used,
               COUNT(DISTINCT CASE WHEN status NOT IN %(closed)s THEN name END) AS open_load,
               COUNT(DISTINCT CASE WHEN status IN %(active)s THEN name END) AS active_load
        FROM `tabJob Card`
        WHERE docstatus < 2 AND workstation IN %(names)s
        GROUP BY workstation
        """,
        {
            "closed": list(CLOSED_JOB_CARD_STATUSES),
            "active": list(ACTIVE_JOB_CARD_STATUSES),
            "names": tuple(names),
        },
        as_dict=True,
    ):
        metrics[row.workstation] = {
            "active_load": int(row.active_load or 0),
            "open_load": int(row.open_load or 0),
            "last_used": str(row.last_used or ""),
        }

    return metrics


def is_workstation_eligible(workstation, reasons=None):
    """A workstation can take work when it exists and is not blocked by status."""
    if not workstation:
        return False

    if not frappe.db.exists("Workstation", workstation):
        if reasons is not None:
            reasons.append(f"Workstation '{workstation}' does not exist")
        return False

    status = frappe.db.get_value("Workstation", workstation, "status")
    if (status or "") in BLOCKED_WORKSTATION_STATUSES:
        if reasons is not None:
            reasons.append(f"Workstation '{workstation}' is marked {status}")
        return False

    return True


def pick_workstation(workstation_type, reasons=None, candidates=None):
    """
    Shared workstation-selection service (Business Rule JC-006).

    This service deliberately does not schedule. It answers "which eligible
    workstation should this Job Card go to?" so the same rules can be used by
    the current allocation hook and by a future capacity planner.

    Current phase: queue-balanced least-recently-used rotation across eligible
    workstations of `workstation_type`.

    Future capacity planning: the planner should compute which workstations
    have a free time slot for the operation (working hours, holidays, existing
    scheduled operations, duration, dependencies) and pass that subset as
    `candidates`. This service then applies the same eligibility, workload and
    rotation rules within that subset. Rotation is a tie-breaker between
    equally suitable machines, never a replacement for scheduling.

    Ordering (best first):
      1. machines not already at their concurrent capacity (active_load <
         production_capacity) before those that are
      2. fewest queued Job Cards (open_load), so a batch of new Job Cards is
         spread across the type instead of stacking on the least recently used
         machine
      3. least recently used first, based on actual production activity
         (machines that have never run work sort first)
      4. workstation name (stable tie-break)

    Args:
        workstation_type: Workstation Type to select from.
        reasons: optional list collecting plain-English diagnostics.
        candidates: optional iterable of workstation names to restrict the
            selection to (used by capacity planning to pass time-slot-eligible
            workstations). None means "any workstation of the type".

    Returns:
        Workstation name, or None when no eligible workstation exists.
    """
    if not workstation_type:
        return None

    workstations = frappe.get_all(
        "Workstation",
        filters={"workstation_type": workstation_type},
        fields=["name", "status", "production_capacity"],
    )

    if not workstations:
        if reasons is not None:
            reasons.append(f"no Workstation of type '{workstation_type}'")
        return None

    allowed = set(candidates) if candidates is not None else None
    usable = [
        ws for ws in workstations
        if (ws.status or "") not in BLOCKED_WORKSTATION_STATUSES
        and (allowed is None or ws.name in allowed)
    ]

    if not usable:
        if reasons is not None:
            reasons.append(
                f"no eligible Workstation of type '{workstation_type}' "
                f"(blocked: {', '.join(BLOCKED_WORKSTATION_STATUSES)}"
                + (", no free time slot" if allowed is not None else "")
                + ")"
            )
        return None

    workload = workstation_workload([ws.name for ws in usable])

    def selection_key(ws):
        metrics = workload[ws.name]
        capacity = ws.production_capacity or 1
        return (
            metrics["active_load"] >= capacity,
            metrics["open_load"],
            metrics["last_used"],
            ws.name,
        )

    usable.sort(key=selection_key)

    if usable[0] and selection_key(usable[0])[0] and reasons is not None:
        reasons.append(
            f"all Workstations of type '{workstation_type}' are running at "
            f"capacity; assigned the least loaded machine (job creation is not "
            f"blocked)"
        )

    return usable[0].name


def allocate_workstation(doc, method=None):
    """
    Auto-allocate Workstation from BOM Operation

    Business Rule: JC-006 - Workstation auto-assignment

    Trigger: Job Card Before Insert

    Args:
        doc: Job Card document
        method: Event method name (optional)

    Logic:
    - Never rotate a workstation already set on the Job Card. That covers a
      user's choice and, later, a capacity planner's choice. Scheduling must
      call pick_workstation() before it creates time logs instead of relying on
      this hook to correct the machine afterwards.
    - Get the BOM Operation for this Job Card's operation (parent BOM, then the
      item's own BOM for multi-level builds).
    - Route by Workstation Type, which the BOM uses to group interchangeable
      machines: rotate across the eligible workstations of that type (least
      recently used, skipping Maintenance/Problem/Setup and machines already at their
      concurrent capacity where possible).
    - If the BOM Operation has no type, fall back to the type ERPNext copied
      onto the Job Card from the Work Order Operation.
    - Backward compatibility: a BOM Operation that names a machine instead of a
      type is honoured when that machine is eligible. It is treated as a
      preference, not a hard constraint: a blocked machine falls back to
      rotation within its type with a logged warning. Teksons routes by type,
      so this path only handles legacy rows.
    - Assign workstation and copy plant_floor
    """
    if not (doc.work_order and doc.operation):
        return

    # Get BOM from Work Order
    bom_no = frappe.db.get_value("Work Order", doc.work_order, "bom_no")

    bom_op = None
    if bom_no:
        # Fetch BOM Operation from parent BOM
        bom_op = frappe.db.get_value(
            "BOM Operation",
            {"parent": bom_no, "operation": doc.operation},
            ["workstation_type", "workstation"],
            as_dict=True
        )

    # If not found in parent BOM, try child BOM for this item (multi-level)
    if not bom_op and getattr(doc, "production_item", None):
        child_bom = frappe.db.get_value("BOM",
            {"item": doc.production_item, "is_active": 1, "docstatus": 1})
        if child_bom and child_bom != bom_no:
            bom_op = frappe.db.get_value(
                "BOM Operation",
                {"parent": child_bom, "operation": doc.operation},
                ["workstation_type", "workstation"],
                as_dict=True
            )

    reasons = []
    explicit = bom_op.get("workstation") if bom_op else None
    workstation_type = bom_op.get("workstation_type") if bom_op else None
    explicit_is_machine = bool(explicit) and frappe.db.exists("Workstation", explicit)

    if not workstation_type and explicit and not explicit_is_machine:
        # Legacy routing rows store the workstation *type* in `workstation`
        # and leave `workstation_type` blank.
        workstation_type = explicit
        explicit = None
        explicit_is_machine = False

    # ERPNext copies the BOM Operation's routing onto the Work Order Operation
    # and then onto the Job Card, so this is the same type. It matters when the
    # BOM Operation cannot be resolved (e.g. a renamed Operation master).
    workstation_type = workstation_type or doc.get("workstation_type")

    if doc.get("workstation"):
        # A workstation already on the card is a deliberate choice — the user's
        # or, later, the capacity planner's — so it is never rotated. The one
        # exception is a machine configured on a legacy BOM Operation, which
        # ERPNext copies onto the card before insert: it still has to be
        # eligible, otherwise fall back to rotating within its type.
        if not (explicit_is_machine and doc.workstation == explicit):
            return

        if is_workstation_eligible(doc.workstation, reasons):
            return

        workstation_type = workstation_type or frappe.db.get_value(
            "Workstation", explicit, "workstation_type"
        )
    elif not workstation_type and explicit_is_machine:
        # Backward compatibility: BOM Operation names a specific machine.
        # Treat it as a preference (Teksons routes by Workstation Type).
        if is_workstation_eligible(explicit, reasons):
            _assign_workstation(doc, explicit)
            return

        # Blocked machine: the machine is a preference, so rotate within its
        # type when we can and keep the Job Card moving. Log the rejection.
        workstation_type = frappe.db.get_value(
            "Workstation", explicit, "workstation_type"
        )

    if not workstation_type and not reasons:
        reasons.append(
            f"BOM Operation {doc.operation} has no Workstation Type"
        )

    workstation = pick_workstation(workstation_type, reasons)

    if reasons:
        frappe.logger("tekson").warning(
            f"Job Card {doc.get('name') or doc.operation}: " + "; ".join(reasons)
        )

    if workstation:
        if workstation_type and not doc.get("workstation_type"):
            doc.workstation_type = workstation_type
        _assign_workstation(doc, workstation)


def _assign_workstation(doc, workstation):
    """Set the workstation and its plant floor on a Job Card."""
    doc.workstation = workstation

    # Also set plant_floor for warehouse mapping
    plant_floor = frappe.db.get_value("Workstation", workstation, "plant_floor")

    if plant_floor:
        doc.custom_plant_floor = plant_floor


def set_wip_warehouse(doc, method=None):
    """
    Auto-set WIP Warehouse based on Workstation's plant_floor
    
    Called on Job Card validate event
    
    Args:
        doc: Job Card document
        method: Event method name (optional)
    
    Business Rule:
    - Job Card WIP warehouse must match the Workstation's plant floor
    - Format: WIP-{plant_floor} - TPL
    
    Example:
    - Workstation: RP-26_Hydraulic Press (plant_floor: RP)
    - Job Card wip_warehouse: WIP-RP - TPL
    """
    if doc.workstation:
        # Get workstation's plant floor
        plant_floor = frappe.db.get_value('Workstation', doc.workstation, 'plant_floor')
        
        if plant_floor:
            # Set WIP warehouse based on plant floor
            expected_warehouse = f"WIP-{plant_floor} - TPL"
            
            # Update if different or not set
            if doc.wip_warehouse != expected_warehouse:
                doc.wip_warehouse = expected_warehouse
            
            # Also set custom_plant_floor for reference
            doc.custom_plant_floor = plant_floor


def update_work_order_status_if_ready(work_order):
    """
    Update Work Order status to "In Process" if materials are available
    
    Business Rule: WO-001 - Auto-complete when all Job Cards complete
    
    Args:
        work_order: Work Order name
    
    Logic:
    - Check Material Readiness for the WO
    - If materials available in WIP, set status to "In Process"
    - This follows ERPNext standard: WO status changes when production starts
    """
    if not work_order:
        return
    
    try:
        # Cheap status guard FIRST: skip the full material readiness
        # evaluation entirely unless there is something to update
        # (this hook fires on every Job Card insert).
        wo_state = frappe.db.get_value(
            "Work Order", work_order, ["docstatus", "status"], as_dict=True
        )
        if not wo_state or wo_state.docstatus != 1 or wo_state.status != "Not Started":
            return
        
        from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
        
        engine = MaterialReadinessEngine(work_order=work_order)
        readiness = engine.evaluate_material_readiness()
        
        if readiness.is_ready:
            wo = frappe.get_doc("Work Order", work_order)
            # Re-check under load: only update submitted, still Not Started
            if wo.docstatus == 1 and wo.status == "Not Started":
                wo.status = "In Process"
                wo.save(ignore_permissions=True)
                frappe.logger("tekson").info(f"Work Order {work_order} status updated to In Process")
    except Exception as e:
        frappe.logger("tekson").error(f"Error updating WO status: {e}")


def update_job_card_status(doc, method=None):
    """
    Update Job Card status fields (start_status, dependency, material)
    
    Called on Job Card validate event
    
    Business Rules:
    - JC-003: Material readiness check
    - JC-004: Auto-refresh dependent Job Cards
    - MR-015: Live evaluation at Job Card start
    
    Updates:
    - custom_start_status
    - custom_dependency_check
    - custom_can_start_operation
    - custom_material_available_for_operation
    """
    # Skip if document is new or being submitted
    if doc.is_new() or doc.flags.ignore_validate:
        return
    
    # Debug breadcrumb — was frappe.log_error(), which INSERTs an Error Log
    # document on every Job Card save (write amplifier on a hot path).
    frappe.logger("tekson").debug(
        "MES validate hook: update_job_card_status JC=%s status=%s ignore_validate=%s",
        doc.name, doc.status, doc.flags.ignore_validate
    )
    
    from tekson_manufacturing.services.job_card_service import JobCardService
    
    service = JobCardService()
    
    # Set all status fields based on JC state
    if doc.status == "Completed":
        doc.custom_start_status = "Completed"
        doc.custom_can_start_operation = 0
        doc.custom_material_available_for_operation = 0
        return
    
    if doc.status == "Work In Progress":
        doc.custom_start_status = "In Progress"
        doc.custom_can_start_operation = 0
        doc.custom_material_available_for_operation = 0
        return
    
    # Open JC — evaluate readiness
    service.update_start_status(doc)
    service.update_dependency_status(doc)
    service.update_material_status(doc)
    
    # Debug: Log the update
    frappe.logger("tekson").info(f"Job Card {doc.name} status updated: {doc.custom_start_status}")


def validate_job_card_start(doc, method=None):
    """
    Block Job Card start if materials are not available
    
    Business Rules:
    - JC-003: Job Card should not start if materials are not available
    - MR-014: Department WIP as Source of Truth
    
    Only runs on transition to "Work In Progress" (not on every save).
    """
    old_doc = doc.get_doc_before_save()
    
    # Only validate on transition to Work In Progress
    if not old_doc or old_doc.status == "Work In Progress":
        return
    
    if doc.status != "Work In Progress":
        return
    
    if doc.work_order:
        # Check dependency: previous operation must be completed
        from tekson_manufacturing.validation.dependency_engine import DependencyEngine
        dep_engine = DependencyEngine()
        dep_result = dep_engine.validate_previous_operation(doc)
        
        if not dep_result.can_start:
            detail = (
                f"Complete {dep_result.previous_jc_name} first."
                if dep_result.previous_jc_name
                else dep_result.diagnostic
            )
            frappe.throw(
                f"Cannot start {doc.operation}: {dep_result.reason}.<br>{detail}",
                title=_("Previous Operation Not Complete")
            )
        
        # Check material readiness
        from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
        engine = MaterialReadinessEngine(work_order=doc.work_order)
        readiness = engine.evaluate_material_readiness(work_order=doc.work_order, job_card=doc.name)
        
        # Update custom_can_start_operation based on ACTUAL live check result
        doc.custom_can_start_operation = 1 if readiness.is_ready else 0
        doc.custom_material_available_for_operation = 1 if readiness.is_ready else 0
        
        if not readiness.is_ready:
            # Request the planned inter-department transfers BEFORE throwing.
            # after_commit=False on purpose: this call raises next, the
            # transaction rolls back, and a rollback discards after-commit
            # callbacks — queueing now keeps the request alive so stock lands
            # for the retry. (Under bench run-tests now=True runs it sync.)
            from tekson_manufacturing.readiness.material_readiness import (
                enqueue_inter_department_transfers,
            )
            enqueue_inter_department_transfers(
                readiness.pending_transfers, after_commit=False
            )

            # Block the start
            shortage_details = readiness.shortage_details
            
            error_msg = f"Cannot start Job Card: Materials not available in {readiness.warehouse}.<br><br>"
            
            if shortage_details:
                error_msg += "Missing Materials:<br>"
                items = []
                for item in shortage_details[:5]:
                    reason = item.get('reason', '')
                    if reason:
                        items.append(f"{item.get('item_code', 'Unknown')}: {reason}")
                    else:
                        items.append(f"{item.get('item_code', 'Unknown')}: Required {item.get('required_qty', 0)}, Available {item.get('available_qty', 0)}")
                error_msg += "<br>".join(items)
            
            frappe.throw(error_msg, title=_("Material Not Available"))


def update_wo_status_on_jc_start(doc, method=None):
    """
    Update Work Order status to "In Process" when a Job Card starts
    
    Business Rule: WO status should change to "In Process" when first JC starts
    
    Trigger: Job Card on_submit (when status changes to "Work In Progress")
    
    Args:
        doc: Job Card document
        method: Event method name (optional)
    """
    if not doc.work_order:
        return
    
    # Only act on transition to "Work In Progress"
    old_doc = doc.get_doc_before_save()
    if not old_doc or old_doc.status == "Work In Progress":
        return
    
    if doc.status != "Work In Progress":
        return
    
    try:
        wo = frappe.get_doc("Work Order", doc.work_order)
        # Only update if WO is submitted and status is "Not Started"
        if wo.docstatus == 1 and wo.status == "Not Started":
            wo.status = "In Process"
            wo.save(ignore_permissions=True)
            frappe.logger("tekson").info(f"Work Order {doc.work_order} status updated to In Process on JC start")
    except Exception as e:
        frappe.logger("tekson").error(f"Error updating WO status on JC start: {e}")
