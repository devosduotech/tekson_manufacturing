import frappe
from frappe import _


def populate_job_card_fields(doc, method=None):
    """
    Auto-populate all Job Card custom fields from UAT
    
    Business Rules:
    - JC-007: Item visibility
    - JC-008: Quantity visibility
    
    Trigger: Job Card Before Insert
    
    Fields Populated:
    - custom_operation_item_code: From Work Order production_item
    - custom_actual_production_qty: Quantity to produce
    - custom_plant_floor: From Workstation
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
        else:
            doc.custom_actual_production_qty = wo.qty


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
        
        if bom_no:
            # Fetch BOM Operation
            bom_op = frappe.db.get_value(
                "BOM Operation",
                {"parent": bom_no, "operation": doc.operation},
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


def update_job_card_status(doc, method=None):
    """
    Update Job Card status fields (start_status, dependency, material)
    
    Called on Job Card validate event
    
    Args:
        doc: Job Card document
        method: Event method name (optional)
    
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
