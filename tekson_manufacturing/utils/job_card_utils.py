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


def allocate_workstation(doc, method=None):
    """
    Auto-allocate Workstation from BOM Operation
    
    Business Rule: JC-006 - Workstation auto-assignment
    
    Trigger: Job Card Before Insert
    
    Args:
        doc: Job Card document
        method: Event method name (optional)
    
    Logic:
    - If workstation not set and work_order + operation exist
    - Get BOM from Work Order
    - Fetch BOM Operation with matching operation
    - Use workstation_type or workstation from BOM Operation
    - Select first workstation of that type
    - Assign workstation and copy plant_floor
    """
    if not doc.workstation and doc.work_order and doc.operation:
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
        if not bom_op and hasattr(doc, 'production_item') and doc.production_item:
            child_bom = frappe.db.get_value("BOM", 
                {"item": doc.production_item, "is_active": 1, "docstatus": 1})
            if child_bom and child_bom != bom_no:
                bom_op = frappe.db.get_value(
                    "BOM Operation",
                    {"parent": child_bom, "operation": doc.operation},
                    ["workstation_type", "workstation"],
                    as_dict=True
                )
        
        if bom_op:
                # Prefer workstation_type, fallback to workstation
                workstation_type = bom_op.workstation_type or bom_op.workstation
                
                if workstation_type:
                    # Get first workstation of this type (alphabetically)
                    workstation = frappe.db.get_value(
                        "Workstation",
                        {"workstation_type": workstation_type},
                        "name",
                        order_by="name asc"
                    )
                    
                    if workstation:
                        doc.workstation = workstation
                        
                        # Also set plant_floor for warehouse mapping
                        plant_floor = frappe.db.get_value(
                            "Workstation",
                            workstation,
                            "plant_floor"
                        )
                        
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
        from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
        
        engine = MaterialReadinessEngine(work_order=work_order)
        readiness = engine.evaluate_material_readiness()
        
        if readiness.is_ready:
            wo = frappe.get_doc("Work Order", work_order)
            # Only update if WO is submitted and status is "Not Started"
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
    
    from tekson_manufacturing.services.job_card_service import JobCardService
    
    service = JobCardService()
    
    # Update all status fields
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
        from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
        
        engine = MaterialReadinessEngine(work_order=doc.work_order)
        readiness = engine.evaluate_material_readiness(work_order=doc.work_order, job_card=doc.name)
        
        if not readiness.is_ready:
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
