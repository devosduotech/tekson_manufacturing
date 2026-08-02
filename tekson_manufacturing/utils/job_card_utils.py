import frappe


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
